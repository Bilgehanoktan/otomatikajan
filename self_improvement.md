# Faz 5 — Kontrollü Self-Improvement Mimarisi

> **Temel Prensip:** Sistem kendi kodunu doğrudan değiştirmez.
> Öneri üretir, test eder, insana sunar.

## Pipeline Genel Akış

```
╔══════════╗    ╔══════════╗    ╔══════════╗    ╔══════════╗
║ OBSERVE  ║───▶║ PROPOSE  ║───▶║ VERIFY   ║───▶║   GATE   ║
║          ║    ║          ║    ║          ║    ║          ║
║ Metrik   ║    ║  Diff    ║    ║  Test    ║    ║ Onay /   ║
║ toplama  ║    ║  üretme  ║    ║  çalıştır║    ║ Rollback ║
╚══════════╝    ╚══════════╝    ╚══════════╝    ╚══════════╝
```

---

## 1. OBSERVE — Metrik Toplama

Periyodik olarak (heal_engine döngüsüne entegre):

| Metrik | Kaynak | Alarm Eşiği |
|--------|--------|-------------|
| Agent fail rate | `core/heal_engine.py → _snaps` | >30% (son 1 saat) |
| Endpoint error rate | `db/repository.py → ApiMetricRepository` | >5% |
| Ortalama latency | `ApiMetricRepository.endpoint_stats()` | >10s |
| Tekrar eden hatalar | `heal/root_cause.py → RootCauseAnalyzer` | Aynı hata >5 kez |
| Quality scorer ort. | `quality/scorer.py` | <0.6 |

### Sınıf: `ImprovementObserver`
```python
class ImprovementObserver:
    """Sistemdeki iyileştirme fırsatlarını tespit eder."""

    async def scan(self) -> list[ImprovementOpportunity]:
        """Tüm metrikleri tarar, eşik ihlallerini raporlar."""
        ...

    async def prioritize(self, opps: list) -> list:
        """Risk × etki × kolaylık skorlarına göre sıralar."""
        ...
```

---

## 2. PROPOSE — Patch Diff Üretme

LLM'ye sorun bağlamı + ilgili dosya(lar) + hata logları verilir.

### Güvenli Hedef Dosyalar (patch uygulanabilir)
- `heal/recovery_strategies.py` — strateji ekleme/düzenleme
- `config.py` — parametre ayarları
- Prompt template'leri
- DAG ağırlıkları

### Asla Patch Uygulanmayacak Dosyalar
- `db/models.py` — şema değişiklikleri tehlikeli
- `auth/jwt_auth.py` — güvenlik kritik
- `core/orchestrator.py` — merkez bileşen
- `main.py` — uygulama giriş noktası

### Sınıf: `PatchProposer`
```python
class PatchProposer:
    """Tespit edilen sorun için diff üretir."""

    SAFE_TARGETS = [
        "heal/recovery_strategies.py",
        "config.py",
    ]

    async def propose(self, opportunity: ImprovementOpportunity) -> PatchProposal:
        """
        1. İlgili dosyaları oku
        2. LLM'ye sorun + dosyalar + hata logları ver
        3. unified diff formatında patch al
        4. Hedef dosya güvenli listede mi kontrol et
        """
        ...
```

---

## 3. VERIFY — Otomatik Doğrulama

Patch bir sandbox branch/kopya üzerinde uygulandıktan sonra:

| Adım | Komut / İşlem | Başarı Kriteri |
|------|---------------|----------------|
| 1 | `python -m pytest tests/ -x` | Tüm testler pass |
| 2 | `ruff check .` (varsa) | 0 hata |
| 3 | Benchmark: önceki metrik vs sonraki | Kötüleşme ≤ %5 |
| 4 | Güvenlik pattern taraması | Bilinen zafiyet yok |

### Sınıf: `PatchVerifier`
```python
class PatchVerifier:
    """Önerilen patch'i test eder."""

    async def verify(self, proposal: PatchProposal) -> VerificationResult:
        """
        1. Patch'i geçici kopyaya uygula
        2. Test suite çalıştır
        3. Önceki/sonraki metrikleri karşılaştır
        4. VerificationResult döndür (pass/fail + detaylar)
        """
        ...
```

---

## 4. GATE / ROLLBACK — Karar

| Senaryo | Karar |
|---------|-------|
| Tüm testler geçti + benchmark ≥ önceki | ✅ İnsan onayına sun |
| Herhangi bir test fail | ❌ Otomatik reject |
| Benchmark %5'ten fazla kötüleşti | ⚠️ Reject + uyarı |
| Güvenlik sorunu tespit | 🛑 Abort + kritik alarm |

### Sınıf: `ImprovementGate`
```python
class ImprovementGate:
    """Patch'in uygulanıp uygulanmayacağına karar verir."""

    async def evaluate(self, result: VerificationResult) -> GateDecision:
        """
        Karar: APPROVE (insana sun) | REJECT (logla) | ABORT (alarm)
        İlk versiyonda otomatik merge YAPILMAZ.
        """
        ...
```

---

## Veri Modelleri

```python
@dataclass
class ImprovementOpportunity:
    id: str
    source_metric: str        # "agent_fail_rate", "endpoint_error_rate" vb.
    severity: str             # "low", "medium", "high", "critical"
    description: str
    affected_files: list[str]
    evidence: dict            # metrik değerleri, hata örnekleri

@dataclass
class PatchProposal:
    opportunity_id: str
    target_file: str
    diff: str                 # unified diff formatı
    explanation: str          # LLM'nin açıklaması
    risk_score: float         # 0.0 - 1.0

@dataclass
class VerificationResult:
    proposal_id: str
    tests_passed: bool
    test_details: str
    benchmark_before: dict
    benchmark_after: dict
    security_ok: bool

@dataclass
class GateDecision:
    proposal_id: str
    decision: str             # "approve", "reject", "abort"
    reason: str
    requires_human: bool = True  # İlk versiyonda her zaman True
```

---

## Entegrasyon Noktaları

1. **Dashboard** — "Önerilen İyileştirmeler" sekmesi (bekleyen patch'ler, geçmiş kararlar)
2. **Telegram** — `/improvements` komutu (son öneriler ve durumları)
3. **Heal Engine** — `monitor_loop()` içinde periyodik `ImprovementObserver.scan()` çağrısı

---

## Uygulama Sırası

| Sıra | Bileşen | Tahmini Efor |
|------|---------|--------------|
| 1 | `ImprovementObserver` — metrik toplama | Küçük |
| 2 | `PatchProposer` — LLM diff üretme | Orta |
| 3 | `PatchVerifier` — test + benchmark | Orta |
| 4 | `ImprovementGate` — karar + rollback | Küçük |
| 5 | Dashboard sekmesi | Küçük |
| 6 | Telegram komutu | Küçük |

---

## Güvenlik Garantileri

1. **Whitelist yaklaşımı** — sadece izinli dosyalara patch önerilir
2. **Otomatik merge yok** — ilk versiyonda insan onayı zorunlu
3. **Sandbox test** — patch asla production dosyasına doğrudan uygulanmaz
4. **Rollback** — her patch öncesi snapshot alınır
5. **Rate limit** — günde en fazla 5 patch önerisi
6. **Audit log** — her öneri, karar ve uygulama loglanır
