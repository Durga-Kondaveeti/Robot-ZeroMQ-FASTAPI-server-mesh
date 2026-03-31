# General Robotics: Real-Time Robot Telemetry & Control Mesh

## Overview
Real-time data channel between three simulated entities: Robot (edge device), Cloud Service, and a User. Once connected, they establish a decentralized, peer-to-peer network mesh allowing direct publish/subscribe communication between all three parties.

## Architecture
The system is separated into two distinct layers to ensure scalability and a clean separation of concerns:

**1. The Control Plane (Discovery & Matchmaking)**
* Running on **FastAPI** HTTP server.
* Handles robot registration, robot heartbeat monitoring, and connection orchestration.
* When a user connects, the server dynamically spawns a cloud-side "Player" process and returns the necessary connection details (IPs/Ports) for the entities to form the mesh.

**2. The Data Plane (P2P Pub/Sub Mesh)**
* Powered by **ZeroMQ (pyzmq)**.
* Each entity binds its own ZeroMQ `PUB` socket and connects `SUB` sockets to the others.
* This forms a true triangle data channel where entities publish and subscribe directly to each other.

## Repository Structure
```text
repo/
├── cloud_service/      # FastAPI orchestrator and Player background process [cite: 55, 56]
├── robot/              # Robot simulator network logic and mocked hardware SDK [cite: 57, 58]
├── user/               # CLI dashboard client [cite: 59, 60]
├── run.py              # Orchestrator script to run all components locally
├── requirements.txt    # Python dependencies [cite: 62]
└── README.md           # Documentation [cite: 61]
```

## Functional Flow & Topics
All real-time communication over the mesh utilizes the following topics:
* `robot/{robot_id}/sensor`: Robot publishes raw sensor data (e.g., `{ "state": 25.5 }`). Subscribed by the Player and User.
* `robot/{robot_id}/processed`: Player publishes analyzed data (e.g., `{ "state": 25.5, "status": "normal" }`). Subscribed by the User[cite: 34].
* `robot/{robot_id}/command`: User publishes control commands (e.g., `{ "command": "stop" }`). Subscribed by the Robot to actuate the mocked hardware.
* `robot/{robot_id}/status`: Used for general status updates from any entity. Subscribed by all.

## Assumptions
* **Local Network Simulation:** For demonstration on a single machine, ports are dynamically assigned or bound to `localhost` (`127.0.0.1`).
* **Hardware Abstraction:** The robot's physical actions are mocked via a fake Jetbot SDK class.

## Additional features Addressed
* **Scalability:** By using FastAPI strictly for discovery, the Cloud Service is completely unburdened by high-frequency telemetry data, allowing it to efficiently manage thousands of robots.
* **Resource Management & Error Handling:** The REST API expects regular heartbeats. If a robot disconnects, it is gracefully purged from the registry. Player processes are safely terminated when connections drop.
* **Code Quality:** No hardcoded network routes exist in the mesh. Everything is dynamically provisioned during the matchmaking phase[cite: 64].

## How to Run
To be completed