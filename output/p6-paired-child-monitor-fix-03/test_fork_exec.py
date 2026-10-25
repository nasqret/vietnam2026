"""Recorded-prefix assertions plus hypothetical /proc continuations; no real child."""
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
PREVIOUS = HERE.parent / "p6-paired-child-monitor-fix-02"
OLD_SHA = "caff33d11918bad304ddf0a04021550a6d686d254e604342190df094958ce482"
ACTUAL = PROJECT / "output/p6-paired-child-linux-probe-03/observation-001"
ACTUAL_PINS = {
    "result.json": "93a853aa861dbbd477ce929dfc54b05c20b8e8c48b40687eb46804bbf2605973",
    "files/run-01/case-00/execution.json": "4555dedfd8e79315d733105ec7841c2bca9e2fc17762037eb4571da985a0ac35",
    "actual-completion.json": "47cbcc84118577db9a553394b5a2406321f3df167b4371260d898457e5f0d62f",
}
assert sha256((PREVIOUS / "paired_controller.py").read_bytes()).hexdigest() == OLD_SHA


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


previous = load("previous_argv_exit_fixtures", PREVIOUS / "test_argv_exit.py")
old_controller = previous.controller
controller = load("fork_exec_candidate", HERE / "paired_controller.py")
previous.controller = controller
previous.previous.controller = controller
previous.fixtures.controller = controller
previous.fixtures.HERE = HERE
previous.sample.__kwdefaults__["module"] = controller
fixtures = previous.fixtures
LEADER, UID, CHILD = previous.LEADER, previous.UID, previous.CHILD
BASE, FORK, EXIT = 4194304, 4194368, 4194316
SCONTROL_ARGV = previous.previous.ARGV
PARENT_ARGS = [sys.executable, "-B", str(HERE / "paired_case_worker.py"),
               "--request", "/fixture/case-request.json", "--request-sha256", "a" * 64]
PARENT_ARGV = b"\0".join(value.encode() for value in PARENT_ARGS) + b"\0"


def child_stat(state="R", flags=FORK, **changes):
    values = dict(pid=CHILD, ppid=LEADER, pgid=LEADER, sid=LEADER, start=9876, flags=flags)
    values.update(changes)
    return fixtures.stat(state, **values)


def sample(*, module=controller, before=None, after=None, status=None, argv=PARENT_ARGV,
           parent_argv=PARENT_ARGV, children=b"", pending=None, terminal=False,
           disappear=False, read_log=None, pid=CHILD, leader=LEADER):
    if disappear:
        scripts = {"stat": [FileNotFoundError("gone"), FileNotFoundError("still gone")]}
    else:
        scripts = {
            "stat": [child_stat() if before is None else before,
                     child_stat() if after is None else after],
            "status": [fixtures.status("R", rss=25) if status is None else status],
            "cmdline": [argv], "children": [children],
        }
        if terminal:
            terminal_flags = FORK | 4 if pending and not pending["fork_clear_observed"] else EXIT
            scripts["stat"].append(child_stat("Z", terminal_flags))
            scripts["status"].append(fixtures.status("Z"))
            scripts["cmdline"].append(b"")
            scripts["children"].append(b"")

    def read(path, maximum):
        assert str(path).startswith("/proc/" + str(pid) + "/")
        assert maximum == (8192 if path.name in {"stat", "children"} else 65536)
        if read_log is not None:
            read_log.append(path.name)
        value = scripts[path.name].pop(0)
        if isinstance(value, BaseException):
            raise value
        return value

    with mock.patch.object(module, "proc_read", side_effect=read), \
         mock.patch.object(module.os, "getuid", return_value=UID), \
         mock.patch.object(module.os, "waitid", side_effect=AssertionError("never wait a grandchild"), create=True):
        kwargs = {} if module is old_controller else {"parent_argv": parent_argv}
        return module.sample_scheduler_child(pid, leader, fixtures.JOB, fixtures.SCONTROL, pending, **kwargs)


