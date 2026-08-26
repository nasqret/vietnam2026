"""Focused body audit for the outer prefix of transposed-column counts."""

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
from peano_lab.library.eisenstein_transposed_column_candidate import (
    make_eisenstein_transposed_column_candidate_theorems,
)
from peano_lab.library.eisenstein_transposed_column_count_candidate import (
    eisenstein_transposed_column_count_choices,
    eisenstein_transposed_column_count_prefix,
    eisenstein_transposed_column_count_witness,
    make_eisenstein_transposed_column_count_candidate_theorems,
)
from peano_lab.library.finite_repeat_sum_candidate import (
    make_finite_repeat_sum_candidate_theorems,
)
from peano_lab.library.finite_sum_pointwise_add_candidate import (
    make_finite_sum_pointwise_add_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula, _specs_by_name


EXPECTED_NAMES = (
    "eisenstein_transposed_column_count_choices",
    "eisenstein_transposed_column_count_prefix_extend",
    "eisenstein_transposed_column_count_prefix_exists",
    "eisenstein_transposed_column_count_decoded_witness",
    "eisenstein_transposed_column_count_total_exists",
    "eisenstein_transposed_column_count_decoded_partition",
    "eisenstein_transposed_column_count_matches_decoded_constant",
    "eisenstein_rectangle_plus_column_count_total",
)

EXPECTED_DEPENDENCIES = {
    "eisenstein_transposed_column_count_choices": (
        "eisenstein_row_transposed_column_count_partition",
    ),
    "eisenstein_transposed_column_count_prefix_extend": (
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    "eisenstein_transposed_column_count_prefix_exists": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "le_succ",
        "le_refl",
        "eisenstein_transposed_column_count_prefix_extend",
    ),
    "eisenstein_transposed_column_count_decoded_witness": ("beta_at_unique",),
    "eisenstein_transposed_column_count_total_exists": (
        "eisenstein_transposed_column_count_choices",
        "eisenstein_transposed_column_count_prefix_exists",
        "beta_sum_exists",
    ),
    "eisenstein_transposed_column_count_decoded_partition": (
        "eisenstein_transposed_column_count_decoded_witness",
        "beta_at_unique",
    ),
    "eisenstein_transposed_column_count_matches_decoded_constant": (
        "eisenstein_transposed_column_count_decoded_partition",
        "beta_repeat_entry_eq",
    ),
    "eisenstein_rectangle_plus_column_count_total": (
        "eisenstein_transposed_column_count_total_exists",
        "beta_repeat_sum_exists_exact",
        "eisenstein_transposed_column_count_matches_decoded_constant",
        "beta_sum_pointwise_add",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "eisenstein_transposed_column_count_choices": (
        "be7c084820ab7d2d4568022f893b8b0e3a4ea62bb0d9e6a11da596ff75dc7b08"
    ),
    "eisenstein_transposed_column_count_prefix_extend": (
        "c3c7c82307d50cc5d1363635d629753d64d19f7bc2354f431c10d4365eefa123"
    ),
    "eisenstein_transposed_column_count_prefix_exists": (
        "7308a9882e5a85e03710034339b7827b32f8478c03af5c5f8318c0d03dc486db"
    ),
    "eisenstein_transposed_column_count_decoded_witness": (
        "0a6c299abc75a38103ecb62577d49342393e46521f927cb348a98a4e6ed29542"
    ),
    "eisenstein_transposed_column_count_total_exists": (
        "9eb3be69641d32c848000ca71cda5f0521e9c20b024164b48b7f69575bed3d93"
    ),
    "eisenstein_transposed_column_count_decoded_partition": (
        "b39cca396059c9ea8c4681e2b749633a732f0f30cd09e988b3139441289865b0"
    ),
    "eisenstein_transposed_column_count_matches_decoded_constant": (
        "aff6fafa5ff1f17fceb4473aea9e974869b05c6ed4acb840d61d7789144cee04"
    ),
    "eisenstein_rectangle_plus_column_count_total": (
        "2e441227ee47073eafb4223712a77b13ab9ed0e0d7140f7ef535fe189f005977"
    ),
}

EXPECTED_BODY_RECEIPTS = {
    "eisenstein_transposed_column_count_choices": (1, 57, 70, 32, 70, 69, 0),
    "eisenstein_transposed_column_count_prefix_extend": (
        2,
        59,
        88,
        35,
        88,
        87,
        0,
    ),
    "eisenstein_transposed_column_count_prefix_exists": (
        5,
        60,
        68,
        33,
        68,
        67,
        0,
    ),
    "eisenstein_transposed_column_count_decoded_witness": (
        1,
        34,
        59,
        28,
        59,
        58,
        0,
    ),
    "eisenstein_transposed_column_count_total_exists": (
        3,
        48,
        51,
        26,
        51,
        50,
        0,
    ),
    "eisenstein_transposed_column_count_decoded_partition": (
        2,
        52,
        60,
        36,
        60,
        59,
        0,
    ),
    "eisenstein_transposed_column_count_matches_decoded_constant": (
        2,
        56,
        61,
        43,
        61,
        60,
        0,
    ),
    "eisenstein_rectangle_plus_column_count_total": (
        4,
        100,
        116,
        61,
        116,
        115,
        0,
    ),
}

_BODY_DEADLINE_SECONDS = 60


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_eisenstein_transposed_column_count_candidate_theorems(
        TheoremSpec
    )


@lru_cache(maxsize=1)
def _dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for factory in (
        make_eisenstein_rectangle_count_candidate_theorems,
        make_eisenstein_transposed_column_candidate_theorems,
        make_finite_repeat_sum_candidate_theorems,
        make_finite_sum_pointwise_add_candidate_theorems,
    ):
        for item in factory(TheoremSpec):
            core[item.name] = item
    return core


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(
            f"Eisenstein transposed-column-count replay exceeded {seconds}s"
        )

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_column_count_factory_is_exact_ordered_and_isolated() -> None:
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


def test_column_count_helpers_are_hygienic_alpha_native_and_provenanced() -> None:
    witness_left = eisenstein_transposed_column_count_witness(
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "i", "m",
        tag="alpha_left",
    )
    witness_right = eisenstein_transposed_column_count_witness(
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "i", "m",
        tag="alpha_right",
    )
    choices = eisenstein_transposed_column_count_choices(
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "h",
        tag="choices",
    )
    prefix = eisenstein_transposed_column_count_prefix(
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "db", "dc", "h",
        tag="prefix",
    )

    assert witness_left != witness_right
    assert parse_formula(witness_left) == parse_formula(witness_right)
    assert set(parse_formula_with_names(witness_left)[1]) == {
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "i", "m"
    }
    assert set(parse_formula_with_names(choices)[1]) == {
        "p", "q", "h", "k", "ab", "ac", "bb", "bc"
    }
    assert set(parse_formula_with_names(prefix)[1]) == {
        "p", "q", "h", "k", "ab", "ac", "bb", "bc", "db", "dc"
    }
    assert "ab =" in witness_left
    assert "bb =" in witness_left
    assert "+ m = k" in witness_left

    with pytest.raises(ValueError, match="Peano identifier"):
        eisenstein_transposed_column_count_prefix(
            "p + 1", "q", "h", "k", "ab", "ac", "bb", "bc", "db", "dc", "h",
            tag="bad",
        )


def test_column_count_contracts_are_closed_expanded_native_pa() -> None:
    forbidden = (
        "BetaAt(",
        "BitCount(",
        "Column(",
        "Rectangle(",
        "Repeat(",
        "RowIndicator(",
        "Sum(",
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

    total = _candidate_specs()[4]
    partition = _candidate_specs()[5]
    constant = _candidate_specs()[6]
    total_partition = _candidate_specs()[7]
    assert total.statement.startswith("forall p q h k ab ac bb bc.")
    assert partition.statement.endswith("n + m = k")
    assert constant.statement.endswith("n + m = c")
    assert total_partition.statement.startswith("forall p q h k ab ac bb bc N.")
    assert "N + M = h * k" in total_partition.statement


def test_column_count_scripts_have_no_automation_or_classical_escape() -> None:
    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command for command in commands)
    assert all("by_contra" not in command for command in commands)
    assert all("classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)


def test_column_count_bodies_kernel_check_within_laptop_limit() -> None:
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
        "EISENSTEIN TRANSPOSED COLUMN COUNT BODY RECEIPTS "
        f"elapsed={elapsed:.3f}s rows={observed}",
        flush=True,
    )
