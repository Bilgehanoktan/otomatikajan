import logging
from typing import Dict, Any, Optional
from apps.bilgeapi.agents.base import BaseAgent

logger = logging.getLogger("bilgeapi.agents.tester")

class TesterAgent(BaseAgent):
    async def analyze_test_results(
        self,
        test_output: str,
        db_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Analyzes test outputs and coverage metrics.
        Returns suggestions for test suite expansion.
        """
        raw_prompt = (
            f"You are the Test Manager Agent. Analyze the following unit test execution output:\n"
            f"{test_output}\n\n"
            f"Return a structured test analysis in JSON format with the following fields:\n"
            f"- 'summary': Brief summary of test execution status (passes, failures, errors).\n"
            f"- 'failures': List of failing test cases, if any.\n"
            f"- 'coverage_score': Estimated or reported coverage percent (float, 0.0-100.0).\n"
            f"- 'missing_test_recommendations': List of recommendations for missing tests.\n"
        )
        
        prompt = self.secret_scanner.scan_and_mask(raw_prompt)
        
        llm_result = await self.router.generate(
            prompt=prompt,
            options={"complexity": "low"},
            db_session=db_session
        )
        
        clean_text = self.secret_scanner.scan_and_mask(llm_result.text)
        parsed = self._parse_json_safely(clean_text)
        return parsed
