"""
Resource Manager - AGI Kaynak ve Bütçe Denetleyici (Faz 26)
API kotalarını, bütçe limitlerini ve sağlayıcı durumlarını (429/402) izler.
"""
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import select, func
from libs.db.session import session_scope
from libs.db.models import LLMCostLog, Project
from services.observability.logging import get_logger

logger = get_logger("agi_resource_manager")

class ResourceManager:
    def __init__(self):
        self.provider_status: Dict[str, Dict[str, Any]] = {}
        self.global_budget_limit = 50.0  # Varsayılan günlük limit (USD)
        self.current_daily_spend = 0.0
        self._last_check = datetime.min.replace(tzinfo=timezone.utc)

    async def update_status(self):
        """Kullanım verilerini DB'den günceller."""
        now = datetime.now(timezone.utc)
        if now - self._last_check < timedelta(minutes=5):
            return

        async with session_scope() as db:
            # Bugünün toplam harcamasını hesapla
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            stmt = select(func.sum(LLMCostLog.cost_usd)).where(LLMCostLog.created_at >= today_start)
            result = await db.execute(stmt)
            self.current_daily_spend = result.scalar() or 0.0
            
            logger.info(f"Günlük Harcama Özeti: {self.current_daily_spend:.4f} / {self.global_budget_limit} USD")
            self._last_check = now

    def report_error(self, provider: str, error_code: int):
        """API hatalarını kaydeder ve sağlayıcıyı 'cezalandırır'."""
        if provider not in self.provider_status:
            self.provider_status[provider] = {"fails": 0, "last_error": None, "penalty_until": None}
        
        self.provider_status[provider]["fails"] += 1
        self.provider_status[provider]["last_error"] = error_code
        
        if error_code == 429: # Rate Limit
            # 5 dakika ceza
            self.provider_status[provider]["penalty_until"] = datetime.now(timezone.utc) + timedelta(minutes=5)
            logger.warning(f"Resource: {provider} RATE LIMIT (429) algılandı. 5 dk bekleme moduna alındı.")
        elif error_code == 402: # Payment Required
            # 1 saat ceza
            self.provider_status[provider]["penalty_until"] = datetime.now(timezone.utc) + timedelta(hours=1)
            logger.critical(f"Resource: {provider} BÜTÇE/ÖDEME hatası (402). 1 saat devre dışı.")

    def get_strategy_guidance(self) -> Dict[str, Any]:
        """StrategyTuner için kaynak bazlı rehberlik üretir."""
        budget_ratio = self.current_daily_spend / self.global_budget_limit if self.global_budget_limit > 0 else 0
        
        guidance = {
            "mode": "OPTIMAL",
            "preferred_tier": "high",
            "allow_expensive": True,
            "blocked_providers": []
        }

        now = datetime.now(timezone.utc)
        for provider, stats in self.provider_status.items():
            if stats["penalty_until"] and stats["penalty_until"] > now:
                guidance["blocked_providers"].append(provider)

        if budget_ratio > 0.9:
            guidance["mode"] = "CRITICAL_SAVING"
            guidance["preferred_tier"] = "local"
            guidance["allow_expensive"] = False
        elif budget_ratio > 0.7:
            guidance["mode"] = "CONSERVATIVE"
            guidance["preferred_tier"] = "budget"
            guidance["allow_expensive"] = False
            
        return guidance

resource_manager = ResourceManager()
