# Sovereign AGI Project — Agent Instructions & Governance

Bu dosya, bu repoda çalışan tüm yapay zeka ajanları için ortak talimatları, yönetim kurallarını ve çalışma prensiplerini içerir.

## Temel Prensipler

1.  **Önce Planla (Plan Before Execute)**: Karmaşık özellikler veya hata düzeltmeleri öncesinde mutlaka bir uygulama planı (`implementation_plan.md`) oluşturun.
2.  **Test Odaklı Geliştirme (TDD)**: Kod yazmadan önce testleri yazın. Minimum %80 kapsayıcı (coverage) hedeflenir.
3.  **Güvenlik Önceliği (Security-First)**: Hardcoded sır (secret) bırakmayın, girdi doğrulaması yapın ve SQL/XSS açıklarına karşı tetikte olun.
4.  **İzlenebilirlik (Traceability)**: Yapılan her işlem `EpisodeRecord` ve `ActionRecord` olarak kaydedilmeli, nedensellik bağları kurulmalıdır.

## Kullanılabilir Ajan Rolleri (Harness Profile)

| Rol | Amaç | Kullanım Durumu |
| :--- | :--- | :--- |
| **explorer** | Salt-okunur keşif | Kod tabanını anlama, mimari analiz |
| **reviewer** | Doğruluk ve güvenlik kontrolü | Kod değişikliği sonrası, PR öncesi |
| **docs_researcher** | API ve döküman araştırması | Harici kütüphane veya iç API kullanımı |
| **specialist** | Belirli bir skill setine odaklı ajan | TDD, Backend, Frontend vb. özel işler |

## Skill Kataloğu (Portable Skills)

Aşağıdaki çekirdek yetenekler `.agents/skills/` altında tanımlanmıştır ve görev bağlamına göre dinamik olarak seçilir:

- `coding-standards`: Proje genelinde temiz kod standartları.
- `tdd-workflow`: Test-first çalışma döngüsü.
- `verification-loop`: Çıktı doğrulama ve döngüsel iyileştirme.
- `security-review`: Güvenlik açığı taraması ve incelemesi.
- `documentation-lookup`: API ve kütüphane dökümanlarında hızlı arama.
- `api-design`: Tutarlı API sözleşmeleri oluşturma.
- `backend-patterns`: Python/FastAPI ve servis mimarisi desenleri.
- `frontend-patterns`: React/Next.js ve UI/UX standartları.
- `mcp-server-patterns`: Model Context Protocol sunucu geliştirme kuralları.
- `deep-research`: İteratif veri toplama ve analiz deseni.
- `e2e-testing`: Playwright E2E testleri, Page Object Model, CI artifact ve flaky test stratejileri.
- `eval-harness`: Ajan/otomasyon çıktıları için eval-driven development, pass/fail kriterleri ve regresyon kontrolleri.
- `nextjs-turbopack`: Next.js/Turbopack geliştirme, cache, HMR ve webpack fallback kararları.

## Geliştirme Akışı

1.  **Keşif**: Mevcut yapıyı anla (`explorer`).
2.  **Planlama**: Yapılacak işi bölümlere ayır ve plan oluştur.
3.  **Uygulama**: TDD prensipleriyle kodu yaz (`specialist`).
4.  **Doğrulama**: Kod kalitesini ve güvenliğini kontrol et (`reviewer`).
5.  **Öğrenme**: Başarılı/başarısız sonuçları `learning_orchestrator`'a bildir.

## Git ve İletişim

- **Commit Formatı**: `type: description` (feat, fix, refactor, docs, test, chore).
- **PR Özetleri**: Yapılan değişiklikleri, test planını ve riskleri içermelidir.
