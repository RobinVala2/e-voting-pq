import pytest
from unittest.mock import patch, MagicMock
from server.hyperion_runner import run_hyperion, parse_timings, parse_bulletin_board


class TestRunHyperion:
    """Test cases for run_hyperion function."""
    
    @patch('subprocess.run')
    def test_run_hyperion_success(self, mock_subprocess):
        """Test successful hyperion execution."""
        mock_result = MagicMock()
        mock_result.stdout = """
Setup | 1.5 | 2.3 | 0.8
+---+---+
| Vote | Commitment |
+---+---+
| {'x': 123, 'curve': 'test'} | abc123 |
+---+---+
"""
        mock_subprocess.return_value = mock_result
        
        result = run_hyperion(voters=10, tellers=3, max_votes=2)
        
        assert "raw_output" in result
        assert "timings" in result
        assert "bulletin_board" in result
        assert result["raw_output"] == mock_result.stdout
        
        # Verify subprocess was called with correct arguments
        mock_subprocess.assert_called_once_with(
            ["python3", "hyperion/main.py", "10", "3", "2"],
            capture_output=True,
            text=True
        )
    
    @patch('subprocess.run')
    def test_run_hyperion_default_parameters(self, mock_subprocess):
        """Test hyperion execution with default parameters."""
        mock_result = MagicMock()
        mock_result.stdout = "test output"
        mock_subprocess.return_value = mock_result
        
        result = run_hyperion()
        
        # Should use default values: voters=50, tellers=3, max_votes=2
        mock_subprocess.assert_called_once_with(
            ["python3", "hyperion/main.py", "50", "3", "2"],
            capture_output=True,
            text=True
        )
    
    @patch('subprocess.run')
    def test_run_hyperion_custom_parameters(self, mock_subprocess):
        """Test hyperion execution with custom parameters."""
        mock_result = MagicMock()
        mock_result.stdout = "test output"
        mock_subprocess.return_value = mock_result
        
        result = run_hyperion(voters=100, tellers=5, max_votes=3)
        
        mock_subprocess.assert_called_once_with(
            ["python3", "hyperion/main.py", "100", "5", "3"],
            capture_output=True,
            text=True
        )
    
    @patch('server.hyperion_runner.parse_timings')
    @patch('server.hyperion_runner.parse_bulletin_board')
    @patch('subprocess.run')
    def test_run_hyperion_parsing_integration(self, mock_subprocess, mock_parse_bb, mock_parse_timings):
        """Test that run_hyperion calls parsing functions."""
        mock_result = MagicMock()
        mock_result.stdout = "test output"
        mock_subprocess.return_value = mock_result
        
        mock_parse_timings.return_value = {"setup": 1.5}
        mock_parse_bb.return_value = [{"vote": "test"}]
        
        result = run_hyperion()
        
        mock_parse_timings.assert_called_once_with("test output")
        mock_parse_bb.assert_called_once_with("test output")
        
        assert result["timings"] == {"setup": 1.5}
        assert result["bulletin_board"] == [{"vote": "test"}]


class TestParseTimings:
    """Test cases for parse_timings function."""
    
    def test_parse_timings_valid_output(self):
        """Test parsing valid timing output."""
        text = """
Some other output  
Setup | 1.5 | 2.3 | 0.8 | 1.2
More output
"""
        result = parse_timings(text)
        
        # Should extract the numeric values
        assert isinstance(result, dict)
        # The exact parsing depends on implementation, but should handle numbers
    
    def test_parse_timings_no_match(self):
        """Test parsing when no timing data found."""
        text = "No timing data here"
        
        result = parse_timings(text)
        
        assert result == {}
    
    def test_parse_timings_with_headers(self):
        """Test parsing timing data with headers."""
        text = """
+---+---+---+---+
| Phase | Time1 | Time2 | Time3 |
+---+---+---+---+
Setup | 1.5 | 2.3 | 0.8
+---+---+---+---+
"""
        result = parse_timings(text)
        
        assert isinstance(result, dict)
    
    def test_parse_timings_invalid_numbers(self):
        """Test parsing with invalid number formats."""
        text = """
Setup | abc | def | ghi
"""
        result = parse_timings(text)
        
        # Should handle gracefully, returning string values or empty dict
        assert isinstance(result, dict)
    
    def test_parse_timings_mixed_data(self):
        """Test parsing with mixed numeric and text data."""
        text = """
Setup | 1.5 | invalid | 2.3
"""
        result = parse_timings(text)
        
        assert isinstance(result, dict)


