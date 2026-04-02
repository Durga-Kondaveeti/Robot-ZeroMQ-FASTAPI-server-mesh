# General Robotics: Real-Time Robot Telemetry & Control Mesh

## Overview
Real-time data channel between three simulated entities:
1. **Robot** (edge device)
2. **Cloud Service**
3. **User**.

Once connected, they establish a decentralized, peer-to-peer network mesh allowing direct publish/subscribe communication between all three parties, with end-to-end encrypted payloads.

## Architecture
The system is separated into two distinct layers to ensure scalability and a clean separation of concerns.

**1. The Control Plane (Discovery & Matchmaking)**
- Running on a **FastAPI** HTTP server
- Handles robot registration, heartbeat monitoring, and connection orchestration
- When a user connects, the server generates a per-session encryption key, dynamically allocates ports, spawns a Cloud Player process, and returns the full mesh configuration to all entities

**2. The Data Plane (P2P Pub/Sub Mesh)**
- Powered by **ZeroMQ (pyzmq)**
- Each entity binds its own ZMQ `PUB` socket and connects `SUB` sockets to the other two
- All payloads are encrypted with a **Fernet (AES-128)** session key distributed at connection time
- Forms a true triangle mesh where all three entities communicate directly

```text
    Player (Cloud)
    /   \
   /     \
  /       \
 /         \
Robot ──── User
```

## Repository Structure
```text
repo/
├── cloud_service/      # FastAPI orchestrator and Player background process
├── robot/              # Robot simulator, mesh node, and mocked hardware SDK
├── user/               # GUI dashboard client and mesh node
├── tests/              # Full pytest test suite
├── run.py              # Unified entry point to launch all components
├── requirements.txt    # Python dependencies
└── README.md
```

## How to Run

### Prerequisites
- Python 3.9+
- macOS or Linux (terminal spawning uses `osascript` / `gnome-terminal`)

### 1. Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Launch Everything (Recommended)
```bash
# Launch with 2 robots (default)
python3 run.py

# Launch with N robots
python3 run.py 5
```

This opens separate terminal windows for:
- Cloud Service (FastAPI on port 8000)
- Each Robot instance(s)
- User Service
- Cloud Player (spawned automatically when the User connects)

### 3. Manual Startup (Alternative)
Open four separate terminals, all with `.venv` activated:

```bash
# Terminal 1 — Cloud Service
uvicorn cloud_service.main:app --host 0.0.0.0 --port 8000

# Terminal 2 — Robot
python3 -m robot.main

# Terminal 3 — User
python3 -m user.main

# Terminal 4 — Cloud Player (auto-spawned, but can be run manually)
python3 -m cloud_service.player <robot_id> <player_port> <robot_port> <user_port> <session_key>
```

### 4. Using the Dashboard
1. The User GUI will list all active robots
2. Select a robot number to connect
3. The Cloud Player spawns automatically in a new terminal
4. Use the directional buttons to send commands — telemetry streams live into the log window
5. Click **Close Connection** to gracefully tear down the mesh

### 5. Run Tests
```bash
pytest tests/ -v
```

## Pub/Sub Topics
| Topic | Publisher | Subscriber(s) | Purpose |
|---|---|---|---|
| `robot/{id}/sensor` | Robot | Player, User | Raw sensor/location data |
| `robot/{id}/processed` | Player | User | Analyzed data with status |
| `robot/{id}/command` | User | Robot | Directional commands |
| `robot/{id}/status` | Any | All | Heartbeats and shutdown signals |

## Assumptions & Design Decisions

### Security & Encryption
- **Assumption:** In production, FastAPI endpoints would be secured via HTTPS/mTLS, protecting the session key in transit
- **Enhancement:** All ZMQ payloads are encrypted with a per-session **Fernet (AES-128)** key, protecting the data plane
- **Assumption:** CurveZMQ was intentionally avoided to keep dependencies minimal and the project easy to run

### Telemetry & Sensor Data
- **Enhancement:** The spec requires `{ "state": 25.5 }`. We match the `state` key but use a 2D coordinate array `[x, y]` that actively updates with each directional command, making the simulation more realistic for a mobile robot

### Edge Cases & Resource Management
- **Enhancement:** Duplicate registration is rejected with `HTTP 409` if a robot is currently active; stale robots (no heartbeat in 5s) are allowed to re-register
- **Enhancement:** When a User disconnects, a shutdown signal is sent over both the command and status topics so the Robot and Cloud Player both tear down their sockets and free their ports cleanly
- **Enhancement:** A 2-second application-level heartbeat loop over the ZMQ mesh detects silent peer drops

### UX & Orchestration
- **Enhancement:** A **tkinter GUI** cleanly separates the live telemetry stream from the command input, with color-coded log output (white = raw, cyan = processed, yellow = system alerts)
- **Enhancement:** The Cloud Player is spawned in a **visible terminal window** to clearly demonstrate the three-node architecture
- **Enhancement:** `run.py` provides a single command to launch the entire simulation

### Performance & Logging
- **Enhancement:** Sensor payloads carry a timestamp so the User GUI calculates and displays **real-time millisecond latency**
- **Enhancement:** Append-only **CSV logs** are written to `logs/robot_logs/` and `logs/player_logs/` for post-session analysis

## Testing
Tests were generated with AI assistance and, they cover:
- All ZMQ mesh node behavior (robot and user)
- Command routing to the FakeJetbot hardware
- Encryption/decryption flow
- GUI queue and message rendering
- Cloud Service endpoints (register, heartbeat, connect, disconnect)
- Duplicate and stale robot registration
- Graceful disconnect and reconnection
