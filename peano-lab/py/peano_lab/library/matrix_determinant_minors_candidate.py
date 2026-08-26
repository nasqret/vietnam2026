"""Constructive beta-coded cofactor minors and finite signed determinants.

All displayed relations are hygienic abbreviations for the unchanged
first-order Heyting-arithmetic signature.  The proof scripts below are
dependency-curried candidates: a later independently checked release bundle,
not this authoring module or its bounded Python certificates, establishes
checked-use authority.

The matrix-minor results quantify over unrestricted natural dimensions and
delete arbitrary valid rows and columns.  Explicit four-by-four determinants
do not silently imply arbitrary-dimensional determinant, rank, or lattice
theorems.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .finite_fold_surface import _beta_at_term, _binders, _identifier, _variables
from .matrix_dot_product_candidate import (
    MAX_DETERMINANT_DIMENSION,
    MAX_MATRIX_DIMENSION,
    DeterminantCertificate,
    IntegerMatrix,
    MatrixCertificateError,
    certify_integer_determinant,
    integer_matrix,
)


MATRIX_SKIP_INDEX_EXISTS = "matrix_skip_index_exists"
MATRIX_SKIP_INDEX_FUNCTIONAL = "matrix_skip_index_functional"
MATRIX_SKIP_INDEX_AVOIDS_REMOVED = "matrix_skip_index_avoids_removed"
MATRIX_SKIP_INDEX_BOUNDED = "matrix_skip_index_bounded"
BETA_MATRIX_MINOR_CELL_EXISTS = "beta_matrix_minor_cell_exists"
BETA_MATRIX_MINOR_CELL_FUNCTIONAL = "beta_matrix_minor_cell_functional"
BETA_MATRIX_MINOR_POINT_EXISTS = "beta_matrix_minor_point_exists"
BETA_MATRIX_MINOR_PREFIX_EXTEND = "beta_matrix_minor_prefix_extend"
BETA_MATRIX_MINOR_PREFIX_EXISTS_NONZERO = "beta_matrix_minor_prefix_exists_nonzero"
BETA_MATRIX_MINOR_PREFIX_EMPTY_EXISTS = "beta_matrix_minor_prefix_empty_exists"
BETA_MATRIX_MINOR_PREFIX_EXISTS = "beta_matrix_minor_prefix_exists"
BETA_MATRIX_MINOR_EXISTS = "beta_matrix_minor_exists"
BETA_SIGNED_MATRIX_MINOR_EXISTS = "beta_signed_matrix_minor_exists"
SIGNED_MATRIX_FOUR_COFACTOR_EXPANSION_EXISTS = (
    "signed_matrix_four_cofactor_expansion_exists"
)
SIGNED_MATRIX_FOUR_COFACTOR_EXPANSION_FUNCTIONAL = (
    "signed_matrix_four_cofactor_expansion_functional"
)
SIGNED_MATRIX_FOUR_FULL_DETERMINANT_EXISTS = (
    "signed_matrix_four_full_determinant_exists"
)
SIGNED_MATRIX_FOUR_FULL_DETERMINANT_FUNCTIONAL = (
    "signed_matrix_four_full_determinant_functional"
)
MAX_COFACTOR_DIMENSION = min(MAX_DETERMINANT_DIMENSION, 7)
MAX_COFACTOR_ENTRY = 1 << 20


class MatrixMinorError(ValueError):
    """An authoring surface or bounded executable minor is invalid."""


def _safe_tag(tag: str) -> str:
    try:
        return _identifier(tag, "matrix-minor binder tag")
    except ValueError as error:
        raise MatrixMinorError(str(error)) from error


def _lt_terms(left: str, right: str, *, tag: str, avoid: tuple[str, ...]) -> str:
    (gap,) = _binders(f"mdm_lt_{tag}", avoid, ("gap",))
    return f"exists {gap}. {gap} + S ({left}) = ({right})"


def _le_terms(left: str, right: str, *, tag: str, avoid: tuple[str, ...]) -> str:
    (gap,) = _binders(f"mdm_le_{tag}", avoid, ("gap",))
    return f"exists {gap}. {gap} + ({left}) = ({right})"


def _skip_terms(
    index: str,
    removed: str,
    source: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    before = _lt_terms(index, removed, tag=f"{tag}_before", avoid=avoid)
    after = _le_terms(removed, index, tag=f"{tag}_after", avoid=avoid)
    return (
        f"((({before}) /\\ {source} = {index}) \\/ "
        f"(({after}) /\\ {source} = S {index}))"
    )


def matrix_skip_index_relation(
    index: str, removed: str, source: str, *, tag: str
) -> str:
    """Expand the unique index map that omits one arbitrary coordinate."""

    try:
        arguments = _variables(
            (index, "minor coordinate"),
            (removed, "removed coordinate"),
            (source, "original matrix coordinate"),
        )
        safe_tag = _safe_tag(tag)
        return _skip_terms(*arguments, tag=safe_tag, avoid=arguments)
    except ValueError as error:
        raise MatrixMinorError(str(error)) from error


def _minor_cell_terms(
    code: str,
    scale: str,
    width: str,
    removed_row: str,
    removed_column: str,
    row: str,
    column: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    source_row, source_column = _binders(
        f"mdm_cell_{tag}", avoid, ("row", "column")
    )
    nested_avoid = avoid + (source_row, source_column)
    row_mapping = _skip_terms(
        row, removed_row, source_row, tag=f"{tag}_row", avoid=nested_avoid
    )
    column_mapping = _skip_terms(
        column,
        removed_column,
        source_column,
        tag=f"{tag}_column",
        avoid=nested_avoid,
    )
    decoded = _beta_at_term(
        code,
        scale,
        f"({source_row}) * ({width}) + ({source_column})",
        value,
        tag=f"mdm_{tag}_source",
        avoid=nested_avoid,
    )
    return (
        f"exists {source_row} {source_column}. "
        f"(({row_mapping}) /\\ (({column_mapping}) /\\ ({decoded})))"
    )


def matrix_minor_cell_relation(
    code: str,
    scale: str,
    width: str,
    removed_row: str,
    removed_column: str,
    row: str,
    column: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand one genuine source entry of an arbitrary cofactor minor."""

    try:
        arguments = _variables(
            (code, "matrix code"),
            (scale, "matrix scale"),
            (width, "matrix width"),
            (removed_row, "removed row"),
            (removed_column, "removed column"),
            (row, "minor row"),
            (column, "minor column"),
            (value, "matrix entry"),
        )
        safe_tag = _safe_tag(tag)
        return _minor_cell_terms(*arguments, tag=safe_tag, avoid=arguments)
    except ValueError as error:
        raise MatrixMinorError(str(error)) from error


