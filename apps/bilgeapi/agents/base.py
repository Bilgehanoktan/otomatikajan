import re
import json
import logging
from typing import Dict, Any, Optional
from apps.bilgeapi.llm.router import LLMRouter
from apps.bilgeapi.security.secret_scanner import SecretScanner

logger = logging.getLogger("bilgeapi.agents.base")

class BaseAgent:
    def __init__(self, router: Optional[LLMRouter] = None, secret_scanner: Optional[SecretScanner] = None):
        self.router = router or LLMRouter()
        self.secret_scanner = secret_scanner or SecretScanner()

    def _parse_json_safely(self, text: str) -> Dict[str, Any]:
        """
        Extracts and parses JSON from LLM response text.
        If parsing fails or is malformed, returns a structured error dict without crashing.
        """
        if not text:
            return {"error": "Empty LLM response", "raw_text": ""}

        # Attempt 1: Direct JSON parsing
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Attempt 2: Extract from ```json ... ``` code blocks
        json_block_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
        if json_block_match:
            try:
                return json.loads(json_block_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Attempt 3: Regex match the first '{' and matching last '}'
        first_curly = text.find("{")
        last_curly = text.rfind("}")
        if first_curly != -1 and last_curly != -1 and last_curly > first_curly:
            try:
                return json.loads(text[first_curly:last_curly+1].strip())
            except json.JSONDecodeError:
                pass

        logger.warning("Failed to parse JSON from LLM response.")
        return {
            "error": "Malformed JSON",
            "raw_text": text
        }
