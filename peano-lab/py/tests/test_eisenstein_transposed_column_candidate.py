"""Focused body audit for provenance-carrying transposed columns."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

import pytest

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.eisenstein_rectangle_count_candidate import (
    make_eisenstein_rectangle_count_candidate_theorems,
)
from peano_lab.library.eisenstein_row_indicator_candidate import (
    make_eisenstein_row_indicator_candidate_theorems,
)
from peano_lab.library.eisenstein_transposed_cell_candidate import (
    make_eisenstein_transposed_cell_candidate_theorems,
)
from peano_lab.library.eisenstein_transposed_column_candidate import (
    eisenstein_transposed_column_choices,
    eisenstein_transposed_column_entry_witness,
    eisenstein_transposed_column_prefix,
    make_eisenstein_transposed_column_candidate_theorems,
)
from peano_lab.library.eisenstein_transposed_outer_cell_candidate import (
    make_eisenstein_transposed_outer_cell_candidate_theorems,
)
from peano_lab.library.finite_bitcount_complement_candidate import (
    make_finite_bitcount_complement_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "eisenstein_transposed_outer_column_choices",
    "eisenstein_transposed_column_prefix_extend",
    "eisenstein_transposed_column_prefix_exists",
    "eisenstein_transposed_column_prefix_all_bits",
    "eisenstein_transposed_column_pointwise_complement",
    "eisenstein_row_transposed_column_count_partition",
)

EXPECTED_DEPENDENCIES = {
    "eisenstein_transposed_outer_column_choices": (
        "eisenstein_rectangle_decoded_row_count",
        "beta_at_exists",
    ),
    "eisenstein_transposed_column_prefix_extend": (
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    "eisenstein_transposed_column_prefix_exists": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "le_succ",
        "le_refl",
        "eisenstein_transposed_column_prefix_extend",
    ),
    "eisenstein_transposed_column_prefix_all_bits": (
        "eisenstein_row_indicator_decoded_choice",
    ),
    "eisenstein_transposed_column_pointwise_complement": (
        "beta_at_unique",
        "eisenstein_transposed_decoded_cell_bits_complementary",
    ),
    "eisenstein_row_transposed_column_count_partition": (
        "eisenstein_transposed_outer_column_choices",
        "eisenstein_transposed_column_prefix_exists",
        "eisenstein_transposed_column_prefix_all_bits",
        "bit_count_exists",
        "eisenstein_transposed_column_pointwise_complement",
        "complementary_bit_counts_add_length",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "eisenstein_transposed_outer_column_choices": (
        "f329e1df525cb7dae677339576a62b3e06205ecc2f879781c36d7caff10358b9"
    ),
    "eisenstein_transposed_column_prefix_extend": (
        "1044f33e73d52aede20740f6e0502935bd1236e5b0c66dd4615e1fb7e743465e"
    ),
    "eisenstein_transposed_column_prefix_exists": (
        "c4556355792d3c74413054f0d7073f5bb3fbe8fe0ed710f5e71c1dcf6e9387c6"
    ),
    "eisenstein_transposed_column_prefix_all_bits": (
        "91ccae92dd5fd2ee1dc85d1aa4dae7eeef057588fc9f5c30bc672e7582526968"
    ),
    "eisenstein_transposed_column_pointwise_complement": (
        "4ea2370e3f11ca3af56b62627781935751e350b26922504a0ca7efecf9525b86"
    ),
    "eisenstein_row_transposed_column_count_partition": (
        "e777e1bf05763e3cb7f15f5bf6872f39291337fa1b2b5b558ed5b5d88122b9dc"
    ),
}

EXPECTED_BODY_RECEIPTS = {
    "eisenstein_transposed_outer_column_choices": (2, 37, 42, 26, 42, 41, 0),
    "eisenstein_transposed_column_prefix_extend": (2, 55, 80, 31, 80, 79, 0),
    "eisenstein_transposed_column_prefix_exists": (5, 56, 64, 29, 64, 63, 0),
    "eisenstein_transposed_column_prefix_all_bits": (1, 48, 56, 33, 56, 55, 0),
    "eisenstein_transposed_column_pointwise_complement": (
        2,
        64,
        87,
        47,
        87,
        86,
        0,
    ),
    "eisenstein_row_transposed_column_count_partition": (
        6,
        105,
        117,
        56,
        117,
        116,
        0,
    ),
}

_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_eisenstein_transposed_column_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    factories = (
        make_eisenstein_rectangle_count_candidate_theorems,
        make_eisenstein_row_indicator_candidate_theorems,
        make_eisenstein_transposed_cell_candidate_theorems,
        make_eisenstein_transposed_outer_cell_candidate_theorems,
        make_finite_bitcount_complement_candidate_theorems,
    )
    for factory in factories:
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Eisenstein transposed-column replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_transposed_column_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = _candidate_specs()

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_transposed_column_helpers_are_hygienic_alpha_native_and_provenanced() -> None:
    entry_left = eisenstein_transposed_column_entry_witness(
        "p", "q", "h", "bb", "bc", "i", "j", "d", tag="alpha_left"
    )
    entry_right = eisenstein_transposed_column_entry_witness(
        "p", "q", "h", "bb", "bc", "i", "j", "d", tag="alpha_right"
    )
    choices = eisenstein_transposed_column_choices(
        "p", "q", "h", "bb", "bc", "i", "k", tag="choices"
    )
    prefix = eisenstein_transposed_column_prefix(
        "p", "q", "h", "bb", "bc", "i", "z", "e", "k", tag="prefix"
    )

    assert entry_left != entry_right
    assert parse_formula(entry_left) == parse_formula(entry_right)
    assert set(parse_formula_with_names(entry_left)[1]) == {
        "p", "q", "h", "bb", "bc", "i", "j", "d"
    }
    assert set(parse_formula_with_names(choices)[1]) == {
        "p", "q", "h", "bb", "bc", "i", "k"
    }
    assert set(parse_formula_with_names(prefix)[1]) == {
        "p", "q", "h", "bb", "bc", "i", "z", "e", "k"
    }
    # The entry keeps the outer decode, inner row/count, and inner cell decode.
    assert entry_left.count("bb =") == 1
    assert "bc" in entry_left
    assert "q * S" in entry_left
    assert "p * S" in entry_left
    assert entry_left.count("S ((S (i)) *") >= 2

    with pytest.raises(ValueError, match="Peano identifier"):
        eisenstein_transposed_column_prefix(
            "p + 1", "q", "h", "bb", "bc", "i", "z", "e", "k", tag="bad"
        )


def test_transposed_column_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = (
        "AllBits(",
        "BetaAt(",
        "BitCount(",
        "Column(",
        "Rectangle(",
        "RowIndicator(",
        "%",
        "<=",
        "<",
        "∣",
    )
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden)

    endpoint = _candidate_specs()[-1]
    assert endpoint.statement.startswith("forall p q h k i rb rc bb bc n.")
    assert "n + m = k" in endpoint.statement


def test_transposed_column_scripts_have_no_automation_or_classical_escape() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_transposed_column_bodies_kernel_check_within_laptop_limit() -> None:
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
        "EISENSTEIN TRANSPOSED COLUMN BODY RECEIPTS "
        f"elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
