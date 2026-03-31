from pydantic import BaseModel
from typing import Optional

# Response Models
class RegisterResponse(BaseModel):
    robot_id: str
    message: str

class HeartbeatResponse(BaseModel):
    status: str
    mesh_config: Optional[dict] = None