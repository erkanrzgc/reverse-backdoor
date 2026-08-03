from client.commands.base import Command


class PersistenceCommand(Command):
    name = 'persistence'

    def execute(self, ctx, raw: str):
        args = raw[12:].strip().split()
        if not args:
            return self._show_usage(ctx)

        subcmd = args[0].lower()

        if subcmd == 'install':
            return self._handle_install(ctx, args[1:])
        elif subcmd == 'remove':
            return self._handle_remove(ctx, args[1:])
        elif subcmd == 'check':
            return self._handle_check(ctx, args[1:])
        elif subcmd == 'list':
            return self._handle_list(ctx)
        else:
            return self._show_usage(ctx)

    def _show_usage(self, ctx) -> bool:
        from client.modules.persistence import list_methods
        methods = list_methods()
        usage = f"""[-] Usage:
  persistence install <method> [--name <name>]
  persistence remove <method> [--name <name>]
  persistence check [<method>]
  persistence list
{methods}"""
        ctx.protocol.send(usage)
        return True

    def _handle_install(self, ctx, args) -> bool:
        from client.modules.persistence import install_persistence

        if not args:
            ctx.protocol.send('[-] Usage: persistence install <method> [--name <name>]')
            return True

        method = args[0]
        kwargs = {}
        i = 1
        while i < len(args):
            if args[i] == '--name' and i + 1 < len(args):
                kwargs['payload_name'] = args[i + 1]
                i += 2
            else:
                i += 1

        result = install_persistence(method, **kwargs)
        ctx.protocol.send(result)
        return True

    def _handle_remove(self, ctx, args) -> bool:
        from client.modules.persistence import remove_persistence

        if not args:
            ctx.protocol.send('[-] Usage: persistence remove <method> [--name <name>]')
            return True

        method = args[0]
        kwargs = {}
        i = 1
        while i < len(args):
            if args[i] == '--name' and i + 1 < len(args):
                kwargs['payload_name'] = args[i + 1]
                i += 2
            else:
                i += 1

        result = remove_persistence(method, **kwargs)
        ctx.protocol.send(result)
        return True

    def _handle_check(self, ctx, args) -> bool:
        from client.modules.persistence import check_persistence
        method = args[0] if args else None
        result = check_persistence(method)
        ctx.protocol.send(result)
        return True

    def _handle_list(self, ctx) -> bool:
        from client.modules.persistence import list_methods
        ctx.protocol.send(list_methods())
        return True
