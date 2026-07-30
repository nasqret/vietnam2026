"""Tests for the fast, explicitly non-admitting candidate-body preflight."""

from __future__ import annotations

import pytest

from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.theorems import TheoremSpec


def _spec(
    name: str,
    statement: str,
    dependencies: tuple[str, ...],
    script: tuple[str, ...],
) -> TheoremSpec:
    return TheoremSpec(name, statement, dependencies, script, "test candidate")


def test_candidate_body_preflight_checks_dependency_curried_certificate() -> None:
    dependency = _spec("local_reflexive", "forall n. n = n", (), ("intro n", "refl"))
    candidate = _spec(
        "local_reflexive_consumer",
        "forall n. n = n",
        ("local_reflexive",),
        ("intro n", "refl"),
    )

    receipts = replay_candidate_bodies((dependency, candidate), core={})

    assert tuple(receipt.name for receipt in receipts) == (
        "local_reflexive",
        "local_reflexive_consumer",
    )
    assert receipts[1].dependency_count == 1
    assert receipts[1].command_count == 2
    assert receipts[1].proof_nodes > receipts[0].proof_nodes
    assert all(receipt.proof_depth > 0 for receipt in receipts)


def test_candidate_body_preflight_rejects_unknown_dependency() -> None:
    candidate = _spec(
        "missing_consumer",
        "forall n. n = n",
        ("not_available",),
        ("intro n", "refl"),
    )
    with pytest.raises(CandidateBodyError, match="unknown dependency"):
        replay_candidate_bodies((candidate,), core={})


def test_candidate_body_preflight_reports_exact_failing_command() -> None:
    candidate = _spec(
        "bad_body",
        "forall n. n = n",
        (),
        ("intro n", "split"),
    )
    with pytest.raises(CandidateBodyError, match=r"command 1: 'split'"):
        replay_candidate_bodies((candidate,), core={})
