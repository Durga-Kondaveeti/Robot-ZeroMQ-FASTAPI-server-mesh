from cryptography.fernet import Fernet
import requests
import zmq
import json
import threading
import time

CLOUD_URL = "http://localhost:8000"

class UserMeshNode:
    """
    Handles the User's role in the P2P ZeroMQ mesh.
    Binds a PUB socket for sending commands and SUB sockets for receiving data.
    """
    def __init__(self, robot_id: str, user_port: int, robot_port: int, player_port: int, session_key: str, on_message_received):
        self.robot_id = robot_id
        self.user_port = user_port
        self.robot_port = robot_port
        self.player_port = player_port
        # Initialize the cipher suite
        self.fernet = Fernet(session_key.encode('utf-8'))

        # Callback function to route incoming data to the GUI instead of the terminal
        self.on_message_received = on_message_received

        self.context = zmq.Context()
        self.running = False
        self.last_peer_activity = time.time()

    def start(self):
        self.running = True

        # 1. Bind PUB socket (User's local server in the mesh)
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind(f"tcp://*:{self.user_port}")

        # 2. Connect SUB socket to both Robot and Player ports
        self.sub_socket = self.context.socket(zmq.SUB)
        self.sub_socket.connect(f"tcp://localhost:{self.robot_port}")
        self.sub_socket.connect(f"tcp://localhost:{self.player_port}")

        # 3. Subscribe to all relevant data streams
        topics = [
            f"robot/{self.robot_id}/sensor",    # Raw data from Robot
            f"robot/{self.robot_id}/processed", # Analyzed data from Player
            f"robot/{self.robot_id}/status"     # General status updates
        ]
        for topic in topics:
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, topic)

        self.on_message_received((f"[User Mesh] Dashboard online! Publishing commands on {self.user_port}", "system_alert"))

        # Start background threads for networking
        threading.Thread(target=self._listen_loop, daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()


    # ASSUMPTION: ZMQ PUB/SUB sockets do not naturally drop or timeout when a peer
    # disconnects. I assumed an application-layer heartbeat was necessary to detect
    # if the Robot or Player unexpectedly drops from the mesh.
    def _heartbeat_loop(self):
        """Sends a heartbeat to the mesh to let others know the User is active."""
        status_topic = f"robot/{self.robot_id}/status".encode('utf-8')
        while self.running:
            payload = self.fernet.encrypt(json.dumps({"type": "heartbeat", "source": "user"}).encode('utf-8'))
            self.pub_socket.send_multipart([status_topic, payload])

            # Check for mesh health: If no messages received in 5s, peer might be gone
            if time.time() - self.last_peer_activity > 5.0:
                self.on_message_received(("[Warning] Mesh Timeout: No activity from Robot/Player.", "system_alert"))

            time.sleep(2)

    def _listen_loop(self):
        while self.running:
            try:
                topic_bytes, msg_bytes = self.sub_socket.recv_multipart(flags=zmq.NOBLOCK)

                self.last_peer_activity = time.time()
                topic = topic_bytes.decode('utf-8')

                # --- DECRYPT INCOMING PAYLOAD ---
                decrypted_bytes = self.fernet.decrypt(msg_bytes)
                data = json.loads(decrypted_bytes.decode('utf-8'))

                # Calculate Simple Latency if the payload has a timestamp
                latency_str = ""
                if "timestamp" in data:
                    latency_ms = (time.time() - data["timestamp"]) * 1000
                    latency_str = f" [Latency: {latency_ms:.1f} ms]"

                # Route to GUI with appropriate color tags
                if topic.endswith("/sensor"):
                    self.on_message_received((f"[Robot Raw] {data}{latency_str}", "robot_raw"))
                elif topic.endswith("/processed"):
                    self.on_message_received((f"[Cloud Processed] {data}{latency_str}", "player_processed"))
                else:
                    self.on_message_received((f"[Status] {topic}: {data}", "system_alert"))

            except zmq.Again:
                time.sleep(0.05)
            except Exception as e:
                if self.running:
                    self.on_message_received((f"[Error] {e}", "system_alert"))

    def send_disconnect(self):
        """Signals the mesh to tear down and closes local sockets."""
        # 1. Send to the Command topic (so the Robot shuts down)
        self.send_command("disconnect")

        # 2. Send to the Status topic (so the Cloud Player shuts down)
        status_topic = f"robot/{self.robot_id}/status".encode('utf-8')
        status_payload = self.fernet.encrypt(json.dumps({"command": "disconnect"}).encode('utf-8'))
        self.pub_socket.send_multipart([status_topic, status_payload])

        self.running = False

        # 3. Notify the Control Plane to clear the config (FIXED: self.robot_id)
        try:
            requests.post(f"{CLOUD_URL}/disconnect/{self.robot_id}")
        except Exception as e:
            print(f"Error disconnecting from cloud: {e}")

        # Give the disconnect messages a fraction of a second to send before closing the socket
        time.sleep(0.2)
        self.pub_socket.close()
        self.sub_socket.close()


    def send_command(self, command: str):
        """Publishes a JSON command to the Robot over the mesh."""
        topic = f"robot/{self.robot_id}/command".encode('utf-8')
        # --- ENCRYPT OUTGOING PAYLOAD ---
        json_string = json.dumps({"command": command})
        encrypted_payload = self.fernet.encrypt(json_string.encode('utf-8'))
        self.pub_socket.send_multipart([topic, encrypted_payload])
