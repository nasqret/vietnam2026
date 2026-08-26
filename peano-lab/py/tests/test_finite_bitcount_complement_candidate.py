"""Focused native-body audit for complementary beta-bit counts."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.finite_bitcount_complement_candidate import (
    make_finite_bitcount_complement_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAME = "complementary_bit_counts_add_length"
EXPECTED_DEPENDENCIES = (
    "bit_count_zero",
    "bit_count_succ_decompose",
    "le_succ",
    "le_refl",
    "add_succ_left",
)
EXPECTED_STATEMENT_SHA256 = (
    "233fdf090aeec2383f7da78f56ec559c8c35ec10f2b7d2d776718cac2501e4bd"
)
EXPECTED_BODY_METRICS = (220, 46, 211, 219, 9)
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_spec() -> TheoremSpec:
    (candidate,) = make_finite_bitcount_complement_candidate_theorems(
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
        raise TimeoutError(f"complementary BitCount replay exceeded {seconds}s")

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
    return nodes, depth, objects, edges, reused, perf_counter() - started


def test_complement_count_factory_is_exact_deterministic_and_isolated() -> None:
    first = _candidate_spec()
    second = make_finite_bitcount_complement_candidate_theorems(TheoremSpec)[0]

    assert second == first
    assert first.name == EXPECTED_NAME
    assert first.dependencies == EXPECTED_DEPENDENCIES
    assert len(first.script) == 112
    assert sha256(first.statement.encode()).hexdigest() == EXPECTED_STATEMENT_SHA256
    assert first.name not in _specs_by_name()


def test_complement_count_contract_is_closed_expanded_native_pa() -> None:
    item = _candidate_spec()
    formula, free_names = parse_formula_with_names(item.statement)

    assert not free_names
    assert formula == parse_formula(item.statement)
    assert formula == _closed_formula(item.statement)
    assert item.statement.startswith("forall b c z e l n m.")
    assert "((a = 0 /\\ d = 1) \\/ (a = 1 /\\ d = 0))" in item.statement
    assert item.statement.endswith("n + m = l")
    assert all(
        token not in item.statement
        for token in ("BetaAt(", "BitCount(", "List(", "<=", "<", "%", "∣")
    )


def test_complement_count_body_is_constructive_and_bounded() -> None:
    nodes, depth, objects, edges, reused, elapsed = _body_receipt()

    assert (nodes, depth, objects, edges, reused) == EXPECTED_BODY_METRICS
    assert elapsed < _BODY_DEADLINE_SECONDS
    print(
        "COMPLEMENTARY BITCOUNT BODY RECEIPT "
        f"name={EXPECTED_NAME} nodes={nodes} depth={depth} objects={objects} "
        f"edges={edges} reused={reused} commands=112",
        flush=True,
    )
