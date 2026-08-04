"""Constructive congruence foundation for binary generalized CRT.

This isolated layer contains the subtraction-free congruence algebra and the
necessity direction of the binary noncoprime Chinese remainder theorem.  The
kernel sees only ordinary formulas over ``0, S, +, *, =``.  ``ModEq`` and
``CRTSolution`` below are authoring surfaces whose binders are generated
hygienically after every interpolated term has been parsed in an explicit
finite context.

The additive-left-cancellation rung already exists, with an audited proof, in
``finite_sum_pointwise_mod_candidate``.  ``promoted_mod_eq_add_cancel_left``
returns that exact theorem specification instead of copying its statement or
proof.  The seven new rows depend on it by name where needed.  Nothing here is
registered or admitted.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.kernel.terms import parse_term_in_context, pretty_term

from .finite_sum_pointwise_mod_candidate import (
    make_finite_sum_pointwise_mod_candidate_theorems,
)
from .ha_canonical_gcd_candidate import is_gcd


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


def _checked_term(source: str, variables: tuple[str, ...]) -> str:
    if not isinstance(source, str):
        raise ValueError("congruence term must be parser text")
    term = parse_term_in_context(source, list(variables))
    rendered = pretty_term(term, list(variables)).replace("·", "*")
    if rendered in variables or rendered in {"0", "1"}:
        return rendered
    return f"({rendered})"


def balanced_mod_eq(
    modulus: str,
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand balanced congruence after parsing all three terms safely."""

    if (
        not isinstance(variables, tuple)
        or not variables
        or len(set(variables)) != len(variables)
    ):
        raise ValueError(
            "term context must be a nonempty tuple of distinct identifiers"
        )
    checked_variables = tuple(
        _identifier(variable, "term context variable")
        for variable in variables
    )
    modulus_term = _checked_term(modulus, checked_variables)
    left_term = _checked_term(left, checked_variables)
    right_term = _checked_term(right, checked_variables)
    safe_tag = _identifier(tag, "binder tag")
    left_witness = f"hgcrt_mod_left_{safe_tag}"
    right_witness = f"hgcrt_mod_right_{safe_tag}"
    if (
        left_witness == right_witness
        or {left_witness, right_witness} & set(checked_variables)
    ):
        raise ValueError("generated balanced-congruence binder captures an argument")
    return (
        f"exists {left_witness} {right_witness}. "
        f"{left_term} + {modulus_term} * {left_witness} = "
        f"{right_term} + {modulus_term} * {right_witness}"
    )


