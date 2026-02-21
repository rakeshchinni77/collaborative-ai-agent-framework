from __future__ import annotations

import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

from src.config import settings

# =========================================================
# Detect pytest environment
# =========================================================
TESTING = os.getenv("PYTEST_RUNNING", "0") == "1"

# =========================================================
# Database URL selection
# =========================================================
if TESTING:
    DATABASE_URL = "sqlite:///:memory:"
else:
    DATABASE_URL = settings.DATABASE_URL

# =========================================================
# Engine configuration
# =========================================================
from sqlalchemy.pool import StaticPool

if TESTING:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        future=True,
    )

# =========================================================
# Session factory
# =========================================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

# =========================================================
# Base model
# =========================================================
Base = declarative_base()


# =========================================================
# Database initialization
# =========================================================
def init_db() -> None:
    """
    Initializes the database.

    Runtime (Postgres):
    ✔ Enables pgcrypto
    ✔ Creates tables

    Pytest (SQLite):
    ✔ Skips pgcrypto
    ✔ Creates tables in memory
    """

    try:
        # Import models so they register with Base
        from src.models.task_model import Task  # noqa: F401

        if not TESTING:
            # Enable pgcrypto ONLY for Postgres
            with engine.begin() as connection:
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))

        # Create tables for both Postgres and SQLite
        Base.metadata.create_all(bind=engine)

    except SQLAlchemyError as e:
        raise RuntimeError(f"Database initialization failed: {str(e)}") from e


# =========================================================
# FastAPI DB dependency
# =========================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()