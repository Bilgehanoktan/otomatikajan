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
