"""Coordinator tests only: all worker results are explicit fabricated fixtures.

No models, native checker, subprocesses, network, or quality claims are involved.
"""
import copy
from pathlib import Path
import sys
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from portfolio_runtime import run_portfolio

ORIGINAL = "0=0"
CANONICAL = "0 = 0"
REQUEST = {"theorem": ORIGINAL, "search_mode": "portfolio", "search_profile": "portfolio",
           "model_id": "wmi-c6-vanilla47", "max_model_calls": 128, "beam_width": 1}


def result(phase="sequential", *, proved=False, **updates):
    symbolic = phase == "symbolic"
    value = {"kind": phase, "theorem": CANONICAL, "original_theorem": ORIGINAL,
             "kernel_source_commit": "fixture-native-source", "status": "proved" if proved else "exhausted" if symbolic else "unknown",
             "kernel_checked": proved, "goals": [] if proved else ["fixture remaining goal"],
             "proof_nodes": 1 if proved else None, "commands": ["refl"] if proved else [],
             "trace": [{"tactic": "refl", "status": "ok", "error": None},
                       {"qed": True, "theorem": CANONICAL, "tactic_count": 1, "proof_size": 1}] if proved else [],
             "model": {"name": "fixture model"}, "model_used": not symbolic,
             "vampire_used": symbolic, "proof_sources": {"heuristic" if symbolic else "model": 1} if proved else {},
             "search": {"model_calls": 0 if symbolic else 2, "vampire_calls": 1 if symbolic else 0,
                        "states_expanded": 3 if symbolic else 2, "tactic_attempts": 5 if symbolic else 2,
                        "forward_passes": 0 if symbolic else 4,
                        "generated_token_steps" if symbolic else "generated_token_slots": 0 if symbolic else 4,
                        "model_loaded": not symbolic, "accepted_model_steps": 1,
                        "stop_reason": "proved" if proved else "no_candidate",
                        "provenance": [{"source": "heuristic" if symbolic else "model"}] if proved else [],
                        "independent_replay": proved, "replay_evidence": {
                            "status": "completed", "actual_exit_code": 0, "child_process_id": 12345} if proved else None}}
    if not symbolic:
        value.update(proof_profile="sequential", native_admission={"input_theorem": ORIGINAL,
            "theorem": CANONICAL, "ast_metrics": {"maximum_bound_variables": 0}})
    value.update(updates)
    return value


def completion(value=None, **updates):
    outcome = {"result": value, "error": None, "cancelled": False, "elapsed_seconds": 2.0,
               "peak_sampled_rss_bytes": 20, "peak_sampled_solver_rss_bytes": 5,
               "quiescent": True, "worker_started": True, "worker_exit_code": 0}
    outcome.update(updates)
    return outcome


class FakeWorker:
    def __init__(self, outputs, *, cancel_on=None, cancel_event=None, durations=None, raises=False):
        self.outputs = outputs
        self.requests = []
        self.now = 0.0
        self.cancel_on = cancel_on
        self.cancel_event = cancel_event
        self.durations = durations or [2.0] * len(outputs)
        self.raises = raises

    def __call__(self, mode, request, cancel, progress):
        self.requests.append((mode, copy.deepcopy(request), cancel))
        if self.raises:
            raise RuntimeError("fixture callback failure before cleanup")
        i = len(self.requests) - 1
        self.now += self.durations[i]
        progress({"phase": "fixture", "model_calls": 0})
        if self.cancel_on == i:
            self.cancel_event.set()
        return copy.deepcopy(self.outputs[i])


