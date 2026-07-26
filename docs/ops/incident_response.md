# Incident Response Runbook

Bu runbook OtomatikAjan sisteminde oluşan hatalara müdahale için kullanılır.

## Incident Seviyeleri

### SEV-1 Critical

- Production tamamen erişilemez.
- Auth veya görev oluşturma tamamen bozuk.
- Veri kaybı veya security breach şüphesi var.
- Production deploy sonrası sistem açılmıyor.

Aksiyon:

- Otomasyon safe mode'a alınır.
- Production rollback değerlendirilir.
- İnsan onayı zorunludur.

### SEV-2 High

- Ana API akışlarından biri çalışmıyor.
- Worker queue birikiyor.
- Error rate ciddi yükseldi.
- Self-healing yanlış davranıyor.

Aksiyon:

- Incident issue açılır.
- Root cause analizi yapılır.
- Hotfix veya rollback değerlendirilir.

### SEV-3 Medium

- Kullanıcı etkisi sınırlı.
- Loglarda tekrar eden hata var.
- Monitoring veya evidence eksikliği var.

Aksiyon:

- Issue açılır.
- Sprint/faz backlog'una alınır.

### SEV-4 Low

- Dokümantasyon, uyarı veya küçük kalite eksikleri.

Aksiyon:

- Normal backlog.

## İlk Müdahale

1. Etki alanını belirle: API, UI, DB, Redis, Celery, DeerFlow, GitHub workflow.
2. Son değişikliği bul: commit, PR, release tag, migration.
3. Health kontrolü yap.
4. Logları al.
5. Risk seviyesini belirle.
6. Safe mode veya rollback gerekip gerekmediğine karar ver.

## Temel Komutlar

```bash
curl -f http://localhost:8000/health
curl -f http://localhost:8000/docs
docker compose ps
docker compose logs --tail=200 app
```

Full-stack:

```bash
docker compose --profile full-stack ps
docker compose --profile full-stack logs --tail=200 app worker beat redis db
```

## Incident Issue Formatı

```md
## Incident Level
SEV-1 / SEV-2 / SEV-3 / SEV-4

## Impact

## Timeline
- Detected:
- First action:
- Recovery:

## Suspected Cause

## Actions
- [ ] Temporary mitigation
- [ ] Root cause analysis
- [ ] Permanent fix
- [ ] Test added
- [ ] Runbook updated

## Evidence
```

## Self-Healing Sınırları

Self-healing insan onayı olmadan şunları yapabilir:

- Health kontrolü.
- Log özetleme.
- Incident issue açma.
- Staging smoke test tetikleme.
- Öneri PR hazırlama.

Self-healing insan onayı olmadan şunları yapamaz:

- Production deploy.
- Production rollback.
- Secret değiştirme.
- Database migration uygulama.
- Kullanıcı verisi silme.
- PR merge.

## Incident Sonrası Review

Her SEV-1 ve SEV-2 sonrası şu sorular cevaplanır:

- Bu hata CI'da yakalanabilir miydi?
- Smoke test kapsamı yeterli miydi?
- Rollback hızlı mıydı?
- Loglar kök nedeni bulmaya yetti mi?
- Aynı hatayı engellemek için hangi test veya monitor eklenecek?
