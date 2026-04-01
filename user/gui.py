import requests
import queue
import tkinter as tk
from tkinter import scrolledtext
from .mesh_node import UserMeshNode

CLOUD_URL = "http://localhost:8000"

class RobotDashboard(tk.Tk):
    def __init__(self, target_robot, config):
        super().__init__()
        self.title(f"Robot Dashboard - {target_robot}")
        self.geometry("600x450")

        self.target_robot = target_robot
        self.msg_queue = queue.Queue()

        # UI Setup
        self.setup_ui()

        # Start Mesh Network
        self.mesh = UserMeshNode(
            robot_id=target_robot,
            user_port=config["user_pub_port"],
            robot_port=config["robot_pub_port"],
            player_port=config["player_pub_port"],
            on_message_received=self.queue_message
        )
        self.mesh.start()

        self.log_message(f"Connected to Mesh for {target_robot}")

        # Start checking the queue for incoming ZMQ messages
        self.check_queue()

    def setup_ui(self):
        # Top Label
        tk.Label(self, text="Real-Time Telemetry", font=("Arial", 14, "bold")).pack(pady=5)

        # Scrolled Text Box for Logs (Read-only)
        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, width=70, height=15, state='disabled')
        self.log_area.pack(pady=5, padx=10)

        # Control Buttons Frame
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        # Buttons calling mesh.send_command
        tk.Button(btn_frame, text="Forward", width=10, command=lambda: self.mesh.send_command("forward")).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(btn_frame, text="Left", width=10, command=lambda: self.mesh.send_command("left")).grid(row=1, column=0, padx=5, pady=5)
        tk.Button(btn_frame, text="Stop", width=10, command=lambda: self.mesh.send_command("stop")).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(btn_frame, text="Right", width=10, command=lambda: self.mesh.send_command("right")).grid(row=1, column=2, padx=5, pady=5)

        # Disconnect Button
        tk.Button(self, text="Close Connection", command=self.close_connection).pack(pady=5)

    def queue_message(self, msg):
        """Called by the ZMQ background thread."""
        self.msg_queue.put(msg)

    def check_queue(self):
        """Checks for new messages and updates the UI safely."""
        while not self.msg_queue.empty():
            msg = self.msg_queue.get()
            self.log_message(msg)

        # Check again in 100ms
        self.after(100, self.check_queue)

    def log_message(self, msg):
        """Inserts text into the scrolling log area."""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END) # Auto-scroll to bottom
        self.log_area.config(state='disabled')

    def close_connection(self):
        self.mesh.send_disconnect()
        self.log_message("Disconnected. Closing UI...")
        self.after(1000, self.destroy) # Close window after 1 second
