import os
import re
import fnmatch
from typing import Tuple, List, Dict, Any

class RiskEngine:
    def __init__(self, risk_rules: List[Dict[str, Any]]):
        self.rules = risk_rules

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalizes file path and checks for traversal attempts."""
        normalized = path.replace('\\', '/')
        parts = normalized.split('/')
        if '..' in parts:
            raise ValueError("Path traversal attempt detected")
        return normalized

    @staticmethod
    def _is_protected(path: str) -> Tuple[bool, str]:
        """Checks if a path belongs to a protected area or sensitive file type."""
        try:
            normalized = RiskEngine.normalize_path(path).lower()
        except ValueError as e:
            return True, str(e)
            
        parts = normalized.split('/')
        
        if '.git' in parts:
            return True, "Access to .git folder is protected"
        if '.bilgeapi' in parts:
            return True, "Access to .bilgeapi folder is protected"
        
        # Check specific sensitive files or extensions
        filename = parts[-1] if parts else ""
        if filename.startswith('.env') or '.env' in filename:
            return True, "Access to environment configuration files is protected"
        if filename.endswith('.key') or filename.endswith('.pem'):
            return True, "Access to private keys is protected"
        if filename.endswith('.db') or filename.endswith('.sqlite') or filename.endswith('.sqlite3'):
            return True, "Access to database files is protected"
            
        return False, ""

    def evaluate_path(self, path: str) -> Tuple[str, float, str]:
        """
        Evaluates the risk of a path.
        Returns:
            Tuple[str, float, str]: (risk_level, risk_score, reason)
        """
        try:
            normalized = self.normalize_path(path)
        except ValueError as e:
            return "CRITICAL", 10.0, str(e)

        # 1. Protected paths check
        is_prot, prot_reason = self._is_protected(normalized)
        if is_prot:
            return "CRITICAL", 10.0, prot_reason

        # 2. Evaluate against risk rules
        highest_level = "LOW"
        highest_score = 1.0
        match_reason = "Default low risk path"
        
        level_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        score_map = {
            "LOW": 1.5,
            "MEDIUM": 4.5,
            "HIGH": 7.0,
            "CRITICAL": 9.0
        }

        for rule in self.rules:
            pattern = rule.get("path_pattern")
            if not pattern:
                continue
            
            if self._match_pattern(normalized, pattern):
                rule_level = rule.get("risk_level", "LOW").upper()
                rule_reason = rule.get("reason", "Matched risk rule pattern")
                
                rule_score = score_map.get(rule_level, 1.5)
                
                if level_order.get(rule_level, 1) > level_order.get(highest_level, 1):
                    highest_level = rule_level
                    highest_score = rule_score
                    match_reason = rule_reason

        return highest_level, highest_score, match_reason

    def _match_pattern(self, path: str, pattern: str) -> bool:
        pattern = pattern.replace('\\', '/')
        parts = pattern.split('**')
        escaped_parts = []
        for part in parts:
            regex_part = fnmatch.translate(part)
            # Remove trailing anchors for all python versions
            regex_part = regex_part.replace('\\z', '').replace('\\Z', '').replace('(?ms)', '')
            escaped_parts.append(regex_part)
            
        full_regex = '.*'.join(escaped_parts)
        if not full_regex.startswith('^'):
            full_regex = '^' + full_regex
        if not full_regex.endswith('$'):
            full_regex = full_regex + '$'
            
        try:
            rx = re.compile(full_regex, re.IGNORECASE)
            return bool(rx.match(path))
        except Exception:
            return False
