"""Focused native-body audit for bounded Eisenstein lattice orientation."""

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
    exclusive_lattice_cell_orientation,
    half_rectangle_orientation,
    make_eisenstein_lattice_orientation_candidate_theorems,
)
from peano_lab.library.gauss_magnitude_coprime_candidate import (
    make_gauss_magnitude_coprime_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "distinct_odd_prime_half_products_ne",
    "distinct_odd_prime_half_cell_oriented",
    "distinct_odd_prime_half_rectangle_oriented",
)

EXPECTED_DEPENDENCIES = {
    "distinct_odd_prime_half_products_ne": (
        "odd_half_strictly_below_modulus",
        "lt_of_le_of_lt",
        "euclid_prime_dvd_product",
        "prime_divisor_eq_one_or_self",
        "succ_ne_zero",
        "divisor_le_nonzero",
        "lt_not_le",
    ),
    "distinct_odd_prime_half_cell_oriented": (
        "distinct_odd_prime_half_products_ne",
        "lt_trichotomy",
        "lt_to_le",
        "lt_not_le",
    ),
    "distinct_odd_prime_half_rectangle_oriented": (
        "distinct_odd_prime_half_cell_oriented",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "distinct_odd_prime_half_products_ne": (
        "efce7909656125a8cd6401330a1818d76b0150cbfb272dd0dcc83981f3ce4676"
    ),
    "distinct_odd_prime_half_cell_oriented": (
        "7a55eb878f0f159bff0aa30559bc52a3ce9d3212ceb600364ea9da6b1ec4cf89"
    ),
    "distinct_odd_prime_half_rectangle_oriented": (
        "dd2b4d18148a957249d6a6aaf77ce78a1bd4580cd8a29a699e36c3edd0374b1a"
    ),
}

EXPECTED_BODY_METRICS = {
    "distinct_odd_prime_half_products_ne": (72, 30, 72, 71, 0),
    "distinct_odd_prime_half_cell_oriented": (77, 34, 77, 76, 0),
    "distinct_odd_prime_half_rectangle_oriented": (53, 34, 53, 52, 0),
}

_BODY_DEADLINE_SECONDS = 60


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_eisenstein_lattice_orientation_candidate_theorems(TheoremSpec)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Eisenstein lattice replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _explicit_dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for dependency in make_gauss_magnitude_coprime_candidate_theorems(
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


def test_eisenstein_lattice_factory_has_exact_isolated_contract() -> None:
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


def test_lattice_helpers_are_hygienic_alpha_native_and_exact() -> None:
    cell_left = exclusive_lattice_cell_orientation(
        "p", "q", "i", "j", tag="alpha_left"
    )
    cell_right = exclusive_lattice_cell_orientation(
        "p", "q", "i", "j", tag="alpha_right"
    )
    rectangle_left = half_rectangle_orientation(
        "p", "q", "h", "k", tag="alpha_left"
    )
    rectangle_right = half_rectangle_orientation(
        "p", "q", "h", "k", tag="alpha_right"
    )

    assert cell_left != cell_right
    assert parse_formula(cell_left) == parse_formula(cell_right)
    _, cell_free_names = parse_formula_with_names(cell_left)
    assert set(cell_free_names) == {"p", "q", "i", "j"}
    assert "elo_gap_alpha_left_left" in cell_left
    assert "q * S i" in cell_left
    assert "p * S j" in cell_left

    assert rectangle_left != rectangle_right
    assert parse_formula(rectangle_left) == parse_formula(rectangle_right)
    _, rectangle_free_names = parse_formula_with_names(rectangle_left)
    assert set(rectangle_free_names) == {"p", "q", "h", "k"}
    assert "forall elo_p_index_alpha_left elo_q_index_alpha_left" in rectangle_left
    assert "elo_gap_alpha_left_p_bound" in rectangle_left

    with pytest.raises(ValueError, match="Peano identifier"):
        exclusive_lattice_cell_orientation(
            "p + 1", "q", "i", "j", tag="bad"
        )
    with pytest.raises(ValueError, match="captures an argument"):
        exclusive_lattice_cell_orientation(
            "elo_gap_capture_left", "q", "i", "j", tag="capture"
        )
    with pytest.raises(ValueError, match="captures an argument"):
        half_rectangle_orientation(
            "p", "q", "elo_p_index_capture", "k", tag="capture"
        )
    with pytest.raises(ValueError, match="binder tag"):
        half_rectangle_orientation("p", "q", "h", "k", tag="bad tag")


def test_eisenstein_lattice_contracts_are_closed_expanded_native_pa() -> None:
    forbidden_surface_tokens = (
        "BetaAt(",
        "BitCount(",
        "CellOrientation(",
        "DivRem(",
        "HalfRectangle(",
        "Prime(",
        "Product(",
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
    assert capstone.startswith("forall p q h k. p = 2 * h + 1 ->")
    assert "forall elo_p_index_lattice_rectangle_result" in capstone
    assert "elo_q_index_lattice_rectangle_result" in capstone
    assert "q * S elo_p_index_lattice_rectangle_result" in capstone
    assert "p * S elo_q_index_lattice_rectangle_result" in capstone


def test_eisenstein_lattice_bodies_are_constructive_and_bounded() -> None:
    rows, elapsed = _body_receipts()
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    assert {row[0]: row[1:6] for row in rows} == EXPECTED_BODY_METRICS
    assert elapsed < _BODY_DEADLINE_SECONDS

    for name, nodes, depth, objects, edges, reused, commands in rows:
        print(
            "EISENSTEIN LATTICE BODY RECEIPT "
            f"name={name} nodes={nodes} depth={depth} objects={objects} "
            f"edges={edges} reused={reused} commands={commands}",
            flush=True,
        )
