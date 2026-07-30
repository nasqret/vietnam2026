"""Isolated admission checks for the native beta-coded BitCount tranche."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache

from peano_lab.engine.state import proof_identity_metrics, proof_metrics
from peano_lab.engine.state import start
from peano_lab.engine.tactics import (
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library.finite_bitcount_theorems import (
    make_finite_bitcount_theorems,
)
from peano_lab.library.finite_fold_surface import (
    BIT_COUNT_BOUNDED,
    BIT_COUNT_EXISTS,
    BIT_COUNT_FUNCTIONAL,
)
from peano_lab.library.theorems import (
    CheckedTheorem,
    FINITE_BITCOUNT_THEOREMS,
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    get,
    replay,
)


BITCOUNT_THEOREMS = make_finite_bitcount_theorems(TheoremSpec)
BITCOUNT_TABLE = {spec.name: spec for spec in BITCOUNT_THEOREMS}

EXPECTED_METRICS = (
    ("all_bits_zero", 41, 15),
    ("all_bits_prefix_succ", 71, 20),
    ("all_bits_last_succ", 48, 15),
    ("bit_count_exists", 30_514, 87),
    ("bit_count_functional", 1_488, 62),
    ("bit_count_zero", 1_216, 61),
    ("bit_count_succ_decompose", 2_608, 63),
    ("bit_count_bounded", 3_987, 65),
)

EXPECTED_IDENTITY_METRICS = (
    ("all_bits_zero", 41, 40, 0),
    ("all_bits_prefix_succ", 69, 70, 2),
    ("all_bits_last_succ", 48, 47, 0),
    ("bit_count_exists", 4_771, 5_006, 236),
    ("bit_count_functional", 1_015, 1_053, 39),
    ("bit_count_zero", 787, 823, 37),
    ("bit_count_succ_decompose", 949, 990, 42),
    ("bit_count_bounded", 1_147, 1_191, 45),
)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@lru_cache(maxsize=None)
def _replay_bitcount(name: str) -> CheckedTheorem:
    spec = BITCOUNT_TABLE[name]
    formula = _closed_formula(spec.statement)
    target = formula
    for dependency in reversed(spec.dependencies):
        dependency_statement = (
            BITCOUNT_TABLE[dependency].statement
            if dependency in BITCOUNT_TABLE
            else replay(dependency).spec.statement
        )
        target = Imp(_closed_formula(dependency_statement), target)

    state = start(target)
    for dependency in spec.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in spec.script:
        tactic, args = _primitive(command)
        state = apply_tactic(state, tactic, args)
    certificate = checked_final(state, target)

    body = certificate
    for _dependency in spec.dependencies:
        assert type(body) is ImpIntro
        body = body.body
    for dependency in reversed(spec.dependencies):
        checked_dependency = (
            _replay_bitcount(dependency)
            if dependency in BITCOUNT_TABLE
            else replay(dependency)
        )
        body = Cut(
            checked_dependency.formula,
            formula,
            checked_dependency.certificate,
            body,
        )

    assert check((), body, formula)
    return CheckedTheorem(spec, formula, body, proof_metrics(body)[0])


def _cold_rows() -> tuple[tuple[str, int, int], ...]:
    _replay_bitcount.cache_clear()
    replay.cache_clear()
    _specs_by_name.cache_clear()
    rows = []
    for spec in BITCOUNT_THEOREMS:
        theorem = _replay_bitcount(spec.name)
        assert check((), theorem.certificate, theorem.formula)
        nodes, depth = proof_metrics(theorem.certificate)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        rows.append((spec.name, nodes, depth))
    return tuple(rows)


def test_bitcount_tranche_replays_deterministically_and_constructively() -> None:
    first = _cold_rows()
    second = _cold_rows()

    assert first == EXPECTED_METRICS
    assert second == first
    assert all(nodes <= MAX_USE_CERTIFICATE_NODES for _, nodes, _ in first)
    assert all(depth <= MAX_USE_PROOF_DEPTH for _, _, depth in first)
    identities = tuple(
        (spec.name, *proof_identity_metrics(_replay_bitcount(spec.name).certificate))
        for spec in BITCOUNT_THEOREMS
    )
    assert identities == EXPECTED_IDENTITY_METRICS
    assert all(
        objects <= MAX_USE_CERTIFICATE_OBJECTS
        for _, objects, _, _ in identities
    )


def test_bitcount_public_contracts_are_exact_expanded_surface_formulas() -> None:
    assert BITCOUNT_TABLE["bit_count_exists"].statement == BIT_COUNT_EXISTS
    assert BITCOUNT_TABLE["bit_count_functional"].statement == BIT_COUNT_FUNCTIONAL
    assert BITCOUNT_TABLE["bit_count_bounded"].statement == BIT_COUNT_BOUNDED
    for spec in BITCOUNT_THEOREMS:
        assert _replay_bitcount(spec.name).formula == parse_formula(spec.statement)
        assert all(
            token not in spec.statement
            for token in ("AllBits", "BitCount", "Sum", "%", "^", "∣")
        )


def test_bitcount_tranche_has_stable_registry_bindings_and_lookup() -> None:
    assert FINITE_BITCOUNT_THEOREMS == BITCOUNT_THEOREMS
    for spec in FINITE_BITCOUNT_THEOREMS:
        assert get(spec.name) is spec
        assert replay(spec.name).formula == _replay_bitcount(spec.name).formula


def test_bitcount_certificate_rejects_an_inconsistent_nearby_contract() -> None:
    theorem = _replay_bitcount("bit_count_zero")
    statement = BITCOUNT_TABLE["bit_count_zero"].statement
    assert statement.endswith("n = 0")
    inconsistent = parse_formula(statement.removesuffix("n = 0") + "n = 1")
    assert not check((), theorem.certificate, inconsistent)
