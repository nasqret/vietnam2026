from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_policy import evaluation_replay as canonical_replay  # noqa: E402
from training.peano_policy import legacy_evaluation_replay as legacy  # noqa: E402


REPORT = (
    ROOT
    / "artifacts"
    / "peano-policy"
    / "model-v3-evaluation-2026-08-02"
    / "trained-report.json"
)
TRAINING_MANIFEST = REPORT.with_name("training-manifest.json")


def test_exact_historical_report_is_independently_kernel_replayed() -> None:
    attestation = legacy.replay_historical_evaluation_report(
        REPORT, TRAINING_MANIFEST
    )

    assert attestation["format"] == legacy.REPORT_FORMAT
    assert attestation["v"] == legacy.REPORT_VERSION
    assert attestation["status"] == "passed"
    assert attestation["input"]["bytes"] == legacy.EXPECTED_REPORT_BYTES
    assert attestation["input"]["sha256"] == legacy.EXPECTED_REPORT_SHA256
    assert attestation["input"]["training_manifest"]["bytes"] == (
        legacy.EXPECTED_TRAINING_MANIFEST_BYTES
    )
    assert attestation["input"]["training_manifest"]["sha256"] == (
        legacy.EXPECTED_TRAINING_MANIFEST_SHA256
    )
    assert attestation["evaluation"]["source_commit"] == (
        legacy.EXPECTED_SOURCE_COMMIT
    )
    assert attestation["evaluation"]["job_id"] == (
        legacy.EXPECTED_EVALUATION_JOB_ID
    )
    assert attestation["summary"]["attempts"] == 4
    assert attestation["summary"]["claimed_proofs"] == 3
    assert attestation["summary"]["kernel_replayed_proofs"] == 3
    assert attestation["summary"]["proved_goals"] == 3
    assert attestation["summary"]["pass@k"] == 0.75

    proofs = {
        proof["name"]: (proof["commands"], proof["proof_nodes"])
        for proof in attestation["proofs"]
    }
    assert proofs == {
        "closed_arithmetic_seven": (["norm_num"], 98),
        "existential_subtraction_two": (["exists 5", "norm_num"], 29),
        "double_right_zero": (["intro n", "rewrite PA3", "simp"], 10),
    }
    assert all(
        proof["replay"]["kernel_checked"] is True
        for proof in attestation["proofs"]
    )

    compatibility = attestation["compatibility"]
    assert compatibility["profile"] == legacy.COMPATIBILITY_PROFILE
    assert compatibility["canonical_replay_unchanged"] is True
    assert compatibility["reconstruction"] == {
        "status": "exact-projection-of-pinned-complete-authority",
        "fields": dict(legacy.RECONSTRUCTED_ENVIRONMENT_FIELDS),
        "complete_environment_record_sha256": (
            legacy.EXPECTED_FULL_ENVIRONMENT_RECORD_SHA256
        ),
        "verified_complete_environment_record_sha256": (
            legacy.EXPECTED_FULL_ENVIRONMENT_RECORD_SHA256
        ),
    }
    assert attestation["compatibility_replay_authority"][
        "current_context_checked_before_and_after"
    ] is True
    assert attestation["compatibility_replay_authority"][
        "tool_sources_checked_before_and_after"
    ] is True
    assert attestation["compatibility_replay_authority"][
        "training_manifest_checked_before_and_after"
    ] is True
    training = attestation["compatibility_replay_authority"]["training_manifest"]
    assert training["manifest_bytes"] == legacy.EXPECTED_TRAINING_MANIFEST_BYTES
    assert training["manifest_sha256"] == legacy.EXPECTED_TRAINING_MANIFEST_SHA256
    assert training["run_name"] == "qwen3-1.7b-peano-lora-v3-library"
    assert training["base_model"] == {
        "id": "Qwen/Qwen3-1.7B-Base",
        "requested_revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
        "resolved_snapshot_hash": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
        "config_sha256": (
            "a325c9f27de176887b8ca7f68d21714247f9c8106e8c120219789338da9a5dcd"
        ),
        "weight_shards_content_hashed": False,
        "identity_scope": (
            "requested/resolved revision and config SHA-256 provenance"
        ),
        "limitation": (
            "Base-weight shards are not content-hashed; this is revision/config "
            "provenance, not a bit-for-bit base-weight attestation."
        ),
    }
    assert training["adapter"]["sha256"] == legacy.EXPECTED_ADAPTER_SHA256
    assert training["adapter"]["files"] == dict(legacy.EXPECTED_ADAPTER_FILES)
    assert training["tokenizer"]["sha256"] == legacy.EXPECTED_TOKENIZER_SHA256
    assert training["dataset_sha256"] == legacy.EXPECTED_DATASET_SHA256
    assert training["optimizer_steps"] == {"expected": 649, "actual": 649}
    assert training["training_job"] == {
        "scheduler": "slurm",
        "job_id": "217859",
        "source_commit": legacy.EXPECTED_SOURCE_COMMIT,
    }
    assert training["report_provenance_cross_match"] == {
        "status": "matched",
        "fields": [
            "adapter_sha256",
            "base_model_id",
            "base_model_revision",
            "dataset_sha256",
            "environment_sha256",
            "held_out_contract_sha256",
            "library_snapshot_sha256",
            "prompt_contract_sha256",
            "prompt_version",
            "run_name",
            "training_manifest_sha256",
        ],
        "training_job_binding": True,
    }


def test_changed_report_is_rejected_before_current_authority_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = json.loads(REPORT.read_text(encoding="utf-8"))
    record["proved_goals"] = 2
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
        match="report bytes differ from the one pinned historical evaluation",
    ):
        legacy.replay_historical_evaluation_report(changed, TRAINING_MANIFEST)


def test_changed_training_manifest_is_rejected_before_current_authority_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = TRAINING_MANIFEST.read_bytes()
    changed_raw = raw.replace(
        b"qwen3-1.7b-peano-lora-v3-library",
        b"qwen3-1.7b-peano-lora-v3-librarx",
        1,
    )
    assert len(changed_raw) == len(raw) and changed_raw != raw
    changed = tmp_path / "changed-training-manifest.json"
    changed.write_bytes(changed_raw)

    def unexpected_context_load() -> canonical_replay.ReplayContext:
        raise AssertionError(
            "current authority must not load for changed manifest bytes"
        )

    monkeypatch.setattr(
        canonical_replay, "current_replay_context", unexpected_context_load
    )
    with pytest.raises(
        canonical_replay.EvaluationReplayError,
        match="training manifest bytes differ from the pinned completed run",
    ):
        legacy.replay_historical_evaluation_report(REPORT, changed)
