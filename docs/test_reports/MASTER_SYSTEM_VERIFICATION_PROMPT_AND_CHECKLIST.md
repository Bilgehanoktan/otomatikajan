# Sovereign AGI / BilgeAPI Master Sistem Doğrulama Promptu ve Checklisti

> Sürüm: 1.0
>
> Hedef repo: `E:\ai_company_faz12.1`
>
> Amaç: Sistemi kaynak koddan canlı kullanıcı akışına, veri katmanından governance ve recovery katmanına kadar kanıt tabanlı olarak doğrulamak.

Bu doküman bir geçmiş başarı raporu değildir. Her çalıştırmada canlı checkout, çalışan servisler ve o çalıştırmada üretilen kanıtlar yeniden doğrulanmalıdır. Eski raporlar yalnızca baseline veya regresyon karşılaştırması olarak kullanılabilir.

## 1. Kapsam ve mevcut sistem yüzeyleri

Master kontrol en az aşağıdaki yüzeyleri kapsar:

| Alan | Repo veya runtime yüzeyi | Beklenen canlı yüzey |
|---|---|---|
| Ana API | `apps/public_api`, `services/workflow_api` | `http://127.0.0.1:8000` |
| Control plane UI / CMS | `apps/refine_control_plane` | `http://127.0.0.1:3100` |
| BilgeAPI | `apps/bilgeapi` | `http://127.0.0.1:8100` |
| PostgreSQL + pgvector | `db` | host `127.0.0.1:5433`, container `5432` |
| Redis | `redis` | host `127.0.0.1:6380`, container `6379` |
| Celery | `worker`, `deerflow-worker`, `beat` | queue, schedule, retry ve result akışları |
| DeerFlow | `deerflow-bridge` | `http://127.0.0.1:8010` |
| Telegram | `telegram-bot`, `apps/telegram_bot`, `apps/bilgeapi/integrations/telegram.py` | polling/webhook ve kontrollü canlı gönderim |
| Governance | `services/governance`, `services/govern`, `libs/governance` | approval, policy, quorum, proof, audit ve veto |
| Repair / Project Factory | `services/ui_repair`, `services/repair`, `services/project_factory` | incident -> diagnose -> repair -> verify -> human gate |
| Agent runtime | `agents`, `apps/agent_runtime`, `services/orchestration` | planlama, kuyruk, execution ve kayıt zinciri |
| Veri ve hafıza | `libs/db`, `libs/memory`, `knowledge`, `runtime/data` | migration, persistence, provenance ve recovery |
| Gözlemlenebilirlik | `libs/observability`, `services/observability` | logs, metrics, correlation, health/readiness |
| CI / release | `.github/workflows`, `Dockerfile*`, `scripts/run_release_gate.py` | CI parity, image, package ve release kararı |

Bu tablo sabit bir envanter kabul edilmemelidir. Her audit başlangıcında repo tekrar taranmalı; yeni `app`, `service`, router, worker, queue, UI route, migration, integration ve test grubu otomatik olarak kapsama eklenmelidir.

## 2. Kullanım parametreleri

Promptu çalıştırmadan önce aşağıdaki değerleri doldurun:

```text
TARGET_ENV=local|staging|production
AUDIT_MODE=verification-only|repair-authorized
START_MODE=existing-stack|BASLAT-fullstack|docker-compose-full-stack
ALLOW_STACK_START=true|false
ALLOW_DB_WRITES=true|false
ALLOW_MIGRATION_EXECUTION=true|false
ALLOW_EXTERNAL_SENDS=true|false
ALLOW_SAFE_CHAOS=true|false
ALLOW_PARALLEL_AGENTS=true|false
CRITICAL_REPEAT_COUNT=3
SOAK_DURATION_MINUTES=30
PUBLIC_API_BASE_URL=http://127.0.0.1:8000
CONTROL_PLANE_BASE_URL=http://127.0.0.1:3100
BILGEAPI_BASE_URL=http://127.0.0.1:8100
DEERFLOW_BASE_URL=http://127.0.0.1:8010
EVIDENCE_ROOT=runtime/validation-artifacts
```

Güvenli varsayılanlar:

- `AUDIT_MODE=verification-only`
- `ALLOW_STACK_START=false`
- `ALLOW_DB_WRITES=false`
- `ALLOW_MIGRATION_EXECUTION=false`
- `ALLOW_EXTERNAL_SENDS=false`
- `ALLOW_SAFE_CHAOS=false`
- `ALLOW_PARALLEL_AGENTS=false`
- Üretim verisi, kalıcı volume, gerçek kullanıcı, gerçek PR, gerçek deploy veya dış bildirim üzerinde değişiklik yapılmaz.

Tam E2E sonucu için dış gönderim, migration/recovery veya chaos gibi izin gerektiren bir kapı kapalıysa bu kontrol gizlice atlanmaz. Sonuç `FULL_PASS` olamaz; ilgili madde `BLOCKED` veya gerekçeli `NOT_RUN` olarak raporlanır.

## 3. Kopyala-yapıştır master kontrol promptu

