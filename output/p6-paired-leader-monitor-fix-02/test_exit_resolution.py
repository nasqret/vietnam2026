"""Pure /proc and virtual-clock fixtures; never creates an actual child.

The real supervisor, reader, WNOWAIT function and cleanup function are used.
Only OS/process boundaries and time are scripted. These fixtures are not a
claim to have reproduced the Linux teardown interval on a real machine.
"""
import ast
from contextlib import ExitStack
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import signal
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
ORIGINAL = PROJECT / "output/hydra-implementation-2026-09-04/combined-source-bundle-03/source/output/hydra-implementation-2026-09-04/paired-evaluation-v2"
PREVIOUS = HERE.parent / "p6-paired-leader-monitor-fix-01/paired_controller.py"
assert sha256((ORIGINAL / "paired_controller.py").read_bytes()).hexdigest() == "84e78193613505cab6d8d139720a5bb1b0f460db09aec3b0456fbabe4cd76e94"
assert sha256(PREVIOUS.read_bytes()).hexdigest() == "70506feb48a1896411c301f20a4b56ffe79f6312c90745db5d358d6a070a9ad1"
sys.path.insert(0, str(ORIGINAL))  # Metadata-only paired_common, never a native/model import.
spec = importlib.util.spec_from_file_location("paired_exit_resolution_candidate", HERE / "paired_controller.py")
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)

LEADER, PARENT, UID, START = 101, 303, 404, 1234
JOB, SCONTROL = "21980166", "/fixed/bin/scontrol"


def stat(state="R", *, pid=LEADER, ppid=PARENT, pgid=LEADER, sid=LEADER, start=START, flags=4):
    tail = ["0"] * 22
    for index, value in ((0, state), (1, ppid), (2, pgid), (3, sid), (6, flags), (19, start)):
        tail[index] = str(value)
    return (str(pid) + " (worker) " + " ".join(tail) + "\n").encode()


def status(state="R", *, uids=(UID,) * 4, rss=None):
    text = "Name:\tworker\nState:\t" + state + " (fixture)\nUid:\t" + "\t".join(map(str, uids)) + "\n"
    if rss is not None:
        text += "VmRSS:\t" + str(rss) + " kB\n"
    return text.encode()


