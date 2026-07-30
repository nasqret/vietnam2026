"""Independent admission audit for exact QRes classifications mod 3, 5, 7."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from functools import lru_cache

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.qr_small_moduli import make_qr_small_moduli_theorems
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


# name -> structural occurrences, depth, distinct objects, object edges,
# reused object references
EXPECTED = {
    "lt_three_cases": (182, 21, 178, 181, 4),
    "lt_five_cases": (331, 24, 213, 218, 6),
    "lt_seven_cases": (480, 27, 248, 255, 8),
    "bounded_square_mod3_classify": (1_767, 62, 1_149, 1_177, 29),
    "bounded_square_mod5_classify": (2_567, 62, 1_835, 1_865, 31),
    "bounded_square_mod7_classify": (4_033, 91, 3_187, 3_219, 33),
    "qres_mod3_zero": (40, 14, 40, 39, 0),
    "qres_mod3_one": (57, 14, 57, 56, 0),
    "qres_mod5_zero": (44, 16, 44, 43, 0),
    "qres_mod5_one": (61, 16, 61, 60, 0),
    "qres_mod5_four": (90, 18, 90, 89, 0),
    "qres_mod7_zero": (48, 18, 48, 47, 0),
    "qres_mod7_one": (65, 18, 65, 64, 0),
    "qres_mod7_two": (208, 27, 208, 207, 0),
    "qres_mod7_four": (94, 18, 94, 93, 0),
    "qres_mod3_canonical_iff": (4_050, 65, 1_850, 1_930, 81),
    "qres_mod5_canonical_iff": (4_955, 65, 2_641, 2_723, 83),
    "qres_mod7_canonical_iff": (6_648, 94, 4_220, 4_304, 85),
    "not_qres_mod3_two": (4_103, 66, 1_903, 1_983, 81),
    "not_qres_mod5_two": (5_025, 66, 2_711, 2_793, 83),
    "not_qres_mod5_three": (5_034, 66, 2_720, 2_802, 83),
    "not_qres_mod7_three": (6_743, 95, 4_315, 4_399, 85),
    "not_qres_mod7_five": (6_756, 95, 4_328, 4_412, 85),
    "not_qres_mod7_six": (6_761, 95, 4_333, 4_417, 85),
}

POSITIVE_NAMES = {
    3: ("qres_mod3_zero", "qres_mod3_one"),
    5: ("qres_mod5_zero", "qres_mod5_one", "qres_mod5_four"),
    7: (
        "qres_mod7_zero",
        "qres_mod7_one",
        "qres_mod7_two",
        "qres_mod7_four",
    ),
}

NEGATIVE_NAMES = {
    3: ("not_qres_mod3_two",),
    5: ("not_qres_mod5_two", "not_qres_mod5_three"),
    7: (
        "not_qres_mod7_three",
        "not_qres_mod7_five",
        "not_qres_mod7_six",
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
    specs = make_qr_small_moduli_theorems(TheoremSpec)
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


def _rows() -> tuple[tuple[str, int, int, int, int, int], ...]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    specs, run = _fresh_replayer()
    rows = []
    for spec in specs:
        theorem = run(spec.name)
        nodes, depth = proof_metrics(theorem.certificate)
        objects, edges, reused = proof_identity_metrics(theorem.certificate)
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        rows.append((spec.name, nodes, depth, objects, edges, reused))
    return tuple(rows)


def test_small_moduli_replay_deterministically_and_constructively() -> None:
    first = _rows()
    second = _rows()

    assert second == first
    assert tuple(row[0] for row in first) == tuple(EXPECTED)
    assert {row[0]: row[1:] for row in first} == EXPECTED
    assert all(row[1] <= MAX_USE_CERTIFICATE_NODES for row in first)
    assert all(row[2] <= MAX_USE_PROOF_DEPTH for row in first)
    assert all(row[3] <= MAX_USE_CERTIFICATE_OBJECTS for row in first)


def test_small_moduli_contracts_are_closed_expanded_and_complete() -> None:
    specs = make_qr_small_moduli_theorems(TheoremSpec)
    table = {spec.name: spec for spec in specs}

    assert tuple(table) == tuple(EXPECTED)
    assert sum(len(names) for names in POSITIVE_NAMES.values()) == 9
    assert sum(len(names) for names in NEGATIVE_NAMES.values()) == 6
    assert set(name for names in POSITIVE_NAMES.values() for name in names) <= set(table)
    assert set(name for names in NEGATIVE_NAMES.values() for name in names) <= set(table)

    expected_cases = {
        3: "a = 0 \\/ a = 1",
        5: "a = 0 \\/ a = 1 \\/ a = 4",
        7: "a = 0 \\/ a = 1 \\/ a = 2 \\/ a = 4",
    }
    for modulus, cases in expected_cases.items():
        statement = table[f"qres_mod{modulus}_canonical_iff"].statement
        assert statement.count(cases) == 2

    for spec in specs:
        assert _closed_formula(spec.statement) == parse_formula(spec.statement)
        assert len(spec.statement) < 4_000
        assert all(
            token not in spec.statement
            for token in (
                "QRes(",
                "BoundedQRes(",
                "ModEq(",
                "%",
                "^",
                "∣",
            )
        )


def test_small_moduli_reject_false_contract_and_cut_mutations() -> None:
    specs, run = _fresh_replayer()
    table = {spec.name: spec for spec in specs}

    positive = run("qres_mod7_two")
    false_positive = parse_formula(
        "exists x. exists u v. x * x + 7 * u = 3 + 7 * v"
    )
    assert not check((), positive.certificate, false_positive)

    classification = run("qres_mod7_canonical_iff")
    statement = table["qres_mod7_canonical_iff"].statement
    assert statement.count("a = 4") == 2
    false_classification = parse_formula(statement.replace("a = 4", "a = 3"))
    assert not check((), classification.certificate, false_classification)

    negative = run("not_qres_mod7_six")
    false_negative = parse_formula(
        "~(exists x. exists u v. x * x + 7 * u = 4 + 7 * v)"
    )
    assert not check((), negative.certificate, false_negative)

    assert type(negative.certificate) is Cut
    zero = Zero()
    true = Eq(zero, zero)
    mutated = replace(
        negative.certificate,
        proposition=true,
        lemma=EqRefl(zero),
    )
    assert not check((), mutated, negative.formula)

