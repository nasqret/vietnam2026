"""Kernel, mutation, semantic, and capacity audit for valuation laws."""

from __future__ import annotations

from dataclasses import fields, replace
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
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.bertrand_power_growth_candidate import (
    make_bertrand_power_growth_candidate_theorems,
)
from peano_lab.library.bertrand_power_order_candidate import (
    make_bertrand_power_order_candidate_theorems,
)
from peano_lab.library.bertrand_power_valuation_candidate import (
    make_bertrand_power_valuation_candidate_theorems,
)
from peano_lab.library.bertrand_power_valuation_laws_candidate import (
    make_bertrand_power_valuation_law_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED = {
    "prime_two_le": {
        "length": 275,
        "sha256": "1b3c7c140e6ce0e53d771c6580a3b8cf081835013d994878a22e5de1d1a04e7c",
        "dependencies": ("prime_is_succ_succ",),
        "body": (1, 15, 27, 12, 27, 26, 0),
        "closure": (125, 14, 125, 124, 0),
    },
    "succ_le_mul_of_two_le_right": {
        "length": 162,
        "sha256": "201972639fe0cde658f6249560fe41d3a8904c77500aa72787162006a556b8c5",
        "dependencies": (
            "mul_lt_mul_succ_left_nonzero",
            "mul_le_mul_left",
            "mul_one",
            "le_trans",
        ),
        "body": (4, 23, 28, 15, 28, 27, 0),
        "closure": (316, 19, 249, 267, 19),
    },
    "prime_power_exponent_le": {
        "length": 3_410,
        "sha256": "8867c628e09cfa8890c2644b7b3df87d9951b10041f0e91da0d7d870ff54f53b",
        "dependencies": (
            "pow_successor_decompose",
            "zero_le",
            "prime_nonzero",
            "one_le_of_ne_zero",
            "pow_nonzero_of_one_le",
            "prime_two_le",
            "succ_le_succ",
            "succ_le_mul_of_two_le_right",
            "le_trans",
        ),
        "body": (9, 67, 84, 33, 84, 83, 0),
        "closure": (7_303, 71, 1_442, 1_500, 59),
    },
    "prime_power_divides_exponent_le_value": {
        "length": 4_031,
        "sha256": "f5fd95b11baeb9187a402f1a2cb1ccfd7fc5a793ac548138c1606f36e26c748e",
        "dependencies": (
            "prime_power_exponent_le",
            "divisor_le_nonzero",
            "le_trans",
        ),
        "body": (3, 27, 34, 18, 34, 33, 0),
        "closure": (7_458, 72, 1_518, 1_580, 63),
    },
    "power_valuation_successor_not_divides": {
        "length": 12_795,
        "sha256": "2db989e4c49867e39aede51d867d65c496cd47d56f69fcd139f6db30a66603f6",
        "dependencies": (
            "prime_power_divides_exponent_le_value",
            "zero_add",
            "lt_not_le",
        ),
        "body": (3, 30, 34, 20, 34, 33, 0),
        "closure": (7_565, 73, 1_608, 1_671, 64),
    },
    "power_valuation_selected_and_successor_not_divides": {
        "length": 16_757,
        "sha256": "c2f7d22ed9ae46992ff28f8511511554c5876f0309a13e0f476b14ed741f4ff5",
        "dependencies": (
            "power_valuation_power_divides",
            "power_valuation_successor_not_divides",
        ),
        "body": (2, 21, 46, 21, 46, 45, 0),
        "closure": (7_632, 75, 1_675, 1_738, 64),
    },
}


@lru_cache(maxsize=1)
def _order_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_power_order_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _growth_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_power_growth_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _valuation_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_power_valuation_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_power_valuation_law_candidate_theorems(TheoremSpec)


def _local() -> dict[str, TheoremSpec]:
    items = (*_order_specs(), *_growth_specs(), *_valuation_specs(), *_specs())
    assert len({item.name for item in items}) == len(items)
    return {item.name: item for item in items}


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local()


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for field in fields(proof)
        if isinstance((child := getattr(proof, field.name)), Proof)
    )


def _walk_proof(proof: Proof):
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        if id(node) in seen:
            continue
        seen.add(id(node))
        yield node
        pending.extend(_proof_children(node))


