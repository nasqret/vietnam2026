"""Static, isolated finite scale-product candidate for the Fermat route.

The theorem in this module is independent of residue-map construction.  It is
kept outside the public registry until WMI discovery and a receipt-pinned
admission replay both close its exact expanded first-order PA certificate.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, power_relation, product_relation


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
    names = tuple(f"fsp_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Fermat-scale binder captures an argument")
    return names


def strictly_below(left: str, right: str, *, tag: str) -> str:
    """Expand the witness-defined strict order ``left < right``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "lower term"), (right, "upper term"))
    )
    (gap,) = _binders(tag, variables, ("gap",))
    return f"exists {gap}. {gap} + S {left} = {right}"


def scaled_entry_mod(
    modulus: str,
    multiplier: str,
    source: str,
    target: str,
    *,
    tag: str,
) -> str:
    """Expand ``multiplier*source == target (mod modulus)``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (multiplier, "multiplier"),
            (source, "source value"),
            (target, "target value"),
        )
    )
    left_witness, right_witness = _binders(
        tag,
        variables,
        ("mod_left", "mod_right"),
    )
    return (
        f"exists {left_witness} {right_witness}. "
        f"{multiplier} * {source} + {modulus} * {left_witness} = "
        f"{target} + {modulus} * {right_witness}"
    )


def product_left_mod(
    modulus: str,
    left_factor: str,
    right_factor: str,
    target: str,
    *,
    tag: str,
) -> str:
    """Expand ``left_factor*right_factor == target (mod modulus)``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (left_factor, "left factor"),
            (right_factor, "right factor"),
            (target, "target"),
        )
    )
    left_witness, right_witness = _binders(
        tag,
        variables,
        ("product_mod_left", "product_mod_right"),
    )
    return (
        f"exists {left_witness} {right_witness}. "
        f"({left_factor} * {right_factor}) + {modulus} * {left_witness} = "
        f"{target} + {modulus} * {right_witness}"
    )


