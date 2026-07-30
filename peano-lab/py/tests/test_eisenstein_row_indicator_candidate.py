"""Focused native-body audit for beta-coded Eisenstein row indicators."""

from __future__ import annotations

import signal
from contextlib import contextmanager
from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from time import perf_counter

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.eisenstein_lattice_orientation_candidate import (
    make_eisenstein_lattice_orientation_candidate_theorems,
)
from peano_lab.library.eisenstein_row_indicator_candidate import (
    eisenstein_cell_indicator_choice,
    eisenstein_row_indicator_choices,
    eisenstein_row_indicator_prefix,
    make_eisenstein_row_indicator_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "distinct_odd_prime_half_cell_indicator_choice",
    "eisenstein_row_indicator_prefix_extend",
    "eisenstein_row_indicator_prefix_exists",
    "distinct_odd_prime_half_row_indicator_choices",
    "eisenstein_row_indicator_prefix_all_bits",
    "eisenstein_row_indicator_decoded_choice",
    "distinct_odd_prime_half_row_count_exists",
)

EXPECTED_DEPENDENCIES = {
    "distinct_odd_prime_half_cell_indicator_choice": (
        "distinct_odd_prime_half_cell_oriented",
    ),
    "eisenstein_row_indicator_prefix_extend": (
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    "eisenstein_row_indicator_prefix_exists": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "le_succ",
        "le_refl",
        "eisenstein_row_indicator_prefix_extend",
    ),
    "distinct_odd_prime_half_row_indicator_choices": (
        "distinct_odd_prime_half_cell_indicator_choice",
    ),
    "eisenstein_row_indicator_prefix_all_bits": (),
    "eisenstein_row_indicator_decoded_choice": ("beta_at_unique",),
    "distinct_odd_prime_half_row_count_exists": (
        "distinct_odd_prime_half_row_indicator_choices",
        "eisenstein_row_indicator_prefix_exists",
        "eisenstein_row_indicator_prefix_all_bits",
        "bit_count_exists",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "distinct_odd_prime_half_cell_indicator_choice": (
        "c7a5784da80e14558c16f8df131198f2be6c178275c5754c3968e9920cbe3163"
    ),
    "eisenstein_row_indicator_prefix_extend": (
        "f80bab534c746d332bc1baf16e0b278b28aa559f4741cfc37e71c9a579bbd1fe"
    ),
    "eisenstein_row_indicator_prefix_exists": (
        "df117ec1555d30a9ce4b23908b5094af790e59eafbd8bec2cac2d1c73b1b020f"
    ),
    "distinct_odd_prime_half_row_indicator_choices": (
        "5086e7f72ccc06481a6527a30a0810efe0dfbe588e466d5f452800c1f510cefc"
    ),
    "eisenstein_row_indicator_prefix_all_bits": (
        "2b3dde7840d44a8d09c802a42f62990cb3f5714262af8a3d35bb0c0368d6c00e"
    ),
    "eisenstein_row_indicator_decoded_choice": (
        "c0391f6ff1d144463bbaff0d7a53a3fdf61a7e97bb539b3511bba9b6656f3302"
    ),
    "distinct_odd_prime_half_row_count_exists": (
        "f6b21c5757631b361644e0301f3483054ea89355f9828bc2714ef2082104b0be"
    ),
}

EXPECTED_BODY_METRICS = {
    "distinct_odd_prime_half_cell_indicator_choice": (46, 29, 46, 45, 0),
    "eisenstein_row_indicator_prefix_extend": (71, 27, 71, 70, 0),
    "eisenstein_row_indicator_prefix_exists": (58, 23, 58, 57, 0),
    "distinct_odd_prime_half_row_indicator_choices": (53, 34, 53, 52, 0),
    "eisenstein_row_indicator_prefix_all_bits": (27, 16, 27, 26, 0),
    "eisenstein_row_indicator_decoded_choice": (43, 23, 43, 42, 0),
    "distinct_odd_prime_half_row_count_exists": (63, 29, 63, 62, 0),
}

_BODY_DEADLINE_SECONDS = 60


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_eisenstein_row_indicator_candidate_theorems(TheoremSpec)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Eisenstein row-indicator replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _explicit_dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for dependency in make_eisenstein_lattice_orientation_candidate_theorems(
        TheoremSpec
    ):
        assert dependency.name not in core
        core[dependency.name] = dependency
    return core


@lru_cache(maxsize=1)
def _body_receipts():
    specs = _candidate_specs()
    local = {item.name: item for item in specs}
    core = _explicit_dependency_core()
    rows = []
    started = perf_counter()

    with _body_deadline(_BODY_DEADLINE_SECONDS):
        for item in specs:
            formula = _closed_formula(item.statement)
            target = formula
            for dependency_name in reversed(item.dependencies):
                dependency = local.get(dependency_name) or core[dependency_name]
                target = Imp(_closed_formula(dependency.statement), target)

            state = start(target)
            for dependency_name in item.dependencies:
                state = apply_tactic(state, "intro", dependency_name)
            for command in item.script:
                tactic, arguments = _primitive(command)
                state = apply_tactic(state, tactic, arguments)

            certificate = checked_final(state, target)
            assert check((), certificate, target)
            assert not any(type(node) is DNE for node in _walk(certificate))
            nodes, depth = proof_metrics(certificate)
            objects, edges, reused = proof_identity_metrics(certificate)
            rows.append(
                (
                    item.name,
                    nodes,
                    depth,
                    objects,
                    edges,
                    reused,
                    len(item.script),
                )
            )

    return tuple(rows), perf_counter() - started


def test_eisenstein_row_factory_has_exact_isolated_contract() -> None:
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


def test_row_indicator_helpers_are_hygienic_alpha_native_and_exact() -> None:
    cell_left = eisenstein_cell_indicator_choice(
        "p", "q", "i", "j", "a", tag="alpha_left"
    )
    cell_right = eisenstein_cell_indicator_choice(
        "p", "q", "i", "j", "a", tag="alpha_right"
    )
    choices_left = eisenstein_row_indicator_choices(
        "p", "q", "i", "k", tag="alpha_left"
    )
    choices_right = eisenstein_row_indicator_choices(
        "p", "q", "i", "k", tag="alpha_right"
    )
    prefix_left = eisenstein_row_indicator_prefix(
        "p", "q", "i", "b", "c", "k", tag="alpha_left"
    )
    prefix_right = eisenstein_row_indicator_prefix(
        "p", "q", "i", "b", "c", "k", tag="alpha_right"
    )

    for left, right, expected_free in (
        (cell_left, cell_right, {"p", "q", "i", "j", "a"}),
        (choices_left, choices_right, {"p", "q", "i", "k"}),
        (prefix_left, prefix_right, {"p", "q", "i", "b", "c", "k"}),
    ):
        assert left != right
        assert parse_formula(left) == parse_formula(right)
        _, free_names = parse_formula_with_names(left)
        assert set(free_names) == expected_free

    assert "a = 1" in cell_left
    assert "S (p * S j) = q * S i" in cell_left
    assert "forall eri_column_alpha_left" in prefix_left
    assert "exists eri_bit_alpha_left" in prefix_left
    assert "ff_h_eri_alpha_left_decoded" in prefix_left
    assert "BetaAt(" not in prefix_left

    with pytest.raises(ValueError, match="Peano identifier"):
        eisenstein_cell_indicator_choice(
            "p + 1", "q", "i", "j", "a", tag="bad"
        )
    with pytest.raises(ValueError, match="captures an argument"):
        eisenstein_cell_indicator_choice(
            "eri_gap_capture_left", "q", "i", "j", "a", tag="capture"
        )
    with pytest.raises(ValueError, match="captures an argument"):
        eisenstein_row_indicator_choices(
            "p", "q", "i", "eri_column_capture", tag="capture"
        )
    with pytest.raises(ValueError, match="binder tag"):
        eisenstein_row_indicator_prefix(
            "p", "q", "i", "b", "c", "k", tag="bad tag"
        )


def test_eisenstein_row_contracts_are_closed_expanded_native_pa() -> None:
    forbidden_surface_tokens = (
        "AllBits(",
        "BetaAt(",
        "BitCount(",
        "CellIndicator(",
        "Prime(",
        "RowIndicator(",
        "Sum(",
        "%",
        "<",
        "∣",
        "≡",
    )

    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(token not in item.statement for token in forbidden_surface_tokens)

    capstone = _candidate_specs()[-1].statement
    assert capstone.startswith("forall p q h k i. p = 2 * h + 1 ->")
    assert "exists rb rc n." in capstone
    assert "forall eri_column_row_indicator_counted_prefix" in capstone
    assert "ff_u_row_indicator_count_relation_sum" in capstone
    assert "ff_i_row_indicator_count_relation_bits" in capstone


def test_eisenstein_row_bodies_are_constructive_and_bounded() -> None:
    rows, elapsed = _body_receipts()
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    assert {row[0]: row[1:6] for row in rows} == EXPECTED_BODY_METRICS
    assert elapsed < _BODY_DEADLINE_SECONDS

    for name, nodes, depth, objects, edges, reused, commands in rows:
        print(
            "EISENSTEIN ROW BODY RECEIPT "
            f"name={name} nodes={nodes} depth={depth} objects={objects} "
            f"edges={edges} reused={reused} commands={commands}",
            flush=True,
        )
