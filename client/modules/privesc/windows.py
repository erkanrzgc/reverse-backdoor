import os
import subprocess

if os.name != 'nt':
    def check_uac():
        return '[-] Windows-only'

    def check_services():
        return '[-] Windows-only'

    def check_unquoted_paths():
        return '[-] Windows-only'

    def check_always_install_elevated():
        return '[-] Windows-only'
else:
    def check_uac():
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
        try:
            output = subprocess.check_output(
                'sc query state= all | findstr /i "SERVICE_NAME"',
                shell=True, timeout=10
            ).decode(errors='replace')
            return output.strip() or '[-] Service enumeration failed'
        except Exception:
            return '[-] Service enumeration failed'

    def check_unquoted_paths():
        try:
            output = subprocess.check_output(
                'wmic service get name,pathname',
                shell=True, timeout=10
            ).decode(errors='replace')
            lines = output.split('\n')
            unquoted = [l for l in lines if l.strip()
                       and 'C:\\Windows' not in l
                       and '"' not in l
                       and l.strip() != 'Name']
            if unquoted:
                return f'[!] {len(unquoted)} potentially unquoted paths found:\n' + '\n'.join(unquoted[:10])
            return '[-] No unquoted paths found'
        except Exception:
            return '[-] Unquoted path check failed'

    def check_always_install_elevated():
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
