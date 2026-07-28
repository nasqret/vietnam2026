"""Regression for the first WMI-trained policy result artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from peano_lab.batch import (
    MODEL_V1_COMMANDS,
    MODEL_V1_THEOREMS,
    capability_sha256,
    run_proof,
)
from peano_lab.ui.prove import SurfaceCapabilities


REPO = Path(__file__).resolve().parents[3]
ARTIFACTS = REPO / "artifacts" / "peano-policy"
SUMMARY = ARTIFACTS / "qwen3-1.7b-wmi-smoke-summary.json"
SCRIPT = ARTIFACTS / "qwen3-1.7b-wmi-easy-witness.pa"
TRAINING_MANIFEST = ARTIFACTS / "qwen3-1.7b-wmi-training-manifest.json"
HELD_OUT_REPORT = ARTIFACTS / "qwen3-1.7b-wmi-heldout-k4.json"
PARITY_REPORT = ARTIFACTS / "qwen3-1.7b-wmi-parity-k16.json"
EASY_WITNESS_REPORT = ARTIFACTS / "qwen3-1.7b-wmi-easy-witness-k8.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_wmi_smoke_summary_records_the_negative_and_positive_results() -> None:
    record = json.loads(SUMMARY.read_text(encoding="utf-8"))

    assert record["format"] == "peano-policy-wmi-smoke-summary"
    assert record["v"] == 1
    assert record["causal_attribution"] == "pending_pretrained_base_baseline"
    assert record["held_out"]["proved_goals"] == 0
    assert record["held_out"]["pass_at_k"] == 0.0
    assert record["held_out"]["report_path"] == HELD_OUT_REPORT.name
    assert record["held_out"]["report_sha256"] == _sha256(HELD_OUT_REPORT)
    assert record["arbitrary_probes"][0]["proved"] is False
    assert record["arbitrary_probes"][0]["report_path"] == PARITY_REPORT.name
    assert record["arbitrary_probes"][0]["report_sha256"] == _sha256(PARITY_REPORT)
    positive = record["arbitrary_probes"][1]
    assert positive["dataset_exact_formula_occurrences"] == 0
    assert positive["proved"] is True
    assert positive["proof_nodes"] == 7
    assert positive["proof_sha256"] == _sha256(SCRIPT)
    assert positive["report_path"] == EASY_WITNESS_REPORT.name
    assert positive["report_sha256"] == _sha256(EASY_WITNESS_REPORT)
    assert record["training"]["manifest_path"] == TRAINING_MANIFEST.name
    assert record["training"]["manifest_sha256"] == _sha256(TRAINING_MANIFEST)
    assert "induction" in record["curriculum_audit"]["missing_tactic_heads"]


def test_published_wmi_reports_match_the_compact_result_index() -> None:
    record = json.loads(SUMMARY.read_text(encoding="utf-8"))
    manifest = json.loads(TRAINING_MANIFEST.read_text(encoding="utf-8"))
    held_out = json.loads(HELD_OUT_REPORT.read_text(encoding="utf-8"))
    parity = json.loads(PARITY_REPORT.read_text(encoding="utf-8"))
    easy = json.loads(EASY_WITNESS_REPORT.read_text(encoding="utf-8"))

    assert manifest["adapter"]["sha256"] == record["training"]["adapter_sha256"]
    assert manifest["metrics"]["train"]["train_loss"] == record["training"]["train_loss"]
    assert manifest["metrics"]["eval"]["eval_loss"] == record["training"]["validation_loss"]
    assert held_out["goal_set_sha256"] == record["held_out"]["goal_set_sha256"]
    assert held_out["proved_goals"] == record["held_out"]["proved_goals"]
    assert held_out["status_counts"] == record["held_out"]["status_counts"]
    assert parity["proof_publication"] == {"status": "no-proof"}
    assert parity["status_counts"] == record["arbitrary_probes"][0]["status_counts"]
    assert easy["status_counts"] == record["arbitrary_probes"][1]["status_counts"]
    assert easy["proof_publication"]["script_sha256"] == _sha256(SCRIPT)
    assert easy["proof_publication"]["replay"]["kernel_checked"] is True


def test_wmi_model_script_replays_under_its_attested_authority() -> None:
    lines = tuple(
        line.strip()
        for line in SCRIPT.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    assert lines[0].startswith("pa prove ")
    assert lines[-1] == "qed"
    theorem = lines[0].removeprefix("pa prove ")
    capabilities = SurfaceCapabilities(
        label="model-v1",
        allowed_commands=MODEL_V1_COMMANDS,
        allowed_theorems=frozenset(MODEL_V1_THEOREMS),
    )

    result = run_proof(
        theorem,
        lines[1:-1],
        request_id="wmi-trained-easy-witness-artifact",
        capabilities=capabilities,
    )

    assert result.status == "proved"
    assert result.kernel_checked is True
    assert result.proof_nodes == 7
    assert result.environment_sha256 == capability_sha256(capabilities)
    assert result.environment_sha256 == (
        "ea753147079f48c14e9bd197051264a1ab29868a0bac84bd13c420baf1b63e1f"
    )
