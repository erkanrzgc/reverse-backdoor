from client.commands.base import Command
from client.modules.shell import run_command


class PsCommand(Command):
    name = 'ps'

    def execute(self, ctx, raw: str):
        run_command(ctx.protocol, ctx.platform.process_list_cmd(), ctx.proc_holder)
        return True


class IfconfigCommand(Command):
    name = 'ifconfig'
    aliases = ['ip']

    def execute(self, ctx, raw: str):
        run_command(ctx.protocol, ctx.platform.network_info_cmd(), ctx.proc_holder)
        return True


class KillCommand(Command):
    name = 'kill'

    def execute(self, ctx, raw: str):
        target = raw[5:].strip()
        from client.modules.process_ops import kill_process
        kill_process(ctx.protocol, ctx.platform, target)
        return True


class PkillCommand(Command):
    name = 'pkill'

    def execute(self, ctx, raw: str):
        target = raw[6:].strip()
        run_command(ctx.protocol, ctx.platform.pkill_cmd(target), ctx.proc_holder)
        return True


class GrepCommand(Command):
    name = 'grep'

    def execute(self, ctx, raw: str):
        pattern = raw[5:].strip()
        run_command(ctx.protocol, ctx.platform.grep_cmd(pattern), ctx.proc_holder)
        return True
