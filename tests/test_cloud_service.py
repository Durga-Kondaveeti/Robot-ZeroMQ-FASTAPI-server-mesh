# tests/test_cloud_service.py
import time
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from cloud_service.main import app, registry

ROBOT_PORT = 5555
USER_PORT = 6666
client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_registry():
    """Wipe the in-memory registry before every test."""
    registry.clear()
    yield
    registry.clear()


# --- Registration ---

def test_register_robot():
    res = client.post("/robot/register?robot_id=robot_1", json={"robot_port": ROBOT_PORT})
    assert res.status_code == 200
    assert res.json() == {"robot_id": "robot_1", "message": "Registration successful"}


def test_register_robot_appears_in_registry():
    client.post("/robot/register?robot_id=robot_1", json={"robot_port": ROBOT_PORT})
    assert "robot_1" in registry


def test_register_duplicate_active_robot_returns_409():
    client.post("/robot/register?robot_id=robot_1", json={"robot_port": ROBOT_PORT})
    client.post("/robot/robot_1/heartbeat")  # make it active
    res = client.post("/robot/register?robot_id=robot_1", json={"robot_port": ROBOT_PORT})
    assert res.status_code == 409


def test_register_stale_robot_allows_reregistration():
    client.post("/robot/register?robot_id=robot_1", json={"robot_port": ROBOT_PORT})
    registry["robot_1"].last_heartbeat = time.time() - 10  # backdate to stale
    res = client.post("/robot/register?robot_id=robot_1", json={"robot_port": ROBOT_PORT})
    assert res.status_code == 200


# --- Heartbeat ---

def test_heartbeat_unknown_robot_returns_404():
    res = client.post("/robot/ghost_robot/heartbeat")
    assert res.status_code == 404


def test_heartbeat_alive():
    client.post("/robot/register?robot_id=robot_1", json={"robot_port": ROBOT_PORT})
    res = client.post("/robot/robot_1/heartbeat")
    assert res.status_code == 200
    assert res.json()["status"] == "alive"


def test_heartbeat_no_mesh_config_by_default():
    client.post("/robot/register?robot_id=robot_1", json={"robot_port": ROBOT_PORT})
    res = client.post("/robot/robot_1/heartbeat")
    assert res.json()["mesh_config"] is None


def test_heartbeat_returns_mesh_config_after_connect():
    client.post("/robot/register?robot_id=robot_1", json={"robot_port": ROBOT_PORT})
    with patch("cloud_service.main.multiprocessing.Process") as mock_process:
        mock_process.return_value.is_alive.return_value = False
        client.post("/connect/robot_1", json={"user_pub_port": USER_PORT})

    res = client.post("/robot/robot_1/heartbeat")
    assert res.json()["mesh_config"] is not None


# --- Active Robot Listing ---

def test_list_active_robots():
    client.post("/robot/register?robot_id=robot_1", json={"robot_port": ROBOT_PORT})
    client.post("/robot/robot_1/heartbeat")
    res = client.get("/robots")
    assert "robot_1" in res.json()["active_robots"]


def test_stale_robot_not_listed():
    client.post("/robot/register?robot_id=robot_1", json={"robot_port": ROBOT_PORT})
    # Backdate the heartbeat so it looks stale
    registry["robot_1"].last_heartbeat = time.time() - 10
    res = client.get("/robots")
    assert "robot_1" not in res.json()["active_robots"]


# --- Connect ---

def test_connect_unknown_robot_returns_404():
    res = client.post("/connect/ghost_robot", json={"user_pub_port": USER_PORT})
    assert res.status_code == 404


def test_connect_provisions_mesh():
    client.post("/robot/register?robot_id=robot_1", json={"robot_port": ROBOT_PORT})
    with patch("cloud_service.main.multiprocessing.Process") as mock_process:
        mock_process.return_value.is_alive.return_value = False
        res = client.post("/connect/robot_1", json={"user_pub_port": USER_PORT})

    assert res.status_code == 200
    body = res.json()
    assert body["message"] == "Mesh provisioned successfully"
    config = body["mesh_config"]
    assert "robot_pub_port" in config
    assert "player_pub_port" in config
    assert "user_pub_port" in config
    # All three ports should be different
    ports = [config["robot_pub_port"], config["player_pub_port"], config["user_pub_port"]]
    assert len(set(ports)) == 3


def test_connect_provisions_mesh_and_spawns_terminal():
    client.post("/robot/register?robot_id=robot_1", json={"robot_port": ROBOT_PORT})
    with patch("cloud_service.main.launch_player_terminal") as mock_terminal:
        res = client.post("/connect/robot_1", json={"user_pub_port": USER_PORT})

    assert res.status_code == 200
    assert res.json()["message"] == "Mesh provisioned successfully"
    mock_terminal.assert_called_once()
    call_args = mock_terminal.call_args[0]
    assert call_args[0] == "robot_1"  # correct robot_id passed


def test_connect_already_connected():
    client.post("/robot/register?robot_id=robot_1", json={"robot_port": ROBOT_PORT})
    with patch("cloud_service.main.multiprocessing.Process") as mock_process:
        mock_process.return_value.is_alive.return_value = False
        client.post("/connect/robot_1", json={"user_pub_port": USER_PORT})
        # Simulate the player process still running
        registry["robot_1"].player_process = MagicMock()
        registry["robot_1"].player_process.is_alive.return_value = True
        res = client.post("/connect/robot_1", json={"user_pub_port": USER_PORT})

    assert res.json()["message"] == "Already connected"
