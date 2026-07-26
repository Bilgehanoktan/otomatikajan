# Reel Schedule Test Result - 2026-07-25

Hesap: `@ai_gucum_`

Sonuc: `PASS`

## Canli Meta testi

- Yuzey: Meta Business Suite `Content -> Scheduled`
- URL: `https://business.facebook.com/latest/posts/scheduled_posts?asset_id=1194885453711219&business_id=1547688643555667&ir_qe_exposed=1`
- Dogrulanan icerik: `GitHub Copilot model secicisine... Claude Opus 5`
- Dogrulanan format: `Instagram`, `Reel`, `ai_gucum_`
- Dogrulanan zaman: `Tue Jul 28, 8:30pm`
- Dogrulanan gizlilik: `Public`

## Yerel dosya testi

- Final video var: `runtime/social_growth/first_week_2026-07-24/02_claude_opus_5_copilot/claude_opus_5_copilot_final.mp4`
- Boyut: `981612` bytes
- MP4 kutu sinyalleri: `ftyp`, `moov`, `mdat`
- Codec sinyalleri: `avc1` video, `mp4a` audio
- Dogrulama kareleri var:
  - `verification/frame_01.png`
  - `verification/frame_12.png`
  - `verification/frame_24.png`

## Proje durumu testi

- `manifest.json` parse edildi.
- `manifest.status`: `LIVE_IN_PROGRESS`
- `manifest.account`: `@ai_gucum_`
- `manifest.posts`: `3`
- `reel_delivery_evidence.md` icinde `META_SCHEDULED`, `2026-07-28 20:30 Europe/Istanbul`, `1080x1920`, `25.00s`, `Your reel is safe to publish!` ve `No copyright issues were found.` kayitlari bulundu.

## Not

Onceki `ffmpeg` binary yolu bu test sirasinda bulunamadi; bu nedenle codec testi dis bagimlilik yerine MP4 dosya sinyalleri uzerinden yapildi. Onceki teslim kanitindaki ayrintili ffmpeg teknik kapisi korunuyor.
