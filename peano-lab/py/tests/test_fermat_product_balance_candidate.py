"""WMI-only discovery audit for the isolated Fermat product balance."""

from __future__ import annotations

import gc
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
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.fermat_product_balance_candidate import (
    make_fermat_product_balance_candidate_theorems,
    residue_reindex_data,
    residue_reindex_witness,
)
from peano_lab.library.fermat_residue_map_candidate import (
    make_fermat_residue_map_candidate_theorems,
)
from peano_lab.library.fermat_residue_product_candidate import (
    make_fermat_residue_product_candidate_theorems,
)
from peano_lab.library.fermat_residue_reindex_candidate import (
    make_fermat_residue_reindex_candidate_theorems,
)
from peano_lab.library.fermat_scale_product_candidate import (
    make_fermat_scale_product_candidate_theorems,
)
from peano_lab.library.finite_product_reindex_candidate import (
    make_finite_product_reindex_candidate,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAME = "prime_mul_residue_product_balance"
EXPECTED_DEPENDENCIES = (
    "prime_mul_residue_reindex_exists",
    "beta_product_pointwise_scale_mod",
    "beta_product_exists",
    "beta_product_permutation_invariant",
)


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


def _candidate_sources() -> tuple[tuple[TheoremSpec, ...], tuple[TheoremSpec, ...]]:
    prerequisites = (
        make_fermat_residue_product_candidate_theorems(TheoremSpec)
        + make_fermat_residue_map_candidate_theorems(TheoremSpec)
        + make_fermat_scale_product_candidate_theorems(TheoremSpec)
        + make_fermat_residue_reindex_candidate_theorems(TheoremSpec)
        + make_finite_product_reindex_candidate(TheoremSpec)
    )
    targets = make_fermat_product_balance_candidate_theorems(TheoremSpec)
    return prerequisites, targets


def _fresh_replayer():
    prerequisites, targets = _candidate_sources()
    core = _specs_by_name()
    local: dict[str, TheoremSpec] = {}
    for candidate in prerequisites + targets:
        if candidate.name in core:
            assert core[candidate.name] == candidate
        else:
            assert candidate.name not in local
            local[candidate.name] = candidate
    assert all(item.name not in core for item in targets)

    @lru_cache(maxsize=None)
    def run(name: str) -> _Checked:
        if name in core:
            checked = replay(name)
            return _Checked(checked.formula, checked.certificate)
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
            checked_dependency = run(dependency)
            body = Cut(
                checked_dependency.formula,
                formula,
                checked_dependency.certificate,
                body,
            )
        assert check((), body, formula)
        return _Checked(formula, body)

    return targets, local, core, run


def _cold_row():
    replay.cache_clear()
    _specs_by_name.cache_clear()
    targets, local, _, run = _fresh_replayer()
    assert len(targets) == 1
    spec = targets[0]
    theorem = run(spec.name)
    nodes, depth = proof_metrics(theorem.certificate)
    objects, edges, reused = proof_identity_metrics(theorem.certificate)
    cuts = sum(type(node) is Cut for node in _walk(theorem.certificate))
    row = (
        spec.name,
        nodes,
        depth,
        objects,
        edges,
        reused,
        cuts,
        len(spec.statement),
        sha256(spec.statement.encode()).hexdigest(),
        sha256("\n".join(spec.script).encode()).hexdigest(),
        sha256("\0".join(spec.dependencies).encode()).hexdigest(),
    )
    assert check((), theorem.certificate, theorem.formula)
    assert not any(type(node) is DNE for node in _walk(theorem.certificate))
    return spec, theorem, row, local


@lru_cache(maxsize=1)
def _discovery_runs():
    first = _cold_row()
    first_row = first[2]
    del first
    gc.collect()
    second = _cold_row()
    assert second[2] == first_row
    return second


def _cut_spine(certificate: Proof, dependencies: tuple[str, ...], local):
    propositions = []
    body = certificate
    for dependency in dependencies:
        assert type(body) is Cut
        dependency_spec = (
            local[dependency] if dependency in local else _specs_by_name()[dependency]
        )
        expected = _closed_formula(dependency_spec.statement)
        assert body.proposition == expected
        propositions.append(body.proposition)
        body = body.body
    return tuple(propositions)


def _mutate_cut_at(certificate: Proof, index: int) -> Proof:
    assert type(certificate) is Cut
    if index == 0:
        zero = Zero()
        return replace(certificate, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(certificate, body=_mutate_cut_at(certificate.body, index - 1))


def test_fermat_product_balance_contract_is_deterministic_closed_expanded_pa() -> None:
    first = make_fermat_product_balance_candidate_theorems(TheoremSpec)
    second = make_fermat_product_balance_candidate_theorems(TheoremSpec)
    assert second == first
    assert tuple(item.name for item in first) == (EXPECTED_NAME,)
    assert first[0].dependencies == EXPECTED_DEPENDENCIES

    statement = first[0].statement
    formula, free_names = parse_formula_with_names(statement)
    assert not free_names
    assert _closed_formula(statement) == formula
    assert formula == parse_formula(statement)
    assert len(statement) < 8_192
    assert all(
        token not in statement
        for token in (
            "Aligned(",
            "BetaAt(",
            "Bounded(",
            "Dvd(",
            "Injective(",
            "ModEq(",
            "Pow(",
            "Prime(",
            "Product(",
            "Range(",
            "ScaleMod(",
            "%",
            "^",
            "∣",
        )
    )


def test_fermat_product_balance_helpers_are_alpha_stable_and_fail_closed() -> None:
    data = residue_reindex_data(
        "r", "s", "b", "c", "z", "d", "n", "p", "a", tag="audit_data"
    )
    witness = residue_reindex_witness("b", "c", "n", "p", "a", tag="audit")
    _, data_free = parse_formula_with_names(data)
    _, witness_free = parse_formula_with_names(witness)
    assert set(data_free) == {"r", "s", "b", "c", "z", "d", "n", "p", "a"}
    assert set(witness_free) == {"b", "c", "n", "p", "a"}

    alpha_left = residue_reindex_witness("b", "c", "n", "p", "a", tag="alpha_left")
    alpha_right = residue_reindex_witness("b", "c", "n", "p", "a", tag="alpha_right")
    assert alpha_left != alpha_right
    assert parse_formula(alpha_left) == parse_formula(alpha_right)

    with pytest.raises(ValueError, match="Peano identifier"):
        residue_reindex_witness("b", "c", "n + 1", "p", "a", tag="bad_term")
    with pytest.raises(ValueError, match="binder tag"):
        residue_reindex_data(
            "r", "s", "b", "c", "z", "d", "n", "p", "a", tag="bad tag"
        )
    with pytest.raises(ValueError, match="captures an argument"):
        residue_reindex_witness(
            "fpb_map_code_capture", "c", "n", "p", "a", tag="capture"
        )


def test_fermat_product_balance_dependency_boundary_is_exact_and_isolated() -> None:
    prerequisites, targets = _candidate_sources()
    core = _specs_by_name()
    assert all(item.name not in core for item in targets)
    assert len({item.name for item in prerequisites + targets}) == len(
        prerequisites + targets
    )
    available = set(core) | {item.name for item in prerequisites + targets}
    assert all(
        dependency in available
        for item in prerequisites + targets
        for dependency in item.dependencies
    )
    ordered = prerequisites + targets
    positions = {item.name: index for index, item in enumerate(ordered)}
    assert all(
        dependency not in positions or positions[dependency] < positions[item.name]
        for item in ordered
        for dependency in item.dependencies
    )


def test_fermat_product_balance_replays_twice_profiles_constructively() -> None:
    spec, theorem, row, local = _discovery_runs()
    (
        name,
        nodes,
        depth,
        objects,
        edges,
        reused,
        cuts,
        length,
        statement_digest,
        script_digest,
        dependencies_digest,
    ) = row
    print(
        "WMI FERMAT BALANCE RECEIPT "
        f"name={name} nodes={nodes} depth={depth} objects={objects} "
        f"edges={edges} reused={reused} cuts={cuts} "
        f"statement_length={length} statement_sha256={statement_digest} "
        f"script_sha256={script_digest} "
        f"dependencies_sha256={dependencies_digest}",
        flush=True,
    )
    assert nodes <= MAX_USE_CERTIFICATE_NODES
    assert depth <= MAX_USE_PROOF_DEPTH
    assert objects <= MAX_USE_CERTIFICATE_OBJECTS
    _cut_spine(theorem.certificate, spec.dependencies, local)


def test_fermat_product_balance_rejects_contract_and_cut_mutations() -> None:
    spec, theorem, _, _ = _discovery_runs()
    marker = "= F + p * fsp_product_mod_right_balance_result"
    assert spec.statement.count(marker) == 1
    false_contract = parse_formula(
        spec.statement.replace(
            marker,
            "= S F + p * fsp_product_mod_right_balance_result",
        )
    )
    assert not check((), theorem.certificate, false_contract)

    outer_mutation = _mutate_cut_at(theorem.certificate, 0)
    assert not check((), outer_mutation, theorem.formula)
    reindex_index = spec.dependencies.index("beta_product_permutation_invariant")
    reindex_mutation = _mutate_cut_at(theorem.certificate, reindex_index)
    assert not check((), reindex_mutation, theorem.formula)
