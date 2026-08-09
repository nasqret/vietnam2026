"""Kernel, mutation, capacity, and semantic audit for Legendre successors."""

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
from peano_lab.library.bertrand_legendre_successor_candidate import (
    make_bertrand_legendre_successor_candidate_theorems,
)
from peano_lab.library.bertrand_legendre_valuation_bridge_candidate import (
    make_bertrand_legendre_valuation_bridge_candidate_theorems,
)
from peano_lab.library.bertrand_power_divisibility_candidate import (
    make_bertrand_power_divisibility_candidate_theorems,
)
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
from peano_lab.library.eisenstein_initial_segment_count_candidate import (
    make_eisenstein_initial_segment_count_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED = {
    "division_remainder_successor_cases": {
        "length": 442,
        "sha256": "d086df3cbac2b6d1ac0ad5cb4329aab602090774ac1ba7d48b0abacd7b06307b",
        "dependencies": ("le_eq_or_lt", "division_remainder_unique"),
        "body": (2, 70, 93, 24, 93, 92, 0),
        "closure": (1_045, 59, 683, 707, 25),
    },
    "division_successor_quotient_by_bit": {
        "length": 368,
        "sha256": "08bfcac7df8ece3337a2975c3e48dda3d5199d6189e74f893851660955b95777",
        "dependencies": (
            "division_remainder_successor_cases",
            "add_eq_zero_right",
            "succ_ne_zero",
            "multiple_has_zero_remainder",
            "division_remainder_unique",
            "zero_remainder_implies_multiple",
        ),
        "body": (6, 99, 148, 36, 148, 147, 0),
        "closure": (2_134, 62, 906, 936, 31),
    },
    "valuation_threshold_bit_decides_power_divides": {
        "length": 23_347,
        "sha256": "940541b3f5616546a3715898d4079cfbb9179ae42648f3841f0350fd83b4dc14",
        "dependencies": (
            "power_divides_of_exponent_le_valuation",
            "prime_power_divides_exponent_le_valuation",
            "lt_not_le",
        ),
        "body": (3, 41, 53, 26, 53, 52, 0),
        "closure": (74_493, 92, 6_382, 6_663, 282),
    },
    "power_quotient_prefix_decoded_divrem": {
        "length": 10_312,
        "sha256": "3516e4b3a5e03a653c94a7dd5e704a6d24f88c7ba2d449f36d48c1f5f5e9daf3",
        "dependencies": ("beta_at_unique",),
        "body": (1, 34, 41, 26, 41, 40, 0),
        "closure": (1_162, 60, 733, 769, 37),
    },
    "power_quotient_successor_pointwise_add": {
        "length": 27_039,
        "sha256": "9106c2218c1b4e2a420334e522270246747fca65d83642a65507f05f8eeefc46",
        "dependencies": (
            "power_quotient_prefix_decoded_divrem",
            "eisenstein_initial_segment_decoded_choice",
            "valuation_threshold_bit_decides_power_divides",
            "pow_functional",
            "division_successor_quotient_by_bit",
            "succ_ne_zero",
        ),
        "body": (6, 127, 171, 48, 171, 170, 0),
        "closure": (81_828, 95, 6_931, 7_226, 296),
    },
}


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_bertrand_power_order_candidate_theorems(TheoremSpec),
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec),
        *make_bertrand_power_valuation_candidate_theorems(TheoremSpec),
        *make_bertrand_power_valuation_law_candidate_theorems(TheoremSpec),
        *make_bertrand_power_divisibility_candidate_theorems(TheoremSpec),
        *make_bertrand_legendre_valuation_bridge_candidate_theorems(TheoremSpec),
        *make_eisenstein_initial_segment_count_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_legendre_successor_candidate_theorems(TheoremSpec)


def _local() -> dict[str, TheoremSpec]:
    rows = (*_prior_specs(), *_specs())
    assert len({row.name for row in rows}) == len(rows)
    return {row.name: row for row in rows}


def _available() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _local()


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
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
        return replace(
            certificate,
            proposition=Eq(zero, zero),
            lemma=EqRefl(zero),
        )
    return replace(
        certificate,
        body=_mutate_direct_cut(certificate.body, index - 1),
    )


