"""RFC-v1 H/J base window beginning at square root thirty two.

This isolated candidate tranche supplies the finite base needed before the
six-step Bertrand transport can start at ``n = 512``.  ``PowTotal``, ``Pow``,
``CeilDivSix``, and order notation are authoring conveniences only: every
occurrence is expanded into the existing first-order Peano language before a
theorem specification is returned.

The tranche is a dependency-ordered modular ladder: reusable power and budget
rows feed six fixed-root H envelopes, one uniform J envelope, and a thin
constructive dispatcher for exactly the roots ``32`` through ``37``.  No new
predicate, axiom, proof rule, or classical principle is introduced.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_ceil_sqrt_candidate import ceil_div_six_relation
from .bertrand_power_total_candidate import power_total_relation
from .bertrand_quotient_budget_candidate import witness_le
from .power_algebra_theorems import _power_terms


def make_bertrand_hj_base_thirty_two_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the modular RFC-v1 root-32 base-window tranche."""

    block_total = power_total_relation(tag="hj32_block")
    block_left_seed = _power_terms("a", "d", "x", tag="hj32_block_left_seed")
    block_right_seed = _power_terms("b", "e", "y", tag="hj32_block_right_seed")
    block_seed_bound = witness_le("x", "y", tag="hj32_block_seed_bound")
    block_left = _power_terms("a", "d * m", "X", tag="hj32_block_left")
    block_right = _power_terms("b", "e * m", "Y", tag="hj32_block_right")
    block_result = witness_le("X", "Y", tag="hj32_block_result")
    block_left_outer = _power_terms("x", "m", "q", tag="hj32_block_left_outer")
    block_right_outer = _power_terms("y", "m", "q", tag="hj32_block_right_outer")

    three_four_total = power_total_relation(tag="hj32_three_four")
    three_five = _power_terms("3", "5", "x", tag="hj32_three_five")
    four_four = _power_terms("4", "4", "y", tag="hj32_four_four")
    three_four_result = witness_le("x", "y", tag="hj32_three_four_result")
    three_zero_any = _power_terms("3", "0", "q", tag="hj32_three_zero_any")
    four_zero_any = _power_terms("4", "0", "q", tag="hj32_four_zero_any")
    three_zero = _power_terms("3", "0", "1", tag="hj32_three_zero")
    three_one_value = "1 * 3"
    three_two_value = f"({three_one_value}) * 3"
    three_three_value = f"({three_two_value}) * 3"
    three_four_value = f"({three_three_value}) * 3"
    three_five_value = f"({three_four_value}) * 3"
    three_one = _power_terms("3", "1", three_one_value, tag="hj32_three_one")
    three_two = _power_terms("3", "2", three_two_value, tag="hj32_three_two")
    three_three = _power_terms("3", "3", three_three_value, tag="hj32_three_three")
    three_four = _power_terms("3", "4", three_four_value, tag="hj32_three_four")
    three_five_exact = _power_terms(
        "3", "5", three_five_value, tag="hj32_three_five_exact"
    )
    four_zero = _power_terms("4", "0", "1", tag="hj32_four_zero")
    four_one_value = "1 * 4"
    four_two_value = f"({four_one_value}) * 4"
    four_three_value = f"({four_two_value}) * 4"
    four_four_value = f"({four_three_value}) * 4"
    four_one = _power_terms("4", "1", four_one_value, tag="hj32_four_one")
    four_two = _power_terms("4", "2", four_two_value, tag="hj32_four_two")
    four_three = _power_terms("4", "3", four_three_value, tag="hj32_four_three")
    four_four_exact = _power_terms(
        "4", "4", four_four_value, tag="hj32_four_four_exact"
    )

    eleven_two_total = power_total_relation(tag="hj32_eleven_two")
    eleven_two = _power_terms("11", "2", "x", tag="hj32_eleven_two_left")
    two_seven = _power_terms("2", "7", "y", tag="hj32_eleven_two_right")
    eleven_two_result = witness_le("x", "y", tag="hj32_eleven_two_result")
    seed_two_two = _power_terms("2", "2", "4", tag="hj32_seed_two_two")
    seed_two_seven = _power_terms("2", "7", "128", tag="hj32_seed_two_seven")
    two_three_value = "4 * 2"
    two_four_value = f"({two_three_value}) * 2"
    two_five_value = f"({two_four_value}) * 2"
    two_six_value = f"({two_five_value}) * 2"
    two_seven_value = f"({two_six_value}) * 2"
    two_three_exact = _power_terms(
        "2", "3", two_three_value, tag="hj32_two_three_exact"
    )
    two_four_exact = _power_terms(
        "2", "4", two_four_value, tag="hj32_two_four_exact"
    )
    two_five_exact = _power_terms(
        "2", "5", two_five_value, tag="hj32_two_five_exact"
    )
    two_six_exact = _power_terms(
        "2", "6", two_six_value, tag="hj32_two_six_exact"
    )
    two_seven_exact = _power_terms(
        "2", "7", two_seven_value, tag="hj32_two_seven_exact"
    )

    six_ten_total = power_total_relation(tag="hj32_six_ten")
    six_ten = _power_terms("6", "10", "x", tag="hj32_six_ten_left")
    four_thirteen = _power_terms("4", "13", "y", tag="hj32_six_ten_right")
    six_ten_result = witness_le("x", "y", tag="hj32_six_ten_result")
    row_four_three_five = _power_terms("3", "5", "q", tag="hj32_row4_three_five")
    row_four_four_four = _power_terms("4", "4", "q", tag="hj32_row4_four_four")
    row_four_three_ten = _power_terms("3", "10", "q", tag="hj32_row4_three_ten")
    row_four_four_eight = _power_terms("4", "8", "q", tag="hj32_row4_four_eight")
    row_four_three_ten_block = _power_terms(
        "3", "5 * 2", "x3", tag="hj32_row4_three_ten_block"
    )
    row_four_four_eight_block = _power_terms(
        "4", "4 * 2", "x4", tag="hj32_row4_four_eight_block"
    )
    row_four_two_ten = _power_terms("2", "10", "q", tag="hj32_row4_two_ten")
    row_four_four_five = _power_terms("4", "5", "q", tag="hj32_row4_four_five")
    row_four_six_factor = _power_terms("2 * 3", "10", "x", tag="hj32_row4_six_factor")

    base_total = power_total_relation(tag="hj32_base")
    base_lower = witness_le("32", "s", tag="hj32_base_lower")
    base_upper = witness_le("s", "37", tag="hj32_base_upper")
    base_ceiling = ceil_div_six_relation(
        "s * s", "e", tag="hj32_base_ceiling"
    )
    base_h = _power_terms("s + 1", "2 * s + 2", "h", tag="hj32_base_h")
    base_h_bound = _power_terms("4", "e", "u", tag="hj32_base_h_bound")
    base_j = _power_terms("s + 7", "12", "j", tag="hj32_base_j")
    base_j_bound = _power_terms("4", "s + 5", "g", tag="hj32_base_j_bound")
    base_h_result = witness_le("h", "u", tag="hj32_base_h_result")
    base_j_result = witness_le("j", "g", tag="hj32_base_j_result")

    # The capstone is exposed through a modular ladder below.  In particular,
    # the generic arithmetic row keeps every closed root certificate below the
    # kernel's bounded-normalization ceiling: callers supply only factorized
    # carrier equalities, never a normalized square or scaled budget.
    linear_square_budget = witness_le(
        "a * k", "r * r", tag="hj32_linear_square_budget"
    )
    linear_square_budget_script = (
        "intro a",
        "intro q",
        "intro r",
        "intro t",
        "intro c",
        "intro k",
        "intro d",
        "intro hr",
        "intro hk",
        "intro hd",
        "exists d",
        "rewrite hk",
        "have hmul_add : a * (q * r + c) = a * (q * r) + a * c",
        "specialize mul_add a",
        "specialize mul_add (q * r)",
        "specialize mul_add c",
        "apply mul_add",
        "rewrite hmul_add",
        "have hassoc_one : d + (a * (q * r) + a * c) = "
        "(d + a * (q * r)) + a * c",
        "symm",
        "specialize add_assoc d",
        "specialize add_assoc (a * (q * r))",
        "specialize add_assoc (a * c)",
        "apply add_assoc",
        "rewrite hassoc_one",
        "have hcomm_one : d + a * (q * r) = a * (q * r) + d",
        "specialize add_comm d",
        "specialize add_comm (a * (q * r))",
        "apply add_comm",
        "rewrite hcomm_one",
        "have hassoc_two : (a * (q * r) + d) + a * c = "
        "a * (q * r) + (d + a * c)",
        "specialize add_assoc (a * (q * r))",
        "specialize add_assoc d",
        "specialize add_assoc (a * c)",
        "apply add_assoc",
        "rewrite hassoc_two",
        "have hcomm_two : a * (q * r) + (d + a * c) = "
        "(d + a * c) + a * (q * r)",
        "specialize add_comm (a * (q * r))",
        "specialize add_comm (d + a * c)",
        "apply add_comm",
        "rewrite hcomm_two",
        "rewrite hd",
        "have hmul_assoc : (a * q) * r = a * (q * r)",
        "specialize mul_assoc a",
        "specialize mul_assoc q",
        "specialize mul_assoc r",
        "apply mul_assoc",
        "rewrite <- hmul_assoc",
        "have hadd_mul : (t + a * q) * r = t * r + (a * q) * r",
        "specialize add_mul t",
        "specialize add_mul (a * q)",
        "specialize add_mul r",
        "apply add_mul",
        "rewrite <- hadd_mul",
        "have hcomm_three : t + a * q = a * q + t",
        "specialize add_comm t",
        "specialize add_comm (a * q)",
        "apply add_comm",
        "rewrite hcomm_three",
        "rewrite <- hr",
        "refl",
    )

    root_budget_terms = {
        32: "(4 * 13 + 1) + 4 * 29",
        33: "13 * 13 + 8",
        34: "13 * 14",
        35: "13 * 14 + 6",
        36: "2 * 37 + 2 * (5 * 13)",
        37: "2 * 38 + 7 * 19",
    }
    root_budget_results = {
        root: witness_le(
            f"6 * ({budget})",
            f"{root} * {root}",
            tag=f"hj32_scaled_budget_root_{root}",
        )
        for root, budget in root_budget_terms.items()
    }

    # Filled one root at a time below.  Keeping the six scripts separate is a
    # deliberate capacity boundary and makes every finite carrier auditable.
    root_budget_scripts: dict[int, tuple[str, ...]] = {}
    root_budget_dependencies = {
        32: ("linear_square_budget", "mul_add", "add_assoc", "add_comm"),
        33: ("linear_square_budget", "add_mul", "mul_add", "add_assoc"),
        34: ("linear_square_budget", "add_mul", "mul_add", "add_assoc"),
        35: ("linear_square_budget", "mul_add", "add_mul", "add_assoc"),
        36: (
            "linear_square_budget",
            "mul_add",
            "mul_assoc",
            "mul_comm",
            "add_mul",
            "add_assoc",
            "add_comm",
        ),
        37: (
            "linear_square_budget",
            "mul_add",
            "mul_assoc",
            "mul_comm",
            "add_mul",
            "add_assoc",
            "add_comm",
        ),
    }

    def root_budget_prefix(
        root: int, offset: int, remainder: int, gap: str
    ) -> tuple[str, ...]:
        budget = root_budget_terms[root]
        return (
            "specialize linear_square_budget 6",
            "specialize linear_square_budget 5",
            f"specialize linear_square_budget {root}",
            f"specialize linear_square_budget {offset}",
            f"specialize linear_square_budget {remainder}",
            f"specialize linear_square_budget ({budget})",
            f"specialize linear_square_budget ({gap})",
            "apply linear_square_budget",
            "norm_num",
        )

    root_budget_scripts[36] = (
        *root_budget_prefix(36, 6, 24, "2 * 36"),
        "have hk_first : 2 * 37 = 5 * 10 + 24",
        "norm_num",
        "rewrite hk_first",
        "have hk_second : 2 * (5 * 13) = 5 * 26",
        "trans (2 * 5) * 13",
        "symm",
        "specialize mul_assoc 2",
        "specialize mul_assoc 5",
        "specialize mul_assoc 13",
        "apply mul_assoc",
        "trans (5 * 2) * 13",
        "congr",
        "specialize mul_comm 2",
        "specialize mul_comm 5",
        "apply mul_comm",
        "refl",
        "trans 5 * (2 * 13)",
        "specialize mul_assoc 5",
        "specialize mul_assoc 2",
        "specialize mul_assoc 13",
        "apply mul_assoc",
        "have hk_twenty_six : 2 * 13 = 26",
        "norm_num",
        "rewrite hk_twenty_six",
        "refl",
        "rewrite hk_second",
        "have hk_assoc_one : (5 * 10 + 24) + 5 * 26 = "
        "5 * 10 + (24 + 5 * 26)",
        "specialize add_assoc (5 * 10)",
        "specialize add_assoc 24",
        "specialize add_assoc (5 * 26)",
        "apply add_assoc",
        "rewrite hk_assoc_one",
        "have hk_comm : 24 + 5 * 26 = 5 * 26 + 24",
        "specialize add_comm 24",
        "specialize add_comm (5 * 26)",
        "apply add_comm",
        "rewrite hk_comm",
        "have hk_assoc_two : 5 * 10 + (5 * 26 + 24) = "
        "(5 * 10 + 5 * 26) + 24",
        "symm",
        "specialize add_assoc (5 * 10)",
        "specialize add_assoc (5 * 26)",
        "specialize add_assoc 24",
        "apply add_assoc",
        "rewrite hk_assoc_two",
        "have hk_factor : 5 * (10 + 26) = 5 * 10 + 5 * 26",
        "specialize mul_add 5",
        "specialize mul_add 10",
        "specialize mul_add 26",
        "apply mul_add",
        "rewrite <- hk_factor",
        "have hk_root : 10 + 26 = 36",
        "norm_num",
        "rewrite hk_root",
        "refl",
        "have hd_bridge : 6 * 24 = 4 * 36",
        "have hd_twenty_four : 24 = 4 * 6",
        "norm_num",
        "rewrite hd_twenty_four",
        "trans (6 * 4) * 6",
        "symm",
        "specialize mul_assoc 6",
        "specialize mul_assoc 4",
        "specialize mul_assoc 6",
        "apply mul_assoc",
        "trans (4 * 6) * 6",
        "congr",
        "specialize mul_comm 6",
        "specialize mul_comm 4",
        "apply mul_comm",
        "refl",
        "trans 4 * (6 * 6)",
        "specialize mul_assoc 4",
        "specialize mul_assoc 6",
        "specialize mul_assoc 6",
        "apply mul_assoc",
        "have hd_thirty_six : 36 = 6 * 6",
        "norm_num",
        "rewrite <- hd_thirty_six",
        "refl",
        "rewrite hd_bridge",
        "have hd_factor : (2 + 4) * 36 = 2 * 36 + 4 * 36",
        "specialize add_mul 2",
        "specialize add_mul 4",
        "specialize add_mul 36",
        "apply add_mul",
        "rewrite <- hd_factor",
        "have hd_six : 2 + 4 = 6",
        "norm_num",
        "rewrite hd_six",
        "refl",
    )

    root_budget_scripts[37] = (
        *root_budget_prefix(37, 7, 24, "3 * 37 + 4"),
        "have hk_first : 2 * 38 = 5 * 10 + 26",
        "norm_num",
        "rewrite hk_first",
        "have hk_second : 7 * 19 = 5 * 20 + 33",
        "have hk_seven : 7 = 5 + 2",
        "norm_num",
        "rewrite hk_seven",
        "trans 5 * 19 + 2 * 19",
        "specialize add_mul 5",
        "specialize add_mul 2",
        "specialize add_mul 19",
        "apply add_mul",
        "have hk_two_nineteen : 2 * 19 = 38",
        "norm_num",
        "rewrite hk_two_nineteen",
        "have hk_right : 5 * 20 + 33 = 5 * 19 + 38",
        "have hk_step : 5 * 20 = 5 * 19 + 5",
        "have hk_twenty : 20 = 19 + 1",
        "norm_num",
        "rewrite hk_twenty",
        "trans 5 * 19 + 5 * 1",
        "specialize mul_add 5",
        "specialize mul_add 19",
        "specialize mul_add 1",
        "apply mul_add",
        "congr",
        "refl",
        "norm_num",
        "rewrite hk_step",
        "have hk_assoc_step : (5 * 19 + 5) + 33 = 5 * 19 + (5 + 33)",
        "specialize add_assoc (5 * 19)",
        "specialize add_assoc 5",
        "specialize add_assoc 33",
        "apply add_assoc",
        "rewrite hk_assoc_step",
        "have hk_thirty_eight : 5 + 33 = 38",
        "norm_num",
        "rewrite hk_thirty_eight",
        "refl",
        "symm",
        "exact hk_right",
        "rewrite hk_second",
        "have hk_assoc_one : (5 * 10 + 26) + (5 * 20 + 33) = "
        "5 * 10 + (26 + (5 * 20 + 33))",
        "specialize add_assoc (5 * 10)",
        "specialize add_assoc 26",
        "specialize add_assoc (5 * 20 + 33)",
        "apply add_assoc",
        "rewrite hk_assoc_one",
        "have hk_assoc_two : 26 + (5 * 20 + 33) = (26 + 5 * 20) + 33",
        "symm",
        "specialize add_assoc 26",
        "specialize add_assoc (5 * 20)",
        "specialize add_assoc 33",
        "apply add_assoc",
        "rewrite hk_assoc_two",
        "have hk_comm : 26 + 5 * 20 = 5 * 20 + 26",
        "specialize add_comm 26",
        "specialize add_comm (5 * 20)",
        "apply add_comm",
        "rewrite hk_comm",
        "have hk_assoc_three : (5 * 20 + 26) + 33 = 5 * 20 + (26 + 33)",
        "specialize add_assoc (5 * 20)",
        "specialize add_assoc 26",
        "specialize add_assoc 33",
        "apply add_assoc",
        "rewrite hk_assoc_three",
        "have hk_assoc_four : 5 * 10 + (5 * 20 + (26 + 33)) = "
        "(5 * 10 + 5 * 20) + (26 + 33)",
        "symm",
        "specialize add_assoc (5 * 10)",
        "specialize add_assoc (5 * 20)",
        "specialize add_assoc (26 + 33)",
        "apply add_assoc",
        "rewrite hk_assoc_four",
        "have hk_factor_one : 5 * (10 + 20) = 5 * 10 + 5 * 20",
        "specialize mul_add 5",
        "specialize mul_add 10",
        "specialize mul_add 20",
        "apply mul_add",
        "rewrite <- hk_factor_one",
        "have hk_thirty : 10 + 20 = 30",
        "norm_num",
        "rewrite hk_thirty",
        "have hk_remainder : 26 + 33 = 5 * 7 + 24",
        "norm_num",
        "rewrite hk_remainder",
        "have hk_assoc_five : 5 * 30 + (5 * 7 + 24) = "
        "(5 * 30 + 5 * 7) + 24",
        "symm",
        "specialize add_assoc (5 * 30)",
        "specialize add_assoc (5 * 7)",
        "specialize add_assoc 24",
        "apply add_assoc",
        "rewrite hk_assoc_five",
        "have hk_factor_two : 5 * (30 + 7) = 5 * 30 + 5 * 7",
        "specialize mul_add 5",
        "specialize mul_add 30",
        "specialize mul_add 7",
        "apply mul_add",
        "rewrite <- hk_factor_two",
        "have hk_root : 30 + 7 = 37",
        "norm_num",
        "rewrite hk_root",
        "refl",
        "have hd_bridge : 6 * 24 = 4 * 36",
        "have hd_twenty_four : 24 = 4 * 6",
        "norm_num",
        "rewrite hd_twenty_four",
        "trans (6 * 4) * 6",
        "symm",
        "specialize mul_assoc 6",
        "specialize mul_assoc 4",
        "specialize mul_assoc 6",
        "apply mul_assoc",
        "trans (4 * 6) * 6",
        "congr",
        "specialize mul_comm 6",
        "specialize mul_comm 4",
        "apply mul_comm",
        "refl",
        "trans 4 * (6 * 6)",
        "specialize mul_assoc 4",
        "specialize mul_assoc 6",
        "specialize mul_assoc 6",
        "apply mul_assoc",
        "have hd_thirty_six : 36 = 6 * 6",
        "norm_num",
        "rewrite <- hd_thirty_six",
        "refl",
        "rewrite hd_bridge",
        "have hd_assoc : (3 * 37 + 4) + 4 * 36 = "
        "3 * 37 + (4 + 4 * 36)",
        "specialize add_assoc (3 * 37)",
        "specialize add_assoc 4",
        "specialize add_assoc (4 * 36)",
        "apply add_assoc",
        "rewrite hd_assoc",
        "have hd_step : 4 + 4 * 36 = 4 * 37",
        "have hd_thirty_seven : 37 = 1 + 36",
        "norm_num",
        "rewrite hd_thirty_seven",
        "trans 4 * 1 + 4 * 36",
        "congr",
        "norm_num",
        "refl",
        "symm",
        "specialize mul_add 4",
        "specialize mul_add 1",
        "specialize mul_add 36",
        "apply mul_add",
        "rewrite hd_step",
        "have hd_factor : (3 + 4) * 37 = 3 * 37 + 4 * 37",
        "specialize add_mul 3",
        "specialize add_mul 4",
        "specialize add_mul 37",
        "apply add_mul",
        "rewrite <- hd_factor",
        "have hd_seven : 3 + 4 = 7",
        "norm_num",
        "rewrite hd_seven",
        "refl",
    )

    # Final capacity-safe carrier bodies.  Large values are never represented
    # by deep unary numerals: every normalization target is a shallow product
    # or sum whose value is at most 128.
    root_budget_scripts[32] = (
        *root_budget_prefix(32, 2, 9, "10"),
        "have hk_part_one : 4 * 13 + 1 = 5 * 10 + 3",
        "norm_num",
        "rewrite hk_part_one",
        "have hk_part_two : 4 * 29 = 5 * 22 + 6",
        "norm_num",
        "rewrite hk_part_two",
        "have hk_assoc_one : (5 * 10 + 3) + (5 * 22 + 6) = "
        "5 * 10 + (3 + (5 * 22 + 6))",
        "specialize add_assoc (5 * 10)",
        "specialize add_assoc 3",
        "specialize add_assoc (5 * 22 + 6)",
        "apply add_assoc",
        "rewrite hk_assoc_one",
        "have hk_assoc_two : 3 + (5 * 22 + 6) = (3 + 5 * 22) + 6",
        "symm",
        "specialize add_assoc 3",
        "specialize add_assoc (5 * 22)",
        "specialize add_assoc 6",
        "apply add_assoc",
        "rewrite hk_assoc_two",
        "have hk_comm : 3 + 5 * 22 = 5 * 22 + 3",
        "specialize add_comm 3",
        "specialize add_comm (5 * 22)",
        "apply add_comm",
        "rewrite hk_comm",
        "have hk_assoc_three : (5 * 22 + 3) + 6 = 5 * 22 + (3 + 6)",
        "specialize add_assoc (5 * 22)",
        "specialize add_assoc 3",
        "specialize add_assoc 6",
        "apply add_assoc",
        "rewrite hk_assoc_three",
        "have hk_assoc_four : 5 * 10 + (5 * 22 + (3 + 6)) = "
        "(5 * 10 + 5 * 22) + (3 + 6)",
        "symm",
        "specialize add_assoc (5 * 10)",
        "specialize add_assoc (5 * 22)",
        "specialize add_assoc (3 + 6)",
        "apply add_assoc",
        "rewrite hk_assoc_four",
        "have hk_factor : 5 * (10 + 22) = 5 * 10 + 5 * 22",
        "specialize mul_add 5",
        "specialize mul_add 10",
        "specialize mul_add 22",
        "apply mul_add",
        "rewrite <- hk_factor",
        "have hk_root : 10 + 22 = 32",
        "norm_num",
        "rewrite hk_root",
        "have hk_remainder : 3 + 6 = 9",
        "norm_num",
        "rewrite hk_remainder",
        "refl",
        "norm_num",
    )

    root_budget_scripts[33] = (
        *root_budget_prefix(33, 3, 12, "27"),
        "have hk_split : 13 * 13 = 9 * 13 + 4 * 13",
        "have hk_thirteen : 13 = 9 + 4",
        "norm_num",
        "rewrite hk_thirteen",
        "specialize add_mul 9",
        "specialize add_mul 4",
        "specialize add_mul 13",
        "apply add_mul",
        "rewrite hk_split",
        "have hk_bridge : 9 * 13 = 5 * 21 + 12",
        "norm_num",
        "rewrite hk_bridge",
        "have hk_assoc_one : (5 * 21 + 12) + 4 * 13 = "
        "5 * 21 + (12 + 4 * 13)",
        "specialize add_assoc (5 * 21)",
        "specialize add_assoc 12",
        "specialize add_assoc (4 * 13)",
        "apply add_assoc",
        "rewrite hk_assoc_one",
        "have hk_assoc_two : (5 * 21 + (12 + 4 * 13)) + 8 = "
        "5 * 21 + ((12 + 4 * 13) + 8)",
        "specialize add_assoc (5 * 21)",
        "specialize add_assoc (12 + 4 * 13)",
        "specialize add_assoc 8",
        "apply add_assoc",
        "rewrite hk_assoc_two",
        "have hk_remainder : (12 + 4 * 13) + 8 = 5 * 12 + 12",
        "norm_num",
        "rewrite hk_remainder",
        "have hk_assoc_three : 5 * 21 + (5 * 12 + 12) = "
        "(5 * 21 + 5 * 12) + 12",
        "symm",
        "specialize add_assoc (5 * 21)",
        "specialize add_assoc (5 * 12)",
        "specialize add_assoc 12",
        "apply add_assoc",
        "rewrite hk_assoc_three",
        "have hk_factor : 5 * (21 + 12) = 5 * 21 + 5 * 12",
        "specialize mul_add 5",
        "specialize mul_add 21",
        "specialize mul_add 12",
        "apply mul_add",
        "rewrite <- hk_factor",
        "have hk_root : 21 + 12 = 33",
        "norm_num",
        "rewrite hk_root",
        "refl",
        "norm_num",
    )

    root_budget_scripts[34] = (
        *root_budget_prefix(34, 4, 12, "2 * 32"),
        "have hk_split : 13 * 14 = 5 * 14 + 8 * 14",
        "have hk_thirteen : 13 = 5 + 8",
        "norm_num",
        "rewrite hk_thirteen",
        "specialize add_mul 5",
        "specialize add_mul 8",
        "specialize add_mul 14",
        "apply add_mul",
        "rewrite hk_split",
        "have hk_bridge : 8 * 14 = 5 * 20 + 12",
        "norm_num",
        "rewrite hk_bridge",
        "have hk_assoc : 5 * 14 + (5 * 20 + 12) = "
        "(5 * 14 + 5 * 20) + 12",
        "symm",
        "specialize add_assoc (5 * 14)",
        "specialize add_assoc (5 * 20)",
        "specialize add_assoc 12",
        "apply add_assoc",
        "rewrite hk_assoc",
        "have hk_factor : 5 * (14 + 20) = 5 * 14 + 5 * 20",
        "specialize mul_add 5",
        "specialize mul_add 14",
        "specialize mul_add 20",
        "apply mul_add",
        "rewrite <- hk_factor",
        "have hk_root : 14 + 20 = 34",
        "norm_num",
        "rewrite hk_root",
        "refl",
        "have hd_left : 2 * 32 = 4 * 16",
        "norm_num",
        "rewrite hd_left",
        "have hd_right : 6 * 12 = 4 * 18",
        "norm_num",
        "rewrite hd_right",
        "have hd_factor : 4 * (16 + 18) = 4 * 16 + 4 * 18",
        "specialize mul_add 4",
        "specialize mul_add 16",
        "specialize mul_add 18",
        "apply mul_add",
        "rewrite <- hd_factor",
        "have hd_root : 16 + 18 = 34",
        "norm_num",
        "rewrite hd_root",
        "refl",
    )

    root_budget_scripts[35] = (
        *root_budget_prefix(35, 5, 13, "2 * 35 + 27"),
        "have hk_split : 13 * 14 = 5 * 14 + 8 * 14",
        "have hk_thirteen : 13 = 5 + 8",
        "norm_num",
        "rewrite hk_thirteen",
        "specialize add_mul 5",
        "specialize add_mul 8",
        "specialize add_mul 14",
        "apply add_mul",
        "rewrite hk_split",
        "have hk_bridge : 8 * 14 = 5 * 20 + 12",
        "norm_num",
        "rewrite hk_bridge",
        "have hk_assoc_one : 5 * 14 + (5 * 20 + 12) = "
        "(5 * 14 + 5 * 20) + 12",
        "symm",
        "specialize add_assoc (5 * 14)",
        "specialize add_assoc (5 * 20)",
        "specialize add_assoc 12",
        "apply add_assoc",
        "rewrite hk_assoc_one",
        "have hk_factor : 5 * (14 + 20) = 5 * 14 + 5 * 20",
        "specialize mul_add 5",
        "specialize mul_add 14",
        "specialize mul_add 20",
        "apply mul_add",
        "rewrite <- hk_factor",
        "have hk_thirty_four : 14 + 20 = 34",
        "norm_num",
        "rewrite hk_thirty_four",
        "have hk_assoc_two : (5 * 34 + 12) + 6 = 5 * 34 + (12 + 6)",
        "specialize add_assoc (5 * 34)",
        "specialize add_assoc 12",
        "specialize add_assoc 6",
        "apply add_assoc",
        "rewrite hk_assoc_two",
        "have hk_remainder : 12 + 6 = 5 + 13",
        "norm_num",
        "rewrite hk_remainder",
        "have hk_assoc_three : 5 * 34 + (5 + 13) = (5 * 34 + 5) + 13",
        "symm",
        "specialize add_assoc (5 * 34)",
        "specialize add_assoc 5",
        "specialize add_assoc 13",
        "apply add_assoc",
        "rewrite hk_assoc_three",
        "have hk_step : 5 * 35 = 5 * 34 + 5",
        "have hk_thirty_five : 35 = 34 + 1",
        "norm_num",
        "rewrite hk_thirty_five",
        "trans 5 * 34 + 5 * 1",
        "specialize mul_add 5",
        "specialize mul_add 34",
        "specialize mul_add 1",
        "apply mul_add",
        "congr",
        "refl",
        "norm_num",
        "rewrite <- hk_step",
        "refl",
        "have hd_assoc : (2 * 35 + 27) + 6 * 13 = "
        "2 * 35 + (27 + 6 * 13)",
        "specialize add_assoc (2 * 35)",
        "specialize add_assoc 27",
        "specialize add_assoc (6 * 13)",
        "apply add_assoc",
        "rewrite hd_assoc",
        "have hd_bridge : 27 + 6 * 13 = 3 * 35",
        "norm_num",
        "rewrite hd_bridge",
        "have hd_factor : (2 + 3) * 35 = 2 * 35 + 3 * 35",
        "specialize add_mul 2",
        "specialize add_mul 3",
        "specialize add_mul 35",
        "apply add_mul",
        "rewrite <- hd_factor",
        "have hd_five : 2 + 3 = 5",
        "norm_num",
        "rewrite hd_five",
        "refl",
    )

    ceil_budget_source = ceil_div_six_relation(
        "x", "e", tag="hj32_ceil_budget_source"
    )
    ceil_budget_scaled = witness_le(
        "6 * k", "x", tag="hj32_ceil_budget_scaled"
    )
    ceil_budget_result = witness_le(
        "k", "e", tag="hj32_ceil_budget_result"
    )
    ceil_budget_script = (
        "intro x",
        "intro k",
        "intro e",
        "intro hceiling",
        "intro hscaled",
        "cases hceiling",
        "have hscaled_to_ceiling : "
        f"{witness_le('6 * k', '6 * e', tag='hj32_ceil_budget_chain')}",
        "specialize le_trans (6 * k)",
        "specialize le_trans x",
        "specialize le_trans (6 * e)",
        "apply le_trans",
        "exact hscaled",
        "exact hceiling_left",
        "specialize mul_le_cancel_left_nonzero 6",
        "specialize mul_le_cancel_left_nonzero k",
        "specialize mul_le_cancel_left_nonzero e",
        "apply mul_le_cancel_left_nonzero",
        "specialize succ_ne_zero 5",
        "exact succ_ne_zero",
        "exact hscaled_to_ceiling",
    )

    residual_six_total = power_total_relation(tag="hj32_residual_six")
    residual_six_left = _power_terms(
        "6", "6", "x", tag="hj32_residual_six_left"
    )
    residual_six_right = _power_terms(
        "4", "8", "y", tag="hj32_residual_six_right"
    )
    residual_six_result = witness_le(
        "x", "y", tag="hj32_residual_six_result"
    )
    residual_four_total = power_total_relation(tag="hj32_residual_four")
    residual_four_left = _power_terms(
        "6", "4", "x", tag="hj32_residual_four_left"
    )
    residual_four_right = _power_terms(
        "4", "6", "y", tag="hj32_residual_four_right"
    )
    residual_four_result = witness_le(
        "x", "y", tag="hj32_residual_four_result"
    )
    h_root_data: dict[int, dict[str, str]] = {}
    for root in range(32, 38):
        h_root_data[root] = {
            "total": power_total_relation(tag=f"hj32_h_root_{root}"),
            "ceiling": ceil_div_six_relation(
                f"{root} * {root}",
                "e",
                tag=f"hj32_h_root_{root}_ceiling",
            ),
            "h": _power_terms(
                f"{root} + 1",
                f"2 * {root} + 2",
                "h",
                tag=f"hj32_h_root_{root}_h",
            ),
            "u": _power_terms(
                "4", "e", "u", tag=f"hj32_h_root_{root}_u"
            ),
            "result": witness_le(
                "h", "u", tag=f"hj32_h_root_{root}_result"
            ),
        }
    h_root_scripts: dict[int, tuple[str, ...]] = {}
    h_root_dependencies: dict[int, tuple[str, ...]] = {}

    class LocalPowerScript:
        """Deterministically expand power-algebra steps into primitive commands."""

        def __init__(self, *, first_witness_index: int) -> None:
            self.commands: list[str] = []
            self.witness_index = first_witness_index

        def add(self, *commands: str) -> None:
            self.commands.extend(commands)

        def total(self, label: str, base: str, exponent: str) -> tuple[str, str]:
            index = self.witness_index
            result = "x" if index == 0 else f"x{index}"
            self.witness_index += 1
            binder = f"hj32_local_value_{label}"
            relation = _power_terms(
                base, exponent, binder, tag=f"hj32_local_total_{label}"
            )
            self.add(
                f"have {label} : exists {binder}. ({relation})",
                f"specialize htotal {base}",
                f"specialize htotal {exponent}",
                "exact htotal",
                f"cases {label}",
            )
            return result, f"{label}_witness"

        def add_equality(
            self,
            label: str,
            base: str,
            left_exponent: str,
            right_exponent: str,
            total_exponent: str,
            left_result: str,
            right_result: str,
            total_result: str,
            left_power: str,
            right_power: str,
            total_power_name: str,
            equality_commands: tuple[str, ...] = ("norm_num",),
        ) -> str:
            self.add(
                f"have {label} : {total_result} = {left_result} * {right_result}",
                f"specialize pow_add {base}",
                f"specialize pow_add {left_exponent}",
                f"specialize pow_add {right_exponent}",
                f"specialize pow_add {total_exponent}",
                f"specialize pow_add {left_result}",
                f"specialize pow_add {right_result}",
                f"specialize pow_add {total_result}",
                "apply pow_add",
                *equality_commands,
                f"exact {left_power}",
                f"exact {right_power}",
                f"exact {total_power_name}",
            )
            return label

        def iterated_equality(
            self,
            label: str,
            base: str,
            seed_exponent: str,
            outer_exponent: str,
            total_exponent: str,
            seed_result: str,
            outer_result: str,
            total_result: str,
            seed_power: str,
            outer_power: str,
            total_power_name: str,
            equality_commands: tuple[str, ...] = ("norm_num",),
        ) -> str:
            self.add(
                f"have {label} : {outer_result} = {total_result}",
                f"specialize pow_mul_exp_from_total {base}",
                f"specialize pow_mul_exp_from_total {seed_exponent}",
                f"specialize pow_mul_exp_from_total {outer_exponent}",
                f"specialize pow_mul_exp_from_total {total_exponent}",
                f"specialize pow_mul_exp_from_total {seed_result}",
                f"specialize pow_mul_exp_from_total {outer_result}",
                f"specialize pow_mul_exp_from_total {total_result}",
                "apply pow_mul_exp_from_total",
                "exact htotal",
                *equality_commands,
                f"exact {seed_power}",
                f"exact {outer_power}",
                f"exact {total_power_name}",
            )
            return label

        def product_equality(
            self,
            label: str,
            left_base: str,
            right_base: str,
            numeric_base: str,
            exponent: str,
            left_result: str,
            right_result: str,
            total_result: str,
            left_power: str,
            right_power: str,
            total_power_name: str,
        ) -> str:
            relation = _power_terms(
                f"{left_base} * {right_base}",
                exponent,
                total_result,
                tag=f"hj32_local_product_{label}",
            )
            self.add(
                f"have {label}_graph : {relation}",
                f"have {label}_base : {left_base} * {right_base} = {numeric_base}",
                "norm_num",
                f"rewrite {label}_base",
                f"rewrite {label}_base",
                f"exact {total_power_name}",
                f"have {label} : {total_result} = {left_result} * {right_result}",
                f"specialize pow_mul_base {left_base}",
                f"specialize pow_mul_base {right_base}",
                f"specialize pow_mul_base {exponent}",
                f"specialize pow_mul_base {left_result}",
                f"specialize pow_mul_base {right_result}",
                f"specialize pow_mul_base {total_result}",
                "apply pow_mul_base",
                f"exact {left_power}",
                f"exact {right_power}",
                f"exact {label}_graph",
            )
            return label

        def product_bound(
            self,
            label: str,
            left_a: str,
            right_a: str,
            left_b: str,
            right_b: str,
            first_bound: str,
            second_bound: str,
        ) -> str:
            relation = witness_le(
                f"{left_a} * {left_b}",
                f"{right_a} * {right_b}",
                tag=f"hj32_local_product_bound_{label}",
            )
            self.add(
                f"have {label} : {relation}",
                f"specialize mul_le_mul {left_a}",
                f"specialize mul_le_mul {right_a}",
                f"specialize mul_le_mul {left_b}",
                f"specialize mul_le_mul {right_b}",
                "apply mul_le_mul",
                f"exact {first_bound}",
                f"exact {second_bound}",
            )
            return label

        def base_bound(
            self,
            label: str,
            left_base: str,
            right_base: str,
            exponent: str,
            left_result: str,
            right_result: str,
            base_bound_name: str,
            left_power: str,
            right_power: str,
        ) -> str:
            relation = witness_le(
                left_result, right_result, tag=f"hj32_local_base_bound_{label}"
            )
            self.add(
                f"have {label} : {relation}",
                f"specialize pow_base_monotone {left_base}",
                f"specialize pow_base_monotone {right_base}",
                f"specialize pow_base_monotone {exponent}",
                f"specialize pow_base_monotone {left_result}",
                f"specialize pow_base_monotone {right_result}",
                "apply pow_base_monotone",
                f"exact {base_bound_name}",
                f"exact {left_power}",
                f"exact {right_power}",
            )
            return label

        def block_bound(
            self,
            label: str,
            left_base: str,
            right_base: str,
            left_seed_exponent: str,
            right_seed_exponent: str,
            multiplier: str,
            left_seed_result: str,
            right_seed_result: str,
            left_result: str,
            right_result: str,
            left_seed: str,
            right_seed: str,
            seed_bound: str,
            left_power: str,
            right_power: str,
        ) -> str:
            relation = witness_le(
                left_result, right_result, tag=f"hj32_local_block_bound_{label}"
            )
            self.add(
                f"have {label} : {relation}",
                f"specialize pow_block_bound_from_total {left_base}",
                f"specialize pow_block_bound_from_total {right_base}",
                f"specialize pow_block_bound_from_total {left_seed_exponent}",
                f"specialize pow_block_bound_from_total {right_seed_exponent}",
                f"specialize pow_block_bound_from_total {multiplier}",
                f"specialize pow_block_bound_from_total {left_seed_result}",
                f"specialize pow_block_bound_from_total {right_seed_result}",
                f"specialize pow_block_bound_from_total {left_result}",
                f"specialize pow_block_bound_from_total {right_result}",
                "apply pow_block_bound_from_total",
                "exact htotal",
                f"exact {left_seed}",
                f"exact {right_seed}",
                f"exact {seed_bound}",
                f"exact {left_power}",
                f"exact {right_power}",
            )
            return label

        def exponent_bound(
            self,
            label: str,
            base: str,
            left_exponent: str,
            right_exponent: str,
            left_result: str,
            right_result: str,
            exponent_bound_name: str,
            left_power: str,
            right_power: str,
            base_gap: str,
        ) -> str:
            relation = witness_le(
                left_result,
                right_result,
                tag=f"hj32_local_exponent_bound_{label}",
            )
            self.add(
                f"have {label} : {relation}",
                f"specialize pow_exponent_monotone_from_total {base}",
                f"specialize pow_exponent_monotone_from_total {left_exponent}",
                f"specialize pow_exponent_monotone_from_total {right_exponent}",
                f"specialize pow_exponent_monotone_from_total {left_result}",
                f"specialize pow_exponent_monotone_from_total {right_result}",
                "apply pow_exponent_monotone_from_total",
                "exact htotal",
                f"exists {base_gap}",
                "norm_num",
                f"exact {exponent_bound_name}",
                f"exact {left_power}",
                f"exact {right_power}",
            )
            return label

        def trans_bound(
            self,
            label: str,
            left: str,
            middle: str,
            right: str,
            first_bound: str,
            second_bound: str,
        ) -> str:
            relation = witness_le(
                left, right, tag=f"hj32_local_trans_bound_{label}"
            )
            self.add(
                f"have {label} : {relation}",
                f"specialize le_trans {left}",
                f"specialize le_trans {middle}",
                f"specialize le_trans {right}",
                "apply le_trans",
                f"exact {first_bound}",
                f"exact {second_bound}",
            )
            return label

    residual_six = LocalPowerScript(first_witness_index=1)
    residual_six.add(
        "intro x",
        "intro y",
        "intro htotal",
        "intro hx",
        "intro hy",
    )
    rs_p3_five_r, rs_p3_five = residual_six.total("rs_p3_five", "3", "5")
    rs_p4_four_r, rs_p4_four = residual_six.total("rs_p4_four", "4", "4")
    residual_six.add(
        "have rs_seed : "
        f"{witness_le(rs_p3_five_r, rs_p4_four_r, tag='hj32_rs_seed')}",
        f"specialize pow_three_five_le_pow_four_four_from_total {rs_p3_five_r}",
        f"specialize pow_three_five_le_pow_four_four_from_total {rs_p4_four_r}",
        "apply pow_three_five_le_pow_four_four_from_total",
        "exact htotal",
        f"exact {rs_p3_five}",
        f"exact {rs_p4_four}",
    )
    rs_p3_one_r, rs_p3_one = residual_six.total("rs_p3_one", "3", "1")
    rs_p4_one_r, rs_p4_one = residual_six.total("rs_p4_one", "4", "1")
    residual_six.add(
        "have rs_base : " + witness_le("3", "4", tag="hj32_rs_base"),
        "exists 1",
        "norm_num",
    )
    rs_one_bound = residual_six.base_bound(
        "rs_one_bound",
        "3",
        "4",
        "1",
        rs_p3_one_r,
        rs_p4_one_r,
        "rs_base",
        rs_p3_one,
        rs_p4_one,
    )
    rs_p3_six_r, rs_p3_six = residual_six.total("rs_p3_six", "3", "6")
    rs_p4_five_r, rs_p4_five = residual_six.total("rs_p4_five", "4", "5")
    rs_three_product = residual_six.add_equality(
        "rs_three_product",
        "3",
        "5",
        "1",
        "6",
        rs_p3_five_r,
        rs_p3_one_r,
        rs_p3_six_r,
        rs_p3_five,
        rs_p3_one,
        rs_p3_six,
    )
    rs_four_product = residual_six.add_equality(
        "rs_four_product",
        "4",
        "4",
        "1",
        "5",
        rs_p4_four_r,
        rs_p4_one_r,
        rs_p4_five_r,
        rs_p4_four,
        rs_p4_one,
        rs_p4_five,
    )
    rs_three_bound = residual_six.product_bound(
        "rs_three_bound",
        rs_p3_five_r,
        rs_p4_four_r,
        rs_p3_one_r,
        rs_p4_one_r,
        "rs_seed",
        rs_one_bound,
    )
    residual_six.add(
        f"rewrite <- {rs_three_product} at {rs_three_bound}",
        f"rewrite <- {rs_four_product} at {rs_three_bound}",
        f"have rs_seeds : ({seed_two_two}) /\\ ({seed_two_seven})",
        "apply pow_two_seed_bundle_from_total",
        "exact htotal",
        "cases rs_seeds",
    )
    rs_p2_six_r, rs_p2_six = residual_six.total("rs_p2_six", "2", "6")
    rs_p4_three_r, rs_p4_three = residual_six.total("rs_p4_three", "4", "3")
    rs_two_bridge = residual_six.iterated_equality(
        "rs_two_bridge",
        "2",
        "2",
        "3",
        "6",
        "4",
        rs_p4_three_r,
        rs_p2_six_r,
        "rs_seeds_left",
        rs_p4_three,
        rs_p2_six,
    )
    residual_six.add(
        "have rs_two_bound : "
        f"{witness_le(rs_p2_six_r, rs_p4_three_r, tag='hj32_rs_two_bound')}",
        f"rewrite {rs_two_bridge}",
        f"specialize le_refl {rs_p2_six_r}",
        "exact le_refl",
    )
    rs_six_product = residual_six.product_equality(
        "rs_six_product",
        "2",
        "3",
        "6",
        "6",
        rs_p2_six_r,
        rs_p3_six_r,
        "x",
        rs_p2_six,
        rs_p3_six,
        "hx",
    )
    rs_eight_product = residual_six.add_equality(
        "rs_eight_product",
        "4",
        "3",
        "5",
        "8",
        rs_p4_three_r,
        rs_p4_five_r,
        "y",
        rs_p4_three,
        rs_p4_five,
        "hy",
    )
    rs_result = residual_six.product_bound(
        "rs_result",
        rs_p2_six_r,
        rs_p4_three_r,
        rs_p3_six_r,
        rs_p4_five_r,
        "rs_two_bound",
        rs_three_bound,
    )
    residual_six.add(
        f"rewrite <- {rs_six_product} at {rs_result}",
        f"rewrite <- {rs_eight_product} at {rs_result}",
        f"exact {rs_result}",
    )
    residual_six_script = tuple(residual_six.commands)

    residual_four = LocalPowerScript(first_witness_index=1)
    residual_four.add(
        "intro x",
        "intro y",
        "intro htotal",
        "intro hx",
        "intro hy",
        f"have rf_seeds : ({seed_two_two}) /\\ ({seed_two_seven})",
        "apply pow_two_seed_bundle_from_total",
        "exact htotal",
        "cases rf_seeds",
    )
    rf_p2_four_r, rf_p2_four = residual_four.total("rf_p2_four", "2", "4")
    rf_p4_two_r, rf_p4_two = residual_four.total("rf_p4_two", "4", "2")
    rf_two_bridge = residual_four.iterated_equality(
        "rf_two_bridge",
        "2",
        "2",
        "2",
        "4",
        "4",
        rf_p4_two_r,
        rf_p2_four_r,
        "rf_seeds_left",
        rf_p4_two,
        rf_p2_four,
    )
    residual_four.add(
        "have rf_two_bound : "
        f"{witness_le(rf_p2_four_r, rf_p4_two_r, tag='hj32_rf_two_bound')}",
        f"rewrite {rf_two_bridge}",
        f"specialize le_refl {rf_p2_four_r}",
        "exact le_refl",
    )
    rf_p3_four_r, rf_p3_four = residual_four.total("rf_p3_four", "3", "4")
    rf_p4_four_r, rf_p4_four = residual_four.total("rf_p4_four", "4", "4")
    residual_four.add(
        "have rf_base : " + witness_le("3", "4", tag="hj32_rf_base"),
        "exists 1",
        "norm_num",
    )
    rf_three_bound = residual_four.base_bound(
        "rf_three_bound",
        "3",
        "4",
        "4",
        rf_p3_four_r,
        rf_p4_four_r,
        "rf_base",
        rf_p3_four,
        rf_p4_four,
    )
    rf_six_product = residual_four.product_equality(
        "rf_six_product",
        "2",
        "3",
        "6",
        "4",
        rf_p2_four_r,
        rf_p3_four_r,
        "x",
        rf_p2_four,
        rf_p3_four,
        "hx",
    )
    rf_six_power = residual_four.add_equality(
        "rf_six_power",
        "4",
        "2",
        "4",
        "6",
        rf_p4_two_r,
        rf_p4_four_r,
        "y",
        rf_p4_two,
        rf_p4_four,
        "hy",
    )
    rf_result = residual_four.product_bound(
        "rf_result",
        rf_p2_four_r,
        rf_p4_two_r,
        rf_p3_four_r,
        rf_p4_four_r,
        "rf_two_bound",
        rf_three_bound,
    )
    residual_four.add(
        f"rewrite <- {rf_six_product} at {rf_result}",
        f"rewrite <- {rf_six_power} at {rf_result}",
        f"exact {rf_result}",
    )
    residual_four_script = tuple(residual_four.commands)

    three_plus_total = power_total_relation(tag="hj32_three_plus")
    three_plus_left = _power_terms(
        "3", "5 * m + 1", "x", tag="hj32_three_plus_left"
    )
    three_plus_right = _power_terms(
        "4", "4 * m + 1", "y", tag="hj32_three_plus_right"
    )
    three_plus_result = witness_le(
        "x", "y", tag="hj32_three_plus_result"
    )

    three_plus = LocalPowerScript(first_witness_index=1)
    three_plus.add(
        "intro m",
        "intro x",
        "intro y",
        "intro htotal",
        "intro hx",
        "intro hy",
    )
    tp_p3_five_r, tp_p3_five = three_plus.total("tp_p3_five", "3", "5")
    tp_p4_four_r, tp_p4_four = three_plus.total("tp_p4_four", "4", "4")
    three_plus.add(
        "have tp_seed : "
        + witness_le(tp_p3_five_r, tp_p4_four_r, tag="hj32_tp_seed"),
        f"specialize pow_three_five_le_pow_four_four_from_total {tp_p3_five_r}",
        f"specialize pow_three_five_le_pow_four_four_from_total {tp_p4_four_r}",
        "apply pow_three_five_le_pow_four_four_from_total",
        "exact htotal",
        f"exact {tp_p3_five}",
        f"exact {tp_p4_four}",
    )
    tp_p3_block_r, tp_p3_block = three_plus.total(
        "tp_p3_block", "3", "5 * m"
    )
    tp_p4_block_r, tp_p4_block = three_plus.total(
        "tp_p4_block", "4", "4 * m"
    )
    tp_block_bound = three_plus.block_bound(
        "tp_block_bound",
        "3",
        "4",
        "5",
        "4",
        "m",
        tp_p3_five_r,
        tp_p4_four_r,
        tp_p3_block_r,
        tp_p4_block_r,
        tp_p3_five,
        tp_p4_four,
        "tp_seed",
        tp_p3_block,
        tp_p4_block,
    )
    tp_p3_one_r, tp_p3_one = three_plus.total("tp_p3_one", "3", "1")
    tp_p4_one_r, tp_p4_one = three_plus.total("tp_p4_one", "4", "1")
    three_plus.add(
        "have tp_base : " + witness_le("3", "4", tag="hj32_tp_base"),
        "exists 1",
        "norm_num",
    )
    tp_one_bound = three_plus.base_bound(
        "tp_one_bound",
        "3",
        "4",
        "1",
        tp_p3_one_r,
        tp_p4_one_r,
        "tp_base",
        tp_p3_one,
        tp_p4_one,
    )
    tp_left_product = three_plus.add_equality(
        "tp_left_product",
        "3",
        "5 * m",
        "1",
        "5 * m + 1",
        tp_p3_block_r,
        tp_p3_one_r,
        "x",
        tp_p3_block,
        tp_p3_one,
        "hx",
        ("refl",),
    )
    tp_right_product = three_plus.add_equality(
        "tp_right_product",
        "4",
        "4 * m",
        "1",
        "4 * m + 1",
        tp_p4_block_r,
        tp_p4_one_r,
        "y",
        tp_p4_block,
        tp_p4_one,
        "hy",
        ("refl",),
    )
    tp_result = three_plus.product_bound(
        "tp_result",
        tp_p3_block_r,
        tp_p4_block_r,
        tp_p3_one_r,
        tp_p4_one_r,
        tp_block_bound,
        tp_one_bound,
    )
    three_plus.add(
        f"rewrite <- {tp_left_product} at {tp_result}",
        f"rewrite <- {tp_right_product} at {tp_result}",
        f"exact {tp_result}",
    )
    three_plus_script = tuple(three_plus.commands)

    two_double_total = power_total_relation(tag="hj32_two_double")
    two_double_left = _power_terms(
        "2", "2 * k", "x", tag="hj32_two_double_left"
    )
    two_double_right = _power_terms(
        "4", "k", "y", tag="hj32_two_double_right"
    )
    two_double_script = (
        "intro k",
        "intro x",
        "intro y",
        "intro htotal",
        "intro hx",
        "intro hy",
        f"have td_seeds : ({seed_two_two}) /\\ ({seed_two_seven})",
        "apply pow_two_seed_bundle_from_total",
        "exact htotal",
        "cases td_seeds",
        "have td_bridge : y = x",
        "specialize pow_mul_exp_from_total 2",
        "specialize pow_mul_exp_from_total 2",
        "specialize pow_mul_exp_from_total k",
        "specialize pow_mul_exp_from_total (2 * k)",
        "specialize pow_mul_exp_from_total 4",
        "specialize pow_mul_exp_from_total y",
        "specialize pow_mul_exp_from_total x",
        "apply pow_mul_exp_from_total",
        "exact htotal",
        "refl",
        "exact td_seeds_left",
        "exact hy",
        "exact hx",
        "symm",
        "exact td_bridge",
    )

    two_odd_total = power_total_relation(tag="hj32_two_odd")
    two_odd_left = _power_terms(
        "2", "2 * k + 1", "x", tag="hj32_two_odd_left"
    )
    two_odd_right = _power_terms(
        "4", "k + 1", "y", tag="hj32_two_odd_right"
    )
    two_odd_result = witness_le("x", "y", tag="hj32_two_odd_result")
    two_odd = LocalPowerScript(first_witness_index=1)
    two_odd.add(
        "intro k",
        "intro x",
        "intro y",
        "intro htotal",
        "intro hx",
        "intro hy",
    )
    to_p2_even_r, to_p2_even = two_odd.total("to_p2_even", "2", "2 * k")
    to_p2_one_r, to_p2_one = two_odd.total("to_p2_one", "2", "1")
    to_p4_even_r, to_p4_even = two_odd.total("to_p4_even", "4", "k")
    to_p4_one_r, to_p4_one = two_odd.total("to_p4_one", "4", "1")
    two_odd.add(
        "have to_even_eq : " + f"{to_p2_even_r} = {to_p4_even_r}",
        f"specialize pow_two_double_eq_pow_four_from_total k",
        f"specialize pow_two_double_eq_pow_four_from_total {to_p2_even_r}",
        f"specialize pow_two_double_eq_pow_four_from_total {to_p4_even_r}",
        "apply pow_two_double_eq_pow_four_from_total",
        "exact htotal",
        f"exact {to_p2_even}",
        f"exact {to_p4_even}",
        "have to_even_bound : "
        + witness_le(
            to_p2_even_r, to_p4_even_r, tag="hj32_to_even_bound"
        ),
        "rewrite to_even_eq",
        f"specialize le_refl {to_p4_even_r}",
        "exact le_refl",
        "have to_base : " + witness_le("2", "4", tag="hj32_to_base"),
        "exists 2",
        "norm_num",
    )
    to_one_bound = two_odd.base_bound(
        "to_one_bound",
        "2",
        "4",
        "1",
        to_p2_one_r,
        to_p4_one_r,
        "to_base",
        to_p2_one,
        to_p4_one,
    )
    to_left_product = two_odd.add_equality(
        "to_left_product",
        "2",
        "2 * k",
        "1",
        "2 * k + 1",
        to_p2_even_r,
        to_p2_one_r,
        "x",
        to_p2_even,
        to_p2_one,
        "hx",
        ("refl",),
    )
    to_right_product = two_odd.add_equality(
        "to_right_product",
        "4",
        "k",
        "1",
        "k + 1",
        to_p4_even_r,
        to_p4_one_r,
        "y",
        to_p4_even,
        to_p4_one,
        "hy",
        ("refl",),
    )
    to_result = two_odd.product_bound(
        "to_result",
        to_p2_even_r,
        to_p4_even_r,
        to_p2_one_r,
        to_p4_one_r,
        "to_even_bound",
        to_one_bound,
    )
    two_odd.add(
        f"rewrite <- {to_left_product} at {to_result}",
        f"rewrite <- {to_right_product} at {to_result}",
        f"exact {to_result}",
    )
    two_odd_script = tuple(two_odd.commands)

    eleven_block_total = power_total_relation(tag="hj32_eleven_block")
    eleven_block_left = _power_terms(
        "11", "2 * m", "x", tag="hj32_eleven_block_left"
    )
    eleven_block_right = _power_terms(
        "2", "7 * m", "y", tag="hj32_eleven_block_right"
    )
    eleven_block_result = witness_le(
        "x", "y", tag="hj32_eleven_block_result"
    )
    eleven_block = LocalPowerScript(first_witness_index=1)
    eleven_block.add(
        "intro m",
        "intro x",
        "intro y",
        "intro htotal",
        "intro hx",
        "intro hy",
    )
    eb_p11_two_r, eb_p11_two = eleven_block.total("eb_p11_two", "11", "2")
    eb_p2_seven_r, eb_p2_seven = eleven_block.total("eb_p2_seven", "2", "7")
    eleven_block.add(
        "have eb_seed : "
        + witness_le(eb_p11_two_r, eb_p2_seven_r, tag="hj32_eb_seed"),
        f"specialize pow_eleven_two_le_pow_two_seven_from_total {eb_p11_two_r}",
        f"specialize pow_eleven_two_le_pow_two_seven_from_total {eb_p2_seven_r}",
        "apply pow_eleven_two_le_pow_two_seven_from_total",
        "exact htotal",
        f"exact {eb_p11_two}",
        f"exact {eb_p2_seven}",
    )
    eb_bound = eleven_block.block_bound(
        "eb_bound",
        "11",
        "2",
        "2",
        "7",
        "m",
        eb_p11_two_r,
        eb_p2_seven_r,
        "x",
        "y",
        eb_p11_two,
        eb_p2_seven,
        "eb_seed",
        "hx",
        "hy",
    )
    eleven_block.add(f"exact {eb_bound}")
    eleven_block_script = tuple(eleven_block.commands)

    eleven_even_total = power_total_relation(tag="hj32_eleven_even")
    eleven_even_parity = "7 * m = 2 * k"
    eleven_even_left = _power_terms(
        "11", "2 * m", "x", tag="hj32_eleven_even_left"
    )
    eleven_even_right = _power_terms(
        "4", "k", "y", tag="hj32_eleven_even_right"
    )
    eleven_even_result = witness_le("x", "y", tag="hj32_eleven_even_result")
    eleven_even = LocalPowerScript(first_witness_index=1)
    eleven_even.add(
        "intro m",
        "intro k",
        "intro x",
        "intro y",
        "intro htotal",
        "intro hparity",
        "intro hx",
        "intro hy",
    )
    ee_p2_r, ee_p2 = eleven_even.total("ee_p2", "2", "7 * m")
    eleven_even.add(
        "have ee_block : "
        + witness_le("x", ee_p2_r, tag="hj32_ee_block"),
        "specialize pow_eleven_double_block_le_pow_two_seven_block_from_total m",
        "specialize "
        f"pow_eleven_double_block_le_pow_two_seven_block_from_total x",
        "specialize "
        f"pow_eleven_double_block_le_pow_two_seven_block_from_total {ee_p2_r}",
        "apply pow_eleven_double_block_le_pow_two_seven_block_from_total",
        "exact htotal",
        "exact hx",
        f"exact {ee_p2}",
        "have ee_parity_power : "
        + _power_terms("2", "2 * k", ee_p2_r, tag="hj32_ee_parity_power"),
        "rewrite <- hparity",
        "rewrite <- hparity",
        "rewrite <- hparity",
        "rewrite <- hparity",
        f"exact {ee_p2}",
        f"have ee_eq : {ee_p2_r} = y",
        "specialize pow_two_double_eq_pow_four_from_total k",
        f"specialize pow_two_double_eq_pow_four_from_total {ee_p2_r}",
        "specialize pow_two_double_eq_pow_four_from_total y",
        "apply pow_two_double_eq_pow_four_from_total",
        "exact htotal",
        "exact ee_parity_power",
        "exact hy",
        "rewrite ee_eq at ee_block",
        "exact ee_block",
    )
    eleven_even_script = tuple(eleven_even.commands)

    eleven_odd_total = power_total_relation(tag="hj32_eleven_odd")
    eleven_odd_parity = "7 * m = 2 * k + 1"
    eleven_odd_left = _power_terms(
        "11", "2 * m", "x", tag="hj32_eleven_odd_left"
    )
    eleven_odd_right = _power_terms(
        "4", "k + 1", "y", tag="hj32_eleven_odd_right"
    )
    eleven_odd_result = witness_le("x", "y", tag="hj32_eleven_odd_result")
    eleven_odd = LocalPowerScript(first_witness_index=1)
    eleven_odd.add(
        "intro m",
        "intro k",
        "intro x",
        "intro y",
        "intro htotal",
        "intro hparity",
        "intro hx",
        "intro hy",
    )
    eo_p2_r, eo_p2 = eleven_odd.total("eo_p2", "2", "7 * m")
    eleven_odd.add(
        "have eo_block : "
        + witness_le("x", eo_p2_r, tag="hj32_eo_block"),
        "specialize pow_eleven_double_block_le_pow_two_seven_block_from_total m",
        "specialize "
        f"pow_eleven_double_block_le_pow_two_seven_block_from_total x",
        "specialize "
        f"pow_eleven_double_block_le_pow_two_seven_block_from_total {eo_p2_r}",
        "apply pow_eleven_double_block_le_pow_two_seven_block_from_total",
        "exact htotal",
        "exact hx",
        f"exact {eo_p2}",
        "have eo_parity_power : "
        + _power_terms(
            "2", "2 * k + 1", eo_p2_r, tag="hj32_eo_parity_power"
        ),
        "rewrite <- hparity",
        "rewrite <- hparity",
        "rewrite <- hparity",
        "rewrite <- hparity",
        f"exact {eo_p2}",
        "have eo_bound : "
        + witness_le(eo_p2_r, "y", tag="hj32_eo_bound"),
        "specialize pow_two_successor_double_le_pow_four_successor_from_total k",
        "specialize "
        f"pow_two_successor_double_le_pow_four_successor_from_total {eo_p2_r}",
        "specialize pow_two_successor_double_le_pow_four_successor_from_total y",
        "apply pow_two_successor_double_le_pow_four_successor_from_total",
        "exact htotal",
        "exact eo_parity_power",
        "exact hy",
        "specialize le_trans x",
        f"specialize le_trans {eo_p2_r}",
        "specialize le_trans y",
        "apply le_trans",
        "exact eo_block",
        "exact eo_bound",
    )
    eleven_odd_script = tuple(eleven_odd.commands)

    six_block_total = power_total_relation(tag="hj32_six_block")
    six_block_left = _power_terms(
        "6", "10 * m", "x", tag="hj32_six_block_left"
    )
    six_block_right = _power_terms(
        "4", "13 * m", "y", tag="hj32_six_block_right"
    )
    six_block_result = witness_le("x", "y", tag="hj32_six_block_result")
    six_block = LocalPowerScript(first_witness_index=1)
    six_block.add(
        "intro m",
        "intro x",
        "intro y",
        "intro htotal",
        "intro hx",
        "intro hy",
    )
    sb_p6_ten_r, sb_p6_ten = six_block.total("sb_p6_ten", "6", "10")
    sb_p4_thirteen_r, sb_p4_thirteen = six_block.total(
        "sb_p4_thirteen", "4", "13"
    )
    six_block.add(
        "have sb_seed : "
        + witness_le(sb_p6_ten_r, sb_p4_thirteen_r, tag="hj32_sb_seed"),
        f"specialize pow_six_ten_le_pow_four_thirteen_from_total {sb_p6_ten_r}",
        f"specialize pow_six_ten_le_pow_four_thirteen_from_total {sb_p4_thirteen_r}",
        "apply pow_six_ten_le_pow_four_thirteen_from_total",
        "exact htotal",
        f"exact {sb_p6_ten}",
        f"exact {sb_p4_thirteen}",
    )
    sb_bound = six_block.block_bound(
        "sb_bound",
        "6",
        "4",
        "10",
        "13",
        "m",
        sb_p6_ten_r,
        sb_p4_thirteen_r,
        "x",
        "y",
        sb_p6_ten,
        sb_p4_thirteen,
        "sb_seed",
        "hx",
        "hy",
    )
    six_block.add(f"exact {sb_bound}")
    six_block_script = tuple(six_block.commands)

    thirty_six_total = power_total_relation(tag="hj32_thirty_six_block")
    thirty_six_left = _power_terms(
        "36", "2 * m", "x", tag="hj32_thirty_six_left"
    )
    thirty_six_right = _power_terms(
        "6", "4 * m", "y", tag="hj32_thirty_six_right"
    )
    thirty_six_script = (
        "intro m",
        "intro x",
        "intro y",
        "intro htotal",
        "intro hx",
        "intro hy",
        "have ts_seed_any : exists ts_value. ("
        + _power_terms("6", "2", "ts_value", tag="hj32_ts_seed_any")
        + ")",
        "specialize htotal 6",
        "specialize htotal 2",
        "exact htotal",
        "cases ts_seed_any",
        "have ts_value : x1 = 36",
        "have ts_square : x1 = 6 * 6",
        "specialize pow_two 6",
        "specialize pow_two 2",
        "specialize pow_two x1",
        "apply pow_two",
        "refl",
        "exact ts_seed_any_witness",
        "trans 6 * 6",
        "exact ts_square",
        "norm_num",
        "have ts_seed : "
        + _power_terms("6", "2", "36", tag="hj32_ts_seed"),
        "rewrite <- ts_value",
        "rewrite <- ts_value",
        "exact ts_seed_any_witness",
        "have ts_exponent : 4 * m = 2 * (2 * m)",
        "have ts_four : 4 = 2 * 2",
        "norm_num",
        "rewrite ts_four",
        "specialize mul_assoc 2",
        "specialize mul_assoc 2",
        "specialize mul_assoc m",
        "apply mul_assoc",
        "specialize pow_mul_exp_from_total 6",
        "specialize pow_mul_exp_from_total 2",
        "specialize pow_mul_exp_from_total (2 * m)",
        "specialize pow_mul_exp_from_total (4 * m)",
        "specialize pow_mul_exp_from_total 36",
        "specialize pow_mul_exp_from_total x",
        "specialize pow_mul_exp_from_total y",
        "apply pow_mul_exp_from_total",
        "exact htotal",
        "exact ts_exponent",
        "exact ts_seed",
        "exact hx",
        "exact hy",
    )

    def begin_h_root(root: int) -> tuple[LocalPowerScript, str]:
        upper_exponent = f"2 * {root + 1}"
        script = LocalPowerScript(first_witness_index=0)
        script.add(
            "intro e",
            "intro h",
            "intro u",
            "intro htotal",
            "intro hceiling",
            "intro hh",
            "intro hu",
            "have hh_route : "
            + _power_terms(
                str(root + 1),
                upper_exponent,
                "h",
                tag=f"hj32_h_{root}_route",
            ),
            f"have hh_base : {root} + 1 = {root + 1}",
            "norm_num",
            f"have hh_exponent : 2 * {root} + 2 = {upper_exponent}",
            "norm_num",
            "rewrite <- hh_exponent",
            "rewrite <- hh_exponent",
            "rewrite <- hh_exponent",
            "rewrite <- hh_exponent",
            "rewrite <- hh_base",
            "rewrite <- hh_base",
            "exact hh",
        )
        return script, upper_exponent

    def finish_h_root(
        script: LocalPowerScript,
        *,
        root: int,
        budget_result: str,
        budget_power: str,
        h_to_budget: str,
    ) -> None:
        budget = root_budget_terms[root]
        script.add(
            "have hscaled : " + root_budget_results[root],
            f"apply bertrand_scaled_budget_root_{root}",
            "have hbudget_exponent : "
            + witness_le(
                budget, "e", tag=f"hj32_h_{root}_budget_exponent"
            ),
            f"specialize ceil_div_six_budget_of_scaled_le ({root} * {root})",
            f"specialize ceil_div_six_budget_of_scaled_le ({budget})",
            "specialize ceil_div_six_budget_of_scaled_le e",
            "apply ceil_div_six_budget_of_scaled_le",
            "exact hceiling",
            "exact hscaled",
        )
        growth = script.exponent_bound(
            f"h{root}_budget_growth",
            "4",
            budget,
            "e",
            budget_result,
            "u",
            "hbudget_exponent",
            budget_power,
            "hu",
            "3",
        )
        result = script.trans_bound(
            f"h{root}_result",
            "h",
            budget_result,
            "u",
            h_to_budget,
            growth,
        )
        script.add(f"exact {result}")

    def build_h_root_32_thin() -> tuple[str, ...]:
        root = 32
        script, exponent = begin_h_root(root)
        p3_exp_r, p3_exp = script.total("h32t_p3_exp", "3", exponent)
        p11_exp_r, p11_exp = script.total("h32t_p11_exp", "11", exponent)
        h_product = script.product_equality(
            "h32t_product",
            "3",
            "11",
            "33",
            exponent,
            p3_exp_r,
            p11_exp_r,
            "h",
            p3_exp,
            p11_exp,
            "hh_route",
        )
        script.add(
            "have h32t_three_power : "
            + _power_terms(
                "3", "5 * 13 + 1", p3_exp_r, tag="hj32_h32t_three_power"
            ),
            "have h32t_three_exponent : 2 * 33 = 5 * 13 + 1",
            "norm_num",
            "rewrite <- h32t_three_exponent",
            "rewrite <- h32t_three_exponent",
            "rewrite <- h32t_three_exponent",
            "rewrite <- h32t_three_exponent",
            f"exact {p3_exp}",
        )
        p4_head_r, p4_head = script.total(
            "h32t_p4_head", "4", "4 * 13 + 1"
        )
        script.add(
            "have h32t_three_bound : "
            + witness_le(p3_exp_r, p4_head_r, tag="hj32_h32t_three_bound"),
            "specialize "
            "pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total 13",
            "specialize "
            f"pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total {p3_exp_r}",
            "specialize "
            f"pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total {p4_head_r}",
            "apply "
            "pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total",
            "exact htotal",
            "exact h32t_three_power",
            f"exact {p4_head}",
        )
        odd_half = "14 * 8 + 3"
        p4_tail_r, p4_tail = script.total("h32t_p4_tail", "4", "4 * 29")
        script.add(
            "have h32t_tail_power : "
            + _power_terms(
                "4", f"({odd_half}) + 1", p4_tail_r, tag="hj32_h32t_tail_power"
            ),
            f"have h32t_tail_exponent : ({odd_half}) + 1 = 4 * 29",
            "norm_num",
            "rewrite h32t_tail_exponent",
            "rewrite h32t_tail_exponent",
            "rewrite h32t_tail_exponent",
            "rewrite h32t_tail_exponent",
            f"exact {p4_tail}",
            f"have h32t_parity : 7 * 33 = 2 * ({odd_half}) + 1",
            "have h32t_parity_left : 7 * 33 = 28 * 8 + 7",
            "have h32t_root : 33 = 4 * 8 + 1",
            "norm_num",
            "rewrite h32t_root",
            "have h32t_left_distrib : 7 * (4 * 8 + 1) = "
            "7 * (4 * 8) + 7 * 1",
            "specialize mul_add 7",
            "specialize mul_add (4 * 8)",
            "specialize mul_add 1",
            "apply mul_add",
            "rewrite h32t_left_distrib",
            "have h32t_left_assoc : 7 * (4 * 8) = (7 * 4) * 8",
            "symm",
            "specialize mul_assoc 7",
            "specialize mul_assoc 4",
            "specialize mul_assoc 8",
            "apply mul_assoc",
            "rewrite h32t_left_assoc",
            "have h32t_twenty_eight : 7 * 4 = 28",
            "norm_num",
            "rewrite h32t_twenty_eight",
            "have h32t_seven : 7 * 1 = 7",
            "norm_num",
            "rewrite h32t_seven",
            "refl",
            f"have h32t_parity_right : 2 * ({odd_half}) + 1 = 28 * 8 + 7",
            "have h32t_right_distrib : 2 * (14 * 8 + 3) = "
            "2 * (14 * 8) + 2 * 3",
            "specialize mul_add 2",
            "specialize mul_add (14 * 8)",
            "specialize mul_add 3",
            "apply mul_add",
            "rewrite h32t_right_distrib",
            "have h32t_right_assoc : 2 * (14 * 8) = (2 * 14) * 8",
            "symm",
            "specialize mul_assoc 2",
            "specialize mul_assoc 14",
            "specialize mul_assoc 8",
            "apply mul_assoc",
            "rewrite h32t_right_assoc",
            "have h32t_right_twenty_eight : 2 * 14 = 28",
            "norm_num",
            "rewrite h32t_right_twenty_eight",
            "have h32t_right_assoc_add : (28 * 8 + 2 * 3) + 1 = "
            "28 * 8 + (2 * 3 + 1)",
            "specialize add_assoc (28 * 8)",
            "specialize add_assoc (2 * 3)",
            "specialize add_assoc 1",
            "apply add_assoc",
            "rewrite h32t_right_assoc_add",
            "have h32t_right_seven : 2 * 3 + 1 = 7",
            "norm_num",
            "rewrite h32t_right_seven",
            "refl",
            "trans 28 * 8 + 7",
            "exact h32t_parity_left",
            "symm",
            "exact h32t_parity_right",
            "have h32t_eleven_bound : "
            + witness_le(p11_exp_r, p4_tail_r, tag="hj32_h32t_eleven_bound"),
            "specialize pow_eleven_double_block_le_pow_four_odd_from_total 33",
            f"specialize pow_eleven_double_block_le_pow_four_odd_from_total ({odd_half})",
            f"specialize pow_eleven_double_block_le_pow_four_odd_from_total {p11_exp_r}",
            f"specialize pow_eleven_double_block_le_pow_four_odd_from_total {p4_tail_r}",
            "apply pow_eleven_double_block_le_pow_four_odd_from_total",
            "exact htotal",
            "exact h32t_parity",
            f"exact {p11_exp}",
            "exact h32t_tail_power",
        )
        total_bound = script.product_bound(
            "h32t_total_bound",
            p3_exp_r,
            p4_head_r,
            p11_exp_r,
            p4_tail_r,
            "h32t_three_bound",
            "h32t_eleven_bound",
        )
        budget = root_budget_terms[root]
        p4_budget_r, p4_budget = script.total("h32t_p4_budget", "4", budget)
        budget_product = script.add_equality(
            "h32t_budget_product",
            "4",
            "4 * 13 + 1",
            "4 * 29",
            budget,
            p4_head_r,
            p4_tail_r,
            p4_budget_r,
            p4_head,
            p4_tail,
            p4_budget,
            ("refl",),
        )
        script.add(
            f"rewrite <- {h_product} at {total_bound}",
            f"rewrite <- {budget_product} at {total_bound}",
        )
        finish_h_root(
            script,
            root=root,
            budget_result=p4_budget_r,
            budget_power=p4_budget,
            h_to_budget=total_bound,
        )
        return tuple(script.commands)

    h_root_dependencies[32] = (
        "bertrand_scaled_budget_root_32",
        "ceil_div_six_budget_of_scaled_le",
        "pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total",
        "pow_eleven_double_block_le_pow_four_odd_from_total",
        "pow_mul_base",
        "pow_add",
        "pow_exponent_monotone_from_total",
        "mul_le_mul",
        "le_trans",
        "mul_add",
        "mul_assoc",
        "add_assoc",
    )
    h_root_scripts[32] = build_h_root_32_thin()

    def append_odd_four_block_parity(
        script: LocalPowerScript, *, prefix: str, block: int
    ) -> str:
        root = 4 * block + 1
        half = f"14 * {block} + 3"
        name = f"{prefix}_parity"
        script.add(
            f"have {name} : 7 * {root} = 2 * ({half}) + 1",
            f"have {prefix}_left : 7 * {root} = 28 * {block} + 7",
            f"have {prefix}_root : {root} = 4 * {block} + 1",
            "norm_num",
            f"rewrite {prefix}_root",
            f"have {prefix}_left_distrib : 7 * (4 * {block} + 1) = "
            f"7 * (4 * {block}) + 7 * 1",
            "specialize mul_add 7",
            f"specialize mul_add (4 * {block})",
            "specialize mul_add 1",
            "apply mul_add",
            f"rewrite {prefix}_left_distrib",
            f"have {prefix}_left_assoc : 7 * (4 * {block}) = "
            f"(7 * 4) * {block}",
            "symm",
            "specialize mul_assoc 7",
            "specialize mul_assoc 4",
            f"specialize mul_assoc {block}",
            "apply mul_assoc",
            f"rewrite {prefix}_left_assoc",
            f"have {prefix}_twenty_eight : 7 * 4 = 28",
            "norm_num",
            f"rewrite {prefix}_twenty_eight",
            f"have {prefix}_seven : 7 * 1 = 7",
            "norm_num",
            f"rewrite {prefix}_seven",
            "refl",
            f"have {prefix}_right : 2 * ({half}) + 1 = "
            f"28 * {block} + 7",
            f"have {prefix}_right_distrib : 2 * (14 * {block} + 3) = "
            f"2 * (14 * {block}) + 2 * 3",
            "specialize mul_add 2",
            f"specialize mul_add (14 * {block})",
            "specialize mul_add 3",
            "apply mul_add",
            f"rewrite {prefix}_right_distrib",
            f"have {prefix}_right_assoc : 2 * (14 * {block}) = "
            f"(2 * 14) * {block}",
            "symm",
            "specialize mul_assoc 2",
            "specialize mul_assoc 14",
            f"specialize mul_assoc {block}",
            "apply mul_assoc",
            f"rewrite {prefix}_right_assoc",
            f"have {prefix}_right_twenty_eight : 2 * 14 = 28",
            "norm_num",
            f"rewrite {prefix}_right_twenty_eight",
            f"have {prefix}_right_add : (28 * {block} + 2 * 3) + 1 = "
            f"28 * {block} + (2 * 3 + 1)",
            f"specialize add_assoc (28 * {block})",
            "specialize add_assoc (2 * 3)",
            "specialize add_assoc 1",
            "apply add_assoc",
            f"rewrite {prefix}_right_add",
            f"have {prefix}_right_seven : 2 * 3 + 1 = 7",
            "norm_num",
            f"rewrite {prefix}_right_seven",
            "refl",
            f"trans 28 * {block} + 7",
            f"exact {prefix}_left",
            "symm",
            f"exact {prefix}_right",
        )
        return name

    def build_h_root_44_thin(root: int) -> tuple[str, ...]:
        script, exponent = begin_h_root(root)
        p44_r, p44 = script.total(f"h{root}t_p44", "44", exponent)
        script.add(
            f"have h{root}t_base : "
            + witness_le(
                str(root + 1), "44", tag=f"hj32_h{root}t_base"
            ),
            f"exists {44 - (root + 1)}",
            "norm_num",
        )
        h_to_44 = script.base_bound(
            f"h{root}t_to_44",
            str(root + 1),
            "44",
            exponent,
            "h",
            p44_r,
            f"h{root}t_base",
            "hh_route",
            p44,
        )
        p4_exp_r, p4_exp = script.total(f"h{root}t_p4_exp", "4", exponent)
        p11_exp_r, p11_exp = script.total(f"h{root}t_p11_exp", "11", exponent)
        p44_product = script.product_equality(
            f"h{root}t_p44_product",
            "4",
            "11",
            "44",
            exponent,
            p4_exp_r,
            p11_exp_r,
            p44_r,
            p4_exp,
            p11_exp,
            p44,
        )
        tail_budget = "2 * (5 * 13)" if root == 36 else "7 * 19"
        p4_tail_r, p4_tail = script.total(
            f"h{root}t_p4_tail", "4", tail_budget
        )
        if root == 36:
            odd_half = "14 * 9 + 3"
            script.add(
                "have h36t_tail_power : "
                + _power_terms(
                    "4",
                    f"({odd_half}) + 1",
                    p4_tail_r,
                    tag="hj32_h36t_tail_power",
                ),
                f"have h36t_tail_exponent : ({odd_half}) + 1 = {tail_budget}",
                "have h36t_tail_left : (14 * 9 + 3) + 1 = "
                "2 * (7 * 9 + 2)",
                "have h36t_tail_assoc : (14 * 9 + 3) + 1 = "
                "14 * 9 + (3 + 1)",
                "specialize add_assoc (14 * 9)",
                "specialize add_assoc 3",
                "specialize add_assoc 1",
                "apply add_assoc",
                "rewrite h36t_tail_assoc",
                "have h36t_four : 3 + 1 = 2 * 2",
                "norm_num",
                "rewrite h36t_four",
                "have h36t_fourteen : 14 = 2 * 7",
                "norm_num",
                "rewrite h36t_fourteen",
                "have h36t_assoc_mul : (2 * 7) * 9 = 2 * (7 * 9)",
                "specialize mul_assoc 2",
                "specialize mul_assoc 7",
                "specialize mul_assoc 9",
                "apply mul_assoc",
                "rewrite h36t_assoc_mul",
                "have h36t_factor : 2 * (7 * 9 + 2) = "
                "2 * (7 * 9) + 2 * 2",
                "specialize mul_add 2",
                "specialize mul_add (7 * 9)",
                "specialize mul_add 2",
                "apply mul_add",
                "rewrite <- h36t_factor",
                "refl",
                "have h36t_tail_right : 2 * (7 * 9 + 2) = 2 * (5 * 13)",
                "have h36t_inside : 7 * 9 + 2 = 5 * 13",
                "norm_num",
                "rewrite h36t_inside",
                "refl",
                "trans 2 * (7 * 9 + 2)",
                "exact h36t_tail_left",
                "exact h36t_tail_right",
                "rewrite h36t_tail_exponent",
                "rewrite h36t_tail_exponent",
                "rewrite h36t_tail_exponent",
                "rewrite h36t_tail_exponent",
                f"exact {p4_tail}",
            )
            parity = append_odd_four_block_parity(
                script, prefix="h36t", block=9
            )
            script.add(
                "have h36t_eleven_bound : "
                + witness_le(
                    p11_exp_r, p4_tail_r, tag="hj32_h36t_eleven_bound"
                ),
                "specialize pow_eleven_double_block_le_pow_four_odd_from_total 37",
                f"specialize pow_eleven_double_block_le_pow_four_odd_from_total ({odd_half})",
                f"specialize pow_eleven_double_block_le_pow_four_odd_from_total {p11_exp_r}",
                f"specialize pow_eleven_double_block_le_pow_four_odd_from_total {p4_tail_r}",
                "apply pow_eleven_double_block_le_pow_four_odd_from_total",
                "exact htotal",
                f"exact {parity}",
                f"exact {p11_exp}",
                "exact h36t_tail_power",
            )
            eleven_bound = "h36t_eleven_bound"
        else:
            script.add(
                "have h37t_parity : 7 * 38 = 2 * (7 * 19)",
                "have h37t_root : 38 = 2 * 19",
                "norm_num",
                "rewrite h37t_root",
                "trans (7 * 2) * 19",
                "symm",
                "specialize mul_assoc 7",
                "specialize mul_assoc 2",
                "specialize mul_assoc 19",
                "apply mul_assoc",
                "trans (2 * 7) * 19",
                "congr",
                "specialize mul_comm 7",
                "specialize mul_comm 2",
                "apply mul_comm",
                "refl",
                "specialize mul_assoc 2",
                "specialize mul_assoc 7",
                "specialize mul_assoc 19",
                "apply mul_assoc",
                "have h37t_eleven_bound : "
                + witness_le(
                    p11_exp_r, p4_tail_r, tag="hj32_h37t_eleven_bound"
                ),
                "specialize pow_eleven_double_block_le_pow_four_even_from_total 38",
                "specialize pow_eleven_double_block_le_pow_four_even_from_total (7 * 19)",
                f"specialize pow_eleven_double_block_le_pow_four_even_from_total {p11_exp_r}",
                f"specialize pow_eleven_double_block_le_pow_four_even_from_total {p4_tail_r}",
                "apply pow_eleven_double_block_le_pow_four_even_from_total",
                "exact htotal",
                "exact h37t_parity",
                f"exact {p11_exp}",
                f"exact {p4_tail}",
            )
            eleven_bound = "h37t_eleven_bound"
        script.add(
            f"have h{root}t_four_refl : "
            + witness_le(
                p4_exp_r, p4_exp_r, tag=f"hj32_h{root}t_four_refl"
            ),
            f"specialize le_refl {p4_exp_r}",
            "exact le_refl",
        )
        product_bound = script.product_bound(
            f"h{root}t_product_bound",
            p4_exp_r,
            p4_exp_r,
            p11_exp_r,
            p4_tail_r,
            f"h{root}t_four_refl",
            eleven_bound,
        )
        budget = root_budget_terms[root]
        p4_budget_r, p4_budget = script.total(
            f"h{root}t_p4_budget", "4", budget
        )
        budget_product = script.add_equality(
            f"h{root}t_budget_product",
            "4",
            exponent,
            tail_budget,
            budget,
            p4_exp_r,
            p4_tail_r,
            p4_budget_r,
            p4_exp,
            p4_tail,
            p4_budget,
            ("refl",),
        )
        script.add(
            f"rewrite <- {p44_product} at {product_bound}",
            f"rewrite <- {budget_product} at {product_bound}",
        )
        h_to_budget = script.trans_bound(
            f"h{root}t_to_budget",
            "h",
            p44_r,
            p4_budget_r,
            h_to_44,
            product_bound,
        )
        finish_h_root(
            script,
            root=root,
            budget_result=p4_budget_r,
            budget_power=p4_budget,
            h_to_budget=h_to_budget,
        )
        return tuple(script.commands)

    h_root_dependencies[36] = (
        "bertrand_scaled_budget_root_36",
        "ceil_div_six_budget_of_scaled_le",
        "pow_eleven_double_block_le_pow_four_odd_from_total",
        "pow_mul_base",
        "pow_add",
        "pow_base_monotone",
        "pow_exponent_monotone_from_total",
        "mul_le_mul",
        "le_refl",
        "le_trans",
        "mul_add",
        "mul_assoc",
        "add_assoc",
    )
    h_root_dependencies[37] = (
        "bertrand_scaled_budget_root_37",
        "ceil_div_six_budget_of_scaled_le",
        "pow_eleven_double_block_le_pow_four_even_from_total",
        "pow_mul_base",
        "pow_add",
        "pow_base_monotone",
        "pow_exponent_monotone_from_total",
        "mul_le_mul",
        "le_refl",
        "le_trans",
        "mul_assoc",
        "mul_comm",
    )
    h_root_scripts[36] = build_h_root_44_thin(36)
    h_root_scripts[37] = build_h_root_44_thin(37)

    def build_h_root_six_thin(root: int) -> tuple[str, ...]:
        script, exponent = begin_h_root(root)
        block = root + 1
        p36_r, p36 = script.total(f"h{root}s_p36", "36", exponent)
        script.add(
            f"have h{root}s_base : "
            + witness_le(
                str(root + 1), "36", tag=f"hj32_h{root}s_base"
            ),
            f"exists {36 - (root + 1)}",
            "norm_num",
        )
        h_to_36 = script.base_bound(
            f"h{root}s_to_36",
            str(root + 1),
            "36",
            exponent,
            "h",
            p36_r,
            f"h{root}s_base",
            "hh_route",
            p36,
        )
        p6_total_r, p6_total = script.total(
            f"h{root}s_p6_total", "6", f"4 * {block}"
        )
        script.add(
            f"have h{root}s_conversion : {p36_r} = {p6_total_r}",
            "specialize "
            f"pow_thirty_six_double_block_eq_pow_six_four_block_from_total {block}",
            "specialize "
            f"pow_thirty_six_double_block_eq_pow_six_four_block_from_total {p36_r}",
            "specialize "
            f"pow_thirty_six_double_block_eq_pow_six_four_block_from_total {p6_total_r}",
            "apply pow_thirty_six_double_block_eq_pow_six_four_block_from_total",
            "exact htotal",
            f"exact {p36}",
            f"exact {p6_total}",
            f"rewrite h{root}s_conversion at h{root}s_to_36",
        )
        h_to_six = f"h{root}s_to_36"
        budget = root_budget_terms[root]
        main_multiplier = "13" if root == 33 else "14"
        main_target = budget if root == 34 else f"13 * {main_multiplier}"
        p6_main_r, p6_main = script.total(
            f"h{root}s_p6_main", "6", f"10 * {main_multiplier}"
        )
        p4_main_r, p4_main = script.total(
            f"h{root}s_p4_main", "4", main_target
        )
        script.add(
            f"have h{root}s_main_bound : "
            + witness_le(
                p6_main_r, p4_main_r, tag=f"hj32_h{root}s_main_bound"
            ),
            f"specialize pow_six_ten_block_le_pow_four_thirteen_block_from_total {main_multiplier}",
            "specialize "
            f"pow_six_ten_block_le_pow_four_thirteen_block_from_total {p6_main_r}",
            "specialize "
            f"pow_six_ten_block_le_pow_four_thirteen_block_from_total {p4_main_r}",
            "apply pow_six_ten_block_le_pow_four_thirteen_block_from_total",
            "exact htotal",
            f"exact {p6_main}",
            f"exact {p4_main}",
        )
        if root == 34:
            script.add(
                "have h34s_exponent : 4 * 35 = 10 * 14",
                "have h34s_thirty_five : 35 = 5 * 7",
                "norm_num",
                "rewrite h34s_thirty_five",
                "have h34s_left_assoc : 4 * (5 * 7) = (4 * 5) * 7",
                "symm",
                "specialize mul_assoc 4",
                "specialize mul_assoc 5",
                "specialize mul_assoc 7",
                "apply mul_assoc",
                "rewrite h34s_left_assoc",
                "have h34s_fourteen : 14 = 2 * 7",
                "norm_num",
                "rewrite h34s_fourteen",
                "have h34s_right_assoc : 10 * (2 * 7) = (10 * 2) * 7",
                "symm",
                "specialize mul_assoc 10",
                "specialize mul_assoc 2",
                "specialize mul_assoc 7",
                "apply mul_assoc",
                "rewrite h34s_right_assoc",
                "have h34s_right_twenty : 10 * 2 = 20",
                "norm_num",
                "rewrite h34s_right_twenty",
                "have h34s_left_twenty : 4 * 5 = 20",
                "norm_num",
                "rewrite h34s_left_twenty",
                "refl",
                "have h34s_main_power : "
                + _power_terms(
                    "6", "10 * 14", p6_total_r, tag="hj32_h34s_main_power"
                ),
                "rewrite <- h34s_exponent",
                "rewrite <- h34s_exponent",
                "rewrite <- h34s_exponent",
                "rewrite <- h34s_exponent",
                f"exact {p6_total}",
                "have h34s_direct_bound : "
                + witness_le(
                    p6_total_r, p4_main_r, tag="hj32_h34s_direct_bound"
                ),
                "specialize pow_six_ten_block_le_pow_four_thirteen_block_from_total 14",
                "specialize "
                f"pow_six_ten_block_le_pow_four_thirteen_block_from_total {p6_total_r}",
                "specialize "
                f"pow_six_ten_block_le_pow_four_thirteen_block_from_total {p4_main_r}",
                "apply pow_six_ten_block_le_pow_four_thirteen_block_from_total",
                "exact htotal",
                "exact h34s_main_power",
                f"exact {p4_main}",
            )
            h_to_budget = script.trans_bound(
                "h34s_to_budget",
                "h",
                p6_total_r,
                p4_main_r,
                h_to_six,
                "h34s_direct_bound",
            )
            finish_h_root(
                script,
                root=root,
                budget_result=p4_main_r,
                budget_power=p4_main,
                h_to_budget=h_to_budget,
            )
            return tuple(script.commands)

        residual_exponent = "6" if root == 33 else "4"
        residual_target = "8" if root == 33 else "6"
        p6_residual_r, p6_residual = script.total(
            f"h{root}s_p6_residual", "6", residual_exponent
        )
        p4_residual_r, p4_residual = script.total(
            f"h{root}s_p4_residual", "4", residual_target
        )
        residual_theorem = (
            "pow_six_six_le_pow_four_eight_from_total"
            if root == 33
            else "pow_six_four_le_pow_four_six_from_total"
        )
        script.add(
            f"have h{root}s_residual_bound : "
            + witness_le(
                p6_residual_r,
                p4_residual_r,
                tag=f"hj32_h{root}s_residual_bound",
            ),
            f"specialize {residual_theorem} {p6_residual_r}",
            f"specialize {residual_theorem} {p4_residual_r}",
            f"apply {residual_theorem}",
            "exact htotal",
            f"exact {p6_residual}",
            f"exact {p4_residual}",
        )
        if root == 33:
            script.add(
                "have h33s_exponent : 4 * 34 = 10 * 13 + 6",
                "have h33s_thirty_four : 34 = 13 + 21",
                "norm_num",
                "rewrite h33s_thirty_four",
                "have h33s_distrib_one : 4 * (13 + 21) = "
                "4 * 13 + 4 * 21",
                "specialize mul_add 4",
                "specialize mul_add 13",
                "specialize mul_add 21",
                "apply mul_add",
                "rewrite h33s_distrib_one",
                "have h33s_bridge : 4 * 21 = 6 * 14",
                "norm_num",
                "rewrite h33s_bridge",
                "have h33s_fourteen : 14 = 13 + 1",
                "norm_num",
                "rewrite h33s_fourteen",
                "have h33s_distrib_two : 6 * (13 + 1) = "
                "6 * 13 + 6 * 1",
                "specialize mul_add 6",
                "specialize mul_add 13",
                "specialize mul_add 1",
                "apply mul_add",
                "rewrite h33s_distrib_two",
                "have h33s_six : 6 * 1 = 6",
                "norm_num",
                "rewrite h33s_six",
                "have h33s_assoc : 4 * 13 + (6 * 13 + 6) = "
                "(4 * 13 + 6 * 13) + 6",
                "symm",
                "specialize add_assoc (4 * 13)",
                "specialize add_assoc (6 * 13)",
                "specialize add_assoc 6",
                "apply add_assoc",
                "rewrite h33s_assoc",
                "have h33s_factor : (4 + 6) * 13 = 4 * 13 + 6 * 13",
                "specialize add_mul 4",
                "specialize add_mul 6",
                "specialize add_mul 13",
                "apply add_mul",
                "rewrite <- h33s_factor",
                "have h33s_ten : 4 + 6 = 10",
                "norm_num",
                "rewrite h33s_ten",
                "refl",
            )
        else:
            script.add(
                "have h35s_exponent : 4 * 36 = 10 * 14 + 4",
                "have h35s_thirty_six : 36 = 5 * 7 + 1",
                "norm_num",
                "rewrite h35s_thirty_six",
                "have h35s_distrib : 4 * (5 * 7 + 1) = "
                "4 * (5 * 7) + 4 * 1",
                "specialize mul_add 4",
                "specialize mul_add (5 * 7)",
                "specialize mul_add 1",
                "apply mul_add",
                "rewrite h35s_distrib",
                "have h35s_left_assoc : 4 * (5 * 7) = (4 * 5) * 7",
                "symm",
                "specialize mul_assoc 4",
                "specialize mul_assoc 5",
                "specialize mul_assoc 7",
                "apply mul_assoc",
                "rewrite h35s_left_assoc",
                "have h35s_fourteen : 14 = 2 * 7",
                "norm_num",
                "rewrite h35s_fourteen",
                "have h35s_right_assoc : 10 * (2 * 7) = (10 * 2) * 7",
                "symm",
                "specialize mul_assoc 10",
                "specialize mul_assoc 2",
                "specialize mul_assoc 7",
                "apply mul_assoc",
                "rewrite h35s_right_assoc",
                "have h35s_right_twenty : 10 * 2 = 20",
                "norm_num",
                "rewrite h35s_right_twenty",
                "have h35s_twenty : 4 * 5 = 20",
                "norm_num",
                "rewrite h35s_twenty",
                "have h35s_four : 4 * 1 = 4",
                "norm_num",
                "rewrite h35s_four",
                "refl",
            )
        left_product = script.add_equality(
            f"h{root}s_left_product",
            "6",
            f"10 * {main_multiplier}",
            residual_exponent,
            f"4 * {block}",
            p6_main_r,
            p6_residual_r,
            p6_total_r,
            p6_main,
            p6_residual,
            p6_total,
            (f"exact h{root}s_exponent",),
        )
        p4_budget_r, p4_budget = script.total(
            f"h{root}s_p4_budget", "4", budget
        )
        right_product = script.add_equality(
            f"h{root}s_right_product",
            "4",
            f"13 * {main_multiplier}",
            residual_target,
            budget,
            p4_main_r,
            p4_residual_r,
            p4_budget_r,
            p4_main,
            p4_residual,
            p4_budget,
            ("refl",),
        )
        six_bound = script.product_bound(
            f"h{root}s_six_bound",
            p6_main_r,
            p4_main_r,
            p6_residual_r,
            p4_residual_r,
            f"h{root}s_main_bound",
            f"h{root}s_residual_bound",
        )
        script.add(
            f"rewrite <- {left_product} at {six_bound}",
            f"rewrite <- {right_product} at {six_bound}",
        )
        h_to_budget = script.trans_bound(
            f"h{root}s_to_budget",
            "h",
            p6_total_r,
            p4_budget_r,
            h_to_six,
            six_bound,
        )
        finish_h_root(
            script,
            root=root,
            budget_result=p4_budget_r,
            budget_power=p4_budget,
            h_to_budget=h_to_budget,
        )
        return tuple(script.commands)

    h_root_dependencies[33] = (
        "bertrand_scaled_budget_root_33",
        "ceil_div_six_budget_of_scaled_le",
        "pow_thirty_six_double_block_eq_pow_six_four_block_from_total",
        "pow_six_ten_block_le_pow_four_thirteen_block_from_total",
        "pow_six_six_le_pow_four_eight_from_total",
        "pow_add",
        "pow_base_monotone",
        "pow_exponent_monotone_from_total",
        "mul_le_mul",
        "le_trans",
        "mul_add",
        "add_mul",
        "add_assoc",
    )
    h_root_dependencies[34] = (
        "bertrand_scaled_budget_root_34",
        "ceil_div_six_budget_of_scaled_le",
        "pow_thirty_six_double_block_eq_pow_six_four_block_from_total",
        "pow_six_ten_block_le_pow_four_thirteen_block_from_total",
        "pow_base_monotone",
        "pow_exponent_monotone_from_total",
        "le_trans",
        "mul_assoc",
    )
    h_root_dependencies[35] = (
        "bertrand_scaled_budget_root_35",
        "ceil_div_six_budget_of_scaled_le",
        "pow_thirty_six_double_block_eq_pow_six_four_block_from_total",
        "pow_six_ten_block_le_pow_four_thirteen_block_from_total",
        "pow_six_four_le_pow_four_six_from_total",
        "pow_add",
        "pow_base_monotone",
        "pow_exponent_monotone_from_total",
        "mul_le_mul",
        "le_trans",
        "mul_add",
        "mul_assoc",
    )
    h_root_scripts[33] = build_h_root_six_thin(33)
    h_root_scripts[34] = build_h_root_six_thin(34)
    h_root_scripts[35] = build_h_root_six_thin(35)

    # Uniform J envelope on the frozen RFC-v1 base window:
    #
    #   (s + 7)^12 <= 44^12
    #                = 4^12 * 11^12
    #               <= 4^12 * 4^21
    #                = 4^33
    #               <= 4^(s + 5).
    #
    # The only range-dependent steps are s + 7 <= 44 and 33 <= s + 5.
    j_script = LocalPowerScript(first_witness_index=0)
    j_script.add(
        "intro s",
        "intro j",
        "intro g",
        "intro htotal",
        "intro hlower",
        "intro hupper",
        "intro hj",
        "intro hg",
    )
    j_p11_block_r, j_p11_block = j_script.total(
        "j_p11_block", "11", "2 * 6"
    )
    j_p4_twenty_one_r, j_p4_twenty_one = j_script.total(
        "j_p4_twenty_one", "4", "21"
    )
    j_script.add(
        "have j_parity : 7 * 6 = 2 * 21",
        "norm_num",
        "have j_eleven_bound : "
        + witness_le(
            j_p11_block_r,
            j_p4_twenty_one_r,
            tag="hj32_j_eleven_bound",
        ),
        "specialize pow_eleven_double_block_le_pow_four_even_from_total 6",
        "specialize pow_eleven_double_block_le_pow_four_even_from_total 21",
        "specialize "
        f"pow_eleven_double_block_le_pow_four_even_from_total {j_p11_block_r}",
        "specialize "
        f"pow_eleven_double_block_le_pow_four_even_from_total {j_p4_twenty_one_r}",
        "apply pow_eleven_double_block_le_pow_four_even_from_total",
        "exact htotal",
        "exact j_parity",
        f"exact {j_p11_block}",
        f"exact {j_p4_twenty_one}",
        "have j_twelve : 2 * 6 = 12",
        "norm_num",
        "have j_h_block : "
        + _power_terms(
            "s + 7", "2 * 6", "j", tag="hj32_j_h_block"
        ),
        "rewrite j_twelve",
        "rewrite j_twelve",
        "rewrite j_twelve",
        "rewrite j_twelve",
        "exact hj",
    )
    j_p4_block_r, j_p4_block = j_script.total(
        "j_p4_block", "4", "2 * 6"
    )
    j_p44_block_r, j_p44_block = j_script.total(
        "j_p44_block", "44", "2 * 6"
    )
    j_p4_thirty_three_r, j_p4_thirty_three = j_script.total(
        "j_p4_thirty_three", "4", "33"
    )
    j_product_44 = j_script.product_equality(
        "j_product_44",
        "4",
        "11",
        "44",
        "2 * 6",
        j_p4_block_r,
        j_p11_block_r,
        j_p44_block_r,
        j_p4_block,
        j_p11_block,
        j_p44_block,
    )
    j_product_33 = j_script.add_equality(
        "j_product_33",
        "4",
        "2 * 6",
        "21",
        "33",
        j_p4_block_r,
        j_p4_twenty_one_r,
        j_p4_thirty_three_r,
        j_p4_block,
        j_p4_twenty_one,
        j_p4_thirty_three,
    )
    j_script.add(
        "have j_four_refl : "
        + witness_le(
            j_p4_block_r,
            j_p4_block_r,
            tag="hj32_j_four_refl",
        ),
        f"specialize le_refl {j_p4_block_r}",
        "exact le_refl",
    )
    j_product_bound = j_script.product_bound(
        "j_product_bound",
        j_p4_block_r,
        j_p4_block_r,
        j_p11_block_r,
        j_p4_twenty_one_r,
        "j_four_refl",
        "j_eleven_bound",
    )
    j_script.add(
        f"rewrite <- {j_product_44} at {j_product_bound}",
        f"rewrite <- {j_product_33} at {j_product_bound}",
        "have j_base_to_upper : "
        + witness_le("s + 7", "37 + 7", tag="hj32_j_base_to_upper"),
        "specialize add_le_add_right s",
        "specialize add_le_add_right 37",
        "specialize add_le_add_right 7",
        "apply add_le_add_right",
        "exact hupper",
        "have j_upper_value : 37 + 7 = 44",
        "norm_num",
        "have j_base_bound : "
        + witness_le("s + 7", "44", tag="hj32_j_base_bound"),
        "rewrite j_upper_value at j_base_to_upper",
        "exact j_base_to_upper",
    )
    j_to_44 = j_script.base_bound(
        "j_to_44",
        "s + 7",
        "44",
        "2 * 6",
        "j",
        j_p44_block_r,
        "j_base_bound",
        "j_h_block",
        j_p44_block,
    )
    j_to_thirty_three = j_script.trans_bound(
        "j_to_thirty_three",
        "j",
        j_p44_block_r,
        j_p4_thirty_three_r,
        j_to_44,
        j_product_bound,
    )
    j_script.add(
        "have j_exponent_from_lower : "
        + witness_le("32 + 5", "s + 5", tag="hj32_j_exponent_from_lower"),
        "specialize add_le_add_right 32",
        "specialize add_le_add_right s",
        "specialize add_le_add_right 5",
        "apply add_le_add_right",
        "exact hlower",
        "have j_lower_value : 32 + 5 = 37",
        "norm_num",
        "have j_thirty_seven_to_target : "
        + witness_le("37", "s + 5", tag="hj32_j_thirty_seven_to_target"),
        "rewrite j_lower_value at j_exponent_from_lower",
        "exact j_exponent_from_lower",
        "have j_seed : "
        + witness_le("33", "37", tag="hj32_j_exponent_seed"),
        "exists 4",
        "norm_num",
    )
    j_exponent_bound = j_script.trans_bound(
        "j_exponent_bound",
        "33",
        "37",
        "s + 5",
        "j_seed",
        "j_thirty_seven_to_target",
    )
    j_growth = j_script.exponent_bound(
        "j_growth",
        "4",
        "33",
        "s + 5",
        j_p4_thirty_three_r,
        "g",
        j_exponent_bound,
        j_p4_thirty_three,
        "hg",
        "3",
    )
    j_result = j_script.trans_bound(
        "j_result",
        "j",
        j_p4_thirty_three_r,
        "g",
        j_to_thirty_three,
        j_growth,
    )
    j_script.add(f"exact {j_result}")

    j_dependencies = (
        "pow_eleven_double_block_le_pow_four_even_from_total",
        "pow_mul_base",
        "pow_add",
        "pow_base_monotone",
        "pow_exponent_monotone_from_total",
        "mul_le_mul",
        "le_refl",
        "le_trans",
        "add_le_add_right",
    )

    # The capstone is intentionally only a constructive finite dispatcher.
    # All arithmetic content lives in the six fixed-root H rows and the
    # uniform J row above.  Expanded CeilDivSix contains four occurrences of
    # its value's root, while expanded Pow contains two base and four exponent
    # occurrences, so every equality transport is explicit.
    capstone_commands: list[str] = [
        "intro s",
        "intro e",
        "intro h",
        "intro u",
        "intro j",
        "intro g",
        "intro htotal",
        "intro hlower",
        "intro hupper",
        "intro hceiling",
        "intro hh",
        "intro hu",
        "intro hj",
        "intro hg",
        "have hjresult : "
        + witness_le("j", "g", tag="hj32_capstone_j_result"),
        "specialize bertrand_j_base_thirty_two_window_from_total s",
        "specialize bertrand_j_base_thirty_two_window_from_total j",
        "specialize bertrand_j_base_thirty_two_window_from_total g",
        "apply bertrand_j_base_thirty_two_window_from_total",
        "exact htotal",
        "exact hlower",
        "exact hupper",
        "exact hj",
        "exact hg",
    ]

    def capstone_add(*commands: str) -> None:
        capstone_commands.extend(commands)

    def finish_capstone_root(root: int, equality_name: str) -> None:
        fixed_ceiling = ceil_div_six_relation(
            f"{root} * {root}",
            "e",
            tag=f"hj32_capstone_{root}_ceiling",
        )
        fixed_h = _power_terms(
            f"{root} + 1",
            f"2 * {root} + 2",
            "h",
            tag=f"hj32_capstone_{root}_h",
        )
        capstone_add(
            f"have hcap_{root}_ceiling : {fixed_ceiling}",
            f"rewrite <- {equality_name}",
            f"rewrite <- {equality_name}",
            f"rewrite <- {equality_name}",
            f"rewrite <- {equality_name}",
            "exact hceiling",
            f"have hcap_{root}_power : {fixed_h}",
            f"rewrite <- {equality_name}",
            f"rewrite <- {equality_name}",
            f"rewrite <- {equality_name}",
            f"rewrite <- {equality_name}",
            f"rewrite <- {equality_name}",
            f"rewrite <- {equality_name}",
            "exact hh",
            f"have hcap_{root}_result : "
            + witness_le("h", "u", tag=f"hj32_capstone_{root}_result"),
            f"specialize bertrand_h_root_{root}_from_total e",
            f"specialize bertrand_h_root_{root}_from_total h",
            f"specialize bertrand_h_root_{root}_from_total u",
            f"apply bertrand_h_root_{root}_from_total",
            "exact htotal",
            f"exact hcap_{root}_ceiling",
            f"exact hcap_{root}_power",
            "exact hu",
            "split",
            f"exact hcap_{root}_result",
            "exact hjresult",
        )

    capstone_add(
        "have hcap_cases_37 : s = 37 \\/ "
        + witness_le("S s", "37", tag="hj32_capstone_lt_37"),
        "specialize le_eq_or_lt s",
        "specialize le_eq_or_lt 37",
        "apply le_eq_or_lt",
        "exact hupper",
        "cases hcap_cases_37",
    )
    finish_capstone_root(37, "hcap_cases_37_left")
    for root in range(36, 32, -1):
        capstone_add(
            f"have hcap_le_{root} : "
            + witness_le("s", str(root), tag=f"hj32_capstone_le_{root}"),
            "specialize le_of_succ_le_succ s",
            f"specialize le_of_succ_le_succ {root}",
            "apply le_of_succ_le_succ",
            f"exact hcap_cases_{root + 1}_right",
            f"have hcap_cases_{root} : s = {root} \\/ "
            + witness_le(
                "S s", str(root), tag=f"hj32_capstone_lt_{root}"
            ),
            "specialize le_eq_or_lt s",
            f"specialize le_eq_or_lt {root}",
            "apply le_eq_or_lt",
            f"exact hcap_le_{root}",
            f"cases hcap_cases_{root}",
        )
        finish_capstone_root(root, f"hcap_cases_{root}_left")
    capstone_add(
        "have hcap_le_32 : "
        + witness_le("s", "32", tag="hj32_capstone_le_32"),
        "specialize le_of_succ_le_succ s",
        "specialize le_of_succ_le_succ 32",
        "apply le_of_succ_le_succ",
        "exact hcap_cases_33_right",
        "have hcap_eq_32 : s = 32",
        "specialize le_antisymm s",
        "specialize le_antisymm 32",
        "apply le_antisymm",
        "exact hcap_le_32",
        "exact hlower",
    )
    finish_capstone_root(32, "hcap_eq_32")
    base_script = tuple(capstone_commands)
    base_dependencies = (
        "le_eq_or_lt",
        "le_of_succ_le_succ",
        "le_antisymm",
        *(f"bertrand_h_root_{root}_from_total" for root in range(32, 38)),
        "bertrand_j_base_thirty_two_window_from_total",
    )

    return (
        spec(
            "pow_block_bound_from_total",
            "forall a b d e m x y X Y. "
            f"({block_total}) -> ({block_left_seed}) -> ({block_right_seed}) -> "
            f"({block_seed_bound}) -> ({block_left}) -> ({block_right}) -> "
            f"({block_result})",
            ("pow_mul_exp_from_total", "pow_base_monotone"),
            (
                "intro a",
                "intro b",
                "intro d",
                "intro e",
                "intro m",
                "intro x",
                "intro y",
                "intro X",
                "intro Y",
                "intro htotal",
                "intro hx",
                "intro hy",
                "intro hxy",
                "intro hX",
                "intro hY",
                f"have hxm : exists q. ({block_left_outer})",
                "specialize htotal x",
                "specialize htotal m",
                "exact htotal",
                "cases hxm",
                f"have hym : exists q. ({block_right_outer})",
                "specialize htotal y",
                "specialize htotal m",
                "exact htotal",
                "cases hym",
                "have houter : "
                f"{witness_le('x1', 'x2', tag='hj32_block_outer_bound')}",
                "specialize pow_base_monotone x",
                "specialize pow_base_monotone y",
                "specialize pow_base_monotone m",
                "specialize pow_base_monotone x1",
                "specialize pow_base_monotone x2",
                "apply pow_base_monotone",
                "exact hxy",
                "exact hxm_witness",
                "exact hym_witness",
                "have hleft : x1 = X",
                "specialize pow_mul_exp_from_total a",
                "specialize pow_mul_exp_from_total d",
                "specialize pow_mul_exp_from_total m",
                "specialize pow_mul_exp_from_total (d * m)",
                "specialize pow_mul_exp_from_total x",
                "specialize pow_mul_exp_from_total x1",
                "specialize pow_mul_exp_from_total X",
                "apply pow_mul_exp_from_total",
                "exact htotal",
                "refl",
                "exact hx",
                "exact hxm_witness",
                "exact hX",
                "have hright : x2 = Y",
                "specialize pow_mul_exp_from_total b",
                "specialize pow_mul_exp_from_total e",
                "specialize pow_mul_exp_from_total m",
                "specialize pow_mul_exp_from_total (e * m)",
                "specialize pow_mul_exp_from_total y",
                "specialize pow_mul_exp_from_total x2",
                "specialize pow_mul_exp_from_total Y",
                "apply pow_mul_exp_from_total",
                "exact htotal",
                "refl",
                "exact hy",
                "exact hym_witness",
                "exact hY",
                "rewrite hleft at houter",
                "rewrite hright at houter",
                "exact houter",
            ),
            "A supplied power bound remains true after a common block multiplier.",
        ),
        spec(
            "pow_three_five_le_pow_four_four_from_total",
            "forall x y. "
            f"({three_four_total}) -> ({three_five}) -> ({four_four}) -> "
            f"({three_four_result})",
            (
                "pow_zero",
                "pow_successor_compose_from_total",
                "pow_functional",
                "add_mul",
                "add_assoc",
                "add_comm",
            ),
            (
                "intro x",
                "intro y",
                "intro htotal",
                "intro hx",
                "intro hy",
                f"have hthree_zero_any : exists q. ({three_zero_any})",
                "specialize htotal 3",
                "specialize htotal 0",
                "exact htotal",
                "cases hthree_zero_any",
                "have hthree_zero_value : x1 = 1",
                "specialize pow_zero 3",
                "specialize pow_zero 0",
                "specialize pow_zero x1",
                "apply pow_zero",
                "refl",
                "exact hthree_zero_any_witness",
                f"have hthree_zero : {three_zero}",
                "rewrite hthree_zero_value at hthree_zero_any_witness",
                "rewrite hthree_zero_value at hthree_zero_any_witness",
                "exact hthree_zero_any_witness",
                f"have hthree_one : {three_one}",
                "specialize pow_successor_compose_from_total 3",
                "specialize pow_successor_compose_from_total 0",
                "specialize pow_successor_compose_from_total 1",
                f"specialize pow_successor_compose_from_total ({three_one_value})",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hthree_zero",
                "refl",
                f"have hthree_two : {three_two}",
                "specialize pow_successor_compose_from_total 3",
                "specialize pow_successor_compose_from_total 1",
                f"specialize pow_successor_compose_from_total ({three_one_value})",
                f"specialize pow_successor_compose_from_total ({three_two_value})",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hthree_one",
                "refl",
                f"have hthree_three : {three_three}",
                "specialize pow_successor_compose_from_total 3",
                "specialize pow_successor_compose_from_total 2",
                f"specialize pow_successor_compose_from_total ({three_two_value})",
                f"specialize pow_successor_compose_from_total ({three_three_value})",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hthree_two",
                "refl",
                f"have hthree_four : {three_four}",
                "specialize pow_successor_compose_from_total 3",
                "specialize pow_successor_compose_from_total 3",
                f"specialize pow_successor_compose_from_total ({three_three_value})",
                f"specialize pow_successor_compose_from_total ({three_four_value})",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hthree_three",
                "refl",
                f"have hthree_five : {three_five_exact}",
                "specialize pow_successor_compose_from_total 3",
                "specialize pow_successor_compose_from_total 4",
                f"specialize pow_successor_compose_from_total ({three_four_value})",
                f"specialize pow_successor_compose_from_total ({three_five_value})",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hthree_four",
                "refl",
                f"have hfour_zero_any : exists q. ({four_zero_any})",
                "specialize htotal 4",
                "specialize htotal 0",
                "exact htotal",
                "cases hfour_zero_any",
                "have hfour_zero_value : x2 = 1",
                "specialize pow_zero 4",
                "specialize pow_zero 0",
                "specialize pow_zero x2",
                "apply pow_zero",
                "refl",
                "exact hfour_zero_any_witness",
                f"have hfour_zero : {four_zero}",
                "rewrite hfour_zero_value at hfour_zero_any_witness",
                "rewrite hfour_zero_value at hfour_zero_any_witness",
                "exact hfour_zero_any_witness",
                f"have hfour_one : {four_one}",
                "specialize pow_successor_compose_from_total 4",
                "specialize pow_successor_compose_from_total 0",
                "specialize pow_successor_compose_from_total 1",
                f"specialize pow_successor_compose_from_total ({four_one_value})",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hfour_zero",
                "refl",
                f"have hfour_two : {four_two}",
                "specialize pow_successor_compose_from_total 4",
                "specialize pow_successor_compose_from_total 1",
                f"specialize pow_successor_compose_from_total ({four_one_value})",
                f"specialize pow_successor_compose_from_total ({four_two_value})",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hfour_one",
                "refl",
                f"have hfour_three : {four_three}",
                "specialize pow_successor_compose_from_total 4",
                "specialize pow_successor_compose_from_total 2",
                f"specialize pow_successor_compose_from_total ({four_two_value})",
                f"specialize pow_successor_compose_from_total ({four_three_value})",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hfour_two",
                "refl",
                f"have hfour_four : {four_four_exact}",
                "specialize pow_successor_compose_from_total 4",
                "specialize pow_successor_compose_from_total 3",
                f"specialize pow_successor_compose_from_total ({four_three_value})",
                f"specialize pow_successor_compose_from_total ({four_four_value})",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hfour_three",
                "refl",
                f"have hx_value : x = {three_five_value}",
                "specialize pow_functional 3",
                "specialize pow_functional 5",
                "specialize pow_functional x",
                f"specialize pow_functional ({three_five_value})",
                "apply pow_functional",
                "exact hx",
                "exact hthree_five",
                f"have hy_value : y = {four_four_value}",
                "specialize pow_functional 4",
                "specialize pow_functional 4",
                "specialize pow_functional y",
                f"specialize pow_functional ({four_four_value})",
                "apply pow_functional",
                "exact hy",
                "exact hfour_four",
                "rewrite hx_value",
                "rewrite hy_value",
                "exists 13",
                f"have hthree_four_split : {three_four_value} = "
                f"({four_three_value}) + 17",
                "norm_num",
                "rewrite hthree_four_split",
                f"specialize add_mul ({four_three_value})",
                "specialize add_mul 17",
                "specialize add_mul 3",
                "rewrite add_mul",
                f"have hfour_step : ({four_three_value}) * 4 = "
                f"({four_three_value}) * 3 + ({four_three_value})",
                "apply PA6",
                "rewrite hfour_step",
                "have hseventeen_three : 17 * 3 = 51",
                "norm_num",
                "rewrite hseventeen_three",
                f"have hthirteen_fifty_one : 13 + 51 = {four_three_value}",
                "norm_num",
                f"trans (13 + ({four_three_value}) * 3) + 51",
                "symm",
                "specialize add_assoc 13",
                f"specialize add_assoc (({four_three_value}) * 3)",
                "specialize add_assoc 51",
                "apply add_assoc",
                f"trans (({four_three_value}) * 3 + 13) + 51",
                "congr",
                "specialize add_comm 13",
                f"specialize add_comm (({four_three_value}) * 3)",
                "apply add_comm",
                "refl",
                f"trans ({four_three_value}) * 3 + (13 + 51)",
                f"specialize add_assoc (({four_three_value}) * 3)",
                "specialize add_assoc 13",
                "specialize add_assoc 51",
                "apply add_assoc",
                "rewrite hthirteen_fifty_one",
                "refl",
            ),
            "The concrete seed inequality 3^5 <= 4^4 in the relational graph.",
        ),
        spec(
            "pow_eleven_two_le_pow_two_seven_from_total",
            "forall x y. "
            f"({eleven_two_total}) -> ({eleven_two}) -> ({two_seven}) -> "
            f"({eleven_two_result})",
            (
                "pow_two",
                "pow_two_seed_bundle_from_total",
                "pow_successor_compose_from_total",
                "pow_functional",
                "pow_add",
                "add_mul",
                "mul_add",
                "add_assoc",
                "add_comm",
            ),
            (
                "intro x",
                "intro y",
                "intro htotal",
                "intro hx",
                "intro hy",
                "have hx_square : x = 11 * 11",
                "specialize pow_two 11",
                "specialize pow_two 2",
                "specialize pow_two x",
                "apply pow_two",
                "refl",
                "exact hx",
                f"have hseeds : ({seed_two_two}) /\\ ({seed_two_seven})",
                "apply pow_two_seed_bundle_from_total",
                "exact htotal",
                "cases hseeds",
                f"have htwo_three : {two_three_exact}",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 4",
                f"specialize pow_successor_compose_from_total ({two_three_value})",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hseeds_left",
                "refl",
                f"have htwo_four : {two_four_exact}",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 3",
                f"specialize pow_successor_compose_from_total ({two_three_value})",
                f"specialize pow_successor_compose_from_total ({two_four_value})",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact htwo_three",
                "refl",
                f"have htwo_five : {two_five_exact}",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 4",
                f"specialize pow_successor_compose_from_total ({two_four_value})",
                f"specialize pow_successor_compose_from_total ({two_five_value})",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact htwo_four",
                "refl",
                f"have htwo_six : {two_six_exact}",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 5",
                f"specialize pow_successor_compose_from_total ({two_five_value})",
                f"specialize pow_successor_compose_from_total ({two_six_value})",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact htwo_five",
                "refl",
                f"have htwo_seven : {two_seven_exact}",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 6",
                f"specialize pow_successor_compose_from_total ({two_six_value})",
                f"specialize pow_successor_compose_from_total ({two_seven_value})",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact htwo_six",
                "refl",
                f"have htwo_seven_product : {two_seven_value} = "
                f"({two_three_value}) * ({two_four_value})",
                "specialize pow_add 2",
                "specialize pow_add 3",
                "specialize pow_add 4",
                "specialize pow_add 7",
                f"specialize pow_add ({two_three_value})",
                f"specialize pow_add ({two_four_value})",
                f"specialize pow_add ({two_seven_value})",
                "apply pow_add",
                "norm_num",
                "exact htwo_three",
                "exact htwo_four",
                "exact htwo_seven",
                f"have hy_value : y = {two_seven_value}",
                "specialize pow_functional 2",
                "specialize pow_functional 7",
                "specialize pow_functional y",
                f"specialize pow_functional ({two_seven_value})",
                "apply pow_functional",
                "exact hy",
                "exact htwo_seven",
                "rewrite hx_square",
                "rewrite hy_value",
                "exists 7",
                "rewrite htwo_seven_product",
                f"have heleven_split : 11 = ({two_three_value}) + 3",
                "norm_num",
                "rewrite heleven_split",
                f"specialize add_mul ({two_three_value})",
                "specialize add_mul 3",
                "specialize add_mul 11",
                "rewrite add_mul",
                f"have htwo_four_split : {two_four_value} = 11 + 5",
                "norm_num",
                "rewrite htwo_four_split",
                f"specialize mul_add ({two_three_value})",
                "specialize mul_add 11",
                "specialize mul_add 5",
                "rewrite mul_add",
                f"have hsmall_gap : 7 + 3 * 11 = ({two_three_value}) * 5",
                "norm_num",
                f"trans (7 + ({two_three_value}) * 11) + 3 * 11",
                "symm",
                "specialize add_assoc 7",
                f"specialize add_assoc (({two_three_value}) * 11)",
                "specialize add_assoc (3 * 11)",
                "apply add_assoc",
                f"trans (({two_three_value}) * 11 + 7) + 3 * 11",
                "congr",
                "specialize add_comm 7",
                f"specialize add_comm (({two_three_value}) * 11)",
                "apply add_comm",
                "refl",
                f"trans ({two_three_value}) * 11 + (7 + 3 * 11)",
                f"specialize add_assoc (({two_three_value}) * 11)",
                "specialize add_assoc 7",
                "specialize add_assoc (3 * 11)",
                "apply add_assoc",
                "rewrite hsmall_gap",
                "refl",
            ),
            "The concrete seed inequality 11^2 <= 2^7 in the relational graph.",
        ),
        spec(
            "pow_six_ten_le_pow_four_thirteen_from_total",
            "forall x y. "
            f"({six_ten_total}) -> ({six_ten}) -> ({four_thirteen}) -> "
            f"({six_ten_result})",
            (
                "pow_block_bound_from_total",
                "pow_three_five_le_pow_four_four_from_total",
                "pow_two_seed_bundle_from_total",
                "pow_mul_exp_from_total",
                "pow_mul_base",
                "pow_add",
                "mul_le_mul",
                "le_refl",
            ),
            (
                "intro x",
                "intro y",
                "intro htotal",
                "intro hx",
                "intro hy",
                f"have hthree_five : exists q. ({row_four_three_five})",
                "specialize htotal 3",
                "specialize htotal 5",
                "exact htotal",
                "cases hthree_five",
                f"have hfour_four : exists q. ({row_four_four_four})",
                "specialize htotal 4",
                "specialize htotal 4",
                "exact htotal",
                "cases hfour_four",
                "have hseed : "
                f"{witness_le('x1', 'x2', tag='hj32_row4_seed_bound')}",
                "specialize pow_three_five_le_pow_four_four_from_total x1",
                "specialize pow_three_five_le_pow_four_four_from_total x2",
                "apply pow_three_five_le_pow_four_four_from_total",
                "exact htotal",
                "exact hthree_five_witness",
                "exact hfour_four_witness",
                f"have hthree_ten : exists q. ({row_four_three_ten})",
                "specialize htotal 3",
                "specialize htotal 10",
                "exact htotal",
                "cases hthree_ten",
                f"have hfour_eight : exists q. ({row_four_four_eight})",
                "specialize htotal 4",
                "specialize htotal 8",
                "exact htotal",
                "cases hfour_eight",
                f"have hthree_ten_block : {row_four_three_ten_block}",
                "have hthree_ten_exponent : 5 * 2 = 10",
                "norm_num",
                "rewrite hthree_ten_exponent",
                "rewrite hthree_ten_exponent",
                "rewrite hthree_ten_exponent",
                "rewrite hthree_ten_exponent",
                "exact hthree_ten_witness",
                f"have hfour_eight_block : {row_four_four_eight_block}",
                "have hfour_eight_exponent : 4 * 2 = 8",
                "norm_num",
                "rewrite hfour_eight_exponent",
                "rewrite hfour_eight_exponent",
                "rewrite hfour_eight_exponent",
                "rewrite hfour_eight_exponent",
                "exact hfour_eight_witness",
                "have hblock : "
                f"{witness_le('x3', 'x4', tag='hj32_row4_block_bound')}",
                "specialize pow_block_bound_from_total 3",
                "specialize pow_block_bound_from_total 4",
                "specialize pow_block_bound_from_total 5",
                "specialize pow_block_bound_from_total 4",
                "specialize pow_block_bound_from_total 2",
                "specialize pow_block_bound_from_total x1",
                "specialize pow_block_bound_from_total x2",
                "specialize pow_block_bound_from_total x3",
                "specialize pow_block_bound_from_total x4",
                "apply pow_block_bound_from_total",
                "exact htotal",
                "exact hthree_five_witness",
                "exact hfour_four_witness",
                "exact hseed",
                "exact hthree_ten_block",
                "exact hfour_eight_block",
                f"have htwo_ten : exists q. ({row_four_two_ten})",
                "specialize htotal 2",
                "specialize htotal 10",
                "exact htotal",
                "cases htwo_ten",
                f"have hfour_five : exists q. ({row_four_four_five})",
                "specialize htotal 4",
                "specialize htotal 5",
                "exact htotal",
                "cases hfour_five",
                f"have hseeds : ({seed_two_two}) /\\ ({seed_two_seven})",
                "apply pow_two_seed_bundle_from_total",
                "exact htotal",
                "cases hseeds",
                "have htwo_bridge : x6 = x5",
                "specialize pow_mul_exp_from_total 2",
                "specialize pow_mul_exp_from_total 2",
                "specialize pow_mul_exp_from_total 5",
                "specialize pow_mul_exp_from_total 10",
                "specialize pow_mul_exp_from_total 4",
                "specialize pow_mul_exp_from_total x6",
                "specialize pow_mul_exp_from_total x5",
                "apply pow_mul_exp_from_total",
                "exact htotal",
                "norm_num",
                "exact hseeds_left",
                "exact hfour_five_witness",
                "exact htwo_ten_witness",
                f"have hxfactor : {row_four_six_factor}",
                "have hsix : 2 * 3 = 6",
                "norm_num",
                "rewrite hsix",
                "rewrite hsix",
                "exact hx",
                "have hxproduct : x = x5 * x3",
                "specialize pow_mul_base 2",
                "specialize pow_mul_base 3",
                "specialize pow_mul_base 10",
                "specialize pow_mul_base x5",
                "specialize pow_mul_base x3",
                "specialize pow_mul_base x",
                "apply pow_mul_base",
                "exact htwo_ten_witness",
                "exact hthree_ten_witness",
                "exact hxfactor",
                "have hyproduct : y = x6 * x4",
                "specialize pow_add 4",
                "specialize pow_add 5",
                "specialize pow_add 8",
                "specialize pow_add 13",
                "specialize pow_add x6",
                "specialize pow_add x4",
                "specialize pow_add y",
                "apply pow_add",
                "norm_num",
                "exact hfour_five_witness",
                "exact hfour_eight_witness",
                "exact hy",
                "rewrite htwo_bridge at hyproduct",
                "have hfactor_bound : "
                f"{witness_le('x5 * x3', 'x5 * x4', tag='hj32_row4_product_bound')}",
                "specialize mul_le_mul x5",
                "specialize mul_le_mul x5",
                "specialize mul_le_mul x3",
                "specialize mul_le_mul x4",
                "apply mul_le_mul",
                "specialize le_refl x5",
                "exact le_refl",
                "exact hblock",
                "rewrite <- hxproduct at hfactor_bound",
                "rewrite <- hyproduct at hfactor_bound",
                "exact hfactor_bound",
            ),
            "The block seed 6^10 <= 4^13 used by the finite H window.",
        ),
        spec(
            "linear_square_budget",
            "forall a q r t c k d. "
            "r = a * q + t -> k = q * r + c -> d + a * c = t * r -> "
            f"({linear_square_budget})",
            ("mul_add", "mul_assoc", "add_assoc", "add_comm", "add_mul"),
            linear_square_budget_script,
            "A factorized linear budget lies below a square by an explicit gap.",
        ),
        *(
            spec(
                f"bertrand_scaled_budget_root_{root}",
                root_budget_results[root],
                root_budget_dependencies[root],
                root_budget_scripts[root],
                f"The factorized RFC-v1 H budget at root {root} lies below its square.",
            )
            for root in range(32, 38)
        ),
        spec(
            "ceil_div_six_budget_of_scaled_le",
            "forall x k e. "
            f"({ceil_budget_source}) -> ({ceil_budget_scaled}) -> "
            f"({ceil_budget_result})",
            ("le_trans", "succ_ne_zero", "mul_le_cancel_left_nonzero"),
            ceil_budget_script,
            "A scaled lower bound cancels against the lower half of CeilDivSix.",
        ),
        spec(
            "pow_six_six_le_pow_four_eight_from_total",
            "forall x y. "
            f"({residual_six_total}) -> ({residual_six_left}) -> "
            f"({residual_six_right}) -> ({residual_six_result})",
            (
                "pow_three_five_le_pow_four_four_from_total",
                "pow_two_seed_bundle_from_total",
                "pow_mul_exp_from_total",
                "pow_mul_base",
                "pow_add",
                "pow_base_monotone",
                "mul_le_mul",
                "le_refl",
            ),
            residual_six_script,
            "The capacity-safe residual block 6^6 <= 4^8.",
        ),
        spec(
            "pow_six_four_le_pow_four_six_from_total",
            "forall x y. "
            f"({residual_four_total}) -> ({residual_four_left}) -> "
            f"({residual_four_right}) -> ({residual_four_result})",
            (
                "pow_two_seed_bundle_from_total",
                "pow_mul_exp_from_total",
                "pow_mul_base",
                "pow_add",
                "pow_base_monotone",
                "mul_le_mul",
                "le_refl",
            ),
            residual_four_script,
            "The capacity-safe residual block 6^4 <= 4^6.",
        ),
        spec(
            "pow_three_five_block_plus_one_le_pow_four_four_block_plus_one_from_total",
            "forall m x y. "
            f"({three_plus_total}) -> ({three_plus_left}) -> "
            f"({three_plus_right}) -> ({three_plus_result})",
            (
                "pow_block_bound_from_total",
                "pow_three_five_le_pow_four_four_from_total",
                "pow_add",
                "pow_base_monotone",
                "mul_le_mul",
            ),
            three_plus_script,
            "The seed 3^5 <= 4^4 extends by blocks and one residual factor.",
        ),
        spec(
            "pow_two_double_eq_pow_four_from_total",
            "forall k x y. "
            f"({two_double_total}) -> ({two_double_left}) -> "
            f"({two_double_right}) -> x = y",
            ("pow_two_seed_bundle_from_total", "pow_mul_exp_from_total"),
            two_double_script,
            "An even power of two is the matching power of four.",
        ),
        spec(
            "pow_two_successor_double_le_pow_four_successor_from_total",
            "forall k x y. "
            f"({two_odd_total}) -> ({two_odd_left}) -> "
            f"({two_odd_right}) -> ({two_odd_result})",
            (
                "pow_two_double_eq_pow_four_from_total",
                "pow_base_monotone",
                "pow_add",
                "mul_le_mul",
                "le_refl",
            ),
            two_odd_script,
            "An odd power of two is bounded by the next power of four.",
        ),
        spec(
            "pow_eleven_double_block_le_pow_two_seven_block_from_total",
            "forall m x y. "
            f"({eleven_block_total}) -> ({eleven_block_left}) -> "
            f"({eleven_block_right}) -> ({eleven_block_result})",
            (
                "pow_block_bound_from_total",
                "pow_eleven_two_le_pow_two_seven_from_total",
            ),
            eleven_block_script,
            "The seed 11^2 <= 2^7 extends through a common block count.",
        ),
        spec(
            "pow_eleven_double_block_le_pow_four_even_from_total",
            "forall m k x y. "
            f"({eleven_even_total}) -> {eleven_even_parity} -> "
            f"({eleven_even_left}) -> ({eleven_even_right}) -> "
            f"({eleven_even_result})",
            (
                "pow_eleven_double_block_le_pow_two_seven_block_from_total",
                "pow_two_double_eq_pow_four_from_total",
            ),
            eleven_even_script,
            "An even 11-to-2 block exponent converts exactly to base four.",
        ),
        spec(
            "pow_eleven_double_block_le_pow_four_odd_from_total",
            "forall m k x y. "
            f"({eleven_odd_total}) -> {eleven_odd_parity} -> "
            f"({eleven_odd_left}) -> ({eleven_odd_right}) -> "
            f"({eleven_odd_result})",
            (
                "pow_eleven_double_block_le_pow_two_seven_block_from_total",
                "pow_two_successor_double_le_pow_four_successor_from_total",
                "le_trans",
            ),
            eleven_odd_script,
            "An odd 11-to-2 block exponent converts to the next base-four power.",
        ),
        spec(
            "pow_six_ten_block_le_pow_four_thirteen_block_from_total",
            "forall m x y. "
            f"({six_block_total}) -> ({six_block_left}) -> "
            f"({six_block_right}) -> ({six_block_result})",
            (
                "pow_block_bound_from_total",
                "pow_six_ten_le_pow_four_thirteen_from_total",
            ),
            six_block_script,
            "The seed 6^10 <= 4^13 extends through a common block count.",
        ),
        spec(
            "pow_thirty_six_double_block_eq_pow_six_four_block_from_total",
            "forall m x y. "
            f"({thirty_six_total}) -> ({thirty_six_left}) -> "
            f"({thirty_six_right}) -> x = y",
            ("pow_two", "pow_mul_exp_from_total", "mul_assoc"),
            thirty_six_script,
            "A double block of base thirty six is a fourfold block of base six.",
        ),
        *(
            spec(
                f"bertrand_h_root_{root}_from_total",
                "forall e h u. "
                f"({h_root_data[root]['total']}) -> "
                f"({h_root_data[root]['ceiling']}) -> "
                f"({h_root_data[root]['h']}) -> "
                f"({h_root_data[root]['u']}) -> "
                f"({h_root_data[root]['result']})",
                h_root_dependencies[root],
                h_root_scripts[root],
                f"The RFC-v1 H envelope at the fixed root {root}.",
            )
            for root in range(32, 38)
        ),
        spec(
            "bertrand_j_base_thirty_two_window_from_total",
            "forall s j g. "
            f"({base_total}) -> ({base_lower}) -> ({base_upper}) -> "
            f"({base_j}) -> ({base_j_bound}) -> ({base_j_result})",
            j_dependencies,
            tuple(j_script.commands),
            "The RFC-v1 J envelope uniformly covers roots 32 through 37.",
        ),
        spec(
            "bertrand_hj_base_window_thirty_two_from_total",
            "forall s e h u j g. "
            f"({base_total}) -> ({base_lower}) -> ({base_upper}) -> "
            f"({base_ceiling}) -> ({base_h}) -> ({base_h_bound}) -> "
            f"({base_j}) -> ({base_j_bound}) -> "
            f"(({base_h_result}) /\\ ({base_j_result}))",
            base_dependencies,
            base_script,
            "All six roots 32 through 37 satisfy both RFC-v1 H/J base bounds.",
        ),
    )


__all__ = ["make_bertrand_hj_base_thirty_two_candidate_theorems"]
