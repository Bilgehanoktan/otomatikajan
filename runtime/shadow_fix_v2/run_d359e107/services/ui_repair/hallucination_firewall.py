import logging
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import (
    UICognitiveIntegrityCheck, 
    UIHallucinationFinding, 
    UICognitiveFindingType,
    UIRepairCase,
    UIRepairVerifierRun
)

logger = logging.getLogger(__name__)

class HallucinationFirewall:
    """Phase 20: Detects fabricated references in LLM outputs."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_hallucinations(self, check_id: str, content: str, source_id: str) -> List[UIHallucinationFinding]:
        findings = []
        
        # 1. Check for fabricated files
        file_findings = await self._check_fabricated_files(check_id, content)
        findings.extend(file_findings)
        
        # 2. Check for fabricated test results
        test_findings = await self._check_fabricated_test_results(check_id, content, source_id)
        findings.extend(test_findings)
        
        # 3. Check for fabricated evidence IDs
        evidence_findings = await self._check_fabricated_evidence(check_id, content, source_id)
        findings.extend(evidence_findings)
        
        return findings

    async def _check_fabricated_files(self, check_id: str, content: str) -> List[UIHallucinationFinding]:
        findings = []
        # Mock repo index for demonstration
        valid_files = ["app/page.tsx", "components/Button.tsx", "libs/utils.py", "services/api.py"]
        
        # Simple regex to find file-like patterns
        file_patterns = re.findall(r'[\w/]+\.(?:py|tsx|js|html|css|json)', content)
        for file_path in file_patterns:
            if file_path not in valid_files and "/" in file_path: # Basic heuristic
                findings.append(UIHallucinationFinding(
                    check_id=check_id,
                    finding_type=UICognitiveFindingType.FABRICATED_FILE,
                    severity="HIGH",
                    description=f"LLM referenced a file that does not exist in the repository index: {file_path}",
                    unsupported_reference=file_path,
                    suggested_action="Verify file path or regenerate output.",
                    blocked=True
                ))
        return findings

    async def _check_fabricated_test_results(self, check_id: str, content: str, source_id: str) -> List[UIHallucinationFinding]:
        findings = []
        # Check if LLM claims a test passed that actually failed or doesn't exist
        if "test" in content.lower() and ("passed" in content.lower() or "success" in content.lower()):
            # Search for actual verifier runs for this source
            stmt = select(UIRepairVerifierRun).where(UIRepairVerifierRun.case_id == source_id)
            res = await self.db.execute(stmt)
            verifier_runs = res.scalars().all()
            
            if not verifier_runs:
                findings.append(UIHallucinationFinding(
                    check_id=check_id,
                    finding_type=UICognitiveFindingType.FABRICATED_TEST_RESULT,
                    severity="CRITICAL",
                    description="LLM claimed test success but no verifier runs were found for this case.",
                    unsupported_reference="VerifierRun",
                    suggested_action="Ensure verifier is executed before diagnostic.",
                    blocked=True
                ))
            else:
                any_pass = any(run.status == "PASSED" for run in verifier_runs)
                if not any_pass and "successfully" in content.lower():
                    findings.append(UIHallucinationFinding(
                        check_id=check_id,
                        finding_type=UICognitiveFindingType.FABRICATED_TEST_RESULT,
                        severity="CRITICAL",
                        description="LLM claimed test success but all recorded verifier runs failed.",
                        unsupported_reference="VerifierRunStatus",
                        suggested_action="Correct the diagnostic to reflect test failures.",
                        blocked=True
                    ))
        return findings

    async def _check_fabricated_evidence(self, check_id: str, content: str, source_id: str) -> List[UIHallucinationFinding]:
        findings = []
        # Check for UUID-like strings that might be fake evidence refs
        uuid_patterns = re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', content)
        
        # For simplicity, we assume we only care about evidence directly linked to the case
        stmt = select(UIRepairCase).where(UIRepairCase.id == source_id)
        res = await self.db.execute(stmt)
        case = res.scalar_one_or_none()
        valid_refs = [str(case.id)] if case else []
        
        for ref in uuid_patterns:
            if ref not in valid_refs:
                # This could be a legitimate ID from another system, but for high-security we flag it
                findings.append(UIHallucinationFinding(
                    check_id=check_id,
                    finding_type=UICognitiveFindingType.MISSING_EVIDENCE,
                    severity="MEDIUM",
                    description=f"LLM referenced an external ID without verifiable evidence grounding: {ref}",
                    unsupported_reference=ref,
                    suggested_action="Verify if this ID exists in global lineage.",
                    blocked=False
                ))
        return findings
