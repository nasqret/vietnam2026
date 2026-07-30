"""Focused body audit for the complete Gauss--Eisenstein data package."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.distinct_primes_nondivisibility_candidate import (
    make_distinct_primes_nondivisibility_candidate_theorems,
)
from peano_lab.library.eisenstein_quotient_sum_identity_candidate import (
    make_eisenstein_quotient_sum_identity_candidate_theorems,
)
from peano_lab.library.eisenstein_rectangle_count_candidate import (
    make_eisenstein_rectangle_count_candidate_theorems,
)
from peano_lab.library.eisenstein_scaled_division_candidate import (
    make_eisenstein_scaled_division_candidate_theorems,
)
from peano_lab.library.gauss_eisenstein_data_candidate import (
    make_gauss_eisenstein_data_candidate_theorems,
)
from peano_lab.library.gauss_eisenstein_sum_candidate import (
    make_gauss_eisenstein_sum_candidate_theorems,
)
from peano_lab.library.gauss_lemma_arbitrary_candidate import (
    make_gauss_lemma_arbitrary_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "odd_prime_gauss_eisenstein_orientation_data_exists",
    "distinct_odd_primes_gauss_eisenstein_data_exists",
)
EXPECTED_DEPENDENCIES = {
    "odd_prime_gauss_eisenstein_orientation_data_exists": (
        "beta_range_exists",
        "arbitrary_gauss_lemma_complete",
        "prime_scaled_half_quotient_sum_exists",
        "gauss_eisenstein_sign_count_mod_quotient_sum",
        "mod_eq_symm",
    ),
    "distinct_odd_primes_gauss_eisenstein_data_exists": (
        "distinct_primes_mutually_nondivisible",
        "odd_prime_gauss_eisenstein_orientation_data_exists",
        "distinct_odd_prime_half_rectangle_total_exists",
        "distinct_odd_prime_eisenstein_quotient_sum_identity",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "odd_prime_gauss_eisenstein_orientation_data_exists": (
        "6448a5aaa39ad5eb6e8454733a3a1843e113d72df0d43153f9ae72b1b4263325"
    ),
    "distinct_odd_primes_gauss_eisenstein_data_exists": (
        "82904526598c84de0e56fd23b9b1302cd13720e42172c50535114474af223d06"
    ),
}
EXPECTED_STATEMENT_LENGTH = {
    "odd_prime_gauss_eisenstein_orientation_data_exists": 6_967,
    "distinct_odd_primes_gauss_eisenstein_data_exists": 4_355,
}
EXPECTED_BODY_RECEIPTS = {
    "odd_prime_gauss_eisenstein_orientation_data_exists": (
        5, 102, 139, 67, 139, 138, 0,
    ),
    "distinct_odd_primes_gauss_eisenstein_data_exists": (
        4, 150, 222, 77, 222, 221, 0,
    ),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_gauss_eisenstein_data_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_gauss_lemma_arbitrary_candidate_theorems,
        make_eisenstein_scaled_division_candidate_theorems,
        make_gauss_eisenstein_sum_candidate_theorems,
        make_distinct_primes_nondivisibility_candidate_theorems,
        make_eisenstein_rectangle_count_candidate_theorems,
        make_eisenstein_quotient_sum_identity_candidate_theorems,
    ):
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Gauss--Eisenstein data replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_data_factory_is_exact_ordered_and_isolated() -> None:
    specs = _candidate_specs()
    assert make_gauss_eisenstein_data_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in specs
    } == EXPECTED_STATEMENT_SHA256
    assert {item.name: len(item.statement) for item in specs} == EXPECTED_STATEMENT_LENGTH
    public = _specs_by_name()
    assert all(item.name not in public for item in specs)


def test_data_contracts_are_closed_expanded_native_pa() -> None:
    orientation, pair = _candidate_specs()
    for item in (orientation, pair):
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "Prime(", "QRes(", "Even(", "Odd(", "ModEq(",
                "BetaAt(", "DivRem(", "Sum(", "%", "<=", "<", "∣",
            )
        )
    assert orientation.statement.startswith("forall p h a. p = 2 * h + 1")
    assert "exists tb tc qb qc rb rc e Q." in orientation.statement
    assert pair.statement.startswith(
        "forall p q h k. p = 2 * h + 1 -> q = 2 * k + 1"
    )
    assert "exists e f Q U." in pair.statement
    assert "Q + U = h * k" in pair.statement
    assert all(name not in pair.statement for name in ("tb", "tc", "qb", "qc", "rb", "rc"))


def test_data_scripts_are_constructive_and_use_the_intended_join() -> None:
    orientation, pair = _candidate_specs()
    assert orientation.script.count("apply arbitrary_gauss_lemma_complete") == 1
    assert orientation.script.count("apply prime_scaled_half_quotient_sum_exists") == 1
    assert orientation.script.count(
        "apply gauss_eisenstein_sign_count_mod_quotient_sum"
    ) == 1
    assert pair.script.count(
        "apply odd_prime_gauss_eisenstein_orientation_data_exists"
    ) == 2
    assert pair.script.count(
        "apply distinct_odd_prime_half_rectangle_total_exists"
    ) == 2
    assert pair.script.count(
        "apply distinct_odd_prime_eisenstein_quotient_sum_identity"
    ) == 1
    commands = orientation.script + pair.script
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all(
        fragment not in command
        for command in commands
        for fragment in ("DNE", "by_contra", "classical", "sorry")
    )


def test_data_bodies_kernel_check_within_laptop_limit() -> None:
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
        f"GAUSS EISENSTEIN DATA BODY RECEIPTS elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
