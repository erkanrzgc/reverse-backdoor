import json
import base64
import socket
import threading
from typing import Any

from common.crypto import ECDHEncryption


class EncryptedProtocol:
    MAX_MESSAGE_SIZE = 100 * 1024 * 1024

    def __init__(self, sock: socket.socket):
        self.sock = sock
        self._recv_buffer = b''
        self._send_lock = threading.Lock()
        self._crypto = ECDHEncryption()

    def perform_key_exchange(self, initiator: bool = False) -> None:
        if initiator:
            self.sock.sendall(self._crypto.public_key_bytes)
            peer_pub = self._recv_exact(self._crypto.PUBLIC_KEY_SIZE)
        else:
            peer_pub = self._recv_exact(self._crypto.PUBLIC_KEY_SIZE)
            self.sock.sendall(self._crypto.public_key_bytes)
        if not peer_pub:
            raise ConnectionError("Connection closed during key exchange")
        self._crypto.compute_shared_key(peer_pub)

    def _recv_exact(self, n: int) -> bytes:
        data = b''
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def send(self, data: Any) -> None:
        if not self._crypto.is_ready():
            raise RuntimeError("Key exchange not completed")
        raw = json.dumps(data).encode()
        encrypted = self._crypto.encrypt(raw)
        payload = base64.b64encode(encrypted) + b'\n'
        with self._send_lock:
            self.sock.sendall(payload)

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
            chunk = self.sock.recv(8192)
            if not chunk:
                raise ConnectionError("Connection closed")
            self._recv_buffer += chunk
            if len(self._recv_buffer) > self.MAX_MESSAGE_SIZE:
                raise ValueError("Message exceeds maximum size")

    def drain(self, timeout: float = 1.0) -> None:
        try:
            self.sock.settimeout(timeout)
            while True:
                self.sock.recv(8192)
        except (socket.timeout, OSError):
            pass
        finally:
            self.sock.settimeout(None)
