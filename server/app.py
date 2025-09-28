from fastapi import FastAPI, HTTPException
from server.models import RegisterReq, CastReq
from server import storage

app = FastAPI(title="Hyperion PoC")
LAST_TALLY = None

@app.post("/register")
async def register(req: RegisterReq):
    storage.register_voter(req.voter_id, req.h)
    return {"status": "ok"}

@app.post("/cast")
async def cast(req: CastReq):
    row = storage.cast_ballot(req.voter_id, req.h, req.enc_vote, req.signed_ballot)
    return {"status": "ok", "row_id": row["row_id"]}

@app.get("/bb")
async def get_bb():
    return {"bb": storage.get_bb()}

@app.post("/tally")
async def tally():
    global LAST_TALLY
    tally_result = storage.run_tally()
    LAST_TALLY = tally_result
    return {"status": "ok", "tally": tally_result}

@app.get("/tally_results")
async def tally_results():
    if not LAST_TALLY:
        raise HTTPException(status_code=404, detail="No tally results yet")
    return {"tally": LAST_TALLY}

@app.get("/notify/{voter_id}")
async def notify(voter_id: str):
    info = storage.get_notify(voter_id)
    if not info or "g_r" not in info:
        raise HTTPException(status_code=404, detail="no notification yet")
    return {"g_r": info["g_r"]}