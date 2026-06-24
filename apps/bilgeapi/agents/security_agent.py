import logging
from typing import Dict, Any, Optional
from apps.bilgeapi.agents.base import BaseAgent

logger = logging.getLogger("bilgeapi.agents.security")

class SecurityAgent(BaseAgent):
    async def evaluate_risk(
        self,
        action_type: str,
        file_path: str,
        proposed_change: str,
        db_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluates risk of a proposed action on a file.
        Returns a structured risk assessment object.
        """
        raw_prompt = (
            f"You are the Security Analyst Agent. Evaluate the risk of the following proposed action:\n"
            f"Action Type: {action_type}\n"
            f"Target File: {file_path}\n"
            f"Proposed Change:\n{proposed_change}\n\n"
            f"Return a structured risk assessment in JSON format with exactly the following keys:\n"
            f"- 'risk_level': must be one of 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'\n"
            f"- 'risk_score': a float value between 1.0 (safest) and 10.0 (riskiest)\n"
            f"- 'reasons': a list of strings explaining the risk analysis\n"
            f"- 'requires_approval': boolean, true if risk is HIGH or CRITICAL, or touches protected paths\n"
            f"- 'recommended_action': string recommending whether to ALLOW, BLOCK, or request approval.\n"
        )
        
        prompt = self.secret_scanner.scan_and_mask(raw_prompt)
        
        # Use medium complexity for security evaluations
        llm_result = await self.router.generate(
            prompt=prompt,
            options={"complexity": "medium"},
            db_session=db_session
        )
        
        clean_text = self.secret_scanner.scan_and_mask(llm_result.text)
        parsed = self._parse_json_safely(clean_text)
        
        # Fallback validation for malformed output or parsed error
        if "error" in parsed:
            # If LLM returned malformed JSON, escalate risk as a precaution (Constraint 11)
            logger.warning("Malformed JSON from SecurityAgent. Escalating risk to CRITICAL.")
            return {
                "risk_level": "CRITICAL",
                "risk_score": 10.0,
                "reasons": ["Malformed security agent output parsed. Escalated to CRITICAL for safety.", parsed.get("error", "Unknown error")],
                "requires_approval": True,
                "recommended_action": "BLOCK"
            }
            
        # Ensure default keys exist and have safe types
        parsed["risk_level"] = str(parsed.get("risk_level", "HIGH")).upper()
        if parsed["risk_level"] not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            parsed["risk_level"] = "HIGH"
            
        try:
            parsed["risk_score"] = float(parsed.get("risk_score", 7.0))
        except ValueError:
            parsed["risk_score"] = 7.0
            
        parsed["reasons"] = list(parsed.get("reasons", ["Ambiguous risk analysis"]))
        parsed["requires_approval"] = bool(parsed.get("requires_approval", True))
        parsed["recommended_action"] = str(parsed.get("recommended_action", "BLOCK"))
        
        return parsed
