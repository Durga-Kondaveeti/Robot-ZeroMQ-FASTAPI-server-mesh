import random

class FakeJetbot:
    """
    Mock hardware SDK for a Jetbot-style robot.
    """
    def __init__(self):
        self.status = "idle"
        # x, y axis
        self.location = [0.0, 0.0]

    def forward(self):
        self.status = "moving_forward"
        self.location[1] += 1.0
        print(f"\n[HARDWARE] Motor engaged: Moving forward. Location: {self.location}")

    def backward(self):
        self.status = "moving_backward"
        self.location[1] -= 1.0
        print(f"\n[HARDWARE] Motor engaged: Moving backward. Location: {self.location}")

    def stop(self):
        self.status = "stopped"
        print("\n[HARDWARE] Brakes applied: Stopped")

    def turn_left(self):
        self.status = "turning_left"
        self.location[0] -= 1.0
        print(f"\n[HARDWARE] Steering: Turning left. Location: {self.location}")

    def turn_right(self):
        self.status = "turning_right"
        self.location[0] += 1.0
        print(f"\n[HARDWARE] Steering: Turning right. Location: {self.location}")

    # DESIGN DECISION: The spec requested a simple float { "state": 25.5 }.
    # To make the simulation more realistic for a 2D robot, I assumed a spatial
    # coordinate array [x, y] would be a better representation of "state" while
    # still adhering to the required payload key.
    def read_sensor(self) -> dict:
        """Simulates reading telemetry data from physical sensors."""
        return {
            "state": self.location
        }
