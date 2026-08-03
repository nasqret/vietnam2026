"""Focused audit for complementary cells exposed by outer row prefixes."""

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
from peano_lab.library.eisenstein_rectangle_count_candidate import (
    make_eisenstein_rectangle_count_candidate_theorems,
)
from peano_lab.library.eisenstein_transposed_cell_candidate import (
    make_eisenstein_transposed_cell_candidate_theorems,
)
from peano_lab.library.eisenstein_transposed_outer_cell_candidate import (
    make_eisenstein_transposed_outer_cell_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAME = "eisenstein_transposed_outer_prefix_cell_witness"
EXPECTED_DEPENDENCIES = (
    "eisenstein_rectangle_decoded_row_count",
    "beta_at_exists",
    "eisenstein_transposed_decoded_cell_bits_complementary",
)
EXPECTED_STATEMENT_SHA256 = (
    "6ddfd6cd709172d148c3623722c9dc3a780da27d423e49ec62e8e8e2119b08bd"
)
EXPECTED_BODY_METRICS = (116, 58, 116, 115, 0)
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_spec() -> TheoremSpec:
    (candidate,) = make_eisenstein_transposed_outer_cell_candidate_theorems(
        TheoremSpec
    )
    return candidate


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_eisenstein_rectangle_count_candidate_theorems,
        make_eisenstein_transposed_cell_candidate_theorems,
    ):
        core.update({item.name: item for item in factory(TheoremSpec)})
    return core


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"transposed outer-cell replay exceeded {seconds}s")

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
    core = _dependency_core()
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


def test_transposed_outer_cell_factory_is_exact_and_isolated() -> None:
    first = _candidate_spec()
    second = make_eisenstein_transposed_outer_cell_candidate_theorems(
        TheoremSpec
    )[0]

    assert second == first
    assert first.name == EXPECTED_NAME
    assert first.dependencies == EXPECTED_DEPENDENCIES
    assert len(first.script) == 101
    assert sha256(first.statement.encode()).hexdigest() == EXPECTED_STATEMENT_SHA256
    assert first.name not in _specs_by_name()


def test_transposed_outer_cell_contract_is_closed_expanded_native_pa() -> None:
    item = _candidate_spec()
    formula, free_names = parse_formula_with_names(item.statement)

    assert not free_names
    assert formula == parse_formula(item.statement)
    assert formula == _closed_formula(item.statement)
    assert item.statement.startswith("forall p q h k ab ac bb bc i j n m.")
    assert "((a = 0 /\\ d = 1) \\/ (a = 1 /\\ d = 0))" in item.statement
    assert all(
        token not in item.statement
        for token in (
            "BetaAt(",
            "BitCount(",
            "Rectangle(",
            "RowIndicator(",
            "<=",
            "<",
            "%",
            "∣",
        )
    )


def test_transposed_outer_cell_body_is_constructive_and_bounded() -> None:
    nodes, depth, objects, edges, reused, elapsed = _body_receipt()

    assert (nodes, depth, objects, edges, reused) == EXPECTED_BODY_METRICS
    assert elapsed < _BODY_DEADLINE_SECONDS
    print(
        "EISENSTEIN TRANSPOSED OUTER CELL BODY RECEIPT "
        f"name={EXPECTED_NAME} nodes={nodes} depth={depth} objects={objects} "
        f"edges={edges} reused={reused} commands=101",
        flush=True,
    )
