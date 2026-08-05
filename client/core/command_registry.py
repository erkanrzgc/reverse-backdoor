from typing import Optional


class CommandRegistry:
    def __init__(self):
        self._key_map: dict[str, object] = {}

    def register(self, command: object) -> None:
        for key in [command.name] + getattr(command, 'aliases', []):
            self._key_map[key] = command

    def dispatch(self, ctx: object, raw: str) -> Optional[bool]:
        if not raw or not raw.strip():
            return True
        cmd_name = raw.split()[0] if raw else raw
        if cmd_name in self._key_map:
            return self._key_map[cmd_name].execute(ctx, raw)
        return None
