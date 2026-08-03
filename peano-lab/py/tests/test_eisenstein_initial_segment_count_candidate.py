"""Focused native-body audit for Eisenstein initial-segment counts."""

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
from peano_lab.library.eisenstein_initial_segment_count_candidate import (
    eisenstein_initial_segment_choice,
    eisenstein_initial_segment_prefix,
    make_eisenstein_initial_segment_count_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "eisenstein_initial_segment_indicator_choice",
    "eisenstein_initial_segment_prefix_extend",
    "eisenstein_initial_segment_prefix_exists",
    "eisenstein_initial_segment_prefix_all_bits",
    "eisenstein_initial_segment_decoded_choice",
    "beta_all_one_bit_count_exact",
    "eisenstein_initial_segment_bit_count_functional",
    "eisenstein_initial_segment_bit_count_exact",
)

EXPECTED_DEPENDENCIES = {
    "eisenstein_initial_segment_indicator_choice": ("le_or_lt",),
    "eisenstein_initial_segment_prefix_extend": (
        "beta_prefix_extend",
        "finite_lt_succ_eq_or_lt",
    ),
    "eisenstein_initial_segment_prefix_exists": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "le_succ",
        "le_refl",
        "eisenstein_initial_segment_indicator_choice",
        "eisenstein_initial_segment_prefix_extend",
    ),
    "eisenstein_initial_segment_prefix_all_bits": (),
    "eisenstein_initial_segment_decoded_choice": ("beta_at_unique",),
    "beta_all_one_bit_count_exact": (
        "bit_count_zero",
        "bit_count_succ_decompose",
        "all_bits_prefix_succ",
        "beta_at_unique",
        "le_succ",
        "le_refl",
    ),
    "eisenstein_initial_segment_bit_count_functional": (
        "le_zero",
        "le_eq_or_lt",
        "le_of_succ_le_succ",
        "le_succ",
        "le_refl",
        "lt_not_le",
        "bit_count_zero",
        "bit_count_succ_decompose",
        "eisenstein_initial_segment_decoded_choice",
        "beta_all_one_bit_count_exact",
    ),
    "eisenstein_initial_segment_bit_count_exact": (
        "eisenstein_initial_segment_prefix_all_bits",
        "bit_count_exists",
        "eisenstein_initial_segment_bit_count_functional",
    ),
}

_BODY_DEADLINE_SECONDS = 60


EXPECTED_RECEIPTS = {
    "eisenstein_initial_segment_indicator_choice": (23, 12, 23, 22, 0, 15),
    "eisenstein_initial_segment_prefix_extend": (63, 25, 63, 62, 0, 46),
    "eisenstein_initial_segment_prefix_exists": (40, 19, 40, 39, 0, 33),
    "eisenstein_initial_segment_prefix_all_bits": (25, 14, 25, 24, 0, 23),
    "eisenstein_initial_segment_decoded_choice": (41, 21, 41, 40, 0, 27),
    "beta_all_one_bit_count_exact": (91, 28, 91, 90, 0, 62),
    "eisenstein_initial_segment_bit_count_functional": (
        160,
        37,
        160,
        159,
        0,
        129,
    ),
    "eisenstein_initial_segment_bit_count_exact": (49, 21, 49, 48, 0, 33),
}

EXPECTED_STATEMENT_HASHES = {
    "eisenstein_initial_segment_indicator_choice": "fd63fc3d003ddc6b31729bdc3b1408b45f7e3e435920baa5bf39470619e99d23",
    "eisenstein_initial_segment_prefix_extend": "e6bdc012743870d4ebce325d86d78e4138a796dfcec67f825ea24de87374e364",
    "eisenstein_initial_segment_prefix_exists": "d8da07c23b4358a3de037d7469eca479edd099362e5a70e6266365c7534d10ef",
    "eisenstein_initial_segment_prefix_all_bits": "910772a46dad50758f23be69f9789c249adde801357ce5bb34cc4b2777ebc72b",
    "eisenstein_initial_segment_decoded_choice": "43ebed1b2ade99466bde691b4350b1786a74b6929766bdaabaebbb66e7221a81",
    "beta_all_one_bit_count_exact": "eac6185d0f5c61eaac0f8bc98f7495a3f9a28f3b50c76376f146f30751334503",
    "eisenstein_initial_segment_bit_count_functional": "0134da1f6ba1176ed4427f980bf1761b5775a489295ad1b69bc58465d5e71b50",
    "eisenstein_initial_segment_bit_count_exact": "6749a5f76921cbd97ad4b17e2626780a985469430400df944371ab639ec8b1cc",
}


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_eisenstein_initial_segment_count_candidate_theorems(TheoremSpec)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@contextmanager
def _body_deadline(seconds: int):
    def expired(_signum, _frame):
        raise TimeoutError(f"Eisenstein initial-segment replay exceeded {seconds}s")

    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


@lru_cache(maxsize=None)
def _body_receipt(name: str):
    specs = _candidate_specs()
    local = {item.name: item for item in specs}
    item = local[name]
    core = _specs_by_name()
    target = _closed_formula(item.statement)
    for dependency_name in reversed(item.dependencies):
        dependency = local.get(dependency_name) or core[dependency_name]
        target = Imp(_closed_formula(dependency.statement), target)

    started = perf_counter()
    with _body_deadline(_BODY_DEADLINE_SECONDS):
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

    return (
        nodes,
        depth,
        objects,
        edges,
        reused,
        len(item.script),
        perf_counter() - started,
    )


def test_initial_segment_factory_is_isolated_and_dependency_ordered() -> None:
    first = _candidate_specs()
    second = _candidate_specs()

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    public = _specs_by_name()
    assert all(item.name not in public for item in first)


def test_initial_segment_helpers_are_hygienic_alpha_native_and_exact() -> None:
    choice_left = eisenstein_initial_segment_choice(
        "q", "j", "a", tag="alpha_left"
    )
    choice_right = eisenstein_initial_segment_choice(
        "q", "j", "a", tag="alpha_right"
    )
    prefix_left = eisenstein_initial_segment_prefix(
        "q", "b", "c", "k", tag="alpha_left"
    )
    prefix_right = eisenstein_initial_segment_prefix(
        "q", "b", "c", "k", tag="alpha_right"
    )

    assert choice_left != choice_right
    assert prefix_left != prefix_right
    assert parse_formula(choice_left) == parse_formula(choice_right)
    assert parse_formula(prefix_left) == parse_formula(prefix_right)
    _, choice_names = parse_formula_with_names(choice_left)
    _, prefix_names = parse_formula_with_names(prefix_left)
    assert set(choice_names) == {"q", "j", "a"}
    assert set(prefix_names) == {"q", "b", "c", "k"}
    assert "a = 1" in choice_left
    assert "S j" in choice_left
    assert "a = 0" in choice_left
    assert all(token not in prefix_left for token in ("BetaAt(", "BitCount(", "<=", "<"))

    with pytest.raises(ValueError, match="Peano identifier"):
        eisenstein_initial_segment_prefix(
            "q + 1", "b", "c", "k", tag="bad"
        )
    with pytest.raises(ValueError, match="captures an argument"):
        eisenstein_initial_segment_choice(
            "eis_le_gap_capture_inside", "j", "a", tag="capture"
        )


def test_initial_segment_contracts_are_closed_expanded_native_pa() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "BetaAt(",
                "BitCount(",
                "InitialSegment(",
                "<=",
                "<",
                "%",
                "∣",
            )
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_initial_segment_bodies_are_constructive_exact_and_bounded(
    name: str,
) -> None:
    nodes, depth, objects, edges, reused, commands, elapsed = _body_receipt(name)
    assert (nodes, depth, objects, edges, reused, commands) == EXPECTED_RECEIPTS[name]
    assert elapsed < _BODY_DEADLINE_SECONDS
    statement_hash = sha256(
        {item.name: item for item in _candidate_specs()}[name].statement.encode()
    ).hexdigest()
    assert statement_hash == EXPECTED_STATEMENT_HASHES[name]
    print(
        "EISENSTEIN INITIAL SEGMENT BODY RECEIPT "
        f"name={name} nodes={nodes} depth={depth} objects={objects} "
        f"edges={edges} reused={reused} commands={commands} "
        f"sha256={statement_hash}",
        flush=True,
    )
