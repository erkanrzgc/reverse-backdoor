import time
import random
import threading
import collections

from dataclasses import dataclass, field
from typing import Optional, Callable


@dataclass
class BeaconConfig:
    sleep_time: float = 5.0
    jitter: float = 0.3
    kill_date: Optional[str] = None
    working_hours: Optional[tuple[int, int]] = None

    def get_sleep(self) -> float:
        base = self.sleep_time
        j = base * self.jitter
        return base + random.uniform(-j, j)

    def should_activate(self) -> bool:
        from datetime import datetime
        if self.kill_date:
            try:
                deadline = datetime.strptime(self.kill_date, '%Y-%m-%d')
                if datetime.now() > deadline:
                    return False
            except Exception:
                pass
        if self.working_hours:
            start, end = self.working_hours
            hour = datetime.now().hour
            if not (start <= hour < end):
                return False
        return True


class TaskQueue:
    def __init__(self):
        self._queue = collections.deque()
        self._lock = threading.Lock()
        self._results: dict[int, str] = {}
        self._counter = 0

    def enqueue(self, command: str) -> int:
        with self._lock:
            self._counter += 1
            task_id = self._counter
            self._queue.append((task_id, command))
            return task_id

    def dequeue(self) -> Optional[tuple[int, str]]:
        with self._lock:
            return self._queue.popleft() if self._queue else None

    def put_result(self, task_id: int, result: str):
        with self._lock:
            self._results[task_id] = result

    def get_result(self, task_id: int) -> Optional[str]:
        with self._lock:
            return self._results.pop(task_id, None)

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._queue)

    def is_empty(self) -> bool:
        with self._lock:
            return len(self._queue) == 0


class BeaconMode:
    def __init__(self, config: BeaconConfig = None):
        self.config = config or BeaconConfig()
        self.task_queue = TaskQueue()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self, on_checkin: Callable, on_task: Callable):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._beacon_loop,
            args=(on_checkin, on_task),
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _beacon_loop(self, on_checkin, on_task):
        while self._running:
            if not self.config.should_activate():
                time.sleep(30)
                continue

            try:
                on_checkin()
            except Exception:
                pass

            while not self.task_queue.is_empty():
                task = self.task_queue.dequeue()
                if task:
                    try:
                        result = on_task(task[1])
                        self.task_queue.put_result(task[0], result)
                    except Exception as e:
                        self.task_queue.put_result(task[0], f'[-] Task error: {str(e)}')

            sleep_duration = self.config.get_sleep()
            time.sleep(sleep_duration)

    def queue_command(self, command: str) -> int:
        return self.task_queue.enqueue(command)

    def get_pending(self) -> int:
        return self.task_queue.pending_count
