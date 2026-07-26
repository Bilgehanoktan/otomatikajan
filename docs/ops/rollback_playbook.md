# Rollback Playbook

Bu playbook OtomatikAjan deployment veya migration hatalarında son stabil duruma dönüş için kullanılır.

## Rollback Tetikleme Kriterleri

- `/health` başarısız.
- API veya worker restart döngüsünde.
- Auth veya temel task akışı çalışmıyor.
- Migration sonrası sistem açılmıyor.
- Error rate kabul edilebilir seviyenin üstünde.
- Production veri etkisi beklenmeyen şekilde oluştu.
- Secret veya güvenlik ihlali şüphesi var.

## Ön Hazırlık

Rollback öncesi şu bilgiler toplanır:

- Hatalı commit veya release tag.
- Son başarılı release tag.
- Migration uygulanıp uygulanmadığı.
- Log çıktıları.
- CI ve deploy workflow sonucu.
- Kullanıcı etkisi.

## Uygulama Rollback

Son stabil tag'e dönme örneği:

```bash
git checkout otomatikajan-vX.Y.Z
docker compose build app
docker compose up -d app
```

Production ortamında bu işlem doğrudan sunucu politikası veya GitHub Actions rollback workflow'u üzerinden yapılmalıdır.

## Database Rollback

Migration etkisi varsa önce veri kaybı riski değerlendirilir.

Güvenli downgrade varsa:

```bash
alembic downgrade -1
```

Güvenli downgrade yoksa:

- Eski kod yeni schema ile uyumlu hale getirilir.
- Hotfix PR açılır.
- Veri kaybı riski varsa manuel onay alınır.

## Smoke Test

Rollback sonrası minimum doğrulama:

```bash
curl -f http://localhost:8000/health
curl -f http://localhost:8000/docs
```

Full-stack doğrulama:

```bash
docker compose --profile full-stack ps
docker compose --profile full-stack logs --tail=100 app worker beat
```

## Rollback Evidence

`docs/evidence/` altında şu formatla kayıt tutulur:

```md
# Rollback Evidence

Date:
Environment:
Failed commit/tag:
Rollback target:
Operator:
Related issue/PR:

## Reason

## Actions

## Verification
- Health:
- Smoke:
- Logs:

## Result
Recovered / Partially recovered / Failed
```

## Kalıcı Aksiyon

Rollback sonrası mutlaka issue açılır:

- Kök neden.
- Eksik test.
- Eksik CI kalite kapısı.
- Eksik runbook adımı.
- Tekrarı önleyici aksiyon.

Rollback sistemi ayağa kaldırmak içindir. Kalıcı çözüm ayrı PR ile yapılmalıdır.
