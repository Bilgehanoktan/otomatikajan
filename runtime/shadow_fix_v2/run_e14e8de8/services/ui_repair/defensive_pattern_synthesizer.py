import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UIDefensivePattern, UIRedTeamFinding, GuardrailDomain
)
from services.observability.logging import get_logger

_log = get_logger("pattern_synthesizer")

class DefensivePatternSynthesizer:
    """Phase 25: Synthesizes reusable defensive patterns from Red Team findings."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def synthesize_patterns(self) -> List[UIDefensivePattern]:
        """Scans for new findings and synthesizes patterns."""
        _log.info("Starting defensive pattern synthesis...")
        
        # 1. Fetch findings that don't have patterns yet
        stmt = select(UIRedTeamFinding).where(UIRedTeamFinding.severity.in_(["CRITICAL", "HIGH"]))
        result = await self.db.execute(stmt)
        findings = result.scalars().all()
        
        patterns = []
        for finding in findings:
            # Check if pattern already exists for this finding
            exists_stmt = select(UIDefensivePattern).where(UIDefensivePattern.source_finding_id == finding.id)
            exists_res = await self.db.execute(exists_stmt)
            if exists_res.scalar_one_or_none():
                continue
                
            pattern = self._create_pattern_from_finding(finding)
            if pattern:
                self.db.add(pattern)
                patterns.append(pattern)
                
        if patterns:
            await self.db.commit()
            _log.info(f"Synthesized {len(patterns)} new defensive patterns.")
            
        return patterns

    def _create_pattern_from_finding(self, finding: UIRedTeamFinding) -> UIDefensivePattern:
        """Logic to derive a generic pattern from a specific finding."""
        pattern_key = f"DP-{finding.id.hex[:8].upper()}"
        
        # Determine pattern type and domain
        ptype = "DETECTION"
        domain = GuardrailDomain.POLICY_AS_CODE
        
        if finding.affected_domain:
            # Map RedTeamTargetDomain to GuardrailDomain if possible
            try:
                domain = GuardrailDomain(finding.affected_domain.name)
            except (ValueError, AttributeError):
                domain = GuardrailDomain.POLICY_AS_CODE

        # Mock rule generation (In Phase 25, this would use LLM or templates)
        detection_rule = {
            "condition": f"event.type == '{finding.finding_type}'",
            "threshold": 0.9 if finding.severity == "CRITICAL" else 0.7,
            "lookback": "1h"
        }
        
        mitigation_rule = {
            "action": "BLOCK" if finding.severity == "CRITICAL" else "CHALLENGE",
            "fallback": "AUDIT"
        }
        
        return UIDefensivePattern(
            id=uuid.uuid4(),
            pattern_key=pattern_key,
            source_finding_id=finding.id,
            pattern_type=ptype,
            affected_domain=domain,
            description=f"Automated pattern derived from: {finding.description}",
            detection_rule_json=detection_rule,
            mitigation_rule_json=mitigation_rule,
            confidence=0.85 if finding.feasible else 0.6,
            status="DRAFT"
        )