def scale_mod_prefix(
    modulus: str,
    multiplier: str,
    source_code: str,
    source_scale: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand pointwise multiplication congruence between two beta prefixes."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (multiplier, "multiplier"),
            (source_code, "source code"),
            (source_scale, "source scale"),
            (target_code, "target code"),
            (target_scale, "target scale"),
            (length, "length"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    (
        index,
        source,
        target,
        gap,
        source_height,
        source_quotient,
        target_height,
        target_quotient,
        left_witness,
        right_witness,
    ) = _binders(
        safe_tag,
        variables,
        (
            "index",
            "source",
            "target",
            "gap",
            "source_height",
            "source_quotient",
            "target_height",
            "target_quotient",
            "mod_left",
            "mod_right",
        ),
    )
    source_modulus = f"S ((S ({index})) * {source_scale})"
    target_modulus = f"S ((S ({index})) * {target_scale})"
    bound = f"exists {gap}. {gap} + S {index} = {length}"
    source_entry = (
        f"((exists {source_height}. {source_height} + S ({source}) = "
        f"{source_modulus}) /\\ exists {source_quotient}. "
        f"{source_code} = {source_quotient} * {source_modulus} + ({source}))"
    )
    target_entry = (
        f"((exists {target_height}. {target_height} + S ({target}) = "
        f"{target_modulus}) /\\ exists {target_quotient}. "
        f"{target_code} = {target_quotient} * {target_modulus} + ({target}))"
    )
    congruence = (
        f"exists {left_witness} {right_witness}. "
        f"{multiplier} * {source} + {modulus} * {left_witness} = "
        f"{target} + {modulus} * {right_witness}"
    )
    return (
        f"forall {index} {source} {target}. ({bound}) -> "
        f"({source_entry}) -> ({target_entry}) -> ({congruence})"
    )


def _product_decomposition(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "factor code"),
            (scale, "factor scale"),
            (length, "length"),
            (result, "product result"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    factor, prefix = _binders(
        safe_tag,
        variables,
        ("decomposition_factor", "decomposition_prefix"),
    )
    final_factor = beta_at(
        code,
        scale,
        length,
        factor,
        tag=f"{safe_tag}_factor",
    )
    prefix_product = product_relation(
        code,
        scale,
        length,
        prefix,
        tag=f"{safe_tag}_prefix",
    )
    return (
        f"exists {factor} {prefix}. ({final_factor}) /\\ "
        f"(({prefix_product}) /\\ {result} = {prefix} * {factor})"
    )


def _power_decomposition(
    base: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (base, "power base"),
            (length, "power length"),
            (result, "power result"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    (prefix,) = _binders(safe_tag, variables, ("power_prefix",))
    prefix_power = power_relation(
        base,
        length,
        prefix,
        tag=f"{safe_tag}_relation",
    )
    return f"exists {prefix}. ({prefix_power}) /\\ {result} = {prefix} * {base}"


def make_fermat_scale_product_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated pointwise-scale product theorem data."""

    pointwise = scale_mod_prefix(
        "m",
        "a",
        "b",
        "c",
        "z",
        "d",
        "l",
        tag="pointwise",
    )
    source_product = product_relation("b", "c", "l", "P", tag="source")
    target_product = product_relation("z", "d", "l", "Q", tag="target")
    power = power_relation("a", "l", "A", tag="scale_power")
    result = product_left_mod("m", "A", "P", "Q", tag="result")

    source_decomposition = _product_decomposition(
        "b",
        "c",
        "l",
        "P",
        tag="source_decomposition",
    )
    target_decomposition = _product_decomposition(
        "z",
        "d",
        "l",
        "Q",
        tag="target_decomposition",
    )
    power_decomposition = _power_decomposition(
        "a",
        "l",
        "A",
        tag="power_decomposition",
    )
    pointwise_prefix = scale_mod_prefix(
        "m",
        "a",
        "b",
        "c",
        "z",
        "d",
        "l",
        tag="pointwise_prefix",
    )

    return (
        spec(
            "beta_product_pointwise_scale_mod",
            f"forall m a b c z d l P Q A. ({pointwise}) -> "
            f"({source_product}) -> ({target_product}) -> ({power}) -> ({result})",
            (
                "beta_product_zero",
                "beta_product_succ_decompose",
                "pow_zero",
                "pow_successor_decompose",
                "le_succ",
                "le_refl",
                "mod_eq_refl",
                "mod_eq_mul",
                "mul_assoc",
                "mul_comm",
                "one_mul",
            ),
            (
                "intro m",
                "intro a",
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "induction l",
                "intro P",
                "intro Q",
                "intro A",
                "intro hpw",
                "intro hP",
                "intro hQ",
                "intro hA",
                "have hP1 : P = 1",
                "specialize beta_product_zero b",
                "specialize beta_product_zero c",
                "specialize beta_product_zero P",
                "apply beta_product_zero",
                "exact hP",
                "have hQ1 : Q = 1",
                "specialize beta_product_zero z",
                "specialize beta_product_zero d",
                "specialize beta_product_zero Q",
                "apply beta_product_zero",
                "exact hQ",
                "have hA1 : A = 1",
                "specialize pow_zero a",
                "specialize pow_zero 0",
                "specialize pow_zero A",
                "apply pow_zero",
                "refl",
                "exact hA",
                "rewrite hA1",
                "rewrite hP1",
                "rewrite hQ1",
                "have hone : 1 * 1 = 1",
                "specialize one_mul 1",
                "exact one_mul",
                "rewrite hone",
                "specialize mod_eq_refl m",
                "specialize mod_eq_refl 1",
                "exact mod_eq_refl",
                "intro P",
                "intro Q",
                "intro A",
                "intro hpw",
                "intro hP",
                "intro hQ",
                "intro hA",
                f"have hPd : {source_decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose l",
                "specialize beta_product_succ_decompose P",
                "apply beta_product_succ_decompose",
                "exact hP",
                "cases hPd",
                "cases hPd_witness",
                "cases hPd_witness_witness",
                "cases hPd_witness_witness_right",
                f"have hQd : {target_decomposition}",
                "specialize beta_product_succ_decompose z",
                "specialize beta_product_succ_decompose d",
                "specialize beta_product_succ_decompose l",
                "specialize beta_product_succ_decompose Q",
                "apply beta_product_succ_decompose",
                "exact hQ",
                "cases hQd",
                "cases hQd_witness",
                "cases hQd_witness_witness",
                "cases hQd_witness_witness_right",
                f"have hAd : {power_decomposition}",
                "specialize pow_successor_decompose a",
                "specialize pow_successor_decompose l",
                "specialize pow_successor_decompose (S l)",
                "specialize pow_successor_decompose A",
                "apply pow_successor_decompose",
                "refl",
                "exact hA",
                "cases hAd",
                "cases hAd_witness",
                f"have hpw_prefix : {pointwise_prefix}",
                "intro i",
                "intro v",
                "intro w",
                "intro hi",
                "intro hv",
                "intro hw",
                "specialize hpw i",
                "specialize hpw v",
                "specialize hpw w",
                "apply hpw",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact hv",
                "exact hw",
                "have hprefix : exists u v. (x4 * x1) + m * u = "
                "x3 + m * v",
                "specialize IH x1",
                "specialize IH x3",
                "specialize IH x4",
                "apply IH",
                "exact hpw_prefix",
                "exact hPd_witness_witness_right_left",
                "exact hQd_witness_witness_right_left",
                "exact hAd_witness_left",
                "have hentry : exists u v. (a * x) + m * u = "
                "x2 + m * v",
                "specialize hpw l",
                "specialize hpw x",
                "specialize hpw x2",
                "apply hpw",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hPd_witness_witness_left",
                "exact hQd_witness_witness_left",
                "have hfold : exists u v. ((x4 * x1) * (a * x)) + "
                "m * u = (x3 * x2) + m * v",
                "specialize mod_eq_mul m",
                "specialize mod_eq_mul (x4 * x1)",
                "specialize mod_eq_mul x3",
                "specialize mod_eq_mul (a * x)",
                "specialize mod_eq_mul x2",
                "apply mod_eq_mul",
                "exact hprefix",
                "exact hentry",
                "have hshuffle : (x4 * a) * (x1 * x) = "
                "(x4 * x1) * (a * x)",
                "simp [mul_assoc, mul_comm]",
                "rewrite hAd_witness_right",
                "rewrite hPd_witness_witness_right_right",
                "rewrite hQd_witness_witness_right_right",
                "rewrite hshuffle",
                "exact hfold",
            ),
            "Pointwise multiplication by a constant scales a finite product by its power.",
        ),
    )


__all__ = [
    "make_fermat_scale_product_candidate_theorems",
    "product_left_mod",
    "scale_mod_prefix",
    "scaled_entry_mod",
    "strictly_below",
]