class OwnedLifecycle:
    """One fake, unreaped Popen and an advancing virtual monotonic clock."""
    pid = LEADER

    def __init__(self, *, exit_at=0.4, missing_at=0.0, flags=4, change_at=None,
                 change=None, status_mutation=None, state_mutation=None,
                 rss_return_at=None, worker_exit=0, tick=True, children=b""):
        self.now = 0.0
        self.exit_at = exit_at
        self.missing_at = missing_at
        self.flags = flags
        self.change_at = change_at
        self.change = change or {}
        self.status_mutation = status_mutation
        self.state_mutation = state_mutation
        self.rss_return_at = rss_return_at
        self.worker_exit = worker_exit
        self.tick = tick
        self.children = children
        self.returncode = None
        self.forced = False
        self.reads, self.events, self.sleeps = [], [], []

    @property
    def natural(self):
        return self.now >= self.exit_at

    @property
    def changed(self):
        return self.change_at is not None and self.now >= self.change_at

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        assert 0 <= seconds <= controller.RESOURCE_LIMITS["sample_seconds"] + 1e-9
        self.sleeps.append(seconds)
        if self.tick:
            self.now += seconds

    def waitid(self, which, pid, options):
        assert which == controller.os.P_PID and pid == self.pid
        assert options & controller.os.WNOWAIT and options & controller.os.WNOHANG
        assert self.returncode is None, "waitid after reap"
        self.events.append((self.now, "peek", self.natural or self.forced))
        return SimpleNamespace(si_pid=self.pid) if self.natural or self.forced else None

    def getpgid(self, pid):
        assert pid == self.pid and self.returncode is None
        return self.pid

    def killpg(self, pid, sig):
        assert pid == self.pid
        self.events.append((self.now, "group_signal", int(sig)))
        if sig == 0:
            if self.returncode is not None:
                raise ProcessLookupError("owned group is empty")
            return
        assert sig == signal.SIGKILL and self.returncode is None, "kill after reap or undeclared signal"
        self.forced = self.forced or not self.natural

    def kill(self, pid, sig):
        assert pid == self.pid and sig == signal.SIGKILL and self.returncode is None
        self.events.append((self.now, "leader_signal", int(sig)))
        self.forced = self.forced or not self.natural

    def wait(self, timeout):
        assert timeout >= 0 and self.returncode is None
        assert self.natural or self.forced, "unbounded wait for a live child"
        self.events.append((self.now, "wait", timeout))
        self.returncode = -signal.SIGKILL if self.forced else self.worker_exit
        return self.returncode

    def read(self, path, maximum):
        assert self.returncode is None, "reading a reaped /proc identity"
        name = str(path)
        self.reads.append((self.now, name, maximum))
        if name == "/proc/101/task/101/children":
            assert maximum == 8192
            return self.children
        state = "Z" if self.natural else "R"
        if self.state_mutation is not None:
            state = self.state_mutation(self, state)
        if name == "/proc/101/stat":
            assert maximum == 8192
            updates = self.change if self.changed else {}
            return stat(state, flags=self.flags if self.now >= self.missing_at else 0, **updates)
        if name == "/proc/101/status":
            assert maximum == 65536
            rss = 100 if self.now < self.missing_at else None
            if self.rss_return_at is not None and self.now >= self.rss_return_at and not self.natural:
                rss = 200
            raw = status(state, rss=rss)
            return self.status_mutation(self, raw) if self.status_mutation else raw
        raise AssertionError("Undeclared process read: " + name)


def supervise(lifecycle, *, should_stop=lambda: False, sample_wrapper=None):
    original_iterdir = Path.iterdir

    def iterdir(path):
        if str(path) == "/proc/101/task":
            return iter([Path("/proc/101/task/101")])
        assert not str(path).startswith("/proc/"), "Unexpected task inventory"
        return original_iterdir(path)

    with TemporaryDirectory(prefix="pure-exit-", dir=HERE) as temporary, ExitStack() as stack:
        app = Path(temporary) / "app"
        app.mkdir()
        directory = Path(temporary) / "case"
        directory.mkdir()
        request = directory / "case-request.json"
        request.write_text("{}\n")
        patches = [
            mock.patch.object(controller.subprocess, "Popen", return_value=lifecycle),
            mock.patch.object(controller.shutil, "which", return_value=SCONTROL),
            mock.patch.object(controller, "environment", return_value={}),
            mock.patch.object(controller, "proc_read", side_effect=lifecycle.read),
            mock.patch.object(controller.os, "getuid", return_value=UID),
            mock.patch.object(controller.os, "getpid", return_value=PARENT),
            mock.patch.object(controller.os, "getpgid", side_effect=lifecycle.getpgid),
            mock.patch.object(controller.os, "waitid", side_effect=lifecycle.waitid, create=True),
            mock.patch.object(controller.os, "P_PID", 1, create=True),
            mock.patch.object(controller.os, "WEXITED", 4, create=True),
            mock.patch.object(controller.os, "WNOHANG", 1, create=True),
            mock.patch.object(controller.os, "WNOWAIT", 0x1000000, create=True),
            mock.patch.object(controller.os, "killpg", side_effect=lifecycle.killpg),
            mock.patch.object(controller.os, "kill", side_effect=lifecycle.kill),
            mock.patch.object(controller.time, "monotonic", side_effect=lifecycle.monotonic),
            mock.patch.object(controller.time, "sleep", side_effect=lifecycle.sleep),
            mock.patch.object(Path, "iterdir", iterdir),
        ]
        for patch in patches:
            stack.enter_context(patch)
        if sample_wrapper is not None:
            original_sample = controller.sample_owned
            stack.enter_context(mock.patch.object(controller, "sample_owned",
                side_effect=lambda *args: sample_wrapper(original_sample(*args))))
        result = controller.supervise_case(app, request, "a" * 64, {"job_id": JOB},
                                             "fixed-wall-30-v1", should_stop)
        assert json.loads((directory / "execution.json").read_text()) == result
    return result


