"""
Viral & Deep Value Carousel Content Generator for @Ai_gucum_.
Transforms raw AI tool data into high-converting, actionable, deep-value 6-slide Instagram carousels.
Packs concrete code snippets, real prompts, benchmark comparisons, and actionable tips into every slide.
"""

import sys
from typing import List, Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DEEP_TOOL_DATABASE = {
    "DeepSeek R1": {
        "name": "DeepSeek R1",
        "category": "YAPAY ZEKA / AKIL YÜRÜTME",
        "pricing": "%100 ÜCRETSİZ & AÇIK KAYNAK",
        "subtitle_1": "OpenAI o1'i Tahtından İndiren %100 Açık Kaynaklı Akıl Yürütme Modeli.",
        "comp_old": "❌ OpenAI o1 ($200/ay & Kapalı Kaynak)",
        "comp_new": "⚡ DeepSeek R1 (%100 Ücretsiz & Açık Kaynak)",
        "comp_sub": "OpenAI'ın 100 kat daha ucuza eğittiği ve tüm matematik/kodlama testlerinde birinci olan devrim!",
        "code_lang": "DEEPSEEK R1 YEREL KURULUM & PROMPT",
        "code": '# Terminalde Yerel Çalıştır (Ollama):\n$ ollama run deepseek-r1:8b\n\n# Akıl Yürütme Promptu:\n"Bana Python ile yüksek performanslı distributed queue mimarisi yaz ve <think> aşamalarını göster."',
        "feat_1_title": "🧠 Uçtan Uca CoT Akıl Yürütme",
        "feat_1_desc": "Hatalı cevap vermeden önce <think> etiketleri içinde adım adım mantık yürüterek sıfır hata ile kod üretir.",
        "feat_2_title": "💻 %100 Yerel Cihazda Çalışma",
        "feat_2_desc": "Ollama ve LM Studio ile kendi bilgisayarınızda internete ihtiyaç duymadan ve veriniz dışarı çıkmadan çalıştırın.",
        "feat_3_title": "🚀 MATH & HumanEval Şampiyonu",
        "feat_3_desc": "Matematik ve karmaşık yazılım testlerinde GPT-4o ve Claude 3.5 Sonnet'i geride bırakarak liderliğe yerleşti.",
        "recap_1": "Karmaşık yazılım mimarileri, matematiksel analizler ve algoritma optimizasyonu için.",
        "recap_2": "%100 Ücretsiz, açık kaynak ve yerel donanımda tamamen gizli çalışma garantisi.",
        "recap_3": "Ollama veya DeepSeek web arayüzü üzerinden 10 saniyede ücretsiz kullanmaya başlayın.",
        "trigger": "DEEPSEEK"
    },
    "Bolt.new": {
        "name": "Bolt.new",
        "category": "YAPAY ZEKA / WEB GELİŞTİRME",
        "pricing": "ÜCRETSİZ BAŞLANGIÇ (PRO: $20/AY)",
        "subtitle_1": "Tarayıcı Üzerinde Tek Komutla Full-Stack Web Uygulaması Üreten Yapay Zeka.",
        "comp_old": "❌ Geleneksel (2 Hafta Kodlama & Server Setup)",
        "comp_new": "⚡ Bolt.new (30 Saniyede Canlı Web App)",
        "comp_sub": "Tek satir ortam kurulumu yapmadan direkt tarayıcıda Full-Stack projenizi canlıya alın!",
        "code_lang": "BOLT.NEW PROMPT FORMÜLÜ",
        "code": '# Full-Stack Web App Promptu:\n"Create a modern SaaS Dashboard with Next.js 15, TailwindCSS, Auth, Stripe integration and dark mode UI."\n\n>> %100 Canlıda & Sıfır Hata!',
        "feat_1_title": "🌐 WebContainer Teknolojisi",
        "feat_1_desc": "Node.js sunucusunu doğrudan tarayıcınızın içinde çalıştırarak paket kurulumlarını anında tamamlar.",
        "feat_2_title": "💻 Canlı Terminal & Paket Yöneticisi",
        "feat_2_desc": "npm install, git push ve terminal komutlarını kendi kendine otonom olarak çalıştırır.",
        "feat_3_title": "🚀 Tek Tıkla Vercel / Netlify Deploy",
        "feat_3_desc": "Hazırladığı projeyi tek bir butonla Netlify veya Vercel üzerine canlıya alır.",
        "recap_1": "Fikirlerinizi 1 dakikada prototipten çalışan canlı ürüne dönüştürmek istediğinizde.",
        "recap_2": "Tarayıcıda Node.js çalıştırma, npm paketleri yükleme ve anında canlı önizleme imkanı.",
        "recap_3": "Bolt.new adresine girip hayalinizdeki uygulamayı İngilizce/Türkçe tarif edin.",
        "trigger": "BOLT"
    },
    "Claude 3.5 Sonnet": {
        "name": "Claude 3.5 Sonnet",
        "category": "YAPAY ZEKA / KOD & ANALİZ",
        "pricing": "ÜCRETSİZ BAŞLANGIÇ (PRO: $20/AY)",
        "subtitle_1": "Yazılımcıların 1 Numaralı Kod Asistanı & Canlı Interactive Artifacts.",
        "comp_old": "❌ ChatGPT (Düz Metin & Parçalı Snippet)",
        "comp_new": "⚡ Claude 3.5 Sonnet (Interactive Artifacts)",
        "comp_sub": "Ürettiği kodları ve web tasarımlarını sağ taraftaki canlı Artifacts penceresinde anında test edin!",
        "code_lang": "CLAUDE 3.5 ARTIFACT PROMPT",
        "code": '# Interactive Artifact Promptu:\n"Build a fully interactive SVG Mind-Map Editor in React 19 with drag-and-drop, export PNG and glassmorphism styling."\n\n>> Artifacts Penceresinde Anında Çalışır!',
        "feat_1_title": "🎨 Canlı Interactive Artifacts",
        "feat_1_desc": "Yazdığı React, HTML, SVG ve Mermaid diyagramlarını anında sağ panelde canlı olarak çalıştırır.",
        "feat_2_title": "🔍 200K Token Devasa Context",
        "feat_2_desc": "Tüm projenizin kaynak kodlarını tek seferde okuyup eksiksiz refactoring ve hata analizi yapar.",
        "feat_3_title": "🛡️ SWE-bench Kodlama Şampiyonu",
        "feat_3_desc": "Gerçek dünya GitHub hatalarını çözme testlerinde %49 ile tüm yapay zeka modellerinin önünde.",
        "recap_1": "Karmaşık yazılım refactoring, interaktif arayüzler ve büyük kod tabanı analizleri için.",
        "recap_2": "Canlı Artifacts penceresi, 200K token hafıza ve üstün kodlama yeteneği.",
        "recap_3": "Claude.ai adresine girip kodlarınızı yapıştırın ve Artifacts modunu açın.",
        "trigger": "CLAUDE"
    },
    "Flux 1.1 Pro": {
        "name": "Flux 1.1 Pro",
        "category": "YAPAY ZEKA / GÖRSEL TASARIM",
        "pricing": "ÜCRETSİZ DENEME (API BAZLI)",
        "subtitle_1": "Midjourney Devrini Bitiren 6 Kat Hızlı Foto-Gerçekçi Görsel Modeli.",
        "comp_old": "❌ Midjourney v6 (Yavaş & Discord Zorunlu)",
        "comp_new": "⚡ Flux 1.1 Pro (6 Kat Hızlı & Kusursuz Metin)",
        "comp_sub": "Metin ve el/parmak çizimlerindeki hataları tamamen sıfırlayan Black Forest Labs mucizesi!",
        "code_lang": "FLUX 1.1 PROMET FORMÜLÜ",
        "code": '# Hiper-Gerçekçi Görsel Promptu:\n"A cinematic portrait of a cybernetic software engineer in a dark glassmorphism room, neon cyan lighting, 8k resolution, photorealistic, 35mm lens --ar 16:9"\n\n>> Metin ve Parmak Çizimi Sıfır Hata!',
        "feat_1_title": "🔤 Kusursuz Tipografi ve Metin",
        "feat_1_desc": "Görsel üzerindeki tabelalara ve ürünlere harf hatası olmadan doğru Türkçe/İngilizce metin çizer.",
        "feat_2_title": "⚡ 6 Kat Daha Hızlı Render",
        "feat_2_desc": "Kullanıcı taleplerini ortalama 2.5 saniyede yüksek çözünürlüklü olarak teslim eder.",
        "feat_3_title": "📸 Stüdyo Kalitesinde Aydınlatma",
        "feat_3_desc": "Işık kırılmaları, alan derinliği ve doku detaylarında gerçek profesyonel fotoğrafları aratmaz.",
        "recap_1": "Sosyal medya görselleri, ürün reklamları ve tipografi içeren görsel tasarımlar için.",
        "recap_2": "Elde/parmakta ve yazılarda hatasız sonuç, 6 kat daha hızlı üretim süresi.",
        "recap_3": "Replicate veya Black Forest Labs API üzerinden anında kullanın.",
        "trigger": "FLUX"
    },
    "ElevenLabs": {
        "name": "ElevenLabs",
        "category": "YAPAY ZEKA / SES KLONLAMA",
        "pricing": "ÜCRETSİZ BAŞLANGIÇ (PRO: $5/AY)",
        "subtitle_1": "1 Dakikada Kendi Sesinizi Klonlayan 29+ Dil Destekli Yapay Zeka Devrimi.",
        "comp_old": "❌ Stüdyo Kaydı ($1000+ & Günler Süren Kayıt)",
        "comp_new": "⚡ ElevenLabs (10 Saniyede Kendi Sesinizle Konuşma)",
        "comp_sub": "Sadece 1 dakikalık ses örneğinizle kendi sesinizi 29 dilde doğal vurgularla konuşturun!",
        "code_lang": "ELEVENLABS PYTHON SDK INTEGRATION",
        "code": '# Python İle Seslendirme Örneği:\nfrom elevenlabs import generate, play\n\naudio = generate(\n  text="Merhaba! Geleceğin yapay zeka araçları burada.",\n  voice="Bilgehan", model="eleven_multilingual_v2"\n)\nplay(audio)',
        "feat_1_title": "🎙️ Instant Voice Cloning",
        "feat_1_desc": "1 dakikalık ses kaydıyla tonlamanızı, nefes alışınızı ve vurgularınızı bütünüyle klonlar.",
        "feat_2_title": "🌐 29+ Dilde Doğal Konuşma",
        "feat_2_desc": "Türkçe konuştuğunuz sesinizle İngilizce, Almanca veya Japonca aksansız içerik üretin.",
        "feat_3_title": "🎬 AI Dublaj & Sound Effects",
        "feat_3_desc": "Videoları otomatik Türkçe dublaj yapın veya sadece metin yazarak film efekti üretin.",
        "recap_1": "Reels/TikTok içerikleri, ses kitapları, video dublajları ve sesli asistanlar için.",
        "recap_2": "Kendi ses tonunuzu koruyarak 29 farklı dilde profesyonel seslendirme yapma gücü.",
        "recap_3": "ElevenLabs.io sitesine kaydolup ses örneğinizi yükleyin.",
        "trigger": "ELEVENLABS"
    }
}

