"""SQLAlchemy models for the calorie counting app."""
from __future__ import annotations

from datetime import datetime as dt
from sqlalchemy import Column, String, Float, Text, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Optional

from calorie_count.src.utils import config

Base = declarative_base()


class FoodModel(Base):
    """SQLAlchemy model for Food table."""
    __tablename__ = 'food'

    name = Column(String, primary_key=True)
    portion = Column(Float, default=0)
    protein = Column(Float, default=0)
    fats = Column(Float, default=0)
    carbs = Column(Float, default=0)
    sugar = Column(Float, default=0)
    sodium = Column(Float, default=0)
    water = Column(Float, default=0)
    id = Column(String)

    def __repr__(self):
        return f"<FoodModel(name='{self.name}', id='{self.id}')>"


class MealEntryModel(Base):
    """SQLAlchemy model for MealEntry table."""
    __tablename__ = 'meal_entries'

    id = Column(String, primary_key=True)
    meal_id = Column(String)
    portion = Column(Float)
    date = Column(String)

    def __repr__(self):
        return f"<MealEntryModel(id='{self.id}', meal_id='{self.meal_id}', date='{self.date}')>"


class ExternalFoodModel(Base):
    """SQLAlchemy model for External Foods table."""
    __tablename__ = 'foods'

    description = Column(Text, primary_key=True)
    portions = Column(Text)
    protein = Column(Float)
    fats = Column(Float)
    carbs = Column(Float)
    sodium = Column(Float)
    sugar = Column(Float)
    water = Column(Float)

    def __repr__(self):
        return f"<ExternalFoodModel(description='{self.description}')>"


# Session management
_engines = {}
_sessions = {}


def get_engine(db_path: Optional[str] = None) -> create_engine:
    """Get or create SQLAlchemy engine for a database path."""
    db_path = db_path or config.get_db_path()
    if db_path not in _engines:
        _engines[db_path] = create_engine(
            f'sqlite:///{db_path}',
            connect_args={'timeout': 15},
            echo=False
        )
    return _engines[db_path]


def get_session(db_path: Optional[str] = None) -> Session:
    """Get or create SQLAlchemy session for a database path."""
    db_path = db_path or config.get_db_path()
    if db_path not in _sessions:
        engine = get_engine(db_path)
        SessionLocal = sessionmaker(bind=engine)
        _sessions[db_path] = SessionLocal
    return _sessions[db_path]()


def create_tables(db_path: Optional[str] = None):
    """Create all tables in the database."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)


def close_all_sessions():
    """Close all active sessions and engines."""
    for session_factory in _sessions.values():
        # Close any active sessions
        pass
    for engine in _engines.values():
        engine.dispose()
    _sessions.clear()
    _engines.clear()
