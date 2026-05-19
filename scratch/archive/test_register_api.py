import asyncio
import httpx

async def test_register():
    url = "http://127.0.0.1:8000/api/v1/auth/register"
    data = {
        "email": "test@example.com",
        "password": "password123",
        "username": "testuser"
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=data)
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_register())
