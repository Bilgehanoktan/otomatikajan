import logging
from typing import List, Dict, Any, Optional
from apps.bilgeapi.agents.base import BaseAgent

logger = logging.getLogger("bilgeapi.agents.analyst")

class AnalystAgent(BaseAgent):
    async def analyze_system(
        self,
        file_structure: List[str],
        health_score: float,
        db_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Analyzes the system files and health score to recommend improvements.
        All inputs and outputs are redacted.
        """
        files_str = "\n".join(file_structure)
        
        raw_prompt = (
            f"You are the System Analyst Agent. Analyze the following project structure:\n"
            f"{files_str}\n\n"
            f"Current Health Score: {health_score:.1f}/100.0\n\n"
            f"Provide a structured analysis in JSON format with the following fields:\n"
            f"- 'summary': Brief description of the codebase type and structure.\n"
            f"- 'discovered_issues': List of architectural/structure issues found.\n"
            f"- 'suggestions': List of recommendations to improve the health score.\n"
            f"- 'next_recommended_tasks': List of action items.\n"
        )
        
        # Redact prompt before sending
        prompt = self.secret_scanner.scan_and_mask(raw_prompt)
        
        # Generate LLM response using low-complexity routing
        llm_result = await self.router.generate(
            prompt=prompt,
            options={"complexity": "low"},
            db_session=db_session
        )
        
        # Redact response text
        clean_text = self.secret_scanner.scan_and_mask(llm_result.text)
        
        # Parse JSON output
        parsed = self._parse_json_safely(clean_text)
        return parsed
