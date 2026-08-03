from typing import Optional


class ServerCommandRouter:
    def __init__(self):
        self._commands: dict[str, object] = {}
        self._transfer_commands: set = set()

    def register(self, command: object) -> None:
        for key in [command.name] + command.aliases:
            self._commands[key] = command
        if hasattr(command, 'is_transfer') and command.is_transfer:
            self._transfer_commands.add(command.name)
            for alias in command.aliases:
                self._transfer_commands.add(alias)

    def is_transfer_command(self, cmd_name: str) -> bool:
        return cmd_name in self._transfer_commands

    def dispatch(self, ctx: object, raw: str) -> Optional[bool]:
        if not raw or not raw.strip():
            return True
        raw = raw.strip()
        cmd_name = raw.split()[0] if raw.strip() else raw
        if cmd_name in self._commands:
            return self._commands[cmd_name].execute(ctx, raw)
        return None
