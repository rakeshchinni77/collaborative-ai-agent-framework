from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.ext.mutable import MutableList

from src.database import Base


class Task(Base):
    """
    Database-agnostic Task model.

    ✔ SQLite compatible (pytest)
    ✔ Postgres compatible (Docker)
    ✔ Mutable JSON logs (no rollback errors)
    """

    __tablename__ = "tasks"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    prompt = Column(Text, nullable=False)

    status = Column(String(50), nullable=False, default="PENDING")

    result = Column(Text, nullable=True)

    # CRITICAL FIX — mutable JSON for SQLite + Postgres
    agent_logs = Column(MutableList.as_mutable(JSON), default=list, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )