"""Focused native-body audit for nested Eisenstein rectangle counts."""

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
from peano_lab.library.eisenstein_rectangle_count_candidate import (
    eisenstein_rectangle_row_count_choices,
    eisenstein_rectangle_row_count_prefix,
    eisenstein_row_count_witness,
    make_eisenstein_rectangle_count_candidate_theorems,
)
from peano_lab.library.eisenstein_row_indicator_candidate import (
    make_eisenstein_row_indicator_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "distinct_odd_prime_half_row_count_choice",
    "eisenstein_rectangle_row_count_prefix_extend",
    "eisenstein_rectangle_row_count_prefix_exists",
    "distinct_odd_prime_half_row_count_choices_bounded",
    "distinct_odd_prime_half_row_count_prefix_exists_bounded",
    "distinct_odd_prime_half_row_count_prefix_exists",
    "eisenstein_rectangle_decoded_row_count",
    "distinct_odd_prime_half_rectangle_total_exists",
)

EXPECTED_DEPENDENCIES = {
    "distinct_odd_prime_half_row_count_choice": (
        "distinct_odd_prime_half_row_count_exists",
    ),
    "eisenstein_rectangle_row_count_prefix_extend": (
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    "eisenstein_rectangle_row_count_prefix_exists": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "le_succ",
        "le_refl",
        "eisenstein_rectangle_row_count_prefix_extend",
    ),
    "distinct_odd_prime_half_row_count_choices_bounded": (
        "lt_of_lt_of_le",
        "distinct_odd_prime_half_row_count_choice",
    ),
    "distinct_odd_prime_half_row_count_prefix_exists_bounded": (
        "distinct_odd_prime_half_row_count_choices_bounded",
        "eisenstein_rectangle_row_count_prefix_exists",
    ),
    "distinct_odd_prime_half_row_count_prefix_exists": (
        "le_refl",
        "distinct_odd_prime_half_row_count_prefix_exists_bounded",
    ),
    "eisenstein_rectangle_decoded_row_count": ("beta_at_unique",),
    "distinct_odd_prime_half_rectangle_total_exists": (
        "distinct_odd_prime_half_row_count_prefix_exists",
        "beta_sum_exists",
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "distinct_odd_prime_half_row_count_choice": (
        "3aaddf27730a7e10cf238b5fe9e69e7c0375307e18964579f09f6ef5cd952444"
    ),
    "eisenstein_rectangle_row_count_prefix_extend": (
        "b5692308b1336b712d107fa558637c35c198445ec33f83e9bc835185ded0c6c1"
    ),
    "eisenstein_rectangle_row_count_prefix_exists": (
        "4074f12286b0c972fb9683a3820cc2c68e9387b8eac0ad2c6de6810795418fac"
    ),
    "distinct_odd_prime_half_row_count_choices_bounded": (
        "494f8796925115447b74dc0c703e899a5aa63208a66fbb2010abaa25dc3c7e5c"
    ),
    "distinct_odd_prime_half_row_count_prefix_exists_bounded": (
        "ba51a9a6cb3a0ec00b5f6c6673185d782b426acd5296236df5549546656109a8"
    ),
    "distinct_odd_prime_half_row_count_prefix_exists": (
        "fcbd2e52f5800b82d3243e8881d9a07f870de50c9e4c850f0bfee0e37aa7526d"
    ),
    "eisenstein_rectangle_decoded_row_count": (
        "0baa129db14a6fc7c97062a5f135121b136ac33a22212a10133ef547fd9900de"
    ),
    "distinct_odd_prime_half_rectangle_total_exists": (
        "ca54b72cf92092696df0c5b1909abde17332725e52d7b07901b429be35fed2a8"
    ),
}

EXPECTED_BODY_METRICS = {
    "distinct_odd_prime_half_row_count_choice": (39, 25, 39, 38, 0),
    "eisenstein_rectangle_row_count_prefix_extend": (71, 27, 71, 70, 0),
    "eisenstein_rectangle_row_count_prefix_exists": (58, 23, 58, 57, 0),
    "distinct_odd_prime_half_row_count_choices_bounded": (40, 27, 40, 39, 0),
    "distinct_odd_prime_half_row_count_prefix_exists_bounded": (
        37,
        26,
        37,
        36,
        0,
    ),
    "distinct_odd_prime_half_row_count_prefix_exists": (30, 23, 30, 29, 0),
    "eisenstein_rectangle_decoded_row_count": (43, 23, 43, 42, 0),
    "distinct_odd_prime_half_rectangle_total_exists": (40, 22, 40, 39, 0),
}

_BODY_DEADLINE_SECONDS = 60


def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_eisenstein_rectangle_count_candidate_theorems(TheoremSpec)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Eisenstein rectangle replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _explicit_dependency_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for dependency in make_eisenstein_row_indicator_candidate_theorems(
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


def test_eisenstein_rectangle_factory_has_exact_isolated_contract() -> None:
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


def test_rectangle_helpers_are_hygienic_alpha_native_and_nested() -> None:
    witness_left = eisenstein_row_count_witness(
        "p", "q", "k", "i", "n", tag="alpha_left"
    )
    witness_right = eisenstein_row_count_witness(
        "p", "q", "k", "i", "n", tag="alpha_right"
    )
    choices_left = eisenstein_rectangle_row_count_choices(
        "p", "q", "k", "h", tag="alpha_left"
    )
    choices_right = eisenstein_rectangle_row_count_choices(
        "p", "q", "k", "h", tag="alpha_right"
    )
    prefix_left = eisenstein_rectangle_row_count_prefix(
        "p", "q", "k", "b", "c", "h", tag="alpha_left"
    )
    prefix_right = eisenstein_rectangle_row_count_prefix(
        "p", "q", "k", "b", "c", "h", tag="alpha_right"
    )

    for left, right, expected_free in (
        (witness_left, witness_right, {"p", "q", "k", "i", "n"}),
        (choices_left, choices_right, {"p", "q", "k", "h"}),
        (prefix_left, prefix_right, {"p", "q", "k", "b", "c", "h"}),
    ):
        assert left != right
        assert parse_formula(left) == parse_formula(right)
        _, free_names = parse_formula_with_names(left)
        assert set(free_names) == expected_free

    assert "exists erc_row_code_alpha_left erc_row_scale_alpha_left" in witness_left
    assert "forall erc_row_alpha_left" in prefix_left
    assert "exists erc_count_alpha_left" in prefix_left
    assert "ff_h_erc_alpha_left_decoded" in prefix_left
    assert "erc_row_code_alpha_left_witness" in prefix_left
    assert "BetaAt(" not in prefix_left
    assert "BitCount(" not in prefix_left

    with pytest.raises(ValueError, match="Peano identifier"):
        eisenstein_row_count_witness(
            "p + 1", "q", "k", "i", "n", tag="bad"
        )
    with pytest.raises(ValueError, match="captures an argument"):
        eisenstein_row_count_witness(
            "erc_row_code_capture", "q", "k", "i", "n", tag="capture"
        )
    with pytest.raises(ValueError, match="captures an argument"):
        eisenstein_rectangle_row_count_choices(
            "p", "q", "k", "erc_row_capture", tag="capture"
        )
    with pytest.raises(ValueError, match="binder tag"):
        eisenstein_rectangle_row_count_prefix(
            "p", "q", "k", "b", "c", "h", tag="bad tag"
        )


def test_eisenstein_rectangle_contracts_are_closed_expanded_native_pa() -> None:
    forbidden_surface_tokens = (
        "BetaAt(",
        "BitCount(",
        "Prime(",
        "RectangleCount(",
        "RowCount(",
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
    assert capstone.startswith("forall p q h k. p = 2 * h + 1 ->")
    assert "exists cb cc total." in capstone
    assert "forall erc_row_rectangle_count_total_prefix" in capstone
    assert "erc_row_code_rectangle_count_total_prefix_witness" in capstone
    assert "ff_u_rectangle_count_total_sum" in capstone
    assert "ff_h_rectangle_count_total_sum_terminal" in capstone


def test_eisenstein_rectangle_bodies_are_constructive_and_bounded() -> None:
    rows, elapsed = _body_receipts()
    assert tuple(row[0] for row in rows) == EXPECTED_NAMES
    assert {row[0]: row[1:6] for row in rows} == EXPECTED_BODY_METRICS
    assert elapsed < _BODY_DEADLINE_SECONDS

    for name, nodes, depth, objects, edges, reused, commands in rows:
        print(
            "EISENSTEIN RECTANGLE BODY RECEIPT "
            f"name={name} nodes={nodes} depth={depth} objects={objects} "
            f"edges={edges} reused={reused} commands={commands}",
            flush=True,
        )
