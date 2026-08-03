"""Focused native-body audit for the canonical modular-inverse package."""

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
    make_ha_canonical_remainder_candidate_theorems,
)
from peano_lab.library.ha_modular_inverse_candidate import (
    bounded_modular_inverse,
    coprime,
    make_ha_modular_inverse_candidate_theorems,
    modular_inverse,
    strictly_below,
    unique_bounded_modular_inverse,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)
from peano_lab.library.wilson_inverse_point_candidate import (
    make_wilson_inverse_point_candidate_theorems,
)


EXPECTED_NAMES = (
    "coprime_bounded_mod_inverse",
    "mod_inverse_implies_coprime",
    "coprime_iff_unique_bounded_mod_inverse",
)
EXPECTED_DEPENDENCIES = {
    "coprime_bounded_mod_inverse": (
        "canonical_remainder_exists",
        "coprime_mod_inverse",
        "mul_comm",
        "remainder_decomposition_to_mod_eq",
        "mod_eq_mul_left",
        "mod_eq_symm",
        "mod_eq_trans",
    ),
    "mod_inverse_implies_coprime": (
        "common_divisor_divides_balanced_result",
        "zero_add",
        "divisor_one",
    ),
    "coprime_iff_unique_bounded_mod_inverse": (
        "coprime_bounded_mod_inverse",
        "bounded_mod_inverse_unique",
        "mod_inverse_implies_coprime",
    ),
}
EXPECTED_STATEMENT_SHA256 = {
    "coprime_bounded_mod_inverse":
        "84b14ceae7ab398b01e4b2033fd192110eef89ab6f921aeecb0c24eac424c3e8",
    "mod_inverse_implies_coprime":
        "e43d577e91195ee611ede2e8e3ad6511db34b1d45a22eb12d6b37b09f708d905",
    "coprime_iff_unique_bounded_mod_inverse":
        "213e325ff123d568d2faa49a8314bcf075069d5b7b2b256a0925c49b5ae915eb",
}
EXPECTED_BODY_RECEIPTS = {
    "coprime_bounded_mod_inverse": (7, 61, 70, 28, 70, 69, 0),
    "mod_inverse_implies_coprime": (3, 36, 43, 25, 43, 42, 0),
    "coprime_iff_unique_bounded_mod_inverse": (3, 37, 49, 22, 49, 48, 0),
}


@lru_cache(maxsize=1)
def _candidate_specs() -> tuple[TheoremSpec, ...]:
    return make_ha_modular_inverse_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def _external_candidate_specs() -> dict[str, TheoremSpec]:
    canonical = {
        item.name: item
        for item in make_ha_canonical_remainder_candidate_theorems(TheoremSpec)
        if item.name == "canonical_remainder_exists"
    }
    wilson = {
        item.name: item
        for item in make_wilson_inverse_point_candidate_theorems(TheoremSpec)
        if item.name == "bounded_mod_inverse_unique"
    }
    assert tuple(canonical) == ("canonical_remainder_exists",)
    assert tuple(wilson) == ("bounded_mod_inverse_unique",)
    return canonical | wilson


def _body_core() -> dict[str, TheoremSpec]:
    return dict(_specs_by_name()) | _external_candidate_specs()


def _walk(proof: Proof):
    yield proof
    for item in fields(proof):
        child = getattr(proof, item.name)
        if isinstance(child, Proof):
            yield from _walk(child)


def _curried_target(item: TheoremSpec, statement: str | None = None):
    available = _body_core() | {
        candidate.name: candidate for candidate in _candidate_specs()
    }
    target = _closed_formula(item.statement if statement is None else statement)
    for dependency_name in reversed(item.dependencies):
        target = Imp(_closed_formula(available[dependency_name].statement), target)
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


def test_modular_inverse_factory_is_exact_ordered_and_isolated() -> None:
    first = _candidate_specs()
    second = make_ha_modular_inverse_candidate_theorems(TheoremSpec)

    assert second == first
    assert tuple(item.name for item in first) == EXPECTED_NAMES
    assert {item.name: item.dependencies for item in first} == EXPECTED_DEPENDENCIES
    assert {
        item.name: sha256(item.statement.encode()).hexdigest() for item in first
    } == EXPECTED_STATEMENT_SHA256

    public = _specs_by_name()
    assert all(public[item.name] == item for item in first)
    assert public["canonical_remainder_exists"] == _external_candidate_specs()[
        "canonical_remainder_exists"
    ]
    assert public["bounded_mod_inverse_unique"] == _external_candidate_specs()[
        "bounded_mod_inverse_unique"
    ]
    assert "division_remainder_exists" not in first[0].dependencies
    assert "canonical_remainder_exists" in first[0].dependencies


