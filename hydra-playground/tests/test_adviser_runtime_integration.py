"""Pure adviser/controller/worker boundaries; every process call is a mock.

No native engine or CAS/SMT/model framework is imported. This checks admission,
budget accounting and the worker audit callback without installing that audit
hook, launching a child, allocating a model or checking a theorem.
"""
from collections import Counter
from pathlib import Path
import stat
import sys
import threading
import time
from types import SimpleNamespace
import unittest
from unittest import mock

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import adviser_process
import adviser_runtime
import experimental_runtime
import server
import vampire_process
import worker
from adviser_protocol import AdviserSession, ProtocolError, RequestLease, canonical_json, external_request


def request(backend="vampire"):
    return external_request(backend, b"fixture-only-input", canonical_json({
        "schema": "hydra-adviser-semantic-context-v1", "fixture": True}),
        {"backend": backend, "profile": "deep", "version": "fixture"})


def execution(req, *, launched=False, cached=False):
    return {"executed": launched, "status": "cached_unsuccessful" if cached else "unavailable",
        "exit_code": 0 if launched else None, "problem_sha256": req.input_sha256, "elapsed_seconds": 0.001}


def pool_fixture():
    pool = adviser_runtime.AdviserPool.__new__(adviser_runtime.AdviserPool)
    pool.session = AdviserSession(deadline=time.monotonic() + 100)
    pool.identity = "a" * 64
    pool.requests = 0
    pool.by_backend = Counter()
    runner = SimpleNamespace(calls=0, records=[])
    adviser = SimpleNamespace(advise=mock.Mock(return_value={"status": "unsupported",
        "suggestions": [], "kernel_checked": False, "solver": {"invocations": 0}}))
    pool.runners, pool.advisors = {"sympy": runner}, {"sympy": adviser}
    return pool, adviser, runner


class SharedControllerTests(unittest.TestCase):
    def test_all_five_backends_share_twelve_requests_without_starvation(self):
        pool, _, _ = pool_fixture()
        for name in ("cvc5", "egg", "e", "vampire"):
            pool.runners[name] = SimpleNamespace(calls=0, records=[])
            pool.advisors[name] = SimpleNamespace(advise=mock.Mock(return_value={
                "status":"unsupported", "suggestions":[], "solver":{"invocations":0}}))
        for _ in range(8):
            pool.request("sympy", object())
        self.assertFalse(pool.can_request_for("sympy"))
        for name in ("cvc5", "egg", "e", "vampire"):
            self.assertTrue(pool.can_request_for(name))
            pool.request(name, object())
        self.assertEqual(pool.requests, 12)
        self.assertFalse(pool.can_request)
        self.assertEqual(pool.by_backend, {"sympy":8, "cvc5":1, "egg":1, "e":1, "vampire":1})

    def test_early_arithmetic_keeps_one_opportunity_for_deferred_vampire(self):
        pool, advisor, runner = pool_fixture()
        for backend in ("cvc5","vampire"):
            pool.runners[backend]=SimpleNamespace(calls=0,records=[])
            pool.advisors[backend]=SimpleNamespace(advise=mock.Mock(return_value={
                "status":"unsupported","suggestions":[],"solver":{"invocations":0}}))
        for _ in range(10):
            self.assertTrue(pool.can_request_for("sympy"))
            pool.request("sympy",object())
        self.assertFalse(pool.can_request_for("sympy"))
        self.assertTrue(pool.can_request_for("cvc5"))
        pool.request("cvc5",object())
        self.assertFalse(pool.can_request_for("sympy"))
        self.assertFalse(pool.can_request_for("cvc5"))
        self.assertTrue(pool.can_request_for("vampire"))
        pool.request("vampire",object())
        self.assertEqual(pool.requests,12)
        self.assertFalse(pool.can_request)
        self.assertEqual(pool.by_backend,{"sympy":10,"cvc5":1,"vampire":1})

    def test_unsupported_requests_spend_controller_budget_without_invented_launches(self):
        pool, advisor, runner = pool_fixture()
        for _ in range(12):
            self.assertEqual(pool.request("sympy", object())["status"], "unsupported")
        self.assertFalse(pool.can_request)
        self.assertEqual(pool.request("sympy", object())["status"], "shared_budget_stop")
        self.assertEqual(advisor.advise.call_count, 12)
        report = pool.report()
        self.assertEqual(report["controller_requests"], 12)
        self.assertEqual(report["requests_by_backend"], {"sympy": 12})
        self.assertEqual(report["shared"]["actual_launches"], runner.calls)
        self.assertEqual(report["shared"]["requests"], 0)

    def test_unknown_ownership_blocks_more_work_and_is_not_reported_as_zero(self):
        pool, _, _ = pool_fixture()
        with pool.session.lease(request("sympy")):
            pass
        self.assertFalse(pool.can_request)
        report = pool.report()["shared"]
        self.assertFalse(report["accounting_complete"])
        self.assertIsNone(report["actual_launches"])
        self.assertIsNotNone(report["active_request"])

    def test_controller_rejects_disagreement_with_actual_runner_count(self):
        pool, _, runner = pool_fixture()
        runner.calls = 1
        with self.assertRaisesRegex(ProtocolError, "disagree"):
            pool.report()

    def test_zero_launch_cache_record_needs_no_dispatch(self):
        session = AdviserSession(deadline=time.monotonic() + 100)
        req = request()
        with session.lease(req) as lease:
            lease.record_external(execution(req, cached=True), cache_hit=True, quiescent=True)
        report = session.report()
        self.assertEqual((report["requests"], report["actual_launches"], report["cache_hits"]), (1, 0, 1))
        self.assertIsNone(report["active_request"])


