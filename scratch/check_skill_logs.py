import asyncio
import sys
import json

sys.path.append('e:/ai_company_faz12.1')

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import SkillExecutionLog
from sqlalchemy import select

async def main():
    target_id = "4cb93bf0-8388-4b76-b1e2-e27b4510d847"
    output_lines = []
    
    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(SkillExecutionLog)
            .where(SkillExecutionLog.project_id == target_id)
            .order_by(SkillExecutionLog.created_at.asc())
        )
        logs = res.scalars().all()
        output_lines.append(f"=== SKILL EXECUTION LOGS ({len(logs)} found) ===")
        for log in logs:
            output_lines.append(f"[{log.created_at}] Agent: {log.agent_id}, Skill: {log.skill_id}, Success: {log.success}")
            output_lines.append(f"  Summary: {log.summary}")
            if log.data:
                output_lines.append(f"  Data: {json.dumps(log.data, ensure_ascii=False)}")
            output_lines.append("-" * 40)

    with open('scratch/skill_logs_output.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    print("Successfully wrote output to scratch/skill_logs_output.txt")

if __name__ == "__main__":
    asyncio.run(main())
