"""Kernel, closure, mutation, and semantic audit for finite Legendre sums."""

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
from peano_lab.library.bertrand_legendre_sum_candidate import (
    legendre_sum,
    make_bertrand_legendre_sum_candidate_theorems,
    power_quotient_prefix,
)
from peano_lab.library.bertrand_power_growth_candidate import (
    make_bertrand_power_growth_candidate_theorems,
)
from peano_lab.library.bertrand_power_order_candidate import (
    make_bertrand_power_order_candidate_theorems,
)
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.finite_fold_surface import beta_at
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
    "prime_power_quotient_prefix_exists": {
        "length": 3_996,
        "sha256": "d6d45e7f9ad602bb932055be2f4a32a9f294493032defc20a5aff293ae0fb446",
        "dependencies": (
            "add_eq_zero_right",
            "succ_ne_zero",
            "pow_exists",
            "prime_nonzero",
            "one_le_of_ne_zero",
            "pow_nonzero_of_one_le",
            "division_remainder_exists",
            "beta_prefix_extend",
            "finite_lt_succ_eq_or_lt",
        ),
        "body": (9, 109, 142, 41, 142, 141, 0),
        "closure": (93_562, 91, 5_491, 5_751, 261),
    },
    "power_quotient_prefix_transport": {
        "length": 10_069,
        "sha256": "5b6c0774bcdc14d0314914738a9c296e8087c7948c1c8e656cf89fbfce447268",
        "dependencies": (
            "beta_at_unique",
            "pow_functional",
            "division_remainder_unique",
        ),
        "body": (3, 72, 175, 39, 175, 174, 0),
        "closure": (4_855, 65, 1_286, 1_327, 42),
    },
    "prime_legendre_sum_exists": {
        "length": 6_657,
        "sha256": "1810e771379951eff3d54ad0ca40951ed5727a58547efc1460c12aa50f72487d",
        "dependencies": (
            "prime_power_quotient_prefix_exists",
            "beta_sum_exists",
        ),
        "body": (2, 23, 25, 13, 25, 24, 0),
        "closure": (124_078, 92, 5_725, 5_997, 273),
    },
    "legendre_sum_functional": {
        "length": 16_385,
        "sha256": "5609f810c39831c291f6676ebf93ec3bd52c2f1bc588a6b8478151c068403209",
        "dependencies": (
            "power_quotient_prefix_transport",
            "beta_sum_transport_prefix",
            "beta_sum_functional",
        ),
        "body": (3, 49, 62, 34, 62, 61, 0),
        "closure": (6_415, 66, 1_660, 1_704, 45),
    },
    "legendre_sum_zero": {
        "length": 6_301,
        "sha256": "3980bf0a90671e66282c846c07a6b7f3900198321380e6dd86a24772b1e10f5c",
        "dependencies": ("beta_sum_zero",),
        "body": (1, 16, 48, 26, 48, 47, 0),
        "closure": (1_219, 61, 790, 826, 37),
    },
}


@lru_cache(maxsize=1)
def _prior_specs() -> tuple[TheoremSpec, ...]:
    # The first two factories close ``pow_nonzero_of_one_le`` natively; the
    # last closes the body-only sum-transport prerequisite with no dependency.
    return (
        *make_bertrand_power_order_candidate_theorems(TheoremSpec),
        *make_bertrand_power_growth_candidate_theorems(TheoremSpec),
        *make_finite_sum_transport_candidate_theorems(TheoremSpec),
    )


@lru_cache(maxsize=1)
def _specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_legendre_sum_candidate_theorems(TheoremSpec)


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


