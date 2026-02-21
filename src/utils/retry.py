from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable, TypeVar

from src.services.logger import get_logger

logger = get_logger("retry_util")

F = TypeVar("F", bound=Callable[..., Any])


def retry(max_attempts: int = 2, delay: float = 0.0) -> Callable[[F], F]:
    """
    Reusable retry decorator with structured JSON logging.

    Logs:
    - Failure with status=tool_error
    - Retry attempts
    - Success after retry
    - Max retry exhaustion

    Celery-safe: final exception is re-raised.
    """

    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            task_id = kwargs.get("task_id")
            last_exception: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)


                    # Success after retry logging
                    if attempt > 1:
                        logger.info(
                            "Tool succeeded after retry",
                            extra={
                                "service": "retry_util",
                                "agent_name": "ResearchAgent",
                                "task_id": task_id,
                                "action_details": f"{func.__name__} succeeded on attempt {attempt}",
                            },
                        )

                    return result

                except Exception as e:
                    last_exception = e

                    # Log failure

                    logger.error(
                        "Tool execution failed",
                        extra={
                            "service": "retry_util",
                            "agent_name": "ResearchAgent",
                            "task_id": task_id,
                            "action_details": f"{func.__name__} failed on attempt {attempt}",
                            "status": "tool_error",
                            "error": str(e),
                        },
                    )

                    # Retry if attempts remain

                    if attempt < max_attempts:
                        logger.info(
                            "Retrying tool",
                            extra={
                                "service": "retry_util",
                                "agent_name": "ResearchAgent",
                                "task_id": task_id,
                                "action_details": f"Retrying {func.__name__} (attempt {attempt + 1})",
                            },
                        )

                        if delay > 0:
                            time.sleep(delay)

                    else:
                        # Max attempts reached
                        logger.error(
                            "Max retry attempts reached",
                            extra={
                                "service": "retry_util",
                                "agent_name": "ResearchAgent",
                                "task_id": task_id,
                                "action_details": f"{func.__name__} failed after {max_attempts} attempts",
                                "status": "tool_error",
                            },
                        )

                        raise last_exception

            # Safety fallback
            raise last_exception  # type: ignore

        return wrapper  # type: ignore

    return decorator
