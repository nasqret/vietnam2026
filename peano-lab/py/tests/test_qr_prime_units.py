"""Independent admission audit for the isolated QR prime/unit tranche."""

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
from peano_lab.library.qr_prime_units import make_qr_prime_unit_theorems
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED = {
    "prime_coprime_or_divides": (1_572, 47, 1_069, 1_134, 66),
    "prime_not_divides_coprime": (1_588, 48, 1_085, 1_150, 66),
    "distinct_primes_coprime": (1_675, 50, 1_115, 1_181, 67),
    "coprime_balanced_mod_inverse": (2_365, 49, 1_269, 1_350, 82),
    "coprime_mod_inverse": (3_820, 51, 1_549, 1_642, 94),
    "mod_eq_cancel_coprime": (5_804, 52, 1_762, 1_863, 102),
    "prime_mod_inverse": (5_491, 54, 1_946, 2_063, 118),
    "prime_mod_cancel": (7_494, 56, 2_178, 2_303, 126),
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
    specs = make_qr_prime_unit_theorems(TheoremSpec)
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


def test_prime_unit_tranche_replays_deterministically_and_constructively() -> None:
    first = _rows()
    second = _rows()

    assert second == first
    assert tuple(row[0] for row in first) == tuple(EXPECTED)
    assert {row[0]: row[1:] for row in first} == EXPECTED
    assert all(row[1] <= MAX_USE_CERTIFICATE_NODES for row in first)
    assert all(row[2] <= MAX_USE_PROOF_DEPTH for row in first)
    assert all(row[3] <= MAX_USE_CERTIFICATE_OBJECTS for row in first)


def test_prime_unit_contracts_are_closed_native_pa_formulas() -> None:
    specs = make_qr_prime_unit_theorems(TheoremSpec)
    assert tuple(spec.name for spec in specs) == tuple(EXPECTED)
    for spec in specs:
        assert _closed_formula(spec.statement) == parse_formula(spec.statement)
        assert all(
            token not in spec.statement
            for token in (
                "Prime(",
                "Coprime(",
                "ModEq(",
                "Dvd(",
                "%",
                "^",
                "∣",
            )
        )


def test_prime_mod_cancel_rejects_contract_and_cut_mutations() -> None:
    _, run = _fresh_replayer()
    theorem = run("prime_mod_cancel")
    inconsistent = parse_formula(
        "forall p a x y. "
        "(~(p = 1) /\\ forall c e. p = c * e -> c = 1 \\/ e = 1) -> "
        "~(exists k. a = p * k) -> "
        "(exists u v. (a * x) + p * u = (a * y) + p * v) -> "
        "(exists r s. x + p * r = y + p * s) /\\ "
        "~(exists r s. x + p * r = y + p * s)"
    )
    assert not check((), theorem.certificate, inconsistent)

    assert type(theorem.certificate) is Cut
    zero = Zero()
    true = Eq(zero, zero)
    mutated = replace(
        theorem.certificate,
        proposition=true,
        lemma=EqRefl(zero),
    )
    assert not check((), mutated, theorem.formula)

