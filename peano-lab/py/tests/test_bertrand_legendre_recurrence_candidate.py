"""Kernel, mutation, capacity, and semantic audit for Legendre recurrence."""

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
from peano_lab.library.bertrand_legendre_recurrence_candidate import (
    make_bertrand_legendre_recurrence_candidate_theorems,
)
from peano_lab.library.bertrand_legendre_successor_candidate import (
    make_bertrand_legendre_successor_candidate_theorems,
)
from peano_lab.library.bertrand_legendre_sum_candidate import (
    make_bertrand_legendre_sum_candidate_theorems,
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
from peano_lab.library.finite_sum_pointwise_add_candidate import (
    make_finite_sum_pointwise_add_candidate_theorems,
)
from peano_lab.library.finite_fold_surface import sum_relation
from peano_lab.library.finite_sum_theorems import _at, _sum_relation_terms
from peano_lab.library.finite_sum_transport_candidate import (
    make_finite_sum_transport_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


EXPECTED = {
    "beta_sum_succ_last_zero": {
        "length": 4_722,
        "sha256": "e24868a0d2c58178f11b2f626ca4ec7ba14b29d49007271b052ab2ec899df87c",
        "dependencies": ("beta_sum_succ_decompose", "beta_at_unique"),
        "body": (2, 34, 63, 24, 62, 62, 1),
        "closure": (2_441, 63, 846, 886, 41),
    },
    "prime_power_quotient_prefix_last_zero": {
        "length": 4_798,
        "sha256": "b30b3c885267d588c07108989cad9747fa33fc1592edac75c740c7c31c46977e",
        "dependencies": (
            "prime_power_quotient_tail_zero",
            "division_remainder_unique",
            "zero_add",
        ),
        "body": (3, 42, 105, 26, 105, 104, 0),
        "closure": (8_329, 73, 1_580, 1_641, 62),
    },
    "legendre_sum_zero_extended_prefix": {
        "length": 14_493,
        "sha256": "4ee30bba2c2538f1c9b1807a18c565d2937d17a051c1baea8e1cf224ba50809a",
        "dependencies": (
            "prime_power_quotient_prefix_exists",
            "prime_power_quotient_prefix_last_zero",
            "beta_sum_exists",
            "beta_sum_succ_last_zero",
            "le_succ",
            "legendre_sum_functional",
        ),
        "body": (6, 65, 110, 32, 109, 109, 1),
        "closure": (141_388, 92, 7_212, 7_516, 305),
    },
    "initial_segment_prefix_sum_exists": {
        "length": 2_862,
        "sha256": "4560b69d5200799f2720499b4516bd7f59687dafbe01924dcfc31d97229aa38b",
        "dependencies": (
            "eisenstein_initial_segment_prefix_exists",
            "eisenstein_initial_segment_bit_count_exact",
        ),
        "body": (2, 23, 25, 18, 25, 24, 0),
        "closure": (70_639, 91, 5_735, 5_998, 264),
    },
    "prime_legendre_sum_succ": {
        "length": 26_345,
        "sha256": "0ea3639db84cfdebc2bccbb0fc9bd61d225dc5c864a25a7a921ba78b97edf2d8",
        "dependencies": (
            "legendre_sum_zero_extended_prefix",
            "initial_segment_prefix_sum_exists",
            "power_quotient_successor_pointwise_add",
            "beta_sum_pointwise_add",
        ),
        "body": (4, 66, 83, 36, 83, 82, 0),
        "closure": (296_732, 98, 9_307, 9_675, 369),
    },
}


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    # Every body-only prerequisite is present as a concrete local theorem.
    # In particular, closure never treats an initial-segment constructor or
    # beta_sum_pointwise_add as authority merely because its name is known.
    return (
        *make_bertrand_power_order_candidate_theorems(TheoremSpec),
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec),
        *make_bertrand_power_valuation_candidate_theorems(TheoremSpec),
        *make_bertrand_power_valuation_law_candidate_theorems(TheoremSpec),
        *make_bertrand_power_divisibility_candidate_theorems(TheoremSpec),
        *make_bertrand_legendre_valuation_bridge_candidate_theorems(
            TheoremSpec
        ),
        *make_finite_sum_transport_candidate_theorems(TheoremSpec),
        *make_bertrand_legendre_sum_candidate_theorems(TheoremSpec),
        *make_eisenstein_initial_segment_count_candidate_theorems(TheoremSpec),
        *make_finite_sum_pointwise_add_candidate_theorems(TheoremSpec),
        *make_bertrand_legendre_successor_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_legendre_recurrence_candidate_theorems(TheoremSpec)


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


def test_recurrence_factory_is_frozen_native_isolated_and_topological() -> None:
    specs = _specs()
    assert tuple(item.name for item in specs) == tuple(EXPECTED)
    assert make_bertrand_legendre_recurrence_candidate_theorems(
        TheoremSpec
    ) == specs
    assert not (set(EXPECTED) & set(_specs_by_name()))

    local = _local()
    public = _specs_by_name()
    body_only_support = {
        "eisenstein_initial_segment_indicator_choice",
        "eisenstein_initial_segment_prefix_extend",
        "eisenstein_initial_segment_prefix_exists",
        "eisenstein_initial_segment_prefix_all_bits",
        "eisenstein_initial_segment_decoded_choice",
        "beta_all_one_bit_count_exact",
        "eisenstein_initial_segment_bit_count_functional",
        "eisenstein_initial_segment_bit_count_exact",
        "beta_sum_pointwise_add",
    }
    assert body_only_support <= set(local)
    assert not (body_only_support & set(public))

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
                "BetaAt(",
                "Sum(",
                "Pow(",
                "PowDiv(",
                "PowerVal(",
                "PowerQuotPrefix(",
                "InitialSegment(",
                "LegendreSum(",
                "Prime(",
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


def test_recurrence_bodies_kernel_check_with_exact_receipts() -> None:
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


def test_recurrence_rejects_false_contracts_and_every_removed_edge() -> None:
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


def test_recurrence_rejects_zero_tail_and_sum_boundary_mutations() -> None:
    specs = {item.name: item for item in _specs()}

    drop = specs["beta_sum_succ_last_zero"]
    old_drop = sum_relation(
        "b", "c", "l", "n", tag="blrr_drop_predecessor"
    )
    new_drop = _sum_relation_terms(
        "b", "c", "l", "S n", tag="blrr_drop_predecessor"
    )
    changed_drop = drop.statement.replace(old_drop, new_drop, 1)

    tail = specs["prime_power_quotient_prefix_last_zero"]
    old_tail = _at("b", "c", "n", "0", tag="blrr_tail_zero")
    new_tail = _at("b", "c", "n", "1", tag="blrr_tail_zero")
    changed_tail = tail.statement.replace(old_tail, new_tail, 1)

    extended = specs["legendre_sum_zero_extended_prefix"]
    old_extended = _sum_relation_terms(
        "b", "c", "S n", "e", tag="blrr_extend_sum"
    )
    new_extended = _sum_relation_terms(
        "b", "c", "S n", "S e", tag="blrr_extend_sum"
    )
    changed_extended = extended.statement.replace(
        old_extended, new_extended, 1
    )

    initial = specs["initial_segment_prefix_sum_exists"]
    old_initial = sum_relation(
        "b", "c", "k", "q", tag="blrr_initial_sum"
    )
    new_initial = _sum_relation_terms(
        "b", "c", "k", "S q", tag="blrr_initial_sum"
    )
    changed_initial = initial.statement.replace(old_initial, new_initial, 1)

    successor = specs["prime_legendre_sum_succ"]
    changed_successor = successor.statement.removesuffix("g = e + f") + (
        "g = S (e + f)"
    )

    mutations = {
        drop.name: changed_drop,
        tail.name: changed_tail,
        extended.name: changed_extended,
        initial.name: changed_initial,
        successor.name: changed_successor,
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


def test_recurrence_empty_context_closures_and_every_direct_cut() -> None:
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
    assert direct_cut_mutations == 17


def _valuation(prime: int, value: int) -> int:
    exponent = 0
    while value % (prime ** (exponent + 1)) == 0:
        exponent += 1
    return exponent


def _legendre(prime: int, value: int) -> int:
    return sum(value // (prime**exponent) for exponent in range(1, value + 1))


def test_recurrence_semantics_match_standard_naturals() -> None:
    # These bounded computations are regression fixtures, never proof authority.
    for values in ((), (3,), (2, 5, 0), (7, 0, 0, 0)):
        assert sum((*values, 0)) == sum(values)

    for prime in (2, 3, 5, 7, 11):
        for n in range(80):
            assert n // (prime ** (n + 1)) == 0
            old_terms = [n // (prime**exponent) for exponent in range(1, n + 1)]
            assert sum((*old_terms, 0)) == _legendre(prime, n)

            valuation = _valuation(prime, n + 1)
            bits = [int(index + 1 <= valuation) for index in range(n + 1)]
            assert sum(bits) == valuation
            assert _legendre(prime, n + 1) == (
                _legendre(prime, n) + valuation
            )

    for length in range(20):
        for threshold in range(length + 1):
            bits = [int(index + 1 <= threshold) for index in range(length)]
            assert sum(bits) == threshold
