"""Original-kernel constructive arbitrary matrix multiplication and signing."""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256

import pytest

from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library import editions_v20 as v20
from peano_lab.library import matrix_coded_product_candidate as candidate
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.matrix_dot_product_candidate import IntegerMatrix, integer_matrix
from peano_lab.library.theorems import TheoremSpec, _closed_formula


EXPECTED_NAMES = (
    "beta_affine_matrix_slice_extend",
    "beta_affine_matrix_slice_exists",
    "beta_matrix_row_slice_exists",
    "beta_matrix_column_slice_exists",
    "beta_matrix_product_cell_exists",
    "beta_matrix_product_point_exists",
    "beta_matrix_product_prefix_extend",
    "beta_matrix_product_prefix_exists_nonzero",
    "beta_matrix_product_exists_nonzero_width",
    "beta_matrix_product_empty_exists",
    "beta_matrix_product_exists",
    "beta_pointwise_add_prefix_extend",
    "beta_pointwise_add_prefix_exists",
    "beta_signed_matrix_product_exists",
    "signed_pair_product_exists",
    "signed_pair_product_functional",
    "beta_signed_dot_product_exists",
    "beta_signed_dot_product_functional",
    "beta_signed_dot_product_exists_unique",
    "signed_matrix_two_full_determinant_exists",
    "signed_matrix_two_full_determinant_functional",
    "signed_matrix_three_full_determinant_exists",
    "signed_matrix_three_full_determinant_functional",
)
EXPECTED_NAMES_SHA256 = (
    "21012fdc098513a9d0f5ca9bd57a31afd8f69d174c4df32639b4f2cf3a3814c3"
)
EXPECTED_PROOF_NODES = (
    99,
    52,
    27,
    27,
    46,
    38,
    97,
    59,
    40,
    23,
    38,
    121,
    62,
    98,
    9,
    35,
    55,
    133,
    115,
    13,
    39,
    23,
    49,
)
EXPECTED_ROOTS = {
    "beta_matrix_product_exists": (
        "c2d3335be60c889559096aa9a36ed8d9bd38c8b33b5f776d73cdec0a60e951c2"
    ),
    "beta_pointwise_add_prefix_exists": (
        "0003860b43d5c86f8b1880d746f7d1025bb545146e6e1067b7965b1f76ed21c4"
    ),
    "beta_signed_matrix_product_exists": (
        "13291ba49b84a8b1345863e446bca126321e7962eb912bd84b48761f9db24c7f"
    ),
    "beta_signed_dot_product_exists_unique": (
        "f84fbb5d723d32ea972a38d562c3e59cbedc78ab485e9f20cda90c0c4f186c04"
    ),
    "signed_matrix_three_full_determinant_exists": (
        "edd7918f03a700f96dc345ba77e3dae458485fb323162139c2e93dbc09fae784"
    ),
}


@lru_cache(maxsize=1)
def rows() -> tuple[TheoremSpec, ...]:
    return candidate.make_matrix_coded_product_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core() -> dict[str, TheoremSpec]:
    return {item.name: item for item in v20.ALPHA_CHECKED_SPECS}


@lru_cache(maxsize=1)
def receipts():
    return replay_candidate_bodies(rows(), core=core())


def test_twenty_three_matrix_theorems_are_closed_fresh_and_dependency_ordered() -> None:
    actual = rows()
    assert tuple(item.name for item in actual) == EXPECTED_NAMES
    assert sha256("\n".join(EXPECTED_NAMES).encode()).hexdigest() == EXPECTED_NAMES_SHA256
    assert sum(len(item.dependencies) for item in actual) == 41
    assert sum(len(item.script) for item in actual) == 998
    known = set(core())
    for item in actual:
        formula, free_names = parse_formula_with_names(item.statement)
        assert not free_names
        assert formula == _closed_formula(item.statement)
        assert set(item.dependencies) <= known
        assert item.name not in v20.ALPHA_EDITION.by_name
        assert not any(
            command == "sorry"
            or command == "admit"
            or "DNE" in command
            or command.startswith("use ")
            for command in item.script
        )
        known.add(item.name)


