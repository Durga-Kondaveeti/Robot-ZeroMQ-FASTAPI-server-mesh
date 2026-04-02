# tests/test_robot.py
import pytest
from unittest.mock import patch, MagicMock
from robot.jetbot import FakeJetbot


@pytest.fixture
def bot():
    return FakeJetbot()


def test_initial_state(bot):
    assert bot.status == "idle"
    assert bot.location == [0.0, 0.0]


def test_forward(bot):
    bot.forward()
    assert bot.status == "moving_forward"
    assert bot.location[1] == 1.0


def test_backward(bot):
    bot.backward()
    assert bot.status == "moving_backward"
    assert bot.location[1] == -1.0


def test_stop(bot):
    bot.forward()
    bot.stop()
    assert bot.status == "stopped"


def test_turn_left(bot):
    bot.turn_left()
    assert bot.status == "turning_left"
    assert bot.location[0] == -1.0


def test_turn_right(bot):
    bot.turn_right()
    assert bot.status == "turning_right"
    assert bot.location[0] == 1.0


def test_read_sensor_keys(bot):
    data = bot.read_sensor()
    assert "state" in data


def test_read_sensor_reflects_location(bot):
    bot.forward()
    data = bot.read_sensor()
    assert data["state"] == [0.0, 1.0]


# --- Robot main.py ---

@patch("robot.main.requests.post")
def test_main_registers_on_boot(mock_post):
    mock_post.side_effect = [
        MagicMock(raise_for_status=MagicMock()),
        KeyboardInterrupt
    ]

    with pytest.raises(KeyboardInterrupt):
        from robot.main import main
        main("robot_1")

    first_call = mock_post.call_args_list[0]
    assert "register" in first_call.args[0]


@patch("robot.main.requests.post")
def test_main_exits_if_cloud_unreachable(mock_post):
    mock_post.side_effect = Exception("Connection refused")

    with pytest.raises(SystemExit) as exc:
        from robot.main import main
        main("robot_1")

    assert exc.value.code == 1
