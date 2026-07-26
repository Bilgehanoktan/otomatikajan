# Implementation Plan — Faz 32B: External Agent Capability Registry & Sandbox

## Amaç

Faz 32B, dış ajanların sisteme kontrolsüz erişmesini engelleyen capability registry, policy engine, sandbox executor ve ledger kayıt hattını tamamlar.

Hedef akış:

```text
Agent request -> Capability registry -> Policy engine -> Sandbox executor -> Redacted run ledger -> AgentRunModel audit trail
```

Bu faz dış ajanı doğrudan ana repo üzerinde serbest çalıştırmaz. Ajan isteği önce capability kaydı ve policy kurallarından geçer; ardından sadece izinli handler ve sandbox sınırları içinde yürütülür.

## Güvenlik Sınırları

- Default ajanlar disabled gelir.
- Default sandbox modu `read-only`.
- `requires_human_approval` default `true`.
- `shell=True` kullanılmaz.
- Komut çalıştırma handler allowlist mantığına bağlıdır.
- Canonical path validation repo dışına kaçışı engeller.
- Network policy default `disabled`.
- `stdout` / `stderr` redaction ve truncation uygulanır.
- Her run ledger/audit trail üzerinde izlenebilir.

## Kapsam

### Database Models

`libs/db/models/repair_models.py` içinde:

- `AgentCapabilityModel`
  - `repair_agent_capabilities`
  - `agent_key`, `agent_name`, `enabled`, `risk_level`
  - `allowed_directories`, `blocked_directories`
  - `allowed_commands`, `blocked_commands`
  - `sandbox_mode`, `network_policy`, `allowed_domains`
  - `requires_human_approval`

- `AgentRunModel`
  - `repair_agent_runs`
  - `run_id`, `agent_key`, `status`, `workspace_path`
  - `input_parameters`, `commands_executed`, `policy_violations`
  - `stdout`, `stderr`, `cost`, hash alanları, `ledger_chain_id`

### Migration

Yeni Alembic migration:

```text
libs/db/migrations/alembic/versions/32b9c1d4e5f6_add_repair_agent_capability_tables.py
```

Oluşturulan tablolar:

- `repair_agent_capabilities`
- `repair_agent_runs`

Migration idempotent table-existence check içerir ve JSON alanları SQLite/Postgres uyumlu tanımlar.

### Services

- `services/repair/external_agents/agent_capability_registry.py`
- `services/repair/external_agents/agent_policy_engine.py`
- `services/repair/external_agents/agent_sandbox_executor.py`
- `services/repair/external_agents/agent_ledger_reporter.py`

### API

`services/repair/external_agents/router.py`:

- `GET /capabilities`
- `GET /capabilities/{agent_key}`
- `POST /capabilities/{agent_key}/enable`
- `POST /capabilities/{agent_key}/disable`
- `POST /runs`
- `GET /runs`
- `GET /runs/{run_id}`

Router `services/workflow_api/main.py` üzerinden kayıtlıdır.

## Doğrulama Planı

```powershell
py -3.13 -m pytest tests/repair/test_agent_registry_sandbox_phase32b.py -v
py -3.13 -c "import services.workflow_api.main; print('workflow api import ok')"
$env:DATABASE_URL='sqlite+aiosqlite:///runtime/data/cortex_local_v2.db'; py -3.13 -c "import os, sys; os.environ['DATABASE_URL']='sqlite+aiosqlite:///runtime/data/cortex_local_v2.db'; from alembic.config import main; sys.argv=['alembic','upgrade','head']; main()"
py -3.13 scripts/verify_bilgeapi_migrations.py
```

## Kabul Kriterleri

- `AgentCapabilityModel` ve `AgentRunModel` için gerçek DB migration vardır.
- Faz 32B testleri geçer.
- External agent router import edilir.
- Tag son Faz 32B kapanış commit’i üzerinde durur.
- `implementation_plan.md`, `task.md`, `walkthrough.md` Faz 32B’ye özel içerik taşır.

---

## Ek Uygulama Planı — BilgeAPI Ops stale API key onarımı

### Amaç

