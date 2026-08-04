"""Focused audit for the relational-LCM generalized-CRT classification."""

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
from peano_lab.library.ha_generalized_crt_classification_candidate import (
    divides,
    make_ha_generalized_crt_classification_candidate_theorems,
)
from peano_lab.library.ha_generalized_crt_congruence_candidate import (
    make_ha_generalized_crt_congruence_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED_NAMES = (
    "mod_eq_ordered_gap_multiple",
    "mod_eq_lcm_merge",
    "mod_eq_lcm_iff_pair",
    "crt_solution_class_iff_lcm",
)
EXPECTED_DEPENDENCIES = {
    "mod_eq_ordered_gap_multiple": (
        "add_comm",
        "add_assoc",
        "add_left_cancel",
        "factor_difference",
    ),
    "mod_eq_lcm_merge": (
        "le_total",
        "mod_eq_symm",
        "mod_eq_ordered_gap_multiple",
        "is_lcm_least",
        "mul_comm",
        "remainder_decomposition_to_mod_eq",
    ),
    "mod_eq_lcm_iff_pair": (
        "is_lcm_multiple_left",
        "is_lcm_multiple_right",
        "mod_eq_of_mod_eq_multiple",
        "mod_eq_lcm_merge",
    ),
    "crt_solution_class_iff_lcm": (
        "crt_solution_pair_congruent",
        "mod_eq_lcm_iff_pair",
        "mod_eq_trans",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "mod_eq_ordered_gap_multiple":
        "c6d40a1a63937393206bef422e5a44021e14b19cab3b55fdec6ad78238fa64b0",
    "mod_eq_lcm_merge":
        "069eb5e4684895e186da5015966fa347b78403b3848cb8040c812f6bb46abcca",
    "mod_eq_lcm_iff_pair":
        "baa85529864c7d201d6b9320f290e05de84b9f61903ea7970d56abb2ec4fa19d",
    "crt_solution_class_iff_lcm":
        "bf8c300329f1d13f6f62101c6654f17a5369079034e1685c888c25301159e1c9",
}
EXPECTED_SCRIPT_REPR_SHA256 = {
    "mod_eq_ordered_gap_multiple":
        "36f1d45511b7a7941ff69887f691fa4e271a571b1c4648c15bfc2daacd59542a",
    "mod_eq_lcm_merge":
        "0b9cdbf5ff31c5536cdd25cf95a3fabf1a957b432dab1b5286eb26e99fd900bb",
    "mod_eq_lcm_iff_pair":
        "f8343a6d75682fa5129eaa2a19ef92f6b3a965241cda645d23c6817499fe989d",
    "crt_solution_class_iff_lcm":
        "763b8aea13fe50a65ff8397d076aa3b0defda847b57ebf8e626c4f11043c005e",
}
EXPECTED_BODY_RECEIPTS = {
    "mod_eq_ordered_gap_multiple": (4, 31, 44, 21, 44, 43, 0),
    "mod_eq_lcm_merge": (6, 113, 127, 26, 127, 126, 0),
    "mod_eq_lcm_iff_pair": (4, 46, 56, 21, 56, 55, 0),
    "crt_solution_class_iff_lcm": (3, 62, 79, 27, 79, 78, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "mod_eq_ordered_gap_multiple": (
        558, 30, 310, 325, 16, 13, 0,
        "6a30012cfc1213bf167be2de794e05cdae2893ab075cfc24abf9b181bde9be67",
    ),
    "mod_eq_lcm_merge": (
        1_315, 33, 653, 685, 33, 25, 0,
        "46cd67f69ccf0c669de283fca6a74a0a85cf18d54f248f1a6f428122196a331b",
    ),
    "mod_eq_lcm_iff_pair": (
        1_570, 37, 864, 908, 45, 32, 0,
        "855d5745c1613304fc0a5f26c70fe9f795ed3ebcff4a7276e3745681d41fc91a",
    ),
    "crt_solution_class_iff_lcm": (
        2_208, 39, 1_055, 1_104, 50, 40, 0,
        "305a913aaca1c3e307d8ca77bb90c063dd67f3fa9f9bdd69e28cf4064cdff7b3",
    ),
}


@lru_cache(maxsize=1)
def _congruence_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_congruence_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_generalized_crt_classification_candidate_theorems(
        TheoremSpec
    )


def _local_specs() -> dict[str, TheoremSpec]:
    return {
        item.name: item
        for item in (*_congruence_specs(), *_candidate_specs())
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


def test_classification_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_generalized_crt_classification_candidate_theorems(
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
        theorem_registry, "HA_GENERALIZED_CRT_CLASSIFICATION_THEOREMS"
    )


def test_classification_divides_constructor_is_hygienic() -> None:
    assert divides(
        "d", "k", tag="audit", variables=("d", "k")
    ) == "exists hgcrt_divides_factor_audit. k = d * hgcrt_divides_factor_audit"
    for arguments in (
        {"divisor": "d", "value": "k", "tag": "audit", "variables": ["d", "k"]},
        {"divisor": "d", "value": "k", "tag": "audit", "variables": ("d", "d", "k")},
        {"divisor": "d", "value": "k", "tag": "audit", "variables": ("d",)},
        {"divisor": "d", "value": "k", "tag": "audit", "variables": ("k",)},
        {"divisor": "d", "value": "k", "tag": "bad-tag", "variables": ("d", "k")},
        {
            "divisor": "d",
            "value": "k",
            "tag": "audit",
            "variables": ("d", "k", "hgcrt_divides_factor_audit"),
        },
    ):
        with pytest.raises(ValueError):
            divides(**arguments)


def test_classification_contracts_are_closed_native_and_bounded() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert len(item.statement) < 4000
        assert all(
            token not in item.statement
            for token in (
                "IsLCM(",
                "ModEq(",
                "CRTSolution(",
                "Dvd(",
                "%",
                "<=",
                "<->",
            )
        )

    assert "k = d *" in _candidate_specs()[0].statement
    assert _candidate_specs()[1].statement.startswith("forall l m n x y.")
    assert "/\\" in _candidate_specs()[2].statement
    assert _candidate_specs()[3].statement.startswith(
        "forall l m n a b x y."
    )


def test_classification_bodies_are_constructive_and_mutation_sensitive() -> None:
    core = dict(_specs_by_name()) | {
        item.name: item for item in _congruence_specs()
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
        "mod_eq_ordered_gap_multiple": lambda statement:
            statement.replace("k = d *", "S k = d *", 1),
        "mod_eq_lcm_merge": lambda statement:
            statement.replace("x + l *", "S x + l *", 1),
        "mod_eq_lcm_iff_pair": lambda statement:
            statement.replace("x + l *", "S x + l *", 1),
        "crt_solution_class_iff_lcm": lambda statement:
            statement.replace("y + l *", "S y + l *", 1),
    }
    for item in _candidate_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))


def test_classification_empty_context_closures_are_deterministic() -> None:
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


def _divides(divisor: int, value: int) -> bool:
    return value == 0 if divisor == 0 else value % divisor == 0


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


def test_classification_bounded_all_modulus_semantics() -> None:
    for divisor, gap, left in product(range(6), repeat=3):
        right = gap + left
        if _mod_eq(divisor, left, right):
            assert _divides(divisor, gap)

    lcm_equivalence_cases = 0
    for left_modulus, right_modulus, left, right in product(
        range(6), repeat=4
    ):
        lcm_equivalence_cases += 1
        modulus_lcm = lcm(left_modulus, right_modulus)
        pair = _mod_eq(left_modulus, left, right) and _mod_eq(
            right_modulus, left, right
        )
        merged = _mod_eq(modulus_lcm, left, right)
        assert pair == merged
    assert lcm_equivalence_cases == 1_296

    fixed_solution_class_cases = 0
    zero_lcm_class_cases = 0
    for left_modulus, right_modulus, left_residue, right_residue in product(
        range(5), repeat=4
    ):
        modulus_lcm = lcm(left_modulus, right_modulus)
        for fixed, candidate in product(range(6), repeat=2):
            fixed_solution = _crt_solution(
                fixed,
                left_modulus,
                right_modulus,
                left_residue,
                right_residue,
            )
            if not fixed_solution:
                continue
            fixed_solution_class_cases += 1
            if modulus_lcm == 0:
                zero_lcm_class_cases += 1
            candidate_solution = _crt_solution(
                candidate,
                left_modulus,
                right_modulus,
                left_residue,
                right_residue,
            )
            same_class = _mod_eq(modulus_lcm, candidate, fixed)
            assert candidate_solution == same_class
    assert fixed_solution_class_cases == 4_692
    assert zero_lcm_class_cases == 678

    assert gcd(0, 0) == 0
    assert lcm(0, 0) == 0
