import os
import json
from typing import Dict, Any, Optional
from fastapi import Request

class I18nService:
    def __init__(self, locales_dir: Optional[str] = None):
        if locales_dir is None:
            # Determine path relative to this file
            locales_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
        self.locales_dir = locales_dir
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_translations()

    def load_translations(self):
        for lang in ["en", "tr"]:
            file_path = os.path.join(self.locales_dir, f"{lang}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.translations[lang] = json.load(f)
                except Exception:
                    self.translations[lang] = {}
            else:
                self.translations[lang] = {}

    def translate(self, key: str, lang: str = "en") -> str:
        lang = lang.lower() if lang else "en"
        # Only support en and tr
        if lang not in ["en", "tr"]:
            # Check prefix like 'en-US' or 'tr-TR'
            if lang.startswith("tr"):
                lang = "tr"
            else:
                lang = "en"
                
        # Try translation in requested lang
        tr_dict = self.translations.get(lang, {})
        if key in tr_dict:
            return tr_dict[key]
            
        # Fallback to English
        fallback_dict = self.translations.get("en", {})
        if key in fallback_dict:
            return fallback_dict[key]
            
        return key

i18n_service = I18nService()

def get_locale(request: Request) -> str:
    # 1. Query Param
    lang = request.query_params.get("lang")
    if lang:
        lang = lang.lower()
        if lang.startswith("tr"):
            return "tr"
        if lang.startswith("en"):
            return "en"
            
    # 2. Accept-Language Header
    accept_lang = request.headers.get("accept-language")
    if accept_lang:
        # e.g. "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
        parts = [p.split(";")[0].strip().lower() for p in accept_lang.split(",")]
        for p in parts:
            if p.startswith("tr"):
                return "tr"
            if p.startswith("en"):
                return "en"
                
    return "en"
