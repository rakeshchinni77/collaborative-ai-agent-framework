from __future__ import annotations

from typing import Optional

from src.agents.base_agent import BaseAgent


class WritingAgent(BaseAgent):
    """
    Agent responsible for converting research notes
    into a technical comparison summary.

    Responsibilities:
    - Accept research text
    - Generate structured comparison output
    - Log structured actions
    """

    def __init__(self) -> None:
        super().__init__(agent_name="WritingAgent")

    def run(self, research_text: str, task_id: Optional[str] = None) -> str:
        """
        Executes writing step.

        Args:
            research_text: Output from ResearchAgent
            task_id: Task identifier for logging

        Returns:
            Technical comparison summary
        """

        if not research_text:
            raise ValueError("WritingAgent received empty research_text")

        self.log_action(
            "Writing started",
            task_id=task_id,
        )

        self.update_status(task_id, "RUNNING")
        self.push_ws_update(task_id, "RUNNING")

        try:
            # Lazy import → LLM optional for now
            from src.utils.llm_client import llm_client  # noqa

            writing_prompt = (
                "You are a technical writer.\n"
                "Using the following research notes, produce a concise "
                "technical comparison summary with:\n"
                "- Overview\n"
                "- Key differences\n"
                "- When to use each\n\n"
                f"{research_text}"
            )

            writing_output = llm_client.generate(writing_prompt)

            if not writing_output:
                raise ValueError("LLM returned empty writing output")

            self.log_action(
                "Writing completed",
                task_id=task_id,
            )

            return writing_output

        except ImportError:
            # Safe fallback for testing without LLM
            fallback_output = (
                "Technical Comparison Summary\n\n"
                "Overview:\n"
                "LangGraph enables stateful graph-based orchestration for "
                "multi-agent workflows, while CrewAI focuses on role-based "
                "autonomous agents with task delegation.\n\n"
                "Key Differences:\n"
                "- LangGraph: Graph execution, state management, deterministic flows\n"
                "- CrewAI: Role-based agents, collaboration, autonomy\n\n"
                "When to Use:\n"
                "- Use LangGraph for structured pipelines and control\n"
                "- Use CrewAI for autonomous multi-agent collaboration\n"
            )

            self.log_action(
                "LLM client not available, using fallback writing output",
                task_id=task_id,
            )

            return fallback_output

        except Exception as e:
            self.log_action(
                "Writing failed",
                task_id=task_id,
                level="error",
                extra={"error": str(e)},
            )
            raise
