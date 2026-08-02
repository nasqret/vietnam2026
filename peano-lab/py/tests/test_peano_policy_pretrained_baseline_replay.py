from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_policy import evaluation_replay as canonical_replay  # noqa: E402
from training.peano_policy import pretrained_baseline_replay as baseline  # noqa: E402


REPORT = (
    ROOT
    / "artifacts"
    / "peano-policy"
    / "model-v3-evaluation-2026-08-02"
    / "pretrained-base-report.json"
)
MANIFEST = REPORT.with_name("training-manifest.json")


def test_exact_pretrained_base_report_is_strictly_admitted() -> None:
    attestation = baseline.replay_pretrained_baseline_report(REPORT, MANIFEST)

    assert attestation["format"] == baseline.REPORT_FORMAT
    assert attestation["v"] == baseline.REPORT_VERSION
    assert attestation["status"] == "passed"
    assert attestation["input"]["evaluation_report"]["bytes"] == (
        baseline.EXPECTED_REPORT_BYTES
    )
    assert attestation["input"]["evaluation_report"]["sha256"] == (
        baseline.EXPECTED_REPORT_SHA256
    )
    assert attestation["input"]["training_manifest"] == {
        "path": str(MANIFEST.resolve()),
        "bytes": baseline.EXPECTED_TRAINING_MANIFEST_BYTES,
        "sha256": baseline.EXPECTED_TRAINING_MANIFEST_SHA256,
    }
    assert attestation["evaluation"]["source_commit"] == (
        baseline.EXPECTED_SOURCE_COMMIT
    )
    assert attestation["evaluation"]["job_id"] == (
        baseline.EXPECTED_EVALUATION_JOB_ID
    )
    assert attestation["summary"] == {
        "attempts": 4,
        "claimed_proofs": 0,
        "kernel_replayed_proofs": 0,
        "proved_goals": 0,
        "pass@k": 0.0,
        "status_counts": {
            "failing": 4,
            "invalid": 0,
            "limit": 0,
            "proof": 0,
        },
    }
    assert attestation["proofs"] == []
    assert attestation["pretrained_base"]["adapter_attached"] is False
    assert attestation["pretrained_base"][
        "base_weight_shards_content_attested"
    ] is False
    assert "were not independently hashed" in attestation["pretrained_base"][
        "base_weight_attestation_limitation"
    ]
    assert attestation["pretrained_base"]["completed_training_binding"][
        "dataset_sha256"
    ] == "2e236384ecb6e7b15ccf986abab53fcfd4ec47fc97c7e00f5cc736dbbb4f224e"
    assert attestation["pretrained_base"]["completed_training_binding"][
        "expected_optimizer_steps"
    ] == 649
    assert attestation["pretrained_base"]["completed_training_binding"][
        "actual_optimizer_steps"
    ] == 649
    assert attestation["pretrained_base"]["base_model"] == {
        "id": "Qwen/Qwen3-1.7B-Base",
        "revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
        "config_sha256": (
            "a325c9f27de176887b8ca7f68d21714247f9c8106e8c120219789338da9a5dcd"
        ),
    }
    assert attestation["search_accounting"]["actual"] == {
        "model_generate_calls": 4,
        "states_expanded": 4,
        "states_discovered": 4,
        "candidates_executed": 0,
        "candidate_sequences_requested": 32,
        "candidate_sequences_returned": 32,
        "candidate_lines_returned": 0,
        "malformed_sequences_rejected": 32,
        "frontier_peak_per_goal": 1,
    }
    assert all(
        goal["status"] == "exhausted"
        and goal["model_generate_calls"] == 1
        and goal["candidate_sequences_returned"] == 8
        and goal["malformed_sequences_rejected"] == 8
        and goal["candidates_executed"] == 0
        for goal in attestation["search_accounting"]["goals"]
    )
    accounting_projection = attestation["search_accounting"][
        "accounting_schema_projection"
    ]
    assert attestation["search_accounting"][
        "search_and_goal_payload_unmodified"
    ] is True
    assert "policy_identity.base_policy" in accounting_projection[
        "transformed_fields"
    ]
    assert any(
        "job.deployment.job_script" in field
        for field in accounting_projection["transformed_fields"]
    )
    assert attestation["admission"] == {
        "profile": baseline.ADMISSION_PROFILE,
        "scope": "one immutable pretrained-base control report",
        "canonical_trained_replay_unchanged": True,
        "original_report_edited": False,
        "full_comparison_authority_validated": True,
        "completed_training_manifest_cross_bound": True,
        "unattached_base_identity_and_provenance_validated": True,
        "base_weight_shards_content_attested": False,
        "historical_sources_validated": True,
        "deployment_and_job_validated": True,
        "zero_proof_claims_validated": True,
    }
    assert attestation["admission_authority"][
        "current_context_checked_before_and_after"
    ] is True
    assert attestation["admission_authority"][
        "tool_sources_checked_before_and_after"
    ] is True


def test_changed_report_is_rejected_before_current_authority_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = json.loads(REPORT.read_text(encoding="utf-8"))
    record["proved_goals"] = 1
    changed = tmp_path / "changed-report.json"
    changed.write_text(
        json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    def unexpected_context_load() -> canonical_replay.ReplayContext:
        raise AssertionError("current authority must not load for changed report bytes")

    monkeypatch.setattr(
        canonical_replay, "current_replay_context", unexpected_context_load
    )
    with pytest.raises(
        canonical_replay.EvaluationReplayError,
        match="report bytes differ from the pinned pretrained-base evaluation",
    ):
        baseline.replay_pretrained_baseline_report(changed, MANIFEST)


def test_changed_training_manifest_is_rejected_before_current_authority_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = json.loads(MANIFEST.read_text(encoding="utf-8"))
    record["metrics"]["actual_optimizer_steps"] = 648
    changed = tmp_path / "changed-training-manifest.json"
    changed.write_text(
        json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    def unexpected_context_load() -> canonical_replay.ReplayContext:
        raise AssertionError("current authority must not load for changed manifest")

    monkeypatch.setattr(
        canonical_replay, "current_replay_context", unexpected_context_load
    )
    with pytest.raises(
        canonical_replay.EvaluationReplayError,
        match="training manifest bytes differ from the pinned completed run",
    ):
        baseline.replay_pretrained_baseline_report(REPORT, changed)
