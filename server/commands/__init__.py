from server.core.command_router import ServerCommandRouter
from server.commands.system_commands import HelpCommand, ClearCommand, QuitCommand
from server.commands.transfer_commands import UploadCommand, DownloadCommand, ScreenshotCommand, WebcamCommand


def build_server_router() -> ServerCommandRouter:
    router = ServerCommandRouter()
    router.register(HelpCommand())
    router.register(ClearCommand())
    router.register(QuitCommand())
    router.register(UploadCommand())
    router.register(DownloadCommand())
    router.register(ScreenshotCommand())
    router.register(WebcamCommand())
    return router
