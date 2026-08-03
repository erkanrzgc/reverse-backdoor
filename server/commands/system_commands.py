from server.commands.base import ServerCommand
from server.handlers.local_commands import handle_help, handle_clear
from server.ui.prompt import print_colored


class HelpCommand(ServerCommand):
    name = 'help'

    def execute(self, ctx, raw: str):
        handle_help()
        return True


class ClearCommand(ServerCommand):
    name = 'clear'
    aliases = ['cls']

    def execute(self, ctx, raw: str):
        handle_clear()
        return True


class QuitCommand(ServerCommand):
    name = 'quit'

    def execute(self, ctx, raw: str):
        ctx.protocol.send(raw)
        print_colored('[*] Session terminated', 'yellow')
        return False
