"""Sparse binary carries for the Bertrand B5 prime-power bound.

The quotient of ``n+n`` by a positive power is either twice the quotient of
``n`` or its successor.  This isolated factory beta-encodes those binary
carries, identifies their exact count with the central-binomial valuation,
and turns the final nonzero carry into the bound on the complete prime-power
contribution.  All notation expands to first-order Peano arithmetic before
parsing; no theorem is registered by importing this module.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_b5_order_quotient_candidate import _divrem_term
from .bertrand_central_binom_candidate import _central_binom_relation_term
from .bertrand_central_binom_valuation_candidate import (
    _legendre_sum_term,
)
from .bertrand_choose_foundation_candidate import _le_term, _lt_term
from .bertrand_legendre_sum_candidate import (
    _power_quotient_prefix_terms,
    legendre_sum,
)
from .bertrand_power_valuation_candidate import _power_terms, power_valuation
from .fermat_residue_map_candidate import prime
from .finite_fold_surface import all_bits, bit_count, sum_relation
from .finite_sum_theorems import _at, _sum_relation_terms


DOUBLE_QUOTIENT_CARRY_CHOICE = "double_quotient_carry_choice"
DOUBLE_QUOTIENT_CARRY_PREFIX_EXTEND = (
    "double_quotient_carry_prefix_extend"
)
DOUBLE_QUOTIENT_CARRY_PREFIX_EXISTS = (
    "double_quotient_carry_prefix_exists"
)
DOUBLE_QUOTIENT_CARRY_PREFIX_ALL_BITS = (
    "double_quotient_carry_prefix_all_bits"
)
DOUBLE_QUOTIENT_CARRY_PREFIX_RESTRICT = (
    "double_quotient_carry_prefix_restrict"
)
BIT_COUNT_POSITIVE_LAST_ONE = "bit_count_positive_last_one"
DIVISION_SUCCESSOR_QUOTIENT_DIVISOR_LE = (
    "division_successor_quotient_divisor_le"
)
BETA_SUM_DOUBLE_CARRY_EXACT = "beta_sum_double_carry_exact"
CENTRAL_BINOM_CARRY_BIT_COUNT = "central_binom_carry_bit_count"
CENTRAL_BINOM_PRIME_POWER_CONTRIBUTION_LE_DOUBLE = (
    "central_binom_prime_power_contribution_le_double"
)


def _carry_choice(q: str, Q: str, bit: str) -> str:
    return (
        f"(({bit} = 0 /\\ {Q} = {q} + {q}) \\/ "
        f"({bit} = 1 /\\ {Q} = S ({q} + {q})))"
    )


def _bit_count_term(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    length_marker = f"b5cc_length_marker_{tag}"
    result_marker = f"b5cc_count_marker_{tag}"
    expanded = bit_count(
        code, scale, length_marker, result_marker, tag=tag
    )
    if expanded.count(length_marker) != 4:
        raise AssertionError("unexpected BitCount length occurrence count")
    if expanded.count(result_marker) != 2:
        raise AssertionError("unexpected BitCount result occurrence count")
    return expanded.replace(length_marker, f"({length})").replace(
        result_marker, f"({result})"
    )


def _all_bits_term(code: str, scale: str, length: str, *, tag: str) -> str:
    marker = f"b5cc_bits_length_marker_{tag}"
    expanded = all_bits(code, scale, marker, tag=tag)
    if expanded.count(marker) != 1:
        raise AssertionError("unexpected AllBits length occurrence count")
    return expanded.replace(marker, f"({length})")


def _sum_decomposition(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    entry = _at(code, scale, length, "a", tag=f"{tag}_entry")
    prefix = _sum_relation_terms(
        code, scale, length, "r", tag=f"{tag}_prefix"
    )
    return f"exists a r. ({entry}) /\\ (({prefix}) /\\ {result} = r + a)"


def _carry_point(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    index: str,
    *,
    tag: str,
) -> str:
    left = _at(
        left_code,
        left_scale,
        index,
        "q",
        tag=f"{tag}_left",
    )
    right = _at(
        right_code,
        right_scale,
        index,
        "Q",
        tag=f"{tag}_right",
    )
    return (
        f"exists q Q bit. ({left}) /\\ (({right}) /\\ "
        f"({_carry_choice('q', 'Q', 'bit')}))"
    )


def _carry_stored_point(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    bit_code: str,
    bit_scale: str,
    index: str,
    *,
    tag: str,
) -> str:
    left = _at(
        left_code,
        left_scale,
        index,
        "q",
        tag=f"{tag}_left",
    )
    right = _at(
        right_code,
        right_scale,
        index,
        "Q",
        tag=f"{tag}_right",
    )
    decoded = _at(
        bit_code,
        bit_scale,
        index,
        "bit",
        tag=f"{tag}_bit",
    )
    return (
        f"exists q Q bit. ({left}) /\\ (({right}) /\\ "
        f"(({decoded}) /\\ ({_carry_choice('q', 'Q', 'bit')})))"
    )


def _carry_prefix(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    bit_code: str,
    bit_scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    index = f"b5cc_index_{tag}"
    q = f"b5cc_left_{tag}"
    Q = f"b5cc_right_{tag}"
    bit = f"b5cc_bit_{tag}"
    generated = (index, q, Q, bit)
    if set(generated) & set(variables) or len(set(generated)) != 4:
        raise ValueError("generated carry-prefix binder captures an argument")
    owned = variables + generated
    bound = _lt_term(
        index,
        length,
        tag=f"{tag}_bound",
        variables=owned,
    )
    left = _at(
        left_code,
        left_scale,
        index,
        q,
        tag=f"b5cc_{tag}_left",
    )
    right = _at(
        right_code,
        right_scale,
        index,
        Q,
        tag=f"b5cc_{tag}_right",
    )
    decoded = _at(
        bit_code,
        bit_scale,
        index,
        bit,
        tag=f"b5cc_{tag}_bit",
    )
    choice = _carry_choice(q, Q, bit)
    return (
        f"forall {index}. ({bound}) -> exists {q} {Q} {bit}. "
        f"({left}) /\\ (({right}) /\\ (({decoded}) /\\ ({choice})))"
    )


def make_bertrand_central_binom_carry_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered sparse-carry tranche."""

    choice_variables = ("p", "n", "b", "c", "d", "e", "l", "i")
    choice_left = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "l", tag="b5ccqc_left"
    )
    choice_right = _power_quotient_prefix_terms(
        "p", "n + n", "d", "e", "l", tag="b5ccqc_right"
    )
    choice_bound = _lt_term(
        "i", "l", tag="b5ccqc_bound", variables=choice_variables
    )
    choice_result = _carry_point(
        "b", "c", "d", "e", "i", tag="b5ccqc_result"
    )
    choice_left_data = (
        "exists D q r. "
        f"({_power_terms('p', 'S i', 'D', tag='b5ccqc_left_power')}) /\\ "
        f"(({_at('b', 'c', 'i', 'q', tag='b5ccqc_left_entry')}) /\\ ("
        + _divrem_term(
            "D",
            "n",
            "q",
            "r",
            tag="b5ccqc_left_division",
            variables=choice_variables + ("D", "q", "r"),
        )
        + "))"
    )
    choice_right_data = (
        "exists D q r. "
        f"({_power_terms('p', 'S i', 'D', tag='b5ccqc_right_power')}) /\\ "
        f"(({_at('d', 'e', 'i', 'q', tag='b5ccqc_right_entry')}) /\\ ("
        + _divrem_term(
            "D",
            "n + n",
            "q",
            "r",
            tag="b5ccqc_right_division",
            variables=choice_variables + ("D", "q", "r"),
        )
        + "))"
    )

    prefix_variables = ("b", "c", "d", "e", "f", "g", "l")
    prefix_before = _carry_prefix(
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "l",
        tag="b5ccpe_before",
        variables=prefix_variables,
    )
    prefix_last = _carry_point(
        "b", "c", "d", "e", "l", tag="b5ccpe_last"
    )
    prefix_after = _carry_prefix(
        "b",
        "c",
        "d",
        "e",
        "z",
        "h",
        "S l",
        tag="b5ccpe_after",
        variables=prefix_variables + ("z", "h"),
    )

    exists_variables = ("p", "n", "b", "c", "d", "e", "l")
    exists_left = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "l", tag="b5ccpx_left"
    )
    exists_right = _power_quotient_prefix_terms(
        "p", "n + n", "d", "e", "l", tag="b5ccpx_right"
    )
    exists_result = _carry_prefix(
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "l",
        tag="b5ccpx_result",
        variables=exists_variables + ("f", "g"),
    )

    bits_variables = ("b", "c", "d", "e", "f", "g", "l")
    bits_source = _carry_prefix(
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "l",
        tag="b5ccpab_source",
        variables=bits_variables,
    )
    bits_result = all_bits("f", "g", "l", tag="b5ccpab_result")

    restrict_source = _carry_prefix(
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "S l",
        tag="b5ccpr_source",
        variables=bits_variables,
    )
    restrict_result = _carry_prefix(
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "l",
        tag="b5ccpr_result",
        variables=bits_variables,
    )

    last_count = _bit_count_term(
        "b", "c", "l", "S e", tag="b5ccbclo_count"
    )
    last_bound = _lt_term(
        "i",
        "l",
        tag="b5ccbclo_bound",
        variables=("b", "c", "l", "e", "i"),
    )
    last_entry = _at("b", "c", "i", "1", tag="b5ccbclo_entry")
    last_result_bound = _le_term(
        "S e",
        "S i",
        tag="b5ccbclo_result",
        variables=("b", "c", "l", "e", "i"),
    )
    last_previous = (
        "exists i. ("
        + _lt_term(
            "i",
            "l",
            tag="b5ccbclo_previous_bound",
            variables=("b", "c", "l", "e", "i"),
        )
        + ") /\\ (("
        + _at("b", "c", "i", "1", tag="b5ccbclo_previous_entry")
        + ") /\\ ("
        + _le_term(
            "S e",
            "S i",
            tag="b5ccbclo_previous_result",
            variables=("b", "c", "l", "e", "i"),
        )
        + "))"
    )

    divisor_variables = ("d", "n", "q", "r")
    divisor_source = _divrem_term(
        "d",
        "n",
        "S q",
        "r",
        tag="b5ccsqdl_source",
        variables=divisor_variables,
    )
    divisor_result = _le_term(
        "d", "n", tag="b5ccsqdl_result", variables=divisor_variables
    )

    sum_variables = ("b", "c", "d", "e", "f", "g", "l", "B", "A", "E")
    carry_left_sum = sum_relation(
        "b", "c", "l", "B", tag="b5ccsdce_left_sum"
    )
    carry_right_sum = sum_relation(
        "d", "e", "l", "A", tag="b5ccsdce_right_sum"
    )
    carry_semantics = _carry_prefix(
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "l",
        tag="b5ccsdce_prefix",
        variables=sum_variables,
    )
    carry_count = bit_count(
        "f", "g", "l", "E", tag="b5ccsdce_count"
    )

    exact_variables = ("p", "n", "C", "v")
    exact_prime = prime("p", tag="b5cccbbc_prime")
    exact_central = _central_binom_relation_term(
        "n",
        "C",
        tag="b5cccbbc_central",
        variables=exact_variables,
    )
    exact_valuation = power_valuation(
        "p", "C", "v", tag="b5cccbbc_valuation"
    )
    exact_left = _power_quotient_prefix_terms(
        "p", "n", "b", "s", "n + n", tag="b5cccbbc_left"
    )
    exact_right = _power_quotient_prefix_terms(
        "p", "n + n", "d", "t", "n + n", tag="b5cccbbc_right"
    )
    exact_carries = _carry_prefix(
        "b",
        "s",
        "d",
        "t",
        "f",
        "g",
        "n + n",
        tag="b5cccbbc_carries",
        variables=exact_variables + ("b", "s", "d", "t", "f", "g"),
    )
    exact_count = _bit_count_term(
        "f", "g", "n + n", "v", tag="b5cccbbc_count"
    )
    exact_extended = (
        "exists b s. ("
        + _power_quotient_prefix_terms(
            "p",
            "n",
            "b",
            "s",
            "n + n",
            tag="b5cccbbc_extended_prefix",
        )
        + ") /\\ ("
        + _sum_relation_terms(
            "b",
            "s",
            "n + n",
            "x",
            tag="b5cccbbc_extended_sum",
        )
        + ")"
    )

    contribution_variables = ("p", "n", "C", "v", "D")
    contribution_prime = prime("p", tag="b5ccppcld_prime")
    contribution_positive = _le_term(
        "1",
        "n",
        tag="b5ccppcld_positive",
        variables=contribution_variables,
    )
    contribution_central = _central_binom_relation_term(
        "n",
        "C",
        tag="b5ccppcld_central",
        variables=contribution_variables,
    )
    contribution_valuation = power_valuation(
        "p", "C", "v", tag="b5ccppcld_valuation"
    )
    contribution_power = _power_terms(
        "p", "v", "D", tag="b5ccppcld_power"
    )
    contribution_result = _le_term(
        "D",
        "n + n",
        tag="b5ccppcld_result",
        variables=contribution_variables,
    )
    contribution_package = (
        "exists b s d t f g. ("
        + _power_quotient_prefix_terms(
            "p", "n", "b", "s", "n + n", tag="b5ccppcld_left"
        )
        + ") /\\ (("
        + _power_quotient_prefix_terms(
            "p",
            "n + n",
            "d",
            "t",
            "n + n",
            tag="b5ccppcld_right",
        )
        + ") /\\ (("
        + _carry_prefix(
            "b",
            "s",
            "d",
            "t",
            "f",
            "g",
            "n + n",
            tag="b5ccppcld_carries",
            variables=contribution_variables
            + ("b", "s", "d", "t", "f", "g"),
        )
        + ") /\\ ("
        + _bit_count_term(
            "f", "g", "n + n", "S v", tag="b5ccppcld_count"
        )
        + ")))"
    )
    contribution_last = (
        "exists i. ("
        + _lt_term(
            "i",
            "n + n",
            tag="b5ccppcld_last_bound",
            variables=contribution_variables + ("i",),
        )
        + ") /\\ (("
        + _at("x4", "x5", "i", "1", tag="b5ccppcld_last_entry")
        + ") /\\ ("
        + _le_term(
            "S v",
            "S i",
            tag="b5ccppcld_last_result",
            variables=contribution_variables + ("i",),
        )
        + "))"
    )
    contribution_local_variables = contribution_variables + tuple(
        f"x{index}" if index else "x" for index in range(13)
    )
    contribution_right_data = (
        "exists P Q R. ("
        + _power_terms("p", "S x6", "P", tag="b5ccppcld_right_power")
        + ") /\\ (("
        + _at("x2", "x3", "x6", "Q", tag="b5ccppcld_right_entry")
        + ") /\\ ("
        + _divrem_term(
            "P",
            "n + n",
            "Q",
            "R",
            tag="b5ccppcld_right_division",
            variables=contribution_local_variables + ("P", "Q", "R"),
        )
        + "))"
    )
    contribution_divisor_bound = _le_term(
        "x10",
        "n + n",
        tag="b5ccppcld_divisor_bound",
        variables=contribution_local_variables,
    )
    contribution_power_bound = _le_term(
        "D",
        "x10",
        tag="b5ccppcld_power_bound",
        variables=contribution_local_variables,
    )

    return (
        spec(
            DOUBLE_QUOTIENT_CARRY_CHOICE,
            "forall p n b c d e l i. "
            f"({choice_left}) -> ({choice_right}) -> "
            f"({choice_bound}) -> ({choice_result})",
            ("pow_functional", "division_double_quotient_bit"),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro l",
                "intro i",
                "intro hleft",
                "intro hright",
                "intro hi",
                f"have hleft_data : {choice_left_data}",
                "specialize hleft i",
                "apply hleft",
                "exact hi",
                "cases hleft_data",
                "cases hleft_data_witness",
                "cases hleft_data_witness_witness",
                "cases hleft_data_witness_witness_witness",
                "cases hleft_data_witness_witness_witness_right",
                f"have hright_data : {choice_right_data}",
                "specialize hright i",
                "apply hright",
                "exact hi",
                "cases hright_data",
                "cases hright_data_witness",
                "cases hright_data_witness_witness",
                "cases hright_data_witness_witness_witness",
                "cases hright_data_witness_witness_witness_right",
                "have hpower_eq : x = x3",
                "specialize pow_functional p",
                "specialize pow_functional (S i)",
                "specialize pow_functional x",
                "specialize pow_functional x3",
                "apply pow_functional",
                "exact hleft_data_witness_witness_witness_left",
                "exact hright_data_witness_witness_witness_left",
                "rewrite <- hpower_eq at "
                "hright_data_witness_witness_witness_right_right",
                "rewrite <- hpower_eq at "
                "hright_data_witness_witness_witness_right_right",
                "have hcarry : x4 = x1 + x1 \\/ x4 = S (x1 + x1)",
                "specialize division_double_quotient_bit x",
                "specialize division_double_quotient_bit n",
                "specialize division_double_quotient_bit x1",
                "specialize division_double_quotient_bit x2",
                "specialize division_double_quotient_bit x4",
                "specialize division_double_quotient_bit x5",
                "apply division_double_quotient_bit",
                "exact hleft_data_witness_witness_witness_right_right",
                "exact hright_data_witness_witness_witness_right_right",
                "cases hcarry",
                "exists x1",
                "exists x4",
                "exists 0",
                "split",
                "exact hleft_data_witness_witness_witness_right_left",
                "split",
                "exact hright_data_witness_witness_witness_right_left",
                "left",
                "split",
                "refl",
                "exact hcarry_left",
                "exists x1",
                "exists x4",
                "exists 1",
                "split",
                "exact hleft_data_witness_witness_witness_right_left",
                "split",
                "exact hright_data_witness_witness_witness_right_left",
                "right",
                "split",
                "refl",
                "exact hcarry_right",
            ),
            "Each pair of doubled quotients has a constructive carry bit.",
        ),
        spec(
            DOUBLE_QUOTIENT_CARRY_PREFIX_EXTEND,
            "forall b c d e f g l. "
            f"({prefix_before}) -> ({prefix_last}) -> "
            f"exists z h. ({prefix_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "intro g",
                "intro l",
                "intro hprefix",
                "intro hlast",
                "cases hlast",
                "cases hlast_witness",
                "cases hlast_witness_witness",
                "cases hlast_witness_witness_witness",
                "cases hlast_witness_witness_witness_right",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend f",
                "specialize beta_prefix_extend g",
                "specialize beta_prefix_extend x2",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x3",
                "exists x4",
                "intro i",
                "intro hi",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "have hsplit : i = l \\/ exists k. k + S i = l",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "exact hlast_witness_witness_witness_left",
                "split",
                "exact hlast_witness_witness_witness_right_left",
                "split",
                "exact beta_prefix_extend_witness_witness_left",
                "exact hlast_witness_witness_witness_right_right",
                "have hold : "
                + _carry_stored_point(
                    "b",
                    "c",
                    "d",
                    "e",
                    "f",
                    "g",
                    "i",
                    tag="b5ccpe_old",
                ),
                "specialize hprefix i",
                "apply hprefix",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "cases hold_witness_witness",
                "cases hold_witness_witness_witness",
                "cases hold_witness_witness_witness_right",
                "cases hold_witness_witness_witness_right_right",
                "exists x5",
                "exists x6",
                "exists x7",
                "split",
                "exact hold_witness_witness_witness_left",
                "split",
                "exact hold_witness_witness_witness_right_left",
                "split",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right x7",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_witness_witness_right_right_left",
                "exact hold_witness_witness_witness_right_right_right",
            ),
            "A carry prefix extends by one freshly decoded carry bit.",
        ),
        spec(
            DOUBLE_QUOTIENT_CARRY_PREFIX_EXISTS,
            "forall p n b c d e l. "
            f"({exists_left}) -> ({exists_right}) -> "
            f"exists f g. ({exists_result})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "le_succ",
                "le_refl",
                DOUBLE_QUOTIENT_CARRY_CHOICE,
                DOUBLE_QUOTIENT_CARRY_PREFIX_EXTEND,
            ),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "induction l",
                "intro hleft",
                "intro hright",
                "exists 0",
                "exists 0",
                "intro i",
                "intro hi",
                "exfalso",
                "cases hi",
                "have hzero : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hzero",
                "intro hleft",
                "intro hright",
                "have hleft_prefix : "
                + _power_quotient_prefix_terms(
                    "p", "n", "b", "c", "l", tag="b5ccpx_left_prefix"
                ),
                "intro i",
                "intro hi",
                "specialize hleft i",
                "apply hleft",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "have hright_prefix : "
                + _power_quotient_prefix_terms(
                    "p",
                    "n + n",
                    "d",
                    "e",
                    "l",
                    tag="b5ccpx_right_prefix",
                ),
                "intro i",
                "intro hi",
                "specialize hright i",
                "apply hright",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "have hprefix : exists f g. "
                + _carry_prefix(
                    "b",
                    "c",
                    "d",
                    "e",
                    "f",
                    "g",
                    "l",
                    tag="b5ccpx_previous",
                    variables=exists_variables + ("f", "g"),
                ),
                "apply IH",
                "exact hleft_prefix",
                "exact hright_prefix",
                "cases hprefix",
                "cases hprefix_witness",
                "have hlast : "
                + _carry_point(
                    "b", "c", "d", "e", "l", tag="b5ccpx_last"
                ),
                "specialize double_quotient_carry_choice p",
                "specialize double_quotient_carry_choice n",
                "specialize double_quotient_carry_choice b",
                "specialize double_quotient_carry_choice c",
                "specialize double_quotient_carry_choice d",
                "specialize double_quotient_carry_choice e",
                "specialize double_quotient_carry_choice (S l)",
                "specialize double_quotient_carry_choice l",
                "apply double_quotient_carry_choice",
                "exact hleft",
                "exact hright",
                "specialize le_refl (S l)",
                "exact le_refl",
                "specialize double_quotient_carry_prefix_extend b",
                "specialize double_quotient_carry_prefix_extend c",
                "specialize double_quotient_carry_prefix_extend d",
                "specialize double_quotient_carry_prefix_extend e",
                "specialize double_quotient_carry_prefix_extend x",
                "specialize double_quotient_carry_prefix_extend x1",
                "specialize double_quotient_carry_prefix_extend l",
                "apply double_quotient_carry_prefix_extend",
                "exact hprefix_witness_witness",
                "exact hlast",
            ),
            "Doubled quotient prefixes admit a beta-coded carry prefix.",
        ),
        spec(
            DOUBLE_QUOTIENT_CARRY_PREFIX_ALL_BITS,
            "forall b c d e f g l. "
            f"({bits_source}) -> ({bits_result})",
            (),
            (
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "intro g",
                "intro l",
                "intro hprefix",
                "intro i",
                "intro hi",
                "have hpoint : "
                + _carry_stored_point(
                    "b",
                    "c",
                    "d",
                    "e",
                    "f",
                    "g",
                    "i",
                    tag="b5ccpab_point",
                ),
                "specialize hprefix i",
                "apply hprefix",
                "exact hi",
                "cases hpoint",
                "cases hpoint_witness",
                "cases hpoint_witness_witness",
                "cases hpoint_witness_witness_witness",
                "cases hpoint_witness_witness_witness_right",
                "cases hpoint_witness_witness_witness_right_right",
                "exists x2",
                "split",
                "exact hpoint_witness_witness_witness_right_right_left",
                "cases hpoint_witness_witness_witness_right_right_right",
                "cases hpoint_witness_witness_witness_right_right_right_left",
                "left",
                "exact hpoint_witness_witness_witness_right_right_right_left_left",
                "cases hpoint_witness_witness_witness_right_right_right_right",
                "right",
                "exact hpoint_witness_witness_witness_right_right_right_right_left",
            ),
            "Every value in a carry prefix is zero or one.",
        ),
        spec(
            DOUBLE_QUOTIENT_CARRY_PREFIX_RESTRICT,
            "forall b c d e f g l. "
            f"({restrict_source}) -> ({restrict_result})",
            ("le_succ",),
            (
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "intro g",
                "intro l",
                "intro hprefix",
                "intro i",
                "intro hi",
                "specialize hprefix i",
                "apply hprefix",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
            ),
            "Dropping the final position preserves a carry prefix.",
        ),
        spec(
            BIT_COUNT_POSITIVE_LAST_ONE,
            "forall b c l e. "
            f"({last_count}) -> exists i. ({last_bound}) /\\ "
            f"(({last_entry}) /\\ ({last_result_bound}))",
            (
                "bit_count_zero",
                "bit_count_succ_decompose",
                "bit_count_bounded",
                "le_succ",
                "le_refl",
            ),
            (
                "intro b",
                "intro c",
                "induction l",
                "intro e",
                "intro hcount",
                "have himpossible : S e = 0",
                "specialize bit_count_zero b",
                "specialize bit_count_zero c",
                "specialize bit_count_zero 0",
                "specialize bit_count_zero (S e)",
                "apply bit_count_zero",
                "refl",
                "exact hcount",
                "exfalso",
                "apply PA1",
                "exact himpossible",
                "intro e",
                "intro hcount",
                "have hdecomp : exists a r. "
                f"({_at('b', 'c', 'l', 'a', tag='b5ccbclo_last')}) /\\ "
                f"(({bit_count('b', 'c', 'l', 'r', tag='b5ccbclo_prefix')}) /\\ "
                "((a = 0 \\/ a = 1) /\\ S e = r + a))",
                "specialize bit_count_succ_decompose b",
                "specialize bit_count_succ_decompose c",
                "specialize bit_count_succ_decompose l",
                "specialize bit_count_succ_decompose (S l)",
                "specialize bit_count_succ_decompose (S e)",
                "apply bit_count_succ_decompose",
                "refl",
                "exact hcount",
                "cases hdecomp",
                "cases hdecomp_witness",
                "cases hdecomp_witness_witness",
                "cases hdecomp_witness_witness_right",
                "cases hdecomp_witness_witness_right_right",
                "cases hdecomp_witness_witness_right_right_left",
                "have hprefix_value : S e = x1",
                "rewrite hdecomp_witness_witness_right_right_left_left at "
                "hdecomp_witness_witness_right_right_right",
                "rewrite PA3 at hdecomp_witness_witness_right_right_right",
                "exact hdecomp_witness_witness_right_right_right",
                "rewrite <- hprefix_value at hdecomp_witness_witness_right_left",
                "rewrite <- hprefix_value at hdecomp_witness_witness_right_left",
                f"have hprevious : {last_previous}",
                "specialize IH e",
                "apply IH",
                "exact hdecomp_witness_witness_right_left",
                "cases hprevious",
                "cases hprevious_witness",
                "cases hprevious_witness_right",
                "exists x2",
                "split",
                "specialize le_succ (S x2)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hprevious_witness_left",
                "split",
                "exact hprevious_witness_right_left",
                "exact hprevious_witness_right_right",
                "exists l",
                "split",
                "specialize le_refl (S l)",
                "exact le_refl",
                "split",
                "rewrite hdecomp_witness_witness_right_right_left_right at "
                "hdecomp_witness_witness_left",
                "rewrite hdecomp_witness_witness_right_right_left_right at "
                "hdecomp_witness_witness_left",
                "exact hdecomp_witness_witness_left",
                "specialize bit_count_bounded b",
                "specialize bit_count_bounded c",
                "specialize bit_count_bounded (S l)",
                "specialize bit_count_bounded (S e)",
                "apply bit_count_bounded",
                "exact hcount",
            ),
            "A positive bit count has a one at an index at least its count.",
        ),
        spec(
            DIVISION_SUCCESSOR_QUOTIENT_DIVISOR_LE,
            "forall d n q r. "
            f"({divisor_source}) -> ({divisor_result})",
            ("add_assoc", "add_comm"),
            (
                "intro d",
                "intro n",
                "intro q",
                "intro r",
                "intro hdivision",
                "cases hdivision",
                "exists d * q + r",
                "rewrite hdivision_left",
                "rewrite PA6",
                "have hleft_assoc : "
                "(d * q + r) + d = d * q + (r + d)",
                "apply add_assoc",
                "have hright_assoc : "
                "(d * q + d) + r = d * q + (d + r)",
                "apply add_assoc",
                "trans d * q + (r + d)",
                "exact hleft_assoc",
                "trans d * q + (d + r)",
                "congr",
                "refl",
                "apply add_comm",
                "symm",
                "exact hright_assoc",
            ),
            "A division with successor quotient bounds its divisor by the dividend.",
        ),
        spec(
            BETA_SUM_DOUBLE_CARRY_EXACT,
            "forall b c d e f g l B A E. "
            f"({carry_left_sum}) -> ({carry_right_sum}) -> "
            f"({carry_semantics}) -> ({carry_count}) -> "
            "A = (B + B) + E",
            (
                "beta_sum_zero",
                "beta_sum_succ_decompose",
                "bit_count_zero",
                "bit_count_succ_decompose",
                "beta_at_unique",
                "le_refl",
                DOUBLE_QUOTIENT_CARRY_PREFIX_RESTRICT,
                "add_assoc",
                "add_permute_outer",
                "add_comm",
            ),
            (
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "intro g",
                "induction l",
                "intro B",
                "intro A",
                "intro E",
                "intro hleft",
                "intro hright",
                "intro hcarry",
                "intro hcount",
                "have hB : B = 0",
                "specialize beta_sum_zero b",
                "specialize beta_sum_zero c",
                "specialize beta_sum_zero B",
                "apply beta_sum_zero",
                "exact hleft",
                "have hA : A = 0",
                "specialize beta_sum_zero d",
                "specialize beta_sum_zero e",
                "specialize beta_sum_zero A",
                "apply beta_sum_zero",
                "exact hright",
                "have hE : E = 0",
                "specialize bit_count_zero f",
                "specialize bit_count_zero g",
                "specialize bit_count_zero 0",
                "specialize bit_count_zero E",
                "apply bit_count_zero",
                "refl",
                "exact hcount",
                "rewrite hA",
                "rewrite hB",
                "rewrite hB",
                "rewrite hE",
                "simp",
                "intro B",
                "intro A",
                "intro E",
                "intro hleft",
                "intro hright",
                "intro hcarry",
                "intro hcount",
                "have hleft_decomp : "
                + _sum_decomposition(
                    "b", "c", "l", "B", tag="b5ccsdce_left_decomp"
                ),
                "specialize beta_sum_succ_decompose b",
                "specialize beta_sum_succ_decompose c",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose B",
                "apply beta_sum_succ_decompose",
                "exact hleft",
                "cases hleft_decomp",
                "cases hleft_decomp_witness",
                "cases hleft_decomp_witness_witness",
                "cases hleft_decomp_witness_witness_right",
                "have hright_decomp : "
                + _sum_decomposition(
                    "d", "e", "l", "A", tag="b5ccsdce_right_decomp"
                ),
                "specialize beta_sum_succ_decompose d",
                "specialize beta_sum_succ_decompose e",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose A",
                "apply beta_sum_succ_decompose",
                "exact hright",
                "cases hright_decomp",
                "cases hright_decomp_witness",
                "cases hright_decomp_witness_witness",
                "cases hright_decomp_witness_witness_right",
                "have hcount_decomp : exists bit r. "
                f"({_at('f', 'g', 'l', 'bit', tag='b5ccsdce_count_last')}) /\\ "
                f"(({bit_count('f', 'g', 'l', 'r', tag='b5ccsdce_count_prefix')}) /\\ "
                "((bit = 0 \\/ bit = 1) /\\ E = r + bit))",
                "specialize bit_count_succ_decompose f",
                "specialize bit_count_succ_decompose g",
                "specialize bit_count_succ_decompose l",
                "specialize bit_count_succ_decompose (S l)",
                "specialize bit_count_succ_decompose E",
                "apply bit_count_succ_decompose",
                "refl",
                "exact hcount",
                "cases hcount_decomp",
                "cases hcount_decomp_witness",
                "cases hcount_decomp_witness_witness",
                "cases hcount_decomp_witness_witness_right",
                "cases hcount_decomp_witness_witness_right_right",
                "have hterminal : "
                + _carry_stored_point(
                    "b",
                    "c",
                    "d",
                    "e",
                    "f",
                    "g",
                    "l",
                    tag="b5ccsdce_terminal",
                ),
                "specialize hcarry l",
                "apply hcarry",
                "specialize le_refl (S l)",
                "exact le_refl",
                "cases hterminal",
                "cases hterminal_witness",
                "cases hterminal_witness_witness",
                "cases hterminal_witness_witness_witness",
                "cases hterminal_witness_witness_witness_right",
                "cases hterminal_witness_witness_witness_right_right",
                "have hq : x = x6",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique l",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x6",
                "apply beta_at_unique",
                "exact hleft_decomp_witness_witness_left",
                "exact hterminal_witness_witness_witness_left",
                "have hQ : x2 = x7",
                "specialize beta_at_unique d",
                "specialize beta_at_unique e",
                "specialize beta_at_unique l",
                "specialize beta_at_unique x2",
                "specialize beta_at_unique x7",
                "apply beta_at_unique",
                "exact hright_decomp_witness_witness_left",
                "exact hterminal_witness_witness_witness_right_left",
                "have hbit : x4 = x8",
                "specialize beta_at_unique f",
                "specialize beta_at_unique g",
                "specialize beta_at_unique l",
                "specialize beta_at_unique x4",
                "specialize beta_at_unique x8",
                "apply beta_at_unique",
                "exact hcount_decomp_witness_witness_left",
                "exact hterminal_witness_witness_witness_right_right_left",
                "rewrite hq at hleft_decomp_witness_witness_right_right",
                "rewrite hQ at hright_decomp_witness_witness_right_right",
                "rewrite hbit at hcount_decomp_witness_witness_right_right_right",
                "have hprefix : "
                + _carry_prefix(
                    "b",
                    "c",
                    "d",
                    "e",
                    "f",
                    "g",
                    "l",
                    tag="b5ccsdce_restricted",
                    variables=sum_variables,
                ),
                "specialize double_quotient_carry_prefix_restrict b",
                "specialize double_quotient_carry_prefix_restrict c",
                "specialize double_quotient_carry_prefix_restrict d",
                "specialize double_quotient_carry_prefix_restrict e",
                "specialize double_quotient_carry_prefix_restrict f",
                "specialize double_quotient_carry_prefix_restrict g",
                "specialize double_quotient_carry_prefix_restrict l",
                "apply double_quotient_carry_prefix_restrict",
                "exact hcarry",
                "have hbalance : x3 = (x1 + x1) + x5",
                "specialize IH x1",
                "specialize IH x3",
                "specialize IH x5",
                "apply IH",
                "exact hleft_decomp_witness_witness_right_left",
                "exact hright_decomp_witness_witness_right_left",
                "exact hprefix",
                "exact hcount_decomp_witness_witness_right_left",
                "have hinner : "
                "x5 + (x6 + (x6 + x1)) = "
                "x6 + (x6 + (x5 + x1))",
                "have hleft_assoc : "
                "x5 + (x6 + (x6 + x1)) = "
                "(x5 + x6) + (x6 + x1)",
                "symm",
                "apply add_assoc",
                "have hpermute : "
                "(x5 + x6) + (x6 + x1) = "
                "(x6 + x6) + (x5 + x1)",
                "apply add_permute_outer",
                "have hright_assoc : "
                "(x6 + x6) + (x5 + x1) = "
                "x6 + (x6 + (x5 + x1))",
                "apply add_assoc",
                "trans (x5 + x6) + (x6 + x1)",
                "exact hleft_assoc",
                "trans (x6 + x6) + (x5 + x1)",
                "exact hpermute",
                "exact hright_assoc",
                "cases hterminal_witness_witness_witness_right_right_right",
                "cases hterminal_witness_witness_witness_right_right_right_left",
                "rewrite hright_decomp_witness_witness_right_right",
                "rewrite hleft_decomp_witness_witness_right_right",
                "rewrite hleft_decomp_witness_witness_right_right",
                "rewrite hcount_decomp_witness_witness_right_right_right",
                "rewrite hbalance",
                "rewrite hterminal_witness_witness_witness_right_right_right_left_left",
                "rewrite hterminal_witness_witness_witness_right_right_right_"
                "left_right",
                "simp [add_assoc, add_comm]",
                "cases hterminal_witness_witness_witness_right_right_right_right",
                "rewrite hright_decomp_witness_witness_right_right",
                "rewrite hleft_decomp_witness_witness_right_right",
                "rewrite hleft_decomp_witness_witness_right_right",
                "rewrite hcount_decomp_witness_witness_right_right_right",
                "rewrite hbalance",
                "rewrite hterminal_witness_witness_witness_right_right_right_"
                "right_left",
                "rewrite hterminal_witness_witness_witness_right_right_right_"
                "right_right",
                "simp [add_assoc, add_comm]",
            ),
            "The doubled quotient sum is twice the source sum plus its carries.",
        ),
        spec(
            CENTRAL_BINOM_CARRY_BIT_COUNT,
            "forall p n C v. "
            f"({exact_prime}) -> ({exact_central}) -> ({exact_valuation}) -> "
            "exists b s d t f g. "
            f"({exact_left}) /\\ (({exact_right}) /\\ "
            f"(({exact_carries}) /\\ ({exact_count})))",
            (
                "prime_legendre_sum_exists",
                "central_binom_legendre_valuation_balance",
                "legendre_sum_extended_prefix_exists",
                DOUBLE_QUOTIENT_CARRY_PREFIX_EXISTS,
                DOUBLE_QUOTIENT_CARRY_PREFIX_ALL_BITS,
                "bit_count_exists",
                BETA_SUM_DOUBLE_CARRY_EXACT,
                "add_left_cancel",
            ),
            (
                "intro p",
                "intro n",
                "intro C",
                "intro v",
                "intro hp",
                "intro hcentral",
                "intro hvaluation",
                "have hcolumn : exists B. "
                + legendre_sum("p", "n", "B", tag="b5cccbbc_column"),
                "specialize prime_legendre_sum_exists p",
                "specialize prime_legendre_sum_exists n",
                "apply prime_legendre_sum_exists",
                "exact hp",
                "cases hcolumn",
                "have htotal : exists A. "
                + _legendre_sum_term(
                    "p", "n + n", "A", tag="b5cccbbc_total"
                ),
                "specialize prime_legendre_sum_exists p",
                "specialize prime_legendre_sum_exists (n + n)",
                "apply prime_legendre_sum_exists",
                "exact hp",
                "cases htotal",
                "have hbalance : x1 = (x + x) + v",
                "specialize central_binom_legendre_valuation_balance p",
                "specialize central_binom_legendre_valuation_balance n",
                "specialize central_binom_legendre_valuation_balance C",
                "specialize central_binom_legendre_valuation_balance v",
                "specialize central_binom_legendre_valuation_balance x1",
                "specialize central_binom_legendre_valuation_balance x",
                "apply central_binom_legendre_valuation_balance",
                "exact hp",
                "exact hcentral",
                "exact hvaluation",
                "exact htotal_witness",
                "exact hcolumn_witness",
                f"have hextended : {exact_extended}",
                "specialize legendre_sum_extended_prefix_exists p",
                "specialize legendre_sum_extended_prefix_exists n",
                "specialize legendre_sum_extended_prefix_exists x",
                "specialize legendre_sum_extended_prefix_exists n",
                "apply legendre_sum_extended_prefix_exists",
                "exact hp",
                "exact hcolumn_witness",
                "cases hextended",
                "cases hextended_witness",
                "cases hextended_witness_witness",
                "cases htotal_witness",
                "cases htotal_witness_witness",
                "cases htotal_witness_witness_witness",
                "have hcarry_codes : exists f g. "
                + _carry_prefix(
                    "x2",
                    "x3",
                    "x4",
                    "x5",
                    "f",
                    "g",
                    "n + n",
                    tag="b5cccbbc_codes",
                    variables=exact_variables
                    + ("x", "x1", "x2", "x3", "x4", "x5", "f", "g"),
                ),
                "specialize double_quotient_carry_prefix_exists p",
                "specialize double_quotient_carry_prefix_exists n",
                "specialize double_quotient_carry_prefix_exists x2",
                "specialize double_quotient_carry_prefix_exists x3",
                "specialize double_quotient_carry_prefix_exists x4",
                "specialize double_quotient_carry_prefix_exists x5",
                "specialize double_quotient_carry_prefix_exists (n + n)",
                "apply double_quotient_carry_prefix_exists",
                "exact hextended_witness_witness_left",
                "exact htotal_witness_witness_witness_left",
                "cases hcarry_codes",
                "cases hcarry_codes_witness",
                "have hall_bits : "
                + _all_bits_term(
                    "x6", "x7", "n + n", tag="b5cccbbc_bits"
                ),
                "specialize double_quotient_carry_prefix_all_bits x2",
                "specialize double_quotient_carry_prefix_all_bits x3",
                "specialize double_quotient_carry_prefix_all_bits x4",
                "specialize double_quotient_carry_prefix_all_bits x5",
                "specialize double_quotient_carry_prefix_all_bits x6",
                "specialize double_quotient_carry_prefix_all_bits x7",
                "specialize double_quotient_carry_prefix_all_bits (n + n)",
                "apply double_quotient_carry_prefix_all_bits",
                "exact hcarry_codes_witness_witness",
                "have hcount : exists E. "
                + _bit_count_term(
                    "x6", "x7", "n + n", "E", tag="b5cccbbc_count_exists"
                ),
                "specialize bit_count_exists x6",
                "specialize bit_count_exists x7",
                "specialize bit_count_exists (n + n)",
                "apply bit_count_exists",
                "exact hall_bits",
                "cases hcount",
                "have hcarry_balance : x1 = (x + x) + x8",
                "specialize beta_sum_double_carry_exact x2",
                "specialize beta_sum_double_carry_exact x3",
                "specialize beta_sum_double_carry_exact x4",
                "specialize beta_sum_double_carry_exact x5",
                "specialize beta_sum_double_carry_exact x6",
                "specialize beta_sum_double_carry_exact x7",
                "specialize beta_sum_double_carry_exact (n + n)",
                "specialize beta_sum_double_carry_exact x",
                "specialize beta_sum_double_carry_exact x1",
                "specialize beta_sum_double_carry_exact x8",
                "apply beta_sum_double_carry_exact",
                "exact hextended_witness_witness_right",
                "exact htotal_witness_witness_witness_right",
                "exact hcarry_codes_witness_witness",
                "exact hcount_witness",
                "have hcount_eq : x8 = v",
                "specialize add_left_cancel (x + x)",
                "specialize add_left_cancel x8",
                "specialize add_left_cancel v",
                "apply add_left_cancel",
                "trans x1",
                "symm",
                "exact hcarry_balance",
                "exact hbalance",
                "rewrite hcount_eq at hcount_witness",
                "rewrite hcount_eq at hcount_witness",
                "exists x2",
                "exists x3",
                "exists x4",
                "exists x5",
                "exists x6",
                "exists x7",
                "split",
                "exact hextended_witness_witness_left",
                "split",
                "exact htotal_witness_witness_witness_left",
                "split",
                "exact hcarry_codes_witness_witness",
                "exact hcount_witness",
            ),
            "The valuation exponent is exactly the number of doubled-quotient carries.",
        ),
        spec(
            CENTRAL_BINOM_PRIME_POWER_CONTRIBUTION_LE_DOUBLE,
            "forall p n C v D. "
            f"({contribution_prime}) -> ({contribution_positive}) -> "
            f"({contribution_central}) -> ({contribution_valuation}) -> "
            f"({contribution_power}) -> ({contribution_result})",
            (
                "pow_zero",
                "le_add_right",
                "le_trans",
                "prime_nonzero",
                "one_le_of_ne_zero",
                "beta_at_unique",
                "pow_le_pow_of_exponent_le",
                BIT_COUNT_POSITIVE_LAST_ONE,
                DIVISION_SUCCESSOR_QUOTIENT_DIVISOR_LE,
                CENTRAL_BINOM_CARRY_BIT_COUNT,
            ),
            (
                "intro p",
                "intro n",
                "intro C",
                "induction v",
                "intro D",
                "intro hp",
                "intro hpositive",
                "intro hcentral",
                "intro hvaluation",
                "intro hpower",
                "have hD : D = 1",
                "specialize pow_zero p",
                "specialize pow_zero 0",
                "specialize pow_zero D",
                "apply pow_zero",
                "refl",
                "exact hpower",
                "have hn_double : exists h. h + n = n + n",
                "specialize le_add_right n",
                "specialize le_add_right n",
                "exact le_add_right",
                "have hone_double : exists h. h + 1 = n + n",
                "specialize le_trans 1",
                "specialize le_trans n",
                "specialize le_trans (n + n)",
                "apply le_trans",
                "exact hpositive",
                "exact hn_double",
                "rewrite hD",
                "exact hone_double",
                "intro D",
                "intro hp",
                "intro hpositive",
                "intro hcentral",
                "intro hvaluation",
                "intro hpower",
                f"have hpackage : {contribution_package}",
                "specialize central_binom_carry_bit_count p",
                "specialize central_binom_carry_bit_count n",
                "specialize central_binom_carry_bit_count C",
                "specialize central_binom_carry_bit_count (S v)",
                "apply central_binom_carry_bit_count",
                "exact hp",
                "exact hcentral",
                "exact hvaluation",
                "cases hpackage",
                "cases hpackage_witness",
                "cases hpackage_witness_witness",
                "cases hpackage_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness_witness_witness_right",
                "cases hpackage_witness_witness_witness_witness_witness_"
                "witness_right_right",
                f"have hlast : {contribution_last}",
                "specialize bit_count_positive_last_one x4",
                "specialize bit_count_positive_last_one x5",
                "specialize bit_count_positive_last_one (n + n)",
                "specialize bit_count_positive_last_one v",
                "apply bit_count_positive_last_one",
                "exact hpackage_witness_witness_witness_witness_witness_"
                "witness_right_right_right",
                "cases hlast",
                "cases hlast_witness",
                "cases hlast_witness_right",
                "have hsemantic : "
                + _carry_stored_point(
                    "x",
                    "x1",
                    "x2",
                    "x3",
                    "x4",
                    "x5",
                    "x6",
                    tag="b5ccppcld_semantic",
                ),
                "specialize hpackage_witness_witness_witness_witness_witness_"
                "witness_right_right_left x6",
                "apply hpackage_witness_witness_witness_witness_witness_"
                "witness_right_right_left",
                "exact hlast_witness_left",
                "cases hsemantic",
                "cases hsemantic_witness",
                "cases hsemantic_witness_witness",
                "cases hsemantic_witness_witness_witness",
                "cases hsemantic_witness_witness_witness_right",
                "cases hsemantic_witness_witness_witness_right_right",
                "have hbit : x9 = 1",
                "specialize beta_at_unique x4",
                "specialize beta_at_unique x5",
                "specialize beta_at_unique x6",
                "specialize beta_at_unique x9",
                "specialize beta_at_unique 1",
                "apply beta_at_unique",
                "exact hsemantic_witness_witness_witness_right_right_left",
                "exact hlast_witness_right_left",
                "rewrite hbit at hsemantic_witness_witness_witness_right_right_right",
                "rewrite hbit at hsemantic_witness_witness_witness_right_right_right",
                "cases hsemantic_witness_witness_witness_right_right_right",
                "cases hsemantic_witness_witness_witness_right_right_right_left",
                "exfalso",
                "apply PA1",
                "exact hsemantic_witness_witness_witness_right_right_right_left_left",
                "cases hsemantic_witness_witness_witness_right_right_right_right",
                f"have hright_data : {contribution_right_data}",
                "specialize hpackage_witness_witness_witness_witness_witness_"
                "witness_right_left x6",
                "apply hpackage_witness_witness_witness_witness_witness_"
                "witness_right_left",
                "exact hlast_witness_left",
                "cases hright_data",
                "cases hright_data_witness",
                "cases hright_data_witness_witness",
                "cases hright_data_witness_witness_witness",
                "cases hright_data_witness_witness_witness_right",
                "have hQ : x8 = x11",
                "specialize beta_at_unique x2",
                "specialize beta_at_unique x3",
                "specialize beta_at_unique x6",
                "specialize beta_at_unique x8",
                "specialize beta_at_unique x11",
                "apply beta_at_unique",
                "exact hsemantic_witness_witness_witness_right_left",
                "exact hright_data_witness_witness_witness_right_left",
                "have hquotient : x11 = S (x7 + x7)",
                "trans x8",
                "symm",
                "exact hQ",
                "exact hsemantic_witness_witness_witness_right_right_right_right_right",
                "rewrite hquotient at hright_data_witness_witness_witness_right_right",
                f"have hdivisor_bound : {contribution_divisor_bound}",
                "specialize division_successor_quotient_divisor_le x10",
                "specialize division_successor_quotient_divisor_le (n + n)",
                "specialize division_successor_quotient_divisor_le (x7 + x7)",
                "specialize division_successor_quotient_divisor_le x12",
                "apply division_successor_quotient_divisor_le",
                "exact hright_data_witness_witness_witness_right_right",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                "have hp1 : exists k. k + 1 = p",
                "specialize one_le_of_ne_zero p",
                "apply one_le_of_ne_zero",
                "exact hp0",
                f"have hpower_bound : {contribution_power_bound}",
                "specialize pow_le_pow_of_exponent_le p",
                "specialize pow_le_pow_of_exponent_le (S v)",
                "specialize pow_le_pow_of_exponent_le (S x6)",
                "specialize pow_le_pow_of_exponent_le D",
                "specialize pow_le_pow_of_exponent_le x10",
                "apply pow_le_pow_of_exponent_le",
                "exact hp1",
                "exact hlast_witness_right_right",
                "exact hpower",
                "exact hright_data_witness_witness_witness_left",
                "specialize le_trans D",
                "specialize le_trans x10",
                "specialize le_trans (n + n)",
                "apply le_trans",
                "exact hpower_bound",
                "exact hdivisor_bound",
            ),
            "Every complete prime-power contribution is bounded by twice n.",
        ),
    )


__all__ = ["make_bertrand_central_binom_carry_candidate_theorems"]
