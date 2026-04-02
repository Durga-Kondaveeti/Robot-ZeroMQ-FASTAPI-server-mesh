import socket


def get_free_port() -> int:
    """
    Helper method to dynamically find an available port
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]
