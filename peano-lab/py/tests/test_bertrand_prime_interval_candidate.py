"""Strict-HA audit for the Bertrand B0 prime-interval candidates."""

from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import TacticError, apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula, parse_formula_with_names
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.bertrand_prime_interval_candidate import (
    make_bertrand_prime_interval_candidate_theorems,
    prime_free_open_closed_interval,
    prime_in_open_closed_interval,
    prime_interval_witness,
    prime_strictly_above,
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


EXPECTED_NAMES = (
    "prime_strictly_above_decidable",
    "bounded_prime_interval_search",
    "prime_interval_exclusion_refutes_witness",
    "bounded_prime_interval_decidable",
)
EXPECTED_DEPENDENCIES = {
    "prime_strictly_above_decidable": (
        "prime_decidable",
        "lt_trichotomy",
        "lt_to_le",
        "lt_not_le",
        "le_refl",
    ),
    "bounded_prime_interval_search": (
        "prime_nonzero",
        "le_zero",
        "prime_strictly_above_decidable",
        "le_refl",
        "le_succ",
        "le_eq_or_lt",
        "le_of_succ_le_succ",
    ),
    "prime_interval_exclusion_refutes_witness": (),
    "bounded_prime_interval_decidable": (
        "bounded_prime_interval_search",
        "prime_interval_exclusion_refutes_witness",
    ),
}
EXPECTED_CORE_BOUNDARY = (
    "prime_decidable",
    "lt_trichotomy",
    "lt_to_le",
    "lt_not_le",
    "le_refl",
    "prime_nonzero",
    "le_zero",
    "le_succ",
    "le_eq_or_lt",
    "le_of_succ_le_succ",
)
EXPECTED_STATEMENT_SHA256 = {
    "prime_strictly_above_decidable":
        "c4ea73b0a2dd5a7a05b1769194efad1f87ddf89bc698c458e2ba3ebdc8380593",
    "bounded_prime_interval_search":
        "d95615964e3c308b22103524e101cff76ac1af78d0987862c897a946ffab9f91",
    "prime_interval_exclusion_refutes_witness":
        "8e28fa9dd9b0b2b8a1d4c2284e1613368cd4485147890b1bb5bdeeca30b26905",
    "bounded_prime_interval_decidable":
        "ae76d2a6a668478f8b4c26e9c4fbfa171f6f8bca963ef97cb61d1f18fa543be2",
}
EXPECTED_STATEMENT_LENGTH = {
    "prime_strictly_above_decidable": 791,
    "bounded_prime_interval_search": 1_343,
    "prime_interval_exclusion_refutes_witness": 1_344,
    "bounded_prime_interval_decidable": 1_407,
}
EXPECTED_SCRIPT_REPR_SHA256 = {
    "prime_strictly_above_decidable":
        "eed39af7928988cd8c2f94eb2a0ef11dbbff03a8609d11eaf8111cdef6b2ca7f",
    "bounded_prime_interval_search":
        "b9e0caebf82a493648a382e9ca17f612d7297858eeee09ab33c3a161debfc251",
    "prime_interval_exclusion_refutes_witness":
        "255653bfc2915dcb6bbaf415b72732811e6835f13f8412e00994ddf9e41dd9e9",
    "bounded_prime_interval_decidable":
        "149ff483ca22b0dca903814dfb07474a10cfeb43d5da944f0332576fe02731c9",
}
EXPECTED_BODY_RECEIPTS = {
    "prime_strictly_above_decidable": (5, 38, 107, 33, 107, 106, 0),
    "bounded_prime_interval_search": (7, 68, 95, 25, 95, 94, 0),
    "prime_interval_exclusion_refutes_witness": (0, 13, 33, 19, 33, 32, 0),
    "bounded_prime_interval_decidable": (2, 18, 19, 12, 19, 18, 0),
}
EXPECTED_CLOSED_RECEIPTS = {
    "prime_strictly_above_decidable": (
        2_492, 74, 1_717, 1_781, 65, 71,
        "e89710885e62ad4e572c97d5b0fdb9f759007324021e51a1d3f18303a41157db",
    ),
    "bounded_prime_interval_search": (
        2_844, 77, 1_812, 1_882, 71, 86,
        "a94723f509145a7f6a1cd108487ccd9170973c3a0ca1376688e213e3de2e8aa0",
    ),
    "prime_interval_exclusion_refutes_witness": (
        33, 19, 33, 32, 0, 0,
        "618d01281b7e21d2ad6e8993808150243a52a5a23deedd6e77c550954038ccbc",
    ),
    "bounded_prime_interval_decidable": (
        2_896, 78, 1_864, 1_934, 71, 88,
        "4d763a009dedd7d85ac229df0a88d9851b44bbeb30788c2a7f19f2fe55e14fe4",
    ),
}

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CATALOG_V2 = REPOSITORY_ROOT / "artifacts" / "peano-library" / "alpha" / "catalog-v2.json"


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_bertrand_prime_interval_candidate_theorems(TheoremSpec)


def _local_specs() -> dict[str, TheoremSpec]:
    return {item.name: item for item in _candidate_specs()}


def _dependency_formula(name: str) -> Formula:
    item = _local_specs().get(name) or _specs_by_name()[name]
    return _closed_formula(item.statement)


def _curried_target(
    item: TheoremSpec,
    *,
    statement: str | None = None,
    dependency_override: tuple[int, Formula] | None = None,
) -> Formula:
    dependencies = [_dependency_formula(name) for name in item.dependencies]
    if dependency_override is not None:
        index, formula = dependency_override
        dependencies[index] = formula
    target = _closed_formula(item.statement if statement is None else statement)
    for formula in reversed(dependencies):
        target = Imp(formula, target)
    return target


def _body_certificate(
    item: TheoremSpec,
    *,
    statement: str | None = None,
    dependency_override: tuple[int, Formula] | None = None,
) -> tuple[Proof, Formula]:
    target = _curried_target(
        item,
        statement=statement,
        dependency_override=dependency_override,
    )
    state = start(target)
    for dependency in item.dependencies:
        state = apply_tactic(state, "intro", dependency)
    for command in item.script:
        tactic, arguments = _primitive(command)
        state = apply_tactic(state, tactic, arguments)
    return checked_final(state, target), target


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


@lru_cache(maxsize=None)
def _closed_candidate(name: str) -> tuple[Formula, Proof]:
    public = _specs_by_name()
    if name in public:
        theorem = replay(name)
        return theorem.formula, theorem.certificate

    item = _local_specs()[name]
    certificate, _target = _body_certificate(item)
    body = certificate
    for _dependency in item.dependencies:
        assert type(body) is ImpIntro
        body = body.body

    formula = _closed_formula(item.statement)
    for dependency in reversed(item.dependencies):
        dependency_formula, dependency_proof = _closed_candidate(dependency)
        body = Cut(dependency_formula, formula, dependency_proof, body)
    assert check((), body, formula)
    return formula, body


def _replace_direct_cut_by_true(proof: Proof, index: int) -> Proof:
    assert type(proof) is Cut
    if index == 0:
        return replace(proof, proposition=Eq(Zero(), Zero()), lemma=EqRefl(Zero()))
    return replace(proof, body=_replace_direct_cut_by_true(proof.body, index - 1))


def _is_prime(value: int) -> bool:
    return value != 1 and all(
        left == 1 or right == 1
        for left in range(value + 1)
        for right in range(value + 1)
        if value == left * right
    )


def test_bertrand_b0_factory_is_exact_deterministic_and_isolated() -> None:
    specs = _candidate_specs()
    assert make_bertrand_prime_interval_candidate_theorems(TheoremSpec) == specs
    assert tuple(item.name for item in specs) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in specs} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in specs
    } == EXPECTED_STATEMENT_SHA256
    assert {item.name: len(item.statement) for item in specs} == EXPECTED_STATEMENT_LENGTH
    assert {
        item.name: sha256(repr(item.script).encode()).hexdigest() for item in specs
    } == EXPECTED_SCRIPT_REPR_SHA256

    public = _specs_by_name()
    assert all(item.name not in public for item in specs)
    positions = {item.name: index for index, item in enumerate(specs)}
    assert all(
        dependency not in positions or positions[dependency] < positions[item.name]
        for item in specs
        for dependency in item.dependencies
    )


