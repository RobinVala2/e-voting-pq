import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import hashlib
import httpx
from client.voter import gen_trapdoor, register, cast, notify, show_bb, get_tally


class TestGenTrapdoor:
    """Test cases for trapdoor generation."""
    
    def test_gen_trapdoor_returns_tuple(self):
        """Test that gen_trapdoor returns a tuple."""
        x, h = gen_trapdoor()
        
        assert isinstance(x, str)
        assert isinstance(h, str)
    
    def test_gen_trapdoor_x_length(self):
        """Test that x has expected length (32 hex chars for 16 bytes)."""
        x, h = gen_trapdoor()
        
        assert len(x) == 32  # 16 bytes * 2 (hex encoding)
        # Verify it's valid hex
        int(x, 16)  # Should not raise exception
    
    def test_gen_trapdoor_h_is_sha256(self):
        """Test that h is SHA256 of x."""
        x, h = gen_trapdoor()
        
        expected_h = hashlib.sha256(x.encode()).hexdigest()
        assert h == expected_h
    
    def test_gen_trapdoor_randomness(self):
        """Test that multiple calls produce different values."""
        x1, h1 = gen_trapdoor()
        x2, h2 = gen_trapdoor()
        
        assert x1 != x2
        assert h1 != h2
    
    def test_gen_trapdoor_deterministic_hash(self):
        """Test that same x produces same h."""
        test_x = "1234567890abcdef" * 2  # 32 char hex string
        expected_h = hashlib.sha256(test_x.encode()).hexdigest()
        
        # Monkey patch secrets.token_hex to return our test value
        with patch('client.voter.secrets.token_hex', return_value=test_x):
            x, h = gen_trapdoor()
            
        assert x == test_x
        assert h == expected_h


