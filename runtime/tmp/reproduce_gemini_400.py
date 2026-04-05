import asyncio
import os
import httpx
from dotenv import load_dotenv

# .env'den yükle
env_path = r"c:\Users\BİLGEHAN\Downloads\ai_company_faz12.1\.env"
load_dotenv(env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

async def reproduce():
    if not GEMINI_API_KEY:
        print("HATA: GEMINI_API_KEY bulunamadı.")
        return

    # ModelOrchestrator'daki mantığı taklit et
    messages = [
        {"role": "system", "content": "Sen bir test asistanısın."},
        {"role": "user", "content": "Merhaba, bu bir testtir."}
    ]
    
    combined_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages])
    contents = [{"parts": [{"text": combined_text}]}]
    max_tokens = 2048
    
    url = f"{BASE_URL}?key={GEMINI_API_KEY}"
    payload = {
        "contents": contents,
        "generationConfig": {"maxOutputTokens": max_tokens}
    }
    
    print(f"İstek gönderiliyor: {url}")
    print(f"Payload: {payload}")
    
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload)
        
        print(f"Durum Kodu: {resp.status_code}")
        try:
            print(f"Yanıt (JSON): {resp.json()}")
        except Exception:
            print(f"Yanıt (Metin): {resp.text}")

if __name__ == "__main__":
    asyncio.run(reproduce())