```text
Sen E:\ai_company_faz12.1 reposu için bağımsız Lead Verification Engineer, SRE, Security Reviewer ve Governance Auditor olarak çalışıyorsun.

AMAÇ
Sistemi başlangıçtan sona doğrula: repo bütünlüğü, yapılandırma, bağımlılıklar, build, static analysis, unit/integration/E2E testleri, en az %80 coverage, Docker full-stack, PostgreSQL, Redis, Celery, DeerFlow, public API, BilgeAPI, control-plane UI, bütün UI route'ları, WebSocket, webhook, Telegram, agent orchestration, governance, proof/audit, self-healing, UI repair, Project Factory, güvenlik, performans, dayanıklılık, backup/restore, migration, observability, CI ve release gate.

PARAMETRELER
- TARGET_ENV=<local|staging|production>
- AUDIT_MODE=<verification-only|repair-authorized>
- START_MODE=<existing-stack|BASLAT-fullstack|docker-compose-full-stack>
- ALLOW_STACK_START=<true|false>
- ALLOW_DB_WRITES=<true|false>
- ALLOW_MIGRATION_EXECUTION=<true|false>
- ALLOW_EXTERNAL_SENDS=<true|false>
- ALLOW_SAFE_CHAOS=<true|false>
- ALLOW_PARALLEL_AGENTS=<true|false>
- CRITICAL_REPEAT_COUNT=<default 3>
- SOAK_DURATION_MINUTES=<default 30>
- PUBLIC_API_BASE_URL=http://127.0.0.1:8000
- CONTROL_PLANE_BASE_URL=http://127.0.0.1:3100
- BILGEAPI_BASE_URL=http://127.0.0.1:8100
- DEERFLOW_BASE_URL=http://127.0.0.1:8010
- EVIDENCE_ROOT=runtime/validation-artifacts

ZORUNLU ÇALIŞMA KURALLARI
1. Tüm açıklama ve raporları Türkçe yaz; code identifier, command, path, JSON key, API adı ve stack trace metinlerini değiştirme.
2. Önce AGENTS.md ve kapsam altındaki ek AGENTS.md dosyalarını oku. Karmaşık değişiklik gerekirse implementation_plan.md hazırla/güncelle; verification-only modunda ürün kodunu değiştirme.
3. Eski test raporlarını, memory notlarını, README iddialarını veya geçmiş PASS sonuçlarını canlı gerçek kabul etme. Her iddiayı bu çalıştırmada yeniden kanıtla.
4. Önce salt-okunur envanter çıkar. Repo, servis, route, endpoint, worker, queue, migration, integration ve test listelerinden hiçbirini önceden sabit sayma.
5. Kullanıcı değişikliklerini koru. Başlangıç git durumunu kaydet; audit dışı dirty worktree dosyalarına dokunma. git reset --hard, git checkout --, volume silme, down -v veya geniş recursive delete kullanma.
6. Gerçek secret değerlerini hiçbir çıktıya yazma. Sadece değişkenin var/yok, kaynak tipi ve doğrulama durumunu raporla. Token içeren URL, header, cookie ve payload'ları sanitize et.
7. İzin verilmeyen dış etkiyi yapma. Gerçek Telegram gönderimi, webhook, GitHub PR, e-posta, deploy, migration, DB mutation, backup restore veya chaos için ilgili ALLOW_* true olmalıdır.
8. TARGET_ENV=production ise yalnızca salt-okunur kontroller yap; explicit ayrı izin olmadan test verisi üretme, migration çalıştırma, servis durdurma veya chaos uygulama.
9. Her kontrol için ID, komut/yöntem, başlangıç-bitiş zamanı, exit code, süre, sonuç, kısa kanıt ve artifact path kaydet.
10. Sadece HTTP 200 yeterli değildir. Response schema, bağımlılık durumu, auth/RBAC, yan etki, persistence, queue sonucu, audit kaydı ve kullanıcıya görünen UI sonucu doğrulanmalıdır.
11. Her maddeyi PASS, FAIL, BLOCKED, NOT_RUN veya NOT_APPLICABLE ile kapat. Boş, belirsiz veya gizli skip bırakma. NOT_APPLICABLE için repo kanıtı; BLOCKED/NOT_RUN için neden ve tamamlamak için gereken eylem yaz.
12. test.skip, test.fixme, xfail, skipped_no_sample ve flaky retry sonuçlarını ayrı say. Gerekçesiz veya süresiz skip varsa genel sonucu düşür.
13. Kritik akışlarda pass^k uygula: auth, görev/queue, approval/governance, incident/repair, migration doğrulama, API smoke ve UI smoke CRITICAL_REPEAT_COUNT kez ardışık başarılı olmalı.
14. Güvenlik onayını tamamen otomatikleştirme. CRITICAL/HIGH bulgular, auth/RBAC, secret, tenant isolation, destructive action ve release kararı için manuel reviewer kapısı koy.
15. Hata çıktığında kanıtı koru, kök nedeni sınıflandır ve bağımlı kontrolleri BLOCKED olarak işaretle. Bir başarısızlığı gizlemek için testi daraltma veya assertion kaldırma.
16. AUDIT_MODE=repair-authorized ise önce failing test/eval yaz veya mevcut failing kanıtı sabitle; en küçük kök-neden düzeltmesini yap; security review ve etkilenen + full regression kapılarını tekrar çalıştır. Push, merge veya gerçek PR açma.
17. Uzun build/test sonrası Docker stack, port listener ve health durumunu yeniden kontrol et. Başlangıçta healthy olan stackin hâlâ healthy olduğunu varsayma.
18. RUN_DB_MIGRATIONS=true kullanmadan önce backup kanıtı, disposable restore testi, alembic single-head/current-head uyumu ve migration reconciliation testleri PASS olmalıdır.
19. UI onarımı veya UI regression varsa Playwright screenshot/trace kanıtı, UIRepairPRReview, AuditGate ve VerifierMesh sonucu zorunludur. BLOCKED governance durumunda release/merge kararı NO-GO olmalıdır.
20. Her sistem eyleminde beklenen EpisodeRecord, ActionRecord, correlation ID, causality/provenance ve audit ledger bağlantısını doğrula; kayıt yoksa ilgili iş akışı PASS olamaz.

KANIT DİZİNİ
EVIDENCE_ROOT altında system-audit-YYYYMMDD-HHMMSS adlı benzersiz dizin oluştur. En az şunları üret:
- manifest.json
- environment-sanitized.json
- inventory.json
- command-results.jsonl
- test-summary.json
- coverage.xml ve coverage özeti
- api-contract-matrix.json
- route-audit-results.json
- playwright/ screenshot, trace ve failure video'ları
- security/ sanitize edilmiş tarama sonuçları
- performance/ ölçüm sonuçları
- logs/ sanitize edilmiş servis logları
- governance/ EpisodeRecord, ActionRecord ve gate kanıtları
- final-report.md
Artifact içine secret, access token, refresh token, API key, bot token, cookie, kişisel veri veya production dump koyma.

YÜRÜTME SIRASI
A. Yetki ve güvenlik sınırlarını doğrula.
B. Git, host, disk, saat, toolchain ve dependency baseline al.
C. Repo envanteri ve test/route/endpoint coverage matrisi çıkar.
D. Config, production guardrail, secret ve dependency kontrollerini yap.
E. Import, compile, lint, format, typecheck ve build kapılarını çalıştır.
F. Test collection, unit, security, governance, integration, ops, repair, project_factory, UI repair, resilience, chaos, E2E ve full coverage suite çalıştır.
G. Migration, schema, DB integrity, Redis persistence ve backup/restore kontrollerini yap.
H. İzin varsa full-stack'i güvenli şekilde başlat; bütün container, health, readiness, port ve log kontrollerini yap.
I. public API, BilgeAPI, proxy, WebSocket ve webhook sözleşmelerini pozitif/negatif test et.
J. Auth, workflow, queue, worker, agent, governance, proof, repair, Project Factory ve notification iş akışlarını uçtan uca test et.
K. Bütün Next.js page route'larını canlı backend ile test et; console/page/network error, responsive, accessibility, i18n ve auth guard kanıtı topla.
L. İzin varsa Telegram ve diğer external integration'ları controlled live test ile doğrula.
M. OWASP, SAST, dependency, container, secret, tenant, RBAC ve abuse kontrollerini tamamla; manuel security review iste.
N. Observability, performance, soak, restart, dependency loss, retry, idempotency, recovery ve izinli chaos kontrollerini yap.
O. CI parity, production build, release gate, migration/rollback ve deployment readiness doğrula.
P. Kritik akışları pass^k ile tekrarla, audit sonrası state/diff kontrolü yap ve final karar üret.

STOP-THE-LINE KURALI
Aşağıdakilerden biri varsa genel sonuç FULL_PASS olamaz ve release kararı NO-GO olur:
- doğrulanmamış veya sızmış secret
- CRITICAL veya açık HIGH security bulgusu
- auth bypass, cross-tenant access veya yetki yükseltme
- veri kaybı, migration divergence, backup/restore başarısızlığı
- kritik container/DB/Redis/queue/worker sağlıksızlığı
- build, release gate, critical smoke veya pass^k başarısızlığı
- beklenmeyen UI/API 5xx, console/page error veya kritik route coverage boşluğu
- governance gate BLOCKED, eksik human approval veya kanıtsız autonomous action
- EpisodeRecord/ActionRecord/provenance zincirinin kritik akışta eksik olması
- gerçek test yerine mock sonucu canlı E2E kanıtı gibi sunulması
- izin eksikliği nedeniyle zorunlu kritik kontrolün yapılamaması

FINAL RAPOR
Raporu şu sırayla ver:
1. Overall: FULL_PASS | CONDITIONAL_PASS | FAIL | BLOCKED
2. Release decision: GO | CONDITIONAL_GO | NO_GO
3. Scope ve izinler
4. Git SHA/branch/dirty baseline, environment ve toolchain
5. PASS/FAIL/BLOCKED/NOT_RUN/NOT_APPLICABLE sayıları
6. P0/P1/P2/P3 bulguları
7. Component ve test matrix
8. Route/API coverage ve beklenmeyen skip listesi
9. Security, data/migration, performance, resilience ve governance kararları
10. Çalıştırılan exact command'lar, exit code ve süreler
11. Artifact linkleri
12. Bilinen riskler, test edilmemiş alanlar ve tekrar üretim adımları
13. En küçük önerilen sonraki eylemler

Son cümlede açıkça şunu söyle: “Sistemin tamamı doğrulandı” veya “Sistemin tamamı doğrulanmadı”; ikinci durumda eksik/başarısız kritik alanları tek satırda say.
```

## 4. Sonuç durumları ve karar kuralları

### 4.1 Madde durumları

| Durum | Anlam |
|---|---|
| `PASS` | Kontrol bu çalıştırmada yürütüldü, beklenen sonuç alındı ve kanıt yolu mevcut. |
| `FAIL` | Kontrol yürütüldü; assertion, contract, güvenlik veya operasyon beklentisi karşılanmadı. |
| `BLOCKED` | Kontrol gerekli fakat izin, bağımlılık, veri veya ortam engeli nedeniyle tamamlanamadı. |
| `NOT_RUN` | Kontrol çalıştırılmadı; neden, risk ve çalıştırmak için gereken adım yazılmalı. |
| `NOT_APPLICABLE` | Repo envanteri bu kabiliyetin kapsamda olmadığını kanıtlıyor. Varsayımla verilemez. |

### 4.2 Şiddet seviyeleri

| Seviye | Örnek | Karar etkisi |
|---|---|---|
| `P0` | Secret sızıntısı, auth bypass, cross-tenant erişim, veri kaybı, governance bypass | Derhal `NO_GO` |
| `P1` | Kritik akış bozuk, migration uyumsuz, worker/DB down, release gate fail | `NO_GO` |
| `P2` | Kritik olmayan route, performans/SLO veya gözlemlenebilirlik açığı | En fazla `CONDITIONAL_GO` |
| `P3` | Küçük UX, dokümantasyon veya düşük riskli bakım açığı | Risk kabulüyle `GO` mümkün |

### 4.3 Genel karar

