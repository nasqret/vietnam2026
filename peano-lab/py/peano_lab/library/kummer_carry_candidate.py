"""Constructive three-prefix carry encoding for general Kummer's theorem.

Unlike Bertrand's diagonal ``n+n`` proof, arbitrary addition requires separate
quotient prefixes for both addends and their sum.  The relations below are
capture-safe authoring abbreviations expanded into first-order Peano arithmetic;
they add no kernel primitive, enrollment, or checked-use authority.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_b5_order_quotient_candidate import _divrem_term
from .bertrand_central_binom_valuation_candidate import _legendre_sum_term
from .bertrand_choose_foundation_candidate import _choose_relation_term, _lt_term
from .bertrand_legendre_sum_candidate import _power_quotient_prefix_terms, legendre_sum
from .bertrand_power_valuation_candidate import _power_terms, divides, power_valuation
from .fermat_residue_map_candidate import prime
from .finite_fold_surface import all_bits, bit_count, sum_relation
from .finite_sum_theorems import _at, _sum_relation_terms
from .kummer_valuation_candidate import (
    BINOMIAL_LEGENDRE_VALUATION_BALANCE,
    DIVISION_ADD_QUOTIENT_BIT,
)


ADD_QUOTIENT_CARRY_CHOICE = "add_quotient_carry_choice"
ADD_QUOTIENT_CARRY_PREFIX_EXTEND = "add_quotient_carry_prefix_extend"
ADD_QUOTIENT_CARRY_PREFIX_EXISTS = "add_quotient_carry_prefix_exists"
ADD_QUOTIENT_CARRY_PREFIX_ALL_BITS = "add_quotient_carry_prefix_all_bits"
ADD_QUOTIENT_CARRY_PREFIX_RESTRICT = "add_quotient_carry_prefix_restrict"
BETA_SUM_ADD_CARRY_EXACT = "beta_sum_add_carry_exact"
KUMMER_BINOMIAL_CARRY_BIT_COUNT = "kummer_binomial_carry_bit_count"
PRIME_POWER_VALUATION_ZERO_IFF_NOT_DIVIDES = (
    "prime_power_valuation_zero_iff_not_divides"
)
KUMMER_CARRY_FREE_IFF_NOT_DIVIDES = "kummer_carry_free_iff_not_divides"


def _add_carry_choice(left: str, right: str, total: str, bit: str) -> str:
    return (
        f"(({bit} = 0 /\\ {total} = {left} + {right}) \\/ "
        f"({bit} = 1 /\\ {total} = S ({left} + {right})))"
    )


def _add_carry_point(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    total_code: str,
    total_scale: str,
    index: str,
    *,
    tag: str,
) -> str:
    left = _at(left_code, left_scale, index, "q", tag=f"{tag}_left")
    right = _at(right_code, right_scale, index, "s", tag=f"{tag}_right")
    total = _at(total_code, total_scale, index, "Q", tag=f"{tag}_total")
    return (
        f"exists q s Q bit. ({left}) /\\ (({right}) /\\ "
        f"(({total}) /\\ ({_add_carry_choice('q', 's', 'Q', 'bit')})))"
    )


def _add_carry_stored_point(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    total_code: str,
    total_scale: str,
    bit_code: str,
    bit_scale: str,
    index: str,
    *,
    tag: str,
) -> str:
    left = _at(left_code, left_scale, index, "q", tag=f"{tag}_left")
    right = _at(right_code, right_scale, index, "s", tag=f"{tag}_right")
    total = _at(total_code, total_scale, index, "Q", tag=f"{tag}_total")
    stored = _at(bit_code, bit_scale, index, "bit", tag=f"{tag}_bit")
    return (
        f"exists q s Q bit. ({left}) /\\ (({right}) /\\ "
        f"(({total}) /\\ (({stored}) /\\ "
        f"({_add_carry_choice('q', 's', 'Q', 'bit')}))))"
    )


def _add_carry_prefix(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    total_code: str,
    total_scale: str,
    bit_code: str,
    bit_scale: str,
    length: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    index = f"kmc_index_{tag}"
    left_value = f"kmc_left_{tag}"
    right_value = f"kmc_right_{tag}"
    total_value = f"kmc_total_{tag}"
    bit = f"kmc_bit_{tag}"
    generated = (index, left_value, right_value, total_value, bit)
    if len(set(generated)) != len(generated) or set(generated) & set(variables):
        raise ValueError("generated additive carry-prefix binder captures an argument")
    owned = variables + generated
    bound = _lt_term(index, length, tag=f"{tag}_bound", variables=owned)
    left = _at(left_code, left_scale, index, left_value, tag=f"{tag}_left")
    right = _at(right_code, right_scale, index, right_value, tag=f"{tag}_right")
    total = _at(total_code, total_scale, index, total_value, tag=f"{tag}_total")
    stored = _at(bit_code, bit_scale, index, bit, tag=f"{tag}_bit")
    choice = _add_carry_choice(left_value, right_value, total_value, bit)
    return (
        f"forall {index}. ({bound}) -> exists {left_value} {right_value} "
        f"{total_value} {bit}. ({left}) /\\ (({right}) /\\ (({total}) /\\ "
        f"(({stored}) /\\ ({choice}))))"
    )


def _sum_decomposition(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    entry = _at(code, scale, length, "z", tag=f"{tag}_entry")
    prefix = _sum_relation_terms(code, scale, length, "u", tag=f"{tag}_prefix")
    return f"exists z u. ({entry}) /\\ (({prefix}) /\\ {result} = u + z)"


def _bit_count_term(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    length_marker = f"kmc_length_marker_{tag}"
    result_marker = f"kmc_result_marker_{tag}"
    expanded = bit_count(code, scale, length_marker, result_marker, tag=tag)
    if expanded.count(length_marker) != 4 or expanded.count(result_marker) != 2:
        raise AssertionError("unexpected additive BitCount marker occurrence count")
    return expanded.replace(length_marker, f"({length})").replace(
        result_marker, f"({result})"
    )


def _all_bits_term(code: str, scale: str, length: str, *, tag: str) -> str:
    marker = f"kmc_bits_length_marker_{tag}"
    expanded = all_bits(code, scale, marker, tag=tag)
    if expanded.count(marker) != 1:
        raise AssertionError("unexpected additive AllBits marker occurrence count")
    return expanded.replace(marker, f"({length})")


def make_kummer_carry_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered three-prefix additive carry tranche."""

    choice_variables = ("p", "a", "b", "lb", "lc", "rb", "rc", "tb", "tc", "l", "i")
    choice_left = _power_quotient_prefix_terms(
        "p", "a", "lb", "lc", "l", tag="kmcqc_left"
    )
    choice_right = _power_quotient_prefix_terms(
        "p", "b", "rb", "rc", "l", tag="kmcqc_right"
    )
    choice_total = _power_quotient_prefix_terms(
        "p", "a + b", "tb", "tc", "l", tag="kmcqc_total"
    )
    choice_bound = _lt_term("i", "l", tag="kmcqc_bound", variables=choice_variables)
    choice_result = _add_carry_point(
        "lb", "lc", "rb", "rc", "tb", "tc", "i", tag="kmcqc_result"
    )

    def division_data(
        dividend: str,
        code: str,
        scale: str,
        *,
        tag: str,
    ) -> str:
        powered = _power_terms("p", "S i", "P", tag=f"{tag}_power")
        decoded = _at(code, scale, "i", "q", tag=f"{tag}_entry")
        divided = _divrem_term(
            "P",
            dividend,
            "q",
            "r",
            tag=f"{tag}_division",
            variables=choice_variables + ("P", "q", "r"),
        )
        return f"exists P q r. ({powered}) /\\ (({decoded}) /\\ ({divided}))"

    choice_left_data = division_data("a", "lb", "lc", tag="kmcqc_left_data")
    choice_right_data = division_data("b", "rb", "rc", tag="kmcqc_right_data")
    choice_total_data = division_data("a + b", "tb", "tc", tag="kmcqc_total_data")

    prefix_variables = ("lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "l")
    prefix_before = _add_carry_prefix(
        "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "l",
        tag="kmcpe_before", variables=prefix_variables,
    )
    prefix_last = _add_carry_point(
        "lb", "lc", "rb", "rc", "tb", "tc", "l", tag="kmcpe_last"
    )
    prefix_after = _add_carry_prefix(
        "lb", "lc", "rb", "rc", "tb", "tc", "z", "h", "S l",
        tag="kmcpe_after", variables=prefix_variables + ("z", "h"),
    )

    exists_variables = ("p", "a", "b", "lb", "lc", "rb", "rc", "tb", "tc", "l")
    exists_left = _power_quotient_prefix_terms(
        "p", "a", "lb", "lc", "l", tag="kmcpx_left"
    )
    exists_right = _power_quotient_prefix_terms(
        "p", "b", "rb", "rc", "l", tag="kmcpx_right"
    )
    exists_total = _power_quotient_prefix_terms(
        "p", "a + b", "tb", "tc", "l", tag="kmcpx_total"
    )
    exists_result = _add_carry_prefix(
        "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "l",
        tag="kmcpx_result", variables=exists_variables + ("cb", "cc"),
    )

    bits_source = _add_carry_prefix(
        "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "l",
        tag="kmcpab_source", variables=prefix_variables,
    )
    bits_result = all_bits("cb", "cc", "l", tag="kmcpab_result")

    restrict_source = _add_carry_prefix(
        "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "S l",
        tag="kmcpr_source", variables=prefix_variables,
    )
    restrict_result = _add_carry_prefix(
        "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "l",
        tag="kmcpr_result", variables=prefix_variables,
    )

    sum_variables = prefix_variables + ("L", "M", "T", "E")
    sum_left = sum_relation("lb", "lc", "l", "L", tag="kmcsace_left")
    sum_right = sum_relation("rb", "rc", "l", "M", tag="kmcsace_right")
    sum_total = sum_relation("tb", "tc", "l", "T", tag="kmcsace_total")
    sum_carry = _add_carry_prefix(
        "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "l",
        tag="kmcsace_carry", variables=sum_variables,
    )
    sum_count = bit_count("cb", "cc", "l", "E", tag="kmcsace_count")

    exact_variables = ("p", "a", "b", "C", "v")
    exact_prime = prime("p", tag="kmckbc_prime")
    exact_choose = _choose_relation_term(
        "a + b", "a", "C", tag="kmckbc_choose", variables=exact_variables
    )
    exact_valuation = power_valuation("p", "C", "v", tag="kmckbc_valuation")
    exact_left = _power_quotient_prefix_terms(
        "p", "a", "lb", "lc", "a + b", tag="kmckbc_left"
    )
    exact_right = _power_quotient_prefix_terms(
        "p", "b", "rb", "rc", "a + b", tag="kmckbc_right"
    )
    exact_total = _power_quotient_prefix_terms(
        "p", "a + b", "tb", "tc", "a + b", tag="kmckbc_total"
    )
    exact_carries = _add_carry_prefix(
        "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "a + b",
        tag="kmckbc_carries",
        variables=exact_variables + ("lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc"),
    )
    exact_count = _bit_count_term("cb", "cc", "a + b", "v", tag="kmckbc_count")

    return (
        spec(
            ADD_QUOTIENT_CARRY_CHOICE,
            "forall p a b lb lc rb rc tb tc l i. "
            f"({choice_left}) -> ({choice_right}) -> ({choice_total}) -> "
            f"({choice_bound}) -> ({choice_result})",
            ("pow_functional", DIVISION_ADD_QUOTIENT_BIT),
            (
                "intro p", "intro a", "intro b", "intro lb", "intro lc",
                "intro rb", "intro rc", "intro tb", "intro tc", "intro l",
                "intro i", "intro hleft", "intro hright", "intro htotal", "intro hi",
                f"have hleft_data : {choice_left_data}",
                "specialize hleft i", "apply hleft", "exact hi",
                "cases hleft_data", "cases hleft_data_witness",
                "cases hleft_data_witness_witness",
                "cases hleft_data_witness_witness_witness",
                "cases hleft_data_witness_witness_witness_right",
                f"have hright_data : {choice_right_data}",
                "specialize hright i", "apply hright", "exact hi",
                "cases hright_data", "cases hright_data_witness",
                "cases hright_data_witness_witness",
                "cases hright_data_witness_witness_witness",
                "cases hright_data_witness_witness_witness_right",
                f"have htotal_data : {choice_total_data}",
                "specialize htotal i", "apply htotal", "exact hi",
                "cases htotal_data", "cases htotal_data_witness",
                "cases htotal_data_witness_witness",
                "cases htotal_data_witness_witness_witness",
                "cases htotal_data_witness_witness_witness_right",
                "have hright_power : x = x3",
                "specialize pow_functional p", "specialize pow_functional (S i)",
                "specialize pow_functional x", "specialize pow_functional x3",
                "apply pow_functional",
                "exact hleft_data_witness_witness_witness_left",
                "exact hright_data_witness_witness_witness_left",
                "rewrite <- hright_power at hright_data_witness_witness_witness_right_right",
                "rewrite <- hright_power at hright_data_witness_witness_witness_right_right",
                "have htotal_power : x = x6",
                "specialize pow_functional p", "specialize pow_functional (S i)",
                "specialize pow_functional x", "specialize pow_functional x6",
                "apply pow_functional",
                "exact hleft_data_witness_witness_witness_left",
                "exact htotal_data_witness_witness_witness_left",
                "rewrite <- htotal_power at htotal_data_witness_witness_witness_right_right",
                "rewrite <- htotal_power at htotal_data_witness_witness_witness_right_right",
                "have hcarry : x7 = x1 + x4 \\/ x7 = S (x1 + x4)",
                "specialize division_add_quotient_bit x",
                "specialize division_add_quotient_bit a",
                "specialize division_add_quotient_bit b",
                "specialize division_add_quotient_bit x1",
                "specialize division_add_quotient_bit x2",
                "specialize division_add_quotient_bit x4",
                "specialize division_add_quotient_bit x5",
                "specialize division_add_quotient_bit x7",
                "specialize division_add_quotient_bit x8",
                "apply division_add_quotient_bit",
                "exact hleft_data_witness_witness_witness_right_right",
                "exact hright_data_witness_witness_witness_right_right",
                "exact htotal_data_witness_witness_witness_right_right",
                "cases hcarry",
                "exists x1", "exists x4", "exists x7", "exists 0",
                "split", "exact hleft_data_witness_witness_witness_right_left",
                "split", "exact hright_data_witness_witness_witness_right_left",
                "split", "exact htotal_data_witness_witness_witness_right_left",
                "left", "split", "refl", "exact hcarry_left",
                "exists x1", "exists x4", "exists x7", "exists 1",
                "split", "exact hleft_data_witness_witness_witness_right_left",
                "split", "exact hright_data_witness_witness_witness_right_left",
                "split", "exact htotal_data_witness_witness_witness_right_left",
                "right", "split", "refl", "exact hcarry_right",
            ),
            "Three arbitrary power-quotient prefixes admit a constructive pointwise carry bit.",
        ),
        spec(
            ADD_QUOTIENT_CARRY_PREFIX_EXTEND,
            "forall lb lc rb rc tb tc cb cc l. "
            f"({prefix_before}) -> ({prefix_last}) -> exists z h. ({prefix_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (
                "intro lb", "intro lc", "intro rb", "intro rc", "intro tb",
                "intro tc", "intro cb", "intro cc", "intro l", "intro hprefix",
                "intro hlast",
                "cases hlast", "cases hlast_witness", "cases hlast_witness_witness",
                "cases hlast_witness_witness_witness",
                "cases hlast_witness_witness_witness_witness",
                "cases hlast_witness_witness_witness_witness_right",
                "cases hlast_witness_witness_witness_witness_right_right",
                "specialize beta_prefix_extend l", "specialize beta_prefix_extend cb",
                "specialize beta_prefix_extend cc", "specialize beta_prefix_extend x3",
                "cases beta_prefix_extend", "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x4", "exists x5", "intro i", "intro hi",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "have hsplit : i = l \\/ exists z. z + S i = l",
                "apply finite_lt_succ_eq_or_lt", "exact hi", "cases hsplit",
                "rewrite hsplit_left", "rewrite hsplit_left", "rewrite hsplit_left",
                "rewrite hsplit_left", "rewrite hsplit_left", "rewrite hsplit_left",
                "rewrite hsplit_left", "rewrite hsplit_left",
                "exists x", "exists x1", "exists x2", "exists x3",
                "split", "exact hlast_witness_witness_witness_witness_left",
                "split", "exact hlast_witness_witness_witness_witness_right_left",
                "split", "exact hlast_witness_witness_witness_witness_right_right_left",
                "split", "exact beta_prefix_extend_witness_witness_left",
                "exact hlast_witness_witness_witness_witness_right_right_right",
                "have hold : "
                + _add_carry_stored_point(
                    "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "i",
                    tag="kmcpe_old",
                ),
                "specialize hprefix i", "apply hprefix", "exact hsplit_right",
                "cases hold", "cases hold_witness", "cases hold_witness_witness",
                "cases hold_witness_witness_witness",
                "cases hold_witness_witness_witness_witness",
                "cases hold_witness_witness_witness_witness_right",
                "cases hold_witness_witness_witness_witness_right_right",
                "cases hold_witness_witness_witness_witness_right_right_right",
                "exists x6", "exists x7", "exists x8", "exists x9",
                "split", "exact hold_witness_witness_witness_witness_left",
                "split", "exact hold_witness_witness_witness_witness_right_left",
                "split", "exact hold_witness_witness_witness_witness_right_right_left",
                "split",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right x9",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_witness_witness_witness_right_right_right_left",
                "exact hold_witness_witness_witness_witness_right_right_right_right",
            ),
            "A three-prefix additive carry code extends by one selected terminal bit.",
        ),
        spec(
            ADD_QUOTIENT_CARRY_PREFIX_EXISTS,
            "forall p a b lb lc rb rc tb tc l. "
            f"({exists_left}) -> ({exists_right}) -> ({exists_total}) -> "
            f"exists cb cc. ({exists_result})",
            (
                "add_eq_zero_right", "succ_ne_zero", "le_succ", "le_refl",
                ADD_QUOTIENT_CARRY_CHOICE, ADD_QUOTIENT_CARRY_PREFIX_EXTEND,
            ),
            (
                "intro p", "intro a", "intro b", "intro lb", "intro lc",
                "intro rb", "intro rc", "intro tb", "intro tc", "induction l",
                "intro hleft", "intro hright", "intro htotal",
                "exists 0", "exists 0", "intro i", "intro hi", "exfalso",
                "cases hi", "have hzero : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)", "apply add_eq_zero_right",
                "exact hi_witness", "specialize succ_ne_zero i",
                "apply succ_ne_zero", "exact hzero",
                "intro hleft", "intro hright", "intro htotal",
                "have hleft_prefix : "
                + _power_quotient_prefix_terms(
                    "p", "a", "lb", "lc", "l", tag="kmcpx_left_previous"
                ),
                "intro i", "intro hi", "specialize hleft i", "apply hleft",
                "specialize le_succ (S i)", "specialize le_succ l",
                "apply le_succ", "exact hi",
                "have hright_prefix : "
                + _power_quotient_prefix_terms(
                    "p", "b", "rb", "rc", "l", tag="kmcpx_right_previous"
                ),
                "intro i", "intro hi", "specialize hright i", "apply hright",
                "specialize le_succ (S i)", "specialize le_succ l",
                "apply le_succ", "exact hi",
                "have htotal_prefix : "
                + _power_quotient_prefix_terms(
                    "p", "a + b", "tb", "tc", "l", tag="kmcpx_total_previous"
                ),
                "intro i", "intro hi", "specialize htotal i", "apply htotal",
                "specialize le_succ (S i)", "specialize le_succ l",
                "apply le_succ", "exact hi",
                "have hprefix : exists cb cc. "
                + _add_carry_prefix(
                    "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "l",
                    tag="kmcpx_previous", variables=exists_variables + ("cb", "cc"),
                ),
                "apply IH", "exact hleft_prefix", "exact hright_prefix",
                "exact htotal_prefix", "cases hprefix", "cases hprefix_witness",
                "have hlast : "
                + _add_carry_point(
                    "lb", "lc", "rb", "rc", "tb", "tc", "l", tag="kmcpx_last"
                ),
                "specialize add_quotient_carry_choice p",
                "specialize add_quotient_carry_choice a",
                "specialize add_quotient_carry_choice b",
                "specialize add_quotient_carry_choice lb",
                "specialize add_quotient_carry_choice lc",
                "specialize add_quotient_carry_choice rb",
                "specialize add_quotient_carry_choice rc",
                "specialize add_quotient_carry_choice tb",
                "specialize add_quotient_carry_choice tc",
                "specialize add_quotient_carry_choice (S l)",
                "specialize add_quotient_carry_choice l",
                "apply add_quotient_carry_choice", "exact hleft", "exact hright",
                "exact htotal", "specialize le_refl (S l)", "exact le_refl",
                "specialize add_quotient_carry_prefix_extend lb",
                "specialize add_quotient_carry_prefix_extend lc",
                "specialize add_quotient_carry_prefix_extend rb",
                "specialize add_quotient_carry_prefix_extend rc",
                "specialize add_quotient_carry_prefix_extend tb",
                "specialize add_quotient_carry_prefix_extend tc",
                "specialize add_quotient_carry_prefix_extend x",
                "specialize add_quotient_carry_prefix_extend x1",
                "specialize add_quotient_carry_prefix_extend l",
                "apply add_quotient_carry_prefix_extend",
                "exact hprefix_witness_witness", "exact hlast",
            ),
            "Three arbitrary power-quotient prefixes admit a beta-coded additive carry prefix.",
        ),
        spec(
            ADD_QUOTIENT_CARRY_PREFIX_ALL_BITS,
            "forall lb lc rb rc tb tc cb cc l. "
            f"({bits_source}) -> ({bits_result})",
            (),
            (
                "intro lb", "intro lc", "intro rb", "intro rc", "intro tb",
                "intro tc", "intro cb", "intro cc", "intro l", "intro hprefix",
                "intro i", "intro hi",
                "have hpoint : "
                + _add_carry_stored_point(
                    "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "i",
                    tag="kmcpab_point",
                ),
                "specialize hprefix i", "apply hprefix", "exact hi",
                "cases hpoint", "cases hpoint_witness", "cases hpoint_witness_witness",
                "cases hpoint_witness_witness_witness",
                "cases hpoint_witness_witness_witness_witness",
                "cases hpoint_witness_witness_witness_witness_right",
                "cases hpoint_witness_witness_witness_witness_right_right",
                "cases hpoint_witness_witness_witness_witness_right_right_right",
                "exists x3", "split",
                "exact hpoint_witness_witness_witness_witness_right_right_right_left",
                "cases hpoint_witness_witness_witness_witness_right_right_right_right",
                "cases hpoint_witness_witness_witness_witness_right_right_right_right_left",
                "left",
                "exact hpoint_witness_witness_witness_witness_right_right_right_right_left_left",
                "cases hpoint_witness_witness_witness_witness_right_right_right_right_right",
                "right",
                "exact hpoint_witness_witness_witness_witness_right_right_right_right_right_left",
            ),
            "Every value decoded from a general additive carry prefix is zero or one.",
        ),
        spec(
            ADD_QUOTIENT_CARRY_PREFIX_RESTRICT,
            "forall lb lc rb rc tb tc cb cc l. "
            f"({restrict_source}) -> ({restrict_result})",
            ("le_succ",),
            (
                "intro lb", "intro lc", "intro rb", "intro rc", "intro tb",
                "intro tc", "intro cb", "intro cc", "intro l", "intro hprefix",
                "intro i", "intro hi", "specialize hprefix i", "apply hprefix",
                "specialize le_succ (S i)", "specialize le_succ l",
                "apply le_succ", "exact hi",
            ),
            "Dropping the terminal position preserves a three-prefix additive carry code.",
        ),
        spec(
            BETA_SUM_ADD_CARRY_EXACT,
            "forall lb lc rb rc tb tc cb cc l L M T E. "
            f"({sum_left}) -> ({sum_right}) -> ({sum_total}) -> "
            f"({sum_carry}) -> ({sum_count}) -> T = (L + M) + E",
            (
                "beta_sum_zero", "beta_sum_succ_decompose", "bit_count_zero",
                "bit_count_succ_decompose", "beta_at_unique", "le_refl",
                ADD_QUOTIENT_CARRY_PREFIX_RESTRICT, "add_assoc", "add_comm",
                "add_shuffle_middle",
            ),
            (
                "intro lb", "intro lc", "intro rb", "intro rc", "intro tb",
                "intro tc", "intro cb", "intro cc", "induction l",
                "intro L", "intro M", "intro T", "intro E", "intro hleft",
                "intro hright", "intro htotal", "intro hcarry", "intro hcount",
                "have hL : L = 0", "specialize beta_sum_zero lb",
                "specialize beta_sum_zero lc", "specialize beta_sum_zero L",
                "apply beta_sum_zero", "exact hleft",
                "have hM : M = 0", "specialize beta_sum_zero rb",
                "specialize beta_sum_zero rc", "specialize beta_sum_zero M",
                "apply beta_sum_zero", "exact hright",
                "have hT : T = 0", "specialize beta_sum_zero tb",
                "specialize beta_sum_zero tc", "specialize beta_sum_zero T",
                "apply beta_sum_zero", "exact htotal",
                "have hE : E = 0", "specialize bit_count_zero cb",
                "specialize bit_count_zero cc", "specialize bit_count_zero 0",
                "specialize bit_count_zero E", "apply bit_count_zero", "refl",
                "exact hcount", "rewrite hT", "rewrite hL", "rewrite hM",
                "rewrite hE", "simp",
                "intro L", "intro M", "intro T", "intro E", "intro hleft",
                "intro hright", "intro htotal", "intro hcarry", "intro hcount",
                "have hleft_decomp : "
                + _sum_decomposition("lb", "lc", "l", "L", tag="kmcsace_left_decomp"),
                "specialize beta_sum_succ_decompose lb",
                "specialize beta_sum_succ_decompose lc",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose L",
                "apply beta_sum_succ_decompose", "exact hleft",
                "cases hleft_decomp", "cases hleft_decomp_witness",
                "cases hleft_decomp_witness_witness",
                "cases hleft_decomp_witness_witness_right",
                "have hright_decomp : "
                + _sum_decomposition("rb", "rc", "l", "M", tag="kmcsace_right_decomp"),
                "specialize beta_sum_succ_decompose rb",
                "specialize beta_sum_succ_decompose rc",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose M",
                "apply beta_sum_succ_decompose", "exact hright",
                "cases hright_decomp", "cases hright_decomp_witness",
                "cases hright_decomp_witness_witness",
                "cases hright_decomp_witness_witness_right",
                "have htotal_decomp : "
                + _sum_decomposition("tb", "tc", "l", "T", tag="kmcsace_total_decomp"),
                "specialize beta_sum_succ_decompose tb",
                "specialize beta_sum_succ_decompose tc",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose T",
                "apply beta_sum_succ_decompose", "exact htotal",
                "cases htotal_decomp", "cases htotal_decomp_witness",
                "cases htotal_decomp_witness_witness",
                "cases htotal_decomp_witness_witness_right",
                "have hcount_decomp : exists bit z. "
                f"({_at('cb', 'cc', 'l', 'bit', tag='kmcsace_count_last')}) /\\ "
                f"(({bit_count('cb', 'cc', 'l', 'z', tag='kmcsace_count_previous')}) /\\ "
                "((bit = 0 \\/ bit = 1) /\\ E = z + bit))",
                "specialize bit_count_succ_decompose cb",
                "specialize bit_count_succ_decompose cc",
                "specialize bit_count_succ_decompose l",
                "specialize bit_count_succ_decompose (S l)",
                "specialize bit_count_succ_decompose E",
                "apply bit_count_succ_decompose", "refl", "exact hcount",
                "cases hcount_decomp", "cases hcount_decomp_witness",
                "cases hcount_decomp_witness_witness",
                "cases hcount_decomp_witness_witness_right",
                "cases hcount_decomp_witness_witness_right_right",
                "have hterminal : "
                + _add_carry_stored_point(
                    "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "l",
                    tag="kmcsace_terminal",
                ),
                "specialize hcarry l", "apply hcarry",
                "specialize le_refl (S l)", "exact le_refl",
                "cases hterminal", "cases hterminal_witness",
                "cases hterminal_witness_witness",
                "cases hterminal_witness_witness_witness",
                "cases hterminal_witness_witness_witness_witness",
                "cases hterminal_witness_witness_witness_witness_right",
                "cases hterminal_witness_witness_witness_witness_right_right",
                "cases hterminal_witness_witness_witness_witness_right_right_right",
                "have hq : x = x8", "specialize beta_at_unique lb",
                "specialize beta_at_unique lc", "specialize beta_at_unique l",
                "specialize beta_at_unique x", "specialize beta_at_unique x8",
                "apply beta_at_unique", "exact hleft_decomp_witness_witness_left",
                "exact hterminal_witness_witness_witness_witness_left",
                "have hs : x2 = x9", "specialize beta_at_unique rb",
                "specialize beta_at_unique rc", "specialize beta_at_unique l",
                "specialize beta_at_unique x2", "specialize beta_at_unique x9",
                "apply beta_at_unique", "exact hright_decomp_witness_witness_left",
                "exact hterminal_witness_witness_witness_witness_right_left",
                "have hQ : x4 = x10", "specialize beta_at_unique tb",
                "specialize beta_at_unique tc", "specialize beta_at_unique l",
                "specialize beta_at_unique x4", "specialize beta_at_unique x10",
                "apply beta_at_unique", "exact htotal_decomp_witness_witness_left",
                "exact hterminal_witness_witness_witness_witness_right_right_left",
                "have hbit : x6 = x11", "specialize beta_at_unique cb",
                "specialize beta_at_unique cc", "specialize beta_at_unique l",
                "specialize beta_at_unique x6", "specialize beta_at_unique x11",
                "apply beta_at_unique", "exact hcount_decomp_witness_witness_left",
                "exact hterminal_witness_witness_witness_witness_right_right_right_left",
                "rewrite hq at hleft_decomp_witness_witness_right_right",
                "rewrite hs at hright_decomp_witness_witness_right_right",
                "rewrite hQ at htotal_decomp_witness_witness_right_right",
                "rewrite hbit at hcount_decomp_witness_witness_right_right_right",
                "have hprefix : "
                + _add_carry_prefix(
                    "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "l",
                    tag="kmcsace_restricted", variables=sum_variables,
                ),
                "specialize add_quotient_carry_prefix_restrict lb",
                "specialize add_quotient_carry_prefix_restrict lc",
                "specialize add_quotient_carry_prefix_restrict rb",
                "specialize add_quotient_carry_prefix_restrict rc",
                "specialize add_quotient_carry_prefix_restrict tb",
                "specialize add_quotient_carry_prefix_restrict tc",
                "specialize add_quotient_carry_prefix_restrict cb",
                "specialize add_quotient_carry_prefix_restrict cc",
                "specialize add_quotient_carry_prefix_restrict l",
                "apply add_quotient_carry_prefix_restrict", "exact hcarry",
                "have hbalance : x5 = (x1 + x3) + x7",
                "specialize IH x1", "specialize IH x3", "specialize IH x5",
                "specialize IH x7", "apply IH",
                "exact hleft_decomp_witness_witness_right_left",
                "exact hright_decomp_witness_witness_right_left",
                "exact htotal_decomp_witness_witness_right_left",
                "exact hprefix", "exact hcount_decomp_witness_witness_right_left",
                "have hinner : x3 + (x7 + (x8 + (x9 + x1))) = "
                "x8 + (x3 + (x9 + (x7 + x1)))",
                "have hleft_assoc : x3 + (x7 + (x8 + (x9 + x1))) = "
                "(x3 + x7) + (x8 + (x9 + x1))",
                "symm", "apply add_assoc",
                "have hshuffle : (x3 + x7) + (x8 + (x9 + x1)) = "
                "(x3 + x8) + (x7 + (x9 + x1))",
                "apply add_shuffle_middle",
                "have hswap : x7 + (x9 + x1) = x9 + (x7 + x1)",
                "trans (x7 + x9) + x1", "symm", "apply add_assoc",
                "trans (x9 + x7) + x1", "congr", "apply add_comm", "refl",
                "apply add_assoc",
                "have hpermute : (x3 + x8) + (x7 + (x9 + x1)) = "
                "(x8 + x3) + (x9 + (x7 + x1))",
                "congr", "apply add_comm", "exact hswap",
                "have hright_assoc : (x8 + x3) + (x9 + (x7 + x1)) = "
                "x8 + (x3 + (x9 + (x7 + x1)))",
                "apply add_assoc",
                "trans (x3 + x7) + (x8 + (x9 + x1))", "exact hleft_assoc",
                "trans (x3 + x8) + (x7 + (x9 + x1))", "exact hshuffle",
                "trans (x8 + x3) + (x9 + (x7 + x1))", "exact hpermute",
                "exact hright_assoc",
                "cases hterminal_witness_witness_witness_witness_right_right_right_right",
                "cases hterminal_witness_witness_witness_witness_right_right_right_right_left",
                "rewrite htotal_decomp_witness_witness_right_right",
                "rewrite hleft_decomp_witness_witness_right_right",
                "rewrite hright_decomp_witness_witness_right_right",
                "rewrite hcount_decomp_witness_witness_right_right_right",
                "rewrite hbalance",
                "rewrite hterminal_witness_witness_witness_witness_right_right_right_right_left_left",
                "rewrite hterminal_witness_witness_witness_witness_right_right_right_right_left_right",
                "simp [add_assoc, add_comm]",
                "cases hterminal_witness_witness_witness_witness_right_right_right_right_right",
                "rewrite htotal_decomp_witness_witness_right_right",
                "rewrite hleft_decomp_witness_witness_right_right",
                "rewrite hright_decomp_witness_witness_right_right",
                "rewrite hcount_decomp_witness_witness_right_right_right",
                "rewrite hbalance",
                "rewrite hterminal_witness_witness_witness_witness_right_right_right_right_right_left",
                "rewrite hterminal_witness_witness_witness_witness_right_right_right_right_right_right",
                "simp [add_assoc, add_comm]",
            ),
            "The sum-prefix quotient total equals both addend totals plus the exact carry count.",
        ),
        spec(
            KUMMER_BINOMIAL_CARRY_BIT_COUNT,
            "forall p a b C v. "
            f"({exact_prime}) -> ({exact_choose}) -> ({exact_valuation}) -> "
            "exists lb lc rb rc tb tc cb cc. "
            f"({exact_left}) /\\ (({exact_right}) /\\ (({exact_total}) /\\ "
            f"(({exact_carries}) /\\ ({exact_count}))))",
            (
                "prime_legendre_sum_exists",
                BINOMIAL_LEGENDRE_VALUATION_BALANCE,
                "legendre_sum_extended_prefix_exists",
                "add_comm",
                ADD_QUOTIENT_CARRY_PREFIX_EXISTS,
                ADD_QUOTIENT_CARRY_PREFIX_ALL_BITS,
                "bit_count_exists",
                BETA_SUM_ADD_CARRY_EXACT,
                "add_left_cancel",
            ),
            (
                "intro p", "intro a", "intro b", "intro C", "intro v",
                "intro hp", "intro hchoose", "intro hvaluation",
                "have hleft_legendre : exists L. "
                + legendre_sum("p", "a", "L", tag="kmckbc_left_legendre"),
                "specialize prime_legendre_sum_exists p",
                "specialize prime_legendre_sum_exists a",
                "apply prime_legendre_sum_exists", "exact hp",
                "cases hleft_legendre",
                "have hright_legendre : exists M. "
                + legendre_sum("p", "b", "M", tag="kmckbc_right_legendre"),
                "specialize prime_legendre_sum_exists p",
                "specialize prime_legendre_sum_exists b",
                "apply prime_legendre_sum_exists", "exact hp",
                "cases hright_legendre",
                "have htotal_legendre : exists T. "
                + _legendre_sum_term("p", "a + b", "T", tag="kmckbc_total_legendre"),
                "specialize prime_legendre_sum_exists p",
                "specialize prime_legendre_sum_exists (a + b)",
                "apply prime_legendre_sum_exists", "exact hp",
                "cases htotal_legendre",
                "have hvaluation_balance : x2 = (x + x1) + v",
                "specialize binomial_legendre_valuation_balance p",
                "specialize binomial_legendre_valuation_balance a",
                "specialize binomial_legendre_valuation_balance b",
                "specialize binomial_legendre_valuation_balance C",
                "specialize binomial_legendre_valuation_balance v",
                "specialize binomial_legendre_valuation_balance x2",
                "specialize binomial_legendre_valuation_balance x",
                "specialize binomial_legendre_valuation_balance x1",
                "apply binomial_legendre_valuation_balance", "exact hp",
                "exact hchoose", "exact hvaluation", "exact htotal_legendre_witness",
                "exact hleft_legendre_witness", "exact hright_legendre_witness",
                "have hleft_extended : exists lb lc. ("
                + _power_quotient_prefix_terms(
                    "p", "a", "lb", "lc", "a + b", tag="kmckbc_left_extended_prefix"
                )
                + ") /\\ ("
                + _sum_relation_terms(
                    "lb", "lc", "a + b", "x", tag="kmckbc_left_extended_sum"
                )
                + ")",
                "specialize legendre_sum_extended_prefix_exists p",
                "specialize legendre_sum_extended_prefix_exists a",
                "specialize legendre_sum_extended_prefix_exists x",
                "specialize legendre_sum_extended_prefix_exists b",
                "apply legendre_sum_extended_prefix_exists", "exact hp",
                "exact hleft_legendre_witness", "cases hleft_extended",
                "cases hleft_extended_witness", "cases hleft_extended_witness_witness",
                "have hright_extended : exists rb rc. ("
                + _power_quotient_prefix_terms(
                    "p", "b", "rb", "rc", "b + a", tag="kmckbc_right_extended_prefix"
                )
                + ") /\\ ("
                + _sum_relation_terms(
                    "rb", "rc", "b + a", "x1", tag="kmckbc_right_extended_sum"
                )
                + ")",
                "specialize legendre_sum_extended_prefix_exists p",
                "specialize legendre_sum_extended_prefix_exists b",
                "specialize legendre_sum_extended_prefix_exists x1",
                "specialize legendre_sum_extended_prefix_exists a",
                "apply legendre_sum_extended_prefix_exists", "exact hp",
                "exact hright_legendre_witness", "cases hright_extended",
                "cases hright_extended_witness", "cases hright_extended_witness_witness",
                "have hlength : b + a = a + b", "apply add_comm",
                "rewrite hlength at hright_extended_witness_witness_left",
                "rewrite hlength at hright_extended_witness_witness_right",
                "rewrite hlength at hright_extended_witness_witness_right",
                "rewrite hlength at hright_extended_witness_witness_right",
                "cases htotal_legendre_witness",
                "cases htotal_legendre_witness_witness",
                "cases htotal_legendre_witness_witness_witness",
                "have hcarry_codes : exists cb cc. "
                + _add_carry_prefix(
                    "x3", "x4", "x5", "x6", "x7", "x8", "cb", "cc", "a + b",
                    tag="kmckbc_carry_codes",
                    variables=exact_variables
                    + ("x", "x1", "x2", "x3", "x4", "x5", "x6", "x7", "x8", "cb", "cc"),
                ),
                "specialize add_quotient_carry_prefix_exists p",
                "specialize add_quotient_carry_prefix_exists a",
                "specialize add_quotient_carry_prefix_exists b",
                "specialize add_quotient_carry_prefix_exists x3",
                "specialize add_quotient_carry_prefix_exists x4",
                "specialize add_quotient_carry_prefix_exists x5",
                "specialize add_quotient_carry_prefix_exists x6",
                "specialize add_quotient_carry_prefix_exists x7",
                "specialize add_quotient_carry_prefix_exists x8",
                "specialize add_quotient_carry_prefix_exists (a + b)",
                "apply add_quotient_carry_prefix_exists",
                "exact hleft_extended_witness_witness_left",
                "exact hright_extended_witness_witness_left",
                "exact htotal_legendre_witness_witness_witness_left",
                "cases hcarry_codes", "cases hcarry_codes_witness",
                "have hall_bits : "
                + _all_bits_term("x9", "x10", "a + b", tag="kmckbc_all_bits"),
                "specialize add_quotient_carry_prefix_all_bits x3",
                "specialize add_quotient_carry_prefix_all_bits x4",
                "specialize add_quotient_carry_prefix_all_bits x5",
                "specialize add_quotient_carry_prefix_all_bits x6",
                "specialize add_quotient_carry_prefix_all_bits x7",
                "specialize add_quotient_carry_prefix_all_bits x8",
                "specialize add_quotient_carry_prefix_all_bits x9",
                "specialize add_quotient_carry_prefix_all_bits x10",
                "specialize add_quotient_carry_prefix_all_bits (a + b)",
                "apply add_quotient_carry_prefix_all_bits",
                "exact hcarry_codes_witness_witness",
                "have hcount : exists E. "
                + _bit_count_term("x9", "x10", "a + b", "E", tag="kmckbc_count_exists"),
                "specialize bit_count_exists x9", "specialize bit_count_exists x10",
                "specialize bit_count_exists (a + b)", "apply bit_count_exists",
                "exact hall_bits", "cases hcount",
                "have hcarry_balance : x2 = (x + x1) + x11",
                "specialize beta_sum_add_carry_exact x3",
                "specialize beta_sum_add_carry_exact x4",
                "specialize beta_sum_add_carry_exact x5",
                "specialize beta_sum_add_carry_exact x6",
                "specialize beta_sum_add_carry_exact x7",
                "specialize beta_sum_add_carry_exact x8",
                "specialize beta_sum_add_carry_exact x9",
                "specialize beta_sum_add_carry_exact x10",
                "specialize beta_sum_add_carry_exact (a + b)",
                "specialize beta_sum_add_carry_exact x",
                "specialize beta_sum_add_carry_exact x1",
                "specialize beta_sum_add_carry_exact x2",
                "specialize beta_sum_add_carry_exact x11",
                "apply beta_sum_add_carry_exact",
                "exact hleft_extended_witness_witness_right",
                "exact hright_extended_witness_witness_right",
                "exact htotal_legendre_witness_witness_witness_right",
                "exact hcarry_codes_witness_witness", "exact hcount_witness",
                "have hcount_eq : x11 = v",
                "specialize add_left_cancel (x + x1)",
                "specialize add_left_cancel x11", "specialize add_left_cancel v",
                "apply add_left_cancel", "trans x2", "symm",
                "exact hcarry_balance", "exact hvaluation_balance",
                "rewrite hcount_eq at hcount_witness",
                "rewrite hcount_eq at hcount_witness",
                "exists x3", "exists x4", "exists x5", "exists x6",
                "exists x7", "exists x8", "exists x9", "exists x10",
                "split", "exact hleft_extended_witness_witness_left",
                "split", "exact hright_extended_witness_witness_left",
                "split", "exact htotal_legendre_witness_witness_witness_left",
                "split", "exact hcarry_codes_witness_witness", "exact hcount_witness",
            ),
            "Kummer's theorem: the valuation of C(a+b,a) is the number of base-p addition carries.",
        ),
    )


