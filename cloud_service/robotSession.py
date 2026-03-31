import time

class RobotSession:
    def __init__(self):
        self.last_heartbeat = time.time()
        self.mesh_config =  None