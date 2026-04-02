import os

CLOUD_HOST = os.getenv("CLOUD_HOST", "127.0.0.1")
CLOUD_PORT = os.getenv("CLOUD_PORT", "8000")

CLOUD_URL = f"http://{CLOUD_HOST}:{CLOUD_PORT}"
