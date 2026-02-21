from __future__ import annotations

from contextlib import contextmanager
from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.models.task_model import Task
from src.services.logger import get_logger

logger = get_logger("task_service")

VALID_STATUSES = {
    "PENDING",
    "RUNNING",
    "AWAITING_APPROVAL",
    "COMPLETED",
    "FAILED",
}


class TaskService:
    @contextmanager
    def _get_session(self) -> Session:
        session: Session = SessionLocal()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as db_error:
            session.rollback()
            self._log_db_action(
                action_details="DB transaction rolled back",
                stage="db_error",
                error=str(db_error),
            )
            raise
        except Exception as e:
            session.rollback()
            self._log_db_action(
                action_details="Unexpected DB error",
                stage="db_error",
                error=str(e),
            )
            raise
        finally:
            session.close()

    def _log_db_action(
        self,
        task_id: Optional[str] = None,
        action_details: str = "",
        stage: Optional[str] = None,
        **extra_fields,
    ) -> None:
        payload = {
            "task_id": task_id,
            "stage": stage,
            "action_details": action_details,
        }
        payload.update(extra_fields)
        logger.info(action_details, extra=payload)

    def create_task(self, task_id: str, prompt: str) -> None:
        with self._get_session() as session:
            new_task = Task(
                id=task_id,
                prompt=prompt,
                status="PENDING",
                result=None,
                agent_logs=[],
            )
            session.add(new_task)

            self._log_db_action(
                task_id=task_id,
                stage="db_created",
                action_details="Task created",
                status="PENDING",
            )

    def update_task_status(self, task_id: str, status: str) -> None:
        if status not in VALID_STATUSES:
            self._log_db_action(
                task_id=task_id,
                stage="status_updated",
                action_details="Invalid status update attempted",
                attempted_status=status,
            )
            return

        try:
            with self._get_session() as session:
                task = session.get(Task, task_id)

                if not task:
                    self._log_db_action(
                        task_id=task_id,
                        stage="status_updated",
                        action_details="Task not found for status update",
                        new_status=status,
                    )
                    return

                old_status = task.status
                task.status = status

                self._log_db_action(
                    task_id=task_id,
                    stage="status_updated",
                    action_details="Status updated",
                    old_status=old_status,
                    new_status=status,
                )

        except Exception as e:
            self._log_db_action(
                task_id=task_id,
                stage="status_updated",
                action_details="Failed to update status",
                error=str(e),
            )

    def append_agent_logs(self, task_id: str, logs: List[dict]) -> None:
        if not logs:
            return

        try:
            with self._get_session() as session:
                task = session.get(Task, task_id)

                if not task:
                    self._log_db_action(
                        task_id=task_id,
                        stage="logs_appended",
                        action_details="Task not found for log append",
                    )
                    return

                existing_logs = task.agent_logs or []
                merged_logs = existing_logs + logs
                task.agent_logs = merged_logs

                self._log_db_action(
                    task_id=task_id,
                    stage="logs_appended",
                    action_details="Agent logs appended",
                    appended_count=len(logs),
                    total_count=len(merged_logs),
                )

        except Exception as e:
            self._log_db_action(
                task_id=task_id,
                stage="logs_appended",
                action_details="Failed to append agent logs",
                error=str(e),
            )

    def store_result(
        self,
        task_id: str,
        result: str,
        logs: List[dict],
    ) -> None:
        try:
            with self._get_session() as session:
                task = session.get(Task, task_id)

                if not task:
                    self._log_db_action(
                        task_id=task_id,
                        stage="result_stored",
                        action_details="Task not found for result storage",
                    )
                    return

                if task.status == "COMPLETED":
                    self._log_db_action(
                        task_id=task_id,
                        stage="result_stored",
                        action_details="store_result skipped — already completed",
                    )
                    return

                existing_logs = task.agent_logs or []
                merged_logs = existing_logs + logs

                task.result = result
                task.status = "COMPLETED"
                task.agent_logs = merged_logs

                self._log_db_action(
                    task_id=task_id,
                    stage="result_stored",
                    action_details="Result stored and task completed",
                    logs_count=len(merged_logs),
                    status="COMPLETED",
                )

        except Exception as e:
            self._log_db_action(
                task_id=task_id,
                stage="result_stored",
                action_details="Failed to store result",
                error=str(e),
            )

    def get_task(self, task_id: str) -> Optional[dict]:
        try:
            with self._get_session() as session:
                task = session.get(Task, task_id)

                if not task:
                    self._log_db_action(
                        task_id=task_id,
                        stage="task_fetched",
                        action_details="Task not found",
                    )
                    return None

                task_data = {
                    "task_id": str(task.id),
                    "prompt": task.prompt,
                    "status": task.status,
                    "result": task.result,
                    "agent_logs": task.agent_logs or [],
                    "created_at": task.created_at,
                    "updated_at": task.updated_at,
                }

                self._log_db_action(
                    task_id=task_id,
                    stage="task_fetched",
                    action_details="Task fetched",
                    status=task.status,
                )

                return task_data

        except Exception as e:
            self._log_db_action(
                task_id=task_id,
                stage="task_fetched",
                action_details="Failed to fetch task",
                error=str(e),
            )
            return None


task_service = TaskService()