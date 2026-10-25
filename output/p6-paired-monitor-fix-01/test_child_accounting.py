"""Pure scripted /proc reads, never real processes, scheduler, native or models."""
from collections import deque
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
ORIGINAL = PROJECT / "output/hydra-implementation-2026-09-04/combined-source-bundle-02/source/output/hydra-implementation-2026-09-04/paired-evaluation-v2"
ORIGINAL_SHA = "fc60ec1eb71747c22052c7f433a3c87492dde41b217224bf848d32c35e106e28"
assert sha256((ORIGINAL / "paired_controller.py").read_bytes()).hexdigest() == ORIGINAL_SHA
sys.path.insert(0, str(ORIGINAL))  # Its common module imports no runtime backend.


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


controller = load("corrected_paired_controller", HERE / "paired_controller.py")
predecessor = load("original_paired_controller", ORIGINAL / "paired_controller.py")
LEADER, CHILD, PARENT, UID = 101, 202, 303, 404
JOB, SCONTROL = "21965180", "/fixed/bin/scontrol"
# Join fields so the job delimiter cannot become an octal escape.
ARGV = b"\0".join([SCONTROL.encode(), b"-o", b"show", b"job", JOB.encode(), b""])


def stat(state="R", *, pid=CHILD, ppid=LEADER, pgid=LEADER, sid=LEADER, start=9876):
    tail = ["0"] * 22
    tail[0], tail[1], tail[2], tail[3], tail[19] = state, str(ppid), str(pgid), str(sid), str(start)
    return (str(pid) + " (scheduler) " + " ".join(tail) + "\n").encode()


def status(state="R", *, uid=UID, rss=25):
    text = "Name:\tscheduler\nState:\t" + state + " (fixture)\nUid:\t" + "\t".join([str(uid)] * 4) + "\n"
    if rss is not None:
        text += "VmRSS:\t" + str(rss) + " kB\n"
    return text.encode()


class ScriptedProc:
    def __init__(self, stats, statuses, argv, children, *, leader=False):
        root = "/proc/" + str(CHILD)
        self.values = {
            root + "/stat": deque(stats), root + "/status": deque(statuses),
            root + "/cmdline": deque(argv), root + "/task/" + str(CHILD) + "/children": deque(children),
        }
        if leader:
            prefix = "/proc/" + str(LEADER)
            self.values.update({
                prefix + "/stat": deque([stat(pid=LEADER, ppid=PARENT, start=1234)]),
                prefix + "/status": deque([status(rss=100)]),
                prefix + "/task/" + str(LEADER) + "/children": deque([str(CHILD).encode()]),
            })
        self.reads = []

    def __call__(self, path, maximum):
        key = str(path)
        expected_bound = 8192 if path.name in {"stat", "children"} else 65536
        assert maximum == expected_bound, (key, maximum, expected_bound)
        self.reads.append((key, maximum))
        assert key in self.values and self.values[key], "Unexpected extra read: " + key
        value = self.values[key].popleft()
        if isinstance(value, Exception):
            raise value
        return value


def live(**overrides):
    values = {"stats": [stat(), stat()], "statuses": [status()], "argv": [ARGV], "children": [b""]}
    values.update(overrides)
    return ScriptedProc(**values)


def exits(**overrides):
    values = {"stats": [stat(), stat("Z"), stat("Z")],
              "statuses": [status("Z", rss=None), status("Z", rss=None)],
              "argv": [b"", b""], "children": [b"", b""]}
    values.update(overrides)
    return ScriptedProc(**values)


