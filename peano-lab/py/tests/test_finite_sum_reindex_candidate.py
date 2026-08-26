"""Focused native-body audit for exact beta-coded sum reindexing."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.finite_sum_permutation_candidate import (
    make_finite_sum_permutation_candidate_theorems,
)
from peano_lab.library.finite_sum_reindex_candidate import (
    make_finite_sum_reindex_candidate_theorems,
)
from peano_lab.library.finite_sum_transport_candidate import (
    make_finite_sum_transport_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "beta_sum_reindex_fixed_last",
    "beta_sum_permutation_invariant",
)
EXPECTED_DEPENDENCIES = {
    "beta_sum_reindex_fixed_last": (
        "beta_sum_succ_decompose",
        "beta_at_unique",
        "le_refl",
    ),
    "beta_sum_permutation_invariant": (
        "finite_bounded_injective_surjective",
        "finite_lt_succ_eq_or_lt",
        "finite_fixed_last_prefix_bounded",
        "finite_injective_prefix_succ",
        "beta_prefix_swap_last_from_entries",
        "finite_swap_last_bounded",
        "finite_swap_last_injective",
        "beta_sum_swap_last_invariant",
        "beta_sum_zero",
        "beta_sum_exists",
        "beta_at_exists",
        "beta_at_unique",
        "beta_reindex_alignment_swap_last",
        "beta_sum_reindex_fixed_last",
        "le_refl",
        "le_succ",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "beta_sum_reindex_fixed_last": (
        "c140c1591925e606be2e15d94bb4ded80972d474fda80c91470c048c4b486d00"
    ),
    "beta_sum_permutation_invariant": (
        "8e1dd7692750459e4e62603f3dc729cf3076d92cbbac70abd74d4afcfdf565c5"
    ),
}
EXPECTED_STATEMENT_LENGTH = {
    "beta_sum_reindex_fixed_last": 5_247,
    "beta_sum_permutation_invariant": 6_806,
}
EXPECTED_BODY_RECEIPTS = {
    "beta_sum_reindex_fixed_last": (3, 65, 85, 33, 85, 84, 0),
    "beta_sum_permutation_invariant": (16, 379, 631, 88, 628, 630, 3),
}
_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_finite_sum_reindex_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    factories = (
        make_finite_sum_transport_candidate_theorems,
        make_finite_sum_permutation_candidate_theorems,
    )
    for factory in factories:
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"finite-sum reindex replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_sum_reindex_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_finite_sum_reindex_candidate_theorems(TheoremSpec)

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


def test_sum_reindex_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = (
        "AlignedPrefix(",
        "BetaAt(",
        "BoundedPrefix(",
        "InjectivePrefix(",
        "Permutation(",
        "Product(",
        "Sum(",
        "SurjectivePrefix(",
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
        assert len(item.statement) < 8_192
        assert all(token not in item.statement for token in forbidden)

    fixed, general = _candidate_specs()
    assert fixed.statement.startswith("forall r s b c z d n p q.")
    assert general.statement.startswith("forall l r s b c z d p q.")
    assert fixed.statement.endswith("p = q")
    assert general.statement.endswith("p = q")
    assert "ff_s_reindex_source_product = " in general.statement
    assert (
        "ff_r_reindex_source_product + ff_a_reindex_source_product"
        in general.statement
    )


def test_sum_reindex_scripts_have_no_automation_or_classical_escape() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_sum_reindex_bodies_kernel_check_within_laptop_limit() -> None:
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
        f"FINITE SUM REINDEX BODY RECEIPTS elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
