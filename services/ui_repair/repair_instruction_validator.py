import logging
import re
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from libs.db.models.ui_repair_models import (
    UICognitiveFindingType,
    UIHallucinationFinding
)

logger = logging.getLogger(__name__)

class RepairInstructionValidator:
    """Phase 20: Validates repair instructions for safety and policy compliance."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    UNSAFE_PATTERNS = [
        (r'delete\s+test', "Deleting tests is prohibited in autonomous repairs."),
        (r'skip\s+test', "Skipping tests is prohibited in autonomous repairs."),
        (r'remove\s+auth', "Removing authentication middleware is prohibited."),
        (r'disable\s+governance', "Disabling governance checks is prohibited."),
        (r'ignore\s+error', "Silencing errors with blanket ignore is risky."),
        (r'password|secret|token', "Potential leak of sensitive information in logs/comments.")
    ]

    async def validate_instructions(self, check_id: str, content: str) -> List[UIHallucinationFinding]:
        findings = []
        
        for pattern, reason in self.UNSAFE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                findings.append(UIHallucinationFinding(
                    check_id=check_id,
                    finding_type=UICognitiveFindingType.UNSAFE_REPAIR_INSTRUCTION,
                    severity="HIGH",
                    description=reason,
                    unsupported_reference=pattern,
                    suggested_action="Refactor repair strategy to maintain security/testing standards.",
                    blocked=True
                ))
        
        return findings
