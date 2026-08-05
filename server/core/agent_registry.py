import threading
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentInfo:
    agent_id: str
    sock: object
    ip: str
    hostname: str = 'unknown'
    os: str = 'unknown'
    user: str = 'unknown'
    privilege: str = 'unknown'
    connected_at: float = field(default_factory=time.time)

    @property
    def label(self) -> str:
        if self.hostname and self.hostname != 'unknown':
            return f'{self.hostname}_{self.ip}'
        return self.ip


class AgentRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    obj = super().__new__(cls)
                    obj._agents = {}
                    obj._counter = 0
                    obj._lock = threading.RLock()
                    cls._instance = obj
        return cls._instance

    def register(self, sock, ip) -> str:
        with self._lock:
            self._counter += 1
            agent_id = f'agent-{self._counter}'
            self._agents[agent_id] = AgentInfo(
                agent_id=agent_id,
                sock=sock,
                ip=ip,
            )
            return agent_id

    def unregister(self, agent_id: str):
        with self._lock:
            self._agents.pop(agent_id, None)

    def get(self, agent_id: str) -> Optional[AgentInfo]:
        return self._agents.get(agent_id)

    def update_info(self, agent_id: str, **kwargs):
        with self._lock:
            info = self._agents.get(agent_id)
            if info:
                for k, v in kwargs.items():
                    if hasattr(info, k):
                        setattr(info, k, v)

    def list_all(self) -> dict:
        with self._lock:
            return dict(self._agents)

    def broadcast(self, command: str) -> None:
        from server.core.protocol import Protocol
        with self._lock:
            for info in list(self._agents.values()):
                try:
                    protocol = Protocol(info.sock)
                    protocol.send(command)
                except Exception:
                    pass
