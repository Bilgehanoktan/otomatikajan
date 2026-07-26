# Controlled Deployment Runbook

Bu runbook OtomatikAjan sisteminin local, staging ve production deployment sürecini tanımlar.

## Ortamlar

### Local Dev

Amaç: Geliştirici doğrulaması.

```bash
make install
make dev
curl http://localhost:8000/health
```

### Minimal Docker

Amaç: API ve control plane temel çalışma doğrulaması.

```bash
docker compose up --build
curl http://localhost:8000/health
```

### Full-Stack Local

Amaç: DB, Redis, worker, beat ve DeerFlow dahil entegrasyon doğrulaması.

```bash
docker compose --profile full-stack up --build
curl http://localhost:8000/health
```

### Staging

Amaç: Production öncesi otomatik doğrulama.

Gerekli kontroller:

- CI başarılı.
- Docker image build başarılı.
- Migration etkisi değerlendirilmiş.
- Smoke test başarılı.
- Evidence kaydı oluşturulmuş.

### Production

Amaç: Canlı ortam.

Production değişiklikleri için insan onayı zorunludur.

## Deployment Öncesi Checklist

- [ ] İlgili issue veya PR var.
- [ ] CI yeşil.
- [ ] Security scan sonucu kabul edilebilir.
- [ ] Docker build başarılı.
- [ ] Migration varsa rollback planı var.
- [ ] `.env` veya secret değişikliği varsa manuel onay var.
- [ ] Smoke test komutu belli.
- [ ] Evidence dosyası hazırlanacak.

## Staging Akışı

```text
Merge veya release candidate oluşturulur
↓
CI çalışır
↓
Docker image build edilir
↓
Staging deploy tetiklenir
↓
Health check çalışır
↓
Smoke test çalışır
↓
Evidence kaydı oluşturulur
```

## Production Akışı

```text
Release tag oluşturulur
↓
Release check workflow çalıştırılır
↓
Staging sonucu doğrulanır
↓
Production approval beklenir
↓
Production deploy yapılır
↓
Production smoke test çalışır
↓
Evidence kaydı tamamlanır
```

## Release Tag Standardı

```text
otomatikajan-vX.Y.Z
```

Örnek:

```bash
git tag otomatikajan-v1.0.0
git push origin otomatikajan-v1.0.0
```

## Smoke Test Standardı

Minimum:

```bash
curl -f http://localhost:8000/health
curl -f http://localhost:8000/docs
```

Full-stack:

```bash
docker compose --profile full-stack ps
docker compose --profile full-stack logs --tail=100 app worker beat
```

## Başarısızlık Kriterleri

Aşağıdakilerden biri varsa deployment başarısız kabul edilir:

- `/health` başarısız.
- API container restart döngüsüne giriyor.
- Auth çalışmıyor.
- Worker queue tüketmiyor.
- Migration sonrası API açılmıyor.
- Error rate belirgin yükseliyor.
- Security kritik bulgu oluşuyor.

Bu durumda `docs/ops/rollback_playbook.md` uygulanır.

## Evidence Formatı

Her deployment için `docs/evidence/` altında kayıt tutulur.

```md
# Deployment Evidence

Date:
Environment:
Commit/Tag:
Operator:
Related issue/PR:

## Checks
- CI:
- Security:
- Docker build:
- Migration:
- Smoke test:
- Health:

## Result
Successful / Failed / Rolled back

## Notes
```
