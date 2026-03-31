# tests/test_cloud_service.py
import time
import pytest
from fastapi.testclient import TestClient
from cloud_service.main import app, registry

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_registry():
    """Wipe the in-memory registry before every test."""
    registry.clear()
    yield
    registry.clear()


# --- Registration ---

def test_register_robot():
    res = client.post("/robot/register?robot_id=robot_1")
    assert res.status_code == 200
    assert res.json() == {"robot_id": "robot_1", "message": "Registration successful"}


def test_register_robot_appears_in_registry():
    client.post("/robot/register?robot_id=robot_1")
    assert "robot_1" in registry


# --- Heartbeat ---

def test_heartbeat_unknown_robot_returns_404():
    res = client.post("/robot/ghost_robot/heartbeat")
    assert res.status_code == 404


def test_heartbeat_alive():
    client.post("/robot/register?robot_id=robot_1")
    res = client.post("/robot/robot_1/heartbeat")
    assert res.status_code == 200
    assert res.json()["status"] == "alive"


def test_heartbeat_no_mesh_config_by_default():
    client.post("/robot/register?robot_id=robot_1")
    res = client.post("/robot/robot_1/heartbeat")
    assert res.json()["mesh_config"] is None


# --- Active Robot Listing ---

def test_list_active_robots():
    client.post("/robot/register?robot_id=robot_1")
    client.post("/robot/robot_1/heartbeat")
    res = client.get("/robots")
    assert "robot_1" in res.json()["active_robots"]


def test_stale_robot_not_listed():
    client.post("/robot/register?robot_id=robot_1")
    # Backdate the heartbeat so it looks stale
    registry["robot_1"].last_heartbeat = time.time() - 10
    res = client.get("/robots")
    assert "robot_1" not in res.json()["active_robots"]