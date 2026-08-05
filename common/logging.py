"""Structured logging with rotation, levels, and per-agent files."""

import os
import sys
import threading
from datetime import datetime
from typing import Optional

LEVELS = {'DEBUG': 10, 'INFO': 20, 'WARN': 30, 'ERROR': 40}
_level_names = {v: k for k, v in LEVELS.items()}


class CommandLog:
    __slots__ = ('agent_id', 'command', 'result_preview', 'response_size',
                 'duration_ms', 'status', 'timestamp')

    def __init__(self, agent_id, command, result_preview='', response_size=0,
                 duration_ms=0, status='ok'):
        self.agent_id = agent_id
        self.command = command
        self.result_preview = result_preview[:500]
        self.response_size = response_size
        self.duration_ms = duration_ms
        self.status = status
        self.timestamp = datetime.now()

    def to_json_dict(self):
        return {
            'ts': self.timestamp.isoformat(),
            'agent': self.agent_id,
            'cmd': self.command,
            'preview': self.result_preview,
            'size': self.response_size,
            'ms': self.duration_ms,
            'status': self.status,
        }

    def to_line(self):
        return (
            f'[{self.timestamp.strftime("%H:%M:%S")}] '
            f'{self.agent_id} | {self.command} | '
            f'{self.status} | {self.response_size}b | {self.duration_ms}ms\n'
        )


class Logger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    obj = super().__new__(cls)
                    obj._handlers = []
                    obj._level = LEVELS['INFO']
                    obj._write_lock = threading.Lock()
                    obj._per_agent_dir: Optional[str] = None
                    obj._agent_handlers: dict = {}
                    obj._command_logs: list = []
                    cls._instance = obj
        return cls._instance

    def set_level(self, level: str):
        self._level = LEVELS.get(level.upper(), LEVELS['INFO'])

    def set_agent_log_dir(self, dirpath: str):
        self._per_agent_dir = dirpath
        os.makedirs(dirpath, exist_ok=True)

    def add_file_handler(self, path: str, max_size: int = 5 * 1024 * 1024, backups: int = 3):
        self._handlers.append(_RotatingFileHandler(path, max_size, backups))

    def add_console_handler(self):
        self._handlers.append(_ConsoleHandler())

    def _get_agent_handler(self, agent_id: str):
        if agent_id not in self._agent_handlers:
            dirpath = self._per_agent_dir or 'loot/logs'
            path = os.path.join(dirpath, f'{agent_id}.log')
            self._agent_handlers[agent_id] = _RotatingFileHandler(path, 2 * 1024 * 1024, 5)
        return self._agent_handlers[agent_id]

    def log_command(self, agent_id: str, command: str, result: str = '',
                    response_size: int = 0, duration_ms: int = 0, status: str = 'ok'):
        entry = CommandLog(agent_id, command, str(result), response_size, duration_ms, status)
        self._command_logs.append(entry)
        if len(self._command_logs) > 2000:
            self._command_logs = self._command_logs[-1000:]

        handler = self._get_agent_handler(agent_id)
        handler.write(entry.to_line())

        self.info(f'{agent_id} executed {command}', module='dispatch',
                  size=response_size, ms=duration_ms, status=status)

    def get_recent_commands(self, agent_id: Optional[str] = None, n: int = 20):
        entries = self._command_logs
        if agent_id:
            entries = [e for e in entries if e.agent_id == agent_id]
        return entries[-n:]

    def command_summary(self) -> dict:
        agents = {}
        for entry in self._command_logs:
            if entry.agent_id not in agents:
                agents[entry.agent_id] = {'total': 0, 'ok': 0, 'error': 0, 'commands': set()}
            agents[entry.agent_id]['total'] += 1
            agents[entry.agent_id]['ok' if entry.status == 'ok' else 'error'] += 1
            agents[entry.agent_id]['commands'].add(entry.command)
        return {
            aid: {
                'total': d['total'],
                'ok': d['ok'],
                'error': d['error'],
                'unique_commands': len(d['commands']),
            }
            for aid, d in agents.items()
        }

    def debug(self, msg: str, **kwargs):
        self._log(LEVELS['DEBUG'], msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self._log(LEVELS['INFO'], msg, **kwargs)

    def warn(self, msg: str, **kwargs):
        self._log(LEVELS['WARN'], msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._log(LEVELS['ERROR'], msg, **kwargs)

    def _log(self, level: int, msg: str, **kwargs):
        if level < self._level:
            return
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        level_name = _level_names.get(level, '?')
        extra = ' ' + ' '.join(f'{k}={v}' for k, v in kwargs.items()) if kwargs else ''
        line = f'[{ts}] [{level_name}] {msg}{extra}\n'
        with self._write_lock:
            for handler in self._handlers:
                try:
                    handler.write(line)
                except Exception:
                    pass


class _RotatingFileHandler:
    def __init__(self, path: str, max_size: int, backups: int):
        self._path = path
        self._max_size = max_size
        self._backups = backups
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        self._lock = threading.Lock()

    def write(self, line: str):
        with self._lock:
            try:
                if os.path.exists(self._path) and os.path.getsize(self._path) > self._max_size:
                    self._rotate()
                with open(self._path, 'a') as f:
                    f.write(line)
            except Exception:
                pass

    def _rotate(self):
        for i in range(self._backups - 1, 0, -1):
            src = f'{self._path}.{i}' if i > 1 else self._path
            dst = f'{self._path}.{i + 1}'
            if os.path.exists(src):
                try:
                    os.rename(src, dst)
                except Exception:
                    pass
        if os.path.exists(self._path):
            try:
                os.rename(self._path, f'{self._path}.1')
            except Exception:
                pass


class _ConsoleHandler:
    def write(self, line: str):
        sys.stderr.write(line)


def get_logger() -> Logger:
    return Logger()
