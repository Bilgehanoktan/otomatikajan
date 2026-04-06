import asyncio
import json
from pathlib import Path

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from packages.skills.base import SkillRequest
from packages.skills.registry import skill_registry
from packages.skills.router import skill_router

async def main():
    print("--- Skills Registry Test ---")
    skills = skill_registry.ids()
    print(f"Registered Skills: {skills}")
    
    print("\n--- Skill Suggestion Test (Bug Task) ---")
    req = SkillRequest(
        task_type="test",
        title="Database Connection Error",
        description="Getting Traceback Error: ConnectionRefusedError at localhost:5432",
        context={"env": "dev"}
    )
    suggestions = skill_router.suggest(req)
    print(f"Suggestions for 'bug' task: {suggestions}")
    
    print("\n--- Optimization Skill Execution Test ---")
    opt_skill = skill_registry.get("optimization")
    if opt_skill:
        res = await opt_skill.execute(req)
        print(f"Optimization Success: {res.success}")
        print(f"Summary: {res.summary}")
        print(f"Data Sample: {list(res.data.keys())}")
        
    print("\n--- File Search Skill Execution Test ---")
    fs_skill = skill_registry.get("file_search")
    if fs_skill:
        res = await fs_skill.execute(req)
        print(f"File Search Success: {res.success}")
        print(f"Summary: {res.summary}")
        # print(f"Hits: {res.data.get('hits', [])[:2]}")

if __name__ == "__main__":
    asyncio.run(main())
