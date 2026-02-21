from src.graph.state import WorkflowState
from src.agents.research_agent import ResearchAgent
from src.services.redis_service import redis_service
from src.services.redis_service import RedisKeyBuilder
from src.services.logger import get_logger


logger = get_logger("workflow_graph")

research_agent = ResearchAgent()


# Research Node
def research_node(state: WorkflowState) -> WorkflowState:
    """
    Executes research step:
    - Calls ResearchAgent with task_id
    - Updates state.research_data
    - Writes research output to Redis scratchpad
    - Appends agent log entry to state
    - Retry-aware (raises on failure)
    """

    try:
        state.status = "RUNNING"

        # Call ResearchAgent (BaseAgent integrated)
      
        research_output = research_agent.run(
            input_data=state.prompt,
            task_id=state.task_id,
        )

        if not research_output:
            raise ValueError("ResearchAgent returned empty output")

        # Update LangGraph state
      
        state.research_data = research_output

        # Write to Redis scratchpad
        # Required key pattern: task:<task_id>:workspace
        workspace_payload = {
            "research_data": research_output,
        }

        redis_success = redis_service.set_workspace(
            task_id=state.task_id,
            data=workspace_payload,
        )

        if not redis_success:
            logger.error(
                "Failed to write research data to Redis",
                extra={
                    "service": "workflow_graph",
                    "node": "research_node",
                    "task_id": state.task_id,
                },
            )

        # Append structured state log
        # (This is separate from BaseAgent logs)
        state.append_log(
            "ResearchAgent",
            "Generated research data and stored in Redis scratchpad",
        )

        return state

    except Exception as e:
        # Structured infra error log
  
        logger.error(
            "Research node failed",
            extra={
                "service": "workflow_graph",
                "node": "research_node",
                "task_id": state.task_id,
                "error": str(e),
            },
        )

        # Append failure to state logs for DB JSONB later
        state.append_log(
            "ResearchAgent",
            f"Research failed: {str(e)}",
        )

        # Raise for Celery retry (Core Requirement 12)
        raise
#Writing Node
from src.agents.writing_agent import WritingAgent

writing_agent = WritingAgent()


# Writing Node
def writing_node(state: WorkflowState) -> WorkflowState:
    """
    Executes writing step:
    - Reads research data from Redis scratchpad
    - Calls WritingAgent with task_id
    - Updates state.draft
    - Appends agent log entry
    - Retry-aware (raises on failure for Celery)
    """

    try:
        state.status = "RUNNING"

        # Read research data from Redis scratchpad
        # Required key pattern: task:<task_id>:workspace
        
        workspace = redis_service.get_workspace(task_id=state.task_id)

        if not workspace or "research_data" not in workspace:
            raise ValueError("No research data found in Redis workspace")

        research_data = workspace.get("research_data")

        if not research_data:
            raise ValueError("Research data is empty")

      
        # Call WritingAgent (BaseAgent integrated)
       
        draft_output = writing_agent.run(
            research_text=research_data,
            task_id=state.task_id,
        )

        if not draft_output:
            raise ValueError("WritingAgent returned empty draft")

        # Update LangGraph state
        
        state.draft = draft_output

        # Append structured state log
        # (separate from BaseAgent logs)
        
        state.append_log(
            "WritingAgent",
            "Generated draft summary from Redis research data",
        )

        return state

    except Exception as e:
        
        # Structured infra error log
        
        logger.error(
            "Writing node failed",
            extra={
                "service": "workflow_graph",
                "node": "writing_node",
                "task_id": state.task_id,
                "error": str(e),
            },
        )

        # Append failure to state logs for DB JSONB later
        state.append_log(
            "WritingAgent",
            f"Writing failed: {str(e)}",
        )

        # Raise for Celery retry (Core Requirement 12)
        raise
      
# Approval Gate Node

def approval_gate_node(state: WorkflowState) -> WorkflowState:
    """
    Human-in-the-loop approval gate.

    Behavior:
    - Sets task status to AWAITING_APPROVAL
    - Appends agent log
    - Halts graph execution until externally resumed
    """

    try:
        state.status = "AWAITING_APPROVAL"

        state.append_log(
            "System",
            "Workflow paused awaiting human approval",
        )

        return state

    except Exception as e:
        logger.error(
            "Approval gate node failed",
            extra={
                "service": "workflow_graph",
                "node": "approval_gate_node",
                "task_id": state.task_id,
                "error": str(e),
            },
        )
        return state

# Approval Router (Conditional Edge)

def approval_router(state: WorkflowState) -> str:
    """
    Determines next step after approval gate.

    Returns:
    - "finalize" if approved
    - "await" if still waiting
    """

    try:
        if getattr(state, "approved", False):
            return "finalize"

        return "await"

    except Exception as e:
        logger.error(
            "Approval routing failed",
            extra={
                "service": "workflow_graph",
                "node": "approval_router",
                "task_id": state.task_id,
                "error": str(e),
            },
        )
        return "await"
      
# Finalization Node

def finalization_node(state: WorkflowState) -> WorkflowState:
    """
    Final step of workflow.

    Behavior:
    - Moves draft to final_result
    - Updates status to COMPLETED
    - Deletes Redis scratchpad
    - Appends agent log
    """

    try:
        # Move draft to final result
        if state.draft:
            state.final_result = state.draft

        # Update status
        state.status = "COMPLETED"

        # Delete Redis scratchpad
        delete_success = redis_service.delete_workspace(task_id=state.task_id)

        if not delete_success:
            logger.error(
                "Failed to delete Redis workspace during finalization",
                extra={
                    "service": "workflow_graph",
                    "node": "finalization_node",
                    "task_id": state.task_id,
                },
            )

        # Append agent log
        state.append_log(
            "System",
            "Workflow finalized and Redis scratchpad cleaned",
        )

        return state

    except Exception as e:
        logger.error(
            "Finalization node failed",
            extra={
                "service": "workflow_graph",
                "node": "finalization_node",
                "task_id": state.task_id,
                "error": str(e),
            },
        )
        return state
from langgraph.graph import StateGraph, END

# Build Workflow Graph

def build_workflow_graph():
    """
    Constructs the LangGraph workflow with:
    research → writing → approval → conditional → final
    """

    workflow = StateGraph(WorkflowState)

    
    # Register Nodes
    
    workflow.add_node("research", research_node)
    workflow.add_node("writing", writing_node)
    workflow.add_node("approval", approval_gate_node)
    workflow.add_node("finalize", finalization_node)

  
    # Linear Edges
  
    workflow.set_entry_point("research")

    workflow.add_edge("research", "writing")
    workflow.add_edge("writing", "approval")

    # Conditional Edge from Approval
  
    workflow.add_conditional_edges(
    "approval",
    approval_router,
    {
        "finalize": "finalize",
        "await": END,  # pause workflow here
    },
  )

    # Final Edge
    workflow.add_edge("finalize", END)

    return workflow.compile()

# Singleton Compiled Graph

_workflow_graph = None


def get_workflow_graph():
    """
    Returns a singleton compiled LangGraph instance.
    Prevents recompilation on every task execution.
    """

    global _workflow_graph

    if _workflow_graph is None:
        _workflow_graph = build_workflow_graph()

        logger.info(
            "LangGraph workflow compiled",
            extra={"service": "workflow_graph"},
        )

    return _workflow_graph
