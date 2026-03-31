from fastapi import FastAPI
from .models import RegisterResponse, HeartbeatResponse

app = FastAPI(title="Cloud Service Orchestrator")

@app.post("/robot/register", response_model=RegisterResponse)
def register_robot(robot_id: str):
    """Called by the Robot when it boots up."""
    pass

@app.post("/robot/{robot_id}/heartbeat", response_model=HeartbeatResponse)
def robot_heartbeat(robot_id: str):
    """
    Robot pings this every second. 
    If a user has initiated a connection, we return the mesh configuration 
    so the robot can start its ZMQ pub/sub server.
    """
    pass

@app.get("/robots")
def list_robots():
    """Called by the User to see available robots."""
    pass

@app.post("/connect/{robot_id}")
def connect_user_to_robot(robot_id: str):
    """
    Called by the User. Orchestrates the creation of the P2P mesh.
    """
    pass