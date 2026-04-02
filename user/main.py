import os
import requests
from .gui import RobotDashboard

from common.config import CLOUD_URL


def clear_terminal():
    os.system('clear' if os.name != 'nt' else 'cls')


def get_robot_selection():
    """Handles the terminal UI for browsing and selecting active robots."""
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
            input("Press Enter to retry...")


def main():
    # 1. Fetch available robots from the Cloud Service
    target_robot = get_robot_selection()

    # Exit cleanly if the user selected Quit
    if target_robot is None:
        print("Exiting User Dashboard.")
        return

    # 2. Request connection to form the P2P mesh
    print(f"\nConnecting to {target_robot}...")
    try:
        res = requests.post(f"{CLOUD_URL}/connect/{target_robot}")
        res.raise_for_status()
        config = res.json()["mesh_config"]
    except Exception as e:
        print(f"Failed to establish mesh connection: {e}")
        return

    # 3. Hand off the config to the Graphical Dashboard
    # The RobotDashboard class will initialize the UserMeshNode and manage the ZMQ threads
    print("Mesh provisioned. Launching Graphical Dashboard...")
    app = RobotDashboard(target_robot, config)
    app.mainloop()

if __name__ == "__main__":
    main()
