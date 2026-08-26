"""Focused native-body audit for the canonical-remainder congruence bridge."""

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
from peano_lab.library.ha_canonical_congruence_candidate import (
    balanced_mod_eq,
    make_ha_canonical_congruence_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NAME = "canonical_remainders_characterize_mod_eq"
EXPECTED_STATEMENT = (
    "forall m a b r s. (((exists hcr_quotient_left. a = m * "
    "hcr_quotient_left + r) /\\ exists hcr_gap_left. hcr_gap_left + S r = m)) "
    "-> (((exists hcr_quotient_right. b = m * hcr_quotient_right + s) /\\ "
    "exists hcr_gap_right. hcr_gap_right + S s = m)) -> (((exists "
    "hcc_mod_left_source hcc_mod_right_source. a + m * hcc_mod_left_source = "
    "b + m * hcc_mod_right_source) -> r = s) /\\ (r = s -> (exists "
    "hcc_mod_left_result hcc_mod_right_result. a + m * hcc_mod_left_result = "
    "b + m * hcc_mod_right_result)))"
)
EXPECTED_STATEMENT_SHA256 = (
    "c0fd6329ca9ec05b406a558920dfc49926e8e8fedb1e90fc1afcd698aa436f7f"
)
EXPECTED_DEPENDENCIES = (
    "mul_comm",
    "remainder_decomposition_to_mod_eq",
    "mod_eq_symm",
    "mod_eq_trans",
    "mod_eq_bounded_unique",
)
EXPECTED_BODY_RECEIPT = (5, 83, 118, 28, 118, 117, 0)


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_canonical_congruence_candidate_theorems(TheoremSpec)


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _curried_target(item: TheoremSpec, statement: str | None = None):
    target = _closed_formula(item.statement if statement is None else statement)
    core = _specs_by_name()
    for dependency_name in reversed(item.dependencies):
        target = Imp(_closed_formula(core[dependency_name].statement), target)
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


def test_canonical_congruence_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_canonical_congruence_candidate_theorems(TheoremSpec)

    assert second == first
    assert len(first) == 1
    item = first[0]
    assert item.name == EXPECTED_NAME
    assert item.statement == EXPECTED_STATEMENT
    assert sha256(item.statement.encode()).hexdigest() == EXPECTED_STATEMENT_SHA256
    assert item.dependencies == EXPECTED_DEPENDENCIES
    assert _specs_by_name()[item.name] == item
    assert all(not name.startswith("canonical_remainder_") for name in item.dependencies)


def test_balanced_mod_eq_surface_is_hygienic_and_expanded() -> None:
    left = balanced_mod_eq("m", "a", "b", tag="alpha_left")
    right = balanced_mod_eq("m", "a", "b", tag="alpha_right")

    assert left != right
    assert parse_formula(left) == parse_formula(right)
    _, free_names = parse_formula_with_names(left)
    assert set(free_names) == {"m", "a", "b"}
    assert "exists hcc_mod_left_alpha_left hcc_mod_right_alpha_left" in left
    assert "a + m * hcc_mod_left_alpha_left" in left
    assert all(token not in left for token in ("ModEq(", "%", "<", "<="))
    assert parse_formula_in_context(left, ["m", "a", "b"]) == (
        parse_defined_formula_in_context("ModEq(m,a,b)", ["m", "a", "b"])
    )

    with pytest.raises(ValueError, match="Peano identifier"):
        balanced_mod_eq("m + 1", "a", "b", tag="bad_term")
    with pytest.raises(ValueError, match="binder tag"):
        balanced_mod_eq("m", "a", "b", tag="bad tag")
    with pytest.raises(ValueError, match="captures an argument"):
        balanced_mod_eq(
            "hcc_mod_left_capture", "a", "b", tag="capture"
        )


def test_canonical_congruence_contract_is_closed_base_ha_without_extra_premise() -> None:
    (item,) = _candidate_specs()
    formula, free_names = parse_formula_with_names(item.statement)

    assert not free_names
    assert formula == parse_formula(item.statement)
    assert formula == _closed_formula(item.statement)
    assert all(
        token not in item.statement
        for token in (
            "Rem(",
            "ModEq(",
            "DivRem(",
            "%",
            "<",
            "<=",
            "<->",
            "exists unique",
        )
    )
    assert "~(m = 0)" not in item.statement
    assert item.statement.count("hcr_gap_") == 4
    assert item.statement.count("-> r = s") == 1
    assert item.statement.count("r = s ->") == 1


def test_canonical_congruence_body_is_constructive_exact_and_mutation_sensitive() -> None:
    (item,) = _candidate_specs()
    (receipt,) = replay_candidate_bodies((item,), core=dict(_specs_by_name()))
    observed = (
        receipt.dependency_count,
        receipt.command_count,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
    )
    assert observed == EXPECTED_BODY_RECEIPT

    automation = {"auto", "compact_arith", "norm_num", "ring", "simp", "use"}
    assert all(command.split(maxsplit=1)[0] not in automation for command in item.script)
    assert all(
        "DNE" not in command and "classical" not in command and "sorry" not in command
        for command in item.script
    )

    certificate, target = _body_certificate(item)
    assert check((), certificate, target)
    assert not any(type(node) is DNE for node in _walk(certificate))

    mutated_statement = item.statement.replace(
        "-> r = s) /\\ (r = s ->",
        "-> S r = s) /\\ (r = s ->",
        1,
    )
    assert mutated_statement != item.statement
    assert not check((), certificate, _curried_target(item, mutated_statement))
