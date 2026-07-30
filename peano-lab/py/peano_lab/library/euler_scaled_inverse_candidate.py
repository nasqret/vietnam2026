"""Isolated pointwise scaled-inverse candidates for Euler's criterion.

For nonzero residues below a prime ``p`` this module studies the relation

    x * y == a (mod p).

The intended map is ``x |-> a * x^-1``.  The relation-first presentation is
native to Peano Lab: existence and bounded uniqueness make it functional,
symmetry makes it involutive, and its fixed points are exactly the bounded
unit roots of ``x*x == a``.  Every helper expands immediately to the
unchanged first-order PA language.  Nothing here is registered as a public
theorem; WMI body validation and recursive discovery are separate gates.
"""

from __future__ import annotations

from typing import Any, Callable

from .quadratic_residue_surface import quadratic_residue


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


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"esi_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Euler scaled-inverse binder captures an argument")
    return names


def prime(value: str, *, tag: str) -> str:
    """Expand primality through the native nonunit factor-pair formula."""

    variable = _identifier(value, "prime candidate")
    left, right = _binders(tag, (variable,), ("prime_left", "prime_right"))
    return (
        f"(~({variable} = 1) /\\ forall {left} {right}. "
        f"{variable} = {left} * {right} -> {left} = 1 \\/ {right} = 1)"
    )


def strictly_below(left: str, right: str, *, tag: str) -> str:
    """Expand the witness-defined strict inequality ``left < right``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "lower term"), (right, "upper term"))
    )
    (gap,) = _binders(tag, variables, ("strict_gap",))
    return f"exists {gap}. {gap} + S {left} = {right}"


def _balanced_mod(
    modulus: str,
    left: str,
    right: str,
    *,
    variables: tuple[str, ...],
    tag: str,
) -> str:
    """Expand balanced congruence between two audited native terms."""

    checked = tuple(_identifier(value, "congruence variable") for value in variables)
    modulus = _identifier(modulus, "modulus")
    if modulus not in checked:
        raise ValueError("the modulus must occur in the audited variable set")
    mod_left, mod_right = _binders(tag, checked, ("mod_left", "mod_right"))
    return (
        f"exists {mod_left} {mod_right}. ({left}) + {modulus} * {mod_left} = "
        f"({right}) + {modulus} * {mod_right}"
    )


def unit_residue(modulus: str, value: str, *, tag: str) -> str:
    """Expand ``value != 0`` together with ``value < modulus``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in ((modulus, "modulus"), (value, "residue"))
    )
    modulus, value = variables
    return (
        f"(~({value} = 0) /\\ "
        f"({strictly_below(value, modulus, tag=f'{tag}_bound')}))"
    )


