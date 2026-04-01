import random
import time
import requests
import sys

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

    # 2. Main Event Loop (Heartbeats)
    while True:
        try:
            requests.post(f"{CLOUD_URL}/robot/{robot_id}/heartbeat")    
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
