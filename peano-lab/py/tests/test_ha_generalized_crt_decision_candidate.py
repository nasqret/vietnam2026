"""Focused audit for the executable generalized-CRT decision boundary."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256
from itertools import product
from math import gcd, lcm

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import theorems as theorem_registry
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.ha_generalized_crt_congruence_candidate import (
    make_ha_generalized_crt_congruence_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_decision_candidate import (
    make_ha_generalized_crt_decision_candidate_theorems,
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
    "mod_eq_decidable",
    "generalized_binary_crt_solution_or_obstruction",
)
ADMITTED_NAMES = EXPECTED_NAMES
EXPECTED_DEPENDENCIES = {
    "mod_eq_decidable": (
        "eq_decidable",
        "mod_eq_zero_iff_eq",
        "mod_eq_decidable_nonzero",
    ),
    "generalized_binary_crt_solution_or_obstruction": (
        "mod_eq_decidable",
        "generalized_binary_crt_sufficient",
        "crt_incompatibility_obstructs_solution",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "mod_eq_decidable":
        "b9a37c915c3f13386135830dcc03f17990caf279d6f9f3f7d9cf57539f6b8737",
    "generalized_binary_crt_solution_or_obstruction":
        "54f7722b7e718aff0cd85aeae4ce6b86528892a5e52074d5f2e86eec4d6a3aec",
}
EXPECTED_SCRIPT_REPR_SHA256 = {
    "mod_eq_decidable":
        "da2c71136a3513768b230d475366ef1275a7996bba32e1808eeac8ce58f5cb8d",
    "generalized_binary_crt_solution_or_obstruction":
        "b8e9e45aa8310ef0de7323c4d7f6f2e698bbad4388102ffb18c0075ba3aa3507",
}
EXPECTED_BODY_RECEIPTS = {
    "mod_eq_decidable": (3, 35, 47, 16, 47, 46, 0),
    "generalized_binary_crt_solution_or_obstruction": (
        3, 36, 43, 22, 43, 42, 0,
    ),
}
EXPECTED_CLOSED_RECEIPTS = {
    "mod_eq_decidable": (
        2_339, 70, 1_217, 1_278, 62, 44, 0,
        "298e2b18fff84bcf3a2ec69dbc464454f958d4155b7afb687f0bab2fd95efe7e",
    ),
    "generalized_binary_crt_solution_or_obstruction": (
        14_182, 80, 3_909, 4_090, 182, 182, 0,
        "16e7cb1c430fa4e17ea878adc72d34c92e0bc3f135c4a3cf24cb2a296b38e525",
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
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_decision_candidate_theorems(TheoremSpec)


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


def test_decision_factory_is_exact_ordered_and_publicly_admitted() -> None:
    first = _candidate_specs()
    second = make_ha_generalized_crt_decision_candidate_theorems(TheoremSpec)
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


def test_decision_contracts_are_closed_native_and_bounded() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert len(item.statement) < 4000
        assert all(
            token not in item.statement
            for token in (
                "IsGCD(",
                "ModEq(",
                "CRTSolution(",
                "Dvd(",
                "%",
                "<=",
                "<->",
            )
        )

    assert _candidate_specs()[0].statement.startswith("forall d a b.")
    assert "\\/" in _candidate_specs()[0].statement
    assert _candidate_specs()[1].statement.startswith("forall g m n a b.")
    assert "~(exists x." in _candidate_specs()[1].statement


def test_decision_bodies_are_constructive_and_mutation_sensitive() -> None:
    core = dict(_specs_by_name()) | {
        item.name: item
        for item in (
            *_congruence_specs(),
            *_sufficiency_specs(),
            *_zero_boundary_specs(),
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
        "mod_eq_decidable": lambda statement: statement.replace(
            "a + d * hgcrt_mod_left_decision_yes",
            "S a + d * hgcrt_mod_left_decision_yes",
            1,
        ),
        "generalized_binary_crt_solution_or_obstruction": lambda statement:
            statement.replace(
                "a + g * hgcrt_mod_left_decision_boundary_incompatible",
                "S a + g * hgcrt_mod_left_decision_boundary_incompatible",
                1,
            ),
    }
    for item in _candidate_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_decision_empty_context_closures_are_deterministic() -> None:
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


def test_mod_eq_decision_bounded_all_modulus_semantics() -> None:
    cases = 0
    congruent_cases = 0
    incongruent_cases = 0
    zero_modulus_cases = 0
    for modulus, left, right in product(range(7), range(11), range(11)):
        cases += 1
        decision = _mod_eq(modulus, left, right)
        if decision:
            congruent_cases += 1
        else:
            incongruent_cases += 1
        if modulus == 0:
            zero_modulus_cases += 1
            assert decision == (left == right)

    assert cases == 847
    assert congruent_cases == 311
    assert incongruent_cases == 536
    assert zero_modulus_cases == 121


def test_solution_or_obstruction_bounded_semantics() -> None:
    systems = 0
    solution_cases = 0
    obstruction_cases = 0
    zero_gcd_solution_cases = 0
    zero_gcd_obstruction_cases = 0
    for left_modulus, right_modulus, left_residue, right_residue in product(
        range(7), range(7), range(11), range(11)
    ):
        systems += 1
        common_gcd = gcd(left_modulus, right_modulus)
        compatible = _mod_eq(common_gcd, left_residue, right_residue)
        common_lcm = lcm(left_modulus, right_modulus)

        if common_lcm == 0:
            fixed = left_residue if left_modulus == 0 else right_residue
            solution_exists = _crt_solution(
                fixed,
                left_modulus,
                right_modulus,
                left_residue,
                right_residue,
            )
        else:
            solution_exists = any(
                _crt_solution(
                    candidate,
                    left_modulus,
                    right_modulus,
                    left_residue,
                    right_residue,
                )
                for candidate in range(common_lcm)
            )
        assert solution_exists == compatible

        if compatible:
            solution_cases += 1
            if common_gcd == 0:
                zero_gcd_solution_cases += 1
        else:
            obstruction_cases += 1
            if common_gcd == 0:
                zero_gcd_obstruction_cases += 1

    assert systems == 5_929
    assert solution_cases == 4_021
    assert obstruction_cases == 1_908
    assert zero_gcd_solution_cases == 11
    assert zero_gcd_obstruction_cases == 110
