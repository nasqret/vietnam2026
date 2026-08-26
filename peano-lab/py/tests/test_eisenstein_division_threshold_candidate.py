"""Focused native-body audit for the Eisenstein division threshold."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.eisenstein_division_threshold_candidate import (
    division_positive_multiple_threshold,
    make_eisenstein_division_threshold_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAME = "nonzero_remainder_division_positive_multiple_threshold"
EXPECTED_DEPENDENCIES = (
    "division_block_upper",
    "lt_trans",
    "le_or_lt",
    "mul_le_mul_left",
    "lt_not_le",
    "nonzero_is_succ",
    "add_comm",
    "lt_of_le_of_lt",
)
EXPECTED_STATEMENT_SHA256 = (
    "b8c1439640cf86bb0e408c03bed5575cca16fb81fa40b3cdc6a45230f261c085"
)
EXPECTED_BODY_METRICS = (92, 30, 91, 91, 1)
_BODY_DEADLINE_SECONDS = 60


def _candidate_spec() -> TheoremSpec:
    (candidate,) = make_eisenstein_division_threshold_candidate_theorems(
        TheoremSpec
    )
    return candidate


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Eisenstein threshold replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


@lru_cache(maxsize=1)
def _body_receipt():
    item = _candidate_spec()
    core = _specs_by_name()
    target = _closed_formula(item.statement)
    for dependency_name in reversed(item.dependencies):
        target = Imp(_closed_formula(core[dependency_name].statement), target)

    started = perf_counter()
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        state = start(target)
        for dependency_name in item.dependencies:
            state = apply_tactic(state, "intro", dependency_name)
        for command in item.script:
            tactic, arguments = _primitive(command)
            state = apply_tactic(state, tactic, arguments)

        certificate = checked_final(state, target)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)

    return (
        item.name,
        nodes,
        depth,
        objects,
        edges,
        reused,
        len(item.script),
        perf_counter() - started,
    )


def test_eisenstein_threshold_factory_has_exact_isolated_contract() -> None:
    first = _candidate_spec()
    second = _candidate_spec()

    assert second == first
    assert first.name == EXPECTED_NAME
    assert first.dependencies == EXPECTED_DEPENDENCIES
    assert sha256(first.statement.encode()).hexdigest() == EXPECTED_STATEMENT_SHA256
    assert first.name not in _specs_by_name()


def test_division_threshold_helper_is_hygienic_alpha_native_and_exact() -> None:
    left = division_positive_multiple_threshold(
        "p", "n", "q", "j", tag="alpha_left"
    )
    right = division_positive_multiple_threshold(
        "p", "n", "q", "j", tag="alpha_right"
    )

    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"p", "n", "q", "j"}
    assert "S (p * S j) = n" in left
    assert "+ (S j) = q" in left
    assert "<" not in left
    assert "<=" not in left

    with pytest.raises(ValueError, match="Peano identifier"):
        division_positive_multiple_threshold(
            "p + 1", "n", "q", "j", tag="bad"
        )
    with pytest.raises(ValueError, match="captures an argument"):
        division_positive_multiple_threshold(
            "edt_lt_gap_capture_below",
            "n",
            "q",
            "j",
            tag="capture",
        )
    with pytest.raises(ValueError, match="binder tag"):
        division_positive_multiple_threshold(
            "p", "n", "q", "j", tag="bad tag"
        )


def test_eisenstein_threshold_contract_is_closed_expanded_native_pa() -> None:
    item = _candidate_spec()
    formula, free_names = parse_formula_with_names(item.statement)

    assert not free_names
    assert formula == parse_formula(item.statement)
    assert formula == _closed_formula(item.statement)
    assert item.statement.startswith(
        "forall p n q r j. n = p * q + r -> ~(r = 0) ->"
    )
    assert "p * S j" in item.statement
    assert "+ (S j) = q" in item.statement
    assert all(
        token not in item.statement
        for token in ("DivRem(", "Floor(", "%", "<", "<=", "∣", "⌊")
    )


def test_eisenstein_threshold_body_is_constructive_and_bounded() -> None:
    name, nodes, depth, objects, edges, reused, commands, elapsed = _body_receipt()

    assert name == EXPECTED_NAME
    assert (nodes, depth, objects, edges, reused) == EXPECTED_BODY_METRICS
    assert commands == 67
    assert elapsed < _BODY_DEADLINE_SECONDS
    print(
        "EISENSTEIN THRESHOLD BODY RECEIPT "
        f"name={name} nodes={nodes} depth={depth} objects={objects} "
        f"edges={edges} reused={reused} commands={commands}",
        flush=True,
    )
