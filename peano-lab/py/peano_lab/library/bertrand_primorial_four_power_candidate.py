"""The elementary four-power upper bound for the Bertrand Primorial.

The six rows below isolate the small boundary arithmetic, package the large
Primorial/Choose support laws once, and prove ``Primorial(n) <= 4^n`` by a
bounded induction whose boundary is split into even and odd indices.  Every
readable relation expands to first-order Peano arithmetic before parsing.
This module creates no trusted primitive, authority enrollment, or checked-
use grant.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _choose_relation_term,
    _le_term,
)
from peano_lab.library.bertrand_primorial_foundation_candidate import (
    _factor_choice_rendered,
    _primorial_relation_term,
)
from peano_lab.library.bertrand_primorial_interval_candidate import (
    _primorial_interval_relation_term,
)
from peano_lab.library.power_algebra_theorems import _power_terms


PRIMORIAL_ONE = "primorial_one"
DOUBLE_HALF_PREDECESSOR_DATA = "double_half_predecessor_data"
ODD_POSITIVE_PREFIX_PREDECESSOR_BOUND = (
    "odd_positive_prefix_predecessor_bound"
)
CENTRAL_BINOM_NONZERO_STRONG_UPPER = (
    "central_binom_nonzero_strong_upper"
)
PRIMORIAL_FOUR_POWER_SUPPORT_PACKAGE = (
    "primorial_four_power_support_package"
)
PRIMORIAL_LE_FOUR_POW_BOUNDED = "primorial_le_four_pow_bounded"
PRIMORIAL_LE_FOUR_POW = "primorial_le_four_pow"


def make_bertrand_primorial_four_power_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered Primorial four-power tranche."""

    one_source = _primorial_relation_term(
        "1",
        "z",
        tag="bpo_source",
        variables=("z",),
    )
    one_previous = _primorial_relation_term(
        "0",
        "r",
        tag="bpo_previous",
        variables=("z", "p", "r"),
    )
    one_choice = _factor_choice_rendered(
        "0",
        "p",
        tag="bpo_factor",
        avoid=("z", "p", "r"),
    )
    one_decomposition = (
        f"exists p r. ({one_choice}) /\\ "
        f"(({one_previous}) /\\ z = r * p)"
    )
    one_script = (
        "intro z",
        "intro hprimorial",
        f"have hdecomposition : {one_decomposition}",
        "specialize primorial_succ_decompose 0",
        "specialize primorial_succ_decompose z",
        "apply primorial_succ_decompose",
        "exact hprimorial",
        "cases hdecomposition",
        "cases hdecomposition_witness",
        "cases hdecomposition_witness_witness",
        "cases hdecomposition_witness_witness_right",
        "have hr : x1 = 1",
        "apply primorial_zero",
        "exact hdecomposition_witness_witness_right_left",
        "cases hdecomposition_witness_witness_left",
        "cases hdecomposition_witness_witness_left_left",
        "rewrite hr at hdecomposition_witness_witness_right_right",
        "rewrite hdecomposition_witness_witness_left_left_right at "
        "hdecomposition_witness_witness_right_right",
        "trans 1 * 1",
        "exact hdecomposition_witness_witness_right_right",
        "norm_num",
        "cases hdecomposition_witness_witness_left_right",
        "rewrite hr at hdecomposition_witness_witness_right_right",
        "rewrite hdecomposition_witness_witness_left_right_right at "
        "hdecomposition_witness_witness_right_right",
        "trans 1 * 1",
        "exact hdecomposition_witness_witness_right_right",
        "norm_num",
    )

    double_bound = _le_term(
        "k",
        "n",
        tag="bdhpb_result",
        variables=("n", "k"),
    )
    double_script = (
        "intro n",
        "induction k",
        "intro heq",
        "exfalso",
        "apply PA1",
        "trans 2 * 0",
        "exact heq",
        "norm_num",
        "intro heq",
        "split",
        "intro hk",
        "apply PA1",
        "exact hk",
        "exists k",
        "apply PA2",
        "trans 2 * S k",
        "simp [two_mul_eq_add_self, add_succ_left]",
        "symm",
        "exact heq",
    )

    odd_prefix_bound = _le_term(
        "S k",
        "n",
        tag="boppb_result",
        variables=("n", "k"),
    )
    odd_bounds_script = (
        "intro n",
        "induction k",
        "intro heq",
        "intro hpositive",
        "cases hpositive",
        "exfalso",
        "apply PA1",
        "symm",
        "exact hpositive_witness",
        "intro heq",
        "intro hpositive",
        "exists k",
        "apply PA2",
        "trans 2 * S k + 1",
        "simp [two_mul_eq_add_self, add_succ_left]",
        "symm",
        "exact heq",
    )

    nonzero_variables = ("n", "c", "q")
    nonzero_central = _central_binom_relation_term(
        "n",
        "c",
        tag="bcnzsu_central",
        variables=nonzero_variables,
    )
    nonzero_power = _power_terms(
        "4",
        "n",
        "q",
        tag="bcnzsu_power",
    )
    nonzero_result = _le_term(
        "2 * c",
        "q",
        tag="bcnzsu_result",
        variables=nonzero_variables,
    )
    nonzero_script = (
        "induction n",
        "intro c",
        "intro q",
        "intro hnonzero",
        "intro hcentral",
        "intro hpower",
        "exfalso",
        "apply hnonzero",
        "refl",
        "intro c",
        "intro q",
        "intro hnonzero",
        "intro hcentral",
        "intro hpower",
        "specialize central_binom_strong_upper n",
        "specialize central_binom_strong_upper c",
        "specialize central_binom_strong_upper q",
        "apply central_binom_strong_upper",
        "exact hcentral",
        "exact hpower",
    )

    central_exists_relation = _central_binom_relation_term(
        "n",
        "c",
        tag="bpfpsp_central_exists",
        variables=("n", "c"),
    )
    central_exists = (
        f"forall n. exists c. ({central_exists_relation})"
    )
    choose_exists_relation = _choose_relation_term(
        "n",
        "k",
        "c",
        tag="bpfpsp_choose_exists",
        variables=("n", "k", "c"),
    )
    choose_exists = (
        f"forall n k. exists c. ({choose_exists_relation})"
    )
    split_source = _primorial_relation_term(
        "a + l",
        "z",
        tag="bpfpsp_split_source",
        variables=("a", "l", "z"),
    )
    split_prefix = _primorial_relation_term(
        "a",
        "x",
        tag="bpfpsp_split_prefix",
        variables=("a", "l", "z", "x", "y"),
    )
    split_interval = _primorial_interval_relation_term(
        "a",
        "l",
        "y",
        tag="bpfpsp_split_interval",
        variables=("a", "l", "z", "x", "y"),
    )
    split_law = (
        "forall a l z. "
        f"({split_source}) -> exists x y. ({split_prefix}) /\\ "
        f"(({split_interval}) /\\ z = x * y)"
    )
    even_interval = _primorial_interval_relation_term(
        "n",
        "n",
        "z",
        tag="bpfpsp_even_interval",
        variables=("n", "z", "c"),
    )
    even_central = _central_binom_relation_term(
        "n",
        "c",
        tag="bpfpsp_even_central",
        variables=("n", "z", "c"),
    )
    even_result = _le_term(
        "z",
        "c",
        tag="bpfpsp_even_result",
        variables=("n", "z", "c"),
    )
    even_law = (
        "forall n z c. "
        f"({even_interval}) -> ({even_central}) -> ({even_result})"
    )
    odd_interval = _primorial_interval_relation_term(
        "S n",
        "n",
        "z",
        tag="bpfpsp_odd_interval",
        variables=("n", "z", "c"),
    )
    odd_middle = _choose_relation_term(
        "S (n + n)",
        "n",
        "c",
        tag="bpfpsp_odd_middle",
        variables=("n", "z", "c"),
    )
    odd_result = _le_term(
        "z",
        "c",
        tag="bpfpsp_odd_result",
        variables=("n", "z", "c"),
    )
    odd_law = (
        "forall n z c. "
        f"({odd_interval}) -> ({odd_middle}) -> ({odd_result})"
    )
    odd_upper_middle = _choose_relation_term(
        "S (n + n)",
        "n",
        "c",
        tag="bpfpsp_odd_upper_middle",
        variables=("n", "c", "q"),
    )
    odd_upper_power = _power_terms(
        "4",
        "n",
        "q",
        tag="bpfpsp_odd_upper_power",
    )
    odd_upper_result = _le_term(
        "c",
        "q",
        tag="bpfpsp_odd_upper_result",
        variables=("n", "c", "q"),
    )
    odd_upper_law = (
        "forall n c q. "
        f"({odd_upper_middle}) -> ({odd_upper_power}) -> "
        f"({odd_upper_result})"
    )
    support_package = (
        f"({central_exists}) /\\ (({choose_exists}) /\\ "
        f"(({split_law}) /\\ (({even_law}) /\\ "
        f"(({odd_law}) /\\ ({odd_upper_law})))))"
    )
    package_script = (
        "split",
        "exact central_binom_exists",
        "split",
        "exact choose_exists",
        "split",
        "exact primorial_prefix_interval_split",
        "split",
        "exact primorial_even_interval_le_central",
        "split",
        "exact primorial_odd_interval_le_middle",
        "exact central_binom_odd_middle_le_four_pow",
    )

    bounded_variables = ("N", "n", "z", "q")
    bounded_index = _le_term(
        "n",
        "N",
        tag="bplfpb_index",
        variables=bounded_variables,
    )
    bounded_primorial = _primorial_relation_term(
        "n",
        "z",
        tag="bplfpb_primorial",
        variables=bounded_variables,
    )
    bounded_power = _power_terms(
        "4",
        "n",
        "q",
        tag="bplfpb_power",
    )
    bounded_result = _le_term(
        "z",
        "q",
        tag="bplfpb_result",
        variables=bounded_variables,
    )
    bounded_formula = (
        "forall N n z q. "
        f"({bounded_index}) -> ({bounded_primorial}) -> "
        f"({bounded_power}) -> ({bounded_result})"
    )

    base_zero_primorial = _primorial_relation_term(
        "0",
        "z",
        tag="bplfpb_zero_primorial",
        variables=bounded_variables,
    )
    base_one_primorial = _primorial_relation_term(
        "1",
        "z",
        tag="bplfpb_one_primorial",
        variables=bounded_variables,
    )
    even_primorial = _primorial_relation_term(
        "x + x",
        "z",
        tag="bplfpb_even_primorial",
        variables=bounded_variables + ("x",),
    )
    even_prefix = _primorial_relation_term(
        "x",
        "a",
        tag="bplfpb_even_prefix",
        variables=bounded_variables + ("x", "a", "b", "c", "r"),
    )
    even_interval_relation = _primorial_interval_relation_term(
        "x",
        "x",
        "b",
        tag="bplfpb_even_interval",
        variables=bounded_variables + ("x", "a", "b", "c", "r"),
    )
    even_central_relation = _central_binom_relation_term(
        "x",
        "c",
        tag="bplfpb_even_central",
        variables=bounded_variables + ("x", "a", "b", "c", "r"),
    )
    even_power_relation = _power_terms(
        "4",
        "x",
        "r",
        tag="bplfpb_even_power",
    )
    odd_primorial = _primorial_relation_term(
        "S x + x",
        "z",
        tag="bplfpb_odd_primorial",
        variables=bounded_variables + ("x",),
    )
    odd_prefix = _primorial_relation_term(
        "S x",
        "a",
        tag="bplfpb_odd_prefix",
        variables=bounded_variables + ("x", "a", "b", "c", "r", "s"),
    )
    odd_interval_relation = _primorial_interval_relation_term(
        "S x",
        "x",
        "b",
        tag="bplfpb_odd_interval",
        variables=bounded_variables + ("x", "a", "b", "c", "r", "s"),
    )
    odd_middle_relation = _choose_relation_term(
        "S (x + x)",
        "x",
        "c",
        tag="bplfpb_odd_middle",
        variables=bounded_variables + ("x", "a", "b", "c", "r", "s"),
    )
    odd_prefix_power = _power_terms(
        "4",
        "S x",
        "r",
        tag="bplfpb_odd_prefix_power",
    )
    odd_half_power = _power_terms(
        "4",
        "x",
        "s",
        tag="bplfpb_odd_half_power",
    )
    odd_prefix_index_bound = _le_term(
        "S x",
        "N",
        tag="bplfpb_prefix_index",
        variables=bounded_variables + ("x",),
    )

    bounded_script = (
        "intro hpackage",
        "cases hpackage",
        "cases hpackage_right",
        "cases hpackage_right_right",
        "cases hpackage_right_right_right",
        "cases hpackage_right_right_right_right",
        "induction N",
        "intro n",
        "intro z",
        "intro q",
        "intro hbound",
        "intro hprimorial",
        "intro hpower",
        "have hn : n = 0",
        "apply le_zero",
        "exact hbound",
        f"have hzero_primorial : {base_zero_primorial}",
        "specialize primorial_index_eq_transport n",
        "specialize primorial_index_eq_transport 0",
        "specialize primorial_index_eq_transport z",
        "apply primorial_index_eq_transport",
        "exact hn",
        "exact hprimorial",
        "have hz : z = 1",
        "apply primorial_zero",
        "exact hzero_primorial",
        "have hq : q = 1",
        "specialize pow_zero 4",
        "specialize pow_zero n",
        "specialize pow_zero q",
        "apply pow_zero",
        "exact hn",
        "exact hpower",
        "rewrite hz",
        "rewrite hq",
        "specialize le_refl 1",
        "exact le_refl",
        "intro n",
        "intro z",
        "intro q",
        "intro hbound",
        "intro hprimorial",
        "intro hpower",
        "have hboundary : n = S N \/ exists g. g + S n = S N",
        "specialize le_eq_or_lt n",
        "specialize le_eq_or_lt (S N)",
        "apply le_eq_or_lt",
        "exact hbound",
        "cases hboundary",
        "have hparity : exists k. n = 2 * k \/ n = 2 * k + 1",
        "specialize parity_cases n",
        "exact parity_cases",
        "cases hparity",
        "cases hparity_witness",
        "have hdouble : S N = 2 * x",
        "trans n",
        "symm",
        "exact hboundary_left",
        "exact hparity_witness_left",
        "have hhalf_data : ~(x = 0) /\\ exists g. g + x = N",
        "apply double_half_predecessor_data",
        "exact hdouble",
        "cases hhalf_data",
        "have hsum : n = x + x",
        "trans 2 * x",
        "exact hparity_witness_left",
        "specialize two_mul_eq_add_self x",
        "exact two_mul_eq_add_self",
        f"have heven_primorial : {even_primorial}",
        "specialize primorial_index_eq_transport n",
        "specialize primorial_index_eq_transport (x + x)",
        "specialize primorial_index_eq_transport z",
        "apply primorial_index_eq_transport",
        "exact hsum",
        "exact hprimorial",
        "have hsplit : exists a b. "
        f"({even_prefix}) /\\ (({even_interval_relation}) /\\ z = a * b)",
        "specialize hpackage_right_right_left x",
        "specialize hpackage_right_right_left x",
        "specialize hpackage_right_right_left z",
        "apply hpackage_right_right_left",
        "exact heven_primorial",
        "cases hsplit",
        "cases hsplit_witness",
        "cases hsplit_witness_witness",
        "cases hsplit_witness_witness_right",
        f"have hhalf_power : exists r. ({even_power_relation})",
        "specialize pow_exists 4",
        "specialize pow_exists x",
        "exact pow_exists",
        "cases hhalf_power",
        f"have hcentral : exists c. ({even_central_relation})",
        "specialize hpackage_left x",
        "exact hpackage_left",
        "cases hcentral",
        "have hprefix_bound : exists g. g + x1 = x3",
        "specialize IH x",
        "specialize IH x1",
        "specialize IH x3",
        "apply IH",
        "exact hhalf_data_right",
        "exact hsplit_witness_witness_left",
        "exact hhalf_power_witness",
        "have hinterval_bound : exists g. g + x2 = x4",
        "specialize hpackage_right_right_right_left x",
        "specialize hpackage_right_right_right_left x2",
        "specialize hpackage_right_right_right_left x4",
        "apply hpackage_right_right_right_left",
        "exact hsplit_witness_witness_right_left",
        "exact hcentral_witness",
        "have hstrong : exists g. g + 2 * x4 = x3",
        "specialize central_binom_nonzero_strong_upper x",
        "specialize central_binom_nonzero_strong_upper x4",
        "specialize central_binom_nonzero_strong_upper x3",
        "apply central_binom_nonzero_strong_upper",
        "exact hhalf_data_left",
        "exact hcentral_witness",
        "exact hhalf_power_witness",
        "have hcentral_double : exists g. g + x4 = 2 * x4",
        "have hcentral_add : exists g. g + x4 = x4 + x4",
        "specialize le_add_right x4",
        "specialize le_add_right x4",
        "exact le_add_right",
        "specialize two_mul_eq_add_self x4",
        "rewrite two_mul_eq_add_self",
        "exact hcentral_add",
        "have hcentral_bound : exists g. g + x4 = x3",
        "specialize le_trans x4",
        "specialize le_trans (2 * x4)",
        "specialize le_trans x3",
        "apply le_trans",
        "exact hcentral_double",
        "exact hstrong",
        "have hinterval_power_bound : exists g. g + x2 = x3",
        "specialize le_trans x2",
        "specialize le_trans x4",
        "specialize le_trans x3",
        "apply le_trans",
        "exact hinterval_bound",
        "exact hcentral_bound",
        "have hproduct_bound : exists g. g + x1 * x2 = x3 * x3",
        "specialize mul_le_mul x1",
        "specialize mul_le_mul x3",
        "specialize mul_le_mul x2",
        "specialize mul_le_mul x3",
        "apply mul_le_mul",
        "exact hprefix_bound",
        "exact hinterval_power_bound",
        "have hpower_product : q = x3 * x3",
        "specialize pow_add 4",
        "specialize pow_add x",
        "specialize pow_add x",
        "specialize pow_add n",
        "specialize pow_add x3",
        "specialize pow_add x3",
        "specialize pow_add q",
        "apply pow_add",
        "exact hsum",
        "exact hhalf_power_witness",
        "exact hhalf_power_witness",
        "exact hpower",
        "rewrite hsplit_witness_witness_right_right",
        "rewrite hpower_product",
        "exact hproduct_bound",
        "have hxcase : x = 0 \/ exists h. x = S h",
        "specialize zero_or_succ x",
        "exact zero_or_succ",
        "cases hxcase",
        "have hone : n = 1",
        "trans 2 * x + 1",
        "exact hparity_witness_right",
        "rewrite hxcase_left",
        "norm_num",
        f"have hone_primorial : {base_one_primorial}",
        "specialize primorial_index_eq_transport n",
        "specialize primorial_index_eq_transport 1",
        "specialize primorial_index_eq_transport z",
        "apply primorial_index_eq_transport",
        "exact hone",
        "exact hprimorial",
        "have hz : z = 1",
        "apply primorial_one",
        "exact hone_primorial",
        "have hq : q = 4",
        "specialize pow_one 4",
        "specialize pow_one n",
        "specialize pow_one q",
        "apply pow_one",
        "exact hone",
        "exact hpower",
        "rewrite hz",
        "rewrite hq",
        "exists 3",
        "norm_num",
        "have hodd : S N = 2 * x + 1",
        "trans n",
        "symm",
        "exact hboundary_left",
        "exact hparity_witness_right",
        f"have hprefix_index_bound : {odd_prefix_index_bound}",
        "apply odd_positive_prefix_predecessor_bound",
        "exact hodd",
        "exact hxcase_right",
        "have hsum : n = S x + x",
        "trans 2 * x + 1",
        "exact hparity_witness_right",
        "simp [two_mul_eq_add_self, add_succ_left]",
        f"have hodd_primorial : {odd_primorial}",
        "specialize primorial_index_eq_transport n",
        "specialize primorial_index_eq_transport (S x + x)",
        "specialize primorial_index_eq_transport z",
        "apply primorial_index_eq_transport",
        "exact hsum",
        "exact hprimorial",
        "have hsplit : exists a b. "
        f"({odd_prefix}) /\\ (({odd_interval_relation}) /\\ z = a * b)",
        "specialize hpackage_right_right_left (S x)",
        "specialize hpackage_right_right_left x",
        "specialize hpackage_right_right_left z",
        "apply hpackage_right_right_left",
        "exact hodd_primorial",
        "cases hsplit",
        "cases hsplit_witness",
        "cases hsplit_witness_witness",
        "cases hsplit_witness_witness_right",
        f"have hprefix_power : exists r. ({odd_prefix_power})",
        "specialize pow_exists 4",
        "specialize pow_exists (S x)",
        "exact pow_exists",
        "cases hprefix_power",
        f"have hhalf_power : exists s. ({odd_half_power})",
        "specialize pow_exists 4",
        "specialize pow_exists x",
        "exact pow_exists",
        "cases hhalf_power",
        "have hprefix_bound : exists g. g + x1 = x3",
        "specialize IH (S x)",
        "specialize IH x1",
        "specialize IH x3",
        "apply IH",
        "exact hprefix_index_bound",
        "exact hsplit_witness_witness_left",
        "exact hprefix_power_witness",
        "have hmiddle : exists c. "
        f"({odd_middle_relation})",
        "specialize hpackage_right_left (S (x + x))",
        "specialize hpackage_right_left x",
        "exact hpackage_right_left",
        "cases hmiddle",
        "have hinterval_bound : exists g. g + x2 = x5",
        "specialize hpackage_right_right_right_right_left x",
        "specialize hpackage_right_right_right_right_left x2",
        "specialize hpackage_right_right_right_right_left x5",
        "apply hpackage_right_right_right_right_left",
        "exact hsplit_witness_witness_right_left",
        "exact hmiddle_witness",
        "have hmiddle_bound : exists g. g + x5 = x4",
        "specialize hpackage_right_right_right_right_right x",
        "specialize hpackage_right_right_right_right_right x5",
        "specialize hpackage_right_right_right_right_right x4",
        "apply hpackage_right_right_right_right_right",
        "exact hmiddle_witness",
        "exact hhalf_power_witness",
        "have hinterval_power_bound : exists g. g + x2 = x4",
        "specialize le_trans x2",
        "specialize le_trans x5",
        "specialize le_trans x4",
        "apply le_trans",
        "exact hinterval_bound",
        "exact hmiddle_bound",
        "have hproduct_bound : exists g. g + x1 * x2 = x3 * x4",
        "specialize mul_le_mul x1",
        "specialize mul_le_mul x3",
        "specialize mul_le_mul x2",
        "specialize mul_le_mul x4",
        "apply mul_le_mul",
        "exact hprefix_bound",
        "exact hinterval_power_bound",
        "have hpower_product : q = x3 * x4",
        "specialize pow_add 4",
        "specialize pow_add (S x)",
        "specialize pow_add x",
        "specialize pow_add n",
        "specialize pow_add x3",
        "specialize pow_add x4",
        "specialize pow_add q",
        "apply pow_add",
        "exact hsum",
        "exact hprefix_power_witness",
        "exact hhalf_power_witness",
        "exact hpower",
        "rewrite hsplit_witness_witness_right_right",
        "rewrite hpower_product",
        "exact hproduct_bound",
        "have hpredecessor_bound : exists g. g + n = N",
        "specialize le_of_succ_le_succ n",
        "specialize le_of_succ_le_succ N",
        "apply le_of_succ_le_succ",
        "exact hboundary_right",
        "specialize IH n",
        "specialize IH z",
        "specialize IH q",
        "apply IH",
        "exact hpredecessor_bound",
        "exact hprimorial",
        "exact hpower",
    )

    public_variables = ("n", "z", "q")
    public_primorial = _primorial_relation_term(
        "n",
        "z",
        tag="bplfp_primorial",
        variables=public_variables,
    )
    public_power = _power_terms(
        "4",
        "n",
        "q",
        tag="bplfp_power",
    )
    public_result = _le_term(
        "z",
        "q",
        tag="bplfp_result",
        variables=public_variables,
    )
    public_script = (
        "intro n",
        "intro z",
        "intro q",
        "intro hprimorial",
        "intro hpower",
        f"have hbounded_all : {bounded_formula}",
        "apply primorial_le_four_pow_bounded",
        "exact primorial_four_power_support_package",
        "specialize hbounded_all n",
        "specialize hbounded_all n",
        "specialize hbounded_all z",
        "specialize hbounded_all q",
        "apply hbounded_all",
        "specialize le_refl n",
        "exact le_refl",
        "exact hprimorial",
        "exact hpower",
    )

    return (
        spec(
            PRIMORIAL_ONE,
            f"forall z. ({one_source}) -> z = 1",
            ("primorial_zero", "primorial_succ_decompose"),
            one_script,
            "The inclusive Primorial at one is exactly one.",
        ),
        spec(
            DOUBLE_HALF_PREDECESSOR_DATA,
            "forall n k. S n = 2 * k -> "
            f"(~(k = 0) /\\ ({double_bound}))",
            ("two_mul_eq_add_self", "add_succ_left"),
            double_script,
            "An even successor has a nonzero half below its predecessor.",
        ),
        spec(
            ODD_POSITIVE_PREFIX_PREDECESSOR_BOUND,
            "forall n k. S n = 2 * k + 1 -> "
            f"(exists h. k = S h) -> ({odd_prefix_bound})",
            ("two_mul_eq_add_self", "add_succ_left"),
            odd_bounds_script,
            "The positive prefix half of an odd successor is smaller.",
        ),
        spec(
            CENTRAL_BINOM_NONZERO_STRONG_UPPER,
            "forall n c q. ~(n = 0) -> "
            f"({nonzero_central}) -> ({nonzero_power}) -> "
            f"({nonzero_result})",
            ("central_binom_strong_upper",),
            nonzero_script,
            "The strong central bound extends to every nonzero index.",
        ),
        spec(
            PRIMORIAL_FOUR_POWER_SUPPORT_PACKAGE,
            support_package,
            (
                "central_binom_exists",
                "choose_exists",
                "primorial_prefix_interval_split",
                "primorial_even_interval_le_central",
                "primorial_odd_interval_le_middle",
                "central_binom_odd_middle_le_four_pow",
            ),
            package_script,
            "The large interval and coefficient laws close once.",
        ),
        spec(
            PRIMORIAL_LE_FOUR_POW_BOUNDED,
            f"({support_package}) -> ({bounded_formula})",
            (
                "le_zero",
                "le_eq_or_lt",
                "le_of_succ_le_succ",
                "zero_or_succ",
                "le_refl",
                "le_add_right",
                "le_trans",
                "mul_le_mul",
                "two_mul_eq_add_self",
                "add_succ_left",
                "parity_cases",
                "pow_exists",
                "pow_zero",
                "pow_one",
                "pow_add",
                "primorial_index_eq_transport",
                "primorial_zero",
                PRIMORIAL_ONE,
                DOUBLE_HALF_PREDECESSOR_DATA,
                ODD_POSITIVE_PREFIX_PREDECESSOR_BOUND,
                CENTRAL_BINOM_NONZERO_STRONG_UPPER,
            ),
            bounded_script,
            "Every bounded Primorial is at most the matching fourth power.",
        ),
        spec(
            PRIMORIAL_LE_FOUR_POW,
            "forall n z q. "
            f"({public_primorial}) -> ({public_power}) -> ({public_result})",
            (
                "le_refl",
                PRIMORIAL_FOUR_POWER_SUPPORT_PACKAGE,
                PRIMORIAL_LE_FOUR_POW_BOUNDED,
            ),
            public_script,
            "The inclusive Primorial is bounded by four to its index.",
        ),
    )


__all__ = ["make_bertrand_primorial_four_power_candidate_theorems"]
