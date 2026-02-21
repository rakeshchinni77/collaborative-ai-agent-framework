from __future__ import annotations

import os
from datetime import datetime

from src.services.task_service import task_service
from src.services.logger import get_logger

logger = get_logger("worker")

TESTING = os.getenv("PYTEST_RUNNING", "0") == "1"


# =========================================================
# Sync worker for pytest
# =========================================================
def process_task_sync(task_id: str) -> None:
    task_service.update_task_status(task_id, "RUNNING")

    task_service.append_agent_logs(
        task_id,
        [
            {
                "agent": "ResearchAgent",
                "action": "Collected research data",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ],
    )

    task_service.update_task_status(task_id, "AWAITING_APPROVAL")


def resume_task_sync(task_id: str) -> None:
    task_service.append_agent_logs(
        task_id,
        [
            {
                "agent": "WritingAgent",
                "action": "Generated final draft",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ],
    )

    task_service.store_result(
        task_id=task_id,
        result="Final synthesized response",
        logs=[
            {
                "agent": "System",
                "action": "Workflow completed",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ],
    )


# =========================================================
# Celery runtime only
# =========================================================
if not TESTING:
    from src.worker.celery_app import celery_app

    @celery_app.task(name="process_task")
    def process_task(task_id: str):
        process_task_sync(task_id)

    @celery_app.task(name="resume_task")
    def resume_task(task_id: str):
        resume_task_sync(task_id)