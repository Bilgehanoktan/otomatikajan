import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).parent.parent.absolute())
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.task_routing import task_router
from observability.logging import get_logger

logger = get_logger("tests.routing_demo")

async def run_routing_test():
    scenarios = [
        {
            "title": "Yeni Mikroservis Mimarisi Tasarla",
            "description": "Sistem için yeni bir ödeme mikroservisi tasarlanacak. Veritabanı şeması ve API dokümantasyonu çıkarılmalı.",
            "expected_hint": "deerflow_plan"
        },
        {
            "title": "Repo Bağımlılık Analizi",
            "description": "Mevcut projedeki paketlerin versiyonlarını ve olası güvenlik açıklarını incele, bir rapor sun.",
            "expected_hint": "deerflow_research"
        },
        {
            "title": "Kod İncelemesi ve Refactoring",
            "description": "Auth modülündeki kodları temizle, SOLID prensiplerine göre tekrar düzenle.",
            "expected_hint": "deerflow_review"
        },
        {
            "title": "Sistem Çökmesi - Acil Müdahale",
            "description": "Üretim ortamındaki sunucular yanıt vermiyor. Logları kontrol et ve sistemi ayağa kaldır.",
            "expected_hint": "deerflow_recovery"
        },
        {
            "title": "Basit Bir Form Oluştur",
            "description": "Kullanıcı kayıt formu için HTML ve CSS dosyası hazırla.",
            "expected_hint": "run_project"
        }
    ]

    print("\n" + "="*60)
    print("      DEERFLOW SEMANTIC ROUTER - CANLI TEST SİMÜLASYONU")
    print("="*60 + "\n")

    for i, s in enumerate(scenarios, 1):
        print(f"TEST {i}: {s['title']}")
        print(f"Detay: {s['description'][:70]}...")
        
        # Router'ı gerçek (veya mock) LLM ile çağır
        decision = await task_router.route_task(s['title'], s['description'])
        
        print(f"KARAR: >>> {decision.upper()} <<<")
        print("-" * 40)

    print("\n[BİTTİ] Router tüm senaryoları başarıyla işledi.")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("UYARI: Hiçbir API anahtarı bulunamadı. Test başarısız olabilir veya fallback kullanabilir.")
        # We could set a fake key just for the mock orchestrator if needed, 
        # but task_router might fail if LLM call fails.
    
    asyncio.run(run_routing_test())
