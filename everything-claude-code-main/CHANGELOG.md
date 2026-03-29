# Changelog
## 1.9.9 (DeerFlow 4.0.0-RC1.4) - 2026-03-29

### GStack Integration Polish
- **Core Integration**: Anthropic Claude-3.5-Sonnet (v3) API anahtarı sisteme güvenli bir şekilde entegre edildi. 
- **Start-up Modernization**: `baslat.bat` süreci optimize edildi, Docker build aşamasındaki `.env` bağımlılık hataları giderildi.
- **Environment Hydration**: Eksik olan DeerFlow Bridge yapılandırmaları ve güvenlik (JWT/Admin) anahtarları otomatik olarak oluşturuldu.

## 1.9.8 (DeerFlow 4.0.0-RC1.3) - 2026-03-29

### Phase 12.1 Architecture Hardening & Contract Testing
- **Monitoring Decoupling**: `job_queue` metrikleri orkestratörden bağımsızlaştırıldı; servis kesintilerinde bile dashboard üzerinden izlenebilirlik sağlandı.
- **Explicit Capabilities**: Dashboard'un kuyruk yeteneklerini (cancel/pause) arka uçtan teyit alarak dinamik göstermesi sağlandı, "Honest UI" prensibi güçlendirildi.
- **Redis-Based Debate Persistence**: Ajanlar arası tartışma (debate) state'i Redis üzerine taşınarak (`faz12:active_debates`) sistem restartlarında veri kaybı önlendi.
- **Contract Testing Execution**: Mimari bütünlüğü korumak için 7 yeni sözleşme testi (monitoring, dashboard, queue backend, import hygiene, env hygienevb.) implemente edildi ve doğrulandı.
- **Production-Grade Verifier**: `PatchVerifier` geçici sandbox dizinlerinde gerçek dosya doğrulama yapacak şekilde modernize edildi.
- **Repository Hygiene**: Gereksiz cache (`__pycache__`, `.pytest_cache`) ve hassas env dosyaları temizlendi, `.gitignore` üretim standartlarına güncellendi.

## 1.9.7 (DeerFlow 4.0.0-RC1.2) - 2026-03-29

### Repair Center Visibility & Stabilization
- **Visibility Hardening**: "Invalid Date" hatası giderildi, `first_seen_at` alanı dashboard ile senkronize edildi.
- **API Response Normalization**: Dashboard'un beklediği `active_jobs` ve `open_incidents` anahtarları API root seviyesine taşındı.
- **Case-Insensitive Status**: Veritabanındaki 'open' vs 'OPEN' durum uyuşmazlıkları giderildi, `IncidentMemory` katmanında esnek arama implemente edildi.
- **Version Update**: Sistem sürümü **4.0.0-RC1.2** olarak güncellendi ve `prevention_plan.md` oluşturuldu.

## 1.9.6 - 2026-03-29

### Finance Dashboard & Operational Stabilization

- **Maliyet Kontrol Paneli**: Entegre "Maliyet Kontrolü" sayfası eklendi. Bütçe takibi, en maliyetli görevler ve 7 günlük harcama geçmişi artık dashboard üzerinden izlenebilir.
- **Enum Hardening**: Sistem genelindeki tüm durum (status) değerleri `UPPERCASE` (`PENDING`, `COMPLETED`, `ERROR`) olarak standardize edildi. Bu sayede SQLAlchemy `LookupError` hataları tamamen giderildi.
- **Repository Optimization**: `ProjectRepository` sınıfına `get_total_cost` metodu eklendi; `counts_by_status` metodu frontend uyumluluğu için haritalama (mapping) desteği ile güçlendirildi.
- **UI Görsel İyileştirme**: Dashboard sidebar'ına yeni ikonlarla "Maliyet Kontrolü" sekmesi eklendi; bütçe ilerleme çubuğu (progress bar) ve detaylı harcama tabloları implemente edildi.
- **Sistem Bütünlüğü**: Veritabanı şeması ve SQLAlchemy modelleri arasındaki `updated_at`, `cost_usd` ve `latency_s` sütun uyumsuzlukları giderilerek 500 hataları engellendi.

## 1.9.5 - 2026-03-29

### Skill Traceability & Persistence (Phase 12.1 Hardening)

- **Skill Execution Logs**: Implemented full database persistence for skill executions using a new `SkillExecutionLog` model and Alembic migration (`0007`).
- **Dashboard Traceability**: Integrated a stylish "Zekâ / Beceri İzlenebilirliği" (Skill Traceability) timeline into the task detail modal, providing transparent "Honest UI" for autonomous actions.
- **UI Resilience**: Fixed a critical `ReferenceError: tags is not defined` in `submitCreateTask` and improved the frontend's ability to handle tag-based task metadata.
- **Backend Optimization**: Decentralized skill logging into the `SkillRegistry.execute` method to ensure 100% audit coverage for all autonomous skill calls.
- **Regression Testing**: Verified the entire Skill Layer (32/32 tests) against the persistent database environment with 100% success.