class ForkLifecycle(previous.previous.ChildLifecycle):
    """A new child appears, may exec, and may exit; all times/data are synthetic."""
    def __init__(self, *, fork_at=0.1, exec_at=0.2, exit_at=0.3,
                 zombie_at=0.4, reaped_at=0.5, parent_exit=0.7, **kwargs):
        super().__init__(pending_at=fork_at, zombie_at=zombie_at, reaped_at=reaped_at,
                         parent_exit=parent_exit, **kwargs)
        self.args = list(PARENT_ARGS)
        self.exec_at, self.child_exit_at = exec_at, exit_at

    def read(self, path, maximum):
        name = str(path)
        if name == "/proc/101/task/101/children" and self.now < self.pending_at:
            self.reads.append((self.now, name, maximum))
            return b""
        raw = super().read(path, maximum)
        if not name.startswith("/proc/202/"):
            return raw
        if path.name == "stat":
            prefix, tail = raw.decode().rsplit(") ", 1)
            fields = tail.split()
            if fields[0] == "D":
                fields[0] = "R"
            fields[6] = str((FORK if self.now < self.exec_at else BASE)
                            | (4 if self.now >= self.child_exit_at else 0))
            return (prefix + ") " + " ".join(fields) + "\n").encode()
        if path.name == "status":
            raw = raw.replace(b"State:\tD ", b"State:\tR ")
            if self.now < min(self.child_exit_at, self.zombie_at) and b"VmRSS:" not in raw:
                raw += b"VmRSS:\t25 kB\n"
        if path.name == "cmdline":
            if self.now >= self.child_exit_at:
                return b""
            return PARENT_ARGV if self.now < self.exec_at else SCONTROL_ARGV
        return raw


