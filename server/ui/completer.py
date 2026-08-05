import os
import readline
from typing import Optional, Callable


class C2Completer:
    def __init__(self):
        self._commands: list[str] = []
        self._get_agents: Optional[Callable] = None
        self._registry = None

    def set_commands(self, commands: list[str]):
        self._commands = sorted(commands)

    def set_agent_provider(self, fn: Callable):
        self._get_agents = fn

    def set_registry(self, registry):
        self._registry = registry

    def complete(self, text: str, state: int) -> Optional[str]:
        line = readline.get_line_buffer()
        tokens = line.split()

        if not line or (len(tokens) == 0 and not line.endswith(' ')):
            candidates = [c + ' ' for c in self._commands if c.startswith(text)]
        elif len(tokens) == 1 and not line.endswith(' '):
            candidates = [c + ' ' for c in self._commands if c.startswith(text)]
        elif len(tokens) >= 2 and tokens[0] == 'interact':
            candidates = self._complete_agent(text)
        elif len(tokens) >= 2 and tokens[0] == 'cd':
            candidates = self._complete_path(text, is_dir=True)
        elif len(tokens) >= 2 and tokens[0] in ('cat', 'rm', 'upload', 'download', 'mv', 'touch',
                                                  'timestomp'):
            candidates = self._complete_path(text, is_dir=False)
        elif len(tokens) >= 2 and tokens[0] == 'persistence':
            candidates = self._complete_persistence(text, tokens)
        elif len(tokens) >= 2 and tokens[0] == 'inject':
            candidates = self._complete_process(text)
        elif len(tokens) >= 2 and tokens[0] in ('steal_token', 'kill'):
            if tokens[0] == 'steal_token' and len(tokens) == 2:
                candidates = [f'{text} ' for _ in range(1)]
            else:
                candidates = self._complete_nothing(text)
        elif len(tokens) >= 2 and tokens[0] == 'priv_enable':
            candidates = self._complete_privilege(text)
        else:
            candidates = [t for t in self._commands if t.startswith(text)]

        try:
            return candidates[state]
        except IndexError:
            return None

    def _complete_agent(self, text: str) -> list[str]:
        if self._get_agents:
            agents = self._get_agents()
            return [f'{aid} ' for aid in agents if aid.startswith(text)]
        return []

    def _complete_path(self, text: str, is_dir: bool = False) -> list[str]:
        try:
            directory = os.path.dirname(text) or '.'
            prefix = os.path.basename(text)
            entries = []
            for entry in os.listdir(directory):
                full = os.path.join(directory, entry)
                if is_dir and not os.path.isdir(full):
                    continue
                if entry.startswith(prefix):
                    match = os.path.join(directory, entry) if directory != '.' else entry
                    if os.path.isdir(full):
                        match += '/'
                    entries.append(match + ' ')
            return entries
        except Exception:
            return []

    def _complete_persistence(self, text: str, tokens: list) -> list[str]:
        methods = ['crontab', 'systemd', 'bashrc', 'xdg',
                    'registry', 'scheduled_task', 'startup_folder', 'wmi']
        if len(tokens) == 2 and tokens[1] in ('install', 'remove', 'check'):
            return [m + ' ' for m in methods if m.startswith(text)]
        if len(tokens) == 2:
            subcommands = ['install', 'remove', 'check', 'list']
            return [s + ' ' for s in subcommands if s.startswith(text)]
        return []

    def _complete_process(self, text: str) -> list[str]:
        common = ['explorer', 'notepad', 'chrome', 'firefox', 'svchost', 'lsass',
                   'winlogon', 'cmd', 'powershell', 'bash', 'python', 'java']
        return [p + ' ' for p in common if p.startswith(text)]

    def _complete_privilege(self, text: str) -> list[str]:
        privs = ['SeDebugPrivilege', 'SeImpersonatePrivilege', 'SeAssignPrimaryTokenPrivilege',
                  'SeTcbPrivilege', 'SeBackupPrivilege', 'SeRestorePrivilege',
                  'SeCreateTokenPrivilege', 'SeLoadDriverPrivilege']
        return [p + ' ' for p in privs if p.startswith(text) or p.lower().startswith(text.lower())]

    def _complete_nothing(self, text: str) -> list[str]:
        return []


def setup_readline(completer: C2Completer, history_file: str = None):
    readline.parse_and_bind('tab: complete')
    readline.set_completer(completer.complete)
    readline.set_completer_delims(' \t\n;')

    if history_file:
        try:
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            readline.read_history_file(history_file)
        except Exception:
            pass

    readline.set_history_length(1000)


def save_history(history_file: str = None):
    if history_file:
        try:
            readline.write_history_file(history_file)
        except Exception:
            pass
