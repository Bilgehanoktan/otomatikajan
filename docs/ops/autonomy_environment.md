# Autonomy Environment Controls

Bu doküman OtomatikAjan'ın otonomi ve güvenlik modları için kullanılacak environment değişkenlerini tanımlar.

## Amaç

Otonom davranışı kod, CI, staging ve production ortamlarında merkezi şekilde kontrol etmek.

## Önerilen Değişkenler

```env
AUTONOMY_MODE=supervised
AUTONOMY_SAFE_MODE=false
AUTONOMY_REQUIRE_HUMAN_APPROVAL_FOR_PRODUCTION=true
AUTONOMY_ALLOW_PRODUCTION_DEPLOY=false
AUTONOMY_ALLOW_PRODUCTION_ROLLBACK=false
AUTONOMY_ALLOW_DB_MIGRATION=false
AUTONOMY_ALLOW_USER_DATA_DELETION=false
AUTONOMY_ALLOW_PR_MERGE=false
AUTONOMY_MAX_AUTO_RISK=medium
AUTONOMY_AUDIT_ENABLED=true
```

## AUTONOMY_MODE

| Değer | Davranış |
|---|---|
| `supervised` | Ajanlar policy sınırları içinde analiz, issue, branch ve PR hazırlayabilir. |
| `read_only` | Kill-switch modu. Ajanlar sadece okuma, analiz ve issue açma yapabilir. |
| `disabled` | Otonom ajan aksiyonları kapalıdır. |

## Safe Mode

`AUTONOMY_SAFE_MODE=true` olduğunda sistem yeni otomatik aksiyonları durdurur ve yalnızca analiz/evidence/incident akışına izin verir.

Tetikleyiciler:

- CI üst üste başarısız.
- Health check kritik hata üretir.
- Ajan çıktısı sözleşme dışına çıkar.
- Risk seviyesi belirlenemez.
- Production etkisi belirsizdir.

## Production Kısıtları

Production için varsayılan davranış:

```env
AUTONOMY_REQUIRE_HUMAN_APPROVAL_FOR_PRODUCTION=true
AUTONOMY_ALLOW_PRODUCTION_DEPLOY=false
AUTONOMY_ALLOW_PRODUCTION_ROLLBACK=false
```

Bu değerler production deploy/rollback aksiyonlarını insan onayına bağlar.

## Risk Sınırı

```env
AUTONOMY_MAX_AUTO_RISK=medium
```

Bu ayar, otomasyonun en fazla hangi risk seviyesinde PR veya staging aksiyonu hazırlayabileceğini belirtir.

Önerilen davranış:

| Risk | Otomatik Aksiyon |
|---|---|
| low | PR hazırlayabilir |
| medium | PR hazırlayabilir, review gerekir |
| high | Sadece öneri/issue |
| critical | Otomasyon durur |

## Audit

```env
AUTONOMY_AUDIT_ENABLED=true
```

Bu değer açıkken ajan kararları, risk seviyesi, PR oluşturma, test sonucu ve onay ihtiyacı audit log'a yazılmalıdır.

## İlgili Dokümanlar

- `docs/ops/governance_policy.md`
- `docs/architecture/agent_output_contract.md`
- `docs/ops/incident_response.md`
