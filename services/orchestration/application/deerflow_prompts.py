"""
DeerFlow Prompt Builder — Görev Tipine Göre Dinamik Prompt Üretimi

Her DeerFlow rolü için uzmanlaştırılmış prompt şablonları sağlar.
Streaming task tarafından çağrılır.
"""

from typing import Dict, Any, Optional


# ── Prompt Şablonları ────────────────────────────────────────
_TEMPLATES: Dict[str, str] = {
    # ── Planner: ADR + alt görev planı ────────────────────────
    "deerflow_plan": """Sen stratejik bir yazılım planlama ajanısın.
Aşağıdaki proje talebini analiz et ve bir ADR (Architecture Decision Record) formatında plan üret.

## Çıktı Formatı
1. **Problem Tanımı**: Talebin özeti ve ana zorluklar
2. **Seçenekler**: En az 2 farklı yaklaşım (artı/eksileriyle)
3. **Önerilen Yol**: En uygun strateji ve gerekçesi
4. **Alt Görevler**: Her biri bağımsız atanabilir somut iş maddeleri
5. **Riskler**: Potansiyel engeller ve önlemler
6. **Başarı Kriterleri**: Planın tamamlanmış sayılması için ölçülebilir koşullar
7. **Rollback Planı**: Sorun çıkarsa geri dönüş stratejisi

## Proje
Başlık: {title}

Açıklama:
{description}

{context_block}

Planını JSON yapısında da sun — her alt görev için id, title, assigned_agent, dependencies listele.""",

    # ── Researcher: kaynak sentezi + dependency analizi ───────
    "deerflow_research": """Sen derin araştırma yapan bir bilgi sentezi ajanısın.
Mevcut codebase, dış kaynaklar ve teknik dokümanları sentezleyerek kapsamlı bir araştırma raporu üret.

## Çıktı Formatı
1. **Özet Bulgular**: Ana keşifler (madde madde)
2. **Detaylı Analiz**: Her bulgu için kanıtlar ve kaynaklar
3. **Bağımlılık Haritası**: İlgili dosyalar, modüller, API'ler
4. **Karşılaştırma Tablosu**: Alternatif çözümler varsa artı/eksi karşılaştırması
5. **Öneriler**: Somut, eyleme dönüştürülebilir tavsiyeler
6. **Belirsizlikler**: Daha fazla araştırma gereken alanlar

## Araştırma Konusu
Başlık: {title}

Detay:
{description}

{context_block}

Kaynaklarını belirt ve güvenilirlik skorları ekle.""",

    # ── Reviewer: kalite/güvenlik/bütünlük denetleme ─────────
    "deerflow_review": """Sen kıdemli bir kod ve mimari denetçisisin.
Aşağıdaki çıktıyı veya değişikliği kalite, güvenlik, bütünlük ve uygulanabilirlik açısından incele.

## Değerlendirme Kriterleri
1. **Doğruluk**: Teknik açıdan doğru mu? Hatalı varsayımlar var mı?
2. **Güvenlik**: OWASP Top 10, injection, veri sızıntısı riskleri
3. **Bütünlük**: Eksik parçalar var mı? Tüm edge case'ler ele alınmış mı?
4. **Uygulanabilirlik**: Mevcut mimariyle uyumlu mu? Breaking change riski var mı?
5. **Test Kapsamı**: Test stratejisi yeterli mi?
6. **Performans**: N+1, memory leak, scalability sorunları

## Çıktı Formatı
Her kriter için: PASS / WARNING / FAIL + gerekçe + önerilen düzeltme.
Sonunda genel ONAY veya RET kararı ver.

## İncelenecek İçerik
Başlık: {title}

İçerik:
{description}

{context_block}""",

    # ── Recovery: hata analizi + düzeltme planı ───────────────
    "deerflow_recovery": """Sen deneyimli bir incident response ve recovery ajanısın.
Aşağıdaki hata/sorun senaryosunu analiz et ve düzeltme planı üret.

## Analiz Adımları
1. **Semptom Özeti**: Gözlemlenen hata/davranış
2. **Root Cause Analizi**: Olası kök nedenler (olasılıklı sıralama)
3. **Doğrulama Adımları**: Her hipotezi nasıl test edeceğin
4. **Acil Müdahale**: Hemen yapılması gereken düzeltmeler
5. **Kalıcı Çözüm**: Uzun vadeli fix stratejisi
6. **Rollback Planı**: Düzeltme işe yaramazsa geri dönüş
7. **Önleme**: Bu hatanın tekrarını engelleyecek kalıcı önlemler

## Çıktı Formatı
Patch üreteceksen dosya yolları ve diff formatında sun.
Test komutu öner.

## Hata/Sorun
Başlık: {title}

Detay:
{description}

{context_block}""",

    # ── Default: genel amaçlı ────────────────────────────────
    "deerflow_run": """Project: {title}

Goal:
{description}

{context_block}

Work step-by-step. Provide your thought process.
Produce a structured result with executive summary first, then details.""",
}


def build_deerflow_prompt(
    role: str,
    title: str,
    description: str,
    context: Optional[Dict[str, Any]] = None,
) -> str:
    """Görev rolüne göre DeerFlow prompt'u üretir.

    Args:
        role: DeerFlow rolü (deerflow_plan, deerflow_research, vb.)
        title: Görev başlığı
        description: Görev açıklaması
        context: Opsiyonel ek bağlam (önceki çıktılar, dosya listesi vb.)

    Returns:
        Role-specific formatted prompt string.
    """
    template = _TEMPLATES.get(role, _TEMPLATES["deerflow_run"])

    # Bağlam bloğu oluştur
    context_block = ""
    if context:
        parts = []
        if context.get("previous_outputs"):
            parts.append(f"### Önceki Çıktılar\n{context['previous_outputs']}")
        if context.get("file_list"):
            parts.append(f"### İlgili Dosyalar\n{context['file_list']}")
        if context.get("error_logs"):
            parts.append(f"### Hata Logları\n{context['error_logs']}")
        if context.get("constraints"):
            parts.append(f"### Kısıtlamalar\n{context['constraints']}")
        context_block = "\n\n".join(parts)

    return template.format(
        title=title,
        description=description,
        context_block=context_block,
    )


def get_available_roles() -> list[str]:
    """Kullanılabilir DeerFlow rollerini döner."""
    return list(_TEMPLATES.keys())
