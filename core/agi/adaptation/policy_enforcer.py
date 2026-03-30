from typing import List, Optional, Any
from core.agi.schemas import ContextPackage
from memory.store import memory_store
from sqlalchemy.ext.asyncio import AsyncSession
from observability.logging import get_logger

_log = get_logger("agi_policy_enforcer")

class PolicyEnforcer:
    """
    Adaptation Core (Katman 8): Meta-Learning Enforcement.
    Öğrenilen politika ve kuralların (Policies) otonom olarak uygulanmasını sağlar.
    """
    def __init__(self):
        pass

    async def get_active_policies(self, db: AsyncSession) -> List[str]:
        """
        Bellekteki (Memory) aktif politika önerilerini çeker.
        """
        try:
            # Sadece 'policy_proposal' kategorisindeki ve 'active' (varsayılan: pending/active) kayıtları al
            policies = await memory_store.get_recent(db, category="policy_proposal", limit=5)
            
            hints = []
            for p in policies:
                rule = p.metadata_.get("proposed_rule", "")
                if rule:
                    hints.append(f"POLİTİKA: {rule}")
            
            return hints
        except Exception as e:
            _log.error(f"Politika çekme hatası: {e}")
            return []

    def inject(self, context: ContextPackage, policies: List[str]):
        """
        Politikaları ContextPackage'e enjekte eder.
        """
        if not policies:
            return
            
        _log.info(f"{len(policies)} Aktif Politika bağlama enjekte ediliyor.")
        context.policy_hints.extend(policies)

# --- Singleton ---
policy_enforcer = PolicyEnforcer()
