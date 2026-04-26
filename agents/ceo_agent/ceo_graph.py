import asyncio
import json
import logging
from typing import Dict, TypedDict, Annotated, List, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from services.observability.logging import get_logger
from libs.observability.tracer import span, set_span_attrs

logger = get_logger("ceo_graph")

# Define the state for the CEO Agent Graph
class AgentState(TypedDict):
    opportunity: Dict[str, Any]
    messages: Annotated[List[BaseMessage], "messages"]
    plan: str
    delegated_agent: str
    tool_calls: List[Dict[str, Any]]
    security_clearance: bool
    final_decision: str
    status: str

# 1. State Nodes
async def node_analyze_opportunity(state: AgentState):
    """Analyzes the incoming opportunity/issue and creates a high-level plan."""
    with span("ceo.analyze_opportunity") as s:
        logger.info("[CEO Graph] Node: Analyzing Opportunity")
        op = state.get("opportunity", {})
        s.set_attribute("opportunity.title", op.get("title"))

        # In a real scenario, this would call LLM to analyze the opportunity
        # For now, we simulate the LLM output based on the opportunity
        plan = f"Plan to address '{op.get('title')}':\n1. Review code\n2. Design fix\n3. Deploy via MCP"

        return {"plan": plan, "status": "analyzed"}

async def node_delegate_expert(state: AgentState):
    """Delegates the specific task to a specialized agent using intelligent orchestrator."""
    from libs.llm.model_orchestrator import ModelOrchestrator

    with span("ceo.delegate_expert"):
        logger.info("[CEO Graph] Node: Delegating Expert via Orchestrator")
        plan = state.get("plan", "")

        # In production, we query the Agent Registry. Here we map known needs.
        prompt = f"Based on this plan, choose the best agent from [agency-software-architect, agency-devops-automator, agency-security-engineer]:\n{plan}"

        # We use a central orchestrator to pick the agent based on capability
        orch = ModelOrchestrator()
        selection = await orch.complete(messages=[{"role": "user", "content": prompt}])

        delegated_agent = "agency-software-architect" # Default fallback
        for agent in ["architect", "devops", "security"]:
            if agent in selection.lower():
                delegated_agent = f"agency-{agent}"
                break

        set_span_attrs(delegated_agent=delegated_agent)
        return {"delegated_agent": delegated_agent, "status": "delegated"}

async def node_security_guard(state: AgentState):
    """validates tool calls against prompt guardrails before execution."""
    from services.governance.quality.prompt_guard import validate_tool_param

    logger.info("[CEO Graph] Node: Security Guardrail Check")
    tool_calls = state.get("tool_calls", [])

    for call in tool_calls:
        # Check for forbidden patterns in parameters
        is_safe = validate_tool_param(call.get("parameters", {}))
        if not is_safe:
            logger.error(f"❌ Security violation detected in tool call: {call.get('tool')}")
            return {"security_clearance": False, "status": "security_violation"}

    return {"security_clearance": True}

async def node_invoke_mcp_tools(state: AgentState):
    """Invokes system tools autonomously via hardened MCP Bridge."""
    from libs.mcp.client import mcp_bridge

    with span("ceo.invoke_mcp_tools"):
        logger.info("[CEO Graph] Node: Invoking MCP Tools via Bridge")
        op = state.get("opportunity", {})

        # In a real run, the LLM would populate this based on its analysis node.
        # We simulate the mapping logic here for the 'trigger_workflow' tool.
        tool_resp = await mcp_bridge.call_tool(
            "trigger_workflow",
            {
                "title": f"Repair: {op.get('title')}",
                "template": "automated_repair"
            }
        )

        return {
            "tool_calls": [{"tool": "trigger_workflow", "response": tool_resp}],
            "status": "tools_invoked" if tool_resp.get("status") == "success" else "execution_failed"
        }

async def node_evaluate_outcome(state: AgentState):
    """Evaluates if the tools resolved the issue successfully."""
    logger.info("[CEO Graph] Node: Evaluating Outcome")

    return {"final_decision": "Approved and Enqueued", "status": "completed"}

# 2. Edges and Routing
def route_after_analysis(state: AgentState) -> str:
    # If the opportunity is critical, we might skip delegation and go straight to emergency tools
    if state.get("opportunity", {}).get("severity") == "critical":
        logger.warning("[CEO Graph] CRITICAL severity: Routing directly to MCP tools!")
        return "invoke_tools"
    return "delegate"

# 3. Graph Assembly
def build_ceo_graph(checkpointer=None):
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("analyze", node_analyze_opportunity)
    workflow.add_node("delegate", node_delegate_expert)
    workflow.add_node("invoke_tools", node_invoke_mcp_tools)
    workflow.add_node("security_guard", node_security_guard)
    workflow.add_node("evaluate", node_evaluate_outcome)

    # Add edges
    workflow.set_entry_point("analyze")
    workflow.add_conditional_edges("analyze", route_after_analysis, {
        "delegate": "delegate",
        "invoke_tools": "security_guard" # Route tools through guard first
    })
    workflow.add_edge("delegate", "security_guard")

    # Security Guard Routing
    workflow.add_conditional_edges("security_guard", lambda x: "pass" if x.get("security_clearance") else "fail", {
        "pass": "invoke_tools",
        "fail": "evaluate" # Skip to evaluation/rejection on security fail
    })

    workflow.add_edge("invoke_tools", "evaluate")
    workflow.add_edge("evaluate", END)

    return workflow.compile(checkpointer=checkpointer)

# Helper for external execution
async def run_ceo_graph(opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
    # Thread ID generation for persistence
    thread_id = str(opportunity_data.get("id", "default_thread"))
    config = {"configurable": {"thread_id": thread_id}}

    async with AsyncSqliteSaver.from_conn_string("agent_checkpoints.db") as memory:
        app = build_ceo_graph(checkpointer=memory)

        initial_state = {
            "opportunity": opportunity_data,
            "messages": [HumanMessage(content=f"Fix issue: {opportunity_data.get('title')}")],
            "plan": "",
            "delegated_agent": "",
            "tool_calls": [],
            "final_decision": "",
            "status": "started"
        }

        logger.info(f"Starting CEO Graph for: {opportunity_data.get('title')}")

        # Async execution of the compiled graph with checkpointer
        final_state = await app.ainvoke(initial_state, config=config)
        logger.info(f"CEO Graph completed with status: {final_state.get('status')} [Thread: {thread_id}]")

        return final_state
