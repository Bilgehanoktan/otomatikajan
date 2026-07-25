"""
AI & Software Tools Data Researcher / Source Provider
Extracts key value props, pain points, features, and affiliate details for target tools.
"""

from typing import Dict, Any, List

TOOLS_DATABASE = {
    "Cursor AI": {
        "name": "Cursor AI",
        "tagline": "Yazılımcıların Günde 3 Saat Tasarruf Ettiren Yapay Zeka Kod Editörü",
        "category": "Yapay Zeka / Kodlama",
        "target_audience": "Yazılımcılar, Geliştiriciler & Veri Bilimciler",
        "problem": "Saatlerce spagetti kod ayıklamak, karmaşık hatalarla boğuşmak ve dokümantasyon okumak vakit çalar.",
        "agitation": "Proje teslim süresi yaklaşıyor, hatalar bitmiyor ve geceler boyu bilgisayar başında yoruluyorsunuz.",
        "solution": "Cursor AI, VS Code üzerine kurulu yerleşik yapay zekası ile kodunuzu saniyeler içinde anlar ve yazar.",
        "features": [
            {
                "title": "⚡ Composer (Ctrl + I)",
                "desc": "Tüm projeyi tek bir komutla uçtan uca düzenler ve yeni özellikler ekler."
            },
            {
                "title": "🔍 Kod Tabanı İle Sohbet (@Codebase)",
                "desc": "Binlerce satırlık projenize soru sorun, anında doğru dosyayı ve yanıtı bulsun."
            },
            {
                "title": "🛡️ Otonom Hata Düzeltme",
                "desc": "Terminaldeki hataları tek tıkla analiz eder ve anında düzeltilmiş kodu uygular."
            }
        ],
        "cta_headline": "🔥 Ücretsiz İndirin & Hemen Deneyin!",
        "cta_subtext": "Profilimdeki bağlantıya tıklayarak Cursor AI'ı ücretsiz indirebilir ve kodlama hızınızı 10 katına çıkarabilirsiniz.",
        "affiliate_link": "https://cursor.com/?ref=otomatikajan",
        "pricing": "Ücretsiz Başlangıç Planı Mevcut (Pro: $20/ay)",
        "hashtags": ["#cursorai", "#yapayzeka", "#yazılım", "#kodlama", "#python", "#otomasyon"]
    },
    "Perplexity AI": {
        "name": "Perplexity AI",
        "tagline": "Google Arama Devrini Bitiren Akademik Yapay Zeka Arama Motoru",
        "category": "Yapay Zeka / Araştırma",
        "target_audience": "Öğrenciler, Araştırmacılar, Girişimciler & İçerik Üreticileri",
        "problem": "Google'da arama yaparken reklamlar, spam siteler ve doğrulanmamış içerikler arasında kayboluyorsunuz.",
        "agitation": "Doğru bilgiye ulaşmak saatlerinizi alıyor ve eski bilgileri okuyarak zaman kaybediyorsunuz.",
        "solution": "Perplexity AI, tüm interneti canlı tarayarak sorularınıza akademik kaynaklı ve doğrudan yanıtlar verir.",
        "features": [
            {
                "title": "📚 Canlı Kaynak Gösterimi",
                "desc": "Verdiği her bilginin makale, akademik yayın veya web kaynağını dipnot olarak sunar."
            },
            {
                "title": "🔍 Pro Search (Derin Odaklı Arama)",
                "desc": "Karmaşık konuları adım adım analiz eder ve eksiksiz özet rapor çıkarır."
            },
            {
                "title": "📄 Doküman & PDF Analizi",
                "desc": "Yüzlerce sayfalık raporları yükleyin, saniyeler içinde soru-cevap yapın."
            }
        ],
        "cta_headline": "🚀 Google Yaptığınız Aramalara Veda Edin!",
        "cta_subtext": "Profilimdeki bağlantıya tıklayarak Perplexity AI'ı ücretsiz deneyebilir ve araştırmalarınızı 5 kat hızlandırabilirsiniz.",
        "affiliate_link": "https://perplexity.ai/?ref=otomatikajan",
        "pricing": "Ücretsiz Kullanım (Pro: $20/ay)",
        "hashtags": ["#perplexity", "#yapayzeka", "#araştırma", "#google", "#teknoloji", "#öğrenci"]
    },
    "NotebookLM": {
        "name": "NotebookLM",
        "tagline": "Google'ın Notlarınızı Sesli Podcaste Dönüştüren Ücretsiz AI Asistanı",
        "category": "Yapay Zeka / Verimlilik",
        "target_audience": "Öğrenciler, Kitap Okurları, Akademisyenler & Yöneticiler",
        "problem": "Uzun PDF'leri, ders notlarını veya karmaşık kitapları okuyacak vaktiniz yok mu?",
        "agitation": "Sınavlar veya toplantılar yaklaşıyor ama yüzlerce sayfalık belgenin özetini çıkarmak imkansız görünüyor.",
        "solution": "Google NotebookLM, belgelerinizi yüklediğiniz an onları tartışan 2 yapay zeka sunucusunun podcast sohbetine dönüştürür!",
        "features": [
            {
                "title": "🎙️ Audio Overview (Sesli Podcast)",
                "desc": "Metinlerinizi iki uzman AI sunucusunun heyecanlı radyo sohbeti şeklinde dinleyin."
            },
            {
                "title": "🔒 %100 Güvenli ve Özelleştirilmiş",
                "desc": "Sadece yüklediğiniz kaynaklara dayanarak yanıt verir, asla uydurma bilgi üretmez."
            },
            {
                "title": "📊 Çalışma Kılavuzu & Sınav Sorusu",
                "desc": "Tek tıkla belgelerinizden çalışma kartları, SSS ve zaman çizelgesi oluşturur."
            }
        ],
        "cta_headline": "🎧 Notlarınızı Dinlemeye Başlayın!",
        "cta_subtext": "Profilimdeki bağlantıya tıklayarak Google NotebookLM'i tamamen ücretsiz kullanmaya başlayabilirsiniz.",
        "affiliate_link": "https://notebooklm.google.com/?ref=otomatikajan",
        "pricing": "%100 ÜCRETSİZ (Google Hesabı Yeterli)",
        "hashtags": ["#notebooklm", "#google", "#yapayzeka", "#podcast", "#öğrenci", "#dersçalışma"]
    },
    "v0.dev": {
        "name": "v0.dev",
        "tagline": "Sadece Cümle Yazarak Tam Web Sitesi Üreten Yapay Zeka Sistem",
        "category": "Yapay Zeka / Web Geliştirme",
        "target_audience": "Tasarımcılar, Frontend Geliştiriciler & Girişimciler",
        "problem": "Figma tasarımı yapıp sonra saatlerce React ve CSS kodu yazmak büyük zaman kaybıdır.",
        "agitation": "Müşterilerinize veya projenize hızlı prototip sunmanız gerekiyor ama kodlama günlerinizi alıyor.",
        "solution": "Vercel v0.dev, sadece ne istediğinizi tarif ettiğinizde kopyalamaya hazır React & Tailwind kodları üretir.",
        "features": [
            {
                "title": "🎨 Anında Canlı Önizleme",
                "desc": "Prompt yazın, saniyeler içinde çalışan interaktif arayüz bileşeni karşınızda olsun."
            },
            {
                "title": "💻 Modern Tech Stack (React + Tailwind)",
                "desc": "Ürettiği kod temiz, modüler ve projelerinize doğrudan yapıştırılabilir."
            },
            {
                "title": "🔄 İteratif Revize",
                "desc": "'Buton rengini mavi yap ve gölge ekle' diyerek tasarımı anında güncelleyin."
            }
        ],
        "cta_headline": "⚡ Hayalinizdeki Web Sitesini Dakikalar İçinde Kurun!",
        "cta_subtext": "Profilimdeki bağlantıya tıklayarak v0.dev ile ilk web sitenizi ücretsiz oluşturun.",
        "affiliate_link": "https://v0.dev/?ref=otomatikajan",
        "pricing": "Ücretsiz Başlangıç (Premium: $20/ay)",
        "hashtags": ["#v0dev", "#webtasarım", "#react", "#tailwind", "#yapayzeka", "#girişimcilik"]
    },
    "Midjourney": {
        "name": "Midjourney v6",
        "tagline": "Fotoğraftan Ayırt Edilemeyen İnanılmaz Görseller Üreten AI Kralı",
        "category": "Yapay Zeka / Görsel Tasarım",
        "target_audience": "Grafik Tasarımcılar, Reklamcılar & Dijital İçerik Üreticileri",
        "problem": "Stok fotoğraflara yüzlerce dolar harcamak veya hayalinizdeki görseli bulamamak can sıkıcıdır.",
        "agitation": "Reklam kampanyalarınız veya sosyal medya gönderileriniz sıradan göründüğü için dikkat çekmiyor.",
        "solution": "Midjourney v6, sadece metin yazarak stüdyo kalitesinde fotogerçekçi görseller ve illüstrasyonlar üretir.",
        "features": [
            {
                "title": "📸 Hiper-Gerçekçi Detaylar",
                "desc": "Işık, kamera açısı ve dokularda gerçek fotoğraflardan farksız sonuçlar sunar."
            },
            {
                "title": "🔤 Metin Yazma Yeteneği",
                "desc": "Görsellerin üzerine doğrudan doğru imla ile tabelalar ve yazılar ekleyebilir."
            },
            {
                "title": "🎨 Stil Referansı (--sref)",
                "desc": "Beğendiğiniz bir görsel stilini tüm yeni tasarımlarınıza anında uygular."
            }
        ],
        "cta_headline": "🎨 Hayal Gücünüzü Görsele Dönüştürün!",
        "cta_subtext": "Profilimdeki bağlantıdan Midjourney rehberine ulaşabilir ve hemen harika görseller tasarlayabilirsiniz.",
        "affiliate_link": "https://midjourney.com/?ref=otomatikajan",
        "pricing": "Aylık $10'dan Başlayan Planlar",
        "hashtags": ["#midjourney", "#görseltasarım", "#yapayzeka", "#tasarım", "#fotografçılık", "#art"]
    }
}

def get_target_tool_data(tool_name: str = "Cursor AI") -> dict:
    """Returns structured data for a target tool in the AI & Software niche."""
    return TOOLS_DATABASE.get(tool_name, TOOLS_DATABASE["Cursor AI"])

def get_all_tools() -> List[dict]:
    """Returns all available tools in the database."""
    return list(TOOLS_DATABASE.values())
