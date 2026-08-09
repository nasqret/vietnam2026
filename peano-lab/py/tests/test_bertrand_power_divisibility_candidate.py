"""Full audit for PowDiv algebra and valuation multiplication candidates."""

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
    "mul_shuffle_four": {
        "length": 53,
        "sha256": "19b66d6067bb43e0b83b85fb2608c48f5a9ffd6b14f34b217c852b9e0820cb25",
        "dependencies": ("mul_assoc", "mul_comm"),
        "body": (2, 23, 39, 15, 39, 38, 0),
        "closure": (377, 26, 311, 344, 34),
    },
    "power_divides_exponent_antitone": {
        "length": 6_651,
        "sha256": "a55f7b6504d1c5aa7d841ff0127e2ddae4899ef611623bc0994e54f7bc2f878a",
        "dependencies": ("pow_exists", "pow_add", "add_comm", "mul_assoc"),
        "body": (4, 51, 60, 33, 60, 59, 0),
        "closure": (66_829, 89, 5_731, 5_989, 259),
    },
    "power_divides_add_mul": {
        "length": 9_709,
        "sha256": "bc59b8c39cfce44b3beef19b9717d275dbb189d1e5d45645f644061759ff5a6e",
        "dependencies": ("pow_exists", "pow_add", "mul_shuffle_four"),
        "body": (3, 47, 61, 36, 61, 60, 0),
        "closure": (67_018, 89, 5_771, 6_029, 259),
    },
    "power_divides_successor_of_cofactor": {
        "length": 6_595,
        "sha256": "ca4fd229a6bde9c593b7948b0abf14786a80db9bd0c24343770abcef342abc23",
        "dependencies": ("pow_exists", "pow_successor_pair_mul", "mul_assoc"),
        "body": (3, 38, 47, 30, 47, 46, 0),
        "closure": (65_281, 89, 5_529, 5_780, 252),
    },
    "prime_power_successor_cancel_cofactor": {
        "length": 6_581,
        "sha256": "e31164bb3d38f8b8cc3de74b17f6e9cf2d0b7a00525c2b0c183d55f23a4a6e1b",
        "dependencies": (
            "prime_nonzero",
            "one_le_of_ne_zero",
            "pow_nonzero_of_one_le",
            "pow_successor_pair_mul",
            "mul_left_cancel_nonzero",
            "mul_assoc",
        ),
        "body": (6, 59, 72, 32, 72, 71, 0),
        "closure": (9_854, 69, 1_855, 1_920, 66),
    },
    "prime_nondivisor_mul": {
        "length": 456,
        "sha256": "f1950ba21ba465ab263a9788abfdaf46dec2d234613142e4661daa115ca460ec",
        "dependencies": ("euclid_prime_dvd_product",),
        "body": (1, 19, 23, 15, 23, 22, 0),
        "closure": (5_405, 56, 1_829, 1_941, 113),
    },
    "power_valuation_exact_cofactor": {
        "length": 12_821,
        "sha256": "52ad2dcbb6081c8f9a5380f905c5427c2a1168219875f958bdb9c14065ea6c44",
        "dependencies": (
            "power_valuation_selected_and_successor_not_divides",
            "power_divides_successor_of_cofactor",
        ),
        "body": (2, 42, 67, 26, 67, 66, 0),
        "closure": (72_980, 91, 6_301, 6_576, 276),
    },
    "power_valuation_mul_successor_not_divides": {
        "length": 22_061,
        "sha256": "901e81718280314d7721bbae7ddede7b1f9995a78e6c80b696347d12d2b9e4a9",
        "dependencies": (
            "power_valuation_exact_cofactor",
            "pow_exists",
            "pow_add",
            "mul_shuffle_four",
            "prime_nondivisor_mul",
            "prime_power_successor_cancel_cofactor",
        ),
        "body": (6, 87, 112, 41, 112, 111, 0),
        "closure": (155_308, 92, 6_933, 7_238, 306),
    },
    "power_valuation_mul_lower": {
        "length": 27_748,
        "sha256": "25a7880e19a3694c80eba908f2af9e8e0bb827c380227e3468d8302af7fd32f9",
        "dependencies": (
            "power_valuation_power_divides",
            "power_divides_add_mul",
            "mul_ne_zero",
            "prime_power_divides_exponent_le_value",
            "power_valuation_dominates",
        ),
        "body": (5, 59, 90, 30, 90, 89, 0),
        "closure": (74_676, 91, 6_351, 6_633, 283),
    },
    "power_valuation_mul_upper": {
        "length": 27_748,
        "sha256": "b6e66d62b853f86becf7f4a9ded9633e55acaf1821cad08f3202b8e6f001185e",
        "dependencies": (
            "le_or_lt",
            "power_valuation_power_divides",
            "power_divides_exponent_antitone",
            "power_valuation_mul_successor_not_divides",
        ),
        "body": (4, 45, 53, 30, 53, 52, 0),
        "closure": (222_259, 96, 7_094, 7_404, 311),
    },
    "prime_power_valuation_mul": {
        "length": 27_676,
        "sha256": "6fd025a8b94441961ffc3bdf7820ba071ac5bf0ac9a638244392fbc73af7844b",
        "dependencies": (
            "power_valuation_mul_lower",
            "power_valuation_mul_upper",
            "le_antisymm",
        ),
        "body": (3, 45, 58, 30, 58, 57, 0),
        "closure": (297_211, 98, 7_438, 7_758, 321),
    },
}


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    return (
        *make_bertrand_power_order_candidate_theorems(TheoremSpec),
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec),
        *make_bertrand_power_valuation_candidate_theorems(TheoremSpec),
        *make_bertrand_power_valuation_law_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_power_divisibility_candidate_theorems(TheoremSpec)


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
    return replace(
        certificate,
        body=_mutate_direct_cut(certificate.body, index - 1),
    )


