import pytest
from pydantic import ValidationError
from server.models import RegisterReq, CastReq


class TestRegisterReq:
    """Test cases for RegisterReq model."""
    
    def test_valid_register_request(self):
        """Test creating valid register request."""
        data = {
            "voter_id": "voter123",
            "pk_voter": "public_key_data",
            "h": "hash_value",
            "proof": "zero_knowledge_proof"
        }
        
        req = RegisterReq(**data)
        
        assert req.voter_id == data["voter_id"]
        assert req.pk_voter == data["pk_voter"]
        assert req.h == data["h"]
        assert req.proof == data["proof"]
    
    def test_register_request_missing_voter_id(self):
        """Test register request without voter_id."""
        data = {
            "pk_voter": "public_key_data",
            "h": "hash_value",
            "proof": "zero_knowledge_proof"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RegisterReq(**data)
        
        error = exc_info.value.errors()[0]
        assert error["loc"] == ("voter_id",)
        assert error["type"] == "missing"
    
    def test_register_request_missing_pk_voter(self):
        """Test register request without pk_voter."""
        data = {
            "voter_id": "voter123",
            "h": "hash_value",
            "proof": "zero_knowledge_proof"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RegisterReq(**data)
        
        error = exc_info.value.errors()[0]
        assert error["loc"] == ("pk_voter",)
        assert error["type"] == "missing"
    
    def test_register_request_missing_h(self):
        """Test register request without h."""
        data = {
            "voter_id": "voter123",
            "pk_voter": "public_key_data",
            "proof": "zero_knowledge_proof"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RegisterReq(**data)
        
        error = exc_info.value.errors()[0]
        assert error["loc"] == ("h",)
        assert error["type"] == "missing"
    
    def test_register_request_missing_proof(self):
        """Test register request without proof."""
        data = {
            "voter_id": "voter123",
            "pk_voter": "public_key_data",
            "h": "hash_value"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RegisterReq(**data)
        
        error = exc_info.value.errors()[0]
        assert error["loc"] == ("proof",)
        assert error["type"] == "missing"
    
    def test_register_request_empty_strings(self):
        """Test register request with empty strings."""
        data = {
            "voter_id": "",
            "pk_voter": "",
            "h": "",
            "proof": ""
        }
        
        req = RegisterReq(**data)
        
        # Pydantic allows empty strings by default
        assert req.voter_id == ""
        assert req.pk_voter == ""
        assert req.h == ""
        assert req.proof == ""
    
    def test_register_request_extra_fields(self):
        """Test register request with extra fields."""
        data = {
            "voter_id": "voter123",
            "pk_voter": "public_key_data",
            "h": "hash_value",
            "proof": "zero_knowledge_proof",
            "extra_field": "should_be_ignored"
        }
        
        req = RegisterReq(**data)
        
        # Extra fields should be ignored
        assert not hasattr(req, "extra_field")
        assert req.voter_id == data["voter_id"]


class TestCastReq:
    """Test cases for CastReq model."""
    
    def test_valid_cast_request(self):
        """Test creating valid cast request."""
        data = {
            "voter_id": "voter123",
            "signed_ballot": "digital_signature",
            "enc_vote": "encrypted_vote_data",
            "h": "hash_value",
            "proofs": "validity_proofs"
        }
        
        req = CastReq(**data)
        
        assert req.voter_id == data["voter_id"]
        assert req.signed_ballot == data["signed_ballot"]
        assert req.enc_vote == data["enc_vote"]
        assert req.h == data["h"]
        assert req.proofs == data["proofs"]
    
    def test_cast_request_missing_voter_id(self):
        """Test cast request without voter_id."""
        data = {
            "signed_ballot": "digital_signature",
            "enc_vote": "encrypted_vote_data",
            "h": "hash_value",
            "proofs": "validity_proofs"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CastReq(**data)
        
        error = exc_info.value.errors()[0]
        assert error["loc"] == ("voter_id",)
        assert error["type"] == "missing"
    
    def test_cast_request_missing_signed_ballot(self):
        """Test cast request without signed_ballot."""
        data = {
            "voter_id": "voter123",
            "enc_vote": "encrypted_vote_data",
            "h": "hash_value",
            "proofs": "validity_proofs"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CastReq(**data)
        
        error = exc_info.value.errors()[0]
        assert error["loc"] == ("signed_ballot",)
        assert error["type"] == "missing"
    
    def test_cast_request_missing_enc_vote(self):
        """Test cast request without enc_vote."""
        data = {
            "voter_id": "voter123",
            "signed_ballot": "digital_signature",
            "h": "hash_value",
            "proofs": "validity_proofs"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CastReq(**data)
        
        error = exc_info.value.errors()[0]
        assert error["loc"] == ("enc_vote",)
        assert error["type"] == "missing"
    
    def test_cast_request_missing_h(self):
        """Test cast request without h."""
        data = {
            "voter_id": "voter123",
            "signed_ballot": "digital_signature",
            "enc_vote": "encrypted_vote_data",
            "proofs": "validity_proofs"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CastReq(**data)
        
        error = exc_info.value.errors()[0]
        assert error["loc"] == ("h",)
        assert error["type"] == "missing"
    
    def test_cast_request_missing_proofs(self):
        """Test cast request without proofs."""
        data = {
            "voter_id": "voter123",
            "signed_ballot": "digital_signature",
            "enc_vote": "encrypted_vote_data",
            "h": "hash_value"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CastReq(**data)
        
        error = exc_info.value.errors()[0]
        assert error["loc"] == ("proofs",)
        assert error["type"] == "missing"
    
    def test_cast_request_empty_strings(self):
        """Test cast request with empty strings."""
        data = {
            "voter_id": "",
            "signed_ballot": "",
            "enc_vote": "",
            "h": "",
            "proofs": ""
        }
        
        req = CastReq(**data)
        
        # Pydantic allows empty strings by default
        assert req.voter_id == ""
        assert req.signed_ballot == ""
        assert req.enc_vote == ""
        assert req.h == ""
        assert req.proofs == ""
    
    def test_cast_request_extra_fields(self):
        """Test cast request with extra fields."""
        data = {
            "voter_id": "voter123",
            "signed_ballot": "digital_signature",
            "enc_vote": "encrypted_vote_data",
            "h": "hash_value",
            "proofs": "validity_proofs",
            "timestamp": "should_be_ignored",
            "extra_data": "also_ignored"
        }
        
        req = CastReq(**data)
        
        # Extra fields should be ignored
        assert not hasattr(req, "timestamp")
        assert not hasattr(req, "extra_data")
        assert req.voter_id == data["voter_id"]


class TestModelSerialization:
    """Test cases for model serialization."""
    
    def test_register_req_json_serialization(self):
        """Test RegisterReq JSON serialization."""
        data = {
            "voter_id": "voter123",
            "pk_voter": "public_key_data",
            "h": "hash_value",
            "proof": "zero_knowledge_proof"
        }
        
        req = RegisterReq(**data)
        json_data = req.model_dump()
        
        assert json_data == data
    
    def test_cast_req_json_serialization(self):
        """Test CastReq JSON serialization."""
        data = {
            "voter_id": "voter123",
            "signed_ballot": "digital_signature",
            "enc_vote": "encrypted_vote_data",
            "h": "hash_value",
            "proofs": "validity_proofs"
        }
        
        req = CastReq(**data)
        json_data = req.model_dump()
        
        assert json_data == data
    
    def test_register_req_from_json(self):
        """Test creating RegisterReq from JSON."""
        json_str = '{"voter_id": "voter123", "pk_voter": "pk", "h": "hash", "proof": "proof"}'
        
        import json
        data = json.loads(json_str)
        req = RegisterReq(**data)
        
        assert req.voter_id == "voter123"
        assert req.pk_voter == "pk"
        assert req.h == "hash"
        assert req.proof == "proof"
    
    def test_cast_req_from_json(self):
        """Test creating CastReq from JSON."""
        json_str = '{"voter_id": "voter123", "signed_ballot": "sig", "enc_vote": "vote", "h": "hash", "proofs": "proofs"}'
        
        import json
        data = json.loads(json_str)
        req = CastReq(**data)
        
        assert req.voter_id == "voter123"
        assert req.signed_ballot == "sig"
        assert req.enc_vote == "vote"
        assert req.h == "hash"
        assert req.proofs == "proofs"
