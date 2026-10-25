"""Pure scripted /proc fixtures; no real subprocess, native code or model."""
import ast
from collections import deque
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
ORIGINAL = PROJECT / "output/hydra-implementation-2026-09-04/combined-source-bundle-03/source/output/hydra-implementation-2026-09-04/paired-evaluation-v2"
ORIGINAL_SHA = "84e78193613505cab6d8d139720a5bb1b0f460db09aec3b0456fbabe4cd76e94"
assert sha256((ORIGINAL / "paired_controller.py").read_bytes()).hexdigest() == ORIGINAL_SHA
sys.path.insert(0, str(ORIGINAL))  # paired_common defines metadata functions; no runtime import.


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


controller = load("candidate_leader_controller", HERE / "paired_controller.py")
predecessor = load("previous_leader_controller", ORIGINAL / "paired_controller.py")
LEADER, PARENT, UID, START = 101, 303, 404, 1234
PROCESS = SimpleNamespace(pid=LEADER, returncode=None)
JOB, SCONTROL = "21979201", "/fixed/bin/scontrol"


def stat(state="R", *, pid=LEADER, ppid=PARENT, pgid=LEADER, sid=LEADER, start=START):
    tail = ["0"] * 22
    tail[0], tail[1], tail[2], tail[3], tail[19] = state, str(ppid), str(pgid), str(sid), str(start)
    return (str(pid) + " (worker) " + " ".join(tail) + "\n").encode()


def status(state="R", *, uids=(UID,) * 4, rss=100):
    text = "Name:\tworker\nState:\t" + state + " (fixture)\nUid:\t" + "\t".join(map(str, uids)) + "\n"
    if rss is not None:
        text += "VmRSS:\t" + str(rss) + " kB\n"
    return text.encode()


class ScriptedProc:
    def __init__(self, stats, statuses, extra=None):
        root = "/proc/" + str(LEADER)
        self.values = {root + "/stat": deque(stats), root + "/status": deque(statuses)}
        self.values.update({name: deque(values) for name, values in (extra or {}).items()})
        self.reads = []

    def __call__(self, path, maximum):
        key = str(path)
        bound = 8192 if path.name in {"stat", "children"} else 65536
        assert maximum == bound, (key, maximum, bound)
        assert key in self.values and self.values[key], "Unexpected extra read: " + key
        self.reads.append((key, maximum))
        value = self.values[key].popleft()
        if isinstance(value, Exception):
            raise value
        return value


def live(**overrides):
    values = {"stats": [stat(), stat()], "statuses": [status()]}
    values.update(overrides)
    return ScriptedProc(**values)


def exiting(**overrides):
    values = {"stats": [stat(), stat("Z"), stat("Z")],
              "statuses": [status("Z", rss=None), status("Z", rss=None)]}
    values.update(overrides)
    return ScriptedProc(**values)


