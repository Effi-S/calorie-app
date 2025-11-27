"""This module holds a connection for our Food Database "FoodDB"
Parameters to and from this DB are passed with instances of the  dataclass "Food". """
from __future__ import annotations

from dataclasses import dataclass, field, astuple, asdict
from datetime import datetime as dt
from typing import Iterable, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from calorie_count.src.utils import config
from calorie_count.src.DB.models import FoodModel, get_session, create_tables


@dataclass
class Food:
    """This dataclass represents a row in FoodDB"""
    name: str
    portion: float  # (g)
    proteins: float  # (g)
    fats: float  # (g)
    carbs: float  # (g)
    sugar: float  # (g)
    sodium: float  # (mg)
    water: float  # (g)
    id: str = field(default=None)

    def __post_init__(self):
        self.portion = self.portion or 0
        self.sodium = self.sodium or 0
        self.sugar = self.sugar or 0
        self.water = self.water or 0
        self.id = self.name or dt.now().isoformat()

    @property
    def cals(self):
        """Calculate the calories of the Food."""
        return self.proteins * 4 + self.carbs * 4 + self.fats * 9

    @staticmethod
    def columns() -> tuple[str, ...]:
        """Get all the column headers for representing a 'Food' to the customer."""
        return 'Name', 'Portion (g)', 'Protein (g)', 'Fats (g)', 'Carbs (g)', \
            'Sugar (g)', 'Sodium (mg)', 'Water (g)', 'Calories'

    @property
    def values(self) -> tuple[float, ...] | tuple[float | any, ...]:
        """Get all the Values in the Food to represent to the customer."""
        return astuple(self)[:-1] + (self.cals,)  # everything but "id" + calories

    @classmethod
    def from_model(cls, model: FoodModel) -> 'Food':
        """Create Food dataclass from SQLAlchemy model."""
        return cls(
            name=model.name or '',
            portion=model.portion or 0,
            proteins=model.protein or 0,
            fats=model.fats or 0,
            carbs=model.carbs or 0,
            sugar=model.sugar or 0,
            sodium=model.sodium or 0,
            water=model.water or 0,
            id=model.id or ''
        )

    def to_model(self) -> FoodModel:
        """Convert Food dataclass to SQLAlchemy model."""
        return FoodModel(
            name=self.name,
            portion=self.portion,
            protein=self.proteins,
            fats=self.fats,
            carbs=self.carbs,
            sugar=self.sugar,
            sodium=self.sodium,
            water=self.water,
            id=self.id
        )


class FoodDB:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.get_db_path()
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

    def get_all_foods(self) -> list[Food]:
        """Get all foods from the database."""
        foods = self.session.query(FoodModel).filter(FoodModel.name != '').all()
        return [Food.from_model(f) for f in foods if f.name]

    def get_all_food_names(self) -> list[str]:
        """Get all food names from the database."""
        names = self.session.query(FoodModel.name).filter(FoodModel.name != '').all()
        return [str(name[0]) for name in names if name[0]]

    def get_food_by_name(self, name: str) -> Food:
        """Get food by name."""
        food_model = self.session.query(FoodModel).filter(FoodModel.name == name).first()
        if food_model:
            return Food.from_model(food_model)
        # Return empty Food if not found (maintaining backward compatibility)
        return Food('', 0, 0, 0, 0, 0, 0, 0)

    def get_food_by_id(self, id_: str) -> Food:
        """Get food by ID."""
        food_model = self.session.query(FoodModel).filter(FoodModel.id == id_).first()
        if food_model:
            return Food.from_model(food_model)
        # Return empty Food if not found (maintaining backward compatibility)
        return Food('', 0, 0, 0, 0, 0, 0, 0)

    def add_food(self, food: Food, update: bool = False):
        """Add or update food in the database."""
        food_model = self.session.query(FoodModel).filter(FoodModel.name == food.name).first()
        
        if food_model and update:
            # Update existing food
            food_model.portion = food.portion
            food_model.protein = food.proteins
            food_model.fats = food.fats
            food_model.carbs = food.carbs
            food_model.sugar = food.sugar
            food_model.sodium = food.sodium
            food_model.water = food.water
            food_model.id = food.id
        elif not food_model:
            # Insert new food
            food_model = food.to_model()
            self.session.add(food_model)
        
        self.session.commit()

    def remove(self, names: Optional[str | list[str]]) -> None:
        """Remove foods by name(s)."""
        if isinstance(names, str):
            names = [names]
        if not names:
            return

        # Check for references in meal_entries
        from calorie_count.src.DB.models import MealEntryModel
        referenced_query = self.session.query(FoodModel.name).join(
            MealEntryModel, MealEntryModel.meal_id == FoodModel.id
        ).filter(FoodModel.name.in_(names))
        referenced_names = referenced_query.all()
        
        to_clear_name = [name[0] for name in referenced_names if name[0]]
        to_delete = [n for n in names if n not in to_clear_name]

        if to_delete:
            self.session.query(FoodModel).filter(FoodModel.name.in_(to_delete)).delete(synchronize_session=False)
            self.session.commit()

        if to_clear_name:
            # Clear name instead of deleting (food is referenced)
            self.session.query(FoodModel).filter(FoodModel.name.in_(to_clear_name)).update(
                {FoodModel.name: ''}, synchronize_session=False
            )
            self.session.commit()