class ChildAccountingTests(unittest.TestCase):
    def sample(self, script):
        with mock.patch.object(controller, "proc_read", script), mock.patch.object(controller.os, "getuid", return_value=UID):
            return controller.sample_scheduler_child(CHILD, LEADER, JOB, SCONTROL)

    def rejected(self, script, message):
        with self.assertRaisesRegex(ValueError, message) as caught:
            self.sample(script)
        diagnostic = caught.exception.accounting_diagnostic
        encoded = json.dumps(diagnostic, sort_keys=True).encode()
        self.assertLessEqual(len(encoded), 2048)
        self.assertNotIn(SCONTROL.encode(), encoded)
        self.assertLessEqual(len(script.reads), 9)
        return diagnostic

    def test_live_child_keeps_exact_rss_and_bounds(self):
        script = live()
        self.assertEqual(self.sample(script), 25 * 1024)
        self.assertEqual(len(script.reads), 5)

    def test_live_to_zombie_before_status_is_confirmed_once(self):
        script = exits()
        self.assertEqual(self.sample(script), 0)
        self.assertEqual(len(script.reads), 9)

    def test_partial_live_status_requires_confirmed_terminal_identity(self):
        # State may be observed before the mm/RSS fields disappear. The first
        # missing RSS is not accepted unless the same child is then confirmed Z.
        script = exits(statuses=[status("R", rss=None), status("Z", rss=None)])
        self.assertEqual(self.sample(script), 0)
        self.rejected(live(statuses=[status("R", rss=None)]), "Missing or ambiguous live RSS")

    def test_exit_between_status_and_cmdline_preserves_observed_rss(self):
        script = exits(statuses=[status("R", rss=31), status("Z", rss=None)])
        self.assertEqual(self.sample(script), 31 * 1024)

    def test_missing_task_children_needs_same_terminal_identity(self):
        script = exits(children=[FileNotFoundError("exit"), FileNotFoundError("exit")])
        self.assertEqual(self.sample(script), 0)
        self.rejected(live(children=[FileNotFoundError("missing")]), "Live scheduler-query descendant")

    def test_missing_or_empty_cmdline_needs_same_terminal_identity(self):
        for value in (b"", FileNotFoundError("missing")):
            with self.subTest(value=type(value).__name__):
                self.rejected(live(argv=[value]), "Live scheduler-query command line")
        self.assertEqual(self.sample(exits(argv=[FileNotFoundError("exit"), FileNotFoundError("exit")])), 0)

    def test_live_missing_status_is_not_zero_accounting(self):
        diagnostic = self.rejected(live(statuses=[FileNotFoundError("missing")]), "Missing or ambiguous live RSS")
        self.assertIsNone(diagnostic["records"][0]["status_bytes"])
        self.assertEqual(diagnostic["stats"]["after"]["state"], "R")

    def test_unambiguous_gone_stat_is_ignored_as_before(self):
        self.assertIsNone(self.sample(live(stats=[FileNotFoundError("gone")])) )
        self.assertIsNone(self.sample(live(stats=[stat(), FileNotFoundError("reaped")])) )

    def test_duplicate_uid_or_rss_is_never_a_terminal_exemption(self):
        for extra in (b"Uid:\t404\t404\t404\t404\n", b"VmRSS:\t4 kB\n"):
            with self.subTest(extra=extra.split(b":")[0]):
                self.rejected(exits(statuses=[status(rss=25) + extra]), "Missing or ambiguous live RSS/ownership")

    def test_changed_uid_initial_or_terminal_is_rejected(self):
        self.rejected(live(statuses=[status(uid=UID + 1)]), "uid changed")
        self.rejected(exits(statuses=[status("Z", rss=None), status("Z", uid=UID + 1, rss=None)]), "uid changed")

    def test_changed_pid_parent_group_session_or_start_is_rejected(self):
        for changed in ({"pid": CHILD + 1}, {"ppid": LEADER + 1}, {"pgid": LEADER + 1},
                        {"sid": LEADER + 1}, {"start": 9877}):
            with self.subTest(changed=changed):
                self.rejected(live(stats=[stat(), stat(**changed)]), "Malformed|Unowned|identity changed")
                self.rejected(exits(stats=[stat(), stat("Z"), stat("Z", **changed)]), "Malformed|Unowned|identity changed")

    def test_unknown_executable_or_argument_is_not_waived_after_exit(self):
        for bad in (ARGV.replace(b"scontrol", b"othercmd"), ARGV.replace(JOB.encode(), b"123")):
            with self.subTest(bad=bad):
                self.rejected(exits(argv=[bad]), "undeclared executable or arguments")
                self.rejected(exits(argv=[b"", bad]), "undeclared executable or arguments")

    def test_descendants_are_rejected_on_first_and_terminal_reads(self):
        self.rejected(exits(children=[b"505\n"]), "further descendant")
        self.rejected(exits(children=[b"", b"505\n"]), "further descendant")

    def test_terminal_state_must_remain_terminal(self):
        self.rejected(exits(stats=[stat(), stat("Z"), stat()]), "terminal accounting is not coherent")
        self.rejected(exits(statuses=[status("Z", rss=None), status("R", rss=25)]), "terminal accounting is not coherent")
        self.rejected(live(stats=[stat("Z"), stat()], statuses=[status()]), "terminal state changed")

    def test_terminal_uid_record_cannot_disappear_while_identity_remains(self):
        self.rejected(exits(statuses=[status("Z", rss=None), FileNotFoundError("missing")]), "terminal accounting is not coherent")

    def test_duplicate_or_missing_state_is_not_coherent_accounting(self):
        for bad in (status() + b"State:\tZ (zombie)\n", status().replace(b"State:", b"Other:")):
            self.rejected(live(statuses=[bad]), "Missing or ambiguous scheduler-query status state")

    def test_failure_keeps_bounded_redacted_state_and_field_diagnostics(self):
        diagnostic = self.rejected(live(statuses=[status(rss=None)]), "Missing or ambiguous live RSS")
        self.assertEqual(diagnostic["pid"], str(CHILD))
        self.assertEqual(diagnostic["stats"]["before"]["start_ticks"], "9876")
        self.assertEqual(diagnostic["stats"]["after"]["state"], "R")
        self.assertEqual(diagnostic["records"][0]["rss_fields"], 0)
        self.assertTrue(diagnostic["records"][0]["uid_matches"])

    def test_old_monitor_rejects_scripted_race_and_new_owned_monitor_accepts(self):
        for module, succeeds in ((predecessor, False), (controller, True)):
            script = exits(leader=True)
            with mock.patch.object(module, "proc_read", script), \
                 mock.patch.object(module.os, "getuid", return_value=UID), \
                 mock.patch.object(module.os, "getpid", return_value=PARENT), \
                 mock.patch.object(Path, "iterdir", return_value=iter([Path("/proc/101/task/101")])):
                if succeeds:
                    result = module.sample_owned(SimpleNamespace(pid=LEADER), JOB, SCONTROL, 1234)
                    self.assertEqual(result, {"rss_bytes": 100 * 1024, "start_ticks": 1234, "descendants": [CHILD]})
                else:
                    with self.assertRaisesRegex(ValueError, "Missing or ambiguous live RSS/ownership"):
                        module.sample_owned(SimpleNamespace(pid=LEADER), JOB, SCONTROL, 1234)


if __name__ == "__main__":
    unittest.main()
