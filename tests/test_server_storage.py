import pytest
import uuid
from unittest.mock import patch
from server import storage


class TestVoterRegistration:
    """Test cases for voter registration in storage."""
    
    def test_register_voter(self):
        """Test voter registration stores data correctly."""
        voter_id = "test_voter"
        h_value = "test_hash"
        
        storage.register_voter(voter_id, h_value)
        
        assert voter_id in storage.secrets_store
        assert storage.secrets_store[voter_id]["h"] == h_value
        assert "g_r" not in storage.secrets_store[voter_id]  # g_r added later
    
    def test_register_multiple_voters(self):
        """Test registering multiple voters."""
        voters_data = [
            ("voter1", "hash1"),
            ("voter2", "hash2"),
            ("voter3", "hash3")
        ]
        
        for voter_id, h_value in voters_data:
            storage.register_voter(voter_id, h_value)
        
        assert len(storage.secrets_store) == 3
        for voter_id, h_value in voters_data:
            assert storage.secrets_store[voter_id]["h"] == h_value


class TestBallotCasting:
    """Test cases for ballot casting in storage."""
    
    def test_cast_ballot(self):
        """Test ballot casting stores data correctly."""
        ballot_data = {
            "voter_id": "test_voter",
            "h": "test_hash",
            "enc_vote": "encrypted_vote",
            "signed_ballot": "signature"
        }
        
        result = storage.cast_ballot(**ballot_data)
        
        assert len(storage.BB) == 1
        assert result["voter_id"] == ballot_data["voter_id"]
        assert result["h"] == ballot_data["h"]
        assert result["enc_vote"] == ballot_data["enc_vote"]
        assert result["signed_ballot"] == ballot_data["signed_ballot"]
        assert "row_id" in result
        
        # Verify UUID format
        uuid.UUID(result["row_id"])  # Should not raise exception
    
    def test_cast_multiple_ballots(self):
        """Test casting multiple ballots."""
        ballots = [
            {
                "voter_id": f"voter{i}",
                "h": f"hash{i}",
                "enc_vote": f"vote{i}",
                "signed_ballot": f"sig{i}"
            }
            for i in range(3)
        ]
        
        results = []
        for ballot in ballots:
            result = storage.cast_ballot(**ballot)
            results.append(result)
        
        assert len(storage.BB) == 3
        
        # Verify all row_ids are unique
        row_ids = [r["row_id"] for r in results]
        assert len(set(row_ids)) == 3
        
        # Verify data integrity
        for i, ballot in enumerate(ballots):
            assert storage.BB[i]["voter_id"] == ballot["voter_id"]
            assert storage.BB[i]["enc_vote"] == ballot["enc_vote"]
    
    def test_cast_ballot_return_structure(self):
        """Test that cast_ballot returns correct structure."""
        result = storage.cast_ballot("voter", "hash", "vote", "sig")
        
        required_fields = ["row_id", "voter_id", "h", "enc_vote", "signed_ballot"]
        for field in required_fields:
            assert field in result


class TestBulletinBoard:
    """Test cases for bulletin board operations."""
    
    def test_get_empty_bb(self):
        """Test getting empty bulletin board."""
        bb = storage.get_bb()
        assert bb == []
        assert isinstance(bb, list)
    
    def test_get_bb_with_data(self):
        """Test getting bulletin board with data."""
        # Add some ballots
        storage.cast_ballot("voter1", "hash1", "vote1", "sig1")
        storage.cast_ballot("voter2", "hash2", "vote2", "sig2")
        
        bb = storage.get_bb()
        
        assert len(bb) == 2
        assert bb[0]["voter_id"] == "voter1"
        assert bb[1]["voter_id"] == "voter2"
    
    def test_bb_reference_integrity(self):
        """Test that get_bb returns reference to actual BB."""
        # Add ballot
        storage.cast_ballot("voter", "hash", "vote", "sig")
        
        bb1 = storage.get_bb()
        bb2 = storage.get_bb()
        
        # Should be same reference
        assert bb1 is bb2
        assert bb1 is storage.BB


