import httpx
import asyncio
import json

async def trigger():
    url = "http://localhost:8011/run"
    data = {
        "thread_id": "verify-model-test",
        "prompt": "Dene bakalım modelin ne?"
    }
    
    print(f"Sending task to {url} (Form Data)...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, data=data)
            print(f"Status: {response.status_code}")
            print(f"Result: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(trigger())
