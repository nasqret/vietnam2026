"""Constructive modulo-eight foundations for the second supplementary law.

For an odd prime ``p = 2*h+1``, Gauss's lemma identifies residuosity of two
with the parity of the reflection count for ``2,4,...,2*h``.  That count has
the arithmetic shape ``h=2*e`` or ``h=2*k+1 and e=S k``.  This module proves
the formerly missing beta-coded count identification by showing pointwise
that every Gauss sign bit complements the floor-half initial-segment bit;
the existing exact indicator-count and complementary-BitCount theorems then
finish the count.  The resulting dependency-checked endpoints give the
unconditional positive, negative, and combined second supplementary laws.

All contracts expand to unchanged first-order constructive Peano arithmetic.
The candidates are isolated, dependency-curried, unregistered and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_initial_segment_count_candidate import (
    eisenstein_initial_segment_choice,
    eisenstein_initial_segment_prefix,
)
from .fermat_residue_map_candidate import prime
from .finite_fold_surface import beta_at, bit_count
from .gauss_signed_prefix_candidate import (
    _entry_term,
    half_range,
    signed_half_prefix,
)
from .quadratic_residue_surface import quadratic_residue


def _even(value: str, *, tag: str) -> str:
    return f"exists qst_even_{tag}. {value} = 2 * qst_even_{tag}"


def _odd(value: str, *, tag: str) -> str:
    return f"exists qst_odd_{tag}. {value} = 2 * qst_odd_{tag} + 1"


def _le(left: str, right: str, *, tag: str) -> str:
    return f"exists qst_le_{tag}. qst_le_{tag} + ({left}) = ({right})"


def _lt(left: str, right: str, *, tag: str) -> str:
    return f"exists qst_lt_{tag}. qst_lt_{tag} + S ({left}) = ({right})"


def _mod_eight(value: str, residue: int, *, tag: str) -> str:
    if residue not in (1, 3, 5, 7):
        raise ValueError("only odd residues modulo eight are supported")
    return (
        f"exists qst_mod_eight_{tag}. "
        f"{value} = 8 * qst_mod_eight_{tag} + {residue}"
    )


def _good_mod_eight(value: str, *, tag: str) -> str:
    return (
        f"(({_mod_eight(value, 1, tag=f'{tag}_one')}) \\/ "
        f"({_mod_eight(value, 7, tag=f'{tag}_seven')}))"
    )


def _bad_mod_eight(value: str, *, tag: str) -> str:
    return (
        f"(({_mod_eight(value, 3, tag=f'{tag}_three')}) \\/ "
        f"({_mod_eight(value, 5, tag=f'{tag}_five')}))"
    )


def _doubling_count_shape(half: str, count: str, *, tag: str) -> str:
    return (
        f"(({half} = 2 * {count}) \\/ "
        f"(exists qst_count_half_{tag}. "
        f"{half} = 2 * qst_count_half_{tag} + 1 /\\ "
        f"{count} = S qst_count_half_{tag}))"
    )


def _quadratic_residue_two(modulus: str, *, tag: str) -> str:
    root = f"qst_root_{tag}"
    left = f"qst_mod_left_{tag}"
    right = f"qst_mod_right_{tag}"
    return (
        f"exists {root}. exists {left} {right}. "
        f"{root} * {root} + {modulus} * {left} = "
        f"2 + {modulus} * {right}"
    )


def _iff(left: str, right: str) -> str:
    return f"((({left}) -> ({right})) /\\ (({right}) -> ({left})))"


def _complementary_prefix(
    sign_code: str,
    sign_scale: str,
    indicator_code: str,
    indicator_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    sign = beta_at(sign_code, sign_scale, "i", "s", tag=f"qst_{tag}_sign")
    indicator = beta_at(
        indicator_code,
        indicator_scale,
        "i",
        "t",
        tag=f"qst_{tag}_indicator",
    )
    return (
        f"forall i s t. (exists qst_complement_gap_{tag}. "
        f"qst_complement_gap_{tag} + S i = {length}) -> "
        f"({sign}) -> ({indicator}) -> "
        "((s = 0 /\\ t = 1) \\/ (s = 1 /\\ t = 0))"
    )


_GOAL_HALF_RANGE = half_range("b", "c", "h", tag="qst_goal_half")
_GOAL_SIGNED_PREFIX = signed_half_prefix(
    "p",
    "h",
    "a",
    "b",
    "c",
    "mb",
    "mc",
    "sb",
    "sc",
    "h",
    tag="qst_goal_signed",
)
_GOAL_SIGN_COUNT = bit_count("sb", "sc", "h", "e", tag="qst_goal_count")
_GOAL_INITIAL_PREFIX = eisenstein_initial_segment_prefix(
    "k", "ib", "ic", "h", tag="qst_goal_initial"
)
_GOAL_COMPLEMENT = _complementary_prefix(
    "sb", "sc", "ib", "ic", "h", tag="goal"
)


DOUBLING_GAUSS_REFLECTION_COUNT_SHAPE_GOAL = (
    "forall p h a b c mb mc sb sc e. p = 2 * h + 1 -> a = 2 -> "
    f"({_GOAL_HALF_RANGE}) -> ({_GOAL_SIGNED_PREFIX}) -> "
    f"({_GOAL_SIGN_COUNT}) -> "
    f"({_doubling_count_shape('h', 'e', tag='goal')})"
)
"""Exact pinned target proved by ``doubling_gauss_reflection_count_shape``."""


DOUBLING_GAUSS_INITIAL_SEGMENT_COMPLEMENT_GOAL = (
    "forall p h a b c mb mc sb sc ib ic k. "
    "p = 2 * h + 1 -> a = 2 -> "
    "((h = 2 * k) \\/ (h = 2 * k + 1)) -> "
    f"({_GOAL_HALF_RANGE}) -> ({_GOAL_SIGNED_PREFIX}) -> "
    f"({_GOAL_INITIAL_PREFIX}) -> ({_GOAL_COMPLEMENT})"
)
"""Exact pinned target proved by ``doubling_gauss_initial_segment_complement``."""


def make_quadratic_supplement_two_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the constructive modulo-eight and count-shape foundation."""

    odd_p = _odd("p", tag="modulus")
    mod_one = _mod_eight("p", 1, tag="one")
    mod_three = _mod_eight("p", 3, tag="three")
    mod_five = _mod_eight("p", 5, tag="five")
    mod_seven = _mod_eight("p", 7, tag="seven")
    odd_mod_eight_cases = (
        f"(({mod_one}) \\/ (({mod_three}) \\/ "
        f"(({mod_five}) \\/ ({mod_seven}))))"
    )
    count_shape = _doubling_count_shape("h", "e", tag="shape")
    good_p = _good_mod_eight("p", tag="modulus")
    bad_p = _bad_mod_eight("p", tag="modulus")
    even_e = _even("e", tag="count")
    odd_e = _odd("e", tag="count")
    parity_classification = (
        f"(({_iff(even_e, good_p)}) /\\ ({_iff(odd_e, bad_p)}))"
    )
    qres_two = _quadratic_residue_two("p", tag="two")
    gauss_classification = (
        f"(({_iff(qres_two, even_e)}) /\\ "
        f"({_iff(f'~({qres_two})', odd_e)}))"
    )
    conditional_law = (
        f"(({_iff(qres_two, good_p)}) /\\ "
        f"({_iff(f'~({qres_two})', bad_p)}))"
    )
    half_shape = "((h = 2 * k) \\/ (h = 2 * k + 1))"
    initial_prefix = eisenstein_initial_segment_prefix(
        "k", "ib", "ic", "h", tag="qst_initial_prefix"
    )
    sign_count = bit_count("sb", "sc", "h", "e", tag="qst_sign_count")
    initial_count = bit_count("ib", "ic", "h", "k", tag="qst_initial_count")
    complement = _complementary_prefix(
        "sb", "sc", "ib", "ic", "h", tag="count"
    )
    floor_le = _le("x", "k", tag="floor")
    floor_lt = _lt("k", "x", tag="floor")
    doubled_le_half = _le("2 * x", "h", tag="doubled")
    doubled_above_half = _lt("h", "2 * x", tag="doubled")
    value_le_half = _le("x", "h", tag="source")
    doubled_below_modulus = _lt("2 * x", "p", tag="canonical")
    magnitude_le_half = _le("m", "h", tag="magnitude")
    alignment_entry = _entry_term(
        "p",
        "h",
        "a",
        "b",
        "c",
        "mb",
        "mc",
        "sb",
        "sc",
        "i",
        tag="qst_alignment",
        variables=(
            "p",
            "h",
            "a",
            "b",
            "c",
            "mb",
            "mc",
            "sb",
            "sc",
            "ib",
            "ic",
            "k",
            "i",
            "s",
            "t",
        ),
    )
    alignment_choice = eisenstein_initial_segment_choice(
        "k", "i", "t", tag="qst_alignment_choice"
    )
    alignment_root = "hentry_witness_witness_witness"
    alignment_positive = f"{alignment_root}_right_right_right_left"
    alignment_bounded = f"{alignment_root}_right_right_right_right_left"
    alignment_branch = f"{alignment_root}_right_right_right_right_right_right"
    a_qres = quadratic_residue("p", "a", tag="qst_gauss_two")
    a_classification = (
        f"(({_iff(a_qres, even_e)}) /\\ "
        f"({_iff(f'~({a_qres})', odd_e)}))"
    )
    gauss_signed = signed_half_prefix(
        "p",
        "h",
        "a",
        "x",
        "x1",
        "mb",
        "mc",
        "sb",
        "sc",
        "h",
        tag="qst_gauss_signed",
    )
    gauss_count = bit_count("sb", "sc", "h", "e", tag="qst_gauss_count")
    gauss_package = (
        "exists e. "
        f"((exists mb mc sb sc. (({gauss_signed}) /\\ ({gauss_count}))) /\\ "
        f"({a_classification}))"
    )

    return (
        spec(
            "eight_mul_eq_double_four",
            "forall a. 8 * a = 2 * (4 * a)",
            ("mul_assoc",),
            (
                "intro a",
                "trans (2 * 4) * a",
                "congr",
                "norm_num",
                "refl",
                "apply mul_assoc",
            ),
            "Multiplication by eight is twice multiplication by four.",
        ),
        spec(
            "odd_mod_eight_cases",
            f"forall p. ({odd_p}) -> ({odd_mod_eight_cases})",
            (
                "parity_cases",
                "mul_add",
                "four_mul_eq_double_double",
                "eight_mul_eq_double_four",
            ),
            (
                "intro p",
                "intro hodd",
                "cases hodd",
                "have hhalf_parity : exists a. x = 2 * a \\/ x = 2 * a + 1",
                "specialize parity_cases x",
                "exact parity_cases",
                "cases hhalf_parity",
                "cases hhalf_parity_witness",
                "have hquarter_parity : exists b. x1 = 2 * b \\/ x1 = 2 * b + 1",
                "specialize parity_cases x1",
                "exact parity_cases",
                "cases hquarter_parity",
                "cases hquarter_parity_witness",
                "left",
                "exists x2",
                "rewrite hodd_witness",
                "rewrite hhalf_parity_witness_left",
                "rewrite hquarter_parity_witness_left",
                "simp [mul_add, four_mul_eq_double_double, eight_mul_eq_double_four]",
                "right",
                "right",
                "left",
                "exists x2",
                "rewrite hodd_witness",
                "rewrite hhalf_parity_witness_left",
                "rewrite hquarter_parity_witness_right",
                "simp [mul_add, four_mul_eq_double_double, eight_mul_eq_double_four]",
                "have hquarter_parity : exists b. x1 = 2 * b \\/ x1 = 2 * b + 1",
                "specialize parity_cases x1",
                "exact parity_cases",
                "cases hquarter_parity",
                "cases hquarter_parity_witness",
                "right",
                "left",
                "exists x2",
                "rewrite hodd_witness",
                "rewrite hhalf_parity_witness_right",
                "rewrite hquarter_parity_witness_left",
                "simp [mul_add, four_mul_eq_double_double, eight_mul_eq_double_four]",
                "right",
                "right",
                "right",
                "exists x2",
                "rewrite hodd_witness",
                "rewrite hhalf_parity_witness_right",
                "rewrite hquarter_parity_witness_right",
                "simp [mul_add, four_mul_eq_double_double, eight_mul_eq_double_four]",
            ),
            "Every odd natural constructively belongs to one of the four "
            "residue classes one, three, five or seven modulo eight.",
        ),
        spec(
            "doubling_gauss_count_shape_exists",
            f"forall h. exists e. ({count_shape})",
            ("parity_cases",),
            (
                "intro h",
                "specialize parity_cases h",
                "cases parity_cases",
                "cases parity_cases_witness",
                "exists x",
                "left",
                "exact parity_cases_witness_left",
                "exists S x",
                "right",
                "exists x",
                "split",
                "exact parity_cases_witness_right",
                "refl",
            ),
            "The explicit reflection-count shape for doubling exists "
            "constructively for every odd-prime half.",
        ),
        spec(
            "mod_eight_remainder_unique",
            "forall p a r b s. p = 8 * a + r -> "
            "(exists u. u + S r = 8) -> p = 8 * b + s -> "
            "(exists v. v + S s = 8) -> r = s",
            ("division_remainder_unique",),
            (
                "intro p",
                "intro a",
                "intro r",
                "intro b",
                "intro s",
                "intro hfirst",
                "intro hrbound",
                "intro hsecond",
                "intro hsbound",
                "have hunique : a = b /\\ r = s",
                "specialize division_remainder_unique 8",
                "specialize division_remainder_unique p",
                "specialize division_remainder_unique a",
                "specialize division_remainder_unique r",
                "specialize division_remainder_unique b",
                "specialize division_remainder_unique s",
                "apply division_remainder_unique",
                "exact hfirst",
                "exact hrbound",
                "exact hsecond",
                "exact hsbound",
                "cases hunique",
                "exact hunique_right",
            ),
            "Two bounded decompositions modulo eight have the same remainder.",
        ),
        spec(
            "mod_eight_good_bad_exclusive",
            f"forall p. ({good_p}) -> ({bad_p}) -> false",
            ("mod_eight_remainder_unique",),
            (
                "intro p",
                "intro hgood",
                "intro hbad",
                "cases hgood",
                "cases hgood_left",
                "cases hbad",
                "cases hbad_left",
                "have hremainders : 1 = 3",
                "specialize mod_eight_remainder_unique p",
                "specialize mod_eight_remainder_unique x",
                "specialize mod_eight_remainder_unique 1",
                "specialize mod_eight_remainder_unique x1",
                "specialize mod_eight_remainder_unique 3",
                "apply mod_eight_remainder_unique",
                "exact hgood_left_witness",
                "exists 6",
                "norm_num",
                "exact hbad_left_witness",
                "exists 4",
                "norm_num",
                "have hzero : 0 = 2",
                "apply PA2",
                "exact hremainders",
                "apply PA1",
                "symm",
                "exact hzero",
                "cases hbad_right",
                "have hremainders : 1 = 5",
                "specialize mod_eight_remainder_unique p",
                "specialize mod_eight_remainder_unique x",
                "specialize mod_eight_remainder_unique 1",
                "specialize mod_eight_remainder_unique x1",
                "specialize mod_eight_remainder_unique 5",
                "apply mod_eight_remainder_unique",
                "exact hgood_left_witness",
                "exists 6",
                "norm_num",
                "exact hbad_right_witness",
                "exists 2",
                "norm_num",
                "have hzero : 0 = 4",
                "apply PA2",
                "exact hremainders",
                "apply PA1",
                "symm",
                "exact hzero",
                "cases hgood_right",
                "cases hbad",
                "cases hbad_left",
                "have hremainders : 7 = 3",
                "specialize mod_eight_remainder_unique p",
                "specialize mod_eight_remainder_unique x",
                "specialize mod_eight_remainder_unique 7",
                "specialize mod_eight_remainder_unique x1",
                "specialize mod_eight_remainder_unique 3",
                "apply mod_eight_remainder_unique",
                "exact hgood_right_witness",
                "exists 0",
                "norm_num",
                "exact hbad_left_witness",
                "exists 4",
                "norm_num",
                "have hfirst : 6 = 2",
                "apply PA2",
                "exact hremainders",
                "have hsecond : 5 = 1",
                "apply PA2",
                "exact hfirst",
                "have hzero : 4 = 0",
                "apply PA2",
                "exact hsecond",
                "apply PA1",
                "exact hzero",
                "cases hbad_right",
                "have hremainders : 7 = 5",
                "specialize mod_eight_remainder_unique p",
                "specialize mod_eight_remainder_unique x",
                "specialize mod_eight_remainder_unique 7",
                "specialize mod_eight_remainder_unique x1",
                "specialize mod_eight_remainder_unique 5",
                "apply mod_eight_remainder_unique",
                "exact hgood_right_witness",
                "exists 0",
                "norm_num",
                "exact hbad_right_witness",
                "exists 2",
                "norm_num",
                "have hfirst : 6 = 4",
                "apply PA2",
                "exact hremainders",
                "have hsecond : 5 = 3",
                "apply PA2",
                "exact hfirst",
                "have hthird : 4 = 2",
                "apply PA2",
                "exact hsecond",
                "have hfourth : 3 = 1",
                "apply PA2",
                "exact hthird",
                "have hzero : 2 = 0",
                "apply PA2",
                "exact hfourth",
                "apply PA1",
                "exact hzero",
            ),
            "The favorable modulo-eight classes one and seven cannot equal "
            "the unfavorable classes three and five.",
        ),
        spec(
            "doubling_gauss_even_count_implies_good_mod_eight",
            f"forall p h e. p = 2 * h + 1 -> ({count_shape}) -> "
            f"({even_e}) -> ({good_p})",
            (
                "even_successor_to_odd",
                "mul_add",
                "four_mul_eq_double_double",
                "eight_mul_eq_double_four",
            ),
            (
                "intro p",
                "intro h",
                "intro e",
                "intro hodd",
                "intro hshape",
                "intro heven",
                "cases hshape",
                "cases heven",
                "left",
                "exists x",
                "rewrite hodd",
                "rewrite hshape_left",
                "rewrite heven_witness",
                "simp [mul_add, four_mul_eq_double_double, eight_mul_eq_double_four]",
                "cases hshape_right",
                "cases hshape_right_witness",
                "cases heven",
                "have hodd_half : exists a. x = 2 * a + 1",
                "specialize even_successor_to_odd x",
                "apply even_successor_to_odd",
                "exists x1",
                "trans e",
                "symm",
                "exact hshape_right_witness_right",
                "exact heven_witness",
                "cases hodd_half",
                "right",
                "exists x2",
                "rewrite hodd",
                "rewrite hshape_right_witness_left",
                "rewrite hodd_half_witness",
                "simp [mul_add, four_mul_eq_double_double, eight_mul_eq_double_four]",
            ),
            "An even doubling reflection count forces the prime to be one or "
            "seven modulo eight.",
        ),
        spec(
            "doubling_gauss_odd_count_implies_bad_mod_eight",
            f"forall p h e. p = 2 * h + 1 -> ({count_shape}) -> "
            f"({odd_e}) -> ({bad_p})",
            (
                "odd_successor_to_even",
                "mul_add",
                "four_mul_eq_double_double",
                "eight_mul_eq_double_four",
            ),
            (
                "intro p",
                "intro h",
                "intro e",
                "intro hpodd",
                "intro hshape",
                "intro hodd",
                "cases hshape",
                "cases hodd",
                "right",
                "exists x",
                "rewrite hpodd",
                "rewrite hshape_left",
                "rewrite hodd_witness",
                "simp [mul_add, four_mul_eq_double_double, eight_mul_eq_double_four]",
                "cases hshape_right",
                "cases hshape_right_witness",
                "cases hodd",
                "have heven_half : exists a. x = 2 * a",
                "specialize odd_successor_to_even x",
                "apply odd_successor_to_even",
                "exists x1",
                "trans e",
                "symm",
                "exact hshape_right_witness_right",
                "exact hodd_witness",
                "cases heven_half",
                "left",
                "exists x2",
                "rewrite hpodd",
                "rewrite hshape_right_witness_left",
                "rewrite heven_half_witness",
                "simp [mul_add, four_mul_eq_double_double, eight_mul_eq_double_four]",
            ),
            "An odd doubling reflection count forces the prime to be three or "
            "five modulo eight.",
        ),
        spec(
            "doubling_gauss_count_parity_mod_eight_complete",
            f"forall p h e. p = 2 * h + 1 -> ({count_shape}) -> "
            f"({parity_classification})",
            (
                "doubling_gauss_even_count_implies_good_mod_eight",
                "doubling_gauss_odd_count_implies_bad_mod_eight",
                "mod_eight_good_bad_exclusive",
                "parity_cases",
            ),
            (
                "intro p",
                "intro h",
                "intro e",
                "intro hpodd",
                "intro hshape",
                "split",
                "split",
                "intro heven",
                "specialize doubling_gauss_even_count_implies_good_mod_eight p",
                "specialize doubling_gauss_even_count_implies_good_mod_eight h",
                "specialize doubling_gauss_even_count_implies_good_mod_eight e",
                "apply doubling_gauss_even_count_implies_good_mod_eight",
                "exact hpodd",
                "exact hshape",
                "exact heven",
                "intro hgood",
                "specialize parity_cases e",
                "cases parity_cases",
                "cases parity_cases_witness",
                "exists x",
                "exact parity_cases_witness_left",
                "exfalso",
                "specialize mod_eight_good_bad_exclusive p",
                "apply mod_eight_good_bad_exclusive",
                "exact hgood",
                "specialize doubling_gauss_odd_count_implies_bad_mod_eight p",
                "specialize doubling_gauss_odd_count_implies_bad_mod_eight h",
                "specialize doubling_gauss_odd_count_implies_bad_mod_eight e",
                "apply doubling_gauss_odd_count_implies_bad_mod_eight",
                "exact hpodd",
                "exact hshape",
                "exists x",
                "exact parity_cases_witness_right",
                "split",
                "intro hodd",
                "specialize doubling_gauss_odd_count_implies_bad_mod_eight p",
                "specialize doubling_gauss_odd_count_implies_bad_mod_eight h",
                "specialize doubling_gauss_odd_count_implies_bad_mod_eight e",
                "apply doubling_gauss_odd_count_implies_bad_mod_eight",
                "exact hpodd",
                "exact hshape",
                "exact hodd",
                "intro hbad",
                "specialize parity_cases e",
                "cases parity_cases",
                "cases parity_cases_witness",
                "exfalso",
                "specialize mod_eight_good_bad_exclusive p",
                "apply mod_eight_good_bad_exclusive",
                "specialize doubling_gauss_even_count_implies_good_mod_eight p",
                "specialize doubling_gauss_even_count_implies_good_mod_eight h",
                "specialize doubling_gauss_even_count_implies_good_mod_eight e",
                "apply doubling_gauss_even_count_implies_good_mod_eight",
                "exact hpodd",
                "exact hshape",
                "exists x",
                "exact parity_cases_witness_left",
                "exact hbad",
                "exists x",
                "exact parity_cases_witness_right",
            ),
            "For the exact doubling reflection-count shape, evenness is "
            "equivalent to classes one/seven and oddness to three/five.",
        ),
        spec(
            "doubling_floor_below_implies_double_at_most_half",
            f"forall h k x. ({half_shape}) -> ({floor_le}) -> "
            f"({doubled_le_half})",
            ("mul_le_mul_left", "add_succ_left"),
            (
                "intro h",
                "intro k",
                "intro x",
                "intro hhalf",
                "intro hfloor",
                "have hscaled : exists gap. gap + 2 * x = 2 * k",
                "specialize mul_le_mul_left x",
                "specialize mul_le_mul_left k",
                "specialize mul_le_mul_left 2",
                "apply mul_le_mul_left",
                "exact hfloor",
                "cases hhalf",
                "rewrite hhalf_left",
                "exact hscaled",
                "cases hscaled",
                "exists S x1",
                "trans S (x1 + 2 * x)",
                "apply add_succ_left",
                "rewrite hscaled_witness",
                "rewrite hhalf_right",
                "simp",
            ),
            "A source at most the odd-half floor has doubled value at most the half.",
        ),
        spec(
            "doubling_floor_above_implies_double_above_half",
            f"forall h k x. ({half_shape}) -> ({floor_lt}) -> "
            f"({doubled_above_half})",
            ("mul_add", "add_assoc", "add_comm", "add_succ_left"),
            (
                "intro h",
                "intro k",
                "intro x",
                "intro hhalf",
                "intro habove",
                "cases habove",
                "cases hhalf",
                "exists 2 * x1 + 1",
                "rewrite hhalf_left",
                "rewrite <- habove_witness",
                "simp [mul_add, add_assoc, add_comm]",
                "congr",
                "apply add_succ_left",
                "exists 2 * x1",
                "rewrite hhalf_right",
                "rewrite <- habove_witness",
                "simp [mul_add, add_assoc, add_comm]",
            ),
            "A source strictly above the odd-half floor doubles beyond the half.",
        ),
        spec(
            "doubling_half_range_below_odd_modulus",
            f"forall p h x. p = 2 * h + 1 -> ({value_le_half}) -> "
            f"({doubled_below_modulus})",
            ("mul_le_mul_left",),
            (
                "intro p",
                "intro h",
                "intro x",
                "intro hpodd",
                "intro hxbelow",
                "have hscaled : exists gap. gap + 2 * x = 2 * h",
                "specialize mul_le_mul_left x",
                "specialize mul_le_mul_left h",
                "specialize mul_le_mul_left 2",
                "apply mul_le_mul_left",
                "exact hxbelow",
                "cases hscaled",
                "exists x1",
                "trans S (x1 + 2 * x)",
                "apply PA4",
                "rewrite hscaled_witness",
                "rewrite hpodd",
                "simp",
            ),
            "Doubling a value in the canonical half range never wraps modulo the odd modulus.",
        ),
        spec(
            "reflected_double_above_odd_half",
            f"forall p h x m. p = 2 * h + 1 -> ({magnitude_le_half}) -> "
            f"2 * x + m = p -> ({doubled_above_half})",
            (
                "add_right_cancel",
                "mul_comm",
                "zero_add",
                "add_assoc",
                "add_comm",
                "add_succ_left",
            ),
            (
                "intro p",
                "intro h",
                "intro x",
                "intro m",
                "intro hpodd",
                "intro hmbelow",
                "intro hreflection",
                "cases hmbelow",
                "have hdouble : h + h = 2 * h",
                "trans h * 2",
                "simp [zero_add]",
                "specialize mul_comm h",
                "specialize mul_comm 2",
                "apply mul_comm",
                "exists x1",
                "specialize add_right_cancel (x1 + S h)",
                "specialize add_right_cancel (2 * x)",
                "specialize add_right_cancel m",
                "apply add_right_cancel",
                "trans S (h + (x1 + m))",
                "trans S (x1 + h) + m",
                "congr",
                "apply PA4",
                "refl",
                "trans S ((x1 + h) + m)",
                "apply add_succ_left",
                "congr",
                "trans x1 + (h + m)",
                "apply add_assoc",
                "trans x1 + (m + h)",
                "congr",
                "refl",
                "apply add_comm",
                "trans (x1 + m) + h",
                "symm",
                "apply add_assoc",
                "apply add_comm",
                "rewrite hmbelow_witness",
                "rewrite hdouble",
                "trans 2 * h + 1",
                "simp",
                "trans p",
                "symm",
                "exact hpodd",
                "symm",
                "exact hreflection",
            ),
            "An exact reflected doubled value necessarily lies above the odd half.",
        ),
        spec(
            "doubling_gauss_initial_segment_complement",
            DOUBLING_GAUSS_INITIAL_SEGMENT_COMPLEMENT_GOAL,
            (
                "beta_range_entry_eq",
                "beta_at_unique",
                "eisenstein_initial_segment_decoded_choice",
                "doubling_half_range_below_odd_modulus",
                "odd_signed_division_branch_exact",
                "doubling_floor_above_implies_double_above_half",
                "doubling_floor_below_implies_double_at_most_half",
                "reflected_double_above_odd_half",
                "lt_not_le",
                "zero_add",
                "add_succ_left",
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro b",
                "intro c",
                "intro mb",
                "intro mc",
                "intro sb",
                "intro sc",
                "intro ib",
                "intro ic",
                "intro k",
                "intro hpodd",
                "intro hatwo",
                "intro hhalf",
                "intro hrange",
                "intro hsigned",
                "intro hinitial",
                "intro i",
                "intro s",
                "intro t",
                "intro hibound",
                "intro hsign",
                "intro hindicator",
                f"have hentry : {alignment_entry}",
                "specialize hsigned i",
                "apply hsigned",
                "exact hibound",
                "cases hentry",
                "cases hentry_witness",
                "cases hentry_witness_witness",
                f"cases {alignment_root}",
                f"cases {alignment_root}_right",
                f"cases {alignment_root}_right_right",
                f"cases {alignment_root}_right_right_right",
                f"cases {alignment_root}_right_right_right_right",
                f"cases {alignment_root}_right_right_right_right_right",
                "have hsource : x = 1 + i",
                "specialize beta_range_entry_eq b",
                "specialize beta_range_entry_eq c",
                "specialize beta_range_entry_eq 1",
                "specialize beta_range_entry_eq h",
                "specialize beta_range_entry_eq i",
                "specialize beta_range_entry_eq x",
                "apply beta_range_entry_eq",
                "exact hrange",
                "exact hibound",
                f"exact {alignment_root}_left",
                "have hsource_succ : x = S i",
                "trans 1 + i",
                "exact hsource",
                "trans S (0 + i)",
                "apply add_succ_left",
                "congr",
                "apply zero_add",
                "have hsource_bound : exists gap. gap + x = h",
                "rewrite hsource_succ",
                "exact hibound",
                "have hdoubled_bound : exists gap. gap + S (2 * x) = p",
                "specialize doubling_half_range_below_odd_modulus p",
                "specialize doubling_half_range_below_odd_modulus h",
                "specialize doubling_half_range_below_odd_modulus x",
                "apply doubling_half_range_below_odd_modulus",
                "exact hpodd",
                "exact hsource_bound",
                "have hsame_sign : x2 = s",
                "specialize beta_at_unique sb",
                "specialize beta_at_unique sc",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x2",
                "specialize beta_at_unique s",
                "apply beta_at_unique",
                f"exact {alignment_root}_right_right_left",
                "exact hsign",
                f"have hchoice : {alignment_choice}",
                "specialize eisenstein_initial_segment_decoded_choice k",
                "specialize eisenstein_initial_segment_decoded_choice ib",
                "specialize eisenstein_initial_segment_decoded_choice ic",
                "specialize eisenstein_initial_segment_decoded_choice h",
                "specialize eisenstein_initial_segment_decoded_choice i",
                "specialize eisenstein_initial_segment_decoded_choice t",
                "apply eisenstein_initial_segment_decoded_choice",
                "exact hinitial",
                "exact hibound",
                "exact hindicator",
                "have hexact : ((x2 = 0 /\\ 2 * x = x1) \\/ "
                "(x2 = 1 /\\ 2 * x + x1 = p))",
                "specialize odd_signed_division_branch_exact p",
                "specialize odd_signed_division_branch_exact h",
                "specialize odd_signed_division_branch_exact (2 * x)",
                "specialize odd_signed_division_branch_exact 0",
                "specialize odd_signed_division_branch_exact (2 * x)",
                "specialize odd_signed_division_branch_exact x1",
                "specialize odd_signed_division_branch_exact x2",
                "apply odd_signed_division_branch_exact",
                "exact hpodd",
                "simp",
                "symm",
                "apply zero_add",
                "exact hdoubled_bound",
                f"exact {alignment_positive}",
                f"exact {alignment_bounded}",
                f"rewrite hatwo at {alignment_branch}",
                f"rewrite hatwo at {alignment_branch}",
                f"exact {alignment_branch}",
                "cases hexact",
                "cases hexact_left",
                "cases hchoice",
                "cases hchoice_left",
                "left",
                "split",
                "trans x2",
                "symm",
                "exact hsame_sign",
                "exact hexact_left_left",
                "exact hchoice_left_left",
                "cases hchoice_right",
                "exfalso",
                "have habove : exists gap. gap + S h = 2 * x",
                "specialize doubling_floor_above_implies_double_above_half h",
                "specialize doubling_floor_above_implies_double_above_half k",
                "specialize doubling_floor_above_implies_double_above_half x",
                "apply doubling_floor_above_implies_double_above_half",
                "exact hhalf",
                "rewrite hsource_succ",
                "exact hchoice_right_right",
                "have hbelow : exists gap. gap + 2 * x = h",
                "rewrite hexact_left_right",
                f"exact {alignment_bounded}",
                "specialize lt_not_le h",
                "specialize lt_not_le (2 * x)",
                "apply lt_not_le",
                "exact habove",
                "exact hbelow",
                "cases hexact_right",
                "cases hchoice",
                "cases hchoice_left",
                "exfalso",
                "have hbelow : exists gap. gap + 2 * x = h",
                "specialize doubling_floor_below_implies_double_at_most_half h",
                "specialize doubling_floor_below_implies_double_at_most_half k",
                "specialize doubling_floor_below_implies_double_at_most_half x",
                "apply doubling_floor_below_implies_double_at_most_half",
                "exact hhalf",
                "rewrite hsource_succ",
                "exact hchoice_left_right",
                "have habove : exists gap. gap + S h = 2 * x",
                "specialize reflected_double_above_odd_half p",
                "specialize reflected_double_above_odd_half h",
                "specialize reflected_double_above_odd_half x",
                "specialize reflected_double_above_odd_half x1",
                "apply reflected_double_above_odd_half",
                "exact hpodd",
                f"exact {alignment_bounded}",
                "exact hexact_right_right",
                "specialize lt_not_le h",
                "specialize lt_not_le (2 * x)",
                "apply lt_not_le",
                "exact habove",
                "exact hbelow",
                "cases hchoice_right",
                "right",
                "split",
                "trans x2",
                "symm",
                "exact hsame_sign",
                "exact hexact_right_left",
                "exact hchoice_right_left",
            ),
            "For multiplication by two, every actual Gauss sign bit is "
            "exactly complementary to the floor-half initial-segment bit.",
        ),
        spec(
            "doubling_half_decomposition_lower_bound",
            f"forall h k. ({half_shape}) -> exists gap. gap + k = h",
            ("mul_comm", "zero_add", "add_succ_left"),
            (
                "intro h",
                "intro k",
                "intro hshape",
                "have hdouble : k + k = 2 * k",
                "trans k * 2",
                "simp [zero_add]",
                "specialize mul_comm k",
                "specialize mul_comm 2",
                "apply mul_comm",
                "cases hshape",
                "exists k",
                "trans 2 * k",
                "exact hdouble",
                "symm",
                "exact hshape_left",
                "exists S k",
                "trans S (k + k)",
                "apply add_succ_left",
                "trans S (2 * k)",
                "congr",
                "exact hdouble",
                "trans 2 * k + 1",
                "simp",
                "symm",
                "exact hshape_right",
            ),
            "A natural half in either doubled decomposition is at most the full length.",
        ),
        spec(
            "doubling_gauss_count_shape_from_initial_segment_complement",
            "forall h k sb sc ib ic e. "
            f"({half_shape}) -> ({initial_prefix}) -> ({sign_count}) -> "
            f"({complement}) -> ({count_shape})",
            (
                "doubling_half_decomposition_lower_bound",
                "eisenstein_initial_segment_bit_count_exact",
                "complementary_bit_counts_add_length",
                "mul_comm",
                "zero_add",
                "add_succ_left",
                "add_right_cancel",
            ),
            (
                "intro h",
                "intro k",
                "intro sb",
                "intro sc",
                "intro ib",
                "intro ic",
                "intro e",
                "intro hhalf",
                "intro hinitial",
                "intro hsigncount",
                "intro hcomplement",
                "have hbound : exists gap. gap + k = h",
                "specialize doubling_half_decomposition_lower_bound h",
                "specialize doubling_half_decomposition_lower_bound k",
                "apply doubling_half_decomposition_lower_bound",
                "exact hhalf",
                f"have hinitialcount : {initial_count}",
                "specialize eisenstein_initial_segment_bit_count_exact k",
                "specialize eisenstein_initial_segment_bit_count_exact ib",
                "specialize eisenstein_initial_segment_bit_count_exact ic",
                "specialize eisenstein_initial_segment_bit_count_exact h",
                "apply eisenstein_initial_segment_bit_count_exact",
                "exact hinitial",
                "exact hbound",
                "have hsum : e + k = h",
                "specialize complementary_bit_counts_add_length sb",
                "specialize complementary_bit_counts_add_length sc",
                "specialize complementary_bit_counts_add_length ib",
                "specialize complementary_bit_counts_add_length ic",
                "specialize complementary_bit_counts_add_length h",
                "specialize complementary_bit_counts_add_length e",
                "specialize complementary_bit_counts_add_length k",
                "apply complementary_bit_counts_add_length",
                "exact hsigncount",
                "exact hinitialcount",
                "exact hcomplement",
                "have hdouble : k + k = 2 * k",
                "trans k * 2",
                "simp [zero_add]",
                "specialize mul_comm k",
                "specialize mul_comm 2",
                "apply mul_comm",
                "cases hhalf",
                "have heq : e = k",
                "specialize add_right_cancel e",
                "specialize add_right_cancel k",
                "specialize add_right_cancel k",
                "apply add_right_cancel",
                "trans h",
                "exact hsum",
                "trans 2 * k",
                "exact hhalf_left",
                "symm",
                "exact hdouble",
                "left",
                "rewrite heq",
                "exact hhalf_left",
                "have hsuccessor : S k + k = 2 * k + 1",
                "trans S (k + k)",
                "apply add_succ_left",
                "trans S (2 * k)",
                "congr",
                "exact hdouble",
                "simp",
                "have heq : e = S k",
                "specialize add_right_cancel e",
                "specialize add_right_cancel (S k)",
                "specialize add_right_cancel k",
                "apply add_right_cancel",
                "trans h",
                "exact hsum",
                "trans 2 * k + 1",
                "exact hhalf_right",
                "symm",
                "exact hsuccessor",
                "right",
                "exists k",
                "split",
                "exact hhalf_right",
                "exact heq",
            ),
            "The existing initial-segment count and complementary BitCount "
            "theorems prove the exact doubling reflection-count shape once "
            "pointwise complementarity of the actual signs is supplied.",
        ),
        spec(
            "doubling_gauss_reflection_count_shape",
            DOUBLING_GAUSS_REFLECTION_COUNT_SHAPE_GOAL,
            (
                "parity_cases",
                "eisenstein_initial_segment_prefix_exists",
                "doubling_gauss_initial_segment_complement",
                "doubling_gauss_count_shape_from_initial_segment_complement",
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro b",
                "intro c",
                "intro mb",
                "intro mc",
                "intro sb",
                "intro sc",
                "intro e",
                "intro hpodd",
                "intro hatwo",
                "intro hrange",
                "intro hsigned",
                "intro hcount",
                "have hhalf : exists k. h = 2 * k \\/ h = 2 * k + 1",
                "specialize parity_cases h",
                "exact parity_cases",
                "cases hhalf",
                "have hinitial : exists ib ic. "
                f"({eisenstein_initial_segment_prefix('x', 'ib', 'ic', 'h', tag='qst_shape_initial')})",
                "specialize eisenstein_initial_segment_prefix_exists x",
                "specialize eisenstein_initial_segment_prefix_exists h",
                "exact eisenstein_initial_segment_prefix_exists",
                "cases hinitial",
                "cases hinitial_witness",
                "have hcomplement : "
                f"({_complementary_prefix('sb', 'sc', 'x1', 'x2', 'h', tag='shape')})",
                "specialize doubling_gauss_initial_segment_complement p",
                "specialize doubling_gauss_initial_segment_complement h",
                "specialize doubling_gauss_initial_segment_complement a",
                "specialize doubling_gauss_initial_segment_complement b",
                "specialize doubling_gauss_initial_segment_complement c",
                "specialize doubling_gauss_initial_segment_complement mb",
                "specialize doubling_gauss_initial_segment_complement mc",
                "specialize doubling_gauss_initial_segment_complement sb",
                "specialize doubling_gauss_initial_segment_complement sc",
                "specialize doubling_gauss_initial_segment_complement x1",
                "specialize doubling_gauss_initial_segment_complement x2",
                "specialize doubling_gauss_initial_segment_complement x",
                "apply doubling_gauss_initial_segment_complement",
                "exact hpodd",
                "exact hatwo",
                "exact hhalf_witness",
                "exact hrange",
                "exact hsigned",
                "exact hinitial_witness_witness",
                "specialize doubling_gauss_count_shape_from_initial_segment_complement h",
                "specialize doubling_gauss_count_shape_from_initial_segment_complement x",
                "specialize doubling_gauss_count_shape_from_initial_segment_complement sb",
                "specialize doubling_gauss_count_shape_from_initial_segment_complement sc",
                "specialize doubling_gauss_count_shape_from_initial_segment_complement x1",
                "specialize doubling_gauss_count_shape_from_initial_segment_complement x2",
                "specialize doubling_gauss_count_shape_from_initial_segment_complement e",
                "apply doubling_gauss_count_shape_from_initial_segment_complement",
                "exact hhalf_witness",
                "exact hinitial_witness_witness",
                "exact hcount",
                "exact hcomplement",
            ),
            "The beta-coded Gauss reflection count for multiplication by two "
            "has exactly the explicit ceiling-half shape.",
        ),
        spec(
            "quadratic_supplement_two_conditional_on_gauss_count_shape",
            f"forall p h e. p = 2 * h + 1 -> "
            f"({prime('p', tag='qst_prime')}) -> ({count_shape}) -> "
            f"({gauss_classification}) -> ({conditional_law})",
            ("doubling_gauss_count_parity_mod_eight_complete",),
            (
                "intro p",
                "intro h",
                "intro e",
                "intro hpodd",
                "intro hprime",
                "intro hshape",
                "intro hgauss",
                f"have hparity : {parity_classification}",
                "specialize doubling_gauss_count_parity_mod_eight_complete p",
                "specialize doubling_gauss_count_parity_mod_eight_complete h",
                "specialize doubling_gauss_count_parity_mod_eight_complete e",
                "apply doubling_gauss_count_parity_mod_eight_complete",
                "exact hpodd",
                "exact hshape",
                "cases hgauss",
                "cases hgauss_left",
                "cases hgauss_right",
                "cases hparity",
                "cases hparity_left",
                "cases hparity_right",
                "split",
                "split",
                "intro hresidue",
                "apply hparity_left_left",
                "apply hgauss_left_left",
                "exact hresidue",
                "intro hgood",
                "apply hgauss_left_right",
                "apply hparity_left_right",
                "exact hgood",
                "split",
                "intro hnonresidue",
                "apply hparity_right_left",
                "apply hgauss_right_left",
                "exact hnonresidue",
                "intro hbad",
                "intro hresidue",
                "apply hgauss_right_right",
                "apply hparity_right_right",
                "exact hbad",
                "exact hresidue",
            ),
            "The exact second supplementary law follows constructively once "
            "the existing Gauss reflection count is identified with the "
            "explicit doubling-count shape.",
        ),
        spec(
            "odd_prime_strictly_exceeds_two",
            "forall p h. p = 2 * h + 1 -> "
            f"({prime('p', tag='qst_bounded_prime')}) -> "
            "exists gap. gap + S 2 = p",
            ("nonzero_is_succ", "mul_add", "zero_add"),
            (
                "intro p",
                "intro h",
                "intro hpodd",
                "intro hprime",
                "have hnonzero : ~(h = 0)",
                "intro hzero",
                "cases hprime",
                "apply hprime_left",
                "rewrite hpodd",
                "rewrite hzero",
                "norm_num",
                "have hsuccessor : exists k. h = S k",
                "specialize nonzero_is_succ h",
                "apply nonzero_is_succ",
                "exact hnonzero",
                "cases hsuccessor",
                "exists 2 * x",
                "rewrite hpodd",
                "rewrite hsuccessor_witness",
                "simp [mul_add, zero_add]",
            ),
            "Every prime admitting an odd decomposition is strictly greater than two.",
        ),
        spec(
            "quadratic_supplement_two_half_complete",
            f"forall p h a. p = 2 * h + 1 -> "
            f"({prime('p', tag='qst_half_prime')}) -> a = 2 -> "
            f"({conditional_law})",
            (
                "odd_prime_strictly_exceeds_two",
                "beta_range_exists",
                "bounded_gauss_lemma_complete",
                "doubling_gauss_reflection_count_shape",
                "quadratic_supplement_two_conditional_on_gauss_count_shape",
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro hpodd",
                "intro hprime",
                "intro hatwo",
                "have hpositive : exists gap. gap + S 0 = a",
                "exists 1",
                "rewrite hatwo",
                "norm_num",
                "have hbound : exists gap. gap + S a = p",
                "rewrite hatwo",
                "specialize odd_prime_strictly_exceeds_two p",
                "specialize odd_prime_strictly_exceeds_two h",
                "apply odd_prime_strictly_exceeds_two",
                "exact hpodd",
                "exact hprime",
                "have hrange : exists b c. "
                f"({half_range('b', 'c', 'h', tag='qst_gauss_range')})",
                "specialize beta_range_exists 1",
                "specialize beta_range_exists h",
                "exact beta_range_exists",
                "cases hrange",
                "cases hrange_witness",
                f"have hgauss : {gauss_package}",
                "specialize bounded_gauss_lemma_complete p",
                "specialize bounded_gauss_lemma_complete h",
                "specialize bounded_gauss_lemma_complete a",
                "specialize bounded_gauss_lemma_complete x",
                "specialize bounded_gauss_lemma_complete x1",
                "apply bounded_gauss_lemma_complete",
                "exact hpodd",
                "exact hprime",
                "exact hpositive",
                "exact hbound",
                "exact hrange_witness_witness",
                "cases hgauss",
                "cases hgauss_witness",
                "cases hgauss_witness_left",
                "cases hgauss_witness_left_witness",
                "cases hgauss_witness_left_witness_witness",
                "cases hgauss_witness_left_witness_witness_witness",
                "cases hgauss_witness_left_witness_witness_witness_witness",
                "have hshape : "
                f"({_doubling_count_shape('h', 'x2', tag='qst_gauss_final_shape')})",
                "specialize doubling_gauss_reflection_count_shape p",
                "specialize doubling_gauss_reflection_count_shape h",
                "specialize doubling_gauss_reflection_count_shape a",
                "specialize doubling_gauss_reflection_count_shape x",
                "specialize doubling_gauss_reflection_count_shape x1",
                "specialize doubling_gauss_reflection_count_shape x3",
                "specialize doubling_gauss_reflection_count_shape x4",
                "specialize doubling_gauss_reflection_count_shape x5",
                "specialize doubling_gauss_reflection_count_shape x6",
                "specialize doubling_gauss_reflection_count_shape x2",
                "apply doubling_gauss_reflection_count_shape",
                "exact hpodd",
                "exact hatwo",
                "exact hrange_witness_witness",
                "exact hgauss_witness_left_witness_witness_witness_witness_left",
                "exact hgauss_witness_left_witness_witness_witness_witness_right",
                "specialize quadratic_supplement_two_conditional_on_gauss_count_shape p",
                "specialize quadratic_supplement_two_conditional_on_gauss_count_shape h",
                "specialize quadratic_supplement_two_conditional_on_gauss_count_shape x2",
                "apply quadratic_supplement_two_conditional_on_gauss_count_shape",
                "exact hpodd",
                "exact hprime",
                "exact hshape",
                "rewrite hatwo at hgauss_witness_right",
                "rewrite hatwo at hgauss_witness_right",
                "rewrite hatwo at hgauss_witness_right",
                "rewrite hatwo at hgauss_witness_right",
                "exact hgauss_witness_right",
            ),
            "Complete constructive second supplementary law for an explicitly "
            "decomposed odd prime, with no unproved count-shape hypothesis.",
        ),
        spec(
            "quadratic_supplement_two_residue_iff_mod_eight_one_or_seven",
            f"forall p. ({prime('p', tag='qst_endpoint_prime')}) -> "
            f"({odd_p}) -> ({_iff(qres_two, good_p)})",
            ("quadratic_supplement_two_half_complete",),
            (
                "intro p",
                "intro hprime",
                "intro hodd",
                "cases hodd",
                f"have hcomplete : {conditional_law}",
                "specialize quadratic_supplement_two_half_complete p",
                "specialize quadratic_supplement_two_half_complete x",
                "specialize quadratic_supplement_two_half_complete 2",
                "apply quadratic_supplement_two_half_complete",
                "exact hodd_witness",
                "exact hprime",
                "refl",
                "cases hcomplete",
                "exact hcomplete_left",
            ),
            "The second supplementary law: two is a quadratic residue modulo "
            "an odd prime exactly in classes one and seven modulo eight.",
        ),
        spec(
            "quadratic_supplement_two_nonresidue_iff_mod_eight_three_or_five",
            f"forall p. ({prime('p', tag='qst_endpoint_prime')}) -> "
            f"({odd_p}) -> ({_iff(f'~({qres_two})', bad_p)})",
            ("quadratic_supplement_two_half_complete",),
            (
                "intro p",
                "intro hprime",
                "intro hodd",
                "cases hodd",
                f"have hcomplete : {conditional_law}",
                "specialize quadratic_supplement_two_half_complete p",
                "specialize quadratic_supplement_two_half_complete x",
                "specialize quadratic_supplement_two_half_complete 2",
                "apply quadratic_supplement_two_half_complete",
                "exact hodd_witness",
                "exact hprime",
                "refl",
                "cases hcomplete",
                "exact hcomplete_right",
            ),
            "The complementary second supplementary law: two is a "
            "nonresidue exactly in classes three and five modulo eight.",
        ),
        spec(
            "quadratic_supplement_two_complete",
            f"forall p. ({prime('p', tag='qst_endpoint_prime')}) -> "
            f"({odd_p}) -> ({conditional_law})",
            (
                "quadratic_supplement_two_residue_iff_mod_eight_one_or_seven",
                "quadratic_supplement_two_nonresidue_iff_mod_eight_three_or_five",
            ),
            (
                "intro p",
                "intro hprime",
                "intro hodd",
                "split",
                "specialize quadratic_supplement_two_residue_iff_mod_eight_one_or_seven p",
                "apply quadratic_supplement_two_residue_iff_mod_eight_one_or_seven",
                "exact hprime",
                "exact hodd",
                "specialize quadratic_supplement_two_nonresidue_iff_mod_eight_three_or_five p",
                "apply quadratic_supplement_two_nonresidue_iff_mod_eight_three_or_five",
                "exact hprime",
                "exact hodd",
            ),
            "Complete constructive second supplementary law: the quadratic "
            "residue status of two is classified exactly by the four odd "
            "classes modulo eight.",
        ),
    )


__all__ = [
    "DOUBLING_GAUSS_INITIAL_SEGMENT_COMPLEMENT_GOAL",
    "DOUBLING_GAUSS_REFLECTION_COUNT_SHAPE_GOAL",
    "make_quadratic_supplement_two_candidate_theorems",
]
