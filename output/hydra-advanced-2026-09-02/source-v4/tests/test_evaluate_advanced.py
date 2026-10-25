"""Only in-memory HTTP fixtures; no sockets, model, solver, or native replay."""
from pathlib import Path
import json
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import evaluate_advanced as runner


class FakeClient:
    def __init__(self, job=None, submit_error=None, poll_error=None):
        self.requests = []
        self.identifier = "a" * 32
        self.final = job
        self.submit_error = submit_error
        self.poll_error = poll_error

    def request(self, method, path, deadline, payload=None):
        self.requests.append((method, path, payload))
        if self.submit_error:
            raise self.submit_error
        return 202, {"ok": True, "job_id": self.identifier}

    def job(self, identifier, deadline):
        if self.poll_error:
            raise self.poll_error
        return {"id": identifier, **self.final}


class AdvancedRunnerTests(unittest.TestCase):
    def test_transport_normalization_precedes_strict_parser_and_original_is_retained(self):
        original = "forall n.\nn = n"
        seen = []
        def parse(text):
            seen.append(text)
            return "forall x. x = x"
        request, normalized, canonical = runner.prepare_request(
            {"theorem": original}, "hybrid", "deep", 32, 4, parse)
        self.assertEqual(seen, ["forall n. n = n"])
        self.assertEqual(request["theorem"], original)
        self.assertEqual(normalized["theorem"], seen[0])
        self.assertEqual(canonical, "forall x. x = x")

    def test_model_only_cannot_silently_use_deep_or_arbitrary_budgets(self):
        for mode, profile, calls, beam in (("model", "deep", 32, 4), ("hybrid", "deep", 9, 4),
                                           ("hybrid", "research", 64, 1)):
            with self.subTest(mode=mode, profile=profile), self.assertRaises(ValueError):
                runner.prepare_request({"theorem": "0=0"}, mode, profile, calls, beam, lambda s: s)

    def test_cleanup_reserves_cover_selected_solver_alarm(self):
        self.assertEqual([runner.cleanup_seconds(p) for p in ("standard", "deep", "research")], [8, 12, 22])

    def run_one(self, client):
        case = {"id": "test_case", "theorem": "0=0", "expected": "provable"}
        request, normalized, canonical = runner.prepare_request(case, "heuristic", "deep", 16, 4, lambda _: "0 = 0")
        with tempfile.TemporaryDirectory() as directory, patch.object(runner.signal, "setitimer"):
            path = Path(directory) / "case.json"
            record = runner.evaluate_one(client, case, request, normalized, canonical,
                path, time.monotonic()+30, {"plan_sha256": "b"*64, "source_pins_sha256": "c"*64})
            saved = json.loads(path.read_text())
            self.assertEqual(record, saved)
            return record

    def test_completed_search_saves_one_submission_and_separate_timings(self):
        result = {"status": "proved", "theorem": "0 = 0", "kernel_checked": True,
            "goals": [], "proof_nodes": 1, "commands": ["refl"],
            "search": {"model_calls": 0, "vampire_calls": 0, "elapsed_seconds": 0.2},
            "execution": {"elapsed_seconds": 0.3, "quiescent": True}}
        client = FakeClient({"state": "completed", "result": result, "elapsed_seconds": 0.4})
        record = self.run_one(client)
        self.assertEqual(record["outcome"], "proved")
        self.assertEqual(len(client.requests), 1)
        self.assertEqual(record["submission_count"], 1)
        self.assertEqual(record["request"]["theorem"], "0=0")
        self.assertEqual([record[k] for k in ("server_elapsed_seconds", "worker_elapsed_seconds", "search_elapsed_seconds")], [0.4, 0.3, 0.2])
        self.assertIsNone(record["metrics"]["values"]["states_expanded"])

    def test_lost_submission_response_is_not_retried_or_cancelled_without_owned_id(self):
        client = FakeClient(submit_error=runner.TransportError("lost response"))
        with patch.object(runner, "cancel_owned") as cancel:
            record = self.run_one(client)
        self.assertEqual(record["outcome"], "submission_outcome_unknown")
        self.assertTrue(record["stop_after_case"])
        self.assertEqual(len(client.requests), 1)
        cancel.assert_not_called()

    def test_poll_failure_cancels_only_the_owned_job(self):
        client = FakeClient(poll_error=runner.TransportError("poll failed"))
        cleanup = {"job_id": client.identifier, "terminal_observed": True,
                   "terminal_job": {"id": client.identifier, "state": "cancelled"}}
        with patch.object(runner, "cancel_owned", return_value=cleanup) as cancel:
            record = self.run_one(client)
        self.assertEqual(record["outcome"], "server_failure")
        self.assertEqual(cancel.call_args.args[:2], (client, client.identifier))
        self.assertEqual(len(client.requests), 1)

    def test_malformed_completed_result_is_retained_not_a_proof(self):
        record = self.run_one(FakeClient({"state": "completed", "result": ["not a result"]}))
        self.assertEqual(record["outcome"], "invalid_server_result")
        self.assertFalse(record["kernel_verified"])

    def test_aggregate_never_marks_partial_or_changed_source_run_complete(self):
        plan = {"jobs": [{"mode": "hybrid"}], "modes": ["hybrid"]}
        self.assertEqual(runner.aggregate(plan, [], time.monotonic(), pins_unchanged=True)["status"], "incomplete")
        record = {"search_mode": "hybrid", "outcome": "unknown", "record_file": "one.json",
                  "metrics": runner.metrics({})}
        self.assertEqual(runner.aggregate(plan, [record], time.monotonic(), pins_unchanged=False)["status"], "incomplete")
        self.assertEqual(runner.aggregate(plan, [record], time.monotonic(), pins_unchanged=True)["status"], "complete")


if __name__ == "__main__":
    unittest.main()
