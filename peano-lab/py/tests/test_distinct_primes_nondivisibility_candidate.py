"""Focused native-body audit for distinct-prime nondivisibility."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.distinct_primes_nondivisibility_candidate import (
    make_distinct_primes_nondivisibility_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "distinct_primes_left_not_divide_right",
    "distinct_primes_right_not_divide_left",
    "distinct_primes_mutually_nondivisible",
)
EXPECTED_DEPENDENCIES = {
    "distinct_primes_left_not_divide_right": ("prime_divisor_eq_one_or_self",),
    "distinct_primes_right_not_divide_left": (
        "distinct_primes_left_not_divide_right",
    ),
    "distinct_primes_mutually_nondivisible": (
        "distinct_primes_left_not_divide_right",
        "distinct_primes_right_not_divide_left",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "distinct_primes_left_not_divide_right":
        "2035f36c0c251c1843c2d69694c676d22f363ad5a786f44249c7466e741bba9d",
    "distinct_primes_right_not_divide_left":
        "a19bbb26bd2f707b835356543e75a25e80991948f9ecc46ce3b8a54df806989b",
    "distinct_primes_mutually_nondivisible":
        "dba0ab40691403c63d954610f16a275026a9e786be5d70902195a7a280ffa676",
}
EXPECTED_STATEMENT_LENGTH = {
    "distinct_primes_left_not_divide_right": 514,
    "distinct_primes_right_not_divide_left": 514,
    "distinct_primes_mutually_nondivisible": 586,
}
EXPECTED_BODY_RECEIPTS = {
    "distinct_primes_left_not_divide_right": (1, 19, 23, 13, 23, 22, 0),
    "distinct_primes_right_not_divide_left": (1, 18, 22, 14, 22, 21, 0),
    "distinct_primes_mutually_nondivisible": (2, 22, 44, 18, 44, 43, 0),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_distinct_primes_nondivisibility_candidate_theorems(TheoremSpec)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"distinct-prime nondivisibility replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_distinct_prime_nondivisibility_factory_is_exact_and_isolated() -> None:
    specs = _candidate_specs()
    assert make_distinct_primes_nondivisibility_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in specs
    } == EXPECTED_STATEMENT_SHA256
    assert {item.name: len(item.statement) for item in specs} == EXPECTED_STATEMENT_LENGTH
    public = _specs_by_name()
    assert all(item.name not in public for item in specs)


def test_distinct_prime_nondivisibility_contracts_are_native_and_closed() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in ("Prime(", "Dvd(", "∣"))


def test_distinct_prime_nondivisibility_scripts_are_constructive() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert "apply prime_divisor_eq_one_or_self" in commands
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_distinct_prime_nondivisibility_bodies_kernel_check() -> None:
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(_candidate_specs(), core=dict(_specs_by_name()))
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
