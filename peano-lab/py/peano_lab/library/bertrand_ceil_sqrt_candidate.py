"""Conservative ceiling-by-six and floor-square candidates for Bertrand B6.

The B6 integer envelope uses two graph relations which are deliberately absent
from the kernel language.  This module expands them before parsing:

``CeilDivSix(x,e)``
    ``x <= 6*e`` and ``6*e < x+6``;

``FloorSqrt(x,s)``
    ``s*s <= x`` and ``x < (S s)*(S s)``.

The theorem factory is isolated from the public registry.  Its bodies are
dependency-curried native-HA certificates; no host quotient, square root, or
evaluated arithmetic is proof authority.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.kernel.terms import parse_term_with_names


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(character.isalnum() or character in "_'" for character in value[1:])
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _term_names(*labelled: tuple[str, str]) -> tuple[str, ...]:
    names: list[str] = []
    for source, label in labelled:
        if not isinstance(source, str) or not source:
            raise ValueError(f"{label} must be a nonempty Peano term")
        try:
            _term, free_names = parse_term_with_names(source)
        except ValueError as exc:
            raise ValueError(f"{label} must be a Peano term: {exc}") from None
        names.extend(free_names)
    return tuple(dict.fromkeys(names))


def _binders(tag: str, avoid: tuple[str, ...], stems: tuple[str, ...]) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"bcs_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(avoid):
        raise ValueError("generated Bertrand ceiling/square binder captures an argument")
    return names


def ceil_div_six_relation(value: str, ceiling: str, *, tag: str) -> str:
    """Expand ``value <= 6*ceiling < value+6`` into witness order."""

    variables = _term_names(
        (value, "ceiling input"),
        (ceiling, "ceiling output"),
    )
    lower, upper = _binders(tag, variables, ("lower_gap", "upper_gap"))
    return (
        f"((exists {lower}. {lower} + ({value}) = 6 * ({ceiling})) /\\ "
        f"exists {upper}. {upper} + S (6 * ({ceiling})) = ({value}) + 6)"
    )


def floor_sqrt_relation(value: str, root: str, *, tag: str) -> str:
    """Expand ``root^2 <= value < (root+1)^2`` without exponentiation."""

    variables = _term_names(
        (value, "floor-square input"),
        (root, "floor-square output"),
    )
    lower, upper = _binders(tag, variables, ("sqrt_lower_gap", "sqrt_upper_gap"))
    return (
        f"((exists {lower}. {lower} + ({root}) * ({root}) = ({value})) /\\ "
        f"exists {upper}. {upper} + S ({value}) = S ({root}) * S ({root}))"
    )


def make_bertrand_ceil_sqrt_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the next dependency-closed B6 integer infrastructure tranche."""

    ceil_shift_source = ceil_div_six_relation("x", "e", tag="shift_source")
    ceil_shift_target = ceil_div_six_relation(
        "x + 6 * k", "e + k", tag="shift_target"
    )
    ceil_total = ceil_div_six_relation("x", "e", tag="total_result")
    ceil_functional_left = ceil_div_six_relation(
        "x", "e", tag="functional_left"
    )
    ceil_functional_right = ceil_div_six_relation(
        "x", "f", tag="functional_right"
    )
    ceil_unique_result = ceil_div_six_relation(
        "x", "e", tag="unique_result"
    )
    ceil_unique_comparison = ceil_div_six_relation(
        "x", "f", tag="unique_comparison"
    )
    ceil_square_source = ceil_div_six_relation(
        "s * s", "e", tag="square_source"
    )
    ceil_square_target = ceil_div_six_relation(
        "(s + 6) * (s + 6)", "f", tag="square_target"
    )
    ceil_square_shifted = ceil_div_six_relation(
        "s * s + 6 * (2 * s + 6)",
        "e + (2 * s + 6)",
        tag="square_shifted",
    )
    ceil_square_rewritten = ceil_div_six_relation(
        "(s + 6) * (s + 6)",
        "e + (2 * s + 6)",
        tag="square_rewritten",
    )

    sqrt_projection = floor_sqrt_relation("x", "s", tag="projection")
    sqrt_functional_left = floor_sqrt_relation(
        "x", "s", tag="sqrt_functional_left"
    )
    sqrt_functional_right = floor_sqrt_relation(
        "x", "t", tag="sqrt_functional_right"
    )

    return (
        spec(
            "ceil_div_six_shift",
            f"forall x e k. ({ceil_shift_source}) -> ({ceil_shift_target})",
            ("mul_add", "add_assoc", "add_comm", "add_succ_left"),
            (
                "intro x",
                "intro e",
                "intro k",
                "intro h",
                "have hmul : 6 * (e + k) = 6 * e + 6 * k",
                "specialize mul_add 6",
                "specialize mul_add e",
                "specialize mul_add k",
                "exact mul_add",
                "cases h",
                "split",
                "cases h_left",
                "exists x1",
                "rewrite hmul",
                "trans (x1 + x) + 6 * k",
                "symm",
                "apply add_assoc",
                "rewrite h_left_witness",
                "refl",
                "cases h_right",
                "exists x1",
                "rewrite hmul",
                "trans x1 + (S (6 * e) + 6 * k)",
                "congr",
                "refl",
                "symm",
                "apply add_succ_left",
                "trans (x1 + S (6 * e)) + 6 * k",
                "symm",
                "apply add_assoc",
                "rewrite h_right_witness",
                "trans x + (6 + 6 * k)",
                "apply add_assoc",
                "trans x + (6 * k + 6)",
                "congr",
                "refl",
                "apply add_comm",
                "symm",
                "apply add_assoc",
            ),
            "Ceiling by six commutes with adding an explicit multiple of six.",
        ),
        spec(
            "ceil_div_six_total",
            f"forall x. exists e. ({ceil_total})",
            (
                "division_remainder_exists",
                "succ_ne_zero",
                "zero_or_succ",
                "zero_add",
                "lt_to_le",
                "add_le_add_left",
                "add_comm",
            ),
            (
                "intro x",
                "have hdiv : exists q r. x = 6 * q + r /\\ "
                "exists h. h + S r = 6",
                "specialize division_remainder_exists 6",
                "specialize division_remainder_exists x",
                "apply division_remainder_exists",
                "intro h6",
                "specialize succ_ne_zero 5",
                "apply succ_ne_zero",
                "exact h6",
                "cases hdiv",
                "cases hdiv_witness",
                "cases hdiv_witness_witness",
                "specialize zero_or_succ x2",
                "cases zero_or_succ",
                "exists x1",
                "split",
                "exists 0",
                "trans x",
                "apply zero_add",
                "trans 6 * x1 + x2",
                "exact hdiv_witness_witness_left",
                "rewrite zero_or_succ_left",
                "apply PA3",
                "exists 5",
                "rewrite hdiv_witness_witness_left",
                "rewrite zero_or_succ_left",
                "trans S (5 + 6 * x1)",
                "apply PA4",
                "trans S (6 * x1 + 5)",
                "congr",
                "apply add_comm",
                "trans 6 * x1 + 6",
                "symm",
                "apply PA4",
                "congr",
                "symm",
                "apply PA3",
                "refl",
                "cases zero_or_succ_right",
                "exists S x1",
                "split",
                "have hrle : exists k. k + x2 = 6",
                "apply lt_to_le",
                "exact hdiv_witness_witness_right",
                "have hlow : exists k. k + (6 * x1 + x2) = 6 * x1 + 6",
                "apply add_le_add_left",
                "exact hrle",
                "have hsixsucc : 6 * S x1 = 6 * x1 + 6",
                "apply PA6",
                "rewrite hsixsucc",
                "rewrite hdiv_witness_witness_left",
                "exact hlow",
                "exists x3",
                "rewrite hdiv_witness_witness_left",
                "rewrite zero_or_succ_right_witness",
                "simp [add_comm]",
            ),
            "Every natural has a constructive ceiling quotient by six.",
        ),
        spec(
            "ceil_div_six_functional",
            "forall x e f. "
            f"({ceil_functional_left}) -> ({ceil_functional_right}) -> e = f",
            (
                "lt_trichotomy",
                "add_le_add_right",
                "mul_le_mul_left",
                "lt_of_lt_of_le",
                "lt_irrefl_expanded",
            ),
            (
                "intro x",
                "intro e",
                "intro f",
                "intro he",
                "intro hf",
                "cases he",
                "cases hf",
                "specialize lt_trichotomy e",
                "specialize lt_trichotomy f",
                "cases lt_trichotomy",
                "exact lt_trichotomy_left",
                "cases lt_trichotomy_right",
                "exfalso",
                "have hx6 : exists k. k + (x + 6) = 6 * e + 6",
                "specialize add_le_add_right x",
                "specialize add_le_add_right (6 * e)",
                "specialize add_le_add_right 6",
                "apply add_le_add_right",
                "exact he_left",
                "have hscaled : exists k. k + 6 * S e = 6 * f",
                "apply mul_le_mul_left",
                "exact lt_trichotomy_right_left",
                "have hsucce : 6 * S e = 6 * e + 6",
                "apply PA6",
                "rewrite hsucce at hscaled",
                "have hfirst : exists k. k + S (6 * f) = 6 * e + 6",
                "specialize lt_of_lt_of_le (6 * f)",
                "specialize lt_of_lt_of_le (x + 6)",
                "specialize lt_of_lt_of_le (6 * e + 6)",
                "apply lt_of_lt_of_le",
                "exact hf_right",
                "exact hx6",
                "have hloop : exists k. k + S (6 * f) = 6 * f",
                "specialize lt_of_lt_of_le (6 * f)",
                "specialize lt_of_lt_of_le (6 * e + 6)",
                "specialize lt_of_lt_of_le (6 * f)",
                "apply lt_of_lt_of_le",
                "exact hfirst",
                "exact hscaled",
                "specialize lt_irrefl_expanded (6 * f)",
                "apply lt_irrefl_expanded",
                "exact hloop",
                "exfalso",
                "have hx6 : exists k. k + (x + 6) = 6 * f + 6",
                "specialize add_le_add_right x",
                "specialize add_le_add_right (6 * f)",
                "specialize add_le_add_right 6",
                "apply add_le_add_right",
                "exact hf_left",
                "have hscaled : exists k. k + 6 * S f = 6 * e",
                "apply mul_le_mul_left",
                "exact lt_trichotomy_right_right",
                "have hsuccf : 6 * S f = 6 * f + 6",
                "apply PA6",
                "rewrite hsuccf at hscaled",
                "have hfirst : exists k. k + S (6 * e) = 6 * f + 6",
                "specialize lt_of_lt_of_le (6 * e)",
                "specialize lt_of_lt_of_le (x + 6)",
                "specialize lt_of_lt_of_le (6 * f + 6)",
                "apply lt_of_lt_of_le",
                "exact he_right",
                "exact hx6",
                "have hloop : exists k. k + S (6 * e) = 6 * e",
                "specialize lt_of_lt_of_le (6 * e)",
                "specialize lt_of_lt_of_le (6 * f + 6)",
                "specialize lt_of_lt_of_le (6 * e)",
                "apply lt_of_lt_of_le",
                "exact hfirst",
                "exact hscaled",
                "specialize lt_irrefl_expanded (6 * e)",
                "apply lt_irrefl_expanded",
                "exact hloop",
            ),
            "The two witness inequalities determine a unique ceiling quotient.",
        ),
        spec(
            "ceil_div_six_exists_unique",
            "forall x. exists e. "
            f"(({ceil_unique_result}) /\\ forall f. "
            f"({ceil_unique_comparison}) -> f = e)",
            ("ceil_div_six_total", "ceil_div_six_functional"),
            (
                "intro x",
                f"have htotal : exists e. ({ceil_total})",
                "specialize ceil_div_six_total x",
                "exact ceil_div_six_total",
                "cases htotal",
                "exists x1",
                "split",
                "exact htotal_witness",
                "intro f",
                "intro hf",
                "specialize ceil_div_six_functional x",
                "specialize ceil_div_six_functional f",
                "specialize ceil_div_six_functional x1",
                "apply ceil_div_six_functional",
                "exact hf",
                "exact htotal_witness",
            ),
            "Ceiling by six is a total single-valued native relation.",
        ),
        spec(
            "square_six_shift_identity",
            "forall s. s * s + 6 * (2 * s + 6) = (s + 6) * (s + 6)",
            ("two_mul_eq_add_self", "mul_add", "add_mul", "mul_comm", "add_assoc"),
            (
                "intro s",
                "have htwo : 2 * s = s + s",
                "apply two_mul_eq_add_self",
                "have hleft : 6 * (2 * s + 6) = "
                "(6 * s + 6 * s) + 6 * 6",
                "trans 6 * (2 * s) + 6 * 6",
                "apply mul_add",
                "rewrite htwo",
                "trans (6 * s + 6 * s) + 6 * 6",
                "congr",
                "apply mul_add",
                "refl",
                "refl",
                "have hright : (s + 6) * (s + 6) = "
                "(s * s + 6 * s) + (6 * s + 6 * 6)",
                "trans s * (s + 6) + 6 * (s + 6)",
                "apply add_mul",
                "trans (s * s + s * 6) + (6 * s + 6 * 6)",
                "congr",
                "apply mul_add",
                "apply mul_add",
                "trans (s * s + 6 * s) + (6 * s + 6 * 6)",
                "congr",
                "congr",
                "refl",
                "apply mul_comm",
                "refl",
                "refl",
                "trans s * s + ((6 * s + 6 * s) + 6 * 6)",
                "congr",
                "refl",
                "exact hleft",
                "trans s * s + (6 * s + (6 * s + 6 * 6))",
                "congr",
                "refl",
                "apply add_assoc",
                "trans (s * s + 6 * s) + (6 * s + 6 * 6)",
                "symm",
                "apply add_assoc",
                "symm",
                "exact hright",
            ),
            "The six-step square increment is exactly six times 2*s+6.",
        ),
        spec(
            "ceil_div_six_square_six_step",
            "forall s e f. "
            f"({ceil_square_source}) -> ({ceil_square_target}) -> "
            "f = e + (2 * s + 6)",
            (
                "ceil_div_six_shift",
                "square_six_shift_identity",
                "ceil_div_six_functional",
            ),
            (
                "intro s",
                "intro e",
                "intro f",
                "intro he",
                "intro hf",
                f"have hshift : {ceil_square_shifted}",
                "specialize ceil_div_six_shift (s * s)",
                "specialize ceil_div_six_shift e",
                "specialize ceil_div_six_shift (2 * s + 6)",
                "apply ceil_div_six_shift",
                "exact he",
                "have hid : s * s + 6 * (2 * s + 6) = "
                "(s + 6) * (s + 6)",
                "specialize square_six_shift_identity s",
                "exact square_six_shift_identity",
                f"have hnext : {ceil_square_rewritten}",
                "rewrite <- hid",
                "rewrite <- hid",
                "exact hshift",
                "specialize ceil_div_six_functional ((s + 6) * (s + 6))",
                "specialize ceil_div_six_functional f",
                "specialize ceil_div_six_functional (e + (2 * s + 6))",
                "apply ceil_div_six_functional",
                "exact hf",
                "exact hnext",
            ),
            "Ceil((s+6)^2/6) is exactly Ceil(s^2/6)+2*s+6.",
        ),
        spec(
            "floor_sqrt_lower_bound",
            f"forall x s. ({sqrt_projection}) -> "
            "exists k. k + s * s = x",
            (),
            (
                "intro x",
                "intro s",
                "intro h",
                "cases h",
                "exact h_left",
            ),
            "The floor-square graph projects its lower square bound.",
        ),
        spec(
            "floor_sqrt_strict_upper_bound",
            f"forall x s. ({sqrt_projection}) -> "
            "exists k. k + S x = S s * S s",
            (),
            (
                "intro x",
                "intro s",
                "intro h",
                "cases h",
                "exact h_right",
            ),
            "The floor-square graph projects its strict successor-square bound.",
        ),
        spec(
            "floor_sqrt_functional",
            "forall x s t. "
            f"({sqrt_functional_left}) -> ({sqrt_functional_right}) -> s = t",
            (
                "lt_trichotomy",
                "mul_le_mul_right",
                "mul_le_mul_left",
                "le_trans",
                "lt_of_lt_of_le",
                "lt_irrefl_expanded",
            ),
            (
                "intro x",
                "intro s",
                "intro t",
                "intro hs",
                "intro ht",
                "cases hs",
                "cases ht",
                "specialize lt_trichotomy s",
                "specialize lt_trichotomy t",
                "cases lt_trichotomy",
                "exact lt_trichotomy_left",
                "cases lt_trichotomy_right",
                "exfalso",
                "have hone : exists k. k + S s * S s = t * S s",
                "apply mul_le_mul_right",
                "exact lt_trichotomy_right_left",
                "have htwo : exists k. k + t * S s = t * t",
                "apply mul_le_mul_left",
                "exact lt_trichotomy_right_left",
                "have hsquare : exists k. k + S s * S s = t * t",
                "specialize le_trans (S s * S s)",
                "specialize le_trans (t * S s)",
                "specialize le_trans (t * t)",
                "apply le_trans",
                "exact hone",
                "exact htwo",
                "have hfirst : exists k. k + S x = t * t",
                "specialize lt_of_lt_of_le x",
                "specialize lt_of_lt_of_le (S s * S s)",
                "specialize lt_of_lt_of_le (t * t)",
                "apply lt_of_lt_of_le",
                "exact hs_right",
                "exact hsquare",
                "have hloop : exists k. k + S x = x",
                "specialize lt_of_lt_of_le x",
                "specialize lt_of_lt_of_le (t * t)",
                "specialize lt_of_lt_of_le x",
                "apply lt_of_lt_of_le",
                "exact hfirst",
                "exact ht_left",
                "specialize lt_irrefl_expanded x",
                "apply lt_irrefl_expanded",
                "exact hloop",
                "exfalso",
                "have hone : exists k. k + S t * S t = s * S t",
                "apply mul_le_mul_right",
                "exact lt_trichotomy_right_right",
                "have htwo : exists k. k + s * S t = s * s",
                "apply mul_le_mul_left",
                "exact lt_trichotomy_right_right",
                "have hsquare : exists k. k + S t * S t = s * s",
                "specialize le_trans (S t * S t)",
                "specialize le_trans (s * S t)",
                "specialize le_trans (s * s)",
                "apply le_trans",
                "exact hone",
                "exact htwo",
                "have hfirst : exists k. k + S x = s * s",
                "specialize lt_of_lt_of_le x",
                "specialize lt_of_lt_of_le (S t * S t)",
                "specialize lt_of_lt_of_le (s * s)",
                "apply lt_of_lt_of_le",
                "exact ht_right",
                "exact hsquare",
                "have hloop : exists k. k + S x = x",
                "specialize lt_of_lt_of_le x",
                "specialize lt_of_lt_of_le (s * s)",
                "specialize lt_of_lt_of_le x",
                "apply lt_of_lt_of_le",
                "exact hfirst",
                "exact hs_left",
                "specialize lt_irrefl_expanded x",
                "apply lt_irrefl_expanded",
                "exact hloop",
            ),
            "The two adjacent-square bounds determine a unique floor square root.",
        ),
    )


__all__ = [
    "ceil_div_six_relation",
    "floor_sqrt_relation",
    "make_bertrand_ceil_sqrt_candidate_theorems",
]
