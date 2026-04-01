import requests

CLOUD_URL = "http://localhost:8000"

def main():
    try:
        response = requests.get(f"{CLOUD_URL}/robots")
        robots = response.json().get("active_robots", [])
        
        if not robots:
            print("No active robots found. Ensure the Robot script is running.")
            return

        print("Available Robots:")
        for idx, r_id in enumerate(robots):
            print(f"{idx + 1}. {r_id}")
        
    except Exception as e:
        print(f"Error fetching robots: {e}")
        return

if __name__ == "__main__":
    main()