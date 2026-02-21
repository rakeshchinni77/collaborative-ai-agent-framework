from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

LOG_FILE_PATH = Path("/app/logs/agent_activity.log")

MAX_LOG_VALUE_LENGTH = 500  #performance safety limit


class JSONFormatter(logging.Formatter):
    """
    Strict JSON formatter for multi-service observability.

    Required fields in every log:
    - timestamp (auto)
    - level
    - service
    - task_id
    - stage
    - action_details
    - message
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "service": getattr(record, "service", record.name),
            "task_id": getattr(record, "task_id", None),
            "stage": getattr(record, "stage", None),
            "action_details": getattr(record, "action_details", None),
        }

        # Include any additional extra fields safely with truncation guard
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
            ):
                if key not in log_record:
                    if isinstance(value, str) and len(value) > MAX_LOG_VALUE_LENGTH:
                        log_record[key] = (
                            value[:MAX_LOG_VALUE_LENGTH] + "...[truncated]"
                        )
                    else:
                        log_record[key] = value

        return json.dumps(log_record, default=str)


def _ensure_log_directory() -> None:
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE_PATH.exists():
        LOG_FILE_PATH.touch()


def get_logger(service_name: str) -> logging.Logger:
    """
    Returns a structured JSON logger.

    ✔ Rotating file handler (5MB x 3 backups)
    ✔ Docker volume safe (/app/logs)
    ✔ No duplicate handlers
    ✔ Contract-safe JSON schema
    """

    _ensure_log_directory()

    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers on reload
    if logger.handlers:
        return logger

    file_handler = RotatingFileHandler(
        LOG_FILE_PATH,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
    )

    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger