# AI Gücüm Social Growth Operator Runbook

## Durum

Bu modül resmi Meta Graph API için hazırlanmıştır. Password tabanlı `instagrapi`,
Playwright login, cookie/session replay ve rakip gönderilerine otomatik tanıtım yorumu
üretim yolu değildir.

Canlı dış etkiler varsayılan olarak kapalıdır. `SOCIAL_GROWTH_LIVE_ACTIONS_APPROVED=true`
olmadan doğrulanmış webhook olayları bile `BLOCKED` evidence üretir ve private reply
göndermez.

## Ön koşullar

- Instagram Professional hesabı
- Meta App ve Instagram webhook subscription
- Gerekli content publishing, comments/private reply ve insights permission'ları
- Herkese açık HTTPS webhook URL'si
- Redis
- Yayınlanacak medya için herkese açık HTTPS URL'leri

## Zorunlu environment değişkenleri

Secret değerleri komut satırına, source dosyasına veya loglara yazılmamalıdır.

```text
INSTAGRAM_ACCOUNT_ID
INSTAGRAM_ACCESS_TOKEN
META_APP_SECRET
META_WEBHOOK_VERIFY_TOKEN
META_API_VERSION
SOCIAL_GROWTH_REDIS_URL
SOCIAL_GROWTH_TRIGGER_LINKS_JSON
SOCIAL_GROWTH_PLANNER_API_KEY
```

İsteğe bağlı:

```text
META_GRAPH_BASE_URL
SOCIAL_GROWTH_EVIDENCE_PATH
SOCIAL_GROWTH_LIVE_ACTIONS_APPROVED
SOCIAL_GROWTH_REVIEW_PROVIDER
OPENAI_API_KEY
SOCIAL_GROWTH_OPENAI_MODEL
GEMINI_API_KEY
MINIMAX_API_KEY
```

Post audit komutu varsayılan olarak AI Company `ModelOrchestrator` içindeki `groq`
provider'ını kullanır; bu nedenle `GROQ_API_KEY` secret store veya process
environment üzerinden sağlanmalıdır. Farklı yapılandırılmış provider kullanılacaksa
adı `SOCIAL_GROWTH_REVIEW_PROVIDER` ile seçilebilir.

`SOCIAL_GROWTH_TRIGGER_LINKS_JSON`, yalnız gerçek ve erişilebilir HTTPS landing-page
linkleri içeren bir JSON nesnesi olmalıdır. Örnek yapı:

```json
{
  "PROMPT": "https://example.com/prompt-rehberi"
}
```

Webhook ingress, Redis üzerinde varsayılan 120 istek/dakika fixed-window limitine,
256 KiB body sınırına ve istek başına 100 event sınırına sahiptir. Meta retry trafiği
için farklı bir eşik gerekirse değişiklik test ve güvenlik incelemesinden geçmelidir.

## Başlatma

```powershell
py -3.13 -m uvicorn services.social_growth.app:create_app --factory --host 127.0.0.1 --port 8200
```

Kontrol yüzeyleri:

```text
GET  /health
GET  /api/v1/social-growth/webhook
POST /api/v1/social-growth/webhook
POST /api/v1/social-growth/content/plans
POST /api/v1/social-growth/content/creative-packages
POST /api/v1/social-growth/account-growth/plans
```

`POST /content/plans`, `X-Content-Orchestrator-Key` header'ını zorunlu tutar ve
istemci başına 30 istek/dakika Redis limiti uygular. Anahtar en az 32 karakter
olmalı ve yalnız secret store veya process environment üzerinden sağlanmalıdır.

Örnek dış etkisiz plan isteği:

```powershell
$headers = @{
  "X-Content-Orchestrator-Key" = $env:SOCIAL_GROWTH_PLANNER_API_KEY
}
$body = @{
  topic = "tek promptla ürün videosu"
  audience = "e-ticaret işletmeleri"
  mode = "lead"
  format = "reel"
  template = "one_prompt_demo"
  cta_mode = "keyword_dm"
  keyword = "VIDEO"
  routing_mode = "compare"
  claims = @()
} | ConvertTo-Json -Depth 5
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8200/api/v1/social-growth/content/plans" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $body
```

Yanıt her zaman `DRY_RUN` ve `external_actions_performed=false` taşır. `veo`,
`seedance`, `kling` ve `hailuo` seçimleri yapılandırılabilir rota etiketleridir;
bu endpoint sağlayıcı API'si çağırmaz ve Instagram'da paylaşım yapmaz.

`POST /content/creative-packages`, aynı korumalı request sözleşmesini OpenAI
Structured Outputs ile `CreativeDraft` haline getirir. `OPENAI_API_KEY` yoksa endpoint
`CREATIVE_PLANNER_NOT_CONFIGURED` ile `503` döner. Yerel `.env.local` kullanılacaksa
servis şu şekilde başlatılabilir; dosya Git tarafından ignore edilmelidir:

```powershell
py -3.13 -m uvicorn services.social_growth.app:create_app --factory `
  --host 127.0.0.1 --port 8200 --env-file .env.local
