"""This module holds a connection for our Meal-Entries Database "MealEntries"
Parameters to and from this DB are passed with instances of the  dataclass "MealEntry". """
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from calorie_count.src.DB.food_db import Food, FoodDB
from calorie_count.src.DB.models import MealEntryModel, create_tables, get_session
from calorie_count.src.utils import config
from calorie_count.src.utils.utils import str2iso


@dataclass
class MealEntry:
    """This dataclass represents the data in the MealEntries DB"""
    name:         Optional[str]    = field(default=None)
    portion:      Optional[float]  = field(default=None)
    date:         Optional[str]    = field(default=None)
    food:         Optional[Food]   = field(default=None)
    id:           Optional[str]    = field(default=None)  # The ID is added only when the entry is added to the DB
    FOOD_DB_PATH: Optional[str]    = None  # init function for FoodDB

    def __post_init__(self):
        assert self.name or self.food, 'name or meal missing'
        if self.name and not self.food:
            with FoodDB(self.FOOD_DB_PATH) as fdb:
                self.food = fdb.get_food_by_name(self.name)
        if self.food and not self.name:
            # means nameless meal-entry
            with FoodDB(self.FOOD_DB_PATH) as fdb:
                fdb.add_food(food=self.food)
                print(f'Added to MealDB: {self.food}.')

        if not self.date:
            self.date = dt.now().date().isoformat()

        if not self.portion:
            self.portion = self.food.portion
        elif self.portion != self.food.portion:
            ratio = self.portion / self.food.portion
            self.food.carbs *= ratio
            self.food.fats *= ratio
            self.food.proteins *= ratio
            self.food.sodium *= ratio
            self.food.sugar *= ratio

    @staticmethod
    def columns() -> tuple[str, ...]:
        """The columns for displaying """
        return 'Date', 'Name', 'Portion (g)', 'Protein (g)', 'Fats (g)', 'Carbs (g)', 'Sugar (g)', 'Sodium (mg)', \
            'Water (g)', 'Calories'

    @property
    def values(self) -> tuple:
        return self.date, self.name, self.portion, self.food.proteins, self.food.fats, self.food.carbs, \
            self.food.sugar, self.food.sodium, self.food.water, self.food.cals

    @classmethod
    def from_model(cls, model: MealEntryModel, food: Food) -> 'MealEntry':
        """Create MealEntry dataclass from SQLAlchemy model and Food."""
        return cls(
            name=food.name,
            portion=model.portion,
            date=model.date,
            food=food,
            id=model.id
        )


class MealEntryDB:
    MealEntry: MealEntry = MealEntry  # coupling MealEntry to MealEntryDB instance

    def __init__(self, db_path: str = None):
        if not db_path:
            db_path = config.get_db_path()
        self.db_path = db_path
        self.MealEntry.FOOD_DB_PATH = db_path

        # Create tables if they don't exist
        create_tables(self.db_path)
        self._session: Optional[Session] = None

    def __enter__(self, *a, **k):
        self._session = get_session(self.db_path)
        return self

    def __exit__(self, *a, **k):
        if self._session:
            self._session.close()
            self._session = None

    @property
    def session(self) -> Session:
        """Get current session, creating one if needed."""
        if self._session is None:
            self._session = get_session(self.db_path)
        return self._session

    def add_meal_entry(self, entry: MealEntry):
        """Add a meal entry to the database."""
        entry.id = dt.now().isoformat()
        meal_entry_model = MealEntryModel(
            id=entry.id,
            meal_id=entry.food.id,
            portion=entry.portion,
            date=entry.date
        )
        self.session.add(meal_entry_model)
        self.session.commit()

    def get_entries_between_dates(self, start_date: str, end_date: str) -> list[MealEntry]:
        """Get meal entries between two dates."""
        entries = self.session.query(MealEntryModel).filter(
            MealEntryModel.date >= start_date,
            MealEntryModel.date <= end_date
        ).all()
        
        ret = []
        with FoodDB(self.db_path) as fdb:
            for entry_model in entries:
                meal = fdb.get_food_by_id(entry_model.meal_id)
                ret.append(self.MealEntry.from_model(entry_model, meal))
        return ret

    def get_first_last_dates(self) -> tuple[dt.date, dt.date]:
        """Get the first and the last date of all entries"""
        result = self.session.query(
            func.min(MealEntryModel.date),
            func.max(MealEntryModel.date)
        ).first()
        
        start, end = result
        if not any((start, end)):
            today = str2iso(dt.now().date().isoformat())
            return today, today

        start, end = str2iso(start), str2iso(end)
        return start, end

    def delete_entry(self, time_stamp: str) -> None:
        """Remove an entry based on its id."""
        self.session.query(MealEntryModel).filter(MealEntryModel.id == time_stamp).delete()
        self.session.commit()
