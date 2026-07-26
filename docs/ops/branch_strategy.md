# Branch and Release Strategy

Bu doküman OtomatikAjan reposunda branch, PR ve release akışını tanımlar.

## Ana Branchler

| Branch | Amaç |
|---|---|
| `main` | Stabil ana hat. Production release için kaynak olabilir. |
| `develop` | Entegrasyon ve pre-release geliştirme hattı. |
| `codex/project-factory-policy-governance` | Otonom dönüşüm, governance, policy ve agentic workflow ana çalışma branch'i. |

## Çalışma Branch İsimleri

| Pattern | Kullanım |
|---|---|
| `phase0/*` | Repo kimliği ve stabilizasyon işleri |
| `phase1/*` | Local/full-stack çalışırlık işleri |
| `phase2/*` | Production readiness işleri |
| `phase3/*` | Agent output contract işleri |
| `phase4/*` | GitHub issue-to-PR otomasyonu |
| `phase5/*` | Controlled deployment ve release işleri |
| `phase6/*` | Observability ve self-healing işleri |
| `phase7/*` | Governance, policy ve kill-switch işleri |
| `fix/*` | Hata düzeltmeleri |
| `docs/*` | Dokümantasyon değişiklikleri |
| `release/*` | Release hazırlığı |

## PR Kuralları

Her PR şu bilgileri içermelidir:

- Summary.
- Changed files.
- Tests.
- Risk level.
- Human approval requirement.
- Rollback plan.
- Evidence link or note.

## Merge Kuralları

- CI yeşil olmadan merge yapılmaz.
- High veya critical riskli PR insan onayı olmadan merge edilmez.
- Migration içeren PR rollback değerlendirmesi olmadan merge edilmez.
- Production etkili PR için staging smoke test ve evidence gerekir.

## Release Tag Standardı

```text
otomatikajan-vX.Y.Z
```

Örnek:

```bash
git tag otomatikajan-v1.0.0
git push origin otomatikajan-v1.0.0
```

## Release Akışı

```text
PR merge
↓
CI başarılı
↓
Staging smoke
↓
Release tag
↓
release-check workflow
↓
Production approval
↓
Production deploy
↓
Production smoke
↓
Evidence kaydı
```

## Production Kısıtı

Production deploy ve rollback hiçbir durumda insan onayı olmadan yapılmaz.
