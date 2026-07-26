# OtomatikAjan Tam Otonom Uygulama Faz Planı

Bu doküman `Bilgehanoktan/otomatikajan` reposunun `codex/project-factory-policy-governance` branch'i için uygulanacak tam otonom dönüşüm fazlarını tanımlar.

## Hedef Mimari

Sistem hedefte şu akışla çalışacaktır:

```text
Kullanıcı veya GitHub issue görev oluşturur
↓
Task intake görevi sınıflandırır
↓
Orchestrator işi ajanlara böler
↓
Ajanlar kod, test, doküman veya operasyon çıktısı üretir
↓
QualityScorer ve ReviewerAgent çıktıyı kontrol eder
↓
Düşük riskli işler için branch/PR hazırlanır
↓
CI kalite kapıları çalışır
↓
Staging'e kadar otomasyon ilerler
↓
Production için insan onayı gerekir
↓
SelfHealEngine ve observability sistemi çalışma durumunu izler
```

## Faz 0 — Repo Kimliği ve Stabilizasyon

Amaç: Repo tek bir ürün gibi yönetilsin.

Yapılacaklar:

- [ ] Proje adı standardı seç: `OtomatikAjan` veya `BilgeAPI`.
- [ ] README içindeki `your-org/ai-yazilim-sirketi` örnekleri gerçek repo adıyla değiştir.
- [ ] Branch stratejisi tanımla: `main`, `develop`, `codex/project-factory-policy-governance`, `release/*`, `fix/*`.
- [ ] Secret ve `.env` dosyalarının repo dışında kaldığını doğrula.
- [ ] Eski veya çakışan dokümanları işaretle.

Çıkış kriteri:

- Repo adı, branch ve ürün kimliği net.
- README güncel.
- CI bu branch üzerinde çalışıyor.

## Faz 1 — Lokal ve Full-Stack Çalışırlık

Amaç: Sistem tek komutla lokal ve full-stack modda kalksın.

Yapılacaklar:

- [ ] `make install` çalışır.
- [ ] `make dev` ile API kalkar.
- [ ] `docker compose up --build` minimal modda kalkar.
- [ ] `docker compose --profile full-stack up --build` ile DB, Redis, worker, beat, DeerFlow kalkar.
- [ ] `/health` ve `/docs` doğrulanır.
- [ ] `scripts/smoke_local_dev.ps1` standart smoke test olarak korunur.

Çıkış kriteri:

- Local dev, minimal Docker ve full-stack Docker için smoke test başarılı.

## Faz 2 — Production Readiness

Amaç: Sistem production'a çıkabilecek kalite kapılarına sahip olsun.

Yapılacaklar:

- [ ] CI; lint, security, test, UI test, frontend build ve Docker build çalıştırır.
- [ ] Security high/critical çıktıları issue'ya dönüştürülür.
- [ ] `.env.example` production ihtiyaçlarını açıkça listeler.
- [ ] Migration policy yazılır.
- [ ] Deployment ve rollback runbook eklenir.
- [ ] Evidence kayıt standardı eklenir.

Çıkış kriteri:

- CI yeşil olmadan merge yapılmaz.
- Docker image build edilir.
- Rollback planı olmayan migration production'a çıkamaz.

## Faz 3 — Agent Output Contract

Amaç: Ajan çıktıları rastgele metin değil, denetlenebilir sözleşme formatı olsun.

Yapılacaklar:

- [ ] Agent output JSON schema tanımlanır.
- [ ] Her ajan dosya etkisi, test etkisi, risk ve onay ihtiyacı bildirir.
- [ ] QualityScorer bu alanları kontrol eder.
- [ ] ReviewerAgent eksik veya riskli çıktıyı reddeder.

Çıkış kriteri:

- Her ajan çıktısı `docs/architecture/agent_output_contract.md` sözleşmesine uyar.

## Faz 4 — GitHub Issue to PR Otomasyonu

Amaç: Sistem GitHub issue okuyup güvenli PR hazırlayabilsin.

Yapılacaklar:

- [ ] Issue sınıflandırıcı: bug, feature, docs, ops, security.
- [ ] Task decomposition servisi.
- [ ] GitHub branch oluşturma akışı.
- [ ] Dosya değişikliği önerisi.
- [ ] Test çalıştırma ve sonucu PR açıklamasına ekleme.
- [ ] PR risk ve rollback notu ekleme.

Çıkış kriteri:

- Bir issue için otomatik branch ve PR taslağı üretilebilir.
- Production etkili PR'lar insan onayı olmadan merge edilemez.

## Faz 5 — Controlled Deployment

Amaç: Staging'e kadar otomatik, production'da insan onaylı deployment.

Yapılacaklar:

- [ ] Release tag standardı: `otomatikajan-vX.Y.Z`.
- [ ] `release-check.yml` workflow'u kullanılır.
- [ ] GitHub Environments: `staging`, `production`.
- [ ] Production environment manuel approval ister.
- [ ] Deployment sonrası smoke test ve evidence kaydı zorunlu olur.

Çıkış kriteri:

- Staging otomatik doğrulanır.
- Production manuel onay kapısına bağlıdır.

## Faz 6 — Observability and Self-Healing

Amaç: Sistem kendi sağlığını izler ve güvenli aksiyon alır.

Yapılacaklar:

- [ ] `/health` API, DB, Redis, Celery, DeerFlow durumunu raporlar.
- [ ] `/metrics` latency, error rate, task success ve queue depth üretir.
- [ ] Incident issue otomasyonu eklenir.
- [ ] Self-heal sadece güvenli aksiyonlarla sınırlandırılır.
- [ ] Her self-heal aksiyonu audit log'a yazılır.

Çıkış kriteri:

- Sistem hata olduğunda issue açabilir, log özetleyebilir ve öneri PR hazırlayabilir.

## Faz 7 — Governance, Policy and Kill-Switch

Amaç: Otonomluk kontrolsüz hale gelmesin.

Yapılacaklar:

- [ ] Agent permission matrix uygulanır.
- [ ] Human approval policy uygulanır.
- [ ] Production safety policy uygulanır.
- [ ] Kill-switch tanımlanır.
- [ ] Safe mode tanımlanır.
- [ ] Audit zorunluluğu tanımlanır.

Çıkış kriteri:

- Riskli aksiyonlarda otomasyon durur ve insan onayı ister.
- Kill-switch aktifken ajanlar sadece okuma, analiz ve issue oluşturma yapar.

## Hedef Seviye

Bu proje için hedef tam kontrolsüz otonomluk değildir. Hedef seviye:

```text
L4.5 — Staging'e kadar otonom, production'da insan onaylı.
```
