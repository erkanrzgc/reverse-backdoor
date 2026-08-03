import os
import sys
import signal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.core.config import load_config
from server.core.listener import start_listener
from server.core.session import run_session, run_master_loop


def main():
    config = load_config()

    def session_callback(sock, ip, encryption):
        loot_dir = config.get('loot_dir', './loot')
        run_session(sock, ip, loot_dir, encryption)

    shutdown_event = start_listener(
        config['bind_host'],
        config['bind_port'],
        session_callback,
        config.get('encryption', False),
        config.get('tls', False),
    )

    signal.signal(signal.SIGINT, lambda s, f: shutdown_event.set())
    signal.signal(signal.SIGTERM, lambda s, f: shutdown_event.set())

    run_master_loop(config.get('loot_dir', './loot'), config['encryption'])

    shutdown_event.set()


if __name__ == '__main__':
    main()
