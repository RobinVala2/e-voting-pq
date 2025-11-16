import httpx, asyncio

SERVER = "http://127.0.0.1:8000"

async def run_hyperion():
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{SERVER}/hyperion")
        print("[HYPERION]", r.json())
