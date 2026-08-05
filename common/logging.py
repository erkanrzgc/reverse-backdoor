"""Structured logging with rotation and levels."""

import os
import sys
import time
import threading
from datetime import datetime

LEVELS = {'DEBUG': 10, 'INFO': 20, 'WARN': 30, 'ERROR': 40}
_level_names = {v: k for k, v in LEVELS.items()}


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
                    cls._instance = obj
        return cls._instance

    def set_level(self, level: str):
        self._level = LEVELS.get(level.upper(), LEVELS['INFO'])

    def add_file_handler(self, path: str, max_size: int = 5 * 1024 * 1024, backups: int = 3):
        handler = _RotatingFileHandler(path, max_size, backups)
        self._handlers.append(handler)

    def add_console_handler(self):
        self._handlers.append(_ConsoleHandler())

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
