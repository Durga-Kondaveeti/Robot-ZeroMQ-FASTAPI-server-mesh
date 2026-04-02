# tests/test_user.py
import pytest
from unittest.mock import patch, MagicMock
from cryptography.fernet import Fernet

TEST_KEY = Fernet.generate_key().decode('utf-8')

MOCK_CONFIG = {
    "user_pub_port": 5003,
    "robot_pub_port": 5001,
    "player_pub_port": 5002,
    "secret_key": TEST_KEY
}


@patch("user.main.requests.get")
def test_get_robot_selection_returns_robot(mock_get):
    mock_get.return_value.json.return_value = {"active_robots": ["robot-123"]}

    with patch("user.main.clear_terminal"), \
         patch("builtins.input", return_value="1"):
        from user.main import get_robot_selection
        result = get_robot_selection()

    assert result == "robot-123"


@patch("user.main.requests.get")
def test_get_robot_selection_quit_returns_none(mock_get):
    mock_get.return_value.json.return_value = {"active_robots": ["robot-123"]}

    with patch("user.main.clear_terminal"), \
         patch("builtins.input", return_value="Q"):
        from user.main import get_robot_selection
        result = get_robot_selection()

    assert result is None


@patch("user.main.requests.get")
@patch("user.main.requests.post")
def test_main_exits_if_user_quits_selection(mock_post, mock_get):
    with patch("user.main.clear_terminal"), \
         patch("builtins.input", return_value="Q"), \
         patch("user.main.RobotDashboard") as mock_gui:
        from user.main import main
        main()

    mock_gui.assert_not_called()


@patch("user.main.requests.get")
@patch("user.main.requests.post")
def test_main_launches_dashboard_on_connect(mock_post, mock_get):
    mock_get.return_value.json.return_value = {"active_robots": ["robot-123"]}
    mock_post.return_value.raise_for_status = MagicMock()
    mock_post.return_value.json.return_value = {"mesh_config": MOCK_CONFIG}

    with patch("user.main.clear_terminal"), \
         patch("builtins.input", return_value="1"), \
         patch("user.main.RobotDashboard") as mock_gui:
        mock_gui.return_value.mainloop = MagicMock()
        from user.main import main
        main()

    mock_gui.assert_called_once()
    mock_gui.return_value.mainloop.assert_called_once()


@patch("user.main.requests.get")
@patch("user.main.requests.post")
def test_main_exits_gracefully_if_connect_fails(mock_post, mock_get):
    mock_get.return_value.json.return_value = {"active_robots": ["robot-123"]}
    mock_post.side_effect = Exception("Connection refused")

    with patch("user.main.clear_terminal"), \
         patch("builtins.input", return_value="1"), \
         patch("user.main.RobotDashboard") as mock_gui:
        from user.main import main
        main()

    mock_gui.assert_not_called()
