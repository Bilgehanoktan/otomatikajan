import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import (
    UIThirdPartyRiskAssessment, UIExternalTool, UIProviderHealth, ProviderStatus, ToolType
)

class ThirdPartyRiskScorer:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def assess_risk(self, provider: str, tool_key: Optional[str] = None) -> UIThirdPartyRiskAssessment:
        """Calculates a risk score (0-100) for a provider/tool combination."""
        
        score = 0.0
        findings = []

        # 1. Provider Health Factor
        health_res = await self.db_session.execute(
            select(UIProviderHealth).where(UIProviderHealth.provider == provider)
        )
        health = health_res.scalars().first()
        if health:
            if health.status == ProviderStatus.UNAVAILABLE:
                score += 40
                findings.append("Provider is currently UNAVAILABLE.")
            elif health.status == ProviderStatus.DEGRADED:
                score += 20
                findings.append("Provider is showing DEGRADED performance.")
            
            if health.error_rate > 0.2:
                score += 15
                findings.append(f"High error rate detected: {health.error_rate*100:.1f}%")

        # 2. Tool Capability Factor
        if tool_key:
            tool_res = await self.db_session.execute(
                select(UIExternalTool).where(UIExternalTool.tool_key == tool_key)
            )
            tool = tool_res.scalars().first()
            if tool:
                if tool.tool_type in [ToolType.FILE_SYSTEM, ToolType.CLOUD_API]:
                    score += 30
                    findings.append("Tool has high-impact capabilities (Filesystem/Cloud Write).")
                elif tool.tool_type == ToolType.BROWSER_AUTOMATION:
                    score += 15
                    findings.append("Tool performs browser automation (Potential data exposure).")
                
                if tool.requires_approval:
                    score -= 10 # Mitigating factor
                    findings.append("Risk mitigated by mandatory operator approval.")

        # 3. Final Level Assignment
        risk_level = "LOW"
        if score >= 75: risk_level = "CRITICAL"
        elif score >= 50: risk_level = "HIGH"
        elif score >= 25: risk_level = "MEDIUM"

        assessment = UIThirdPartyRiskAssessment(
            id=uuid.uuid4(),
            provider=provider,
            tool_key=tool_key,
            risk_score=score,
            risk_level=risk_level,
            findings_json=findings,
            recommendation=self._get_recommendation(risk_level),
            assessed_at=datetime.now(timezone.utc)
        )
        self.db_session.add(assessment)
        await self.db_session.commit()
        return assessment

    def _get_recommendation(self, level: str) -> str:
        if level == "CRITICAL": return "BLOCK IMMEDIATELY. Provider/Tool combination is unsafe."
        if level == "HIGH": return "Enable MANDATORY SANDBOX and approval for all actions."
        if level == "MEDIUM": return "Monitor closely. Enable approval for write actions."
        return "Safe for autonomous operation under standard policy."