## 1.9.4 - 2026-03-29

- **Skill Framework (Faz 12.1)**: Successfully implemented and verified a 5-layer modular skill framework:
    - `SkillRegistry` & `SkillRouter`: Dynamic recommendation engine for task-specific expertise.
    - `OptimizationSkillAdapter`: Intelligent context engineering for token-efficient agent prompts.
    - `DebuggingSkillAdapter`: Autonomous bridge to the proactive `repair_orchestrator`.
    - `FileSearchSkillAdapter`: Deep repository indexing with impact analysis integration.
    - `VaultMemorySkillAdapter`: Persistent structured markdown memory in `memory/vault/`.
    - `SkillCreatorSkillAdapter`: Automated drift detection and draft generation for new skills.
- **Verification Suite**: 100% pass rate across Unit, API, Core, and End-to-End workflow tests for all skill adapters.
- **Engine Hardening**: Eliminated `MultipleResultsFound` database errors in CEO Oversight and Agent routing by enforcing deterministic First-Match policies.
- **Quality Scorer (Phase 4)**: Enriched the `QualityScorer` with 25+ new architectural and agentic keywords for more precise peer evaluation.

## 1.9.3 - 2026-03-29

### Operational Stability & Hardening (Phase 12.1 Final)

- **Unified Quality Gates**: Centralized `QUALITY_PASS_THRESHOLD` in `config.py` and increased the standard to `0.85` for more rigorous autonomous revisions.
- **Database Resilience**: Fixed `ConnectionRefusedError` for background tasks in Docker by making `config.py` Docker-aware (auto-resolving `127.0.0.1` to `db`).
- **Engine Stability**: Resolved `NameError` for `ProjectTask` in `core/orchestrator.py` during runtime task lists.
- **Security Posture**: Enhanced `Production Security Gate` with detailed rejection reasons and refined template matching.
- **Self-Healing Connectivity**: Optimized `db/session.py` with `pool_pre_ping` and improved retry handling for multi-container deployments.

## 1.9.2 - 2026-03-29

### Phase 12.1 System Hardening

- **Hybrid Health Engine**: Implemented weighted scoring and latency-aware health monitoring in `heal_engine.py`.
- **Intelligent Routing**: Added keyword-based pre-routing and few-shot examples to `task_routing.py` for faster, more accurate task assignment.
- **ECC2 Officialization**: Moved `experimental/ecc2` to the root `ecc2/` directory and updated all internal and CI references.
- **Metadata Sync**: Re-synchronized all version fields to `1.9.2`.

## 1.9.1 - 2026-03-29

### Audit & Stability (Phase 12.1 Patch)

- **Metadata Sync**: Re-synchronized all version strings to `1.9.0` (unified package.json, index.ts, and root VERSION file).
- **Test Stability**: Refactored `hooks.test.js` to eliminate `bash -lc` environment leakage, ensuring `HOME` directory isolation during tests.
- **ECC2 Integration**: Fully integrated the `experimental/ecc2` Rust subproject:
    - Added to `files` array for proper distribution.
    - Added automated Rust test/build jobs to `.github/workflows/ci.yml`.
    - Fixed path references in `package.json` scripts.
- **UI Modernization (DeerFlow)**: Standardized task creation modal with premium glassmorphism, internal iconography, and technical field optimizations (spellcheck/rows).

## 1.9.0 - 2026-03-20

### Highlights

- Selective install architecture with manifest-driven pipeline and SQLite state store.
- Language coverage expanded to 10+ ecosystems with 6 new agents and language-specific rules.
- Observer reliability hardened with memory throttling, sandbox fixes, and 5-layer loop guard.
- Self-improving skills foundation with skill evolution and session adapters.

### New Agents

