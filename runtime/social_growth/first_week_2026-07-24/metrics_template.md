# Instagram Ölçüm Şablonu

İlk dört kaliteli ana gönderinin medyanı hesap baseline'ı olacaktır. Sektör
benchmark'ı veya takipçi artış garantisi kullanılmaz.

| Post ID | Snapshot | Views | Accounts reached | Avg. watch time | Likes | Comments | Saves | Shares | Profile visits | Follows | Non-follower reach | Not |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `01_account_promise` | 24h | — | — | N/A | — | — | — | — | — | — | — | Bekleniyor |
| `01_account_promise` | 72h | — | — | N/A | — | — | — | — | — | — | — | Bekleniyor |
| `01_account_promise` | 7d | — | — | N/A | — | — | — | — | — | — | — | Bekleniyor |
| `02_claude_opus_5_copilot` | 24h | — | — | — | — | — | — | — | — | — | — | Bekleniyor |
| `02_claude_opus_5_copilot` | 72h | — | — | — | — | — | — | — | — | — | — | Bekleniyor |
| `02_claude_opus_5_copilot` | 7d | — | — | — | — | — | — | — | — | — | — | Bekleniyor |
| `03_gpt_5_6_models` | 24h | — | — | N/A | — | — | — | — | — | — | — | Bekleniyor |
| `03_gpt_5_6_models` | 72h | — | — | N/A | — | — | — | — | — | — | — | Bekleniyor |
| `03_gpt_5_6_models` | 7d | — | — | N/A | — | — | — | — | — | — | — | Bekleniyor |

## Formüller

- Engagement rate = `(likes + comments + saves + shares) / accounts_reached`
- Save + share rate = `(saves + shares) / accounts_reached`
- Profile-to-follow conversion = `follows / profile_visits`
- Reel retention = `average_watch_time / 25`

Payda `0` veya eksikse oran `unknown` kalır; sıfır uydurulmaz.

