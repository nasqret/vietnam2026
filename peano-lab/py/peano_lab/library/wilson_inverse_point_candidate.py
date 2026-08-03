"""Isolated pointwise inverse-index candidates for the native Wilson route.

The decoded values in this module are zero-based indices: an entry ``j`` at
index ``i`` represents the residue inverse ``S j`` of ``S i`` modulo
``p = S n``.  All readable surfaces expand immediately to the unchanged
first-order Peano language.  The factory is deliberately absent from the
public theorem registry pending WMI discovery and receipt-pinned admission.
"""

from __future__ import annotations

from typing import Any, Callable


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
    names = tuple(f"wip_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Wilson-inverse binder captures an argument")
    return names


def _balanced_terms(
    modulus: str,
    left: str,
    right: str,
    variables: tuple[str, ...],
    *,
    tag: str,
) -> str:
    left_witness, right_witness = _binders(
        tag,
        variables,
        ("mod_left", "mod_right"),
    )
    return (
        f"exists {left_witness} {right_witness}. "
        f"{left} + {modulus} * {left_witness} = "
        f"{right} + {modulus} * {right_witness}"
    )


def prime(value: str, *, tag: str) -> str:
    """Expand primality through the nonunit factor-pair definition."""

    variable = _identifier(value, "prime candidate")
    left, right = _binders(tag, (variable,), ("prime_left", "prime_right"))
    return (
        f"(~({value} = 1) /\\ forall {left} {right}. "
        f"{value} = {left} * {right} -> {left} = 1 \\/ {right} = 1)"
    )


def strictly_below(left: str, right: str, *, tag: str) -> str:
    """Expand the witness-defined strict inequality ``left < right``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "lower term"), (right, "upper term"))
    )
    (gap,) = _binders(tag, variables, ("strict_gap",))
    return f"exists {gap}. {gap} + S {left} = {right}"


def successor_strictly_below(index: str, right: str, *, tag: str) -> str:
    """Expand ``S index < right`` without accepting an arbitrary term."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((index, "index"), (right, "upper term"))
    )
    (gap,) = _binders(tag, variables, ("successor_gap",))
    return f"exists {gap}. {gap} + S (S {index}) = {right}"


def balanced_inverse(
    modulus: str,
    value: str,
    inverse: str,
    *,
    tag: str,
) -> str:
    """Expand ``value * inverse == 1 (mod modulus)``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (modulus, "modulus"),
            (value, "value"),
            (inverse, "inverse"),
        )
    )
    return _balanced_terms(
        modulus,
        f"{value} * {inverse}",
        "1",
        variables,
        tag=tag,
    )


def successor_inverse(
    modulus: str,
    left_index: str,
    right_index: str,
    *,
    tag: str,
) -> str:
    """Expand ``S i * S j == 1 (mod modulus)``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (modulus, "modulus"),
            (left_index, "left index"),
            (right_index, "right index"),
        )
    )
    return _balanced_terms(
        modulus,
        f"(S {left_index}) * S {right_index}",
        "1",
        variables,
        tag=tag,
    )


def bounded_successor_inverse(
    modulus: str,
    index: str,
    *,
    tag: str,
) -> str:
    """Expand existence of a bounded nonzero inverse of ``S index``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in ((modulus, "modulus"), (index, "index"))
    )
    (inverse,) = _binders(tag, variables, ("inverse",))
    bound = strictly_below(inverse, modulus, tag=f"{tag}_bound")
    congruence = _balanced_terms(
        modulus,
        f"(S {index}) * {inverse}",
        "1",
        variables + (inverse,),
        tag=f"{tag}_congruence",
    )
    return (
        f"exists {inverse}. (~({inverse} = 0) /\\ "
        f"(({bound}) /\\ ({congruence})))"
    )


def inverse_index(
    modulus: str,
    length: str,
    left_index: str,
    right_index: str,
    *,
    tag: str,
) -> str:
    """Expand the symmetric bounded inverse-index relation."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (modulus, "modulus"),
            (length, "ambient length"),
            (left_index, "left index"),
            (right_index, "right index"),
        )
    )
    modulus, length, left_index, right_index = variables
    safe_tag = _identifier(tag, "binder tag")
    left_bound = strictly_below(
        left_index,
        length,
        tag=f"{safe_tag}_left_bound",
    )
    right_bound = strictly_below(
        right_index,
        length,
        tag=f"{safe_tag}_right_bound",
    )
    congruence = successor_inverse(
        modulus,
        left_index,
        right_index,
        tag=f"{safe_tag}_inverse",
    )
    return f"(({left_bound}) /\\ (({right_bound}) /\\ ({congruence})))"