- `FULL_PASS / GO`: Zorunlu kontrollerin tamamı `PASS`; kritik akışlar `pass^k`; coverage en az `%80`; açık P0/P1/P2 yok; beklenmeyen skip yok.
- `CONDITIONAL_PASS / CONDITIONAL_GO`: P0/P1 yok; yalnızca sahibi, süresi ve mitigation'ı tanımlı P2/P3 veya kapsam dışı dış entegrasyon vardır.
- `FAIL / NO_GO`: En az bir zorunlu kontrol `FAIL` veya P0/P1 vardır.
- `BLOCKED / NO_GO`: Tam karar için gereken kritik kontrol izin/ortam/veri eksikliği nedeniyle çalıştırılamamıştır.

## 5. Ayrıntılı başlangıçtan-sona checklist

Her satır audit sırasında `[ ]` yerine `[PASS]`, `[FAIL]`, `[BLOCKED]`, `[NOT_RUN]` veya `[NOT_APPLICABLE]` ile kapatılmalıdır.

### A. Yetki, kapsam ve güvenli çalışma sınırları

- [ ] `A-001` `TARGET_ENV`, `AUDIT_MODE`, tüm `ALLOW_*` değerleri ve base URL'ler kaydedildi.
- [ ] `A-002` Production/staging/local ayrımı canlı config ile doğrulandı; yalnızca isimden çıkarım yapılmadı.
- [ ] `A-003` İzin verilen dış etkiler listelendi: stack start, test data, DB write, migration, Telegram, webhook, chaos, PR/deploy.
- [ ] `A-004` Yasaklı işlemler listelendi: real merge, real deploy, production data mutation, volume deletion, secret output.
- [ ] `A-005` Root ve alt dizin `AGENTS.md` talimatları okundu; uygulanacak quality/governance gate'leri kaydedildi.
- [ ] `A-006` Dirty worktree başlangıç snapshot'ı alındı; kullanıcı değişiklikleri ve audit artifact'ları ayrıldı.
- [ ] `A-007` Korunan recovery/backup/volume path'leri tespit edildi; hiçbirinin disposable olmadığı varsayıldı.
- [ ] `A-008` Test verisi için izole tenant/project/user prefix'i ve cleanup stratejisi belirlendi.
- [ ] `A-009` Secret sanitization kuralı log, screenshot, trace, request/response ve artifact katmanlarında etkin.
- [ ] `A-010` Audit komutlarının tamamı timeout, exit code ve süre kaydıyla yürütülecek şekilde hazırlandı.

### B. Host, toolchain ve başlangıç baseline'ı

- [ ] `B-001` `git rev-parse HEAD`, branch, tag ve son commit kaydedildi.
- [ ] `B-002` `git status --short` kaydedildi; cache/artifact gürültüsü ürün değişikliği gibi raporlanmadı.
- [ ] `B-003` Windows sürümü, CPU, RAM ve timezone kaydedildi.
- [ ] `B-004` `C:` ve `E:` free-space ölçüldü; build, image ve artifact için yeterli alan doğrulandı.
- [ ] `B-005` `py -0p`, aktif Python, `pip`, Node, npm, Docker, Compose ve Git sürümleri kaydedildi.
- [ ] `B-006` Python sürümü `pyproject.toml`, CI ve Dockerfile beklentileriyle karşılaştırıldı.
- [ ] `B-007` Node/npm sürümü Next.js ve CI beklentileriyle karşılaştırıldı.
- [ ] `B-008` Sistem saati, timezone ve clock skew kontrol edildi; JWT/webhook zaman testleri için uygun.
- [ ] `B-009` Dinleyen `3100`, `8000`, `8010`, `8100`, `5433`, `6380` portları ve owning PID/container kaydedildi.
- [ ] `B-010` Stale process, duplicate launcher veya paralel Compose build zinciri olmadığı doğrulandı.
- [ ] `B-011` Docker Desktop engine, context ve daemon erişimi ayrı ayrı doğrulandı.
- [ ] `B-012` Kanıt dizini benzersiz timestamp ile oluşturuldu; mevcut artifact overwrite edilmedi.

### C. Repo envanteri ve coverage haritası

- [ ] `C-001` `rg --files` ile repo dosya envanteri çıkarıldı; vendor, archive, generated ve source ayrımı yapıldı.
- [ ] `C-002` `apps`, `services`, `libs`, `workers`, `agents` altındaki bütün birinci seviye modüller listelendi.
- [ ] `C-003` Bütün Python entrypoint, FastAPI app ve router/include_router ilişkileri listelendi.
- [ ] `C-004` Public API ve BilgeAPI OpenAPI route/method listeleri canlı veya import tabanlı çıkarıldı.
- [ ] `C-005` Bütün Next.js `page.tsx`, dynamic route, API/proxy route ve middleware/guard dosyaları listelendi.
- [ ] `C-006` Bütün Celery queue, task, beat schedule, retry ve dead-letter/failure path'leri listelendi.
- [ ] `C-007` Bütün DB model, repository, migration head ve schema ownership alanları listelendi.
- [ ] `C-008` Telegram, DeerFlow, LLM provider, GitHub, MCP, webhook ve diğer external integration'lar listelendi.
- [ ] `C-009` Testler `unit`, `integration`, `e2e`, `live_test`, `security`, `governance`, `ops`, `repair`, `repair_lab`, `project_factory`, `ui_repair`, `resilience`, `chaos`, `taskflow`, `phases` olarak sayıldı.
- [ ] `C-010` Her production component için en az bir test veya gerekçeli gap kaydı bulundu.
- [ ] `C-011` Test dosyalarının referans verdiği helper/harness/fixture/artifact dosyalarının varlığı doğrulandı.
- [ ] `C-012` Generated OpenAPI, JSON schema, route plan ve test plan artifact'larının source ile drift'i kontrol edildi.
- [ ] `C-013` README/Makefile/CI komutları gerçekten var olan dosya ve package isimleriyle karşılaştırıldı.
- [ ] `C-014` Duplicate implementation, duplicate migration tree ve legacy/current import ambiguity listelendi.
- [ ] `C-015` Envanter `inventory.json` ve component-to-test matrix olarak kaydedildi.

### D. Yapılandırma, secret ve production guardrail

- [ ] `D-001` `.env.example` ve `.env.production.example` değişkenleri kodda kullanılan environment değişkenleriyle karşılaştırıldı.
- [ ] `D-002` Zorunlu değişkenlerin yalnızca varlığı doğrulandı; değerler loglanmadı.
- [ ] `D-003` `.env`, private key, token, database dump ve credential file Git tarafından track edilmiyor.
- [ ] `D-004` `JWT_SECRET`, `ADMIN_SECRET`, `DB_PASSWORD`, `REDIS_PASSWORD`, API key ve webhook secret minimum güvenlik koşullarını sağlıyor.
- [ ] `D-005` Production'da debug/dev auto-login/default credential/SQLite fallback/inprocess queue kapalı.
- [ ] `D-006` Production config eksik secret veya zayıf değerle fail-closed davranıyor.
- [ ] `D-007` CORS allowlist, trusted host, proxy headers ve public origin ayarları environment'a uygun.
- [ ] `D-008` Public frontend değişkenlerinde server-only secret bulunmuyor.
- [ ] `D-009` Telegram token, webhook secret ve allowed/admin ID yapılandırması ayrıştırıldı ve sanitize edildi.
- [ ] `D-010` `BILGEAPI_OLLAMA_ALLOWLIST_HOSTS` ve dış URL allowlist'leri SSRF açısından dar kapsamlı.
- [ ] `D-011` `RUN_DB_MIGRATIONS` varsayılanı ve runtime davranışı ortam politikasına uygun.
- [ ] `D-012` Startup validation ve production config guardrail testleri PASS.
- [ ] `D-013` PII, credential, audit evidence ve generated artifact için classification, retention ve deletion politikası tanımlı.
- [ ] `D-014` Test/sandbox verisi production verisinden fiziksel veya mantıksal olarak ayrılmış.

### E. Dependency, supply-chain ve lisans

- [ ] `E-001` Python lock/pin durumu `requirements.txt` ve `pyproject.toml` arasında karşılaştırıldı.
- [ ] `E-002` npm workspace, root ve `apps/refine_control_plane` lockfile tutarlılığı doğrulandı.
- [ ] `E-003` Fresh/isolated install veya lockfile integrity kontrolü PASS.
- [ ] `E-004` `pip check` PASS.
- [ ] `E-005` `pip-audit` sonucu sanitize edilip severity bazında kaydedildi.
- [ ] `E-006` Root ve frontend `npm audit` sonuçları production/dev ayrımıyla kaydedildi.
- [ ] `E-007` Direct ve transitive CRITICAL/HIGH CVE bulunmuyor veya time-bound risk kabulü var.
- [ ] `E-008` Dependency confusion, unpinned Git URL, local path ve abandoned package riski incelendi.
- [ ] `E-009` Kullanılan Python/npm/container lisansları dağıtım politikasıyla uyumlu.
- [ ] `E-010` Mümkünse SBOM üretildi; image/package provenance ile ilişkilendirildi.

