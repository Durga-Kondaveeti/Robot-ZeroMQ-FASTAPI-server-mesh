from pydantic import BaseModel
from typing import Optional

# Response Models
class MeshConfig(BaseModel):
    robot_pub_port: int
    player_pub_port: int
    user_pub_port: int
    secret_key: str

class RegisterResponse(BaseModel):
    robot_id: str
    message: str

class HeartbeatResponse(BaseModel):
    status: str
    mesh_config: Optional[MeshConfig] = None

