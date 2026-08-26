"""Conservative beta-coded matrix multiplication and signed matrix foundations.

This is genuine first-order Heyting-arithmetic authoring evidence.  Matrix
rows and columns are finite, explicitly beta-coded affine slices.  Their
natural dot product produces each multiplication cell, and constructive
finite induction encodes *every* row-major output cell in one beta code.

Signed entries remain natural positive/negative pairs.  Their arbitrary
finite dot products and their explicit two-/three-dimensional determinants
are likewise actual arithmetic relations.  Python certificates are bounded
research aids and never supply theorem or release authority.

Arbitrary-dimensional determinants, rank and lattices are deliberately not
claimed here.  Signed matrix output is assembled by four separately checked
natural products and two constructive pointwise-addition recodings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from .finite_fold_surface import _binders, _identifier, _variables
from .finite_sum_theorems import _at
from .matrix_dot_product_candidate import (
    BETA_DOT_PRODUCT_EXISTS,
    BETA_DOT_PRODUCT_FUNCTIONAL,
    MAX_MATRIX_DIMENSION,
    IntegerMatrix,
    MatrixCertificateError,
    dot_product_relation,
    integer_matrix,
)


BETA_AFFINE_MATRIX_SLICE_EXTEND = "beta_affine_matrix_slice_extend"
BETA_AFFINE_MATRIX_SLICE_EXISTS = "beta_affine_matrix_slice_exists"
BETA_MATRIX_ROW_SLICE_EXISTS = "beta_matrix_row_slice_exists"
BETA_MATRIX_COLUMN_SLICE_EXISTS = "beta_matrix_column_slice_exists"
BETA_MATRIX_PRODUCT_CELL_EXISTS = "beta_matrix_product_cell_exists"
BETA_MATRIX_PRODUCT_POINT_EXISTS = "beta_matrix_product_point_exists"
BETA_MATRIX_PRODUCT_PREFIX_EXTEND = "beta_matrix_product_prefix_extend"
BETA_MATRIX_PRODUCT_PREFIX_EXISTS_NONZERO = "beta_matrix_product_prefix_exists_nonzero"
BETA_MATRIX_PRODUCT_EXISTS_NONZERO_WIDTH = "beta_matrix_product_exists_nonzero_width"
BETA_MATRIX_PRODUCT_EMPTY_EXISTS = "beta_matrix_product_empty_exists"
BETA_MATRIX_PRODUCT_EXISTS = "beta_matrix_product_exists"
BETA_POINTWISE_ADD_PREFIX_EXTEND = "beta_pointwise_add_prefix_extend"
BETA_POINTWISE_ADD_PREFIX_EXISTS = "beta_pointwise_add_prefix_exists"
BETA_SIGNED_MATRIX_PRODUCT_EXISTS = "beta_signed_matrix_product_exists"
SIGNED_PAIR_PRODUCT_EXISTS = "signed_pair_product_exists"
SIGNED_PAIR_PRODUCT_FUNCTIONAL = "signed_pair_product_functional"
BETA_SIGNED_DOT_PRODUCT_EXISTS = "beta_signed_dot_product_exists"
BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL = "beta_signed_dot_product_functional"
BETA_SIGNED_DOT_PRODUCT_EXISTS_UNIQUE = "beta_signed_dot_product_exists_unique"
SIGNED_MATRIX_TWO_FULL_DETERMINANT_EXISTS = "signed_matrix_two_full_determinant_exists"
SIGNED_MATRIX_TWO_FULL_DETERMINANT_FUNCTIONAL = "signed_matrix_two_full_determinant_functional"
SIGNED_MATRIX_THREE_FULL_DETERMINANT_EXISTS = "signed_matrix_three_full_determinant_exists"
SIGNED_MATRIX_THREE_FULL_DETERMINANT_FUNCTIONAL = "signed_matrix_three_full_determinant_functional"

MAX_COMPONENT = 1 << 30


class CodedMatrixError(ValueError):
    """A conservative coded matrix surface or bounded certificate failed."""


def _safe_tag(tag: str) -> str:
    try:
        return _identifier(tag, "coded-matrix binder tag")
    except ValueError as error:
        raise CodedMatrixError(str(error)) from error


def _lt(left: str, right: str, *, tag: str) -> str:
    return f"exists mcp_gap_{tag}. mcp_gap_{tag} + S ({left}) = ({right})"


def _slice_terms(
    code: str,
    scale: str,
    start: str,
    stride: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    safe_tag = _safe_tag(tag)
    index, source, target = _binders(
        f"mcp_{safe_tag}",
        (code, scale, start, stride, target_code, target_scale, length),
        ("index", "source", "target"),
    )
    bounded = _lt(index, length, tag=f"{safe_tag}_bound")
    source_value = _at(
        code,
        scale,
        f"({start}) + ({stride}) * {index}",
        source,
        tag=f"mcp_{safe_tag}_source",
    )
    target_value = _at(
        target_code,
        target_scale,
        index,
        target,
        tag=f"mcp_{safe_tag}_target",
    )
    return (
        f"forall {index} {source} {target}. ({bounded}) -> "
        f"({source_value}) -> ({target_value}) -> {target} = {source}"
    )


def affine_matrix_slice_relation(
    code: str,
    scale: str,
    start: str,
    stride: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand an arbitrary finite affine beta-reindexing hygienically."""

    try:
        variables = _variables(
            (code, "source code"),
            (scale, "source scale"),
            (start, "affine start"),
            (stride, "affine stride"),
            (target_code, "target code"),
            (target_scale, "target scale"),
            (length, "slice length"),
        )
        safe_tag = _safe_tag(tag)
        _binders(f"mcp_{safe_tag}", variables, ("index", "source", "target"))
        return _slice_terms(*variables, tag=safe_tag)
    except ValueError as error:
        raise CodedMatrixError(str(error)) from error


