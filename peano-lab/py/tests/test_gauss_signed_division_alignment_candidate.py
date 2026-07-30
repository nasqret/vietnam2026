"""Focused body audit for exact Gauss/division sign alignment."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.gauss_magnitude_coprime_candidate import (
    make_gauss_magnitude_coprime_candidate_theorems,
)
from peano_lab.library.gauss_signed_division_alignment_candidate import (
    make_gauss_signed_division_alignment_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "odd_half_positive_complement_exists",
    "predecessor_multiple_mod_complement",
    "canonical_remainder_from_mod",
    "odd_signed_division_branch_exact",
)
EXPECTED_DEPENDENCIES = {
    "odd_half_positive_complement_exists": (
        "lt_irrefl_expanded",
        "nonzero_is_succ",
        "add_assoc",
        "add_comm",
        "mul_comm",
        "zero_add",
        "add_succ_left",
    ),
    "predecessor_multiple_mod_complement": (
        "mul_one",
        "mul_succ_left",
        "add_assoc",
        "add_comm",
    ),
    "canonical_remainder_from_mod": (
        "mul_comm",
        "remainder_decomposition_to_mod_eq",
        "mod_eq_symm",
        "mod_eq_trans",
        "mod_eq_bounded_unique",
    ),
    "odd_signed_division_branch_exact": (
        "odd_half_strictly_below_modulus",
        "lt_of_le_of_lt",
        "odd_half_positive_complement_exists",
        "predecessor_multiple_mod_complement",
        "canonical_remainder_from_mod",
        "mod_eq_trans",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "odd_half_positive_complement_exists":
        "682f4a514018334c49e4d46447f992c312e4166643cf9d8a5b39b97d37c957fe",
    "predecessor_multiple_mod_complement":
        "c138375b0d1fc72c86880e64acfc02ff774c593fe8909889db1d014bc4f56967",
    "canonical_remainder_from_mod":
        "fe7357e5c633d8cbae4fdb1db87f40f10a4fc5a8642034dc6ec25f126954195a",
    "odd_signed_division_branch_exact":
        "fadb151ae0310411370fa84c46b1901d5e1dd079e8cc0f4eaadc316c630efa21",
}
EXPECTED_BODY_RECEIPTS = {
    "odd_half_positive_complement_exists": (7, 59, 238, 39, 226, 237, 12),
    "predecessor_multiple_mod_complement": (4, 30, 53, 22, 52, 52, 1),
    "canonical_remainder_from_mod": (5, 43, 49, 24, 49, 48, 0),
    "odd_signed_division_branch_exact": (6, 90, 115, 35, 115, 114, 0),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_gauss_signed_division_alignment_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for item in make_gauss_magnitude_coprime_candidate_theorems(TheoremSpec):
        core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"signed division alignment replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_signed_division_alignment_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    assert make_gauss_signed_division_alignment_candidate_theorems(TheoremSpec) == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_signed_division_alignment_contracts_are_closed_expanded_native_pa() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in ("DivRem(", "ModEq(", "Signed(", "%", "<", "<=")
        )
    endpoint = _candidate_specs()[-1].statement
    assert "s = 0 /\\ r = m" in endpoint
    assert "s = 1 /\\ r + m = p" in endpoint


def test_signed_division_alignment_scripts_are_constructive_and_explicit() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert "apply mod_eq_bounded_unique" in commands
    assert "apply predecessor_multiple_mod_complement" in commands
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_signed_division_alignment_bodies_kernel_check_within_laptop_limit() -> None:
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(
            _candidate_specs(), core=_dependency_core()
        )
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
