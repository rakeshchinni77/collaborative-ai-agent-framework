from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from src.services.logger import get_logger
from src.services.redis_service import redis_service


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Provides:
    - Structured logging
    - Redis access
    - DB status update hook (stub-safe)
    - WebSocket push hook (stub-safe)
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = get_logger(agent_name)
        self.redis = redis_service

    # Abstract run method
  
    @abstractmethod
    def run(self, input_data: str, task_id: Optional[str] = None) -> str:
        """
        Must be implemented by all agents.
        """
        raise NotImplementedError

    # Structured Logging Helper

    def log_action(
        self,
        message: str,
        task_id: Optional[str] = None,
        level: str = "info",
        extra: Optional[dict] = None,
    ) -> None:
        """
        Logs structured JSON entry.

        Includes:
        - agent name
        - task_id
        - custom message
        """

        log_payload = {
            "service": "agent",
            "agent_name": self.agent_name,
            "task_id": task_id,
            "action_details": message,
        }

        if extra:
            log_payload.update(extra)

        if level.lower() == "error":
            self.logger.error(message, extra=log_payload)
        else:
            self.logger.info(message, extra=log_payload)

    # DB Status Update Hook (stub-safe)
  
    def update_status(self, task_id: Optional[str], status: str) -> None:
        """
        Updates task status in DB.

        Currently stub-safe:
        Will be connected to TaskService in Phase 7.
        """

        if not task_id:
            return

        try:
            # Lazy import to avoid circular dependency
            from src.services.task_service import task_service  # noqa

            task_service.update_status(task_id=task_id, status=status)

        except ImportError:
            # TaskService not yet implemented → safe no-op
            self.log_action(
                f"TaskService not available. Skipping DB status update → {status}",
                task_id=task_id,
            )

        except Exception as e:
            self.log_action(
                "Failed to update task status",
                task_id=task_id,
                level="error",
                extra={"error": str(e)},
            )

    # WebSocket Push Hook (stub-safe)
    
    def push_ws_update(self, task_id: Optional[str], status: str) -> None:
        """
        Sends real-time status update.

        Currently stub-safe:
        Will be connected to WebSocketManager later.
        """

        if not task_id:
            return

        try:
            # Lazy import to avoid circular dependency
            from src.services.websocket_manager import websocket_manager  # noqa

            websocket_manager.push_update(task_id=task_id, status=status)

        except ImportError:
            # WebSocketManager not yet implemented → safe no-op
            self.log_action(
                f"WebSocketManager not available. Skipping WS update → {status}",
                task_id=task_id,
            )

        except Exception as e:
            self.log_action(
                "Failed to push WebSocket update",
                task_id=task_id,
                level="error",
                extra={"error": str(e)},
            )
