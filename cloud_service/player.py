import csv
import os

import zmq
import json
import time

from common.security import MeshCipher


def run_player(robot_id: str, player_port: int, robot_port: int, user_port: int, session_key: str):
    """
    The background process spawned for each connected robot.
    It forms one corner of the Pub/Sub triangle mesh.
    """
    context = zmq.Context()

    # Initialize the cipher suite
    cipher = MeshCipher(session_key)

    # 1. Bind the Player's PUB socket (This is the cloud pub/sub server)
    pub_socket = context.socket(zmq.PUB)
    pub_socket.bind(f"tcp://*:{player_port}")

    # 2. Connect the Player's SUB socket to the Robot and User
    sub_socket = context.socket(zmq.SUB)

    # We use localhost here since we are simulating on a single machine.
    # In a real distributed system, these would be the public IPs of the edge and client.
    sub_socket.connect(f"tcp://localhost:{robot_port}")
    sub_socket.connect(f"tcp://localhost:{user_port}")

    # Subscribe to the required topics
    sensor_topic = f"robot/{robot_id}/sensor"
    status_topic = f"robot/{robot_id}/status"

    sub_socket.setsockopt_string(zmq.SUBSCRIBE, sensor_topic)
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, status_topic)

    print(f"\n[Cloud Player {robot_id}] Spun up successfully!")
    print(f"[Cloud Player {robot_id}] Publishing on port {player_port}")
    print(f"[Cloud Player {robot_id}] Subscribed to ports {robot_port} (Robot) and {user_port} (User)\n")

    log_dir = os.path.join("logs", "player_logs", f"{robot_id}-player-1")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "robot_input.csv")

    # Write CSV header if file is new
    if not os.path.isfile(log_file):
        with open(log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["time", "log"])

    while True:
        try:
            topic_bytes, message_bytes = sub_socket.recv_multipart()
            topic = topic_bytes.decode('utf-8')

            data = cipher.decrypt(message_bytes)

            # --- RESOURCE MANAGEMENT TEARDOWN ---
            if topic == status_topic:
                if data.get('command') == "disconnect":
                    print(f"[Cloud Player {robot_id}] Disconnect signal received. Tearing down...")
                    break

            # If we receive raw sensor data, process it and republish
            elif topic == sensor_topic:
                # --- Save logs to disk ---
                with open(log_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([time.time(), json.dumps(data)])

                processed_data = data.copy()
                processed_data["status"] = "normal"

                pub_topic = f"robot/{robot_id}/processed"

                encrypted_payload = cipher.encrypt(processed_data)

                pub_socket.send_multipart([
                    pub_topic.encode('utf-8'),
                    encrypted_payload
                ])
        except Exception as e:
            print(f"[Cloud Player Error] {e}")
            time.sleep(1)

    # Clean up sockets when the loop breaks
    pub_socket.close()
    sub_socket.close()
    context.term()
    print(f"[Cloud Player {robot_id}] Teardown complete. Process exiting.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 6:
        r_id = sys.argv[1]
        p_port = int(sys.argv[2])
        r_port = int(sys.argv[3])
        u_port = int(sys.argv[4])
        s_key = sys.argv[5]
        run_player(r_id, p_port, r_port, u_port, s_key)
    else:
        print("[INVALID DATA]: Unable to start player")
