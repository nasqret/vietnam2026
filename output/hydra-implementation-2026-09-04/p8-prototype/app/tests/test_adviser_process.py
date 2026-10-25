"""Lifecycle fixtures only. This module never starts a subprocess or backend."""
from contextlib import ExitStack
import os
import signal
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from p8_test_support import Clock, identity, request
from adviser_protocol import AdviserSession, BudgetStop, MAX_OUTPUT, ProtocolError, limits_for
import adviser_process as process_module
from adviser_process import AdviserRunner, ENVIRONMENT, authorized_spawn, spawn_argv
from adviser_worker import _audit


class FakeStream:
    def __init__(self, fd):
        self.fd, self.closed = fd, False

    def fileno(self):
        return self.fd

    def close(self):
        self.closed = True


class FakeChild:
    pid = 123456

    def __init__(self, *, cannot_reap=False, natural_exit=0):
        self.stdin, self.stdout, self.stderr = (FakeStream(number) for number in (100, 101, 102))
        self.returncode = None
        self.kills = 0
        self.waits = []
        self.cannot_reap = cannot_reap
        self.natural_exit = natural_exit

    def poll(self):
        return self.returncode

    def kill(self):
        self.kills += 1
        if not self.cannot_reap:
            self.returncode = -9

    def wait(self, timeout):
        self.waits.append(timeout)
        if self.cannot_reap:
            raise subprocess.TimeoutExpired("owned-fixture-only", timeout)
        if self.returncode is None:
            self.returncode = self.natural_exit
        return self.returncode


class FakeSelector:
    def __init__(self, child, clock, *, drain=True):
        self.child, self.clock, self.drain = child, clock, drain
        self.keys, self.closed = {}, False

    def register(self, stream, events, name):
        self.keys[stream.fileno()] = SimpleNamespace(fd=stream.fileno(), fileobj=stream, data=name)

    def unregister(self, stream):
        self.keys.pop(stream.fileno(), None)
        if not self.keys and not self.child.cannot_reap:
            self.child.returncode = self.child.natural_exit

    def get_map(self):
        return self.keys

    def select(self, timeout):
        self.clock.value += max(timeout, 0.025)
        return [(key, 0) for key in list(self.keys.values())] if self.drain else []

    def close(self):
        self.closed = True


