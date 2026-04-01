# tests/test_mesh_nodes.py
import json
import pytest
from unittest.mock import MagicMock, patch


# --- RobotMeshNode ---

@pytest.fixture
def robot_node():
    with patch("robot.robotMeshNode.zmq.Context"):
        from robot.robotMeshNode import RobotMeshNode
        node = RobotMeshNode(
            robot_id="robot-1",
            pub_port=5001,
            player_port=5002,
            user_port=5003
        )
        yield node


def _run_listen_once(node, topic_bytes, payload_bytes):
    """Runs the robot listen loop for exactly one message then stops cleanly."""
    node.robot_hardware = MagicMock()
    node.running = True
    node.sub_socket = MagicMock()

    def fake_recv():
        node.running = False  # stop the while loop after this message
        return (topic_bytes, payload_bytes)

    node.sub_socket.recv_multipart.side_effect = fake_recv
    node._listen_loop()


def test_robot_node_initial_state(robot_node):
    assert robot_node.robot_id == "robot-1"
    assert robot_node.running == False


def test_robot_node_start_sets_running(robot_node):
    with patch("robot.robotMeshNode.threading.Thread"):
        robot_node.start()
    assert robot_node.running == True


def test_robot_node_start_spawns_two_threads(robot_node):
    with patch("robot.robotMeshNode.threading.Thread") as mock_thread:
        robot_node.start()
    assert mock_thread.call_count == 2


def test_robot_routes_forward_command(robot_node):
    topic = f"robot/{robot_node.robot_id}/command".encode()
    payload = json.dumps({"command": "forward"}).encode()
    _run_listen_once(robot_node, topic, payload)
    robot_node.robot_hardware.forward.assert_called_once()


def test_robot_routes_stop_command(robot_node):
    topic = f"robot/{robot_node.robot_id}/command".encode()
    payload = json.dumps({"command": "stop"}).encode()
    _run_listen_once(robot_node, topic, payload)
    robot_node.robot_hardware.stop.assert_called_once()


def test_robot_routes_left_command(robot_node):
    topic = f"robot/{robot_node.robot_id}/command".encode()
    payload = json.dumps({"command": "left"}).encode()
    _run_listen_once(robot_node, topic, payload)
    robot_node.robot_hardware.turn_left.assert_called_once()


def test_robot_routes_right_command(robot_node):
    topic = f"robot/{robot_node.robot_id}/command".encode()
    payload = json.dumps({"command": "right"}).encode()
    _run_listen_once(robot_node, topic, payload)
    robot_node.robot_hardware.turn_right.assert_called_once()


# --- UserMeshNode ---

@pytest.fixture
def user_node():
    with patch("user.mesh_node.zmq.Context"):
        from user.mesh_node import UserMeshNode
        node = UserMeshNode(
            robot_id="robot-1",
            user_port=5003,
            robot_port=5001,
            player_port=5002
        )
        yield node


def test_user_node_initial_state(user_node):
    assert user_node.robot_id == "robot-1"
    assert user_node.running == False


def test_user_node_start_sets_running(user_node):
    with patch("user.mesh_node.threading.Thread"):
        user_node.start()
    assert user_node.running == True


def test_user_node_start_spawns_one_thread(user_node):
    with patch("user.mesh_node.threading.Thread") as mock_thread:
        user_node.start()
    assert mock_thread.call_count == 1


def test_user_send_command(user_node):
    user_node.pub_socket = MagicMock()
    user_node.send_command("forward")

    expected_topic = f"robot/{user_node.robot_id}/command".encode()
    expected_payload = json.dumps({"command": "forward"}).encode()
    user_node.pub_socket.send_multipart.assert_called_once_with(
        [expected_topic, expected_payload]
    )


# --- robot/main.py mesh integration ---

@patch("robot.main.requests.post")
def test_robot_main_spawns_mesh_node_when_config_received(mock_post):
    no_config = MagicMock()
    no_config.json.return_value = {"mesh_config": None}

    config_response = MagicMock()
    config_response.json.return_value = {
        "mesh_config": {
            "robot_pub_port": 5001,
            "player_pub_port": 5002,
            "user_pub_port": 5003
        }
    }

    mock_post.side_effect = [
        MagicMock(raise_for_status=MagicMock()),
        no_config,
        config_response,
        KeyboardInterrupt
    ]

    with patch("robot.main.RobotMeshNode") as mock_node:
        mock_node.return_value.start = MagicMock()
        with pytest.raises(KeyboardInterrupt):
            from robot.main import main
            main("robot-1")

        mock_node.return_value.start.assert_called_once()


@patch("robot.main.requests.post")
def test_robot_main_does_not_spawn_mesh_twice(mock_post):
    config_response = MagicMock()
    config_response.json.return_value = {
        "mesh_config": {
            "robot_pub_port": 5001,
            "player_pub_port": 5002,
            "user_pub_port": 5003
        }
    }

    mock_post.side_effect = [
        MagicMock(raise_for_status=MagicMock()),
        config_response,
        config_response,
        KeyboardInterrupt
    ]

    with patch("robot.main.RobotMeshNode") as mock_node:
        mock_node.return_value.start = MagicMock()
        with pytest.raises(KeyboardInterrupt):
            from robot.main import main
            main("robot-1")

        assert mock_node.call_count == 1
