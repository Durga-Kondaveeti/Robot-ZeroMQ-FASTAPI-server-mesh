import json
from cryptography.fernet import Fernet, InvalidToken


def generate_session_key():
    return Fernet.generate_key().decode('utf-8')


class MeshCipher:
    """
    Helper class to handle end-to-end symmetric encryption for
    the ZMQ Data Plane.
    """

    def __init__(self, secret_key: str):
        self.fernet = Fernet(secret_key.encode('utf-8'))

    def encrypt(self, data: dict) -> bytes:
        """Serializes a dictionary to JSON and encrypts it."""
        json_string = json.dumps(data)
        return self.fernet.encrypt(json_string.encode('utf-8'))

    def decrypt(self, payload: bytes) -> dict:
        """Decrypts a payload and deserializes it back to a dictionary."""
        try:
            decrypted_bytes = self.fernet.decrypt(payload)
            return json.loads(decrypted_bytes.decode('utf-8'))
        except InvalidToken:
            print("[Security Error] Received unencrypted or tampered payload.")
            return {}
