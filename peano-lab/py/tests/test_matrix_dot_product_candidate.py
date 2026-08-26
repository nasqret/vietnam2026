"""Constructive finite matrix-entry, dot-product, and determinant foundations."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import editions_v19 as v19
from peano_lab.library import matrix_dot_product_candidate as candidate
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "beta_matrix_cell_exists",
    "beta_matrix_cell_functional",
    "beta_matrix_cell_exists_unique",
    "beta_dot_product_exists",
    "beta_dot_product_functional",
    "beta_dot_product_exists_unique",
    "beta_dot_product_empty",
    "beta_dot_product_commutative",
    "signed_matrix_two_determinant_exists",
    "signed_matrix_two_determinant_functional",
)

EXPECTED_NAMES_SHA256 = (
    "e45e7c2cb0b858027ce44ae59b67c17737dcb5f3c2b9cecf5591ea36f484c8c3"
)
EXPECTED_PROOF_NODES = (19, 35, 67, 51, 125, 67, 34, 43, 9, 35)


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_matrix_dot_product_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in v19.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def test_ten_exact_matrix_foundation_theorems_are_closed_and_ordered() -> None:
    actual = rows()
    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == (
        EXPECTED_NAMES_SHA256
    )
    assert sum(len(item.dependencies) for item in actual) == 13
    assert sum(len(item.script) for item in actual) == 263
    prior: set[str] = set()
    for item in actual:
        parsed, free = parse_formula_with_names(item.statement)
        assert not free
        assert parsed == _closed_formula(item.statement)
        assert set(item.dependencies) <= set(core()) | prior
        assert item.name not in v19.ALPHA_EDITION.by_name
        assert not any("DNE" in command or command.startswith("use ") for command in item.script)
        prior.add(item.name)


def test_all_matrix_foundation_bodies_pass_the_original_kernel() -> None:
    actual = receipts()
    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert tuple(item.proof_nodes for item in actual) == EXPECTED_PROOF_NODES
    assert sum(item.proof_nodes for item in actual) == 485


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_matrix_conclusions_are_rejected(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, statement=f"({original.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=core() | {item.name: item for item in rows()})


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_matrix_scripts_are_rejected(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, script=original.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=core() | {item.name: item for item in rows()})


@pytest.mark.parametrize("name", EXPECTED_NAMES[:8])
def test_omitted_matrix_dependencies_are_rejected(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, dependencies=original.dependencies[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((forged,), core=core() | {item.name: item for item in rows()})


@pytest.mark.parametrize("bad", ("forall", "S", "n) -> false", ""))
def test_matrix_cell_relation_rejects_unsafe_fragments(bad: str) -> None:
    with pytest.raises(candidate.MatrixCertificateError):
        candidate.matrix_cell_relation("b", "c", "w", "i", "j", bad, tag="safe")


def test_matrix_cell_relation_rejects_binder_capture() -> None:
    with pytest.raises(candidate.MatrixCertificateError, match="captures"):
        candidate.matrix_cell_relation("ff_height_matrix_x", "c", "w", "i", "j", "n", tag="x")


@pytest.mark.parametrize("bad", ("forall", "S", "l /\\ false", ""))
def test_dot_product_relation_rejects_unsafe_fragments(bad: str) -> None:
    with pytest.raises(candidate.MatrixCertificateError):
        candidate.dot_product_relation("mb", "mc", "sb", "sc", bad, "n", tag="safe")


def test_dot_product_relation_rejects_binder_capture() -> None:
    with pytest.raises(candidate.MatrixCertificateError, match="captures"):
        candidate.dot_product_relation("ff_code_dot_x", "mc", "sb", "sc", "l", "n", tag="x")


@pytest.mark.parametrize("bad", ("forall", "S", "tag) -> false", ""))
def test_matrix_surfaces_reject_unsafe_tags(bad: str) -> None:
    with pytest.raises(candidate.MatrixCertificateError):
        candidate.matrix_cell_relation("b", "c", "w", "i", "j", "n", tag=bad)
    with pytest.raises(candidate.MatrixCertificateError):
        candidate.dot_product_relation("mb", "mc", "sb", "sc", "l", "n", tag=bad)


def test_concrete_signed_matrix_product_has_every_dot_witness() -> None:
    left = candidate.integer_matrix(((1, -2, 3), (0, 5, -1)))
    right = candidate.integer_matrix(((4, 2), (-3, 1), (2, -5)))
    receipt = candidate.multiply_integer_matrices(left, right)
    assert receipt.result.rows == ((16, -15), (-17, 10))
    assert receipt.dot_terms[0][0] == (4, 6, 6)
    assert receipt.dot_terms[1][1] == (0, 5, 5)
    assert candidate.verify_matrix_product(receipt)


def test_concrete_matrix_product_rejects_altered_cells_and_terms() -> None:
    receipt = candidate.multiply_integer_matrices(
        candidate.integer_matrix(((1, 2),)), candidate.integer_matrix(((3,), (4,)))
    )
    assert not candidate.verify_matrix_product(
        replace(receipt, result=candidate.integer_matrix(((12,),)))
    )
    assert not candidate.verify_matrix_product(replace(receipt, dot_terms=(((4, 8),),)))


def test_concrete_matrix_product_rejects_incompatible_dimensions() -> None:
    with pytest.raises(candidate.MatrixCertificateError, match="dimensions"):
        candidate.multiply_integer_matrices(
            candidate.integer_matrix(((1, 2),)), candidate.integer_matrix(((3, 4),))
        )


@pytest.mark.parametrize(
    ("rows", "value"),
    (
        ((), 1),
        (((5,),), 5),
        (((1, 2), (3, 4)), -2),
        (((2, -1, 0), (3, 4, 5), (1, 0, -2)), -27),
        (((1, 0, 0), (0, 1, 0), (0, 0, 1)), 1),
    ),
)
def test_exact_integer_determinants_have_signed_permutation_certificates(
    rows: tuple[tuple[int, ...], ...], value: int
) -> None:
    receipt = candidate.certify_integer_determinant(candidate.integer_matrix(rows))
    assert receipt.value == value
    assert candidate.verify_integer_determinant(receipt)
    assert receipt.value == sum(receipt.positive_terms) - sum(receipt.negative_terms)


def test_determinant_verifier_rejects_altered_sign_and_value() -> None:
    receipt = candidate.certify_integer_determinant(candidate.integer_matrix(((1, 2), (3, 4))))
    assert not candidate.verify_integer_determinant(replace(receipt, value=2))
    assert not candidate.verify_integer_determinant(replace(receipt, negative_terms=(5,)))


def test_determinants_reject_nonsquare_and_excessive_matrices() -> None:
    with pytest.raises(candidate.MatrixCertificateError, match="square"):
        candidate.certify_integer_determinant(candidate.integer_matrix(((1, 2),)))
    size = candidate.MAX_DETERMINANT_DIMENSION + 1
    large = candidate.integer_matrix(tuple(tuple(0 for _ in range(size)) for _ in range(size)))
    with pytest.raises(candidate.MatrixCertificateError, match="permutation budget"):
        candidate.certify_integer_determinant(large)


@pytest.mark.parametrize("rows", (((1,), (1, 2)), ((True,),), ((1.5,),), (("1",),)))
def test_integer_matrix_rejects_nonrectangular_and_noninteger_values(
    rows: tuple[tuple[object, ...], ...],
) -> None:
    with pytest.raises(candidate.MatrixCertificateError):
        candidate.integer_matrix(rows)  # type: ignore[arg-type]


@pytest.mark.parametrize("forged", (None, (), 0, True, {"value": 5}))
def test_matrix_verifiers_reject_noncertificates(forged: object) -> None:
    assert not candidate.verify_matrix_product(forged)  # type: ignore[arg-type]
    assert not candidate.verify_integer_determinant(forged)  # type: ignore[arg-type]