def test_power_divisibility_factory_is_frozen_native_isolated_topological() -> None:
    specs = _specs()
    assert tuple(item.name for item in specs) == tuple(EXPECTED)
    assert make_bertrand_power_divisibility_candidate_theorems(TheoremSpec) == specs
    public = _specs_by_name()
    assert not (set(EXPECTED) & set(public))

    available = set(public) | {item.name for item in _prior_specs()}
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
                "PVal(",
                "Prime(",
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


def test_power_divisibility_bodies_kernel_check_with_exact_receipts() -> None:
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


def test_power_divisibility_rejects_false_contracts_and_every_removed_edge() -> None:
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


def test_power_divisibility_empty_context_closures_and_cuts_are_checked() -> None:
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


def _valuation(prime: int, value: int) -> int:
    assert prime >= 2 and value > 0
    exponent = 0
    while value % (prime ** (exponent + 1)) == 0:
        exponent += 1
    return exponent


def test_power_divisibility_semantics_match_standard_naturals() -> None:
    for a in range(6):
        for b in range(6):
            for c in range(6):
                for d in range(6):
                    assert (a * b) * (c * d) == (a * c) * (b * d)

    for prime in (2, 3, 5, 7):
        for value in range(1, 81):
            valuation = _valuation(prime, value)
            cofactor = value // (prime**valuation)
            assert value == (prime**valuation) * cofactor
            assert cofactor != 0
            assert cofactor % prime != 0

            for lower in range(valuation + 1):
                assert value % (prime**lower) == 0

        for left in range(1, 41):
            for right in range(1, 41):
                left_valuation = _valuation(prime, left)
                right_valuation = _valuation(prime, right)
                product_valuation = _valuation(prime, left * right)
                assert product_valuation == left_valuation + right_valuation
                assert (
                    left * right
                ) % (prime ** (left_valuation + right_valuation)) == 0
                assert (
                    left * right
                ) % (prime ** (left_valuation + right_valuation + 1)) != 0