def _row_slice(
    code: str,
    scale: str,
    width: str,
    row: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    return _slice_terms(
        code,
        scale,
        f"({row}) * ({width})",
        "1",
        target_code,
        target_scale,
        length,
        tag=tag,
    )


def _column_slice(
    code: str,
    scale: str,
    width: str,
    column: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    return _slice_terms(
        code, scale, column, width, target_code, target_scale, length, tag=tag
    )


def _product_cell_terms(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    inner_width: str,
    output_width: str,
    row: str,
    column: str,
    result: str,
    *,
    tag: str,
) -> str:
    safe_tag = _safe_tag(tag)
    left_row, left_row_scale, right_column, right_column_scale = _binders(
        f"mcp_cell_{safe_tag}",
        (
            left_code,
            left_scale,
            right_code,
            right_scale,
            inner_width,
            output_width,
            row,
            column,
            result,
        ),
        ("left", "left_scale", "right", "right_scale"),
    )
    first = _row_slice(
        left_code,
        left_scale,
        inner_width,
        row,
        left_row,
        left_row_scale,
        inner_width,
        tag=f"{safe_tag}_row",
    )
    second = _column_slice(
        right_code,
        right_scale,
        output_width,
        column,
        right_column,
        right_column_scale,
        inner_width,
        tag=f"{safe_tag}_column",
    )
    dot = dot_product_relation(
        left_row,
        left_row_scale,
        right_column,
        right_column_scale,
        inner_width,
        result,
        tag=f"mcp_{safe_tag}_dot",
    )
    return (
        f"exists {left_row} {left_row_scale} {right_column} {right_column_scale}. "
        f"(({first}) /\\ (({second}) /\\ ({dot})))"
    )


def matrix_product_cell_relation(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    inner_width: str,
    output_width: str,
    row: str,
    column: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand one exact row-column finite dot-product matrix entry."""

    try:
        variables = _variables(
            (left_code, "left matrix code"),
            (left_scale, "left matrix scale"),
            (right_code, "right matrix code"),
            (right_scale, "right matrix scale"),
            (inner_width, "inner matrix dimension"),
            (output_width, "output matrix width"),
            (row, "output row"),
            (column, "output column"),
            (result, "matrix product cell"),
        )
        return _product_cell_terms(*variables, tag=_safe_tag(tag))
    except ValueError as error:
        raise CodedMatrixError(str(error)) from error


def _point_terms(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    inner_width: str,
    output_width: str,
    index: str,
    *,
    tag: str,
) -> str:
    row, column, value = _binders(
        f"mcp_point_{tag}",
        (
            left_code,
            left_scale,
            right_code,
            right_scale,
            inner_width,
            output_width,
            index,
        ),
        ("row", "column", "value"),
    )
    cell = _product_cell_terms(
        left_code,
        left_scale,
        right_code,
        right_scale,
        inner_width,
        output_width,
        row,
        column,
        value,
        tag=f"{tag}_cell",
    )
    bounded = _lt(column, output_width, tag=f"{tag}_column")
    return (
        f"exists {row} {column} {value}. "
        f"(({index}) = ({output_width}) * {row} + {column} /\\ "
        f"(({bounded}) /\\ ({cell})))"
    )


def _product_prefix_terms(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    inner_width: str,
    output_width: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    index, row, column, value = _binders(
        f"mcp_prefix_{tag}",
        (
            left_code,
            left_scale,
            right_code,
            right_scale,
            inner_width,
            output_width,
            target_code,
            target_scale,
            length,
        ),
        ("index", "row", "column", "value"),
    )
    bounded_index = _lt(index, length, tag=f"{tag}_index")
    bounded_column = _lt(column, output_width, tag=f"{tag}_column")
    cell = _product_cell_terms(
        left_code,
        left_scale,
        right_code,
        right_scale,
        inner_width,
        output_width,
        row,
        column,
        value,
        tag=f"{tag}_cell",
    )
    entry = _at(target_code, target_scale, index, value, tag=f"mcp_{tag}_entry")
    return (
        f"forall {index}. ({bounded_index}) -> exists {row} {column} {value}. "
        f"(({index}) = ({output_width}) * {row} + {column} /\\ "
        f"(({bounded_column}) /\\ (({cell}) /\\ ({entry}))))"
    )


def matrix_product_prefix_relation(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    inner_width: str,
    output_width: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand every exact row-major output entry of a finite matrix product."""

    try:
        variables = _variables(
            (left_code, "left matrix code"),
            (left_scale, "left matrix scale"),
            (right_code, "right matrix code"),
            (right_scale, "right matrix scale"),
            (inner_width, "inner matrix dimension"),
            (output_width, "output matrix width"),
            (target_code, "output matrix code"),
            (target_scale, "output matrix scale"),
            (length, "output prefix length"),
        )
        return _product_prefix_terms(*variables, tag=_safe_tag(tag))
    except ValueError as error:
        raise CodedMatrixError(str(error)) from error


def _pointwise_add_terms(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    safe_tag = _safe_tag(tag)
    index, left, right, target = _binders(
        f"mcp_add_{safe_tag}",
        (left_code, left_scale, right_code, right_scale, target_code, target_scale, length),
        ("index", "left", "right", "target"),
    )
    bounded = _lt(index, length, tag=f"{safe_tag}_bound")
    first = _at(left_code, left_scale, index, left, tag=f"mcp_{safe_tag}_left")
    second = _at(right_code, right_scale, index, right, tag=f"mcp_{safe_tag}_right")
    total = _at(target_code, target_scale, index, target, tag=f"mcp_{safe_tag}_target")
    return (
        f"forall {index} {left} {right} {target}. ({bounded}) -> "
        f"({first}) -> ({second}) -> ({total}) -> {target} = {left} + {right}"
    )


def pointwise_add_prefix_relation(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand exact componentwise addition of two finite beta-coded prefixes."""

    try:
        variables = _variables(
            (left_code, "left summand code"),
            (left_scale, "left summand scale"),
            (right_code, "right summand code"),
            (right_scale, "right summand scale"),
            (target_code, "sum code"),
            (target_scale, "sum scale"),
            (length, "sum prefix length"),
        )
        safe_tag = _safe_tag(tag)
        _binders(f"mcp_add_{safe_tag}", variables, ("index", "left", "right", "target"))
        return _pointwise_add_terms(*variables, tag=safe_tag)
    except ValueError as error:
        raise CodedMatrixError(str(error)) from error


def _signed_matrix_product_terms(
    left_positive_code: str,
    left_positive_scale: str,
    left_negative_code: str,
    left_negative_scale: str,
    right_positive_code: str,
    right_positive_scale: str,
    right_negative_code: str,
    right_negative_scale: str,
    inner_width: str,
    output_width: str,
    rows: str,
    positive_code: str,
    positive_scale: str,
    negative_code: str,
    negative_scale: str,
    *,
    tag: str,
) -> str:
    safe_tag = _safe_tag(tag)
    pp, pps, nn, nns, pn, pns, np, nps = _binders(
        f"mcp_smatrix_{safe_tag}",
        (
            left_positive_code,
            left_positive_scale,
            left_negative_code,
            left_negative_scale,
            right_positive_code,
            right_positive_scale,
            right_negative_code,
            right_negative_scale,
            inner_width,
            output_width,
            rows,
            positive_code,
            positive_scale,
            negative_code,
            negative_scale,
        ),
        ("pp", "pps", "nn", "nns", "pn", "pns", "np", "nps"),
    )
    length = f"({rows}) * ({output_width})"
    first = _product_prefix_terms(
        left_positive_code,
        left_positive_scale,
        right_positive_code,
        right_positive_scale,
        inner_width,
        output_width,
        pp,
        pps,
        length,
        tag=f"{safe_tag}_pp",
    )
    second = _product_prefix_terms(
        left_negative_code,
        left_negative_scale,
        right_negative_code,
        right_negative_scale,
        inner_width,
        output_width,
        nn,
        nns,
        length,
        tag=f"{safe_tag}_nn",
    )
    third = _product_prefix_terms(
        left_positive_code,
        left_positive_scale,
        right_negative_code,
        right_negative_scale,
        inner_width,
        output_width,
        pn,
        pns,
        length,
        tag=f"{safe_tag}_pn",
    )
    fourth = _product_prefix_terms(
        left_negative_code,
        left_negative_scale,
        right_positive_code,
        right_positive_scale,
        inner_width,
        output_width,
        np,
        nps,
        length,
        tag=f"{safe_tag}_np",
    )
    positive = _pointwise_add_terms(
        pp, pps, nn, nns, positive_code, positive_scale, length, tag=f"{safe_tag}_positive"
    )
    negative = _pointwise_add_terms(
        pn, pns, np, nps, negative_code, negative_scale, length, tag=f"{safe_tag}_negative"
    )
    return (
        f"exists {pp} {pps} {nn} {nns} {pn} {pns} {np} {nps}. "
        f"(({first}) /\\ (({second}) /\\ (({third}) /\\ "
        f"(({fourth}) /\\ (({positive}) /\\ ({negative}))))))"
    )


def signed_matrix_product_relation(
    left_positive_code: str,
    left_positive_scale: str,
    left_negative_code: str,
    left_negative_scale: str,
    right_positive_code: str,
    right_positive_scale: str,
    right_negative_code: str,
    right_negative_scale: str,
    inner_width: str,
    output_width: str,
    rows: str,
    positive_code: str,
    positive_scale: str,
    negative_code: str,
    negative_scale: str,
    *,
    tag: str,
) -> str:
    """Expand an exact arbitrary-dimensional signed beta-coded matrix product."""

    try:
        variables = _variables(
            (left_positive_code, "left positive matrix code"),
            (left_positive_scale, "left positive matrix scale"),
            (left_negative_code, "left negative matrix code"),
            (left_negative_scale, "left negative matrix scale"),
            (right_positive_code, "right positive matrix code"),
            (right_positive_scale, "right positive matrix scale"),
            (right_negative_code, "right negative matrix code"),
            (right_negative_scale, "right negative matrix scale"),
            (inner_width, "inner matrix dimension"),
            (output_width, "output matrix width"),
            (rows, "output matrix height"),
            (positive_code, "positive output matrix code"),
            (positive_scale, "positive output matrix scale"),
            (negative_code, "negative output matrix code"),
            (negative_scale, "negative output matrix scale"),
        )
        return _signed_matrix_product_terms(*variables, tag=_safe_tag(tag))
    except ValueError as error:
        raise CodedMatrixError(str(error)) from error


def _signed_dot_terms(
    left_positive_code: str,
    left_positive_scale: str,
    left_negative_code: str,
    left_negative_scale: str,
    right_positive_code: str,
    right_positive_scale: str,
    right_negative_code: str,
    right_negative_scale: str,
    length: str,
    positive: str,
    negative: str,
    *,
    tag: str,
) -> str:
    safe_tag = _safe_tag(tag)
    pp, nn, pn, np = _binders(
        f"mcp_signed_{safe_tag}",
        (
            left_positive_code,
            left_positive_scale,
            left_negative_code,
            left_negative_scale,
            right_positive_code,
            right_positive_scale,
            right_negative_code,
            right_negative_scale,
            length,
            positive,
            negative,
        ),
        ("pp", "nn", "pn", "np"),
    )
    first = dot_product_relation(
        left_positive_code,
        left_positive_scale,
        right_positive_code,
        right_positive_scale,
        length,
        pp,
        tag=f"mcp_{safe_tag}_pp",
    )
    second = dot_product_relation(
        left_negative_code,
        left_negative_scale,
        right_negative_code,
        right_negative_scale,
        length,
        nn,
        tag=f"mcp_{safe_tag}_nn",
    )
    third = dot_product_relation(
        left_positive_code,
        left_positive_scale,
        right_negative_code,
        right_negative_scale,
        length,
        pn,
        tag=f"mcp_{safe_tag}_pn",
    )
    fourth = dot_product_relation(
        left_negative_code,
        left_negative_scale,
        right_positive_code,
        right_positive_scale,
        length,
        np,
        tag=f"mcp_{safe_tag}_np",
    )
    return (
        f"exists {pp} {nn} {pn} {np}. (({first}) /\\ (({second}) /\\ "
        f"(({third}) /\\ (({fourth}) /\\ "
        f"({positive} = {pp} + {nn} /\\ {negative} = {pn} + {np})))))"
    )


def signed_dot_product_relation(
    left_positive_code: str,
    left_positive_scale: str,
    left_negative_code: str,
    left_negative_scale: str,
    right_positive_code: str,
    right_positive_scale: str,
    right_negative_code: str,
    right_negative_scale: str,
    length: str,
    positive: str,
    negative: str,
    *,
    tag: str,
) -> str:
    """Expand the exact positive/negative pair of a signed finite dot product."""

    try:
        variables = _variables(
            (left_positive_code, "left positive code"),
            (left_positive_scale, "left positive scale"),
            (left_negative_code, "left negative code"),
            (left_negative_scale, "left negative scale"),
            (right_positive_code, "right positive code"),
            (right_positive_scale, "right positive scale"),
            (right_negative_code, "right negative code"),
            (right_negative_scale, "right negative scale"),
            (length, "signed vector length"),
            (positive, "positive output component"),
            (negative, "negative output component"),
        )
        return _signed_dot_terms(*variables, tag=_safe_tag(tag))
    except ValueError as error:
        raise CodedMatrixError(str(error)) from error


def _pair_product(
    left: tuple[str, str], right: tuple[str, str]
) -> tuple[str, str]:
    ap, an = left
    bp, bn = right
    return (f"(({ap}) * ({bp}) + ({an}) * ({bn}))", f"(({ap}) * ({bn}) + ({an}) * ({bp}))")


def _pair_sum(left: tuple[str, str], right: tuple[str, str]) -> tuple[str, str]:
    return (f"(({left[0]}) + ({right[0]}))", f"(({left[1]}) + ({right[1]}))")


def _pair_difference(left: tuple[str, str], right: tuple[str, str]) -> tuple[str, str]:
    return (f"(({left[0]}) + ({right[1]}))", f"(({left[1]}) + ({right[0]}))")


def _determinant_two_terms() -> tuple[str, str]:
    ad = _pair_product(("ap", "an"), ("dp", "dn"))
    bc = _pair_product(("bp", "bn"), ("cp", "cn"))
    return _pair_difference(ad, bc)


def _determinant_three_terms() -> tuple[str, str]:
    a = ("ap", "an")
    b = ("bp", "bn")
    c = ("cp", "cn")
    d = ("dp", "dn")
    e = ("ep", "en")
    f = ("fp", "fn")
    g = ("gp", "gn")
    h = ("hp", "hn")
    i = ("ip", "inn")
    first = _pair_product(a, _pair_difference(_pair_product(e, i), _pair_product(f, h)))
    second = _pair_product(b, _pair_difference(_pair_product(d, i), _pair_product(f, g)))
    third = _pair_product(c, _pair_difference(_pair_product(d, h), _pair_product(e, g)))
    return _pair_sum(_pair_difference(first, second), third)


def make_matrix_coded_product_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered constructive coded matrix campaign."""

    before = _slice_terms("b", "c", "s", "d", "u", "v", "l", tag="extend_before")
    source_last = _at("b", "c", "s + d * l", "a", tag="mcp_extend_source_last")
    after = _slice_terms("b", "c", "s", "d", "z", "e", "S l", tag="extend_after")
    exists_slice = _slice_terms("b", "c", "s", "d", "u", "v", "l", tag="exists_result")
    previous_slice = _slice_terms("b", "c", "s", "d", "u", "v", "l", tag="exists_previous")
    row_slice = _row_slice("b", "c", "w", "i", "u", "v", "l", tag="row_result")
    column_slice = _column_slice("b", "c", "w", "j", "u", "v", "l", tag="column_result")
    cell = _product_cell_terms("lb", "lc", "rb", "rc", "w", "v", "i", "j", "n", tag="cell_result")
    point = _point_terms("lb", "lc", "rb", "rc", "w", "v", "k", tag="point_result")
    point_last = _point_terms("lb", "lc", "rb", "rc", "w", "v", "l", tag="prefix_last")
    prefix_before = _product_prefix_terms("lb", "lc", "rb", "rc", "w", "v", "tb", "tc", "l", tag="prefix_before")
    prefix_after = _product_prefix_terms("lb", "lc", "rb", "rc", "w", "v", "z", "d", "S l", tag="prefix_after")
    prefix_result = _product_prefix_terms("lb", "lc", "rb", "rc", "w", "v", "tb", "tc", "l", tag="prefix_result")
    prefix_previous = _product_prefix_terms("lb", "lc", "rb", "rc", "w", "v", "tb", "tc", "l", tag="prefix_previous")
    full = _product_prefix_terms("lb", "lc", "rb", "rc", "w", "v", "tb", "tc", "r * v", tag="full_result")
    empty = _product_prefix_terms("lb", "lc", "rb", "rc", "w", "v", "tb", "tc", "0", tag="empty_result")
    add_before = _pointwise_add_terms("mb", "mc", "sb", "sc", "tb", "tc", "l", tag="add_before")
    add_left = _at("mb", "mc", "l", "a", tag="mcp_add_last_left")
    add_right = _at("sb", "sc", "l", "b", tag="mcp_add_last_right")
    add_after = _pointwise_add_terms("mb", "mc", "sb", "sc", "z", "d", "S l", tag="add_after")
    add_exists = _pointwise_add_terms("mb", "mc", "sb", "sc", "tb", "tc", "l", tag="add_exists")
    add_previous = _pointwise_add_terms("mb", "mc", "sb", "sc", "tb", "tc", "l", tag="add_previous")
    signed_matrix = _signed_matrix_product_terms(
        "ab", "ac", "db", "dc", "eb", "ec", "fb", "fc", "w", "v", "r", "pb", "pc", "nb", "nc", tag="signed_matrix_result"
    )

    signed_args = ("ab", "ac", "db", "dc", "eb", "ec", "fb", "fc", "l")
    signed = _signed_dot_terms(*signed_args, "p", "n", tag="signed_result")
    signed_other = _signed_dot_terms(*signed_args, "q", "m", tag="signed_other")
    det2p, det2n = _determinant_two_terms()
    det3p, det3n = _determinant_three_terms()

    def dot_exists(code1: str, scale1: str, code2: str, scale2: str, label: str, tag: str) -> tuple[str, ...]:
        relation = dot_product_relation(code1, scale1, code2, scale2, "l", "z", tag=tag)
        return (
            f"have {label} : exists z. ({relation})",
            f"specialize {BETA_DOT_PRODUCT_EXISTS} {code1}",
            f"specialize {BETA_DOT_PRODUCT_EXISTS} {scale1}",
            f"specialize {BETA_DOT_PRODUCT_EXISTS} {code2}",
            f"specialize {BETA_DOT_PRODUCT_EXISTS} {scale2}",
            f"specialize {BETA_DOT_PRODUCT_EXISTS} l",
            f"exact {BETA_DOT_PRODUCT_EXISTS}",
            f"cases {label}",
        )

    def dot_unique(code1: str, scale1: str, code2: str, scale2: str, first: str, second: str, left_hyp: str, right_hyp: str, label: str) -> tuple[str, ...]:
        return (
            f"have {label} : {first} = {second}",
            f"specialize {BETA_DOT_PRODUCT_FUNCTIONAL} {code1}",
            f"specialize {BETA_DOT_PRODUCT_FUNCTIONAL} {scale1}",
            f"specialize {BETA_DOT_PRODUCT_FUNCTIONAL} {code2}",
            f"specialize {BETA_DOT_PRODUCT_FUNCTIONAL} {scale2}",
            f"specialize {BETA_DOT_PRODUCT_FUNCTIONAL} l",
            f"specialize {BETA_DOT_PRODUCT_FUNCTIONAL} {first}",
            f"specialize {BETA_DOT_PRODUCT_FUNCTIONAL} {second}",
            f"apply {BETA_DOT_PRODUCT_FUNCTIONAL}",
            f"exact {left_hyp}",
            f"exact {right_hyp}",
        )

    def matrix_exists(code1: str, scale1: str, code2: str, scale2: str, label: str, tag: str) -> tuple[str, ...]:
        relation = _product_prefix_terms(code1, scale1, code2, scale2, "w", "v", "tb", "tc", "r * v", tag=tag)
        return (
            f"have {label} : exists tb tc. ({relation})",
            f"specialize {BETA_MATRIX_PRODUCT_EXISTS} {code1}",
            f"specialize {BETA_MATRIX_PRODUCT_EXISTS} {scale1}",
            f"specialize {BETA_MATRIX_PRODUCT_EXISTS} {code2}",
            f"specialize {BETA_MATRIX_PRODUCT_EXISTS} {scale2}",
            f"specialize {BETA_MATRIX_PRODUCT_EXISTS} w",
            f"specialize {BETA_MATRIX_PRODUCT_EXISTS} v",
            f"specialize {BETA_MATRIX_PRODUCT_EXISTS} r",
            f"exact {BETA_MATRIX_PRODUCT_EXISTS}",
            f"cases {label}",
            f"cases {label}_witness",
        )

    return (
        spec(
            BETA_AFFINE_MATRIX_SLICE_EXTEND,
            f"forall b c s d u v l a. ({before}) -> ({source_last}) -> exists z e. ({after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt", "beta_at_exists", "beta_at_unique"),
            (
                "intro b", "intro c", "intro s", "intro d", "intro u", "intro v", "intro l", "intro a",
                "intro hprevious", "intro hlast",
                "specialize beta_prefix_extend l", "specialize beta_prefix_extend u", "specialize beta_prefix_extend v", "specialize beta_prefix_extend a",
                "cases beta_prefix_extend", "cases beta_prefix_extend_witness", "cases beta_prefix_extend_witness_witness",
                "exists x", "exists x1", "intro i", "intro source", "intro target", "intro hi", "intro hsource", "intro htarget",
                "have hsplit : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l", "specialize finite_lt_succ_eq_or_lt i", "apply finite_lt_succ_eq_or_lt", "exact hi",
                "cases hsplit",
                "rewrite hsplit_left at hsource", "rewrite hsplit_left at hsource", "rewrite hsplit_left at htarget", "rewrite hsplit_left at htarget",
                "have hsource_value : a = source",
                "specialize beta_at_unique b", "specialize beta_at_unique c", "specialize beta_at_unique (s + d * l)", "specialize beta_at_unique a", "specialize beta_at_unique source", "apply beta_at_unique", "exact hlast", "exact hsource",
                "have htarget_value : target = a",
                "specialize beta_at_unique x", "specialize beta_at_unique x1", "specialize beta_at_unique l", "specialize beta_at_unique target", "specialize beta_at_unique a", "apply beta_at_unique", "exact htarget", "exact beta_prefix_extend_witness_witness_left",
                "trans a", "exact htarget_value", "exact hsource_value",
                f"have hold : exists z. ({_at('u', 'v', 'i', 'z', tag='mcp_extend_old')})",
                "specialize beta_at_exists u", "specialize beta_at_exists v", "specialize beta_at_exists i", "exact beta_at_exists", "cases hold",
                f"have hpreserved : {_at('x', 'x1', 'i', 'x2', tag='mcp_extend_preserved')}",
                "specialize beta_prefix_extend_witness_witness_right i", "specialize beta_prefix_extend_witness_witness_right x2", "apply beta_prefix_extend_witness_witness_right", "exact hsplit_right", "exact hold_witness",
                "have htarget_old : target = x2",
                "specialize beta_at_unique x", "specialize beta_at_unique x1", "specialize beta_at_unique i", "specialize beta_at_unique target", "specialize beta_at_unique x2", "apply beta_at_unique", "exact htarget", "exact hpreserved",
                "have hold_source : x2 = source",
                "specialize hprevious i", "specialize hprevious source", "specialize hprevious x2", "apply hprevious", "exact hsplit_right", "exact hsource", "exact hold_witness",
                "trans x2", "exact htarget_old", "exact hold_source",
            ),
            "Extend an affine beta-coded matrix slice while preserving every earlier decoded value.",
        ),
        spec(
            BETA_AFFINE_MATRIX_SLICE_EXISTS,
            f"forall b c s d l. exists u v. ({exists_slice})",
            ("add_eq_zero_right", "succ_ne_zero", "beta_at_exists", BETA_AFFINE_MATRIX_SLICE_EXTEND),
            (
                "intro b", "intro c", "intro s", "intro d", "induction l",
                "exists 0", "exists 0", "intro i", "intro source", "intro target", "intro hi", "intro hsource", "intro htarget", "exfalso", "cases hi",
                "have hzero : S i = 0", "specialize add_eq_zero_right x", "specialize add_eq_zero_right (S i)", "apply add_eq_zero_right", "exact hi_witness", "specialize succ_ne_zero i", "apply succ_ne_zero", "exact hzero",
                f"have hprevious : exists u v. ({previous_slice})", "exact IH", "cases hprevious", "cases hprevious_witness",
                f"have hsource : exists a. ({_at('b', 'c', 's + d * l', 'a', tag='mcp_exists_last')})",
                "specialize beta_at_exists b", "specialize beta_at_exists c", "specialize beta_at_exists (s + d * l)", "exact beta_at_exists", "cases hsource",
                f"specialize {BETA_AFFINE_MATRIX_SLICE_EXTEND} b", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXTEND} c", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXTEND} s", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXTEND} d", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXTEND} x", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXTEND} x1", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXTEND} l", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXTEND} x2",
                f"apply {BETA_AFFINE_MATRIX_SLICE_EXTEND}", "exact hprevious_witness_witness", "exact hsource_witness",
            ),
            "Every finite affine reindexing of a beta-coded natural matrix has its own complete beta code.",
        ),
        spec(
            BETA_MATRIX_ROW_SLICE_EXISTS,
            f"forall b c w i l. exists u v. ({row_slice})",
            (BETA_AFFINE_MATRIX_SLICE_EXISTS,),
            (
                "intro b", "intro c", "intro w", "intro i", "intro l",
                f"specialize {BETA_AFFINE_MATRIX_SLICE_EXISTS} b", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXISTS} c", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXISTS} (i * w)", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXISTS} 1", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXISTS} l", f"exact {BETA_AFFINE_MATRIX_SLICE_EXISTS}",
            ),
            "Every requested finite matrix row has an explicitly encoded row-major beta slice.",
        ),
        spec(
            BETA_MATRIX_COLUMN_SLICE_EXISTS,
            f"forall b c w j l. exists u v. ({column_slice})",
            (BETA_AFFINE_MATRIX_SLICE_EXISTS,),
            (
                "intro b", "intro c", "intro w", "intro j", "intro l",
                f"specialize {BETA_AFFINE_MATRIX_SLICE_EXISTS} b", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXISTS} c", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXISTS} j", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXISTS} w", f"specialize {BETA_AFFINE_MATRIX_SLICE_EXISTS} l", f"exact {BETA_AFFINE_MATRIX_SLICE_EXISTS}",
            ),
            "Every requested finite matrix column has an explicitly encoded stride-width beta slice.",
        ),
        spec(
            BETA_MATRIX_PRODUCT_CELL_EXISTS,
            f"forall lb lc rb rc w v i j. exists n. ({cell})",
            (BETA_MATRIX_ROW_SLICE_EXISTS, BETA_MATRIX_COLUMN_SLICE_EXISTS, BETA_DOT_PRODUCT_EXISTS),
            (
                "intro lb", "intro lc", "intro rb", "intro rc", "intro w", "intro v", "intro i", "intro j",
                f"have hrow : exists u t. ({_row_slice('lb', 'lc', 'w', 'i', 'u', 't', 'w', tag='cell_have_row')})",
                f"specialize {BETA_MATRIX_ROW_SLICE_EXISTS} lb", f"specialize {BETA_MATRIX_ROW_SLICE_EXISTS} lc", f"specialize {BETA_MATRIX_ROW_SLICE_EXISTS} w", f"specialize {BETA_MATRIX_ROW_SLICE_EXISTS} i", f"specialize {BETA_MATRIX_ROW_SLICE_EXISTS} w", f"exact {BETA_MATRIX_ROW_SLICE_EXISTS}", "cases hrow", "cases hrow_witness",
                f"have hcolumn : exists u t. ({_column_slice('rb', 'rc', 'v', 'j', 'u', 't', 'w', tag='cell_have_column')})",
                f"specialize {BETA_MATRIX_COLUMN_SLICE_EXISTS} rb", f"specialize {BETA_MATRIX_COLUMN_SLICE_EXISTS} rc", f"specialize {BETA_MATRIX_COLUMN_SLICE_EXISTS} v", f"specialize {BETA_MATRIX_COLUMN_SLICE_EXISTS} j", f"specialize {BETA_MATRIX_COLUMN_SLICE_EXISTS} w", f"exact {BETA_MATRIX_COLUMN_SLICE_EXISTS}", "cases hcolumn", "cases hcolumn_witness",
                f"have hdot : exists n. ({dot_product_relation('x', 'x1', 'x2', 'x3', 'w', 'n', tag='mcp_cell_have_dot')})",
                f"specialize {BETA_DOT_PRODUCT_EXISTS} x", f"specialize {BETA_DOT_PRODUCT_EXISTS} x1", f"specialize {BETA_DOT_PRODUCT_EXISTS} x2", f"specialize {BETA_DOT_PRODUCT_EXISTS} x3", f"specialize {BETA_DOT_PRODUCT_EXISTS} w", f"exact {BETA_DOT_PRODUCT_EXISTS}", "cases hdot",
                "exists x4", "exists x", "exists x1", "exists x2", "exists x3", "split", "exact hrow_witness_witness", "split", "exact hcolumn_witness_witness", "exact hdot_witness",
            ),
            "Every row and column of two arbitrary finite coded natural matrices has an exactly witnessed product cell.",
        ),
        spec(
            BETA_MATRIX_PRODUCT_POINT_EXISTS,
            f"forall lb lc rb rc w v k. ~(v = 0) -> ({point})",
            ("division_remainder_exists", BETA_MATRIX_PRODUCT_CELL_EXISTS),
            (
                "intro lb", "intro lc", "intro rb", "intro rc", "intro w", "intro v", "intro k", "intro hv",
                "have hcoordinates : exists i j. k = v * i + j /\\ exists gap. gap + S j = v",
                "specialize division_remainder_exists v", "specialize division_remainder_exists k", "apply division_remainder_exists", "exact hv", "cases hcoordinates", "cases hcoordinates_witness", "cases hcoordinates_witness_witness",
                f"have hcell : exists n. ({_product_cell_terms('lb', 'lc', 'rb', 'rc', 'w', 'v', 'x', 'x1', 'n', tag='point_have_cell')})",
                f"specialize {BETA_MATRIX_PRODUCT_CELL_EXISTS} lb", f"specialize {BETA_MATRIX_PRODUCT_CELL_EXISTS} lc", f"specialize {BETA_MATRIX_PRODUCT_CELL_EXISTS} rb", f"specialize {BETA_MATRIX_PRODUCT_CELL_EXISTS} rc", f"specialize {BETA_MATRIX_PRODUCT_CELL_EXISTS} w", f"specialize {BETA_MATRIX_PRODUCT_CELL_EXISTS} v", f"specialize {BETA_MATRIX_PRODUCT_CELL_EXISTS} x", f"specialize {BETA_MATRIX_PRODUCT_CELL_EXISTS} x1", f"exact {BETA_MATRIX_PRODUCT_CELL_EXISTS}", "cases hcell",
                "exists x", "exists x1", "exists x2", "split", "exact hcoordinates_witness_witness_left", "split", "exact hcoordinates_witness_witness_right", "exact hcell_witness",
            ),
            "A nonempty output width constructs the exact row, column and product value of every flat output index.",
        ),
        spec(
            BETA_MATRIX_PRODUCT_PREFIX_EXTEND,
            f"forall lb lc rb rc w v tb tc l. ({prefix_before}) -> ({point_last}) -> exists z d. ({prefix_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                "intro lb", "intro lc", "intro rb", "intro rc", "intro w", "intro v", "intro tb", "intro tc", "intro l", "intro hprevious", "intro hpoint",
                "cases hpoint", "cases hpoint_witness", "cases hpoint_witness_witness", "cases hpoint_witness_witness_witness", "cases hpoint_witness_witness_witness_right",
                "specialize beta_prefix_extend l", "specialize beta_prefix_extend tb", "specialize beta_prefix_extend tc", "specialize beta_prefix_extend x2", "cases beta_prefix_extend", "cases beta_prefix_extend_witness", "cases beta_prefix_extend_witness_witness",
                "exists x3", "exists x4", "intro k", "intro hk",
                "have hsplit : k = l \\/ exists gap. gap + S k = l", "specialize finite_lt_succ_eq_or_lt l", "specialize finite_lt_succ_eq_or_lt k", "apply finite_lt_succ_eq_or_lt", "exact hk", "cases hsplit",
                "exists x", "exists x1", "exists x2", "split", "rewrite hsplit_left", "exact hpoint_witness_witness_witness_left", "split", "exact hpoint_witness_witness_witness_right_left", "split", "exact hpoint_witness_witness_witness_right_right", "rewrite hsplit_left", "rewrite hsplit_left", "exact beta_prefix_extend_witness_witness_left",
                f"have hold : exists i j n. (k = v * i + j /\\ (({_lt('j', 'v', tag='extend_old_bound')}) /\\ (({_product_cell_terms('lb','lc','rb','rc','w','v','i','j','n',tag='extend_old_cell')}) /\\ ({_at('tb','tc','k','n',tag='mcp_extend_old_output')}))))",
                "specialize hprevious k", "apply hprevious", "exact hsplit_right", "cases hold", "cases hold_witness", "cases hold_witness_witness", "cases hold_witness_witness_witness", "cases hold_witness_witness_witness_right", "cases hold_witness_witness_witness_right_right",
                "exists x5", "exists x6", "exists x7", "split", "exact hold_witness_witness_witness_left", "split", "exact hold_witness_witness_witness_right_left", "split", "exact hold_witness_witness_witness_right_right_left",
                "specialize beta_prefix_extend_witness_witness_right k", "specialize beta_prefix_extend_witness_witness_right x7", "apply beta_prefix_extend_witness_witness_right", "exact hsplit_right", "exact hold_witness_witness_witness_right_right_right",
            ),
            "Append one computed matrix-product cell to a beta-coded row-major prefix without losing any earlier exact cell.",
        ),
        spec(
            BETA_MATRIX_PRODUCT_PREFIX_EXISTS_NONZERO,
            f"forall lb lc rb rc w v l. ~(v = 0) -> exists tb tc. ({prefix_result})",
            ("add_eq_zero_right", "succ_ne_zero", BETA_MATRIX_PRODUCT_POINT_EXISTS, BETA_MATRIX_PRODUCT_PREFIX_EXTEND),
            (
                "intro lb", "intro lc", "intro rb", "intro rc", "intro w", "intro v", "induction l", "intro hv", "exists 0", "exists 0", "intro k", "intro hk", "exfalso", "cases hk",
                "have hzero : S k = 0", "specialize add_eq_zero_right x", "specialize add_eq_zero_right (S k)", "apply add_eq_zero_right", "exact hk_witness", "specialize succ_ne_zero k", "apply succ_ne_zero", "exact hzero",
                "intro hv", f"have hprevious : exists tb tc. ({prefix_previous})", "apply IH", "exact hv", "cases hprevious", "cases hprevious_witness",
                f"have hpoint : {_point_terms('lb','lc','rb','rc','w','v','l',tag='exists_have_point')}",
                f"specialize {BETA_MATRIX_PRODUCT_POINT_EXISTS} lb", f"specialize {BETA_MATRIX_PRODUCT_POINT_EXISTS} lc", f"specialize {BETA_MATRIX_PRODUCT_POINT_EXISTS} rb", f"specialize {BETA_MATRIX_PRODUCT_POINT_EXISTS} rc", f"specialize {BETA_MATRIX_PRODUCT_POINT_EXISTS} w", f"specialize {BETA_MATRIX_PRODUCT_POINT_EXISTS} v", f"specialize {BETA_MATRIX_PRODUCT_POINT_EXISTS} l", f"apply {BETA_MATRIX_PRODUCT_POINT_EXISTS}", "exact hv",
                f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXTEND} lb", f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXTEND} lc", f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXTEND} rb", f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXTEND} rc", f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXTEND} w", f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXTEND} v", f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXTEND} x", f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXTEND} x1", f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXTEND} l", f"apply {BETA_MATRIX_PRODUCT_PREFIX_EXTEND}", "exact hprevious_witness_witness", "exact hpoint",
            ),
            "Every finite prefix of the product of arbitrary coded natural matrices admits one complete output beta code.",
        ),
        spec(
            BETA_MATRIX_PRODUCT_EXISTS_NONZERO_WIDTH,
            f"forall lb lc rb rc w v r. ~(v = 0) -> exists tb tc. ({full})",
            (BETA_MATRIX_PRODUCT_PREFIX_EXISTS_NONZERO,),
            (
                "intro lb", "intro lc", "intro rb", "intro rc", "intro w", "intro v", "intro r", "intro hv",
                f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXISTS_NONZERO} lb", f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXISTS_NONZERO} lc", f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXISTS_NONZERO} rb", f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXISTS_NONZERO} rc", f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXISTS_NONZERO} w", f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXISTS_NONZERO} v", f"specialize {BETA_MATRIX_PRODUCT_PREFIX_EXISTS_NONZERO} (r * v)", f"apply {BETA_MATRIX_PRODUCT_PREFIX_EXISTS_NONZERO}", "exact hv",
            ),
            "Arbitrary finite natural matrix multiplication with a nonzero output width has a fully coded row-major output.",
        ),
        spec(
            BETA_MATRIX_PRODUCT_EMPTY_EXISTS,
            f"forall lb lc rb rc w v. exists tb tc. ({empty})",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro lb", "intro lc", "intro rb", "intro rc", "intro w", "intro v", "exists 0", "exists 0", "intro k", "intro hk", "exfalso", "cases hk", "have hzero : S k = 0", "specialize add_eq_zero_right x", "specialize add_eq_zero_right (S k)", "apply add_eq_zero_right", "exact hk_witness", "specialize succ_ne_zero k", "apply succ_ne_zero", "exact hzero",
            ),
            "Every empty matrix-output prefix has a constructive beta code regardless of the declared dimensions.",
        ),
        spec(
            BETA_MATRIX_PRODUCT_EXISTS,
            f"forall lb lc rb rc w v r. exists tb tc. ({full})",
            ("eq_decidable", BETA_MATRIX_PRODUCT_EMPTY_EXISTS, BETA_MATRIX_PRODUCT_EXISTS_NONZERO_WIDTH),
            (
                "intro lb", "intro lc", "intro rb", "intro rc", "intro w", "intro v", "intro r", "specialize eq_decidable v", "specialize eq_decidable 0", "cases eq_decidable",
                "have hlength : r * v = 0", "rewrite eq_decidable_left", "apply PA5", "rewrite hlength",
                f"specialize {BETA_MATRIX_PRODUCT_EMPTY_EXISTS} lb", f"specialize {BETA_MATRIX_PRODUCT_EMPTY_EXISTS} lc", f"specialize {BETA_MATRIX_PRODUCT_EMPTY_EXISTS} rb", f"specialize {BETA_MATRIX_PRODUCT_EMPTY_EXISTS} rc", f"specialize {BETA_MATRIX_PRODUCT_EMPTY_EXISTS} w", f"specialize {BETA_MATRIX_PRODUCT_EMPTY_EXISTS} v", f"exact {BETA_MATRIX_PRODUCT_EMPTY_EXISTS}",
                f"specialize {BETA_MATRIX_PRODUCT_EXISTS_NONZERO_WIDTH} lb", f"specialize {BETA_MATRIX_PRODUCT_EXISTS_NONZERO_WIDTH} lc", f"specialize {BETA_MATRIX_PRODUCT_EXISTS_NONZERO_WIDTH} rb", f"specialize {BETA_MATRIX_PRODUCT_EXISTS_NONZERO_WIDTH} rc", f"specialize {BETA_MATRIX_PRODUCT_EXISTS_NONZERO_WIDTH} w", f"specialize {BETA_MATRIX_PRODUCT_EXISTS_NONZERO_WIDTH} v", f"specialize {BETA_MATRIX_PRODUCT_EXISTS_NONZERO_WIDTH} r", f"apply {BETA_MATRIX_PRODUCT_EXISTS_NONZERO_WIDTH}", "exact eq_decidable_right",
            ),
            "Every pair of arbitrary finite natural matrices, including zero-width boundaries, has a complete beta-coded product.",
        ),
        spec(
            BETA_POINTWISE_ADD_PREFIX_EXTEND,
            f"forall mb mc sb sc tb tc l a b. ({add_before}) -> ({add_left}) -> ({add_right}) -> exists z d. ({add_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt", "beta_at_exists", "beta_at_unique"),
            (
                "intro mb", "intro mc", "intro sb", "intro sc", "intro tb", "intro tc", "intro l", "intro a", "intro b", "intro hprevious", "intro hleft", "intro hright",
                "specialize beta_prefix_extend l", "specialize beta_prefix_extend tb", "specialize beta_prefix_extend tc", "specialize beta_prefix_extend (a + b)", "cases beta_prefix_extend", "cases beta_prefix_extend_witness", "cases beta_prefix_extend_witness_witness",
                "exists x", "exists x1", "intro i", "intro m", "intro n", "intro target", "intro hi", "intro hm", "intro hn", "intro ht",
                "have hsplit : i = l \\/ exists gap. gap + S i = l", "specialize finite_lt_succ_eq_or_lt l", "specialize finite_lt_succ_eq_or_lt i", "apply finite_lt_succ_eq_or_lt", "exact hi", "cases hsplit",
                "rewrite hsplit_left at hm", "rewrite hsplit_left at hm", "rewrite hsplit_left at hn", "rewrite hsplit_left at hn", "rewrite hsplit_left at ht", "rewrite hsplit_left at ht",
                "have hfirst : a = m", "specialize beta_at_unique mb", "specialize beta_at_unique mc", "specialize beta_at_unique l", "specialize beta_at_unique a", "specialize beta_at_unique m", "apply beta_at_unique", "exact hleft", "exact hm",
                "have hsecond : b = n", "specialize beta_at_unique sb", "specialize beta_at_unique sc", "specialize beta_at_unique l", "specialize beta_at_unique b", "specialize beta_at_unique n", "apply beta_at_unique", "exact hright", "exact hn",
                "have htotal : target = a + b", "specialize beta_at_unique x", "specialize beta_at_unique x1", "specialize beta_at_unique l", "specialize beta_at_unique target", "specialize beta_at_unique (a + b)", "apply beta_at_unique", "exact ht", "exact beta_prefix_extend_witness_witness_left",
                "trans a + b", "exact htotal", "congr", "exact hfirst", "exact hsecond",
                f"have hold : exists q. ({_at('tb','tc','i','q',tag='mcp_add_old_exists')})", "specialize beta_at_exists tb", "specialize beta_at_exists tc", "specialize beta_at_exists i", "exact beta_at_exists", "cases hold",
                f"have hnew_old : {_at('x','x1','i','x2',tag='mcp_add_new_old')}", "specialize beta_prefix_extend_witness_witness_right i", "specialize beta_prefix_extend_witness_witness_right x2", "apply beta_prefix_extend_witness_witness_right", "exact hsplit_right", "exact hold_witness",
                "have htarget_old : target = x2", "specialize beta_at_unique x", "specialize beta_at_unique x1", "specialize beta_at_unique i", "specialize beta_at_unique target", "specialize beta_at_unique x2", "apply beta_at_unique", "exact ht", "exact hnew_old",
                "have hold_sum : x2 = m + n", "specialize hprevious i", "specialize hprevious m", "specialize hprevious n", "specialize hprevious x2", "apply hprevious", "exact hsplit_right", "exact hm", "exact hn", "exact hold_witness", "trans x2", "exact htarget_old", "exact hold_sum",
            ),
            "Extend a beta-coded pointwise sum while preserving every earlier decoded summand and sum.",
        ),
        spec(
            BETA_POINTWISE_ADD_PREFIX_EXISTS,
            f"forall mb mc sb sc l. exists tb tc. ({add_exists})",
            ("add_eq_zero_right", "succ_ne_zero", "beta_at_exists", BETA_POINTWISE_ADD_PREFIX_EXTEND),
            (
                "intro mb", "intro mc", "intro sb", "intro sc", "induction l", "exists 0", "exists 0", "intro i", "intro a", "intro b", "intro target", "intro hi", "intro ha", "intro hb", "intro ht", "exfalso", "cases hi", "have hzero : S i = 0", "specialize add_eq_zero_right x", "specialize add_eq_zero_right (S i)", "apply add_eq_zero_right", "exact hi_witness", "specialize succ_ne_zero i", "apply succ_ne_zero", "exact hzero",
                f"have hprevious : exists tb tc. ({add_previous})", "exact IH", "cases hprevious", "cases hprevious_witness",
                f"have hleft : exists a. ({_at('mb','mc','l','a',tag='mcp_add_exists_left')})", "specialize beta_at_exists mb", "specialize beta_at_exists mc", "specialize beta_at_exists l", "exact beta_at_exists", "cases hleft",
                f"have hright : exists b. ({_at('sb','sc','l','b',tag='mcp_add_exists_right')})", "specialize beta_at_exists sb", "specialize beta_at_exists sc", "specialize beta_at_exists l", "exact beta_at_exists", "cases hright",
                f"specialize {BETA_POINTWISE_ADD_PREFIX_EXTEND} mb", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXTEND} mc", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXTEND} sb", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXTEND} sc", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXTEND} x", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXTEND} x1", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXTEND} l", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXTEND} x2", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXTEND} x3", f"apply {BETA_POINTWISE_ADD_PREFIX_EXTEND}", "exact hprevious_witness_witness", "exact hleft_witness", "exact hright_witness",
            ),
            "Every pair of finite beta-coded natural vectors has a fully coded exact pointwise sum.",
        ),
        spec(
            BETA_SIGNED_MATRIX_PRODUCT_EXISTS,
            f"forall ab ac db dc eb ec fb fc w v r. exists pb pc nb nc. ({signed_matrix})",
            (BETA_MATRIX_PRODUCT_EXISTS, BETA_POINTWISE_ADD_PREFIX_EXISTS),
            (
                "intro ab", "intro ac", "intro db", "intro dc", "intro eb", "intro ec", "intro fb", "intro fc", "intro w", "intro v", "intro r",
                *matrix_exists("ab", "ac", "eb", "ec", "hpp", "smatrix_have_pp"),
                *matrix_exists("db", "dc", "fb", "fc", "hnn", "smatrix_have_nn"),
                *matrix_exists("ab", "ac", "fb", "fc", "hpn", "smatrix_have_pn"),
                *matrix_exists("db", "dc", "eb", "ec", "hnp", "smatrix_have_np"),
                f"have hpositive : exists pb pc. ({_pointwise_add_terms('x','x1','x2','x3','pb','pc','r * v',tag='smatrix_have_positive')})",
                f"specialize {BETA_POINTWISE_ADD_PREFIX_EXISTS} x", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXISTS} x1", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXISTS} x2", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXISTS} x3", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXISTS} (r * v)", f"exact {BETA_POINTWISE_ADD_PREFIX_EXISTS}", "cases hpositive", "cases hpositive_witness",
                f"have hnegative : exists nb nc. ({_pointwise_add_terms('x4','x5','x6','x7','nb','nc','r * v',tag='smatrix_have_negative')})",
                f"specialize {BETA_POINTWISE_ADD_PREFIX_EXISTS} x4", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXISTS} x5", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXISTS} x6", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXISTS} x7", f"specialize {BETA_POINTWISE_ADD_PREFIX_EXISTS} (r * v)", f"exact {BETA_POINTWISE_ADD_PREFIX_EXISTS}", "cases hnegative", "cases hnegative_witness",
                "exists x8", "exists x9", "exists x10", "exists x11", "exists x", "exists x1", "exists x2", "exists x3", "exists x4", "exists x5", "exists x6", "exists x7", "split", "exact hpp_witness_witness", "split", "exact hnn_witness_witness", "split", "exact hpn_witness_witness", "split", "exact hnp_witness_witness", "split", "exact hpositive_witness_witness", "exact hnegative_witness_witness",
            ),
            "Every pair of arbitrary finite signed natural-pair matrices has a complete exact beta-coded signed matrix product, including all zero-dimensional boundaries.",
        ),
        spec(
            SIGNED_PAIR_PRODUCT_EXISTS,
            "forall a b c d. exists p n. (p = a * c + b * d /\\ n = a * d + b * c)",
            (),
            ("intro a", "intro b", "intro c", "intro d", "exists a * c + b * d", "exists a * d + b * c", "split", "refl", "refl"),
            "Every pair of signed natural-pair integers has exact positive and negative multiplication components.",
        ),
        spec(
            SIGNED_PAIR_PRODUCT_FUNCTIONAL,
            "forall a b c d p n q m. (p = a * c + b * d /\\ n = a * d + b * c) -> (q = a * c + b * d /\\ m = a * d + b * c) -> (p = q /\\ n = m)",
            (),
            (
                "intro a", "intro b", "intro c", "intro d", "intro p", "intro n", "intro q", "intro m", "intro hleft", "intro hright", "cases hleft", "cases hright", "split", "trans a * c + b * d", "exact hleft_left", "symm", "exact hright_left", "trans a * d + b * c", "exact hleft_right", "symm", "exact hright_right",
            ),
            "Exact positive and negative multiplication components of two signed pairs are independently unique.",
        ),
        spec(
            BETA_SIGNED_DOT_PRODUCT_EXISTS,
            f"forall ab ac db dc eb ec fb fc l. exists p n. ({signed})",
            (BETA_DOT_PRODUCT_EXISTS,),
            (
                "intro ab", "intro ac", "intro db", "intro dc", "intro eb", "intro ec", "intro fb", "intro fc", "intro l",
                *dot_exists("ab", "ac", "eb", "ec", "hpp", "mcp_signed_have_pp"),
                *dot_exists("db", "dc", "fb", "fc", "hnn", "mcp_signed_have_nn"),
                *dot_exists("ab", "ac", "fb", "fc", "hpn", "mcp_signed_have_pn"),
                *dot_exists("db", "dc", "eb", "ec", "hnp", "mcp_signed_have_np"),
                "exists x + x1", "exists x2 + x3", "exists x", "exists x1", "exists x2", "exists x3", "split", "exact hpp_witness", "split", "exact hnn_witness", "split", "exact hpn_witness", "split", "exact hnp_witness", "split", "refl", "refl",
            ),
            "Every pair of arbitrarily long beta-coded signed vectors has an exact constructive signed dot product.",
        ),
        spec(
            BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL,
            f"forall ab ac db dc eb ec fb fc l p n q m. ({signed}) -> ({signed_other}) -> (p = q /\\ n = m)",
            (BETA_DOT_PRODUCT_FUNCTIONAL,),
            (
                "intro ab", "intro ac", "intro db", "intro dc", "intro eb", "intro ec", "intro fb", "intro fc", "intro l", "intro p", "intro n", "intro q", "intro m", "intro hleft", "intro hright",
                "cases hleft", "cases hleft_witness", "cases hleft_witness_witness", "cases hleft_witness_witness_witness", "cases hleft_witness_witness_witness_witness", "cases hleft_witness_witness_witness_witness_right", "cases hleft_witness_witness_witness_witness_right_right", "cases hleft_witness_witness_witness_witness_right_right_right", "cases hleft_witness_witness_witness_witness_right_right_right_right",
                "cases hright", "cases hright_witness", "cases hright_witness_witness", "cases hright_witness_witness_witness", "cases hright_witness_witness_witness_witness", "cases hright_witness_witness_witness_witness_right", "cases hright_witness_witness_witness_witness_right_right", "cases hright_witness_witness_witness_witness_right_right_right", "cases hright_witness_witness_witness_witness_right_right_right_right",
                *dot_unique("ab", "ac", "eb", "ec", "x", "x4", "hleft_witness_witness_witness_witness_left", "hright_witness_witness_witness_witness_left", "hpp"),
                *dot_unique("db", "dc", "fb", "fc", "x1", "x5", "hleft_witness_witness_witness_witness_right_left", "hright_witness_witness_witness_witness_right_left", "hnn"),
                *dot_unique("ab", "ac", "fb", "fc", "x2", "x6", "hleft_witness_witness_witness_witness_right_right_left", "hright_witness_witness_witness_witness_right_right_left", "hpn"),
                *dot_unique("db", "dc", "eb", "ec", "x3", "x7", "hleft_witness_witness_witness_witness_right_right_right_left", "hright_witness_witness_witness_witness_right_right_right_left", "hnp"),
                "split", "trans x + x1", "exact hleft_witness_witness_witness_witness_right_right_right_right_left", "trans x4 + x5", "congr", "exact hpp", "exact hnn", "symm", "exact hright_witness_witness_witness_witness_right_right_right_right_left", "trans x2 + x3", "exact hleft_witness_witness_witness_witness_right_right_right_right_right", "trans x6 + x7", "congr", "exact hpn", "exact hnp", "symm", "exact hright_witness_witness_witness_witness_right_right_right_right_right",
            ),
            "Both natural components of the arbitrary finite signed dot product are independent of all product-code witnesses.",
        ),
        spec(
            BETA_SIGNED_DOT_PRODUCT_EXISTS_UNIQUE,
            f"forall ab ac db dc eb ec fb fc l. exists p n. (({signed}) /\\ forall q m. ({signed_other}) -> (p = q /\\ n = m))",
            (BETA_SIGNED_DOT_PRODUCT_EXISTS, BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL),
            (
                "intro ab", "intro ac", "intro db", "intro dc", "intro eb", "intro ec", "intro fb", "intro fc", "intro l",
                f"specialize {BETA_SIGNED_DOT_PRODUCT_EXISTS} ab", f"specialize {BETA_SIGNED_DOT_PRODUCT_EXISTS} ac", f"specialize {BETA_SIGNED_DOT_PRODUCT_EXISTS} db", f"specialize {BETA_SIGNED_DOT_PRODUCT_EXISTS} dc", f"specialize {BETA_SIGNED_DOT_PRODUCT_EXISTS} eb", f"specialize {BETA_SIGNED_DOT_PRODUCT_EXISTS} ec", f"specialize {BETA_SIGNED_DOT_PRODUCT_EXISTS} fb", f"specialize {BETA_SIGNED_DOT_PRODUCT_EXISTS} fc", f"specialize {BETA_SIGNED_DOT_PRODUCT_EXISTS} l", f"cases {BETA_SIGNED_DOT_PRODUCT_EXISTS}", f"cases {BETA_SIGNED_DOT_PRODUCT_EXISTS}_witness", "exists x", "exists x1", "split", f"exact {BETA_SIGNED_DOT_PRODUCT_EXISTS}_witness_witness", "intro q", "intro m", "intro hother",
                f"specialize {BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL} ab", f"specialize {BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL} ac", f"specialize {BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL} db", f"specialize {BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL} dc", f"specialize {BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL} eb", f"specialize {BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL} ec", f"specialize {BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL} fb", f"specialize {BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL} fc", f"specialize {BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL} l", f"specialize {BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL} x", f"specialize {BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL} x1", f"specialize {BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL} q", f"specialize {BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL} m", f"apply {BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL}", f"exact {BETA_SIGNED_DOT_PRODUCT_EXISTS}_witness_witness", "exact hother",
            ),
            "Every arbitrarily long beta-coded signed vector pair has exactly one positive/negative dot-product pair.",
        ),
        spec(
            SIGNED_MATRIX_TWO_FULL_DETERMINANT_EXISTS,
            f"forall ap an bp bn cp cn dp dn. exists p n. (p = {det2p} /\\ n = {det2n})",
            (),
            ("intro ap", "intro an", "intro bp", "intro bn", "intro cp", "intro cn", "intro dp", "intro dn", f"exists {det2p}", f"exists {det2n}", "split", "refl", "refl"),
            "Every genuinely signed two-by-two integer matrix has an exact subtraction-free signed determinant pair.",
        ),
        spec(
            SIGNED_MATRIX_TWO_FULL_DETERMINANT_FUNCTIONAL,
            f"forall ap an bp bn cp cn dp dn p n q m. (p = {det2p} /\\ n = {det2n}) -> (q = {det2p} /\\ m = {det2n}) -> (p = q /\\ n = m)",
            (),
            ("intro ap", "intro an", "intro bp", "intro bn", "intro cp", "intro cn", "intro dp", "intro dn", "intro p", "intro n", "intro q", "intro m", "intro hleft", "intro hright", "cases hleft", "cases hright", "split", f"trans {det2p}", "exact hleft_left", "symm", "exact hright_left", f"trans {det2n}", "exact hleft_right", "symm", "exact hright_right"),
            "Both natural components of a genuinely signed two-by-two determinant are unique.",
        ),
        spec(
            SIGNED_MATRIX_THREE_FULL_DETERMINANT_EXISTS,
            f"forall ap an bp bn cp cn dp dn ep en fp fn gp gn hp hn ip inn. exists p n. (p = {det3p} /\\ n = {det3n})",
            (),
            (*tuple(f"intro {name}" for name in ("ap", "an", "bp", "bn", "cp", "cn", "dp", "dn", "ep", "en", "fp", "fn", "gp", "gn", "hp", "hn", "ip", "inn")), f"exists {det3p}", f"exists {det3n}", "split", "refl", "refl"),
            "Every genuinely signed three-by-three integer matrix has its exact constructive cofactor-expansion determinant pair.",
        ),
        spec(
            SIGNED_MATRIX_THREE_FULL_DETERMINANT_FUNCTIONAL,
            f"forall ap an bp bn cp cn dp dn ep en fp fn gp gn hp hn ip inn p n q m. (p = {det3p} /\\ n = {det3n}) -> (q = {det3p} /\\ m = {det3n}) -> (p = q /\\ n = m)",
            (),
            (*tuple(f"intro {name}" for name in ("ap", "an", "bp", "bn", "cp", "cn", "dp", "dn", "ep", "en", "fp", "fn", "gp", "gn", "hp", "hn", "ip", "inn", "p", "n", "q", "m")), "intro hleft", "intro hright", "cases hleft", "cases hright", "split", f"trans {det3p}", "exact hleft_left", "symm", "exact hright_left", f"trans {det3n}", "exact hleft_right", "symm", "exact hright_right"),
            "Both exact constructive cofactor components of every signed three-by-three determinant are unique.",
        ),
    )


