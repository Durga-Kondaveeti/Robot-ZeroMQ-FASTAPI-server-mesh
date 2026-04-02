import multiprocessing
import os
import socket
import subprocess
import sys
import time
from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException
from typing import Dict

from cloud_service.player import run_player

from .models import MeshConfig, RegisterResponse, HeartbeatResponse
from .robotSession import RobotSession

app = FastAPI(title="Cloud Service Orchestrator")

# In-memory storage for the simulation
registry: Dict[str, RobotSession] = {}

@app.post("/robot/register", response_model=RegisterResponse)
def register_robot(robot_id: str):
    """Called by the Robot when it boots up."""
    # Check if the robot is already registered and active
    if robot_id in registry:
        current_time = time.time()
        # If we received a heartbeat recently, reject the new registration
        if current_time - registry[robot_id].last_heartbeat < 5.0:
            print(f"[Cloud Warning] Duplicate registration attempt for active robot '{robot_id}'.")
            raise HTTPException(status_code=409, detail="Robot ID already registered and active")
        else:
            print(f"[Cloud] Re-registering stale robot '{robot_id}'.")
    registry[robot_id] = RobotSession()
    print(f"[Cloud] Robot '{robot_id}' registered successfully.")
    return RegisterResponse(robot_id=robot_id, message="Registration successful")


@app.post("/robot/{robot_id}/heartbeat", response_model=HeartbeatResponse)
def robot_heartbeat(robot_id: str):
    """
    Robot pings this every second.
    If a user has initiated a connection, we return the mesh configuration
    so the robot can start its ZMQ pub/sub server.
    """
    if robot_id not in registry:
        raise HTTPException(status_code=404, detail="Robot not registered")

    registry[robot_id].last_heartbeat = time.time()

    # Return the config if a user has requested a connection
    config = registry[robot_id].mesh_config
    print("LOG CHCEK", robot_id, registry[robot_id].mesh_config)
    return HeartbeatResponse(status="alive", mesh_config=config)


@app.get("/robots")
def list_robots():
    """Called by the User to see available robots."""
    current_time = time.time()
    # Filter out robots that haven't sent a heartbeat in the last 5 seconds
    active_robots = [
        r_id for r_id, session in registry.items()
        if current_time - session.last_heartbeat < 5.0
    ]
    return {"active_robots": active_robots}


def get_free_port() -> int:
    """Helper method to dynamically find an available port"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def launch_player_terminal(robot_id: str, player_port: int, robot_port: int, user_port: int, session_key: str):
    """Spawns the Cloud Player in a brand new, visible terminal window."""
    command = f"python3 -m cloud_service.player {robot_id} {player_port} {robot_port} {user_port} {session_key}"

    if sys.platform == "darwin":
        script = f'tell application "Terminal" to do script "cd {os.getcwd()} && source .venv/bin/activate && {command}"'
        subprocess.run(["osascript", "-e", script])
    elif sys.platform.startswith("linux"):
        subprocess.Popen(["gnome-terminal", "--title", f"Cloud Player - {robot_id}", "--", "bash", "-c", f"source .venv/bin/activate && {command}; exec bash"])
    else:
        # Fallback if OS isn't caught
        subprocess.Popen(command.split())


@app.post("/connect/{robot_id}")
def connect_user_to_robot(robot_id: str):
    """Called by the User. Orchestrates the creation of the P2P mesh."""
    if robot_id not in registry:
        raise HTTPException(status_code=404, detail="Robot not found or offline")

    session = registry[robot_id]

    if session.player_process and session.player_process.is_alive():
        return {"message": "Already connected", "mesh_config": session.mesh_config}

    session_key = Fernet.generate_key().decode('utf-8')

    # 1. Allocate ports
    config = MeshConfig(
        robot_pub_port=get_free_port(),
        player_pub_port=get_free_port(),
        user_pub_port=get_free_port(),
        secret_key=session_key
    )
    session.mesh_config = config

    # 2. Spawn the Cloud Player in a visible terminal window
    launch_player_terminal(
        robot_id,
        config.player_pub_port,
        config.robot_pub_port,
        config.user_pub_port,
        session_key
    )

    print(f"[Cloud] Orchestrated mesh for '{robot_id}'. Terminal spawned.")

    return {"message": "Mesh provisioned successfully", "mesh_config": config}


@app.post("/disconnect/{robot_id}")
def disconnect_user(robot_id: str):
    """Called by the User to clear the mesh configuration."""
    if robot_id in registry:
        registry[robot_id].mesh_config = None
    return {"message": "Mesh configuration cleared"}