class TerminalResolutionTests(unittest.TestCase):
    def assert_failed(self, result, pattern):
        self.assertRegex(result["termination_reason"], pattern)
        self.assertFalse(result["quiescent"])
        self.assertTrue(result["leader_reaped"])
        self.assertEqual(controller.classify_case(result, {"status": "unknown"}), "infrastructure_failure")

    def test_longer_than_five_reads_resolves_naturally_and_preserves_peak(self):
        life = OwnedLifecycle(exit_at=0.6, missing_at=0.1)
        result = supervise(life)
        resolution = result["terminal_resolution"]
        self.assertEqual(result["termination_reason"], "process_exit")
        self.assertEqual((result["exit_code"], result["quiescent"], result["leader_reaped"]), (0, True, True))
        self.assertEqual(resolution["outcome"], "natural_exit_confirmed")
        self.assertTrue(resolution["natural_exit_confirmed_before_cleanup"])
        self.assertFalse(resolution["missing_rss_was_zero_filled"])
        self.assertGreater(resolution["sample_count"], 5)
        self.assertGreater(resolution["elapsed_seconds"], 0.4)
        self.assertLessEqual(resolution["resolution_and_cleanup_seconds"], 3)
        self.assertEqual(result["peak_sampled_host_rss_bytes"], 100 * 1024)
        self.assertEqual(result["rss_samples"], 3)  # Two real live samples and one confirmed terminal sample.
        pending = resolution["samples"][:-1]
        self.assertTrue(all(frame["leader"]["records"][0]["rss_fields"] == 0 for frame in pending))
        self.assertTrue(all(frame["leader"]["stats"]["after"]["state"] == "R" for frame in pending))
        self.assertTrue(all(int(frame["leader"]["stats"]["after"]["flags"]) & 4 for frame in pending))
        self.assertEqual(resolution["samples"][-1]["leader"]["exit_observations"], [True, True])
        signals = [row for row in life.events if row[1] in {"group_signal", "leader_signal"} and row[2] != 0]
        self.assertTrue(signals)
        self.assertTrue(all(row[0] >= life.exit_at for row in signals))
        self.assertFalse(life.forced)
        signal_index = next(i for i, row in enumerate(life.events) if row[1] == "group_signal" and row[2] == signal.SIGKILL)
        wait_index = next(i for i, row in enumerate(life.events) if row[1] == "wait")
        self.assertLess(signal_index, wait_index)
        self.assertLessEqual(len(controller.canonical(resolution)), 256 * 1024)

    def test_expiry_shares_cleanup_budget_and_forced_exit_is_not_success(self):
        life = OwnedLifecycle(exit_at=4.0)
        result = supervise(life)
        self.assert_failed(result, "exit remained unproven within cleanup budget")
        resolution = result["terminal_resolution"]
        self.assertEqual(resolution["outcome"], "failed")
        self.assertFalse(resolution["natural_exit_confirmed_before_cleanup"])
        self.assertEqual(result["rss_samples"], 0)
        self.assertEqual(result["exit_code"], -signal.SIGKILL)
        self.assertGreaterEqual(life.now, 2.9)
        self.assertLessEqual(life.now, 3)
        self.assertLessEqual(resolution["cleanup_seconds_remaining"], 0.051)
        self.assertLessEqual(resolution["sample_count"], 61)
        self.assertTrue(life.forced)

    def test_missing_rss_without_exiting_flag_fails_immediately(self):
        life = OwnedLifecycle(flags=0)
        result = supervise(life)
        self.assert_failed(result, "without PF_EXITING")
        self.assertIsNone(result["terminal_resolution"])
        self.assertEqual(life.sleeps, [])
        self.assertEqual(result["accounting_diagnostic"]["records"][0]["rss_fields"], 0)

    def test_duplicate_or_malformed_rss_is_never_a_pending_absence(self):
        for extra in (b"VmRSS:\tbad kB\n", b"VmRSS:\t2 MB\n", b"VmRSS:\t1 kB\nVmRSS:\t2 kB\n"):
            with self.subTest(extra=extra):
                life = OwnedLifecycle(status_mutation=lambda life, raw: raw + extra)
                result = supervise(life)
                self.assert_failed(result, "Malformed or ambiguous.*RSS")
                self.assertIsNone(result["terminal_resolution"])
                self.assertEqual(life.sleeps, [])

    def test_all_uid_fields_remain_exact_during_pending_resolution(self):
        for index in range(4):
            def changed(life, raw):
                if life.now < 0.1:
                    return raw
                uids = [UID] * 4
                uids[index] += 1
                return status(uids=uids)
            with self.subTest(index=index):
                result = supervise(OwnedLifecycle(status_mutation=changed))
                self.assert_failed(result, "uid changed")
                self.assertEqual(result["terminal_resolution"]["outcome"], "failed")
                self.assertFalse(result["accounting_diagnostic"]["records"][0]["uid_matches"])

    def test_ambiguous_missing_or_malformed_uid_fails_even_on_later_exit(self):
        variants = (lambda raw: raw + b"Uid:\t404\t404\t404\t404\n",
                    lambda raw: raw.replace(b"Uid:", b"Other:"),
                    lambda raw: raw.replace(b"404\t404\t404\t404", b"404\t404"))
        for mutate in variants:
            with self.subTest(mutate=mutate):
                life = OwnedLifecycle(exit_at=0.3, status_mutation=lambda life, raw: mutate(raw) if life.now >= 0.1 else raw)
                result = supervise(life)
                self.assert_failed(result, "UID accounting")
                self.assertLess(life.now, life.exit_at)

    def test_pid_start_parent_group_session_changes_still_fail(self):
        for change in ({"pid": LEADER + 1}, {"start": START + 1}, {"ppid": PARENT + 1},
                       {"pgid": LEADER + 1}, {"sid": LEADER + 1}):
            with self.subTest(change=change):
                result = supervise(OwnedLifecycle(change_at=0.1, change=change))
                self.assert_failed(result, "Malformed|identity changed|owned session")
                self.assertEqual(result["terminal_resolution"]["outcome"], "failed")

    def test_resumed_rss_is_not_an_exit_confirmation(self):
        result = supervise(OwnedLifecycle(rss_return_at=0.1))
        self.assert_failed(result, "resumed RSS without proving")
        self.assertFalse(result["terminal_resolution"]["natural_exit_confirmed_before_cleanup"])

    def test_zombie_state_regression_across_pending_samples_is_rejected(self):
        def state(life, actual):
            return "Z" if 0.1 <= life.now < 0.2 else actual
        result = supervise(OwnedLifecycle(state_mutation=state))
        self.assert_failed(result, "terminal resolution changed state")
        self.assertEqual(result["terminal_resolution"]["outcome"], "failed")

    def test_cancellation_does_not_turn_cleanup_signal_into_natural_exit(self):
        life = OwnedLifecycle(exit_at=2)
        result = supervise(life, should_stop=lambda: life.now >= 0.1)
        self.assertEqual(result["termination_reason"], "cancelled")
        self.assertFalse(result["quiescent"])
        self.assertEqual(result["terminal_resolution"]["outcome"], "failed")
        self.assertFalse(result["terminal_resolution"]["natural_exit_confirmed_before_cleanup"])

    def test_terminal_resolution_does_not_extend_case_wall(self):
        life = OwnedLifecycle(exit_at=91, missing_at=89)
        result = supervise(life)
        self.assertEqual(result["termination_reason"], "case_wall_limit")
        self.assertLessEqual(life.now, 90.00001)
        self.assertFalse(result["quiescent"])
        self.assertFalse(result["terminal_resolution"]["natural_exit_confirmed_before_cleanup"])

    def test_independent_sample_count_bounds_a_nonadvancing_clock(self):
        result = supervise(OwnedLifecycle(exit_at=1, tick=False))
        self.assert_failed(result, "exit remained unproven")
        self.assertEqual(result["terminal_resolution"]["sample_count"], 61)

    def test_known_memory_over_limit_still_stops_pending_resolution(self):
        def excessive(sample):
            self.assertTrue(sample["pending_leader_exit"])
            return {**sample, "known_rss_bytes": controller.RESOURCE_LIMITS["host_sampled_rss_bytes"] + 1}
        result = supervise(OwnedLifecycle(), sample_wrapper=excessive)
        self.assertEqual(result["termination_reason"], "host_sampled_rss_limit")
        self.assertFalse(result["quiescent"])
        self.assertFalse(result["terminal_resolution"]["natural_exit_confirmed_before_cleanup"])
        self.assertGreater(result["peak_sampled_host_rss_bytes"], controller.RESOURCE_LIMITS["host_sampled_rss_bytes"])

    def test_pending_leader_does_not_bypass_child_inventory_limit(self):
        result = supervise(OwnedLifecycle(children=b"202 203"))
        self.assert_failed(result, "more than its one scheduler-query descendant")
        self.assertFalse((result["terminal_resolution"] or {}).get("natural_exit_confirmed_before_cleanup", False))

    def test_native_worker_failure_is_not_relabelled_by_successful_accounting(self):
        result = supervise(OwnedLifecycle(worker_exit=3))
        self.assertEqual(result["exit_code"], 3)
        self.assertTrue(result["quiescent"])
        self.assertEqual(controller.classify_case(result, {"status": "resource_stop"}), "resource_stop")
        self.assertEqual(controller.classify_case(result, {"status": "unknown"}), "infrastructure_failure")

    def test_stat_flags_are_exact_unsigned_field_nine(self):
        value = controller.parse_proc_stat(stat(flags=4194308).decode(), LEADER)
        self.assertEqual(value["flags"], 4194308)
        self.assertEqual(value["start_ticks"], START)
        self.assertTrue(value["flags"] & controller.PF_EXITING)
        for flags in (-4, "wrong", 2**32):
            with self.subTest(flags=flags), self.assertRaisesRegex(ValueError, "Malformed owned-process flags"):
                controller.parse_proc_stat(stat(flags=flags).decode(), LEADER)

    def test_scope_keeps_cleanup_wnowait_caps_and_all_inference_code_unchanged(self):
        old = ast.parse(PREVIOUS.read_text())
        new = ast.parse((HERE / "paired_controller.py").read_text())
        functions = lambda tree: {node.name: ast.dump(node, include_attributes=False)
                                  for node in tree.body if isinstance(node, ast.FunctionDef)}
        before, after = functions(old), functions(new)
        self.assertEqual(set(before), set(after))
        self.assertEqual({name for name in before if before[name] != after[name]},
                         {"parse_proc_stat", "sample_leader", "sample_owned", "supervise_case"})
        strip = lambda tree: [ast.dump(node, include_attributes=False) for node in tree.body
                              if not isinstance(node, ast.FunctionDef)
                              and not (isinstance(node, ast.Assign)
                                       and any(isinstance(target, ast.Name) and target.id == "PF_EXITING"
                                               for target in node.targets))]
        self.assertEqual(strip(old), strip(new))
        for name in ("peek_owned_exit", "terminate_owned", "sample_scheduler_child", "reservation_spec",
                     "run", "selected_cases", "classify_case"):
            self.assertEqual(before[name], after[name], name)


if __name__ == "__main__":
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (20, 25))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(30)
    unittest.main(verbosity=2)