@dataclass(frozen=True, slots=True)
class SignedPair:
    """An immutable exact positive-minus-negative natural representation."""

    positive: int
    negative: int

    @property
    def value(self) -> int:
        return self.positive - self.negative


@dataclass(frozen=True, slots=True)
class SignedDotCertificate:
    left: tuple[SignedPair, ...]
    right: tuple[SignedPair, ...]
    positive_positive: tuple[int, ...]
    negative_negative: tuple[int, ...]
    positive_negative: tuple[int, ...]
    negative_positive: tuple[int, ...]
    result: SignedPair


@dataclass(frozen=True, slots=True)
class AffineSliceCertificate:
    source: tuple[int, ...]
    start: int
    stride: int
    length: int
    values: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class CodedNaturalMatrixProductCertificate:
    left: IntegerMatrix
    right: IntegerMatrix
    result: IntegerMatrix
    row_slices: tuple[tuple[int, ...], ...]
    column_slices: tuple[tuple[int, ...], ...]
    row_major_cells: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class CodedSignedMatrixProductCertificate:
    """The four natural products and both exact signed-output components."""

    left: IntegerMatrix
    right: IntegerMatrix
    positive_positive: CodedNaturalMatrixProductCertificate
    negative_negative: CodedNaturalMatrixProductCertificate
    positive_negative: CodedNaturalMatrixProductCertificate
    negative_positive: CodedNaturalMatrixProductCertificate
    positive_output: IntegerMatrix
    negative_output: IntegerMatrix
    signed_output: IntegerMatrix


