"""Focused body audit for the explicitly conditional reciprocity wrappers."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.gauss_count_sum_parity_candidate import (
    make_gauss_count_sum_parity_candidate_theorems,
)
from peano_lab.library.quadratic_reciprocity_conditional_candidate import (
    make_quadratic_reciprocity_conditional_candidate_theorems,
)
from peano_lab.library.quadratic_reciprocity_parity_candidate import (
    make_quadratic_reciprocity_parity_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "conditional_qres_same_status_from_oriented_gauss_counts",
    "conditional_qres_opposite_status_from_oriented_gauss_counts",
)
EXPECTED_DEPENDENCIES = {
    "conditional_qres_same_status_from_oriented_gauss_counts": (
        "gauss_count_sum_mod_two_from_quotient_sums",
        "qres_same_status_from_mod_four_one",
    ),
    "conditional_qres_opposite_status_from_oriented_gauss_counts": (
        "gauss_count_sum_mod_two_from_quotient_sums",
        "qres_opposite_status_from_mod_four_three",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "conditional_qres_same_status_from_oriented_gauss_counts": (
        "77bef7a0c39cb63bea30f0a617c1f7c1e9654a9b4fce742892eb955910151250"
    ),
    "conditional_qres_opposite_status_from_oriented_gauss_counts": (
        "6b2189b0db7adab3b699111219eeb5d134adcecff628b192e1e6bc359fa0c870"
    ),
}
EXPECTED_STATEMENT_LENGTH = {
    "conditional_qres_same_status_from_oriented_gauss_counts": 2_257,
    "conditional_qres_opposite_status_from_oriented_gauss_counts": 2_265,
}
EXPECTED_BODY_RECEIPTS = {
    "conditional_qres_same_status_from_oriented_gauss_counts": (
        2, 40, 49, 31, 49, 48, 0,
    ),
    "conditional_qres_opposite_status_from_oriented_gauss_counts": (
        2, 40, 49, 31, 49, 48, 0,
    ),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_quadratic_reciprocity_conditional_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_gauss_count_sum_parity_candidate_theorems,
        make_quadratic_reciprocity_parity_candidate_theorems,
    ):
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"conditional reciprocity replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_conditional_reciprocity_factory_is_exact_ordered_and_isolated() -> None:
    specs = _candidate_specs()
    assert make_quadratic_reciprocity_conditional_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in specs
    } == EXPECTED_STATEMENT_SHA256
    assert {item.name: len(item.statement) for item in specs} == EXPECTED_STATEMENT_LENGTH
    public = _specs_by_name()
    assert all(item.name not in public for item in specs)


def test_conditional_reciprocity_contracts_are_closed_expanded_native_pa() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert item.statement.startswith("forall p q e f Q U h k.")
        assert "p = 2 * h + 1" in item.statement
        assert "q = 2 * k + 1" in item.statement
        assert "Q + U = h * k" in item.statement
        assert all(
            token not in item.statement
            for token in ("QRes(", "Even(", "Odd(", "ModEq(", "%", "<", "<=")
        )
    same, opposite = _candidate_specs()
    assert "4 * qrc_one_p" in same.statement
    assert "4 * qrc_one_q" in same.statement
    assert "4 * qrc_three_p" in opposite.statement
    assert "4 * qrc_three_q" in opposite.statement


def test_conditional_reciprocity_scripts_are_constructive_and_explicit() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert commands.count("apply gauss_count_sum_mod_two_from_quotient_sums") == 2
    assert "apply qres_same_status_from_mod_four_one" in commands
    assert "apply qres_opposite_status_from_mod_four_three" in commands
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all(
        fragment not in command
        for command in commands
        for fragment in ("DNE", "by_contra", "classical", "sorry")
    )


def test_conditional_reciprocity_bodies_kernel_check_within_laptop_limit() -> None:
    started = perf_counter()
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(_candidate_specs(), core=_dependency_core())
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
        f"CONDITIONAL RECIPROCITY BODY RECEIPTS elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
