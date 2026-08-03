import subprocess
import os


def check_sudo_exploits():
    """Check for sudo privilege escalation opportunities."""
    results = []
    try:
        output = subprocess.check_output(
            'sudo -l', shell=True, stderr=subprocess.STDOUT, timeout=5
        ).decode(errors='replace')
        if 'NOPASSWD' in output:
            results.append('[!] Sudo NOPASSWD entries found:\n' + output)
        elif 'may run' in output:
            results.append('[+] Sudo entries found:\n' + output)
    except Exception:
        pass
    return '\n'.join(results) if results else '[-] No sudo opportunities found'


def find_suid_binaries():
    """Find SUID binaries for potential privilege escalation."""
    try:
        output = subprocess.check_output(
            'find / -perm -4000 -type f 2>/dev/null',
            shell=True, timeout=30
        ).decode(errors='replace')
        return output.strip() or '[-] No SUID binaries found'
    except Exception:
        return '[-] SUID scan failed'


def check_kernel_exploits():
    """Suggest known kernel exploits based on kernel version."""
    try:
        version = subprocess.check_output(
            'uname -r', shell=True
        ).decode(errors='replace').strip()
        return f'[*] Kernel version: {version}\n[*] Check exploit-db for applicable exploits'
    except Exception:
        return '[-] Could not determine kernel version'


def check_service_permissions():
    """Check for misconfigured service permissions."""
    try:
        output = subprocess.check_output(
            'find /etc/systemd/system /lib/systemd/system -type f -writable 2>/dev/null',
            shell=True, timeout=10
        ).decode(errors='replace')
        return output.strip() or '[-] No writable service files found'
    except Exception:
        return '[-] Service check failed'
