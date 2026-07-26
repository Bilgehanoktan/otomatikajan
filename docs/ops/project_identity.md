# Project Identity

Bu doküman OtomatikAjan reposunun ürün kimliğini ve ana çalışma branch'ini tanımlar.

## Karar

```text
Product name: OtomatikAjan
Repository: Bilgehanoktan/otomatikajan
Primary working branch: codex/project-factory-policy-governance
Target autonomy level: L4.5 — staging'e kadar otonom, production'da insan onaylı
```

## İsimlendirme Kararı

Bu repo için ana ürün adı **OtomatikAjan** olarak kabul edilir.

BilgeAPI, bu repo içinde ayrı çalışan incident intake, diagnostic lifecycle ve repair request governance API bileşenidir. BilgeAPI ana ürün adı değildir; OtomatikAjan'ın operasyonel alt servisi olarak ele alınır.

## Kapsam

OtomatikAjan şu alanları kapsar:

- Çoklu ajan orkestrasyonu.
- Task intake ve GitHub issue işleme.
- Agent output contract.
- QualityScorer ve ReviewerAgent kontrolü.
- GitHub issue-to-PR otomasyonu.
- CI kalite kapıları.
- Controlled deployment.
- Self-healing ve incident response.
- Governance, safe mode ve kill-switch.

## Kapsam Dışı

Bu proje şu anda tam kontrolsüz production otonomisini hedeflemez.

Yasaklı veya insan onayı gerektiren alanlar:

- Production deploy.
- Production rollback.
- Secret değişikliği.
- Canlı DB migration uygulama.
- Kullanıcı verisi silme.
- Yetki yükseltme.
- Manuel onay olmadan PR merge.

## Doküman Kaynakları

- `README.md`
- `docs/ops/autonomous_phase_plan.md`
- `docs/ops/governance_policy.md`
- `docs/architecture/agent_output_contract.md`