class LeaderAccountingTests(unittest.TestCase):
    def sample(self, script, peeks=(), *, process=PROCESS, initial_start=START, owned=False):
        with mock.patch.object(controller, "proc_read", script), \
             mock.patch.object(controller.os, "getuid", return_value=UID), \
             mock.patch.object(controller.os, "getpid", return_value=PARENT), \
             mock.patch.object(controller, "peek_owned_exit", side_effect=list(peeks)) as peek:
            if owned:
                result = controller.sample_owned(process, JOB, SCONTROL, initial_start)
            else:
                result = controller.sample_leader(process, initial_start)
        return result, peek.call_count

    def rejected(self, script, message, peeks=(), **kwargs):
        with self.assertRaisesRegex((OSError, ValueError), message) as caught:
            self.sample(script, peeks, **kwargs)
        self.assertTrue(caught.exception.leader_accounting_violation)
        diagnostic = caught.exception.accounting_diagnostic
        encoded = json.dumps(diagnostic, sort_keys=True).encode()
        self.assertLessEqual(len(encoded), 3072)
        self.assertNotIn(b"/proc/", encoded)
        self.assertNotIn(SCONTROL.encode(), encoded)
        self.assertLessEqual(len(script.reads), 5)
        self.assertLessEqual(len(diagnostic["exit_observations"]), 2)
        return diagnostic

    def test_live_leader_keeps_exact_rss_with_three_bounded_reads(self):
        script = live()
        result, peeks = self.sample(script)
        self.assertEqual(result["rss_bytes"], 100 * 1024)
        self.assertFalse(result["exited"])
        self.assertEqual(result["info"]["start_ticks"], START)
        self.assertEqual((len(script.reads), peeks), (3, 0))

    def test_predecessor_rejects_stale_state_but_candidate_confirms_exit(self):
        # This is a scripted lifecycle race, not a claim to reproduce Linux.
        previous = exiting()
        with mock.patch.object(predecessor, "proc_read", previous), \
             mock.patch.object(predecessor.os, "getuid", return_value=UID), \
             mock.patch.object(predecessor.os, "getpid", return_value=PARENT):
            with self.assertRaisesRegex(ValueError, "Missing or ambiguous live RSS/ownership"):
                predecessor.sample_owned(PROCESS, JOB, SCONTROL, START)
        script = exiting()
        result, peeks = self.sample(script, [False, True], owned=True)
        self.assertEqual(result, {"rss_bytes": 0, "start_ticks": START,
                                  "descendants": [], "leader_exit_confirmed": True})
        self.assertEqual((len(script.reads), peeks), (5, 2))

    def test_nonwaitable_teardown_must_become_confirmed_terminal(self):
        script = exiting(stats=[stat(), stat(), stat("Z")],
                         statuses=[status(rss=None), status("Z", rss=None)])
        result, peeks = self.sample(script, [False, True])
        self.assertTrue(result["exited"])
        self.assertEqual((len(script.reads), peeks), (5, 2))

    def test_terminal_confirmation_preserves_largest_observed_rss(self):
        for first, final in ((131, None), (31, 151)):
            with self.subTest(first=first, final=final):
                script = exiting(statuses=[status(rss=first), status("Z", rss=final)])
                result, _ = self.sample(script, [False, True])
                self.assertEqual(result["rss_bytes"], max(first, final or 0) * 1024)

    def test_live_missing_rss_remains_a_bounded_failure(self):
        script = live(stats=[stat(), stat(), stat()], statuses=[status(rss=None), status(rss=None)])
        diagnostic = self.rejected(script, "Missing live RSS or unproven", [False, False])
        self.assertEqual(diagnostic["stats"]["terminal"]["state"], "R")
        self.assertEqual(diagnostic["records"][0]["rss_fields"], 0)
        self.assertTrue(diagnostic["records"][0]["uid_matches"])
        self.assertEqual(diagnostic["exit_observations"], [False, False])

    def test_zombie_without_waitable_exit_is_not_zero_live_accounting(self):
        self.rejected(exiting(), "Missing live RSS or unproven", [False, False])

    def test_exit_observation_alone_cannot_replace_terminal_identity(self):
        script = live(stats=[stat(), stat(), stat()], statuses=[status(rss=None), status(rss=None)])
        self.rejected(script, "Missing live RSS or unproven", [True, True])

    def test_missing_malformed_or_duplicate_uid_is_never_waived(self):
        invalid = [status().replace(b"Uid:", b"Other:"),
                   status().replace(b"404\t404\t404\t404", b"404"),
                   status() + b"Uid:\t404\t404\t404\t404\n"]
        for raw in invalid:
            with self.subTest(raw=raw):
                self.rejected(live(statuses=[raw]), "UID accounting")
                self.rejected(exiting(statuses=[status("Z", rss=None), raw]),
                              "UID accounting", [True])

    def test_each_uid_field_must_preserve_ownership(self):
        for index in range(4):
            uids = [UID] * 4
            uids[index] += 1
            with self.subTest(field=index):
                self.rejected(live(statuses=[status(uids=uids)]), "uid changed")
                self.rejected(exiting(statuses=[status("Z", rss=None), status("Z", uids=uids, rss=None)]),
                              "uid changed", [True])

    def test_malformed_or_duplicate_rss_is_not_terminal_absence(self):
        invalid = [status().replace(b"100 kB", b"bad kB"),
                   status() + b"VmRSS:\t5 kB\n", status().replace(b"100 kB", b"100 MB")]
        for raw in invalid:
            with self.subTest(raw=raw):
                self.rejected(live(statuses=[raw]), "Malformed or ambiguous.*RSS")
                self.rejected(exiting(statuses=[status("Z", rss=None), raw]),
                              "Malformed or ambiguous.*RSS", [True])

    def test_pid_parent_group_session_and_start_cannot_change(self):
        for change in ({"pid": LEADER + 1}, {"ppid": PARENT + 1}, {"pgid": LEADER + 1},
                       {"sid": LEADER + 1}, {"start": START + 1}):
            with self.subTest(change=change):
                self.rejected(live(stats=[stat(), stat(**change)]), "Malformed|owned session|identity changed")
                self.rejected(exiting(stats=[stat(), stat("Z"), stat("Z", **change)]),
                              "Malformed|owned session|identity changed", [True])
        self.rejected(live(), "identity changed", initial_start=START + 1)

    def test_status_state_is_required_and_cannot_regress_from_zombie(self):
        for raw in (status() + b"State:\tZ (zombie)\n", status().replace(b"State:", b"Other:"),
                    status().replace(b"State:\tR", b"State:\t?")):
            with self.subTest(raw=raw):
                self.rejected(live(statuses=[raw]), "status state")
        self.rejected(exiting(stats=[stat(), stat(), stat("Z")]), "terminal state regressed")
        self.rejected(exiting(statuses=[status("Z", rss=None), status()]), "terminal state regressed", [True])

    def test_disappeared_or_malformed_proc_is_not_an_exit_exemption(self):
        self.rejected(live(stats=[FileNotFoundError("stat missing")]), "stat missing")
        self.rejected(live(statuses=[FileNotFoundError("status missing")]), "status missing")
        self.rejected(exiting(stats=[stat(), stat("Z"), FileNotFoundError("final stat missing")]),
                      "final stat missing", [True])
        self.rejected(live(stats=[b"wrong process bytes"]), "Malformed owned-process stat")

    def test_reaped_leader_is_rejected_before_any_proc_read(self):
        script = live()
        self.rejected(script, "reaped before accounting", process=SimpleNamespace(pid=LEADER, returncode=3))
        self.assertEqual(script.reads, [])

    def test_live_thread_children_remain_accounted_and_multiple_children_rejected(self):
        tasks = [Path("/proc/101/task/101"), Path("/proc/101/task/102")]
        extra = {str(tasks[0] / "children"): [b""], str(tasks[1] / "children"): [b"202 203"]}
        with mock.patch.object(Path, "iterdir", return_value=iter(tasks)):
            with self.assertRaisesRegex(ValueError, "more than its one scheduler-query descendant"):
                self.sample(live(extra=extra), owned=True)


