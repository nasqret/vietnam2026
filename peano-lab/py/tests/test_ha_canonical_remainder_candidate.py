"""Focused native-body audit for the canonical remainder interface."""

from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.engine.state import start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import (
    Imp,
    parse_formula,
    parse_formula_in_context,
    parse_formula_with_names,
)
from peano_lab.kernel.proofs import DNE, Proof
from peano_lab.library.candidate_validation import replay_candidate_bodies
from peano_lab.library.defined_syntax import parse_defined_formula_in_context
from peano_lab.library.ha_canonical_remainder_candidate import (
    canonical_remainder,
    make_ha_canonical_remainder_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAMES = (
    "canonical_remainder_exists",
    "canonical_remainder_functional",
    "canonical_remainder_zero_impossible",
    "canonical_remainder_exists_unique",
)
EXPECTED_DEPENDENCIES = {
    "canonical_remainder_exists": ("division_remainder_exists",),
    "canonical_remainder_functional": ("division_remainder_unique",),
    "canonical_remainder_zero_impossible": ("succ_ne_zero",),
    "canonical_remainder_exists_unique": (
        "canonical_remainder_exists",
        "canonical_remainder_functional",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "canonical_remainder_exists":
        "a2b6494d6a1369a763858443ba842e1602874c81f1c2b549a8b82ed135f81cf1",
    "canonical_remainder_functional":
        "018a8e4f76080da565e2db4f36964ded346bfa8b5c75b295db9ac9bf18c5b418",
    "canonical_remainder_zero_impossible":
        "d6056b5b8107b48a1d1fed6068cfeee3dcc7e73cbd35982f7ce278e6eb3bfd6b",
    "canonical_remainder_exists_unique":
        "e542ed4a706554b52c8e7263031f88a8a74f579061f2b5a782b42c86d7738919",
}
EXPECTED_BODY_RECEIPTS = {
    "canonical_remainder_exists": (1, 16, 19, 11, 19, 18, 0),
    "canonical_remainder_functional": (1, 24, 31, 21, 31, 30, 0),
    "canonical_remainder_zero_impossible": (1, 16, 20, 13, 20, 19, 0),
    "canonical_remainder_exists_unique": (2, 21, 25, 17, 25, 24, 0),
}


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_canonical_remainder_candidate_theorems(TheoremSpec)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _curried_target(item: TheoremSpec, statement: str | None = None):
    core = _specs_by_name()
    local = {candidate.name: candidate for candidate in _candidate_specs()}
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency_name in reversed(item.dependencies):
        dependency = local.get(dependency_name) or core[dependency_name]
        target = Imp(_closed_formula(dependency.statement), target)
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


def test_canonical_remainder_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_canonical_remainder_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256
    public = _specs_by_name()
    assert all(public[item.name] == item for item in first)


def test_canonical_remainder_surface_is_hygienic_and_expanded() -> None:
    left = canonical_remainder("m", "n", "r", tag="alpha_left")
    right = canonical_remainder("m", "n", "r", tag="alpha_right")

    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"m", "n", "r"}
    assert "exists hcr_quotient_alpha_left" in left
    assert "exists hcr_gap_alpha_left" in left
    assert "hcr_gap_alpha_left + S r = m" in left
    assert all(token not in left for token in ("Rem(", "%", "<", "<="))
    assert parse_formula_in_context(left, ["m", "n", "r"]) == (
        parse_defined_formula_in_context(
            "(exists q. n = m * q + r) /\\ Lt(r,m)", ["m", "n", "r"]
        )
    )

    with pytest.raises(ValueError, match="Peano identifier"):
        canonical_remainder("m + 1", "n", "r", tag="bad_term")
    with pytest.raises(ValueError, match="binder tag"):
        canonical_remainder("m", "n", "r", tag="bad tag")
    with pytest.raises(ValueError, match="captures an argument"):
        canonical_remainder(
            "hcr_quotient_capture", "n", "r", tag="capture"
        )


def test_canonical_remainder_contracts_are_closed_base_ha_formulas() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in ("Rem(", "DivRem(", "%", "<", "<=", "exists unique")
        )

    packaged = _candidate_specs()[-1].statement
    assert "forall s." in packaged
    assert packaged.endswith("-> s = r)")


def test_canonical_remainder_bodies_are_constructive_exact_and_mutation_sensitive() -> None:
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

    commands = tuple(command for item in _candidate_specs() for command in item.script)
    assert all(not command.startswith(("auto", "ring")) for command in commands)
    assert all("DNE" not in command and "classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)

    mutations = {
        "canonical_remainder_exists": lambda statement: statement.replace(
            "hcr_gap_result + S r = m",
            "hcr_gap_result + S r = S m",
        ),
        "canonical_remainder_functional": lambda statement: statement.removesuffix(
            "r = s"
        ) + "S r = s",
        "canonical_remainder_zero_impossible": lambda statement: statement.replace(
            "hcr_gap_zero_impossible + S r = m",
            "hcr_gap_zero_impossible + S r = S m",
        ),
        "canonical_remainder_exists_unique": lambda statement: statement.replace(
            "-> s = r)",
            "-> S s = r)",
        ),
    }
    for item in _candidate_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))