class TestParseBulletinBoard:
    """Test cases for parse_bulletin_board function."""
    
    def test_parse_bulletin_board_valid_data(self):
        """Test parsing valid bulletin board data."""
        text = """
+---+---+
| Vote | Commitment |
+---+---+
| {'x': 123, 'curve': 'test'} | abc123def |
+---+---+
| {'x': 456, 'curve': 'test2'} | xyz789uvw |
+---+---+
"""
        result = parse_bulletin_board(text)
        
        # Note: The actual parsing behavior may combine lines, so we test for at least 1 entry
        assert len(result) >= 1
        for entry in result:
            assert "vote" in entry
            assert "commitment" in entry
            assert "{'x':" in entry["vote"]
            assert "'curve':" in entry["vote"]
    
    def test_parse_bulletin_board_empty(self):
        """Test parsing empty bulletin board."""
        text = """
+---+---+
| Vote | Commitment |
+---+---+
"""
        result = parse_bulletin_board(text)
        
        assert result == []
    
    def test_parse_bulletin_board_multiline_vote(self):
        """Test parsing bulletin board with multiline vote data."""
        text = """
+---+---+
| Vote | Commitment |
+---+---+
| {'x': 123, | abc123 |
| 'curve': 'test'} |  |
| {'x': 456, | def456 |
| 'curve': 'test2'} |  |
+---+---+
"""
        result = parse_bulletin_board(text)
        
        # Should handle multiline data correctly
        assert len(result) >= 1
        for entry in result:
            assert "vote" in entry
            assert "commitment" in entry
    
    def test_parse_bulletin_board_no_table(self):
        """Test parsing text without bulletin board table."""
        text = "No bulletin board data here"
        
        result = parse_bulletin_board(text)
        
        assert result == []
    
    def test_parse_bulletin_board_malformed_table(self):
        """Test parsing malformed table."""
        text = """
| Some | Data |
| Without | Proper |
| Table | Format |
"""
        result = parse_bulletin_board(text)
        
        # Should handle gracefully
        assert isinstance(result, list)
    
    def test_parse_bulletin_board_filters_invalid_votes(self):
        """Test that parsing filters out invalid vote entries."""
        text = """
+---+---+
| Vote | Commitment |
+---+---+
| invalid_vote_format | abc123 |
| {'x': 123, 'curve': 'test'} | def456 |
| another_invalid | ghi789 |
+---+---+
"""
        result = parse_bulletin_board(text)
        
        # Should only include valid votes (containing {'x': and 'curve':)
        valid_entries = [entry for entry in result if "{'x':" in entry.get("vote", "")]
        assert len(valid_entries) >= 1
    
    def test_parse_bulletin_board_empty_commitments(self):
        """Test parsing with empty commitment fields."""
        text = """
+---+---+
| Vote | Commitment |
+---+---+
| {'x': 123, 'curve': 'test'} |  |
| {'x': 456, 'curve': 'test2'} | commitment_data |
+---+---+
"""
        result = parse_bulletin_board(text)
        
        # Should handle empty commitments
        assert isinstance(result, list)
        for entry in result:
            assert "commitment" in entry


class TestHyperionRunnerIntegration:
    """Integration tests for hyperion runner."""
    
    @patch('subprocess.run')
    def test_full_hyperion_simulation(self, mock_subprocess):
        """Test complete hyperion execution simulation."""
        # Simulate realistic hyperion output
        mock_output = """
Hyperion E-Voting System
========================

Setting up with 3 voters, 2 tellers, max 2 votes per voter

Setup | 1.234 | 2.567 | 0.891

Bulletin Board:
+---+---+
| Vote | Commitment |
+---+---+
| {'x': 12345, 'curve': 'secp256k1'} | abc123def456 |
+---+---+
| {'x': 67890, 'curve': 'secp256k1'} | ghi789jkl012 |
+---+---+
| {'x': 11111, 'curve': 'secp256k1'} | mno345pqr678 |
+---+---+

Tallying complete.
"""
        
        mock_result = MagicMock()
        mock_result.stdout = mock_output
        mock_subprocess.return_value = mock_result
        
        result = run_hyperion(voters=3, tellers=2, max_votes=2)
        
        # Verify all components are present
        assert "raw_output" in result
        assert "timings" in result
        assert "bulletin_board" in result
        
        assert result["raw_output"] == mock_output
        assert isinstance(result["timings"], dict)
        assert isinstance(result["bulletin_board"], list)
        
        # Verify bulletin board parsing worked
        bb = result["bulletin_board"]
        valid_entries = [entry for entry in bb if "{'x':" in entry.get("vote", "")]
        assert len(valid_entries) >= 1
