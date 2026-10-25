"""Profile boundaries and termination accounting without launching a solver."""
from collections import deque
from pathlib import Path
import signal
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import vampire_limits as policy
import vampire_process as runner
import vampire_worker as helper


class ProfileTests(unittest.TestCase):
    def test_profiles_have_only_fixed_args_and_independent_limit_copies(self):
        expected = {"standard": (1, 2, 3, 256), "deep": (5, 6, 8, 512), "research": (15, 16, 18, 512)}
        for profile, (solver, cpu, wall, sampled_rss) in expected.items():
            with self.subTest(profile=profile):
                limits = runner.solver_limits(profile)
                self.assertEqual(limits, {"profile": profile, "solver_seconds": solver,
                    "cpu_seconds": cpu, "wall_seconds": wall, "solver_memory_mib": 256,
                    "sampled_rss_bytes": sampled_rss * 1024**2,
                    "input_bytes": 65536, "output_bytes": 262144, "max_simultaneous_children": 1})
                self.assertEqual(policy.solver_args(profile), ["--mode", "vampire", "--input_syntax", "tptp",
                    "--proof", "tptp", "--output_axiom_names", "on", "-t", str(solver), "-m", "256"])
                limits["wall_seconds"] = 99999
                self.assertEqual(runner.solver_limits(profile)["wall_seconds"], wall)
        self.assertEqual(runner.SOLVER_ARGS, policy.solver_args("standard"))
        self.assertEqual(runner.spawn_argv(), [sys.executable, "-I", "-B", str(runner.HELPER)])
        self.assertEqual(policy.RUNTIME_POLICY, "hydra-playground-vampire-runtime-policy-v2")

    def test_invalid_profiles_and_noncanonical_helper_arguments_fail_closed(self):
        for invalid in (None, False, 1, [], {}, "", "DEEP", "deep ", "--mode portfolio", "standard;sh"):
            with self.subTest(profile=invalid):
                for operation in (runner.solver_limits, runner.spawn_argv, runner.metadata_status, runner.VampireRunner):
                    with self.assertRaises(ValueError):
                        operation(invalid)
        for invalid in (["--profile", "standard"], ["--profile", "research", "--version"],
                        ["--profile", "deep", "-t", "90"], ["--profile", "unknown"],
                        ["--profile", "research", "-m", "512"],
                        ["-t", "15"], ["--version", "--profile", "deep"], ["--mode", "portfolio"],
                        ["--profile"], "--version", [False]):
            with self.subTest(arguments=invalid), self.assertRaises(ValueError):
                policy.parse_helper_arguments(invalid)

    def test_authorization_is_bound_to_one_profile_and_exact_environment(self):
        for authorized in policy.PROFILE_NAMES:
            for requested in policy.PROFILE_NAMES:
                with self.subTest(authorized=authorized, requested=requested):
                    self.assertEqual(runner.authorized_spawn(sys.executable, runner.spawn_argv(requested),
                        str(APP), dict(runner.ENVIRONMENT), profile=authorized), requested == authorized)
            args = runner.spawn_argv(authorized)
            for changed in (("/bin/sh", args, str(APP), dict(runner.ENVIRONMENT)),
                            (sys.executable, [*args, "-t", "999"], str(APP), dict(runner.ENVIRONMENT)),
                            (sys.executable, args, "/tmp", dict(runner.ENVIRONMENT)),
                            (sys.executable, args, str(APP), {**runner.ENVIRONMENT, "PYTHONPATH": "/tmp"}),
                            (sys.executable, None, str(APP), dict(runner.ENVIRONMENT))):
                self.assertFalse(runner.authorized_spawn(*changed, profile=authorized))

    def test_new_profile_policy_does_not_extend_the_old_smoke_attestation(self):
        manifest = {"executable": {"sha256": "b" * 64}}
        with patch.object(runner, "package", return_value=(APP / "unused", manifest, {})):
            for profile in policy.PROFILE_NAMES:
                status = runner.metadata_status(profile)
                self.assertTrue(status["available"])
                self.assertEqual(status["runtime_policy"], policy.RUNTIME_POLICY)
                self.assertEqual(status["solver_args"], policy.solver_args(profile))
                self.assertEqual(status["limits"], policy.solver_limits(profile))
                self.assertEqual(status["limits"]["solver_memory_mib"], 256)
                self.assertEqual(status["limits"]["sampled_rss_bytes"],
                                 (256 if profile == "standard" else 512) * 1024**2)
                self.assertEqual(status["package_smoke"], {"profile": "standard", "ready_record_verified": True,
                    "covers_selected_profile": profile == "standard"})


