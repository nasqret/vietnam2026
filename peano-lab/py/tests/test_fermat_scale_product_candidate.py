"""WMI-only discovery audit for the isolated Fermat scale-product theorem."""

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
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.fermat_scale_product_candidate import (
    make_fermat_scale_product_candidate_theorems,
    product_left_mod,
    scale_mod_prefix,
    scaled_entry_mod,
    strictly_below,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAME = "beta_product_pointwise_scale_mod"
EXPECTED_DEPENDENCIES = (
    "beta_product_zero",
    "beta_product_succ_decompose",
    "pow_zero",
    "pow_successor_decompose",
    "le_succ",
    "le_refl",
    "mod_eq_refl",
    "mod_eq_mul",
    "mul_assoc",
    "mul_comm",
    "one_mul",
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


def _fresh_replayer():
    specs = make_fermat_scale_product_candidate_theorems(TheoremSpec)
    assert len(specs) == 1
    spec = specs[0]
    core = _specs_by_name()
    assert spec.name not in core

    @lru_cache(maxsize=None)
    def run() -> _Checked:
        formula = _closed_formula(spec.statement)
        target = formula
        for dependency in reversed(spec.dependencies):
            target = Imp(_closed_formula(core[dependency].statement), target)

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
            checked_dependency = replay(dependency)
            body = Cut(
                checked_dependency.formula,
                formula,
                checked_dependency.certificate,
                body,
            )

        assert check((), body, formula)
        return _Checked(formula, body)

    return spec, run


def _cold_row():
    replay.cache_clear()
    _specs_by_name.cache_clear()
    spec, run = _fresh_replayer()
    theorem = run()
    nodes, depth = proof_metrics(theorem.certificate)
    objects, edges, reused = proof_identity_metrics(theorem.certificate)
    cuts = sum(type(node) is Cut for node in _walk(theorem.certificate))
    assert check((), theorem.certificate, theorem.formula)
    assert not any(type(node) is DNE for node in _walk(theorem.certificate))
    return (
        spec,
        theorem,
        (
            spec.name,
            nodes,
            depth,
            objects,
            edges,
            reused,
            cuts,
            len(spec.statement),
            sha256(spec.statement.encode()).hexdigest(),
        ),
    )


def test_fermat_scale_contract_is_deterministic_closed_expanded_pa() -> None:
    first = make_fermat_scale_product_candidate_theorems(TheoremSpec)
    second = make_fermat_scale_product_candidate_theorems(TheoremSpec)
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
            "BetaAt(",
            "ModEq(",
            "Pow(",
            "Product(",
            "ScaleMod(",
            "%",
            "^",
            "∣",
        )
    )


def test_fermat_scale_helpers_are_hygienic_expanded_and_fail_closed() -> None:
    surfaces = {
        strictly_below("i", "l", tag="audit_lt"): {"i", "l"},
        scaled_entry_mod("m", "a", "x", "y", tag="audit_entry"): {
            "m",
            "a",
            "x",
            "y",
        },
        product_left_mod("m", "A", "P", "Q", tag="audit_product"): {
            "m",
            "A",
            "P",
            "Q",
        },
        scale_mod_prefix(
            "m",
            "a",
            "b",
            "c",
            "z",
            "d",
            "l",
            tag="audit_prefix",
        ): {"m", "a", "b", "c", "z", "d", "l"},
    }
    for surface, expected_free_names in surfaces.items():
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected_free_names

    with pytest.raises(ValueError, match="Peano identifier"):
        scaled_entry_mod("m", "a * b", "x", "y", tag="bad_term")
    with pytest.raises(ValueError, match="binder tag"):
        product_left_mod("m", "A", "P", "Q", tag="bad tag")
    with pytest.raises(ValueError, match="captures an argument"):
        scaled_entry_mod(
            "m",
            "a",
            "fsp_mod_left_capture",
            "y",
            tag="capture",
        )
    with pytest.raises(ValueError, match="captures an argument"):
        scale_mod_prefix(
            "fsp_index_capture",
            "a",
            "b",
            "c",
            "z",
            "d",
            "l",
            tag="capture",
        )


def test_fermat_scale_replays_twice_profiles_and_rejects_mutations() -> None:
    first_spec, first_theorem, first = _cold_row()
    _, _, second = _cold_row()
    assert second == first

    name, nodes, depth, objects, edges, reused, cuts, length, digest = first
    print(
        "WMI FERMAT SCALE RECEIPT "
        f"name={name} nodes={nodes} depth={depth} objects={objects} "
        f"edges={edges} reused={reused} cuts={cuts} "
        f"statement_length={length} statement_sha256={digest}",
        flush=True,
    )
    assert nodes <= MAX_USE_CERTIFICATE_NODES
    assert depth <= MAX_USE_PROOF_DEPTH
    assert objects <= MAX_USE_CERTIFICATE_OBJECTS

    marker = "= Q + m * fsp_product_mod_right_result"
    assert first_spec.statement.count(marker) == 1
    false_contract = parse_formula(
        first_spec.statement.replace(
            marker,
            "= S Q + m * fsp_product_mod_right_result",
        )
    )
    assert not check((), first_theorem.certificate, false_contract)

    assert type(first_theorem.certificate) is Cut
    zero = Zero()
    true = Eq(zero, zero)
    mutated_cut = replace(
        first_theorem.certificate,
        proposition=true,
        lemma=EqRefl(zero),
    )
    assert not check((), mutated_cut, first_theorem.formula)
