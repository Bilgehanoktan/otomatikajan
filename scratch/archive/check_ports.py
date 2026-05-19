import socket
import sys

def test_port(port):
    try:
        with socket.create_connection(("localhost", port), timeout=1.0) as s:
            print(f"Port {port} is OPEN")
            return True
    except Exception as e:
        print(f"Port {port} is CLOSED: {e}")
        return False

test_port(5433)
test_port(5432)
