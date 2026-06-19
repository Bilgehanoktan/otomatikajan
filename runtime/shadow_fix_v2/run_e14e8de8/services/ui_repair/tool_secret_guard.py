import re
from typing import Any, Dict, List, Tuple

class ToolSecretGuard:
    """Phase 18: Scans and redacts secrets from tool inputs/outputs."""
    
    # Common secret patterns
    SECRET_PATTERNS = {
        "GITHUB_TOKEN": r"(?:ghp_|gho_|ghu_|ghs_|ghr_)[a-zA-Z0-9]{36}",
        "OPENAI_KEY": r"sk-[a-zA-Z0-9]{48}",
        "GENERIC_API_KEY": r"(?i)(?:api_key|apikey|secret|password|token)[\s:=]+['\"]?([a-zA-Z0-9]{20,})['\"]?",
        "CONNECTION_STRING": r"(?i)(?:mongodb\+srv|postgres|mysql|sqlite):\/\/[^:]+:([^@]+)@",
        "BEARER_TOKEN": r"(?i)Bearer\s+[a-zA-Z0-9\-\._~+/]+=*",
        "JWT": r"eyJh[a-zA-Z0-9-_]+\.eyJh[a-zA-Z0-9-_]+\.[a-zA-Z0-9-_]+",
        "AWS_KEY": r"AKIA[0-9A-Z]{16}"
    }

    def redact_text(self, text: str) -> Tuple[str, bool]:
        """Redacts secrets in a string and returns (redacted_text, was_redacted)."""
        if not text:
            return text, False
        
        redacted = text
        was_redacted = False
        
        for name, pattern in self.SECRET_PATTERNS.items():
            matches = re.finditer(pattern, redacted)
            for match in matches:
                # For generic API key, we might only want to redact the captured group 1
                if name == "GENERIC_API_KEY" and len(match.groups()) > 0:
                    secret_val = match.group(1)
                    redacted = redacted.replace(secret_val, "[REDACTED_" + name + "]")
                elif name == "CONNECTION_STRING" and len(match.groups()) > 0:
                    password = match.group(1)
                    redacted = redacted.replace(password, "[REDACTED_PWD]")
                else:
                    redacted = redacted.replace(match.group(0), "[REDACTED_" + name + "]")
                was_redacted = True
                
        return redacted, was_redacted

    def sanitize_data(self, data: Any) -> Tuple[Any, bool]:
        """Recursively sanitizes dicts, lists, and strings."""
        if isinstance(data, str):
            return self.redact_text(data)
        
        if isinstance(data, list):
            new_list = []
            any_redacted = False
            for item in data:
                val, red = self.sanitize_data(item)
                new_list.append(val)
                if red: any_redacted = True
            return new_list, any_redacted
        
        if isinstance(data, dict):
            new_dict = {}
            any_redacted = False
            for k, v in data.items():
                # If key name suggests a secret, redact it regardless of value content (if value is string)
                if isinstance(v, str) and any(kw in k.lower() for kw in ["key", "token", "secret", "password", "pwd"]):
                    new_dict[k] = "[REDACTED_BY_KEY_NAME]"
                    any_redacted = True
                    continue
                
                val, red = self.sanitize_data(v)
                new_dict[k] = val
                if red: any_redacted = True
            return new_dict, any_redacted
            
        return data, False
