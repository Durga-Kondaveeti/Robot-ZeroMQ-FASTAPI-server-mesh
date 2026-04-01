# tests/test_robot.py
import sys
import pytest
from unittest.mock import patch, MagicMock
from robot.jetbot import FakeJetbot


# --- FakeJetbot ---

@pytest.fixture
def bot():
    return FakeJetbot()


def test_initial_state(bot):
    assert bot.status == "idle"
    assert bot.speed == 0.0


def test_forward(bot):
    bot.forward(0.5)
    assert bot.status == "moving_forward"
    assert bot.speed == 0.5


def test_stop(bot):
    bot.forward(1.0)
    bot.stop()
    assert bot.status == "stopped"
    assert bot.speed == 0.0


def test_turn_left(bot):
    bot.turn_left()
    assert bot.status == "turning_left"


def test_turn_right(bot):
    bot.turn_right()
    assert bot.status == "turning_right"


def test_read_sensor_keys(bot):
    data = bot.read_sensor()
    assert "temperature" in data
    assert "battery_level" in data
    assert "hardware_state" in data


def test_read_sensor_temperature_range(bot):
    for _ in range(20):
        data = bot.read_sensor()
        assert 25.0 <= data["temperature"] <= 35.0


def test_read_sensor_reflects_hardware_state(bot):
    bot.forward(1.0)
    data = bot.read_sensor()
    assert data["hardware_state"] == "moving_forward"


# --- Robot main.py ---

@patch("robot.main.requests.post")
def test_main_registers_on_boot(mock_post):
    mock_post.return_value.raise_for_status = MagicMock()
    # Break out of the infinite heartbeat loop after one iteration
    mock_post.side_effect = [MagicMock(raise_for_status=MagicMock()), KeyboardInterrupt]

    with pytest.raises(KeyboardInterrupt):
        from robot.main import main
        main("robot_1")

    first_call = mock_post.call_args_list[0]
    assert "register" in first_call.args[0]
    assert "robot_1" in first_call.args[0]


@patch("robot.main.requests.post")
def test_main_exits_if_cloud_unreachable(mock_post):
    mock_post.side_effect = Exception("Connection refused")

    with pytest.raises(SystemExit) as exc:
        from robot.main import main
        main("robot_1")

    assert exc.value.code == 1