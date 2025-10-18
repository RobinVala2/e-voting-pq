from fastapi import FastAPI, HTTPException
from .models import RegisterReq, CastReq
from . import storage
from .hyperion_runner import run_hyperion
import asyncio

app = FastAPI(title="Hyperion PoC")
LAST_TALLY = None
LAST_BB = None
RUNNING = False

# ---------- Registration and voting endpoints ----------
@app.post("/register")
async def register(req: RegisterReq):
    storage.register_voter(req.voter_id, req.h)
    return {"status": "ok"}

@app.post("/cast")
async def cast(req: CastReq):
    row = storage.cast_ballot(req.voter_id, req.h, req.enc_vote, req.signed_ballot)
    return {"status": "ok", "row_id": row["row_id"]}

# ---------- Tallying ----------
@app.post("/tally")
async def tally():
    global LAST_TALLY, LAST_BB, RUNNING
    if RUNNING:
        raise HTTPException(status_code=409, detail="Hyperion run already in progress")
    try:
        RUNNING = True
        # Run in background thread to not block event loop
        result = await asyncio.to_thread(run_hyperion)
        LAST_TALLY = result
        LAST_BB = result["bulletin_board"]
        return {
            "status": "ok",
            "tally": result["bulletin_board"],
            "timings": result["timings"],
            "raw_output": result["raw_output"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        RUNNING = False

# ---------- Bulletin board ----------
@app.get("/bb")
async def get_bb():
    if LAST_BB:
        return {"status": "ok", "bb": LAST_BB}
    raise HTTPException(status_code=404, detail="No bulletin board available. Run /tally first.")

# ---------- Tally results ----------
@app.get("/tally_results")
async def tally_results():
    if LAST_TALLY:
        return {"status": "ok", "tally": LAST_TALLY}
    raise HTTPException(status_code=404, detail="No tally results yet. Run /tally first.")

# --- Notification (example placeholder) ---
@app.get("/notify/{voter_id}")
async def notify(voter_id: str):
    if not LAST_TALLY:
        raise HTTPException(status_code=404, detail="No tally results yet.")
    # Placeholder: extract something from LAST_TALLY if needed
    info = storage.get_notify(voter_id)
    if not info or "g_r" not in info:
        raise HTTPException(status_code=404, detail="No notification for voter.")
    return {"g_r": info["g_r"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
