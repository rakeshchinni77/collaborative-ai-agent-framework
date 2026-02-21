from __future__ import annotations

from typing import Dict

from src.services.logger import get_logger
from src.utils.retry import retry

logger = get_logger("flaky_tool")

# In-memory attempt tracker (deterministic across calls)
_flaky_attempt_counter: Dict[str, int] = {}


@retry(max_attempts=2, delay=0)
def flaky_search_tool(query: str, task_id: str | None = None) -> str:
    """
    Deterministic flaky tool with structured logging.

    Logs:
    - Tool start
    - Tool failure (attempt 1)
    - Retry attempt (from retry_util)
    - Tool success
    """

    if not query:
        raise ValueError("flaky_search_tool received empty query")

    attempt = _flaky_attempt_counter.get(query, 0) + 1
    _flaky_attempt_counter[query] = attempt

    # Tool start log
    logger.info(
        "Flaky tool started",
        extra={
            "service": "flaky_tool",
            "agent_name": "ResearchAgent",
            "task_id": task_id,
            "action_details": f"Tool started | query={query} | attempt={attempt}",
        },
    )

    # Deterministic failure on first attempt
    if query == "__FLAKY_TEST__" and attempt == 1:
        logger.error(
            "Flaky tool simulated failure",
            extra={
                "service": "flaky_tool",
                "agent_name": "ResearchAgent",
                "task_id": task_id,
                "action_details": "Tool failed on attempt 1 (simulated)",
                "status": "tool_error",
            },
        )
        raise RuntimeError("Simulated flaky tool failure (attempt 1)")

    # Success path
    result = (
        "Flaky tool search results:\n"
        "- LangGraph: graph-based orchestration, stateful execution\n"
        "- CrewAI: role-based autonomous agents, task delegation\n"
    )

    logger.info(
        "Flaky tool completed successfully",
        extra={
            "service": "flaky_tool",
            "agent_name": "ResearchAgent",
            "task_id": task_id,
            "action_details": f"Tool succeeded on attempt {attempt}",
        },
    )

    return result
