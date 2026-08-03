"""Independent admission audit for the constructive Gauss-sign bridge."""

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
from peano_lab.library.gauss_sign_bridge import make_gauss_sign_bridge_theorems
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
    "predecessor_square_mod_one": (426, 27, 234, 263, 30),
    "even_successor_to_odd": (1_074, 62, 751, 785, 35),
    "odd_successor_to_even": (1_102, 62, 773, 813, 41),
    "pow_predecessor_parity_mod": (9_249, 67, 1_758, 1_859, 102),
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
    specs = make_gauss_sign_bridge_theorems(TheoremSpec)
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


def test_gauss_sign_bridge_replays_deterministically_constructively() -> None:
    first = _rows()
    second = _rows()

    assert second == first
    assert tuple(row[0] for row in first) == tuple(EXPECTED)
    assert {row[0]: row[1:] for row in first} == EXPECTED
    assert all(row[1] <= MAX_USE_CERTIFICATE_NODES for row in first)
    assert all(row[2] <= MAX_USE_PROOF_DEPTH for row in first)
    assert all(row[3] <= MAX_USE_CERTIFICATE_OBJECTS for row in first)


def test_gauss_sign_contracts_are_closed_expanded_native_pa() -> None:
    specs = make_gauss_sign_bridge_theorems(TheoremSpec)
    table = {spec.name: spec for spec in specs}

    assert tuple(table) == tuple(EXPECTED)
    assert table["predecessor_square_mod_one"].statement == (
        "forall p r. p = S r -> exists gs_u_square gs_v_square. "
        "(r * r) + p * gs_u_square = (1) + p * gs_v_square"
    )
    main = table["pow_predecessor_parity_mod"]
    assert len(main.statement) == 2_344
    assert main.script.count("induction e") == 1
    assert "p = S r" in main.statement
    assert "e = 2 * gs_even_main" in main.statement
    assert "e = 2 * gs_odd_main + 1" in main.statement

    for spec in specs:
        assert _closed_formula(spec.statement) == parse_formula(spec.statement)
        assert len(spec.statement) < 8_192
        assert all(
            token not in spec.statement
            for token in (
                "Pow(",
                "Even(",
                "Odd(",
                "ModEq(",
                "%",
                "^",
                "∣",
            )
        )


def test_gauss_sign_rejects_false_contract_and_cut_mutations() -> None:
    specs, run = _fresh_replayer()
    table = {spec.name: spec for spec in specs}

    square = run("predecessor_square_mod_one")
    false_square = parse_formula(
        "forall p r. p = S r -> exists u v. "
        "(r * r) + p * u = 0 + p * v"
    )
    assert not check((), square.certificate, false_square)

    power = run("pow_predecessor_parity_mod")
    statement = table["pow_predecessor_parity_mod"].statement
    marker = "= (1) + p * gs_v_result_even"
    assert statement.count(marker) == 1
    false_power = parse_formula(statement.replace(marker, "= (r) + p * gs_v_result_even"))
    assert not check((), power.certificate, false_power)

    assert type(power.certificate) is Cut
    zero = Zero()
    true = Eq(zero, zero)
    mutated = replace(
        power.certificate,
        proposition=true,
        lemma=EqRefl(zero),
    )
    assert not check((), mutated, power.formula)