def test_every_coded_matrix_body_passes_the_original_kernel() -> None:
    actual = receipts()
    assert tuple(receipt.name for receipt in actual) == EXPECTED_NAMES
    assert tuple(receipt.proof_nodes for receipt in actual) == EXPECTED_PROOF_NODES
    assert sum(receipt.proof_nodes for receipt in actual) == 1_298


@pytest.mark.parametrize(("name", "expected"), EXPECTED_ROOTS.items())
def test_major_coded_matrix_root_statements_are_immutable(name: str, expected: str) -> None:
    row = next(item for item in rows() if item.name == name)
    assert sha256(row.statement.encode()).hexdigest() == expected


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_false_coded_matrix_conclusions_are_rejected(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, statement=f"({original.statement}) /\\ false")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {item.name: item for item in rows()}
        )


@pytest.mark.parametrize("name", EXPECTED_NAMES)
def test_truncated_coded_matrix_proof_bodies_are_rejected(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    forged = replace(original, script=original.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {item.name: item for item in rows()}
        )


@pytest.mark.parametrize(
    "name",
    tuple(
        name
        for name in EXPECTED_NAMES
        if name
        not in {
            "signed_pair_product_exists",
            "signed_pair_product_functional",
            "signed_matrix_two_full_determinant_exists",
            "signed_matrix_two_full_determinant_functional",
            "signed_matrix_three_full_determinant_exists",
            "signed_matrix_three_full_determinant_functional",
        }
    ),
)
def test_omitting_any_required_matrix_dependency_is_rejected(name: str) -> None:
    original = next(item for item in rows() if item.name == name)
    assert original.dependencies
    forged = replace(original, dependencies=original.dependencies[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies(
            (forged,), core=core() | {item.name: item for item in rows()}
        )


SURFACES = (
    (
        candidate.affine_matrix_slice_relation,
        ("b", "c", "s", "d", "u", "v", "l"),
        "ff_index_mcp_safe",
    ),
    (
        candidate.matrix_product_cell_relation,
        ("lb", "lc", "rb", "rc", "w", "v", "i", "j", "n"),
        "ff_left_mcp_cell_safe",
    ),
    (
        candidate.matrix_product_prefix_relation,
        ("lb", "lc", "rb", "rc", "w", "v", "tb", "tc", "l"),
        "ff_index_mcp_prefix_safe",
    ),
    (
        candidate.pointwise_add_prefix_relation,
        ("mb", "mc", "sb", "sc", "tb", "tc", "l"),
        "ff_index_mcp_add_safe",
    ),
    (
        candidate.signed_dot_product_relation,
        ("ab", "ac", "db", "dc", "eb", "ec", "fb", "fc", "l", "p", "n"),
        "ff_pp_mcp_signed_safe",
    ),
    (
        candidate.signed_matrix_product_relation,
        (
            "ab",
            "ac",
            "db",
            "dc",
            "eb",
            "ec",
            "fb",
            "fc",
            "w",
            "v",
            "r",
            "pb",
            "pc",
            "nb",
            "nc",
        ),
        "ff_pp_mcp_smatrix_safe",
    ),
)


@pytest.mark.parametrize(("builder", "arguments", "_capture"), SURFACES)
def test_all_matrix_definition_surfaces_have_exactly_declared_free_variables(
    builder, arguments: tuple[str, ...], _capture: str
) -> None:
    _, actual = parse_formula_with_names(builder(*arguments, tag="safe"))
    assert set(actual) == set(arguments)


@pytest.mark.parametrize("bad", ("", "forall", "S", "x) -> false", "x /\\ false"))
@pytest.mark.parametrize(("builder", "arguments", "_capture"), SURFACES)
def test_coded_matrix_surfaces_reject_injected_or_reserved_arguments(
    builder, arguments: tuple[str, ...], _capture: str, bad: str
) -> None:
    with pytest.raises(candidate.CodedMatrixError):
        builder(bad, *arguments[1:], tag="safe")


@pytest.mark.parametrize("bad", ("", "forall", "S", "safe) -> false"))
@pytest.mark.parametrize(("builder", "arguments", "_capture"), SURFACES)
def test_coded_matrix_surfaces_reject_injected_binder_tags(
    builder, arguments: tuple[str, ...], _capture: str, bad: str
) -> None:
    with pytest.raises(candidate.CodedMatrixError):
        builder(*arguments, tag=bad)


@pytest.mark.parametrize(("builder", "arguments", "capture"), SURFACES)
def test_coded_matrix_surfaces_reject_actual_binder_capture(
    builder, arguments: tuple[str, ...], capture: str
) -> None:
    with pytest.raises(candidate.CodedMatrixError, match="captures"):
        builder(capture, *arguments[1:], tag="safe")


def test_affine_slices_expose_rows_columns_and_constant_stride_zero() -> None:
    source = (2, 3, 5, 7, 11, 13)
    row = candidate.certify_affine_slice(source, 3, 1, 3)
    column = candidate.certify_affine_slice(source, 1, 3, 2)
    repeated = candidate.certify_affine_slice(source, 2, 0, 4)
    assert row.values == (7, 11, 13)
    assert column.values == (3, 11)
    assert repeated.values == (5, 5, 5, 5)
    assert candidate.verify_affine_slice(row)
    assert candidate.verify_affine_slice(column)
    assert candidate.verify_affine_slice(repeated)


def test_empty_affine_slices_require_no_in_bounds_source() -> None:
    receipt = candidate.certify_affine_slice((), 100, 5, 0)
    assert receipt.values == ()
    assert candidate.verify_affine_slice(receipt)


@pytest.mark.parametrize(
    ("source", "start", "stride", "length"),
    (
        ((1, 2), 1, 1, 2),
        ((1, -2), 0, 1, 1),
        ((True,), 0, 1, 1),
        ((1,), -1, 0, 1),
        ((1,), 0, -1, 1),
        ((1,), 0, 1, -1),
        ((1,), 0, 1, candidate.MAX_MATRIX_DIMENSION + 1),
        ((1,), True, 0, 1),
    ),
)
def test_affine_slices_reject_invalid_coordinates_and_sources(
    source: tuple[object, ...], start: int, stride: int, length: int
) -> None:
    with pytest.raises(candidate.CodedMatrixError):
        candidate.certify_affine_slice(source, start, stride, length)  # type: ignore[arg-type]


def test_affine_slice_verifier_rejects_forged_values_and_coordinates() -> None:
    receipt = candidate.certify_affine_slice((2, 3, 5, 7), 1, 2, 2)
    assert not candidate.verify_affine_slice(replace(receipt, values=(3, 6)))
    assert not candidate.verify_affine_slice(replace(receipt, stride=1))
    assert not candidate.verify_affine_slice(replace(receipt, source=(2, 4, 5, 7)))


def test_signed_pairs_allow_noncanonical_constructive_representations() -> None:
    assert candidate.signed_pair(7, 3).value == 4
    assert candidate.signed_pair(0, 8).value == -8
    assert candidate.signed_pair(5, 5).value == 0


@pytest.mark.parametrize(
    ("positive", "negative"),
    ((-1, 0), (0, -1), (True, 0), (0, False), (1.5, 0), (candidate.MAX_COMPONENT + 1, 0)),
)
def test_signed_pairs_reject_non_natural_or_unbounded_components(
    positive: object, negative: object
) -> None:
    with pytest.raises(candidate.CodedMatrixError):
        candidate.signed_pair(positive, negative)  # type: ignore[arg-type]


def test_exact_signed_dot_preserves_all_four_component_products() -> None:
    left = (
        candidate.signed_pair(1, 0),
        candidate.signed_pair(0, 2),
        candidate.signed_pair(3, 1),
    )
    right = (
        candidate.signed_pair(4, 0),
        candidate.signed_pair(0, 3),
        candidate.signed_pair(1, 5),
    )
    receipt = candidate.certify_signed_dot(left, right)
    assert receipt.positive_positive == (4, 0, 3)
    assert receipt.negative_negative == (0, 6, 5)
    assert receipt.positive_negative == (0, 0, 15)
    assert receipt.negative_positive == (0, 0, 1)
    assert receipt.result == candidate.signed_pair(18, 16)
    assert receipt.result.value == sum(a.value * b.value for a, b in zip(left, right))
    assert candidate.verify_signed_dot(receipt)


def test_empty_signed_dot_is_exactly_zero() -> None:
    receipt = candidate.certify_signed_dot((), ())
    assert receipt.result == candidate.signed_pair(0, 0)
    assert candidate.verify_signed_dot(receipt)


def test_signed_dot_rejects_mismatched_forged_and_unbounded_vectors() -> None:
    value = candidate.signed_pair(1, 0)
    with pytest.raises(candidate.CodedMatrixError):
        candidate.certify_signed_dot((value,), ())
    with pytest.raises(candidate.CodedMatrixError):
        candidate.certify_signed_dot((1,), (value,))  # type: ignore[arg-type]
    with pytest.raises(candidate.CodedMatrixError):
        candidate.certify_signed_dot((candidate.SignedPair(-1, 0),), (value,))
    with pytest.raises(candidate.CodedMatrixError):
        candidate.certify_signed_dot(
            (value,) * (candidate.MAX_MATRIX_DIMENSION + 1),
            (value,) * (candidate.MAX_MATRIX_DIMENSION + 1),
        )
    with pytest.raises(candidate.CodedMatrixError):
        candidate.certify_signed_dot(
            (candidate.signed_pair(candidate.MAX_COMPONENT, 0),),
            (candidate.signed_pair(2, 0),),
        )


def test_signed_dot_verifier_rejects_every_forged_component() -> None:
    receipt = candidate.certify_signed_dot(
        (candidate.signed_pair(2, 1),), (candidate.signed_pair(3, 4),)
    )
    for forged in (
        replace(receipt, positive_positive=(7,)),
        replace(receipt, negative_negative=(5,)),
        replace(receipt, positive_negative=(9,)),
        replace(receipt, negative_positive=(4,)),
        replace(receipt, result=candidate.signed_pair(9, 10)),
    ):
        assert not candidate.verify_signed_dot(forged)


def test_arbitrary_natural_matrix_product_has_exact_flattened_output() -> None:
    left = integer_matrix(((1, 2, 3), (4, 5, 6)))
    right = integer_matrix(((7, 8), (9, 10), (11, 12)))
    receipt = candidate.certify_coded_natural_matrix_product(left, right)
    assert receipt.row_slices == ((1, 2, 3), (4, 5, 6))
    assert receipt.column_slices == ((7, 9, 11), (8, 10, 12))
    assert receipt.row_major_cells == (58, 64, 139, 154)
    assert receipt.result.rows == ((58, 64), (139, 154))
    assert candidate.verify_coded_natural_matrix_product(receipt)


@pytest.mark.parametrize(
    ("left_rows", "right_rows", "result"),
    (((), (), ()), (((), ()), (), ((), ())), (((5,),), ((7,),), ((35,),))),
)
def test_natural_matrix_products_handle_empty_and_singleton_boundaries(
    left_rows: tuple[tuple[int, ...], ...],
    right_rows: tuple[tuple[int, ...], ...],
    result: tuple[tuple[int, ...], ...],
) -> None:
    receipt = candidate.certify_coded_natural_matrix_product(
        integer_matrix(left_rows), integer_matrix(right_rows)
    )
    assert receipt.result.rows == result
    assert candidate.verify_coded_natural_matrix_product(receipt)


def test_natural_matrix_products_reject_signed_entries_and_incompatible_shapes() -> None:
    with pytest.raises(candidate.CodedMatrixError):
        candidate.certify_coded_natural_matrix_product(
            integer_matrix(((-1,),)), integer_matrix(((2,),))
        )
    with pytest.raises(candidate.CodedMatrixError):
        candidate.certify_coded_natural_matrix_product(
            integer_matrix(((1, 2),)), integer_matrix(((3, 4),))
        )


def test_natural_matrix_verifier_rejects_forged_cells_slices_and_result() -> None:
    receipt = candidate.certify_coded_natural_matrix_product(
        integer_matrix(((1, 2),)), integer_matrix(((3,), (4,)))
    )
    for forged in (
        replace(receipt, row_major_cells=(12,)),
        replace(receipt, row_slices=((1, 3),)),
        replace(receipt, column_slices=((3, 5),)),
        replace(receipt, result=integer_matrix(((12,),))),
    ):
        assert not candidate.verify_coded_natural_matrix_product(forged)


def test_full_signed_matrix_product_has_four_exact_natural_component_matrices() -> None:
    left = integer_matrix(((1, -2, 3), (0, 5, -1)))
    right = integer_matrix(((4, 2), (-3, 1), (2, -5)))
    receipt = candidate.certify_coded_signed_matrix_product(left, right)
    assert receipt.signed_output.rows == ((16, -15), (-17, 10))
    assert receipt.positive_output.rows == ((16, 2), (0, 10))
    assert receipt.negative_output.rows == ((0, 17), (17, 0))
    assert receipt.positive_positive.result.rows == ((10, 2), (0, 5))
    assert receipt.negative_negative.result.rows == ((6, 0), (0, 5))
    assert receipt.positive_negative.result.rows == ((0, 15), (15, 0))
    assert receipt.negative_positive.result.rows == ((0, 2), (2, 0))
    assert candidate.verify_coded_signed_matrix_product(receipt)


@pytest.mark.parametrize(("left", "right"), (((), ()), (((), ()), ())))
def test_signed_matrix_products_handle_all_representable_empty_boundaries(
    left: tuple[tuple[int, ...], ...], right: tuple[tuple[int, ...], ...]
) -> None:
    receipt = candidate.certify_coded_signed_matrix_product(
        integer_matrix(left), integer_matrix(right)
    )
    assert candidate.verify_coded_signed_matrix_product(receipt)
    assert receipt.signed_output.rows == left


def test_signed_matrix_products_reject_incompatible_or_over_budget_inputs() -> None:
    with pytest.raises(candidate.CodedMatrixError):
        candidate.certify_coded_signed_matrix_product(
            integer_matrix(((1, 2),)), integer_matrix(((3,),))
        )
    with pytest.raises(candidate.CodedMatrixError):
        candidate.certify_coded_signed_matrix_product(
            integer_matrix(((candidate.MAX_COMPONENT + 1,),)), integer_matrix(((1,),))
        )
    with pytest.raises(candidate.CodedMatrixError):
        candidate.certify_coded_signed_matrix_product(
            integer_matrix(((candidate.MAX_COMPONENT,),)), integer_matrix(((2,),))
        )


def test_signed_matrix_verifier_rejects_every_forged_product_and_component() -> None:
    receipt = candidate.certify_coded_signed_matrix_product(
        integer_matrix(((2, -1),)), integer_matrix(((3,), (-4,)))
    )
    forged_pp = replace(receipt.positive_positive, row_major_cells=(7,))
    for forged in (
        replace(receipt, positive_positive=forged_pp),
        replace(receipt, positive_output=integer_matrix(((11,),))),
        replace(receipt, negative_output=integer_matrix(((1,),))),
        replace(receipt, signed_output=integer_matrix(((11,),))),
    ):
        assert not candidate.verify_coded_signed_matrix_product(forged)


@pytest.mark.parametrize("forged", (None, (), 0, True, {"value": 2}, IntegerMatrix(())))
def test_all_matrix_verifiers_fail_closed_on_forged_certificate_types(forged: object) -> None:
    assert not candidate.verify_affine_slice(forged)  # type: ignore[arg-type]
    assert not candidate.verify_signed_dot(forged)  # type: ignore[arg-type]
    assert not candidate.verify_coded_natural_matrix_product(forged)  # type: ignore[arg-type]
    assert not candidate.verify_coded_signed_matrix_product(forged)  # type: ignore[arg-type]
