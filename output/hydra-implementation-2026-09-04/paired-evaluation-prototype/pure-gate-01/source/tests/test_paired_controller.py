"""Pure constructed-record tests; no native/model/scheduler/process execution."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import paired_common as common
import paired_controller as controller
import paired_case_worker as worker


def exposure():
    return {"training_rows": 2047, "validation_rows": 432, "expected_optimizer_steps": 256,
            "training_row_ids_sha256": "a" * 64, "validation_row_ids_sha256": "b" * 64,
            "dataset_sha256": common.DATASET_SHA, "holdout_sha256": common.HOLDOUT_SHA,
            "epochs": 1, "prompt_schema": "primitive_v4", "planner_rows_allowed": False,
            "objective_sha256": "c" * 64}


def study():
    arms = {"symbolic": None}
    for name in common.REQUIRED_ARMS[1:]:
        arms[name] = {"model_key": common.MODEL_KEYS[name], "base_directory": "/local/base/" + name,
            "adapter_directory": "/local/adapter/" + name,
            "adapter_kind": "historical_retention" if name == "historical_1_7b" else "fresh_decision_pilot",
            "adapter_manifest_sha256": common.HISTORICAL_SHA if name == "historical_1_7b" else "d" * 64}
    return {"schema": "hydra-p6-p10-paired-study-v1", "study_id": "constructed-test",
        "scope": "full16", "comparison": "fixed_native_work_guarded", "wall_profile": "guarded-work-60-v1",
        "holdout_sha256": common.HOLDOUT_SHA, "slice_sha256": controller.SLICE_SHA,
        "source_pins_sha256": "e" * 64, "arms": arms, "features": deepcopy(common.FEATURES),
        "native_work": common.search_settings("guarded-work-60-v1"), "model_limits": deepcopy(common.MODEL_LIMITS),
        "resource_limits": deepcopy(common.RESOURCE_LIMITS), "fresh_training_exposure": exposure(),
        "distilled_training_exposure": None, "training_allowed": False, "retrieval_allowed": False,
        "automatic_retry": False, "resume": False}


def reservation(s=None):
    s = s or study()
    return {"schema": controller.RESERVATION_SCHEMA, "job_id": "123456", "job_name": "hydra-paired-test",
        "nonce": "1" * 32, "uid": os.getuid(), "account": common.ACCOUNT, "partition": common.PARTITION,
        "gpus": 1, "nodes": 1, "cpus": 8, "memory_gib": 64,
        "seconds": common.job_seconds(s["scope"], s["wall_profile"]), "arm": "fresh_4b",
        "study_sha256": sha256(common.canonical(s)).hexdigest(), "source_pins_sha256": s["source_pins_sha256"],
        "controller_sha256": "1" * 64, "case_worker_sha256": "2" * 64, "common_sha256": "3" * 64,
        "holdout_sha256": common.HOLDOUT_SHA, "slice_sha256": controller.SLICE_SHA}


def search_record():
    row = {"status": "limit", "theorem": "0 = 0", "classical": False, "kernel_checked": False,
        "commands": [], "tactic_attempts": 20, "states_expanded": 4, "states_discovered": 12,
        "depth_reached": 5, "model_calls": 2, "model_advisor_calls": 3,
        "structured_planning": {"enabled": False, "requests": 0, "provider": None},
        "lemma_library": None, "branch_ranker": {"enabled": False}}
    for name in ("vampire", "sympy", "cvc5", "egg", "e"):
        row[name + "_calls"] = row[name + "_advisor_calls"] = 0
    return row


def replay_record():
    return {"theorem": "0 = 0", "kernel_checked": True, "status": "proved", "classical": False,
            "goals": [], "tactics_requested": 1, "tactics_applied": 1, "proof_nodes": 1,
            "environment_sha256": "d" * 64}


class AdmissionTests(unittest.TestCase):
    def test_exact_four_arm_spec(self):
        value = study()
        self.assertIs(common.study_spec(value, controller.SLICE_SHA), value)

    def test_wall_limits_cannot_be_unbound_or_enlarged(self):
        for key, value in (("wall_profile", None), ("wall_profile", "unbounded")):
            row = study(); row[key] = value
            with self.assertRaises(ValueError):
                common.study_spec(row, controller.SLICE_SHA)
        row = study(); row["native_work"]["max_tactic_attempts"] += 1
        with self.assertRaises(ValueError):
            common.study_spec(row, controller.SLICE_SHA)

    def test_booleans_cannot_impersonate_numeric_settings(self):
        row = study(); row["model_limits"]["seed"] = False
        with self.assertRaises(ValueError):
            common.study_spec(row, controller.SLICE_SHA)

    def test_size_comparison_cannot_enable_extra_information(self):
        for key, value in (("library", True), ("planner", True), ("external_advisers", ["vampire"]), ("ranker", True)):
            row = study(); row["features"][key] = value
            with self.assertRaises(ValueError):
                common.study_spec(row, controller.SLICE_SHA)

    def test_no_expected_label_or_reference_enters_search_payload(self):
        row = {"id": "private-case-label", "theorem": "0 = 0", "expected": "provable",
               "counterexample": "not search input", "reference_script": ["refl"], "family": "private-family"}
        payload = common.case_payload(row, "guarded-work-60-v1")
        self.assertEqual(set(payload), {"theorem", "settings"})
        for label in ("private-case-label", "provable", "not search input", "private-family"):
            self.assertNotIn(label, common.canonical(payload).decode())

    def test_exact_historical_adapter_and_model(self):
        for field, value in (("adapter_manifest_sha256", "a" * 64), ("model_key", "qwen3-4b-base")):
            row = study(); row["arms"]["historical_1_7b"][field] = value
            with self.assertRaises(ValueError):
                common.study_spec(row, controller.SLICE_SHA)

    def test_full_scope_cannot_substitute_optional_arm(self):
        row = study(); row["arms"]["fresh_8b"] = row["arms"].pop("fresh_4b")
        with self.assertRaises(ValueError):
            common.study_spec(row, controller.SLICE_SHA)

    def test_smaller_scope_has_finite_predeclared_budget(self):
        self.assertEqual(common.job_seconds("full16", "guarded-work-60-v1"), 2000)
        self.assertEqual(common.job_seconds("paired5", "guarded-work-60-v1"), 680)
        self.assertEqual(common.job_seconds("full16", "fixed-wall-30-v1"), 1520)
        self.assertLess(4 * common.job_seconds("full16", "guarded-work-60-v1") + 600, 6 * 3600)

    def test_new_reservation_binds_exact_job_arm_and_limits(self):
        s = study(); value = reservation(s)
        self.assertIs(controller.reservation_spec(value, s, value["study_sha256"]), value)
        for key, replacement in (("seconds", 7200), ("gpus", 2), ("arm", "fresh_8b"), ("nonce", "*" * 32),
                                 ("schema", "hydra-p6-smoke-reservation-v1"), ("uid", -1)):
            bad = deepcopy(value); bad[key] = replacement
            with self.assertRaises(ValueError):
                controller.reservation_spec(bad, s, value["study_sha256"])

    def test_claim_cannot_be_reused_after_first_actual_scheduler_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reservation.json"
            value = reservation(); common.save(path, value); digest = common.pin(path)["sha256"]
            first = {"job_id": value["job_id"]}
            claim = controller.claim_reservation(path, digest, value, Path(directory), first)
            self.assertTrue(claim.is_file())
            with self.assertRaises(FileExistsError):
                controller.claim_reservation(path, digest, value, Path(directory), first)

    def test_duplicate_and_nonfinite_json_rejected(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}'):
            with self.assertRaises(ValueError):
                common.strict_json(raw)

    def test_incomplete_training_exposure_rejected(self):
        row = study(); del row["fresh_training_exposure"]["training_row_ids_sha256"]
        with self.assertRaises(ValueError):
            common.study_spec(row, controller.SLICE_SHA)

    def test_fresh_completed_exposure_must_have_heldout_admission(self):
        e = exposure()
        record = {"schema": "hydra-decision-pilot-artifact-v1", "model_trained": True,
            "resume": False, "automatic_retry": False, "actual_optimizer_steps": 256,
            "plan": {**{key: e[key] for key in common.EXPOSURE_FIELDS}, "schema": "hydra-decision-pilot-plan-v2",
                     "epochs": 1, "prompt_schema": "primitive_v4", "planner_rows_allowed": False,
                     "resume": False, "automatic_retry": False, "objective": {"task": "fixture"},
                     "data_attestation": {"holdout_sha256": common.HOLDOUT_SHA,
                         "regenerated_byte_exact": True, "manifest_sha256": common.DATASET_SHA}}}
        got = common.training_exposure(record)
        self.assertEqual(got["training_rows"], 2047)
        record["plan"]["data_attestation"]["holdout_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            common.training_exposure(record)


class AccountingAndProofTests(unittest.TestCase):
    def test_exact_search_provider_session_accounting(self):
        counters = common.validate_counts(search_record(),
            {"actual_model_calls": 2, "generated_token_slots": 64, "forward_passes": 16},
            {"calls": 2, "generated_tokens": 64})
        self.assertEqual(counters["actual_model_calls"], 2)
        self.assertEqual(counters["planner_calls"], 0)

    def test_counter_mismatch_is_not_zero(self):
        with self.assertRaises(ValueError):
            common.validate_counts(search_record(),
                {"actual_model_calls": 3, "generated_token_slots": 64, "forward_passes": 16},
                {"calls": 2, "generated_tokens": 64})

    def test_symbolic_cannot_hide_model_calls(self):
        with self.assertRaises(ValueError):
            common.validate_counts(search_record(), None, None)

    def test_native_work_and_external_call_bounds(self):
        for key, replacement in (("tactic_attempts", 6001), ("states_discovered", 2049), ("e_calls", 1)):
            row = search_record(); row[key] = replacement
            with self.assertRaises(ValueError):
                common.validate_counts(row, {"actual_model_calls": 2, "generated_token_slots": 64, "forward_passes": 16},
                                       {"calls": 2, "generated_tokens": 64})

    def proof(self):
        row = search_record()
        row.update(status="proof", kernel_checked=True, commands=["refl"], certificate_nodes=1,
                   replay=replay_record(), provenance=[{"source": "heuristic", "command": "refl"}])
        return row

    def test_complete_same_target_same_authority_replay_required(self):
        row = self.proof(); replay = replay_record()
        self.assertTrue(common.proof_acceptance(row, replay, "0 = 0"))
        for field, value in (("theorem", "0 = S 0"), ("kernel_checked", False), ("goals", ["0 = 0"]),
                             ("classical", True), ("environment_sha256", "e" * 64), ("proof_nodes", 2)):
            bad = dict(replay); bad[field] = value
            with self.assertRaises(ValueError):
                common.proof_acceptance(row, bad, "0 = 0")

    def test_external_winning_step_cannot_enter_disabled_portfolio(self):
        row = self.proof(); row["provenance"][0]["source"] = "e"
        with self.assertRaises(ValueError):
            common.proof_acceptance(row, replay_record(), "0 = 0")

    def test_resource_stop_overrides_apparent_complete_proof(self):
        execution = {"helper_launches": 1, "quiescent": True, "leader_reaped": True,
                     "exit_code": 0, "termination_reason": "host_sampled_rss_limit"}
        self.assertEqual(controller.classify_case(execution, {"status": "proved"}), "resource_stop")

    def test_missing_result_and_cleanup_are_not_proof(self):
        execution = {"helper_launches": 1, "quiescent": True, "leader_reaped": True,
                     "exit_code": 0, "termination_reason": "process_exit"}
        self.assertEqual(controller.classify_case(execution, None), "infrastructure_failure")
        execution["quiescent"] = False
        self.assertEqual(controller.classify_case(execution, {"status": "proved"}), "infrastructure_failure")

    def test_cpu_signal_distinguished_from_unexplained_kill(self):
        execution = {"helper_launches": 1, "quiescent": True, "leader_reaped": True,
                     "exit_code": -signal.SIGXCPU, "termination_reason": "process_exit"}
        self.assertEqual(controller.classify_case(execution, None), "resource_stop")
        execution["exit_code"] = -signal.SIGKILL
        self.assertEqual(controller.classify_case(execution, None), "infrastructure_failure")

    def test_gpu_memory_stops_instead_of_returning_failed_candidate(self):
        cuda = mock.Mock()
        cuda.max_memory_allocated.return_value = common.RESOURCE_LIMITS["gpu_observed_bytes"] + 1
        session = mock.Mock(); session.torch.cuda = cuda
        with self.assertRaises(MemoryError):
            worker.check_gpu_memory(session)


class ProcTests(unittest.TestCase):
    def test_proc_stat_accounts_spaces_and_parentheses_in_command(self):
        fields = ["S", "77", "88", "88"] + ["0"] * 15 + ["1234"] + ["0"] * 8
        row = controller.parse_proc_stat("88 (a strange (name)) " + " ".join(fields), 88)
        self.assertEqual(row, {"state": "S", "ppid": 77, "pgid": 88, "sid": 88, "start_ticks": 1234})

    def test_live_short_or_missing_rss_fails_closed(self):
        with self.assertRaises(ValueError):
            controller.parse_proc_status("Uid:\t12 12 12 12\n", "R")
        self.assertEqual(controller.parse_proc_status("Uid:\t12 12 12 12\n", "Z"), (12, 0))

    def test_duplicate_rss_rejected(self):
        raw = "Uid:\t12 12 12 12\nVmRSS:\t100 kB\nVmRSS:\t200 kB\n"
        with self.assertRaises(ValueError):
            controller.parse_proc_status(raw, "R")

    def test_environment_excludes_secrets_and_python_path(self):
        with mock.patch.dict(os.environ, {"SOME_API_KEY": "private", "PYTHONPATH": "/unreviewed", "SLURM_JOB_ID": "123"}):
            value = controller.environment()
        self.assertNotIn("SOME_API_KEY", value)
        self.assertNotIn("PYTHONPATH", value)
        self.assertEqual(value["HF_HUB_OFFLINE"], "1")
        self.assertEqual(value["SLURM_JOB_ID"], "123")

    def test_cleanup_waits_and_reports_group_quiescence(self):
        process = mock.Mock(pid=123); process.wait.return_value = -9
        with mock.patch.object(controller, "group_is_empty", side_effect=[False, True, True]), \
             mock.patch.object(controller.os, "killpg") as kill:
            result = controller.terminate_owned(process)
        kill.assert_called_once_with(123, signal.SIGKILL)
        self.assertEqual(result, {"exit_code": -9, "quiescent": True, "leader_reaped": True})
        process.wait.assert_called_once()


if __name__ == "__main__":
    forbidden = {"torch", "mlx", "sympy", "cvc5", "peano_lab", "hybrid_search", "experimental_model"}
    with mock.patch("subprocess.Popen", side_effect=AssertionError("Pure tests cannot spawn a child")):
        suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    if forbidden.intersection(sys.modules):
        raise RuntimeError("Pure gate imported a forbidden framework/native module.")
    raise SystemExit(0 if result.wasSuccessful() else 1)
