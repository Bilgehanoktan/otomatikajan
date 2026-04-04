"""
Merkezi LLM Prompt Deposu (Faz 2 Mimari İyileştirme)
Hard-coded metinleri kod mantığından ayırmak için kullanılır.
"""

DEBATE_PROMPT_A = """{history}
--- Tur {round_num} ---
Sen {agent_a} rolündesin. Persona: {persona_a}

Konuyu kendi uzmanlık perspektifinden analiz et. {context_hint}
Kısa (max 3 paragraf), somut ve teknik ol.
"""

DEBATE_PROMPT_B = """{history}
Sen {agent_b} rolündesin. Persona: {persona_b}

{agent_a}'in argümanını değerlendir. Katılıyorsan gerekçeni belirt, katılmıyorsan teknik itirazını yap. Ortak zemin varsa açıkça belirt.
"""

DEBATE_PROMPT_MOD = """{history}
Sen {moderator} rolündesin. Persona: {persona_m}

Bu turun tartışmasını 1-2 cümleyle özetle ve uzlaşı alanlarını belirt. Eğer tam uzlaşı sağlandıysa cevabının başına [UZLAŞI] yaz.
"""

DEBATE_SYNTHESIS_PROMPT = """{history}
=== FİNAL KARAR ===
Sen {moderator} rolündesin. {persona_m}

Tüm tartışmayı analiz et ve şu formatla nihai kararı ver:
1. Tavsiye edilen yaklaşım (1-2 cümle)
2. Gerekçe (2-3 madde)
3. Risk / dikkat edilecekler (1-2 madde)
4. Sonraki adım (1 madde)
"""

CEO_DELEGATION_PROMPT = """
Sistem analizi bir iyileştirme fırsatı tespit etti:
Başlık: {title}
Kaynak: {source_type}
Önem Derecesi: {severity}
Açıklama: {description}
Kategori: {category}
Öncelik Skoru: {priority_score}
Kanıt (Evidence): {evidence}

KOD TABANI BAĞLAMI (CODEBASE CONTEXT):
{context}

UZMAN AJAN ADAYLARI (En uygun olanı seçin):
{specialist_list_str}

CEO olarak durumu yorumlayın ve en iyi Uzman Ajanı (veya gerekliyse bir yol haritasını) görevlendirin.
Yanıtınızı JSON formatında dönün:
{{
    "title": "Profesyonel görev başlığı",
    "description": "İndekslenmiş bağlama atıfta bulunan spesifik direktif.",
    "reasoning": "Bu durumun neden öncelikli olduğunu ve neden bu spesifik uzman ajanı seçtiğinizi açıklayın.",
    "agent_id": "Listedeki uzman ajanın tam ID'si",
    "confidence": 0.95,
    "is_roadmap": true,
    "steps": [
        {{"title": "1. Adım Başlığı", "description": "...", "agent_id": "..."}},
        {{"title": "2. Adım Başlığı", "description": "...", "agent_id": "..."}}
    ],
    "projection": {{
        "estimated_cost": 250.0,
        "risk_reduction_pct": 80,
        "performance_gain": "high"
    }}
}}

ÖNEMLİ: Tüm açıklamalar, başlıklar ve gerekçeler TÜRKÇE olmalıdır.
"""
