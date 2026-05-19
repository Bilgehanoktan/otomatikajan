
import httpx
import asyncio

async def test_login():
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                "http://127.0.0.1:8000/api/v1/auth/login/",
                json={"email": "admin@sovereign.agi", "password": "admin1234"}
            )
            print(f"STATUS: {res.status_code}")
        except Exception as e:
            print(f"FAILED: {e}")
    
    print("Waiting 3s for background logs...")
    await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(test_login())
