"""Exact prefix/suffix splitting for beta-coded finite products.

The two candidates in this module factor a product of length ``l + m`` into
an initial prefix of length ``l`` and a separately coded suffix of length
``m``.  The suffix code is related to the source code only extensionally: its
entry at ``i`` is the source entry at ``l + i``.  The converse row concatenates
two such product witnesses without identifying their raw beta codes.

Every helper below expands to ordinary first-order Peano arithmetic before
parsing.  In particular, ``l + i`` and ``l + m`` are assembled only by the
private hygienic compound-term builders; no Product, BetaAt, list, interval,
function, or fold primitive is added to the parser or kernel.  This factory is
deliberately absent from the public theorem registry.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, product_relation


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(
            character.isalnum() or character in "_'"
            for character in value[1:]
        )
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _binders(
    tag: str,
    avoid: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"fps_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(avoid):
        raise ValueError("generated prefix/suffix binder captures an argument")
    return names


def _beta_at_term(
    code: str,
    scale: str,
    index_term: str,
    value_term: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    height, quotient = _binders(tag, avoid, ("height", "quotient"))
    modulus = f"S ((S ({index_term})) * {scale})"
    return (
        f"((exists {height}. {height} + S ({value_term}) = {modulus}) /\\ "
        f"exists {quotient}. {code} = {quotient} * {modulus} + "
        f"({value_term}))"
    )


def _product_relation_term(
    code: str,
    scale: str,
    length_term: str,
    result_term: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    accumulator, accumulator_scale, index, factor, partial, successor = (
        _binders(
            tag,
            avoid,
            ("accumulator", "scale", "index", "factor", "partial", "successor"),
        )
    )
    bound = _binders(
        f"{tag}_bound",
        avoid
        + (
            accumulator,
            accumulator_scale,
            index,
            factor,
            partial,
            successor,
        ),
        ("gap",),
    )[0]
    local_avoid = avoid + (
        accumulator,
        accumulator_scale,
        index,
        factor,
        partial,
        successor,
        bound,
    )
    start = _beta_at_term(
        accumulator,
        accumulator_scale,
        "0",
        "1",
        tag=f"{tag}_start",
        avoid=local_avoid,
    )
    terminal = _beta_at_term(
        accumulator,
        accumulator_scale,
        length_term,
        result_term,
        tag=f"{tag}_terminal",
        avoid=local_avoid,
    )
    decoded_factor = _beta_at_term(
        code,
        scale,
        index,
        factor,
        tag=f"{tag}_factor",
        avoid=local_avoid,
    )
    decoded_partial = _beta_at_term(
        accumulator,
        accumulator_scale,
        index,
        partial,
        tag=f"{tag}_partial",
        avoid=local_avoid,
    )
    decoded_successor = _beta_at_term(
        accumulator,
        accumulator_scale,
        f"S {index}",
        successor,
        tag=f"{tag}_successor",
        avoid=local_avoid,
    )
    return (
        f"exists {accumulator} {accumulator_scale}. "
        f"(({start}) /\\ (({terminal}) /\\ forall {index}. "
        f"(exists {bound}. {bound} + S {index} = {length_term}) -> "
        f"exists {factor} {partial} {successor}. "
        f"(({decoded_factor}) /\\ (({decoded_partial}) /\\ "
        f"(({decoded_successor}) /\\ "
        f"{successor} = {partial} * {factor})))))"
    )


def _offset_beta_at(
    code: str,
    scale: str,
    offset: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand ``BetaAt(code,scale,offset + index,value)`` hygienically."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (code, "code"),
            (scale, "scale"),
            (offset, "offset"),
            (index, "index"),
            (value, "value"),
        )
    )
    return _beta_at_term(
        code,
        scale,
        f"{offset} + {index}",
        value,
        tag=tag,
        avoid=variables,
    )


def _product_sum_relation(
    code: str,
    scale: str,
    left_length: str,
    right_length: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand ``Product(code,scale,left_length + right_length,result)``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (code, "factor code"),
            (scale, "factor scale"),
            (left_length, "left length"),
            (right_length, "right length"),
            (result, "result"),
        )
    )
    return _product_relation_term(
        code,
        scale,
        f"{left_length} + {right_length}",
        result,
        tag=tag,
        avoid=variables,
    )


def _product_sum_mul_relation(
    code: str,
    scale: str,
    left_length: str,
    right_length: str,
    left_result: str,
    right_result: str,
    *,
    tag: str,
) -> str:
    """Expand the sum-length Product whose result is ``left * right``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (code, "factor code"),
            (scale, "factor scale"),
            (left_length, "left length"),
            (right_length, "right length"),
            (left_result, "left result"),
            (right_result, "right result"),
        )
    )
    return _product_relation_term(
        code,
        scale,
        f"{left_length} + {right_length}",
        f"{left_result} * {right_result}",
        tag=tag,
        avoid=variables,
    )


