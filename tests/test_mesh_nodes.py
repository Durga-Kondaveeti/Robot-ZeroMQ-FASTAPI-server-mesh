# tests/test_mesh_nodes.py
import json
import queue
import pytest
from unittest.mock import MagicMock, patch
import zmq as zmq_lib


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
    node.robot_hardware = MagicMock()
    node.running = True
    node.sub_socket = MagicMock()

    def fake_recv():
        node.running = False
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


def test_robot_routes_disconnect_calls_shutdown(robot_node):
    robot_node.pub_socket = MagicMock()
    robot_node.sub_socket = MagicMock()
    robot_node.context = MagicMock()
    robot_node.robot_hardware = MagicMock()
    robot_node.shutdown = MagicMock()
    robot_node.running = True

    topic = f"robot/{robot_node.robot_id}/command".encode()
    payload = json.dumps({"command": "disconnect"}).encode()

    def fake_recv():
        robot_node.running = False
        return (topic, payload)

    robot_node.sub_socket.recv_multipart.side_effect = fake_recv
    robot_node._listen_loop()

    robot_node.shutdown.assert_called_once()


def test_robot_shutdown_closes_sockets(robot_node):
    robot_node.running = True
    robot_node.pub_socket = MagicMock()
    robot_node.sub_socket = MagicMock()
    robot_node.context = MagicMock()

    robot_node.shutdown()

    assert robot_node.running == False
    robot_node.pub_socket.close.assert_called_once()
    robot_node.sub_socket.close.assert_called_once()
    robot_node.context.term.assert_called_once()


# --- UserMeshNode ---

@pytest.fixture
def mock_callback():
    return MagicMock()


@pytest.fixture
def user_node(mock_callback):
    with patch("user.mesh_node.zmq.Context"):
        from user.userMeshNode import UserMeshNode
        node = UserMeshNode(
            robot_id="robot-1",
            user_port=5003,
            robot_port=5001,
            player_port=5002,
            on_message_received=mock_callback
        )
        yield node


def test_user_node_initial_state(user_node):
    assert user_node.robot_id == "robot-1"
    assert user_node.running == False


def test_user_node_start_sets_running(user_node):
    with patch("user.mesh_node.threading.Thread"):
        user_node.start()
    assert user_node.running == True


def test_user_node_start_spawns_two_threads(user_node):
    with patch("user.mesh_node.threading.Thread") as mock_thread:
        user_node.start()
    assert mock_thread.call_count == 2


def test_user_send_command(user_node):
    user_node.pub_socket = MagicMock()
    user_node.send_command("forward")

    expected_topic = f"robot/{user_node.robot_id}/command".encode()
    expected_payload = json.dumps({"command": "forward"}).encode()
    user_node.pub_socket.send_multipart.assert_called_once_with(
        [expected_topic, expected_payload]
    )


def test_user_listen_loop_routes_message_to_callback(user_node, mock_callback):
    user_node.running = True
    user_node.sub_socket = MagicMock()

    topic = f"robot/{user_node.robot_id}/sensor".encode()
    payload = json.dumps({"temperature": 30.0}).encode()

    def fake_recv(flags=None):
        user_node.running = False
        return (topic, payload)

    user_node.sub_socket.recv_multipart.side_effect = fake_recv
    user_node._listen_loop()

    mock_callback.assert_called()
    assert "temperature" in mock_callback.call_args[0][0]


def test_user_listen_loop_handles_zmq_again_without_crashing(user_node):
    """zmq.Again (empty pipe) should be swallowed silently."""
    user_node.running = True
    user_node.sub_socket = MagicMock()

    call_count = 0
    def fake_recv(flags=None):
        nonlocal call_count
        call_count += 1
        if call_count >= 3:
            user_node.running = False
        raise zmq_lib.Again()

    user_node.sub_socket.recv_multipart.side_effect = fake_recv
    user_node._listen_loop()  # Should not raise


def test_user_send_disconnect(user_node):
    user_node.pub_socket = MagicMock()
    user_node.sub_socket = MagicMock()
    user_node.running = True

    user_node.send_disconnect()

    assert user_node.running == False
    user_node.pub_socket.close.assert_called_once()
    user_node.sub_socket.close.assert_called_once()


# --- RobotDashboard (GUI) ---

def test_dashboard_close_connection_calls_disconnect():
    with patch("user.gui.tk.Tk.__init__", return_value=None):
        from user.gui import RobotDashboard
        dashboard = RobotDashboard.__new__(RobotDashboard)
        dashboard.mesh = MagicMock()
        dashboard.after = MagicMock()
        dashboard.log_message = MagicMock()

        dashboard.close_connection()

        dashboard.mesh.send_disconnect.assert_called_once()
        dashboard.after.assert_called_once()


def test_dashboard_queue_message_puts_to_queue():
    with patch("user.gui.tk.Tk.__init__", return_value=None):
        from user.gui import RobotDashboard
        dashboard = RobotDashboard.__new__(RobotDashboard)
        dashboard.msg_queue = queue.Queue()

        dashboard.queue_message("hello from mesh")

        assert not dashboard.msg_queue.empty()
        assert dashboard.msg_queue.get() == "hello from mesh"


def test_dashboard_check_queue_drains_messages():
    with patch("user.gui.tk.Tk.__init__", return_value=None):
        from user.gui import RobotDashboard
        dashboard = RobotDashboard.__new__(RobotDashboard)
        dashboard.msg_queue = queue.Queue()
        dashboard.log_message = MagicMock()
        dashboard.after = MagicMock()

        dashboard.msg_queue.put("msg1")
        dashboard.msg_queue.put("msg2")
        dashboard.check_queue()

        assert dashboard.log_message.call_count == 2


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