import random
import time
import requests
import sys
from .robotMeshNode import RobotMeshNode

CLOUD_URL = "http://localhost:8000"

def main(robot_id: str):
    print(f"--- Booting Robot Edge Device: {robot_id} ---")

    # 1. Register with the Cloud Service
    try:
        res = requests.post(f"{CLOUD_URL}/robot/register?robot_id={robot_id}")
        res.raise_for_status()
        print(f"[Robot Orchestrator] Registered successfully with Cloud.")
    except Exception as e:
        print(f"[Robot Orchestrator] Fatal Error: Could not reach Cloud Service. {e}")
        sys.exit(1)

    mesh_node = None
    current_config = None

    # 2. Main Event Loop (Heartbeats)
    while True:
        try:
            res = requests.post(f"{CLOUD_URL}/robot/{robot_id}/heartbeat")
            data = res.json()

            # Check if a user has connected and triggered the mesh setup
            config = data.get("mesh_config")

            # If a mesh node exists, but its threads have shut down (self.running == False)
            if mesh_node and not mesh_node.running:
                print(f"\n[Robot Orchestrator] Mesh closed. Returning to idle heartbeat mode.")
                mesh_node = None
                current_config = None

            # If we received a config and haven't spun up our ZMQ node yet
            if config and config != current_config and mesh_node is None:
                print(f"\n[Robot Orchestrator] Received mesh configuration. Spawning P2P Node...")
                current_config = config

                mesh_node = RobotMeshNode(
                    robot_id=robot_id,
                    pub_port=config["robot_pub_port"],
                    player_port=config["player_pub_port"],
                    user_port=config["user_pub_port"],
                    session_key=config["secret_key"],
                )
                mesh_node.start()

        except Exception as e:
            print(f"[Robot Orchestrator] Heartbeat failed: {e}")

        time.sleep(1) # Wait 1 second before next heartbeat


def generate_robot_id() -> str:
    timestamp = int(time.time() * 1_000_000)  # microseconds
    suffix = random.randint(1000, 9999)
    return f"robot-{timestamp}-{suffix}"


if __name__ == "__main__":
    robot_id = generate_robot_id()
    main(robot_id)
