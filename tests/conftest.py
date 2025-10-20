import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server.app import app
from server import storage

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_storage():
    """Reset storage and app state before each test."""
    storage.BB.clear()
    storage.secrets_store.clear()
    
    # Reset app globals
    import server.app as server_app
    server_app.LAST_TALLY = None
    server_app.LAST_BB = None
    server_app.RUNNING = False
    
    yield
    
    storage.BB.clear()
    storage.secrets_store.clear()
    server_app.LAST_TALLY = None
    server_app.LAST_BB = None
    server_app.RUNNING = False

@pytest.fixture
def sample_voter_data():
    """Sample voter data for testing."""
    return {
        "voter_id": "voter123",
        "pk_voter": "pk_test_key",
        "h": "hash123456",
        "proof": "zkp-test-proof"
    }

@pytest.fixture
def sample_cast_data():
    """Sample cast ballot data for testing."""
    return {
        "voter_id": "voter123",
        "signed_ballot": "signature123",
        "enc_vote": "encrypted_vote_data",
        "h": "hash123456",
        "proofs": "proof_data"
    }
