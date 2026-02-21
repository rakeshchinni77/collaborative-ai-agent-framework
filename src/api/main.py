from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.services.logger import get_logger
from src.api.routes import tasks as tasks_router

from src.database import Base, engine, init_db
import os

logger = get_logger("api")

TESTING = os.getenv("PYTEST_RUNNING") == "1"
# ===============================
# Lifespan (Startup / Shutdown)
# ===============================
@asynccontextmanager
async def lifespan(app: FastAPI):

    # DB must initialize here because pytest loads THIS app
    if TESTING:
        Base.metadata.create_all(bind=engine)
    else:
        init_db()

    logger.info(
        "FastAPI service started",
        extra={
            "service": "api",
            "action_details": "API startup complete",
        },
    )

    yield

    logger.info(
        "FastAPI service stopped",
        extra={
            "service": "api",
            "action_details": "API shutdown complete",
        },
    )

# FastAPI App Instance
app = FastAPI(
    title="Collaborative AI Agent Framework API",
    version="1.0.0",
    lifespan=lifespan,
)


# Health Endpoint (Docker probe)
@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}


# Router Mounting (WITH PREFIX)
app.include_router(
    tasks_router.router,
    prefix="/api/v1/tasks",
    tags=["tasks"],
)


# Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.error(
        "Request validation failed",
        extra={
            "service": "api",
            "path": request.url.path,
            "errors": exc.errors(),
            "action_details": "422 validation error",
        },
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "details": exc.errors(),
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    logger.error(
        "HTTP exception occurred",
        extra={
            "service": "api",
            "path": request.url.path,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "action_details": "HTTP error",
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "detail": exc.detail,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "Unhandled server error",
        extra={
            "service": "api",
            "path": request.url.path,
            "error": str(exc),
            "action_details": "500 internal error",
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "detail": "An unexpected error occurred.",
        },
    )
