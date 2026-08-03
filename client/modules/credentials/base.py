from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class CredentialEntry:
    source: str
    identity: str
    username: str
    password: str


class CredentialCollector(ABC):
    @abstractmethod
    def collect(self) -> List[CredentialEntry]:
        ...