### F. Static analysis, import, type, lint ve build

- [ ] `F-001` Python source compile/parse kontrolü PASS; syntax error yok.
- [ ] `F-002` `apps.public_api.main`, `services.workflow_api.main` ve canonical BilgeAPI app import smoke PASS.
- [ ] `F-003` Production environment import smoke PASS; import sırasında istenmeyen dış çağrı veya mutation yok.
- [ ] `F-004` `ruff check .` PASS.
- [ ] `F-005` `ruff format --check .` PASS veya format drift açıkça raporlandı.
- [ ] `F-006` `mypy`/uygulanabilir type checker sonucu kaydedildi; çalışmıyorsa gap olarak işaretlendi.
- [ ] `F-007` Frontend `npm run lint --workspace apps/refine_control_plane` PASS.
- [ ] `F-008` Frontend TypeScript `tsc --noEmit` PASS.
- [ ] `F-009` Frontend production build PASS; generated route list envanterle karşılaştırıldı.
- [ ] `F-010` Root Nx lint/test graph çalışıyor veya workspace config drift'i raporlandı.
- [ ] `F-011` Dockerfile build context içinde gereksiz secret, dump, cache veya dev artifact yok.
- [ ] `F-012` Dead import, circular import, duplicate metric registration ve import-side-effect kontrolleri PASS.
- [ ] `F-013` Generated package/wheel import smoke temiz ortamda PASS.

### G. Test collection, test kalitesi ve coverage

- [ ] `G-001` `pytest --collect-only` collection error olmadan tamamlandı.
- [ ] `G-002` Toplam test sayısı ve grup bazlı test sayıları artifact'a kaydedildi.
- [ ] `G-003` Marker'lar `pytest.ini` ile uyumlu; unknown marker yok.
- [ ] `G-004` Unit test suite PASS.
- [ ] `G-005` Security test suite PASS.
- [ ] `G-006` Governance test suite PASS.
- [ ] `G-007` Integration test suite gerçek DB/Redis ile PASS; yalnızca mock sonucu sayılmadı.
- [ ] `G-008` Ops ve migration reconciliation testleri PASS.
- [ ] `G-009` Repair ve repair_lab testleri PASS.
- [ ] `G-010` Project Factory testleri PASS.
- [ ] `G-011` UI repair regression testleri PASS.
- [ ] `G-012` Resilience ve chaos testleri güvenli izole ortamda PASS veya izin yoksa BLOCKED.
- [ ] `G-013` Python E2E ve smoke testleri PASS.
- [ ] `G-014` Live-test helper/harness dosyaları mevcut; live-test suite PASS.
- [ ] `G-015` Full `pytest tests` suite PASS.
- [ ] `G-016` Coverage line/branch mümkün olan alanlarda ölçüldü; toplam en az `%80`.
- [ ] `G-017` Kritik auth, RBAC, tenant, migration, queue, governance ve repair modülleri ayrı ayrı anlamlı coverage'a sahip.
- [ ] `G-018` Gerekçesiz `skip`, `xfail`, `fixme`, flaky retry veya collection deselection yok.
- [ ] `G-019` Testler environment değişkeni, zaman, sıra ve shared DB state açısından izole.
- [ ] `G-020` Aynı kritik test grubu ardışık `CRITICAL_REPEAT_COUNT` kez PASS.
- [ ] `G-021` Failure artifact'ları assertion, seed ve environment bilgisiyle tekrar üretilebilir.

### H. Database, migration, Redis ve veri bütünlüğü

- [ ] `H-001` DB bağlantısı, sürüm, pgvector extension ve timezone doğrulandı.
- [ ] `H-002` `alembic heads` tek head döndürüyor.
- [ ] `H-003` `alembic current` beklenen head ile uyumlu.
- [ ] `H-004` Duplicate migration tree'lerin revision/down_revision zinciri karşılaştırıldı.
- [ ] `H-005` Migration reconciliation testi PASS; recovered schema ile conflict yok.
- [ ] `H-006` Disposable boş DB üzerinde `upgrade head` PASS.
- [ ] `H-007` Uygulanabilen migration için downgrade/upgrade round-trip disposable DB üzerinde PASS.
- [ ] `H-008` Production-benzeri sanitize edilmiş backup disposable DB'ye restore edildi ve schema/data integrity PASS.
- [ ] `H-009` Backup dosyasının checksum, timestamp, encryption ve erişim izinleri doğrulandı.
- [ ] `H-010` FK, unique, not-null, enum/status ve tenant constraints beklenen şekilde enforcement yapıyor.
- [ ] `H-011` Orphan row, invalid status, duplicate idempotency key ve bozuk audit linkage taraması temiz.
- [ ] `H-012` Transaction rollback, concurrent update ve race-condition senaryoları veri kaybetmiyor.
- [ ] `H-013` Tenant isolation DB query/repository seviyesinde doğrulandı.
- [ ] `H-014` Redis `PING`, auth, DB index, TTL, eviction policy ve persistence davranışı doğrulandı.
- [ ] `H-015` Queue state, retry metadata, scheduled jobs ve stale locks incelendi.
- [ ] `H-016` Redis kaybı/geri gelişi sonrası idempotent recovery doğrulandı.
- [ ] `H-017` Test sonunda başlangıçtaki kalıcı veri ve migration state'i korunuyor.

### I. Docker image, Compose ve canlı runtime

- [ ] `I-001` `docker compose config --quiet` PASS; environment interpolation error yok.
- [ ] `I-002` `docker compose --profile full-stack config --services` envanterle eşleşiyor.
- [ ] `I-003` Root, CMS ve BilgeAPI image build'leri cache bağımsız doğrulandı.
- [ ] `I-004` Image'larda root user, gereksiz capability, writable filesystem, secret layer ve büyük gereksiz dosya kontrol edildi.
- [ ] `I-005` İzin varsa full-stack tek bir launcher/build zinciriyle başlatıldı.
- [ ] `I-006` `app`, `cms`, `db`, `redis`, `worker`, `deerflow-worker`, `beat`, `deerflow-bridge`, `telegram-bot`, `bilgeapi` beklenen durumda.
- [ ] `I-007` Healthcheck tanımlı servislerin tamamı `healthy`; healthcheck olmayan servisler process/functional probe ile doğrulandı.
- [ ] `I-008` `app:8000`, `cms:3100`, `bilgeapi:8100`, `deerflow-bridge:8010`, `db:5432`, `redis:6379` container içinden erişilebilir.
- [ ] `I-009` Host mapping `8000`, `3100`, `8100`, `8010`, `5433`, `6380` doğru listener/container'a gidiyor.
- [ ] `I-010` `pg_isready` ve `redis-cli ping` PASS.
- [ ] `I-011` Worker/deerflow-worker Celery ping, registered task ve queue subscription kontrolü PASS.
- [ ] `I-012` Beat process canlı ve schedule üretimi doğrulandı; duplicate scheduler yok.
- [ ] `I-013` Container restart count, OOMKilled, unhealthy history ve exit logları incelendi.
- [ ] `I-014` Startup loglarında traceback, migration error, token leak veya sürekli reconnect loop yok.
- [ ] `I-015` Uzun build/test sonrasında Compose/health kontrolleri tekrar PASS.
- [ ] `I-016` Tek tek güvenli restart sonrası readiness ve state recovery PASS.
- [ ] `I-017` Host reboot/cold start prosedürü veya eşdeğer disposable testte sistem doğru sırayla ayağa kalkıyor.

### J. Health, readiness, API contract ve proxy