def _minor_point_terms(
    code: str,
    scale: str,
    width: str,
    removed_row: str,
    removed_column: str,
    minor_width: str,
    index: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    row, column, value = _binders(
        f"mdm_point_{tag}", avoid, ("row", "column", "value")
    )
    nested_avoid = avoid + (row, column, value)
    bounded = _lt_terms(
        column, minor_width, tag=f"{tag}_column_bound", avoid=nested_avoid
    )
    cell = _minor_cell_terms(
        code,
        scale,
        width,
        removed_row,
        removed_column,
        row,
        column,
        value,
        tag=f"{tag}_cell",
        avoid=nested_avoid,
    )
    return (
        f"exists {row} {column} {value}. "
        f"({index} = ({minor_width}) * {row} + {column} /\\ "
        f"(({bounded}) /\\ ({cell})))"
    )


def _minor_prefix_terms(
    code: str,
    scale: str,
    width: str,
    removed_row: str,
    removed_column: str,
    target_code: str,
    target_scale: str,
    minor_width: str,
    length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    index, row, column, value = _binders(
        f"mdm_prefix_{tag}", avoid, ("index", "row", "column", "value")
    )
    nested_avoid = avoid + (index, row, column, value)
    bounded_index = _lt_terms(
        index, length, tag=f"{tag}_index_bound", avoid=nested_avoid
    )
    bounded_column = _lt_terms(
        column, minor_width, tag=f"{tag}_column_bound", avoid=nested_avoid
    )
    cell = _minor_cell_terms(
        code,
        scale,
        width,
        removed_row,
        removed_column,
        row,
        column,
        value,
        tag=f"{tag}_cell",
        avoid=nested_avoid,
    )
    target = _beta_at_term(
        target_code,
        target_scale,
        index,
        value,
        tag=f"mdm_{tag}_target",
        avoid=nested_avoid,
    )
    return (
        f"forall {index}. ({bounded_index}) -> exists {row} {column} {value}. "
        f"({index} = ({minor_width}) * {row} + {column} /\\ "
        f"(({bounded_column}) /\\ (({cell}) /\\ ({target}))))"
    )


def matrix_minor_prefix_relation(
    code: str,
    scale: str,
    width: str,
    removed_row: str,
    removed_column: str,
    target_code: str,
    target_scale: str,
    minor_width: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand every exact row-major entry of a beta-coded cofactor minor."""

    try:
        arguments = _variables(
            (code, "matrix code"),
            (scale, "matrix scale"),
            (width, "matrix width"),
            (removed_row, "removed row"),
            (removed_column, "removed column"),
            (target_code, "minor code"),
            (target_scale, "minor scale"),
            (minor_width, "minor width"),
            (length, "encoded prefix length"),
        )
        safe_tag = _safe_tag(tag)
        return _minor_prefix_terms(*arguments, tag=safe_tag, avoid=arguments)
    except ValueError as error:
        raise MatrixMinorError(str(error)) from error


def _signed_minor_terms(
    positive_code: str,
    positive_scale: str,
    negative_code: str,
    negative_scale: str,
    width: str,
    removed_row: str,
    removed_column: str,
    minor_width: str,
    target_positive_code: str,
    target_positive_scale: str,
    target_negative_code: str,
    target_negative_scale: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    positive = _minor_prefix_terms(
        positive_code,
        positive_scale,
        width,
        removed_row,
        removed_column,
        target_positive_code,
        target_positive_scale,
        minor_width,
        f"({minor_width}) * ({minor_width})",
        tag=f"{tag}_positive",
        avoid=avoid,
    )
    negative = _minor_prefix_terms(
        negative_code,
        negative_scale,
        width,
        removed_row,
        removed_column,
        target_negative_code,
        target_negative_scale,
        minor_width,
        f"({minor_width}) * ({minor_width})",
        tag=f"{tag}_negative",
        avoid=avoid,
    )
    return f"(({positive}) /\\ ({negative}))"


def signed_matrix_minor_relation(
    positive_code: str,
    positive_scale: str,
    negative_code: str,
    negative_scale: str,
    width: str,
    removed_row: str,
    removed_column: str,
    minor_width: str,
    target_positive_code: str,
    target_positive_scale: str,
    target_negative_code: str,
    target_negative_scale: str,
    *,
    tag: str,
) -> str:
    """Expand both complete natural-component codes of a signed minor."""

    try:
        arguments = _variables(
            (positive_code, "positive source code"),
            (positive_scale, "positive source scale"),
            (negative_code, "negative source code"),
            (negative_scale, "negative source scale"),
            (width, "source matrix width"),
            (removed_row, "removed row"),
            (removed_column, "removed column"),
            (minor_width, "minor width"),
            (target_positive_code, "positive minor code"),
            (target_positive_scale, "positive minor scale"),
            (target_negative_code, "negative minor code"),
            (target_negative_scale, "negative minor scale"),
        )
        safe_tag = _safe_tag(tag)
        return _signed_minor_terms(*arguments, tag=safe_tag, avoid=arguments)
    except ValueError as error:
        raise MatrixMinorError(str(error)) from error


def _pair_product_terms(
    left: tuple[str, str], right: tuple[str, str]
) -> tuple[str, str]:
    return (
        f"(({left[0]}) * ({right[0]}) + ({left[1]}) * ({right[1]}))",
        f"(({left[0]}) * ({right[1]}) + ({left[1]}) * ({right[0]}))",
    )


def _pair_add_terms(
    left: tuple[str, str], right: tuple[str, str]
) -> tuple[str, str]:
    return (
        f"(({left[0]}) + ({right[0]}))",
        f"(({left[1]}) + ({right[1]}))",
    )


def _pair_subtract_terms(
    left: tuple[str, str], right: tuple[str, str]
) -> tuple[str, str]:
    return (
        f"(({left[0]}) + ({right[1]}))",
        f"(({left[1]}) + ({right[0]}))",
    )


def _cofactor_expansion_terms(
    first_row: tuple[tuple[str, str], ...],
    minors: tuple[tuple[str, str], ...],
) -> tuple[str, str]:
    if len(first_row) != len(minors) or not first_row:
        raise MatrixMinorError("cofactor expansion requires equal nonempty rows")
    result = _pair_product_terms(first_row[0], minors[0])
    for column, (entry, minor) in enumerate(zip(first_row[1:], minors[1:]), 1):
        product = _pair_product_terms(entry, minor)
        result = (
            _pair_subtract_terms(result, product)
            if column % 2
            else _pair_add_terms(result, product)
        )
    return result


def _signed_determinant_terms(
    rows: tuple[tuple[tuple[str, str], ...], ...],
) -> tuple[str, str]:
    if not rows:
        return ("1", "0")
    if any(len(row) != len(rows) for row in rows):
        raise MatrixMinorError("formal determinant terms require a square matrix")
    if len(rows) == 1:
        return rows[0][0]
    minors = tuple(
        _signed_determinant_terms(
            tuple(row[:column] + row[column + 1 :] for row in rows[1:])
        )
        for column in range(len(rows))
    )
    return _cofactor_expansion_terms(rows[0], minors)


def make_matrix_determinant_minors_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build dependency-ordered original-kernel matrix-minor candidates."""

    skip = _skip_terms("i", "r", "s", tag="result", avoid=("i", "r", "s"))
    skip_other = _skip_terms(
        "i", "r", "t", tag="other", avoid=("i", "r", "t")
    )
    below_width = _lt_terms(
        "i", "q", tag="bounded_input", avoid=("i", "r", "s", "q")
    )
    below_successor = _lt_terms(
        "s", "S q", tag="bounded_output", avoid=("i", "r", "s", "q")
    )
    cell = _minor_cell_terms(
        "b", "c", "w", "r", "d", "i", "j", "z",
        tag="cell_result", avoid=("b", "c", "w", "r", "d", "i", "j", "z")
    )
    other_cell = _minor_cell_terms(
        "b", "c", "w", "r", "d", "i", "j", "t",
        tag="cell_other", avoid=("b", "c", "w", "r", "d", "i", "j", "t")
    )
    point = _minor_point_terms(
        "b", "c", "w", "r", "d", "q", "k",
        tag="point_result", avoid=("b", "c", "w", "r", "d", "q", "k")
    )
    point_last = _minor_point_terms(
        "b", "c", "w", "r", "d", "q", "l",
        tag="prefix_last", avoid=("b", "c", "w", "r", "d", "q", "l")
    )
    prefix_before = _minor_prefix_terms(
        "b", "c", "w", "r", "d", "u", "v", "q", "l",
        tag="prefix_before", avoid=("b", "c", "w", "r", "d", "u", "v", "q", "l")
    )
    prefix_after = _minor_prefix_terms(
        "b", "c", "w", "r", "d", "z", "e", "q", "S l",
        tag="prefix_after", avoid=("b", "c", "w", "r", "d", "z", "e", "q", "l")
    )
    prefix_result = _minor_prefix_terms(
        "b", "c", "w", "r", "d", "u", "v", "q", "l",
        tag="prefix_result", avoid=("b", "c", "w", "r", "d", "u", "v", "q", "l")
    )
    prefix_previous = _minor_prefix_terms(
        "b", "c", "w", "r", "d", "u", "v", "q", "l",
        tag="prefix_previous", avoid=("b", "c", "w", "r", "d", "u", "v", "q", "l")
    )
    prefix_empty = _minor_prefix_terms(
        "b", "c", "w", "r", "d", "u", "v", "q", "0",
        tag="prefix_empty", avoid=("b", "c", "w", "r", "d", "u", "v", "q")
    )
    prefix_full = _minor_prefix_terms(
        "b", "c", "w", "r", "d", "u", "v", "q", "h * q",
        tag="prefix_full", avoid=("b", "c", "w", "r", "d", "u", "v", "q", "h")
    )
    square_minor = _minor_prefix_terms(
        "b", "c", "S q", "r", "d", "u", "v", "q", "q * q",
        tag="square_minor", avoid=("b", "c", "q", "r", "d", "u", "v")
    )
    removed_row_bound = _lt_terms(
        "r", "S q", tag="removed_row", avoid=("q", "r", "d")
    )
    removed_column_bound = _lt_terms(
        "d", "S q", tag="removed_column", avoid=("q", "r", "d")
    )
    signed_minor = _signed_minor_terms(
        "pb", "pc", "nb", "nc", "S q", "r", "d", "q", "up", "us", "un", "ut",
        tag="signed_minor", avoid=("pb", "pc", "nb", "nc", "q", "r", "d", "up", "us", "un", "ut")
    )
    cofactor_variables = (
        "ap", "an", "bp", "bn", "cp", "cn", "dp", "dn",
        "up", "un", "vp", "vn", "wp", "wn", "xp", "xn",
    )
    first_row = (("ap", "an"), ("bp", "bn"), ("cp", "cn"), ("dp", "dn"))
    cofactor_minors = (("up", "un"), ("vp", "vn"), ("wp", "wn"), ("xp", "xn"))
    cofactor_positive, cofactor_negative = _cofactor_expansion_terms(
        first_row, cofactor_minors
    )
    four_matrix = tuple(
        tuple((f"a{row}{column}p", f"a{row}{column}n") for column in range(4))
        for row in range(4)
    )
    four_variables = tuple(component for row in four_matrix for pair in row for component in pair)
    four_minors = tuple(
        _signed_determinant_terms(
            tuple(row[:column] + row[column + 1 :] for row in four_matrix[1:])
        )
        for column in range(4)
    )
    determinant_positive, determinant_negative = _cofactor_expansion_terms(
        four_matrix[0], four_minors
    )

    return (
        spec(
            MATRIX_SKIP_INDEX_EXISTS,
            f"forall i r. exists s. ({skip})",
            ("le_or_lt",),
            (
                "intro i",
                "intro r",
                "specialize le_or_lt r",
                "specialize le_or_lt i",
                "cases le_or_lt",
                "exists S i",
                "right",
                "split",
                "exact le_or_lt_left",
                "refl",
                "exists i",
                "left",
                "split",
                "exact le_or_lt_right",
                "refl",
            ),
            "Every minor coordinate has a constructive source coordinate that skips an arbitrary deleted index.",
        ),
        spec(
            MATRIX_SKIP_INDEX_FUNCTIONAL,
            f"forall i r s t. ({skip}) -> ({skip_other}) -> s = t",
            ("lt_not_le",),
            (
                "intro i",
                "intro r",
                "intro s",
                "intro t",
                "intro hfirst",
                "intro hsecond",
                "cases hfirst",
                "cases hfirst_left",
                "cases hsecond",
                "cases hsecond_left",
                "trans i",
                "exact hfirst_left_right",
                "symm",
                "exact hsecond_left_right",
                "cases hsecond_right",
                "exfalso",
                "specialize lt_not_le i",
                "specialize lt_not_le r",
                "apply lt_not_le",
                "exact hfirst_left_left",
                "exact hsecond_right_left",
                "cases hfirst_right",
                "cases hsecond",
                "cases hsecond_left",
                "exfalso",
                "specialize lt_not_le i",
                "specialize lt_not_le r",
                "apply lt_not_le",
                "exact hsecond_left_left",
                "exact hfirst_right_left",
                "cases hsecond_right",
                "trans S i",
                "exact hfirst_right_right",
                "symm",
                "exact hsecond_right_right",
            ),
            "Deleting one coordinate induces a unique source coordinate, including both threshold branches.",
        ),
        spec(
            MATRIX_SKIP_INDEX_AVOIDS_REMOVED,
            f"forall i r s. ({skip}) -> ~(s = r)",
            ("lt_irrefl_expanded", "succ_le_succ"),
            (
                "intro i", "intro r", "intro s", "intro hskip", "intro hequal",
                "cases hskip",
                "cases hskip_left",
                "have heqi : i = r",
                "trans s", "symm", "exact hskip_left_right", "exact hequal",
                "rewrite heqi at hskip_left_left",
                "specialize lt_irrefl_expanded r",
                "apply lt_irrefl_expanded", "exact hskip_left_left",
                "cases hskip_right",
                "have hbound : exists gap. gap + S r = S i",
                "specialize succ_le_succ r", "specialize succ_le_succ i",
                "apply succ_le_succ", "exact hskip_right_left",
                "have heqi : S i = r",
                "trans s", "symm", "exact hskip_right_right", "exact hequal",
                "rewrite heqi at hbound",
                "specialize lt_irrefl_expanded r",
                "apply lt_irrefl_expanded", "exact hbound",
            ),
            "A skipped matrix coordinate never equals the row or column that was actually deleted.",
        ),
        spec(
            MATRIX_SKIP_INDEX_BOUNDED,
            f"forall i r s q. ({skip}) -> ({below_width}) -> ({below_successor})",
            ("lt_of_lt_of_le", "le_succ_self", "succ_le_succ"),
            (
                "intro i", "intro r", "intro s", "intro q",
                "intro hskip", "intro hbound", "cases hskip",
                "cases hskip_left", "rewrite hskip_left_right",
                "specialize lt_of_lt_of_le i", "specialize lt_of_lt_of_le q",
                "specialize lt_of_lt_of_le (S q)", "apply lt_of_lt_of_le",
                "exact hbound", "specialize le_succ_self q", "exact le_succ_self",
                "cases hskip_right", "rewrite hskip_right_right",
                "specialize succ_le_succ (S i)", "specialize succ_le_succ q",
                "apply succ_le_succ", "exact hbound",
            ),
            "Every minor coordinate below width q maps to an original coordinate strictly below S q.",
        ),
        spec(
            BETA_MATRIX_MINOR_CELL_EXISTS,
            f"forall b c w r d i j. exists z. ({cell})",
            (MATRIX_SKIP_INDEX_EXISTS, "beta_at_exists"),
            (
                "intro b", "intro c", "intro w", "intro r", "intro d",
                "intro i", "intro j",
                f"have hrow : exists s. ({_skip_terms('i','r','s',tag='cell_have_row',avoid=('i','r','s'))})",
                f"specialize {MATRIX_SKIP_INDEX_EXISTS} i",
                f"specialize {MATRIX_SKIP_INDEX_EXISTS} r",
                f"exact {MATRIX_SKIP_INDEX_EXISTS}", "cases hrow",
                f"have hcolumn : exists s. ({_skip_terms('j','d','s',tag='cell_have_column',avoid=('j','d','s'))})",
                f"specialize {MATRIX_SKIP_INDEX_EXISTS} j",
                f"specialize {MATRIX_SKIP_INDEX_EXISTS} d",
                f"exact {MATRIX_SKIP_INDEX_EXISTS}", "cases hcolumn",
                f"have hvalue : exists z. ({_beta_at_term('b','c','x * w + x1','z',tag='mdm_cell_have_value',avoid=('b','c','x','w','x1','z'))})",
                "specialize beta_at_exists b", "specialize beta_at_exists c",
                "specialize beta_at_exists (x * w + x1)",
                "exact beta_at_exists", "cases hvalue",
                "exists x2", "exists x", "exists x1", "split",
                "exact hrow_witness", "split", "exact hcolumn_witness",
                "exact hvalue_witness",
            ),
            "Every coordinate of an arbitrary deleted-row/deleted-column matrix minor has its exact decoded source value.",
        ),
        spec(
            BETA_MATRIX_MINOR_CELL_FUNCTIONAL,
            f"forall b c w r d i j z t. ({cell}) -> ({other_cell}) -> z = t",
            (MATRIX_SKIP_INDEX_FUNCTIONAL, "beta_at_unique"),
            (
                "intro b", "intro c", "intro w", "intro r", "intro d",
                "intro i", "intro j", "intro z", "intro t",
                "intro hfirst", "intro hsecond",
                "cases hfirst", "cases hfirst_witness",
                "cases hfirst_witness_witness",
                "cases hfirst_witness_witness_right",
                "cases hsecond", "cases hsecond_witness",
                "cases hsecond_witness_witness",
                "cases hsecond_witness_witness_right",
                "have hrow : x = x2",
                f"specialize {MATRIX_SKIP_INDEX_FUNCTIONAL} i",
                f"specialize {MATRIX_SKIP_INDEX_FUNCTIONAL} r",
                f"specialize {MATRIX_SKIP_INDEX_FUNCTIONAL} x",
                f"specialize {MATRIX_SKIP_INDEX_FUNCTIONAL} x2",
                f"apply {MATRIX_SKIP_INDEX_FUNCTIONAL}",
                "exact hfirst_witness_witness_left",
                "exact hsecond_witness_witness_left",
                "have hcolumn : x1 = x3",
                f"specialize {MATRIX_SKIP_INDEX_FUNCTIONAL} j",
                f"specialize {MATRIX_SKIP_INDEX_FUNCTIONAL} d",
                f"specialize {MATRIX_SKIP_INDEX_FUNCTIONAL} x1",
                f"specialize {MATRIX_SKIP_INDEX_FUNCTIONAL} x3",
                f"apply {MATRIX_SKIP_INDEX_FUNCTIONAL}",
                "exact hfirst_witness_witness_right_left",
                "exact hsecond_witness_witness_right_left",
                "rewrite hrow at hfirst_witness_witness_right_right",
                "rewrite hrow at hfirst_witness_witness_right_right",
                "rewrite hcolumn at hfirst_witness_witness_right_right",
                "rewrite hcolumn at hfirst_witness_witness_right_right",
                "specialize beta_at_unique b", "specialize beta_at_unique c",
                "specialize beta_at_unique (x2 * w + x3)",
                "specialize beta_at_unique z", "specialize beta_at_unique t",
                "apply beta_at_unique",
                "exact hfirst_witness_witness_right_right",
                "exact hsecond_witness_witness_right_right",
            ),
            "The decoded value of a beta-coded cofactor minor is independent of every skipped-coordinate witness.",
        ),
        spec(
            BETA_MATRIX_MINOR_POINT_EXISTS,
            f"forall b c w r d q k. ~(q = 0) -> ({point})",
            ("division_remainder_exists", BETA_MATRIX_MINOR_CELL_EXISTS),
            (
                "intro b", "intro c", "intro w", "intro r", "intro d",
                "intro q", "intro k", "intro hq",
                "have hcoordinates : exists i j. k = q * i + j /\\ exists gap. gap + S j = q",
                "specialize division_remainder_exists q",
                "specialize division_remainder_exists k",
                "apply division_remainder_exists", "exact hq",
                "cases hcoordinates", "cases hcoordinates_witness",
                "cases hcoordinates_witness_witness",
                f"have hcell : exists z. ({_minor_cell_terms('b','c','w','r','d','x','x1','z',tag='point_have_cell',avoid=('b','c','w','r','d','x','x1','z'))})",
                f"specialize {BETA_MATRIX_MINOR_CELL_EXISTS} b",
                f"specialize {BETA_MATRIX_MINOR_CELL_EXISTS} c",
                f"specialize {BETA_MATRIX_MINOR_CELL_EXISTS} w",
                f"specialize {BETA_MATRIX_MINOR_CELL_EXISTS} r",
                f"specialize {BETA_MATRIX_MINOR_CELL_EXISTS} d",
                f"specialize {BETA_MATRIX_MINOR_CELL_EXISTS} x",
                f"specialize {BETA_MATRIX_MINOR_CELL_EXISTS} x1",
                f"exact {BETA_MATRIX_MINOR_CELL_EXISTS}", "cases hcell",
                "exists x", "exists x1", "exists x2", "split",
                "exact hcoordinates_witness_witness_left", "split",
                "exact hcoordinates_witness_witness_right", "exact hcell_witness",
            ),
            "Every flat index of a nonempty cofactor-minor row has genuine quotient, remainder and skipped-source witnesses.",
        ),
        spec(
            BETA_MATRIX_MINOR_PREFIX_EXTEND,
            f"forall b c w r d u v q l. ({prefix_before}) -> ({point_last}) -> exists z e. ({prefix_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                "intro b", "intro c", "intro w", "intro r", "intro d",
                "intro u", "intro v", "intro q", "intro l",
                "intro hprevious", "intro hpoint",
                "cases hpoint", "cases hpoint_witness",
                "cases hpoint_witness_witness",
                "cases hpoint_witness_witness_witness",
                "cases hpoint_witness_witness_witness_right",
                "specialize beta_prefix_extend l", "specialize beta_prefix_extend u",
                "specialize beta_prefix_extend v", "specialize beta_prefix_extend x2",
                "cases beta_prefix_extend", "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x3", "exists x4", "intro k", "intro hk",
                "have hsplit : k = l \\/ exists gap. gap + S k = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt k",
                "apply finite_lt_succ_eq_or_lt", "exact hk", "cases hsplit",
                "exists x", "exists x1", "exists x2", "split",
                "rewrite hsplit_left",
                "exact hpoint_witness_witness_witness_left",
                "split", "exact hpoint_witness_witness_witness_right_left",
                "split", "exact hpoint_witness_witness_witness_right_right",
                "rewrite hsplit_left", "rewrite hsplit_left",
                "exact beta_prefix_extend_witness_witness_left",
                f"have hold : exists i j z. (k = q * i + j /\\ (({_lt_terms('j','q',tag='extend_old_column',avoid=('j','q','k','i','z'))}) /\\ (({_minor_cell_terms('b','c','w','r','d','i','j','z',tag='extend_old_cell',avoid=('b','c','w','r','d','i','j','z','k','q'))}) /\\ ({_beta_at_term('u','v','k','z',tag='mdm_extend_old_output',avoid=('u','v','k','z'))}))))",
                "specialize hprevious k", "apply hprevious", "exact hsplit_right",
                "cases hold", "cases hold_witness", "cases hold_witness_witness",
                "cases hold_witness_witness_witness",
                "cases hold_witness_witness_witness_right",
                "cases hold_witness_witness_witness_right_right",
                "exists x5", "exists x6", "exists x7", "split",
                "exact hold_witness_witness_witness_left", "split",
                "exact hold_witness_witness_witness_right_left", "split",
                "exact hold_witness_witness_witness_right_right_left",
                "specialize beta_prefix_extend_witness_witness_right k",
                "specialize beta_prefix_extend_witness_witness_right x7",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_witness_witness_right_right_right",
            ),
            "Extend one exact row-major beta-coded cofactor minor while preserving every earlier skipped-source entry.",
        ),
        spec(
            BETA_MATRIX_MINOR_PREFIX_EXISTS_NONZERO,
            f"forall b c w r d q l. ~(q = 0) -> exists u v. ({prefix_result})",
            (
                "add_eq_zero_right", "succ_ne_zero",
                BETA_MATRIX_MINOR_POINT_EXISTS, BETA_MATRIX_MINOR_PREFIX_EXTEND,
            ),
            (
                "intro b", "intro c", "intro w", "intro r", "intro d",
                "intro q", "induction l", "intro hq",
                "exists 0", "exists 0", "intro k", "intro hk", "exfalso",
                "cases hk", "have hzero : S k = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S k)",
                "apply add_eq_zero_right", "exact hk_witness",
                "specialize succ_ne_zero k", "apply succ_ne_zero", "exact hzero",
                "intro hq",
                f"have hprevious : exists u v. ({prefix_previous})",
                "apply IH", "exact hq", "cases hprevious",
                "cases hprevious_witness",
                f"have hpoint : {_minor_point_terms('b','c','w','r','d','q','l',tag='exists_have_point',avoid=('b','c','w','r','d','q','l'))}",
                f"specialize {BETA_MATRIX_MINOR_POINT_EXISTS} b",
                f"specialize {BETA_MATRIX_MINOR_POINT_EXISTS} c",
                f"specialize {BETA_MATRIX_MINOR_POINT_EXISTS} w",
                f"specialize {BETA_MATRIX_MINOR_POINT_EXISTS} r",
                f"specialize {BETA_MATRIX_MINOR_POINT_EXISTS} d",
                f"specialize {BETA_MATRIX_MINOR_POINT_EXISTS} q",
                f"specialize {BETA_MATRIX_MINOR_POINT_EXISTS} l",
                f"apply {BETA_MATRIX_MINOR_POINT_EXISTS}", "exact hq",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXTEND} b",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXTEND} c",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXTEND} w",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXTEND} r",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXTEND} d",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXTEND} x",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXTEND} x1",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXTEND} q",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXTEND} l",
                f"apply {BETA_MATRIX_MINOR_PREFIX_EXTEND}",
                "exact hprevious_witness_witness", "exact hpoint",
            ),
            "Every finite prefix of a nonempty arbitrary-dimensional cofactor minor has one complete beta code.",
        ),
        spec(
            BETA_MATRIX_MINOR_PREFIX_EMPTY_EXISTS,
            f"forall b c w r d q. exists u v. ({prefix_empty})",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro b", "intro c", "intro w", "intro r", "intro d",
                "intro q", "exists 0", "exists 0", "intro k", "intro hk",
                "exfalso", "cases hk", "have hzero : S k = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S k)",
                "apply add_eq_zero_right", "exact hk_witness",
                "specialize succ_ne_zero k", "apply succ_ne_zero", "exact hzero",
            ),
            "The zero-dimensional cofactor minor has an unconditional constructive empty beta code.",
        ),
        spec(
            BETA_MATRIX_MINOR_PREFIX_EXISTS,
            f"forall b c w r d q h. exists u v. ({prefix_full})",
            (
                "eq_decidable", BETA_MATRIX_MINOR_PREFIX_EMPTY_EXISTS,
                BETA_MATRIX_MINOR_PREFIX_EXISTS_NONZERO,
            ),
            (
                "intro b", "intro c", "intro w", "intro r", "intro d",
                "intro q", "intro h", "specialize eq_decidable q",
                "specialize eq_decidable 0", "cases eq_decidable",
                "have hlength : h * q = 0", "rewrite eq_decidable_left",
                "apply PA5", "rewrite hlength",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EMPTY_EXISTS} b",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EMPTY_EXISTS} c",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EMPTY_EXISTS} w",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EMPTY_EXISTS} r",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EMPTY_EXISTS} d",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EMPTY_EXISTS} q",
                f"exact {BETA_MATRIX_MINOR_PREFIX_EMPTY_EXISTS}",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXISTS_NONZERO} b",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXISTS_NONZERO} c",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXISTS_NONZERO} w",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXISTS_NONZERO} r",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXISTS_NONZERO} d",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXISTS_NONZERO} q",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXISTS_NONZERO} (h * q)",
                f"apply {BETA_MATRIX_MINOR_PREFIX_EXISTS_NONZERO}",
                "exact eq_decidable_right",
            ),
            "Every arbitrary finite rectangular deleted-row/deleted-column matrix prefix is beta-coded, including width zero.",
        ),
        spec(
            BETA_MATRIX_MINOR_EXISTS,
            f"forall b c q r d. ({removed_row_bound}) -> ({removed_column_bound}) -> exists u v. ({square_minor})",
            (BETA_MATRIX_MINOR_PREFIX_EXISTS,),
            (
                "intro b", "intro c", "intro q", "intro r", "intro d",
                "intro hrow", "intro hcolumn",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXISTS} b",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXISTS} c",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXISTS} (S q)",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXISTS} r",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXISTS} d",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXISTS} q",
                f"specialize {BETA_MATRIX_MINOR_PREFIX_EXISTS} q",
                f"exact {BETA_MATRIX_MINOR_PREFIX_EXISTS}",
            ),
            "Deleting any valid row and column from an unrestricted square beta-coded natural matrix constructs its complete exact square cofactor minor.",
        ),
        spec(
            BETA_SIGNED_MATRIX_MINOR_EXISTS,
            f"forall pb pc nb nc q r d. ({removed_row_bound}) -> ({removed_column_bound}) -> exists up us un ut. ({signed_minor})",
            (BETA_MATRIX_MINOR_EXISTS,),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro q",
                "intro r", "intro d", "intro hrow", "intro hcolumn",
                f"have hpositive : exists up us. ({_minor_prefix_terms('pb','pc','S q','r','d','up','us','q','q * q',tag='signed_have_positive',avoid=('pb','pc','q','r','d','up','us'))})",
                f"specialize {BETA_MATRIX_MINOR_EXISTS} pb",
                f"specialize {BETA_MATRIX_MINOR_EXISTS} pc",
                f"specialize {BETA_MATRIX_MINOR_EXISTS} q",
                f"specialize {BETA_MATRIX_MINOR_EXISTS} r",
                f"specialize {BETA_MATRIX_MINOR_EXISTS} d",
                f"apply {BETA_MATRIX_MINOR_EXISTS}", "exact hrow", "exact hcolumn",
                "cases hpositive", "cases hpositive_witness",
                f"have hnegative : exists un ut. ({_minor_prefix_terms('nb','nc','S q','r','d','un','ut','q','q * q',tag='signed_have_negative',avoid=('nb','nc','q','r','d','un','ut'))})",
                f"specialize {BETA_MATRIX_MINOR_EXISTS} nb",
                f"specialize {BETA_MATRIX_MINOR_EXISTS} nc",
                f"specialize {BETA_MATRIX_MINOR_EXISTS} q",
                f"specialize {BETA_MATRIX_MINOR_EXISTS} r",
                f"specialize {BETA_MATRIX_MINOR_EXISTS} d",
                f"apply {BETA_MATRIX_MINOR_EXISTS}", "exact hrow", "exact hcolumn",
                "cases hnegative", "cases hnegative_witness",
                "exists x", "exists x1", "exists x2", "exists x3", "split",
                "exact hpositive_witness_witness",
                "exact hnegative_witness_witness",
            ),
            "Every arbitrary-dimensional signed integer matrix has the complete exact beta-coded minor obtained by deleting any valid row and column.",
        ),
        spec(
            SIGNED_MATRIX_FOUR_COFACTOR_EXPANSION_EXISTS,
            f"forall {' '.join(cofactor_variables)}. exists p n. (p = {cofactor_positive} /\\ n = {cofactor_negative})",
            (),
            (
                *tuple(f"intro {name}" for name in cofactor_variables),
                f"exists {cofactor_positive}", f"exists {cofactor_negative}",
                "split", "refl", "refl",
            ),
            "Four arbitrary signed first-row entries and four signed minor determinants have their exact alternating subtraction-free Laplace cofactor expansion.",
        ),
        spec(
            SIGNED_MATRIX_FOUR_COFACTOR_EXPANSION_FUNCTIONAL,
            f"forall {' '.join(cofactor_variables)} p n q m. "
            f"(p = {cofactor_positive} /\\ n = {cofactor_negative}) -> "
            f"(q = {cofactor_positive} /\\ m = {cofactor_negative}) -> "
            "(p = q /\\ n = m)",
            (),
            (
                *tuple(f"intro {name}" for name in cofactor_variables),
                "intro p", "intro n", "intro q", "intro m",
                "intro hfirst", "intro hsecond", "cases hfirst", "cases hsecond",
                "split", f"trans {cofactor_positive}", "exact hfirst_left",
                "symm", "exact hsecond_left", f"trans {cofactor_negative}",
                "exact hfirst_right", "symm", "exact hsecond_right",
            ),
            "Both natural components of a four-term signed Laplace cofactor expansion are unique.",
        ),
        spec(
            SIGNED_MATRIX_FOUR_FULL_DETERMINANT_EXISTS,
            f"forall {' '.join(four_variables)}. "
            f"exists p n. (p = {determinant_positive} /\\ n = {determinant_negative})",
            (SIGNED_MATRIX_FOUR_COFACTOR_EXPANSION_EXISTS,),
            (
                *tuple(f"intro {name}" for name in four_variables),
                *tuple(
                    f"specialize {SIGNED_MATRIX_FOUR_COFACTOR_EXPANSION_EXISTS} {term}"
                    for term in (
                        *(component for pair in four_matrix[0] for component in pair),
                        *(component for pair in four_minors for component in pair),
                    )
                ),
                f"exact {SIGNED_MATRIX_FOUR_COFACTOR_EXPANSION_EXISTS}",
            ),
            "Every genuinely signed four-by-four integer matrix has its exact constructive first-row cofactor determinant with all 32 natural entry components.",
        ),
        spec(
            SIGNED_MATRIX_FOUR_FULL_DETERMINANT_FUNCTIONAL,
            f"forall {' '.join(four_variables)} p n q m. "
            f"(p = {determinant_positive} /\\ n = {determinant_negative}) -> "
            f"(q = {determinant_positive} /\\ m = {determinant_negative}) -> "
            "(p = q /\\ n = m)",
            (SIGNED_MATRIX_FOUR_COFACTOR_EXPANSION_FUNCTIONAL,),
            (
                *tuple(f"intro {name}" for name in four_variables),
                "intro p", "intro n", "intro q", "intro m",
                "intro hfirst", "intro hsecond",
                *tuple(
                    f"specialize {SIGNED_MATRIX_FOUR_COFACTOR_EXPANSION_FUNCTIONAL} {term}"
                    for term in (
                        *(component for pair in four_matrix[0] for component in pair),
                        *(component for pair in four_minors for component in pair),
                        "p", "n", "q", "m",
                    )
                ),
                f"apply {SIGNED_MATRIX_FOUR_COFACTOR_EXPANSION_FUNCTIONAL}",
                "exact hfirst", "exact hsecond",
            ),
            "Both exact subtraction-free components of every signed four-by-four cofactor determinant are independent of the witnesses.",
        ),
    )


