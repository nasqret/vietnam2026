"""Scripted /proc and virtual time only; no real child or backend is run."""
import ast
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import signal
import sys
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
PREVIOUS = HERE.parent / "p6-paired-child-monitor-fix-01"
OLD_SHA = "cb5ba7840f85c00bf54953bddf5bb168414a0e6e84c9b41369da63b315e195be"
ACTUAL = PROJECT / "output/hydra-implementation-2026-09-04/paired-launchers-v11/prepared/arms/fresh_1_7b/observation-007/result/case-06/execution.json"
ACTUAL_SHA = "5e1021ef879805672baa3bdef79679f8ce8eee160a51353ebb9f662f904dd5c2"
assert sha256((PREVIOUS / "paired_controller.py").read_bytes()).hexdigest() == OLD_SHA


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


previous = load("previous_child_fixtures", PREVIOUS / "test_child_exit.py")
old_controller = previous.controller
controller = load("argv_exit_candidate", HERE / "paired_controller.py")
previous.controller = controller
previous.fixtures.controller = controller
previous.fixtures.HERE = HERE
fixtures = previous.fixtures
LEADER, UID, CHILD = previous.LEADER, previous.UID, previous.CHILD
BASE_FLAGS, EXIT_FLAGS = 4194304, 4194316


def child_stat(state="R", flags=EXIT_FLAGS, **changes):
    fields = dict(pid=CHILD, ppid=LEADER, pgid=LEADER, sid=LEADER, start=9876, flags=flags)
    fields.update(changes)
    return fixtures.stat(state, **fields)


def sample(*, module=controller, before=None, after=None, status=None, argv=b"",
           children=b"", pending=None, terminal=False, disappear=False):
    if disappear:
        scripts = {"stat": [FileNotFoundError("gone"), FileNotFoundError("still gone")]}
    else:
        scripts = {
            "stat": [child_stat(flags=BASE_FLAGS) if before is None else before,
                     child_stat() if after is None else after],
            "status": [fixtures.status("R", rss=25) if status is None else status],
            "cmdline": [argv], "children": [children],
        }
        if terminal:
            scripts["stat"].append(child_stat("Z"))
            scripts["status"].append(fixtures.status("Z"))
            scripts["cmdline"].append(b"")
            scripts["children"].append(b"")
    def read(path, maximum):
        assert str(path).startswith("/proc/202/")
        assert maximum == (8192 if path.name in {"stat", "children"} else 65536)
        value = scripts[path.name].pop(0)
        if isinstance(value, BaseException):
            raise value
        return value
    with mock.patch.object(module, "proc_read", side_effect=read), \
         mock.patch.object(module.os, "getuid", return_value=UID), \
         mock.patch.object(module.os, "waitid", side_effect=AssertionError("never wait a grandchild"), create=True):
        return module.sample_scheduler_child(CHILD, LEADER, fixtures.JOB, fixtures.SCONTROL, pending)


class ArgvLifecycle(previous.ChildLifecycle):
    """The actual read order, followed by hypothetical bounded outcomes."""
    def __init__(self, *, rss_missing_at=0.2, **kwargs):
        super().__init__(**kwargs)
        self.rss_missing_at = rss_missing_at
        self.exiting_stat_reads = 0

    def read(self, path, maximum):
        raw = super().read(path, maximum)
        if not str(path).startswith("/proc/202/") or self.now < self.pending_at:
            return raw
        if path.name == "stat":
            prefix, tail = raw.decode().rsplit(") ", 1)
            fields = tail.split()
            if fields[0] == "D":
                fields[0] = "R"
            fields[6] = str(BASE_FLAGS if self.exiting_stat_reads == 0 else EXIT_FLAGS)
            self.exiting_stat_reads += 1
            return (prefix + ") " + " ".join(fields) + "\n").encode()
        if path.name == "status":
            raw = raw.replace(b"State:\tD ", b"State:\tR ")
            if self.now < min(self.rss_missing_at, self.zombie_at) and b"VmRSS:" not in raw:
                raw += b"VmRSS:\t25 kB\n"
        return raw


