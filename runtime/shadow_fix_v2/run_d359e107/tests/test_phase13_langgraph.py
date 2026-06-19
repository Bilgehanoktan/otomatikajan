import asyncio
import logging

from services.observability.logging import get_logger
from agents.ceo_agent.ceo_graph import run_ceo_graph

logger = get_logger("test_langgraph")

async def test_normal_flow():
    logger.info("=== TEST 1: Normal Flow ===")
    opportunity = {
        "title": "Refactor User Model",
        "description": "User model has legacy fields causing database bloat.",
        "severity": "medium",
        "source_type": "technical_debt"
    }
    
    result = await run_ceo_graph(opportunity)
    logger.info(f"Final State Status: {result['status']}")
    logger.info(f"Delegated Agent: {result.get('delegated_agent')}")
    logger.info(f"Tool Calls: {result.get('tool_calls')}")
    logger.info("===========================\n")

async def test_critical_flow():
    logger.info("=== TEST 2: Critical Fast-Track Flow ===")
    opportunity = {
        "title": "Database Connection Pool Exhausted",
        "description": "Services are dropping due to exhausted connections.",
        "severity": "critical",
        "source_type": "incident"
    }
    
    result = await run_ceo_graph(opportunity)
    logger.info(f"Final State Status: {result['status']}")
    logger.info(f"Delegated Agent (Should be empty): {result.get('delegated_agent')}")
    logger.info(f"Tool Calls: {result.get('tool_calls')}")
    logger.info("===========================\n")

if __name__ == "__main__":
    asyncio.run(test_normal_flow())
    asyncio.run(test_critical_flow())
