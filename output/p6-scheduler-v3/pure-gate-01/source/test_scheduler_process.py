"""Finite scheduler-query lifecycle fixtures; no real child or scheduler."""
import importlib.util
from pathlib import Path
from unittest.mock import patch
import unittest

SPEC = importlib.util.spec_from_file_location("scheduler_v3_test", Path(__file__).with_name("remote_provider_smoke.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Child:
    def __init__(self, payload=b"one job", code=0, finish=True):
        self.payload, self.exit_code, self.finish = payload, code, finish
        self.polls = self.kills = self.waits = 0
        self.returncode = None

    def launch(self, argv, **kwargs):
        self.argv = argv
        kwargs["stdout"].write(self.payload)
        kwargs["stdout"].flush()
        return self

    def poll(self):
        self.polls += 1
        if self.returncode is None and self.finish and self.polls > 1:
            self.returncode = self.exit_code
        return self.returncode

    def kill(self):
        self.kills += 1
        self.returncode = -9

    def wait(self, timeout):
        assert timeout == 3
        self.waits += 1
        return self.returncode


class SchedulerProcessTests(unittest.TestCase):
    def query(self, child, elapsed, sleep_error=None):
        with patch.object(MODULE.shutil, "which", return_value="/usr/bin/scontrol"), \
             patch.object(MODULE.subprocess, "Popen", side_effect=child.launch) as launch, \
             patch.object(MODULE.time, "monotonic", side_effect=[0, elapsed]), \
             patch.object(MODULE.time, "sleep", side_effect=sleep_error):
            try:
                return MODULE.read_scontrol("21911045")
            finally:
                self.assertEqual(launch.call_count, 1, "No automatic retry is permitted")
                self.assertEqual(child.argv, ["/usr/bin/scontrol", "-o", "show", "job", "21911045"])

    def test_one_slow_reply_within_finite_limit_completes(self):
        child = Child()
        self.assertEqual(self.query(child, 6), ("one job", 0))
        self.assertEqual((child.kills, child.waits), (0, 1))

    def test_wall_stop_reports_actual_reason_and_reaps_once(self):
        child = Child(finish=False)
        with self.assertRaisesRegex(RuntimeError, r"wall ceiling; elapsed_seconds=15.1; output_bytes=7; actual_child_exit=-9; no retry"):
            self.query(child, 15.1)
        self.assertEqual((child.kills, child.waits), (1, 1))

    def test_output_ceiling_is_not_enlarged_by_wall_change(self):
        child = Child(payload=b"x" * 65537, finish=False)
        with self.assertRaisesRegex(RuntimeError, r"output ceiling;.*output_bytes=65537"):
            self.query(child, 0.1)
        self.assertEqual((child.kills, child.waits), (1, 1))

    def test_outer_cancellation_still_kills_the_exact_child(self):
        child = Child(finish=False)
        with self.assertRaises(KeyboardInterrupt):
            self.query(child, 0.1, KeyboardInterrupt())
        self.assertEqual((child.kills, child.waits), (1, 1))

    def test_failed_reply_does_not_retry_or_become_a_reservation(self):
        child = Child(code=1)
        with self.assertRaisesRegex(ValueError, "nonzero actual exit"):
            self.query(child, 0.1)
        self.assertEqual((child.kills, child.waits), (0, 1))

    def test_missing_client_fails_before_launch(self):
        with patch.object(MODULE.shutil, "which", return_value=None), \
             patch.object(MODULE.subprocess, "Popen") as launch:
            with self.assertRaisesRegex(ValueError, "unavailable"):
                MODULE.read_scontrol("21911045")
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