class ArgvExitTests(unittest.TestCase):
    def failed(self, life, pattern, **kwargs):
        result = fixtures.supervise(life, **kwargs)
        self.assertRegex(result["termination_reason"], pattern)
        self.assertFalse(result["quiescent"])
        self.assertTrue(result["leader_reaped"])
        self.assertNotEqual(controller.classify_case(result, {"status": "proved"}), "proved")
        return result

    def test_recorded_transition_previously_fails_now_stays_pending_with_known_rss(self):
        raw = ACTUAL.read_bytes()
        self.assertEqual(sha256(raw).hexdigest(), ACTUAL_SHA)
        actual = json.loads(raw)
        diagnostic = actual["accounting_diagnostic"]
        self.assertEqual(diagnostic["pid"], "930392")
        self.assertEqual([int(diagnostic["stats"][key]["flags"]) for key in ("before", "after")],
                         [BASE_FLAGS, EXIT_FLAGS])
        self.assertEqual({value["start_ticks"] for value in diagnostic["stats"].values()}, {"3746494"})
        observed = diagnostic["records"][0]
        self.assertEqual((observed["state"], observed["rss_fields"], observed["valid_rss_fields"],
                          observed["argv_empty"], observed["uid_matches"]), ("R", 1, 1, True, True))
        self.assertIsNone(actual["child_terminal_resolution"])
        self.assertEqual(actual["exit_code"], -9)
        with self.assertRaisesRegex(ValueError, "command line is unavailable"):
            sample(module=old_controller)
        result = sample()
        self.assertTrue(result["pending_exit"])
        self.assertIsNone(result["rss_bytes"])
        self.assertIsNone(result["terminal"])
        self.assertEqual(result["known_rss_bytes"], 25 * 1024)
        self.assertFalse(result["rss_absence_observed"])

    def test_valid_rss_can_remain_pending_then_naturally_reach_z_or_disappear(self):
        first = sample()
        second = sample(before=child_stat(), pending=first)
        self.assertTrue(second["pending_exit"])
        self.assertFalse(second["rss_absence_observed"])
        terminal = sample(before=child_stat(), after=child_stat("Z"),
                          status=fixtures.status("R"), pending=second, terminal=True)
        self.assertEqual((terminal["pending_exit"], terminal["terminal"]), (False, "zombie"))
        self.assertTrue(terminal["rss_absence_observed"])
        self.assertEqual(terminal["known_rss_bytes"], 25 * 1024)
        gone = sample(pending=second, disappear=True)
        self.assertEqual(gone["terminal"], "disappeared")
        self.assertEqual(gone["diagnostic"]["absent_stat_reads"], 2)

    def test_actual_read_shape_uses_unchanged_supervisor_until_natural_exit(self):
        captured = []
        def capture(value):
            captured.append(value)
            return value
        result = fixtures.supervise(ArgvLifecycle(), sample_wrapper=capture)
        self.assertEqual((result["termination_reason"], result["exit_code"], result["quiescent"]),
                         ("process_exit", 0, True))
        pending = [row for row in captured if row.get("child_exit_observation", {}).get("pending_exit")]
        self.assertTrue(any(not row["child_exit_observation"]["rss_absence_observed"] for row in pending))
        self.assertTrue(any(row["child_exit_observation"]["rss_absence_observed"] for row in pending))
        self.assertTrue(all(row["rss_bytes"] is None and row["known_rss_bytes"] == 125 * 1024 for row in pending))
        episode = result["child_terminal_resolution"]["episodes"][0]
        self.assertEqual(episode["outcome"], "natural_exit_confirmed")
        self.assertFalse(episode["missing_rss_was_zero_filled"])
        self.assertLessEqual(result["child_terminal_resolution"]["resolution_and_cleanup_seconds"], 3)
        self.assertEqual(result["peak_sampled_host_rss_bytes"], 125 * 1024)

    def test_wrong_identity_and_each_uid_field_fail_before_pending(self):
        for change in ({"pid": CHILD + 1}, {"ppid": LEADER + 1}, {"pgid": LEADER + 1},
                       {"sid": LEADER + 1}, {"start": 9877}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "Malformed|Unowned|identity changed"):
                sample(after=child_stat(**change))
        for index in range(4):
            uids = [UID] * 4
            uids[index] += 1
            with self.subTest(uid=index), self.assertRaisesRegex(ValueError, "uid changed"):
                sample(status=fixtures.status("R", rss=25, uids=tuple(uids)))

    def test_nonempty_wrong_argv_missing_command_or_missing_flag_never_admits(self):
        with self.assertRaisesRegex(ValueError, "undeclared executable"):
            sample(argv=previous.ARGV.replace(b"scontrol", b"othercmd"))
        with self.assertRaisesRegex(ValueError, "command line is unavailable"):
            sample(argv=FileNotFoundError("cmdline disappeared alone"))
        with self.assertRaisesRegex(ValueError, "command line is unavailable"):
            sample(after=child_stat(flags=BASE_FLAGS))
        with self.assertRaisesRegex(ValueError, "further descendant"):
            sample(children=b"909")

    def test_exiting_flag_regression_and_matching_argv_resumption_fail(self):
        with self.assertRaisesRegex(ValueError, "flag regressed"):
            sample(before=child_stat(), after=child_stat(flags=BASE_FLAGS))
        pending = sample()
        with self.assertRaisesRegex(ValueError, "flag regressed"):
            sample(before=child_stat(flags=BASE_FLAGS), pending=pending)
        with self.assertRaisesRegex(ValueError, "command line is unavailable"):
            sample(before=child_stat(), argv=previous.ARGV, pending=pending)

    def test_rss_must_never_resume_after_absence_even_before_later_disappearance(self):
        pending = sample()
        missing = sample(before=child_stat(), status=fixtures.status("R"), pending=pending)
        self.assertTrue(missing["rss_absence_observed"])
        with self.assertRaisesRegex(ValueError, "resumed RSS"):
            sample(before=child_stat(), pending=missing)
        with self.assertRaisesRegex(ValueError, "resumed RSS"):
            sample(before=child_stat(), after=FileNotFoundError("too late to waive observed RSS"), pending=missing)

    def test_pending_child_overlap_still_fails(self):
        self.failed(ArgvLifecycle(zombie_at=2, reaped_at=2.1, parent_missing=0.2, parent_exit=0.4), "Overlapping")
        self.failed(ArgvLifecycle(zombie_at=2, reaped_at=2.1, parent_exit=0.2), "leader exited before")

    def test_new_pending_path_retains_cancel_wall_memory_and_cleanup_sample_caps(self):
        life = ArgvLifecycle(zombie_at=2, reaped_at=2.1, parent_exit=3)
        self.failed(life, "cancelled", should_stop=lambda: life.now >= 0.15)
        self.failed(ArgvLifecycle(pending_at=89, rss_missing_at=92, zombie_at=91, reaped_at=92, parent_exit=93),
                    "case_wall_limit")
        life = ArgvLifecycle(pending_at=0)
        self.failed(life, "host_sampled_rss_limit", sample_wrapper=lambda row: {
            **row, "known_rss_bytes": controller.RESOURCE_LIMITS["host_sampled_rss_bytes"] + 1})
        result = self.failed(ArgvLifecycle(pending_at=0, rss_missing_at=5, zombie_at=6,
                             reaped_at=7, parent_exit=8, tick=False), "remained unproven")
        resolution = result["child_terminal_resolution"]
        self.assertLessEqual(resolution["sample_count"], 61)
        self.assertLessEqual(resolution["resolution_and_cleanup_seconds"], 3.000001)
        self.assertLessEqual(len(controller.canonical(resolution)), 256 * 1024)

    def test_scope_only_changes_child_sampler_preserving_all_other_code_and_limits(self):
        before = ast.parse((PREVIOUS / "paired_controller.py").read_text())
        after = ast.parse((HERE / "paired_controller.py").read_text())
        functions = lambda tree: {n.name: ast.dump(n, include_attributes=False)
                                 for n in tree.body if isinstance(n, ast.FunctionDef)}
        old, new = functions(before), functions(after)
        self.assertEqual(old.keys(), new.keys())
        self.assertEqual({name for name in old if old[name] != new[name]}, {"sample_scheduler_child"})
        other = lambda tree: [ast.dump(n, include_attributes=False) for n in tree.body
                              if not isinstance(n, ast.FunctionDef)]
        self.assertEqual(other(before), other(after))
        self.assertEqual(sha256((PREVIOUS / "paired_controller.py").read_bytes()).hexdigest(), OLD_SHA)
        self.assertFalse(any(name in sys.modules for name in ("torch", "transformers", "peano_lab")))


def suite():
    result = unittest.defaultTestLoader.loadTestsFromTestCase(ArgvExitTests)
    # Only the affected child API needs its original behavior regressions here.
    # Its old scope assertion describes a different predecessor, so replace it.
    result.addTests(previous.ChildResolutionTests(name)
                    for name in unittest.defaultTestLoader.getTestCaseNames(previous.ChildResolutionTests)
                    if name != "test_scope_retains_leader_fix_cleanup_limits_and_all_work_selection")
    return result


if __name__ == "__main__":
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (10, 15))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(20)
    result = unittest.TextTestRunner(verbosity=2).run(suite())
    print(json.dumps({"schema": "hydra-child-argv-exit-pure-fixtures-v1", "tests": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
        "passed": result.wasSuccessful(), "new_path_tests": 10, "unchanged_child_behavior_tests": 19,
        "real_processes": 0, "real_linux_validation": False, "model_calls": 0, "native_calls": 0,
        "controller_sha256": sha256((HERE / "paired_controller.py").read_bytes()).hexdigest(),
        "test_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "actual_failure_sha256": ACTUAL_SHA}, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
