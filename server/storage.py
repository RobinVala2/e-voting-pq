import uuid, random

BB = []             # Bulletin board
secrets_store = {}  # voter_id -> {h, g_r?}

def register_voter(voter_id: str, h: str):
    secrets_store[voter_id] = {"h":h}

def cast_ballot(voter_id: str, h: str, enc_vote: str, signed_ballot: str):
    row = {
        "row_id": str(uuid.uuid4()),
        "voter_id": voter_id,
        "h": h,
        "enc_vote": enc_vote,
        "signed_ballot": signed_ballot,
    }
    BB.append(row)
    return row

def get_bb():
    return BB

def run_tally():
    random.shuffle(BB)
    tally = []
    for row in BB:
        plaintext = row["enc_vote"]
        g_r = f"g_r_{row['row_id']}"
        secrets_store[row["voter_id"]]["g_r"] = g_r
        tally.append({"row_id": row["row_id"], "vote": plaintext, "h_r": g_r})
    return tally

def get_notify(voter_id: str):
    return secrets_store.get(voter_id)