def crt_solution(
    value: str,
    left_modulus: str,
    right_modulus: str,
    left_residue: str,
    right_residue: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand the conjunction defining one binary CRT solution."""

    safe_tag = _identifier(tag, "CRT-solution tag")
    left = balanced_mod_eq(
        left_modulus,
        value,
        left_residue,
        tag=f"{safe_tag}_left",
        variables=variables,
    )
    right = balanced_mod_eq(
        right_modulus,
        value,
        right_residue,
        tag=f"{safe_tag}_right",
        variables=variables,
    )
    return f"(({left}) /\\ ({right}))"


def promoted_mod_eq_add_cancel_left(spec: Callable[..., Any]) -> Any:
    """Return the exact existing additive-cancellation theorem specification."""

    candidates = make_finite_sum_pointwise_mod_candidate_theorems(spec)
    promoted = candidates[0]
    if promoted.name != "mod_eq_add_cancel_left":
        raise ValueError("the reviewed cancellation support row moved unexpectedly")
    return promoted


def make_ha_generalized_crt_congruence_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the seven new rows following the promoted cancellation support."""

    zero_source = balanced_mod_eq(
        "0", "a", "b", tag="zero_source", variables=("a", "b")
    )
    zero_result = balanced_mod_eq(
        "0", "a", "b", tag="zero_result", variables=("a", "b")
    )
    right_cancel_source = balanced_mod_eq(
        "d",
        "a + c",
        "b + c",
        tag="right_cancel_source",
        variables=("d", "a", "b", "c"),
    )
    right_cancel_result = balanced_mod_eq(
        "d",
        "a",
        "b",
        tag="right_cancel_result",
        variables=("d", "a", "b", "c"),
    )
    scale_source = balanced_mod_eq(
        "m", "a", "b", tag="scale_source", variables=("k", "m", "a", "b")
    )
    scale_result = balanced_mod_eq(
        "k * m",
        "k * a",
        "k * b",
        tag="scale_result",
        variables=("k", "m", "a", "b"),
    )
    unscale_source = balanced_mod_eq(
        "k * m",
        "k * a",
        "k * b",
        tag="unscale_source",
        variables=("k", "m", "a", "b"),
    )
    unscale_result = balanced_mod_eq(
        "m",
        "a",
        "b",
        tag="unscale_result",
        variables=("k", "m", "a", "b"),
    )
    solution_variables = ("m", "n", "a", "b", "x", "y")
    solution_x = crt_solution(
        "x", "m", "n", "a", "b", tag="pair_x", variables=solution_variables
    )
    solution_y = crt_solution(
        "y", "m", "n", "a", "b", tag="pair_y", variables=solution_variables
    )
    pair_mod_m = balanced_mod_eq(
        "m", "x", "y", tag="pair_mod_m", variables=solution_variables
    )
    pair_mod_n = balanced_mod_eq(
        "n", "x", "y", tag="pair_mod_n", variables=solution_variables
    )
    necessity_variables = ("g", "m", "n", "a", "b", "x")
    necessity_gcd = is_gcd("g", "m", "n", tag="crt_necessity")
    necessity_solution = crt_solution(
        "x",
        "m",
        "n",
        "a",
        "b",
        tag="necessity_solution",
        variables=necessity_variables,
    )
    compatibility = balanced_mod_eq(
        "g", "a", "b", tag="necessity_compatibility", variables=necessity_variables
    )
    obstruction_variables = ("g", "m", "n", "a", "b")
    obstruction_gcd = is_gcd("g", "m", "n", tag="crt_obstruction")
    obstruction_compatibility = balanced_mod_eq(
        "g",
        "a",
        "b",
        tag="obstruction_compatibility",
        variables=obstruction_variables,
    )
    obstruction_solution = crt_solution(
        "x",
        "m",
        "n",
        "a",
        "b",
        tag="obstruction_solution",
        variables=(*obstruction_variables, "x"),
    )

    return (
        spec(
            "mod_eq_zero_iff_eq",
            f"forall a b. ((({zero_source}) -> a = b) /\\ "
            f"(a = b -> ({zero_result})))",
            ("mul_zero_left",),
            (
                "intro a",
                "intro b",
                "split",
                "intro h",
                "cases h",
                "cases h_witness",
                "trans a + 0 * x",
                "symm",
                "trans a + 0",
                "congr",
                "refl",
                "apply mul_zero_left",
                "apply PA3",
                "trans b + 0 * x1",
                "exact h_witness_witness",
                "trans b + 0",
                "congr",
                "refl",
                "apply mul_zero_left",
                "apply PA3",
                "intro h",
                "exists 0",
                "exists 0",
                "rewrite h",
                "refl",
            ),
            "Balanced congruence modulo zero is exactly equality.",
        ),
        spec(
            "mod_eq_add_cancel_right",
            f"forall d a b c. ({right_cancel_source}) -> "
            f"({right_cancel_result})",
            ("mod_eq_add_cancel_left", "add_comm"),
            (
                "intro d",
                "intro a",
                "intro b",
                "intro c",
                "intro h",
                "have hac : a + c = c + a",
                "apply add_comm",
                "have hbc : b + c = c + b",
                "apply add_comm",
                "rewrite hac at h",
                "rewrite hbc at h",
                "specialize mod_eq_add_cancel_left d",
                "specialize mod_eq_add_cancel_left c",
                "specialize mod_eq_add_cancel_left a",
                "specialize mod_eq_add_cancel_left b",
                "apply mod_eq_add_cancel_left",
                "exact h",
            ),
            "Balanced congruence cancels a common additive right term.",
        ),
        spec(
            "mod_eq_scale",
            f"forall k m a b. ({scale_source}) -> ({scale_result})",
            ("mul_add", "mul_assoc"),
            (
                "intro k",
                "intro m",
                "intro a",
                "intro b",
                "intro h",
                "cases h",
                "cases h_witness",
                "exists x",
                "exists x1",
                "trans k * a + k * (m * x)",
                "congr",
                "refl",
                "apply mul_assoc",
                "trans k * (a + m * x)",
                "symm",
                "apply mul_add",
                "trans k * (b + m * x1)",
                "congr",
                "refl",
                "exact h_witness_witness",
                "trans k * b + k * (m * x1)",
                "apply mul_add",
                "congr",
                "refl",
                "symm",
                "apply mul_assoc",
            ),
            "Scaling values and their modulus preserves balanced congruence.",
        ),
        spec(
            "mod_eq_unscale_nonzero",
            f"forall k m a b. ~(k = 0) -> ({unscale_source}) -> "
            f"({unscale_result})",
            ("mul_add", "mul_assoc", "mul_left_cancel_nonzero"),
            (
                "intro k",
                "intro m",
                "intro a",
                "intro b",
                "intro hk",
                "intro h",
                "cases h",
                "cases h_witness",
                "have hscaled : k * (a + m * x) = k * (b + m * x1)",
                "trans k * a + k * (m * x)",
                "apply mul_add",
                "trans k * a + (k * m) * x",
                "congr",
                "refl",
                "symm",
                "apply mul_assoc",
                "trans k * b + (k * m) * x1",
                "exact h_witness_witness",
                "trans k * b + k * (m * x1)",
                "congr",
                "refl",
                "apply mul_assoc",
                "symm",
                "apply mul_add",
                "have hab : a + m * x = b + m * x1",
                "specialize mul_left_cancel_nonzero k",
                "specialize mul_left_cancel_nonzero (a + m * x)",
                "specialize mul_left_cancel_nonzero (b + m * x1)",
                "apply mul_left_cancel_nonzero",
                "exact hk",
                "exact hscaled",
                "exists x",
                "exists x1",
                "exact hab",
            ),
            "A nonzero common scale cancels from values and modulus.",
        ),
        spec(
            "crt_solution_pair_congruent",
            f"forall m n a b x y. ({solution_x}) -> ({solution_y}) -> "
            f"(({pair_mod_m}) /\\ ({pair_mod_n}))",
            ("mod_eq_symm", "mod_eq_trans"),
            (
                "intro m",
                "intro n",
                "intro a",
                "intro b",
                "intro x",
                "intro y",
                "intro hx",
                "intro hy",
                "cases hx",
                "cases hy",
                "split",
                f"have hay : {balanced_mod_eq('m', 'a', 'y', tag='pair_a_y', variables=solution_variables)}",
                "specialize mod_eq_symm m",
                "specialize mod_eq_symm y",
                "specialize mod_eq_symm a",
                "apply mod_eq_symm",
                "exact hy_left",
                "specialize mod_eq_trans m",
                "specialize mod_eq_trans x",
                "specialize mod_eq_trans a",
                "specialize mod_eq_trans y",
                "apply mod_eq_trans",
                "exact hx_left",
                "exact hay",
                f"have hby : {balanced_mod_eq('n', 'b', 'y', tag='pair_b_y', variables=solution_variables)}",
                "specialize mod_eq_symm n",
                "specialize mod_eq_symm y",
                "specialize mod_eq_symm b",
                "apply mod_eq_symm",
                "exact hy_right",
                "specialize mod_eq_trans n",
                "specialize mod_eq_trans x",
                "specialize mod_eq_trans b",
                "specialize mod_eq_trans y",
                "apply mod_eq_trans",
                "exact hx_right",
                "exact hby",
            ),
            "Any two solutions of one binary CRT problem agree modulo each modulus.",
        ),
        spec(
            "crt_common_solution_implies_gcd_compatible",
            f"forall g m n a b x. ({necessity_gcd}) -> "
            f"({necessity_solution}) -> ({compatibility})",
            (
                "is_gcd_dvd_left",
                "is_gcd_dvd_right",
                "mod_eq_of_mod_eq_multiple",
                "mod_eq_symm",
                "mod_eq_trans",
            ),
            (
                "intro g",
                "intro m",
                "intro n",
                "intro a",
                "intro b",
                "intro x",
                "intro hg",
                "intro hx",
                "cases hx",
                "have hgm : exists q. m = g * q",
                "specialize is_gcd_dvd_left g",
                "specialize is_gcd_dvd_left m",
                "specialize is_gcd_dvd_left n",
                "apply is_gcd_dvd_left",
                "exact hg",
                "have hgn : exists q. n = g * q",
                "specialize is_gcd_dvd_right g",
                "specialize is_gcd_dvd_right m",
                "specialize is_gcd_dvd_right n",
                "apply is_gcd_dvd_right",
                "exact hg",
                f"have hxa : {balanced_mod_eq('g', 'x', 'a', tag='necessity_x_a', variables=necessity_variables)}",
                "specialize mod_eq_of_mod_eq_multiple g",
                "specialize mod_eq_of_mod_eq_multiple m",
                "specialize mod_eq_of_mod_eq_multiple x",
                "specialize mod_eq_of_mod_eq_multiple a",
                "apply mod_eq_of_mod_eq_multiple",
                "exact hgm",
                "exact hx_left",
                f"have hxb : {balanced_mod_eq('g', 'x', 'b', tag='necessity_x_b', variables=necessity_variables)}",
                "specialize mod_eq_of_mod_eq_multiple g",
                "specialize mod_eq_of_mod_eq_multiple n",
                "specialize mod_eq_of_mod_eq_multiple x",
                "specialize mod_eq_of_mod_eq_multiple b",
                "apply mod_eq_of_mod_eq_multiple",
                "exact hgn",
                "exact hx_right",
                f"have hax : {balanced_mod_eq('g', 'a', 'x', tag='necessity_a_x', variables=necessity_variables)}",
                "specialize mod_eq_symm g",
                "specialize mod_eq_symm x",
                "specialize mod_eq_symm a",
                "apply mod_eq_symm",
                "exact hxa",
                "specialize mod_eq_trans g",
                "specialize mod_eq_trans a",
                "specialize mod_eq_trans x",
                "specialize mod_eq_trans b",
                "apply mod_eq_trans",
                "exact hax",
                "exact hxb",
            ),
            "A common CRT solution forces the residues to be congruent modulo every relational gcd.",
        ),
        spec(
            "crt_incompatibility_obstructs_solution",
            f"forall g m n a b. ({obstruction_gcd}) -> "
            f"~({obstruction_compatibility}) -> "
            f"~(exists x. ({obstruction_solution}))",
            ("crt_common_solution_implies_gcd_compatible",),
            (
                "intro g",
                "intro m",
                "intro n",
                "intro a",
                "intro b",
                "intro hg",
                "intro hnot",
                "intro hsolution",
                "cases hsolution",
                "apply hnot",
                "specialize crt_common_solution_implies_gcd_compatible g",
                "specialize crt_common_solution_implies_gcd_compatible m",
                "specialize crt_common_solution_implies_gcd_compatible n",
                "specialize crt_common_solution_implies_gcd_compatible a",
                "specialize crt_common_solution_implies_gcd_compatible b",
                "specialize crt_common_solution_implies_gcd_compatible x",
                "apply crt_common_solution_implies_gcd_compatible",
                "exact hg",
                "exact hsolution_witness",
            ),
            "Failure of gcd compatibility constructively refutes every common CRT solution.",
        ),
    )


def make_ha_generalized_crt_congruence_stack(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return the promoted support row followed by the seven new candidates."""

    return (
        promoted_mod_eq_add_cancel_left(spec),
        *make_ha_generalized_crt_congruence_candidate_theorems(spec),
    )


__all__ = [
    "balanced_mod_eq",
    "crt_solution",
    "make_ha_generalized_crt_congruence_candidate_theorems",
    "make_ha_generalized_crt_congruence_stack",
    "promoted_mod_eq_add_cancel_left",
]