@dataclass(frozen=True, slots=True)
class MatrixMinorCertificate:
    """A bounded executable row/column deletion, not proof authority."""

    matrix: IntegerMatrix
    removed_row: int
    removed_column: int
    source_coordinates: tuple[tuple[tuple[int, int], ...], ...]
    minor: IntegerMatrix


@dataclass(frozen=True, slots=True)
class SignedCofactorTerm:
    """One witnessed signed Laplace summand and its actual source minor."""

    column: int
    entry: int
    minor: MatrixMinorCertificate
    determinant: DeterminantCertificate
    positive: int
    negative: int

    @property
    def value(self) -> int:
        return self.positive - self.negative


@dataclass(frozen=True, slots=True)
class SignedCofactorDeterminantCertificate:
    """A bounded complete first-row cofactor certificate."""

    matrix: IntegerMatrix
    terms: tuple[SignedCofactorTerm, ...]
    positive: int
    negative: int
    determinant: int


def matrix_skip_index(index: int, removed: int) -> int:
    """Execute the unique order-preserving skipped-coordinate map."""

    if type(index) is not int or type(removed) is not int:
        raise MatrixMinorError("minor coordinates must be exact Python integers")
    if not 0 <= index <= MAX_MATRIX_DIMENSION or not 0 <= removed <= MAX_MATRIX_DIMENSION:
        raise MatrixMinorError("minor coordinates exceed their bounded matrix budget")
    return index if index < removed else index + 1


