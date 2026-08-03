from client.commands.base import Command
from client.modules.file_ops import list_dir, change_dir, current_dir, delete, move, read_file, touch
from client.modules.shell import run_command


class LsCommand(Command):
    name = 'ls'

    def execute(self, ctx, raw: str):
        path = raw[3:].strip() if len(raw) > 2 else None
        list_dir(ctx.protocol, ctx.platform, path)
        return True


class CdCommand(Command):
    name = 'cd'

    def execute(self, ctx, raw: str):
        target = raw[3:].strip()
        change_dir(ctx.protocol, target)
        return True


class PwdCommand(Command):
    name = 'pwd'

    def execute(self, ctx, raw: str):
        current_dir(ctx.protocol)
        return True


class RmCommand(Command):
    name = 'rm'

    def execute(self, ctx, raw: str):
        arg_str = raw[3:].strip()
        delete(ctx.protocol, arg_str)
        return True


class MvCommand(Command):
    name = 'mv'

    def execute(self, ctx, raw: str):
        arg_str = raw[3:].strip()
        move(ctx.protocol, arg_str)
        return True


class CatCommand(Command):
    name = 'cat'

    def execute(self, ctx, raw: str):
        path = raw[4:].strip()
        read_file(ctx.protocol, ctx.platform, path)
        return True


class TouchCommand(Command):
    name = 'touch'

    def execute(self, ctx, raw: str):
        path = raw[6:].strip()
        touch(ctx.protocol, ctx.platform, path)
        return True
