import asyncio
import sys
import os

# Add relevant paths
sys.path.append(os.getcwd())

async def verify_mcp():
    print("--- MCP Registry Verification ---")
    try:
        # Import registry and tools (this triggers registration via decorators)
        from libs.mcp.registry import mcp_registry
        import libs.mcp.tools
        from services.orchestration.agi.operational.tool_executor import tool_executor
        
        tools = mcp_registry.get_all_metadata()
        print(f"Total Standardized Tools: {len(tools)}")
        print("-" * 30)
        for t in tools:
            print(f"Tool: {t.name}")
            print(f"  Desc: {t.description}")
            print(f"  Params: {list(t.parameters.keys())}")
            print("-" * 30)
            
        # Verify ToolExecutor routing
        print("\nVerifying ToolExecutor Routing...")
        from services.governance.quality.output_schema import ToolCall
        
        # Test read_file tool via executor
        test_file = "test_mcp_verify.txt"
        with open(test_file, "w") as f: f.write("Neural Content Verified")
        
        call = ToolCall(tool_name="read_file", tool_input={"path": test_file})
        # Mock context with workflow_id
        results = await tool_executor.execute_calls("test_task", "test_agent", [call], {"workflow_id": "test_wf_123"})
        
        print(f"Execution Result: {results[0]['status']}")
        if results[0]['status'] == "success":
            print("SUCCESS: ToolExecutor successfully routed call through MCP Registry.")
        else:
            print(f"FAILURE: {results[0].get('error')}")
            
        os.remove(test_file)
        
    except Exception as e:
        print(f"ERROR during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_mcp())
