"""Focused native-body audit for complete parity classification of sums."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.parity_sum_classification_candidate import (
    make_parity_sum_classification_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "even_sum_parity_cases",
    "odd_sum_parity_cases",
    "even_sum_iff_same_parity",
    "odd_sum_iff_opposite_parity",
)
EXPECTED_DEPENDENCIES = {
    "even_sum_parity_cases": (
        "parity_cases",
        "even_add_odd",
        "odd_add_even",
        "even_not_odd",
    ),
    "odd_sum_parity_cases": (
        "parity_cases",
        "even_add_even",
        "odd_add_odd",
        "odd_not_even",
    ),
    "even_sum_iff_same_parity": (
        "even_sum_parity_cases",
        "even_add_even",
        "odd_add_odd",
    ),
    "odd_sum_iff_opposite_parity": (
        "odd_sum_parity_cases",
        "even_add_odd",
        "odd_add_even",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "even_sum_parity_cases": (
        "1a3f2b8787f3561cb421c4ce4053cc16575a3cea3040e87ae3cb1ac0cd2f3b5e"
    ),
    "odd_sum_parity_cases": (
        "36883b9e2eadd7b185b652b69ebeaf40e10c9dc2be95ce6a89d3618bfb2a5d1d"
    ),
    "even_sum_iff_same_parity": (
        "41e3c7ad8f14543a6c99503544b71c943084bb0b3c786581442f70ef3dccff85"
    ),
    "odd_sum_iff_opposite_parity": (
        "21e3b195f2abe054cd77c0a569e124904ee9539bebf03fa28c5715c5f27b8669"
    ),
}
EXPECTED_BODY_RECEIPTS = {
    "even_sum_parity_cases": (4, 52, 61, 18, 61, 60, 0),
    "odd_sum_parity_cases": (4, 52, 61, 18, 61, 60, 0),
    "even_sum_iff_same_parity": (3, 22, 63, 19, 63, 62, 0),
    "odd_sum_iff_opposite_parity": (3, 22, 63, 19, 63, 62, 0),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_parity_sum_classification_candidate_theorems(TheoremSpec)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"sum-parity classification replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_sum_parity_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_parity_sum_classification_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_sum_parity_contracts_are_closed_expanded_native_pa() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in ("Even(", "Odd(", "Parity(", "%", "<", "<=")
        )

    assert _candidate_specs()[0].statement.startswith("forall m n.")
    assert "m + n = 2 *" in _candidate_specs()[0].statement
    assert "m + n = 2 *" in _candidate_specs()[1].statement


def test_sum_parity_scripts_have_no_automation_or_classical_escape() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_sum_parity_bodies_kernel_check_within_laptop_limit() -> None:
    started = perf_counter()
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(_candidate_specs())
    elapsed = perf_counter() - started
    observed = {
        receipt.name: (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    }
    assert observed == EXPECTED_BODY_RECEIPTS
    assert elapsed < _BODY_DEADLINE_SECONDS
    print(
        f"SUM PARITY BODY RECEIPTS elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
