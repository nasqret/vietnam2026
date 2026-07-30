"""Independent admission audit for checked QR bounded prime units."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import (
    Eq,
    Formula,
    Imp,
    parse_formula,
    parse_formula_with_names,
)
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.qr_bounded_units import (
    balanced_inverse,
    bounded_nonzero_inverse,
    make_qr_bounded_unit_theorems,
    prime,
    strictly_below,
)
from peano_lab.library.theorems import (
    QR_BOUNDED_UNIT_THEOREMS,
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    get,
    replay,
)


# name -> structural occurrences, depth, distinct objects, object edges,
# reused object references, Cut occurrences.  These are exact receipts from
# genuinely cold isolated replays.
EXPECTED = {
    "prime_is_succ_succ": (98, 13, 98, 97, 0, 4),
    "prime_bounded_nonzero_mod_inverse": (
        8_684,
        71,
        2_801,
        2_951,
        151,
        260,
    ),
}

EXPECTED_DEPENDENCIES = {
    "prime_is_succ_succ": ("prime_nonzero", "nonzero_is_succ"),
    "prime_bounded_nonzero_mod_inverse": (
        "prime_is_succ_succ",
        "prime_nonzero",
        "divisor_le_nonzero",
        "lt_not_le",
        "prime_mod_inverse",
        "division_remainder_exists",
        "mul_comm",
        "remainder_decomposition_to_mod_eq",
        "mod_eq_mul_left",
        "mod_eq_symm",
        "mod_eq_trans",
        "mod_eq_bounded_unique",
        "succ_ne_zero",
    ),
}

EXPECTED_STATEMENTS = {
    "prime_is_succ_succ": (
        "forall p. ((~(p = 1) /\\ forall qrbu_factor_left_prime_p "
        "qrbu_factor_right_prime_p. p = qrbu_factor_left_prime_p * "
        "qrbu_factor_right_prime_p -> qrbu_factor_left_prime_p = 1 \\/ "
        "qrbu_factor_right_prime_p = 1)) -> exists k. p = S (S k)"
    ),
    "prime_bounded_nonzero_mod_inverse": (
        "forall p a. ((~(p = 1) /\\ forall qrbu_factor_left_prime_p "
        "qrbu_factor_right_prime_p. p = qrbu_factor_left_prime_p * "
        "qrbu_factor_right_prime_p -> qrbu_factor_left_prime_p = 1 \\/ "
        "qrbu_factor_right_prime_p = 1)) -> ~(a = 0) -> (exists "
        "qrbu_gap_a_lt_p. qrbu_gap_a_lt_p + S a = p) -> (exists "
        "qrbu_inverse_bounded_inverse. "
        "(~(qrbu_inverse_bounded_inverse = 0) /\\ ((exists "
        "qrbu_gap_bounded_inverse_bound. "
        "qrbu_gap_bounded_inverse_bound + S "
        "qrbu_inverse_bounded_inverse = p) /\\ (exists "
        "qrbu_mod_left_bounded_inverse_mod "
        "qrbu_mod_right_bounded_inverse_mod. a * "
        "qrbu_inverse_bounded_inverse + p * "
        "qrbu_mod_left_bounded_inverse_mod = 1 + p * "
        "qrbu_mod_right_bounded_inverse_mod))))"
    ),
}

EXPECTED_STATEMENT_SHA256 = {
    "prime_is_succ_succ": (
        "3ade15c63f82b8b6f96ddbc586c1b59313dee6864a8e2cc690c3359b19cebc7e"
    ),
    "prime_bounded_nonzero_mod_inverse": (
        "67905ae851dfcbf579ebf65b1f411b870c81a35367a23dea591006a7d8a1df92"
    ),
}


@dataclass(frozen=True)
class _Checked:
    formula: Formula
    certificate: Proof


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _fresh_replayer():
    specs = make_qr_bounded_unit_theorems(TheoremSpec)
    local = {spec.name: spec for spec in specs}
    core = _specs_by_name()

    @lru_cache(maxsize=None)
    def run(name: str) -> _Checked:
        spec = local[name]
        formula = _closed_formula(spec.statement)
        target = formula
        for dependency in reversed(spec.dependencies):
            dependency_spec = local.get(dependency) or core[dependency]
            target = Imp(_closed_formula(dependency_spec.statement), target)

        state = start(target)
        for dependency in spec.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in spec.script:
            tactic, args = _primitive(command)
            state = apply_tactic(state, tactic, args)
        certificate = checked_final(state, target)

        body = certificate
        for _ in spec.dependencies:
            assert type(body) is ImpIntro
            body = body.body
        for dependency in reversed(spec.dependencies):
            checked_dependency = (
                run(dependency) if dependency in local else replay(dependency)
            )
            body = Cut(
                checked_dependency.formula,
                formula,
                checked_dependency.certificate,
                body,
            )

        assert check((), body, formula)
        return _Checked(formula, body)

    return specs, run


def _rows() -> tuple[tuple[str, int, int, int, int, int, int], ...]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    specs, run = _fresh_replayer()
    rows = []
    for spec in specs:
        theorem = run(spec.name)
        nodes, depth = proof_metrics(theorem.certificate)
        objects, edges, reused = proof_identity_metrics(theorem.certificate)
        cuts = sum(type(node) is Cut for node in _walk(theorem.certificate))
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        rows.append((spec.name, nodes, depth, objects, edges, reused, cuts))
    return tuple(rows)


def test_bounded_units_replay_twice_with_exact_receipts() -> None:
    first = _rows()
    second = _rows()

    assert second == first
    assert tuple(row[0] for row in first) == tuple(EXPECTED)
    assert {row[0]: row[1:] for row in first} == EXPECTED
    assert all(row[1] <= MAX_USE_CERTIFICATE_NODES for row in first)
    assert all(row[2] <= MAX_USE_PROOF_DEPTH for row in first)
    assert all(row[3] <= MAX_USE_CERTIFICATE_OBJECTS for row in first)


def test_bounded_unit_contracts_are_exact_closed_expanded_native_pa() -> None:
    specs = make_qr_bounded_unit_theorems(TheoremSpec)
    table = {spec.name: spec for spec in specs}

    assert tuple(table) == tuple(EXPECTED)
    assert QR_BOUNDED_UNIT_THEOREMS == specs
    for item in QR_BOUNDED_UNIT_THEOREMS:
        assert get(item.name) is item
        assert replay(item.name).formula == _closed_formula(item.statement)
    assert {name: item.dependencies for name, item in table.items()} == (
        EXPECTED_DEPENDENCIES
    )
    assert {name: item.statement for name, item in table.items()} == (
        EXPECTED_STATEMENTS
    )
    assert {
        name: sha256(item.statement.encode()).hexdigest()
        for name, item in table.items()
    } == EXPECTED_STATEMENT_SHA256

    for item in specs:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert _closed_formula(item.statement) == formula
        assert formula == parse_formula(item.statement)
        assert len(item.statement) < 8_192
        assert all(
            token not in item.statement
            for token in (
                "Prime(",
                "StrictlyBelow(",
                "BoundedInverse(",
                "ModEq(",
                "%",
                "^",
                "∣",
            )
        )


def test_bounded_unit_surface_helpers_are_exact_and_hygienic() -> None:
    surfaces = {
        prime("p", tag="audit_prime"): {
            "p",
        },
        strictly_below("a", "p", tag="audit_lt"): {"a", "p"},
        balanced_inverse("p", "a", "z", tag="audit_inverse"): {
            "a",
            "p",
            "z",
        },
        bounded_nonzero_inverse("p", "a", tag="audit_bounded"): {
            "a",
            "p",
        },
    }
    expected = (
        "(~(p = 1) /\\ forall qrbu_factor_left_audit_prime "
        "qrbu_factor_right_audit_prime. p = qrbu_factor_left_audit_prime * "
        "qrbu_factor_right_audit_prime -> qrbu_factor_left_audit_prime = 1 "
        "\\/ qrbu_factor_right_audit_prime = 1)",
        "exists qrbu_gap_audit_lt. qrbu_gap_audit_lt + S a = p",
        "exists qrbu_mod_left_audit_inverse qrbu_mod_right_audit_inverse. "
        "a * z + p * qrbu_mod_left_audit_inverse = 1 + p * "
        "qrbu_mod_right_audit_inverse",
        "exists qrbu_inverse_audit_bounded. "
        "(~(qrbu_inverse_audit_bounded = 0) /\\ ((exists "
        "qrbu_gap_audit_bounded_bound. qrbu_gap_audit_bounded_bound + S "
        "qrbu_inverse_audit_bounded = p) /\\ (exists "
        "qrbu_mod_left_audit_bounded_mod qrbu_mod_right_audit_bounded_mod. "
        "a * qrbu_inverse_audit_bounded + p * "
        "qrbu_mod_left_audit_bounded_mod = 1 + p * "
        "qrbu_mod_right_audit_bounded_mod)))",
    )

    assert tuple(surfaces) == expected
    for surface, expected_free_names in surfaces.items():
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected_free_names

    with pytest.raises(ValueError, match="Peano identifier"):
        strictly_below("a + 1", "p", tag="bad_term")
    with pytest.raises(ValueError, match="binder tag"):
        prime("p", tag="bad tag")
    with pytest.raises(ValueError, match="captures an argument"):
        prime("qrbu_factor_left_capture", tag="capture")


def test_bounded_inverse_rejects_false_contract_and_cut_mutations() -> None:
    specs, run = _fresh_replayer()
    theorem = run("prime_bounded_nonzero_mod_inverse")
    statement = next(
        item.statement
        for item in specs
        if item.name == "prime_bounded_nonzero_mod_inverse"
    )
    marker = "~(qrbu_inverse_bounded_inverse = 0)"
    assert statement.count(marker) == 1
    false_contract = parse_formula(
        statement.replace(marker, "qrbu_inverse_bounded_inverse = 0")
    )
    assert not check((), theorem.certificate, false_contract)

    assert type(theorem.certificate) is Cut
    zero = Zero()
    true = Eq(zero, zero)
    mutated_cut = replace(
        theorem.certificate,
        proposition=true,
        lemma=EqRefl(zero),
    )
    assert not check((), mutated_cut, theorem.formula)