class TestTallyOperations:
    """Test cases for tally operations."""
    
    def test_run_tally_empty_bb(self):
        """Test running tally with empty bulletin board."""
        result = storage.run_tally()
        
        assert result == []
        assert isinstance(result, list)
    
    @patch('random.shuffle')
    def test_run_tally_with_ballots(self, mock_shuffle):
        """Test running tally with ballots."""
        # Register voters first
        storage.register_voter("voter1", "hash1")
        storage.register_voter("voter2", "hash2")
        
        # Cast ballots
        ballot1 = storage.cast_ballot("voter1", "hash1", "vote_candidate_A", "sig1")
        ballot2 = storage.cast_ballot("voter2", "hash2", "vote_candidate_B", "sig2")
        
        result = storage.run_tally()
        
        assert len(result) == 2
        assert mock_shuffle.called
        
        # Check result structure
        for tally_entry in result:
            assert "row_id" in tally_entry
            assert "vote" in tally_entry
            assert "h_r" in tally_entry
        
        # Check that votes are preserved (plaintext in this PoC)
        votes = [entry["vote"] for entry in result]
        assert "vote_candidate_A" in votes
        assert "vote_candidate_B" in votes
    
    def test_run_tally_updates_secrets_store(self):
        """Test that tally updates secrets store with g_r values."""
        # Register voter and cast ballot
        storage.register_voter("voter1", "hash1")
        ballot = storage.cast_ballot("voter1", "hash1", "vote", "sig")
        
        # Run tally
        result = storage.run_tally()
        
        # Check that g_r was added to secrets store
        assert "g_r" in storage.secrets_store["voter1"]
        g_r_value = storage.secrets_store["voter1"]["g_r"]
        assert g_r_value.startswith("g_r_")
        assert ballot["row_id"] in g_r_value
        
        # Check that tally result contains matching h_r
        assert result[0]["h_r"] == g_r_value
    
    @patch('random.shuffle')
    def test_tally_shuffles_bb(self, mock_shuffle):
        """Test that tally shuffles the bulletin board."""
        # Add multiple ballots
        for i in range(3):
            storage.register_voter(f"voter{i}", f"hash{i}")
            storage.cast_ballot(f"voter{i}", f"hash{i}", f"vote{i}", f"sig{i}")
        
        storage.run_tally()
        
        # Verify shuffle was called with BB
        mock_shuffle.assert_called_once_with(storage.BB)


class TestNotificationOperations:
    """Test cases for voter notification operations."""
    
    def test_get_notify_nonexistent_voter(self):
        """Test getting notification for non-existent voter."""
        result = storage.get_notify("nonexistent")
        assert result is None
    
    def test_get_notify_registered_voter_no_gr(self):
        """Test getting notification for registered voter without g_r."""
        storage.register_voter("voter1", "hash1")
        
        result = storage.get_notify("voter1")
        
        assert result is not None
        assert result["h"] == "hash1"
        assert "g_r" not in result
    
    def test_get_notify_after_tally(self):
        """Test getting notification after tally (with g_r)."""
        # Register voter and cast ballot
        storage.register_voter("voter1", "hash1")
        storage.cast_ballot("voter1", "hash1", "vote", "sig")
        
        # Run tally to generate g_r
        storage.run_tally()
        
        result = storage.get_notify("voter1")
        
        assert result is not None
        assert result["h"] == "hash1"
        assert "g_r" in result
        assert result["g_r"].startswith("g_r_")


class TestStorageIntegration:
    """Integration tests for storage operations."""
    
    def test_full_voting_flow(self):
        """Test complete voting flow from registration to notification."""
        voter_id = "integration_voter"
        h_value = "integration_hash"
        vote = "candidate_A"
        signature = "integration_sig"
        
        # 1. Register voter
        storage.register_voter(voter_id, h_value)
        assert voter_id in storage.secrets_store
        
        # 2. Cast ballot
        ballot = storage.cast_ballot(voter_id, h_value, vote, signature)
        assert len(storage.BB) == 1
        assert ballot["voter_id"] == voter_id
        
        # 3. Get bulletin board
        bb = storage.get_bb()
        assert len(bb) == 1
        assert bb[0]["row_id"] == ballot["row_id"]
        
        # 4. Run tally
        tally_result = storage.run_tally()
        assert len(tally_result) == 1
        assert tally_result[0]["vote"] == vote
        
        # 5. Get notification
        notification = storage.get_notify(voter_id)
        assert notification is not None
        assert "g_r" in notification
        assert notification["h"] == h_value
    
    def test_multiple_voters_flow(self):
        """Test voting flow with multiple voters."""
        voters = [
            ("voter1", "hash1", "candidate_A"),
            ("voter2", "hash2", "candidate_B"),
            ("voter3", "hash3", "candidate_A")
        ]
        
        # Register all voters
        for voter_id, h_value, _ in voters:
            storage.register_voter(voter_id, h_value)
        
        # Cast all ballots
        for voter_id, h_value, vote in voters:
            storage.cast_ballot(voter_id, h_value, vote, f"sig_{voter_id}")
        
        assert len(storage.BB) == 3
        
        # Run tally
        tally_result = storage.run_tally()
        assert len(tally_result) == 3
        
        # Check all voters can get notifications
        for voter_id, h_value, _ in voters:
            notification = storage.get_notify(voter_id)
            assert notification is not None
            assert "g_r" in notification
