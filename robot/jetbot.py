import random

class FakeJetbot:
    """
    Mock hardware SDK for a Jetbot-style robot.
    """
    def __init__(self):
        self.status = "idle"
        self.speed = 0.0

    def forward(self, speed: float = 1.0):
        self.status = "moving_forward"
        self.speed = speed
        print(f"\n[HARDWARE] Motor engaged: Moving forward at speed {self.speed}")

    def stop(self):
        self.status = "stopped"
        self.speed = 0.0
        print("\n[HARDWARE] Brakes applied: Stopped")

    def turn_left(self):
        self.status = "turning_left"
        print("\n[HARDWARE] Steering: Turning left")

    def turn_right(self):
        self.status = "turning_right"
        print("\n[HARDWARE] Steering: Turning right")

    def read_sensor(self) -> dict:
        """Simulates reading telemetry data from physical sensors."""
        # generate random values
        temperature = round(random.uniform(25.0, 35.0), 2)
        battery_level = random.randint(20, 100),
        return {
            "temperature": temperature,
            "battery_level": battery_level,
            "hardware_state": self.status
        }