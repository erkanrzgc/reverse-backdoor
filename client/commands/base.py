from abc import ABC, abstractmethod
from typing import Optional


class Command(ABC):
    name: str = ''
    aliases: list[str] = []

    def matches(self, raw: str) -> bool:
        cmd_name = raw.split()[0] if raw.strip() else raw
        return cmd_name == self.name or cmd_name in self.aliases

    @abstractmethod
    def execute(self, ctx, raw: str) -> Optional[bool]:
        ...
