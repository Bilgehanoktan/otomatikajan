import asyncio
import sys

sys.path.append('e:/ai_company_faz12.1')

from services.orchestration.application.velocity_engine import velocity_engine

async def main():
    print("Testing Velocity Engine fix...")
    # Mock some arguments
    agent_id = "architect"
    prompt = "Create a basic system design outline for a microservice."
    context = {"requirements": prompt, "shared_context": ""}
    task_id = "00000000-0000-0000-0000-000000000000"
    
    # We will simulate and execute
    try:
        result = await velocity_engine.simulate_and_execute(
            agent_id=agent_id,
            prompt=prompt,
            context=context,
            task_id=task_id
        )
        print(f"Success: {result.success}")
        print(f"Output: {result.output_data}")
        print(f"Errors: {result.errors}")
    except Exception as e:
        print(f"Failed with exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