def make_wilson_inverse_point_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the four isolated pointwise inverse-index candidates."""

    prime_p = prime("p", tag="exists_prime")
    i_below_n = strictly_below("i", "n", tag="exists_index_bound")
    successor_i_below_p = successor_strictly_below(
        "i", "p", tag="exists_residue_bound"
    )
    raw_inverse = bounded_successor_inverse("p", "i", tag="exists_raw")
    exists_result = inverse_index("p", "n", "i", "j", tag="exists_result")

    y_below_p = strictly_below("y", "p", tag="unique_y_bound")
    z_below_p = strictly_below("z", "p", tag="unique_z_bound")
    inverse_xy = balanced_inverse("p", "x", "y", tag="unique_xy")
    inverse_xz = balanced_inverse("p", "x", "z", tag="unique_xz")
    reverse_xz = _balanced_terms(
        "p", "1", "x * z", ("p", "x", "z"), tag="unique_reverse_xz"
    )
    left_scaled = _balanced_terms(
        "p",
        "y * 1",
        "y * (x * z)",
        ("p", "x", "y", "z"),
        tag="unique_left_scaled",
    )
    right_scaled = _balanced_terms(
        "p",
        "(x * y) * z",
        "1 * z",
        ("p", "x", "y", "z"),
        tag="unique_right_scaled",
    )
    y_congruent_z = _balanced_terms(
        "p", "y", "z", ("p", "y", "z"), tag="unique_result"
    )

    left_relation = inverse_index("p", "n", "i", "j", tag="index_unique_left")
    right_relation = inverse_index(
        "p", "n", "i", "k", tag="index_unique_right"
    )
    successor_j_below_p = successor_strictly_below(
        "j", "p", tag="index_unique_j_bound"
    )
    successor_k_below_p = successor_strictly_below(
        "k", "p", tag="index_unique_k_bound"
    )
    symmetric_source = inverse_index("p", "n", "i", "j", tag="symmetric_source")
    symmetric_target = inverse_index("p", "n", "j", "i", tag="symmetric_target")

    return (
        spec(
            "prime_inverse_index_exists",
            f"forall p n i. p = S n -> ({prime_p}) -> ({i_below_n}) -> "
            f"exists j. ({exists_result})",
            (
                "succ_ne_zero",
                "succ_le_succ",
                "prime_bounded_nonzero_mod_inverse",
                "nonzero_is_succ",
                "le_of_succ_le_succ",
            ),
            (
                "intro p",
                "intro n",
                "intro i",
                "intro hpn",
                "intro hp",
                "intro hi",
                "have hsi0 : ~(S i = 0)",
                "specialize succ_ne_zero i",
                "exact succ_ne_zero",
                f"have hsip : {successor_i_below_p}",
                "rewrite hpn",
                "specialize succ_le_succ (S i)",
                "specialize succ_le_succ n",
                "apply succ_le_succ",
                "exact hi",
                f"have hinv : {raw_inverse}",
                "specialize prime_bounded_nonzero_mod_inverse p",
                "specialize prime_bounded_nonzero_mod_inverse (S i)",
                "apply prime_bounded_nonzero_mod_inverse",
                "exact hp",
                "exact hsi0",
                "exact hsip",
                "cases hinv",
                "cases hinv_witness",
                "cases hinv_witness_right",
                "have hpred : exists j. x = S j",
                "specialize nonzero_is_succ x",
                "apply nonzero_is_succ",
                "exact hinv_witness_left",
                "cases hpred",
                f"have hjn : {strictly_below('x1', 'n', tag='exists_output_bound')}",
                "specialize le_of_succ_le_succ (S x1)",
                "specialize le_of_succ_le_succ n",
                "apply le_of_succ_le_succ",
                "rewrite <- hpred_witness",
                "rewrite <- hpn",
                "exact hinv_witness_right_left",
                "exists x1",
                "split",
                "exact hi",
                "split",
                "exact hjn",
                "rewrite hpred_witness at hinv_witness_right_right",
                "exact hinv_witness_right_right",
            ),
            "Every nonzero prime residue index has a bounded inverse index.",
        ),
        spec(
            "bounded_mod_inverse_unique",
            f"forall p x y z. ({y_below_p}) -> ({z_below_p}) -> "
            f"({inverse_xy}) -> ({inverse_xz}) -> y = z",
            (
                "mod_eq_symm",
                "mod_eq_mul_left",
                "mod_eq_mul_right",
                "mul_assoc",
                "mul_comm",
                "mul_one",
                "one_mul",
                "mod_eq_trans",
                "mod_eq_bounded_unique",
            ),
            (
                "intro p",
                "intro x",
                "intro y",
                "intro z",
                "intro hy",
                "intro hz",
                "intro hxy",
                "intro hxz",
                f"have hreverse : {reverse_xz}",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm (x * z)",
                "specialize mod_eq_symm 1",
                "apply mod_eq_symm",
                "exact hxz",
                f"have hleftscaled : {left_scaled}",
                "specialize mod_eq_mul_left p",
                "specialize mod_eq_mul_left 1",
                "specialize mod_eq_mul_left (x * z)",
                "specialize mod_eq_mul_left y",
                "apply mod_eq_mul_left",
                "exact hreverse",
                f"have hrightscaled : {right_scaled}",
                "specialize mod_eq_mul_right p",
                "specialize mod_eq_mul_right (x * y)",
                "specialize mod_eq_mul_right 1",
                "specialize mod_eq_mul_right z",
                "apply mod_eq_mul_right",
                "exact hxy",
                "have hleft : y * 1 = y",
                "specialize mul_one y",
                "exact mul_one",
                "have hmiddle : y * (x * z) = (x * y) * z",
                "trans (y * x) * z",
                "symm",
                "specialize mul_assoc y",
                "specialize mul_assoc x",
                "specialize mul_assoc z",
                "apply mul_assoc",
                "congr",
                "apply mul_comm",
                "refl",
                "have hright : 1 * z = z",
                "specialize one_mul z",
                "exact one_mul",
                "rewrite hleft at hleftscaled",
                "rewrite hmiddle at hleftscaled",
                "rewrite hright at hrightscaled",
                f"have hyz : {y_congruent_z}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans y",
                "specialize mod_eq_trans ((x * y) * z)",
                "specialize mod_eq_trans z",
                "apply mod_eq_trans",
                "exact hleftscaled",
                "exact hrightscaled",
                "specialize mod_eq_bounded_unique p",
                "specialize mod_eq_bounded_unique y",
                "specialize mod_eq_bounded_unique z",
                "apply mod_eq_bounded_unique",
                "exact hy",
                "exact hz",
                "exact hyz",
            ),
            "Two bounded inverses of the same residue are equal.",
        ),
        spec(
            "bounded_inverse_index_unique",
            f"forall p n i j k. p = S n -> ({left_relation}) -> "
            f"({right_relation}) -> j = k",
            (
                "succ_le_succ",
                "bounded_mod_inverse_unique",
                "succ_injective",
            ),
            (
                "intro p",
                "intro n",
                "intro i",
                "intro j",
                "intro k",
                "intro hpn",
                "intro hij",
                "intro hik",
                "cases hij",
                "cases hij_right",
                "cases hik",
                "cases hik_right",
                f"have hjp : {successor_j_below_p}",
                "rewrite hpn",
                "specialize succ_le_succ (S j)",
                "specialize succ_le_succ n",
                "apply succ_le_succ",
                "exact hij_right_left",
                f"have hkp : {successor_k_below_p}",
                "rewrite hpn",
                "specialize succ_le_succ (S k)",
                "specialize succ_le_succ n",
                "apply succ_le_succ",
                "exact hik_right_left",
                "have hsucc : S j = S k",
                "specialize bounded_mod_inverse_unique p",
                "specialize bounded_mod_inverse_unique (S i)",
                "specialize bounded_mod_inverse_unique (S j)",
                "specialize bounded_mod_inverse_unique (S k)",
                "apply bounded_mod_inverse_unique",
                "exact hjp",
                "exact hkp",
                "exact hij_right_right",
                "exact hik_right_right",
                "specialize succ_injective j",
                "specialize succ_injective k",
                "apply succ_injective",
                "exact hsucc",
            ),
            "A bounded inverse index is unique.",
        ),
        spec(
            "inverse_index_symmetric",
            f"forall p n i j. ({symmetric_source}) -> ({symmetric_target})",
            ("mul_comm",),
            (
                "intro p",
                "intro n",
                "intro i",
                "intro j",
                "intro hij",
                "cases hij",
                "cases hij_right",
                "split",
                "exact hij_right_left",
                "split",
                "exact hij_left",
                "have hcomm : (S i) * S j = (S j) * S i",
                "apply mul_comm",
                "rewrite hcomm at hij_right_right",
                "exact hij_right_right",
            ),
            "The bounded inverse-index relation is symmetric.",
        ),
    )


__all__ = [
    "balanced_inverse",
    "bounded_successor_inverse",
    "inverse_index",
    "make_wilson_inverse_point_candidate_theorems",
    "prime",
    "strictly_below",
    "successor_inverse",
    "successor_strictly_below",
]