def make_kummer_carry_corollary_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated valuation-zero bridge and carry-free Kummer corollary."""

    bridge_prime = prime("p", tag="kmcvznd_prime")
    bridge_valuation = power_valuation("p", "c", "e", tag="kmcvznd_valuation")
    bridge_divides = divides("p", "c", tag="kmcvznd_divides")

    variables = ("p", "a", "b", "C", "v")
    corollary_prime = prime("p", tag="kmccfnd_prime")
    corollary_choose = _choose_relation_term(
        "a + b", "a", "C", tag="kmccfnd_choose", variables=variables
    )
    corollary_valuation = power_valuation("p", "C", "v", tag="kmccfnd_valuation")
    corollary_divides = divides("p", "C", tag="kmccfnd_divides")
    corollary_left = _power_quotient_prefix_terms(
        "p", "a", "lb", "lc", "a + b", tag="kmccfnd_left"
    )
    corollary_right = _power_quotient_prefix_terms(
        "p", "b", "rb", "rc", "a + b", tag="kmccfnd_right"
    )
    corollary_total = _power_quotient_prefix_terms(
        "p", "a + b", "tb", "tc", "a + b", tag="kmccfnd_total"
    )
    corollary_carries = _add_carry_prefix(
        "lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "a + b",
        tag="kmccfnd_carries",
        variables=variables + ("lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc"),
    )
    corollary_count = _bit_count_term(
        "cb", "cc", "a + b", "v", tag="kmccfnd_count"
    )
    corollary_zero_count = _bit_count_term(
        "cb", "cc", "a + b", "0", tag="kmccfnd_zero_count"
    )

    package = (
        "exists lb lc rb rc tb tc cb cc. "
        f"({corollary_left}) /\\ (({corollary_right}) /\\ (({corollary_total}) /\\ "
        f"(({corollary_carries}) /\\ ({corollary_count}))))"
    )
    package_hypothesis = "hpackage" + "_witness" * 8

    return (
        spec(
            PRIME_POWER_VALUATION_ZERO_IFF_NOT_DIVIDES,
            "forall p c e. "
            f"({bridge_prime}) -> ~(c = 0) -> ({bridge_valuation}) -> "
            f"((e = 0 -> ~({bridge_divides})) /\\ "
            f"(~({bridge_divides}) -> e = 0))",
            (
                "prime_divisor_power_valuation_nonzero",
                "power_valuation_nonzero_exponent_divides_base",
                "eq_decidable",
            ),
            (
                "intro p", "intro c", "intro e", "intro hp", "intro hc",
                "intro hvaluation", "split",
                "intro hzero", "intro hdivides",
                "specialize prime_divisor_power_valuation_nonzero p",
                "specialize prime_divisor_power_valuation_nonzero c",
                "specialize prime_divisor_power_valuation_nonzero e",
                "apply prime_divisor_power_valuation_nonzero", "exact hp",
                "exact hc", "exact hvaluation", "exact hdivides",
                "exact hzero",
                "intro hnotdivides", "specialize eq_decidable e",
                "specialize eq_decidable 0", "cases eq_decidable",
                "exact eq_decidable_left", "exfalso", "apply hnotdivides",
                "specialize power_valuation_nonzero_exponent_divides_base p",
                "specialize power_valuation_nonzero_exponent_divides_base c",
                "specialize power_valuation_nonzero_exponent_divides_base e",
                "apply power_valuation_nonzero_exponent_divides_base",
                "exact hvaluation", "exact eq_decidable_right",
            ),
            "At a prime base and nonzero value, valuation zero is equivalent to nondivisibility.",
        ),
        spec(
            KUMMER_CARRY_FREE_IFF_NOT_DIVIDES,
            "forall p a b C v. "
            f"({corollary_prime}) -> ({corollary_choose}) -> ({corollary_valuation}) -> "
            "exists lb lc rb rc tb tc cb cc. "
            f"({corollary_left}) /\\ (({corollary_right}) /\\ (({corollary_total}) /\\ "
            f"(({corollary_carries}) /\\ (({corollary_count}) /\\ "
            f"((({corollary_zero_count}) -> ~({corollary_divides})) /\\ "
            f"(~({corollary_divides}) -> ({corollary_zero_count})))))))",
            (
                "choose_positive", "add_comm",
                PRIME_POWER_VALUATION_ZERO_IFF_NOT_DIVIDES,
                KUMMER_BINOMIAL_CARRY_BIT_COUNT, "bit_count_functional",
            ),
            (
                "intro p", "intro a", "intro b", "intro C", "intro v",
                "intro hp", "intro hchoose", "intro hvaluation",
                "have hc_nonzero : ~(C = 0)", "intro hzero",
                "have hbound : exists z. z + a = a + b", "exists b",
                "apply add_comm",
                "have hpositive : exists z. C = S z",
                "specialize choose_positive (a + b)",
                "specialize choose_positive a", "specialize choose_positive C",
                "apply choose_positive", "exact hbound", "exact hchoose",
                "cases hpositive", "apply PA1", "trans C", "symm",
                "exact hpositive_witness", "exact hzero",
                f"have hbridge : (v = 0 -> ~({corollary_divides})) /\\ "
                f"(~({corollary_divides}) -> v = 0)",
                "specialize prime_power_valuation_zero_iff_not_divides p",
                "specialize prime_power_valuation_zero_iff_not_divides C",
                "specialize prime_power_valuation_zero_iff_not_divides v",
                "apply prime_power_valuation_zero_iff_not_divides", "exact hp",
                "exact hc_nonzero", "exact hvaluation", "cases hbridge",
                f"have hpackage : {package}",
                "specialize kummer_binomial_carry_bit_count p",
                "specialize kummer_binomial_carry_bit_count a",
                "specialize kummer_binomial_carry_bit_count b",
                "specialize kummer_binomial_carry_bit_count C",
                "specialize kummer_binomial_carry_bit_count v",
                "apply kummer_binomial_carry_bit_count", "exact hp",
                "exact hchoose", "exact hvaluation",
                "cases hpackage", "cases hpackage_witness",
                "cases hpackage_witness_witness",
                "cases hpackage_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness_witness_witness_witness",
                f"cases {package_hypothesis}",
                f"cases {package_hypothesis}_right",
                f"cases {package_hypothesis}_right_right",
                f"cases {package_hypothesis}_right_right_right",
                "exists x", "exists x1", "exists x2", "exists x3",
                "exists x4", "exists x5", "exists x6", "exists x7",
                "split", f"exact {package_hypothesis}_left",
                "split", f"exact {package_hypothesis}_right_left",
                "split", f"exact {package_hypothesis}_right_right_left",
                "split", f"exact {package_hypothesis}_right_right_right_left",
                "split", f"exact {package_hypothesis}_right_right_right_right",
                "split", "intro hzero_count", "intro hdivides", "apply hbridge_left",
                "specialize bit_count_functional x6",
                "specialize bit_count_functional x7",
                "specialize bit_count_functional (a + b)",
                "specialize bit_count_functional v",
                "specialize bit_count_functional 0",
                "apply bit_count_functional",
                f"exact {package_hypothesis}_right_right_right_right",
                "exact hzero_count", "exact hdivides",
                "intro hnotdivides", "have hv_zero : v = 0",
                "apply hbridge_right", "exact hnotdivides",
                f"rewrite hv_zero at {package_hypothesis}_right_right_right_right",
                f"rewrite hv_zero at {package_hypothesis}_right_right_right_right",
                f"exact {package_hypothesis}_right_right_right_right",
            ),
            "A constructed general-Kummer carry prefix has count zero exactly when p does not divide the binomial coefficient.",
        ),
    )


__all__ = [
    "ADD_QUOTIENT_CARRY_CHOICE",
    "ADD_QUOTIENT_CARRY_PREFIX_ALL_BITS",
    "ADD_QUOTIENT_CARRY_PREFIX_EXISTS",
    "ADD_QUOTIENT_CARRY_PREFIX_EXTEND",
    "ADD_QUOTIENT_CARRY_PREFIX_RESTRICT",
    "BETA_SUM_ADD_CARRY_EXACT",
    "KUMMER_BINOMIAL_CARRY_BIT_COUNT",
    "KUMMER_CARRY_FREE_IFF_NOT_DIVIDES",
    "PRIME_POWER_VALUATION_ZERO_IFF_NOT_DIVIDES",
    "make_kummer_carry_corollary_candidate_theorems",
    "make_kummer_carry_candidate_theorems",
]