def test_legendre_surface_is_hygienic_fully_expanded_and_topological() -> None:
    prefix = power_quotient_prefix("p", "n", "b", "c", "l", tag="surface")
    total = legendre_sum("p", "n", "e", tag="surface")
    for statement in (
        f"forall p n b c l. {prefix}",
        f"forall p n e. {total}",
    ):
        formula, free_names = parse_formula_with_names(statement)
        assert not free_names
        assert formula == _closed_formula(statement)
        assert all(
            marker not in statement
            for marker in (
                "PowerQuotPrefix(",
                "LegendreSum(",
                "Prime(",
                "Pow(",
                "DivRem(",
                "BetaAt(",
                "Sum(",
                "^",
                "%",
                "∣",
                "<=",
            )
        )

    with pytest.raises(ValueError, match="Peano identifier"):
        power_quotient_prefix("p", "S n", "b", "c", "l", tag="bad_term")
    with pytest.raises(ValueError, match="binder tag"):
        legendre_sum("p", "n", "e", tag="bad-tag")
    with pytest.raises(ValueError, match="captures"):
        power_quotient_prefix(
            "bls_index_capture", "n", "b", "c", "l", tag="capture"
        )
    with pytest.raises(ValueError, match="captures"):
        power_quotient_prefix(
            "bpvi_b_bls_nested_power", "n", "b", "c", "l", tag="nested"
        )
    with pytest.raises(ValueError, match="captures"):
        legendre_sum("bls_code_capture", "n", "e", tag="capture")
    with pytest.raises(ValueError, match="captures"):
        legendre_sum(
            "bpvi_b_bls_nested_prefix_power", "n", "e", tag="nested"
        )

    specs = _specs()
    assert tuple(item.name for item in specs) == tuple(EXPECTED)
    assert make_bertrand_legendre_sum_candidate_theorems(TheoremSpec) == specs
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
                "PowerQuotPrefix(",
                "LegendreSum(",
                "Prime(",
                "Pow(",
                "DivRem(",
                "BetaAt(",
                "Sum(",
                "^",
                "%",
                "∣",
                "<=",
            )
        )

    public = _specs_by_name()
    assert "beta_prefix_extend" in public
    assert "pow_nonzero_of_one_le" not in public
    assert "beta_sum_transport_prefix" not in public
    assert {"pow_nonzero_of_one_le", "beta_sum_transport_prefix"} <= set(_local())

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


def test_legendre_bodies_kernel_check_with_exact_receipts() -> None:
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


def test_legendre_rejects_false_contracts_and_every_removed_edge() -> None:
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


def test_legendre_rejects_boundary_mutations() -> None:
    specs = {item.name: item for item in _specs()}

    prefix = specs["prime_power_quotient_prefix_exists"]
    changed_prefix = prefix.statement.replace(
        "bls_gap_bls_exists_bound + S (bls_index_bls_exists) = (l)",
        "bls_gap_bls_exists_bound + S (bls_index_bls_exists) = (0)",
        1,
    )

    transport = specs["power_quotient_prefix_transport"]
    target_entry = beta_at("z", "d", "i", "q", tag="bls_transport_result")
    changed_entry = target_entry.replace("S (q)", "S (S q)", 1)
    transport_before, transport_after = transport.statement.rsplit(target_entry, 1)
    changed_transport = transport_before + changed_entry + transport_after

    existence = specs["prime_legendre_sum_exists"]
    changed_existence = existence.statement.replace(
        "-> exists e.", "-> exists e. e = 0 /\\", 1
    )

    mutations = {
        "prime_power_quotient_prefix_exists": changed_prefix,
        "power_quotient_prefix_transport": changed_transport,
        "prime_legendre_sum_exists": changed_existence,
        "legendre_sum_functional": specs["legendre_sum_functional"].statement.rsplit(
            "e = f", 1
        )[0]
        + "e = S f",
        "legendre_sum_zero": specs["legendre_sum_zero"].statement.rsplit(
            "e = 0", 1
        )[0]
        + "e = 1",
    }
    for name, statement in mutations.items():
        item = specs[name]
        assert statement != item.statement
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((replace(item, statement=statement),), core=_available())


def test_legendre_empty_context_closures_and_direct_cuts_are_checked() -> None:
    for prerequisite in ("pow_nonzero_of_one_le", "beta_sum_transport_prefix"):
        formula, certificate = _close(prerequisite)
        assert check((), certificate, formula)
        assert not any(type(node) is DNE for node in _walk_proof(certificate))

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


def test_legendre_semantics_match_standard_naturals_with_finite_stopping() -> None:
    for prime_value in (2, 3, 5, 7, 11):
        for n in range(16):
            quotients = tuple(
                n // (prime_value**exponent) for exponent in range(1, n + 1)
            )
            legendre_value = sum(quotients)
            factorial_value = factorial(n)
            valuation = sum(
                1
                for exponent in range(1, n + 1)
                if factorial_value % (prime_value**exponent) == 0
            )

            assert legendre_value == valuation
            assert n // (prime_value ** (n + 1)) == 0
            assert all(
                n // (prime_value**exponent) == 0
                for exponent in range(n + 1, n + 4)
            )
            if n == 0:
                assert quotients == ()
                assert legendre_value == 0
