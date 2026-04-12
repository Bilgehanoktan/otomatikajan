"""
Register Telegram Bot Commands — Faz 4
Bot komutlarını Telegram API'sine kaydeder.
Komutlar botun "/" menüsünde görünecektir.

Kullanım: python scripts/register_telegram_commands.py
"""

import os
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv

if os.path.exists(".env"):
    load_dotenv(".env", override=False)
if os.path.exists(".env.local"):
    load_dotenv(".env.local", override=False)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

COMMANDS = [
    {"command": "start",    "description": "Botu başlat"},
    {"command": "help",     "description": "Komut listesi"},
    {"command": "status",   "description": "Sistem durumu"},
    {"command": "tasks",    "description": "Son görevler"},
    {"command": "task",     "description": "Görev detayı: /task <id>"},
    {"command": "newtask",  "description": "Yeni görev: /newtask başlık | açıklama"},
    {"command": "agents",   "description": "Ajan durumu"},
    {"command": "logs",     "description": "Son sistem logları"},
    {"command": "errors",   "description": "Son hatalar"},
    {"command": "queue",    "description": "Kuyruk durumu"},
    {"command": "metrics",  "description": "Performans metrikleri"},
    {"command": "incidents","description": "Faz 11: Açık incident'ler"},
    {"command": "repair",   "description": "Faz 11: Repair job başlat"},
    {"command": "proposals","description": "Faz 11: Bekleyen PR önerileri"},
]

async def register():
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set!")
        return

    print(f"Registering Bot Commands (Token: {BOT_TOKEN[:8]}...)...")
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(url, json={"commands": COMMANDS})
            data = resp.json()
            if data.get("ok"):
                print("Success: Telegram commands registered.")
            else:
                print(f"Failed: {data.get('description')}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(register())