def signed_pair(positive: int, negative: int) -> SignedPair:
    if type(positive) is not int or type(negative) is not int:
        raise CodedMatrixError("signed components must be exact Python integers")
    if not 0 <= positive <= MAX_COMPONENT or not 0 <= negative <= MAX_COMPONENT:
        raise CodedMatrixError("signed components must be bounded natural numbers")
    return SignedPair(positive, negative)


def certify_signed_dot(
    left: Iterable[SignedPair], right: Iterable[SignedPair]
) -> SignedDotCertificate:
    try:
        lhs = tuple(left)
        rhs = tuple(right)
    except TypeError as error:
        raise CodedMatrixError("signed vectors must be finite exact iterables") from error
    if len(lhs) != len(rhs) or len(lhs) > MAX_MATRIX_DIMENSION:
        raise CodedMatrixError("signed vectors require matching bounded lengths")
    if any(type(value) is not SignedPair for value in (*lhs, *rhs)):
        raise CodedMatrixError("signed vectors require exact signed-pair entries")
    for value in (*lhs, *rhs):
        if signed_pair(value.positive, value.negative) != value:
            raise CodedMatrixError("invalid signed-pair entry")
    pp = tuple(a.positive * b.positive for a, b in zip(lhs, rhs))
    nn = tuple(a.negative * b.negative for a, b in zip(lhs, rhs))
    pn = tuple(a.positive * b.negative for a, b in zip(lhs, rhs))
    np = tuple(a.negative * b.positive for a, b in zip(lhs, rhs))
    positive = sum(pp) + sum(nn)
    negative = sum(pn) + sum(np)
    if positive > MAX_COMPONENT or negative > MAX_COMPONENT:
        raise CodedMatrixError("signed dot output exceeds its bounded component budget")
    return SignedDotCertificate(lhs, rhs, pp, nn, pn, np, signed_pair(positive, negative))