`/bilgeapi-ops` sayfasının `sessionStorage` içinde kalmış geçersiz bir API key nedeniyle tüm dashboard verilerini `Unauthorized: Invalid API key` olarak göstermesini düzeltmek ve yetki hatasını gerçek kısmi-veri hatalarından ayırmak.

### Kök neden ve güvenlik sınırı

- `loadBilgeApiOpsSnapshot()` alt isteklerdeki tüm hataları `settle()` ile yutuyor; bu nedenle üst seviye `refresh()` içindeki stale-key temizleme yolu çalışmıyor.
- Düzeltme, snapshot yüklemesinden önce düşük yetkili bir BilgeAPI erişim probu çalıştıracak ve `401/403` durumlarını tipli hata olarak üst katmana taşıyacak.
- API key loglanmayacak, hata metnine eklenmeyecek ve yeni bir plaintext secret repoya yazılmayacak.
- Var olan kısmi-veri davranışı auth dışındaki endpoint arızaları için korunacak.

### TDD akışı

1. `tests/unit/bilgeapi/test_phase27_ops_console_static.py` içinde auth probu, tipli HTTP hata sınıfı ve stale-key temizleme sözleşmesini doğrulayan regresyon testlerini ekle.
2. Testleri çalıştırıp mevcut kodda kırmızı sonucu kaydet.
3. `bilgeapiOpsClient.ts` ve `page.tsx` içinde minimum düzeltmeyi uygula.
4. Unit test, TypeScript, ESLint, production build ve canlı browser doğrulamasını çalıştır.

### Kabul kriterleri

- Geçersiz API key snapshot içindeki altı kısmi hata olarak kalmaz; tek bir auth hatası olarak ele alınır.
- Stale key `sessionStorage` üzerinden temizlenir ve yerel geliştirme fallback’i en fazla bir kez denenir.
- Auth dışındaki endpoint arızaları `partialData` görünümünde kalmaya devam eder.
- Geçerli anahtarla `/v1/admin/api-keys` ve `/bilgeapi-ops` canlı doğrulaması geçer.
- Browser console/page error sonucu ve screenshot kanıtı üretilir.

---

# Implementation Plan — ContentOrchestrator MVP

## Amaç

Instagram içerik araştırmasından çıkan tekrar edilebilir büyüme kalıplarını,
canlı yayın veya ücretli sağlayıcı çağrısı yapmadan güvenli bir kampanya planına
dönüştüren `ContentOrchestrator` çekirdeğini oluşturmak.

## Kapsam

- İçerik amaçları: `reach`, `lead`, `save`, `authority`.
- Formatlar: `reel`, `carousel`, `hybrid`.
- Üç MVP şablonu: araç listesi carousel'i, tek-prompt demo Reels'i ve duygusal
  mini hikâye Reels'i.
- CTA modları: `save_share` ve benzersiz anahtar kelimeye bağlı `keyword_dm`.
- Sağlayıcı yönlendirme modları: `auto`, `compare`, `pipeline`.
- Sağlayıcı adayları: `veo`, `seedance`, `kling`, `hailuo`; profil ve yetenekler
  yapılandırılabilir olacak, dış API çağrısı yapılmayacak.
- Kaynaksız doğrulanabilir iddialar için fail-closed claim gate.
- İzlenecek metrikler: üç saniye tutma, tamamlanma, kaydetme, paylaşma, yorum,
  DM dönüşümü ve satış dönüşümü.
- Her plan `OperationEvidence` üzerinden `EpisodeRecord` / `ActionRecord`
  kanıt hattına yazılabilecek.
- FastAPI üzerinde yalnız plan üreten, dış etkisiz `POST /content/plans` sözleşmesi.

## TDD ve Doğrulama

1. Önce unit ve API contract testleri yazılacak ve eksik uygulama nedeniyle
   başarısız oldukları doğrulanacak.
2. Minimum uygulama ile testler geçirilecek; dış sağlayıcı ve Meta publish
   işlemleri kapsam dışında kalacak.
3. Hedefli coverage en az `%80`, Ruff ve import/type smoke çalıştırılacak.
4. Diff yalnız `services/social_growth`, `tests/social_growth` ve bu planın yeni
   bölümü için gözden geçirilecek.

