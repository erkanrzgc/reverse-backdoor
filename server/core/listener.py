import socket
import threading

from server.ui.prompt import print_colored
from server.core.agent_registry import AgentRegistry


def _accept_loop(host, port, session_callback, encryption, shutdown_event):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(10)
        sock.settimeout(1.0)
    except Exception as e:
        print_colored(f'[-] Failed to bind listener: {str(e)}', 'red')
        shutdown_event.set()
        return

    print_colored(f'[+] Listening on {host}:{port}', 'green')

    while not shutdown_event.is_set():
        try:
            target, ip = sock.accept()
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


def start_listener(host, port, session_callback, encryption=False):
    shutdown_event = threading.Event()
    accept_thread = threading.Thread(
        target=_accept_loop,
        args=(host, port, session_callback, encryption, shutdown_event),
        daemon=True,
    )
    accept_thread.start()
    return shutdown_event
