"""Focused audit for the all-modulus canonical generalized-CRT boundary."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from itertools import product
from math import gcd, lcm

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_generalized_crt_canonical_boundary_candidate import (
    below,
    make_ha_generalized_crt_canonical_boundary_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_classification_candidate import (
    make_ha_generalized_crt_classification_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_congruence_candidate import (
    make_ha_generalized_crt_congruence_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_sufficiency_candidate import (
    make_ha_generalized_crt_sufficiency_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_zero_boundary_candidate import (
    make_ha_generalized_crt_zero_boundary_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "crt_solution_unique_lcm_zero",
    "crt_solution_canonical_remainder_nonzero",
    "generalized_binary_crt_canonical_boundary",
)
ADMITTED_NAMES = EXPECTED_NAMES
EXPECTED_DEPENDENCIES = {
    "crt_solution_unique_lcm_zero": (
        "crt_solution_class_iff_lcm",
        "mod_eq_zero_iff_eq",
    ),
    "crt_solution_canonical_remainder_nonzero": (
        "division_remainder_exists",
        "mul_comm",
        "remainder_decomposition_to_mod_eq",
        "mod_eq_symm",
        "crt_solution_class_iff_lcm",
        "mod_eq_bounded_unique",
    ),
    "generalized_binary_crt_canonical_boundary": (
        "eq_decidable",
        "generalized_binary_crt_sufficient",
        "crt_solution_unique_lcm_zero",
        "crt_solution_canonical_remainder_nonzero",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "crt_solution_unique_lcm_zero":
        "d84b07e3b9274fcf8914ad69c75ea56fb64a96268ccc701a5da8aadca9ecc199",
    "crt_solution_canonical_remainder_nonzero":
        "02710fb2f9af9110f8267dd1feef6815040bc92e81337ff3c347282121904056",
    "generalized_binary_crt_canonical_boundary":
        "fc76bb161c4986e700253da58219aa9a37ac39e2f3ebebc64c966c73c696ef75",
}
EXPECTED_SCRIPT_REPR_SHA256 = {
    "crt_solution_unique_lcm_zero":
        "20ed38cb1935d72a89d802ace5d56cf5749e01e4910a91283e9db626f5e7cdca",
    "crt_solution_canonical_remainder_nonzero":
        "c9e38af3c4809e6389dbc65cf0ef6e66736457d229fbf7fd21e1169b52b6541a",
    "generalized_binary_crt_canonical_boundary":
        "ce5d3a9752368b8b36d98b8e9ed704260053c94a9bdba2ad228483c90acf6fb0",
}
EXPECTED_BODY_RECEIPTS = {
    "crt_solution_unique_lcm_zero": (2, 33, 37, 28, 37, 36, 0),
    "crt_solution_canonical_remainder_nonzero": (6, 83, 141, 39, 141, 140, 0),
    "generalized_binary_crt_canonical_boundary": (4, 66, 76, 33, 76, 75, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "crt_solution_unique_lcm_zero": (
        2_300, 40, 1_126, 1_176, 51, 43, 0,
        "2afc46ac88613c95400eb37f80b1fbda095b18a7f6a774255426b48c35aed9ac",
    ),
    "crt_solution_canonical_remainder_nonzero": (
        4_086, 65, 1_668, 1_746, 79, 64, 0,
        "091e8f2b1ba7e4665b87071fcd924ea1098880d65a97bcdd264ed544e33ff0e4",
    ),
    "generalized_binary_crt_canonical_boundary": (
        17_750, 80, 4_239, 4_426, 188, 193, 0,
        "c704a17f6feed83142b160bbeafcc14764d5ae6590999187eed5455c3ad03bd7",
    ),
}


@lru_cache(maxsize=1)
def _congruence_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_congruence_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _sufficiency_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_sufficiency_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _zero_boundary_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_zero_boundary_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _classification_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_classification_candidate_theorems(
        TheoremSpec
    )


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_canonical_boundary_candidate_theorems(
        TheoremSpec
    )


def _assert_public_admission() -> None:
    reviewed = {item.name: item for item in _candidate_specs()}
    public = _specs_by_name()
    admitted = tuple(
        item
        for item in theorem_registry.HA_NUMBER_THEORY_M5_GENERALIZED_CRT_THEOREMS
        if item.name in ADMITTED_NAMES
    )

    assert admitted == tuple(reviewed[name] for name in ADMITTED_NAMES)
    assert all(public[name] == reviewed[name] for name in ADMITTED_NAMES)


def _local_specs() -> dict[str, TheoremSpec]:
    return {
        item.name: item
        for item in (
            *_congruence_specs(),
            *_sufficiency_specs(),
            *_zero_boundary_specs(),
            *_classification_specs(),
            *_candidate_specs(),
        )
    }


def _available_specs() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local_specs()


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk(proof: Proof):
    yield proof
    for child in _proof_children(proof):
        yield from _walk(child)


def _walk_unique(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        yield node
        pending.extend(_proof_children(node))


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
        for item in fields(node):
            value = getattr(node, item.name)
            payload.append(
                digests[id(value)] if isinstance(value, Proof) else repr(value)
            )
        digests[identity] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def _curried_target(item: TheoremSpec, statement: str | None = None):
    available = _available_specs()
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency_name in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency_name].statement), target)
    return target


def _body_certificate(item: TheoremSpec):
    target = _curried_target(item)
    state = start(target)
    for dependency_name in item.dependencies:
        state = apply_tactic(state, "intro", dependency_name)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _cold_closed_receipts():
    replay.cache_clear()
    _specs_by_name.cache_clear()
    local = _local_specs()
    public = _specs_by_name()

    @lru_cache(maxsize=None)
    def close(name: str):
        if name in public:
            checked = replay(name)
            return checked.formula, checked.certificate

        item = local[name]
        formula = _closed_formula(item.statement)
        dependency_specs = tuple(
            local.get(dependency) or public[dependency]
            for dependency in item.dependencies
        )
        target = formula
        for dependency_spec in reversed(dependency_specs):
            target = Imp(_closed_formula(dependency_spec.statement), target)

        state = start(target)
        for dependency in item.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in item.script:
            tactic, arguments = _primitive(command)
            state = apply_tactic(state, tactic, arguments)
        body = checked_final(state, target)
        for _dependency in item.dependencies:
            assert type(body) is ImpIntro
            body = body.body
        for dependency in reversed(item.dependencies):
            dependency_formula, dependency_certificate = close(dependency)
            body = Cut(
                dependency_formula,
                formula,
                dependency_certificate,
                body,
            )
        assert check((), body, formula)
        return formula, body

    receipts = {}
    for item in _candidate_specs():
        formula, certificate = close(item.name)
        assert formula == _closed_formula(item.statement)
        assert check((), certificate, formula)
        unique_nodes = tuple(_walk_unique(certificate))
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        receipts[item.name] = (
            nodes,
            depth,
            objects,
            edges,
            reused,
            sum(type(node) is Cut for node in unique_nodes),
            sum(type(node) is DNE for node in unique_nodes),
            _proof_dag_digest(certificate),
        )
    return receipts


def test_canonical_boundary_factory_is_exact_ordered_and_publicly_admitted() -> None:
    first = _candidate_specs()
    second = make_ha_generalized_crt_canonical_boundary_candidate_theorems(
        TheoremSpec
    )
    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
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
    _assert_public_admission()


def test_canonical_boundary_below_constructor_is_hygienic() -> None:
    assert below(
        "r", "l", tag="audit", variables=("l", "r")
    ) == "exists hgcrt_below_gap_audit. hgcrt_below_gap_audit + S r = l"
    for arguments in (
        {"value": "r", "bound": "l", "tag": "audit", "variables": ["l", "r"]},
        {"value": "r", "bound": "l", "tag": "audit", "variables": ("l", "l", "r")},
        {"value": "r", "bound": "l", "tag": "audit", "variables": ("l",)},
        {"value": "r", "bound": "l", "tag": "audit", "variables": ("r",)},
        {"value": "r", "bound": "l", "tag": "bad-tag", "variables": ("l", "r")},
        {
            "value": "r",
            "bound": "l",
            "tag": "audit",
            "variables": ("l", "r", "hgcrt_below_gap_audit"),
        },
    ):
        with pytest.raises(ValueError):
            below(**arguments)


def test_canonical_boundary_contracts_are_closed_native_and_bounded() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert len(item.statement) < 4000
        assert all(
            token not in item.statement
            for token in (
                "IsGCD(",
                "IsLCM(",
                "ModEq(",
                "CRTSolution(",
                "Below(",
                "Dvd(",
                "%",
                "<=",
                "<->",
            )
        )

    assert _candidate_specs()[0].statement.endswith("-> y = x")
    assert "exists r." in _candidate_specs()[1].statement
    assert "hgcrt_below_gap_canonical_nonzero_result" in (
        _candidate_specs()[1].statement
    )
    assert "\\/" in _candidate_specs()[2].statement


def test_canonical_boundary_bodies_are_constructive_and_mutation_sensitive() -> None:
    core = dict(_specs_by_name()) | {
        item.name: item
        for item in (
            *_congruence_specs(),
            *_sufficiency_specs(),
            *_zero_boundary_specs(),
            *_classification_specs(),
        )
    }
    receipts = replay_candidate_bodies(_candidate_specs(), core=core)
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

    commands = tuple(
        command for item in _candidate_specs() for command in item.script
    )
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
        for command in commands
    )
    assert all(
        forbidden not in command
        for command in commands
        for forbidden in ("DNE", "classical", "by_contra", "sorry")
    )

    mutations = {
        "crt_solution_unique_lcm_zero": lambda statement:
            statement.replace("-> y = x", "-> S y = x", 1),
        "crt_solution_canonical_remainder_nonzero": lambda statement:
            statement.replace("-> s = r", "-> S s = r", 1),
        "generalized_binary_crt_canonical_boundary": lambda statement:
            statement.replace("-> y = x", "-> S y = x", 1),
    }
    for item in _candidate_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_canonical_boundary_empty_context_closures_are_deterministic() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()
    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first
    assert all(
        receipt[6] == 0 for receipt in EXPECTED_CLOSED_RECEIPTS.values()
    )
    _assert_public_admission()


def _mod_eq(modulus: int, left: int, right: int) -> bool:
    return left == right if modulus == 0 else left % modulus == right % modulus


def _crt_solution(
    value: int,
    left_modulus: int,
    right_modulus: int,
    left_residue: int,
    right_residue: int,
) -> bool:
    return _mod_eq(left_modulus, value, left_residue) and _mod_eq(
        right_modulus, value, right_residue
    )


def test_canonical_boundary_bounded_all_modulus_semantics() -> None:
    compatible_cases = 0
    zero_lcm_cases = 0
    nonzero_lcm_cases = 0
    for left_modulus, right_modulus, left_residue, right_residue in product(
        range(7), range(7), range(11), range(11)
    ):
        common_gcd = gcd(left_modulus, right_modulus)
        if not _mod_eq(common_gcd, left_residue, right_residue):
            continue
        compatible_cases += 1
        common_lcm = lcm(left_modulus, right_modulus)

        if common_lcm == 0:
            zero_lcm_cases += 1
            fixed = left_residue if left_modulus == 0 else right_residue
            assert _crt_solution(
                fixed,
                left_modulus,
                right_modulus,
                left_residue,
                right_residue,
            )
            for candidate in range(25):
                if _crt_solution(
                    candidate,
                    left_modulus,
                    right_modulus,
                    left_residue,
                    right_residue,
                ):
                    assert candidate == fixed
            continue

        nonzero_lcm_cases += 1
        representatives = tuple(
            candidate
            for candidate in range(common_lcm)
            if _crt_solution(
                candidate,
                left_modulus,
                right_modulus,
                left_residue,
                right_residue,
            )
        )
        assert len(representatives) == 1
        representative = representatives[0]
        for candidate in range(2 * common_lcm + 1):
            if _crt_solution(
                candidate,
                left_modulus,
                right_modulus,
                left_residue,
                right_residue,
            ):
                assert _mod_eq(common_lcm, candidate, representative)

    assert compatible_cases == 4_021
    assert zero_lcm_cases == 611
    assert nonzero_lcm_cases == 3_410
