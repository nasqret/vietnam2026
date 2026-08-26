"""Focused kernel, closure, mutation, and semantic audit for factorial valuations."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
from math import factorial

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
from peano_lab.library.bertrand_factorial_valuation_candidate import (
    factorial_valuation,
    make_bertrand_factorial_valuation_candidate_theorems,
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
    "factorial_nonzero": {
        "length": 2_595,
        "sha256": "ae7d7fada679e216a6c49741ac76cc84e20e8fa211638a5d1da65fea2ad4e801",
        "dependencies": (
            "factorial_zero",
            "factorial_succ_decompose",
            "succ_ne_zero",
            "mul_ne_zero",
        ),
        "body": (4, 47, 58, 21, 58, 57, 0),
        "closure": (3_941, 65, 1_117, 1_161, 45),
    },
    "prime_power_valuation_one_zero": {
        "length": 7_831,
        "sha256": "814fe3e6f732c3317abe83a5c245fd339156ce333d8b7780546b5fc92a1822a9",
        "dependencies": (
            "power_valuation_power_divides",
            "zero_or_succ",
            "pow_successor_decompose",
            "mul_eq_one_components",
        ),
        "body": (4, 56, 60, 26, 60, 59, 0),
        "closure": (2_806, 66, 1_105, 1_161, 57),
    },
    "factorial_valuation_exists": {
        "length": 13_036,
        "sha256": "65efe0afbd47d5a7120ac1bb8104199ee6c328d83ea61d00f1fe6ea0c995523d",
        "dependencies": ("factorial_exists", "power_valuation_exists"),
        "body": (2, 16, 16, 10, 16, 15, 0),
        "closure": (185_327, 94, 6_057, 6_324, 268),
    },
    "factorial_valuation_functional": {
        "length": 31_433,
        "sha256": "542cf8f94fc9427f92f4981012cac9cb819ffd0dedf6a0848d04b3ac5356e025",
        "dependencies": ("factorial_functional", "power_valuation_functional"),
        "body": (2, 28, 71, 22, 71, 70, 0),
        "closure": (3_027, 64, 1_356, 1_398, 43),
    },
    "prime_factorial_valuation_zero": {
        "length": 12_990,
        "sha256": "9327fd37f8bcf5263accdb30733a476a93699dc76380c9df8e599f26d0029048",
        "dependencies": ("factorial_zero", "prime_power_valuation_one_zero"),
        "body": (2, 21, 28, 17, 28, 27, 0),
        "closure": (4_057, 68, 1_235, 1_292, 58),
    },
    "prime_factorial_valuation_succ": {
        "length": 42_782,
        "sha256": "0234c6d5d9c583b74ede22478a6f02ff5795fab48e21161a2a6531aa037e77b0",
        "dependencies": (
            "factorial_succ_decompose",
            "factorial_functional",
            "factorial_nonzero",
            "succ_ne_zero",
            "prime_power_valuation_mul",
        ),
        "body": (5, 70, 134, 32, 134, 133, 0),
        "closure": (306_585, 103, 7_908, 8_242, 335),
    },
    "prime_factorial_valuation_succ_invert": {
        "length": 43_814,
        "sha256": "97de3eff47fa88f963bee282be9d1babbf79afaa1785d192027c558d249898b0",
        "dependencies": (
            "power_valuation_exists",
            "prime_factorial_valuation_succ",
        ),
        "body": (2, 29, 35, 26, 35, 34, 0),
        "closure": (432_090, 105, 8_418, 8_771, 354),
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
    return make_bertrand_factorial_valuation_candidate_theorems(TheoremSpec)


def _local() -> dict[str, TheoremSpec]:
    items = (*_prior_specs(), *_specs())
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
    return replace(certificate, body=_mutate_direct_cut(certificate.body, index - 1))


def test_factorial_valuation_factory_is_hygienic_expanded_and_topological() -> None:
    sample = factorial_valuation("p", "n", "e", tag="surface")
    formula, free_names = parse_formula_with_names(f"forall p n e. {sample}")
    assert not free_names
    assert formula == _closed_formula(f"forall p n e. {sample}")
    assert sample.startswith("exists bfv_factorial_surface.")
    for marker in ("Factorial(", "FactorialVal(", "PowerVal(", "Prime(", "Pow("):
        assert marker not in sample

    with pytest.raises(ValueError, match="Peano identifier"):
        factorial_valuation("p", "S n", "e", tag="bad_length")
    with pytest.raises(ValueError, match="binder tag"):
        factorial_valuation("p", "n", "e", tag="bad-tag")
    with pytest.raises(ValueError, match="captures"):
        factorial_valuation("bfv_factorial_capture", "n", "e", tag="capture")

    specs = _specs()
    assert tuple(item.name for item in specs) == tuple(EXPECTED)
    assert make_bertrand_factorial_valuation_candidate_theorems(TheoremSpec) == specs
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
                "Factorial(",
                "FactorialVal(",
                "PowerVal(",
                "Prime(",
                "Pow(",
                "^",
                "<=",
                "∣",
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


def test_factorial_valuation_bodies_kernel_check_with_exact_receipts() -> None:
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


def test_factorial_valuation_rejects_false_contracts_and_every_removed_edge() -> None:
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


def test_factorial_valuation_rejects_arithmetic_boundary_mutations() -> None:
    specs = {item.name: item for item in _specs()}
    mutations = {
        "factorial_nonzero": lambda statement: statement.replace(
            "~(F = 0)", "~(F = 1)", 1
        ),
        "prime_power_valuation_one_zero": lambda statement: statement.rsplit(
            "e = 0", 1
        )[0]
        + "e = 1",
        "factorial_valuation_functional": lambda statement: statement.rsplit(
            "e = f", 1
        )[0]
        + "e = S f",
        "prime_factorial_valuation_zero": lambda statement: statement.rsplit(
            "e = 0", 1
        )[0]
        + "e = 1",
        "prime_factorial_valuation_succ": lambda statement: statement.rsplit(
            "g = e + f", 1
        )[0]
        + "g = S (e + f)",
        "prime_factorial_valuation_succ_invert": lambda statement: statement.rsplit(
            "g = e + f", 1
        )[0]
        + "g = S (e + f)",
    }
    for name, mutate in mutations.items():
        item = specs[name]
        changed = mutate(item.statement)
        assert changed != item.statement
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((replace(item, statement=changed),), core=_available())


def test_factorial_valuation_empty_context_closures_and_cuts_are_checked() -> None:
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
            assert not check((), _mutate_direct_cut(certificate, index), formula), (
                f"accepted mutated direct Cut {item.name}[{index}]"
            )
    assert observed == {
        name: expected["closure"] for name, expected in EXPECTED.items()
    }


def _valuation(prime_value: int, value: int) -> int:
    assert prime_value >= 2 and value > 0
    exponent = 0
    while value % (prime_value ** (exponent + 1)) == 0:
        exponent += 1
    return exponent


def test_factorial_valuation_semantics_match_standard_naturals() -> None:
    for prime_value in (2, 3, 5, 7, 11):
        previous = 0
        for n in range(13):
            value = factorial(n)
            exponent = _valuation(prime_value, value)
            assert value != 0
            assert value % (prime_value**exponent) == 0
            assert value % (prime_value ** (exponent + 1)) != 0
            assert exponent == _valuation(prime_value, value)
            if n == 0:
                assert value == 1
                assert exponent == 0
            else:
                factor_exponent = _valuation(prime_value, n)
                assert value == factorial(n - 1) * n
                assert exponent == previous + factor_exponent
                assert factor_exponent == exponent - previous
            previous = exponent