def test_bertrand_b0_surfaces_are_hygienic_alpha_equivalent_and_native() -> None:
    interval = prime_in_open_closed_interval("l", "u", "p", tag="exact")
    witness = prime_interval_witness("l", "u", tag="exact")
    exclusion = prime_free_open_closed_interval("l", "u", tag="exact")
    assert interval.startswith("(((~(p = 1)")
    assert ") /\\ ((exists " in interval
    assert witness.startswith("exists bpi_value_exact.")
    assert exclusion.startswith("forall bpi_value_exact.")
    assert ") -> ~(" in exclusion

    alpha_pairs = (
        (
            prime_strictly_above("l", "p", tag="alpha_left"),
            prime_strictly_above("l", "p", tag="alpha_right"),
        ),
        (
            prime_interval_witness("l", "u", tag="alpha_left"),
            prime_interval_witness("l", "u", tag="alpha_right"),
        ),
        (
            prime_free_open_closed_interval("l", "u", tag="alpha_left"),
            prime_free_open_closed_interval("l", "u", tag="alpha_right"),
        ),
    )
    for left, right in alpha_pairs:
        assert left != right
        assert parse_formula(left) == parse_formula(right)

    for surface, free in (
        (interval, {"l", "u", "p"}),
        (witness, {"l", "u"}),
        (exclusion, {"l", "u"}),
    ):
        _, names = parse_formula_with_names(surface)
        assert set(names) == free
        assert all(
            token not in surface
            for token in ("Prime(", "Lt(", "Le(", "<", "<=", "∣", "%", "^")
        )

    for bad in (
        lambda: prime_interval_witness("l + 1", "u", tag="bad_lower"),
        lambda: prime_interval_witness("l", "S u", tag="bad_upper"),
        lambda: prime_interval_witness("l", "u", tag="bad tag"),
    ):
        with pytest.raises(ValueError):
            bad()
    with pytest.raises(ValueError, match="captures an argument"):
        prime_interval_witness("bpi_value_capture", "u", tag="capture")


