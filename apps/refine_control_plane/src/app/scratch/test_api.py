
import httpx
import asyncio

async def test_endpoint():
    async with httpx.AsyncClient() as client:
        # Note: I need an auth token if it's protected.
        # But for now, I just want to see if it's a 500 or 401.
        try:
            r = await client.get("http://localhost:8000/api/v1/governance/governor/cases")
            print(f"Status: {r.status_code}")
            if r.status_code == 500:
                print(f"Body: {r.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoint())
