"""Independent admission audit for relational-power algebra."""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from functools import lru_cache

import driver

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
from peano_lab.library.finite_fold_surface import power_relation
from peano_lab.library.power_algebra_theorems import (
    _power_terms,
    make_power_algebra_theorems,
)
from peano_lab.library.theorems import (
    POWER_ALGEBRA_THEOREMS,
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    get,
    replay,
)


# name -> structural occurrences, depth, distinct objects, object edges,
# reused object references
EXPECTED = {
    "pow_two_from_one_successor": (6_431, 67, 1_106, 1_153, 48),
    "pow_two": (6_460, 68, 1_135, 1_182, 48),
    "pow_add": (6_744, 66, 1_530, 1_588, 59),
    "pow_mul_exp": (70_463, 91, 5_786, 6_047, 262),
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
    specs = make_power_algebra_theorems(TheoremSpec)
    local = {spec.name: spec for spec in specs}
    core = _specs_by_name()

    @lru_cache(maxsize=None)
    def run(name: str) -> _Checked:
        spec = local[name]
        formula = _closed_formula(spec.statement)
        target = formula
        for dependency in reversed(spec.dependencies):
            dependency_statement = (
                local[dependency].statement
                if dependency in local
                else core[dependency].statement
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


def test_power_algebra_replays_twice_constructively_within_resources() -> None:
    first = _rows()
    second = _rows()

    assert second == first
    assert tuple(row[0] for row in first) == tuple(EXPECTED)
    assert {row[0]: row[1:] for row in first} == EXPECTED
    assert all(row[1] <= MAX_USE_CERTIFICATE_NODES for row in first)
    assert all(row[2] <= MAX_USE_PROOF_DEPTH for row in first)
    assert all(row[3] <= MAX_USE_CERTIFICATE_OBJECTS for row in first)


def test_power_algebra_contracts_are_closed_expanded_pow_surfaces() -> None:
    specs = {spec.name: spec for spec in make_power_algebra_theorems(TheoremSpec)}
    expected_two = (
        "forall a e n. e = 2 -> "
        f"({power_relation('a', 'e', 'n', tag='two')}) -> n = a * a"
    )
    expected_add = (
        "forall a e f s x y z. s = e + f -> "
        f"({power_relation('a', 'e', 'x', tag='add_left')}) -> "
        f"({power_relation('a', 'f', 'y', tag='add_right')}) -> "
        f"({power_relation('a', 's', 'z', tag='add_total')}) -> z = x * y"
    )
    expected_mul = (
        "forall a e f p x y z. p = e * f -> "
        f"({power_relation('a', 'e', 'x', tag='mul_base')}) -> "
        f"({power_relation('x', 'f', 'y', tag='mul_outer')}) -> "
        f"({power_relation('a', 'p', 'z', tag='mul_total')}) -> y = z"
    )
    assert specs["pow_two"].statement == expected_two
    assert specs["pow_add"].statement == expected_add
    assert specs["pow_mul_exp"].statement == expected_mul
    assert parse_formula(_power_terms("a", "e", "n", tag="probe")) == (
        parse_formula(power_relation("a", "e", "n", tag="probe"))
    )
    _closed_formula(
        f"forall a e f r. ({_power_terms('a', 'e + f', 'r', tag='sum_probe')})"
    )
    for spec in specs.values():
        assert _closed_formula(spec.statement) == parse_formula(spec.statement)
        assert len(spec.statement) < driver.MAX_INPUT
        assert all(
            token not in spec.statement
            for token in ("Pow(", "Repeat(", "Product(", "%", "^", "∣")
        )


def test_power_algebra_has_stable_public_registry_and_kernel_replay() -> None:
    expected = make_power_algebra_theorems(TheoremSpec)
    assert POWER_ALGEBRA_THEOREMS == expected
    _, run = _fresh_replayer()
    for spec in POWER_ALGEBRA_THEOREMS:
        assert get(spec.name) is spec
        public = replay(spec.name)
        isolated = run(spec.name)
        assert public.formula == isolated.formula
        assert check((), public.certificate, public.formula)


def test_power_algebra_rejects_contract_and_cut_mutations() -> None:
    specs, run = _fresh_replayer()
    theorem = run("pow_two")
    statement = next(spec.statement for spec in specs if spec.name == "pow_two")
    assert statement.endswith("n = a * a")
    inconsistent = parse_formula(statement.removesuffix("n = a * a") + "n = a")
    assert not check((), theorem.certificate, inconsistent)

    theorem = run("pow_mul_exp")
    assert type(theorem.certificate) is Cut
    zero = Zero()
    true = Eq(zero, zero)
    mutated = replace(
        theorem.certificate,
        proposition=true,
        lemma=EqRefl(zero),
    )
    assert not check((), mutated, theorem.formula)
