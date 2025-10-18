import httpx, asyncio, secrets, hashlib

SERVER = "http://127.0.0.1:8000"

def gen_trapdoor():
    """
    PoC: generate secret x, and h = sha256(x).
    In real scheme: h = g^x in a group.
    """
    x = secrets.token_hex(16)
    h = hashlib.sha256(x.encode()).hexdigest()
    return x, h

async def register(voter_id, pk_voter, h):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{SERVER}/register", json={
            "voter_id": voter_id,
            "pk_voter": pk_voter,
            "h": h,
            "proof": "zkp-placeholder"
        })
        print("[REGISTER]", r.json())
        return r.json()

async def cast(voter_id, enc_vote, h):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{SERVER}/cast", json={
            "voter_id": voter_id,
            "signed_ballot": "sig_placeholder",
            "enc_vote": enc_vote,
            "h": h,
            "proofs": "proofs-placeholder"
        })
        print("[CAST]", r.json())
        return r.json()

async def notify(voter_id):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{SERVER}/notify/{voter_id}")
        print("[NOTIFY]", r.json())
        return r.json()

async def show_bb():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{SERVER}/bb")
        print("[BULLETIN BOARD]", r.json())
        return r.json()

async def get_tally():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{SERVER}/tally_results")  
        return r.json()
