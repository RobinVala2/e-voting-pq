import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
from client.admin import tally


class TestTallyFunction:
    """Test cases for admin tally function."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_tally_success(self, mock_client_class):
        """Test successful tally execution."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "tally": [
                {"vote": "candidate_A", "commitment": "commit1"},
                {"vote": "candidate_B", "commitment": "commit2"}
            ],
            "timings": {"setup": 1.5, "tally": 2.3, "verification": 0.8},
            "raw_output": "Hyperion execution completed successfully"
        }
        mock_client.post.return_value = mock_response
        
        # Execute tally
        await tally()
        
        # Verify API call was made
        mock_client.post.assert_called_once_with("http://127.0.0.1:8000/tally")
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_tally_http_error(self, mock_client_class):
        """Test tally with HTTP error."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = httpx.RequestError("Connection failed")
        
        with pytest.raises(httpx.RequestError):
            await tally()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_tally_server_error(self, mock_client_class):
        """Test tally with server error response."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": "Hyperion execution failed",
            "details": "Insufficient ballots for tallying"
        }
        mock_client.post.return_value = mock_response
        
        # Should not raise exception, just print the error
        await tally()
        
        mock_client.post.assert_called_once_with("http://127.0.0.1:8000/tally")
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_tally_concurrent_execution(self, mock_client_class):
        """Test tally when another tally is already running."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "error": "Hyperion run already in progress",
            "status_code": 409
        }
        mock_client.post.return_value = mock_response
        
        await tally()
        
        mock_client.post.assert_called_once_with("http://127.0.0.1:8000/tally")
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_tally_empty_response(self, mock_client_class):
        """Test tally with empty bulletin board."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "tally": [],
            "timings": {"setup": 0.1, "tally": 0.0, "verification": 0.0},
            "raw_output": "No ballots to tally"
        }
        mock_client.post.return_value = mock_response
        
        await tally()
        
        mock_client.post.assert_called_once_with("http://127.0.0.1:8000/tally")
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_tally_timeout_error(self, mock_client_class):
        """Test tally with timeout error."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = httpx.TimeoutException("Request timed out")
        
        with pytest.raises(httpx.TimeoutException):
            await tally()
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_tally_custom_server(self, mock_client_class):
        """Test tally with custom server URL."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "tally": [], "timings": {}, "raw_output": ""}
        mock_client.post.return_value = mock_response
        
        # Temporarily change SERVER URL
        import client.admin as admin_module
        original_server = admin_module.SERVER
        admin_module.SERVER = "http://custom-admin-server:9001"
        
        try:
            await tally()
            
            mock_client.post.assert_called_once_with("http://custom-admin-server:9001/tally")
        finally:
            admin_module.SERVER = original_server
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_tally_response_format(self, mock_client_class):
        """Test that tally handles various response formats."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Test with minimal response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok"
        }
        mock_client.post.return_value = mock_response
        
        await tally()
        
        # Test with full response
        mock_response.json.return_value = {
            "status": "ok",
            "tally": [{"vote": "test_vote", "commitment": "test_commit"}],
            "timings": {"setup": 1.0, "tally": 2.0, "verification": 1.0},
            "raw_output": "Full hyperion output with details..."
        }
        
        await tally()
        
        assert mock_client.post.call_count == 2
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_tally_json_decode_error(self, mock_client_class):
        """Test tally with invalid JSON response."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_client.post.return_value = mock_response
        
        # The tally function propagates JSON decode errors because r.json() is called in print()
        with pytest.raises(ValueError, match="Invalid JSON"):
            await tally()


class TestAdminIntegration:
    """Integration tests for admin functionality."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_admin_workflow_simulation(self, mock_client_class):
        """Test complete admin workflow simulation."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Simulate realistic tally response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "ok",
            "tally": [
                {"vote": "{'candidate': 'Alice', 'encrypted': true}", "commitment": "commit_abc123"},
                {"vote": "{'candidate': 'Bob', 'encrypted': true}", "commitment": "commit_def456"},
                {"vote": "{'candidate': 'Alice', 'encrypted': true}", "commitment": "commit_ghi789"}
            ],
            "timings": {
                "setup": 1.234,
                "tally": 3.567,
                "verification": 0.891,
                "total": 5.692
            },
            "raw_output": """
Hyperion E-Voting System
========================
Voters: 3, Tellers: 2, Max votes per voter: 1

Setup phase: 1.234s
Tallying phase: 3.567s
Verification phase: 0.891s
Total time: 5.692s

Results:
Alice: 2 votes
Bob: 1 vote

Tallying completed successfully.
"""
        }
        mock_client.post.return_value = mock_response
        
        # Execute admin tally
        await tally()
        
        # Verify the call was made correctly
        mock_client.post.assert_called_once_with("http://127.0.0.1:8000/tally")
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_multiple_tally_attempts(self, mock_client_class):
        """Test multiple tally attempts (should fail after first)."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # First call succeeds
        success_response = MagicMock()
        success_response.json.return_value = {
            "status": "ok",
            "tally": [],
            "timings": {},
            "raw_output": "First tally completed"
        }
        
        # Second call fails (already running)
        conflict_response = MagicMock()
        conflict_response.json.return_value = {
            "error": "Hyperion run already in progress",
            "status_code": 409
        }
        
        mock_client.post.side_effect = [success_response, conflict_response]
        
        # First tally should succeed
        await tally()
        
        # Second tally should handle conflict gracefully
        await tally()
        
        assert mock_client.post.call_count == 2
