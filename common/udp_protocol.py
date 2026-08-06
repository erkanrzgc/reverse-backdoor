import json
import socket
import threading
import uuid
from typing import Any, Optional, Tuple


class UdpProtocol:
    MAX_SIZE = 65535

    def __init__(self, sock=None):
        self.sock = sock or socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._lock = threading.Lock()

    def send(self, data: Any, addr: Tuple[str, int]) -> None:
        payload = json.dumps(data).encode()
        with self._lock:
            self.sock.sendto(payload, addr)

    def recv(self, timeout: Optional[float] = None) -> Tuple[Any, Tuple[str, int]]:
        if timeout is not None:
            self.sock.settimeout(timeout)
        try:
            data, addr = self.sock.recvfrom(self.MAX_SIZE)
            return json.loads(data.decode()), addr
        except socket.timeout:
            raise
        finally:
            if timeout is not None:
                self.sock.settimeout(None)

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


class UdpServer(UdpProtocol):
    def __init__(self, host: str = '0.0.0.0', port: int = 5555):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((host, port))
        super().__init__(sock)
        self._sessions: dict[str, Tuple[str, int]] = {}
        self._session_lock = threading.Lock()

    def register_client(self, addr: Tuple[str, int]) -> str:
        session_id = uuid.uuid4().hex[:12]
        with self._session_lock:
            self._sessions[session_id] = addr
        return session_id

    def get_addr(self, session_id: str) -> Optional[Tuple[str, int]]:
        with self._session_lock:
            return self._sessions.get(session_id)

    def remove_client(self, session_id: str):
        with self._session_lock:
            self._sessions.pop(session_id, None)

    def sendto(self, data: Any, session_id: str) -> None:
        addr = self.get_addr(session_id)
        if addr is None:
            raise ValueError(f"Unknown session: {session_id}")
        self.send(data, addr)

    def recvfrom(self, timeout: Optional[float] = None) -> Tuple[Any, str, Tuple[str, int]]:
        data, addr = self.recv(timeout)
        with self._session_lock:
            for sid, sad in self._sessions.items():
                if sad == addr:
                    return data, sid, addr
        sid = self.register_client(addr)
        return data, sid, addr

    @property
    def sessions(self) -> dict:
        with self._session_lock:
            return dict(self._sessions)


class UdpClient(UdpProtocol):
    def __init__(self, host: str = '127.0.0.1', port: int = 5555):
        super().__init__()
        self._server_addr: Tuple[str, int] = (host, port)
        self._session_id: Optional[str] = None

    def send(self, data: Any) -> None:
        super().send(data, self._server_addr)

    def recv(self, timeout: Optional[float] = None) -> Any:
        data, addr = super().recv(timeout)
        return data

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    @session_id.setter
    def session_id(self, value: str):
        self._session_id = value

    @property
    def server_addr(self) -> Tuple[str, int]:
        return self._server_addr
