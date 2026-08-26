"""Focused body audit for the constructive reciprocity parity split."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.parity_mod_two_candidate import (
    make_parity_mod_two_candidate_theorems,
)
from peano_lab.library.parity_odd_half_mod_four_candidate import (
    make_parity_odd_half_mod_four_candidate_theorems,
)
from peano_lab.library.parity_sum_classification_candidate import (
    make_parity_sum_classification_candidate_theorems,
)
from peano_lab.library.quadratic_reciprocity_parity_candidate import (
    make_quadratic_reciprocity_parity_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "qres_same_status_from_even_count_sum",
    "qres_opposite_status_from_odd_count_sum",
    "qres_same_status_from_even_half_product_mod_two",
    "qres_opposite_status_from_odd_half_product_mod_two",
    "qres_same_status_from_mod_four_one",
    "qres_opposite_status_from_mod_four_three",
)
EXPECTED_DEPENDENCIES = {
    "qres_same_status_from_even_count_sum": ("even_sum_parity_cases",),
    "qres_opposite_status_from_odd_count_sum": ("odd_sum_parity_cases",),
    "qres_same_status_from_even_half_product_mod_two": (
        "mod_two_preserves_parity",
        "qres_same_status_from_even_count_sum",
    ),
    "qres_opposite_status_from_odd_half_product_mod_two": (
        "mod_two_preserves_parity",
        "qres_opposite_status_from_odd_count_sum",
    ),
    "qres_same_status_from_mod_four_one": (
        "odd_half_even_iff_mod4_one",
        "even_mul_left",
        "even_mul_right",
        "qres_same_status_from_even_half_product_mod_two",
    ),
    "qres_opposite_status_from_mod_four_three": (
        "odd_half_odd_iff_mod4_three",
        "odd_mul_odd",
        "qres_opposite_status_from_odd_half_product_mod_two",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "qres_same_status_from_even_count_sum":
        "5df74f9fc441594b538acf03bd3ec02f6a1a08d19801728fea45480e8351cb1f",
    "qres_opposite_status_from_odd_count_sum":
        "1c34fc7d331fe1cd9a24b243224d2abf28d9f5e57fc3f9c16ae8bd3166303d63",
    "qres_same_status_from_even_half_product_mod_two":
        "777b64e0c3319b4d14ccf1c8b9a77dd032917a0147917c4608041a9795d30e47",
    "qres_opposite_status_from_odd_half_product_mod_two":
        "d8776653a10a8c7108fa54cf2808558ebd61d68e394983b41d73ef8ed15ed728",
    "qres_same_status_from_mod_four_one":
        "81d03fae2c60673db6141b01b7dade17e9674f55bb5336cf2615ba28c0fd9fdc",
    "qres_opposite_status_from_mod_four_three":
        "81a45122463f889c6e9f93c22b8f52df1c7a70fe29c1dcfb0a006f41e6b12641",
}
EXPECTED_STATEMENT_LENGTH = {
    "qres_same_status_from_even_count_sum": 2_025,
    "qres_opposite_status_from_odd_count_sum": 2_027,
    "qres_same_status_from_even_half_product_mod_two": 2_154,
    "qres_opposite_status_from_odd_half_product_mod_two": 2_156,
    "qres_same_status_from_mod_four_one": 2_211,
    "qres_opposite_status_from_mod_four_three": 2_219,
}
EXPECTED_BODY_RECEIPTS = {
    "qres_same_status_from_even_count_sum": (1, 37, 48, 17, 48, 47, 0),
    "qres_opposite_status_from_odd_count_sum": (1, 37, 48, 17, 48, 47, 0),
    "qres_same_status_from_even_half_product_mod_two": (2, 28, 31, 20, 31, 30, 0),
    "qres_opposite_status_from_odd_half_product_mod_two": (2, 28, 31, 20, 31, 30, 0),
    "qres_same_status_from_mod_four_one": (4, 51, 56, 27, 56, 55, 0),
    "qres_opposite_status_from_mod_four_three": (3, 48, 52, 26, 52, 51, 0),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_quadratic_reciprocity_parity_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_parity_sum_classification_candidate_theorems,
        make_parity_mod_two_candidate_theorems,
        make_parity_odd_half_mod_four_candidate_theorems,
    ):
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"reciprocity parity replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_qr_parity_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    assert make_quadratic_reciprocity_parity_candidate_theorems(TheoremSpec) == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    assert {item.name: len(item.statement) for item in first} == EXPECTED_STATEMENT_LENGTH
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_qr_parity_contracts_are_closed_expanded_native_pa() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in ("QRes(", "Even(", "Odd(", "ModEq(", "%", "<", "<=")
        )
    assert "4 *" in _candidate_specs()[-1].statement


def test_qr_parity_scripts_are_constructive_and_explicit() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert "apply even_sum_parity_cases" in commands
    assert "apply odd_sum_parity_cases" in commands
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_qr_parity_bodies_kernel_check_within_laptop_limit() -> None:
    with _body_deadline(_BODY_DEADLINE_SECONDS):
        receipts = replay_candidate_bodies(_candidate_specs(), core=_dependency_core())
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