```

Başarılı yanıtın durumu `AWAITING_HUMAN_APPROVAL` olur. GPT çıktısı yalnız brief'te
verilen `source_urls` değerlerini kullanabilir; yeni URL eklerse istek
`BLOCKED_UNGROUNDED_CREATIVE` olur. Bu endpoint video üretmez ve paylaşım yapmaz.

`POST /account-growth/plans`, 12 hafta ve 36 ana gönderiden oluşan, 24h/72h/7d
ölçüm checkpoint'li `DRY_RUN` plan döndürür. Takipçi garantisi veya uydurma sektör
benchmark'ı içermez.

## Video provider yürütme katmanı

`ProviderExecutionRegistry` maliyetli provider çağrılarını HTTP'de doğrudan açmaz.
İç workflow, deterministik `plan_id` ile aynı `HumanApproval` kanıtını sağlamalıdır.
Onay yoksa `BLOCKED_HUMAN_APPROVAL_REQUIRED`, plan eşleşmiyorsa
`BLOCKED_APPROVAL_PLAN_MISMATCH` döner ve transport çağrılmaz.
Onay ayrıca `CreativeProductionPackage.artifact_hash` değerine bağlanır; GPT taslağı
onaydan sonra değişirse `BLOCKED_APPROVAL_ARTIFACT_MISMATCH` döner.

- `VeoVideoAdapter`: Gemini `veo-3.1-generate-preview` long-running görev sözleşmesi.
- `HailuoVideoAdapter`: `MiniMax-Hailuo-2.3` submit, query ve file metadata akışı.
- `Seedance` ve `Kling`: doğrulanmış operator API sözleşmesi eklenene kadar
  `BLOCKED_PROVIDER_NOT_CONFIGURED`.

Provider download URL yalnız metadata olarak döner; sistem dosyayı otomatik indirmez.
Instagram publish için ayrıca ayrı insan onayı ve Meta provider ID doğrulaması gerekir.
`GEMINI_API_KEY` veya `MINIMAX_API_KEY` mevcutsa ilgili adaptör yalnız internal
`app.state.video_provider_registry` yüzeyine kaydedilir; internetten çağrılabilen bir
video submit endpoint'i açılmaz.

Content publishing HTTP endpoint olarak bilerek açılmamıştır. Onaylı workflow,
`SocialGrowthService.plan_carousel()` sonucunu incelemeli; insan geçidinden sonra
`SocialGrowthService.publish_carousel()` çağrısını yapmalıdır.

## AI Company post audit

Son gönderiler secret içermeyen bir snapshot dosyasına alındıktan sonra projenin
kendi `reviewer` ajanı şu komutla çalıştırılır:

```powershell
py -3.13 -m scripts.ai_company_post_audit `
  --input runtime\social_growth\live_post_sample.json `
  --output runtime\social_growth\live_post_audit.json
```

Komut önce deterministik kalite kurallarını çalıştırır, ardından yalnız bu bulgulara
dayanabilen AI Company incelemesini şema doğrulamasından geçirir. Provider yoksa veya
ajan bozuk/uydurulmuş çıktı üretirse `BLOCKED_AI_REVIEW` döner. Üretilen evidence
dosyası her durumda `live_actions=BLOCKED` taşır; audit komutu gönderi silmez,
düzenlemez, paylaşmaz, yorum veya DM göndermez.

Sürekli resmî veri alımı için `INSTAGRAM_ACCOUNT_ID` ve `INSTAGRAM_ACCESS_TOKEN`
sağlanmalı ve `MetaGraphClient.list_recent_media()` çıktısı aynı snapshot sözleşmesine
aktarılmalıdır. Tarayıcı gözlemi yalnız ilk doğrulama örneğidir.

## Kademeli canlıya alma

1. `SOCIAL_GROWTH_LIVE_ACTIONS_APPROVED` kapalıyken challenge, HMAC, payload ve Redis
   idempotency doğrulanır.
2. Meta test hesabında tek trigger ve tek private reply ile provider ID kanıtı alınır.
3. Evidence JSONL içinde `EpisodeRecord`, `ActionRecord` ve provider ID doğrulanır.
4. İnsan onayından sonra canlı-eylem bayrağı açılır.
5. Rate-limit, webhook retry, duplicate event ve token rotation senaryoları izlenir.

## Güvenlik müdahalesi

Prototipte daha önce source içine yazılmış Instagram password artık kaldırılmıştır.
Ancak source temizliği tek başına credential rotation değildir:

1. Instagram password değiştirilmelidir.
2. Aktif Instagram oturumları kapatılmalıdır.
3. Eski Meta token'ları revoke edilip en az yetkili yeni token üretilmelidir.
4. Yerel `workspace/carousel_engine/browser_profile` içindeki cookie/session verisi
   artık Git tarafından ignore edilir; oturumlar revoke edildikten sonra operatör
   tarafından güvenli biçimde kaldırılmalıdır.

## Evidence yorumlama

- `SUCCEEDED`: Meta provider ID vardır.
- `DRY_RUN`: Doğrulama yapılmıştır, dış etki yoktur.
- `BLOCKED`: Policy veya insan onayı geçidi kapalıdır.
- `DUPLICATE`: Aynı comment olayı daha önce claim edilmiştir.
- `IGNORED`: İzinli trigger eşleşmemiştir.
- `FAILED`: Provider/transport doğrulaması tamamlanmamıştır.

`PASSED`, `DM_SENT_SUCCESSFULLY` veya `COMMENT_POSTED_TOP_RANKED` gibi provider kanıtı
olmayan legacy etiketleri canlı başarı sayılmaz.