def verify_signed_dot(receipt: SignedDotCertificate) -> bool:
    if type(receipt) is not SignedDotCertificate:
        return False
    try:
        return receipt == certify_signed_dot(receipt.left, receipt.right)
    except (CodedMatrixError, IndexError, OverflowError, TypeError, ValueError):
        return False


def certify_affine_slice(
    source: Iterable[int], start: int, stride: int, length: int
) -> AffineSliceCertificate:
    try:
        values = tuple(source)
    except TypeError as error:
        raise CodedMatrixError("slice sources must be finite natural iterables") from error
    if any(type(value) is not int or value < 0 for value in values):
        raise CodedMatrixError("slice sources must contain exact natural integers")
    if any(type(value) is not int or value < 0 for value in (start, stride, length)):
        raise CodedMatrixError("affine slice coordinates must be exact naturals")
    if length > MAX_MATRIX_DIMENSION:
        raise CodedMatrixError("affine slice exceeds its bounded length")
    if length and start + stride * (length - 1) >= len(values):
        raise CodedMatrixError("affine slice exceeds its supplied source prefix")
    return AffineSliceCertificate(
        values, start, stride, length, tuple(values[start + stride * index] for index in range(length))
    )


def verify_affine_slice(receipt: AffineSliceCertificate) -> bool:
    if type(receipt) is not AffineSliceCertificate:
        return False
    try:
        return receipt == certify_affine_slice(
            receipt.source, receipt.start, receipt.stride, receipt.length
        )
    except (CodedMatrixError, IndexError, OverflowError, TypeError, ValueError):
        return False


