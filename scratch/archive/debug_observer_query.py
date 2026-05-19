
import asyncio
import sys
from sqlalchemy import select, cast, String

# Workspace root
sys.path.append("e:/ai_company_faz12.1")

from libs.db.session import AsyncSessionLocal
from libs.db.models.core_models import WorkflowEvent, SubTask

async def debug_join():
    async with AsyncSessionLocal() as session:
        # WorkflowEvent'leri al
        events = await session.execute(select(WorkflowEvent).where(WorkflowEvent.event_type == "step_failed"))
        all_ev = events.scalars().all()
        
        for ev in all_ev:
            print(f"Event step_id: '{ev.step_id}' (Type: {type(ev.step_id)})")
            
            # SubTask ile eÅŸleÅŸtir
            st_id = ev.step_id
            st_res = await session.execute(select(SubTask).where(cast(SubTask.id, String) == st_id))
            st = st_res.scalar_one_or_none()
            if st:
                print(f"  MATCH FOUND! SubTask ID: {st.id}, InputData: {st.input_data}")
            else:
                # Alternatif deneme (case insensitive veya baÅŸka bir ÅŸey)
                print(f"  NO MATCH with direct cast.")
                # TÃ¼m SubTask'larÄ± dÃ¶k ve cast hallerini bas
                all_st_res = await session.execute(select(SubTask))
                for s in all_st_res.scalars().all():
                    print(f"    Possible SubTask: '{str(s.id)}' vs '{st_id}'")

if __name__ == "__main__":
    asyncio.run(debug_join())
