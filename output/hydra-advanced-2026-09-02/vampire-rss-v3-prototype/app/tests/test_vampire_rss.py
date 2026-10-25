"""Owned-child memory stops; all solver executions in these tests are mocked."""
from collections import deque
import ctypes
from pathlib import Path
import signal
import sys
import unittest
from unittest.mock import Mock, call, patch

APP = Path(__file__).resolve().parents[1]
SOURCE = APP.parent / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
sys.path[:0] = [str(APP), str(SOURCE), str(SOURCE / "peano-lab/py")]
import vampire_limits as policy
import vampire_process as runner
import vampire_bridge as bridge
from test_vampire_profiles import _Selector, _Stream


class ReaderTests(unittest.TestCase):
    def test_fixed_darwin_layout_and_full_response_are_required(self):
        self.assertEqual(ctypes.sizeof(runner._ProcTaskInfo), 96)
        self.assertEqual(runner._ProcTaskInfo.resident_size.offset, 8)

        def full_response(pid, flavor, arg, buffer, size):
            self.assertEqual((pid, flavor, arg, size), (731, 4, 0, 96))
            ctypes.cast(buffer, ctypes.POINTER(runner._ProcTaskInfo)).contents.resident_size = 123456
            return size

        query = Mock(side_effect=full_response)
        with patch.object(runner, "_proc_pidinfo", return_value=query):
            self.assertEqual(runner._resident_size(731), 123456)
        query.assert_called_once()
        for received in (0, -1, 95):
            with self.subTest(received=received), patch.object(runner, "_proc_pidinfo", return_value=lambda *_: received):
                with self.assertRaises(OSError):
                    runner._resident_size(731)
        with patch.object(runner, "_proc_pidinfo", return_value=lambda *_: 96):
            with self.assertRaises(OSError):
                runner._resident_size(731)  # A live zero-RSS result is incomplete.

    def test_no_query_after_reaping_and_completion_race_is_not_failure(self):
        done = Mock(pid=731)
        done.poll.return_value = 0
        with patch.object(runner, "_resident_size") as read:
            self.assertIsNone(runner._owned_child_rss(done))
        read.assert_not_called()
        raced = Mock(pid=731)
        raced.poll.side_effect = [None, 0]
        with patch.object(runner, "_resident_size", side_effect=OSError("already exited")):
            self.assertIsNone(runner._owned_child_rss(raced))
        live = Mock(pid=731)
        live.poll.return_value = None
        with patch.object(runner, "_resident_size", side_effect=OSError("accounting denied")):
            with self.assertRaises(OSError):
                runner._owned_child_rss(live)


