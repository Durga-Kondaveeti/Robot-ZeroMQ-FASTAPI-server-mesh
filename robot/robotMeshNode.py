import zmq
import json
import threading
import time
from .jetbot import FakeJetbot

class RobotMeshNode:
    """
    Handles the P2P ZeroMQ network layer for the robot.
    Binds a PUB socket to broadcast data and connects a SUB socket to listen for commands.
    """
    def __init__(self, robot_id: str, pub_port: int, player_port: int, user_port: int):
        self.robot_id = robot_id
        self.pub_port = pub_port
        self.player_port = player_port
        self.user_port = user_port
        
        self.robot_hardware = FakeJetbot()
        self.context = zmq.Context()
        self.running = False

    def start(self):
        """Spins up the ZMQ sockets and background threads."""
        self.running = True
        
        # Bind PUB socket (Robot's server)
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind(f"tcp://*:{self.pub_port}")
        
        # Connect SUB socket (Listening to Cloud Player & User)
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(f"tcp://localhost:{self.player_port}")
        self.sub_socket.connect(f"tcp://localhost:{self.user_port}")
        
        # Subscribe to the topics
        command_topic = f"robot/{self.robot_id}/command"
        status_topic = f"robot/{self.robot_id}/status"
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, command_topic)
        self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, status_topic)
        
        print(f"[Robot Mesh] Node online! Publishing on {self.pub_port}")
        
        # Start networking threads
        threading.Thread(target=self._listen_loop, daemon=True).start()
        threading.Thread(target=self._publish_loop, daemon=True).start()

    def _listen_loop(self):
        """Listens for incoming commands and status updates."""
        while self.running:
            try:
                topic_bytes, msg_bytes = self.sub_socket.recv_multipart()
                topic = topic_bytes.decode('utf-8')
                data = json.loads(msg_bytes.decode('utf-8'))
                
                print(f"[Robot Network] Received on {topic}: {data}")
                
                # Command routing logic
                if topic.endswith("/command"):
                    cmd = data.get("command")
                    if cmd == "forward":
                        self.robot_hardware.forward()
                    elif cmd == "stop":
                        self.robot_hardware.stop()
                    elif cmd == "left":
                        self.robot_hardware.turn_left()
                    elif cmd == "right":
                        self.robot_hardware.turn_right()
                        
            except Exception as e:
                print(f"[Robot Network Error] Listen loop failed: {e}")

    def _publish_loop(self):
        """Publishes raw sensor data every second."""
        sensor_topic = f"robot/{self.robot_id}/sensor".encode('utf-8')
        
        while self.running:
            try:
                # Get fresh data from the mocked hardware SDK
                sensor_data = self.robot_hardware.read_sensor()
                
                # Publish to the mesh
                self.pub_socket.send_multipart([
                    sensor_topic,
                    json.dumps(sensor_data).encode('utf-8')
                ])
                time.sleep(1) # Publish once per second
            except Exception as e:
                print(f"[Robot Network Error] Publish loop failed: {e}")