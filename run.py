import subprocess
import time
import sys
import os

def run_in_new_terminal(command, title):
    """
    Opens a new terminal window and executes a command.
    Adjusted for macOS (Terminal.app) or Linux (gnome-terminal).
    """
    if sys.platform == "darwin":  # macOS
        # Uses AppleScript to open a new window, activate the venv, and run the script
        script = f'tell application "Terminal" to do script "cd {os.getcwd()} && source .venv/bin/activate && {command}"'
        subprocess.run(["osascript", "-e", script])
    elif sys.platform.startswith("linux"):  # Linux
        # Opens gnome-terminal with the command
        subprocess.Popen(["gnome-terminal", "--", "bash", "-c", f"source .venv/bin/activate && {command}; exec bash"])
    else:
        print(f"Unsupported OS for automatic terminal spawning. Please run manually: {command}")

def main():
    print("--- Launching Each simulation session in a separate terminals ---")
    number_of_robots_to_launch = 2
    if len(sys.argv) > 1:
        try:
            number_of_robots_to_launch = int(sys.argv[1])
        except:
            number_of_robots_to_launch = 2
    
    # 1. Start the Cloud Service (FastAPI + Uvicorn)
    print("[1/3] Launching Cloud Service...")
    run_in_new_terminal("uvicorn cloud_service.main:app --host 0.0.0.0 --port 8000", "Cloud Service")
    print("Cloud server started\n")

    # Give the server a moment to boot
    time.sleep(2)

    # 2. Start the Robot
    # Since your robot now generates its own ID, it will register itself automatically 
    print("[2/3] Launching Robot Edge Devices...")
    print(f"Launch {number_of_robots_to_launch} robot instances")
    for robot in range(number_of_robots_to_launch):
        run_in_new_terminal("python3 -m robot.main", "Robot Simulator")
        print(f"{robot + 1} Robot started\n")
    print("All robot devices started\n")

    # Give the robot a moment to register and start heartbeats
    time.sleep(2)

    # 3. Start the User CLI
    # The User will query the Cloud to find the auto-generated Robot ID
    print("[3/3] Launching User Controls...")
    run_in_new_terminal("python3 -m user.main", "User Controls")
    print("Launching Robot started\n")

    print("\nAll services are launching in separate windows.")
    print("Check the 'User Dashboard' terminal to begin the simulation.")

if __name__ == "__main__":
    main()