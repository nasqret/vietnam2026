"""Mocked lifecycle/exec tests only. No native helper or tactic is executed."""
from contextlib import ExitStack
from types import SimpleNamespace
import unittest
from unittest import mock

from p8_test_support import Clock, state
from adviser_protocol import (AdviserSession, ProtocolError, canonical_json, external_request,
                              limits_for, prepare_request)
import adviser_process as process
import adviser_worker as worker
from test_adviser_process import FakeChild, FakeSelector
from vampire_bridge import export_state


def request(backend):
    identity = {"backend": backend, "version": "3.3.6" if backend == "e" else "0.11.0", "profile": "deep",
                "package_sha256": "1" * 64, "helper_sha256": "2" * 64}
    context = canonical_json({"schema": "hydra-adviser-semantic-context-v1", "test": True})
    if backend == "e":
        return external_request("e", export_state(state()).text.encode(), context, identity), identity
    return prepare_request("egg", {}, context, identity), identity


class NativeAuthorityTests(unittest.TestCase):
    def test_exact_backend_spawn_and_cpu_wall_bounds(self):
        for backend, cpu, wall in (("egg", 1, 2), ("e", 6, 8)):
            args = process.spawn_argv(backend)
            self.assertTrue(process.authorized_spawn(process.sys.executable, args, str(process.APP), process.ENVIRONMENT, backend=backend))
            self.assertFalse(process.authorized_spawn(process.sys.executable, args + ["--auto-schedule"], str(process.APP), process.ENVIRONMENT, backend=backend))
            self.assertEqual(limits_for(backend)["cpu_seconds"], cpu)
            self.assertEqual(limits_for(backend)["wall_seconds"], wall)
            self.assertEqual(limits_for(backend)["sampled_stop_bytes"], 384 * 1024**2)
            self.assertEqual(limits_for(backend)["parent_sampled_rss_bytes"], 512 * 1024**2)
        self.assertNotIn("--auto-schedule", process.native_argv("e"))
        self.assertEqual(len(process.native_argv("egg")), 1)

    def test_native_exec_authority_is_exact_and_once(self):
        for backend in ("e", "egg"):
            argv = process.native_argv(backend)
            audit = worker._native_exec_audit(backend)
            with self.assertRaises(PermissionError):
                audit("os.exec", ("/bin/sh", argv, process.ENVIRONMENT))
            with self.assertRaises(PermissionError):
                audit("os.exec", (argv[0], argv + ["--version"], process.ENVIRONMENT))
            with self.assertRaises(PermissionError):
                audit("os.exec", (argv[0], argv, {**process.ENVIRONMENT, "PATH": "/tmp"}))
            audit("os.exec", (argv[0], argv, dict(process.ENVIRONMENT)))
            with self.assertRaises(PermissionError):
                audit("os.exec", (argv[0], argv, process.ENVIRONMENT))
            for event in ("subprocess.Popen", "os.fork", "os.kill", "socket.connect"):
                with self.assertRaises(PermissionError):
                    audit(event, ())

    def test_fixed_worker_preserves_stdin_until_same_pid_exec(self):
        for backend, cpu, wall in (("e", 6, 8), ("egg", 1, 2)):
            forbidden_read = mock.Mock(side_effect=AssertionError("stdin must reach exec untouched"))
            with ExitStack() as stack:
                stack.enter_context(mock.patch.object(worker.sys, "argv", [str(worker.APP / "adviser_worker.py"), "--backend", backend]))
                stack.enter_context(mock.patch.object(worker.sys, "stdin", SimpleNamespace(buffer=SimpleNamespace(read=forbidden_read))))
                limits = stack.enter_context(mock.patch.object(worker.resource, "setrlimit"))
                alarm = stack.enter_context(mock.patch.object(worker.signal, "alarm"))
                stack.enter_context(mock.patch.object(process, "native_package", return_value={}))
                hook = stack.enter_context(mock.patch.object(worker.sys, "addaudithook"))
                execute = stack.enter_context(mock.patch.object(worker.os, "execve", side_effect=RuntimeError("fixture exec boundary")))
                with self.assertRaisesRegex(RuntimeError, "fixture exec boundary"):
                    worker.main()
                forbidden_read.assert_not_called()
                argv = process.native_argv(backend)
                execute.assert_called_once_with(argv[0], argv, dict(process.ENVIRONMENT))
                hook.assert_called_once()
                alarm.assert_called_once_with(wall)
                self.assertIn(mock.call(worker.resource.RLIMIT_CPU, (cpu, cpu)), limits.call_args_list)

    def test_scoped_e_input_refuses_include_file_symbols_and_roles(self):
        raw = export_state(state()).text.encode()
        process.validate_native_input("e", raw)
        bad = (raw + b"include('secret').\n", raw.replace(b"hydra_zero", b"unexported_symbol"),
               raw.replace(b",conjecture,", b",axiom,"), raw + raw.splitlines()[1] + b"\n")
        for value in bad:
            with self.assertRaises(ProtocolError):
                process.validate_native_input("e", value)

    def test_native_package_metadata_is_pinned_without_running_it(self):
        data = process.native_package(verify_files=True)
        self.assertEqual(data["executables"]["e"]["sha256"], "948adbc7b00c685f08359caf7ae703b4dea1bf5439b6313e6b38b1d90a9ae44b")
        self.assertEqual(data["executables"]["egg"]["sha256"], "0ba2c1a0ccf011824839e44be4a28a1d3887f0b98afb10a642e0245f32c9d8e8")


