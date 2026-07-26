# İlk Hafta Operatör Yayın Takvimi

Saat dilimi: `Europe/Istanbul`

Durum: `LIVE_IN_PROGRESS`

Saatler hesap insight verisi oluşana kadar test hipotezidir. İlk hafta sonunda
gerçek erişim ve izleme verilerine göre değiştirilir.

| Tarih | Saat | Yüzey | İçerik | Operatör işlemi | Başarı ölçütü |
|---|---:|---|---|---|---|
| 24 Temmuz 2026 | — | Profil | Avatar, ad ve bio kontrolü | Avatar yüklemesi hâlen bloke; bio korunur | Profil tamamlanma |
| 24 Temmuz 2026 | 23:58 | Carousel | `01_account_promise` | `PUBLISHED_CONFIRMED`; 6 görsel, caption ve 6 alt metin canlı doğrulandı | Profil ziyareti → takip |
| 25 Temmuz 2026 | 12:30 | Story | `day_02_start_01` | `META_ACTIVE`; Meta Business Suite üzerinden yayımlandı | Yanıt, profil ziyareti |
| 25 Temmuz 2026 | 12:31 | Story | `day_02_start_02` | `META_ACTIVE`; Meta Business Suite üzerinden yayımlandı | Yanıt, profil ziyareti |
| 26 Temmuz 2026 | 00:30 | Story | `day_02_start_03_auto_reply` | `META_SCHEDULED`; 25 Temmuz 15:15 denemesi `FAILED_TO_PUBLISH`, temiz kayıtla yeniden planlandı | Story yanıtı, profil ziyareti |
| 26 Temmuz 2026 | 20:30 | Highlight | Başla | Story'ler aktif olduktan sonra `Başla` Highlight'ına mobil/Instagram üzerinden ekle; önceden zamanlanamaz | Highlight görüntüleme |
| 27 Temmuz 2026 | 19:30 | Story | `day_04_poll_auto_reply` | `META_SCHEDULED`; desteklenmeyen anket etiketi yerine Story yanıt CTA'sı kullanıldı | Yanıt sayısı ve konu dağılımı |
| 28 Temmuz 2026 | 20:30 | Reel | `02_claude_opus_5_copilot` | `META_SCHEDULED`; H.264/AAC MP4, Türkçe özgün ses, özel kapak ve caption Meta Scheduled listesinde doğrulandı | İzleme süresi, takip |
| 29 Temmuz 2026 | 12:30–12:31 | Story | `day_06_process_01`, `day_06_process_02_auto_time` | `META_SCHEDULED`; iki ayrı bulut kaydı doğrulandı | Yanıt, hatırlatıcı |
| 30 Temmuz 2026 | 20:30 | Carousel | `03_gpt_5_6_models` | `META_SCHEDULED`; caption, 7 görsel ve 7 alt metin Planner'da doğrulandı | Kaydetme, paylaşma |
| 31 Temmuz 2026 | 20:30 | Analiz | İlk snapshot | 24 saatlik uygun gönderileri ölçüm tablosuna işle | Baseline başlangıcı |

## Stop-the-line

- Görsel ile caption konusu uyuşmuyorsa yayımlama.
- Kaynak URL erişilemiyorsa ürün iddiasını yayımlama.
- Reel `1080x1920 MP4` ve ses kontrolü tamamlanmadan yayımlama.
- Aynı gün iki feed gönderisi yayımlama.
- Caption, tek CTA ve alt metin olmadan paylaşma.
