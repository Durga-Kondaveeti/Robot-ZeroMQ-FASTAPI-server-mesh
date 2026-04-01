# tests/test_user.py
import pytest
from unittest.mock import patch, MagicMock


@patch("user.main.requests.get")
def test_lists_active_robots(mock_get, capsys):
    mock_get.return_value.json.return_value = {"active_robots": ["robot-123-4567"]}
    
    from user.main import main
    main()
    
    captured = capsys.readouterr()
    assert "robot-123-4567" in captured.out


@patch("user.main.requests.get")
def test_no_active_robots(mock_get, capsys):
    mock_get.return_value.json.return_value = {"active_robots": []}
    
    from user.main import main
    main()
    
    captured = capsys.readouterr()
    assert "No active robots found" in captured.out


@patch("user.main.requests.get")
def test_cloud_unreachable(mock_get, capsys):
    mock_get.side_effect = Exception("Connection refused")
    
    from user.main import main
    main()
    
    captured = capsys.readouterr()
    assert "Error fetching robots" in captured.out