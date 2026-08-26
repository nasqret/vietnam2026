"""Kernel, mutation, capacity, and semantic audit for valuation bridges."""

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
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED = {
    "prime_power_quotient_tail_zero": {
        "length": 3_571,
        "sha256": "4dab0178fcbda112f058c05629a323ddbcc6ae2ddd23c91256ab692a072962fe",
        "dependencies": ("prime_power_exponent_le", "zero_add"),
        "body": (2, 18, 33, 17, 33, 32, 0),
        "closure": (7_353, 72, 1_475, 1_534, 60),
    },
    "prime_power_divides_exponent_le_valuation": {
        "length": 13_151,
        "sha256": "8f6cb78d3d5cfc70d371d3c729258e4064101bc04b457029713a10e09d12a56e",
        "dependencies": (
            "prime_power_divides_exponent_le_value",
            "power_valuation_dominates",
        ),
        "body": (2, 24, 30, 19, 30, 29, 0),
        "closure": (7_512, 73, 1_572, 1_634, 63),
    },
    "power_divides_of_exponent_le_valuation": {
        "length": 12_933,
        "sha256": "acce58503ec69525258a4e726467ce185a4a5b5d3ccf11575e4b5768c94bbb16",
        "dependencies": (
            "power_valuation_power_divides",
            "power_divides_exponent_antitone",
        ),
        "body": (2, 19, 22, 15, 22, 21, 0),
        "closure": (66_872, 91, 5_774, 6_032, 259),
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
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_legendre_valuation_bridge_candidate_theorems(
        TheoremSpec
    )


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


def test_bridge_factory_is_frozen_native_isolated_and_topological() -> None:
    specs = _specs()
    assert tuple(item.name for item in specs) == tuple(EXPECTED)
    assert (
        make_bertrand_legendre_valuation_bridge_candidate_theorems(
            TheoremSpec
        )
        == specs
    )
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
                "Pow(",
                "PowDiv(",
                "PowerVal(",
                "Prime(",
                "DivRem(",
                "^",
                "<=",
                "∣",
                "%",
            )
        )

    commands = tuple(command for item in specs for command in item.script)
    assert all(
        command.split(maxsplit=1)[0]
        not in {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
        for command in commands
    )
    assert all(
        forbidden not in command
        for command in commands
        for forbidden in ("DNE", "by_contra", "classical", "sorry")
    )


def test_bridge_bodies_kernel_check_with_exact_receipts() -> None:
    core = dict(_specs_by_name()) | {
        item.name: item for item in _prior_specs()
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


def test_bridge_rejects_false_contracts_and_every_removed_edge() -> None:
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


def test_bridge_rejects_quotient_and_order_boundary_mutations() -> None:
    specs = {item.name: item for item in _specs()}

    tail = specs["prime_power_quotient_tail_zero"]
    changed_tail = tail.statement.replace(
        "n = (d) * (0) + (n)",
        "n = (d) * (1) + (n)",
        1,
    )

    forward = specs["prime_power_divides_exponent_le_valuation"]
    forward_prefix, forward_conclusion = forward.statement.rsplit(
        "bpv_gap_blvb_candidate_bound + k = f", 1
    )
    changed_forward = (
        forward_prefix
        + "bpv_gap_blvb_candidate_bound + S k = f"
        + forward_conclusion
    )

    reverse = specs["power_divides_of_exponent_le_valuation"]
    changed_reverse = reverse.statement.replace(
        "bpv_gap_blvb_candidate_bound + k = f",
        "bpv_gap_blvb_candidate_bound + f = k",
        1,
    )

    mutations = {
        tail.name: changed_tail,
        forward.name: changed_forward,
        reverse.name: changed_reverse,
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


def test_bridge_empty_context_closures_and_every_direct_cut_are_checked() -> None:
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
    assert direct_cut_mutations == 6


def _valuation(prime: int, value: int) -> int:
    exponent = 0
    while value % (prime ** (exponent + 1)) == 0:
        exponent += 1
    return exponent


def test_bridge_semantics_match_standard_naturals() -> None:
    # These bounded host calculations are regression fixtures, never proof
    # authority.  The theorem certificates above are checked independently.
    for prime in (2, 3, 5, 7, 11):
        for n in range(25):
            divisor = prime ** (n + 1)
            quotient, remainder = divmod(n, divisor)
            assert quotient == 0
            assert remainder == n
            assert n == divisor * quotient + remainder
            assert remainder < divisor

        for value in range(1, 101):
            valuation = _valuation(prime, value)
            for exponent in range(valuation + 4):
                divides = value % (prime**exponent) == 0
                assert divides == (exponent <= valuation)
