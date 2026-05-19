import asyncio
import sys
import json

sys.path.append('e:/ai_company_faz12.1')

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import Project, SubTask, TaskLog
from sqlalchemy import select

async def main():
    target_id = "4cb93bf0-8388-4b76-b1e2-e27b4510d847"
    output_lines = []
    
    async with AsyncSessionLocal() as db:
        # 1. Fetch project to verify it
        res = await db.execute(select(Project).where(Project.id == target_id))
        proj = res.scalar_one_or_none()
        if not proj:
            output_lines.append(f"Project {target_id} not found.")
            return

        output_lines.append(f"=== PROJECT: {proj.title} ===")
        output_lines.append(f"Status: {proj.status}")
        output_lines.append(f"Error Detail: {proj.error_detail}")
        
        # 2. Fetch subtasks
        subtasks_res = await db.execute(
            select(SubTask)
            .where(SubTask.project_id == target_id)
            .order_by(SubTask.created_at.asc())
        )
        subtasks = subtasks_res.scalars().all()
        output_lines.append("\n=== SUBTASKS ===")
        for sub in subtasks:
            output_lines.append(f"- ID: {sub.id}")
            output_lines.append(f"  Agent ID: {sub.agent_id}")
            output_lines.append(f"  Status: {sub.status}")
            output_lines.append(f"  Quality Score: {sub.quality_score}")
            output_lines.append(f"  Causal Anchor: {sub.causal_anchor}")
            result_snippet = (sub.result or "")[:500]
            output_lines.append(f"  Result snippet: {result_snippet}")
            output_lines.append("-" * 40)

        # 3. Fetch TaskLogs
        logs_res = await db.execute(
            select(TaskLog)
            .where(TaskLog.project_id == target_id)
            .order_by(TaskLog.created_at.asc())
        )
        logs = logs_res.scalars().all()
        output_lines.append("\n=== TASK LOGS ===")
        for log in logs:
            output_lines.append(f"[{log.created_at}] {log.level.upper()} - {log.event}: {log.message}")
            if log.payload:
                output_lines.append(f"  Payload: {json.dumps(log.payload, ensure_ascii=False)}")

    with open('scratch/workflow_logs_output.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    print("Successfully wrote output to scratch/workflow_logs_output.txt")

if __name__ == "__main__":
    asyncio.run(main())
