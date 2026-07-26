# Meta Business Suite Bulut Zamanlama Kanıtı

Kontrol zamanı: `2026-07-25 22:31 +03:00`

Hesap: `ai_gucum_`

Meta kimlikleri:

- `business_id=1547688643555667`
- `asset_id=1194885453711219`

## Doğrulanmış durum

| Tarih ve saat (`Europe/Istanbul`) | İçerik | Meta kanıtı | Sonuç |
|---|---|---|---|
| 25 Temmuz 12:30 | `day_02_start_01.png` | Stories → Active satırı ve Planner `12:30 PM Instagram Active` | `ACTIVE` |
| 25 Temmuz 12:31 | `day_02_start_02.png` | Stories → Active satırı ve Planner `12:31 PM Instagram Active` | `ACTIVE` |
| 25 Temmuz 15:15 | `day_02_start_03_auto_reply.png` | Stories → Scheduled satırında `Failed to publish` | `FAILED_TO_PUBLISH` |
| 26 Temmuz 00:30 | `day_02_start_03_auto_reply.png` | Meta başarı bildirimi ve Stories → Scheduled `Sun Jul 26, 12:30am` | `META_SCHEDULED` |
| 27 Temmuz 19:30 | `day_04_poll_auto_reply.png` | Meta başarı bildirimi, Planner `7:30 PM Instagram`, Stories → Scheduled satırı | `META_SCHEDULED` |
| 28 Temmuz 20:30 | `02_claude_opus_5_copilot` | Meta başarı bildirimi ve Content → Scheduled `Tue Jul 28, 8:30pm` video satırı | `META_SCHEDULED` |
| 29 Temmuz 12:30 | `day_06_process_01.png` | Meta başarı bildirimi, Planner `12:30 PM Instagram`, Stories → Scheduled satırı | `META_SCHEDULED` |
| 29 Temmuz 12:31 | `day_06_process_02_auto_time.png` | Meta başarı bildirimi, Planner `12:31 PM Instagram`, Stories → Scheduled satırı | `META_SCHEDULED` |
| 30 Temmuz 20:30 | `03_gpt_5_6_models` | Planner `8:30 PM Instagram` | `META_SCHEDULED` |

30 Temmuz carousel kaydı 7 adet `1080x1350` görsel, 725 karakterlik
caption ve 7 alt metinle oluşturuldu. Composer uzun süre işlem ekranında kalsa
da ayrı Planner sekmesinde `8:30 PM Instagram` kaydı görüldüğü için durum
`META_SCHEDULED` olarak doğrulandı.

## Meta web sınırlamaları ve uygulanan uyarlamalar

- Story editöründe soru, anket ve geri sayım etiketleri yok; yalnız `Link`
  sticker seçeneği vardı.
- `day_02_start_03.png`, soru etiketi yerine doğrudan Story yanıt CTA'sıyla
  `day_02_start_03_auto_reply.png` olarak uyarlandı.
- `day_04_poll.png`, anket etiketi yerine yanıt seçenekleri içeren
  `day_04_poll_auto_reply.png` olarak uyarlandı.
- `day_06_process_02.png`, geri sayım etiketi yerine sabit yayın saati içeren
  `day_06_process_02_auto_time.png` olarak uyarlandı.
- Highlight'a ekleme önceden zamanlanamaz; Story aktif olduktan sonra Instagram
  içinden yapılmalıdır.
- `claude_opus_5_copilot_review.webm`, H.264/AAC MP4'e dönüştürüldü; Türkçe
  özgün ses, özel kapak ve Meta telif kontrolüyle kalite kapısını geçti.
- Meta editöründe harici müzik eklenmedi; Reel özgün Türkçe anlatımla zamanlandı.

## PC kapalıyken çalışma

`META_SCHEDULED` satırları Meta Business Suite bulutunda kayıtlıdır; yayın
saatinde bu bilgisayarın veya Codex oturumunun açık olması gerekmez. Yerel
Codex otomasyonları ve henüz zamanlanmamış Highlight işlemi bilgisayar kapalıyken
kendiliğinden çalışmaz.
