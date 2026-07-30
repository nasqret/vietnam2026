"""Isolated admission checks for the beta-coded consecutive Range tranche."""

from __future__ import annotations

from dataclasses import fields

from peano_lab.engine.state import proof_metrics, proof_size, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import theorems
from peano_lab.library.finite_fold_surface import RANGE_EXISTS, range_relation
from peano_lab.library.finite_range_theorems import make_finite_range_theorems


SPECS = theorems.FINITE_RANGE_THEOREMS

EXPECTED_METRICS = (
    ("beta_range_empty", 42, 16),
    ("beta_range_succ_extend", 29_230, 81),
    ("beta_range_exists", 29_328, 83),
    ("beta_range_entry_eq", 1_144, 60),
    ("beta_range_transport_entry", 1_191, 61),
)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _replay_isolated() -> dict[str, tuple[Proof, object]]:
    """Replay the tranche without mutating the public theorem registry."""

    global_specs = theorems._specs_by_name()
    local_specs = {spec.name: spec for spec in SPECS}
    checked: dict[str, tuple[Proof, object]] = {}

    for spec in SPECS:
        formula = parse_formula(spec.statement)
        target = formula
        dependency_formulas = []
        for dependency in spec.dependencies:
            if dependency in local_specs:
                dependency_formula = parse_formula(local_specs[dependency].statement)
            else:
                dependency_formula = parse_formula(global_specs[dependency].statement)
            dependency_formulas.append(dependency_formula)
        for dependency_formula in reversed(dependency_formulas):
            target = Imp(dependency_formula, target)

        state = start(target)
        for dependency in spec.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in spec.script:
            pieces = command.strip().split(maxsplit=1)
            state = apply_tactic(
                state, pieces[0], pieces[1] if len(pieces) == 2 else ""
            )
        body = checked_final(state, target)
        for dependency in spec.dependencies:
            assert type(body) is ImpIntro
            body = body.body

        dependency_proofs = []
        for dependency in spec.dependencies:
            if dependency in checked:
                dependency_proofs.append(checked[dependency][0])
            else:
                dependency_proofs.append(theorems.replay(dependency).certificate)
        for dependency_formula, dependency_proof in reversed(
            tuple(zip(dependency_formulas, dependency_proofs, strict=True))
        ):
            body = Cut(dependency_formula, formula, dependency_proof, body)

        assert check((), body, formula)
        assert proof_size(body) == proof_metrics(body)[0]
        checked[spec.name] = (body, formula)

    return checked


def _cold_rows() -> tuple[tuple[str, int, int], ...]:
    theorems.replay.cache_clear()
    theorems._specs_by_name.cache_clear()
    checked = _replay_isolated()
    rows = []
    for spec in SPECS:
        certificate, _ = checked[spec.name]
        nodes, depth = proof_metrics(certificate)
        assert not any(type(node) is DNE for node in _walk(certificate))
        rows.append((spec.name, nodes, depth))
    return tuple(rows)


def test_range_tranche_replays_deterministically_and_constructively() -> None:
    first = _cold_rows()
    second = _cold_rows()

    assert first == EXPECTED_METRICS
    assert second == first


def test_range_exists_is_the_exact_hygienic_surface_contract() -> None:
    specs = {spec.name: spec for spec in SPECS}
    assert SPECS == make_finite_range_theorems(theorems.TheoremSpec)
    assert tuple(specs) == tuple(name for name, _, _ in EXPECTED_METRICS)
    assert specs["beta_range_exists"].statement == RANGE_EXISTS
    assert all(theorems.get(spec.name) is spec for spec in SPECS)
    assert all(
        token not in RANGE_EXISTS for token in ("Range", "BetaAt", "%", "^", "∣")
    )


def test_range_certificate_rejects_a_shifted_contract() -> None:
    certificate, _ = _replay_isolated()["beta_range_exists"]
    shifted = range_relation("b", "c", "l", "a", tag="shifted")
    wrong = parse_formula(f"forall a l. exists b c. ({shifted})")
    assert not check((), certificate, wrong)