def certify_coded_natural_matrix_product(
    left: IntegerMatrix, right: IntegerMatrix
) -> CodedNaturalMatrixProductCertificate:
    if type(left) is not IntegerMatrix or type(right) is not IntegerMatrix:
        raise CodedMatrixError("coded matrix products require exact integer matrices")
    if left.width != right.height:
        raise CodedMatrixError("coded matrix multiplication dimensions do not match")
    if any(value < 0 for row in (*left.rows, *right.rows) for value in row):
        raise CodedMatrixError("natural coded matrix multiplication rejects signed entries")
    rows = tuple(tuple(row) for row in left.rows)
    columns = tuple(
        tuple(right.rows[index][column] for index in range(right.height))
        for column in range(right.width)
    )
    cells = tuple(
        sum(left_value * right_value for left_value, right_value in zip(row, column))
        for row in rows
        for column in columns
    )
    result_rows = tuple(
        tuple(cells[row * right.width + column] for column in range(right.width))
        for row in range(left.height)
    )
    try:
        result = integer_matrix(result_rows)
    except MatrixCertificateError as error:
        raise CodedMatrixError(str(error)) from error
    return CodedNaturalMatrixProductCertificate(left, right, result, rows, columns, cells)


def verify_coded_natural_matrix_product(
    receipt: CodedNaturalMatrixProductCertificate,
) -> bool:
    if type(receipt) is not CodedNaturalMatrixProductCertificate:
        return False
    try:
        return receipt == certify_coded_natural_matrix_product(receipt.left, receipt.right)
    except (CodedMatrixError, IndexError, OverflowError, TypeError, ValueError):
        return False


