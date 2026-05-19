
import httpx
import asyncio

async def test_health():
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get("http://127.0.0.1:8000/api/v1/health/dashboard")
            print(f"STATUS: {res.status_code}")
        except Exception as e:
            print(f"FAILED: {e}")
    
    print("Waiting 3s for background logs...")
    await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(test_health())