class HelperTests(unittest.TestCase):
    def test_helper_sets_profile_limits_before_exact_exec_with_no_fork(self):
        for arguments in ([], ["--profile", "deep"], ["--profile", "research"], ["--version"]):
            profile, version = policy.parse_helper_arguments(arguments)
            limits = policy.solver_limits(profile)
            with self.subTest(arguments=arguments), \
                 patch.object(helper.sys, "flags", SimpleNamespace(isolated=1)), \
                 patch.object(helper.sys, "dont_write_bytecode", True), \
                 patch.object(helper.sys, "argv", [str(runner.HELPER), *arguments]), \
                 patch.object(helper.resource, "setrlimit") as setlimit, \
                 patch.object(helper.signal, "signal"), patch.object(helper.signal, "setitimer") as timer, \
                 patch.object(helper, "package", return_value=(Path("/unused/pinned-vampire"), {}, {})) as package, \
                 patch.object(helper.os, "execve") as execute:
                helper.main()
                setlimit.assert_has_calls([
                    call(helper.resource.RLIMIT_CPU, (limits["cpu_seconds"], limits["cpu_seconds"])),
                    call(helper.resource.RLIMIT_CORE, (0, 0)), call(helper.resource.RLIMIT_FSIZE, (0, 0)),
                    call(helper.resource.RLIMIT_NOFILE, (64, 64))])
                timer.assert_called_once_with(signal.ITIMER_REAL, limits["wall_seconds"])
                package.assert_called_once_with(verify_binary=True, require_ready=False)
                options = ["--version"] if version else policy.solver_args(profile)
                execute.assert_called_once_with("/unused/pinned-vampire", ["/unused/pinned-vampire", *options],
                                                dict(runner.ENVIRONMENT))

    def test_helper_rejects_overrides_before_any_limit_or_exec(self):
        with patch.object(helper.sys, "flags", SimpleNamespace(isolated=1)), \
             patch.object(helper.sys, "dont_write_bytecode", True), \
             patch.object(helper.sys, "argv", [str(runner.HELPER), "--profile", "research", "-t", "999"]), \
             patch.object(helper.resource, "setrlimit") as setlimit, \
             patch.object(helper.os, "execve") as execute:
            with self.assertRaises(SystemExit):
                helper.main()
            setlimit.assert_not_called()
            execute.assert_not_called()


class TerminationTests(unittest.TestCase):
    def test_actual_recorded_fermats_one_second_stop_is_timeout_not_solver_error(self):
        path = APP.parent / "output/hydra-fermat-test-2026-09-01/vampire-diagnostic-01/stdout.txt"
        if not path.is_file():
            self.skipTest("The preserved local diagnostic is not in this checkout")
        output = path.read_text()
        result = policy.classify_termination(output, "", exit_code=1)
        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["termination"]["reason"], "solver_time_limit")
        self.assertIsNone(result["termination"]["szs_status"])
        self.assertTrue(any("Time limit" in item["text"] for item in result["termination"]["evidence"]))

    def test_szs_resource_stops_and_real_errors_are_distinct(self):
        for szs in ("Timeout", "CPUTimeout", "WCTimeout", "MemoryOut", "ResourceOut", "SyntaxError", "Error"):
            with self.subTest(szs=szs):
                output = "% SZS status " + szs + " for fixture\n"
                result = policy.classify_termination(output, "", exit_code=1)
                expected = "timeout" if "Timeout" in szs else "resource_limit" if szs in {"MemoryOut", "ResourceOut"} else "failed"
                self.assertEqual(result["status"], expected)
                self.assertEqual(result["termination"]["szs_status"], szs)
                self.assertEqual(result["timed_out"], expected == "timeout")
        for code, expected in ((-signal.SIGALRM, "timeout"), (-signal.SIGXCPU, "timeout"), (-signal.SIGKILL, "failed")):
            self.assertEqual(policy.classify_termination("", "", exit_code=code)["status"], expected)
        self.assertEqual(policy.classify_termination("% Timeout options are enabled\n", "", exit_code=1)["status"], "failed")
        self.assertEqual(policy.classify_termination("% SZS status Theorem for fixture\n", "", exit_code=1)["status"], "failed")

    def test_termination_evidence_is_small_and_conflicting_statuses_do_not_succeed(self):
        result = policy.classify_termination(("% Termination reason: " + "x" * 2000 + "\n") * 50,
                                             "error\n", exit_code=1)
        self.assertLessEqual(len(result["termination"]["evidence"]), policy.MAX_EVIDENCE_LINES)
        self.assertTrue(all(len(item["text"]) <= policy.MAX_EVIDENCE_CHARACTERS for item in result["termination"]["evidence"]))
        self.assertTrue(result["termination"]["evidence_truncated"])
        result = policy.classify_termination("% SZS status Theorem\n% SZS status Timeout\n", "", exit_code=0)
        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["termination"]["szs_status_conflict"])


