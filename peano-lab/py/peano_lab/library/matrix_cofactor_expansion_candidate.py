"""Constructive complete cofactor-minor families and arbitrary signed Laplace folds.

Every public relation is a hygienic abbreviation over unchanged first-order
Heyting arithmetic.  The independently checked Alpha-v24 parent already
constructs each individual signed minor; this layer assembles *all* first-row
minors into one beta-coded finite family and computes arbitrary-length signed
alternating cofactor folds.  Supplied cofactor values are not asserted to be
determinants without an actual recursive evaluation certificate.  Thus the
full unrestricted determinant/rank/lattice milestone remains open.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .finite_fold_surface import _beta_at_term, _binders, _identifier, _variables, sum_relation
from .matrix_coded_product_candidate import _slice_terms
from .matrix_determinant_minors_candidate import (
    MAX_COFACTOR_DIMENSION,
    MAX_COFACTOR_ENTRY,
    MatrixMinorCertificate,
    _signed_minor_terms,
    certify_matrix_minor,
    verify_matrix_minor,
)
from .matrix_dot_product_candidate import (
    IntegerMatrix,
    MatrixCertificateError,
    certify_integer_determinant,
    integer_matrix,
)


class MatrixCofactorExpansionError(ValueError):
    """An exact conservative cofactor relation or bounded certificate failed."""


def _safe(tag: str) -> str:
    try:
        return _identifier(tag, "matrix-cofactor binder tag")
    except ValueError as error:
        raise MatrixCofactorExpansionError(str(error)) from error


def _arguments(*labelled: tuple[str, str]) -> tuple[str, ...]:
    try:
        values = _variables(*labelled)
        if len(set(values)) != len(values):
            raise ValueError("matrix-cofactor arguments must be distinct identifiers")
        if any(value.startswith(("ff_", "mce_")) for value in values):
            raise ValueError("generated matrix-cofactor binder captures an argument")
        return values
    except ValueError as error:
        raise MatrixCofactorExpansionError(str(error)) from error


def _at(code: str, scale: str, index: str, value: str, *, tag: str) -> str:
    safe = _safe(tag)
    avoid = tuple(item for item in (code, scale, index, value) if item.isidentifier())
    try:
        return _beta_at_term(code, scale, index, value, tag=f"mce_{safe}", avoid=avoid)
    except ValueError as error:
        raise MatrixCofactorExpansionError(str(error)) from error


def _lt(left: str, right: str, *, tag: str, avoid: tuple[str, ...] = ()) -> str:
    safe = _safe(tag)
    try:
        (gap,) = _binders(f"mce_{safe}", avoid, ("gap",))
    except ValueError as error:
        raise MatrixCofactorExpansionError(str(error)) from error
    return f"exists {gap}. {gap} + S ({left}) = ({right})"


def _le(left: str, right: str, *, tag: str, avoid: tuple[str, ...] = ()) -> str:
    safe = _safe(tag)
    try:
        (gap,) = _binders(f"mce_{safe}", avoid, ("gap",))
    except ValueError as error:
        raise MatrixCofactorExpansionError(str(error)) from error
    return f"exists {gap}. {gap} + ({left}) = ({right})"


def _pair(left: str, right: str) -> str:
    return f"(({left}) + ({right})) * S (({left}) + ({right})) + (({right}) + ({right}))"


def _pack_four(up: str, us: str, un: str, ut: str) -> str:
    return _pair(_pair(up, us), _pair(un, ut))


def _cases_exists(name: str, count: int) -> tuple[str, ...]:
    return tuple(f"cases {name}{'_witness' * index}" for index in range(count))


def _cases_conjunction(name: str, count: int) -> tuple[str, ...]:
    return tuple(f"cases {name}{'_right' * index}" for index in range(count - 1))


def _conjunction_factor(name: str, count: int, index: int) -> str:
    return f"{name}{'_right' * index}{'_left' if index < count - 1 else ''}"


def _sum_terms(code: str, scale: str, length: str, result: str, *, tag: str) -> str:
    safe = _safe(tag)
    if length.isidentifier():
        return sum_relation(code, scale, length, result, tag=f"mce_{safe}")
    marker = f"mce_length_marker_{safe}"
    expression = sum_relation(code, scale, marker, result, tag=f"mce_{safe}")
    if marker not in expression:
        raise MatrixCofactorExpansionError("exact finite-sum length marker disappeared")
    return expression.replace(marker, f"({length})")


def _beta_equality(
    code: str, scale: str, index: str, left: str, right: str,
    left_proof: str, right_proof: str, label: str,
) -> tuple[str, ...]:
    return (
        f"have {label} : {left} = {right}",
        f"specialize beta_at_unique {code}", f"specialize beta_at_unique {scale}",
        f"specialize beta_at_unique {index}", f"specialize beta_at_unique {left}",
        f"specialize beta_at_unique {right}", "apply beta_at_unique",
        f"exact {left_proof}", f"exact {right_proof}",
    )


def matrix_minor_four_code_relation(
    code: str, positive: str, positive_scale: str, negative: str, negative_scale: str,
    *, tag: str,
) -> str:
    """Expand the exact canonical nested doubled-Cantor minor-record code."""

    values = _arguments(
        (code, "minor record code"), (positive, "positive minor code"),
        (positive_scale, "positive minor scale"), (negative, "negative minor code"),
        (negative_scale, "negative minor scale"),
    )
    _safe(tag)
    return f"{values[0]} = {_pack_four(*values[1:])}"


def _record_terms(
    pb: str, pc: str, nb: str, nc: str, q: str, j: str, record: str, *, tag: str,
) -> str:
    safe = _safe(tag)
    avoid = tuple(value for value in (pb, pc, nb, nc, q, j, record) if value.isidentifier())
    up, us, un, ut = _binders(f"mce_record_{safe}", avoid, ("up", "us", "un", "ut"))
    nested = avoid + (up, us, un, ut)
    minor = _signed_minor_terms(
        pb, pc, nb, nc, f"S ({q})", "0", j, q, up, us, un, ut,
        tag=f"mce_{safe}_minor", avoid=nested,
    )
    return (
        f"exists {up} {us} {un} {ut}. "
        f"(({record} = {_pack_four(up, us, un, ut)}) /\\ ({minor}))"
    )


def signed_matrix_minor_record_relation(
    pb: str, pc: str, nb: str, nc: str, q: str, j: str, record: str, *, tag: str,
) -> str:
    """Expand one genuinely decoded signed first-row cofactor-minor record."""

    values = _arguments(
        (pb, "positive matrix code"), (pc, "positive matrix scale"),
        (nb, "negative matrix code"), (nc, "negative matrix scale"),
        (q, "minor width"), (j, "deleted column"), (record, "minor record code"),
    )
    return _record_terms(*values, tag=tag)


def _family_terms(
    pb: str, pc: str, nb: str, nc: str, q: str, code: str, scale: str, length: str,
    *, tag: str,
) -> str:
    safe = _safe(tag)
    avoid = tuple(
        item for item in (pb, pc, nb, nc, q, code, scale, length) if item.isidentifier()
    )
    index, value = _binders(f"mce_family_{safe}", avoid, ("index", "value"))
    bound = _lt(index, length, tag=f"{safe}_index", avoid=avoid + (index, value))
    entry = _at(code, scale, index, value, tag=f"{safe}_entry")
    record = _record_terms(pb, pc, nb, nc, q, index, value, tag=f"{safe}_record")
    return f"forall {index}. ({bound}) -> exists {value}. (({entry}) /\\ ({record}))"


def signed_cofactor_minor_prefix_relation(
    pb: str, pc: str, nb: str, nc: str, q: str, code: str, scale: str, length: str,
    *, tag: str,
) -> str:
    """Expand a complete prefix whose actual entries code exact signed minors."""

    values = _arguments(
        (pb, "positive matrix code"), (pc, "positive matrix scale"),
        (nb, "negative matrix code"), (nc, "negative matrix scale"),
        (q, "minor width"), (code, "minor family code"),
        (scale, "minor family scale"), (length, "minor family prefix length"),
    )
    return _family_terms(*values, tag=tag)


def _term_terms(ap: str, an: str, bp: str, bn: str, i: str, p: str, n: str, *, tag: str) -> str:
    safe = _safe(tag)
    avoid = tuple(value for value in (ap, an, bp, bn, i, p, n) if value.isidentifier())
    even, odd = _binders(f"mce_term_{safe}", avoid, ("even", "odd"))
    positive = f"({ap}) * ({bp}) + ({an}) * ({bn})"
    negative = f"({ap}) * ({bn}) + ({an}) * ({bp})"
    return (
        f"((exists {even}. {i} = 2 * {even}) /\\ "
        f"({p} = {positive} /\\ {n} = {negative})) \\/ "
        f"((exists {odd}. {i} = 2 * {odd} + 1) /\\ "
        f"({p} = {negative} /\\ {n} = {positive}))"
    )


def signed_alternating_cofactor_term_relation(
    ap: str, an: str, bp: str, bn: str, i: str, p: str, n: str, *, tag: str,
) -> str:
    """Expand one exact parity-correct genuinely signed Laplace product."""

    values = _arguments(
        (ap, "positive row entry"), (an, "negative row entry"),
        (bp, "positive cofactor entry"), (bn, "negative cofactor entry"),
        (i, "cofactor column"), (p, "positive signed product"),
        (n, "negative signed product"),
    )
    return _term_terms(*values, tag=tag)


def _alternating_prefix_terms(
    ab: str, ac: str, db: str, dc: str, eb: str, ec: str, fb: str, fc: str,
    ub: str, uc: str, vb: str, vc: str, length: str, *, tag: str,
) -> str:
    safe = _safe(tag)
    avoid = tuple(
        item for item in (ab, ac, db, dc, eb, ec, fb, fc, ub, uc, vb, vc, length)
        if item.isidentifier()
    )
    i, ap, an, bp, bn, p, n = _binders(
        f"mce_alternating_{safe}", avoid, ("index", "ap", "an", "bp", "bn", "p", "n")
    )
    bound = _lt(i, length, tag=f"{safe}_index", avoid=avoid + (i, ap, an, bp, bn, p, n))
    first = _at(ab, ac, i, ap, tag=f"{safe}_ap")
    second = _at(db, dc, i, an, tag=f"{safe}_an")
    third = _at(eb, ec, i, bp, tag=f"{safe}_bp")
    fourth = _at(fb, fc, i, bn, tag=f"{safe}_bn")
    positive = _at(ub, uc, i, p, tag=f"{safe}_positive")
    negative = _at(vb, vc, i, n, tag=f"{safe}_negative")
    term = _term_terms(ap, an, bp, bn, i, p, n, tag=f"{safe}_term")
    return (
        f"forall {i}. ({bound}) -> exists {ap} {an} {bp} {bn} {p} {n}. "
        f"(({first}) /\\ (({second}) /\\ (({third}) /\\ (({fourth}) /\\ "
        f"(({positive}) /\\ (({negative}) /\\ ({term})))))))"
    )


def signed_alternating_product_prefix_relation(
    ab: str, ac: str, db: str, dc: str, eb: str, ec: str, fb: str, fc: str,
    ub: str, uc: str, vb: str, vc: str, length: str, *, tag: str,
) -> str:
    """Expand every parity-correct product of four signed beta input streams."""

    values = _arguments(
        *((value, label) for value, label in zip(
            (ab, ac, db, dc, eb, ec, fb, fc, ub, uc, vb, vc, length),
            ("row positive code", "row positive scale", "row negative code", "row negative scale",
             "cofactor positive code", "cofactor positive scale", "cofactor negative code",
             "cofactor negative scale", "term positive code", "term positive scale",
             "term negative code", "term negative scale", "cofactor prefix length"),
        ))
    )
    return _alternating_prefix_terms(*values, tag=tag)


def _fold_terms(
    ab: str, ac: str, db: str, dc: str, eb: str, ec: str, fb: str, fc: str,
    length: str, positive: str, negative: str, *, tag: str,
) -> str:
    safe = _safe(tag)
    avoid = tuple(
        item for item in (ab, ac, db, dc, eb, ec, fb, fc, length, positive, negative)
        if item.isidentifier()
    )
    ub, uc, vb, vc = _binders(f"mce_fold_{safe}", avoid, ("ub", "uc", "vb", "vc"))
    prefix = _alternating_prefix_terms(
        ab, ac, db, dc, eb, ec, fb, fc, ub, uc, vb, vc, length, tag=f"{safe}_prefix"
    )
    left = _sum_terms(ub, uc, length, positive, tag=f"{safe}_positive")
    right = _sum_terms(vb, vc, length, negative, tag=f"{safe}_negative")
    return f"exists {ub} {uc} {vb} {vc}. (({prefix}) /\\ (({left}) /\\ ({right})))"


def signed_alternating_cofactor_fold_relation(
    ab: str, ac: str, db: str, dc: str, eb: str, ec: str, fb: str, fc: str,
    length: str, positive: str, negative: str, *, tag: str,
) -> str:
    """Expand the unique arbitrary-length signed alternating Laplace sum."""

    values = _arguments(
        *((value, label) for value, label in zip(
            (ab, ac, db, dc, eb, ec, fb, fc, length, positive, negative),
            ("row positive code", "row positive scale", "row negative code", "row negative scale",
             "cofactor positive code", "cofactor positive scale", "cofactor negative code",
             "cofactor negative scale", "cofactor prefix length", "positive sum", "negative sum"),
        ))
    )
    return _fold_terms(*values, tag=tag)


def _first_row_terms(
    pb: str, pc: str, nb: str, nc: str, q: str, eb: str, ec: str, fb: str,
    fc: str, positive: str, negative: str, *, tag: str,
) -> str:
    safe = _safe(tag)
    avoid = tuple(
        item for item in (pb, pc, nb, nc, q, eb, ec, fb, fc, positive, negative)
        if item.isidentifier()
    )
    ab, ac, db, dc = _binders(f"mce_row_{safe}", avoid, ("ab", "ac", "db", "dc"))
    posrow = _slice_terms(pb, pc, "0", "1", ab, ac, f"S ({q})", tag=f"mce_{safe}_positive")
    negrow = _slice_terms(nb, nc, "0", "1", db, dc, f"S ({q})", tag=f"mce_{safe}_negative")
    fold = _fold_terms(ab, ac, db, dc, eb, ec, fb, fc, f"S ({q})", positive, negative, tag=f"{safe}_fold")
    return f"exists {ab} {ac} {db} {dc}. (({posrow}) /\\ (({negrow}) /\\ ({fold})))"


def signed_first_row_cofactor_fold_relation(
    pb: str, pc: str, nb: str, nc: str, q: str, eb: str, ec: str, fb: str,
    fc: str, positive: str, negative: str, *, tag: str,
) -> str:
    """Expand the actual decoded first row and separately supplied cofactor values."""

    values = _arguments(
        *((value, label) for value, label in zip(
            (pb, pc, nb, nc, q, eb, ec, fb, fc, positive, negative),
            ("positive matrix code", "positive matrix scale", "negative matrix code",
             "negative matrix scale", "minor width", "cofactor positive code",
             "cofactor positive scale", "cofactor negative code", "cofactor negative scale",
             "positive Laplace sum", "negative Laplace sum"),
        ))
    )
    return _first_row_terms(*values, tag=tag)


def make_matrix_cofactor_expansion_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build dependency-ordered original-kernel first-row cofactor candidates."""

    pack = _pack_four("up", "us", "un", "ut")
    pack_other = _pack_four("vp", "vs", "vn", "vt")
    record = _record_terms("pb", "pc", "nb", "nc", "q", "j", "z", tag="result")
    record_minor = _signed_minor_terms(
        "pb", "pc", "nb", "nc", "S q", "0", "j", "q", "up", "us", "un", "ut",
        tag="mce_record_projection", avoid=("pb", "pc", "nb", "nc", "q", "j", "up", "us", "un", "ut"),
    )
    column_bound = _lt("j", "S q", tag="record_column", avoid=("q", "j"))
    row_bound = _lt("0", "S q", tag="record_row", avoid=("q",))
    family_empty = _family_terms("pb", "pc", "nb", "nc", "q", "u", "v", "0", tag="empty")
    family_before = _family_terms("pb", "pc", "nb", "nc", "q", "u", "v", "l", tag="before")
    family_after = _family_terms("pb", "pc", "nb", "nc", "q", "z", "e", "S l", tag="after")
    family_last_record = _record_terms("pb", "pc", "nb", "nc", "q", "l", "k", tag="last")
    family_result = _family_terms("pb", "pc", "nb", "nc", "q", "u", "v", "l", tag="result")
    family_full = _family_terms("pb", "pc", "nb", "nc", "q", "u", "v", "S q", tag="full")
    family_entry = _record_terms("pb", "pc", "nb", "nc", "q", "j", "z", tag="family_entry")
    length_bound = _le("l", "S q", tag="family_length", avoid=("q", "l"))
    term = _term_terms("ap", "an", "bp", "bn", "i", "p", "n", tag="result")
    term_other = _term_terms("ap", "an", "bp", "bn", "i", "r", "s", tag="other")
    source_codes = ("ab", "ac", "db", "dc", "eb", "ec", "fb", "fc")
    source_intro = tuple(f"intro {name}" for name in source_codes)
    alt_empty = _alternating_prefix_terms(*source_codes, "ub", "uc", "vb", "vc", "0", tag="empty")
    alt_before = _alternating_prefix_terms(*source_codes, "ub", "uc", "vb", "vc", "l", tag="before")
    alt_after = _alternating_prefix_terms(*source_codes, "xb", "xc", "yb", "yc", "S l", tag="after")
    alt_result = _alternating_prefix_terms(*source_codes, "ub", "uc", "vb", "vc", "l", tag="existence")
    last_entries = tuple(
        _at(code, scale, "l", value, tag=f"last_{value}")
        for code, scale, value in (("ab","ac","ap"),("db","dc","an"),("eb","ec","bp"),("fb","fc","bn"))
    )
    last_term = _term_terms("ap", "an", "bp", "bn", "l", "p", "n", tag="last")
    fold_result = _fold_terms(*source_codes, "l", "p", "n", tag="result")
    fold_other = _fold_terms(*source_codes, "l", "r", "s", tag="other")
    fold_empty = _fold_terms(*source_codes, "0", "p", "n", tag="empty")
    prefix_successor = _alternating_prefix_terms(
        *source_codes, "ub", "uc", "vb", "vc", "S l", tag="successor"
    )
    prefix_restricted = _alternating_prefix_terms(
        *source_codes, "ub", "uc", "vb", "vc", "l", tag="restricted"
    )
    prefix_other = _alternating_prefix_terms(
        *source_codes, "wb", "wc", "zb", "zc", "l", tag="other"
    )
    value_bound = _lt("i", "l", tag="value_bound", avoid=("i", "l"))
    value_entries = tuple(
        _at(code, scale, "i", value, tag=f"value_{value}")
        for code, scale, value in (("ab","ac","ap"),("db","dc","an"),("eb","ec","bp"),("fb","fc","bn"))
    )
    first_row = _first_row_terms("pb","pc","nb","nc","q","eb","ec","fb","fc","p","n",tag="result")

    def fold_transport(*, negative: bool) -> tuple[str, ...]:
        old_code, old_scale, new_code, new_scale, result = (
            ("x2", "x3", "x6", "x7", "n")
            if negative else ("x", "x1", "x4", "x5", "p")
        )
        old_other_code, old_other_scale = (("x", "x1") if negative else ("x2", "x3"))
        first_sum = (
            "hfirst_witness_witness_witness_witness_right_right"
            if negative else "hfirst_witness_witness_witness_witness_right_left"
        )
        label = "htransport_negative" if negative else "htransport_positive"
        equality = "x8 = x9 /\\ a = x10" if negative else "a = x9 /\\ x8 = x10"
        return (
            f"have {label} : ({sum_relation(new_code,new_scale,'l',result,tag='mce_transport_'+('negative' if negative else 'positive'))})",
            f"specialize beta_sum_transport_prefix {old_code}",
            f"specialize beta_sum_transport_prefix {old_scale}",
            f"specialize beta_sum_transport_prefix {new_code}",
            f"specialize beta_sum_transport_prefix {new_scale}",
            "specialize beta_sum_transport_prefix l",
            f"specialize beta_sum_transport_prefix {result}",
            "apply beta_sum_transport_prefix", f"exact {first_sum}",
            "intro i", "intro a", "intro hi", "intro ha",
            f"have holdother : exists z. ({_at(old_other_code,old_other_scale,'i','z',tag='transport_old_other_'+('n' if negative else 'p'))})",
            f"specialize beta_at_exists {old_other_code}",
            f"specialize beta_at_exists {old_other_scale}",
            "specialize beta_at_exists i", "exact beta_at_exists", "cases holdother",
            f"have hnewpositive : exists z. ({_at('x4','x5','i','z',tag='transport_new_positive_'+('n' if negative else 'p'))})",
            "specialize beta_at_exists x4", "specialize beta_at_exists x5",
            "specialize beta_at_exists i", "exact beta_at_exists", "cases hnewpositive",
            f"have hnewnegative : exists z. ({_at('x6','x7','i','z',tag='transport_new_negative_'+('n' if negative else 'p'))})",
            "specialize beta_at_exists x6", "specialize beta_at_exists x7",
            "specialize beta_at_exists i", "exact beta_at_exists", "cases hnewnegative",
            f"have hequal : {equality}",
            *tuple(f"specialize signed_alternating_product_prefix_pointwise_functional {value}" for value in source_codes),
            *tuple(f"specialize signed_alternating_product_prefix_pointwise_functional {value}" for value in
                   ("x","x1","x2","x3","x4","x5","x6","x7","l","i")),
            *tuple(f"specialize signed_alternating_product_prefix_pointwise_functional {value}" for value in
                   (("x8","a","x9","x10") if negative else ("a","x8","x9","x10"))),
            "apply signed_alternating_product_prefix_pointwise_functional",
            "exact hfirst_witness_witness_witness_witness_left",
            "exact hsecond_witness_witness_witness_witness_left", "exact hi",
            *( ("exact holdother_witness", "exact ha") if negative else
               ("exact ha", "exact holdother_witness") ),
            "exact hnewpositive_witness", "exact hnewnegative_witness", "cases hequal",
            *( ("rewrite hequal_right", "rewrite hequal_right", "exact hnewnegative_witness")
               if negative else
               ("rewrite hequal_left", "rewrite hequal_left", "exact hnewpositive_witness") ),
        )
    return (
        spec(
            "matrix_minor_four_code_exists",
            f"forall up us un ut. exists z. z = {pack}",
            (),
            ("intro up", "intro us", "intro un", "intro ut", f"exists {pack}", "refl"),
            "Four arbitrary natural minor-code components have one exact nested doubled-Cantor record.",
        ),
        spec(
            "matrix_minor_four_code_output_functional",
            f"forall up us un ut z w. z = {pack} -> w = {pack} -> z = w",
            (),
            (
                "intro up", "intro us", "intro un", "intro ut", "intro z", "intro w",
                "intro hz", "intro hw", f"trans {pack}", "exact hz", "symm", "exact hw",
            ),
            "The canonical four-component minor-record output is unique.",
        ),
        spec(
            "matrix_minor_four_code_components_injective",
            f"forall z up us un ut vp vs vn vt. z = {pack} -> z = {pack_other} -> "
            "(up = vp /\\ (us = vs /\\ (un = vn /\\ ut = vt)))",
            ("pair_code_injective",),
            (
                "intro z", "intro up", "intro us", "intro un", "intro ut",
                "intro vp", "intro vs", "intro vn", "intro vt", "intro hfirst", "intro hsecond",
                f"have houter : {_pair('up','us')} = {_pair('vp','vs')} /\\ "
                f"{_pair('un','ut')} = {_pair('vn','vt')}",
                "specialize pair_code_injective z",
                f"specialize pair_code_injective ({_pair('up','us')})",
                f"specialize pair_code_injective ({_pair('un','ut')})",
                f"specialize pair_code_injective ({_pair('vp','vs')})",
                f"specialize pair_code_injective ({_pair('vn','vt')})",
                "apply pair_code_injective", "exact hfirst", "exact hsecond",
                "cases houter",
                "have hpositive : up = vp /\\ us = vs",
                f"specialize pair_code_injective ({_pair('up','us')})",
                "specialize pair_code_injective up", "specialize pair_code_injective us",
                "specialize pair_code_injective vp", "specialize pair_code_injective vs",
                "apply pair_code_injective", "refl", "exact houter_left",
                "have hnegative : un = vn /\\ ut = vt",
                f"specialize pair_code_injective ({_pair('un','ut')})",
                "specialize pair_code_injective un", "specialize pair_code_injective ut",
                "specialize pair_code_injective vn", "specialize pair_code_injective vt",
                "apply pair_code_injective", "refl", "exact houter_right",
                "cases hpositive", "cases hnegative", "split", "exact hpositive_left",
                "split", "exact hpositive_right", "split", "exact hnegative_left",
                "exact hnegative_right",
            ),
            "An exact nested doubled-Cantor cofactor record uniquely determines all four minor-code components.",
        ),
        spec(
            "signed_cofactor_minor_record_exists",
            f"forall pb pc nb nc q j. ({column_bound}) -> exists z. ({record})",
            ("zero_le", "succ_le_succ", "beta_signed_matrix_minor_exists"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro q", "intro j", "intro hj",
                f"have hrow : {row_bound}",
                "specialize succ_le_succ 0", "specialize succ_le_succ q",
                "apply succ_le_succ", "specialize zero_le q", "exact zero_le",
                f"have hminor : exists up us un ut. ({record_minor})",
                "specialize beta_signed_matrix_minor_exists pb",
                "specialize beta_signed_matrix_minor_exists pc",
                "specialize beta_signed_matrix_minor_exists nb",
                "specialize beta_signed_matrix_minor_exists nc",
                "specialize beta_signed_matrix_minor_exists q",
                "specialize beta_signed_matrix_minor_exists 0",
                "specialize beta_signed_matrix_minor_exists j",
                "apply beta_signed_matrix_minor_exists", "exact hrow", "exact hj",
                "cases hminor", "cases hminor_witness", "cases hminor_witness_witness",
                "cases hminor_witness_witness_witness",
                f"exists {_pack_four('x','x1','x2','x3')}",
                "exists x", "exists x1", "exists x2", "exists x3", "split", "refl",
                "exact hminor_witness_witness_witness_witness",
            ),
            "Every valid first-row column has one exact record containing the entire independently constructed signed cofactor minor.",
        ),
        spec(
            "signed_cofactor_minor_record_projects_minor",
            f"forall pb pc nb nc q j z. ({record}) -> exists up us un ut. ({record_minor})",
            (),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro q", "intro j", "intro z",
                "intro hrecord", "cases hrecord", "cases hrecord_witness",
                "cases hrecord_witness_witness", "cases hrecord_witness_witness_witness",
                "cases hrecord_witness_witness_witness_witness",
                "exists x", "exists x1", "exists x2", "exists x3",
                "exact hrecord_witness_witness_witness_witness_right",
            ),
            "Every cofactor record projects an actual complete signed deleted-row/deleted-column matrix minor.",
        ),
        spec(
            "signed_cofactor_minor_prefix_empty",
            f"forall pb pc nb nc q u v. ({family_empty})",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro q", "intro u", "intro v",
                "intro i", "intro hi", "exfalso", "cases hi",
                "have hzero : S i = 0", "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)", "apply add_eq_zero_right",
                "exact hi_witness", "specialize succ_ne_zero i", "apply succ_ne_zero",
                "exact hzero",
            ),
            "Every beta code vacuously describes the genuinely empty signed cofactor-minor prefix.",
        ),
        spec(
            "signed_cofactor_minor_prefix_extend",
            f"forall pb pc nb nc q u v l k. ({family_before}) -> ({family_last_record}) -> "
            f"exists z e. ({family_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro q", "intro u", "intro v",
                "intro l", "intro k", "intro hprefix", "intro hrecord",
                f"have hext : exists z e. (({_at('z','e','l','k',tag='family_extension')}) /\\ "
                f"forall i a. ({_lt('i','l',tag='family_preserved')}) -> "
                f"({_at('u','v','i','a',tag='family_old')}) -> ({_at('z','e','i','a',tag='family_new')}))",
                "specialize beta_prefix_extend l", "specialize beta_prefix_extend u",
                "specialize beta_prefix_extend v", "specialize beta_prefix_extend k",
                "exact beta_prefix_extend", "cases hext", "cases hext_witness",
                "cases hext_witness_witness", "exists x", "exists x1", "intro i", "intro hi",
                "have hsplit : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l", "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt", "exact hi", "cases hsplit",
                "exists k", "split", "rewrite hsplit_left", "rewrite hsplit_left",
                "exact hext_witness_witness_left", "rewrite hsplit_left", "rewrite hsplit_left",
                "rewrite hsplit_left", "rewrite hsplit_left",
                "exact hrecord",
                f"have hprevious : exists a. (({_at('u','v','i','a',tag='family_have_previous')}) /\\ "
                f"({_record_terms('pb','pc','nb','nc','q','i','a',tag='family_have_record')}))",
                "specialize hprefix i", "apply hprefix", "exact hsplit_right",
                "cases hprevious", "cases hprevious_witness", "exists x2", "split",
                "specialize hext_witness_witness_right i",
                "specialize hext_witness_witness_right x2", "apply hext_witness_witness_right",
                "exact hsplit_right", "exact hprevious_witness_left",
                "exact hprevious_witness_right",
            ),
            "Appending one genuinely constructed signed minor preserves every previously encoded cofactor record.",
        ),
        spec(
            "signed_cofactor_minor_prefix_exists_bounded",
            f"forall pb pc nb nc q l. ({length_bound}) -> exists u v. ({family_result})",
            (
                "le_of_succ_le_succ", "le_succ", "signed_cofactor_minor_prefix_empty",
                "signed_cofactor_minor_record_exists", "signed_cofactor_minor_prefix_extend",
            ),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro q", "induction l",
                "intro hbound", "exists 0", "exists 0",
                "specialize signed_cofactor_minor_prefix_empty pb",
                "specialize signed_cofactor_minor_prefix_empty pc",
                "specialize signed_cofactor_minor_prefix_empty nb",
                "specialize signed_cofactor_minor_prefix_empty nc",
                "specialize signed_cofactor_minor_prefix_empty q",
                "specialize signed_cofactor_minor_prefix_empty 0",
                "specialize signed_cofactor_minor_prefix_empty 0",
                "exact signed_cofactor_minor_prefix_empty",
                "intro hbound",
                f"have hshort : {_le('l','S q',tag='induction_short')}",
                "have hpredecessor : exists gap. gap + l = q",
                "specialize le_of_succ_le_succ l", "specialize le_of_succ_le_succ q",
                "apply le_of_succ_le_succ", "exact hbound",
                "specialize le_succ l", "specialize le_succ q", "apply le_succ",
                "exact hpredecessor",
                f"have hprevious : exists u v. ({_family_terms('pb','pc','nb','nc','q','u','v','l',tag='induction_previous')})",
                "apply IH", "exact hshort", "cases hprevious", "cases hprevious_witness",
                f"have hrecord : exists z. ({_record_terms('pb','pc','nb','nc','q','l','z',tag='induction_record')})",
                "specialize signed_cofactor_minor_record_exists pb",
                "specialize signed_cofactor_minor_record_exists pc",
                "specialize signed_cofactor_minor_record_exists nb",
                "specialize signed_cofactor_minor_record_exists nc",
                "specialize signed_cofactor_minor_record_exists q",
                "specialize signed_cofactor_minor_record_exists l",
                "apply signed_cofactor_minor_record_exists", "exact hbound",
                "cases hrecord",
                "specialize signed_cofactor_minor_prefix_extend pb",
                "specialize signed_cofactor_minor_prefix_extend pc",
                "specialize signed_cofactor_minor_prefix_extend nb",
                "specialize signed_cofactor_minor_prefix_extend nc",
                "specialize signed_cofactor_minor_prefix_extend q",
                "specialize signed_cofactor_minor_prefix_extend x",
                "specialize signed_cofactor_minor_prefix_extend x1",
                "specialize signed_cofactor_minor_prefix_extend l",
                "specialize signed_cofactor_minor_prefix_extend x2",
                "apply signed_cofactor_minor_prefix_extend",
                "exact hprevious_witness_witness", "exact hrecord_witness",
            ),
            "Every constructively bounded first-row cofactor prefix has one beta code containing all actual signed minors.",
        ),
        spec(
            "signed_cofactor_minor_family_exists",
            f"forall pb pc nb nc q. exists u v. ({family_full})",
            ("le_refl", "signed_cofactor_minor_prefix_exists_bounded"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro q",
                "specialize signed_cofactor_minor_prefix_exists_bounded pb",
                "specialize signed_cofactor_minor_prefix_exists_bounded pc",
                "specialize signed_cofactor_minor_prefix_exists_bounded nb",
                "specialize signed_cofactor_minor_prefix_exists_bounded nc",
                "specialize signed_cofactor_minor_prefix_exists_bounded q",
                "specialize signed_cofactor_minor_prefix_exists_bounded (S q)",
                "apply signed_cofactor_minor_prefix_exists_bounded",
                "specialize le_refl (S q)", "exact le_refl",
            ),
            "Every arbitrary-dimensional signed square matrix has one complete beta-coded family containing ALL exact first-row signed cofactor minors.",
        ),
        spec(
            "signed_cofactor_minor_family_entry_exists",
            f"forall pb pc nb nc q u v j. ({family_full}) -> ({column_bound}) -> "
            f"exists z. (({_at('u','v','j','z',tag='entry_result')}) /\\ ({family_entry}))",
            (),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro q", "intro u",
                "intro v", "intro j", "intro hfamily", "intro hbound",
                "specialize hfamily j", "apply hfamily", "exact hbound",
            ),
            "Each valid first-row column extracts its exact actual signed cofactor record from the complete family.",
        ),
        spec(
            "signed_cofactor_minor_family_entry_projects_minor",
            f"forall pb pc nb nc q u v j. ({family_full}) -> ({column_bound}) -> "
            f"exists up us un ut. ({record_minor})",
            (
                "signed_cofactor_minor_family_entry_exists",
                "signed_cofactor_minor_record_projects_minor",
            ),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro q", "intro u",
                "intro v", "intro j", "intro hfamily", "intro hbound",
                f"have hentry : exists z. (({_at('u','v','j','z',tag='project_entry')}) /\\ "
                f"({_record_terms('pb','pc','nb','nc','q','j','z',tag='project_record')}))",
                "specialize signed_cofactor_minor_family_entry_exists pb",
                "specialize signed_cofactor_minor_family_entry_exists pc",
                "specialize signed_cofactor_minor_family_entry_exists nb",
                "specialize signed_cofactor_minor_family_entry_exists nc",
                "specialize signed_cofactor_minor_family_entry_exists q",
                "specialize signed_cofactor_minor_family_entry_exists u",
                "specialize signed_cofactor_minor_family_entry_exists v",
                "specialize signed_cofactor_minor_family_entry_exists j",
                "apply signed_cofactor_minor_family_entry_exists", "exact hfamily", "exact hbound",
                "cases hentry", "cases hentry_witness",
                "specialize signed_cofactor_minor_record_projects_minor pb",
                "specialize signed_cofactor_minor_record_projects_minor pc",
                "specialize signed_cofactor_minor_record_projects_minor nb",
                "specialize signed_cofactor_minor_record_projects_minor nc",
                "specialize signed_cofactor_minor_record_projects_minor q",
                "specialize signed_cofactor_minor_record_projects_minor j",
                "specialize signed_cofactor_minor_record_projects_minor x",
                "apply signed_cofactor_minor_record_projects_minor", "exact hentry_witness_right",
            ),
            "Every decoded member of the complete first-row cofactor family is a genuine independently encoded signed matrix minor.",
        ),
        spec(
            "signed_alternating_cofactor_term_exists",
            f"forall ap an bp bn i. exists p n. ({term})",
            ("parity_cases",),
            (
                "intro ap", "intro an", "intro bp", "intro bn", "intro i",
                "specialize parity_cases i", "cases parity_cases",
                "cases parity_cases_witness",
                "exists ap * bp + an * bn", "exists ap * bn + an * bp",
                "left", "split", "exists x", "exact parity_cases_witness_left",
                "split", "refl", "refl",
                "exists ap * bn + an * bp", "exists ap * bp + an * bn",
                "right", "split", "exists x", "exact parity_cases_witness_right",
                "split", "refl", "refl",
            ),
            "Every genuinely signed row/cofactor pair has its exact parity-correct alternating product.",
        ),
        spec(
            "signed_alternating_cofactor_term_functional",
            f"forall ap an bp bn i p n r s. ({term}) -> ({term_other}) -> (p = r /\\ n = s)",
            ("even_not_odd", "odd_not_even"),
            (
                "intro ap", "intro an", "intro bp", "intro bn", "intro i",
                "intro p", "intro n", "intro r", "intro s", "intro hfirst", "intro hsecond",
                "cases hfirst", "cases hfirst_left", "cases hfirst_left_right",
                "cases hsecond", "cases hsecond_left", "cases hsecond_left_right",
                "split", "trans ap * bp + an * bn", "exact hfirst_left_right_left",
                "symm", "exact hsecond_left_right_left",
                "trans ap * bn + an * bp", "exact hfirst_left_right_right",
                "symm", "exact hsecond_left_right_right",
                "cases hsecond_right", "exfalso", "specialize even_not_odd i",
                "apply even_not_odd", "exact hfirst_left_left", "exact hsecond_right_left",
                "cases hfirst_right", "cases hfirst_right_right",
                "cases hsecond", "cases hsecond_left", "exfalso",
                "specialize odd_not_even i", "apply odd_not_even",
                "exact hfirst_right_left", "exact hsecond_left_left",
                "cases hsecond_right", "cases hsecond_right_right", "split",
                "trans ap * bn + an * bp", "exact hfirst_right_right_left",
                "symm", "exact hsecond_right_right_left",
                "trans ap * bp + an * bn", "exact hfirst_right_right_right",
                "symm", "exact hsecond_right_right_right",
            ),
            "Both components of the signed alternating cofactor product are uniquely determined.",
        ),
        spec(
            "signed_alternating_cofactor_term_even",
            f"forall ap an bp bn i p n. ({term}) -> (exists k. i = 2 * k) -> "
            "(p = ap * bp + an * bn /\\ n = ap * bn + an * bp)",
            ("even_not_odd",),
            (
                "intro ap", "intro an", "intro bp", "intro bn", "intro i", "intro p", "intro n",
                "intro hterm", "intro heven", "cases hterm", "cases hterm_left",
                "exact hterm_left_right", "cases hterm_right", "exfalso",
                "specialize even_not_odd i", "apply even_not_odd", "exact heven",
                "exact hterm_right_left",
            ),
            "At every even cofactor column, the signed alternating product has the unswapped exact positive and negative components.",
        ),
        spec(
            "signed_alternating_cofactor_term_odd",
            f"forall ap an bp bn i p n. ({term}) -> (exists k. i = 2 * k + 1) -> "
            "(p = ap * bn + an * bp /\\ n = ap * bp + an * bn)",
            ("odd_not_even",),
            (
                "intro ap", "intro an", "intro bp", "intro bn", "intro i", "intro p", "intro n",
                "intro hterm", "intro hodd", "cases hterm", "cases hterm_left", "exfalso",
                "specialize odd_not_even i", "apply odd_not_even", "exact hodd",
                "exact hterm_left_left", "cases hterm_right", "exact hterm_right_right",
            ),
            "At every odd cofactor column, the signed alternating product swaps its exact positive and negative components.",
        ),
        spec(
            "signed_alternating_cofactor_term_exists_unique",
            f"forall ap an bp bn i. exists p n. (({term}) /\\ "
            f"forall r s. ({term_other}) -> (p = r /\\ n = s))",
            ("signed_alternating_cofactor_term_exists", "signed_alternating_cofactor_term_functional"),
            (
                "intro ap", "intro an", "intro bp", "intro bn", "intro i",
                "specialize signed_alternating_cofactor_term_exists ap",
                "specialize signed_alternating_cofactor_term_exists an",
                "specialize signed_alternating_cofactor_term_exists bp",
                "specialize signed_alternating_cofactor_term_exists bn",
                "specialize signed_alternating_cofactor_term_exists i",
                "cases signed_alternating_cofactor_term_exists",
                "cases signed_alternating_cofactor_term_exists_witness",
                "exists x", "exists x1", "split",
                "exact signed_alternating_cofactor_term_exists_witness_witness",
                "intro r", "intro s", "intro hother",
                "specialize signed_alternating_cofactor_term_functional ap",
                "specialize signed_alternating_cofactor_term_functional an",
                "specialize signed_alternating_cofactor_term_functional bp",
                "specialize signed_alternating_cofactor_term_functional bn",
                "specialize signed_alternating_cofactor_term_functional i",
                "specialize signed_alternating_cofactor_term_functional x",
                "specialize signed_alternating_cofactor_term_functional x1",
                "specialize signed_alternating_cofactor_term_functional r",
                "specialize signed_alternating_cofactor_term_functional s",
                "apply signed_alternating_cofactor_term_functional",
                "exact signed_alternating_cofactor_term_exists_witness_witness", "exact hother",
            ),
            "Every arbitrary genuinely signed cofactor term has exactly one parity-correct subtraction-free component pair.",
        ),
        spec(
            "signed_alternating_product_prefix_empty",
            f"forall {' '.join(source_codes)} ub uc vb vc. ({alt_empty})",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                *source_intro, "intro ub", "intro uc", "intro vb", "intro vc",
                "intro i", "intro hi", "exfalso", "cases hi",
                "have hzero : S i = 0", "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)", "apply add_eq_zero_right",
                "exact hi_witness", "specialize succ_ne_zero i", "apply succ_ne_zero",
                "exact hzero",
            ),
            "The length-zero signed alternating product prefix has no unjustified cofactor terms.",
        ),
        spec(
            "signed_alternating_product_prefix_extend",
            f"forall {' '.join(source_codes)} ub uc vb vc l ap an bp bn p n. "
            f"({alt_before}) -> ({last_entries[0]}) -> ({last_entries[1]}) -> "
            f"({last_entries[2]}) -> ({last_entries[3]}) -> ({last_term}) -> "
            f"exists xb xc yb yc. ({alt_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                *source_intro, "intro ub", "intro uc", "intro vb", "intro vc", "intro l",
                "intro ap", "intro an", "intro bp", "intro bn", "intro p", "intro n",
                "intro hprefix", "intro hap", "intro han", "intro hbp", "intro hbn", "intro hterm",
                f"have hpos : exists xb xc. (({_at('xb','xc','l','p',tag='extend_positive')}) /\\ "
                f"forall i a. ({_lt('i','l',tag='extend_positive_bound')}) -> "
                f"({_at('ub','uc','i','a',tag='extend_positive_old')}) -> "
                f"({_at('xb','xc','i','a',tag='extend_positive_new')}))",
                "specialize beta_prefix_extend l", "specialize beta_prefix_extend ub",
                "specialize beta_prefix_extend uc", "specialize beta_prefix_extend p",
                "exact beta_prefix_extend", "cases hpos", "cases hpos_witness",
                "cases hpos_witness_witness",
                f"have hneg : exists yb yc. (({_at('yb','yc','l','n',tag='extend_negative')}) /\\ "
                f"forall i a. ({_lt('i','l',tag='extend_negative_bound')}) -> "
                f"({_at('vb','vc','i','a',tag='extend_negative_old')}) -> "
                f"({_at('yb','yc','i','a',tag='extend_negative_new')}))",
                "specialize beta_prefix_extend l", "specialize beta_prefix_extend vb",
                "specialize beta_prefix_extend vc", "specialize beta_prefix_extend n",
                "exact beta_prefix_extend", "cases hneg", "cases hneg_witness",
                "cases hneg_witness_witness",
                "exists x", "exists x1", "exists x2", "exists x3", "intro i", "intro hi",
                "have hsplit : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l", "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt", "exact hi", "cases hsplit",
                "exists ap", "exists an", "exists bp", "exists bn", "exists p", "exists n",
                "split", "rewrite hsplit_left", "rewrite hsplit_left", "exact hap",
                "split", "rewrite hsplit_left", "rewrite hsplit_left", "exact han",
                "split", "rewrite hsplit_left", "rewrite hsplit_left", "exact hbp",
                "split", "rewrite hsplit_left", "rewrite hsplit_left", "exact hbn",
                "split", "rewrite hsplit_left", "rewrite hsplit_left", "exact hpos_witness_witness_left",
                "split", "rewrite hsplit_left", "rewrite hsplit_left", "exact hneg_witness_witness_left",
                "rewrite hsplit_left", "rewrite hsplit_left", "exact hterm",
                f"have hprevious : exists ap an bp bn p n. "
                f"(({_at('ab','ac','i','ap',tag='previous_ap')}) /\\ "
                f"(({_at('db','dc','i','an',tag='previous_an')}) /\\ "
                f"(({_at('eb','ec','i','bp',tag='previous_bp')}) /\\ "
                f"(({_at('fb','fc','i','bn',tag='previous_bn')}) /\\ "
                f"(({_at('ub','uc','i','p',tag='previous_positive')}) /\\ "
                f"(({_at('vb','vc','i','n',tag='previous_negative')}) /\\ "
                f"({_term_terms('ap','an','bp','bn','i','p','n',tag='previous_term')})))))))",
                "specialize hprefix i", "apply hprefix", "exact hsplit_right",
                *_cases_exists("hprevious", 6),
                *_cases_conjunction("hprevious" + "_witness" * 6, 7),
                "exists x4", "exists x5", "exists x6", "exists x7", "exists x8", "exists x9",
                "split", f"exact {_conjunction_factor('hprevious'+'_witness'*6,7,0)}",
                "split", f"exact {_conjunction_factor('hprevious'+'_witness'*6,7,1)}",
                "split", f"exact {_conjunction_factor('hprevious'+'_witness'*6,7,2)}",
                "split", f"exact {_conjunction_factor('hprevious'+'_witness'*6,7,3)}",
                "split", "specialize hpos_witness_witness_right i",
                "specialize hpos_witness_witness_right x8", "apply hpos_witness_witness_right",
                "exact hsplit_right", f"exact {_conjunction_factor('hprevious'+'_witness'*6,7,4)}",
                "split", "specialize hneg_witness_witness_right i",
                "specialize hneg_witness_witness_right x9", "apply hneg_witness_witness_right",
                "exact hsplit_right", f"exact {_conjunction_factor('hprevious'+'_witness'*6,7,5)}",
                f"exact {_conjunction_factor('hprevious'+'_witness'*6,7,6)}",
            ),
            "Two beta recodings simultaneously append the exact parity-correct signed cofactor product and preserve all earlier terms.",
        ),
        spec(
            "signed_alternating_product_prefix_exists",
            f"forall {' '.join(source_codes)} l. exists ub uc vb vc. ({alt_result})",
            (
                "beta_at_exists", "signed_alternating_cofactor_term_exists",
                "signed_alternating_product_prefix_empty",
                "signed_alternating_product_prefix_extend",
            ),
            (
                *source_intro, "induction l", "exists 0", "exists 0", "exists 0", "exists 0",
                *tuple(f"specialize signed_alternating_product_prefix_empty {value}" for value in source_codes),
                "specialize signed_alternating_product_prefix_empty 0",
                "specialize signed_alternating_product_prefix_empty 0",
                "specialize signed_alternating_product_prefix_empty 0",
                "specialize signed_alternating_product_prefix_empty 0",
                "exact signed_alternating_product_prefix_empty",
                *_cases_exists("IH", 4),
                f"have hap : exists a. ({_at('ab','ac','l','a',tag='exists_ap')})",
                "specialize beta_at_exists ab", "specialize beta_at_exists ac",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases hap",
                f"have han : exists a. ({_at('db','dc','l','a',tag='exists_an')})",
                "specialize beta_at_exists db", "specialize beta_at_exists dc",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases han",
                f"have hbp : exists a. ({_at('eb','ec','l','a',tag='exists_bp')})",
                "specialize beta_at_exists eb", "specialize beta_at_exists ec",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases hbp",
                f"have hbn : exists a. ({_at('fb','fc','l','a',tag='exists_bn')})",
                "specialize beta_at_exists fb", "specialize beta_at_exists fc",
                "specialize beta_at_exists l", "exact beta_at_exists", "cases hbn",
                f"have hterm : exists p n. ({_term_terms('x4','x5','x6','x7','l','p','n',tag='exists_term')})",
                "specialize signed_alternating_cofactor_term_exists x4",
                "specialize signed_alternating_cofactor_term_exists x5",
                "specialize signed_alternating_cofactor_term_exists x6",
                "specialize signed_alternating_cofactor_term_exists x7",
                "specialize signed_alternating_cofactor_term_exists l",
                "exact signed_alternating_cofactor_term_exists", "cases hterm", "cases hterm_witness",
                *tuple(f"specialize signed_alternating_product_prefix_extend {value}" for value in source_codes),
                "specialize signed_alternating_product_prefix_extend x",
                "specialize signed_alternating_product_prefix_extend x1",
                "specialize signed_alternating_product_prefix_extend x2",
                "specialize signed_alternating_product_prefix_extend x3",
                "specialize signed_alternating_product_prefix_extend l",
                "specialize signed_alternating_product_prefix_extend x4",
                "specialize signed_alternating_product_prefix_extend x5",
                "specialize signed_alternating_product_prefix_extend x6",
                "specialize signed_alternating_product_prefix_extend x7",
                "specialize signed_alternating_product_prefix_extend x8",
                "specialize signed_alternating_product_prefix_extend x9",
                "apply signed_alternating_product_prefix_extend",
                "exact IH_witness_witness_witness_witness", "exact hap_witness", "exact han_witness",
                "exact hbp_witness", "exact hbn_witness", "exact hterm_witness_witness",
            ),
            "Every arbitrary finite signed row and signed cofactor-value stream has complete beta-coded positive and negative alternating-product streams.",
        ),
        spec(
            "signed_alternating_product_prefix_restrict",
            f"forall {' '.join(source_codes)} ub uc vb vc l. ({prefix_successor}) -> ({prefix_restricted})",
            ("le_succ",),
            (
                *source_intro, "intro ub", "intro uc", "intro vb", "intro vc", "intro l",
                "intro hprefix", "intro i", "intro hi", "specialize hprefix i", "apply hprefix",
                "specialize le_succ (S i)", "specialize le_succ l", "apply le_succ", "exact hi",
            ),
            "An exact signed alternating cofactor prefix of successor length restricts to its genuine earlier prefix.",
        ),
        spec(
            "signed_alternating_product_prefix_exact_term",
            f"forall {' '.join(source_codes)} ub uc vb vc l i ap an bp bn p n. "
            f"({alt_before}) -> ({value_bound}) -> ({value_entries[0]}) -> "
            f"({value_entries[1]}) -> ({value_entries[2]}) -> ({value_entries[3]}) -> "
            f"({_at('ub','uc','i','p',tag='value_positive')}) -> "
            f"({_at('vb','vc','i','n',tag='value_negative')}) -> ({term})",
            ("beta_at_unique",),
            (
                *source_intro, "intro ub", "intro uc", "intro vb", "intro vc", "intro l",
                "intro i", "intro ap", "intro an", "intro bp", "intro bn", "intro p", "intro n",
                "intro hprefix", "intro hbound", "intro hap", "intro han", "intro hbp",
                "intro hbn", "intro hp", "intro hn",
                f"have hentry : exists aa dd ee ff pp nn. "
                f"(({_at('ab','ac','i','aa',tag='exact_ap')}) /\\ "
                f"(({_at('db','dc','i','dd',tag='exact_an')}) /\\ "
                f"(({_at('eb','ec','i','ee',tag='exact_bp')}) /\\ "
                f"(({_at('fb','fc','i','ff',tag='exact_bn')}) /\\ "
                f"(({_at('ub','uc','i','pp',tag='exact_positive')}) /\\ "
                f"(({_at('vb','vc','i','nn',tag='exact_negative')}) /\\ "
                f"({_term_terms('aa','dd','ee','ff','i','pp','nn',tag='exact_term')})))))))",
                "specialize hprefix i", "apply hprefix", "exact hbound",
                *_cases_exists("hentry",6), *_cases_conjunction("hentry"+"_witness"*6,7),
                *_beta_equality("ab","ac","i","x","ap",_conjunction_factor("hentry"+"_witness"*6,7,0),"hap","hapa"),
                *_beta_equality("db","dc","i","x1","an",_conjunction_factor("hentry"+"_witness"*6,7,1),"han","hana"),
                *_beta_equality("eb","ec","i","x2","bp",_conjunction_factor("hentry"+"_witness"*6,7,2),"hbp","hbpa"),
                *_beta_equality("fb","fc","i","x3","bn",_conjunction_factor("hentry"+"_witness"*6,7,3),"hbn","hbna"),
                *_beta_equality("ub","uc","i","x4","p",_conjunction_factor("hentry"+"_witness"*6,7,4),"hp","hpa"),
                *_beta_equality("vb","vc","i","x5","n",_conjunction_factor("hentry"+"_witness"*6,7,5),"hn","hna"),
                *tuple(f"rewrite hapa at {_conjunction_factor('hentry'+'_witness'*6,7,6)}" for _ in range(4)),
                *tuple(f"rewrite hana at {_conjunction_factor('hentry'+'_witness'*6,7,6)}" for _ in range(4)),
                *tuple(f"rewrite hbpa at {_conjunction_factor('hentry'+'_witness'*6,7,6)}" for _ in range(4)),
                *tuple(f"rewrite hbna at {_conjunction_factor('hentry'+'_witness'*6,7,6)}" for _ in range(4)),
                *tuple(f"rewrite hpa at {_conjunction_factor('hentry'+'_witness'*6,7,6)}" for _ in range(2)),
                *tuple(f"rewrite hna at {_conjunction_factor('hentry'+'_witness'*6,7,6)}" for _ in range(2)),
                f"exact {_conjunction_factor('hentry'+'_witness'*6,7,6)}",
            ),
            "Any actual entries decoded from a signed alternating prefix satisfy the exact parity-correct signed cofactor term relation.",
        ),
        spec(
            "signed_alternating_product_prefix_pointwise_functional",
            f"forall {' '.join(source_codes)} ub uc vb vc wb wc zb zc l i p n r s. "
            f"({alt_before}) -> ({prefix_other}) -> ({value_bound}) -> "
            f"({_at('ub','uc','i','p',tag='pointwise_first_positive')}) -> "
            f"({_at('vb','vc','i','n',tag='pointwise_first_negative')}) -> "
            f"({_at('wb','wc','i','r',tag='pointwise_second_positive')}) -> "
            f"({_at('zb','zc','i','s',tag='pointwise_second_negative')}) -> (p = r /\\ n = s)",
            (
                "beta_at_exists", "signed_alternating_product_prefix_exact_term",
                "signed_alternating_cofactor_term_functional",
            ),
            (
                *source_intro, "intro ub", "intro uc", "intro vb", "intro vc",
                "intro wb", "intro wc", "intro zb", "intro zc", "intro l", "intro i",
                "intro p", "intro n", "intro r", "intro s", "intro hfirst", "intro hsecond",
                "intro hbound", "intro hp", "intro hn", "intro hr", "intro hs",
                f"have hap : exists a. ({_at('ab','ac','i','a',tag='functional_ap')})",
                "specialize beta_at_exists ab", "specialize beta_at_exists ac",
                "specialize beta_at_exists i", "exact beta_at_exists", "cases hap",
                f"have han : exists a. ({_at('db','dc','i','a',tag='functional_an')})",
                "specialize beta_at_exists db", "specialize beta_at_exists dc",
                "specialize beta_at_exists i", "exact beta_at_exists", "cases han",
                f"have hbp : exists a. ({_at('eb','ec','i','a',tag='functional_bp')})",
                "specialize beta_at_exists eb", "specialize beta_at_exists ec",
                "specialize beta_at_exists i", "exact beta_at_exists", "cases hbp",
                f"have hbn : exists a. ({_at('fb','fc','i','a',tag='functional_bn')})",
                "specialize beta_at_exists fb", "specialize beta_at_exists fc",
                "specialize beta_at_exists i", "exact beta_at_exists", "cases hbn",
                f"have hleft : ({_term_terms('x','x1','x2','x3','i','p','n',tag='functional_left')})",
                *tuple(f"specialize signed_alternating_product_prefix_exact_term {value}" for value in source_codes),
                *tuple(f"specialize signed_alternating_product_prefix_exact_term {value}" for value in
                       ("ub","uc","vb","vc","l","i","x","x1","x2","x3","p","n")),
                "apply signed_alternating_product_prefix_exact_term", "exact hfirst", "exact hbound",
                "exact hap_witness", "exact han_witness", "exact hbp_witness", "exact hbn_witness",
                "exact hp", "exact hn",
                f"have hright : ({_term_terms('x','x1','x2','x3','i','r','s',tag='functional_right')})",
                *tuple(f"specialize signed_alternating_product_prefix_exact_term {value}" for value in source_codes),
                *tuple(f"specialize signed_alternating_product_prefix_exact_term {value}" for value in
                       ("wb","wc","zb","zc","l","i","x","x1","x2","x3","r","s")),
                "apply signed_alternating_product_prefix_exact_term", "exact hsecond", "exact hbound",
                "exact hap_witness", "exact han_witness", "exact hbp_witness", "exact hbn_witness",
                "exact hr", "exact hs",
                "specialize signed_alternating_cofactor_term_functional x",
                "specialize signed_alternating_cofactor_term_functional x1",
                "specialize signed_alternating_cofactor_term_functional x2",
                "specialize signed_alternating_cofactor_term_functional x3",
                "specialize signed_alternating_cofactor_term_functional i",
                "specialize signed_alternating_cofactor_term_functional p",
                "specialize signed_alternating_cofactor_term_functional n",
                "specialize signed_alternating_cofactor_term_functional r",
                "specialize signed_alternating_cofactor_term_functional s",
                "apply signed_alternating_cofactor_term_functional", "exact hleft", "exact hright",
            ),
            "Both components of every arbitrary-arity signed alternating cofactor term are independent of all beta-recoding witnesses.",
        ),
        spec(
            "signed_alternating_cofactor_fold_exists",
            f"forall {' '.join(source_codes)} l. exists p n. ({fold_result})",
            ("signed_alternating_product_prefix_exists", "beta_sum_exists"),
            (
                *source_intro, "intro l",
                f"have hprefix : exists ub uc vb vc. ({alt_result})",
                *tuple(f"specialize signed_alternating_product_prefix_exists {value}" for value in source_codes),
                "specialize signed_alternating_product_prefix_exists l",
                "exact signed_alternating_product_prefix_exists",
                *_cases_exists("hprefix",4),
                f"have hpositive : exists p. ({sum_relation('x','x1','l','p',tag='mce_fold_have_positive')})",
                "specialize beta_sum_exists x", "specialize beta_sum_exists x1",
                "specialize beta_sum_exists l", "exact beta_sum_exists", "cases hpositive",
                f"have hnegative : exists n. ({sum_relation('x2','x3','l','n',tag='mce_fold_have_negative')})",
                "specialize beta_sum_exists x2", "specialize beta_sum_exists x3",
                "specialize beta_sum_exists l", "exact beta_sum_exists", "cases hnegative",
                "exists x4", "exists x5", "exists x", "exists x1", "exists x2", "exists x3",
                "split", "exact hprefix_witness_witness_witness_witness", "split",
                "exact hpositive_witness", "exact hnegative_witness",
            ),
            "Every arbitrary-length pair of signed beta-coded row/cofactor streams has exact positive and negative alternating Laplace-sum components.",
        ),
        spec(
            "signed_alternating_cofactor_fold_functional",
            f"forall {' '.join(source_codes)} l p n r s. ({fold_result}) -> ({fold_other}) -> "
            "(p = r /\\ n = s)",
            (
                "beta_at_exists", "beta_sum_transport_prefix", "beta_sum_functional",
                "signed_alternating_product_prefix_pointwise_functional",
            ),
            (
                *source_intro, "intro l", "intro p", "intro n", "intro r", "intro s",
                "intro hfirst", "intro hsecond",
                *_cases_exists("hfirst",4), "cases hfirst_witness_witness_witness_witness",
                "cases hfirst_witness_witness_witness_witness_right",
                *_cases_exists("hsecond",4), "cases hsecond_witness_witness_witness_witness",
                "cases hsecond_witness_witness_witness_witness_right",
                *fold_transport(negative=False), *fold_transport(negative=True), "split",
                "specialize beta_sum_functional x4", "specialize beta_sum_functional x5",
                "specialize beta_sum_functional l", "specialize beta_sum_functional p",
                "specialize beta_sum_functional r", "apply beta_sum_functional",
                "exact htransport_positive", "exact hsecond_witness_witness_witness_witness_right_left",
                "specialize beta_sum_functional x6", "specialize beta_sum_functional x7",
                "specialize beta_sum_functional l", "specialize beta_sum_functional n",
                "specialize beta_sum_functional s", "apply beta_sum_functional",
                "exact htransport_negative", "exact hsecond_witness_witness_witness_witness_right_right",
            ),
            "Both components of an arbitrary finite signed alternating Laplace cofactor fold are independent of every beta-coding and finite-sum witness.",
        ),
        spec(
            "signed_alternating_cofactor_fold_exists_unique",
            f"forall {' '.join(source_codes)} l. exists p n. (({fold_result}) /\\ "
            f"forall r s. ({fold_other}) -> (p = r /\\ n = s))",
            ("signed_alternating_cofactor_fold_exists", "signed_alternating_cofactor_fold_functional"),
            (
                *source_intro, "intro l",
                *tuple(f"specialize signed_alternating_cofactor_fold_exists {value}" for value in source_codes),
                "specialize signed_alternating_cofactor_fold_exists l",
                "cases signed_alternating_cofactor_fold_exists",
                "cases signed_alternating_cofactor_fold_exists_witness",
                "exists x", "exists x1", "split",
                "exact signed_alternating_cofactor_fold_exists_witness_witness",
                "intro r", "intro s", "intro hother",
                *tuple(f"specialize signed_alternating_cofactor_fold_functional {value}" for value in source_codes),
                "specialize signed_alternating_cofactor_fold_functional l",
                "specialize signed_alternating_cofactor_fold_functional x",
                "specialize signed_alternating_cofactor_fold_functional x1",
                "specialize signed_alternating_cofactor_fold_functional r",
                "specialize signed_alternating_cofactor_fold_functional s",
                "apply signed_alternating_cofactor_fold_functional",
                "exact signed_alternating_cofactor_fold_exists_witness_witness", "exact hother",
            ),
            "Every arbitrary-length signed row/cofactor pair has exactly one subtraction-free signed alternating Laplace value.",
        ),
        spec(
            "signed_alternating_cofactor_fold_empty",
            f"forall {' '.join(source_codes)} p n. ({fold_empty}) -> (p = 0 /\\ n = 0)",
            ("beta_sum_zero",),
            (
                *source_intro, "intro p", "intro n", "intro hfold",
                *_cases_exists("hfold",4),
                "cases hfold_witness_witness_witness_witness",
                "cases hfold_witness_witness_witness_witness_right", "split",
                "specialize beta_sum_zero x", "specialize beta_sum_zero x1",
                "specialize beta_sum_zero p", "apply beta_sum_zero",
                "exact hfold_witness_witness_witness_witness_right_left",
                "specialize beta_sum_zero x2", "specialize beta_sum_zero x3",
                "specialize beta_sum_zero n", "apply beta_sum_zero",
                "exact hfold_witness_witness_witness_witness_right_right",
            ),
            "The arbitrary signed alternating cofactor fold has the exact empty value (0,0).",
        ),
        spec(
            "signed_matrix_first_row_components_exists",
            "forall pb pc nb nc q. exists ab ac db dc. "
            f"(({_slice_terms('pb','pc','0','1','ab','ac','S q',tag='mce_first_row_positive')}) /\\ "
            f"({_slice_terms('nb','nc','0','1','db','dc','S q',tag='mce_first_row_negative')}))",
            ("beta_affine_matrix_slice_exists",),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro q",
                f"have hpositive : exists ab ac. ({_slice_terms('pb','pc','0','1','ab','ac','S q',tag='mce_have_row_positive')})",
                "specialize beta_affine_matrix_slice_exists pb",
                "specialize beta_affine_matrix_slice_exists pc",
                "specialize beta_affine_matrix_slice_exists 0",
                "specialize beta_affine_matrix_slice_exists 1",
                "specialize beta_affine_matrix_slice_exists (S q)",
                "exact beta_affine_matrix_slice_exists", "cases hpositive", "cases hpositive_witness",
                f"have hnegative : exists db dc. ({_slice_terms('nb','nc','0','1','db','dc','S q',tag='mce_have_row_negative')})",
                "specialize beta_affine_matrix_slice_exists nb",
                "specialize beta_affine_matrix_slice_exists nc",
                "specialize beta_affine_matrix_slice_exists 0",
                "specialize beta_affine_matrix_slice_exists 1",
                "specialize beta_affine_matrix_slice_exists (S q)",
                "exact beta_affine_matrix_slice_exists", "cases hnegative", "cases hnegative_witness",
                "exists x", "exists x1", "exists x2", "exists x3", "split",
                "exact hpositive_witness_witness", "exact hnegative_witness_witness",
            ),
            "Every arbitrary-dimensional signed square matrix has two complete beta-coded first-row natural-component streams.",
        ),
        spec(
            "signed_first_row_cofactor_fold_exists",
            "forall pb pc nb nc q eb ec fb fc. exists p n. "
            f"({first_row})",
            ("signed_matrix_first_row_components_exists", "signed_alternating_cofactor_fold_exists"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro q",
                "intro eb", "intro ec", "intro fb", "intro fc",
                "have hrow : exists ab ac db dc. "
                f"(({_slice_terms('pb','pc','0','1','ab','ac','S q',tag='mce_actual_row_positive')}) /\\ "
                f"({_slice_terms('nb','nc','0','1','db','dc','S q',tag='mce_actual_row_negative')}))",
                "specialize signed_matrix_first_row_components_exists pb",
                "specialize signed_matrix_first_row_components_exists pc",
                "specialize signed_matrix_first_row_components_exists nb",
                "specialize signed_matrix_first_row_components_exists nc",
                "specialize signed_matrix_first_row_components_exists q",
                "exact signed_matrix_first_row_components_exists",
                *_cases_exists("hrow",4), "cases hrow_witness_witness_witness_witness",
                f"have hfold : exists p n. ({_fold_terms('x','x1','x2','x3','eb','ec','fb','fc','S q','p','n',tag='actual_fold')})",
                "specialize signed_alternating_cofactor_fold_exists x",
                "specialize signed_alternating_cofactor_fold_exists x1",
                "specialize signed_alternating_cofactor_fold_exists x2",
                "specialize signed_alternating_cofactor_fold_exists x3",
                "specialize signed_alternating_cofactor_fold_exists eb",
                "specialize signed_alternating_cofactor_fold_exists ec",
                "specialize signed_alternating_cofactor_fold_exists fb",
                "specialize signed_alternating_cofactor_fold_exists fc",
                "specialize signed_alternating_cofactor_fold_exists (S q)",
                "exact signed_alternating_cofactor_fold_exists", "cases hfold", "cases hfold_witness",
                "exists x4", "exists x5", "exists x", "exists x1", "exists x2", "exists x3",
                "split", "exact hrow_witness_witness_witness_witness_left", "split",
                "exact hrow_witness_witness_witness_witness_right",
                "exact hfold_witness_witness",
            ),
            "The ACTUAL decoded first row of every signed square matrix has an exact arbitrary-arity alternating fold against any supplied signed cofactor values.",
        ),
        spec(
            "signed_matrix_cofactor_family_and_fold_exists",
            "forall pb pc nb nc q eb ec fb fc. exists u v p n. "
            f"(({family_full}) /\\ ({first_row}))",
            ("signed_cofactor_minor_family_exists", "signed_first_row_cofactor_fold_exists"),
            (
                "intro pb", "intro pc", "intro nb", "intro nc", "intro q", "intro eb",
                "intro ec", "intro fb", "intro fc",
                f"have hfamily : exists u v. ({family_full})",
                "specialize signed_cofactor_minor_family_exists pb",
                "specialize signed_cofactor_minor_family_exists pc",
                "specialize signed_cofactor_minor_family_exists nb",
                "specialize signed_cofactor_minor_family_exists nc",
                "specialize signed_cofactor_minor_family_exists q",
                "exact signed_cofactor_minor_family_exists", "cases hfamily", "cases hfamily_witness",
                f"have hfold : exists p n. ({first_row})",
                "specialize signed_first_row_cofactor_fold_exists pb",
                "specialize signed_first_row_cofactor_fold_exists pc",
                "specialize signed_first_row_cofactor_fold_exists nb",
                "specialize signed_first_row_cofactor_fold_exists nc",
                "specialize signed_first_row_cofactor_fold_exists q",
                "specialize signed_first_row_cofactor_fold_exists eb",
                "specialize signed_first_row_cofactor_fold_exists ec",
                "specialize signed_first_row_cofactor_fold_exists fb",
                "specialize signed_first_row_cofactor_fold_exists fc",
                "exact signed_first_row_cofactor_fold_exists", "cases hfold", "cases hfold_witness",
                "exists x", "exists x1", "exists x2", "exists x3", "split",
                "exact hfamily_witness_witness", "exact hfold_witness_witness",
            ),
            "Every arbitrary signed square matrix simultaneously has ALL genuine first-row signed minors and the exact alternating fold of its ACTUAL first row against separately supplied signed cofactor values.",
        ),
    )