- [ ] `J-001` `GET :8000/health` yalnızca `200` değil, dependency ve runtime profile açısından doğru.
- [ ] `J-002` `GET :8100/health` yalnızca `200` değil, DB ve gerekli subsystem durumları açısından doğru.
- [ ] `J-003` `GET :8010/health` DeerFlow bridge işlevini doğruluyor.
- [ ] `J-004` `GET :3100` HTML render, hydration ve backend erişimiyle PASS.
- [ ] `J-005` Liveness ve readiness ayrımı doğru; dependency down iken yanlış healthy sonucu yok.
- [ ] `J-006` `:8000/docs`, `:8000/openapi.json`, `:8100/docs`, `:8100/openapi.json` erişim politikasıyla uyumlu.
- [ ] `J-007` OpenAPI schema parse oluyor; duplicate operationId, eksik response veya invalid ref yok.
- [ ] `J-008` Source route envanteri ile OpenAPI endpoint/method envanteri arasında açıklanamayan fark yok.
- [ ] `J-009` Her endpoint için auth gereksinimi, role/tenant, request schema, positive response ve controlled negative response test edildi.
- [ ] `J-010` BilgeAPI `scripts/smoke_bilgeapi.py` API key ile tam PASS.
- [ ] `J-011` BilgeAPI auth enforcement key olmadan beklenen `401/403` sonucunu veriyor.
- [ ] `J-012` UI `3100` proxy üzerinden public API ve BilgeAPI istekleri doğru origin'e gidiyor.
- [ ] `J-013` Proxy 4xx/5xx body/status'u bozup yanlış `200` üretmiyor.
- [ ] `J-014` Pagination, filtering, sorting, limit ve malformed query sınırları test edildi.
- [ ] `J-015` Idempotency key tekrarında duplicate side effect oluşmuyor.
- [ ] `J-016` Timeout, retry, cancellation ve downstream error mapping tutarlı.
- [ ] `J-017` Error response secret, stack trace, SQL veya internal path sızdırmıyor.
- [ ] `J-018` WebSocket token/auth, connect, event, reconnect, expired token ve unauthorized senaryoları PASS.
- [ ] `J-019` Webhook signature, replay, invalid timestamp, duplicate delivery ve retry senaryoları PASS.
- [ ] `J-020` Rate limit hem Redis hem fallback modunda fail-safe ve tenant/user bazında doğru.
- [ ] `J-021` Invalid JSON, yanlış `Content-Type`, aşırı payload, eksik alan, ekstra alan ve Unicode sınırları kontrollü hata veriyor.
- [ ] `J-022` Backward compatibility/versioning ve generated client contract drift'i değerlendirildi.

### K. Auth, kullanıcı, RBAC ve tenant akışları

- [ ] `K-001` Register policy, input validation ve duplicate identity davranışı PASS.
- [ ] `K-002` Doğru credential ile login; yanlış credential ile kontrollü hata PASS.
- [ ] `K-003` Access token expiration, signature, issuer/audience ve clock skew doğrulandı.
- [ ] `K-004` Refresh token rotation eski tokenı geçersiz kılıyor.
- [ ] `K-005` Logout/revoke sonrası access/refresh/API key tekrar kullanılamıyor.
- [ ] `K-006` Brute-force/rate-limit/account lock davranışı test edildi.
- [ ] `K-007` Her rol için allow/deny matrix test edildi; default deny uygulanıyor.
- [ ] `K-008` Horizontal ve vertical privilege escalation negatif testleri PASS.
- [ ] `K-009` Tenant A kullanıcısı Tenant B entity/list/count/export sonucuna erişemiyor.
- [ ] `K-010` Disabled/quarantined user/agent yeni iş alamıyor ve mevcut token politikaya uygun davranıyor.
- [ ] `K-011` Auth olayları sanitize edilmiş güvenlik logu ve audit record üretiyor.
- [ ] `K-012` UI route guard, direct URL, browser back ve expired session senaryolarında bypass yok.

### L. Workflow, queue, agent ve scheduler E2E

- [ ] `L-001` API/UI üzerinden test workflow/task oluşturuldu; unique correlation ID alındı.
- [ ] `L-002` Task doğru queue ve priority ile enqueue edildi.
- [ ] `L-003` Uygun worker taskı aldı; status zinciri geçerli state machine izledi.
- [ ] `L-004` Başarılı sonuç DB'de persist edildi ve API/UI'ye yansıdı.
- [ ] `L-005` Planned subtask, dependency ve parent-child ilişkileri doğru.
- [ ] `L-006` Retryable hata exponential/backoff politikasıyla tekrarlandı; duplicate action oluşmadı.
- [ ] `L-007` Non-retryable hata terminal state, error code ve audit evidence üretti.
- [ ] `L-008` Cancel/timeout/dead-letter veya equivalent failure path doğrulandı.
- [ ] `L-009` Worker restart sırasında in-flight task kaybolmadı veya iki kez uygulanmadı.
- [ ] `L-010` Beat tarafından üretilen scheduled task doğru zamanda tek kez çalıştı.
- [ ] `L-011` Queue hydration ve startup consumer restart sonrası pending işleri doğru yüklüyor.
- [ ] `L-012` Budget/quota/priority sınırı pahalı veya yetkisiz execution'ı blokluyor.
- [ ] `L-013` Agent capability/skill policy uygun ajanı seçiyor; karantina ve promotion gate uygulanıyor.
- [ ] `L-014` LLM/provider unavailable iken fallback/fail-closed kararı policy ile uyumlu.
- [ ] `L-015` Her plan, tool/action, result ve decision için EpisodeRecord/ActionRecord/causality ilişkisi var.
- [ ] `L-016` Audit UI/API üzerinden workflow ile aynı correlation chain izlenebiliyor.

### M. Governance, safety, proof ve autonomous repair

- [ ] `M-001` Policy load/sync/version/hash bütünlüğü doğrulandı.
- [ ] `M-002` Approval create/list/approve/reject/expire akışları doğru rol ve tenant ile PASS.
- [ ] `M-003` Quorum eksikse karar uygulanmıyor; quorum tamamlanınca tek kez uygulanıyor.
- [ ] `M-004` Veto, inhibition ve freeze mode execution'ı gerçekten blokluyor.
- [ ] `M-005` Risk/severity mapping güvenli default ile çalışıyor; belirsizlik fail-open yapmıyor.
- [ ] `M-006` Proof snapshot/seal/verify/tamper detection akışı PASS.
- [ ] `M-007` Audit ledger append-only/tamper-evident davranışı doğrulandı.
- [ ] `M-008` Incident oluşturma -> diagnosis -> repair plan zinciri tam.
- [ ] `M-009` Repair patch yalnızca allowlisted workspace/path içinde üretiliyor.
- [ ] `M-010` Sandbox execution network, filesystem ve command policy sınırlarını aşılamıyor.
- [ ] `M-011` Patch tournament/scoring sonucu deterministic kanıtla açıklanıyor.
- [ ] `M-012` VerifierMesh test/evidence olmadan proposalı onaylamıyor.
- [ ] `M-013` UIRepairPRReview, AuditGate ve human gate BLOCKED iken merge/release gerçekleşmiyor.
- [ ] `M-014` Self-healing severity gate destructive veya high-risk eylemi otomatik uygulamıyor.
- [ ] `M-015` `BILGEAPI_AUTONOMY_MODE`/equivalent modlar policy-bound davranıyor.
- [ ] `M-016` External agent/tool governance allowlist, timeout ve result validation uyguluyor.
- [ ] `M-017` Project Factory requirement -> candidate -> implementation -> verification -> PR draft -> final decision akışı PASS.
- [ ] `M-018` Gerçek GitHub PR/merge yerine dry-run/draft adapter kullanıldı; izin yokken dış değişiklik olmadı.
- [ ] `M-019` Learning/memory yalnızca doğrulanmış outcome'u kaydediyor; başarısız veya sahte evidence promotion yapmıyor.
- [ ] `M-020` Governance kararları UI, API, DB ve ledger arasında tutarlı.

### N. Control-plane UI ve tarayıcı E2E

