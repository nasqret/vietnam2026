"""Original-kernel complete signed cofactor families and alternating finite folds."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import editions_v24 as v24
from peano_lab.library import matrix_cofactor_expansion_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.matrix_dot_product_candidate import (
    IntegerMatrix,
    certify_integer_determinant,
    integer_matrix,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "matrix_minor_four_code_exists",
    "matrix_minor_four_code_output_functional",
    "matrix_minor_four_code_components_injective",
    "signed_cofactor_minor_record_exists",
    "signed_cofactor_minor_record_projects_minor",
    "signed_cofactor_minor_prefix_empty",
    "signed_cofactor_minor_prefix_extend",
    "signed_cofactor_minor_prefix_exists_bounded",
    "signed_cofactor_minor_family_exists",
    "signed_cofactor_minor_family_entry_exists",
    "signed_cofactor_minor_family_entry_projects_minor",
    "signed_alternating_cofactor_term_exists",
    "signed_alternating_cofactor_term_functional",
    "signed_alternating_cofactor_term_even",
    "signed_alternating_cofactor_term_odd",
    "signed_alternating_cofactor_term_exists_unique",
    "signed_alternating_product_prefix_empty",
    "signed_alternating_product_prefix_extend",
    "signed_alternating_product_prefix_exists",
    "signed_alternating_product_prefix_restrict",
    "signed_alternating_product_prefix_exact_term",
    "signed_alternating_product_prefix_pointwise_functional",
    "signed_alternating_cofactor_fold_exists",
    "signed_alternating_cofactor_fold_functional",
    "signed_alternating_cofactor_fold_exists_unique",
    "signed_alternating_cofactor_fold_empty",
    "signed_matrix_first_row_components_exists",
    "signed_first_row_cofactor_fold_exists",
    "signed_matrix_cofactor_family_and_fold_exists",
)
EXPECTED_NAMES_SHA256 = (
    "87a9308cecf3d377fd03c6bf51b8d28c17c334a472deec98387419e6b7055675"
)
EXPECTED_PROOF_NODES = (
    6, 12, 99, 42, 29, 22, 72, 63, 38, 17, 37, 32, 137, 39, 39, 79, 27, 193,
    101, 34, 333, 138, 49, 290, 115, 67, 31, 50, 40,
)
EXPECTED_ROOTS = {
    "signed_cofactor_minor_family_exists": (
        "8486fcb74e3c32d6967e4ec4a3058c06ef7d2a6b031551e0722f73ce62b0355c"
    ),
    "signed_alternating_cofactor_fold_exists": (
        "ff2d10b22ea031df2a613a9d668cdeee3c52fef7f7ab635784f68164b2a4940d"
    ),
    "signed_alternating_cofactor_fold_exists_unique": (
        "cded0e0b36963f8d799d0b1a2d5a89b58ca00219d40e378bdd31cfc58addfbd5"
    ),
    "signed_first_row_cofactor_fold_exists": (
        "f39d7ee0acfd090d87e144b68d18ed7cb61aee9bc29dc9087c9b8f440974eb73"
    ),
    "signed_matrix_cofactor_family_and_fold_exists": (
        "1f013b934c7540f73e135257094d612345f43f3163b5ee7280dbe97f4f142d2a"
    ),
}


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_matrix_cofactor_expansion_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in v24.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def test_twenty_nine_cofactor_family_theorems_are_closed_fresh_and_ordered() -> None:
    actual = rows()
    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert sum(len(item.dependencies) for item in actual) == 51
    assert sum(len(item.script) for item in actual) == 1370
    available = set(core())
    for item in actual:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert item.name not in v24.ALPHA_EDITION.by_name
        assert set(item.dependencies) <= available
        assert not any(
            command in {"sorry", "admit"}
            or "DNE" in command
            or command.startswith("use ")
            for command in item.script
        )
        available.add(item.name)


def test_every_cofactor_family_body_passes_the_unchanged_original_kernel() -> None:
    actual = receipts()
    assert tuple(receipt.name for receipt in actual) == EXPECTED_NAMES
    assert tuple(receipt.proof_nodes for receipt in actual) == EXPECTED_PROOF_NODES
    assert sum(receipt.proof_nodes for receipt in actual) == 2231
    assert max(receipt.proof_depth for receipt in actual) == 72


@pytest.mark.parametrize(("name", "expected"), EXPECTED_ROOTS.items())
def test_exact_unrestricted_cofactor_family_roots_are_frozen(name: str, expected: str) -> None:
    theorem = next(item for item in rows() if item.name == name)
    assert sha256(theorem.statement.encode()).hexdigest() == expected


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_forged_false_cofactor_family_conclusions_are_rejected(name: str) -> None:
    theorem = next(item for item in rows() if item.name == name)
    forged = replace(theorem, statement=f"({theorem.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {item.name: item for item in rows()}
        )


@pytest.mark.parametrize(
    "name",
    (
        "matrix_minor_four_code_exists",
        "signed_cofactor_minor_record_exists",
        "signed_cofactor_minor_family_exists",
        "signed_alternating_cofactor_term_exists",
        "signed_alternating_product_prefix_empty",
        "signed_alternating_cofactor_fold_exists",
        "signed_first_row_cofactor_fold_exists",
        "signed_matrix_cofactor_family_and_fold_exists",
    ),
)
def test_truncated_genuine_cofactor_family_bodies_are_rejected(name: str) -> None:
    theorem = next(item for item in rows() if item.name == name)
    forged = replace(theorem, script=theorem.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {item.name: item for item in rows()}
        )


@pytest.mark.parametrize("name", EXPECTED_ROOTS)
def test_missing_major_cofactor_family_dependencies_are_rejected(name: str) -> None:
    theorem = next(item for item in rows() if item.name == name)
    assert theorem.dependencies
    forged = replace(theorem, dependencies=theorem.dependencies[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {item.name: item for item in rows()}
        )


SURFACES = (
    (candidate.matrix_minor_four_code_relation, ("z", "up", "us", "un", "ut")),
    (
        candidate.signed_matrix_minor_record_relation,
        ("pb", "pc", "nb", "nc", "q", "j", "z"),
    ),
    (
        candidate.signed_cofactor_minor_prefix_relation,
        ("pb", "pc", "nb", "nc", "q", "b", "c", "l"),
    ),
    (
        candidate.signed_alternating_cofactor_term_relation,
        ("ap", "an", "bp", "bn", "i", "p", "n"),
    ),
    (
        candidate.signed_alternating_product_prefix_relation,
        ("ab", "ac", "db", "dc", "eb", "ec", "fb", "fc", "ub", "uc", "vb", "vc", "l"),
    ),
    (
        candidate.signed_alternating_cofactor_fold_relation,
        ("ab", "ac", "db", "dc", "eb", "ec", "fb", "fc", "l", "p", "n"),
    ),
    (
        candidate.signed_first_row_cofactor_fold_relation,
        ("pb", "pc", "nb", "nc", "q", "eb", "ec", "fb", "fc", "p", "n"),
    ),
)


@pytest.mark.parametrize(("builder", "arguments"), SURFACES)
def test_cofactor_surfaces_have_exactly_declared_free_variables(
    builder, arguments: tuple[str, ...]
) -> None:
    _, names = parse_formula_with_names(builder(*arguments, tag="safe"))
    assert set(names) == set(arguments)


@pytest.mark.parametrize(("builder", "arguments"), SURFACES)
def test_distinct_hygienic_cofactor_tags_have_identical_ast(
    builder, arguments: tuple[str, ...]
) -> None:
    left, left_names = parse_formula_with_names(builder(*arguments, tag="first"))
    right, right_names = parse_formula_with_names(builder(*arguments, tag="second"))
    assert left_names == right_names
    assert left == right


@pytest.mark.parametrize("bad", ("", "forall", "S", "x) -> false", "ff_capture"))
@pytest.mark.parametrize(("builder", "arguments"), SURFACES)
def test_cofactor_surfaces_reject_injected_or_captured_arguments(
    builder, arguments: tuple[str, ...], bad: str
) -> None:
    with pytest.raises(candidate.MatrixCofactorExpansionError):
        builder(bad, *arguments[1:], tag="safe")


@pytest.mark.parametrize("bad", ("", "forall", "S", "safe) -> false"))
@pytest.mark.parametrize(("builder", "arguments"), SURFACES)
def test_cofactor_surfaces_reject_unsafe_binder_tags(
    builder, arguments: tuple[str, ...], bad: str
) -> None:
    with pytest.raises(candidate.MatrixCofactorExpansionError):
        builder(*arguments, tag=bad)


@pytest.mark.parametrize(("builder", "arguments"), SURFACES)
def test_cofactor_surfaces_reject_duplicate_free_variables(
    builder, arguments: tuple[str, ...]
) -> None:
    with pytest.raises(candidate.MatrixCofactorExpansionError):
        builder(arguments[1], *arguments[1:], tag="safe")


@pytest.mark.parametrize(
    "values",
    (
        ((-7,),),
        ((1, -2), (3, 4)),
        ((2, -3, 5), (7, 11, -13), (17, -19, 23)),
        ((2, -3, 5, 7), (11, 13, -17, 19), (23, 29, 31, -37), (-41, 43, 47, 53)),
    ),
)
def test_complete_executable_family_uses_every_actual_minor_and_exact_sign(
    values: tuple[tuple[int, ...], ...]
) -> None:
    matrix = integer_matrix(values)
    receipt = candidate.certify_signed_cofactor_family(matrix)
    assert receipt.value == certify_integer_determinant(matrix).value
    assert receipt.positive - receipt.negative == receipt.value
    assert tuple(item.column for item in receipt.entries) == tuple(range(matrix.width))
    assert sum(item.positive for item in receipt.entries) == receipt.positive
    assert sum(item.negative for item in receipt.entries) == receipt.negative
    for item in receipt.entries:
        assert candidate.verify_matrix_minor(item.minor)
        assert item.minor.removed_row == 0
        assert item.minor.removed_column == item.column
        assert item.minor_determinant == certify_integer_determinant(item.minor.minor).value
        assert item.positive - item.negative == (
            (-1) ** item.column * matrix.rows[0][item.column] * item.minor_determinant
        )
    assert candidate.verify_signed_cofactor_family(receipt)


@pytest.mark.parametrize("field", ("column", "minor_determinant", "positive", "negative"))
def test_family_verifier_rejects_every_forged_cofactor_record_field(field: str) -> None:
    receipt = candidate.certify_signed_cofactor_family(
        integer_matrix(((2, -3, 5), (7, 11, -13), (17, -19, 23)))
    )
    item = receipt.entries[1]
    forged_item = replace(item, **{field: getattr(item, field) + 1})
    forged = replace(receipt, entries=(receipt.entries[0], forged_item, receipt.entries[2]))
    assert not candidate.verify_signed_cofactor_family(forged)


@pytest.mark.parametrize("field", ("positive", "negative", "value"))
def test_family_verifier_rejects_forged_fold_totals(field: str) -> None:
    receipt = candidate.certify_signed_cofactor_family(integer_matrix(((2, 3), (5, 7))))
    assert not candidate.verify_signed_cofactor_family(
        replace(receipt, **{field: getattr(receipt, field) + 1})
    )


def test_family_verifier_rejects_forged_actual_minor_or_wrong_type() -> None:
    receipt = candidate.certify_signed_cofactor_family(integer_matrix(((2, 3), (5, 7))))
    forged_minor = replace(receipt.entries[0].minor, removed_column=1)
    forged_entry = replace(receipt.entries[0], minor=forged_minor)
    assert not candidate.verify_signed_cofactor_family(
        replace(receipt, entries=(forged_entry, receipt.entries[1]))
    )
    assert not candidate.verify_signed_cofactor_family(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "matrix",
    (
        integer_matrix(()),
        integer_matrix(((1, 2),)),
        integer_matrix(((candidate.MAX_COFACTOR_ENTRY + 1,),)),
        integer_matrix(tuple(tuple(0 for _ in range(8)) for _ in range(8))),
    ),
)
def test_executable_family_rejects_empty_nonsquare_and_unbounded_inputs(
    matrix: IntegerMatrix,
) -> None:
    with pytest.raises(candidate.MatrixCofactorExpansionError):
        candidate.certify_signed_cofactor_family(matrix)


def test_bounded_execution_does_not_limit_unrestricted_formal_family() -> None:
    root = next(item for item in rows() if item.name == "signed_cofactor_minor_family_exists")
    fold = next(item for item in rows() if item.name == "signed_first_row_cofactor_fold_exists")
    assert root.statement.startswith("forall pb pc nb nc q.")
    assert fold.statement.startswith("forall pb pc nb nc q eb ec fb fc.")
    assert "1048576" not in root.statement
    assert "1048576" not in fold.statement
    assert "determinant" not in fold.statement