class OwnedRunnerTests(unittest.TestCase):
    def run_fixture(self, *, readings, clock, code=-signal.SIGKILL, live=True,
                    chunks=(b"% SZS status Theorem for untrusted_fixture\n", b""), finish_on_eof=False):
        process = Mock(pid=731, stdin=_Stream(301), stdout=_Stream(302), stderr=_Stream(303))
        process.poll.return_value = None if live else code
        process.wait.return_value = code
        buffers = {302: deque(chunks), 303: deque([b""])}

        def read(fd, _count):
            item = buffers[fd].popleft()
            if fd == 302 and item == b"" and finish_on_eof:
                process.poll.return_value = code
            return item

        manifest = {"executable": {"sha256": "b" * 64}}
        with patch.object(runner, "package", return_value=(APP / "unused", manifest, {})), \
             patch.object(runner, "_resident_size", side_effect=readings) as accounting, \
             patch.object(runner.subprocess, "Popen", return_value=process) as launch, \
             patch.object(runner.selectors, "DefaultSelector", _Selector), \
             patch.object(runner.os, "set_blocking"), \
             patch.object(runner.os, "write", side_effect=lambda _fd, data: len(data)), \
             patch.object(runner.os, "read", side_effect=read), \
             patch.object(runner.time, "monotonic", side_effect=clock), \
             patch.object(runner.os, "kill") as kill_pid, patch.object(runner.os, "killpg") as kill_group:
            instance = runner.VampireRunner("research")
            result = instance("fof(goal,conjecture,(a = a)).\n")
        kill_pid.assert_not_called()
        kill_group.assert_not_called()
        return instance, result, process, launch, accounting

    def test_accounting_failure_prevents_startup(self):
        instance, result, process, launch, accounting = self.run_fixture(
            readings=[OSError("denied")], clock=[0, 0.01])
        self.assertEqual(result["status"], "unavailable")
        self.assertFalse(result["available"])
        self.assertFalse(result["executed"])
        self.assertEqual(instance.calls, 0)
        self.assertEqual(instance.records, [])
        launch.assert_not_called()
        process.kill.assert_not_called()
        accounting.assert_called_once_with(runner.os.getpid())

    def test_memory_stop_kills_and_reaps_only_owned_child_and_preserves_evidence(self):
        stop = policy.solver_limits("research")["solver_rss_stop_bytes"]
        instance, result, process, launch, accounting = self.run_fixture(
            readings=[16 * 1024**2, 32 * 1024**2, stop + 4096], clock=[0, 0, 0.02, 0.021])
        self.assertEqual(result["status"], "resource_limit")
        self.assertTrue(result["resource_limited"])
        self.assertEqual(result["termination"]["reason"], "owned_child_rss_watchdog")
        self.assertEqual(result["exit_code"], -signal.SIGKILL)
        self.assertEqual(result["peak_sampled_rss_bytes"], stop + 4096)
        self.assertEqual(result["rss_samples"], 2)
        self.assertIn("SZS status Theorem", result["stdout"])
        self.assertEqual(instance.calls, 1)
        self.assertEqual(len(instance.records), 1)
        self.assertNotIn("stdout", instance.records[0])
        self.assertEqual(instance.records[0]["peak_sampled_rss_bytes"], stop + 4096)
        process.kill.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=0.5)
        accounting.assert_has_calls([call(runner.os.getpid()), call(731), call(731)])
        launch.assert_called_once_with(runner.spawn_argv("research"), cwd=str(APP), env=dict(runner.ENVIRONMENT),
            stdin=runner.subprocess.PIPE, stdout=runner.subprocess.PIPE, stderr=runner.subprocess.PIPE,
            close_fds=True, start_new_session=False)

    def test_live_accounting_failure_still_kills_reaps_and_returns_no_proof(self):
        instance, result, process, _, _ = self.run_fixture(
            readings=[16 * 1024**2, 32 * 1024**2, OSError("short response")],
            clock=[0, 0, 0.02, 0.021])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["termination"]["reason"], "owned_child_rss_accounting_error")
        self.assertEqual(result["exit_code"], -signal.SIGKILL)
        self.assertEqual(result["rss_samples"], 1)
        self.assertEqual(result["peak_sampled_rss_bytes"], 32 * 1024**2)
        self.assertEqual(instance.calls, 1)
        process.kill.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=0.5)

    def test_completed_child_is_drained_and_reaped_without_false_resource_failure(self):
        instance, result, process, _, accounting = self.run_fixture(
            readings=[16 * 1024**2], clock=[0, 0, 0, 0.01], code=0, live=False)
        self.assertEqual(result["status"], "completed")
        self.assertFalse(result["resource_limited"])
        self.assertEqual(result["rss_samples"], 0)
        self.assertEqual(result["peak_sampled_rss_bytes"], 0)
        self.assertIn("SZS status Theorem", result["stdout"])
        self.assertEqual(instance.calls, 1)
        accounting.assert_called_once_with(runner.os.getpid())
        process.kill.assert_not_called()
        self.assertTrue(process.wait.called)

    def test_busy_output_does_not_sample_more_often_than_fixed_cadence(self):
        instance, result, process, _, accounting = self.run_fixture(
            readings=[16 * 1024**2, 32 * 1024**2, 32 * 1024**2],
            clock=[0, 0, 0.005, 0.010, 0.015, 0.020, 0.025, 0.026],
            chunks=(b"x", b"x", b"x", b"x", b"x", b""), code=0, finish_on_eof=True)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["rss_samples"], 2)
        self.assertEqual(accounting.call_count, 3)  # Includes the one self-probe.
        self.assertEqual(instance.calls, 1)
        process.kill.assert_not_called()


class ResourceAdviceTests(unittest.TestCase):
    def test_resource_stop_rejects_even_complete_external_refutation(self):
        # The fixture is a complete dependency graph for an equality goal.
        # Resource metadata must reject it before native suggestions are made.
        from peano_lab.engine.state import start
        from peano_lab.engine.tactics import apply_tactic
        from peano_lab.kernel.formulas import parse_formula_with_names
        target, names = parse_formula_with_names("forall a b. a=b -> a=b")
        state = start(target, names)
        for args in ("a", "b", "h"):
            state = apply_tactic(state, "intro", args)
        problem = bridge.export_state(state)
        output = ("% SZS status Theorem for fixture\n% SZS output start Proof for fixture\n"
                  "fof(f1,hypothesis,(hydra_c1=hydra_c0),file('unknown',hydra_h0)).\n"
                  "fof(f2,negated_conjecture,~(hydra_c1=hydra_c0),file('unknown',hydra_goal)).\n"
                  "fof(f3,plain,$false,inference(equality_resolution,[],[f1,f2])).\n"
                  "% SZS output end Proof for fixture\n")
        used, count = bridge.proof_used_inputs(output, {"hydra_goal", "hydra_h0"})
        self.assertEqual(used, ("hydra_h0",))
        self.assertEqual(count, 3)
        run = {"available": True, "executed": True, "exit_code": 0, "status": "resource_limit",
               "stdout": output, "stderr": "", "problem_sha256": problem.sha256,
               "peak_sampled_rss_bytes": 384 * 1024**2 + 4096, "rss_samples": 2,
               "termination": {"reason": "owned_child_rss_watchdog"}}
        ordinary = {**run, "status": "completed", "termination": {"reason": "exit_zero"}}
        advisory = bridge.VampireAdvisor(lambda _: ordinary).advise(state)
        self.assertEqual(advisory["status"], "advisory_theorem")
        self.assertTrue(advisory["suggestions"])
        result = bridge.VampireAdvisor(lambda _: run).advise(state)
        self.assertEqual(result["status"], "resource_limit")
        self.assertEqual(result["suggestions"], [])
        self.assertEqual(result["candidates"], ())
        self.assertFalse(result["kernel_checked"])
        self.assertEqual(result["solver"]["termination"]["reason"], "owned_child_rss_watchdog")
        self.assertEqual(result["solver"]["peak_sampled_rss_bytes"], run["peak_sampled_rss_bytes"])
        self.assertEqual(result["solver"]["rss_samples"], 2)


if __name__ == "__main__":
    unittest.main()
