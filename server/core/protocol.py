import json
import socket
import threading
from typing import Any


class Protocol:
    """Newline-delimited JSON wire protocol. One instance per connection."""

    MAX_MESSAGE_SIZE = 100 * 1024 * 1024

    def __init__(self, sock: socket.socket):
        self._sock = sock
        self._recv_buffer = b''
        self._send_lock = threading.Lock()

    def send(self, data: Any) -> None:
        payload = json.dumps(data).encode() + b'\n'
        with self._send_lock:
            self._sock.sendall(payload)

    def recv(self) -> Any:
        while True:
            if b'\n' in self._recv_buffer:
                message, self._recv_buffer = self._recv_buffer.split(b'\n', 1)
                try:
                    return json.loads(message.decode())
                except (ValueError, UnicodeDecodeError):
                    continue
            chunk = self._sock.recv(8192)
            if not chunk:
                raise ConnectionError("Connection closed")
            self._recv_buffer += chunk
            if len(self._recv_buffer) > self.MAX_MESSAGE_SIZE:
                raise ValueError("Message exceeds maximum size")

    def drain(self, timeout: float = 1.0) -> None:
        try:
            self._sock.settimeout(timeout)
            while True:
                self._sock.recv(8192)
        except (socket.timeout, OSError):
            pass
        finally:
            self._sock.settimeout(None)
