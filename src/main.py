from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.database import Base, engine, init_db
from src.utils.health import health_router
from src.api.main import app as api_app
import src.models.task_model  # register SQLAlchemy model

TESTING = os.getenv("PYTEST_RUNNING") == "1"


# --------------------------------------------------
# Lifespan (DB init)
# --------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):

    if TESTING:
        # pytest → create tables only
        Base.metadata.create_all(bind=engine)
    else:
        # docker → postgres init
        init_db()

    yield


app = FastAPI(
    title="Collaborative AI Agent Framework",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.mount("", api_app)