def certify_matrix_minor(
    matrix: IntegerMatrix, removed_row: int, removed_column: int
) -> MatrixMinorCertificate:
    """Certify each exact surviving source coordinate of a bounded minor."""

    if type(matrix) is not IntegerMatrix:
        raise MatrixMinorError("a cofactor minor requires an exact integer matrix")
    if type(removed_row) is not int or type(removed_column) is not int:
        raise MatrixMinorError("deleted coordinates must be exact Python integers")
    if matrix.height == 0 or matrix.width == 0:
        raise MatrixMinorError("an empty matrix has no row/column deletion minor")
    if not 0 <= removed_row < matrix.height or not 0 <= removed_column < matrix.width:
        raise MatrixMinorError("the deleted row and column must be present")
    try:
        if integer_matrix(matrix.rows) != matrix:
            raise MatrixMinorError("the source matrix is not canonical")
        coordinates = tuple(
            tuple(
                (
                    matrix_skip_index(row, removed_row),
                    matrix_skip_index(column, removed_column),
                )
                for column in range(matrix.width - 1)
            )
            for row in range(matrix.height - 1)
        )
        minor = integer_matrix(
            tuple(matrix.rows[source_row][source_column] for source_row, source_column in row)
            for row in coordinates
        )
    except (MatrixCertificateError, IndexError, OverflowError, TypeError, ValueError) as error:
        raise MatrixMinorError("the requested matrix minor is malformed") from error
    return MatrixMinorCertificate(matrix, removed_row, removed_column, coordinates, minor)


