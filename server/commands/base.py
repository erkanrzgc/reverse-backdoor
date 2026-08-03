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
    screenshot_count: int = 0


class ServerCommand(ABC):
    name: str = ''
    aliases: list[str] = []
    is_transfer: bool = False

    @abstractmethod
    def execute(self, ctx: ServerSessionContext, raw: str) -> Optional[bool]:
        ...