## Kabul Kriterleri

- Geçersiz `keyword_dm`, tekrarlanan sağlayıcı veya kaynaksız claim fail-closed
  davranır.
- `auto`, `compare` ve `pipeline` deterministik ve test edilebilir rota üretir.
- Her plan hook, içerik parçaları, CTA, provider route, kalite geçitleri ve ölçüm
  sözleşmesi içerir.
- Plan üretimi `DRY_RUN` evidence oluşturur ve canlı paylaşım iddiasında bulunmaz.

---

# Implementation Plan — Governed Multi-Provider Creative Agent ve 90 Günlük Büyüme

## Amaç

Mevcut `ContentOrchestrator` planını OpenAI Structured Outputs ile üretim taslağına
dönüştürmek, Veo/Hailuo için doğrulanmış API sözleşmelerini adaptör katmanına almak,
Seedance/Kling'i doğrulanmış operator konfigürasyonu yokken fail-closed tutmak ve
`@ai_gucum_` için ölçülebilir 90 günlük hesap büyüme planı üretmek.

## Yönetişim Sınırları

- GPT yalnızca verilen brief, claim ve kaynaklardan yapılandırılmış taslak üretir.
- LLM tarafından eklenen kaynak URL veya kaynak dışı doğrulanabilir iddia engellenir.
- Video üretimi maliyetli bir dış etkidir; planla eşleşen `HumanApproval` olmadan
  hiçbir provider çağrısı yapılmaz.
- Veo ve Hailuo endpoint/model sözleşmeleri resmi dokümana dayanır.
- Seedance ve Kling için doğrulanmamış endpoint veya payload şeması uydurulmaz;
  operator tarafından yapılandırılana kadar `BLOCKED_PROVIDER_NOT_CONFIGURED` döner.
- API key, access token ve authorization header evidence/log/response içine yazılmaz.
- Instagram publish, yorum ve DM otomasyonu bu fazda kapsam dışıdır.

## TDD Uygulama Sırası

1. `OpenAICreativePlanner` yapılandırılmış çıktı, grounding ve güvenli hata testleri.
2. `HumanApproval` fail-closed kararı ile provider registry testleri.
3. Veo ve Hailuo submit/poll sözleşme testleri; gizli header'ların çıktıdan
   sızmadığının testi.
4. Seedance/Kling yapılandırılmamış durum testleri.
5. 12 haftalık `AccountGrowthPlanBuilder`, içerik dağılımı ve KPI checkpoint testleri.
6. Korumalı HTTP contract testleri ve mevcut endpoint regresyon testleri.

## 90 Günlük Operasyon Modeli

- Haftalık ritim: 2 Reel + 1 carousel, 4-6 gün Story.
- 36 ana içerik: 11 güncel AI, 11 uygulamalı iş akışı, 7 karşılaştırma,
  4 AI Company perde arkası ve 3 güvenlik/mit içeriği.
- Hafta 1-2: profil onarımı ve ilk dört kaliteli gönderiden baseline.
- Hafta 3-6: hook, format ve yayın penceresi deneyleri.
- Hafta 7-10: doğrulanmış lead magnet ve keyword-DM dönüşüm deneyi.
- Hafta 11-12: yalnız provider metriğiyle kazanan sütunları ölçekleme.
- 24h/72h/7d snapshot; garanti takipçi hedefi veya uydurma benchmark yok.

## Kabul Kriterleri

- GPT çıktısı Pydantic şemasına uyar; çıktı yoksa veya yeni kaynak eklerse fail-closed.
- Onaysız ya da yanlış `plan_id` onaylı video işi provider transport'una ulaşmaz.
- Veo/Hailuo görev kimlikleri normalize edilmiş `VideoJob` olarak döner.
- Seedance/Kling varsayılan durumda açık bir blocker kodu verir.
- 90 günlük plan tam 12 hafta, 36 ana gönderi ve 24h/72h/7d checkpoint içerir.
- Hedefli test coverage en az `%80`; Ruff, mypy ve Bandit geçer.
