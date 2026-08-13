import unittest

from task_manager import GenerationCancelled, TaskManager


class TaskManagerTests(unittest.TestCase):
    def test_only_one_worker_can_be_active(self):
        manager = TaskManager()
        first_id, active_id = manager.create_task()
        self.assertIsNotNone(first_id)
        self.assertIsNone(active_id)

        second_id, active_id = manager.create_task()
        self.assertIsNone(second_id)
        self.assertEqual(active_id, first_id)

        manager.update(first_id, status="completed", progress=100)
        manager.finish_worker(first_id)
        second_id, active_id = manager.create_task()
        self.assertIsNotNone(second_id)
        self.assertIsNone(active_id)

    def test_cancel_flag_cannot_be_overwritten_by_worker(self):
        manager = TaskManager()
        task_id, _ = manager.create_task()

        success, _ = manager.cancel(task_id)
        self.assertTrue(success)
        self.assertFalse(manager.update(task_id, status="generating", progress=50))
        self.assertEqual(manager.get(task_id)["status"], "cancelled")

        with self.assertRaises(GenerationCancelled):
            manager.raise_if_cancelled(task_id)

    def test_terminal_task_retention_is_bounded(self):
        manager = TaskManager(retention_seconds=3600, max_completed_tasks=2)
        ids = []
        for _ in range(3):
            task_id, _ = manager.create_task()
            ids.append(task_id)
            manager.update(task_id, status="completed")
            manager.finish_worker(task_id)

        retained = [manager.get(task_id) for task_id in ids]
        self.assertEqual(sum(task is not None for task in retained), 2)


if __name__ == "__main__":
    unittest.main()
