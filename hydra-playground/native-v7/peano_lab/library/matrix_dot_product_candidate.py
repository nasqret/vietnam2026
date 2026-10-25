"""Conservative coded matrix entries, dot products, and finite determinants.

This is the first genuine layer of T13, not the entire proposed integer-matrix
and lattice campaign. Matrix coordinates are flattened as ``row * width +
column`` inside the existing Gödel-beta relation. Dot products existentially
package an already constructively encoded pointwise-product prefix with its
independently encoded finite sum. Signed 2-by-2 determinants are represented
by a pair of natural positive/negative components.

Every relation expands to unchanged first-order Heyting arithmetic. Concrete
integer-matrix certificates support experimentation but confer no theorem or
release authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations
from typing import Any, Callable, Iterable

from .finite_fold_surface import _binders, _identifier, _variables, sum_relation
from .finite_pointwise_mul_product_candidate import pointwise_mul_prefix
from .finite_sum_theorems import _at


BETA_MATRIX_CELL_EXISTS = "beta_matrix_cell_exists"
BETA_MATRIX_CELL_FUNCTIONAL = "beta_matrix_cell_functional"
BETA_MATRIX_CELL_EXISTS_UNIQUE = "beta_matrix_cell_exists_unique"
BETA_DOT_PRODUCT_EXISTS = "beta_dot_product_exists"
BETA_DOT_PRODUCT_FUNCTIONAL = "beta_dot_product_functional"
BETA_DOT_PRODUCT_EXISTS_UNIQUE = "beta_dot_product_exists_unique"
BETA_DOT_PRODUCT_EMPTY = "beta_dot_product_empty"
BETA_DOT_PRODUCT_COMMUTATIVE = "beta_dot_product_commutative"
SIGNED_MATRIX_TWO_DETERMINANT_EXISTS = "signed_matrix_two_determinant_exists"
SIGNED_MATRIX_TWO_DETERMINANT_FUNCTIONAL = "signed_matrix_two_determinant_functional"

MAX_MATRIX_DIMENSION = 32
MAX_DETERMINANT_DIMENSION = 8


class MatrixCertificateError(ValueError):
    """A conservative matrix relation or concrete computation certificate failed."""


def _safe_tag(tag: str) -> str:
    try:
        return _identifier(tag, "matrix binder tag")
    except ValueError as error:
        raise MatrixCertificateError(str(error)) from error


def matrix_cell_relation(
    code: str,
    scale: str,
    columns: str,
    row: str,
    column: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand a flattened finite matrix entry without adding term symbols."""

    try:
        variables = _variables(
            (code, "matrix code"),
            (scale, "matrix scale"),
            (columns, "matrix width"),
            (row, "matrix row"),
            (column, "matrix column"),
            (value, "matrix value"),
        )
        safe_tag = _safe_tag(tag)
        _binders(f"matrix_{safe_tag}", variables, ("height", "quotient"))
        return _at(code, scale, f"{row} * {columns} + {column}", value, tag=f"matrix_{safe_tag}")
    except ValueError as error:
        raise MatrixCertificateError(str(error)) from error


