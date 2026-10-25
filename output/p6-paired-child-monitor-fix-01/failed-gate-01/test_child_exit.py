"""Pure scripted /proc and virtual time; no actual process or backend is run."""
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
PREDECESSOR = HERE.parent / "p6-paired-leader-monitor-fix-02"
PREDECESSOR_SHA = "05100256d9e303810fbac78ef34e788377223225bcc6828bb0100564c6f36217"
assert sha256((PREDECESSOR / "paired_controller.py").read_bytes()).hexdigest() == PREDECESSOR_SHA


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Its imports are stdlib plus the frozen metadata-only paired_common module.
fixtures = load("unchanged_leader_fixtures", PREDECESSOR / "test_exit_resolution.py")
controller = load("child_exit_candidate", HERE / "paired_controller.py")
fixtures.controller = controller
fixtures.HERE = HERE  # Temporary fixture files remain in this new directory.
LEADER, UID, CHILD = fixtures.LEADER, fixtures.UID, 202
ARGV = b"\0".join([fixtures.SCONTROL.encode(), b"-o", b"show", b"job", fixtures.JOB.encode(), b""])


class ChildLifecycle(fixtures.OwnedLifecycle):
    def __init__(self, *, pending_at=0.1, zombie_at=0.3, reaped_at=0.4,
                 child_flags=4, mutate_at=0.2, changed=None, wrong_argv=False,
                 child_uid=None, child_rss_again=False, descendants=False,
                 status_extra=b"", status_state=None, regress_flags=False,
                 reappear=False, stale_inventory=False, parent_exit=0.6,
                 parent_missing=float("inf"), tick=True):
        super().__init__(exit_at=parent_exit, missing_at=parent_missing, tick=tick)
        self.pending_at, self.zombie_at, self.reaped_at = pending_at, zombie_at, reaped_at
        self.child_flags, self.mutate_at, self.changed_child = child_flags, mutate_at, changed or {}
        self.wrong_argv, self.child_uid, self.child_rss_again = wrong_argv, child_uid, child_rss_again
        self.descendants, self.status_extra, self.status_state = descendants, status_extra, status_state
        self.regress_flags, self.reappear, self.stale_inventory = regress_flags, reappear, stale_inventory

    def read(self, path, maximum):
        name = str(path)
        if name == "/proc/101/task/101/children":
            self.reads.append((self.now, name, maximum))
            assert maximum == 8192
            return b"202" if self.now < self.reaped_at or self.stale_inventory else b""
        if not name.startswith("/proc/202/"):
            return super().read(path, maximum)
        self.reads.append((self.now, name, maximum))
        assert self.returncode is None
        assert maximum == (8192 if path.name in {"stat", "children"} else 65536)
        if self.now >= self.reaped_at:
            if self.reappear and path.name == "stat":
                return fixtures.stat("R", pid=CHILD, ppid=LEADER, start=9877)
            raise FileNotFoundError("scripted owner-reaped child")
        changed = self.now >= self.mutate_at
        state = "Z" if self.now >= self.zombie_at else ("D" if self.now >= self.pending_at else "R")
        if path.name == "stat":
            values = {"pid": CHILD, "ppid": LEADER, "pgid": LEADER, "sid": LEADER, "start": 9876,
                      "flags": self.child_flags if self.now >= self.pending_at else 0}
            if changed:
                values.update(self.changed_child)
                if self.regress_flags:
                    values["flags"] = 0
            return fixtures.stat(state, **values)
        if path.name == "status":
            rss = 25 if self.now < self.pending_at else None
            if changed and self.child_rss_again:
                rss = 31
            uids = (UID,) * 4 if not changed or self.child_uid is None else self.child_uid
            observed_state = self.status_state if changed and self.status_state else state
            raw = fixtures.status(observed_state, uids=uids, rss=rss)
            return raw + (self.status_extra if changed else b"")
        if path.name == "cmdline":
            if changed and self.wrong_argv:
                return ARGV.replace(b"scontrol", b"othercmd")
            return ARGV if self.now < self.pending_at else b""
        if path.name == "children":
            return b"909" if changed and self.descendants else b""
        raise AssertionError("unexpected child read: " + name)