def test_modular_inverse_surfaces_are_hygienic_and_expanded() -> None:
    surfaces = (
        lambda tag: strictly_below("r", "m", tag=tag),
        lambda tag: coprime("a", "m", tag=tag),
        lambda tag: modular_inverse("a", "m", "r", tag=tag),
        lambda tag: bounded_modular_inverse("a", "m", "r", tag=tag),
        lambda tag: unique_bounded_modular_inverse("a", "m", tag=tag),
    )
    expected_free_names = (
        {"r", "m"},
        {"a", "m"},
        {"a", "m", "r"},
        {"a", "m", "r"},
        {"a", "m"},
    )
    for build, free_names in zip(surfaces, expected_free_names, strict=True):
        left = build("alpha_left")
        right = build("alpha_right")
        assert left != right
        assert parse_formula(left) == parse_formula(right)
        _, observed_free_names = parse_formula_with_names(left)
        assert set(observed_free_names) == free_names
        assert all(
            token not in left
            for token in (
                "Coprime(",
                "ModEq(",
                "ModInv(",
                "Unique(",
                "%",
                "<",
                "<=",
                "exists unique",
            )
        )

    assert parse_formula_in_context(
        strictly_below("r", "m", tag="defined_lt"), ["r", "m"]
    ) == (
        parse_defined_formula_in_context("Lt(r,m)", ["r", "m"])
    )
    assert parse_formula_in_context(
        coprime("a", "m", tag="defined_coprime"), ["a", "m"]
    ) == (
        parse_defined_formula_in_context("Coprime(a,m)", ["a", "m"])
    )
    assert parse_formula_in_context(
        modular_inverse("a", "m", "r", tag="defined_mod_eq"),
        ["a", "m", "r"],
    ) == parse_defined_formula_in_context(
        "ModEq(m,a * r,1)", ["a", "m", "r"]
    )

    with pytest.raises(ValueError, match="Peano identifier"):
        modular_inverse("a + 1", "m", "r", tag="bad_term")
    with pytest.raises(ValueError, match="binder tag"):
        unique_bounded_modular_inverse("a", "m", tag="bad tag")
    with pytest.raises(ValueError, match="captures an argument"):
        strictly_below("hmi_gap_capture", "m", tag="capture")
    with pytest.raises(ValueError, match="captures an argument"):
        modular_inverse("hmi_left_offset_capture", "m", "r", tag="capture")
    with pytest.raises(ValueError, match="captures an argument"):
        unique_bounded_modular_inverse("hmi_solution_capture", "m", tag="capture")


def test_modular_inverse_contracts_are_closed_base_ha_formulas() -> None:
    for item in _candidate_specs():
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == parse_formula(item.statement)
        assert formula == _closed_formula(item.statement)
        assert all(
            token not in item.statement
            for token in (
                "Coprime(",
                "ModEq(",
                "ModInv(",
                "Unique(",
                "%",
                "<",
                "<=",
                "exists unique",
            )
        )

    converse = _candidate_specs()[1].statement
    assert "~(m = 0)" not in converse
    package = _candidate_specs()[2].statement
    assert package.startswith("forall a m. ~(m = 0) ->")
    assert "forall hmi_comparison_package_result." in package


def test_modular_inverse_bodies_are_constructive_exact_and_mutation_sensitive() -> None:
    receipts = replay_candidate_bodies(_candidate_specs(), core=_body_core())
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
    assert all(
        not command.startswith(("auto", "compact_arith", "norm_num", "ring", "simp"))
        for command in commands
    )
    assert all("DNE" not in command and "classical" not in command for command in commands)
    assert all("sorry" not in command for command in commands)

    mutations = {
        "coprime_bounded_mod_inverse": lambda statement: statement.replace(
            "hmi_gap_result_bound + S r = m",
            "hmi_gap_result_bound + S r = S m",
        ),
        "mod_inverse_implies_coprime": lambda statement: statement.replace(
            "hmi_divisor_converse_result = 1",
            "hmi_divisor_converse_result = 0",
        ),
        "coprime_iff_unique_bounded_mod_inverse": lambda statement: statement.replace(
            "hmi_comparison_package_result = hmi_solution_package_result",
            "S hmi_comparison_package_result = hmi_solution_package_result",
        ),
    }
    for item in _candidate_specs():
        certificate, target = _body_certificate(item)
        assert check((), certificate, target)
        assert not any(type(node) is DNE for node in _walk(certificate))
        mutated_statement = mutations[item.name](item.statement)
        assert mutated_statement != item.statement
        assert not check((), certificate, _curried_target(item, mutated_statement))
