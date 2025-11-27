"""External foods database using SQLAlchemy."""
from __future__ import annotations

import atexit
from dataclasses import asdict, astuple, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import Column, func
from sqlalchemy.orm import Session

from calorie_count.src.DB.models import (
    ExternalFoodModel,
    create_tables,
    get_engine,
    get_session,
)


def similarity(a: str, b: str) -> float:
    """Get similarity between 2 strings based on diff-lib's SequenceMatcher ratio"""
    return SequenceMatcher(None, str(a), str(b)).ratio()


@dataclass
class FoodData:
    """This class represents a Searchable Food """
    description: str   | Column[str]
    portions:    str   | Column[str]   # string representation of mapping portion to quantity(g)  e.x - 'cup:30,bowl:100'...
    protein:     float | Column[float]
    fats:        float | Column[float]
    carbs:       float | Column[float]
    sodium:      float | Column[float]
    sugar:       float | Column[float]
    water:       float | Column[float]
    
    def __post_init__(self):
        self.description = self.description.replace('"', '')

    def portions_dict(self) -> dict[str, float]:
        """Parse portions string into dictionary."""
        result = {}
        if bool(self.portions):
            for item in self.portions.split(','):
                if ':' in item:
                    key, value = item.split(':', 1)
                    try:
                        result[key.strip()] = float(value.strip())
                    except ValueError:
                        pass
        return result

    @classmethod
    def from_model(cls, model: ExternalFoodModel) -> 'FoodData':
        """Create FoodData from SQLAlchemy model."""
        return cls(
            description=model.description,
            portions=model.portions,
            protein=model.protein or 0,
            fats=model.fats or 0,
            carbs=model.carbs or 0,
            sodium=model.sodium or 0,
            sugar=model.sugar or 0,
            water=model.water or 0
        )

    def to_model(self) -> ExternalFoodModel:
        """Convert FoodData to SQLAlchemy model."""
        return ExternalFoodModel(
            description=self.description,
            portions=self.portions,
            protein=self.protein,
            fats=self.fats,
            carbs=self.carbs,
            sodium=self.sodium,
            sugar=self.sugar,
            water=self.water
        )


class ExternalFoodsDB:
    def __init__(self, locally: bool = False):
        path = next(iter(Path().glob('**/external_foods')), None)
        assert path, 'Could not find "external_foods" file'
        self.db_path = str(path)
        
        # Create tables if they don't exist
        create_tables(self.db_path)
        
        # Register custom similarity function for SQLite
        # This needs to be done per connection, so we'll do it in get_session
        # For now, we'll handle similarity in Python instead of SQL
        
        self._session: Optional[Session] = None
        atexit.register(lambda: self._cleanup())

    def _cleanup(self):
        """Cleanup method called on exit."""
        if self._session:
            self._session.close()
            self._session = None

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

    def add_food(self, food: FoodData):
        """Add a food to the external foods database."""
        food_model = self.session.query(ExternalFoodModel).filter(
            ExternalFoodModel.description == food.description
        ).first()
        
        if not food_model:
            food_model = food.to_model()
            self.session.add(food_model)
            self.session.commit()

    def get_similar_food_by_name(self, name: str, max_results: int = 15) -> Generator[FoodData]:
        """Given a name of a food return the most similar food in the DB.
        Ordered most similar to least similar.
        By default maximum of 15 values in the list, override 'max_results' to change this.

        Algorithm of similarity:
            1. Get foods where the given name is contained in the description.
            2. If none found in 1. - iterate row-by-row running edit-distance on them
            add those that are > 0.9 ratio.
            (Note: SQLite has 'editdist3' but I don't think it can work on android)"""
        # First, try LIKE search
        foods = self.session.query(ExternalFoodModel).filter(
            ExternalFoodModel.description.like(f'%{name}%')
        ).limit(max_results).all()
        
        count = 0
        for food_model in foods:
            yield FoodData.from_model(food_model)
            count += 1

        # If we need more results, use similarity function
        if count < max_results:
            # Note: SQLAlchemy doesn't directly support custom SQLite functions in WHERE
            # So we'll fetch all and filter in Python for similarity >= 0.9
            all_foods = self.session.query(ExternalFoodModel).all()
            similar_foods = []
            for food_model in all_foods:
                if similarity(food_model.description, name) >= 0.9: # type: ignore
                    similar_foods.append(food_model)
                    if len(similar_foods) >= (max_results - count):
                        break
            
            for food_model in similar_foods:
                yield FoodData.from_model(food_model)
