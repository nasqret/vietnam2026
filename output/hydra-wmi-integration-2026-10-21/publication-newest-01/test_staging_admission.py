"""Synthetic receipt fixtures only; no network, native replay, model or publication."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

PATH = Path(__file__).with_name("stage_http_model_proof.py")
spec = importlib.util.spec_from_file_location("hydra_staging_admission_fixture", PATH)
publisher = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = publisher
spec.loader.exec_module(publisher)


def fixture():
    request = {"theorem": "0=0", "model_id": publisher.MODEL_ID, "search_mode": "portfolio",
               "search_profile": "portfolio", "max_model_calls": 128, "beam_width": 1}
    model = {"selection_id": publisher.MODEL_ID, "checkpoint_sha256": publisher.CHECKPOINT,
             "exported_adapter_sha256": publisher.EXPORT, "selected_step": 16384}
    native_execution = {"error": None, "cancelled": False, "elapsed_seconds": 1.0,
        "peak_sampled_rss_bytes": 1, "peak_sampled_solver_rss_bytes": 1,
        "quiescent": True, "worker_started": True, "worker_exit_code": 0}
    phase = {"phase": "sequential", "request": {**request, "search_mode": "sequential", "search_profile": "sequential"},
             "execution": native_execution}
    execution = {**native_execution, "worker_exit_code": None, "portfolio_phases": [phase]}
    result = {"kind": "portfolio", "status": "proved", "kernel_checked": True,
        "theorem": "0 = 0", "original_theorem": "0=0", "commands": ["refl"], "goals": [], "proof_nodes": 1,
        "kernel_source_commit": publisher.worker.SOURCE_COMMIT, "environment_sha256": publisher.ENVIRONMENT,
        "classical": False, "tactics_requested": 1, "tactics_applied": 1, "failed_tactics": 0,
        "failed_step": None, "error": None, "proof_profile": "sequential", "model_used": True,
        "model": model, "execution": execution, "proof_sources": {"model": 1},
        "native_admission": {"input_theorem": "0=0", "theorem": "0 = 0"},
        "trace": [{"v": 1, "step": 1, "focus": 0, "tactic": "refl", "status": "ok", "error": None,
                   "goals_before": ["⊢ 0 = 0"], "goals_after": [], "session": "fixture-original"},
                  {"qed": True, "theorem": "0 = 0", "tactic_count": 1, "proof_size": 1}],
        "search": {"model_calls": 1, "vampire_calls": 0, "independent_replay": True,
                   "replay_evidence": {"status": "completed", "actual_exit_code": 0, "child_process_id": 99999},
                   "provenance": [{"source": "model", "command": "refl"}]},
        "portfolio": {"selected_model_id": publisher.MODEL_ID, "winner": "sequential",
                      "original_theorem": "0=0", "script_combination": False,
                      "fallback": {"status": "not_needed", "reason": "model_proof"}, "phases": [phase]}}
    job = {"id": "a" * 32, "state": "completed", "error": None, "execution": execution, "result": result}
    return {"REQUEST.json": request, "TERMINAL_JOB.json": {"ok": True, "job": job},
        "SUBMITTED.json": {"ok": True, "job_id": job["id"]},
        "SUBMISSION_INTENT.json": {"job_count": 1, "automatic_retry": False, "model_inference": True},
        "STATUS_BEFORE.json": {"models": {publisher.MODEL_ID: {**model, "available": True}}},
        "STATUS_AFTER.json": {"computation_active": False},
        "SUMMARY.json": {"schema": "hydra-portfolio-http-smoke-v1", "job_id": job["id"],
                         "state": "completed", "automatic_retry": False}, "SMOKE_CHECK.json": {"passed": True}}


class StagingAdmission(unittest.TestCase):
    def test_complete_model_fixture_is_admitted_without_execution(self):
        records = fixture()
        request, job, result = publisher.admit_http(records)
        self.assertEqual(request, records["REQUEST.json"])
        self.assertEqual(result["proof_sources"], {"model": 1})
        self.assertEqual(job["id"], "a" * 32)

    def test_wrong_origin_model_work_winner_and_cleanup_are_rejected(self):
        for change in ("checkpoint", "zero_calls", "symbolic_winner", "heuristic_step", "cleanup", "job_id"):
            records = fixture()
            result = records["TERMINAL_JOB.json"]["job"]["result"]
            if change == "checkpoint": result["model"]["checkpoint_sha256"] = "0" * 64
            elif change == "zero_calls": result["search"]["model_calls"] = 0
            elif change == "symbolic_winner": result["portfolio"]["winner"] = "symbolic"
            elif change == "heuristic_step": result["search"]["provenance"][0]["source"] = "heuristic"
            elif change == "cleanup": result["execution"]["quiescent"] = False
            else: records["SUBMITTED.json"]["job_id"] = "b" * 32
            with self.subTest(change=change), self.assertRaises(ValueError):
                publisher.admit_http(records)

    def test_replay_accepts_new_session_but_rejects_proof_changes(self):
        _, _, original = publisher.admit_http(fixture())
        replay = copy.deepcopy(original)
        replay.update(kind="manual", model_used=False)
        replay["trace"][0]["session"] = "fixture-fresh-child"
        execution = {"error": None, "cancelled": False, "quiescent": True, "worker_started": True,
                     "worker_exit_code": 0, "result": replay}
        publisher.validate_publication_replay(execution, original)
        for change in ("goal", "command", "nodes", "authority"):
            altered = copy.deepcopy(execution)
            if change == "goal": altered["result"]["trace"][0]["goals_before"] = ["⊢ 0 = 1"]
            elif change == "command": altered["result"]["commands"] = ["exact zero"]
            elif change == "nodes": altered["result"]["proof_nodes"] = 2
            else: altered["result"]["environment_sha256"] = "0" * 64
            with self.subTest(change=change), self.assertRaises(ValueError):
                publisher.validate_publication_replay(altered, original)


if __name__ == "__main__":
    unittest.main()
