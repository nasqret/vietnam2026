"""Exact relational-power bridges for the Bertrand B6 base window.

This isolated candidate factory closes the deliberately postponed bridge from
the scalar bound ``s + 7 <= 128`` to the power guard.  The constants are not
evaluated by Python and ``Pow`` is not added to the kernel: every occurrence is
expanded to the existing beta-coded finite-product relation before parsing.

The key identity is proved structurally through a common relational power::

    128^12 = (2^7)^12 = 2^84 = (2^2)^42 = 4^42.

Only small numeral equalities are discharged by ``norm_num``; the powers
themselves are witnessed and compared through ``pow_successor_pair_mul``,
``pow_mul_exp``, and the kernel-checked relational power graph.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_quotient_budget_candidate import witness_le
from .finite_fold_surface import power_relation
from .power_algebra_theorems import _power_terms


def make_bertrand_power_bridge_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact-power and six-residue guard bridge tranche."""

    predecessor = power_relation("a", "e", "r", tag="bpb_predecessor")
    successor = _power_terms("a", "S e", "n", tag="bpb_successor")
    successor_witness = _power_terms(
        "a", "S e", "x", tag="bpb_successor_witness"
    )

    two_two = _power_terms("2", "2", "4", tag="bpb_two_two")
    two_two_witness = _power_terms(
        "2", "2", "x", tag="bpb_two_two_witness"
    )

    two_three = _power_terms("2", "3", "8", tag="bpb_two_three")
    two_four = _power_terms("2", "4", "16", tag="bpb_two_four")
    two_five = _power_terms("2", "5", "32", tag="bpb_two_five")
    two_six = _power_terms("2", "6", "64", tag="bpb_two_six")
    two_seven = _power_terms("2", "7", "128", tag="bpb_two_seven")

    two_eighty_four = _power_terms(
        "2", "7 * 12", "z", tag="bpb_two_eighty_four"
    )
    one_twenty_eight_twelve = _power_terms(
        "128", "12", "x", tag="bpb_one_twenty_eight_twelve"
    )
    four_forty_two = _power_terms(
        "4", "42", "y", tag="bpb_four_forty_two"
    )

    residue_lower = witness_le("64", "s", tag="bpb_residue_lower")
    residue_upper = witness_le("s", "69", tag="bpb_residue_upper")
    guard_left = _power_terms(
        "s + 7", "12", "x", tag="bpb_guard_left"
    )
    guard_right = _power_terms(
        "4", "s + 5", "y", tag="bpb_guard_right"
    )
    guard_result = witness_le("x", "y", tag="bpb_guard_result")
    guard_linear = (
        f"({witness_le('s + 1', '128', tag='bpb_linear_successor')}) /\\ "
        f"(({witness_le('s + 7', '128', tag='bpb_linear_guard')}) /\\ "
        f"({witness_le('42', 's + 5', tag='bpb_linear_exponent')}))"
    )
    upper_power = _power_terms(
        "128", "12", "z", tag="bpb_guard_upper_power"
    )
    common_power = _power_terms(
        "4", "42", "w", tag="bpb_guard_common_power"
    )

    return (
        spec(
            "pow_successor_compose",
            f"forall a e r n. ({predecessor}) -> n = r * a -> ({successor})",
            ("pow_exists", "pow_successor_pair_mul"),
            (
                "intro a",
                "intro e",
                "intro r",
                "intro n",
                "intro hprevious",
                "intro hn",
                f"have hsuccessor : exists x. ({successor_witness})",
                "specialize pow_exists a",
                "specialize pow_exists (S e)",
                "exact pow_exists",
                "cases hsuccessor",
                "have hx : x = r * a",
                "specialize pow_successor_pair_mul a",
                "specialize pow_successor_pair_mul e",
                "specialize pow_successor_pair_mul (S e)",
                "specialize pow_successor_pair_mul r",
                "specialize pow_successor_pair_mul x",
                "apply pow_successor_pair_mul",
                "refl",
                "exact hprevious",
                "exact hsuccessor_witness",
                "have hxn : x = n",
                "trans r * a",
                "exact hx",
                "symm",
                "exact hn",
                "rewrite <- hxn",
                "rewrite <- hxn",
                "exact hsuccessor_witness",
            ),
            "A checked predecessor power composes with one multiplication step.",
        ),
        spec(
            "pow_two_two_exact",
            two_two,
            ("pow_exists", "pow_two_base_two_value_four"),
            (
                f"have hexists : exists x. ({two_two_witness})",
                "specialize pow_exists 2",
                "specialize pow_exists 2",
                "exact pow_exists",
                "cases hexists",
                "have hx : x = 4",
                "specialize pow_two_base_two_value_four x",
                "apply pow_two_base_two_value_four",
                "exact hexists_witness",
                "rewrite hx at hexists_witness",
                "rewrite hx at hexists_witness",
                "exact hexists_witness",
            ),
            "The fully witnessed beta-coded relational fact 2^2 = 4.",
        ),
        spec(
            "pow_two_seven_exact",
            two_seven,
            ("pow_successor_compose", "pow_two_two_exact"),
            (
                f"have hthree : {two_three}",
                "specialize pow_successor_compose 2",
                "specialize pow_successor_compose 2",
                "specialize pow_successor_compose 4",
                "specialize pow_successor_compose 8",
                "apply pow_successor_compose",
                "exact pow_two_two_exact",
                "norm_num",
                f"have hfour : {two_four}",
                "specialize pow_successor_compose 2",
                "specialize pow_successor_compose 3",
                "specialize pow_successor_compose 8",
                "specialize pow_successor_compose 16",
                "apply pow_successor_compose",
                "exact hthree",
                "norm_num",
                f"have hfive : {two_five}",
                "specialize pow_successor_compose 2",
                "specialize pow_successor_compose 4",
                "specialize pow_successor_compose 16",
                "specialize pow_successor_compose 32",
                "apply pow_successor_compose",
                "exact hfour",
                "norm_num",
                f"have hsix : {two_six}",
                "specialize pow_successor_compose 2",
                "specialize pow_successor_compose 5",
                "specialize pow_successor_compose 32",
                "specialize pow_successor_compose 64",
                "apply pow_successor_compose",
                "exact hfive",
                "symm",
                "rewrite PA6",
                "rewrite PA6",
                "rewrite PA5",
                *("rewrite PA4",) * 32,
                "rewrite PA3",
                *("rewrite PA4",) * 32,
                "rewrite PA3",
                "refl",
                "specialize pow_successor_compose 2",
                "specialize pow_successor_compose 6",
                "specialize pow_successor_compose 64",
                "specialize pow_successor_compose 128",
                "apply pow_successor_compose",
                "exact hsix",
                "symm",
                "rewrite PA6",
                "rewrite PA6",
                "rewrite PA5",
                *("rewrite PA4",) * 64,
                "rewrite PA3",
                *("rewrite PA4",) * 64,
                "rewrite PA3",
                "refl",
            ),
            "The fully witnessed beta-coded relational fact 2^7 = 128.",
        ),
        spec(
            "pow_one_twenty_eight_twelve_eq_pow_four_forty_two",
            f"forall x y. ({one_twenty_eight_twelve}) -> "
            f"({four_forty_two}) -> x = y",
            (
                "pow_exists",
                "pow_two_two_exact",
                "pow_two_seven_exact",
                "pow_mul_exp",
            ),
            (
                "intro x",
                "intro y",
                "intro hx",
                "intro hy",
                f"have hcommon : exists z. ({two_eighty_four})",
                "specialize pow_exists 2",
                "specialize pow_exists (7 * 12)",
                "exact pow_exists",
                "cases hcommon",
                "have hleft : x = x1",
                "specialize pow_mul_exp 2",
                "specialize pow_mul_exp 7",
                "specialize pow_mul_exp 12",
                "specialize pow_mul_exp (7 * 12)",
                "specialize pow_mul_exp 128",
                "specialize pow_mul_exp x",
                "specialize pow_mul_exp x1",
                "apply pow_mul_exp",
                "refl",
                "exact pow_two_seven_exact",
                "exact hx",
                "exact hcommon_witness",
                "have hright : y = x1",
                "specialize pow_mul_exp 2",
                "specialize pow_mul_exp 2",
                "specialize pow_mul_exp 42",
                "specialize pow_mul_exp (7 * 12)",
                "specialize pow_mul_exp 4",
                "specialize pow_mul_exp y",
                "specialize pow_mul_exp x1",
                "apply pow_mul_exp",
                "norm_num",
                "exact pow_two_two_exact",
                "exact hy",
                "exact hcommon_witness",
                "trans x1",
                "exact hleft",
                "symm",
                "exact hright",
            ),
            "The exact identity 128^12 = 4^42 through the common power 2^84.",
        ),
        spec(
            "bertrand_guard_base_residue",
            "forall s x y. "
            f"({residue_lower}) -> ({residue_upper}) -> "
            f"({guard_left}) -> ({guard_right}) -> ({guard_result})",
            (
                "bertrand_base_residue_linear_bounds",
                "pow_exists",
                "pow_base_monotone",
                "pow_one_twenty_eight_twelve_eq_pow_four_forty_two",
                "pow_exponent_monotone",
                "le_trans",
                "zero_add",
            ),
            (
                "intro s",
                "intro x",
                "intro y",
                "intro hlower",
                "intro hupper",
                "intro hx",
                "intro hy",
                f"have hlinear : {guard_linear}",
                "specialize bertrand_base_residue_linear_bounds s",
                "apply bertrand_base_residue_linear_bounds",
                "exact hlower",
                "exact hupper",
                "cases hlinear",
                "cases hlinear_right",
                f"have hupperpower : exists z. ({upper_power})",
                "specialize pow_exists 128",
                "specialize pow_exists 12",
                "exact pow_exists",
                "cases hupperpower",
                "have hxupper : exists k. k + x = x1",
                "specialize pow_base_monotone (s + 7)",
                "specialize pow_base_monotone 128",
                "specialize pow_base_monotone 12",
                "specialize pow_base_monotone x",
                "specialize pow_base_monotone x1",
                "apply pow_base_monotone",
                "exact hlinear_right_left",
                "exact hx",
                "exact hupperpower_witness",
                f"have hcommon : exists w. ({common_power})",
                "specialize pow_exists 4",
                "specialize pow_exists 42",
                "exact pow_exists",
                "cases hcommon",
                "have hequal : x1 = x2",
                "specialize pow_one_twenty_eight_twelve_eq_pow_four_forty_two x1",
                "specialize pow_one_twenty_eight_twelve_eq_pow_four_forty_two x2",
                "apply pow_one_twenty_eight_twelve_eq_pow_four_forty_two",
                "exact hupperpower_witness",
                "exact hcommon_witness",
                "have hfour : exists k. k + 1 = 4",
                "exists 3",
                "norm_num",
                "have hcommontarget : exists k. k + x2 = y",
                "specialize pow_exponent_monotone 4",
                "specialize pow_exponent_monotone 42",
                "specialize pow_exponent_monotone (s + 5)",
                "specialize pow_exponent_monotone x2",
                "specialize pow_exponent_monotone y",
                "apply pow_exponent_monotone",
                "exact hfour",
                "exact hlinear_right_right",
                "exact hcommon_witness",
                "exact hy",
                "have huppercommon : exists k. k + x1 = x2",
                "rewrite hequal",
                "exists 0",
                "apply zero_add",
                "have hxcommon : exists k. k + x = x2",
                "specialize le_trans x",
                "specialize le_trans x1",
                "specialize le_trans x2",
                "apply le_trans",
                "exact hxupper",
                "exact huppercommon",
                "specialize le_trans x",
                "specialize le_trans x2",
                "specialize le_trans y",
                "apply le_trans",
                "exact hxcommon",
                "exact hcommontarget",
            ),
            "Every root 64 through 69 satisfies (s+7)^12 <= 4^(s+5).",
        ),
    )


__all__ = ["make_bertrand_power_bridge_candidate_theorems"]
