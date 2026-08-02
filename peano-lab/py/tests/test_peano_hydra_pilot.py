"""Executable, honestly labeled teacher-oracle plumbing pilot."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
COMMITTED_REPORT = (
    ROOT / "artifacts" / "peano-hydra" / "teacher-oracle-pilot-v1.json"
)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_hydra.pilot import (  # noqa: E402
    DEFAULT_ARTIFACT_COMMANDS,
    DEFAULT_ARTIFACT_PROOF_NODES,
    DEFAULT_ARTIFACT_SHA256,
    MUTATED_THEOREM,
    PILOT_LIMITS,
    TEACHER_ORACLE_LABEL,
    run_teacher_oracle_pilot,
)


def test_teacher_oracle_pilot_is_paired_checked_and_explicitly_not_capability() -> None:
    report = run_teacher_oracle_pilot()

    assert report.artifact.path == "artifacts/triangular-even-readable.pa"
    assert report.artifact.sha256 == DEFAULT_ARTIFACT_SHA256
    assert len(report.artifact.commands) == DEFAULT_ARTIFACT_COMMANDS == 13
    assert report.artifact.replay.status == "proved"
    assert report.artifact.replay.kernel_checked is True
    assert report.artifact.replay.proof_nodes == DEFAULT_ARTIFACT_PROOF_NODES == 180

    assert report.control.status == "exhausted"
    assert report.control.proved is False
    assert report.control.eligible_for_comparison is False
    assert report.hybrid.status == "proof"
    assert report.hybrid.proved is True
    assert report.hybrid.eligible_for_comparison is False
    assert report.hybrid.commands == report.artifact.commands
    assert report.hybrid.search.certificate_nodes == 180
    assert report.hybrid.replay is not None
    assert report.hybrid.replay.kernel_checked is True
    assert report.hybrid.replay.theorem == report.artifact.canonical_theorem
    assert report.hybrid.replay.proof_nodes == 180
    assert report.control.limits == report.hybrid.limits
    assert report.control.environment == report.hybrid.environment
    assert report.control.limits == {
        "max_depth": PILOT_LIMITS.max_depth,
        "beam_width": PILOT_LIMITS.beam_width,
        "candidates_per_state": PILOT_LIMITS.candidates_per_state,
        "max_model_calls": PILOT_LIMITS.max_model_calls,
        "max_states": PILOT_LIMITS.max_states,
    }

    assert len(report.macro_state_sha256s) == 10
    macro_records = tuple(
        record
        for record in report.hybrid.proposal_records
        if record["role"] == "macro"
    )
    assert len(macro_records) == 13
    assert sum(record["outcome"] == "ok" for record in macro_records) == 10
    assert sum(record["outcome"] == "gated" for record in macro_records) == 3
    assert all(
        record["requested"] == 1
        for record in macro_records
        if record["outcome"] == "ok"
    )

    assert report.mutation.theorem.endswith("= 2 · y + 1")
    assert MUTATED_THEOREM.endswith("= 2 * x + 1")
    assert report.mutation.status == "exhausted"
    assert report.mutation.proved is False
    assert report.mutation.eligible_for_comparison is False
    mutation_macro = tuple(
        record
        for record in report.mutation.proposal_records
        if record["role"] == "macro"
    )
    assert len(mutation_macro) == 1
    assert mutation_macro[0]["outcome"] == "gated"
    assert mutation_macro[0]["requested"] == 0

    payload = report.to_dict(include_trace=True)
    assert payload["experiment"] == TEACHER_ORACLE_LABEL
    assert "not Qwen capability" in payload["claim_boundary"]
    assert "not negative-decision evidence" in payload[
        "mutation_integrity_check"
    ]["claim_boundary"]
    assert payload["outcome"] == {
        "control_status": "exhausted",
        "hybrid_status": "proof",
        "hybrid_kernel_checked": True,
        "hybrid_commands_match_teacher": True,
        "hybrid_proof_nodes": 180,
        "mutated_theorem_status": "exhausted",
        "mutated_transcript_rejected": True,
    }
    assert payload["hybrid"]["replay"]["trace"][-1]["qed"] is True
    assert json.loads(report.json(indent=None))["experiment"] == TEACHER_ORACLE_LABEL
    assert report.json(indent=2, include_trace=True) + "\n" == (
        COMMITTED_REPORT.read_text(encoding="utf-8")
    )
