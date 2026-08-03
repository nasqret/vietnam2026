"""WMI-only discovery audit for the isolated Fermat residue reindexing."""

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
from peano_lab.library.fermat_residue_map_candidate import (
    make_fermat_residue_map_candidate_theorems,
)
from peano_lab.library.fermat_residue_product_candidate import (
    make_fermat_residue_product_candidate_theorems,
)
from peano_lab.library.fermat_residue_reindex_candidate import (
    bounded_entry_at,
    make_fermat_residue_reindex_candidate_theorems,
    scaled_indices_mod,
    strictly_below,
    successor_below,
    successor_indices_mod,
    successor_lift_prefix,
    successor_to_scaled_mod,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "fermat_index_map_bounded",
    "prime_mul_index_map_injective",
    "beta_successor_range_reindex_aligned",
    "beta_successor_range_scale_mod",
    "prime_mul_residue_reindex_exists",
)

EXPECTED_DEPENDENCIES = {
    "fermat_index_map_bounded": (),
    "prime_mul_index_map_injective": (
        "beta_at_unique",
        "succ_le_succ",
        "mod_eq_symm",
        "mod_eq_trans",
        "prime_mod_cancel",
        "mod_eq_bounded_unique",
        "succ_injective",
    ),
    "beta_successor_range_reindex_aligned": (
        "beta_at_unique",
        "beta_range_one_entry_eq_succ",
    ),
    "beta_successor_range_scale_mod": (
        "beta_range_one_entry_eq_succ",
        "beta_at_unique",
    ),
    "prime_mul_residue_reindex_exists": (
        "le_refl",
        "prime_mul_index_map_exists_up_to",
        "beta_successor_lift_exists",
        "fermat_index_map_bounded",
        "prime_mul_index_map_injective",
        "beta_successor_range_reindex_aligned",
        "beta_successor_range_scale_mod",
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


def _candidate_sources() -> tuple[tuple[TheoremSpec, ...], tuple[TheoremSpec, ...]]:
    prerequisites = (
        make_fermat_residue_product_candidate_theorems(TheoremSpec)
        + make_fermat_residue_map_candidate_theorems(TheoremSpec)
    )
    targets = make_fermat_residue_reindex_candidate_theorems(TheoremSpec)
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


def _cold_rows():
    replay.cache_clear()
    _specs_by_name.cache_clear()
    targets, _, _, run = _fresh_replayer()
    checked: dict[str, _Checked] = {}
    rows = []
    for spec in targets:
        theorem = run(spec.name)
        checked[spec.name] = theorem
        nodes, depth = proof_metrics(theorem.certificate)
        objects, edges, reused = proof_identity_metrics(theorem.certificate)
        cuts = sum(type(node) is Cut for node in _walk(theorem.certificate))
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
                sha256("\n".join(spec.script).encode()).hexdigest(),
                sha256("\0".join(spec.dependencies).encode()).hexdigest(),
            )
        )
        assert check((), theorem.certificate, theorem.formula)
        assert not any(type(node) is DNE for node in _walk(theorem.certificate))
    return targets, checked, tuple(rows)


@lru_cache(maxsize=1)
def _discovery_runs():
    first = _cold_rows()
    first_rows = first[2]
    del first
    gc.collect()
    second = _cold_rows()
    assert second[2] == first_rows
    return second


def _mutate_cut_at(certificate: Proof, index: int) -> Proof:
    assert type(certificate) is Cut
    if index == 0:
        zero = Zero()
        return replace(certificate, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(certificate, body=_mutate_cut_at(certificate.body, index - 1))


def test_fermat_residue_reindex_contracts_are_deterministic_closed_expanded_pa() -> None:
    first = make_fermat_residue_reindex_candidate_theorems(TheoremSpec)
    second = make_fermat_residue_reindex_candidate_theorems(TheoremSpec)
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
                "Aligned(",
                "BetaAt(",
                "Bounded(",
                "Dvd(",
                "IndexMap(",
                "Injective(",
                "ModEq(",
                "Prime(",
                "Range(",
                "ScaleMod(",
                "%",
                "^",
                "∣",
            )
        )


