import time

from .models import MeshConfig

class RobotSession:
    def __init__(self):
        self.last_heartbeat = time.time()
        self.mesh_config: MeshConfig  =  None
        self.player_process = None