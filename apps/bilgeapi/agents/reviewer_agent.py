import logging
from typing import Dict, Any, Optional
from apps.bilgeapi.agents.base import BaseAgent

logger = logging.getLogger("bilgeapi.agents.reviewer")

class ReviewerAgent(BaseAgent):
    async def review_diff(
        self,
        diff_text: str,
        db_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Performs a code review on a git-like diff.
        Returns code quality and cleanliness recommendations.
        """
        raw_prompt = (
            f"You are the Code Reviewer Agent. Review the following proposed code change diff:\n"
            f"{diff_text}\n\n"
            f"Return a structured code review in JSON format with the following fields:\n"
            f"- 'summary': Brief description of changes.\n"
            f"- 'quality_score': Float from 1.0 (poor) to 10.0 (excellent) for code quality.\n"
            f"- 'cleanliness_recommendations': List of suggestions for readability, style, or performance.\n"
            f"- 'security_flags': List of security flags or concerns, if any.\n"
        )
        
        prompt = self.secret_scanner.scan_and_mask(raw_prompt)
        
        llm_result = await self.router.generate(
            prompt=prompt,
            options={"complexity": "medium"},
            db_session=db_session
        )
        
        clean_text = self.secret_scanner.scan_and_mask(llm_result.text)
        parsed = self._parse_json_safely(clean_text)
        return parsed
