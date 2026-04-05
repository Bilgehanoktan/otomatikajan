# Telegram Bot Entegrasyon Rehberi

Bu belge, sistemin Telegram botu ile nasıl eşleştirileceğini ve kullanılacağını açıklar. Bot; görev yönetimi, sistem izleme ve kritik olay bildirimleri (Faz 11 Self-Repair dahil) için kullanılır.

## 1. Bot Oluşturma
1.  Telegram'da [@BotFather](https://t.me/botfather) ile konuşun.
2.  `/newbot` komutuyla yeni bir bot oluşturun.
3.  Size verilen **API Token**'ı kopyalayın.

## 2. Yapılandırma
`.env` dosyanıza aşağıdaki değişkenleri ekleyin:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ALLOWED_IDS=12345678,87654321  # Virgülle ayrılmış yetkili ID'ler
TELEGRAM_ADMIN_IDS=12345678            # Admin yetkisine sahip ID'ler
TELEGRAM_WEBHOOK_SECRET=my_secret_token # Webhook güvenliği için rastgele bir dize
```

> [!TIP]
> Telegram ID'nizi öğrenmek için [@userinfobot](https://t.me/userinfobot) botunu kullanabilirsiniz.

## 3. Komutları Kaydetme
Botunuzun "/" menüsünde komutların görünmesi için şu betiği çalıştırın:
```bash
python scripts/register_telegram_commands.py
```

## 4. Kullanım Modları

### A. Yerel Geliştirme (Polling)
Dış dünyaya açık bir HTTPS adresiniz (ngrok vb.) yoksa botu polling modunda çalıştırabilirsiniz:
```bash
python telegram_app/polling.py
```

### B. Canlı Ortam (Webhook)
Üretim ortamında bot, FastAPI uygulaması üzerinden webhook ile çalışır. Webhook URL'ini kaydetmek için:
1.  Uygulamayı başlatın.
2.  Şu API endpoint'ine POST isteği gönderin: `/api/v1/telegram/setup`
    - Body: `{"url": "https://sizin-adresiniz.com/api/v1/telegram/webhook"}`

## 5. Kullanılabilir Komutlar
- `/start` — Botu başlatır ve yetki kontrolü yapar.
- `/status` — Sistem genel durumunu ve sağlığını gösterir.
- `/tasks` — Son görevleri listeler.
- `/newtask` — `/newtask Başlık | Açıklama | priority` formatında yeni görev oluşturur.
- `/agents` — Aktif ajanların durumlarını ve başarı oranlarını gösterir.
- `/logs` — Son sistem loglarını getirir.
- `/errors` — Hatalı görevleri listeler.
- `/incidents` — (Faz 11) Açık hata incident'lerini gösterir.
- `/repair` — (Faz 11) Belirli bir incident için onarım sürecini başlatır.
- `/proposals` — (Faz 11) Onay bekleyen PR önerilerini listeler.
- `/approve` — /reject — Önerileri onaylar veya reddeder.
