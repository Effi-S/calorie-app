"""This module holds a connection for our Food Database "FoodDB"
Parameters to and from this DB are passed with instances of the  dataclass "Food"."""

from __future__ import annotations

from dataclasses import astuple, dataclass, field
from datetime import datetime as dt
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from calorie_count.src.DB.models import FoodModel, MealEntryModel, create_tables, get_session
from calorie_count.src.utils import config


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
        return (
            "Name",
            "Portion (g)",
            "Protein (g)",
            "Fats (g)",
            "Carbs (g)",
            "Sugar (g)",
            "Sodium (mg)",
            "Water (g)",
            "Calories",
        )

    @property
    def values(self) -> tuple[float, ...] | tuple[float | Any, ...]:
        """Get all the Values in the Food to represent to the customer."""
        return astuple(self)[:-1] + (self.cals,)  # everything but "id" + calories

    @classmethod
    def from_model(cls, model: FoodModel) -> Food:
        """Create Food dataclass from SQLAlchemy model."""
        return cls(
            name=model.name or "",
            portion=model.portion or 0,
            proteins=model.protein or 0,
            fats=model.fats or 0,
            carbs=model.carbs or 0,
            sugar=model.sugar or 0,
            sodium=model.sodium or 0,
            water=model.water or 0,
            id=model.id or "",
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
            id=self.id,
        )


class FoodDB:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.get_db_path()
        # Create tables if they don't exist
        create_tables(self.db_path)
        self._session: Session | None = None

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
        foods = self.session.scalars(select(FoodModel).where(FoodModel.name != "")).all()
        return [Food.from_model(f) for f in foods if f.name]

    def get_all_food_names(self) -> list[str]:
        """Get all food names from the database."""
        names = self.session.scalars(select(FoodModel.name).where(FoodModel.name != "")).all()
        return [str(name) for name in names if name]

    def get_food_by_name(self, name: str) -> Food:
        """Get food by name."""
        food_model = self.session.scalars(select(FoodModel).where(FoodModel.name == name)).first()
        if food_model:
            return Food.from_model(food_model)
        # Return empty Food if not found (maintaining backward compatibility)
        return Food("", 0, 0, 0, 0, 0, 0, 0)

    def get_food_by_id(self, id_: str) -> Food:
        """Get food by ID."""
        food_model = self.session.scalars(select(FoodModel).where(FoodModel.id == id_)).first()
        if food_model:
            return Food.from_model(food_model)
        # Return empty Food if not found (maintaining backward compatibility)
        return Food("", 0, 0, 0, 0, 0, 0, 0)

    def add_food(self, food: Food, update: bool = False):
        """Add or update food in the database.

        Keyed on `id` (the primary key). An existing row is updated when `update`
        is set, or when its name differs from the incoming food -- the latter
        resurrects a soft-deleted row (one whose name was blanked by remove()).
        """
        food_model = self.session.scalars(select(FoodModel).where(FoodModel.id == food.id)).first()

        if food_model is None:
            # Insert new food
            self.session.add(food.to_model())
        elif update or food_model.name != food.name:
            # Update existing food (or restore a soft-deleted one)
            food_model.name = food.name
            food_model.portion = food.portion
            food_model.protein = food.proteins
            food_model.fats = food.fats
            food_model.carbs = food.carbs
            food_model.sugar = food.sugar
            food_model.sodium = food.sodium
            food_model.water = food.water

        self.session.commit()

    def remove(self, names: str | list[str] | None) -> None:
        """Remove foods by name(s)."""
        if isinstance(names, str):
            names = [names]
        if not names:
            return

        # Names still referenced by a meal entry must be kept (soft-deleted).
        referenced = self.session.scalars(
            select(FoodModel.name)
            .join(MealEntryModel, MealEntryModel.meal_id == FoodModel.id)
            .where(FoodModel.name.in_(names))
        ).all()

        to_clear_name = [name for name in referenced if name]
        to_delete = [n for n in names if n not in to_clear_name]

        if to_delete:
            self.session.execute(
                delete(FoodModel)
                .where(FoodModel.name.in_(to_delete))
                .execution_options(synchronize_session=False)
            )
            self.session.commit()

        if to_clear_name:
            # Clear name instead of deleting (food is still referenced by a meal entry).
            self.session.execute(
                update(FoodModel)
                .where(FoodModel.name.in_(to_clear_name))
                .values(name="")
                .execution_options(synchronize_session=False)
            )
            self.session.commit()
