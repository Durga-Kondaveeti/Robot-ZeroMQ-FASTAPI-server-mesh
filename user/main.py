import requests
from .mesh_node import UserMeshNode

CLOUD_URL = "http://localhost:8000"

def main():
    print("--- User Control Dashboard ---")
    
    # 1. Fetch available robots from the Cloud Service
    try:
        response = requests.get(f"{CLOUD_URL}/robots")
        robots = response.json().get("active_robots", [])
        
        if not robots:
            print("No active robots found. Ensure the Robot script is running.")
            return

        print("Available Robots:")
        for idx, r_id in enumerate(robots):
            print(f"{idx + 1}. {r_id}")
            
        choice = int(input("Select a robot number to connect: ")) - 1
        target_robot = robots[choice]
        
    except Exception as e:
        print(f"Error fetching robots: {e}")
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
            print("Shutting down...")
            break
        elif cmd in ['forward', 'stop', 'left', 'right']:
            mesh.send_command(cmd)
        else:
            print("Unknown command. Try: forward, stop, left, right, or exit.")

if __name__ == "__main__":
    main()