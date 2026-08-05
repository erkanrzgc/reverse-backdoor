import base64
import hashlib
import json
import os

from server.ui.prompt import print_colored


class ChunkedReceiver:
    def __init__(self):
        self._buffers: dict = {}
        self._metas: dict = {}

    def receive(self, protocol, save_path: str) -> bool:
        msg = protocol.recv()
        if not msg:
            return False

        try:
            data = json.loads(msg) if isinstance(msg, str) and msg.startswith('{') else None
        except json.JSONDecodeError:
            data = None

        if isinstance(data, dict) and data.get('type') == 'file_start':
            fid = os.path.basename(save_path)
            self._metas[fid] = {
                'name': data['name'],
                'size': data['size'],
                'chunks': data['chunks'],
                'received': {},
                'sha256': hashlib.sha256(),
            }
            protocol.send('ack')

            for i in range(data['chunks']):
                try:
                    chunk_raw = protocol.recv()
                    chunk_data = json.loads(str(chunk_raw))
                    if chunk_data.get('type') == 'file_chunk':
                        idx = chunk_data['index']
                        raw_bytes = base64.b64decode(chunk_data['data'])
                        self._metas[fid]['received'][idx] = raw_bytes
                        self._metas[fid]['sha256'].update(raw_bytes)
                        protocol.send('ack')
                    else:
                        break
                except Exception:
                    break

            if len(self._metas[fid]['received']) == data['chunks']:
                complete_msg = protocol.recv()
                if isinstance(complete_msg, str) and complete_msg == 'file_complete':
                    self._write_reassembled(fid, save_path)
                    return True
                else:
                    print_colored('[-] Chunked download incomplete', 'yellow')
                    return False
        else:
            with open(save_path, 'wb') as f:
                f.write(base64.b64decode(msg))
            print_colored(f'[+] File saved: {save_path}', 'green')
            return True
        return False

    def _write_reassembled(self, fid: str, save_path: str):
        meta = self._metas.pop(fid, None)
        if not meta:
            return
        ordered = [meta['received'][i] for i in sorted(meta['received'].keys())]
        data = b''.join(ordered)
        with open(save_path, 'wb') as f:
            f.write(data)
        sha = meta['sha256'].hexdigest()
        print_colored(f'[+] File saved: {save_path} ({len(data)} bytes, SHA256: {sha})', 'green')

    def _verify_sha256(self, fid: str, expected: str) -> bool:
        meta = self._metas.get(fid)
        if not meta:
            return False
        actual = meta['sha256'].hexdigest()
        if actual != expected:
            print_colored(f'[-] SHA256 mismatch: expected {expected}, got {actual}', 'red')
            return False
        return True
