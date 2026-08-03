import json
import base64
import socket
import threading
from typing import Any

from client.utils.crypto import ECDHEncryption


class EncryptedProtocol:
    """Encrypted JSON wire protocol with ECDH key exchange + AES-256-GCM."""

    MAX_MESSAGE_SIZE = 100 * 1024 * 1024

    def __init__(self, sock: socket.socket):
        self._sock = sock
        self._recv_buffer = b''
        self._send_lock = threading.Lock()
        self._crypto = ECDHEncryption()

    def perform_key_exchange(self) -> None:
        server_pub = self._sock.recv(1024)
        if not server_pub:
            raise ConnectionError("Connection closed during key exchange")

        client_pub = self._crypto.public_key_bytes
        self._sock.sendall(client_pub)

        self._crypto.compute_shared_key(server_pub)

    def send(self, data: Any) -> None:
        if not self._crypto.is_ready():
            raise RuntimeError("Key exchange not completed")
        raw = json.dumps(data).encode()
        encrypted = self._crypto.encrypt(raw)
        payload = base64.b64encode(encrypted) + b'\n'
        with self._send_lock:
            self._sock.sendall(payload)

    def recv(self) -> Any:
        if not self._crypto.is_ready():
            raise RuntimeError("Key exchange not completed")
        while True:
            if b'\n' in self._recv_buffer:
                message, self._recv_buffer = self._recv_buffer.split(b'\n', 1)
                try:
                    encrypted = base64.b64decode(message)
                    raw = self._crypto.decrypt(encrypted)
                    return json.loads(raw.decode())
                except (ValueError, Exception):
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