def test_successor_factory_is_frozen_native_isolated_and_topological() -> None:
    specs = _specs()
    assert tuple(item.name for item in specs) == tuple(EXPECTED)
    assert make_bertrand_legendre_successor_candidate_theorems(TheoremSpec) == specs
    assert not (set(EXPECTED) & set(_specs_by_name()))

    available = set(_specs_by_name()) | {item.name for item in _prior_specs()}
    for item in specs:
        expected = EXPECTED[item.name]
        assert item.dependencies == expected["dependencies"]
        assert all(dependency in available for dependency in item.dependencies)
        available.add(item.name)
        assert len(item.statement) == expected["length"]
        assert sha256(item.statement.encode()).hexdigest() == expected["sha256"]
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert all(
            marker not in item.statement
            for marker in (
                "DivRem(",
                "Pow(",
                "PowDiv(",
                "PowerVal(",
                "PowerQuotPrefix(",
                "InitialSegment(",
                "Prime(",
                "BetaAt(",
                "^",
                "%",
                "∣",
                "<=",
            )
        )

    commands = tuple(command for item in specs for command in item.script)
    assert all(
        command.split(maxsplit=1)[0]
        not in {
            "auto",
            "choice",
            "compact_arith",
            "norm_num",
            "ring",
            "simp",
            "use",
        }
        for command in commands
    )
    assert all(
        forbidden not in command
        for command in commands
        for forbidden in ("DNE", "by_contra", "classical", "sorry")
    )


def test_successor_bodies_kernel_check_with_exact_receipts() -> None:
    receipts = replay_candidate_bodies(_specs(), core=_available())
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


def test_successor_rejects_false_contracts_and_every_removed_edge() -> None:
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


def test_successor_rejects_arithmetic_and_pointwise_boundary_mutations() -> None:
    specs = {item.name: item for item in _specs()}

    cases = specs["division_remainder_successor_cases"]
    changed_cases = cases.statement.replace("z = S q", "z = q", 1)

    quotient = specs["division_successor_quotient_by_bit"]
    changed_quotient = quotient.statement.removesuffix("z = q + bit") + "z = S (q + bit)"

    threshold = specs["valuation_threshold_bit_decides_power_divides"]
    changed_threshold = threshold.statement.replace(
        "blsr_le_gap_legendre_successor_threshold_inside + (S i) = (f)",
        "blsr_le_gap_legendre_successor_threshold_inside + (S (S i)) = (f)",
        1,
    )

    projection = specs["power_quotient_prefix_decoded_divrem"]
    changed_projection = projection.statement.replace(
        "(n) = (D) * (q) + (r)",
        "(S n) = (D) * (q) + (r)",
        1,
    )

    pointwise = specs["power_quotient_successor_pointwise_add"]
    changed_pointwise = pointwise.statement.removesuffix("s = a + bit") + "s = S (a + bit)"

    mutations = {
        cases.name: changed_cases,
        quotient.name: changed_quotient,
        threshold.name: changed_threshold,
        projection.name: changed_projection,
        pointwise.name: changed_pointwise,
    }
    assert set(mutations) == set(EXPECTED)
    for name, statement in mutations.items():
        item = specs[name]
        assert statement != item.statement
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies(
                (replace(item, statement=statement),),
                core=_available(),
            )


def test_successor_empty_context_closures_and_every_direct_cut_are_checked() -> None:
    observed = {}
    direct_cut_mutations = 0
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
            direct_cut_mutations += 1

    assert observed == {
        name: expected["closure"] for name, expected in EXPECTED.items()
    }
    assert direct_cut_mutations == 18


def _valuation(prime: int, value: int) -> int:
    exponent = 0
    while value % (prime ** (exponent + 1)) == 0:
        exponent += 1
    return exponent


def test_successor_semantics_match_standard_naturals() -> None:
    # Bounded host arithmetic is regression evidence only, never proof authority.
    for divisor in range(1, 13):
        for n in range(80):
            quotient, remainder = divmod(n, divisor)
            successor_quotient, successor_remainder = divmod(n + 1, divisor)
            if remainder + 1 == divisor:
                assert successor_quotient == quotient + 1
                assert successor_remainder == 0
            else:
                assert remainder + 1 < divisor
                assert successor_quotient == quotient
                assert successor_remainder == remainder + 1
            bit = int((n + 1) % divisor == 0)
            assert successor_quotient == quotient + bit

    for prime in (2, 3, 5, 7, 11):
        for value in range(1, 81):
            valuation = _valuation(prime, value)
            for index in range(value + 1):
                bit = int(index + 1 <= valuation)
                divides = value % (prime ** (index + 1)) == 0
                assert bool(bit) == divides

        for n in range(60):
            valuation = _valuation(prime, n + 1)
            for index in range(n + 1):
                divisor = prime ** (index + 1)
                old = n // divisor
                new = (n + 1) // divisor
                bit = int(index + 1 <= valuation)
                assert new == old + bit
