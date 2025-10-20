import pytest
from unittest.mock import patch, MagicMock
from server import storage


class TestRegistrationEndpoint:
    """Test cases for voter registration endpoint."""
    
    def test_register_voter_success(self, client, sample_voter_data):
        """Test successful voter registration."""
        response = client.post("/register", json=sample_voter_data)
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        
        # Verify voter was stored
        assert sample_voter_data["voter_id"] in storage.secrets_store
        assert storage.secrets_store[sample_voter_data["voter_id"]]["h"] == sample_voter_data["h"]
    
    def test_register_voter_missing_fields(self, client):
        """Test registration with missing required fields."""
        incomplete_data = {"voter_id": "voter123"}
        response = client.post("/register", json=incomplete_data)
        
        assert response.status_code == 422  # Validation error


class TestCastBallotEndpoint:
    """Test cases for ballot casting endpoint."""
    
    def test_cast_ballot_success(self, client, sample_cast_data):
        """Test successful ballot casting."""
        response = client.post("/cast", json=sample_cast_data)
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "ok"
        assert "row_id" in result
        
        # Verify ballot was stored in bulletin board
        assert len(storage.BB) == 1
        assert storage.BB[0]["voter_id"] == sample_cast_data["voter_id"]
        assert storage.BB[0]["enc_vote"] == sample_cast_data["enc_vote"]
    
    def test_cast_ballot_missing_fields(self, client):
        """Test casting with missing required fields."""
        incomplete_data = {"voter_id": "voter123"}
        response = client.post("/cast", json=incomplete_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_multiple_ballots_casting(self, client, sample_cast_data):
        """Test casting multiple ballots."""
        # Cast first ballot
        response1 = client.post("/cast", json=sample_cast_data)
        assert response1.status_code == 200
        
        # Cast second ballot with different voter
        sample_cast_data["voter_id"] = "voter456"
        response2 = client.post("/cast", json=sample_cast_data)
        assert response2.status_code == 200
        
        # Verify both ballots are stored
        assert len(storage.BB) == 2
        assert response1.json()["row_id"] != response2.json()["row_id"]


class TestTallyEndpoint:
    """Test cases for tallying endpoint."""
    
    @patch('server.app.run_hyperion')
    def test_tally_success(self, mock_run_hyperion, client, sample_cast_data):
        """Test successful tallying."""
        # Setup mock return value
        mock_result = {
            "bulletin_board": [{"vote": "test_vote", "commitment": "test_commit"}],
            "timings": {"setup": 1.5, "tally": 2.3},
            "raw_output": "Mock hyperion output"
        }
        mock_run_hyperion.return_value = mock_result
        
        # Cast a ballot first
        client.post("/cast", json=sample_cast_data)
        
        # Run tally
        response = client.post("/tally")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "ok"
        assert "tally" in result
        assert "timings" in result
        assert "raw_output" in result
        assert mock_run_hyperion.called
    
    @patch('server.app.run_hyperion')
    def test_tally_concurrent_request(self, mock_run_hyperion, client):
        """Test concurrent tally requests are rejected."""
        # Mock the RUNNING state to simulate concurrent execution
        import server.app as server_app
        
        # Set RUNNING to True to simulate a tally already in progress
        server_app.RUNNING = True
        
        try:
            # This request should fail because RUNNING is True
            response = client.post("/tally")
            assert response.status_code == 409
            assert "already in progress" in response.json()["detail"]
            
            # Verify run_hyperion was not called due to running state
            mock_run_hyperion.assert_not_called()
        finally:
            # Reset the state
            server_app.RUNNING = False
    
    @patch('server.app.run_hyperion')
    def test_tally_error_handling(self, mock_run_hyperion, client):
        """Test tally error handling."""
        mock_run_hyperion.side_effect = Exception("Hyperion failed")
        
        response = client.post("/tally")
        
        assert response.status_code == 500
        assert "Hyperion failed" in response.json()["detail"]


class TestBulletinBoardEndpoint:
    """Test cases for bulletin board endpoint."""
    
    def test_get_bb_no_tally(self, client):
        """Test getting bulletin board before any tally."""
        response = client.get("/bb")
        
        assert response.status_code == 404
        assert "No bulletin board available" in response.json()["detail"]
    
    @patch('server.app.run_hyperion')
    def test_get_bb_after_tally(self, mock_run_hyperion, client):
        """Test getting bulletin board after tally."""
        mock_result = {
            "bulletin_board": [{"vote": "test_vote", "commitment": "test_commit"}],
            "timings": {},
            "raw_output": ""
        }
        mock_run_hyperion.return_value = mock_result
        
        # Run tally first
        client.post("/tally")
        
        # Get bulletin board
        response = client.get("/bb")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "ok"
        assert "bb" in result
        assert result["bb"] == mock_result["bulletin_board"]


class TestTallyResultsEndpoint:
    """Test cases for tally results endpoint."""
    
    def test_get_tally_results_no_tally(self, client):
        """Test getting tally results before any tally."""
        response = client.get("/tally_results")
        
        assert response.status_code == 404
        assert "No tally results yet" in response.json()["detail"]
    
    @patch('server.app.run_hyperion')
    def test_get_tally_results_after_tally(self, mock_run_hyperion, client):
        """Test getting tally results after tally."""
        mock_result = {
            "bulletin_board": [{"vote": "test_vote", "commitment": "test_commit"}],
            "timings": {"setup": 1.5},
            "raw_output": "output"
        }
        mock_run_hyperion.return_value = mock_result
        
        # Run tally first
        client.post("/tally")
        
        # Get tally results
        response = client.get("/tally_results")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "ok"
        assert "tally" in result
        assert result["tally"] == mock_result


class TestNotificationEndpoint:
    """Test cases for voter notification endpoint."""
    
    def test_notify_no_tally(self, client):
        """Test notification before any tally."""
        response = client.get("/notify/voter123")
        
        assert response.status_code == 404
        assert "No tally results yet" in response.json()["detail"]
    
    def test_notify_voter_not_found(self, client):
        """Test notification for non-existent voter."""
        # Mock that tally has run
        from server.app import LAST_TALLY
        with patch('server.app.LAST_TALLY', {"some": "result"}):
            response = client.get("/notify/nonexistent_voter")
            
            assert response.status_code == 404
            assert "No notification for voter" in response.json()["detail"]
    
    @patch('server.app.run_hyperion')
    def test_notify_success(self, mock_run_hyperion, client, sample_voter_data, sample_cast_data):
        """Test successful voter notification."""
        mock_result = {
            "bulletin_board": [{"vote": "test_vote", "commitment": "test_commit"}],
            "timings": {},
            "raw_output": ""
        }
        mock_run_hyperion.return_value = mock_result
        
        # Register voter and cast ballot
        client.post("/register", json=sample_voter_data)
        client.post("/cast", json=sample_cast_data)
        
        # Run tally (this will populate g_r in storage)
        client.post("/tally")
        
        # Add g_r to voter's stored data manually for testing
        storage.secrets_store[sample_voter_data["voter_id"]]["g_r"] = "test_g_r_value"
        
        # Test notification
        response = client.get(f"/notify/{sample_voter_data['voter_id']}")
        
        assert response.status_code == 200
        result = response.json()
        assert "g_r" in result
        assert result["g_r"] == "test_g_r_value"
