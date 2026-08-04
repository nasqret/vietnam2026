"""Focused audit for the raw-input total generalized-CRT decision wrapper."""

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
from peano_lab.library.ha_generalized_crt_total_decision_candidate import (
    make_ha_generalized_crt_total_decision_candidate_theorems,
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


EXPECTED_NAMES = ("generalized_binary_crt_total_decision",)
EXPECTED_DEPENDENCIES = {
    "generalized_binary_crt_total_decision": (
        "gcd_exists_relational",
        "generalized_binary_crt_solution_or_obstruction",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "generalized_binary_crt_total_decision":
        "42d29bf501421be60c1a2b14fa858a14abf230eee2f7669503db019d6b014151",
}
EXPECTED_SCRIPT_REPR_SHA256 = {
    "generalized_binary_crt_total_decision":
        "fbc283041460e388b03902418c6d1a4a26881542e0c06a0db69b48f45b5e65c1",
}
EXPECTED_BODY_RECEIPTS = {
    "generalized_binary_crt_total_decision": (2, 17, 42, 25, 42, 41, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "generalized_binary_crt_total_decision": (
        15_492, 82, 4_052, 4_240, 189, 192, 0,
        "c2d915d2eb60ccbb2dac9f31e9e1f9c310c28264b74483ec97ae33a1a0d965ee",
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
def _decision_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_decision_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_total_decision_candidate_theorems(
        TheoremSpec
    )


def _local_specs() -> dict[str, TheoremSpec]:
    return {
        item.name: item
        for item in (
            *_congruence_specs(),
            *_sufficiency_specs(),
            *_zero_boundary_specs(),
            *_decision_specs(),
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


def test_total_decision_factory_is_exact_and_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_generalized_crt_total_decision_candidate_theorems(
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
    assert all(item.name not in _specs_by_name() for item in first)
    assert not hasattr(
        theorem_registry, "HA_GENERALIZED_CRT_TOTAL_DECISION_THEOREMS"
    )


def test_total_decision_contract_is_closed_native_and_bounded() -> None:
    item = _candidate_specs()[0]
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
    assert item.statement.startswith("forall m n a b. exists g.")
    assert "~(exists x." in item.statement


def test_total_decision_body_is_constructive_and_mutation_sensitive() -> None:
    core = dict(_specs_by_name()) | {
        item.name: item
        for item in (
            *_congruence_specs(),
            *_sufficiency_specs(),
            *_zero_boundary_specs(),
            *_decision_specs(),
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

    item = _candidate_specs()[0]
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
        for command in item.script
    )
    assert all(
        forbidden not in command
        for command in item.script
        for forbidden in ("DNE", "classical", "by_contra", "sorry")
    )

    certificate, target = _body_certificate(item)
    assert check((), certificate, target)
    assert not any(type(node) is DNE for node in _walk(certificate))
    mutated_statement = item.statement.replace(
        "m = g * hag_left_factor_total_decision",
        "S m = g * hag_left_factor_total_decision",
        1,
    )
    assert mutated_statement != item.statement
    assert not check((), certificate, _curried_target(item, mutated_statement))


def test_total_decision_empty_context_closure_is_deterministic() -> None:
    first = _cold_closed_receipts()
    second = _cold_closed_receipts()
    assert first == EXPECTED_CLOSED_RECEIPTS
    assert second == first
    assert all(
        receipt[6] == 0 for receipt in EXPECTED_CLOSED_RECEIPTS.values()
    )
    assert all(item.name not in _specs_by_name() for item in _candidate_specs())


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


def test_total_decision_bounded_raw_input_semantics() -> None:
    systems = 0
    solution_outputs = 0
    obstruction_outputs = 0
    zero_gcd_solution_outputs = 0
    zero_gcd_obstruction_outputs = 0
    for left_modulus, right_modulus, left_residue, right_residue in product(
        range(7), range(7), range(11), range(11)
    ):
        systems += 1
        common_gcd = gcd(left_modulus, right_modulus)
        assert left_modulus == common_gcd * (
            0 if common_gcd == 0 else left_modulus // common_gcd
        )
        assert right_modulus == common_gcd * (
            0 if common_gcd == 0 else right_modulus // common_gcd
        )
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
            solution_outputs += 1
            if common_gcd == 0:
                zero_gcd_solution_outputs += 1
        else:
            obstruction_outputs += 1
            if common_gcd == 0:
                zero_gcd_obstruction_outputs += 1

    assert systems == 5_929
    assert solution_outputs == 4_021
    assert obstruction_outputs == 1_908
    assert zero_gcd_solution_outputs == 11
    assert zero_gcd_obstruction_outputs == 110
