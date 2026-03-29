"""
Test Telegram Connection — Faz 4
Bot token'ını doğrular ve temel API erişimini kontrol eder.

Kullanım: python scripts/test_telegram_connection.py
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

# Env yükle
if os.path.exists(".env"):
    load_dotenv(".env", override=True)
if os.path.exists(".env.local"):
    load_dotenv(".env.local", override=True)

# Token ve ID'leri al
BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_IDS = os.getenv("TELEGRAM_ALLOWED_IDS", "")

async def test_connection():

    print(f"Test: Telegram API (Token: {BOT_TOKEN[:8]}...)...")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url)
            data = resp.json()
            if data.get("ok"):
                bot = data["result"]
                print(f"Success: Connection established!")
                print(f"Bot Name: {bot.get('first_name')}")
                print(f"👤 Username: @{bot.get('username')}")
                print(f"🆔 ID: {bot.get('id')}")
            else:
                print(f"Failed: {data.get('description')}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