- [ ] `N-001` Gerçek `page.tsx` envanteri audit başlangıcında çıkarıldı; route sayısı hardcode edilmedi.
- [ ] `N-002` Route envanterindeki her statik route en az bir canlı browser sonucu ile eşleşiyor.
- [ ] `N-003` Her dynamic route için API/DB'den gerçek test sample keşfedildi.
- [ ] `N-004` Sample bulunmayan dynamic route `skipped_no_sample` ise nedeni, seed gereksinimi ve risk kaydedildi; sessiz PASS sayılmadı.
- [ ] `N-005` Page-audit harness, fixture, password-file ve output path'leri gerçekten mevcut.
- [ ] `N-006` Login gerçek backend ile doğrulandı; mocked login canlı E2E kanıtı sayılmadı.
- [ ] `N-007` Her route doğru heading/landmark ve ana içerikle render oldu; yalnızca HTTP status kontrol edilmedi.
- [ ] `N-008` Her route için `pageerror=0`, beklenmeyen `console.error=0`.
- [ ] `N-009` Her route için beklenmeyen failed request, `4xx`, `5xx`, CORS ve proxy error yok.
- [ ] `N-010` Loading, empty, populated, error ve permission-denied state'leri test edildi.
- [ ] `N-011` CRUD/form akışlarında client + server validation, success ve error feedback doğru.
- [ ] `N-012` Destructive UI action confirmation, authorization ve audit log gerektiriyor.
- [ ] `N-013` Desktop `1440x1100`, tablet ve mobile `390x844` görünümde horizontal overflow ve inaccessible content yok.
- [ ] `N-014` Mobile drawer/navigation açma-kapama, focus ve viewport sınırları PASS.
- [ ] `N-015` Keyboard-only navigation, visible focus, skip/landmark ve modal focus trap PASS.
- [ ] `N-016` Accessibility scan kritik ihlal üretmiyor; label/name/contrast/ARIA kontrolleri yapıldı.
- [ ] `N-017` Türkçe ve İngilizce locale; missing key, bozuk karakter, taşma ve format hatası yok.
- [ ] `N-018` Refresh/deep-link/browser back ve session restore davranışı PASS.
- [ ] `N-019` WebSocket/live event ekranları reconnect ve duplicate event üretmeden güncelleniyor.
- [ ] `N-020` Chromium zorunlu; Firefox/WebKit coverage yoksa açık gap olarak raporlandı.
- [ ] `N-021` Arbitrary sleep yerine locator/response/state wait kullanıldı.
- [ ] `N-022` Failure'da screenshot, trace ve gerekiyorsa video artifact'ı mevcut.
- [ ] `N-023` UI repair değişikliği varsa before/after screenshot ve governance gate evidence mevcut.
- [ ] `N-024` Route audit sonuç sayısı source route envanteriyle bire bir uzlaştırıldı.
- [ ] `N-025` Kritik ekranlarda visual regression/baseline farkı gözden geçirildi; intentional değişiklik açıkça onaylandı.
- [ ] `N-026` Browser cache, stale asset ve hard-refresh sonrasında frontend/backend version uyuşmazlığı oluşmuyor.

### O. Telegram ve diğer external integration'lar

- [ ] `O-001` External integration listesi ve live/synthetic test ayrımı raporlandı.
- [ ] `O-002` Telegram module import, config varlığı ve allowed/admin ID parsing PASS.
- [ ] `O-003` Telegram token hiçbir log, exception, trace veya URL artifact'ında görünmüyor.
- [ ] `O-004` Polling tek instance çalışıyor; duplicate poller veya webhook/polling çakışması yok.
- [ ] `O-005` Webhook secret/signature doğrulaması; invalid secret ve replay negatif testi PASS.
- [ ] `O-006` Unauthorized Telegram user command alamıyor.
- [ ] `O-007` `/status`, `/tasks`, `/agents`, `/incidents`, approval ve ilgili komutların izin/yanıt davranışı doğrulandı.
- [ ] `O-008` `ALLOW_EXTERNAL_SENDS=true` ise controlled live notification gönderimi `TELEGRAM_SEND_OK=True` ile kanıtlandı.
- [ ] `O-009` Nonexistent approval callback beklenen controlled `404` veya domain error veriyor ve mutation yapmıyor.
- [ ] `O-010` Transient DNS/timeout için bounded retry çalışıyor; duplicate Telegram mesajı üretmiyor.
- [ ] `O-011` DeerFlow bridge health dışında gerçek minimal task/response akışı PASS.
- [ ] `O-012` LLM provider key olmadan fail-safe; key varsa izinli minimal live call timeout/cost sınırıyla PASS.
- [ ] `O-013` GitHub/MCP/webhook adapter'ları izin yokken dry-run; izinliyse sandbox/test target üzerinde doğrulandı.
- [ ] `O-014` External result schema, size, trust ve prompt/tool injection kontrollerinden geçiyor.
- [ ] `O-015` Integration outage sistemin core health/readiness politikasına doğru yansıyor.

### P. Güvenlik doğrulaması

- [ ] `P-001` Tracked dosyalarda secret scan yapıldı; doğrulanmış gerçek secret yok.
- [ ] `P-002` Artifact/log/history içinde token-bearing URL, Authorization header, cookie veya password yok.
- [ ] `P-003` Bandit veya eşdeğer SAST target/exclusion'ları doğru kapsamla PASS.
- [ ] `P-004` `pip-audit` ve `npm audit` CRITICAL/HIGH bulguları kapalı veya zaman sınırlı risk kabulünde.
- [ ] `P-005` Container image vulnerability scan yapıldı.
- [ ] `P-006` SQL/NoSQL/command/template injection testleri parametrized ve controlled input ile PASS.
- [ ] `P-007` Reflected/stored/DOM XSS ve unsafe HTML sink kontrolleri PASS.
- [ ] `P-008` SSRF scheme/host/IP/DNS rebinding/redirect bypass negatif testleri PASS.
- [ ] `P-009` Path traversal, symlink escape ve unauthorized file read/write negatif testleri PASS.
- [ ] `P-010` Unsafe deserialization, YAML/pickle/XML entity ve archive bomb riskleri kontrol edildi.
- [ ] `P-011` File upload varsa type, size, name, path, content ve malware policy uygulanıyor.
- [ ] `P-012` CSRF veya same-site protection cookie tabanlı mutation'larda doğrulandı.
- [ ] `P-013` CORS preflight, wildcard+credentials ve origin spoof negatif testleri PASS.
- [ ] `P-014` Security header'lar CSP, HSTS ortam uygunluğu, X-Content-Type-Options, frame ve referrer politikası açısından değerlendirildi.
- [ ] `P-015` JWT alg confusion, none algorithm, key confusion, expired/not-before ve tamper testleri PASS.
- [ ] `P-016` API key create/list/revoke/rotation; plaintext saklama veya response leak yok.
- [ ] `P-017` Password hashing güçlü; plaintext comparison/logging yok.
- [ ] `P-018` Rate limit/quotas distributed ve fallback modunda bypass edilemiyor.
- [ ] `P-019` Mass assignment ve overposting ile role/tenant/status değiştirilemiyor.
- [ ] `P-020` Broken object-level/function-level authorization negatif testleri PASS.
- [ ] `P-021` WebSocket ve webhook güvenliği REST auth kadar sıkı.
- [ ] `P-022` Error, metrics, health, docs ve debug endpoint'lerinde hassas bilgi sızıntısı yok.
- [ ] `P-023` Dependency/container/runtime least-privilege ve network exposure incelendi.
- [ ] `P-024` CRITICAL/HIGH bulgular için bağımsız manuel reviewer kararı kaydedildi.
- [ ] `P-025` Privacy/PII access, export, retention ve deletion akışlarında tenant ve authorization sınırları doğrulandı.
- [ ] `P-026` Prompt injection, tool injection ve untrusted model output'un command/file/network action'a dönüşmesi negatif test edildi.

### Q. Observability, auditability ve operasyon

- [ ] `Q-001` Structured log format, timestamp, level, service, environment ve correlation ID içeriyor.
- [ ] `Q-002` Aynı E2E akış API -> queue -> worker -> DB -> notification boyunca izlenebiliyor.
- [ ] `Q-003` Health/readiness değişimleri log ve metric ile tutarlı.
- [ ] `Q-004` `/metrics` veya mevcut metrics yüzeyi scrape edilebilir ve bounded cardinality kullanıyor.
- [ ] `Q-005` p50/p95/p99 latency, request count, error rate ve saturation metrikleri mevcut.
- [ ] `Q-006` DB pool, Redis, queue depth/lag, worker state ve retry/DLQ metrikleri mevcut.
- [ ] `Q-007` Governance block, auth failure, security event ve autonomous action audit log üretiyor.
- [ ] `Q-008` Alert koşulları kontrollü test sinyaliyle tetiklendi ve recovery'de çözüldü.
- [ ] `Q-009` Log rotation/retention ve disk büyüme riski değerlendirildi.
- [ ] `Q-010` PII/secret redaction pozitif ve negatif örneklerle doğrulandı.
- [ ] `Q-011` Operator dashboard gerçek runtime verisini gösteriyor; stale/static mock veri PASS sayılmadı.
- [ ] `Q-012` Runbook, alert ve dashboard linkleri güncel endpoint/service adlarıyla eşleşiyor.

### R. Performans, kapasite ve soak

- [ ] `R-001` Test host özellikleri, dataset büyüklüğü, concurrency ve warm/cold koşulları kaydedildi.
- [ ] `R-002` Public API ve BilgeAPI temel endpoint baseline latency/throughput/error rate ölçüldü.
- [ ] `R-003` Login/auth, list/pagination, task create/status ve dashboard hot path'leri yük altında ölçüldü.
- [ ] `R-004` Queue throughput, queue lag ve worker saturation ölçüldü.
- [ ] `R-005` DB connection pool exhaustion ve slow query davranışı test edildi.
- [ ] `R-006` Redis memory/eviction ve cache hit/miss davranışı yük altında izlendi.
- [ ] `R-007` UI LCP/CLS/INP veya uygulanabilir browser performance metrikleri kaydedildi.
- [ ] `R-008` Büyük liste, uzun metin, boş veri ve yüksek cardinality UI davranışı kabul edilebilir.
- [ ] `R-009` `SOAK_DURATION_MINUTES` boyunca CPU, memory, handle/thread, DB connection ve queue trendi izlendi.
- [ ] `R-010` Soak sırasında memory leak, unbounded log, reconnect storm veya task duplication yok.
- [ ] `R-011` Performans sonucu tanımlı SLO/baseline ile karşılaştırıldı; SLO yoksa gap yazıldı.
- [ ] `R-012` Test sonrası sistem normal kaynak kullanımına döndü.

