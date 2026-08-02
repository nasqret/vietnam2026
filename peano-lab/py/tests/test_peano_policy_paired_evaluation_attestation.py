from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_policy import paired_evaluation_attestation as paired  # noqa: E402


ARTIFACTS = (
    ROOT
    / "artifacts"
    / "peano-policy"
    / "model-v3-evaluation-2026-08-02"
)
TRAINED_ATTESTATION = ARTIFACTS / "trained-compatibility-replay.json"
PRETRAINED_ATTESTATION = ARTIFACTS / "pretrained-base-replay.json"
TRAINED_REPORT = ARTIFACTS / "trained-report.json"
PRETRAINED_REPORT = ARTIFACTS / "pretrained-base-report.json"
TRAINING_MANIFEST = ARTIFACTS / "training-manifest.json"


def _record(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def test_exact_pair_is_admitted_with_narrow_claim_scope() -> None:
    attestation = paired.attest_paired_evaluation(
        trained_attestation_path=TRAINED_ATTESTATION,
        pretrained_attestation_path=PRETRAINED_ATTESTATION,
        trained_report_path=TRAINED_REPORT,
        pretrained_report_path=PRETRAINED_REPORT,
        training_manifest_path=TRAINING_MANIFEST,
    )

    assert attestation["format"] == paired.REPORT_FORMAT
    assert attestation["v"] == paired.REPORT_VERSION
    assert attestation["status"] == "passed"
    assert attestation["result"] == "paired_launch_smoke_admitted"
    assert attestation["observed_result"] == {
        "metric": "observed_solve_fraction_at_k_1",
        "k": 1,
        "denominator": 4,
        "trained": {
            "solved": 3,
            "solve_fraction": 0.75,
            "kernel_replayed_proofs": 3,
        },
        "pretrained_comparison": {
            "solved": 0,
            "solve_fraction": 0.0,
            "proof_claims": 0,
        },
        "trained_minus_pretrained_solved": 3,
        "trained_minus_pretrained_solve_fraction": 0.75,
    }
    assert attestation["pairing"]["same_goals_seed_search_limits"] is True
    assert attestation["pairing"]["benchmark"]["k"] == 1
    assert attestation["pairing"]["benchmark"]["search_limits"] == {
        "beam_width": 16,
        "candidates_per_state": 8,
        "max_depth": 32,
        "max_model_calls": 512,
        "max_states": 4096,
    }
    assert [
        (proof["commands"], proof["proof_nodes"], proof["kernel_replayed"])
        for proof in attestation["trained_proofs"]
    ] == [
        (["norm_num"], 98, True),
        (["exists 5", "norm_num"], 29, True),
        (["intro n", "rewrite PA3", "simp"], 10, True),
    ]

    producer = attestation["producer_attribution"]
    assert producer["training_job_id"] == "217859"
    assert producer["trained_evaluation_job_id"] == "218171"
    assert producer["pretrained_evaluation_job_id"] == "218172"
    assert producer["source_commit"] == (
        "4d44609ee32d5d28726c082ef7b5649c0a1107a6"
    )
    assert producer["paired_layer_replayed_raw_model_outputs"] is False
    assert producer["model_output_transcripts_present_in_reports"] is False
    historical = producer["historical_sources"]
    assert historical["maps"] == {
        "trained_semantic": 36,
        "pretrained_semantic": 36,
        "trained_evaluation": 61,
        "pretrained_evaluation": 62,
    }
    assert historical["unique_source_blobs_verified"] == 62
    assert historical["all_overlap_digests_agree"] is True
    assert historical["historical_script_blobs_verified"] == 3

    scope = attestation["claim_scope"]
    assert scope["bit_for_bit_base_weight_identity_attested"] is False
    assert scope["statistical_capability_claim"] is False
    assert scope["broad_theorem_proving_capability_claim"] is False
    assert scope["induction_capability_claim"] is False
    assert scope["causal_training_effect_claim"] is False

    core = {
        key: value
        for key, value in attestation.items()
        if key != "attestation_sha256"
    }
    assert attestation["attestation_sha256"] == paired._canonical_sha256(core)


def test_direct_trained_pretrained_cross_binding_mismatch_is_rejected() -> None:
    trained_report = deepcopy(_record(TRAINED_REPORT))
    provenance = trained_report["policy_identity"]["base_policy"]["provenance"]
    provenance["adapter_sha256"] = "0" * 64

    # Exercise the semantic binder directly: this negative is not merely a
    # consequence of the outer whole-file hash pin.
    with pytest.raises(
        paired.PairedEvaluationAttestationError,
        match="pretrained comparison authority versus trained provenance differs",
    ):
        paired._validate_pairing_records(
            trained_report=trained_report,
            pretrained_report=_record(PRETRAINED_REPORT),
            trained_attestation=_record(TRAINED_ATTESTATION),
            pretrained_attestation=_record(PRETRAINED_ATTESTATION),
            training_manifest=_record(TRAINING_MANIFEST),
        )