def _matrix_components(matrix: IntegerMatrix) -> tuple[IntegerMatrix, IntegerMatrix]:
    if type(matrix) is not IntegerMatrix:
        raise CodedMatrixError("signed matrix products require exact integer matrices")
    if any(abs(value) > MAX_COMPONENT for row in matrix.rows for value in row):
        raise CodedMatrixError("signed matrix entries exceed their component budget")
    try:
        return (
            integer_matrix(tuple(tuple(max(value, 0) for value in row) for row in matrix.rows)),
            integer_matrix(tuple(tuple(max(-value, 0) for value in row) for row in matrix.rows)),
        )
    except MatrixCertificateError as error:
        raise CodedMatrixError(str(error)) from error


def certify_coded_signed_matrix_product(
    left: IntegerMatrix, right: IntegerMatrix
) -> CodedSignedMatrixProductCertificate:
    """Construct all four exact products and canonical signed output codes."""

    left_positive, left_negative = _matrix_components(left)
    right_positive, right_negative = _matrix_components(right)
    if left.width != right.height:
        raise CodedMatrixError("signed matrix multiplication dimensions do not match")
    pp = certify_coded_natural_matrix_product(left_positive, right_positive)
    nn = certify_coded_natural_matrix_product(left_negative, right_negative)
    pn = certify_coded_natural_matrix_product(left_positive, right_negative)
    np = certify_coded_natural_matrix_product(left_negative, right_positive)
    positive_rows = tuple(
        tuple(pp.result.rows[row][column] + nn.result.rows[row][column] for column in range(right.width))
        for row in range(left.height)
    )
    negative_rows = tuple(
        tuple(pn.result.rows[row][column] + np.result.rows[row][column] for column in range(right.width))
        for row in range(left.height)
    )
    if any(value > MAX_COMPONENT for row in (*positive_rows, *negative_rows) for value in row):
        raise CodedMatrixError("signed matrix product exceeds its bounded component budget")
    try:
        positive = integer_matrix(positive_rows)
        negative = integer_matrix(negative_rows)
        signed = integer_matrix(
            tuple(
                tuple(positive.rows[row][column] - negative.rows[row][column] for column in range(right.width))
                for row in range(left.height)
            )
        )
    except MatrixCertificateError as error:
        raise CodedMatrixError(str(error)) from error
    return CodedSignedMatrixProductCertificate(left, right, pp, nn, pn, np, positive, negative, signed)