def test_bertrand_b0_contracts_are_closed_expanded_constructive_ha() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert item.script
        assert all("DNE" not in command for command in item.script)
        assert all(not command.startswith(("auto", "ring")) for command in item.script)
        assert all("sorry" not in command for command in item.script)
        assert all(
            token not in item.statement
            for token in ("Prime(", "Lt(", "Le(", "<", "<=", "∣", "%", "^")
        )


def test_bertrand_b0_core_boundary_is_stable_empty_context_checked_use() -> None:
    catalog = json.loads(CATALOG_V2.read_text())
    records = {item["name"]: item for item in catalog["theorems"]}
    public = _specs_by_name()
    assert all(name in public for name in EXPECTED_CORE_BOUNDARY)
    for name in EXPECTED_CORE_BOUNDARY:
        record = records[name]
        assert record["checked_use"] is True
        assert record["evidence_status"] == "stable_closed"
        assert record["empty_context_closure"]["status"] == "checked"


def test_bertrand_b0_dependency_curried_bodies_kernel_check_exactly() -> None:
    receipts = replay_candidate_bodies(_candidate_specs(), core=dict(_specs_by_name()))
    observed = {
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
    }
    assert observed == EXPECTED_BODY_RECEIPTS

    for item in _candidate_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))


def test_bertrand_b0_every_declared_dependency_is_live() -> None:
    true_formula = Eq(Zero(), Zero())
    for item in _candidate_specs():
        for index, _dependency in enumerate(item.dependencies):
            with pytest.raises(TacticError):
                _body_certificate(
                    item,
                    dependency_override=(index, true_formula),
                )


def test_bertrand_b0_empty_context_closure_and_direct_cut_liveness() -> None:
    for item in _candidate_specs():
        formula, certificate = _closed_candidate(item.name)
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        observed = (
            nodes,
            depth,
            objects,
            edges,
            reused,
            sum(type(node) is Cut for node in _walk(certificate)),
            sha256(repr(certificate).encode()).hexdigest(),
        )
        assert observed == EXPECTED_CLOSED_RECEIPTS[item.name]
        assert check((), certificate, formula)
        assert not any(type(node) is DNE for node in _walk(certificate))

        for index, _dependency in enumerate(item.dependencies):
            mutated = _replace_direct_cut_by_true(certificate, index)
            assert not check((), mutated, formula)


def test_bertrand_b0_rejects_semantically_false_contract_mutations() -> None:
    specs = _candidate_specs()
    above = prime_strictly_above("l", "p", tag="above_decidable")
    witness_search = prime_interval_witness("l", "u", tag="search_witness")
    exclusion_search = prime_free_open_closed_interval(
        "l", "u", tag="search_exclusion"
    )
    witness_refute = prime_interval_witness("l", "u", tag="refute_witness")
    exclusion_refute = prime_free_open_closed_interval(
        "l", "u", tag="refute_exclusion"
    )
    witness_decide = prime_interval_witness("l", "u", tag="decide_witness")
    mutations = {
        EXPECTED_NAMES[0]: f"forall l p. ({above}) /\\ ~({above})",
        EXPECTED_NAMES[1]: (
            f"forall l u. ({witness_search}) /\\ ({exclusion_search})"
        ),
        EXPECTED_NAMES[2]: (
            f"forall l u. ({exclusion_refute}) -> ({witness_refute})"
        ),
        EXPECTED_NAMES[3]: (
            f"forall l u. ({witness_decide}) /\\ ~({witness_decide})"
        ),
    }
    for index, item in enumerate(specs):
        mutated_statement = mutations[item.name]
        _, free_names = parse_formula_with_names(mutated_statement)
        assert not free_names
        mutated = replace(item, statement=mutated_statement)
        candidate_stack = specs[:index] + (mutated,) + specs[index + 1 :]
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies(candidate_stack, core=dict(_specs_by_name()))


def test_bertrand_b0_intended_interval_semantics_on_small_naturals() -> None:
    for lower in range(13):
        for upper in range(13):
            witnesses = [
                value
                for value in range(upper + 1)
                if _is_prime(value) and lower < value <= upper
            ]
            explicit_exclusion = all(
                not _is_prime(value)
                for value in range(upper + 1)
                if lower < value <= upper
            )
            assert bool(witnesses) != explicit_exclusion