def _shifted_prefix(
    source_code: str,
    source_scale: str,
    suffix_code: str,
    suffix_scale: str,
    offset: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand one-way source-to-suffix alignment at offset ``l + i``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (source_code, "source code"),
            (source_scale, "source scale"),
            (suffix_code, "suffix code"),
            (suffix_scale, "suffix scale"),
            (offset, "offset"),
            (length, "length"),
        )
    )
    if set(variables) & {"i", "a"}:
        raise ValueError("shifted-prefix binders capture an argument")
    bound = _binders(tag, variables + ("i", "a"), ("bound",))[0]
    avoid = variables + ("i", "a", bound)
    source_entry = _beta_at_term(
        source_code,
        source_scale,
        f"{offset} + i",
        "a",
        tag=f"{tag}_source",
        avoid=avoid,
    )
    suffix_entry = _beta_at_term(
        suffix_code,
        suffix_scale,
        "i",
        "a",
        tag=f"{tag}_suffix",
        avoid=avoid,
    )
    return (
        f"forall i a. (exists {bound}. {bound} + S i = {length}) -> "
        f"({source_entry}) -> ({suffix_entry})"
    )


def make_finite_product_prefix_suffix_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the frozen split row followed by its thin concat converse."""

    split_shift = _shifted_prefix(
        "b", "c", "z", "d", "l", "m", tag="bps_split_shift"
    )
    split_total = _product_sum_relation(
        "b", "c", "l", "m", "n", tag="bps_split_total"
    )
    split_prefix = product_relation(
        "b", "c", "l", "p", tag="bps_split_prefix"
    )
    split_suffix = product_relation(
        "z", "d", "m", "q", tag="bps_split_suffix"
    )
    split_statement = (
        "forall b c z d l m n. "
        f"({split_shift}) -> ({split_total}) -> exists p q. "
        f"({split_prefix}) /\\ (({split_suffix}) /\\ n = p * q)"
    )

    concat_shift = _shifted_prefix(
        "b", "c", "z", "d", "l", "m", tag="bps_concat_shift"
    )
    concat_prefix = product_relation(
        "b", "c", "l", "p", tag="bps_concat_prefix"
    )
    concat_suffix = product_relation(
        "z", "d", "m", "q", tag="bps_concat_suffix"
    )
    concat_total = _product_sum_mul_relation(
        "b", "c", "l", "m", "p", "q", tag="bps_concat_total"
    )
    concat_statement = (
        "forall b c z d l m p q. "
        f"({concat_shift}) -> ({concat_prefix}) -> ({concat_suffix}) -> "
        f"({concat_total})"
    )

    previous_total = _product_sum_relation(
        "b", "c", "l", "m", "r", tag="bps_split_previous_total"
    )
    total_decomposition = (
        "exists a r. "
        f"({_offset_beta_at('b', 'c', 'l', 'm', 'a', tag='bps_split_last')}) "
        f"/\\ (({previous_total}) "
        "/\\ n = r * a)"
    )
    prefix_shift = _shifted_prefix(
        "b", "c", "z", "d", "l", "m", tag="bps_split_previous_shift"
    )
    recursive_prefix = product_relation(
        "b", "c", "l", "p", tag="bps_split_recursive_prefix"
    )
    recursive_suffix = product_relation(
        "z", "d", "m", "q", tag="bps_split_recursive_suffix"
    )
    recursive_result = (
        "exists p q. "
        f"({recursive_prefix}) /\\ (({recursive_suffix}) "
        "/\\ x1 = p * q)"
    )
    suffix_last = beta_at(
        "z", "d", "m", "x", tag="bps_split_suffix_last"
    )
    concat_total_exists = (
        "exists n. "
        f"({_product_sum_relation('b', 'c', 'l', 'm', 'n', tag='bps_concat_exists')})"
    )
    concat_split_prefix = product_relation(
        "b", "c", "l", "p0", tag="bps_concat_split_prefix"
    )
    concat_split_suffix = product_relation(
        "z", "d", "m", "q0", tag="bps_concat_split_suffix"
    )
    concat_split_result = (
        "exists p0 q0. "
        f"({concat_split_prefix}) /\\ (({concat_split_suffix}) "
        "/\\ x = p0 * q0)"
    )

    return (
        spec(
            "beta_product_prefix_suffix_split",
            split_statement,
            (
                "beta_product_exists",
                "beta_product_zero",
                "beta_product_succ_decompose",
                "beta_product_succ_append",
                "le_succ",
                "le_refl",
                "mul_one",
                "mul_assoc",
            ),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro l",
                "induction m",
                "intro n",
                "intro hshift",
                "intro htotal",
                "specialize beta_product_exists z",
                "specialize beta_product_exists d",
                "specialize beta_product_exists 0",
                "cases beta_product_exists",
                "cases beta_product_exists_witness",
                "cases beta_product_exists_witness_witness",
                "have hqone : x = 1",
                "specialize beta_product_zero z",
                "specialize beta_product_zero d",
                "specialize beta_product_zero x",
                "apply beta_product_zero",
                "exists x1",
                "exists x2",
                "exact beta_product_exists_witness_witness_witness",
                "exists n",
                "exists x",
                "split",
                "have hbase : l + 0 = l",
                "apply PA3",
                "rewrite hbase at htotal",
                "rewrite hbase at htotal",
                "rewrite hbase at htotal",
                "exact htotal",
                "split",
                "exists x1",
                "exists x2",
                "exact beta_product_exists_witness_witness_witness",
                "rewrite hqone",
                "specialize mul_one n",
                "symm",
                "exact mul_one",
                "intro n",
                "intro hshift",
                "intro htotal",
                "have hlength : l + S m = S (l + m)",
                "apply PA4",
                "rewrite hlength at htotal",
                "rewrite hlength at htotal",
                "rewrite hlength at htotal",
                f"have hdecomposition : {total_decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose (l + m)",
                "specialize beta_product_succ_decompose n",
                "apply beta_product_succ_decompose",
                "exact htotal",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_right",
                f"have hprefix_shift : {prefix_shift}",
                "intro i",
                "intro a",
                "intro hi",
                "intro ha",
                "specialize hshift i",
                "specialize hshift a",
                "apply hshift",
                "specialize le_succ (S i)",
                "specialize le_succ m",
                "apply le_succ",
                "exact hi",
                "exact ha",
                f"have hrecursive : {recursive_result}",
                "specialize IH x1",
                "apply IH",
                "exact hprefix_shift",
                "exact hdecomposition_witness_witness_right_left",
                "cases hrecursive",
                "cases hrecursive_witness",
                "cases hrecursive_witness_witness",
                "cases hrecursive_witness_witness_right",
                f"have hsuffix_last : {suffix_last}",
                "specialize hshift m",
                "specialize hshift x",
                "apply hshift",
                "specialize le_refl (S m)",
                "exact le_refl",
                "exact hdecomposition_witness_witness_left",
                "exists x2",
                "exists x3 * x",
                "split",
                "exact hrecursive_witness_witness_left",
                "split",
                "specialize beta_product_succ_append z",
                "specialize beta_product_succ_append d",
                "specialize beta_product_succ_append m",
                "specialize beta_product_succ_append x3",
                "specialize beta_product_succ_append x",
                "apply beta_product_succ_append",
                "exact hrecursive_witness_witness_right_left",
                "exact hsuffix_last",
                "rewrite hdecomposition_witness_witness_right_right",
                "rewrite hrecursive_witness_witness_right_right",
                "specialize mul_assoc x2",
                "specialize mul_assoc x3",
                "specialize mul_assoc x",
                "exact mul_assoc",
            ),
            "Split a finite Product into an initial prefix and an aligned suffix.",
        ),
        spec(
            "beta_product_prefix_suffix_concat",
            concat_statement,
            (
                "beta_product_exists",
                "beta_product_functional",
                "beta_product_prefix_suffix_split",
            ),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro l",
                "intro m",
                "intro p",
                "intro q",
                "intro hshift",
                "intro hprefix",
                "intro hsuffix",
                f"have htotal_exists : {concat_total_exists}",
                "specialize beta_product_exists b",
                "specialize beta_product_exists c",
                "specialize beta_product_exists (l + m)",
                "exact beta_product_exists",
                "cases htotal_exists",
                f"have hsplit : {concat_split_result}",
                "specialize beta_product_prefix_suffix_split b",
                "specialize beta_product_prefix_suffix_split c",
                "specialize beta_product_prefix_suffix_split z",
                "specialize beta_product_prefix_suffix_split d",
                "specialize beta_product_prefix_suffix_split l",
                "specialize beta_product_prefix_suffix_split m",
                "specialize beta_product_prefix_suffix_split x",
                "apply beta_product_prefix_suffix_split",
                "exact hshift",
                "exact htotal_exists_witness",
                "cases hsplit",
                "cases hsplit_witness",
                "cases hsplit_witness_witness",
                "cases hsplit_witness_witness_right",
                "cases hsplit_witness_witness_left",
                "cases hsplit_witness_witness_left_witness",
                "cases hprefix",
                "cases hprefix_witness",
                "have hp_equal : x1 = p",
                "specialize beta_product_functional b",
                "specialize beta_product_functional c",
                "specialize beta_product_functional l",
                "specialize beta_product_functional x1",
                "specialize beta_product_functional x3",
                "specialize beta_product_functional x4",
                "specialize beta_product_functional p",
                "specialize beta_product_functional x5",
                "specialize beta_product_functional x6",
                "apply beta_product_functional",
                "exact hsplit_witness_witness_left_witness_witness",
                "exact hprefix_witness_witness",
                "cases hsplit_witness_witness_right_left",
                "cases hsplit_witness_witness_right_left_witness",
                "cases hsuffix",
                "cases hsuffix_witness",
                "have hq_equal : x2 = q",
                "specialize beta_product_functional z",
                "specialize beta_product_functional d",
                "specialize beta_product_functional m",
                "specialize beta_product_functional x2",
                "specialize beta_product_functional x7",
                "specialize beta_product_functional x8",
                "specialize beta_product_functional q",
                "specialize beta_product_functional x9",
                "specialize beta_product_functional x10",
                "apply beta_product_functional",
                "exact hsplit_witness_witness_right_left_witness_witness",
                "exact hsuffix_witness_witness",
                "have hresult : x = p * q",
                "trans x1 * x2",
                "exact hsplit_witness_witness_right_right",
                "rewrite hp_equal",
                "rewrite hq_equal",
                "refl",
                "rewrite <- hresult",
                "rewrite <- hresult",
                "exact htotal_exists_witness",
            ),
            "Concatenate aligned prefix and suffix Product witnesses exactly.",
        ),
    )


__all__ = ["make_finite_product_prefix_suffix_candidate_theorems"]