def _curried_body(item: TheoremSpec) -> tuple[Proof, Formula]:
    available = _available()
    formula = _closed_formula(item.statement)
    target = formula
    for dependency in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency].statement), target)
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), formula


@lru_cache(maxsize=None)
def _close(name: str) -> tuple[Formula, Proof]:
    local = _local()
    if name not in local:
        theorem = replay(name)
        return theorem.formula, theorem.certificate

    item = local[name]
    curried, formula = _curried_body(item)
    body = curried
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body
    for dependency in reversed(item.dependencies):
        dependency_formula, dependency_proof = _close(dependency)
        body = Cut(dependency_formula, formula, dependency_proof, body)
    assert check((), body, formula)
    return formula, body


def _mutate_direct_cut(certificate: Proof, index: int) -> Proof:
    assert type(certificate) is Cut
    if index == 0:
        zero = Zero()
        return replace(certificate, proposition=Eq(zero, zero), lemma=EqRefl(zero))
    return replace(
        certificate,
        body=_mutate_direct_cut(certificate.body, index - 1),
    )


def test_valuation_law_factory_is_frozen_native_isolated_and_topological() -> None:
    specs = _specs()
    assert tuple(item.name for item in specs) == tuple(EXPECTED)
    assert make_bertrand_power_valuation_law_candidate_theorems(TheoremSpec) == specs
    assert not (set(EXPECTED) & set(_specs_by_name()))

    available = set(_specs_by_name()) | set(_local())
    for item in specs:
        expected = EXPECTED[item.name]
        assert item.dependencies == expected["dependencies"]
        assert all(dependency in available for dependency in item.dependencies)
        assert len(item.statement) == expected["length"]
        assert sha256(item.statement.encode()).hexdigest() == expected["sha256"]
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            marker not in item.statement
            for marker in (
                "Pow(",
                "PowDiv(",
                "PVal(",
                "Prime(",
                "^",
                "<=",
                "∣",
            )
        )


def test_valuation_law_bodies_kernel_check_with_exact_receipts() -> None:
    core = dict(_specs_by_name()) | {
        item.name: item
        for item in (*_order_specs(), *_growth_specs(), *_valuation_specs())
    }
    receipts = replay_candidate_bodies(_specs(), core=core)
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
    } == {name: expected["body"] for name, expected in EXPECTED.items()}


def test_valuation_laws_reject_false_contracts_and_every_removed_edge() -> None:
    for item in _specs():
        false_item = replace(item, statement=f"({item.statement}) /\\ false")
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((false_item,), core=_available())

        for dependency in item.dependencies:
            without_edge = replace(
                item,
                dependencies=tuple(
                    candidate
                    for candidate in item.dependencies
                    if candidate != dependency
                ),
            )
            with pytest.raises(CandidateBodyError):
                replay_candidate_bodies((without_edge,), core=_available())


def test_valuation_law_empty_context_closures_and_every_cut_are_checked() -> None:
    observed = {}
    for item in _specs():
        formula, certificate = _close(item.name)
        assert check((), certificate, formula)
        assert not any(type(node) is DNE for node in _walk_proof(certificate))
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        observed[item.name] = (nodes, depth, objects, edges, reused)
        assert nodes <= MAX_USE_CERTIFICATE_NODES
        assert depth <= MAX_USE_PROOF_DEPTH
        assert objects <= MAX_USE_CERTIFICATE_OBJECTS
        for index, _dependency in enumerate(item.dependencies):
            assert not check(
                (),
                _mutate_direct_cut(certificate, index),
                formula,
            ), f"accepted mutated direct Cut {item.name}[{index}]"
    assert observed == {
        name: expected["closure"] for name, expected in EXPECTED.items()
    }


def test_valuation_law_semantics_match_standard_naturals() -> None:
    primes = (2, 3, 5, 7, 11)
    for prime_value in primes:
        assert 2 <= prime_value
        for exponent in range(8):
            power = prime_value**exponent
            assert exponent <= power
            if exponent > 0:
                assert exponent <= power <= power * 3

        for value in range(1, 81):
            exponent = 0
            while value % (prime_value ** (exponent + 1)) == 0:
                exponent += 1
            assert value % (prime_value**exponent) == 0
            assert value % (prime_value ** (exponent + 1)) != 0
            assert exponent <= value
