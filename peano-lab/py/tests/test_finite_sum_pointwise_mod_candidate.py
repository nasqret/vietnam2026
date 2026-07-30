"""Focused body audit for pointwise congruence over exact beta Sums."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.finite_sum_pointwise_mod_candidate import (
    make_finite_sum_pointwise_mod_candidate_theorems,
)
from peano_lab.library.parity_mod_two_candidate import (
    make_parity_mod_two_candidate_theorems,
)
from peano_lab.library.parity_sum_classification_candidate import (
    make_parity_sum_classification_candidate_theorems,
)
from peano_lab.library.signed_division_parity_bridge_candidate import (
    make_signed_division_parity_bridge_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "mod_eq_add_cancel_left",
    "mod_two_cancel_middle",
    "mod_two_zero_sum_to_congruent",
    "beta_sum_pointwise_mod_three_add",
)
EXPECTED_DEPENDENCIES = {
    "mod_eq_add_cancel_left": ("add_left_cancel", "add_assoc"),
    "mod_two_cancel_middle": (
        "mod_eq_add_cancel_left",
        "add_assoc",
        "add_comm",
    ),
    "mod_two_zero_sum_to_congruent": (
        "mod_eq_symm",
        "mod_two_zero_to_even",
        "even_sum_parity_cases",
        "matching_parity_mod_two",
    ),
    "beta_sum_pointwise_mod_three_add": (
        "beta_sum_zero",
        "beta_sum_succ_decompose",
        "mod_eq_add",
        "le_succ",
        "le_refl",
        "add_assoc",
        "add_comm",
        "add_permute_outer",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "mod_eq_add_cancel_left": (
        "2dfa98ec8006d553d44bd99dabe7b140a4d391a404e6dab15e06197eb7f1e68e"
    ),
    "mod_two_cancel_middle": (
        "e079572b7996e39ee324ac94ab1d720c57f5c8f9875018d290bf4933925c5e71"
    ),
    "mod_two_zero_sum_to_congruent": (
        "08bd257273d64d67ed0abf706fa1757e0b3df91908a1556ad194bdc8cdc699a9"
    ),
    "beta_sum_pointwise_mod_three_add": (
        "3e9186ff019d7ecb1b9b8a6563db5320d8a136d0bfad9c55987ae57659e37591"
    ),
}
EXPECTED_STATEMENT_LENGTH = {
    "mod_eq_add_cancel_left": 254,
    "mod_two_cancel_middle": 312,
    "mod_two_zero_sum_to_congruent": 262,
    "beta_sum_pointwise_mod_three_add": 8_453,
}
EXPECTED_BODY_RECEIPTS = {
    "mod_eq_add_cancel_left": (2, 19, 39, 24, 39, 38, 0),
    "mod_two_cancel_middle": (3, 16, 42, 19, 42, 41, 0),
    "mod_two_zero_sum_to_congruent": (4, 22, 24, 15, 24, 23, 0),
    "beta_sum_pointwise_mod_three_add": (8, 181, 328, 66, 328, 327, 0),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_finite_sum_pointwise_mod_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    factories = (
        make_parity_mod_two_candidate_theorems,
        make_parity_sum_classification_candidate_theorems,
        make_signed_division_parity_bridge_candidate_theorems,
    )
    for factory in factories:
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"pointwise Sum congruence replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_pointwise_sum_mod_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_finite_sum_pointwise_mod_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    assert {item.name: len(item.statement) for item in first} == (
        EXPECTED_STATEMENT_LENGTH
    )
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_pointwise_sum_mod_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = (
        "BetaAt(",
        "Congruent(",
        "List(",
        "ModEq(",
        "Product(",
        "Sum(",
        "%",
        "<=",
        "<",
        "^",
        "∣",
    )
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)

    cancel, middle, zero_sum, aggregate = _candidate_specs()
    assert cancel.statement.startswith("forall d a b c.")
    assert middle.statement.startswith("forall x q s.")
    assert zero_sum.statement.startswith("forall q e.")
    assert aggregate.statement.startswith(
        "forall d b c qb qc mb mc sb sc l X Q M E."
    )
    assert "(X) + d *" in aggregate.statement
    assert "(Q + M + E) + d *" in aggregate.statement


def test_pointwise_sum_mod_scripts_are_constructive_and_explicit() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert "apply mod_eq_add" in commands
    assert "apply add_left_cancel" in commands
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_pointwise_sum_mod_bodies_kernel_check_within_laptop_limit() -> None:
    started = perf_counter()
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(
            _candidate_specs(), core=_dependency_core()
        )
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
        f"POINTWISE SUM MOD BODY RECEIPTS elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
