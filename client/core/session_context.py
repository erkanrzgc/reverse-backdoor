from dataclasses import dataclass, field
from typing import Any, Optional
import socket


@dataclass
class SessionContext:
    sock: socket.socket
    protocol: Any
    platform: Any
    keylogger: Optional[Any] = None
    keylogger_thread: Optional[Any] = None
    proc_holder: dict = field(default_factory=lambda: {'proc': None})

    def cleanup(self) -> None:
        if self.keylogger and hasattr(self.keylogger, 'self_destruct'):
            self.keylogger.self_destruct()
        proc = self.proc_holder.get('proc')
        if proc:
            try:
                proc.kill()
            except Exception:
                pass