class DispatchBoundaryTests(unittest.TestCase):
    def captured(self):
        req = request()
        session = AdviserSession(deadline=time.monotonic() + 100)
        runner = mock.Mock(return_value=execution(req, launched=True))
        runner.profile = "deep"
        capture = adviser_runtime._CapturedVampireRunner(runner)
        capture.lease = session.lease(req)
        self.addCleanup(capture.lease.__exit__, None, None, None)
        return req, session, runner, capture

    def test_vampire_capture_rejects_wrong_exact_input_before_call(self):
        _, _, runner, capture = self.captured()
        with self.assertRaises(ProtocolError):
            capture("different-input")
        runner.assert_not_called()

    def test_vampire_capture_consumes_one_dispatch_per_live_lease(self):
        req, _, runner, capture = self.captured()
        capture(req.data.decode())
        with self.assertRaises(ProtocolError):
            capture(req.data.decode())
        self.assertEqual(runner.call_count, 1)

    def test_vampire_capture_rejects_unadmitted_lease(self):
        req = request()
        session = AdviserSession(deadline=time.monotonic() + 100)
        runner = mock.Mock(return_value=execution(req, launched=True))
        runner.profile = "deep"
        capture = adviser_runtime._CapturedVampireRunner(runner)
        capture.lease = RequestLease(session, req, 1, time.monotonic())
        with self.assertRaises(ProtocolError):
            capture(req.data.decode())
        runner.assert_not_called()

    def test_failed_helper_popen_attempt_cannot_retry_same_lease(self):
        req = request("sympy")
        session = AdviserSession(deadline=time.monotonic() + 100)
        runner = adviser_process.AdviserRunner("sympy")
        with session.lease(req) as lease, \
                mock.patch.object(adviser_process.AdviserRunner, "identity", new_callable=mock.PropertyMock,
                    return_value={"backend": "sympy", "profile": "deep", "version": "fixture"}), \
                mock.patch.object(adviser_process, "package"), \
                mock.patch.object(vampire_process, "_resident_size", return_value=1024), \
                mock.patch.object(adviser_process.sys, "version_info", (3, 11, 0)), \
                mock.patch.object(adviser_process.sys, "platform", "darwin"), \
                mock.patch.object(adviser_process.os, "uname", return_value=SimpleNamespace(machine="arm64")), \
                mock.patch.object(adviser_process.subprocess, "Popen", side_effect=OSError("mock launch refused")) as popen:
            result = runner(lease)
            self.assertFalse(result["executed"])
            with self.assertRaises(ProtocolError):
                runner(lease)
            self.assertEqual(popen.call_count, 1)
            lease.record_external(result, quiescent=True)
        self.assertEqual(runner.calls, 0)
        self.assertEqual(session.report()["actual_launches"], 0)