- `typescript-reviewer` — TypeScript/JavaScript code review specialist (#647)
- `pytorch-build-resolver` — PyTorch runtime, CUDA, and training error resolution (#549)
- `java-build-resolver` — Maven/Gradle build error resolution (#538)
- `java-reviewer` — Java and Spring Boot code review (#528)
- `kotlin-reviewer` — Kotlin/Android/KMP code review (#309)
- `kotlin-build-resolver` — Kotlin/Gradle build errors (#309)
- `rust-reviewer` — Rust code review (#523)
- `rust-build-resolver` — Rust build error resolution (#523)
- `docs-lookup` — Documentation and API reference research (#529)

### New Skills

- `pytorch-patterns` — PyTorch deep learning workflows (#550)
- `documentation-lookup` — API reference and library doc research (#529)
- `bun-runtime` — Bun runtime patterns (#529)
- `nextjs-turbopack` — Next.js Turbopack workflows (#529)
- `mcp-server-patterns` — MCP server design patterns (#531)
- `data-scraper-agent` — AI-powered public data collection (#503)
- `team-builder` — Team composition skill (#501)
- `ai-regression-testing` — AI regression test workflows (#433)
- `claude-devfleet` — Multi-agent orchestration (#505)
- `blueprint` — Multi-session construction planning
- `everything-claude-code` — Self-referential ECC skill (#335)
- `prompt-optimizer` — Prompt optimization skill (#418)
- 8 Evos operational domain skills (#290)
- 3 Laravel skills (#420)
- VideoDB skills (#301)

### New Commands

- `/docs` — Documentation lookup (#530)
- `/aside` — Side conversation (#407)
- `/prompt-optimize` — Prompt optimization (#418)
- `/resume-session`, `/save-session` — Session management
- `learn-eval` improvements with checklist-based holistic verdict

### New Rules

- Java language rules (#645)
- PHP rule pack (#389)
- Perl language rules and skills (patterns, security, testing)
- Kotlin/Android/KMP rules (#309)
- C++ language support (#539)
- Rust language support (#523)

### Infrastructure

- Selective install architecture with manifest resolution (`install-plan.js`, `install-apply.js`) (#509, #512)
- SQLite state store with query CLI for tracking installed components (#510)
- Session adapters for structured session recording (#511)
- Skill evolution foundation for self-improving skills (#514)
- Orchestration harness with deterministic scoring (#524)
- Catalog count enforcement in CI (#525)
- Install manifest validation for all 109 skills (#537)
- PowerShell installer wrapper (#532)
- Antigravity IDE support via `--target antigravity` flag (#332)
- Codex CLI customization scripts (#336)

### Bug Fixes

- Resolved 19 CI test failures across 6 files (#519)
- Fixed 8 test failures in install pipeline, orchestrator, and repair (#564)
- Observer memory explosion with throttling, re-entrancy guard, and tail sampling (#536)
- Observer sandbox access fix for Haiku invocation (#661)
- Worktree project ID mismatch fix (#665)
- Observer lazy-start logic (#508)
- Observer 5-layer loop prevention guard (#399)
- Hook portability and Windows .cmd support
- Biome hook optimization — eliminated npx overhead (#359)
- InsAIts security hook made opt-in (#370)
- Windows spawnSync export fix (#431)
- UTF-8 encoding fix for instinct CLI (#353)
- Secret scrubbing in hooks (#348)

### Translations

- Korean (ko-KR) translation — README, agents, commands, skills, rules (#392)
- Chinese (zh-CN) documentation sync (#428)

### Credits

- @ymdvsymd — observer sandbox and worktree fixes
- @pythonstrup — biome hook optimization
- @Nomadu27 — InsAIts security hook
- @hahmee — Korean translation
- @zdocapp — Chinese translation sync
- @cookiee339 — Kotlin ecosystem
- @pangerlkr — CI workflow fixes
- @0xrohitgarg — VideoDB skills
- @nocodemf — Evos operational skills
- @swarnika-cmd — community contributions

## 1.8.0 - 2026-03-04

### Highlights

- Harness-first release focused on reliability, eval discipline, and autonomous loop operations.
- Hook runtime now supports profile-based control and targeted hook disabling.
- NanoClaw v2 adds model routing, skill hot-load, branching, search, compaction, export, and metrics.

### Core

- Added new commands: `/harness-audit`, `/loop-start`, `/loop-status`, `/quality-gate`, `/model-route`.
- Added new skills:
  - `agent-harness-construction`
  - `agentic-engineering`
  - `ralphinho-rfc-pipeline`
  - `ai-first-engineering`
  - `enterprise-agent-ops`
  - `nanoclaw-repl`
  - `continuous-agent-loop`
- Added new agents:
  - `harness-optimizer`
  - `loop-operator`

### Hook Reliability

- Fixed SessionStart root resolution with robust fallback search.
- Moved session summary persistence to `Stop` where transcript payload is available.
- Added quality-gate and cost-tracker hooks.
- Replaced fragile inline hook one-liners with dedicated script files.
- Added `ECC_HOOK_PROFILE` and `ECC_DISABLED_HOOKS` controls.

### Cross-Platform

- Improved Windows-safe path handling in doc warning logic.
- Hardened observer loop behavior to avoid non-interactive hangs.

### Notes

- `autonomous-loops` is kept as a compatibility alias for one release; `continuous-agent-loop` is the canonical name.

### Credits

- inspired by [zarazhangrui](https://github.com/zarazhangrui)
- homunculus-inspired by [humanplane](https://github.com/humanplane)
