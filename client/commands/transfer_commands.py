from client.commands.base import Command
from client.modules.file_ops import download_file, upload_file
from client.modules.shell import run_command


class UploadCommand(Command):
    name = 'upload'

    def execute(self, ctx, raw: str):
        file_name = raw[7:].strip()
        download_file(ctx.protocol, file_name)
        ctx.protocol.send(f'[+] File received: {file_name}')
        return True


class DownloadCommand(Command):
    name = 'download'

    def execute(self, ctx, raw: str):
        file_name = raw[9:].strip()
        upload_file(ctx.protocol, file_name)
        return True
