"""HTTP validation and owned-worker lifecycle tests, without network listeners."""
from __future__ import annotations

from email.message import Message
import io
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import server
import worker


class InMemoryHandler(server.Handler):
    """Exercise real handler methods without creating a socket."""
    def __init__(self, path="/api/replay", body=b"{}", **headers):
        self.path = path
        self.server = SimpleNamespace(server_port=8765, csrf_token="test-token", jobs=server.Jobs())
        self.headers = Message()
        for name, value in {"Host": "127.0.0.1:8765", "Origin": "http://127.0.0.1:8765",
                            "Content-Length": str(len(body)), "Content-Type": "application/json",
                            **headers}.items():
            self.headers[name] = value
        self.rfile = io.BytesIO(body)
        self.response = None

    def _json(self, value, status=200):
        self.response = status, value


class HttpValidationTests(unittest.TestCase):
    def test_heuristic_mode_does_not_require_model_or_vampire_readiness(self):
        body = worker.json_bytes({"theorem": "0=0", "max_model_calls": 8, "beam_width": 1,
                                  "search_mode": "heuristic"})
        handler = InMemoryHandler(path="/api/search", body=body, **{"X-CSRF-Token": "test-token"})
        with patch.object(server, "metadata_status", side_effect=AssertionError("model must not be consulted")), \
             patch.object(server, "vampire_status", side_effect=AssertionError("solver must not be consulted")), \
             patch.object(handler.server.jobs, "start", return_value="example") as start:
            handler.do_POST()
        self.assertEqual(handler.response[0], 202)
        self.assertEqual(start.call_args.args[0]["search_mode"], "heuristic")

    def test_exact_loopback_origin_and_csrf_are_required(self):
        server.validate_origin("127.0.0.1:8765", "http://127.0.0.1:8765", 8765)
        server.validate_origin("localhost:8765", None, 8765)
        for host, origin in (("evil.example:8765", None), ("127.0.0.1:8766", None),
                             ("127.0.0.1:8765", "https://127.0.0.1:8765"),
                             ("127.0.0.1:8765", "http://evil.example")):
            with self.subTest(host=host, origin=origin), self.assertRaises(server.RequestError):
                server.validate_origin(host, origin, 8765)
        for actual in (None, "wrong", "\u0100"):
            with self.assertRaises(server.RequestError):
                server.validate_token(actual, "test-token")
        handler = InMemoryHandler()
        handler.do_POST()
        self.assertEqual(handler.response[0], 403)

    def test_body_length_and_header_ambiguity_fail_before_worker(self):
        for name, value in (("Content-Length", "65537"), ("Content-Length", "-1"),
                            ("Transfer-Encoding", "chunked"), ("Content-Type", "text/plain")):
            with self.subTest(name=name, value=value), self.assertRaises(server.RequestError):
                InMemoryHandler(**{name: value})._body()
        handler = InMemoryHandler()
        handler.headers["Content-Length"] = "2"
        with self.assertRaises(server.RequestError):
            handler._body()
        handler = InMemoryHandler()
        handler.headers["Origin"] = "http://evil.example"
        with self.assertRaises(server.RequestError):
            handler._origin()

    def test_static_routes_do_not_expose_project_or_runtime_files(self):
        for path in ("/../RECOVERY.md", "/.runtime/model/manifest.json", "/worker.py", "/api/unknown"):
            with self.subTest(path=path):
                handler = InMemoryHandler(path=path)
                handler.do_GET()
                self.assertEqual(handler.response[0], 404)
        with self.assertRaises(ValueError):
            server.Server(("0.0.0.0", 8765))  # Rejected before socket creation.


class OwnershipTests(unittest.TestCase):
    def test_unseen_orphan_does_not_make_a_group_look_quiescent(self):
        rows = {101: (1, 100, 2048, ("previously-unseen-solver",))}
        self.assertEqual(server.owned_processes(rows, 100, {100: ("gone-root",)}), {})
        self.assertFalse(server.group_is_empty(rows, 100))
        self.assertTrue(server.group_is_empty({}, 100))

    def test_recycled_leader_is_not_adopted_or_signalled(self):
        old, new = ("old-birth",), ("new-birth",)
        rows = {100: (1, 100, 1024, new)}
        self.assertEqual(server.owned_processes(rows, 100, {100: old}), {})
        self.assertEqual(server.owned_processes(rows, 100, {}), {})
        with patch.object(server, "process_snapshot", return_value=rows), patch.object(server.os, "killpg") as kill:
            server._kill(SimpleNamespace(pid=100, returncode=0), {100: old})
        kill.assert_not_called()

    def test_unreaped_worker_is_killed_even_if_accounting_fails(self):
        with patch.object(server, "process_snapshot", side_effect=RuntimeError("ps denied")), \
             patch.object(server.os, "killpg") as kill:
            with self.assertRaises(RuntimeError):
                server._kill(SimpleNamespace(pid=100, returncode=None), {})
        kill.assert_called_once_with(100, signal.SIGKILL)

    def test_live_descendant_requires_a_matching_owned_birth(self):
        birth = ("original",)
        rows = {100: (1, 100, 1024, birth), 101: (100, 100, 2048, ("child",))}
        self.assertEqual(set(server.owned_processes(rows, 100, {}, unreaped=True)), {100, 101})
        self.assertEqual(server.owned_processes(rows, 100, {100: ("different",)}), {})


