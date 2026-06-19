"""
quality/prompt_guard.py — Output contract enforcement
"""
import json
import re

def enforce_output_contract(text: str, must_be_json: bool = False) -> str:
    """LLM çıktısını temizle ve doğrula."""
    if not text:
        return text
    # JSON bloklarını çıkar
    if must_be_json:
        # ```json ... ``` bloğunu çıkar
        m = re.search(r"```json\s*([\s\S]*?)```", text)
        if m:
            text = m.group(1).strip()
        else:
            m = re.search(r"```([\s\S]*?)```", text)
            if m:
                text = m.group(1).strip()
        # JSON parse doğrulama
        try:
            json.loads(text)
        except json.JSONDecodeError:
            # JSON değilse ham metni dön
            pass
    return text.strip()

def validate_tool_param(params: dict) -> bool:
    """Validates tool parameters against security guardrails."""
    # Simple check for malicious patterns in strings
    forbidden = [";", "&&", "||", "|", "`", "$(", "${"]

    def check_val(v):
        if isinstance(v, str):
            for f in forbidden:
                if f in v:
                    return False
        elif isinstance(v, dict):
            return all(check_val(x) for x in v.values())
        elif isinstance(v, list):
            return all(check_val(x) for x in v)
        return True

    return check_val(params)
