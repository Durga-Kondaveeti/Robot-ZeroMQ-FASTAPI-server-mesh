import zmq
import json
import threading
import time

class UserMeshNode:
    """
    Handles the User's role in the P2P ZeroMQ mesh.
    Binds a PUB socket for sending commands and SUB sockets for receiving data.
    """
    def __init__(self, robot_id: str, user_port: int, robot_port: int, player_port: int, on_message_received):
        self.robot_id = robot_id
        self.user_port = user_port
        self.robot_port = robot_port
        self.player_port = player_port

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

        self.on_message_received(f"[User Mesh] Dashboard online! Publishing commands on {self.user_port}")

        # Start background threads for networking
        threading.Thread(target=self._listen_loop, daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

    def _heartbeat_loop(self):
        """Sends a heartbeat to the mesh to let others know the User is active."""
        status_topic = f"robot/{self.robot_id}/status".encode('utf-8')
        while self.running:
            payload = json.dumps({"type": "heartbeat", "source": "user"}).encode('utf-8')
            self.pub_socket.send_multipart([status_topic, payload])

            # Check for mesh health: If no messages received in 5s, peer might be gone
            if time.time() - self.last_peer_activity > 5.0:
                self.on_message_received("[Warning] Mesh Timeout: No activity from Robot/Player.")

            time.sleep(2)

    def _listen_loop(self):
        """Continuously receives and prints data from the mesh."""
        while self.running:
            try:
                # flags=zmq.NOBLOCK ensures this thread doesn't hang forever when we want to close the app
                topic_bytes, msg_bytes = self.sub_socket.recv_multipart(flags=zmq.NOBLOCK)

                self.last_peer_activity = time.time()
                topic = topic_bytes.decode('utf-8')
                data = json.loads(msg_bytes.decode('utf-8'))

                # Requirement: Each entity should print all data it receives from topics it's subscribed to
                # We route this to the GUI via the callback.
                self.on_message_received(f"[Incoming Data] {topic}: {data}")

            except zmq.Again:
                # Expected exception in NOBLOCK mode when no message is currently in the pipe
                time.sleep(0.1)
            except Exception as e:
                if self.running:
                    self.on_message_received(f"[User Network Error] {e}")

    def send_disconnect(self):
        """Signals the mesh to tear down and closes local sockets."""
        self.send_command("disconnect")
        self.running = False

        # Give the disconnect message a fraction of a second to send before closing the socket
        time.sleep(0.1)
        self.pub_socket.close()
        self.sub_socket.close()

    def send_command(self, command: str):
        """Publishes a JSON command to the Robot over the mesh."""
        topic = f"robot/{self.robot_id}/command".encode('utf-8')
        payload = json.dumps({"command": command}).encode('utf-8')
        self.pub_socket.send_multipart([topic, payload])