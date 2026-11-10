"""SQLAlchemy models for the calorie counting app."""

from __future__ import annotations

from sqlalchemy import Engine, Text, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)
from sqlalchemy.orm import close_all_sessions as _orm_close_all_sessions

from calorie_count.src.utils import config


class Base(DeclarativeBase):
    """Declarative base for all ORM models (SQLAlchemy 2.0 style)."""


class FoodModel(Base):
    """SQLAlchemy model for Food table."""

    __tablename__ = "food"

    # `id` is the primary key: meal entries reference foods by id (see MealEntryModel.meal_id),
    # and soft-deleting a referenced food blanks its `name` to '' (see FoodDB.remove). `name`
    # must therefore allow duplicates/blanks, so it cannot be the primary key.
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(default="", index=True)
    portion: Mapped[float] = mapped_column(default=0)
    protein: Mapped[float] = mapped_column(default=0)
    fats: Mapped[float] = mapped_column(default=0)
    carbs: Mapped[float] = mapped_column(default=0)
    sugar: Mapped[float] = mapped_column(default=0)
    sodium: Mapped[float] = mapped_column(default=0)
    water: Mapped[float] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"<FoodModel(name='{self.name}', id='{self.id}')>"


class MealEntryModel(Base):
    """SQLAlchemy model for MealEntry table."""

    __tablename__ = "meal_entries"

    id: Mapped[str] = mapped_column(primary_key=True)
    meal_id: Mapped[str | None]
    portion: Mapped[float | None]
    date: Mapped[str | None]

    def __repr__(self) -> str:
        return f"<MealEntryModel(id='{self.id}', meal_id='{self.meal_id}', date='{self.date}')>"


class ExternalFoodModel(Base):
    """SQLAlchemy model for External Foods table."""

    __tablename__ = "foods"

    description: Mapped[str] = mapped_column(Text, primary_key=True)
    portions: Mapped[str | None] = mapped_column(Text)
    protein: Mapped[float | None]
    fats: Mapped[float | None]
    carbs: Mapped[float | None]
    sodium: Mapped[float | None]
    sugar: Mapped[float | None]
    water: Mapped[float | None]

    def __repr__(self) -> str:
        return f"<ExternalFoodModel(description='{self.description}')>"


# Session management: one engine + session factory per database path.
_engines: dict[str, Engine] = {}
_session_factories: dict[str, sessionmaker[Session]] = {}


def get_engine(db_path: str | None = None) -> Engine:
    """Get or create the SQLAlchemy engine for a database path."""
    db_path = db_path or config.get_db_path()
    if db_path not in _engines:
        _engines[db_path] = create_engine(
            f"sqlite:///{db_path}", connect_args={"timeout": 15}, echo=False
        )
    return _engines[db_path]


def get_session(db_path: str | None = None) -> Session:
    """Open a new SQLAlchemy session for a database path."""
    db_path = db_path or config.get_db_path()
    if db_path not in _session_factories:
        _session_factories[db_path] = sessionmaker(bind=get_engine(db_path))
    return _session_factories[db_path]()


def create_tables(db_path: str | None = None) -> None:
    """Create all tables in the database."""
    Base.metadata.create_all(get_engine(db_path))


def close_all_sessions() -> None:
    """Close any open sessions and dispose of all engines."""
    _orm_close_all_sessions()
    for engine in _engines.values():
        engine.dispose()
    _session_factories.clear()
    _engines.clear()
