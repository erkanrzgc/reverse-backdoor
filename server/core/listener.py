import socket
import threading
import ssl

from server.ui.prompt import print_colored


def _accept_loop(host, port, session_callback, encryption, tls, shutdown_event):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(10)
        sock.settimeout(1.0)

        if tls:
            try:
                ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE
                ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            except Exception as e:
                print_colored(f'[-] Failed to create TLS context: {str(e)}', 'red')
                shutdown_event.set()
                return

    except Exception as e:
        print_colored(f'[-] Failed to bind listener: {str(e)}', 'red')
        shutdown_event.set()
        return

    proto = 'TLS' if tls else 'TCP'
    print_colored(f'[+] Listening on {host}:{port} ({proto})', 'green')

    while not shutdown_event.is_set():
        try:
            target, ip = sock.accept()
            if tls:
                try:
                    target = ssl_ctx.wrap_socket(target, server_side=True)
                except ssl.SSLError as e:
                    print_colored(f'[-] TLS handshake failed for {ip}: {str(e)[:80]}', 'red')
                    try:
                        target.close()
                    except Exception:
                        pass
                    continue
            target.settimeout(None)
            print_colored(f'[+] Connection from: {ip}', 'green')
            t = threading.Thread(
                target=_session_thread,
                args=(target, ip, session_callback, encryption),
                daemon=True,
            )
            t.start()
        except socket.timeout:
            continue
        except ssl.SSLError as e:
            print_colored(f'[-] TLS error: {str(e)}', 'red')
            continue
        except Exception as e:
            if not shutdown_event.is_set():
                print_colored(f'[-] Accept error: {str(e)}', 'red')
            break

    try:
        sock.close()
    except Exception:
        pass
    print_colored('[-] Listener stopped', 'yellow')


def _session_thread(target, ip, session_callback, encryption):
    try:
        session_callback(target, ip, encryption)
    except Exception:
        pass
    finally:
        try:
            target.close()
        except Exception:
            pass


def start_listener(host, port, session_callback, encryption=False, tls=False):
    shutdown_event = threading.Event()
    accept_thread = threading.Thread(
        target=_accept_loop,
        args=(host, port, session_callback, encryption, tls, shutdown_event),
        daemon=True,
    )
    accept_thread.start()
    return shutdown_event
