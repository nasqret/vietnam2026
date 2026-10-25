"""Constructive beta-coded half-range foundations for Gauss arguments.

This isolated theorem-spec factory adds no trusted notation.  ``Range``,
``BetaAt``, strict bounds, and balanced congruence are fully expanded in every
public contract before the ordinary PA parser and kernel see them.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, range_relation


def _lt(left: str, right: str, *, tag: str) -> str:
    return f"exists gh_lt_{tag}. gh_lt_{tag} + S {left} = {right}"


def _mod_eq(modulus: str, left: str, right: str, *, tag: str) -> str:
    return (
        f"exists gh_u_{tag} gh_v_{tag}. {left} + "
        f"{modulus} * gh_u_{tag} = {right} + {modulus} * gh_v_{tag}"
    )


def _range_one(code: str, scale: str, length: str, *, tag: str) -> str:
    """Expand Range(code,scale,1,length) for module-owned term fragments."""

    i = f"gh_i_{tag}"
    bound = _lt(i, length, tag=f"{tag}_bound")
    modulus = f"S ((S {i}) * {scale})"
    value = f"1 + {i}"
    decoded = (
        f"((exists gh_h_{tag}. gh_h_{tag} + S ({value}) = {modulus}) /\\ "
        f"exists gh_q_{tag}. {code} = gh_q_{tag} * {modulus} + ({value}))"
    )
    return f"forall {i}. ({bound}) -> ({decoded})"


def make_gauss_half_range_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered half-range injection tranche."""

    generic_range = range_relation("b", "c", "a", "l", tag="generic")
    generic_i = beta_at("b", "c", "i", "x", tag="generic_i")
    generic_j = beta_at("b", "c", "j", "y", tag="generic_j")
    generic_injective = (
        f"forall b c a l i j x y. ({generic_range}) -> "
        f"({_lt('i', 'l', tag='generic_i')}) -> "
        f"({_lt('j', 'l', tag='generic_j')}) -> "
        f"({generic_i}) -> ({generic_j}) -> x = y -> i = j"
    )

    half_range = _range_one("b", "c", "h", tag="half")
    half_i = beta_at("b", "c", "i", "x", tag="half_i")
    half_bounds = (
        f"forall p h b c i x. p = 2 * h + 1 -> ({half_range}) -> "
        f"({_lt('i', 'h', tag='half_i')}) -> ({half_i}) -> "
        f"(~(x = 0) /\\ ({_lt('x', 'p', tag='half_value')}))"
    )

    pair_range = _range_one("b", "c", "h", tag="pair")
    pair_i = beta_at("b", "c", "i", "x", tag="pair_i")
    pair_j = beta_at("b", "c", "j", "y", tag="pair_j")
    pair_prefix = (
        f"forall p h b c i j x y. p = 2 * h + 1 -> ({pair_range}) -> "
        f"({_lt('i', 'h', tag='pair_i')}) -> "
        f"({_lt('j', 'h', tag='pair_j')}) -> "
        f"({pair_i}) -> ({pair_j}) -> "
    )
    pair_mod_eq = _mod_eq("p", "x", "y", tag="pair")
    pair_value_statement = f"{pair_prefix}({pair_mod_eq}) -> x = y"
    pair_index_statement = f"{pair_prefix}({pair_mod_eq}) -> i = j"

    return (
        spec(
            "beta_range_injective",
            generic_injective,
            ("beta_range_entry_eq", "add_left_cancel"),
            (
                "intro b",
                "intro c",
                "intro a",
                "intro l",
                "intro i",
                "intro j",
                "intro x",
                "intro y",
                "intro hrange",
                "intro hi",
                "intro hj",
                "intro hxi",
                "intro hyj",
                "intro hxy",
                "have hxia : x = a + i",
                "specialize beta_range_entry_eq b",
                "specialize beta_range_entry_eq c",
                "specialize beta_range_entry_eq a",
                "specialize beta_range_entry_eq l",
                "specialize beta_range_entry_eq i",
                "specialize beta_range_entry_eq x",
                "apply beta_range_entry_eq",
                "exact hrange",
                "exact hi",
                "exact hxi",
                "have hyja : y = a + j",
                "specialize beta_range_entry_eq b",
                "specialize beta_range_entry_eq c",
                "specialize beta_range_entry_eq a",
                "specialize beta_range_entry_eq l",
                "specialize beta_range_entry_eq j",
                "specialize beta_range_entry_eq y",
                "apply beta_range_entry_eq",
                "exact hrange",
                "exact hj",
                "exact hyj",
                "have haij : a + i = a + j",
                "trans x",
                "symm",
                "exact hxia",
                "trans y",
                "exact hxy",
                "exact hyja",
                "specialize add_left_cancel a",
                "specialize add_left_cancel i",
                "specialize add_left_cancel j",
                "apply add_left_cancel",
                "exact haij",
            ),
            "Equal decoded values in one consecutive range have equal indices.",
        ),
        spec(
            "beta_half_range_entry_bounds",
            half_bounds,
            (
                "beta_range_entry_eq",
                "zero_add",
                "add_succ_left",
                "mul_succ_left",
                "mul_zero_left",
                "add_assoc",
                "lt_of_le_of_lt",
            ),
            (
                "intro p",
                "intro h",
                "intro b",
                "intro c",
                "intro i",
                "intro x",
                "intro hp",
                "intro hrange",
                "intro hi",
                "intro hxi",
                "have hx : x = 1 + i",
                "specialize beta_range_entry_eq b",
                "specialize beta_range_entry_eq c",
                "specialize beta_range_entry_eq 1",
                "specialize beta_range_entry_eq h",
                "specialize beta_range_entry_eq i",
                "specialize beta_range_entry_eq x",
                "apply beta_range_entry_eq",
                "exact hrange",
                "exact hi",
                "exact hxi",
                "have hone : 1 + i = S i",
                "trans S (0 + i)",
                "specialize add_succ_left 0",
                "specialize add_succ_left i",
                "exact add_succ_left",
                "congr",
                "specialize zero_add i",
                "exact zero_add",
                "have hxsi : x = S i",
                "trans 1 + i",
                "exact hx",
                "exact hone",
                "split",
                "intro hx0",
                "apply PA1",
                "trans x",
                "symm",
                "exact hxsi",
                "exact hx0",
                "have hxh : exists k. k + x = h",
                "rewrite hxsi",
                "exact hi",
                "have hhp : exists k. k + S h = p",
                "exists h",
                "rewrite hp",
                "simp [mul_succ_left, mul_zero_left, add_succ_left, "
                "zero_add, add_assoc]",
                "specialize lt_of_le_of_lt x",
                "specialize lt_of_le_of_lt h",
                "specialize lt_of_le_of_lt p",
                "apply lt_of_le_of_lt",
                "exact hxh",
                "exact hhp",
            ),
            "Entries 1 through h in an odd half-range are nonzero and below p.",
        ),
        spec(
            "beta_half_range_mod_eq_value",
            pair_value_statement,
            ("beta_half_range_entry_bounds", "mod_eq_bounded_unique"),
            (
                "intro p",
                "intro h",
                "intro b",
                "intro c",
                "intro i",
                "intro j",
                "intro x",
                "intro y",
                "intro hp",
                "intro hrange",
                "intro hi",
                "intro hj",
                "intro hxi",
                "intro hyj",
                "intro hxy",
                "have hxb : ~(x = 0) /\\ exists k. k + S x = p",
                "specialize beta_half_range_entry_bounds p",
                "specialize beta_half_range_entry_bounds h",
                "specialize beta_half_range_entry_bounds b",
                "specialize beta_half_range_entry_bounds c",
                "specialize beta_half_range_entry_bounds i",
                "specialize beta_half_range_entry_bounds x",
                "apply beta_half_range_entry_bounds",
                "exact hp",
                "exact hrange",
                "exact hi",
                "exact hxi",
                "have hyb : ~(y = 0) /\\ exists k. k + S y = p",
                "specialize beta_half_range_entry_bounds p",
                "specialize beta_half_range_entry_bounds h",
                "specialize beta_half_range_entry_bounds b",
                "specialize beta_half_range_entry_bounds c",
                "specialize beta_half_range_entry_bounds j",
                "specialize beta_half_range_entry_bounds y",
                "apply beta_half_range_entry_bounds",
                "exact hp",
                "exact hrange",
                "exact hj",
                "exact hyj",
                "cases hxb",
                "cases hyb",
                "specialize mod_eq_bounded_unique p",
                "specialize mod_eq_bounded_unique x",
                "specialize mod_eq_bounded_unique y",
                "apply mod_eq_bounded_unique",
                "exact hxb_right",
                "exact hyb_right",
                "exact hxy",
            ),
            "Congruent entries in the odd half-range are equal as bounded residues.",
        ),
        spec(
            "beta_half_range_mod_injective",
            pair_index_statement,
            ("beta_half_range_mod_eq_value", "beta_range_injective"),
            (
                "intro p",
                "intro h",
                "intro b",
                "intro c",
                "intro i",
                "intro j",
                "intro x",
                "intro y",
                "intro hp",
                "intro hrange",
                "intro hi",
                "intro hj",
                "intro hxi",
                "intro hyj",
                "intro hxy",
                "have hvalue : x = y",
                "specialize beta_half_range_mod_eq_value p",
                "specialize beta_half_range_mod_eq_value h",
                "specialize beta_half_range_mod_eq_value b",
                "specialize beta_half_range_mod_eq_value c",
                "specialize beta_half_range_mod_eq_value i",
                "specialize beta_half_range_mod_eq_value j",
                "specialize beta_half_range_mod_eq_value x",
                "specialize beta_half_range_mod_eq_value y",
                "apply beta_half_range_mod_eq_value",
                "exact hp",
                "exact hrange",
                "exact hi",
                "exact hj",
                "exact hxi",
                "exact hyj",
                "exact hxy",
                "specialize beta_range_injective b",
                "specialize beta_range_injective c",
                "specialize beta_range_injective 1",
                "specialize beta_range_injective h",
                "specialize beta_range_injective i",
                "specialize beta_range_injective j",
                "specialize beta_range_injective x",
                "specialize beta_range_injective y",
                "apply beta_range_injective",
                "exact hrange",
                "exact hi",
                "exact hj",
                "exact hxi",
                "exact hyj",
                "exact hvalue",
            ),
            "The odd half-range is injective modulo p at the level of indices.",
        ),
    )


__all__ = ["make_gauss_half_range_theorems"]
