import subprocess


def check_uac():
    """Check UAC bypass potential and current privilege level."""
    results = []
    try:
        output = subprocess.check_output(
            'whoami /priv', shell=True, timeout=5
        ).decode(errors='replace')
        results.append(output)
    except Exception:
        results.append('[-] Privilege check failed')
    return '\n'.join(results)


def check_services():
    """Find misconfigured Windows services."""
    try:
        output = subprocess.check_output(
            'wmic service get name,pathname,startname,startmode 2>nul',
            shell=True, timeout=10
        ).decode(errors='replace')
        return output.strip() or '[-] Service enumeration failed'
    except Exception:
        return '[-] wmic not available'


def check_unquoted_paths():
    """Check for unquoted service paths."""
    try:
        output = subprocess.check_output(
            'wmic service get name,pathname | findstr /i /v "C:\\Windows" | findstr /i /v """',
            shell=True, timeout=10
        ).decode(errors='replace')
        if output.strip():
            return f'[!] Unquoted service paths found:\n{output}'
        return '[-] No unquoted paths found'
    except Exception:
        return '[-] Unquoted path check failed'


def check_always_install_elevated():
    """Check AlwaysInstallElevated registry keys."""
    try:
        import winreg
        for path in [
            r'SOFTWARE\Policies\Microsoft\Windows\Installer',
            r'SOFTWARE\Wow6432Node\Policies\Microsoft\Windows\Installer',
        ]:
            for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try:
                    key = winreg.OpenKey(hive, path)
                    val, _ = winreg.QueryValueEx(key, 'AlwaysInstallElevated')
                    if val == 1:
                        return f'[!] AlwaysInstallElevated enabled in {path}'
                except Exception:
                    pass
        return '[-] AlwaysInstallElevated not enabled'
    except Exception:
        return '[-] Registry check failed'
