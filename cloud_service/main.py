import time
from fastapi import FastAPI, HTTPException
from typing import Dict

from .models import RegisterResponse, HeartbeatResponse
from .robotSession import RobotSession

app = FastAPI(title="Cloud Service Orchestrator")

# In-memory storage for the simulation
registry: Dict[str, RobotSession] = {}

@app.post("/robot/register", response_model=RegisterResponse)
def register_robot(robot_id: str):
    """Called by the Robot when it boots up."""
    registry[robot_id] = RobotSession()
    print(f"[Cloud] Robot '{robot_id}' registered.")
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

@app.post("/connect/{robot_id}")
def connect_user_to_robot(robot_id: str):
    """
    Called by the User. Orchestrates the creation of the P2P mesh.
    """
    pass