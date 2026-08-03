import threading
import socket
import struct


class SOCKS5Proxy:
    """SOCKS5 proxy server that tunnels traffic through the agent connection."""

    def __init__(self, protocol, bind_host='127.0.0.1', bind_port=1080):
        self._protocol = protocol
        self._bind_host = bind_host
        self._bind_port = bind_port
        self._running = False

    def start(self):
        self._running = True
        t = threading.Thread(target=self._accept_loop, daemon=True)
        t.start()
        return f'[+] SOCKS5 proxy listening on {self._bind_host}:{self._bind_port}'

    def stop(self):
        self._running = False

    def _accept_loop(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self._bind_host, self._bind_port))
        server.listen(5)
        server.settimeout(1.0)
        while self._running:
            try:
                client, addr = server.accept()
                t = threading.Thread(target=self._handle_client, args=(client,), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except Exception:
                break
        server.close()

    def _handle_client(self, client):
        try:
            data = client.recv(4096)
            if len(data) < 3:
                client.close()
                return
            self._protocol.send(data)
            response = self._protocol.recv()
            client.sendall(response)
        except Exception:
            pass
        finally:
            client.close()
