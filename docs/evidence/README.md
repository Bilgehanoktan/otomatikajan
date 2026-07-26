# Evidence Standard

Bu klasör OtomatikAjan için test, release, deployment, rollback, security ve incident kanıtlarını saklamak için kullanılır.

## Amaç

Her kritik teknik kararın ve production etkili değişikliğin kanıtlı şekilde izlenmesini sağlamak.

## Kanıt Türleri

- CI çıktısı
- Test sonucu
- Lint sonucu
- Security scan sonucu
- Docker build sonucu
- Smoke test sonucu
- Deployment sonucu
- Rollback sonucu
- Migration sonucu
- Incident analiz sonucu
- Agent decision audit özeti

## Dosya İsimlendirme

```text
YYYY-MM-DD_ci_evidence.md
YYYY-MM-DD_staging_deployment.md
YYYY-MM-DD_production_deployment.md
YYYY-MM-DD_rollback_<short_reason>.md
YYYY-MM-DD_incident_<sev>_<short_reason>.md
YYYY-MM-DD_agent_decision_<issue_or_task>.md
```

## Standart Şablon

```md
# Evidence

Date:
Environment:
Commit/Tag:
Operator:
Related issue/PR:

## Checks
- CI:
- Tests:
- Lint:
- Security:
- Docker build:
- Migration:
- Smoke test:
- Health:

## Agent Decision
- Agent:
- Risk:
- Human approval:
- Rollback plan:

## Result
Successful / Failed / Rolled back / Needs review

## Notes

## Raw Output / Links
```

## Minimum Kural

- Production release evidence olmadan tamamlanmış kabul edilmez.
- Migration içeren PR rollback değerlendirmesi olmadan merge edilmez.
- High veya critical riskli ajan çıktısı human approval kaydı olmadan uygulanmaz.