def verify_matrix_minor(receipt: MatrixMinorCertificate) -> bool:
    """Reject forged coordinates, values, dimensions, and non-exact types."""

    if type(receipt) is not MatrixMinorCertificate:
        return False
    try:
        return receipt == certify_matrix_minor(
            receipt.matrix, receipt.removed_row, receipt.removed_column
        )
    except (MatrixMinorError, IndexError, OverflowError, TypeError, ValueError):
        return False


def _signed_components(value: int) -> tuple[int, int]:
    return (value, 0) if value >= 0 else (0, -value)


def certify_signed_cofactor_determinant(
    matrix: IntegerMatrix,
) -> SignedCofactorDeterminantCertificate:
    """Certify bounded Laplace expansion against independent permutation evaluation."""

    if type(matrix) is not IntegerMatrix or matrix.height != matrix.width:
        raise MatrixMinorError("a cofactor determinant requires an exact square matrix")
    if matrix.height > MAX_COFACTOR_DIMENSION:
        raise MatrixMinorError("the cofactor determinant exceeds its bounded work budget")
    try:
        if integer_matrix(matrix.rows) != matrix:
            raise MatrixMinorError("the signed source matrix is not canonical")
        if any(abs(value) > MAX_COFACTOR_ENTRY for row in matrix.rows for value in row):
            raise MatrixMinorError("a matrix entry exceeds the bounded cofactor budget")
        independent = certify_integer_determinant(matrix)
    except (MatrixCertificateError, IndexError, OverflowError, TypeError, ValueError) as error:
        raise MatrixMinorError("the independent determinant is malformed") from error
    if matrix.height == 0:
        return SignedCofactorDeterminantCertificate(matrix, (), 1, 0, 1)

    terms: list[SignedCofactorTerm] = []
    positive = 0
    negative = 0
    for column, entry in enumerate(matrix.rows[0]):
        minor = certify_matrix_minor(matrix, 0, column)
        determinant = certify_integer_determinant(minor.minor)
        entry_positive, entry_negative = _signed_components(entry)
        minor_positive, minor_negative = _signed_components(determinant.value)
        term_positive = entry_positive * minor_positive + entry_negative * minor_negative
        term_negative = entry_positive * minor_negative + entry_negative * minor_positive
        if column % 2:
            term_positive, term_negative = term_negative, term_positive
        terms.append(
            SignedCofactorTerm(
                column, entry, minor, determinant, term_positive, term_negative
            )
        )
        positive += term_positive
        negative += term_negative

    if positive - negative != independent.value:
        raise MatrixMinorError("cofactor and independent permutation determinants disagree")
    return SignedCofactorDeterminantCertificate(
        matrix, tuple(terms), positive, negative, independent.value
    )