class PortfolioTests(unittest.TestCase):
    def invoke(self, worker, cancel=None, progress=lambda _: None, request=None):
        return run_portfolio(copy.deepcopy(request or REQUEST), cancel or threading.Event(), progress,
                             run_worker=worker, clock=lambda: worker.now)

    def test_model_proof_stops_and_preserves_extended_replay(self):
        native = result(proved=True)
        worker = FakeWorker([completion(native)])
        outcome = self.invoke(worker)
        self.assertIsNone(outcome["error"])
        self.assertEqual(len(worker.requests), 1)
        actual = outcome["result"]
        self.assertEqual(actual["kind"], "portfolio")
        self.assertEqual(actual["settings_profile"], "portfolio")
        self.assertEqual(actual["proof_profile"], "sequential")
        self.assertEqual(actual["trace"], native["trace"])
        self.assertEqual(actual["portfolio"]["winner"], "sequential")
        self.assertEqual(actual["proof_sources"], {"model": 1})

    def test_symbolic_winner_starts_original_and_counts_work_not_proof_credit(self):
        symbolic = result("symbolic", proved=True)
        symbolic["search"].update(model_used=False, vampire_used=True,
                                  model_advisor_calls=0, generated_token_steps=0)
        worker = FakeWorker([completion(result()), completion(symbolic, peak_sampled_rss_bytes=30)])
        events = []
        cancel = threading.Event()
        outcome = self.invoke(worker, cancel, events.append)
        self.assertIsNone(outcome["error"])
        self.assertEqual(worker.requests[0][1]["model_id"], REQUEST["model_id"])
        self.assertEqual(worker.requests[1][1], {"theorem": ORIGINAL, "search_mode": "symbolic",
            "search_profile": "standard", "max_model_calls": 16, "beam_width": 4})
        self.assertTrue(all(row[2] is cancel for row in worker.requests))
        actual = outcome["result"]
        self.assertEqual(actual["trace"], symbolic["trace"])
        self.assertEqual(actual["proof_sources"], {"heuristic": 1})
        self.assertEqual(actual["search"]["model_calls"], 2)
        self.assertEqual(actual["search"]["vampire_calls"], 1)
        self.assertEqual(actual["search"]["tactic_attempts"], 7)
        self.assertEqual(actual["search"]["generated_token_slots"], 4)
        self.assertEqual(actual["search"]["forward_passes"], 4)
        self.assertEqual(actual["portfolio"]["phases"][1]["search_counters"]["model_calls"], 0)
        self.assertFalse(actual["portfolio"]["phases"][1]["search_counters"]["model_used"])
        self.assertEqual(actual["portfolio"]["winner"], "symbolic")
        self.assertEqual(actual["model"]["name"], "fixture model")
        self.assertTrue(actual["model_used"])
        self.assertTrue(actual["search"]["model_used"])
        self.assertTrue(actual["vampire_used"])
        self.assertTrue(actual["search"]["vampire_used"])
        self.assertEqual(actual["search"]["model_advisor_calls"], 0)
        self.assertEqual(actual["search"]["generated_token_steps"], 0)
        self.assertEqual(actual["search"]["diagnostic_scope"]["other_fields_phase"], "symbolic")
        self.assertFalse(actual["search"]["diagnostic_scope"]["other_fields_are_aggregate"])
        self.assertIn("model_used", actual["search"]["diagnostic_scope"]["aggregate_fields"])
        self.assertNotIn("model_advisor_calls", actual["search"]["diagnostic_scope"]["aggregate_fields"])
        self.assertFalse(symbolic["search"]["model_used"])
        self.assertEqual(outcome["peak_sampled_rss_bytes"], 30)
        self.assertIsNone(outcome["worker_exit_code"])
        self.assertEqual(events[-1]["model_calls"], 2)
        self.assertNotIn("proof_profile", actual)

    def test_symbolic_win_preserves_model_repeat_stop_without_proof_credit(self):
        guard = {"schema": "hydra-web-repeated-state-guard-v1", "enabled": True,
                 "stop_reason": "repeated_state", "blocked_provider_requests": 1,
                 "repeats": [{"first_visit": 1, "repeated_visit": 3}], "is_disproof": False}
        primary = result()
        primary["search"]["repeated_state_guard"] = copy.deepcopy(guard)
        symbolic = result("symbolic", proved=True)
        outcome = self.invoke(FakeWorker([completion(primary), completion(symbolic)]))
        self.assertIsNone(outcome["error"])
        actual = outcome["result"]
        self.assertEqual(actual["portfolio"]["winner"], "symbolic")
        self.assertEqual(actual["portfolio"]["phases"][0]["stop_reason"], "no_candidate")
        for phases in (actual["portfolio"]["phases"], outcome["portfolio_phases"]):
            self.assertEqual(phases[0]["repeated_state_guard"], guard)
            self.assertEqual(phases[0]["repeated_state_guard"]["blocked_provider_requests"], 1)
            self.assertIsNone(phases[1]["repeated_state_guard"])
        self.assertEqual(actual["search"]["portfolio_model_repeated_state_guard"], guard)
        self.assertEqual(actual["search"]["stop_reason"], "proved")
        self.assertEqual(actual["search"]["model_calls"], 2)
        self.assertEqual(actual["search"]["forward_passes"], 4)
        self.assertEqual(actual["search"]["generated_token_slots"], 4)
        self.assertEqual(actual["proof_sources"], {"heuristic": 1})
        self.assertEqual(actual["trace"], symbolic["trace"])
        self.assertEqual(actual["commands"], symbolic["commands"])
        self.assertTrue(actual["kernel_checked"])
        self.assertTrue(outcome["quiescent"])
        actual["search"]["portfolio_model_repeated_state_guard"]["blocked_provider_requests"] = 99
        self.assertEqual(primary["search"]["repeated_state_guard"], guard)
        self.assertEqual(actual["portfolio"]["phases"][0]["repeated_state_guard"], guard)

    def test_both_unknown_keeps_primary_partial_trace_no_winning_credit(self):
        primary = result(trace=[{"tactic": "intro", "status": "ok"}], commands=["intro"])
        outcome = self.invoke(FakeWorker([completion(primary), completion(result("symbolic"))]))
        actual = outcome["result"]
        self.assertEqual(actual["trace"], primary["trace"])
        self.assertEqual(actual["commands"], ["intro"])
        self.assertFalse(actual["kernel_checked"])
        self.assertEqual(actual["proof_sources"], {})
        self.assertIsNone(actual["portfolio"]["winner"])
        self.assertEqual(actual["portfolio"]["fallback"]["status"], "unknown")

    def test_large_native_admission_skips_only_legacy_fallback(self):
        primary = result()
        primary["native_admission"]["ast_metrics"]["maximum_bound_variables"] = 20
        worker = FakeWorker([completion(primary)])
        outcome = self.invoke(worker)
        self.assertEqual(len(worker.requests), 1)
        self.assertIsNone(outcome["error"])
        self.assertEqual(outcome["result"]["portfolio"]["fallback"]["status"], "unavailable")

    def test_actual_legacy_admission_rejection_keeps_unknown_and_actual_exit(self):
        worker = FakeWorker([completion(result()), completion(error="formula/term source exceeds the 512-token limit",
                                                               worker_exit_code=2)])
        outcome = self.invoke(worker)
        self.assertIsNone(outcome["error"])
        self.assertEqual(outcome["result"]["portfolio"]["fallback"]["status"], "unavailable")
        self.assertEqual(outcome["portfolio_phases"][1]["execution"]["worker_exit_code"], 2)

    def test_unrecognized_symbolic_failure_is_not_admission_unavailability(self):
        outcome = self.invoke(FakeWorker([completion(result()), completion(error="fixture solver unavailable", worker_exit_code=2)]))
        self.assertIsNone(outcome["error"])
        self.assertEqual(outcome["result"]["portfolio"]["fallback"]["status"], "failed")
        self.assertFalse(outcome["result"]["kernel_checked"])
        self.assertIsNone(outcome["result"]["vampire_used"])
        self.assertIsNone(outcome["result"]["search"]["vampire_used"])
        self.assertIsNone(outcome["result"]["search"]["vampire_calls"])
        self.assertIsNone(outcome["result"]["vampire_used"])
        self.assertEqual(outcome["result"]["search"]["model_calls"], 2)
        self.assertEqual(outcome["result"]["search"]["forward_passes"], 4)
        self.assertFalse(outcome["result"]["portfolio"]["component_accounting_complete"])

    def test_primary_infrastructure_and_internal_errors_never_fall_back(self):
        internal = result()
        internal["search"]["stop_reason"] = "error"
        for value in (completion(error="fixture load error", worker_exit_code=2), completion(internal)):
            worker = FakeWorker([value])
            outcome = self.invoke(worker)
            self.assertEqual(len(worker.requests), 1)
            self.assertIsNone(outcome["result"])
            self.assertTrue(outcome["error"])

    def test_unconfirmed_cleanup_stops_and_blocks_new_work(self):
        for outputs in ([completion(error="fixture cleanup", quiescent=False, worker_exit_code=None)],
                        [completion(result()), completion(error="fixture cleanup", quiescent=False, worker_exit_code=None)]):
            worker = FakeWorker(outputs)
            outcome = self.invoke(worker)
            self.assertEqual(len(worker.requests), len(outputs))
            self.assertIsNone(outcome["result"])
            self.assertFalse(outcome["quiescent"])
            self.assertTrue(outcome["error"])

    def test_cancellation_before_start_and_after_either_proof_suppresses_result(self):
        cancel = threading.Event()
        cancel.set()
        worker = FakeWorker([])
        outcome = self.invoke(worker, cancel)
        self.assertTrue(outcome["cancelled"])
        self.assertFalse(worker.requests)
        for outputs in ([completion(result(proved=True))],
                        [completion(result()), completion(result("symbolic", proved=True))]):
            cancel = threading.Event()
            worker = FakeWorker(outputs, cancel_on=len(outputs)-1, cancel_event=cancel)
            outcome = self.invoke(worker, cancel)
            self.assertTrue(outcome["cancelled"])
            self.assertIsNone(outcome["result"])

    def test_cancellation_between_phases_does_not_launch_symbolic(self):
        cancel = threading.Event()
        worker = FakeWorker([completion(result())])
        def progress(event):
            if event.get("portfolio_phase") == "symbolic":
                cancel.set()
        outcome = self.invoke(worker, cancel, progress)
        self.assertEqual(len(worker.requests), 1)
        self.assertTrue(outcome["cancelled"])

    def test_callback_exception_does_not_assume_cleanup(self):
        outcome = self.invoke(FakeWorker([], raises=True))
        self.assertFalse(outcome["quiescent"])
        self.assertIsNone(outcome["result"])

    def test_late_completion_never_publishes_a_proof(self):
        worker = FakeWorker([completion(result(proved=True))], durations=[551])
        outcome = self.invoke(worker)
        self.assertIsNone(outcome["result"])
        self.assertIn("whole wall", outcome["error"])

    def test_fallback_requires_its_full_worker_allowance(self):
        worker = FakeWorker([completion(result())], durations=[371])
        outcome = self.invoke(worker)
        self.assertEqual(len(worker.requests), 1)
        self.assertEqual(outcome["result"]["portfolio"]["fallback"]["reason"], "insufficient_whole_wall_budget")

    def test_mismatched_theorem_invalid_replay_or_model_in_symbolic_is_rejected(self):
        for change in ("theorem", "proof", "model"):
            bad = result("symbolic", proved=True)
            if change == "theorem":
                bad["theorem"] = "0 = 1"
            elif change == "proof":
                bad["trace"][-1]["qed"] = False
            else:
                bad["search"]["model_calls"] = 1
            outcome = self.invoke(FakeWorker([completion(result()), completion(bad)]))
            self.assertIsNone(outcome["result"])
            self.assertTrue(outcome["error"])

    def test_nonfixed_budget_rejected_without_a_worker(self):
        request = {**REQUEST, "max_model_calls": 64}
        worker = FakeWorker([])
        outcome = self.invoke(worker, request=request)
        self.assertIsNone(outcome["result"])
        self.assertTrue(outcome["error"])
        self.assertFalse(worker.requests)


if __name__ == "__main__":
    unittest.main()
