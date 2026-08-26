"""Focused native-body audit for exact beta-sum transport."""

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
from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.finite_sum_transport_candidate import (
    make_finite_sum_transport_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAME = "beta_sum_transport_prefix"
EXPECTED_STATEMENT_SHA256 = (
    "ef6c6fcebc40c7149a557d9037414398349e241100405799e4fc2bbd5c9913b0"
)
EXPECTED_BODY_METRICS = (59, 29, 59, 58, 0)
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_spec() -> TheoremSpec:
    (candidate,) = make_finite_sum_transport_candidate_theorems(TheoremSpec)
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
        raise TimeoutError(f"beta-sum transport replay exceeded {seconds}s")

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
    target = _closed_formula(item.statement)
    started = perf_counter()
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        state = start(target)
        for command in item.script:
            tactic, arguments = _primitive(command)
            state = apply_tactic(state, tactic, arguments)
        certificate = checked_final(state, target)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
    return nodes, depth, objects, edges, reused, perf_counter() - started


def test_sum_transport_factory_is_exact_deterministic_and_isolated() -> None:
    first = _candidate_spec()
    second = make_finite_sum_transport_candidate_theorems(TheoremSpec)[0]

    assert second == first
    assert first.name == EXPECTED_NAME
    assert first.dependencies == ()
    assert len(first.script) == 44
    assert sha256(first.statement.encode()).hexdigest() == EXPECTED_STATEMENT_SHA256
    assert first.name not in _specs_by_name()


def test_sum_transport_contract_is_closed_expanded_native_pa() -> None:
    item = _candidate_spec()
    formula, free_names = parse_formula_with_names(item.statement)

    assert not free_names
    assert formula == parse_formula(item.statement)
    assert formula == _closed_formula(item.statement)
    assert item.statement.startswith("forall b c z e l n.")
    assert "forall i a." in item.statement
    assert "h + S i = l" in item.statement
    assert all(
        token not in item.statement
        for token in ("BetaAt(", "Sum(", "List(", "<=", "<", "%", "∣")
    )


def test_sum_transport_body_is_constructive_and_bounded() -> None:
    nodes, depth, objects, edges, reused, elapsed = _body_receipt()

    assert (nodes, depth, objects, edges, reused) == EXPECTED_BODY_METRICS
    assert elapsed < _BODY_DEADLINE_SECONDS
    print(
        "BETA SUM TRANSPORT BODY RECEIPT "
        f"name={EXPECTED_NAME} nodes={nodes} depth={depth} objects={objects} "
        f"edges={edges} reused={reused} commands=44",
        flush=True,
    )