class WorkerAuthorityTests(unittest.TestCase):
    def test_p9_selection_does_not_authorize_other_helpers_or_native_exec(self):
        options = experimental_runtime.selection({"advisers":["egg", "e"]},
            mode="search", search_mode="heuristic")
        self.assertEqual(options["advisers"], ["e", "egg"])
        with mock.patch.object(worker.sys, "addaudithook") as register:
            worker.install_guard("search", vampire_profile="deep", allowed_advisers=("egg", "e"))
        audit = register.call_args.args[0]
        for name in ("egg", "e"):
            audit("subprocess.Popen", (sys.executable, adviser_process.spawn_argv(name),
                str(APP), adviser_process.ENVIRONMENT))
        with self.assertRaises(RuntimeError):
            audit("subprocess.Popen", (sys.executable, adviser_process.spawn_argv("sympy"),
                str(APP), adviser_process.ENVIRONMENT))
        with self.assertRaises(RuntimeError):
            audit("os.exec", ("/bin/sh", ["/bin/sh"], {}))

    def test_options_are_explicit_and_new_advisers_require_deep(self):
        self.assertIsNone(experimental_runtime.selection(None, mode="search", search_mode="model"))
        request_value = {"theorem": "0=0", "max_model_calls": 32, "beam_width": 4,
            "search_mode": "heuristic", "search_profile": "deep",
            "experimental": {"lemmas": False, "ranker": "linear-v1", "advisers": ["sympy", "cvc5"]}}
        normalized = worker.validate_request("search", request_value)
        self.assertEqual(normalized["experimental"]["advisers"], ["cvc5", "sympy"])
        for changed in ({"search_mode": "hybrid"}, {"search_mode": "model"},
                {"search_profile": "standard", "max_model_calls": 16},
                {"experimental": {"advisers": ["sympy", "sympy"]}},
                {"experimental": {"advisers": ["arbitrary"]}}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                worker.validate_request("search", {**request_value, **changed})

    def test_audit_allows_only_selected_exact_helper_shape(self):
        with mock.patch.object(worker.sys, "addaudithook") as register:
            worker.install_guard("search", allow_vampire=True, vampire_profile="deep", allowed_advisers=("sympy",))
        audit = register.call_args.args[0]
        allowed = (sys.executable, adviser_process.spawn_argv("sympy"), str(APP), adviser_process.ENVIRONMENT)
        audit("subprocess.Popen", allowed)
        denied = [
            (sys.executable, adviser_process.spawn_argv("cvc5"), str(APP), adviser_process.ENVIRONMENT),
            (allowed[0], [*allowed[1], "--extra"], allowed[2], allowed[3]),
            (allowed[0], allowed[1], "/tmp", allowed[3]),
            (allowed[0], allowed[1], allowed[2], {**allowed[3], "PYTHONPATH": "/tmp"})]
        for args in denied:
            with self.assertRaises(RuntimeError):
                audit("subprocess.Popen", args)
        with self.assertRaises(OSError):
            audit("socket.__new__", ())
        with self.assertRaises(PermissionError):
            audit("open", ("/tmp/forbidden-output", "w", 0))
        with mock.patch.object(worker.os, "fstat", return_value=SimpleNamespace(st_mode=stat.S_IFIFO)):
            audit("open", (101, "wb", 0))
        with mock.patch.object(worker.os, "fstat", return_value=SimpleNamespace(st_mode=stat.S_IFREG)):
            with self.assertRaises(PermissionError):
                audit("open", (101, "wb", 0))

    def test_parent_accounts_for_helper_even_when_search_has_no_vampire(self):
        value = {"theorem": "0=0", "max_model_calls": 32, "beam_width": 4,
                 "search_mode": "heuristic", "search_profile": "deep"}
        for advisers, expected in ((None, 0), (["sympy"], 1)):
            request_value = dict(value)
            if advisers is not None:
                request_value["experimental"] = {"lemmas": False, "advisers": advisers}
            with mock.patch.object(server, "process_snapshot", return_value={}), \
                    mock.patch.object(server.selectors, "DefaultSelector"), \
                    mock.patch.object(worker, "solver_limits", wraps=worker.solver_limits) as bounds, \
                    mock.patch.object(server.subprocess, "Popen", side_effect=OSError("mock: no worker launched")):
                result = server.run_worker("search", request_value, threading.Event())
            self.assertEqual(bounds.call_count, expected)
            self.assertFalse(result["worker_started"])
            self.assertTrue(result["quiescent"])
            self.assertIsNone(result["result"])


if __name__ == "__main__":
    unittest.main()
