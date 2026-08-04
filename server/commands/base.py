from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any
import socket


@dataclass
class ServerSessionContext:
    sock: socket.socket
    protocol: Any
    ip: str
    loot_dir: str
    agent_id: str = ''
    screenshot_count: int = 0

    @property
    def agent_loot_dir(self) -> str:
        import os
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        path = os.path.join(self.loot_dir, self.agent_id, today)
        os.makedirs(path, exist_ok=True)
        return path


class ServerCommand(ABC):
    name: str = ''
    aliases: list[str] = []
    is_transfer: bool = False

    @abstractmethod
    def execute(self, ctx: ServerSessionContext, raw: str) -> Optional[bool]:
        ...
