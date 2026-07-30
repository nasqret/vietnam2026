"""Independent admission audit for relational-power congruence."""

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
from peano_lab.library.power_congruence_theorems import (
    make_power_congruence_theorems,
)
from peano_lab.library.quadratic_residue_surface import congruent_mod
from peano_lab.library.theorems import (
    POWER_CONGRUENCE_THEOREMS,
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
    "pow_one_from_zero_successor": (3_827, 64, 1_043, 1_089, 47),
    "pow_one": (3_856, 65, 1_072, 1_118, 47),
    "pow_successor_pair_mul": (5_282, 65, 1_293, 1_338, 46),
    "pow_mod_congruent": (10_671, 68, 1_748, 1_810, 63),
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
    specs = make_power_congruence_theorems(TheoremSpec)
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


def test_power_congruence_replays_twice_constructively_within_resources() -> None:
    first = _rows()
    second = _rows()

    assert second == first
    assert tuple(row[0] for row in first) == tuple(EXPECTED)
    assert {row[0]: row[1:] for row in first} == EXPECTED
    assert all(row[1] <= MAX_USE_CERTIFICATE_NODES for row in first)
    assert all(row[2] <= MAX_USE_PROOF_DEPTH for row in first)
    assert all(row[3] <= MAX_USE_CERTIFICATE_OBJECTS for row in first)


def test_power_congruence_contracts_are_exact_expanded_surfaces() -> None:
    specs = {
        spec.name: spec for spec in make_power_congruence_theorems(TheoremSpec)
    }
    expected_carrier = (
        "forall a z e n. z = 0 -> e = S z -> "
        f"({power_relation('a', 'e', 'n', tag='one_carrier')}) -> n = a"
    )
    expected_one = (
        "forall a e n. e = 1 -> "
        f"({power_relation('a', 'e', 'n', tag='one')}) -> n = a"
    )
    expected_pair = (
        "forall a e se r n. se = S e -> "
        f"({power_relation('a', 'e', 'r', tag='pair_predecessor')}) -> "
        f"({power_relation('a', 'se', 'n', tag='pair_successor')}) -> "
        "n = r * a"
    )
    expected_congruence = (
        "forall m a b e x y. "
        f"({congruent_mod('m', 'a', 'b', tag='base')}) -> "
        f"({power_relation('a', 'e', 'x', tag='left')}) -> "
        f"({power_relation('b', 'e', 'y', tag='right')}) -> "
        f"({congruent_mod('m', 'x', 'y', tag='result')})"
    )
    assert tuple(specs) == tuple(EXPECTED)
    assert specs["pow_one_from_zero_successor"].statement == expected_carrier
    assert specs["pow_one"].statement == expected_one
    assert specs["pow_successor_pair_mul"].statement == expected_pair
    assert specs["pow_mod_congruent"].statement == expected_congruence
    for spec in specs.values():
        assert _closed_formula(spec.statement) == parse_formula(spec.statement)
        assert len(spec.statement) < driver.MAX_INPUT
        assert all(
            token not in spec.statement
            for token in ("Pow(", "Repeat(", "Product(", "ModEq(", "%", "^", "∣")
        )


def test_power_congruence_has_stable_public_registry_and_kernel_replay() -> None:
    expected = make_power_congruence_theorems(TheoremSpec)
    assert POWER_CONGRUENCE_THEOREMS == expected
    _, run = _fresh_replayer()
    for spec in POWER_CONGRUENCE_THEOREMS:
        assert get(spec.name) is spec
        public = replay(spec.name)
        isolated = run(spec.name)
        assert public.formula == isolated.formula
        assert check((), public.certificate, public.formula)


def test_power_congruence_rejects_contract_and_cut_mutations() -> None:
    specs, run = _fresh_replayer()
    theorem = run("pow_one")
    statement = next(spec.statement for spec in specs if spec.name == "pow_one")
    assert statement.endswith("n = a")
    inconsistent = parse_formula(statement.removesuffix("n = a") + "n = 1")
    assert not check((), theorem.certificate, inconsistent)

    theorem = run("pow_mod_congruent")
    assert type(theorem.certificate) is Cut
    zero = Zero()
    true = Eq(zero, zero)
    mutated = replace(
        theorem.certificate,
        proposition=true,
        lemma=EqRefl(zero),
    )
    assert not check((), mutated, theorem.formula)
