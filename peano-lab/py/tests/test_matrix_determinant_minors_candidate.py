"""Original-kernel arbitrary signed cofactor minors and four-dimensional determinants."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import editions_v23 as v23
from peano_lab.library import matrix_determinant_minors_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.matrix_dot_product_candidate import (
    IntegerMatrix,
    certify_integer_determinant,
    integer_matrix,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "matrix_skip_index_exists",
    "matrix_skip_index_functional",
    "matrix_skip_index_avoids_removed",
    "matrix_skip_index_bounded",
    "beta_matrix_minor_cell_exists",
    "beta_matrix_minor_cell_functional",
    "beta_matrix_minor_point_exists",
    "beta_matrix_minor_prefix_extend",
    "beta_matrix_minor_prefix_exists_nonzero",
    "beta_matrix_minor_prefix_empty_exists",
    "beta_matrix_minor_prefix_exists",
    "beta_matrix_minor_exists",
    "beta_signed_matrix_minor_exists",
    "signed_matrix_four_cofactor_expansion_exists",
    "signed_matrix_four_cofactor_expansion_functional",
    "signed_matrix_four_full_determinant_exists",
    "signed_matrix_four_full_determinant_functional",
)
EXPECTED_NAMES_SHA256 = (
    "970a190bfb3064dce0d1caca4970fd100e98c0d26ba4f25e8766718100ca6cfe"
)
EXPECTED_PROOF_NODES = (
    23, 97, 35, 65, 30, 87, 37, 97, 59, 23, 38, 37, 43, 21, 47, 98, 124
)
EXPECTED_ROOTS = {
    "beta_matrix_minor_exists": (
        "3abfa041aa3df531be6ac5580a3167802703e2adc4ecf13ae77f19309a31a8ee"
    ),
    "beta_signed_matrix_minor_exists": (
        "bf6e9238c2928e4f6525a14015198b673b41022924c6da1944ab87c8df61bba1"
    ),
    "signed_matrix_four_cofactor_expansion_exists": (
        "f1bf20e0ba8ca02fd964b85ea1b469923bf9c9e1bb320253ebbc456fea524486"
    ),
    "signed_matrix_four_full_determinant_exists": (
        "7ae77d34a56bc459140fcd9afab5bb70cf4792cdb6ebac833c448381adfff848"
    ),
    "signed_matrix_four_full_determinant_functional": (
        "d1987b1ba2337c22463858a07b85da4144d00f20f8e036c076d53d99de8ada59"
    ),
}


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_matrix_determinant_minors_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in v23.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def test_seventeen_minor_theorems_are_closed_fresh_and_dependency_ordered() -> None:
    actual = rows()
    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert sum(len(item.dependencies) for item in actual) == 28
    assert sum(len(item.script) for item in actual) == 602
    available = set(core())
    for item in actual:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert item.name not in v23.ALPHA_EDITION.by_name
        assert set(item.dependencies) <= available
        assert not any(
            command == "sorry"
            or command == "admit"
            or "DNE" in command
            or command.startswith("use ")
            for command in item.script
        )
        available.add(item.name)


def test_every_cofactor_minor_body_passes_the_unchanged_original_kernel() -> None:
    actual = receipts()
    assert tuple(receipt.name for receipt in actual) == EXPECTED_NAMES
    assert tuple(receipt.proof_nodes for receipt in actual) == EXPECTED_PROOF_NODES
    assert sum(receipt.proof_nodes for receipt in actual) == 961
    assert max(receipt.proof_depth for receipt in actual) == 82


@pytest.mark.parametrize(("name", "expected"), EXPECTED_ROOTS.items())
def test_exact_major_matrix_minor_roots_are_frozen(name: str, expected: str) -> None:
    theorem = next(item for item in rows() if item.name == name)
    assert sha256(theorem.statement.encode()).hexdigest() == expected


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_forged_false_matrix_minor_conclusions_are_rejected(name: str) -> None:
    theorem = next(item for item in rows() if item.name == name)
    forged = replace(theorem, statement=f"({theorem.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {item.name: item for item in rows()}
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_matrix_minor_tactic_bodies_are_rejected(name: str) -> None:
    theorem = next(item for item in rows() if item.name == name)
    forged = replace(theorem, script=theorem.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {item.name: item for item in rows()}
        )


@pytest.mark.parametrize(
    "name",
    tuple(
        name for name in EXPECTED_NAMES
        if name not in {
            "signed_matrix_four_cofactor_expansion_exists",
            "signed_matrix_four_cofactor_expansion_functional",
        }
    ),
)
def test_missing_required_minor_dependencies_are_rejected(name: str) -> None:
    theorem = next(item for item in rows() if item.name == name)
    assert theorem.dependencies
    forged = replace(theorem, dependencies=theorem.dependencies[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {item.name: item for item in rows()}
        )


SURFACES = (
    (
        candidate.matrix_skip_index_relation,
        ("i", "r", "s"),
        "ff_gap_mdm_lt_safe_before",
    ),
    (
        candidate.matrix_minor_cell_relation,
        ("b", "c", "w", "r", "d", "i", "j", "z"),
        "ff_row_mdm_cell_safe",
    ),
    (
        candidate.matrix_minor_prefix_relation,
        ("b", "c", "w", "r", "d", "u", "v", "q", "l"),
        "ff_index_mdm_prefix_safe",
    ),
    (
        candidate.signed_matrix_minor_relation,
        ("pb", "pc", "nb", "nc", "w", "r", "d", "q", "up", "us", "un", "ut"),
        "ff_index_mdm_prefix_safe_positive",
    ),
)


@pytest.mark.parametrize(("builder", "arguments", "_capture"), SURFACES)
def test_minor_surfaces_have_exactly_the_declared_free_variables(
    builder, arguments: tuple[str, ...], _capture: str
) -> None:
    _, actual = parse_formula_with_names(builder(*arguments, tag="safe"))
    assert set(actual) == set(arguments)


@pytest.mark.parametrize(("builder", "arguments", "_capture"), SURFACES)
def test_different_hygienic_minor_tags_expand_to_the_same_ast(
    builder, arguments: tuple[str, ...], _capture: str
) -> None:
    left, names = parse_formula_with_names(builder(*arguments, tag="first"))
    right, other = parse_formula_with_names(builder(*arguments, tag="second"))
    assert names == other
    assert left == right


@pytest.mark.parametrize("bad", ("", "forall", "S", "x) -> false", "x /\\ false"))
@pytest.mark.parametrize(("builder", "arguments", "_capture"), SURFACES)
def test_minor_surfaces_reject_injected_or_reserved_arguments(
    builder, arguments: tuple[str, ...], _capture: str, bad: str
) -> None:
    with pytest.raises(candidate.MatrixMinorError):
        builder(bad, *arguments[1:], tag="safe")


@pytest.mark.parametrize("bad", ("", "forall", "S", "safe) -> false"))
@pytest.mark.parametrize(("builder", "arguments", "_capture"), SURFACES)
def test_minor_surfaces_reject_injected_binder_tags(
    builder, arguments: tuple[str, ...], _capture: str, bad: str
) -> None:
    with pytest.raises(candidate.MatrixMinorError):
        builder(*arguments, tag=bad)


@pytest.mark.parametrize(("builder", "arguments", "capture"), SURFACES)
def test_minor_surfaces_reject_actual_nested_binder_capture(
    builder, arguments: tuple[str, ...], capture: str
) -> None:
    with pytest.raises(candidate.MatrixMinorError, match="captures"):
        builder(capture, *arguments[1:], tag="safe")


@pytest.mark.parametrize(
    ("index", "removed", "expected"),
    ((0, 0, 1), (0, 1, 0), (1, 0, 2), (1, 1, 2), (1, 2, 1), (5, 3, 6)),
)
def test_bounded_skip_execution_omits_exactly_the_deleted_coordinate(
    index: int, removed: int, expected: int
) -> None:
    assert candidate.matrix_skip_index(index, removed) == expected
    assert expected != removed


@pytest.mark.parametrize(("index", "removed"), ((True, 0), (0, False), (-1, 0), (0, -1), (33, 0), (0, 33)))
def test_skip_execution_rejects_nonexact_or_unbounded_coordinates(
    index: int, removed: int
) -> None:
    with pytest.raises(candidate.MatrixMinorError):
        candidate.matrix_skip_index(index, removed)


def test_exact_interior_minor_tracks_every_surviving_source_coordinate() -> None:
    matrix = integer_matrix(((2, -3, 5, 7), (11, 13, -17, 19), (23, 29, 31, -37)))
    receipt = candidate.certify_matrix_minor(matrix, 1, 2)
    assert receipt.source_coordinates == (((0, 0), (0, 1), (0, 3)), ((2, 0), (2, 1), (2, 3)))
    assert receipt.minor == integer_matrix(((2, -3, 7), (23, 29, -37)))
    assert candidate.verify_matrix_minor(receipt)


def test_one_by_one_minor_is_the_genuine_empty_matrix() -> None:
    receipt = candidate.certify_matrix_minor(integer_matrix(((-9,),)), 0, 0)
    assert receipt.source_coordinates == ()
    assert receipt.minor == integer_matrix(())
    assert candidate.verify_matrix_minor(receipt)


@pytest.mark.parametrize(
    ("matrix", "row", "column"),
    (
        (integer_matrix(()), 0, 0),
        (integer_matrix(((),)), 0, 0),
        (integer_matrix(((1, 2), (3, 4))), -1, 0),
        (integer_matrix(((1, 2), (3, 4))), 0, 2),
        (integer_matrix(((1, 2), (3, 4))), True, 0),
        (integer_matrix(((1, 2), (3, 4))), 0, False),
    ),
)
def test_minor_certification_rejects_missing_or_nonexact_coordinates(
    matrix: IntegerMatrix, row: int, column: int
) -> None:
    with pytest.raises(candidate.MatrixMinorError):
        candidate.certify_matrix_minor(matrix, row, column)


def test_minor_verifier_rejects_forged_coordinates_values_and_types() -> None:
    receipt = candidate.certify_matrix_minor(integer_matrix(((2, 3), (5, 7))), 0, 1)
    forged_coordinates = replace(receipt, source_coordinates=(((0, 0),),))
    forged_value = replace(receipt, minor=integer_matrix(((13,),)))
    forged_column = replace(receipt, removed_column=0)
    assert not candidate.verify_matrix_minor(forged_coordinates)
    assert not candidate.verify_matrix_minor(forged_value)
    assert not candidate.verify_matrix_minor(forged_column)
    assert not candidate.verify_matrix_minor(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "values",
    (
        (),
        ((-7,),),
        ((1, -2), (3, 4)),
        ((2, -3, 5), (7, 11, -13), (-17, 19, 23)),
        ((2, -3, 5, 7), (11, 13, -17, 19), (23, 29, 31, -37), (-41, 43, 47, 53)),
    ),
)
def test_signed_laplace_expansion_matches_independent_permutation_determinant(
    values: tuple[tuple[int, ...], ...]
) -> None:
    matrix = integer_matrix(values)
    receipt = candidate.certify_signed_cofactor_determinant(matrix)
    independent = certify_integer_determinant(matrix)
    assert receipt.determinant == independent.value
    assert receipt.positive - receipt.negative == independent.value
    if matrix.height:
        assert tuple(term.column for term in receipt.terms) == tuple(range(matrix.width))
        assert sum(term.value for term in receipt.terms) == independent.value
        assert all(candidate.verify_matrix_minor(term.minor) for term in receipt.terms)
    else:
        assert (receipt.positive, receipt.negative) == (1, 0)
    assert candidate.verify_signed_cofactor_determinant(receipt)


def test_signed_cofactor_verifier_rejects_forged_summands_signs_and_values() -> None:
    receipt = candidate.certify_signed_cofactor_determinant(
        integer_matrix(((2, -3, 5), (7, 11, -13), (-17, 19, 23)))
    )
    forged_term = replace(receipt.terms[1], positive=receipt.terms[1].positive + 1)
    forged_tree = replace(receipt, terms=(receipt.terms[0], forged_term, receipt.terms[2]))
    forged_sign = replace(receipt, positive=receipt.positive + 1)
    forged_value = replace(receipt, determinant=receipt.determinant + 1)
    assert not candidate.verify_signed_cofactor_determinant(forged_tree)
    assert not candidate.verify_signed_cofactor_determinant(forged_sign)
    assert not candidate.verify_signed_cofactor_determinant(forged_value)
    assert not candidate.verify_signed_cofactor_determinant(object())  # type: ignore[arg-type]


def test_cofactor_budgets_do_not_weaken_unrestricted_formal_theorems() -> None:
    oversized = integer_matrix(
        tuple(tuple(0 for _ in range(8)) for _ in range(8))
    )
    huge_entry = integer_matrix(((candidate.MAX_COFACTOR_ENTRY + 1,),))
    for matrix in (oversized, huge_entry, integer_matrix(((1, 2),))):
        with pytest.raises(candidate.MatrixMinorError):
            candidate.certify_signed_cofactor_determinant(matrix)
    signed_root = next(item for item in rows() if item.name == candidate.BETA_SIGNED_MATRIX_MINOR_EXISTS)
    assert "forall pb pc nb nc q r d." in signed_root.statement
    assert "32" not in signed_root.statement
    assert "1048576" not in signed_root.statement
