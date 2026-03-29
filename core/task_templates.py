"""
Görev Şablonları / Workflow Templates

Amaç:
- Serbest metin görevleri daha disiplinli hale getirmek
- Orchestrator ve reviewer için daha öngörülebilir görev girdisi üretmek
- "plan / audit / hotfix / refactor / verify" gibi tekrar eden işleri standardize etmek
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import Any

@dataclass
class QualityProfile:
    name: str
    description: str
    required_score: float
    enforce_tests: bool = False
    enforce_security: bool = False

QUALITY_PROFILES = {
    "standard": QualityProfile("standard", "Standart kalite gereksinimleri", 0.7),
    "strict": QualityProfile("strict", "Sıkı kalite, syntax ve mantık hatalarına tolerans yok", 0.85, True),
    "production": QualityProfile("production", "Üretim ortamı kalitesi, tam test ve güvenlik şart", 0.95, True, True)
}

@dataclass
class TaskTemplate:
    id: str
    name: str
    description: str
    system_prompt_extension: str
    default_quality_profile: str = "standard"
    required_tags: list[str] = field(default_factory=list)

TASK_TEMPLATES = {
    "default": TaskTemplate(
        id="default",
        name="Genel Görev",
        description="Özel bir kısıtlaması olmayan standart görev.",
        system_prompt_extension=""
    ),
    "plan": TaskTemplate(
        id="plan",
        name="Mimari Planlama",
        description="Sistem mimarisi, teknoloji veya veritabanı şeması değişikliklerini planla.",
        system_prompt_extension="Sen bir mimari planlayıcısın. Mevcut sistem dokümanlarını oku ve kararlarını ADR (Architecture Decision Record) formatında detaylandır."
    ),
    "audit": TaskTemplate(
        id="audit",
        name="Kod/Sistem Denetimi",
        description="Mevcut kodu güvenlik, performans ve standartlar açısından denetle.",
        system_prompt_extension="Bir denetçisin. Kodu çalıştırma veya değiştirme. Sadece sorunları bul, risk seviyelerini belirt ve onarım önerileri sun."
    ),
    "hotfix": TaskTemplate(
        id="hotfix",
        name="Acil Hata Düzeltme",
        description="Sistemdeki kritik bir hatayı en hızlı ve güvenli şekilde çöz.",
        system_prompt_extension="Acil durum onarımına odaklan. Kodda asgari düzeyde değişiklik yap. Sorunu çözerken başka bir yeri kırmamaya aşırı özen göster.",
        default_quality_profile="strict"
    ),
    "refactor": TaskTemplate(
        id="refactor",
        name="Yeniden Faktörleme (Refactor)",
        description="İşlevselliği değiştirmeden kodun kalitesini ve okunabilirliğini artır.",
        system_prompt_extension="Kodun davranışını kesinlikle değiştirme. Değişken isimlendirmeleri, fonksiyon ayrıştırması ve SOLID prensiplerini uygula."
    ),
    "verify": TaskTemplate(
        id="verify",
        name="Tam Doğrulama (Verify)",
        description="Yapılan değişikliklerin testlerini çalıştır ve ortamın stabil olduğundan emin ol.",
        system_prompt_extension="Test odaklı düşün. Değişikliğin başarılı olduğunu gösterecek bağımsız kanıtlar sun.",
        default_quality_profile="production"
    ),
    "security": TaskTemplate(
        id="security",
        name="Güvenlik Taraması",
        description="Zafiyetleri bul.",
        system_prompt_extension="Rolün bir güvenlik analisti.",
        default_quality_profile="production"
    )
}

def render_task_payload(
    original_prompt: str,
    template_id: str = "default",
    profile_id: str | None = None,
    acceptance_criteria: list[str] | None = None
) -> dict[str, Any]:
    """
    Kullanıcının girdiği prompt'u şablon kuralları ve kabul kriterleriyle genişletir.
    Döner: {"augmented_prompt": str, "metadata": dict}
    """
    template = TASK_TEMPLATES.get(template_id, TASK_TEMPLATES["default"])
    profile_key = profile_id if profile_id else template.default_quality_profile
    profile = QUALITY_PROFILES.get(profile_key, QUALITY_PROFILES["standard"])
    
    parts = []
    
    if template.system_prompt_extension:
        parts.append(f"--- GÖREV ŞABLONU: {template.name} ---")
        parts.append(template.system_prompt_extension)
        parts.append("")
    
    parts.append("--- GÖREV AÇIKLAMASI ---")
    parts.append(original_prompt)
    parts.append("")
    
    if acceptance_criteria and len(acceptance_criteria) > 0:
        parts.append("--- KABUL KRİTERLERİ (Acceptance Criteria) ---")
        for i, criteria in enumerate(acceptance_criteria, 1):
            parts.append(f"{i}. {criteria}")
        parts.append("Bu kriterlerin her birini karşıladığından emin ol.")
        parts.append("")
        
    parts.append(f"--- KALİTE PROFİLİ: {profile.name.upper()} ---")
    parts.append(f"Beklenen Kalite Skoru: {profile.required_score * 100}%")
    if profile.enforce_tests:
        parts.append("ÖNEMLİ: Test kanıtları (test sufficiency) kesinlikle gereklidir.")
    if profile.enforce_security:
        parts.append("ÖNEMLİ: Güvenlik denetimi sıkı şekilde yapılacaktır.")
        
    augmented = "\n".join(parts)
    
    return {
        "augmented_prompt": augmented,
        "metadata": {
            "workflow_template": template.id,
            "quality_profile": profile.name,
            "required_score": profile.required_score,
            "enforce_tests": profile.enforce_tests,
            "enforce_security": profile.enforce_security
        }
    }