@dataclass(frozen=True, slots=True)
class CofactorFamilyEntry:
    """One bounded genuine first-row minor and its parity-adjusted summand."""

    column: int
    minor: MatrixMinorCertificate
    minor_determinant: int
    positive: int
    negative: int


@dataclass(frozen=True, slots=True)
class SignedCofactorFamilyCertificate:
    """An executable finite cofactor family, never formal-proof authority."""

    matrix: IntegerMatrix
    entries: tuple[CofactorFamilyEntry, ...]
    positive: int
    negative: int
    value: int


def certify_signed_cofactor_family(
    matrix: IntegerMatrix,
) -> SignedCofactorFamilyCertificate:
    """Cross-check every actual minor against independent determinant evaluation."""

    if type(matrix) is not IntegerMatrix or matrix.height != matrix.width:
        raise MatrixCofactorExpansionError(
            "a complete signed cofactor family requires an exact square matrix"
        )
    if matrix.height == 0:
        raise MatrixCofactorExpansionError(
            "a complete first-row cofactor family requires a nonempty matrix"
        )
    if matrix.height > MAX_COFACTOR_DIMENSION:
        raise MatrixCofactorExpansionError(
            "a cofactor family exceeds its independently bounded dimension"
        )

    try:
        if integer_matrix(matrix.rows) != matrix:
            raise MatrixCofactorExpansionError("the source matrix is not canonical")
        if any(abs(entry) > MAX_COFACTOR_ENTRY for row in matrix.rows for entry in row):
            raise MatrixCofactorExpansionError(
                "a source entry exceeds the bounded cofactor budget"
            )

        entries: list[CofactorFamilyEntry] = []
        positive = negative = 0
        for column, entry in enumerate(matrix.rows[0]):
            minor = certify_matrix_minor(matrix, 0, column)
            if not verify_matrix_minor(minor):
                raise MatrixCofactorExpansionError("an actual cofactor minor failed replay")
            determinant = certify_integer_determinant(minor.minor).value
            signed_term = entry * determinant * (-1 if column % 2 else 1)
            term_positive = max(signed_term, 0)
            term_negative = max(-signed_term, 0)
            entries.append(
                CofactorFamilyEntry(
                    column, minor, determinant, term_positive, term_negative
                )
            )
            positive += term_positive
            negative += term_negative

        independent = certify_integer_determinant(matrix).value
        if positive - negative != independent:
            raise MatrixCofactorExpansionError(
                "complete cofactor fold disagrees with independent permutation evaluation"
            )
        return SignedCofactorFamilyCertificate(
            matrix, tuple(entries), positive, negative, independent
        )
    except (MatrixCertificateError, IndexError, OverflowError, TypeError, ValueError) as error:
        if isinstance(error, MatrixCofactorExpansionError):
            raise
        raise MatrixCofactorExpansionError(
            "the bounded signed cofactor family is malformed"
        ) from error


def verify_signed_cofactor_family(receipt: SignedCofactorFamilyCertificate) -> bool:
    """Reject any forged source minor, parity, determinant, term, or total."""

    if type(receipt) is not SignedCofactorFamilyCertificate:
        return False
    try:
        return receipt == certify_signed_cofactor_family(receipt.matrix)
    except (MatrixCofactorExpansionError, IndexError, OverflowError, TypeError, ValueError):
        return False


__all__ = (
    "CofactorFamilyEntry",
    "MatrixCofactorExpansionError",
    "SignedCofactorFamilyCertificate",
    "certify_signed_cofactor_family",
    "make_matrix_cofactor_expansion_candidate_theorems",
    "matrix_minor_four_code_relation",
    "signed_matrix_minor_record_relation",
    "signed_cofactor_minor_prefix_relation",
    "signed_alternating_cofactor_term_relation",
    "signed_alternating_product_prefix_relation",
    "signed_alternating_cofactor_fold_relation",
    "signed_first_row_cofactor_fold_relation",
    "verify_signed_cofactor_family",
)
