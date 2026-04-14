import asyncio
import json
import logging
from typing import Dict, TypedDict, Annotated, List, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
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
    """Delegates the specific task to a specialized agent (e.g. using CrewAI integration)."""
    with span("ceo.delegate_expert"):
        logger.info("[CEO Graph] Node: Delegating Expert")
        plan = state.get("plan", "")
        
        # Simulate LLM choosing an agent based on the plan
        delegated_agent = "agency-software-architect" if "code" in plan.lower() else "agency-devops-automator"
        set_span_attrs(delegated_agent=delegated_agent)
        
        return {"delegated_agent": delegated_agent, "status": "delegated"}

async def node_invoke_mcp_tools(state: AgentState):
    """Invokes system tools autonomously via MCP to resolve the issue."""
    with span("ceo.invoke_mcp_tools"):
        logger.info("[CEO Graph] Node: Invoking MCP Tools")
        
        # Here we would normally take the LLM's requested tool calls and execute them against the MCP Server
        # We will simulate triggering a 'start_workflow' tool
        simulated_tool_call = {
            "tool": "start_workflow",
            "parameters": {
                "workflow_type": "automated_repair",
                "target": state.get("opportunity", {}).get("source_ref", "unknown")
            }
        }
        
        return {"tool_calls": [simulated_tool_call], "status": "tools_invoked"}

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
def build_ceo_graph() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze", node_analyze_opportunity)
    workflow.add_node("delegate", node_delegate_expert)
    workflow.add_node("invoke_tools", node_invoke_mcp_tools)
    workflow.add_node("evaluate", node_evaluate_outcome)
    
    # Add edges
    workflow.set_entry_point("analyze")
    workflow.add_conditional_edges("analyze", route_after_analysis, {
        "delegate": "delegate",
        "invoke_tools": "invoke_tools"
    })
    workflow.add_edge("delegate", "invoke_tools")
    workflow.add_edge("invoke_tools", "evaluate")
    workflow.add_edge("evaluate", END)
    
    # Durable Checkpointer (Faz 13.04)
    # Gerçek senaryoda bu PostgresSaver olabilir, şimdilik SQLite üzerinden persistence sağlıyoruz.
    import sqlite3
    conn = sqlite3.connect("agent_checkpoints.db", check_same_thread=False)
    memory = SqliteSaver(conn)
    
    app = workflow.compile(checkpointer=memory)
    return app

# Helper for external execution
async def run_ceo_graph(opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
    app = build_ceo_graph()
    
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
    
    # Thread ID generation for persistence
    # Opportunity ID veya Title tabanlı bir thread_id kullanarak geçmişi takip edebiliriz.
    thread_id = str(opportunity_data.get("id", "default_thread"))
    config = {"configurable": {"thread_id": thread_id}}
    
    # Async execution of the compiled graph with checkpointer
    final_state = await app.ainvoke(initial_state, config=config)
    logger.info(f"CEO Graph completed with status: {final_state.get('status')} [Thread: {thread_id}]")
    
    return final_state
