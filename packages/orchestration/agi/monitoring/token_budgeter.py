import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from packages.observability.logging import get_logger
from packages.persistence.session import session_scope
from packages.persistence.models import LLMCostLog

_log = get_logger("agi_token_budgeter")

class TokenBudgeter:
    """
    AGI 'Metabolizma' ve Kaynak Yönetim Birimi (Token Budgeter).
    Sistemin LLM kullanımını, maliyetlerini ve hız limitlerini (429) izler.
    Arka plan görevleri ile gerçek zamanlı görevler arasında denge kurar.
    """
    
    def __init__(self):
        self.daily_limit_usd = 50.0      # Günlük toplam sınır
        self.hourly_limit_usd = 10.0     # Saatlik toplam sınır
        self.background_daily_usd = 15.0 # Arka plan (Self-Evolution) sınırı
        
        # Kritik olmayan görevlerin listesi (Arka Plan)
        self.background_agents = [
            "architect", "diagnostic_node", "consolidator", 
            "synapse_stabilizer", "source_refactor"
        ]

    async def check_health(self) -> Dict[str, Any]:
        """Sistemin finansal ve kaynak sağlığını kontrol eder."""
        async with session_scope() as db:
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            hour_start = now - timedelta(hours=1)
            
            # 1. Bugünün Toplam Maliyeti
            today_cost = await self._get_cost(db, today_start)
            
            # 2. Son 1 Saatin Maliyeti
            hour_cost = await self._get_cost(db, hour_start)
            
            # 3. Arka Plan (Self-Evolution) Maliyeti
            bg_cost = await self._get_cost(db, today_start, agent_ids=self.background_agents)
            
            health_score = 1.0
            reasons = []
            
            if today_cost > self.daily_limit_usd * 0.9:
                health_score *= 0.1
                reasons.append("Daily total limit reached (%90+)")
            elif bg_cost > self.background_daily_usd:
                health_score *= 0.3
                reasons.append("Background evolution budget exhausted")
            elif hour_cost > self.hourly_limit_usd:
                health_score *= 0.5
                reasons.append("Hourly velocity limit reached")
                
            return {
                "health_score": round(health_score, 2),
                "today_cost_usd": today_cost,
                "hour_cost_usd": hour_cost,
                "background_cost_usd": bg_cost,
                "reasons": reasons,
                "allow_background": health_score > 0.5
            }

    async def _get_cost(self, db: AsyncSession, start_time: datetime, agent_ids: Optional[list] = None) -> float:
        q = select(func.sum(LLMCostLog.cost_usd)).where(LLMCostLog.created_at >= start_time)
        if agent_ids:
            q = q.where(LLMCostLog.agent_id.in_(agent_ids))
            
        result = await db.execute(q)
        val = result.scalar()
        return float(val) if val else 0.0

    async def should_execute(self, agent_id: str) -> bool:
        """Belirli bir ajanın çalışmaya devam edip edemeyeceğini belirler."""
        # Gerçek zamanlı kullanıcı istekleri her zaman önceliklidir (Eğer $50 limit aşılmadıysa)
        is_bg = agent_id in self.background_agents
        
        health = await self.check_health()
        
        if health["health_score"] <= 0.1: # Kritik durum
            _log.critical("[BUDGET] TÜM SİSTEM DURDURULDU: Günlük bütçe sınırı.")
            return False
            
        if is_bg and not health["allow_background"]:
            _log.warning(f"[BUDGET] Arka plan görevi askıya alındı: {agent_id}. Neden: {health['reasons']}")
            return False
            
        return True

token_budgeter = TokenBudgeter()
