import re

# Compiled regex patterns for detecting common sensitive keys and tokens
SECRET_PATTERNS = [
    # Private Key blocks
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----", re.IGNORECASE),
    
    # Database Connection Strings (Postgres, MySQL, Redis, MongoDB)
    re.compile(r"(mongodb(?:\+srv)?|postgres(?:ql)?|mysql|redis|sqlite)(://[^:\s]+:[^@\s]+@[^\s]+)", re.IGNORECASE),
    
    # Generic API Keys / Secrets / Tokens in config/code assignments
    # e.g., api_key = "abc123XYZ", password: 'my-password'
    re.compile(r"(?i)\b(password|pass|passwd|secret|sec|token|tok|api_?key|apikey|private_?key|auth_?token|jwt_?secret|webhook_?url)\b\s*[:=]\s*['\"]([^'\"]{4,})['\"]"),
    
    # Specific API token formats
    re.compile(r"\b(xox[pborsa]-[0-9]{12}-[0-9]{12}-[0-9]{12}-[a-z0-9]{32})\b", re.IGNORECASE), # Slack tokens
    re.compile(r"\b(gh[pso]_[a-zA-Z0-9]{36,40})\b"),                                            # GitHub tokens
    re.compile(r"\b(AIzaSy[a-zA-Z0-9-_]{33})\b"),                                               # Google API keys
    re.compile(r"\b(sk-[a-zA-Z0-9]{48})\b"),                                                    # OpenAI API keys
]

class SecretScanner:
    @staticmethod
    def scan_and_mask(content: str) -> str:
        """
        Scans a text content for credentials, tokens, or private keys, and masks them.
        
        Args:
            content: The input text.
            
        Returns:
            str: The sanitized text with secrets masked as '[MASKED_SECRET]'.
        """
        if not content:
            return content

        sanitized = content

        # 1. Mask private key blocks
        sanitized = SECRET_PATTERNS[0].sub("[MASKED_PRIVATE_KEY]", sanitized)

        # 2. Mask database connection strings (hide password section)
        def mask_db_url(match):
            scheme = match.group(1)
            # Replace credentials with [MASKED_CREDENTIALS]
            return f"{scheme}://[MASKED_CREDENTIALS]"
        sanitized = SECRET_PATTERNS[1].sub(mask_db_url, sanitized)

        # 3. Mask generic variable assignments (password = "xyz")
        def mask_assignment(match):
            key = match.group(1)
            val = match.group(2)
            # If the value looks like a placeholder or is already masked, don't mask again
            if val.startswith("[MASKED") or val == "[REDACTED]":
                return match.group(0)
            
            # Keep key name, mask the value
            # Let's preserve the quote style of the original match
            original_match = match.group(0)
            quote = "'" if "'" in original_match.split(key)[-1] else '"'
            return f"{key} = {quote}[MASKED_SECRET]{quote}"
        sanitized = SECRET_PATTERNS[2].sub(mask_assignment, sanitized)

        # 4. Mask specific token signatures
        for pattern in SECRET_PATTERNS[3:]:
            sanitized = pattern.sub("[MASKED_TOKEN]", sanitized)

        return sanitized