def verify_coded_signed_matrix_product(
    receipt: CodedSignedMatrixProductCertificate,
) -> bool:
    if type(receipt) is not CodedSignedMatrixProductCertificate:
        return False
    try:
        return receipt == certify_coded_signed_matrix_product(receipt.left, receipt.right)
    except (CodedMatrixError, IndexError, OverflowError, TypeError, ValueError):
        return False


__all__ = [
    "AffineSliceCertificate",
    "BETA_AFFINE_MATRIX_SLICE_EXISTS",
    "BETA_AFFINE_MATRIX_SLICE_EXTEND",
    "BETA_MATRIX_COLUMN_SLICE_EXISTS",
    "BETA_MATRIX_PRODUCT_CELL_EXISTS",
    "BETA_MATRIX_PRODUCT_EMPTY_EXISTS",
    "BETA_MATRIX_PRODUCT_EXISTS",
    "BETA_MATRIX_PRODUCT_EXISTS_NONZERO_WIDTH",
    "BETA_MATRIX_PRODUCT_POINT_EXISTS",
    "BETA_MATRIX_PRODUCT_PREFIX_EXISTS_NONZERO",
    "BETA_MATRIX_PRODUCT_PREFIX_EXTEND",
    "BETA_MATRIX_ROW_SLICE_EXISTS",
    "BETA_POINTWISE_ADD_PREFIX_EXISTS",
    "BETA_POINTWISE_ADD_PREFIX_EXTEND",
    "BETA_SIGNED_DOT_PRODUCT_EXISTS",
    "BETA_SIGNED_DOT_PRODUCT_EXISTS_UNIQUE",
    "BETA_SIGNED_DOT_PRODUCT_FUNCTIONAL",
    "BETA_SIGNED_MATRIX_PRODUCT_EXISTS",
    "CodedMatrixError",
    "CodedNaturalMatrixProductCertificate",
    "CodedSignedMatrixProductCertificate",
    "MAX_COMPONENT",
    "SIGNED_MATRIX_THREE_FULL_DETERMINANT_EXISTS",
    "SIGNED_MATRIX_THREE_FULL_DETERMINANT_FUNCTIONAL",
    "SIGNED_MATRIX_TWO_FULL_DETERMINANT_EXISTS",
    "SIGNED_MATRIX_TWO_FULL_DETERMINANT_FUNCTIONAL",
    "SIGNED_PAIR_PRODUCT_EXISTS",
    "SIGNED_PAIR_PRODUCT_FUNCTIONAL",
    "SignedDotCertificate",
    "SignedPair",
    "affine_matrix_slice_relation",
    "certify_affine_slice",
    "certify_coded_natural_matrix_product",
    "certify_coded_signed_matrix_product",
    "certify_signed_dot",
    "make_matrix_coded_product_candidate_theorems",
    "matrix_product_cell_relation",
    "matrix_product_prefix_relation",
    "pointwise_add_prefix_relation",
    "signed_dot_product_relation",
    "signed_matrix_product_relation",
    "signed_pair",
    "verify_affine_slice",
    "verify_coded_natural_matrix_product",
    "verify_coded_signed_matrix_product",
    "verify_signed_dot",
]