class NativeLifecycleTests(unittest.TestCase):
    def fixture(self, *, backend="e", code=0, output=b"% Version: 3.3.6\n", popen_error=None, rss=123456):
        req, identity = request(backend)
        clock = Clock()
        session = AdviserSession(deadline=400, clock=clock)
        child = FakeChild(natural_exit=code)
        selector = FakeSelector(child, clock)
        buffers = {101: bytearray(output), 102: bytearray()}

        def read(fd, size):
            value = bytes(buffers[fd][:size])
            del buffers[fd][:size]
            return value

        runner = process.AdviserRunner(backend)
        with ExitStack() as stack:
            launch = stack.enter_context(mock.patch.object(process.subprocess, "Popen", side_effect=popen_error, return_value=child))
            stack.enter_context(mock.patch.object(process, "backend_identity", return_value=identity))
            stack.enter_context(mock.patch.object(process, "package", return_value={}))
            stack.enter_context(mock.patch.object(process.time, "monotonic", side_effect=clock))
            stack.enter_context(mock.patch.object(process.selectors, "DefaultSelector", return_value=selector))
            stack.enter_context(mock.patch.object(process.os, "set_blocking"))
            stack.enter_context(mock.patch.object(process.os, "write", side_effect=lambda fd, value: len(value)))
            stack.enter_context(mock.patch.object(process.os, "read", side_effect=read))
            stack.enter_context(mock.patch.object(process.vampire_process, "_resident_size", return_value=123))
            stack.enter_context(mock.patch.object(process.vampire_process, "_owned_child_rss", return_value=rss))
            with session.lease(req) as lease:
                result = runner(lease)
                self.assertTrue(lease.dispatch_claimed)
                with self.assertRaises(ProtocolError):
                    runner(lease)
                lease.record_external(result, quiescent=result["quiescent"])
            return result, runner, child, launch.call_count, session.report()

    def test_dispatch_claim_survives_popen_failure(self):
        result, runner, _, attempts, report = self.fixture(popen_error=OSError("fixture spawn refusal"))
        self.assertEqual(attempts, 1)
        self.assertEqual(runner.calls, 0)
        self.assertEqual(result["helper_launches"], 0)
        self.assertFalse(result["backend_execution_confirmed"])
        self.assertEqual(report["requests"], 1)
        self.assertEqual(report["actual_launches"], 0)

    def test_helper_preflight_failure_is_not_confirmed_backend_execution(self):
        result, _, _, _, report = self.fixture(code=70, output=b"")
        self.assertEqual(result["helper_launches"], 1)
        self.assertFalse(result["backend_execution_confirmed"])
        self.assertEqual(report["actual_launches"], 1)

    def test_e_known_exit_codes_classify_without_reading_proof_flags(self):
        for code, status in ((1, "no_refutation"), (2, "resource_limit"), (8, "timeout"), (9, "resource_limit"), (10, "no_refutation")):
            result, _, child, attempts, report = self.fixture(code=code, output=b"% Version: 3.3.6\n% SZS status Theorem\n")
            self.assertEqual(result["status"], status)
            self.assertTrue(result["backend_execution_confirmed"])
            self.assertTrue(result["quiescent"])
            self.assertEqual(attempts, 1)
            self.assertEqual(report["actual_launches"], 1)

    def test_memory_stop_reaps_owned_child_and_does_not_accept_flags(self):
        result, _, child, _, report = self.fixture(rss=384 * 1024**2 + 1, output=b"% SZS status Theorem\n")
        self.assertEqual(result["status"], "resource_limit")
        self.assertEqual(child.kills, 1)
        self.assertTrue(result["quiescent"])
        self.assertEqual(report["actual_launches"], 1)


if __name__ == "__main__":
    unittest.main()