def dot_product_relation(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand an exact coded finite dot-product witness conservatively."""

    try:
        variables = _variables(
            (left_code, "left vector code"),
            (left_scale, "left vector scale"),
            (right_code, "right vector code"),
            (right_scale, "right vector scale"),
            (length, "vector length"),
            (result, "dot-product result"),
        )
        safe_tag = _safe_tag(tag)
        target_code, target_scale = _binders(
            f"dot_{safe_tag}", variables, ("code", "scale")
        )
        alignment = pointwise_mul_prefix(
            left_code,
            left_scale,
            right_code,
            right_scale,
            target_code,
            target_scale,
            length,
            tag=f"dot_{safe_tag}_pointwise",
        )
        total = sum_relation(target_code, target_scale, length, result, tag=f"dot_{safe_tag}_sum")
        return f"exists {target_code} {target_scale}. (({alignment}) /\\ ({total}))"
    except ValueError as error:
        raise MatrixCertificateError(str(error)) from error


def _dot_terms(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    if length == "0":
        marker = "matrix_dot_zero_length_marker"
        expanded = dot_product_relation(
            left_code, left_scale, right_code, right_scale, marker, result, tag=tag
        )
        return expanded.replace(marker, "0")
    return dot_product_relation(
        left_code, left_scale, right_code, right_scale, length, result, tag=tag
    )


def make_matrix_dot_product_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build actual first-order matrix entry, dot product, and determinant laws."""

    cell = matrix_cell_relation("b", "c", "w", "i", "j", "n", tag="entry")
    cell_other = matrix_cell_relation("b", "c", "w", "i", "j", "m", tag="other")
    dot = dot_product_relation("mb", "mc", "sb", "sc", "l", "n", tag="value")
    dot_other = dot_product_relation("mb", "mc", "sb", "sc", "l", "m", tag="other")
    dot_reverse = dot_product_relation("sb", "sc", "mb", "mc", "l", "n", tag="reverse")
    dot_empty = _dot_terms("mb", "mc", "sb", "sc", "0", "n", tag="empty")

    return (
        spec(
            BETA_MATRIX_CELL_EXISTS,
            f"forall b c w i j. exists n. ({cell})",
            ("beta_at_exists",),
            (
                "intro b", "intro c", "intro w", "intro i", "intro j",
                "specialize beta_at_exists b", "specialize beta_at_exists c",
                "specialize beta_at_exists (i * w + j)", "exact beta_at_exists",
            ),
            "Every requested finite matrix coordinate has a witnessed beta-decoded entry.",
        ),
        spec(
            BETA_MATRIX_CELL_FUNCTIONAL,
            f"forall b c w i j n m. ({cell}) -> ({cell_other}) -> n = m",
            ("beta_at_unique",),
            (
                "intro b", "intro c", "intro w", "intro i", "intro j",
                "intro n", "intro m", "intro hn", "intro hm",
                "specialize beta_at_unique b", "specialize beta_at_unique c",
                "specialize beta_at_unique (i * w + j)",
                "specialize beta_at_unique n", "specialize beta_at_unique m",
                "apply beta_at_unique", "exact hn", "exact hm",
            ),
            "The decoded natural value of every flattened matrix cell is unique.",
        ),
        spec(
            BETA_MATRIX_CELL_EXISTS_UNIQUE,
            f"forall b c w i j. exists n. (({cell}) /\\ forall m. ({cell_other}) -> n = m)",
            (BETA_MATRIX_CELL_EXISTS, BETA_MATRIX_CELL_FUNCTIONAL),
            (
                "intro b", "intro c", "intro w", "intro i", "intro j",
                f"specialize {BETA_MATRIX_CELL_EXISTS} b",
                f"specialize {BETA_MATRIX_CELL_EXISTS} c",
                f"specialize {BETA_MATRIX_CELL_EXISTS} w",
                f"specialize {BETA_MATRIX_CELL_EXISTS} i",
                f"specialize {BETA_MATRIX_CELL_EXISTS} j",
                f"cases {BETA_MATRIX_CELL_EXISTS}",
                "exists x", "split", f"exact {BETA_MATRIX_CELL_EXISTS}_witness",
                "intro m", "intro hm",
                f"specialize {BETA_MATRIX_CELL_FUNCTIONAL} b",
                f"specialize {BETA_MATRIX_CELL_FUNCTIONAL} c",
                f"specialize {BETA_MATRIX_CELL_FUNCTIONAL} w",
                f"specialize {BETA_MATRIX_CELL_FUNCTIONAL} i",
                f"specialize {BETA_MATRIX_CELL_FUNCTIONAL} j",
                f"specialize {BETA_MATRIX_CELL_FUNCTIONAL} x",
                f"specialize {BETA_MATRIX_CELL_FUNCTIONAL} m",
                f"apply {BETA_MATRIX_CELL_FUNCTIONAL}",
                f"exact {BETA_MATRIX_CELL_EXISTS}_witness", "exact hm",
            ),
            "Every finite beta-coded matrix entry has exactly one actual value.",
        ),
        spec(
            BETA_DOT_PRODUCT_EXISTS,
            f"forall mb mc sb sc l. exists n. ({dot})",
            ("beta_pointwise_mul_prefix_exists", "beta_sum_exists"),
            (
                "intro mb", "intro mc", "intro sb", "intro sc", "intro l",
                "specialize beta_pointwise_mul_prefix_exists mb",
                "specialize beta_pointwise_mul_prefix_exists mc",
                "specialize beta_pointwise_mul_prefix_exists sb",
                "specialize beta_pointwise_mul_prefix_exists sc",
                "specialize beta_pointwise_mul_prefix_exists l",
                "cases beta_pointwise_mul_prefix_exists",
                "cases beta_pointwise_mul_prefix_exists_witness",
                "specialize beta_sum_exists x", "specialize beta_sum_exists x1",
                "specialize beta_sum_exists l", "cases beta_sum_exists",
                "exists x2", "exists x", "exists x1", "split",
                "exact beta_pointwise_mul_prefix_exists_witness_witness",
                "exact beta_sum_exists_witness",
            ),
            "Two arbitrary finite coded vectors have an exactly witnessed dot product.",
        ),
        spec(
            BETA_DOT_PRODUCT_FUNCTIONAL,
            f"forall mb mc sb sc l n m. ({dot}) -> ({dot_other}) -> n = m",
            ("beta_at_exists", "beta_sum_transport_prefix", "beta_sum_functional"),
            (
                "intro mb", "intro mc", "intro sb", "intro sc", "intro l",
                "intro n", "intro m", "intro hn", "intro hm",
                "cases hn", "cases hn_witness", "cases hn_witness_witness",
                "cases hm", "cases hm_witness", "cases hm_witness_witness",
                f"have htransport : {sum_relation('x2', 'x3', 'l', 'n', tag='dot_transport')}",
                "specialize beta_sum_transport_prefix x",
                "specialize beta_sum_transport_prefix x1",
                "specialize beta_sum_transport_prefix x2",
                "specialize beta_sum_transport_prefix x3",
                "specialize beta_sum_transport_prefix l",
                "specialize beta_sum_transport_prefix n",
                "apply beta_sum_transport_prefix",
                "exact hn_witness_witness_right",
                "intro i", "intro a", "intro hi", "intro ha",
                f"have hleft : exists z. {_at('mb', 'mc', 'i', 'z', tag='dot_left')}",
                "specialize beta_at_exists mb", "specialize beta_at_exists mc",
                "specialize beta_at_exists i", "exact beta_at_exists", "cases hleft",
                f"have hright : exists z. {_at('sb', 'sc', 'i', 'z', tag='dot_right')}",
                "specialize beta_at_exists sb", "specialize beta_at_exists sc",
                "specialize beta_at_exists i", "exact beta_at_exists", "cases hright",
                f"have htarget : exists z. {_at('x2', 'x3', 'i', 'z', tag='dot_target')}",
                "specialize beta_at_exists x2", "specialize beta_at_exists x3",
                "specialize beta_at_exists i", "exact beta_at_exists", "cases htarget",
                "have hfirst : a = x4 * x5",
                "specialize hn_witness_witness_left i",
                "specialize hn_witness_witness_left x4",
                "specialize hn_witness_witness_left x5",
                "specialize hn_witness_witness_left a",
                "apply hn_witness_witness_left", "exact hi",
                "exact hleft_witness", "exact hright_witness", "exact ha",
                "have hsecond : x6 = x4 * x5",
                "specialize hm_witness_witness_left i",
                "specialize hm_witness_witness_left x4",
                "specialize hm_witness_witness_left x5",
                "specialize hm_witness_witness_left x6",
                "apply hm_witness_witness_left", "exact hi",
                "exact hleft_witness", "exact hright_witness", "exact htarget_witness",
                "have heq : a = x6", "trans x4 * x5", "exact hfirst",
                "symm", "exact hsecond", "rewrite heq", "rewrite heq",
                "exact htarget_witness",
                "specialize beta_sum_functional x2",
                "specialize beta_sum_functional x3",
                "specialize beta_sum_functional l",
                "specialize beta_sum_functional n",
                "specialize beta_sum_functional m",
                "apply beta_sum_functional", "exact htransport",
                "exact hm_witness_witness_right",
            ),
            "The exact finite dot-product value is independent of its coding witness.",
        ),
        spec(
            BETA_DOT_PRODUCT_EXISTS_UNIQUE,
            f"forall mb mc sb sc l. exists n. (({dot}) /\\ forall m. ({dot_other}) -> n = m)",
            (BETA_DOT_PRODUCT_EXISTS, BETA_DOT_PRODUCT_FUNCTIONAL),
            (
                "intro mb", "intro mc", "intro sb", "intro sc", "intro l",
                f"specialize {BETA_DOT_PRODUCT_EXISTS} mb",
                f"specialize {BETA_DOT_PRODUCT_EXISTS} mc",
                f"specialize {BETA_DOT_PRODUCT_EXISTS} sb",
                f"specialize {BETA_DOT_PRODUCT_EXISTS} sc",
                f"specialize {BETA_DOT_PRODUCT_EXISTS} l",
                f"cases {BETA_DOT_PRODUCT_EXISTS}", "exists x", "split",
                f"exact {BETA_DOT_PRODUCT_EXISTS}_witness",
                "intro m", "intro hm",
                f"specialize {BETA_DOT_PRODUCT_FUNCTIONAL} mb",
                f"specialize {BETA_DOT_PRODUCT_FUNCTIONAL} mc",
                f"specialize {BETA_DOT_PRODUCT_FUNCTIONAL} sb",
                f"specialize {BETA_DOT_PRODUCT_FUNCTIONAL} sc",
                f"specialize {BETA_DOT_PRODUCT_FUNCTIONAL} l",
                f"specialize {BETA_DOT_PRODUCT_FUNCTIONAL} x",
                f"specialize {BETA_DOT_PRODUCT_FUNCTIONAL} m",
                f"apply {BETA_DOT_PRODUCT_FUNCTIONAL}",
                f"exact {BETA_DOT_PRODUCT_EXISTS}_witness", "exact hm",
            ),
            "Every pair of coded finite vectors has exactly one natural dot product.",
        ),
        spec(
            BETA_DOT_PRODUCT_EMPTY,
            f"forall mb mc sb sc n. ({dot_empty}) -> n = 0",
            ("beta_sum_zero",),
            (
                "intro mb", "intro mc", "intro sb", "intro sc", "intro n", "intro hdot",
                "cases hdot", "cases hdot_witness", "cases hdot_witness_witness",
                "specialize beta_sum_zero x", "specialize beta_sum_zero x1",
                "specialize beta_sum_zero n", "apply beta_sum_zero",
                "exact hdot_witness_witness_right",
            ),
            "The exact dot product of two empty finite vectors is zero.",
        ),
        spec(
            BETA_DOT_PRODUCT_COMMUTATIVE,
            f"forall mb mc sb sc l n. ({dot}) -> ({dot_reverse})",
            ("mul_comm",),
            (
                "intro mb", "intro mc", "intro sb", "intro sc", "intro l",
                "intro n", "intro hdot", "cases hdot", "cases hdot_witness",
                "cases hdot_witness_witness", "exists x", "exists x1", "split",
                "intro i", "intro a", "intro b", "intro z", "intro hi",
                "intro ha", "intro hb", "intro hz",
                "have hproduct : z = b * a",
                "specialize hdot_witness_witness_left i",
                "specialize hdot_witness_witness_left b",
                "specialize hdot_witness_witness_left a",
                "specialize hdot_witness_witness_left z",
                "apply hdot_witness_witness_left", "exact hi", "exact hb",
                "exact ha", "exact hz", "trans b * a", "exact hproduct",
                "specialize mul_comm b", "specialize mul_comm a", "exact mul_comm",
                "exact hdot_witness_witness_right",
            ),
            "Finite natural dot products are constructively symmetric.",
        ),
        spec(
            SIGNED_MATRIX_TWO_DETERMINANT_EXISTS,
            "forall a b c d. exists p n. (p = a * d /\\ n = b * c)",
            (),
            (
                "intro a", "intro b", "intro c", "intro d",
                "exists a * d", "exists b * c", "split", "refl", "refl",
            ),
            "Every natural 2-by-2 matrix has an exact signed-pair determinant witness.",
        ),
        spec(
            SIGNED_MATRIX_TWO_DETERMINANT_FUNCTIONAL,
            "forall a b c d p n q m. (p = a * d /\\ n = b * c) -> "
            "(q = a * d /\\ m = b * c) -> (p = q /\\ n = m)",
            (),
            (
                "intro a", "intro b", "intro c", "intro d", "intro p", "intro n",
                "intro q", "intro m", "intro hp", "intro hq", "cases hp",
                "cases hq", "split", "trans a * d", "exact hp_left", "symm",
                "exact hq_left", "trans b * c", "exact hp_right", "symm", "exact hq_right",
            ),
            "The positive/negative natural components of a 2-by-2 determinant are unique.",
        ),
    )


@dataclass(frozen=True, slots=True)
class IntegerMatrix:
    """A bounded immutable rectangular matrix of genuine Python integers."""

    rows: tuple[tuple[int, ...], ...]

    @property
    def height(self) -> int:
        return len(self.rows)

    @property
    def width(self) -> int:
        return len(self.rows[0]) if self.rows else 0


@dataclass(frozen=True, slots=True)
class MatrixProductCertificate:
    left: IntegerMatrix
    right: IntegerMatrix
    result: IntegerMatrix
    dot_terms: tuple[tuple[tuple[int, ...], ...], ...]


@dataclass(frozen=True, slots=True)
class DeterminantCertificate:
    matrix: IntegerMatrix
    positive_terms: tuple[int, ...]
    negative_terms: tuple[int, ...]
    value: int


def integer_matrix(rows: Iterable[Iterable[int]]) -> IntegerMatrix:
    try:
        normalized = tuple(tuple(row) for row in rows)
    except TypeError as error:
        raise MatrixCertificateError("matrix rows must be finite integer iterables") from error
    if len(normalized) > MAX_MATRIX_DIMENSION:
        raise MatrixCertificateError("matrix exceeds its bounded row dimension")
    width = len(normalized[0]) if normalized else 0
    if width > MAX_MATRIX_DIMENSION:
        raise MatrixCertificateError("matrix exceeds its bounded column dimension")
    if any(len(row) != width for row in normalized):
        raise MatrixCertificateError("integer matrix must be rectangular")
    if any(type(value) is not int for row in normalized for value in row):
        raise MatrixCertificateError("every matrix entry must be an exact integer")
    return IntegerMatrix(normalized)


def multiply_integer_matrices(
    left: IntegerMatrix, right: IntegerMatrix
) -> MatrixProductCertificate:
    if type(left) is not IntegerMatrix or type(right) is not IntegerMatrix:
        raise MatrixCertificateError("matrix multiplication requires exact matrix certificates")
    if left.width != right.height:
        raise MatrixCertificateError("matrix multiplication dimensions do not match")
    dot_terms = tuple(
        tuple(
            tuple(left.rows[row][index] * right.rows[index][column] for index in range(left.width))
            for column in range(right.width)
        )
        for row in range(left.height)
    )
    result = integer_matrix(tuple(sum(terms) for terms in row) for row in dot_terms)
    return MatrixProductCertificate(left, right, result, dot_terms)


def verify_matrix_product(receipt: MatrixProductCertificate) -> bool:
    if type(receipt) is not MatrixProductCertificate:
        return False
    try:
        return receipt == multiply_integer_matrices(receipt.left, receipt.right)
    except (MatrixCertificateError, IndexError, OverflowError, TypeError, ValueError):
        return False


def certify_integer_determinant(matrix: IntegerMatrix) -> DeterminantCertificate:
    if type(matrix) is not IntegerMatrix or matrix.height != matrix.width:
        raise MatrixCertificateError("determinants require an exact square integer matrix")
    if matrix.height > MAX_DETERMINANT_DIMENSION:
        raise MatrixCertificateError("determinant exceeds its bounded permutation budget")
    positive: list[int] = []
    negative: list[int] = []
    for permutation in permutations(range(matrix.height)):
        inversions = sum(
            permutation[left] > permutation[right]
            for left in range(len(permutation))
            for right in range(left + 1, len(permutation))
        )
        product = 1
        for row, column in enumerate(permutation):
            product *= matrix.rows[row][column]
        (negative if inversions % 2 else positive).append(product)
    return DeterminantCertificate(matrix, tuple(positive), tuple(negative), sum(positive) - sum(negative))


def verify_integer_determinant(receipt: DeterminantCertificate) -> bool:
    if type(receipt) is not DeterminantCertificate:
        return False
    try:
        return receipt == certify_integer_determinant(receipt.matrix)
    except (MatrixCertificateError, IndexError, OverflowError, TypeError, ValueError):
        return False


__all__ = [
    "BETA_DOT_PRODUCT_COMMUTATIVE",
    "BETA_DOT_PRODUCT_EMPTY",
    "BETA_DOT_PRODUCT_EXISTS",
    "BETA_DOT_PRODUCT_EXISTS_UNIQUE",
    "BETA_DOT_PRODUCT_FUNCTIONAL",
    "BETA_MATRIX_CELL_EXISTS",
    "BETA_MATRIX_CELL_EXISTS_UNIQUE",
    "BETA_MATRIX_CELL_FUNCTIONAL",
    "DeterminantCertificate",
    "IntegerMatrix",
    "MAX_DETERMINANT_DIMENSION",
    "MAX_MATRIX_DIMENSION",
    "MatrixCertificateError",
    "MatrixProductCertificate",
    "SIGNED_MATRIX_TWO_DETERMINANT_EXISTS",
    "SIGNED_MATRIX_TWO_DETERMINANT_FUNCTIONAL",
    "certify_integer_determinant",
    "dot_product_relation",
    "integer_matrix",
    "make_matrix_dot_product_candidate_theorems",
    "matrix_cell_relation",
    "multiply_integer_matrices",
    "verify_integer_determinant",
    "verify_matrix_product",
]