class ForkExecTests(unittest.TestCase):
    def failed(self, life, pattern, **kwargs):
        result = fixtures.supervise(life, **kwargs)
        self.assertRegex(result["termination_reason"], pattern)
        self.assertTrue(result["leader_reaped"])
        self.assertFalse(result["quiescent"])
        self.assertNotEqual(controller.classify_case(result, {"status": "proved"}), "proved")
        return result

    def test_actual_failed_prefix_is_authenticated_but_its_continuation_is_unknown(self):
        actual = {}
        for name, expected in ACTUAL_PINS.items():
            raw = (ACTUAL / name).read_bytes()
            self.assertEqual(sha256(raw).hexdigest(), expected)
            actual[name] = json.loads(raw)
        execution = actual["files/run-01/case-00/execution.json"]
        report = actual["result.json"]
        trace = next(row for row in report["retained_child_traces"] if row["pid"] == 171972)
        inherited = b"\0".join(value.encode() for value in execution["argv"]) + b"\0"
        self.assertEqual((len(inherited), sha256(inherited).hexdigest()),
                         (540, "3736d30d1ce99603cde7c24b13439207cd04d146948f3a2f484a2d421777c6f7"))
        self.assertEqual([read["kind"] for read in trace["reads"]], ["stat", "status", "cmdline"])
        self.assertEqual(trace["reads"][2]["cmdline_sha256"], sha256(inherited).hexdigest())
        identity = execution["accounting_diagnostic"]["stats"]["before"]
        self.assertEqual(identity, {"state": "R", "flags": str(FORK), "ppid": "171921",
                                   "pgid": "171921", "sid": "171921", "start_ticks": "2481165"})
        self.assertIsNone(execution["child_terminal_resolution"])
        self.assertEqual((execution["exit_code"], actual["actual-completion.json"]["passed"]), (-9, False))
        # Only flags/argv/identity and the validity (not numeric value) of RSS
        # were retained. The second stat/no-descendant/RSS value below is a fixture.
        stat = child_stat(pid=171972, ppid=171921, pgid=171921, sid=171921, start=2481165)
        reads = []
        with self.assertRaisesRegex(ValueError, "undeclared executable"):
            sample(module=old_controller, pid=171972, leader=171921, before=stat,
                   after=stat, argv=inherited, read_log=reads)
        self.assertEqual(reads, ["stat", "status", "cmdline"])
        reads = []
        observed = sample(pid=171972, leader=171921, before=stat, after=stat,
                          argv=inherited, parent_argv=inherited, read_log=reads)
        self.assertEqual(reads, ["stat", "status", "cmdline", "children", "stat"])
        self.assertEqual((observed["pending_kind"], observed["pending_exit"], observed["terminal"]),
                         ("fork", True, None))
        self.assertFalse(observed["exec_observed"])
        self.assertIsNone(observed["rss_bytes"])
        self.assertEqual(observed["known_rss_bytes"], 25 * 1024)

    def test_inherited_argv_can_span_fork_flag_clearing_in_same_read_set(self):
        pending = sample(after=child_stat(flags=BASE))
        self.assertEqual(pending["lifecycle_phase"], "exec_unconfirmed")
        self.assertTrue(pending["fork_clear_observed"])
        self.assertFalse(pending["exec_observed"])
        self.assertTrue(pending["diagnostic"]["records"][0]["inherited_parent_argv_matches"])
        self.assertEqual(pending["diagnostic"]["records"][0]["rss_bytes"], 25 * 1024)

    def test_later_exact_exec_remains_pending_until_coherent_natural_terminal(self):
        pending = sample()
        running = sample(before=child_stat(flags=BASE), after=child_stat(flags=BASE),
                         argv=SCONTROL_ARGV, status=fixtures.status("R", rss=31), pending=pending)
        self.assertEqual((running["lifecycle_phase"], running["exec_observed"], running["pending_exit"]),
                         ("exec_observed", True, True))
        self.assertEqual(running["known_rss_bytes"], 31 * 1024)
        exiting = sample(before=child_stat(flags=BASE), after=child_stat(flags=EXIT),
                         argv=b"", status=fixtures.status("R", rss=30), pending=running)
        self.assertEqual(exiting["lifecycle_phase"], "exit")
        done = sample(before=child_stat("Z", EXIT), after=child_stat("Z", EXIT),
                      argv=b"", status=fixtures.status("Z"), pending=exiting, terminal=True)
        self.assertEqual((done["terminal"], done["pending_exit"], done["exec_observed"]), ("zombie", False, True))
        self.assertEqual(done["known_rss_bytes"], 31 * 1024)

    def test_terminal_or_disappearance_without_observed_exec_never_claims_exec(self):
        pending = sample()
        done = sample(before=child_stat("Z", FORK | 4), after=child_stat("Z", FORK | 4),
                      argv=b"", status=fixtures.status("Z"), pending=pending, terminal=True)
        gone = sample(pending=pending, disappear=True)
        for observed in (done, gone):
            self.assertFalse(observed["pending_exit"])
            self.assertFalse(observed["exec_observed"])
        self.assertEqual(gone["diagnostic"]["absent_stat_reads"], 2)

    def test_initial_inherited_sample_must_have_complete_identity_bracket(self):
        with self.assertRaisesRegex(ValueError, "initial identity bracket"):
            sample(after=FileNotFoundError("actual continuation was not captured"))
        with self.assertRaisesRegex(ValueError, "descendant accounting is unavailable"):
            sample(children=FileNotFoundError("missing children record"))

    def test_inherited_parent_argv_requires_exact_binding_fork_bit_and_actual_rss(self):
        for kwargs, pattern in (({"parent_argv": None}, "undeclared executable"),
                ({"parent_argv": b"foreign\0"}, "undeclared executable"),
                ({"before": child_stat(flags=BASE)}, "fork-no-exec identity"),
                ({"status": fixtures.status("R")}, "actual live RSS"),
                ({"argv": b""}, "command line is unavailable")):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, pattern):
                sample(**kwargs)

    def test_foreign_nonempty_argv_never_reaches_after_stat_or_terminal_forgiveness(self):
        for pending in (None, sample()):
            reads = []
            with self.subTest(pending=pending is not None), self.assertRaisesRegex(ValueError, "undeclared executable"):
                sample(pending=pending, argv=SCONTROL_ARGV.replace(b"scontrol", b"foreign"),
                       after=child_stat("Z", EXIT), read_log=reads)
            self.assertEqual(reads, ["stat", "status", "cmdline"])

    def test_every_identity_uid_and_descendant_violation_still_fails(self):
        for change in ({"pid": CHILD + 1}, {"ppid": LEADER + 1}, {"pgid": LEADER + 1},
                       {"sid": LEADER + 1}, {"start": 9877}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "Malformed|Unowned|identity changed"):
                sample(after=child_stat(**change))
        for index in range(4):
            uids = [UID] * 4
            uids[index] += 1
            with self.subTest(uid=index), self.assertRaisesRegex(ValueError, "uid changed"):
                sample(status=fixtures.status("R", rss=25, uids=tuple(uids)))
        with self.assertRaisesRegex(ValueError, "further descendant"):
            sample(children=b"909")

    def test_fork_reappearance_exit_regression_and_return_to_parent_argv_fail(self):
        pending = sample(after=child_stat(flags=BASE))
        with self.assertRaisesRegex(ValueError, "fork-no-exec flag reappeared"):
            sample(pending=pending)
        with self.assertRaisesRegex(ValueError, "fork-no-exec identity"):
            sample(before=child_stat(flags=BASE), after=child_stat(flags=BASE), pending=pending)
        executing = sample(before=child_stat(flags=BASE), after=child_stat(flags=BASE),
                           argv=SCONTROL_ARGV, pending=pending)
        exiting = sample(before=child_stat(flags=EXIT), after=child_stat(flags=EXIT),
                         argv=b"", pending=executing)
        with self.assertRaisesRegex(ValueError, "exiting flag regressed"):
            sample(before=child_stat(flags=BASE), argv=SCONTROL_ARGV, pending=exiting)

    def test_pending_parent_binding_pid_reuse_and_resumed_rss_are_not_waived(self):
        pending = sample()
        with self.assertRaisesRegex(ValueError, "owned-parent argv binding"):
            sample(pending=pending, parent_argv=b"different\0")
        with self.assertRaisesRegex(ValueError, "identity changed|PID was reused"):
            sample(before=child_stat(start=9877), pending=pending)
        absent = sample(before=child_stat(flags=EXIT), after=child_stat(flags=EXIT),
                        status=fixtures.status("R"), argv=b"", pending=pending)
        with self.assertRaisesRegex(ValueError, "resumed RSS"):
            sample(before=child_stat(flags=EXIT), after=FileNotFoundError("gone after observed violation"),
                   argv=b"", pending=absent)

    def test_owned_popen_args_threading_and_real_rss_survive_full_virtual_lifecycle(self):
        original = controller.sample_scheduler_child
        bindings = []
        def capture(*args, **kwargs):
            bindings.append(kwargs["parent_argv"])
            return original(*args, **kwargs)
        with mock.patch.object(controller, "sample_scheduler_child", side_effect=capture):
            result = fixtures.supervise(ForkLifecycle())
        self.assertTrue(bindings and all(value == PARENT_ARGV for value in bindings))
        self.assertEqual((result["termination_reason"], result["exit_code"], result["quiescent"]),
                         ("process_exit", 0, True))
        resolution = result["child_terminal_resolution"]
        episode = resolution["episodes"][0]
        self.assertEqual(episode["outcome"], "natural_exit_confirmed")
        frames = [frame["child"] for frame in episode["samples"]]
        self.assertTrue(any(frame["lifecycle_phase"] == "fork" for frame in frames))
        self.assertTrue(any(frame["exec_observed"] for frame in frames))
        self.assertEqual(result["peak_sampled_host_rss_bytes"], 125 * 1024)
        self.assertLessEqual(resolution["resolution_and_cleanup_seconds"], 3)

    def test_missing_or_malformed_owned_launch_args_cannot_admit_inherited_child(self):
        for bad in (None, "a shell command", ["with\0nul"], ["x" * 65536], ["x"] * 33):
            life = ForkLifecycle(fork_at=0)
            life.args = bad
            with self.subTest(bad_type=type(bad).__name__):
                self.failed(life, "owned-worker launch argv|undeclared executable")

    def test_pending_fork_keeps_existing_cancel_wall_memory_overlap_and_sample_deadlines(self):
        life = ForkLifecycle(exec_at=8, exit_at=9, zombie_at=10, reaped_at=11, parent_exit=12)
        self.failed(life, "cancelled", should_stop=lambda: life.now >= 0.2)
        self.failed(ForkLifecycle(fork_at=89, exec_at=92, exit_at=93, zombie_at=94,
                                 reaped_at=95, parent_exit=96), "case_wall_limit")
        self.failed(ForkLifecycle(fork_at=0), "host_sampled_rss_limit", sample_wrapper=lambda row: {
            **row, "known_rss_bytes": controller.RESOURCE_LIMITS["host_sampled_rss_bytes"] + 1})
        self.failed(ForkLifecycle(exec_at=2, exit_at=3, zombie_at=4, reaped_at=5,
                                 parent_exit=0.2), "leader exited before")
        self.failed(ForkLifecycle(exec_at=2, exit_at=3, zombie_at=4, reaped_at=5,
                                 parent_missing=0.15, parent_exit=0.4), "Overlapping")
        for tick in (True, False):
            with self.subTest(clock_advances=tick):
                result = self.failed(ForkLifecycle(fork_at=0, exec_at=8, exit_at=9, zombie_at=10,
                                     reaped_at=11, parent_exit=12, tick=tick), "remained unproven")
                resolution = result["child_terminal_resolution"]
                self.assertLessEqual(resolution["sample_count"], 61)
                self.assertLessEqual(resolution["resolution_and_cleanup_seconds"], 3.000001)
                self.assertLessEqual(len(controller.canonical(resolution)), 256 * 1024)
                self.assertEqual(result["exit_code"], -signal.SIGKILL)

    def test_scope_changes_only_two_samplers_and_one_named_linux_flag(self):
        before = ast.parse((PREVIOUS / "paired_controller.py").read_bytes())
        after = ast.parse((HERE / "paired_controller.py").read_bytes())
        functions = lambda tree: {node.name: ast.dump(node, include_attributes=False)
                                 for node in tree.body if isinstance(node, ast.FunctionDef)}
        old, new = functions(before), functions(after)
        self.assertEqual(old.keys(), new.keys())
        self.assertEqual({name for name in old if old[name] != new[name]},
                         {"sample_scheduler_child", "sample_owned"})
        other = lambda tree: [ast.dump(node, include_attributes=False) for node in tree.body
                             if not isinstance(node, ast.FunctionDef)
                             and not (isinstance(node, ast.Assign) and any(
                                 isinstance(target, ast.Name) and target.id == "PF_FORKNOEXEC"
                                 for target in node.targets))]
        self.assertEqual(other(before), other(after))
        self.assertEqual(controller.PF_FORKNOEXEC, 0x40)
        self.assertEqual(sha256((PREVIOUS / "paired_controller.py").read_bytes()).hexdigest(), OLD_SHA)
        self.assertFalse(any(name in sys.modules for name in ("torch", "transformers", "peano_lab")))


def suite():
    result = unittest.defaultTestLoader.loadTestsFromTestCase(ForkExecTests)
    for case in (previous.ArgvExitTests, previous.previous.ChildResolutionTests):
        result.addTests(case(name) for name in unittest.defaultTestLoader.getTestCaseNames(case)
                        if not name.startswith("test_scope_"))
    return result


if __name__ == "__main__":
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (10, 15))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(20)
    result = unittest.TextTestRunner(verbosity=2).run(suite())
    print(json.dumps({"schema": "hydra-child-fork-exec-pure-fixtures-v1", "tests": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
        "passed": result.wasSuccessful(), "new_path_tests": 14, "unchanged_child_behavior_tests": 28,
        "real_processes": 0, "real_linux_validation": False, "model_calls": 0, "native_calls": 0,
        "controller_sha256": sha256((HERE / "paired_controller.py").read_bytes()).hexdigest(),
        "test_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "actual_failure_pins": ACTUAL_PINS}, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
