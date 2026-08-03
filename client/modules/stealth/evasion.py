def detect_vm():
    """Detect if running inside a virtual machine or sandbox."""
    import os
    import platform

    indicators = []

    if os.name == 'nt':
        try:
            import subprocess
            output = subprocess.check_output(
                'wmic computersystem get model', shell=True, timeout=5
            ).decode(errors='replace').lower()
            vm_strings = ['virtualbox', 'vmware', 'qemu', 'virtual', 'kvm', 'xen']
            for s in vm_strings:
                if s in output:
                    indicators.append(f'VM detected via WMIC: {s}')
        except Exception:
            pass

    if os.path.exists('/.dockerenv'):
        indicators.append('Docker container detected')
    if os.path.exists('/proc/vz'):
        indicators.append('OpenVZ/Virtuozzo detected')

    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read().lower()
            if 'hypervisor' in cpuinfo:
                indicators.append('Hypervisor detected in CPU info')
    except Exception:
        pass

    total_ram = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') if hasattr(os, 'sysconf') else 0
    if 0 < total_ram < (2 * 1024 * 1024 * 1024):
        indicators.append(f'Suspiciously low RAM: {total_ram // (1024*1024)} MB')

    cpu_count = os.cpu_count() or 0
    if 0 < cpu_count < 2:
        indicators.append(f'Suspiciously low CPU count: {cpu_count}')

    return indicators if indicators else ['[-] No VM indicators detected']


def obfuscate_string(s):
    """Simple XOR string obfuscation for embedding strings."""
    import random
    key = random.randint(1, 255)
    return key, ''.join(chr(ord(c) ^ key) for c in s)


def deobfuscate_string(obfuscated, key):
    return ''.join(chr(ord(c) ^ key) for c in obfuscated)
