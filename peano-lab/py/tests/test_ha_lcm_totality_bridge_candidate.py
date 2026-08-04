"""Focused audit for RFC gcd--LCM totality rows A--I."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.kernel.terms import ParseError
from peano_lab.library import ha_lcm_totality_bridge_candidate as bridge_module
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.ha_lcm_totality_bridge_candidate import (
    make_ha_lcm_totality_bridge_candidate_theorems,
)
from peano_lab.library.ha_canonical_gcd_candidate import is_gcd
from peano_lab.library.ha_relational_lcm_candidate import (
    _expand_is_lcm,
    is_lcm,
    make_ha_relational_lcm_candidate_theorems,
)
from peano_lab.library.defined_syntax import parse_defined_formula
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


ROW_A = "balanced_bezout_one_implies_coprime"
ROW_B = "coprime_product_is_lcm"
ROW_C = "is_lcm_scale_nonzero"
ROW_D = "balanced_bezout_cancel_gcd"
ROW_E = "gcd_zero_inputs"
ROW_F = "gcd_lcm_compatible_exists"
ROW_G = "lcm_exists_relational"
ROW_H = "canonical_lcm_exists_unique"
ROW_I = "gcd_lcm_product"
EXPECTED_NAMES = (
    ROW_A,
    ROW_B,
    ROW_C,
    ROW_D,
    ROW_E,
    ROW_F,
    ROW_G,
    ROW_H,
    ROW_I,
)
EXPECTED_DEPENDENCIES = {
    ROW_A: (
        "common_divisor_divides_balanced_result",
        "divisor_one",
    ),
    ROW_B: (
        "mul_comm",
        "gauss_coprime_cancel",
        "mul_assoc",
    ),
    ROW_C: (
        "mul_assoc",
        "mul_left_cancel_nonzero",
    ),
    ROW_D: (
        "mul_left_cancel_nonzero",
        "mul_add",
        "mul_assoc",
        "mul_one",
    ),
    ROW_E: ("mul_zero_left",),
    ROW_F: (
        "gcd_balanced_bezout_exists",
        "eq_decidable",
        "gcd_zero_inputs",
        "is_lcm_zero_left",
        "balanced_bezout_cancel_gcd",
        "balanced_bezout_one_implies_coprime",
        "coprime_product_is_lcm",
        "is_lcm_scale_nonzero",
        "mul_assoc",
        "mul_comm",
    ),
    ROW_G: ("gcd_lcm_compatible_exists",),
    ROW_H: (
        "lcm_exists_relational",
        "is_lcm_unique",
    ),
    ROW_I: (
        "gcd_lcm_compatible_exists",
        "is_gcd_unique",
        "is_lcm_unique",
    ),
}
EXPECTED_ROW_A_STATEMENT = (
    "forall a b xp yp xn yn. "
    "a * xp + b * yp = 1 + (a * xn + b * yn) -> "
    "forall d. (exists u. a = d * u) -> "
    "(exists v. b = d * v) -> d = 1"
)
EXPECTED_ROW_B_RELATION = _expand_is_lcm(
    "a * b", "a", "b", tag="coprime_product"
)
EXPECTED_ROW_B_STATEMENT = (
    "forall a b. (forall d. (exists u. a = d * u) -> "
    "(exists v. b = d * v) -> d = 1) -> "
    f"({EXPECTED_ROW_B_RELATION})"
)
EXPECTED_ROW_C_STATEMENT = (
    "forall k l a b. ~(k = 0) -> "
    "((((exists hscale_left_factor_source. "
    "l = a * hscale_left_factor_source) /\\ "
    "(exists hscale_right_factor_source. "
    "l = b * hscale_right_factor_source)) /\\ "
    "forall hscale_common_source. "
    "(exists hscale_left_common_source. "
    "hscale_common_source = a * hscale_left_common_source) -> "
    "(exists hscale_right_common_source. "
    "hscale_common_source = b * hscale_right_common_source) -> "
    "exists hscale_least_factor_source. "
    "hscale_common_source = l * hscale_least_factor_source)) -> "
    "((((exists hscale_left_factor_target. "
    "(k * l) = (k * a) * hscale_left_factor_target) /\\ "
    "(exists hscale_right_factor_target. "
    "(k * l) = (k * b) * hscale_right_factor_target)) /\\ "
    "forall hscale_common_target. "
    "(exists hscale_left_common_target. "
    "hscale_common_target = (k * a) * hscale_left_common_target) -> "
    "(exists hscale_right_common_target. "
    "hscale_common_target = (k * b) * hscale_right_common_target) -> "
    "exists hscale_least_factor_target. "
    "hscale_common_target = (k * l) * hscale_least_factor_target))"
)
EXPECTED_ROW_D_STATEMENT = (
    "forall g a b A B xp yp xn yn. ~(g = 0) -> "
    "a = g * A -> b = g * B -> "
    "a * xp + b * yp = g + (a * xn + b * yn) -> "
    "A * xp + B * yp = 1 + (A * xn + B * yn)"
)
EXPECTED_ROW_E_RELATION = is_gcd("g", "a", "b", tag="zero_inputs")
EXPECTED_ROW_E_STATEMENT = (
    f"forall g a b. g = 0 -> ({EXPECTED_ROW_E_RELATION}) -> "
    "(a = 0 /\\ b = 0)"
)
EXPECTED_ROW_F_GCD = is_gcd("g", "a", "b", tag="compatible")
EXPECTED_ROW_F_LCM = is_lcm("l", "a", "b", tag="compatible")
EXPECTED_ROW_F_STATEMENT = (
    f"forall a b. exists g l. ((({EXPECTED_ROW_F_GCD}) /\\ "
    f"({EXPECTED_ROW_F_LCM})) /\\ g * l = a * b)"
)
EXPECTED_ROW_G_LCM = is_lcm("l", "a", "b", tag="existence")
EXPECTED_ROW_G_STATEMENT = (
    f"forall a b. exists l. ({EXPECTED_ROW_G_LCM})"
)
EXPECTED_ROW_H_CHOSEN_LCM = is_lcm(
    "l", "a", "b", tag="unique_chosen"
)
EXPECTED_ROW_H_COMPARED_LCM = is_lcm(
    "m", "a", "b", tag="unique_compared"
)
EXPECTED_ROW_H_STATEMENT = (
    f"forall a b. exists l. (({EXPECTED_ROW_H_CHOSEN_LCM}) /\\ "
    f"forall m. ({EXPECTED_ROW_H_COMPARED_LCM}) -> m = l)"
)
EXPECTED_ROW_I_GCD = is_gcd(
    "g", "a", "b", tag="product_gcd_assumption"
)
EXPECTED_ROW_I_LCM = is_lcm(
    "l", "a", "b", tag="product_lcm_assumption"
)
EXPECTED_ROW_I_STATEMENT = (
    f"forall g l a b. ({EXPECTED_ROW_I_GCD}) -> "
    f"({EXPECTED_ROW_I_LCM}) -> g * l = a * b"
)
EXPECTED_STATEMENTS = {
    ROW_A: EXPECTED_ROW_A_STATEMENT,
    ROW_B: EXPECTED_ROW_B_STATEMENT,
    ROW_C: EXPECTED_ROW_C_STATEMENT,
    ROW_D: EXPECTED_ROW_D_STATEMENT,
    ROW_E: EXPECTED_ROW_E_STATEMENT,
    ROW_F: EXPECTED_ROW_F_STATEMENT,
    ROW_G: EXPECTED_ROW_G_STATEMENT,
    ROW_H: EXPECTED_ROW_H_STATEMENT,
    ROW_I: EXPECTED_ROW_I_STATEMENT,
}
EXPECTED_STATEMENT_SHA256 = {
    ROW_A: "15ea38440ee20616b269602106c298e93b8e8e2260dda9cf587ebb67cc04601b",
    ROW_B: "ca92cea1f3eaa8750de6280a3e1c2ef0f805d88cd72f1a0a345b44f7f0068c37",
    ROW_C: "6ac3b09e048aaea3926dcbe3f2aec301e6c94ae106f32ec142b7d699c01db8ac",
    ROW_D: "0439333ca1d13314222adf5ab96ec61079fe8d4f738f697ae780db03c750de0e",
    ROW_E: "df92b2685a693e5be486c34fddd877b12376cbc23b30b03b6cb3019c111e7350",
    ROW_F: "04331aaa9adc6b04b5aea8dbcac34b46fed098b5233a08b88e957a37b9d7ebd5",
    ROW_G: "6269a6276e71f62a970b11a696013faf90b5e67ac498f5eb03a2f0f000f0556c",
    ROW_H: "708dbaee014b840dcde57d6b0fcd43ca4e484cdaf63db7488391beefe147cf7e",
    ROW_I: "f3b5095a728faab08137e6ee281f9da8ce6ea2697abd376170c34b1a62d47176",
}
EXPECTED_SCRIPT_REPR_SHA256 = {
    ROW_A: "aaf2226eb9aadb869c9e23a064da4a6e91630e276da08aa883f3701a333bdae0",
    ROW_B: "060b60f0303758654f1508491f2bb137daae6166222862ada5894827152dd4dd",
    ROW_C: "08b4506deb4485fe80b20fbad2ac37e90e8a09954a075c9357acada4fa7d8124",
    ROW_D: "98885e141cd030fadb6e27538d0aa6ad8ba930c2c3eef72477821dd2cbd4bb14",
    ROW_E: "e7a53151682cebf48e881759268581a67afd2c8b11469a8fe9f622b425570e1b",
    ROW_F: "e9da463aad6e6ef4a86db662cc3189f78a47dd567e895eee08a0df7b6211415c",
    ROW_G: "dd0c3d4345d7d2a4bb0a5df424260c30ed5ab3f0326f1467fa5cfcc8a5e6803b",
    ROW_H: "ca1b6c772c1c570eb974c5c4c1db8a5b5ffa9f8e2fe6151848fe8def8188c660",
    ROW_I: "58119401335d443c99e8e9114cab8c822f82254c9a787167d888a9ef3747ff6d",
}
EXPECTED_BODY_RECEIPTS = {
    ROW_A: (2, 24, 57, 35, 57, 56, 0),
    ROW_B: (3, 40, 53, 22, 53, 52, 0),
    ROW_C: (2, 60, 90, 27, 90, 89, 0),
    ROW_D: (4, 54, 99, 38, 99, 98, 0),
    ROW_E: (1, 18, 41, 21, 41, 40, 0),
    ROW_F: (10, 108, 209, 45, 209, 208, 0),
    ROW_G: (1, 10, 33, 19, 33, 32, 0),
    ROW_H: (2, 17, 40, 24, 40, 39, 0),
    ROW_I: (3, 31, 43, 21, 43, 42, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    ROW_A: (
        871,
        40,
        616,
        656,
        41,
        19,
        0,
        "6c0e03c2f140d71999c98f4c8a4b15095bc3f922a8a61332a8fb58d9108907a2",
    ),
    ROW_B: (
        4191,
        53,
        1552,
        1646,
        95,
        69,
        0,
        "c23fbcd7191b32d3d2543edecb330e42719d366fe1c6e99b471299f4314e7b17",
    ),
    ROW_C: (
        430,
        27,
        371,
        383,
        13,
        10,
        0,
        "03918aed31b503afffd000c497bd8442198d370799d046246fdf088bd83ebeee",
    ),
    ROW_D: (
        549,
        38,
        409,
        426,
        18,
        13,
        0,
        "a938ef67adb719c111c268255c32f6ad2836ab02da82e2a9113245fd25153bfd",
    ),
    ROW_E: (
        62,
        21,
        62,
        61,
        0,
        1,
        0,
        "b1e47b053b892e56877ab5a4cdd4b6f78ca399957dbf97b97fd427df8676d941",
    ),
    ROW_F: (
        9038,
        60,
        2390,
        2510,
        121,
        101,
        0,
        "dfe0e69fb172e48b6aa785c0c088ebf1a7cdf09c95ae436305d51d6224e90bc3",
    ),
    ROW_G: (
        9071,
        61,
        2423,
        2543,
        121,
        102,
        0,
        "f4e764738627255eb885d78b5cefd74663d68be022370a8036ee450b116a7220",
    ),
    ROW_H: (
        9791,
        62,
        2565,
        2691,
        127,
        111,
        0,
        "3ab4c410a0e4c6717e77d7f951d26304a35b5e9451df299167bb42cadf227747",
    ),
    ROW_I: (
        10441,
        61,
        2569,
        2696,
        128,
        112,
        0,
        "c0829496624e993a4c437aa98c32355605109e728acd03d6b5d857fcb5350d0a",
    ),
}
EXPECTED_ROW_A_PUBLIC_DEPENDENCIES = {
    "add_assoc", "add_comm", "add_eq_zero_right", "add_right_cancel",
    "add_succ_left", "common_divisor_divides_balanced_result",
    "divisor_one", "factor_difference", "mul_add", "mul_assoc",
    "mul_eq_one_components", "mul_zero_left", "one_mul", "zero_add",
}
EXPECTED_ROW_B_PUBLIC_DEPENDENCIES = {
    "add_assoc", "add_comm", "add_eq_zero_right", "add_mul",
    "add_permute_outer", "add_right_cancel", "add_succ_left",
    "balanced_bezout_euclid_step", "balanced_combination_scale_right",
    "common_divisor_divides_balanced_result", "coprime_balanced_bezout",
    "divides_linear_step", "divides_remainder", "division_remainder_exists",
    "division_remainder_succ", "factor_difference", "gauss_coprime_cancel",
    "gcd_balanced_bezout_exists", "gcd_balanced_bezout_exists_up_to",
    "is_gcd_euclid_forward", "is_gcd_zero_right", "le_eq_or_lt",
    "le_of_succ_le_succ", "le_refl", "le_zero", "mul_add", "mul_assoc",
    "mul_comm", "mul_one", "mul_succ_left", "mul_zero_left",
    "multiple_refl", "multiple_zero", "one_mul", "zero_add", "zero_or_succ",
}
EXPECTED_ROW_C_PUBLIC_DEPENDENCIES = {
    "add_assoc",
    "add_eq_zero_right",
    "add_right_cancel",
    "mul_add",
    "mul_assoc",
    "mul_eq_zero",
    "mul_left_cancel_nonzero",
    "mul_ne_zero",
    "succ_ne_zero",
}
EXPECTED_ROW_D_PUBLIC_DEPENDENCIES = {
    "add_assoc",
    "add_eq_zero_right",
    "add_right_cancel",
    "mul_add",
    "mul_assoc",
    "mul_eq_zero",
    "mul_left_cancel_nonzero",
    "mul_ne_zero",
    "mul_one",
    "succ_ne_zero",
    "zero_add",
}
EXPECTED_ROW_E_PUBLIC_DEPENDENCIES = {"mul_zero_left"}
EXPECTED_ROW_F_PUBLIC_DEPENDENCIES = {
    "add_assoc",
    "add_comm",
    "add_eq_zero_right",
    "add_mul",
    "add_permute_outer",
    "add_right_cancel",
    "add_succ_left",
    "balanced_bezout_euclid_step",
    "balanced_combination_scale_right",
    "common_divisor_divides_balanced_result",
    "coprime_balanced_bezout",
    "divides_linear_step",
    "divides_remainder",
    "division_remainder_exists",
    "division_remainder_succ",
    "divisor_one",
    "eq_decidable",
    "factor_difference",
    "gauss_coprime_cancel",
    "gcd_balanced_bezout_exists",
    "gcd_balanced_bezout_exists_up_to",
    "is_gcd_euclid_forward",
    "is_gcd_zero_right",
    "le_eq_or_lt",
    "le_of_succ_le_succ",
    "le_refl",
    "le_zero",
    "mul_add",
    "mul_assoc",
    "mul_comm",
    "mul_eq_one_components",
    "mul_eq_zero",
    "mul_left_cancel_nonzero",
    "mul_ne_zero",
    "mul_one",
    "mul_succ_left",
    "mul_zero_left",
    "multiple_refl",
    "multiple_zero",
    "one_mul",
    "succ_ne_zero",
    "zero_add",
    "zero_or_succ",
}
EXPECTED_ROW_F_LOCAL_DEPENDENCIES = {
    "balanced_bezout_cancel_gcd",
    "balanced_bezout_one_implies_coprime",
    "coprime_product_is_lcm",
    "gcd_zero_inputs",
    "is_lcm_scale_nonzero",
    "is_lcm_symm",
    "is_lcm_zero_left",
    "is_lcm_zero_right",
}
EXPECTED_ROW_G_PUBLIC_DEPENDENCIES = EXPECTED_ROW_F_PUBLIC_DEPENDENCIES
EXPECTED_ROW_G_LOCAL_DEPENDENCIES = EXPECTED_ROW_F_LOCAL_DEPENDENCIES | {
    "gcd_lcm_compatible_exists",
}
EXPECTED_ROW_H_PUBLIC_DEPENDENCIES = (
    EXPECTED_ROW_F_PUBLIC_DEPENDENCIES | {"multiple_antisymm"}
)
EXPECTED_ROW_H_LOCAL_DEPENDENCIES = EXPECTED_ROW_G_LOCAL_DEPENDENCIES | {
    "is_lcm_unique",
    "lcm_exists_relational",
}
EXPECTED_ROW_I_PUBLIC_DEPENDENCIES = (
    EXPECTED_ROW_H_PUBLIC_DEPENDENCIES | {"is_gcd_unique"}
)
EXPECTED_ROW_I_LOCAL_DEPENDENCIES = EXPECTED_ROW_F_LOCAL_DEPENDENCIES | {
    "gcd_lcm_compatible_exists",
    "is_lcm_unique",
}
EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES = {
    ROW_A: EXPECTED_ROW_A_PUBLIC_DEPENDENCIES,
    ROW_B: EXPECTED_ROW_B_PUBLIC_DEPENDENCIES,
    ROW_C: EXPECTED_ROW_C_PUBLIC_DEPENDENCIES,
    ROW_D: EXPECTED_ROW_D_PUBLIC_DEPENDENCIES,
    ROW_E: EXPECTED_ROW_E_PUBLIC_DEPENDENCIES,
    ROW_F: EXPECTED_ROW_F_PUBLIC_DEPENDENCIES,
    ROW_G: EXPECTED_ROW_G_PUBLIC_DEPENDENCIES,
    ROW_H: EXPECTED_ROW_H_PUBLIC_DEPENDENCIES,
    ROW_I: EXPECTED_ROW_I_PUBLIC_DEPENDENCIES,
}
EXPECTED_TRANSITIVE_LOCAL_DEPENDENCIES = {
    ROW_A: set(),
    ROW_B: set(),
    ROW_C: set(),
    ROW_D: set(),
    ROW_E: set(),
    ROW_F: EXPECTED_ROW_F_LOCAL_DEPENDENCIES,
    ROW_G: EXPECTED_ROW_G_LOCAL_DEPENDENCIES,
    ROW_H: EXPECTED_ROW_H_LOCAL_DEPENDENCIES,
    ROW_I: EXPECTED_ROW_I_LOCAL_DEPENDENCIES,
}
STRICT_FORBIDDEN_DEPENDENCY_MARKERS = (
    "beta",
    "classical",
    "crt",
    "dne",
)


def _candidates() -> tuple[TheoremSpec, ...]:
    return make_ha_lcm_totality_bridge_candidate_theorems(TheoremSpec)


def _relational_candidates() -> tuple[TheoremSpec, ...]:
    return make_ha_relational_lcm_candidate_theorems(TheoremSpec)


def _local_candidates() -> dict[str, TheoremSpec]:
    rows = _relational_candidates() + _candidates()
    local = {item.name: item for item in rows}
    assert len(local) == len(rows)
    return local


def _candidate_body_core() -> dict[str, TheoremSpec]:
    core = dict(_specs_by_name())
    for item in _relational_candidates():
        assert item.name not in core
        core[item.name] = item
    return core


def _candidate(name: str) -> TheoremSpec:
    return {item.name: item for item in _candidates()}[name]


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for field in fields(proof)
        if isinstance((child := getattr(proof, field.name)), Proof)
    )


def _walk_unique(proof: Proof) -> tuple[Proof, ...]:
    pending = [proof]
    seen: set[int] = set()
    result: list[Proof] = []
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        result.append(node)
        pending.extend(_proof_children(node))
    return tuple(result)


def _proof_dag_digest(proof: Proof) -> str:
    digests: dict[int, str] = {}
    pending: list[tuple[Proof, bool]] = [(proof, False)]
    while pending:
        node, expanded = pending.pop()
        identity = id(node)
        if identity in digests:
            continue
        children = _proof_children(node)
        if not expanded:
            pending.append((node, True))
            pending.extend(
                (child, False)
                for child in children
                if id(child) not in digests
            )
            continue
        payload = [type(node).__name__]
        for field in fields(node):
            value = getattr(node, field.name)
            payload.append(
                digests[id(value)] if isinstance(value, Proof) else repr(value)
            )
        digests[identity] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def _cold_closed_receipt(
    name: str,
) -> tuple[int, int, int, int, int, int, int, str]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    public = _specs_by_name()
    local = _local_candidates()

    @lru_cache(maxsize=None)
    def close(theorem_name: str) -> tuple[object, Proof]:
        if theorem_name in public:
            checked = replay(theorem_name)
            return checked.formula, checked.certificate

        item = local[theorem_name]
        formula = _closed_formula(item.statement)
        target = formula
        for dependency in reversed(item.dependencies):
            dependency_spec = local.get(dependency) or public[dependency]
            target = Imp(_closed_formula(dependency_spec.statement), target)

        state = start(target)
        for dependency in item.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in item.script:
            tactic, arguments = _primitive(command)
            state = apply_tactic(state, tactic, arguments)
        body = checked_final(state, target)
        for _ in item.dependencies:
            assert type(body) is ImpIntro
            body = body.body
        for dependency in reversed(item.dependencies):
            dependency_formula, dependency_proof = close(dependency)
            body = Cut(
                dependency_formula,
                formula,
                dependency_proof,
                body,
            )

        assert check((), body, formula)
        return formula, body

    formula, body = close(name)

    assert check((), body, formula)
    unique_nodes = _walk_unique(body)
    nodes, depth = proof_metrics(body)
    objects, edges, reused = proof_identity_metrics(body)
    assert objects == len(unique_nodes)
    return (
        nodes,
        depth,
        objects,
        edges,
        reused,
        sum(type(node) is Cut for node in unique_nodes),
        sum(type(node) is DNE for node in unique_nodes),
        _proof_dag_digest(body),
    )


def _dependency_boundaries(name: str) -> tuple[set[str], set[str]]:
    public = _specs_by_name()
    local = _local_candidates()
    pending = list(_candidate(name).dependencies)
    seen: set[str] = set()
    local_seen: set[str] = set()
    public_seen: set[str] = set()
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        if name in local:
            local_seen.add(name)
            pending.extend(local[name].dependencies)
        else:
            assert name in public
            public_seen.add(name)
            pending.extend(public[name].dependencies)
    return local_seen, public_seen


def _dependency_closure(name: str) -> set[str]:
    return _dependency_boundaries(name)[1]


def test_lcm_totality_bridge_factory_is_exact_and_registry_isolated() -> None:
    first = _candidates()
    second = make_ha_lcm_totality_bridge_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.statement for item in first} == EXPECTED_STATEMENTS
    assert {item.name: item.dependencies for item in first} == (
        EXPECTED_DEPENDENCIES
    )
    assert {
        item.name: sha256(item.statement.encode()).hexdigest()
        for item in first
    } == EXPECTED_STATEMENT_SHA256
    assert {
        item.name: sha256(repr(item.script).encode()).hexdigest()
        for item in first
    } == EXPECTED_SCRIPT_REPR_SHA256
    assert len(_candidate(ROW_F).statement) == 1015
    for item in first:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)

    public = _specs_by_name()
    assert all(item.name not in public for item in first)
    registry_source = Path(theorem_registry.__file__).read_text(encoding="utf-8")
    assert "ha_lcm_totality_bridge_candidate" not in registry_source
    assert all(f'"{item.name}"' not in registry_source for item in first)


def test_lcm_totality_bridge_defined_surfaces_and_term_wrappers_are_exact() -> None:
    defined_row_a = parse_defined_formula(
        "forall a b. BalancedBezout(1,a,b) -> Coprime(a,b)"
    )
    expanded_packaging = _closed_formula(
        "forall a b. (exists xp yp xn yn. "
        "a * xp + b * yp = 1 + (a * xn + b * yn)) -> "
        "forall d. (exists u. a = d * u) -> "
        "(exists v. b = d * v) -> d = 1"
    )
    assert defined_row_a == expanded_packaging

    row_a = _closed_formula(_candidate(ROW_A).statement)
    forward_target = Imp(row_a, defined_row_a)
    forward = start(forward_target)
    for tactic, arguments in (
        ("intro", "hrow"), ("intro", "a"), ("intro", "b"),
        ("intro", "hbalanced"), ("cases", "hbalanced"),
        ("cases", "hbalanced_witness"),
        ("cases", "hbalanced_witness_witness"),
        ("cases", "hbalanced_witness_witness_witness"),
        ("specialize", "hrow a"), ("specialize", "hrow b"),
        ("specialize", "hrow x"), ("specialize", "hrow x1"),
        ("specialize", "hrow x2"), ("specialize", "hrow x3"),
        ("apply", "hrow"),
        ("exact", "hbalanced_witness_witness_witness_witness"),
    ):
        forward = apply_tactic(forward, tactic, arguments)
    forward_certificate = checked_final(forward, forward_target)
    assert check((), forward_certificate, forward_target)

    reverse_target = Imp(defined_row_a, row_a)
    reverse = start(reverse_target)
    for tactic, arguments in (
        ("intro", "hdefined"), ("intro", "a"), ("intro", "b"),
        ("intro", "xp"), ("intro", "yp"), ("intro", "xn"),
        ("intro", "yn"), ("intro", "hbez"),
        ("specialize", "hdefined a"), ("specialize", "hdefined b"),
        ("apply", "hdefined"), ("exists", "xp"), ("exists", "yp"),
        ("exists", "xn"), ("exists", "yn"), ("exact", "hbez"),
    ):
        reverse = apply_tactic(reverse, tactic, arguments)
    reverse_certificate = checked_final(reverse, reverse_target)
    assert check((), reverse_certificate, reverse_target)

    generated = bridge_module._product_is_lcm(
        "a", "b", tag="wrapper_audit"
    )
    assert generated == _expand_is_lcm(
        "a * b", "a", "b", tag="wrapper_audit"
    )
    short_rfc = (
        "(((exists x. a * b = a * x) /\\ "
        "(exists y. a * b = b * y)) /\\ forall c. "
        "(exists u. c = a * u) -> (exists v. c = b * v) -> "
        "exists w. c = (a * b) * w)"
    )
    assert _closed_formula(f"forall a b. ({generated})") == _closed_formula(
        f"forall a b. ({short_rfc})"
    )

    scale_variables = ("k", "l", "a", "b")
    generated_scale_source = bridge_module._term_is_lcm(
        "l", "a", "b", tag="source", variables=scale_variables
    )
    generated_scale_target = bridge_module._term_is_lcm(
        "k * l",
        "k * a",
        "k * b",
        tag="target",
        variables=scale_variables,
    )
    short_scale_target = (
        "(((exists x. (k * l) = (k * a) * x) /\\ "
        "(exists y. (k * l) = (k * b) * y)) /\\ forall c. "
        "(exists u. c = (k * a) * u) -> "
        "(exists v. c = (k * b) * v) -> "
        "exists w. c = (k * l) * w)"
    )
    assert _closed_formula(
        f"forall k l a b. ({generated_scale_target})"
    ) == _closed_formula(f"forall k l a b. ({short_scale_target})")
    assert _candidate(ROW_C).statement == (
        f"forall k l a b. ~(k = 0) -> ({generated_scale_source}) -> "
        f"({generated_scale_target})"
    )

    defined_gcd = parse_defined_formula("forall g a b. IsGCD(g,a,b)")
    expanded_gcd = _closed_formula(
        f"forall g a b. ({EXPECTED_ROW_E_RELATION})"
    )
    assert expanded_gcd == defined_gcd
    assert EXPECTED_ROW_E_RELATION == is_gcd(
        "g", "a", "b", tag="zero_inputs"
    )
    assert "IsGCD(" not in _candidate(ROW_E).statement
    assert _candidate(ROW_D).statement == EXPECTED_ROW_D_STATEMENT
    assert _candidate(ROW_G).statement == EXPECTED_ROW_G_STATEMENT
    assert _candidate(ROW_H).statement == EXPECTED_ROW_H_STATEMENT
    assert _candidate(ROW_I).statement == EXPECTED_ROW_I_STATEMENT
    assert EXPECTED_ROW_G_LCM == is_lcm(
        "l", "a", "b", tag="existence"
    )
    assert EXPECTED_ROW_H_CHOSEN_LCM == is_lcm(
        "l", "a", "b", tag="unique_chosen"
    )
    assert EXPECTED_ROW_H_COMPARED_LCM == is_lcm(
        "m", "a", "b", tag="unique_compared"
    )
    assert EXPECTED_ROW_I_GCD == is_gcd(
        "g", "a", "b", tag="product_gcd_assumption"
    )
    assert EXPECTED_ROW_I_LCM == is_lcm(
        "l", "a", "b", tag="product_lcm_assumption"
    )
    for row in (ROW_G, ROW_H, ROW_I):
        statement = _candidate(row).statement
        assert "IsGCD(" not in statement
        assert "IsLCM(" not in statement
        assert "~(" not in statement

    for bad in ("0", "a * b", "a + b", "forall", "a) -> false"):
        with pytest.raises(ValueError):
            bridge_module._product_is_lcm(bad, "b", tag="bad")
        with pytest.raises(ValueError):
            bridge_module._product_is_lcm("a", bad, tag="bad")
    with pytest.raises(ValueError):
        bridge_module._product_is_lcm("a", "b", tag="bad-tag")

    for bad_term in ("unknown", "k +", "k) -> false", "forall"):
        with pytest.raises((ParseError, ValueError)):
            bridge_module._term_is_lcm(
                bad_term,
                "k * a",
                "k * b",
                tag="unsafe",
                variables=scale_variables,
            )
    with pytest.raises(ValueError, match="distinct identifiers"):
        bridge_module._term_is_lcm(
            "k", "a", "b", tag="duplicate", variables=("k", "a", "a")
        )
    with pytest.raises(ValueError, match="captures an argument"):
        bridge_module._term_is_lcm(
            "hscale_left_factor_capture",
            "a",
            "b",
            tag="capture",
            variables=("hscale_left_factor_capture", "a", "b"),
        )


def test_lcm_totality_bridge_body_receipt_is_exact() -> None:
    receipts = replay_candidate_bodies(
        _candidates(), core=_candidate_body_core()
    )
    assert {
        receipt.name: (
            receipt.dependency_count,
            receipt.command_count,
            receipt.proof_nodes,
            receipt.proof_depth,
            receipt.proof_objects,
            receipt.proof_edges,
            receipt.reused_objects,
        )
        for receipt in receipts
    } == EXPECTED_BODY_RECEIPTS


def test_lcm_totality_bridge_two_cold_closures_are_identical() -> None:
    first = {name: _cold_closed_receipt(name) for name in EXPECTED_NAMES}
    second = {name: _cold_closed_receipt(name) for name in EXPECTED_NAMES}
    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == EXPECTED_CLOSED_RECEIPTS
    assert first == second
    assert all(receipt[-2] == 0 for receipt in first.values())


def test_lcm_totality_bridge_dependency_boundaries_are_exact() -> None:
    closures = {name: _dependency_closure(name) for name in EXPECTED_NAMES}
    assert closures == EXPECTED_TRANSITIVE_PUBLIC_DEPENDENCIES
    local_boundaries = {
        name: _dependency_boundaries(name)[0] for name in EXPECTED_NAMES
    }
    assert local_boundaries == EXPECTED_TRANSITIVE_LOCAL_DEPENDENCIES
    for closure in closures.values():
        assert not {
            name
            for name in closure
            if any(
                marker in name.lower()
                for marker in STRICT_FORBIDDEN_DEPENDENCY_MARKERS
            )
        }
    assert "division_remainder_exists" not in closures[ROW_A]
    assert "gcd_balanced_bezout_exists" not in closures[ROW_A]
    assert "division_remainder_exists" in closures[ROW_B]
    assert "gcd_balanced_bezout_exists" in closures[ROW_B]
    assert "division_remainder_exists" not in closures[ROW_C]
    assert "gcd_balanced_bezout_exists" not in closures[ROW_C]
    assert "mul_comm" not in closures[ROW_C]
    assert "division_remainder_exists" not in closures[ROW_D]
    assert "gcd_balanced_bezout_exists" not in closures[ROW_D]
    assert closures[ROW_E] == {"mul_zero_left"}
    assert "division_remainder_exists" in closures[ROW_F]
    assert "gcd_balanced_bezout_exists" in closures[ROW_F]
    assert "eq_decidable" in closures[ROW_F]
    assert closures[ROW_G] == closures[ROW_F]
    assert closures[ROW_H] == closures[ROW_F] | {"multiple_antisymm"}
    assert closures[ROW_I] == closures[ROW_H] | {"is_gcd_unique"}
    assert "lcm_exists_relational" in local_boundaries[ROW_H]
    assert "is_lcm_unique" in local_boundaries[ROW_H]
    assert "is_gcd_unique" not in local_boundaries[ROW_I]


def test_lcm_totality_bridge_rejects_row_a_mutations() -> None:
    item = _candidate(ROW_A)
    assert item.statement.endswith("d = 1")
    conclusion_mutation = replace(
        item,
        statement=f"{item.statement[:-len('d = 1')]}d = 0",
    )
    assert item.statement.count("= 1 +") == 1
    result_mutation = replace(
        item,
        statement=item.statement.replace("= 1 +", "= 0 +", 1),
    )
    for mutation in (conclusion_mutation, result_mutation):
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((mutation,))


def test_lcm_totality_bridge_rejects_row_b_leastness_mutation() -> None:
    item = _candidate(ROW_B)
    original = (
        "hlcm_common_coprime_product = a * b * "
        "hlcm_least_factor_coprime_product"
    )
    mutation_text = (
        "hlcm_common_coprime_product = S (a * b) * "
        "hlcm_least_factor_coprime_product"
    )
    assert item.statement.count(original) == 1
    mutation = replace(item, statement=item.statement.replace(original, mutation_text))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutation,))


def test_lcm_totality_bridge_rejects_row_c_mutations() -> None:
    item = _candidate(ROW_C)
    leastness = (
        "hscale_common_target = (k * l) * hscale_least_factor_target"
    )
    false_leastness = (
        "hscale_common_target = S (k * l) * hscale_least_factor_target"
    )
    assert item.statement.count(leastness) == 1
    leastness_mutation = replace(
        item,
        statement=item.statement.replace(leastness, false_leastness),
    )
    premise_mutation = replace(
        item,
        statement=item.statement.replace("~(k = 0)", "k = 0", 1),
    )
    for mutation in (leastness_mutation, premise_mutation):
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((mutation,))


def test_lcm_totality_bridge_rejects_row_d_mutations() -> None:
    item = _candidate(ROW_D)
    result = "= 1 + (A * xn + B * yn)"
    false_result = "= 0 + (A * xn + B * yn)"
    assert item.statement.count(result) == 1
    result_mutation = replace(
        item,
        statement=item.statement.replace(result, false_result),
    )
    premise_mutation = replace(
        item,
        statement=item.statement.replace("~(g = 0)", "g = 0", 1),
    )
    for mutation in (result_mutation, premise_mutation):
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((mutation,))


def test_lcm_totality_bridge_rejects_row_e_mutations() -> None:
    item = _candidate(ROW_E)
    conclusion = "(a = 0 /\\ b = 0)"
    false_conclusion = "(a = 0 /\\ S b = 0)"
    assert item.statement.count(conclusion) == 1
    conclusion_mutation = replace(
        item,
        statement=item.statement.replace(conclusion, false_conclusion),
    )
    premise_mutation = replace(
        item,
        statement=item.statement.replace("g = 0 ->", "g = 1 ->", 1),
    )
    for mutation in (conclusion_mutation, premise_mutation):
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((mutation,))


def test_lcm_totality_bridge_rejects_row_f_branch_mutations() -> None:
    item = _candidate(ROW_F)

    zero_command = "specialize is_lcm_zero_left 0"
    assert item.script.count(zero_command) == 1
    zero_branch_mutation = replace(
        item,
        script=tuple(
            "specialize is_lcm_zero_left 1"
            if command == zero_command
            else command
            for command in item.script
        ),
    )

    nonzero_command = "apply mul_comm"
    assert item.script.count(nonzero_command) == 1
    nonzero_branch_mutation = replace(
        item,
        script=tuple(
            "refl" if command == nonzero_command else command
            for command in item.script
        ),
    )

    for mutation in (zero_branch_mutation, nonzero_branch_mutation):
        mutated_candidates = tuple(
            mutation if candidate.name == ROW_F else candidate
            for candidate in _candidates()
        )
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies(
                mutated_candidates,
                core=_candidate_body_core(),
            )


def test_lcm_totality_bridge_rejects_row_g_projection_mutation() -> None:
    item = _candidate(ROW_G)
    leastness = (
        "hlcm_common_existence = l * hlcm_least_factor_existence"
    )
    false_leastness = (
        "hlcm_common_existence = S l * hlcm_least_factor_existence"
    )
    assert item.statement.count(leastness) == 1
    mutation = replace(
        item,
        statement=item.statement.replace(leastness, false_leastness),
    )
    mutated_candidates = tuple(
        mutation if candidate.name == ROW_G else candidate
        for candidate in _candidates()
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            mutated_candidates,
            core=_candidate_body_core(),
        )


def test_lcm_totality_bridge_rejects_row_h_uniqueness_mutation() -> None:
    item = _candidate(ROW_H)
    assert item.statement.count("m = l") == 1
    mutation = replace(
        item,
        statement=item.statement.replace("m = l", "S m = l"),
    )
    mutated_candidates = tuple(
        mutation if candidate.name == ROW_H else candidate
        for candidate in _candidates()
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            mutated_candidates,
            core=_candidate_body_core(),
        )


def test_lcm_totality_bridge_rejects_row_i_product_mutation() -> None:
    item = _candidate(ROW_I)
    conclusion = "g * l = a * b"
    false_conclusion = "g * l = S (a * b)"
    assert item.statement.count(conclusion) == 1
    mutation = replace(
        item,
        statement=item.statement.replace(conclusion, false_conclusion),
    )
    mutated_candidates = tuple(
        mutation if candidate.name == ROW_I else candidate
        for candidate in _candidates()
    )
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            mutated_candidates,
            core=_candidate_body_core(),
        )
