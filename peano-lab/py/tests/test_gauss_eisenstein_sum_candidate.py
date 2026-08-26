"""Focused body audit for Gauss--Eisenstein terminal Sum cancellation."""

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
from peano_lab.library.finite_sum_reindex_candidate import (
    make_finite_sum_reindex_candidate_theorems,
)
from peano_lab.library.gauss_eisenstein_pointwise_candidate import (
    make_gauss_eisenstein_pointwise_candidate_theorems,
)
from peano_lab.library.gauss_eisenstein_sum_candidate import (
    make_gauss_eisenstein_sum_candidate_theorems,
)
from peano_lab.library.gauss_magnitude_permutation_candidate import (
    make_gauss_magnitude_permutation_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "beta_magnitude_predecessor_recode_aligned_half_range",
    "beta_magnitude_sum_permutation_exact",
    "gauss_signed_half_magnitude_sum_equals_half_sum",
    "gauss_eisenstein_terminal_sums_mod_two",
    "gauss_eisenstein_terminal_cancel_magnitude_mod_two",
    "gauss_eisenstein_sign_count_mod_quotient_sum",
)
EXPECTED_DEPENDENCIES = {
    "beta_magnitude_predecessor_recode_aligned_half_range": (
        "beta_magnitude_predecessor_recode_reflect",
        "beta_at_unique",
        "add_succ_left",
        "zero_add",
    ),
    "beta_magnitude_sum_permutation_exact": (
        "beta_magnitude_predecessor_recode_bounded",
        "beta_magnitude_predecessor_recode_injective",
        "beta_magnitude_predecessor_recode_aligned_half_range",
        "beta_sum_permutation_invariant",
    ),
    "gauss_signed_half_magnitude_sum_equals_half_sum": (
        "gauss_signed_half_magnitude_range",
        "gauss_signed_half_magnitude_injective",
        "gauss_signed_half_predecessor_recode_exists",
        "beta_magnitude_sum_permutation_exact",
    ),
    "gauss_eisenstein_terminal_sums_mod_two": (
        "gauss_eisenstein_prefix_pointwise_mod_two",
        "beta_sum_pointwise_mod_three_add",
    ),
    "gauss_eisenstein_terminal_cancel_magnitude_mod_two": (
        "gauss_eisenstein_terminal_sums_mod_two",
        "gauss_signed_half_magnitude_sum_equals_half_sum",
        "mod_two_cancel_middle",
    ),
    "gauss_eisenstein_sign_count_mod_quotient_sum": (
        "beta_sum_exists",
        "gauss_eisenstein_terminal_cancel_magnitude_mod_two",
        "mod_two_zero_sum_to_congruent",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "beta_magnitude_predecessor_recode_aligned_half_range": (
        "7571ab541a512bcb0485b30de647af24ed52da62d7b3ddfa0f3e3a4a8c75f690"
    ),
    "beta_magnitude_sum_permutation_exact": (
        "56edd22793ad944da24d92faee1661c190e315099471cf9d13afa0ded2d5d0d1"
    ),
    "gauss_signed_half_magnitude_sum_equals_half_sum": (
        "c4007fe11e30acb97e6bc52650280dd8fd7f6947f957ea0128d9fea7693766e8"
    ),
    "gauss_eisenstein_terminal_sums_mod_two": (
        "e3a41687dc6b111279515cdc8db5b042fa856c304b0ba7c3a9ae216c55ac711e"
    ),
    "gauss_eisenstein_terminal_cancel_magnitude_mod_two": (
        "7964137745a2f886d1002b7b1e3e37f8e97491479064f16bbe2668f6712efcf7"
    ),
    "gauss_eisenstein_sign_count_mod_quotient_sum": (
        "dd578e03a8be62368a626000589d2a2f77154a63c6d19187b371911cdb4f660f"
    ),
}
EXPECTED_STATEMENT_LENGTH = {
    "beta_magnitude_predecessor_recode_aligned_half_range": 3_044,
    "beta_magnitude_sum_permutation_exact": 6_727,
    "gauss_signed_half_magnitude_sum_equals_half_sum": 6_403,
    "gauss_eisenstein_terminal_sums_mod_two": 11_623,
    "gauss_eisenstein_terminal_cancel_magnitude_mod_two": 11_911,
    "gauss_eisenstein_sign_count_mod_quotient_sum": 9_313,
}
EXPECTED_BODY_RECEIPTS = {
    "beta_magnitude_predecessor_recode_aligned_half_range": (
        4, 77, 148, 42, 148, 147, 0,
    ),
    "beta_magnitude_sum_permutation_exact": (4, 61, 72, 34, 72, 71, 0),
    "gauss_signed_half_magnitude_sum_equals_half_sum": (
        4, 77, 90, 43, 90, 89, 0,
    ),
    "gauss_eisenstein_terminal_sums_mod_two": (2, 72, 83, 54, 83, 82, 0),
    "gauss_eisenstein_terminal_cancel_magnitude_mod_two": (
        3, 88, 107, 66, 107, 106, 0,
    ),
    "gauss_eisenstein_sign_count_mod_quotient_sum": (
        3, 77, 89, 65, 89, 88, 0,
    ),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_gauss_eisenstein_sum_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    factories = (
        make_finite_sum_pointwise_mod_candidate_theorems,
        make_finite_sum_reindex_candidate_theorems,
        make_gauss_magnitude_permutation_candidate_theorems,
        make_gauss_eisenstein_pointwise_candidate_theorems,
    )
    for factory in factories:
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Gauss--Eisenstein Sum replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_gauss_eisenstein_sum_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_gauss_eisenstein_sum_candidate_theorems(TheoremSpec)

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


def test_gauss_eisenstein_sum_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = (
        "AlignedPrefix(",
        "BetaAt(",
        "DivRem(",
        "HalfRange(",
        "InjectivePrefix(",
        "ModEq(",
        "Permutation(",
        "Prime(",
        "SignedHalfPrefix(",
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

    alignment, exact, gauss_exact, aggregate, canceled, orientation = (
        _candidate_specs()
    )
    assert alignment.statement.startswith("forall b c mb mc rb rc h.")
    assert exact.statement.endswith("X = M")
    assert gauss_exact.statement.endswith("X = M")
    assert aggregate.statement.startswith(
        "forall p h a b c tb tc qb qc rb rc mb mc sb sc X Q M E."
    )
    assert "(X) + 2 *" in aggregate.statement
    assert "(Q + M + E) + 2 *" in aggregate.statement
    assert "(0) + 2 *" in canceled.statement
    assert "(Q + E) + 2 *" in canceled.statement
    assert orientation.statement.startswith(
        "forall p h a b c tb tc qb qc rb rc mb mc sb sc Q E."
    )
    assert "(Q) + 2 *" in orientation.statement
    assert "(E) + 2 *" in orientation.statement


def test_gauss_eisenstein_sum_scripts_are_constructive_and_explicit() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert "apply beta_sum_permutation_invariant" in commands
    assert "apply beta_sum_pointwise_mod_three_add" in commands
    assert "apply mod_two_cancel_middle" in commands
    assert "apply mod_two_zero_sum_to_congruent" in commands
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_gauss_eisenstein_sum_bodies_kernel_check_within_laptop_limit() -> None:
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
        f"GAUSS EISENSTEIN SUM BODY RECEIPTS elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
