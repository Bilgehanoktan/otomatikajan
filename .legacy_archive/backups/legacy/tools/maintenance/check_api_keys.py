import os
import asyncio
import httpx
from dotenv import load_dotenv

async def check_openai(key):
    if not key or "your_" in key:
        return False, "Eksik veya placeholder key."
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5}
            )
            if resp.status_code == 200:
                return True, "Geçerli"
            else:
                return False, f"Hata {resp.status_code}: {resp.json().get('error', {}).get('message')}"
    except Exception as e:
        return False, str(e)

async def check_groq(key):
    if not key or "your_" in key:
        return False, "Eksik veya placeholder key."
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": "llama3-8b-8192", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 5}
            )
            if resp.status_code == 200:
                return True, "Geçerli"
            else:
                return False, f"Hata {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, str(e)

async def main():
    # .env.local'ı yükle
    load_dotenv(".env.local")
    
    print("=== API ANAHTARI KONTROLÜ ===")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    ok, msg = await check_openai(openai_key)
    print(f"OpenAI:  [{'OK' if ok else 'FAIL'}] {msg}")
    
    groq_key = os.getenv("GROQ_API_KEY")
    ok, msg = await check_groq(groq_key)
    print(f"Groq:    [{'OK' if ok else 'FAIL'}] {msg}")
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    print(f"Anthropic: {anthropic_key[:10]}... (Kontrol atlandı)")

if __name__ == "__main__":
    asyncio.run(main())
