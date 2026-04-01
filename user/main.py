import os
import requests
from .mesh_node import UserMeshNode

CLOUD_URL = "http://localhost:8000"


def clear_terminal():
    os.system('clear' if os.name != 'nt' else 'cls')


def get_robot_selection():
    while True:
        clear_terminal()
        print("--- User Control Dashboard ---")
        try:
            response = requests.get(f"{CLOUD_URL}/robots")
            robots = response.json().get("active_robots", [])

            if not robots:
                print("No active robots found. Ensure the Robot script is running.")
            else:
                print("Available Robots:")
                for idx, r_id in enumerate(robots):
                    print(f"{idx + 1}. {r_id}")

            print("\n[R] Reload List | [Q] Quit")
            choice = input("\nSelect a robot or action: ").strip().upper()

            if choice == 'R':
                continue
            if choice == 'Q':
                return None

            if choice.isdigit() and 1 <= int(choice) <= len(robots):
                return robots[int(choice) - 1]

        except Exception as e:
            print(f"Error fetching robots: {e}")
            input("Press any key to retry...")

def main():
    print("--- User Control Dashboard ---")

    # 1. Fetch available robots from the Cloud Service
    target_robot = get_robot_selection()
    # User selected Quit
    if target_robot == None:
        return

    # 2. Request connection to form the P2P mesh
    print(f"Connecting to {target_robot}...")
    try:
        res = requests.post(f"{CLOUD_URL}/connect/{target_robot}")
        res.raise_for_status()
        config = res.json()["mesh_config"]
    except Exception as e:
        print(f"Failed to establish mesh connection: {e}")
        return

    # 3. Start the ZMQ Mesh Node
    mesh = UserMeshNode(
        robot_id=target_robot,
        user_port=config["user_pub_port"],
        robot_port=config["robot_pub_port"],
        player_port=config["player_pub_port"]
    )
    mesh.start()

    # 4. Interactive Command Loop
    print("\n--- Mesh Established ---")
    print("Commands: forward, stop, left, right, exit")

    while True:
        cmd = input("Command: ").strip().lower()
        if cmd == 'exit':
            mesh.send_disconnect()
            print("Shutting down user...")
            break
        elif cmd in ['forward', 'stop', 'left', 'right']:
            mesh.send_command(cmd)
        else:
            print("Unknown command. Try: forward, stop, left, right, or exit.")

if __name__ == "__main__":
    main()