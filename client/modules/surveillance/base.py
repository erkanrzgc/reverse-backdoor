from abc import ABC, abstractmethod
from typing import Optional


class CaptureProvider(ABC):
    @abstractmethod
    def capture(self) -> Optional[bytes]:
        ...

    @property
    @abstractmethod
    def extension(self) -> str:
        ...