class JobLifecycleTests(unittest.TestCase):
    def test_only_one_job_and_cancellation_waits_for_quiescence(self):
        entered, allow_cleanup = threading.Event(), threading.Event()

        def controlled_worker(mode, request, cancel, progress):
            entered.set()
            self.assertTrue(cancel.wait(2))
            self.assertTrue(allow_cleanup.wait(2))
            return {"result": None, "error": None, "cancelled": True, "quiescent": True}

        jobs = server.Jobs()
        with patch.object(server, "run_worker", side_effect=controlled_worker):
            identifier = jobs.start({"theorem": "0 = 0", "max_model_calls": 8, "beam_width": 1})
            self.assertTrue(entered.wait(2))
            jobs.cancel_job(identifier)
            with self.assertRaises(server.RequestError) as caught:
                jobs.start({})
            self.assertEqual(caught.exception.status, 409)
            self.assertNotEqual(jobs.get(identifier)["state"], "cancelled")
            allow_cleanup.set()
            jobs.threads[0].join(timeout=2)
            self.assertFalse(jobs.threads[0].is_alive())
            self.assertEqual(jobs.get(identifier)["state"], "cancelled")
            self.assertIsNone(jobs.get(identifier)["result"])
        jobs.close()

    def test_unconfirmed_cleanup_blocks_future_computation(self):
        jobs = server.Jobs()
        outcome = {"result": None, "error": "cleanup unavailable", "cancelled": False, "quiescent": False}
        with patch.object(server, "run_worker", return_value=outcome):
            self.assertEqual(jobs.replay({}), outcome)
        with self.assertRaises(server.RequestError) as caught:
            jobs.start({})
        self.assertEqual(caught.exception.status, 503)
        with self.assertRaisesRegex(RuntimeError, "unconfirmed worker cleanup"):
            jobs.close()


class BoundedProcessTests(unittest.TestCase):
    """Actual owned child processes only; fixtures do not run models or proofs."""
    def fixture(self, source, cancel=None, progress=lambda _: None, search_mode="model", search_profile="standard"):
        with tempfile.TemporaryDirectory(prefix="hydra-playground-worker-test-") as directory:
            path = Path(directory) / "fixture.py"
            path.write_text(source, encoding="utf-8")
            with patch.object(server, "WORKER", path):
                return server.run_worker("search", {"theorem": "0 = 0",
                                                     "max_model_calls": 8 if search_profile == "standard" else 32,
                                                     "beam_width": 1 if search_profile == "standard" else 8,
                                                     "search_mode": search_mode, "search_profile": search_profile},
                                         cancel or threading.Event(), progress)

    def test_pre_exit_result_is_not_accepted_after_nonzero_exit(self):
        result = self.fixture('import sys\nprint(\'{"type":"result","result":{"kernel_checked":false,"trace":[]}}\', flush=True)\nsys.exit(2)\n')
        self.assertIsNone(result["result"])
        self.assertTrue(result["quiescent"], result)
        self.assertIn("exit 2", result["error"])

    def test_running_worker_is_cancelled_and_reaped(self):
        cancel = threading.Event()
        started = time.monotonic()
        result = self.fixture('import time\nprint(\'{"type":"progress","progress":{"phase":"fixture"}}\', flush=True)\ntime.sleep(30)\n',
                              cancel, lambda _: cancel.set())
        self.assertLess(time.monotonic() - started, 8)
        self.assertTrue(result["cancelled"], result)
        self.assertTrue(result["quiescent"], result)
        self.assertIsNone(result["result"])

    def test_output_overflow_fails_and_cleans_up(self):
        result = self.fixture('import os\nos.write(1, b"x" * 2200000)\n')
        self.assertIsNone(result["result"])
        self.assertTrue(result["quiescent"], result)
        self.assertIn("byte limit", result["error"])

    def test_hybrid_cancellation_reaps_its_one_solver_descendant(self):
        cancel = threading.Event()
        source = ('import subprocess,sys,time\n'
                  'child=subprocess.Popen([sys.executable,"-I","-B","-c","import time;time.sleep(30)"])\n'
                  'print(\'{"type":"progress","progress":{"phase":"solver-running"}}\',flush=True)\n'
                  'time.sleep(30)\n')
        for profile in ("standard", "deep", "research"):
            with self.subTest(profile=profile):
                cancel.clear()
                result = self.fixture(source, cancel, lambda _: cancel.set(), search_mode="hybrid",
                                      search_profile=profile)
                self.assertTrue(result["cancelled"], result)
                self.assertTrue(result["quiescent"], result)
                self.assertIsNone(result["result"])

    def test_model_only_cannot_launch_a_solver_descendant(self):
        source = ('import subprocess,sys,time\n'
                  'child=subprocess.Popen([sys.executable,"-I","-B","-c","import time;time.sleep(30)"])\n'
                  'time.sleep(30)\n')
        result = self.fixture(source)
        self.assertIsNone(result["result"])
        self.assertTrue(result["quiescent"], result)
        self.assertIn("unauthorized", result["error"])


if __name__ == "__main__":
    unittest.main()