class IntegrationAndScopeTests(unittest.TestCase):
    def supervise(self, *, sample=None, error=None):
        captured = {}
        with TemporaryDirectory(prefix="pure-supervise-", dir=HERE) as temporary:
            app = Path(temporary) / "app"
            app.mkdir()
            directory = Path(temporary) / "case"
            directory.mkdir()
            request = directory / "case-request.json"
            request.write_text("{}")

            def cleanup(process, *, accounting_ok):
                self.assertIs(process, PROCESS)
                captured["accounting_ok"] = accounting_ok
                return {"exit_code": 3, "quiescent": accounting_ok, "leader_reaped": True,
                        "cleanup_error": None if accounting_ok else "live_process_accounting_was_incomplete"}

            with mock.patch.object(controller.subprocess, "Popen", return_value=PROCESS) as popen, \
                 mock.patch.object(controller.shutil, "which", return_value=SCONTROL), \
                 mock.patch.object(controller, "environment", return_value={}), \
                 mock.patch.object(controller.os, "getpgid", return_value=LEADER), \
                 mock.patch.object(controller, "peek_owned_exit", side_effect=[False, True]) as peek, \
                 mock.patch.object(controller, "sample_owned", return_value=sample, side_effect=error), \
                 mock.patch.object(controller, "terminate_owned", side_effect=cleanup), \
                 mock.patch.object(controller.time, "monotonic", return_value=1), \
                 mock.patch.object(controller.time, "sleep") as sleep, \
                 mock.patch.object(controller, "save"):
                result = controller.supervise_case(app, request, "a" * 64, {"job_id": JOB}, "fixed-wall-30-v1")
            self.assertEqual(popen.call_count, 1)  # Mocked; no process was created.
            self.assertEqual(sleep.call_count, 0)
        return result, captured, peek.call_count

    def test_later_exit_does_not_erase_leader_accounting_violation(self):
        error = ValueError("Owned process uid changed.")
        error.leader_accounting_violation = True
        error.accounting_diagnostic = {"schema": "hydra-paired-leader-accounting-v1", "pid": "101"}
        result, captured, peeks = self.supervise(error=error)
        self.assertFalse(captured["accounting_ok"])
        self.assertFalse(result["quiescent"])
        self.assertEqual(result["accounting_diagnostic"], error.accounting_diagnostic)
        self.assertIn("owned_process_accounting_error", result["termination_reason"])
        self.assertEqual(peeks, 1)  # No blanket terminal waiver for the proven violation.

    def test_confirmed_terminal_sample_keeps_worker_exit_and_accounting(self):
        sample = {"rss_bytes": 123456, "start_ticks": START, "descendants": [], "leader_exit_confirmed": True}
        result, captured, peeks = self.supervise(sample=sample)
        self.assertTrue(captured["accounting_ok"])
        self.assertTrue(result["quiescent"])
        self.assertEqual(result["exit_code"], 3)  # Accounting never relabels a worker failure as success.
        self.assertEqual(result["termination_reason"], "process_exit")
        self.assertEqual(result["peak_sampled_host_rss_bytes"], 123456)
        self.assertEqual((result["rss_samples"], peeks), (1, 1))

    def test_confirmed_exit_does_not_waive_sampled_memory_ceiling(self):
        sample = {"rss_bytes": controller.RESOURCE_LIMITS["host_sampled_rss_bytes"] + 1,
                  "start_ticks": START, "descendants": [], "leader_exit_confirmed": True}
        result, _, _ = self.supervise(sample=sample)
        self.assertEqual(result["termination_reason"], "host_sampled_rss_limit")

    def test_only_leader_sampling_and_its_caller_changed(self):
        old = ast.parse((ORIGINAL / "paired_controller.py").read_text())
        new = ast.parse((HERE / "paired_controller.py").read_text())
        old_functions = {node.name: ast.dump(node, include_attributes=False)
                         for node in old.body if isinstance(node, ast.FunctionDef)}
        new_functions = {node.name: ast.dump(node, include_attributes=False)
                         for node in new.body if isinstance(node, ast.FunctionDef)}
        self.assertEqual(set(new_functions) - set(old_functions), {"sample_leader"})
        self.assertEqual({name for name in old_functions if old_functions[name] != new_functions[name]},
                         {"sample_owned", "supervise_case"})
        self.assertEqual([ast.dump(node, include_attributes=False) for node in old.body if not isinstance(node, ast.FunctionDef)],
                         [ast.dump(node, include_attributes=False) for node in new.body if not isinstance(node, ast.FunctionDef)])
        # In particular all wall/CPU/memory imports, scheduler-child checks,
        # WNOWAIT implementation, kill-before-wait cleanup and classification are unchanged.
        for name in ("sample_scheduler_child", "peek_owned_exit", "terminate_owned", "classify_case",
                     "reservation_spec", "run", "selected_cases"):
            self.assertEqual(old_functions[name], new_functions[name], name)


if __name__ == "__main__":
    unittest.main()