def verify_signed_cofactor_determinant(
    receipt: SignedCofactorDeterminantCertificate,
) -> bool:
    """Recompute a bounded cofactor tree and reject every changed field."""

    if type(receipt) is not SignedCofactorDeterminantCertificate:
        return False
    try:
        return receipt == certify_signed_cofactor_determinant(receipt.matrix)
    except (MatrixMinorError, IndexError, OverflowError, TypeError, ValueError):
        return False


__all__ = (
    "BETA_MATRIX_MINOR_CELL_EXISTS",
    "BETA_MATRIX_MINOR_CELL_FUNCTIONAL",
    "BETA_MATRIX_MINOR_EXISTS",
    "BETA_MATRIX_MINOR_POINT_EXISTS",
    "BETA_MATRIX_MINOR_PREFIX_EMPTY_EXISTS",
    "BETA_MATRIX_MINOR_PREFIX_EXISTS",
    "BETA_MATRIX_MINOR_PREFIX_EXISTS_NONZERO",
    "BETA_MATRIX_MINOR_PREFIX_EXTEND",
    "BETA_SIGNED_MATRIX_MINOR_EXISTS",
    "MATRIX_SKIP_INDEX_AVOIDS_REMOVED",
    "MATRIX_SKIP_INDEX_BOUNDED",
    "MATRIX_SKIP_INDEX_EXISTS",
    "MATRIX_SKIP_INDEX_FUNCTIONAL",
    "MAX_COFACTOR_DIMENSION",
    "MAX_COFACTOR_ENTRY",
    "MatrixMinorCertificate",
    "MatrixMinorError",
    "SIGNED_MATRIX_FOUR_FULL_DETERMINANT_EXISTS",
    "SIGNED_MATRIX_FOUR_FULL_DETERMINANT_FUNCTIONAL",
    "SIGNED_MATRIX_FOUR_COFACTOR_EXPANSION_EXISTS",
    "SIGNED_MATRIX_FOUR_COFACTOR_EXPANSION_FUNCTIONAL",
    "SignedCofactorDeterminantCertificate",
    "SignedCofactorTerm",
    "certify_matrix_minor",
    "certify_signed_cofactor_determinant",
    "make_matrix_determinant_minors_candidate_theorems",
    "matrix_minor_cell_relation",
    "matrix_minor_prefix_relation",
    "matrix_skip_index_relation",
    "matrix_skip_index",
    "signed_matrix_minor_relation",
    "verify_matrix_minor",
    "verify_signed_cofactor_determinant",
)
