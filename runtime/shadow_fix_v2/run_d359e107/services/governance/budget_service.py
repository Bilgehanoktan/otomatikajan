"""
services/governance/budget_service.py — Phase 30
LLM bütçe denetimi ve finansal yönetişim servisi.
"""
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import select, func
from libs.db.session import get_db, get_db_ctx
from libs.db.models.core_models import LLMCostLog, Project, SovereignEvidence
from services.observability.logging import get_logger

logger = get_logger("governance.budget")

class BudgetService:
    _cache: Dict[str, Any] = {}
    CACHE_TTL = 60  # 60 saniye önbellek

    @classmethod
    async def get_total_consumption(cls, project_id: Optional[str] = None) -> float:
        """
        DB'den gerçek zamanlı maliyet toplamını döner (Önbellekli).
        """
        now = time.time()
        cache_key = f"cost_{project_id or 'global'}"
        
        if cache_key in cls._cache:
            entry = cls._cache[cache_key]
            if now - entry['timestamp'] < cls.CACHE_TTL:
                return entry['total']

        # Cache miss or expired
        total = await cls._fetch_from_db(project_id)
        cls._cache[cache_key] = {'total': total, 'timestamp': now}
        return total

    @staticmethod
    async def _fetch_from_db(project_id: Optional[str] = None) -> float:
        """Sorguyu llm_cost_logs tablosundan çeker."""
        async with get_db_ctx() as db:
            query = select(func.sum(LLMCostLog.cost_usd))
            if project_id:
                query = query.where(LLMCostLog.project_id == project_id)
            
            # Son 30 günlük tüketim (Varsayılan aylık bütçe için)
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
            query = query.where(LLMCostLog.created_at >= start_date)
            
            result = await db.execute(query)
            total = result.scalar() or 0.0
            return float(total)

    @classmethod
    async def check_circuit_breaker(cls, project_id: str, current_cost: float) -> bool:
        """
        Proje bazlı bütçeyi kontrol eder. Limit aşılmışsa False döner.
        """
        async with get_db_ctx() as db:
            res = await db.execute(select(Project).where(Project.id == project_id))
            proj = res.scalar_one_or_none()
            
            if not proj or proj.budget_limit <= 0:
                return True # Sınırsız

            total_consumed = await cls.get_total_consumption(project_id)
            
            if total_consumed >= proj.budget_limit:
                logger.warning(f"BÜTÇE DEVRE KESİCİ TETİKLENDİ: Project {project_id} limit reached (${total_consumed:.4f} >= ${proj.budget_limit})")
                return False
            
            return True

    @staticmethod
    async def log_budget_evidence(project_id: str, total_consumed: float, limit: float):
        """Bütçe durumunu SovereignEvidence olarak kaydeder."""
        async with get_db_ctx() as db:
            evidence = SovereignEvidence(
                evidence_type="economic_drift",
                severity="critical" if total_consumed >= limit else "warning",
                project_id=project_id,
                payload={
                    "total_consumed": total_consumed,
                    "budget_limit": limit,
                    "drift_ratio": round(total_consumed / limit if limit > 0 else 0, 3)
                }
            )
            db.add(evidence)
            await db.commit()