class TestRegisterFunction:
    """Test cases for voter registration function."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_register_success(self, mock_client_class):
        """Test successful voter registration."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Create mock response with synchronous json() method
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_client.post.return_value = mock_response
        
        result = await register("voter123", "pk_data", "hash_value")
        
        assert result == {"status": "ok"}
        mock_client.post.assert_called_once_with(
            "http://127.0.0.1:8000/register",
            json={
                "voter_id": "voter123",
                "pk_voter": "pk_data",
                "h": "hash_value",
                "proof": "zkp-placeholder"
            }
        )
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_register_http_error(self, mock_client_class):
        """Test registration with HTTP error."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = httpx.RequestError("Connection failed")
        
        with pytest.raises(httpx.RequestError):
            await register("voter123", "pk_data", "hash_value")
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_register_server_error(self, mock_client_class):
        """Test registration with server error response."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "Server error"}
        mock_client.post.return_value = mock_response
        
        result = await register("voter123", "pk_data", "hash_value")
        
        assert result == {"error": "Server error"}
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_register_custom_server(self, mock_client_class):
        """Test registration with custom server URL."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_client.post.return_value = mock_response
        
        # Temporarily change SERVER URL
        import client.voter as voter_module
        original_server = voter_module.SERVER
        voter_module.SERVER = "http://custom-server:9000"
        
        try:
            await register("voter123", "pk_data", "hash_value")
            
            mock_client.post.assert_called_once_with(
                "http://custom-server:9000/register",
                json={
                    "voter_id": "voter123",
                    "pk_voter": "pk_data",
                    "h": "hash_value",
                    "proof": "zkp-placeholder"
                }
            )
        finally:
            voter_module.SERVER = original_server


class TestCastFunction:
    """Test cases for ballot casting function."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_cast_success(self, mock_client_class):
        """Test successful ballot casting."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "row_id": "ballot123"}
        mock_client.post.return_value = mock_response
        
        result = await cast("voter123", "encrypted_vote", "hash_value")
        
        assert result == {"status": "ok", "row_id": "ballot123"}
        mock_client.post.assert_called_once_with(
            "http://127.0.0.1:8000/cast",
            json={
                "voter_id": "voter123",
                "signed_ballot": "sig_placeholder",
                "enc_vote": "encrypted_vote",
                "h": "hash_value",
                "proofs": "proofs-placeholder"
            }
        )
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_cast_http_error(self, mock_client_class):
        """Test casting with HTTP error."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.post.side_effect = httpx.RequestError("Network error")
        
        with pytest.raises(httpx.RequestError):
            await cast("voter123", "encrypted_vote", "hash_value")
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_cast_validation_error(self, mock_client_class):
        """Test casting with validation error response."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "Invalid vote format"}
        mock_client.post.return_value = mock_response
        
        result = await cast("voter123", "invalid_vote", "hash_value")
        
        assert result == {"error": "Invalid vote format"}


class TestNotifyFunction:
    """Test cases for voter notification function."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_notify_success(self, mock_client_class):
        """Test successful voter notification."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"g_r": "notification_data"}
        mock_client.get.return_value = mock_response
        
        result = await notify("voter123")
        
        assert result == {"g_r": "notification_data"}
        mock_client.get.assert_called_once_with("http://127.0.0.1:8000/notify/voter123")
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_notify_voter_not_found(self, mock_client_class):
        """Test notification for non-existent voter."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "Voter not found"}
        mock_client.get.return_value = mock_response
        
        result = await notify("nonexistent_voter")
        
        assert result == {"error": "Voter not found"}
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_notify_no_tally(self, mock_client_class):
        """Test notification when no tally has been run."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "No tally results yet"}
        mock_client.get.return_value = mock_response
        
        result = await notify("voter123")
        
        assert result == {"error": "No tally results yet"}


class TestShowBBFunction:
    """Test cases for bulletin board display function."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_show_bb_success(self, mock_client_class):
        """Test successful bulletin board retrieval."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_bb_data = [
            {"vote": "encrypted_vote_1", "commitment": "commit_1"},
            {"vote": "encrypted_vote_2", "commitment": "commit_2"}
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok", "bb": mock_bb_data}
        mock_client.get.return_value = mock_response
        
        result = await show_bb()
        
        assert result == {"status": "ok", "bb": mock_bb_data}
        mock_client.get.assert_called_once_with("http://127.0.0.1:8000/bb")
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_show_bb_no_data(self, mock_client_class):
        """Test bulletin board when no data available."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "No bulletin board available"}
        mock_client.get.return_value = mock_response
        
        result = await show_bb()
        
        assert result == {"error": "No bulletin board available"}
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_show_bb_http_error(self, mock_client_class):
        """Test bulletin board with HTTP error."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        
        with pytest.raises(httpx.RequestError):
            await show_bb()


class TestGetTallyFunction:
    """Test cases for tally results retrieval."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_tally_success(self, mock_client_class):
        """Test successful tally results retrieval."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_tally_data = {
            "status": "ok",
            "tally": {
                "bulletin_board": [{"vote": "result1"}, {"vote": "result2"}],
                "timings": {"setup": 1.5, "tally": 2.3}
            }
        }
        mock_response = MagicMock()
        mock_response.json.return_value = mock_tally_data
        mock_client.get.return_value = mock_response
        
        result = await get_tally()
        
        assert result == mock_tally_data
        mock_client.get.assert_called_once_with("http://127.0.0.1:8000/tally_results")
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_tally_no_results(self, mock_client_class):
        """Test getting tally when no results available."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "No tally results yet"}
        mock_client.get.return_value = mock_response
        
        result = await get_tally()
        
        assert result == {"error": "No tally results yet"}
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_get_tally_http_error(self, mock_client_class):
        """Test tally retrieval with HTTP error."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = httpx.RequestError("Server unreachable")
        
        with pytest.raises(httpx.RequestError):
            await get_tally()


class TestVoterIntegration:
    """Integration tests for voter client functions."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_full_voting_flow(self, mock_client_class):
        """Test complete voting flow from registration to notification."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock responses for each step
        register_response = MagicMock()
        register_response.json.return_value = {"status": "ok"}
        
        cast_response = MagicMock()
        cast_response.json.return_value = {"status": "ok", "row_id": "ballot123"}
        
        notify_response = MagicMock()
        notify_response.json.return_value = {"g_r": "notification_data"}
        
        mock_client.post.side_effect = [register_response, cast_response]
        mock_client.get.return_value = notify_response
        
        # Generate trapdoor
        x, h = gen_trapdoor()
        
        # Complete flow
        reg_result = await register("voter123", "pk_data", h)
        cast_result = await cast("voter123", "my_vote", h)
        notify_result = await notify("voter123")
        
        assert reg_result["status"] == "ok"
        assert cast_result["status"] == "ok"
        assert "row_id" in cast_result
        assert "g_r" in notify_result
        
        # Verify correct API calls were made
        assert mock_client.post.call_count == 2
        assert mock_client.get.call_count == 1
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient') 
    async def test_error_handling_in_flow(self, mock_client_class):
        """Test error handling in voting flow."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Registration succeeds
        register_response = MagicMock()
        register_response.json.return_value = {"status": "ok"}
        
        # Cast fails
        cast_response = MagicMock()
        cast_response.json.return_value = {"error": "Invalid vote"}
        
        mock_client.post.side_effect = [register_response, cast_response]
        
        x, h = gen_trapdoor()
        
        reg_result = await register("voter123", "pk_data", h)
        cast_result = await cast("voter123", "invalid_vote", h)
        
        assert reg_result["status"] == "ok"
        assert "error" in cast_result
        assert cast_result["error"] == "Invalid vote"
