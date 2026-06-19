import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import UITrustScore

class TrustScoreEngine:
    """Phase 19: Tracks behavior and updates identity trust scores."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_score(self, identity_key: str) -> float:
        res = await self.db_session.execute(
            select(UITrustScore).where(UITrustScore.identity_key == identity_key)
        )
        score = res.scalars().first()
        return score.trust_score if score else 0.0

    async def record_event(self, identity_key: str, event_type: str, success: bool = True):
        res = await self.db_session.execute(
            select(UITrustScore).where(UITrustScore.identity_key == identity_key)
        )
        score = res.scalars().first()
        if not score:
            return

        if success:
            score.success_count += 1
            # Slowly increase trust up to 1.0
            score.trust_score = min(1.0, score.trust_score + 0.01)
        else:
            if event_type == "POLICY_VIOLATION":
                score.policy_violation_count += 1
                score.trust_score = max(0.0, score.trust_score - 0.2)
            elif event_type == "FAILED_HANDSHAKE":
                score.failed_handshake_count += 1
                score.trust_score = max(0.0, score.trust_score - 0.1)
            elif event_type == "STALE_TOKEN":
                score.stale_token_count += 1
                score.trust_score = max(0.0, score.trust_score - 0.05)

        score.last_updated_at = datetime.now(timezone.utc)
        await self.db_session.commit()