def scaled_inverse(
    modulus: str,
    target: str,
    left: str,
    right: str,
    *,
    tag: str,
) -> str:
    """Expand the bounded relation ``left * right == target (mod modulus)``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (modulus, "modulus"),
            (target, "target"),
            (left, "left residue"),
            (right, "right residue"),
        )
    )
    modulus, target, left, right = variables
    safe_tag = _identifier(tag, "binder tag")
    left_unit = unit_residue(modulus, left, tag=f"{safe_tag}_left")
    right_unit = unit_residue(modulus, right, tag=f"{safe_tag}_right")
    congruence = _balanced_mod(
        modulus,
        f"{left} * {right}",
        target,
        variables=variables,
        tag=f"{safe_tag}_mod",
    )
    return f"(({left_unit}) /\\ (({right_unit}) /\\ ({congruence})))"


def scaled_fixed_point(
    modulus: str,
    target: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand a bounded unit root of ``value*value == target``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (modulus, "modulus"),
            (target, "target"),
            (value, "residue"),
        )
    )
    modulus, target, value = variables
    safe_tag = _identifier(tag, "binder tag")
    unit = unit_residue(modulus, value, tag=f"{safe_tag}_unit")
    square = _balanced_mod(
        modulus,
        f"{value} * {value}",
        target,
        variables=variables,
        tag=f"{safe_tag}_square",
    )
    return f"(({unit}) /\\ ({square}))"


def make_euler_scaled_inverse_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered pointwise Euler entrance ladder."""

    inverse_xz = _balanced_mod(
        "p", "x * z", "1", variables=("p", "a", "x", "z"), tag="from_unit_source"
    )
    scaled_axz = _balanced_mod(
        "p",
        "a * (x * z)",
        "a * 1",
        variables=("p", "a", "x", "z"),
        tag="from_unit_scaled",
    )
    scaled_result = _balanced_mod(
        "p",
        "x * (a * z)",
        "a",
        variables=("p", "a", "x", "z"),
        tag="from_unit_result",
    )

    transport_source = _balanced_mod(
        "p", "x * y", "a", variables=("p", "a", "x", "y", "z"), tag="transport_source"
    )
    transport_argument = _balanced_mod(
        "p", "y", "z", variables=("p", "a", "x", "y", "z"), tag="transport_argument"
    )
    transport_scaled = _balanced_mod(
        "p", "x * y", "x * z", variables=("p", "a", "x", "y", "z"), tag="transport_scaled"
    )
    transport_reverse = _balanced_mod(
        "p", "x * z", "x * y", variables=("p", "a", "x", "y", "z"), tag="transport_reverse"
    )
    transport_result = _balanced_mod(
        "p", "x * z", "a", variables=("p", "a", "x", "y", "z"), tag="transport_result"
    )

    prime_nonzero_target = prime("p", tag="target_nonzero_prime")
    target_bound = strictly_below("a", "p", tag="target_nonzero_target_bound")
    target_product = _balanced_mod(
        "p", "x * y", "a", variables=("p", "a", "x", "y"), tag="target_nonzero_product"
    )
    zero_target = _balanced_mod(
        "p", "0", "a", variables=("p", "a", "x", "y"), tag="target_nonzero_zero"
    )

    exists_prime = prime("p", tag="exists_prime")
    exists_target_bound = strictly_below("a", "p", tag="exists_target_bound")
    exists_input_bound = strictly_below("x", "p", tag="exists_input_bound")
    exists_inverse_bound = strictly_below("x1", "p", tag="exists_inverse_bound")
    exists_inverse_mod = _balanced_mod(
        "p", "x * x1", "1", variables=("p", "a", "x", "x1"), tag="exists_inverse_mod"
    )
    exists_raw = _balanced_mod(
        "p", "x * (a * x1)", "a", variables=("p", "a", "x", "x1"), tag="exists_raw"
    )
    exists_reduced = _balanced_mod(
        "p", "a * x1", "x3", variables=("p", "a", "x", "x1", "x3"), tag="exists_reduced"
    )
    exists_final = _balanced_mod(
        "p", "x * x3", "a", variables=("p", "a", "x", "x3"), tag="exists_final"
    )
    exists_relation = scaled_inverse("p", "a", "x", "y", tag="exists_result")

    unique_prime = prime("p", tag="unique_prime")
    unique_left = scaled_inverse("p", "a", "x", "y", tag="unique_left")
    unique_right = scaled_inverse("p", "a", "x", "z", tag="unique_right")
    unique_reverse = _balanced_mod(
        "p", "a", "x * z", variables=("p", "a", "x", "y", "z"), tag="unique_reverse"
    )
    unique_products = _balanced_mod(
        "p", "x * y", "x * z", variables=("p", "a", "x", "y", "z"), tag="unique_products"
    )
    unique_residues = _balanced_mod(
        "p", "y", "z", variables=("p", "a", "x", "y", "z"), tag="unique_residues"
    )

    symmetric_source = scaled_inverse("p", "a", "x", "y", tag="symmetric_source")
    symmetric_target = scaled_inverse("p", "a", "y", "x", tag="symmetric_target")
    involutive_prime = prime("p", tag="involutive_prime")
    involutive_xy = scaled_inverse("p", "a", "x", "y", tag="involutive_xy")
    involutive_yz = scaled_inverse("p", "a", "y", "z", tag="involutive_yz")
    involutive_yx = scaled_inverse("p", "a", "y", "x", tag="involutive_yx")

    fixed_relation = scaled_inverse("p", "a", "x", "x", tag="fixed_relation")
    fixed_square = scaled_fixed_point("p", "a", "x", tag="fixed_square")
    nonresidue = quadratic_residue("p", "a", tag="euler_scaled_inverse")
    no_fixed_relation = scaled_inverse("p", "a", "x", "x", tag="no_fixed_relation")
    decision_relation = scaled_inverse("p", "a", "x", "x", tag="decision_relation")

    return (
        spec(
            "scaled_inverse_from_unit_inverse",
            f"forall p a x z. ({inverse_xz}) -> ({scaled_result})",
            ("mod_eq_mul_left", "mul_assoc", "mul_comm", "mul_one"),
            (
                "intro p",
                "intro a",
                "intro x",
                "intro z",
                "intro hxz",
                f"have hscaled : {scaled_axz}",
                "specialize mod_eq_mul_left p",
                "specialize mod_eq_mul_left (x * z)",
                "specialize mod_eq_mul_left 1",
                "specialize mod_eq_mul_left a",
                "apply mod_eq_mul_left",
                "exact hxz",
                "have hleft : a * (x * z) = x * (a * z)",
                "trans (a * x) * z",
                "symm",
                "specialize mul_assoc a",
                "specialize mul_assoc x",
                "specialize mul_assoc z",
                "apply mul_assoc",
                "trans (x * a) * z",
                "congr",
                "apply mul_comm",
                "refl",
                "specialize mul_assoc x",
                "specialize mul_assoc a",
                "specialize mul_assoc z",
                "apply mul_assoc",
                "have hright : a * 1 = a",
                "specialize mul_one a",
                "exact mul_one",
                "rewrite hleft at hscaled",
                "rewrite hright at hscaled",
                "exact hscaled",
            ),
            "Multiplying an ordinary inverse by the target gives a scaled inverse.",
        ),
        spec(
            "scaled_inverse_transport_right",
            f"forall p a x y z. ({transport_source}) -> ({transport_argument}) -> "
            f"({transport_result})",
            ("mod_eq_mul_left", "mod_eq_symm", "mod_eq_trans"),
            (
                "intro p",
                "intro a",
                "intro x",
                "intro y",
                "intro z",
                "intro hxy",
                "intro hyz",
                f"have hscaled : {transport_scaled}",
                "specialize mod_eq_mul_left p",
                "specialize mod_eq_mul_left y",
                "specialize mod_eq_mul_left z",
                "specialize mod_eq_mul_left x",
                "apply mod_eq_mul_left",
                "exact hyz",
                f"have hreverse : {transport_reverse}",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm (x * y)",
                "specialize mod_eq_symm (x * z)",
                "apply mod_eq_symm",
                "exact hscaled",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans (x * z)",
                "specialize mod_eq_trans (x * y)",
                "specialize mod_eq_trans a",
                "apply mod_eq_trans",
                "exact hreverse",
                "exact hxy",
            ),
            "A scaled inverse survives replacement by a congruent right factor.",
        ),
        spec(
            "prime_scaled_inverse_target_nonzero",
            f"forall p a x y. ({prime_nonzero_target}) -> ~(a = 0) -> "
            f"({target_bound}) -> ({target_product}) -> ~(y = 0)",
            ("prime_is_succ_succ", "mod_eq_bounded_unique", "succ_ne_zero"),
            (
                "intro p",
                "intro a",
                "intro x",
                "intro y",
                "intro hp",
                "intro ha0",
                "intro hap",
                "intro hxy",
                "intro hy0",
                "have hp2 : exists k. p = S (S k)",
                "specialize prime_is_succ_succ p",
                "apply prime_is_succ_succ",
                "exact hp",
                "cases hp2",
                "have h0p : exists h. h + S 0 = p",
                "exists S x1",
                "rewrite hp2_witness",
                "simp",
                f"have hzeroa : {zero_target}",
                "cases hxy",
                "cases hxy_witness",
                "exists x2",
                "exists x3",
                "trans (x * y) + p * x2",
                "congr",
                "symm",
                "trans x * 0",
                "congr",
                "refl",
                "exact hy0",
                "apply PA5",
                "refl",
                "exact hxy_witness_witness",
                "have h0a : 0 = a",
                "specialize mod_eq_bounded_unique p",
                "specialize mod_eq_bounded_unique 0",
                "specialize mod_eq_bounded_unique a",
                "apply mod_eq_bounded_unique",
                "exact h0p",
                "exact hap",
                "exact hzeroa",
                "apply ha0",
                "symm",
                "exact h0a",
            ),
            "A scaled inverse of a nonzero bounded target cannot be zero.",
        ),
        spec(
            "prime_scaled_inverse_exists",
            f"forall p a x. ({exists_prime}) -> ~(a = 0) -> "
            f"({exists_target_bound}) -> ~(x = 0) -> ({exists_input_bound}) -> "
            f"exists y. ({exists_relation})",
            (
                "prime_bounded_nonzero_mod_inverse",
                "scaled_inverse_from_unit_inverse",
                "prime_nonzero",
                "division_remainder_exists",
                "mul_comm",
                "remainder_decomposition_to_mod_eq",
                "scaled_inverse_transport_right",
                "prime_scaled_inverse_target_nonzero",
            ),
            (
                "intro p",
                "intro a",
                "intro x",
                "intro hp",
                "intro ha0",
                "intro hap",
                "intro hx0",
                "intro hxp",
                f"have hinv : exists x1. (~(x1 = 0) /\\ (({exists_inverse_bound}) /\\ ({exists_inverse_mod})))",
                "specialize prime_bounded_nonzero_mod_inverse p",
                "specialize prime_bounded_nonzero_mod_inverse x",
                "apply prime_bounded_nonzero_mod_inverse",
                "exact hp",
                "exact hx0",
                "exact hxp",
                "cases hinv",
                "cases hinv_witness",
                "cases hinv_witness_right",
                f"have hraw : {exists_raw}",
                "specialize scaled_inverse_from_unit_inverse p",
                "specialize scaled_inverse_from_unit_inverse a",
                "specialize scaled_inverse_from_unit_inverse x",
                "specialize scaled_inverse_from_unit_inverse x1",
                "apply scaled_inverse_from_unit_inverse",
                "exact hinv_witness_right_right",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                "have hdiv : exists q r. a * x1 = p * q + r /\\ exists h. h + S r = p",
                "specialize division_remainder_exists p",
                "specialize division_remainder_exists (a * x1)",
                "apply division_remainder_exists",
                "exact hp0",
                "cases hdiv",
                "cases hdiv_witness",
                "cases hdiv_witness_witness",
                "have hdecomp : a * x1 = x2 * p + x3",
                "trans p * x2 + x3",
                "exact hdiv_witness_witness_left",
                "congr",
                "apply mul_comm",
                "refl",
                f"have hreduced : {exists_reduced}",
                "specialize remainder_decomposition_to_mod_eq p",
                "specialize remainder_decomposition_to_mod_eq (a * x1)",
                "specialize remainder_decomposition_to_mod_eq x2",
                "specialize remainder_decomposition_to_mod_eq x3",
                "apply remainder_decomposition_to_mod_eq",
                "exact hdecomp",
                f"have hfinal : {exists_final}",
                "specialize scaled_inverse_transport_right p",
                "specialize scaled_inverse_transport_right a",
                "specialize scaled_inverse_transport_right x",
                "specialize scaled_inverse_transport_right (a * x1)",
                "specialize scaled_inverse_transport_right x3",
                "apply scaled_inverse_transport_right",
                "exact hraw",
                "exact hreduced",
                "have hy0 : ~(x3 = 0)",
                "specialize prime_scaled_inverse_target_nonzero p",
                "specialize prime_scaled_inverse_target_nonzero a",
                "specialize prime_scaled_inverse_target_nonzero x",
                "specialize prime_scaled_inverse_target_nonzero x3",
                "intro hx3zero",
                "apply prime_scaled_inverse_target_nonzero",
                "exact hp",
                "exact ha0",
                "exact hap",
                "exact hfinal",
                "exact hx3zero",
                "exists x3",
                "split",
                "split",
                "exact hx0",
                "exact hxp",
                "split",
                "split",
                "exact hy0",
                "exact hdiv_witness_witness_right",
                "exact hfinal",
            ),
            "Every bounded nonzero prime residue has a bounded scaled inverse.",
        ),
        spec(
            "prime_scaled_inverse_unique",
            f"forall p a x y z. ({unique_prime}) -> ({unique_left}) -> "
            f"({unique_right}) -> y = z",
            (
                "divisor_le_nonzero",
                "lt_not_le",
                "mod_eq_symm",
                "mod_eq_trans",
                "prime_mod_cancel",
                "mod_eq_bounded_unique",
            ),
            (
                "intro p",
                "intro a",
                "intro x",
                "intro y",
                "intro z",
                "intro hp",
                "intro hxy",
                "intro hxz",
                "cases hxy",
                "cases hxy_left",
                "cases hxy_right",
                "cases hxy_right_left",
                "cases hxz",
                "cases hxz_left",
                "cases hxz_right",
                "cases hxz_right_left",
                "have hnotdiv : ~(exists k. x = p * k)",
                "intro hdiv",
                "have hpx : exists t. t + p = x",
                "specialize divisor_le_nonzero p",
                "specialize divisor_le_nonzero x",
                "apply divisor_le_nonzero",
                "exact hxy_left_left",
                "exact hdiv",
                "specialize lt_not_le x",
                "specialize lt_not_le p",
                "apply lt_not_le",
                "exact hxy_left_right",
                "exact hpx",
                f"have hreverse : {unique_reverse}",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm (x * z)",
                "specialize mod_eq_symm a",
                "apply mod_eq_symm",
                "exact hxz_right_right",
                f"have hproducts : {unique_products}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans (x * y)",
                "specialize mod_eq_trans a",
                "specialize mod_eq_trans (x * z)",
                "apply mod_eq_trans",
                "exact hxy_right_right",
                "exact hreverse",
                f"have hyz : {unique_residues}",
                "specialize prime_mod_cancel p",
                "specialize prime_mod_cancel x",
                "specialize prime_mod_cancel y",
                "specialize prime_mod_cancel z",
                "apply prime_mod_cancel",
                "exact hp",
                "exact hnotdiv",
                "exact hproducts",
                "specialize mod_eq_bounded_unique p",
                "specialize mod_eq_bounded_unique y",
                "specialize mod_eq_bounded_unique z",
                "apply mod_eq_bounded_unique",
                "exact hxy_right_left_right",
                "exact hxz_right_left_right",
                "exact hyz",
            ),
            "The bounded scaled inverse of a prime unit is unique.",
        ),
        spec(
            "scaled_inverse_symmetric",
            f"forall p a x y. ({symmetric_source}) -> ({symmetric_target})",
            ("mul_comm",),
            (
                "intro p",
                "intro a",
                "intro x",
                "intro y",
                "intro hxy",
                "cases hxy",
                "cases hxy_left",
                "cases hxy_right",
                "cases hxy_right_left",
                "split",
                "split",
                "exact hxy_right_left_left",
                "exact hxy_right_left_right",
                "split",
                "split",
                "exact hxy_left_left",
                "exact hxy_left_right",
                "have hcomm : x * y = y * x",
                "apply mul_comm",
                "rewrite hcomm at hxy_right_right",
                "exact hxy_right_right",
            ),
            "The scaled-inverse relation is symmetric.",
        ),
        spec(
            "prime_scaled_inverse_involutive",
            f"forall p a x y. ({involutive_prime}) -> ({involutive_xy}) -> "
            f"forall z. ({involutive_yz}) -> z = x",
            ("scaled_inverse_symmetric", "prime_scaled_inverse_unique"),
            (
                "intro p",
                "intro a",
                "intro x",
                "intro y",
                "intro hp",
                "intro hxy",
                "intro z",
                "intro hyz",
                f"have hyx : {involutive_yx}",
                "specialize scaled_inverse_symmetric p",
                "specialize scaled_inverse_symmetric a",
                "specialize scaled_inverse_symmetric x",
                "specialize scaled_inverse_symmetric y",
                "apply scaled_inverse_symmetric",
                "exact hxy",
                "specialize prime_scaled_inverse_unique p",
                "specialize prime_scaled_inverse_unique a",
                "specialize prime_scaled_inverse_unique y",
                "specialize prime_scaled_inverse_unique z",
                "specialize prime_scaled_inverse_unique x",
                "apply prime_scaled_inverse_unique",
                "exact hp",
                "exact hyz",
                "exact hyx",
            ),
            "Symmetry plus bounded uniqueness makes the scaled map involutive.",
        ),
        spec(
            "scaled_inverse_fixed_point_iff",
            f"forall p a x. ((({fixed_relation}) -> ({fixed_square})) /\\ "
            f"(({fixed_square}) -> ({fixed_relation})))",
            (),
            (
                "intro p",
                "intro a",
                "intro x",
                "split",
                "intro hrel",
                "cases hrel",
                "cases hrel_right",
                "split",
                "exact hrel_left",
                "exact hrel_right_right",
                "intro hfixed",
                "cases hfixed",
                "split",
                "exact hfixed_left",
                "split",
                "exact hfixed_left",
                "exact hfixed_right",
            ),
            "On the bounded unit domain, fixed points are exactly square roots of a.",
        ),
        spec(
            "scaled_inverse_no_fixed_of_not_qres",
            f"forall p a x. ~({nonresidue}) -> ~({no_fixed_relation})",
            ("scaled_inverse_fixed_point_iff",),
            (
                "intro p",
                "intro a",
                "intro x",
                "intro hnq",
                "intro hrel",
                f"have hfixed : {scaled_fixed_point('p', 'a', 'x', tag='no_fixed_square')}",
                "specialize scaled_inverse_fixed_point_iff p",
                "specialize scaled_inverse_fixed_point_iff a",
                "specialize scaled_inverse_fixed_point_iff x",
                "cases scaled_inverse_fixed_point_iff",
                "apply scaled_inverse_fixed_point_iff_left",
                "exact hrel",
                "cases hfixed",
                "apply hnq",
                "exists x",
                "exact hfixed_right",
            ),
            "A negative QRes witness makes the scaled involution fixed-point-free.",
        ),
        spec(
            "scaled_inverse_qres_or_fixed_free",
            f"forall p a. ~(p = 0) -> (({nonresidue}) \\/ "
            f"forall x. ~({decision_relation}))",
            (
                "quadratic_residue_decidable_nonzero",
                "scaled_inverse_no_fixed_of_not_qres",
            ),
            (
                "intro p",
                "intro a",
                "intro hp0",
                f"have hdec : ({nonresidue}) \\/ ~({nonresidue})",
                "specialize quadratic_residue_decidable_nonzero p",
                "specialize quadratic_residue_decidable_nonzero a",
                "apply quadratic_residue_decidable_nonzero",
                "exact hp0",
                "cases hdec",
                "left",
                "exact hdec_left",
                "right",
                "intro x",
                "specialize scaled_inverse_no_fixed_of_not_qres p",
                "specialize scaled_inverse_no_fixed_of_not_qres a",
                "specialize scaled_inverse_no_fixed_of_not_qres x",
                "intro hfixed",
                "apply scaled_inverse_no_fixed_of_not_qres",
                "exact hdec_right",
                "exact hfixed",
            ),
            "Decidable QRes exposes either a root or a fixed-point-free scaled relation.",
        ),
    )


__all__ = [
    "make_euler_scaled_inverse_candidate_theorems",
    "prime",
    "scaled_fixed_point",
    "scaled_inverse",
    "strictly_below",
    "unit_residue",
]
