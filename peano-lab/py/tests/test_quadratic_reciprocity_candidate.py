"""Focused audit for the exact native quadratic-reciprocity endpoints."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.gauss_eisenstein_data_candidate import (
    make_gauss_eisenstein_data_candidate_theorems,
)
from peano_lab.library.quadratic_reciprocity_candidate import (
    make_quadratic_reciprocity_candidate_theorems,
)
from peano_lab.library.quadratic_reciprocity_conditional_candidate import (
    make_quadratic_reciprocity_conditional_candidate_theorems,
)
from peano_lab.library.quadratic_residue_surface import (
    QUADRATIC_RECIPROCITY_COMBINED,
    QUADRATIC_RECIPROCITY_OPPOSITE_CASE,
    QUADRATIC_RECIPROCITY_SAME_CASE,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "quadratic_reciprocity_same_case",
    "quadratic_reciprocity_opposite_case",
    "quadratic_reciprocity_combined",
)
EXPECTED_DEPENDENCIES = {
    "quadratic_reciprocity_same_case": (
        "distinct_odd_primes_gauss_eisenstein_data_exists",
        "conditional_qres_same_status_from_oriented_gauss_counts",
    ),
    "quadratic_reciprocity_opposite_case": (
        "distinct_odd_primes_gauss_eisenstein_data_exists",
        "conditional_qres_opposite_status_from_oriented_gauss_counts",
    ),
    "quadratic_reciprocity_combined": (
        "distinct_odd_primes_gauss_eisenstein_data_exists",
        "conditional_qres_same_status_from_oriented_gauss_counts",
        "conditional_qres_opposite_status_from_oriented_gauss_counts",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "quadratic_reciprocity_same_case": (
        "ae71a75ff5df37668acd3758e1732a5a5291eb9a27312e1057cb2ac70927d2ea"
    ),
    "quadratic_reciprocity_opposite_case": (
        "1c8a26d5b017a79c96ac8b7512060bfe42cc69d09c7e8d178e96b197c2b9e03d"
    ),
    "quadratic_reciprocity_combined": (
        "2a95f83a5a21a5e21e482d5de8a19d55ee1843f676f086438f8a9853b6a97070"
    ),
}
EXPECTED_STATEMENT_LENGTH = {
    "quadratic_reciprocity_same_case": 980,
    "quadratic_reciprocity_opposite_case": 988,
    "quadratic_reciprocity_combined": 1_520,
}
EXPECTED_BODY_RECEIPTS = {
    "quadratic_reciprocity_same_case": (2, 46, 73, 33, 73, 72, 0),
    "quadratic_reciprocity_opposite_case": (2, 46, 73, 33, 73, 72, 0),
    "quadratic_reciprocity_combined": (3, 65, 113, 35, 113, 112, 0),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_quadratic_reciprocity_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_gauss_eisenstein_data_candidate_theorems,
        make_quadratic_reciprocity_conditional_candidate_theorems,
    ):
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"quadratic-reciprocity body replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_quadratic_reciprocity_factory_is_exact_ordered_and_isolated() -> None:
    specs = _candidate_specs()
    assert make_quadratic_reciprocity_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in specs
    } == EXPECTED_STATEMENT_SHA256
    assert {item.name: len(item.statement) for item in specs} == EXPECTED_STATEMENT_LENGTH
    assert tuple(item.statement for item in specs) == (
        QUADRATIC_RECIPROCITY_SAME_CASE,
        QUADRATIC_RECIPROCITY_OPPOSITE_CASE,
        QUADRATIC_RECIPROCITY_COMBINED,
    )
    public = _specs_by_name()
    assert all(item.name not in public for item in specs)


def test_quadratic_reciprocity_contracts_are_closed_native_pa() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert item.statement.startswith("forall p q.")
        assert all(
            token not in item.statement
            for token in (
                "QRes(", "Prime(", "Odd(", "Even(", "ModEq(",
                "BetaAt(", "Sum(", "%", "<", "<=",
            )
        )


def test_quadratic_reciprocity_scripts_are_constructive_and_explicit() -> None:
    specs = _candidate_specs()
    commands = tuple(command for item in specs for command in item.script)
    assert commands.count("apply distinct_odd_primes_gauss_eisenstein_data_exists") == 3
    assert commands.count(
        "apply conditional_qres_same_status_from_oriented_gauss_counts"
    ) == 2
    assert commands.count(
        "apply conditional_qres_opposite_status_from_oriented_gauss_counts"
    ) == 2
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all(
        fragment not in command
        for command in commands
        for fragment in ("DNE", "by_contra", "classical", "sorry")
    )


def test_quadratic_reciprocity_bodies_kernel_check_within_laptop_limit() -> None:
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
        f"QUADRATIC RECIPROCITY BODY RECEIPTS elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