### S. Resilience, chaos, backup ve recovery

- [ ] `S-001` Her kritik servisin restart davranışı ve readiness recovery süresi ölçüldü.
- [ ] `S-002` Worker kill/restart sırasında task kaybı veya duplicate side effect yok.
- [ ] `S-003` Redis kısa süreli unavailable iken fallback/retry/fail-closed davranışı doğru.
- [ ] `S-004` PostgreSQL unavailable iken health/readiness ve kullanıcı hatası doğru; veri corruption yok.
- [ ] `S-005` DeerFlow/LLM/Telegram/GitHub unavailable iken core system controlled degradation gösteriyor.
- [ ] `S-006` Network timeout, DNS failure ve malformed downstream response bounded retry ile yönetiliyor.
- [ ] `S-007` Region/partition, policy drift ve mesh corruption testleri izole ortamda PASS.
- [ ] `S-008` Freeze/quarantine/circuit-breaker açma-kapama ve recovery doğrulandı.
- [ ] `S-009` Backup restore sonrası record count, checksum ve kritik workflow örneği doğrulandı.
- [ ] `S-010` Migration failure sırasında rollback veya restore prosedürü disposable ortamda çalıştı.
- [ ] `S-011` Disk-low/full sinyali güvenli simülasyonda controlled failure üretiyor; gerçek disk doldurulmadı.
- [ ] `S-012` Process crash sonrası stale lock/job ve partial action reconciliation tamamlanıyor.
- [ ] `S-013` Idempotent replay aynı EpisodeRecord/ActionRecord zincirinde duplicate mutation yapmıyor.
- [ ] `S-014` RTO/RPO ölçüldü veya tanımsızsa release risk gap'i yazıldı.
- [ ] `S-015` Chaos yalnızca `ALLOW_SAFE_CHAOS=true` ve disposable/test ortamında yapıldı.
- [ ] `S-016` Chaos sonrası bütün servisler, veriler ve queues baseline'a döndü.

### T. CI, release, deployment ve rollback readiness

- [ ] `T-001` `.github/workflows/ci.yml` komutları local equivalent ile PASS.
- [ ] `T-002` `.github/workflows/bilgeapi-ci.yml` path/package/requirements varsayımları repo ile uyumlu.
- [ ] `T-003` CI'nin çalıştırdığı lint, format, security, test, coverage, frontend ve Docker kapıları gerçekten fail-closed.
- [ ] `T-004` CI artifact'ları coverage/security/Playwright failure kanıtlarını saklıyor.
- [ ] `T-005` Production Docker image build ve image start smoke PASS.
- [ ] `T-006` BilgeAPI standalone/package wheel build ve temiz ortam import smoke PASS.
- [ ] `T-007` OpenAPI artifact source ile güncel; breaking change varsa versioning kararı var.
- [ ] `T-008` `scripts/verify_bilgeapi_migrations.py` PASS.
- [ ] `T-009` `scripts/verify_bilgeapi_production_hardening.py` PASS.
- [ ] `T-010` `scripts/run_release_gate.py --run-tests` PASS ve DB'ye persisted evidence kaydı doğrulandı.
- [ ] `T-011` Release gate `WARNING` sonucunun otomatik GO gibi değerlendirilmediği doğrulandı.
- [ ] `T-012` Version, Git SHA, image tag, changelog ve provenance birbiriyle uyumlu.
- [ ] `T-013` Production config validation, secret source ve migration job sırası doğrulandı.
- [ ] `T-014` Deployment health/readiness, smoke ve rollback trigger'ları tanımlı.
- [ ] `T-015` Önceki image/version'a rollback ve data compatibility disposable ortamda doğrulandı.
- [ ] `T-016` UI değişikliği için screenshot/trace + UIRepairPRReview + AuditGate + VerifierMesh artifact'ı var.
- [ ] `T-017` Human reviewer security/governance/release kararı imzalı veya kimlikli kayıtla mevcut.
- [ ] `T-018` P0/P1 yok; P2/P3 için owner, deadline ve mitigation tanımlı.
- [ ] `T-019` Clean disposable host/environment üzerinde README quickstart veya eşdeğer bootstrap PASS.
- [ ] `T-020` Startup, shutdown, migration, backup, restore, incident, secret rotation ve rollback runbook'ları gerçek komutlarla uyumlu.
- [ ] `T-021` Runbook'taki path, service, port, package ve endpoint isimleri repo/runtime ile eşleşiyor.
- [ ] `T-022` Operator'ın P0/P1 tespiti, freeze, escalation ve recovery adımları masa-başı veya izole drill ile doğrulandı.
- [ ] `T-023` Release artifact'ı yeniden üretilebilir; dependency ve build provenance kaydı var.
- [ ] `T-024` Artifact retention, ownership ve erişim politikası tanımlı; secret/PII içermiyor.

### U. AI/agent eval, model güvenilirliği ve maliyet sınırları

- [ ] `U-001` Kritik agent capability'leri için beklenen input, output, side effect ve failure kriterleri önceden tanımlandı.
- [ ] `U-002` Capability eval ve regression eval setleri version/control altında mevcut veya eksikliği gap olarak kaydedildi.
- [ ] `U-003` Objective davranışlar deterministic code-based grader ile ölçüldü; model grader gereksiz kullanılmadı.
- [ ] `U-004` Ambiguous kalite ve güvenlik kararlarında human grader/reviewer kapısı kullanıldı.
- [ ] `U-005` Her kritik eval için `pass@1`, gerekiyorsa `pass@3` ve güvenilirlik için `pass^3` kaydedildi.
- [ ] `U-006` Model/provider/prompt/tool version, temperature/equivalent ayar ve seed uygulanabiliyorsa artifact'a kaydedildi.
- [ ] `U-007` Aynı inputta kabul edilemez karar veya side-effect varyansı yok; non-determinism sınırı tanımlı.
- [ ] `U-008` Hallucinated file, endpoint, policy, test sonucu ve citation negatif örnekleri yakalanıyor.
- [ ] `U-009` Agent yalnızca yetkili tool, path, network target ve action sınıfını kullanabiliyor.
- [ ] `U-010` Prompt injection, indirect injection, malicious repository text ve tool-output injection governance bypass yapmıyor.
- [ ] `U-011` Structured model output schema validation; eksik/ekstra/invalid output fail-closed davranıyor.
- [ ] `U-012` Timeout, token, step, recursion, retry, concurrency ve monetary cost budget'ları enforcement yapıyor.
- [ ] `U-013` Provider rate-limit/outage veya model fallback daha zayıf policy modeline sessiz düşmüyor.
- [ ] `U-014` Agent memory/learning'e yalnızca doğrulanmış ve tenant-safe bilgi yazılıyor; poisoned feedback promotion yapmıyor.
- [ ] `U-015` Agent eylemleri açıklanabilir decision rationale, EpisodeRecord, ActionRecord ve evidence linki içeriyor.
- [ ] `U-016` Unsafe/destructive öneri ile gerçek execution arasında human/governance confirmation kapısı var.
- [ ] `U-017` Eval sonuçları baseline commit/model/prompt sürümüyle karşılaştırıldı; regression varsa release bloklandı.

### V. Tekrar, cleanup ve final kanıt uzlaştırması

- [ ] `V-001` Auth, API smoke, workflow/queue, governance, repair ve UI smoke `pass^CRITICAL_REPEAT_COUNT` sağladı.
- [ ] `V-002` Retry ile geçen flaky testler ayrı listelendi; ilk deneme başarısı `pass@1` kaydedildi.
- [ ] `V-003` Test kullanıcı/tenant/project/job kayıtları yalnızca izinli test scope'unda temizlendi.
- [ ] `V-004` Başlangıçta var olan container, volume, DB ve dosya state'i yanlışlıkla silinmedi.
- [ ] `V-005` Final `git status --short` başlangıç snapshot'ıyla karşılaştırıldı.
- [ ] `V-006` Audit'in ürettiği artifact dışındaki beklenmeyen repo değişikliği yok.
- [ ] `V-007` Bütün secret-bearing output sanitize edildi; final leak scan PASS.
- [ ] `V-008` Component sayısı, route sayısı, endpoint sayısı ve test sayısı rapor ile artifact'larda eşleşiyor.
- [ ] `V-009` Her FAIL/BLOCKED/NOT_RUN maddesinin issue, owner veya net sonraki adımı var.
- [ ] `V-010` Final report exact Git SHA, tarih, environment ve izin setine bağlı.
- [ ] `V-011` “Sistemin tamamı doğrulandı” ifadesi yalnızca bütün mandatory gate'ler PASS ise kullanıldı.
- [ ] `V-012` Release kararı stop-the-line kurallarıyla matematiksel olarak tutarlı.