def test_fermat_residue_reindex_helpers_are_exact_alpha_stable_and_fail_closed() -> None:
    assert strictly_below("i", "n", tag="exact") == (
        "exists frr_gap_exact. frr_gap_exact + S i = n"
    )
    assert successor_below("i", "p", tag="exact") == (
        "exists frr_successor_bound_exact. "
        "frr_successor_bound_exact + S (S i) = p"
    )
    assert scaled_indices_mod("p", "a", "i", "k", tag="exact") == (
        "exists frr_scaled_left_exact frr_scaled_right_exact. "
        "a * S i + p * frr_scaled_left_exact = "
        "a * S k + p * frr_scaled_right_exact"
    )
    assert successor_to_scaled_mod("p", "w", "a", "k", tag="exact") == (
        "exists frr_reverse_left_exact frr_reverse_right_exact. "
        "S w + p * frr_reverse_left_exact = "
        "a * S k + p * frr_reverse_right_exact"
    )
    assert successor_indices_mod("p", "i", "k", tag="exact") == (
        "exists frr_cancel_left_exact frr_cancel_right_exact. "
        "S i + p * frr_cancel_left_exact = "
        "S k + p * frr_cancel_right_exact"
    )

    surfaces = {
        bounded_entry_at("r", "s", "i", "n", tag="audit_entry"): {
            "r",
            "s",
            "i",
            "n",
        },
        successor_lift_prefix(
            "r", "s", "z", "d", "n", tag="audit_lift"
        ): {"r", "s", "z", "d", "n"},
        scaled_indices_mod("p", "a", "i", "k", tag="audit_scaled"): {
            "p",
            "a",
            "i",
            "k",
        },
        successor_to_scaled_mod("p", "w", "a", "k", tag="audit_reverse"): {
            "p",
            "w",
            "a",
            "k",
        },
        successor_indices_mod("p", "i", "k", tag="audit_cancel"): {
            "p",
            "i",
            "k",
        },
        successor_below("i", "p", tag="audit_bound"): {"i", "p"},
    }
    for surface, expected_free_names in surfaces.items():
        _, free_names = parse_formula_with_names(surface)
        assert set(free_names) == expected_free_names

    alpha_left = successor_lift_prefix("r", "s", "z", "d", "n", tag="alpha_left")
    alpha_right = successor_lift_prefix("r", "s", "z", "d", "n", tag="alpha_right")
    assert alpha_left != alpha_right
    assert parse_formula(alpha_left) == parse_formula(alpha_right)
    repeated_codes = successor_lift_prefix(
        "r", "s", "r", "s", "n", tag="repeated_codes"
    )
    _, repeated_free = parse_formula_with_names(repeated_codes)
    assert set(repeated_free) == {"r", "s", "n"}

    with pytest.raises(ValueError, match="Peano identifier"):
        successor_below("i + 1", "p", tag="bad_term")
    with pytest.raises(ValueError, match="binder tag"):
        scaled_indices_mod("p", "a", "i", "k", tag="bad tag")
    with pytest.raises(ValueError, match="captures an argument"):
        successor_lift_prefix(
            "frr_index_capture", "s", "z", "d", "n", tag="capture"
        )
    with pytest.raises(ValueError, match="captures an argument"):
        bounded_entry_at(
            "frr_value_capture", "s", "i", "n", tag="capture"
        )


def test_fermat_residue_reindex_dependency_boundary_is_exact_and_isolated() -> None:
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


def test_fermat_residue_reindex_replays_twice_profiles_constructively() -> None:
    first_specs, _, first = _discovery_runs()

    for row in first:
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
            "WMI FERMAT REINDEX RECEIPT "
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

    assert tuple(item.name for item in first_specs) == EXPECTED_NAMES


def test_fermat_residue_reindex_rejects_contract_and_cut_mutations() -> None:
    specs, checked, _ = _discovery_runs()
    by_name = {item.name: item for item in specs}

    injective = by_name["prime_mul_index_map_injective"]
    marker = "fp_i_injective_result = fp_j_injective_result"
    assert injective.statement.count(marker) == 1
    false_injective = parse_formula(
        injective.statement.replace(
            marker,
            "fp_i_injective_result = S fp_j_injective_result",
        )
    )
    assert not check(
        (),
        checked["prime_mul_index_map_injective"].certificate,
        false_injective,
    )

    capstone_spec = by_name["prime_mul_residue_reindex_exists"]
    capstone = checked["prime_mul_residue_reindex_exists"]
    assert type(capstone.certificate) is Cut
    capstone_marker = (
        "fp_i_package_result_injective = fp_j_package_result_injective"
    )
    assert capstone_spec.statement.count(capstone_marker) == 1
    false_capstone = parse_formula(
        capstone_spec.statement.replace(
            capstone_marker,
            "fp_i_package_result_injective = S fp_j_package_result_injective",
        )
    )
    assert not check((), capstone.certificate, false_capstone)

    prerequisites, targets = _candidate_sources()
    source = {item.name: item for item in prerequisites + targets}
    body = capstone.certificate
    for dependency in capstone_spec.dependencies:
        assert type(body) is Cut
        dependency_spec = source.get(dependency) or _specs_by_name()[dependency]
        assert body.proposition == _closed_formula(dependency_spec.statement)
        body = body.body

    local_edge = capstone_spec.dependencies.index("prime_mul_index_map_injective")
    mutated_local_cut = _mutate_cut_at(capstone.certificate, local_edge)
    assert not check((), mutated_local_cut, capstone.formula)
