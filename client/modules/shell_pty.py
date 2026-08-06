import os
import pty
import select
import threading
import subprocess

_pty_master = None


def start_pty_shell(protocol):
    global _pty_master
    if os.name == 'nt':
        _windows_shell(protocol)
        return
    master_fd, slave_fd = pty.openpty()
    _pty_master = master_fd
    pid = os.fork()
    if pid == 0:
        os.close(master_fd)
        os.setsid()
        for fd in (0, 1, 2):
            os.dup2(slave_fd, fd)
        for shell in ('/bin/bash', '/usr/bin/bash', '/usr/local/bin/bash', '/bin/sh'):
            try:
                os.execv(shell, [shell, '-i'])
            except FileNotFoundError:
                continue
        os._exit(1)
    os.close(slave_fd)
    def _reader():
        while True:
            try:
                r, _, _ = select.select([master_fd], [], [], 0.5)
                if r:
                    data = os.read(master_fd, 4096)
                    if not data:
                        break
                    protocol.send(data.decode(errors='replace'))
            except (OSError, ConnectionError):
                break
    def _writer():
        while True:
            try:
                cmd = protocol.recv()
                if cmd is None:
                    break
                os.write(master_fd, (cmd + '\n').encode())
            except (OSError, ConnectionError):
                break
    tw = threading.Thread(target=_writer, daemon=True)
    tw.start()
    tr = threading.Thread(target=_reader, daemon=True)
    tr.start()
    tw.join()
    os.close(master_fd)
    _pty_master = None
    os.waitpid(pid, 0)


def send_special(cmd):
    if _pty_master is None:
        return
    seq = {'ctrl_c': b'\x03', 'ctrl_z': b'\x1a', 'ctrl_d': b'\x04', 'ctrl_l': b'\x0c'}.get(cmd)
    if seq:
        try:
            os.write(_pty_master, seq)
        except OSError:
            pass


def _windows_shell(protocol):
    proc = subprocess.Popen(['cmd.exe'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        try:
            cmd = protocol.recv()
            if cmd is None:
                break
            proc.stdin.write((cmd + '\n').encode())
            proc.stdin.flush()
            out = proc.stdout.readline()
            protocol.send(out.decode(errors='replace'))
        except Exception:
            break
    proc.terminate()
