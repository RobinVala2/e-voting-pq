from pydantic import BaseModel

class RegisterReq(BaseModel):
    voter_id: str
    pk_voter: str
    h: str
    proof: str

class CastReq(BaseModel):
    voter_id: str
    signed_ballot: str
    enc_vote: str
    h: str
    proofs: str