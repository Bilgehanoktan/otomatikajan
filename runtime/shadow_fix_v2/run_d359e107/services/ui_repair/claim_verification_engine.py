import logging
import re
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from libs.db.models.ui_repair_models import (
    UILLMClaim,
    UIRepairCase,
    UIRepairVerifierRun
)

logger = logging.getLogger(__name__)

class ClaimVerificationEngine:
    """Phase 20: Extracts and verifies claims from LLM outputs."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def verify_claims(self, check_id: str, content: str, source_id: str) -> List[UILLMClaim]:
        claims = []
        
        # 1. Extract potential claims
        raw_claims = self._extract_claims(content)
        
        for claim_text in raw_claims:
            verification = await self._verify_single_claim(claim_text, source_id)
            
            claims.append(UILLMClaim(
                check_id=check_id,
                claim_text=claim_text,
                claim_type=verification["type"],
                verification_status=verification["status"],
                evidence_refs_json=verification.get("evidence"),
                confidence=verification["confidence"],
                failure_reason=verification.get("reason")
            ))
            
        return claims

    def _extract_claims(self, content: str) -> List[str]:
        # Split by sentences and look for "is", "was", "passed", "failed", "fixed", "at"
        sentences = re.split(r'(?<=[.!?])\s+', content)
        factual_markers = ["is ", "was ", "passed", "failed", "fixed", "located at", "error in"]
        
        extracted = []
        for s in sentences:
            if any(marker in s.lower() for marker in factual_markers):
                extracted.append(s.strip())
        return extracted[:10] # Limit for demo

    async def _verify_single_claim(self, claim_text: str, source_id: str) -> Dict[str, Any]:
        claim_lower = claim_text.lower()
        
        # Test Result Claims
        if "test" in claim_lower or "pass" in claim_lower or "fail" in claim_lower:
            stmt = select(UIRepairVerifierRun).where(UIRepairVerifierRun.case_id == source_id)
            res = await self.db.execute(stmt)
            verifier_runs = res.scalars().all()
            
            if not verifier_runs:
                return {"type": "test_result", "status": "UNSUPPORTED", "confidence": 0.0, "reason": "No verifier runs found."}
                
            any_pass = any(run.status == "PASSED" for run in verifier_runs)
            any_fail = any(run.status == "FAILED" for run in verifier_runs)
            
            if "passed" in claim_lower or "success" in claim_lower:
                if any_pass:
                    return {"type": "test_result", "status": "VERIFIED", "confidence": 1.0, "evidence": {"run_id": str(verifier_runs[0].id)}}
                else:
                    return {"type": "test_result", "status": "CONTRADICTED", "confidence": 1.0, "reason": "All recorded runs failed."}
            
            if "failed" in claim_lower or "error" in claim_lower:
                if any_fail:
                    return {"type": "test_result", "status": "VERIFIED", "confidence": 1.0, "evidence": {"run_id": str(verifier_runs[0].id)}}
                else:
                    return {"type": "test_result", "status": "CONTRADICTED", "confidence": 1.0, "reason": "No recorded failures found."}

        # File/Root Cause Claims
        if "file" in claim_lower or "cause" in claim_lower:
            return {"type": "root_cause", "status": "UNSUPPORTED", "confidence": 0.5, "reason": "Heuristic verification not implemented for specific code logic."}

        return {"type": "general", "status": "UNSUPPORTED", "confidence": 0.3}