class ChildResolutionTests(unittest.TestCase):
    def failed(self, life, pattern, **kwargs):
        result = fixtures.supervise(life, **kwargs)
        self.assertRegex(result["termination_reason"], pattern)
        self.assertFalse(result["quiescent"])
        self.assertTrue(result["leader_reaped"])
        self.assertNotEqual(controller.classify_case(result, {"status": "proved", "replay": {"complete": True}}), "proved")
        self.assertTrue(all(episode["outcome"] == "failed"
                            for episode in (result["child_terminal_resolution"] or {}).get("episodes", [])))
        return result

    def test_recorded_d_d_shape_with_unknown_exiting_flag_still_fails(self):
        life = ChildLifecycle(pending_at=0, child_flags=0)
        result = self.failed(life, "without PF_EXITING")
        self.assertIsNone(result["child_terminal_resolution"])
        self.assertIsNone(result["terminal_resolution"])
        diagnostic = result["accounting_diagnostic"]
        self.assertEqual([v["state"] for v in diagnostic["stats"].values()], ["D", "D"])
        self.assertEqual(diagnostic["records"][0]["rss_fields"], 0)
        self.assertTrue(diagnostic["records"][0]["argv_empty"])
        self.assertTrue(diagnostic["records"][0]["uid_matches"])
        self.assertEqual(life.sleeps, [])

    def test_hypothetical_flagged_d_d_to_coherent_z_resumes(self):
        life = ChildLifecycle()
        result = fixtures.supervise(life)
        self.assertEqual((result["termination_reason"], result["exit_code"], result["quiescent"]),
                         ("process_exit", 0, True))
        resolution = result["child_terminal_resolution"]
        episode = resolution["episodes"][0]
        self.assertEqual((episode["outcome"], episode["terminal"]), ("natural_exit_confirmed", "zombie"))
        self.assertFalse(episode["missing_rss_was_zero_filled"])
        self.assertTrue(episode["natural_exit_confirmed_before_cleanup"])
        self.assertGreater(len(episode["samples"]), 2)
        self.assertTrue(all(int(f["child"]["stats"]["after"]["flags"]) & 4 for f in episode["samples"]))
        self.assertEqual(result["peak_sampled_host_rss_bytes"], 125 * 1024)
        self.assertLessEqual(resolution["resolution_and_cleanup_seconds"], 3)
        self.assertFalse(life.forced)
        self.assertIsNone(result["terminal_resolution"])
        self.assertLessEqual(len(controller.canonical(resolution)), 256 * 1024)

    def test_pending_rss_is_none_and_leader_is_still_measured(self):
        life = ChildLifecycle()
        samples = []
        def capture(value):
            samples.append(value)
            return value
        fixtures.supervise(life, sample_wrapper=capture)
        pending = [s for s in samples if s.get("child_exit_observation", {}).get("pending_exit")]
        self.assertTrue(pending)
        self.assertTrue(all(s["rss_bytes"] is None and s["known_rss_bytes"] == 100 * 1024 for s in pending))
        self.assertTrue(all(s["leader_accounting_diagnostic"]["records"][0]["rss_fields"] == 1 for s in pending))

    def test_hypothetical_disappearance_requires_two_absent_stats_and_inventory(self):
        result = fixtures.supervise(ChildLifecycle(zombie_at=1, reaped_at=0.25))
        episode = result["child_terminal_resolution"]["episodes"][0]
        self.assertEqual(result["exit_code"], 0)
        self.assertTrue(result["quiescent"])
        self.assertEqual(episode["terminal"], "disappeared")
        self.assertEqual(episode["samples"][-1]["child"]["absent_stat_reads"], 2)

    def test_disappearance_with_pid_reuse_or_stale_child_inventory_fails(self):
        for change in ({"reappear": True}, {"stale_inventory": True}):
            with self.subTest(change=change):
                self.failed(ChildLifecycle(zombie_at=1, reaped_at=0.25, **change),
                            "PID was reused|remains in owned child inventory")

    def test_wrong_uid_or_any_identity_field_never_becomes_exit_advice(self):
        for change in ({"pid": CHILD + 1}, {"ppid": LEADER + 1}, {"pgid": LEADER + 1},
                       {"sid": LEADER + 1}, {"start": 9877}):
            with self.subTest(change=change):
                self.failed(ChildLifecycle(changed=change), "Malformed|Unowned|identity changed")
        for index in range(4):
            uids = [UID] * 4
            uids[index] += 1
            with self.subTest(uid_field=index):
                self.failed(ChildLifecycle(child_uid=tuple(uids)), "uid changed")

    def test_wrong_argv_and_further_descendants_fail(self):
        self.failed(ChildLifecycle(wrong_argv=True), "undeclared executable")
        self.failed(ChildLifecycle(descendants=True), "further descendant")

    def test_missing_malformed_or_duplicate_uid_rss_and_state_fail(self):
        for extra in (b"Uid:\t404\t404\t404\t404\n", b"VmRSS:\tbad kB\n",
                      b"VmRSS:\t1 kB\nVmRSS:\t2 kB\n", b"State:\tD (fixture)\n"):
            with self.subTest(extra=extra):
                self.failed(ChildLifecycle(status_extra=extra), "Malformed|ambiguous")
        self.failed(ChildLifecycle(child_uid=(UID, UID)), "UID accounting")

    def test_resumed_rss_exiting_flag_and_terminal_state_regression_fail(self):
        self.failed(ChildLifecycle(child_rss_again=True), "resumed RSS")
        self.failed(ChildLifecycle(regress_flags=True), "flag regressed")
        self.failed(ChildLifecycle(status_state="D", mutate_at=0.3), "terminal state regressed")

    def test_unresolved_child_cannot_be_completed_by_cleanup_kill(self):
        result = self.failed(ChildLifecycle(zombie_at=4, reaped_at=4.1, parent_exit=5), "remained unproven")
        self.assertEqual(result["exit_code"], -signal.SIGKILL)
        resolution = result["child_terminal_resolution"]
        self.assertLessEqual(resolution["resolution_and_cleanup_seconds"], 3.000001)
        self.assertLessEqual(resolution["sample_count"], 61)
        self.assertFalse(resolution["episodes"][0]["natural_exit_confirmed_before_cleanup"])

    def test_pending_cancellation_remains_failure(self):
        life = ChildLifecycle(zombie_at=2, reaped_at=2.1, parent_exit=3)
        result = self.failed(life, "cancelled", should_stop=lambda: life.now >= 0.2)
        self.assertEqual(result["child_terminal_resolution"]["episodes"][0]["outcome"], "failed")

    def test_nonadvancing_clock_has_independent_sample_bound(self):
        result = self.failed(ChildLifecycle(pending_at=0, tick=False), "remained unproven")
        self.assertEqual(result["child_terminal_resolution"]["sample_count"], 61)

    def test_pending_child_cannot_extend_case_wall(self):
        result = self.failed(ChildLifecycle(pending_at=89, zombie_at=91, reaped_at=92, parent_exit=93),
                             "case_wall_limit")
        self.assertLessEqual(result["elapsed_seconds"], 90.000001)

    def test_known_memory_over_limit_is_enforced_while_child_rss_unknown(self):
        life = ChildLifecycle(pending_at=0)
        def excessive(value):
            return {**value, "known_rss_bytes": controller.RESOURCE_LIMITS["host_sampled_rss_bytes"] + 1}
        self.failed(life, "host_sampled_rss_limit", sample_wrapper=excessive)

    def test_child_and_later_leader_share_one_cleanup_time_and_sample_budget(self):
        life = ChildLifecycle(parent_missing=0.5, parent_exit=4)
        result = fixtures.supervise(life)
        self.assertFalse(result["quiescent"])
        self.assertRegex(result["termination_reason"], "remained unproven")
        child, leader = result["child_terminal_resolution"], result["terminal_resolution"]
        self.assertEqual(child["episodes"][0]["outcome"], "natural_exit_confirmed")
        self.assertEqual(leader["outcome"], "failed")
        self.assertLessEqual(child["sample_count"] + leader["sample_count"], 61)
        self.assertLessEqual(child["resolution_and_cleanup_seconds"], 3.000001)

    def test_overlapping_leader_exit_fails_without_waiving_pending_child(self):
        self.failed(ChildLifecycle(zombie_at=2, reaped_at=2.1, parent_missing=0.2, parent_exit=0.4), "Overlapping")
        self.failed(ChildLifecycle(zombie_at=2, reaped_at=2.1, parent_exit=0.2), "leader exited before")

    def test_scope_retains_leader_fix_cleanup_limits_and_all_work_selection(self):
        old = ast.parse((PREDECESSOR / "paired_controller.py").read_text())
        new = ast.parse((HERE / "paired_controller.py").read_text())
        functions = lambda tree: {n.name: ast.dump(n, include_attributes=False)
                                  for n in tree.body if isinstance(n, ast.FunctionDef)}
        before, after = functions(old), functions(new)
        self.assertEqual(set(after) - set(before), {"owned_child_ids"})
        self.assertEqual({name for name in before if before[name] != after[name]},
                         {"sample_scheduler_child", "sample_owned", "supervise_case"})
        nonfunctions = lambda tree: [ast.dump(n, include_attributes=False)
                                     for n in tree.body if not isinstance(n, ast.FunctionDef)]
        self.assertEqual(nonfunctions(old), nonfunctions(new))
        old_popen = [ast.dump(n, include_attributes=False) for n in ast.walk(old)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "Popen"]
        new_popen = [ast.dump(n, include_attributes=False) for n in ast.walk(new)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "Popen"]
        self.assertEqual(old_popen, new_popen)
        self.assertFalse(any(name in sys.modules for name in ("torch", "transformers", "peano_lab")))


def suite():
    result = unittest.defaultTestLoader.loadTestsFromTestCase(ChildResolutionTests)
    names = unittest.defaultTestLoader.getTestCaseNames(fixtures.TerminalResolutionTests)
    # The old scope test asserts the predecessor's intentionally different diff.
    # Every behavior fixture is reused; the new scope test above replaces it.
    result.addTests(fixtures.TerminalResolutionTests(name) for name in names
                    if name != "test_scope_keeps_cleanup_wnowait_caps_and_all_inference_code_unchanged")
    return result


if __name__ == "__main__":
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (20, 25))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(30)
    checked = unittest.TextTestRunner(verbosity=2).run(suite())
    record = {"schema": "hydra-child-exit-pure-fixtures-v1", "tests": checked.testsRun,
              "failures": len(checked.failures), "errors": len(checked.errors), "skipped": len(checked.skipped),
              "passed": checked.wasSuccessful(), "real_processes": 0, "real_linux_validation": False,
              "model_calls": 0, "native_calls": 0,
              "controller_sha256": sha256((HERE / "paired_controller.py").read_bytes()).hexdigest(),
              "test_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}
    print(json.dumps(record, sort_keys=True))
    raise SystemExit(0 if checked.wasSuccessful() else 1)