## 6. Önerilen komut paketi

Bu bölüm körlemesine çalıştırılacak bir script değildir. Environment ve izinler doğrulandıktan sonra kullanılır; secret değerleri komut satırına veya artifact'a yazılmaz.

### 6.1 Baseline ve envanter

```powershell
git rev-parse HEAD
git branch --show-current
git tag --points-at HEAD
git status --short
[System.IO.DriveInfo]::GetDrives() | Select-Object Name,AvailableFreeSpace,TotalSize
py -0p
py -3.13 --version
node --version
npm --version
docker version
docker compose version
docker context ls
docker compose -f docker-compose.yml --profile full-stack config --services
rg --files apps services libs workers agents tests scripts .github
rg --files apps/refine_control_plane/src/app | rg '(^|[\\/])page\.tsx$'
```

### 6.2 Static analysis, build ve collection

```powershell
py -3.13 -m compileall apps services libs workers agents
py -3.13 -c "import apps.public_api.main; print('public api import ok')"
py -3.13 -c "import services.workflow_api.main; print('workflow api import ok')"
py -3.13 -m ruff check .
py -3.13 -m ruff format --check .
py -3.13 -m pytest --collect-only -q
npm run lint --workspace apps/refine_control_plane
npm run build --workspace apps/refine_control_plane
npx --prefix apps/refine_control_plane tsc --noEmit
```

### 6.3 Test ve coverage

```powershell
py -3.13 -m pytest tests\unit tests\security tests\governance -q
py -3.13 -m pytest tests\integration tests\ops -q
py -3.13 -m pytest tests\repair tests\repair_lab tests\project_factory tests\ui_repair -q
py -3.13 -m pytest tests\resilience tests\chaos tests\e2e tests\live_test -q
py -3.13 -m pytest tests -q --cov=. --cov-report=xml --cov-report=term-missing --cov-fail-under=80
```

### 6.4 Migration ve full-stack

```powershell
py -3.13 scripts\verify_bilgeapi_migrations.py
py -3.13 -m pytest tests\ops\test_migration_reconciliation.py -q
docker compose -f docker-compose.yml --profile full-stack config --quiet
docker compose -f docker-compose.yml --profile full-stack build
docker compose -f docker-compose.yml --profile full-stack up -d
docker compose -f docker-compose.yml --profile full-stack ps
docker compose -f docker-compose.yml --profile full-stack exec db pg_isready -U postgres
docker compose -f docker-compose.yml --profile full-stack exec redis redis-cli ping
```

`up -d`, migration veya DB write komutları yalnızca ilgili izin açıkken çalıştırılır. Korunan volume'larda `down -v` kullanılmaz.

### 6.5 Canlı smoke ve UI

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8100/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8010/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:3100
py -3.13 scripts\smoke_bilgeapi.py --base-url http://127.0.0.1:8100 --api-key <SANITIZED_TEST_KEY_SOURCE>
npx --prefix apps/refine_control_plane playwright test
```

API key değeri rapora, process listesine veya shell history'ye yazılmamalı; environment/secret-store üzerinden aktarılmalıdır.

### 6.6 Security ve release

```powershell
py -3.13 -m bandit -r apps libs services core infra scripts -x tests,alembic,libs/vendor,.legacy_archive -ll
py -3.13 -m pip_audit -r requirements.txt
npm audit
npm audit --workspace apps/refine_control_plane
py -3.13 scripts\verify_bilgeapi_production_hardening.py
py -3.13 scripts\run_release_gate.py --run-tests
```

## 7. Final rapor şablonu

```markdown
# Full System Verification Report

- Audit ID:
- Tarih/saat/timezone:
- Git SHA / branch / tags:
- TARGET_ENV:
- AUDIT_MODE:
- İzinler:
- Evidence root:

## Karar

- Overall: FULL_PASS | CONDITIONAL_PASS | FAIL | BLOCKED
- Release: GO | CONDITIONAL_GO | NO_GO
- Sistem bütünü doğrulandı mı: EVET | HAYIR

## Sonuç sayıları

| PASS | FAIL | BLOCKED | NOT_RUN | NOT_APPLICABLE | Unexpected skips |
|---:|---:|---:|---:|---:|---:|
| | | | | | |

## Stop-the-line kontrolü

| Kural | Sonuç | Kanıt |
|---|---|---|
| Secret leak yok | | |
| CRITICAL/HIGH açık yok | | |
| Auth/RBAC/tenant isolation | | |
| Data/migration/restore | | |
| Critical runtime health | | |
| Build/test/coverage | | |
| API/UI coverage | | |
| Governance/provenance | | |
| pass^k | | |

## P0/P1/P2/P3 bulguları

| ID | Severity | Component | Bulgu | Evidence | Owner | Son tarih |
|---|---|---|---|---|---|---|

## Component matrix

| Component | Build | Test | Live | Security | Observability | Recovery | Sonuç |
|---|---|---|---|---|---|---|---|

## Route ve API coverage

- Source UI route sayısı:
- Audited UI route sayısı:
- Dynamic sample bulunan:
- skipped_no_sample:
- Console/page error:
- OpenAPI operation sayısı:
- Pozitif/negatif contract test edilen:

## Test ve coverage

- Collected:
- Passed:
- Failed:
- Skipped/xfail/fixme:
- Line coverage:
- Kritik modül coverage:
- pass@1:
- pass^k:

## Security review

- SAST:
- Dependency:
- Container:
- OWASP/API abuse:
- Manual reviewer:

## Data, migration ve recovery

- Alembic head/current:
- Reconciliation:
- Disposable upgrade/downgrade:
- Backup/restore:
- RPO/RTO:

## Performance ve resilience

- p50/p95/p99:
- Error rate:
- Queue lag:
- Soak:
- Restart/dependency-loss/chaos:

## Governance ve traceability

- Approval/quorum/veto:
- UIRepairPRReview/AuditGate/VerifierMesh:
- EpisodeRecord/ActionRecord:
- Proof/audit ledger:

## BLOCKED / NOT_RUN / NOT_APPLICABLE

| ID | Durum | Neden | Risk | Tamamlama adımı |
|---|---|---|---|---|

## Çalıştırılan komutlar

| ID | Command | Exit code | Süre | Artifact |
|---|---|---:|---:|---|

## Sonraki eylemler

1.
2.
3.

Nihai ifade: Sistemin tamamı doğrulandı / Sistemin tamamı doğrulanmadı: <kritik nedenler>.
```

## 8. Bu repo için audit öncesi özel dikkat noktaları

Bu maddeler kalıcı gerçek değil, audit başlangıcında yeniden doğrulanacak risk hipotezleridir:

1. `tests/live_test/test_page_audit.py`, `runtime/live-test/page_audit.py` dosyasını yüklemeyi bekliyor. Audit başladığında helper dosyasının varlığı ilk olarak kontrol edilmelidir; yoksa live route coverage `BLOCKED` ve test-harness drift'i `P1/P2` etkisine göre sınıflandırılmalıdır.
2. Route sayısı eski raporlardan alınmamalı; `apps/refine_control_plane/src/app/**/page.tsx` envanteri ile audit sonucu her çalıştırmada uzlaştırılmalıdır.
3. Mevcut Playwright config yalnızca Chromium projesi tanımlıyorsa Firefox/WebKit coverage otomatik PASS sayılamaz.
4. Mock kullanan Playwright testleri component/contract kanıtıdır; canlı backend route auditinin yerine geçmez.
5. PostgreSQL recovered/preserved state üzerinde `RUN_DB_MIGRATIONS=true`, migration reconciliation ve backup/restore kanıtı olmadan açılmamalıdır.
6. Telegram container'ın çalışması tek başına live integration kanıtı değildir; izinli auditte controlled send ve webhook negative test gereklidir.
7. `200 OK` health sonucu DB/Redis/worker/queue/proxy ve gerçek kullanıcı iş akışı doğrulanmadan bütün sistem PASS anlamına gelmez.
8. Çok kirli worktree veya generated cache silinmiş görünüyorsa audit kendi değişikliklerini kullanıcı değişikliklerinden kesin olarak ayırmalıdır.
