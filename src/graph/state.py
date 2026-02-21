from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AgentLogEntry(BaseModel):
    agent: str
    action: str
    timestamp: str


class WorkflowState(BaseModel):
    """
    Shared LangGraph state across all nodes.

    Must be:
    - Mutable
    - Serializable
    - Redis/DB safe
    """

    task_id: str
    prompt: str

    research_data: Optional[str] = None
    draft: Optional[str] = None
    final_result: Optional[str] = None

    status: str = "PENDING"
    approved: bool = False

    agent_logs: List[AgentLogEntry] = Field(default_factory=list)

    # Agent Log Appender Utility

    def append_log(self, agent: str, action: str) -> None:
        """
        Appends a structured agent log entry.

        Format:
        {
          "agent": "...",
          "action": "...",
          "timestamp": "ISO8601"
        }
        """

        entry = AgentLogEntry(
            agent=agent,
            action=action,
            timestamp=datetime.utcnow().isoformat(),
        )

        self.agent_logs.append(entry)

    # JSON-safe export for DB
  
    def export_logs(self) -> List[dict]:
        """
        Converts AgentLogEntry objects into JSON-serializable dicts
        for PostgreSQL JSONB storage.
        """
        return [log.model_dump() for log in self.agent_logs]
