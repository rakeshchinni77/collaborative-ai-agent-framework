from __future__ import annotations

import os
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

from src.schemas.task_schemas import (
    CreateTaskRequest,
    CreateTaskResponse,
    TaskStatusResponse,
    ApproveTaskResponse,
    ErrorResponse,
)
from src.services.task_service import task_service
from src.services.logger import get_logger

TESTING = os.getenv("PYTEST_RUNNING", "0") == "1"

if TESTING:
    from src.worker.tasks import process_task_sync, resume_task_sync
else:
    from src.worker.tasks import process_task, resume_task


router = APIRouter(tags=["tasks"])
logger = get_logger("api")


def log_with_task(logger, message: str, task_id: str, stage: str, **extra):
    logger.info(
        message,
        extra={
            "task_id": task_id,
            "stage": stage,
            "action_details": message,
            **extra,
        },
    )


# ======================================================
# Create Task
# ======================================================
@router.post("", response_model=CreateTaskResponse, status_code=status.HTTP_202_ACCEPTED)
def create_task(request: CreateTaskRequest):
    task_id = str(uuid4())

    try:
        log_with_task(logger, "Create task request received", task_id, "api_received")

        task_service.create_task(task_id=task_id, prompt=request.prompt)

        if TESTING:
            process_task_sync(task_id)
        else:
            try:
                process_task.delay(task_id)
            except Exception as e:
                logger.error(
                    "Failed to dispatch Celery task",
                    extra={
                        "task_id": task_id,
                        "error": str(e),
                        "stage": "dispatch_failed",
                    },
                )

        log_with_task(logger, "Task dispatched to worker", task_id, "task_dispatched")

        return CreateTaskResponse(task_id=task_id, status="PENDING")

    except Exception as e:
        logger.exception(
            "Task creation failed",
            extra={
                "task_id": task_id,
                "stage": "api_error",
                "error": str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task",
        )


# ======================================================
# Get Task Status
# ======================================================
@router.get("/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: UUID):
    task = task_service.get_task(str(task_id))

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                detail=f"Task {task_id} does not exist",
                error_code="TASK_NOT_FOUND",
                task_id=str(task_id),
            ).model_dump(),
        )

    log_with_task(logger, "Task status polled", str(task_id), "status_polled")

    return TaskStatusResponse(**task)


# ======================================================
# Approve Task
# ======================================================
@router.post("/{task_id}/approve", response_model=ApproveTaskResponse)
def approve_task(task_id: UUID):
    task = task_service.get_task(str(task_id))

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                detail=f"Task {task_id} does not exist",
                error_code="TASK_NOT_FOUND",
                task_id=str(task_id),
            ).model_dump(),
        )

    current_status = task["status"]

    # TEST MODE (synchronous worker)
    if TESTING:
        if current_status == "AWAITING_APPROVAL":
            resume_task_sync(str(task_id))

        task = task_service.get_task(str(task_id))
        return ApproveTaskResponse(task_id=str(task_id), status=task["status"])

    # PRODUCTION MODE (Celery async)
    if current_status == "AWAITING_APPROVAL":
        task_service.update_task_status(str(task_id), "RUNNING")

        try:
            resume_task.delay(str(task_id))
        except Exception as e:
            logger.error(
                "Failed to dispatch resume task",
                extra={
                    "task_id": str(task_id),
                    "error": str(e),
                    "stage": "resume_dispatch_failed",
                },
            )

        log_with_task(logger, "Resume dispatched to worker", str(task_id), "resume_dispatched")

        return ApproveTaskResponse(task_id=str(task_id), status="RUNNING")

    return ApproveTaskResponse(task_id=str(task_id), status=current_status)