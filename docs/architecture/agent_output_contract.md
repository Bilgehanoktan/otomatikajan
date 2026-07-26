# Agent Output Contract

Bu sözleşme OtomatikAjan sistemindeki tüm ajanların üretmesi gereken standart çıktı formatını tanımlar.

## Amaç

Ajan çıktılarının denetlenebilir, test edilebilir, risk seviyesi belirlenebilir ve GitHub PR akışına dönüştürülebilir olmasını sağlamak.

## Zorunlu Alanlar

Her ajan çıktısı aşağıdaki bilgileri taşımalıdır:

```json
{
  "agent": "backend_dev",
  "task_id": "task-123",
  "summary": "Health endpoint kapsamı genişletildi.",
  "intent": "code_change",
  "risk": "low",
  "needs_human_approval": false,
  "files_to_change": [
    "apps/public_api/main.py",
    "tests/test_health.py"
  ],
  "proposed_changes": [
    {
      "path": "apps/public_api/main.py",
      "change_type": "modify",
      "reason": "DB ve Redis health kontrolü eklenecek."
    }
  ],
  "tests": [
    "pytest tests/test_health.py -v"
  ],
  "rollback_plan": "Endpoint değişikliği geri alınabilir; migration yok.",
  "evidence": [],
  "blocked_by": []
}
```

## Alan Açıklamaları

| Alan | Zorunlu | Açıklama |
|---|---:|---|
| `agent` | Evet | Çıktıyı üreten ajan adı. |
| `task_id` | Evet | İş veya issue referansı. |
| `summary` | Evet | Kısa değişiklik özeti. |
| `intent` | Evet | `analysis`, `code_change`, `test`, `docs`, `ops`, `security`, `release`. |
| `risk` | Evet | `low`, `medium`, `high`, `critical`. |
| `needs_human_approval` | Evet | İnsan onayı gerekip gerekmediği. |
| `files_to_change` | Evet | Etkilenecek dosya listesi. |
| `proposed_changes` | Evet | Dosya bazlı değişiklik gerekçesi. |
| `tests` | Evet | Çalıştırılacak testler. |
| `rollback_plan` | Evet | Geri alma yaklaşımı. |
| `evidence` | Hayır | Test, log, workflow veya belge linkleri. |
| `blocked_by` | Hayır | Eksik bilgi veya bağımlılıklar. |

## Risk Kuralları

### Low

- Doküman değişikliği.
- Test ekleme.
- Lokal-only yardımcı script.
- Production davranışını etkilemeyen refactor.

Aksiyon: Ajan PR açabilir.

### Medium

- API davranışı değişir.
- Yeni endpoint eklenir.
- Worker veya queue davranışı etkilenir.

Aksiyon: Ajan PR açabilir, insan review gerekir.

### High

- Auth, yetki, deployment, migration veya self-healing davranışı etkilenir.

Aksiyon: Ajan sadece PR taslağı veya öneri üretir, insan onayı şarttır.

### Critical

- Secret değişimi.
- Production veri etkisi.
- Kullanıcı verisi silme.
- Production deploy/rollback.
- Yetki yükseltme.

Aksiyon: Otomasyon durur, insan onayı olmadan işlem yapılmaz.

## ReviewerAgent Kabul Kriterleri

ReviewerAgent aşağıdaki durumlarda çıktıyı reddetmelidir:

- `risk` alanı yoksa.
- `rollback_plan` boşsa.
- Production etkisi olup `needs_human_approval=false` ise.
- Test listesi yoksa ve değişiklik kod değişikliği içeriyorsa.
- Secret veya canlı veri etkisi belirsizse.
- Değiştirilecek dosyalar belirtilmemişse.

## GitHub PR Açıklama Standardı

Ajan PR oluşturduğunda açıklama şu formatta olmalıdır:

```md
## Summary

## Changed Files

## Tests

## Risk
low / medium / high / critical

## Human Approval
Required / Not required

## Rollback Plan

## Evidence
```

## Güvenlik İlkesi

Hiçbir ajan aşağıdaki işlemleri doğrudan uygulayamaz:

- Production deploy.
- Production rollback.
- Secret değiştirme.
- Canlı DB migration uygulama.
- Kullanıcı verisi silme.
- Manuel onay olmadan merge.
