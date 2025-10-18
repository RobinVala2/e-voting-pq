import httpx, asyncio

SERVER = "http://127.0.0.1:8000"

async def tally():
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{SERVER}/tally")
        print("[TALLY]", r.json())
