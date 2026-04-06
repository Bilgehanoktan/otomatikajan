import time
import logging
from packages.persistence.session import AsyncSessionLocal as get_db_session
from packages.persistence.models import SkillExecutionLog
from packages.skills.base import SkillRequest, SkillResult

_log = logging.getLogger("skill_logger")

async def log_skill_execution(req: SkillRequest, res: SkillResult, duration: float):
    """
    Beceri yürütme sonucunu veritabanına kalıcı olarak kaydeder.
    """
    try:
        async with get_db_session() as db:
            log_entry = SkillExecutionLog(
                project_id=req.project_id,
                agent_id=req.agent_id,
                skill_id=res.skill_id,
                success=res.success,
                summary=res.summary,
                data=res.data,
                duration_s=duration
            )
            db.add(log_entry)
            await db.commit()
    except Exception as e:
        _log.error(f"❌ Beceri logu kaydedilemedi ({res.skill_id}): {e}")