class RunnerTests(unittest.TestCase):
    def fixture(self, *, rss=16 * 1024**2, output=b"bounded output", drain=True,
                cannot_reap=False, cancel_after_spawn=False, package_error=None, read_error=None, natural_exit=0):
        clock = Clock()
        child = FakeChild(cannot_reap=cannot_reap, natural_exit=natural_exit)
        selector = FakeSelector(child, clock, drain=drain)
        spawned = {"value": False}
        session = AdviserSession(deadline=400, clock=clock,
            should_stop=lambda: cancel_after_spawn and spawned["value"])
        req = request()
        buffers = {101: bytearray(output), 102: bytearray()}

        def popen(*args, **kwargs):
            spawned["value"] = True
            return child

        def read(fd, size):
            if read_error:
                raise read_error
            part = bytes(buffers[fd][:size])
            del buffers[fd][:size]
            return part

        runner = AdviserRunner("sympy")
        with ExitStack() as stack:
            launch = stack.enter_context(mock.patch.object(process_module.subprocess, "Popen", side_effect=popen))
            stack.enter_context(mock.patch.object(process_module.selectors, "DefaultSelector", return_value=selector))
            stack.enter_context(mock.patch.object(process_module.time, "monotonic", side_effect=clock))
            stack.enter_context(mock.patch.object(process_module, "backend_identity", return_value=identity("sympy")))
            stack.enter_context(mock.patch.object(process_module, "package", side_effect=package_error))
            stack.enter_context(mock.patch.object(process_module.os, "set_blocking"))
            stack.enter_context(mock.patch.object(process_module.os, "write", side_effect=lambda fd, data: len(data)))
            stack.enter_context(mock.patch.object(process_module.os, "read", side_effect=read))
            stack.enter_context(mock.patch.object(process_module.vampire_process, "_resident_size", return_value=123456))
            reader = stack.enter_context(mock.patch.object(process_module.vampire_process, "_owned_child_rss",
                side_effect=rss if isinstance(rss, Exception) else None,
                return_value=None if isinstance(rss, Exception) else rss))
            with session.lease(req) as lease:
                result = runner(lease)
                lease.record_external(result, quiescent=result["quiescent"])
            calls = launch.call_args_list
            reader_calls = reader.call_count
        return SimpleNamespace(result=result, runner=runner, child=child, selector=selector,
                               session=session, calls=calls, reader_calls=reader_calls)

    def test_completed_fixture_is_reaped_and_counted_once(self):
        found = self.fixture()
        self.assertEqual(found.result["status"], "completed")
        self.assertTrue(found.result["quiescent"])
        self.assertEqual(found.child.kills, 0)
        self.assertEqual(found.runner.calls, 1)
        self.assertEqual(found.session.report()["actual_launches"], 1)
        self.assertEqual(len(found.runner.records), 1)
        self.assertNotIn("stdout", found.runner.records[0])
        self.assertTrue(all(stream.closed for stream in (found.child.stdin, found.child.stdout, found.child.stderr)))
        args, kwargs = found.calls[0]
        self.assertEqual(args, (spawn_argv("sympy"),))
        self.assertFalse(kwargs["start_new_session"])
        self.assertTrue(kwargs["close_fds"])
        self.assertEqual(kwargs["env"], ENVIRONMENT)

    def test_startup_failure_never_spawns(self):
        found = self.fixture(package_error=ProtocolError("package fixture unavailable"))
        self.assertEqual(found.calls, [])
        self.assertEqual(found.result["status"], "unavailable")
        self.assertFalse(found.result["executed"])
        self.assertTrue(found.result["quiescent"])
        self.assertEqual(found.session.report()["requests"], 1)

    def test_live_rss_accounting_failure_kills_owned_child_and_reaps(self):
        found = self.fixture(rss=OSError("short accounting fixture"))
        self.assertEqual(found.result["status"], "failed")
        self.assertEqual(found.result["termination"]["reason"], "owned_child_rss_accounting_error")
        self.assertEqual(found.child.kills, 1)
        self.assertTrue(found.result["quiescent"])
        self.assertEqual(found.session.report()["actual_launches"], 1)

    def test_sampled_memory_stop_preserves_peak_and_exit(self):
        peak = limits_for("sympy")["sampled_stop_bytes"] + 1
        found = self.fixture(rss=peak)
        self.assertEqual(found.result["status"], "resource_limit")
        self.assertEqual(found.result["peak_rss_bytes"], peak)
        self.assertEqual(found.result["rss_samples"], 1)
        self.assertEqual(found.result["exit_code"], -9)
        self.assertEqual(found.child.kills, 1)

    def test_caller_cancellation_stops_and_reaps_the_owned_child(self):
        found = self.fixture(cancel_after_spawn=True)
        self.assertEqual(found.result["status"], "cancelled")
        self.assertEqual(found.result["termination"]["reason"], "caller_cancelled")
        self.assertEqual(found.child.kills, 1)
        self.assertTrue(found.result["quiescent"])

    def test_outer_wall_limit_has_bounded_sampling_and_cleanup(self):
        found = self.fixture(drain=False)
        self.assertEqual(found.result["status"], "timeout")
        self.assertEqual(found.child.kills, 1)
        self.assertLessEqual(found.reader_calls, 101)
        self.assertTrue(all(wait <= 0.5 for wait in found.child.waits))
        self.assertGreaterEqual(found.session.report()["external_wall_seconds"], 2.0)

    def test_combined_output_bound_is_not_a_success(self):
        found = self.fixture(output=b"x" * (MAX_OUTPUT + 1))
        self.assertEqual(found.result["status"], "output_limit")
        self.assertEqual(len(found.result["stdout"]) + len(found.result["stderr"]), MAX_OUTPUT)
        self.assertEqual(found.child.kills, 1)
        self.assertTrue(found.result["quiescent"])

    def test_read_failure_after_launch_still_accounts_for_actual_process(self):
        found = self.fixture(read_error=OSError("broken output fixture"))
        self.assertEqual(found.result["status"], "failed")
        self.assertEqual(found.result["termination"]["reason"], "runner_io_error")
        self.assertEqual(found.child.kills, 1)
        self.assertEqual(found.session.report()["actual_launches"], 1)

    def test_unconfirmed_reaping_blocks_another_backend(self):
        found = self.fixture(rss=999 * 1024**2, cannot_reap=True)
        self.assertEqual(found.result["termination"]["reason"], "owned_child_reap_unconfirmed")
        self.assertFalse(found.result["quiescent"])
        self.assertEqual(found.session.report()["blocked_reason"], "external_child_not_reaped")
        with self.assertRaises(BudgetStop):
            found.session.lease(request("cvc5"))

    def test_actual_cpu_and_alarm_signals_are_resource_stops(self):
        cpu = self.fixture(natural_exit=-signal.SIGXCPU)
        self.assertEqual(cpu.result["status"], "resource_limit")
        self.assertEqual(cpu.result["termination"]["reason"], "cpu_limit_signal")
        alarm = self.fixture(natural_exit=-signal.SIGALRM)
        self.assertEqual(alarm.result["status"], "timeout")
        self.assertEqual(alarm.result["termination"]["reason"], "helper_wall_alarm")
        self.assertTrue(cpu.result["quiescent"] and alarm.result["quiescent"])


