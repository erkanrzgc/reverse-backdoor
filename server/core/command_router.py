from typing import Optional


class ServerCommandRouter:
    def __init__(self):
        self._commands: dict[str, object] = {}
        self._transfer_commands: set = set()

    def register(self, command: object) -> None:
        aliases = getattr(command, 'aliases', [])
        for key in [command.name] + aliases:
            self._commands[key] = command
        if getattr(command, 'is_transfer', False):
            self._transfer_commands.add(command.name)
            for alias in aliases:
                self._transfer_commands.add(alias)

    def is_transfer_command(self, cmd_name: str) -> bool:
        return cmd_name in self._transfer_commands

    def dispatch(self, ctx: object, raw: str) -> Optional[bool]:
        if not raw or not raw.strip():
            return True
        cmd_name = raw.split()[0] if raw else raw
        if cmd_name in self._commands:
            return self._commands[cmd_name].execute(ctx, raw)
        return None
