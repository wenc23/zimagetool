"""线程安全的图片生成任务状态管理。"""

import threading
import time
import uuid


TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


class GenerationCancelled(Exception):
    """生成任务被用户取消。"""


class TaskManager:
    def __init__(self, retention_seconds=3600, max_completed_tasks=100):
        self._lock = threading.RLock()
        self._tasks = {}
        self._cancel_events = {}
        self._active_task_id = None
        self._retention_seconds = retention_seconds
        self._max_completed_tasks = max_completed_tasks

    def create_task(self):
        """创建唯一活动任务；仍有工作线程时返回 (None, active_id)。"""
        with self._lock:
            self._cleanup_locked()
            if self._active_task_id is not None:
                return None, self._active_task_id

            task_id = str(uuid.uuid4())
            now = time.time()
            self._tasks[task_id] = {
                "status": "pending",
                "progress": 0,
                "stage": "等待生成...",
                "created_at": now,
                "updated_at": now,
            }
            self._cancel_events[task_id] = threading.Event()
            self._active_task_id = task_id
            return task_id, None

    def update(self, task_id, **changes):
        """更新任务；取消标志一旦设置，不允许工作线程覆盖取消状态。"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return False
            event = self._cancel_events.get(task_id)
            if event is not None and event.is_set():
                return False
            task.update(changes)
            task["updated_at"] = time.time()
            return True

    def fail(self, task_id, message):
        return self.update(task_id, status="failed", message=message, progress=0)

    def cancel(self, task_id):
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return False, "任务不存在"
            if task.get("status") in TERMINAL_STATUSES:
                return False, f"任务已经{task.get('status')}，无法取消"

            event = self._cancel_events.get(task_id)
            if event is not None:
                event.set()
            task.update({
                "status": "cancelled",
                "message": "❌ 任务已被用户取消",
                "stage": "任务已取消",
                "updated_at": time.time(),
            })
            return True, "✅ 任务已取消"

    def raise_if_cancelled(self, task_id):
        with self._lock:
            event = self._cancel_events.get(task_id)
            cancelled = event is not None and event.is_set()
        if cancelled:
            raise GenerationCancelled()

    def is_cancelled(self, task_id):
        with self._lock:
            event = self._cancel_events.get(task_id)
            return event is not None and event.is_set()

    def get(self, task_id):
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            return {
                key: value
                for key, value in task.items()
                if key not in {"created_at", "updated_at"}
            }

    def has_active_worker(self):
        with self._lock:
            return self._active_task_id is not None

    def finish_worker(self, task_id):
        """仅在线程真正退出后允许下一个任务开始。"""
        with self._lock:
            if self._active_task_id == task_id:
                self._active_task_id = None
            self._cancel_events.pop(task_id, None)
            self._cleanup_locked()

    def _cleanup_locked(self):
        now = time.time()
        removable = [
            task_id
            for task_id, task in self._tasks.items()
            if task_id != self._active_task_id
            and task.get("status") in TERMINAL_STATUSES
            and now - task.get("updated_at", now) > self._retention_seconds
        ]
        for task_id in removable:
            self._tasks.pop(task_id, None)
            self._cancel_events.pop(task_id, None)

        completed = sorted(
            (
                (task.get("updated_at", 0), task_id)
                for task_id, task in self._tasks.items()
                if task_id != self._active_task_id
                and task.get("status") in TERMINAL_STATUSES
            ),
            reverse=True,
        )
        for _, task_id in completed[self._max_completed_tasks:]:
            self._tasks.pop(task_id, None)
            self._cancel_events.pop(task_id, None)