class AuthorityTests(unittest.TestCase):
    def test_exact_helper_argv_cwd_environment_and_backend_are_required(self):
        args = spawn_argv("cvc5")
        self.assertTrue(authorized_spawn(process_module.sys.executable, args, str(process_module.APP),
                                         dict(ENVIRONMENT), backend="cvc5"))
        for changed in (args + ["--version"], [*args[:-1], "sympy"], ["/bin/sh", "-c", "anything"]):
            self.assertFalse(authorized_spawn(process_module.sys.executable, changed, str(process_module.APP),
                                              dict(ENVIRONMENT), backend="cvc5"))
        self.assertFalse(authorized_spawn(process_module.sys.executable, args, "/tmp", dict(ENVIRONMENT), backend="cvc5"))
        self.assertFalse(authorized_spawn(process_module.sys.executable, args, str(process_module.APP),
                                          {**ENVIRONMENT, "PYTHONPATH": "/tmp"}, backend="cvc5"))
        with self.assertRaises(ProtocolError):
            spawn_argv("shell")

    def test_child_audit_denies_network_processes_signals_and_writable_open(self):
        for event in ("socket.connect", "subprocess.Popen", "os.posix_spawn", "os.system", "os.kill", "os.killpg"):
            with self.subTest(event=event), self.assertRaises(PermissionError):
                _audit(event, ())
        for args in (("/tmp/file", "w", 0), ("/tmp/file", None, os.O_RDWR)):
            with self.assertRaises(PermissionError):
                _audit("open", args)
        _audit("open", ("/bounded/read/path", "rb", os.O_RDONLY))

    def test_package_file_pin_rejects_symlinks_and_hardlinks_but_handles_empty_python_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.py"
            path.write_bytes(b"")
            self.assertEqual(process_module._file_pin(path, 64)["bytes"], 0)
            link = Path(directory) / "link.py"
            link.symlink_to(path)
            with self.assertRaises(OSError):
                process_module._file_pin(link, 64)
            hard = Path(directory) / "hard.py"
            os.link(path, hard)
            with self.assertRaises(ProtocolError):
                process_module._file_pin(path, 64)

    def test_shared_ceiling_does_not_relax_the_existing_deep_parent_limit(self):
        old = process_module.vampire_limits.solver_limits("deep")
        new = limits_for("cvc5")
        self.assertEqual(new["parent_sampled_rss_bytes"], old["sampled_rss_bytes"])
        self.assertEqual(new["sampled_stop_bytes"], 384 * 1024**2)
        self.assertEqual((new["cpu_seconds"], new["wall_seconds"]), (6, 8))


if __name__ == "__main__":
    unittest.main()