class _Stream:
    def __init__(self, fd):
        self.fd, self.closed = fd, False

    def fileno(self):
        return self.fd

    def close(self):
        self.closed = True


class _Selector:
    def __init__(self):
        self.keys = {}

    def register(self, stream, _events, name):
        self.keys[stream.fd] = SimpleNamespace(fd=stream.fd, fileobj=stream, data=name)

    def unregister(self, stream):
        del self.keys[stream.fd]

    def get_map(self):
        return self.keys

    def select(self, _timeout):
        return [(key, 0) for key in list(self.keys.values())]

    def close(self):
        self.keys.clear()


class RunnerTests(unittest.TestCase):
    def run_mock_solver(self, profile, output, *, code=1, clock=None, running=False):
        process = Mock(stdin=_Stream(201), stdout=_Stream(202), stderr=_Stream(203))
        process.poll.return_value = None if running else code
        process.wait.return_value = code
        chunks = {202: deque([output[index:index + 65536] for index in range(0, len(output), 65536)] + [b""]),
                  203: deque([b""])}
        manifest = {"executable": {"sha256": "b" * 64}}
        with patch.object(runner, "package", return_value=(APP / "unused", manifest, {})), \
             patch.object(runner.subprocess, "Popen", return_value=process) as launch, \
             patch.object(runner.selectors, "DefaultSelector", _Selector), \
             patch.object(runner.os, "set_blocking"), \
             patch.object(runner.os, "write", side_effect=lambda _fd, data: len(data)), \
             patch.object(runner.os, "read", side_effect=lambda fd, _count: chunks[fd].popleft()), \
             patch.object(runner.time, "monotonic", side_effect=clock, return_value=0):
            instance = runner.VampireRunner(profile)
            result = instance("fof(goal,conjecture,(a = a)).\n")
        return instance, result, launch, process

    def test_runner_retains_exit_and_profile_for_normal_solver_timeout(self):
        for profile in policy.PROFILE_NAMES:
            with self.subTest(profile=profile):
                instance, result, launch, _ = self.run_mock_solver(profile, b"% Time limit reached! \n% Termination reason: Time limit\n")
                self.assertEqual(result["exit_code"], 1)
                self.assertEqual(result["status"], "timeout")
                self.assertEqual(result["termination"]["reason"], "solver_time_limit")
                self.assertEqual(result["profile"], profile)
                self.assertEqual(result["solver_args"], policy.solver_args(profile))
                self.assertTrue(result["executed"])
                self.assertEqual(instance.calls, 1)
                self.assertEqual(len(instance.records), 1)
                self.assertNotIn("stdout", instance.records[0])
                self.assertIn("Time limit", instance.records[0]["termination"]["evidence"][0]["text"])
                launch.assert_called_once_with(runner.spawn_argv(profile), cwd=str(APP), env=dict(runner.ENVIRONMENT),
                    stdin=runner.subprocess.PIPE, stdout=runner.subprocess.PIPE, stderr=runner.subprocess.PIPE,
                    close_fds=True, start_new_session=False)

    def test_outer_deadline_uses_selected_profile_not_standard(self):
        for profile in policy.PROFILE_NAMES:
            wall = policy.solver_limits(profile)["wall_seconds"]
            # Still below the selected deadline, then exactly at it. No sleeps.
            instance, result, _, process = self.run_mock_solver(profile, b"% waiting\n", code=-signal.SIGKILL,
                clock=[0, wall - 0.1, wall, wall], running=True)
            self.assertEqual(result["status"], "timeout")
            self.assertEqual(result["termination"]["reason"], "outer_wall_watchdog")
            self.assertIn(str(wall) + "-second", result["detail"])
            self.assertEqual(result["stdout"], "% waiting\n")
            self.assertEqual(result["exit_code"], -signal.SIGKILL)
            process.kill.assert_called_once_with()
            process.wait.assert_called_once_with(timeout=0.5)
            self.assertEqual(instance.calls, 1)

    def test_capture_bound_never_overshoots_or_accepts_truncated_proof(self):
        for payload in (b"x" * (policy.MAX_OUTPUT + 1), b"\xff" * policy.MAX_OUTPUT):
            instance, result, _, _ = self.run_mock_solver("research", payload, code=0)
            self.assertEqual(result["status"], "output_limit")
            self.assertTrue(result["output_limited"])
            self.assertLessEqual(len(result["stdout"].encode()) + len(result["stderr"].encode()), policy.MAX_OUTPUT)
            self.assertLessEqual(instance.records[0]["output_bytes"], policy.MAX_OUTPUT)
            self.assertEqual(result["exit_code"], 0)


if __name__ == "__main__":
    unittest.main()