def generate_carousel_slides(tool_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    tool_name = tool_data.get("name", "DeepSeek R1")
    info = DEEP_TOOL_DATABASE.get(tool_name, None)

    if not info:
        # Fallback to DeepSeek R1 if tool is missing
        info = DEEP_TOOL_DATABASE["DeepSeek R1"]
        info["name"] = tool_name

    category = info["category"]
    pricing = info["pricing"]
    trigger_word = info["trigger"]

    slides = [
        # Slide 1: HOOK (Attention Grabbing & Concrete Tool Identity)
        {
            "slide_number": 1,
            "type": "HOOK",
            "badge_icon": "🔥",
            "badge": f"{category} DEVRİMİ",
            "title": f"ChatGPT'yi Unutturan {info['name']} Hileleri",
            "subtitle": info["subtitle_1"],
            "hero_highlights": [
                {"icon": "⚡", "text": f"Arac: {info['name']}"},
                {"icon": "🎯", "text": f"Kategori: {category}"},
                {"icon": "💰", "text": f"Fiyat: {pricing}"}
            ],
            "footer": "Kaydırın > Detaylar İçeride 🤫"
        },

        # Slide 2: CONTEXT & CONCRETE COMPARISON MATRIX
        {
            "slide_number": 2,
            "type": "COMPARISON",
            "badge_icon": "📊",
            "badge": "NEDEN BU KADAR POPÜLER?",
            "title": "Geleneksel Araçlar vs Yeni Nesil Yapay Zeka",
            "subtitle": info["comp_sub"],
            "comparison_matrix": [
                {"title": info["comp_old"].split("(")[0], "value": info["comp_old"], "is_highlight": False},
                {"title": info["comp_new"].split("(")[0], "value": info["comp_new"], "is_highlight": True}
            ],
            "footer": "Uygulamalı Prompt 3. Slaytta >"
        },

        # Slide 3: PROMPT & CODE EXAMPLE (Actual Practical Prompt & Output Snippet)
        {
            "slide_number": 3,
            "type": "PROMPT",
            "badge_icon": "💻",
            "badge": "CANLI KULLANIM & GERÇEK PROMPT ÖRNEĞİ",
            "title": "Doğrudan Kopyalayıp Kullanabileceğiniz Komut",
            "subtitle": "Aşağıdaki promptu araca yapıştırarak en yüksek doğrulukta sonuç alabilirsiniz:",
            "code_snippet": {
                "lang": info["code_lang"],
                "code": info["code"]
            },
            "footer": "Öne Çıkan Özellikler 4. Slaytta >"
        },

        # Slide 4: BREAKTHROUGH FEATURES (3 Actionable Feature Cards)
        {
            "slide_number": 4,
            "type": "FEATURES",
            "badge_icon": "🚀",
            "badge": "ÖNE ÇIKAN DEVRİM ÖZELLİKLER",
            "title": f"Neden Şimdi {info['name']} Denemelisiniz?",
            "features": [
                {"icon": "⚡", "title": info["feat_1_title"], "desc": info["feat_1_desc"]},
                {"icon": "🎯", "title": info["feat_2_title"], "desc": info["feat_2_desc"]},
                {"icon": "🔒", "title": info["feat_3_title"], "desc": info["feat_3_desc"]}
            ],
            "footer": "Özet Kartı 5. Slaytta >"
        },

        # Slide 5: CHEAT SHEET / RECAP MATRIX (Saveable Matrix)
        {
            "slide_number": 5,
            "type": "CHEAT_SHEET",
            "badge_icon": "📌",
            "badge": "KAYDETMELİK REHBER ÖZETİ",
            "title": f"{info['name']} Hakkında Bilmeniz Gereken 3 Kritik Bilgi",
            "features": [
                {"icon": "1️⃣", "title": "Ne Zaman Kullanılmalı?", "desc": info["recap_1"]},
                {"icon": "2️⃣", "title": "En Büyük Avantajı Ne?", "desc": info["recap_2"]},
                {"icon": "3️⃣", "title": "Nasıl Ücretsiz Başlanır?", "desc": info["recap_3"]}
            ],
            "footer": "Son Slayt > Bağlantı & DM Rehberi"
        },

        # Slide 6: HIGH CONVERTING CTA (Comment Trigger)
        {
            "slide_number": 6,
            "type": "CTA",
            "badge_icon": "🎁",
            "badge": "ÜCRETSİZ BAĞLANTI & GİZLİ REHBER",
            "title": f"{info['name']} Linkini ve Rehberini İster Misiniz?",
            "cta_box": {
                "badge": "OTOMATİK DM REHBERİ",
                "trigger_word": trigger_word,
                "subtext": f"Yorumlara '{trigger_word}' yazın, tüm giriş bağlantısını ve gizli kullanım rehberini anında DM olarak göndereyim! 📩"
            },
            "footer": "Kaydet & Arkadaşınla Paylaş"
        }
    ]

    return slides
