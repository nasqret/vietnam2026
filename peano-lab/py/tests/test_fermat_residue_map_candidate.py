"""WMI-only discovery audit for isolated Fermat residue-map candidates."""

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
from peano_lab.library.fermat_residue_map_candidate import (
    at_most,
    beta_at_successor_value,
    index_map,
    index_map_at,
    make_fermat_residue_map_candidate_theorems,
    not_divides,
    prime,
    scaled_successor_mod,
    strictly_below,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "beta_successor_lift_exists",
    "prime_mul_index_map_exists_up_to",
)

EXPECTED_DEPENDENCIES = {
    "beta_successor_lift_exists": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "finite_lt_succ_eq_or_lt",
        "beta_at_exists",
        "beta_at_unique",
        "beta_prefix_extend",
    ),
    "prime_mul_index_map_exists_up_to": (
        "add_eq_zero_right",
        "succ_ne_zero",
        "lt_to_le",
        "succ_le_succ",
        "prime_nonzero",
        "division_remainder_exists",
        "euclid_prime_dvd_product",
        "divisor_le_nonzero",
        "lt_not_le",
        "nonzero_is_succ",
        "le_of_succ_le_succ",
        "mul_comm",
        "remainder_decomposition_to_mod_eq",
        "finite_lt_succ_eq_or_lt",
        "beta_prefix_extend",
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
    specs = make_fermat_residue_map_candidate_theorems(TheoremSpec)
    local = {spec.name: spec for spec in specs}
    core = _specs_by_name()
    assert not set(local) & set(core)

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


def _cold_rows():
    replay.cache_clear()
    _specs_by_name.cache_clear()
    specs, run = _fresh_replayer()
    rows = []
    checked = {}
    for spec in specs:
        theorem = run(spec.name)
        checked[spec.name] = theorem
        nodes, depth = proof_metrics(theorem.certificate)
        objects, edges, reused = proof_identity_metrics(theorem.certificate)
        cuts = sum(type(node) is Cut for node in _walk(theorem.certificate))
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
        rows.append(
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
            )
        )
    return specs, checked, tuple(rows)


def test_fermat_map_contracts_are_deterministic_closed_expanded_pa() -> None:
    first = make_fermat_residue_map_candidate_theorems(TheoremSpec)
    second = make_fermat_residue_map_candidate_theorems(TheoremSpec)
    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES

    for item in first:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert _closed_formula(item.statement) == formula
        assert formula == parse_formula(item.statement)
        assert len(item.statement) < 8_192
        assert all(
            token not in item.statement
            for token in (
                "BetaAt(",
                "IndexMap(",
                "Prime(",
                "ModEq(",
                "%",
                "^",
                "∣",
            )
        )


def test_fermat_map_helpers_are_hygienic_expanded_and_fail_closed() -> None:
    surfaces = {
        strictly_below("i", "l", tag="audit_lt"): {"i", "l"},
        at_most("l", "n", tag="audit_le"): {"l", "n"},
        prime("p", tag="audit_prime"): {"p"},
        not_divides("p", "a", tag="audit_not_dvd"): {"p", "a"},
        beta_at_successor_value("z", "d", "i", "j", tag="audit_succ"): {
            "z",
            "d",
            "i",
            "j",
        },
        scaled_successor_mod("p", "a", "i", "j", tag="audit_mod"): {
            "p",
            "a",
            "i",
            "j",
        },
        index_map_at("r", "s", "i", "n", "p", "a", tag="audit_at"): {
            "r",
            "s",
            "i",
            "n",
            "p",
            "a",
        },
        index_map("r", "s", "l", "n", "p", "a", tag="audit_map"): {
            "r",
            "s",
            "l",
            "n",
            "p",
            "a",
        },
    }
    for surface, expected_free_names in surfaces.items():
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected_free_names

    with pytest.raises(ValueError, match="Peano identifier"):
        scaled_successor_mod("p", "a + 1", "i", "j", tag="bad_term")
    with pytest.raises(ValueError, match="binder tag"):
        index_map("r", "s", "l", "n", "p", "a", tag="bad tag")
    with pytest.raises(ValueError, match="captures an argument"):
        not_divides("p", "frm_factor_capture", tag="capture")


def test_fermat_map_replays_twice_profiles_and_rejects_mutations() -> None:
    first_specs, first_checked, first = _cold_rows()
    _, _, second = _cold_rows()
    assert second == first

    for row in first:
        name, nodes, depth, objects, edges, reused, cuts, length, digest = row
        print(
            "WMI FERMAT MAP RECEIPT "
            f"name={name} nodes={nodes} depth={depth} objects={objects} "
            f"edges={edges} reused={reused} cuts={cuts} "
            f"statement_length={length} statement_sha256={digest}",
            flush=True,
        )
        assert nodes <= MAX_USE_CERTIFICATE_NODES
        assert depth <= MAX_USE_PROOF_DEPTH
        assert objects <= MAX_USE_CERTIFICATE_OBJECTS

    first_statement = first_specs[0].statement
    marker = "+ (S j))"
    assert first_statement.count(marker) == 1
    false_first = parse_formula(first_statement.replace(marker, "+ (j))"))
    assert not check(
        (),
        first_checked["beta_successor_lift_exists"].certificate,
        false_first,
    )

    capstone = first_checked["prime_mul_index_map_exists_up_to"]
    assert type(capstone.certificate) is Cut
    zero = Zero()
    true = Eq(zero, zero)
    mutated_cut = replace(
        capstone.certificate,
        proposition=true,
        lemma=EqRefl(zero),
    )
    assert not check((), mutated_cut, capstone.formula)
