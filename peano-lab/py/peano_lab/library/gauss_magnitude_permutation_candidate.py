"""Isolated magnitude-range and modular-collision candidates for Gauss.

This untrusted authoring module starts the magnitude-permutation tranche after
``gauss_signed_prefix_candidate``.  It does not register any theorem.  Every
surface helper expands immediately to first-order Peano arithmetic, and every
script is intended first for dependency-curried body replay only.  Closed
replay, profiling, mutation testing, and admission remain WMI-only work.

The key constructive observation is that a mixed-sign collision forces
``a * (x + y) == 0 (mod p)``.  Prime cancellation then forces
``x + y == 0 (mod p)``, contradicting ``0 < x + y < p``.  No excluded middle,
integer subtraction, primitive congruence, or ``ring`` tactic is used.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at
from .finite_permutation_theorems import (
    bounded_prefix,
    injective_prefix,
    surjective_prefix,
)
from .gauss_signed_prefix_candidate import (
    _beta_at_term,
    _entry_term,
    _strictly_below_term,
    _weakly_below_term,
    half_range,
    not_divides,
    prime,
    signed_half_prefix,
)


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
    names = tuple(f"gmp_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Gauss-magnitude binder captures an argument")
    return names


def _balanced_mod_term(
    modulus: str,
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    left_witness, right_witness = _binders(
        tag,
        variables,
        ("mod_left", "mod_right"),
    )
    return (
        f"exists {left_witness} {right_witness}. ({left}) + {modulus} * "
        f"{left_witness} = ({right}) + {modulus} * {right_witness}"
    )


def _magnitude_range_term(
    magnitude_code: str,
    magnitude_scale: str,
    half: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    index, magnitude = _binders(tag, variables, ("index", "magnitude"))
    owned = variables + (index, magnitude)
    index_bound = _strictly_below_term(
        index,
        length_term,
        tag=f"{tag}_index_bound",
        variables=owned,
    )
    decoded = beta_at(
        magnitude_code,
        magnitude_scale,
        index,
        magnitude,
        tag=f"gmp_{tag}_decoded",
    )
    positive = _strictly_below_term(
        "0",
        magnitude,
        tag=f"{tag}_positive",
        variables=owned,
    )
    bounded = _weakly_below_term(
        magnitude,
        half,
        tag=f"{tag}_bounded",
        variables=owned,
    )
    return (
        f"forall {index}. ({index_bound}) -> exists {magnitude}. "
        f"(({decoded}) /\\ (({positive}) /\\ ({bounded})))"
    )


def magnitude_range_prefix(
    magnitude_code: str,
    magnitude_scale: str,
    half: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand: every decoded magnitude lies in the interval ``1,...,half``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (magnitude_code, "magnitude code"),
            (magnitude_scale, "magnitude scale"),
            (half, "half bound"),
            (length, "prefix length"),
        )
    )
    return _magnitude_range_term(
        magnitude_code,
        magnitude_scale,
        half,
        length,
        tag=tag,
        variables=variables,
    )


def _predecessor_recode_term(
    source_code: str,
    source_scale: str,
    target_code: str,
    target_scale: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    index, predecessor = _binders(tag, variables, ("index", "predecessor"))
    owned = variables + (index, predecessor)
    bound = _strictly_below_term(
        index,
        length_term,
        tag=f"{tag}_index_bound",
        variables=owned,
    )
    source = _beta_at_term(
        source_code,
        source_scale,
        index,
        f"S {predecessor}",
        tag=f"gmp_{tag}_source",
        variables=owned,
    )
    target = beta_at(
        target_code,
        target_scale,
        index,
        predecessor,
        tag=f"gmp_{tag}_target",
    )
    return (
        f"forall {index} {predecessor}. ({bound}) -> "
        f"({source}) -> ({target})"
    )


def predecessor_recode_prefix(
    source_code: str,
    source_scale: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand pointwise recoding from decoded ``S r`` to decoded ``r``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (source_code, "source code"),
            (source_scale, "source scale"),
            (target_code, "target code"),
            (target_scale, "target scale"),
            (length, "prefix length"),
        )
    )
    return _predecessor_recode_term(
        source_code,
        source_scale,
        target_code,
        target_scale,
        length,
        tag=tag,
        variables=variables,
    )


def make_gauss_magnitude_permutation_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the first dependency-ordered magnitude-permutation candidates."""

    signed_prefix = signed_half_prefix(
        "p",
        "h",
        "a",
        "b",
        "c",
        "mb",
        "mc",
        "sb",
        "sc",
        "l",
        tag="magnitude_range_source",
    )
    magnitude_range = magnitude_range_prefix(
        "mb", "mc", "h", "l", tag="magnitude_range_result"
    )
    signed_entry_i = _entry_term(
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
        tag="magnitude_range_entry",
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
            "l",
            "i",
        ),
    )

    prime_p = prime("p", tag="collision_prime")
    multiplier_nondivisor = not_divides("p", "a", tag="collision_multiplier")
    x_bound = _strictly_below_term(
        "x",
        "p",
        tag="collision_x_bound",
        variables=("p", "h", "a", "x", "y", "m", "t"),
    )
    y_bound = _strictly_below_term(
        "y",
        "p",
        tag="collision_y_bound",
        variables=("p", "h", "a", "x", "y", "m", "t"),
    )
    ax_target = _balanced_mod_term(
        "p",
        "a * x",
        "t",
        tag="same_target_x",
        variables=("p", "h", "a", "x", "y", "m", "t"),
    )
    ay_target = _balanced_mod_term(
        "p",
        "a * y",
        "t",
        tag="same_target_y",
        variables=("p", "h", "a", "x", "y", "m", "t"),
    )
    target_reverse = _balanced_mod_term(
        "p",
        "t",
        "a * y",
        tag="same_target_reverse",
        variables=("p", "h", "a", "x", "y", "m", "t"),
    )
    scaled_xy = _balanced_mod_term(
        "p",
        "a * x",
        "a * y",
        tag="same_target_scaled",
        variables=("p", "h", "a", "x", "y", "m", "t"),
    )
    canceled_xy = _balanced_mod_term(
        "p",
        "x",
        "y",
        tag="same_target_canceled",
        variables=("p", "h", "a", "x", "y", "m", "t"),
    )

    ax_lower = _balanced_mod_term(
        "p",
        "a * x",
        "m",
        tag="same_sign_x_lower",
        variables=("p", "h", "a", "x", "y", "m"),
    )
    ay_lower = _balanced_mod_term(
        "p",
        "a * y",
        "m",
        tag="same_sign_y_lower",
        variables=("p", "h", "a", "x", "y", "m"),
    )
    reflected_target = "(2 * h) * m"
    ax_reflected = _balanced_mod_term(
        "p",
        "a * x",
        reflected_target,
        tag="same_sign_x_reflected",
        variables=("p", "h", "a", "x", "y", "m"),
    )
    ay_reflected = _balanced_mod_term(
        "p",
        "a * y",
        reflected_target,
        tag="same_sign_y_reflected",
        variables=("p", "h", "a", "x", "y", "m"),
    )
    same_sign_cases = (
        f"((({ax_lower}) /\\ ({ay_lower})) \\/ "
        f"(({ax_reflected}) /\\ ({ay_reflected})))"
    )

    mixed_ax_lower = _balanced_mod_term(
        "p",
        "a * x",
        "m",
        tag="mixed_x_lower",
        variables=("p", "h", "a", "x", "y", "m"),
    )
    mixed_ay_reflected = _balanced_mod_term(
        "p",
        "a * y",
        reflected_target,
        tag="mixed_y_reflected",
        variables=("p", "h", "a", "x", "y", "m"),
    )
    sum_bound = _strictly_below_term(
        "(x + y)",
        "p",
        tag="mixed_sum_bound",
        variables=("p", "h", "a", "x", "y", "m"),
    )
    added_congruence = _balanced_mod_term(
        "p",
        "a * x + a * y",
        f"m + {reflected_target}",
        tag="mixed_added",
        variables=("p", "h", "a", "x", "y", "m"),
    )
    scaled_sum_multiple = _balanced_mod_term(
        "p",
        "a * (x + y)",
        "p * m",
        tag="mixed_scaled_sum_multiple",
        variables=("p", "h", "a", "x", "y", "m"),
    )
    multiple_zero = _balanced_mod_term(
        "p",
        "p * m",
        "0",
        tag="mixed_multiple_zero",
        variables=("p", "h", "a", "x", "y", "m"),
    )
    scaled_sum_zero = _balanced_mod_term(
        "p",
        "a * (x + y)",
        "0",
        tag="mixed_scaled_sum_zero",
        variables=("p", "h", "a", "x", "y", "m"),
    )
    scaled_sum_factor_zero = _balanced_mod_term(
        "p",
        "a * (x + y)",
        "a * 0",
        tag="mixed_scaled_sum_factor_zero",
        variables=("p", "h", "a", "x", "y", "m"),
    )
    sum_zero_mod = _balanced_mod_term(
        "p",
        "x + y",
        "0",
        tag="mixed_sum_zero",
        variables=("p", "h", "a", "x", "y", "m"),
    )
    zero_bound = _strictly_below_term(
        "0",
        "p",
        tag="mixed_zero_bound",
        variables=("p", "h", "a", "x", "y", "m"),
    )

    injective_half_range = half_range("b", "c", "h", tag="injective_source")
    injective_signed_prefix = signed_half_prefix(
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
        tag="injective_signed_source",
    )
    injective_result = injective_prefix(
        "mb", "mc", "h", tag="signed_magnitude_injective"
    )
    injective_entry_i = _entry_term(
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
        tag="injective_entry_i",
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
            "i",
            "j",
            "m",
        ),
    )
    injective_entry_j = _entry_term(
        "p",
        "h",
        "a",
        "b",
        "c",
        "mb",
        "mc",
        "sb",
        "sc",
        "j",
        tag="injective_entry_j",
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
            "i",
            "j",
            "m",
        ),
    )
    injective_i_lower = _balanced_mod_term(
        "p",
        "a * x",
        "m",
        tag="injective_i_lower",
        variables=("p", "h", "a", "x", "x2", "x3", "x5", "m"),
    )
    injective_i_reflected = _balanced_mod_term(
        "p",
        "a * x",
        "(2 * h) * m",
        tag="injective_i_reflected",
        variables=("p", "h", "a", "x", "x2", "x3", "x5", "m"),
    )
    injective_j_lower = _balanced_mod_term(
        "p",
        "a * x3",
        "m",
        tag="injective_j_lower",
        variables=("p", "h", "a", "x", "x2", "x3", "x5", "m"),
    )
    injective_j_reflected = _balanced_mod_term(
        "p",
        "a * x3",
        "(2 * h) * m",
        tag="injective_j_reflected",
        variables=("p", "h", "a", "x", "x2", "x3", "x5", "m"),
    )
    injective_i_signed = (
        f"((x2 = 0 /\\ ({injective_i_lower})) \\/ "
        f"(x2 = 1 /\\ ({injective_i_reflected})))"
    )
    injective_j_signed = (
        f"((x5 = 0 /\\ ({injective_j_lower})) \\/ "
        f"(x5 = 1 /\\ ({injective_j_reflected})))"
    )
    injective_x_bound = _strictly_below_term(
        "x",
        "p",
        tag="injective_x_bound",
        variables=("p", "h", "a", "x", "x3", "m"),
    )
    injective_y_bound = _strictly_below_term(
        "x3",
        "p",
        tag="injective_y_bound",
        variables=("p", "h", "a", "x", "x3", "m"),
    )
    injective_x_le_half = _weakly_below_term(
        "x",
        "h",
        tag="injective_x_le_half",
        variables=("p", "h", "a", "x", "x3", "m"),
    )
    injective_y_le_half = _weakly_below_term(
        "x3",
        "h",
        tag="injective_y_le_half",
        variables=("p", "h", "a", "x", "x3", "m"),
    )
    injective_sum_first = (
        "exists gmp_sum_first_gap. gmp_sum_first_gap + (x + x3) = h + x3"
    )
    injective_sum_second = (
        "exists gmp_sum_second_gap. gmp_sum_second_gap + (h + x3) = h + h"
    )
    injective_sum_le_double = (
        "exists gmp_sum_double_gap. gmp_sum_double_gap + (x + x3) = h + h"
    )
    injective_double_below = (
        "exists gmp_double_below_gap. gmp_double_below_gap + S (h + h) = p"
    )
    injective_sum_bound = _strictly_below_term(
        "(x + x3)",
        "p",
        tag="injective_sum_bound",
        variables=("p", "h", "a", "x", "x3", "m"),
    )
    injective_reverse_sum_bound = _strictly_below_term(
        "(x3 + x)",
        "p",
        tag="injective_reverse_sum_bound",
        variables=("p", "h", "a", "x", "x3", "m"),
    )

    recode_range = magnitude_range_prefix(
        "mb", "mc", "H", "l", tag="predecessor_recode_range"
    )
    recode_previous_range = magnitude_range_prefix(
        "mb", "mc", "H", "l", tag="predecessor_recode_previous_range"
    )
    recode_previous_result = (
        "exists rb rc. "
        f"({predecessor_recode_prefix('mb', 'mc', 'rb', 'rc', 'l', tag='predecessor_recode_previous_result')})"
    )
    recode_result = (
        "exists rb rc. "
        f"({predecessor_recode_prefix('mb', 'mc', 'rb', 'rc', 'l', tag='predecessor_recode_result')})"
    )
    recode_last_entry = beta_at(
        "mb", "mc", "l", "m", tag="gmp_predecessor_recode_last_entry"
    )
    recode_last_positive = _strictly_below_term(
        "0",
        "m",
        tag="predecessor_recode_last_positive",
        variables=("mb", "mc", "H", "l", "m"),
    )
    recode_last_bounded = _weakly_below_term(
        "m",
        "H",
        tag="predecessor_recode_last_bounded",
        variables=("mb", "mc", "H", "l", "m"),
    )
    recode_last = (
        f"exists m. ({recode_last_entry}) /\\ "
        f"(({recode_last_positive}) /\\ ({recode_last_bounded}))"
    )
    signed_recode_range = magnitude_range_prefix(
        "mb", "mc", "h", "h", tag="signed_predecessor_recode_range"
    )
    signed_recode_result = (
        "exists rb rc. "
        f"({predecessor_recode_prefix('mb', 'mc', 'rb', 'rc', 'h', tag='signed_predecessor_recode_result')})"
    )

    transport_range = magnitude_range_prefix(
        "mb", "mc", "H", "l", tag="predecessor_transport_range"
    )
    transport_finite_range = magnitude_range_prefix(
        "mb", "mc", "l", "l", tag="predecessor_transport_finite_range"
    )
    transport_recode = predecessor_recode_prefix(
        "mb", "mc", "rb", "rc", "l", tag="predecessor_transport_recode"
    )
    transport_index_bound = _strictly_below_term(
        "i",
        "l",
        tag="predecessor_transport_index_bound",
        variables=("mb", "mc", "rb", "rc", "H", "l", "i", "r"),
    )
    transport_source_entry = _beta_at_term(
        "mb",
        "mc",
        "i",
        "S r",
        tag="predecessor_transport_source_entry",
        variables=("mb", "mc", "rb", "rc", "H", "l", "i", "r"),
    )
    transport_target_entry = beta_at(
        "rb", "rc", "i", "r", tag="gmp_predecessor_transport_target_entry"
    )
    transport_range_entry = (
        "exists m. "
        f"({beta_at('mb', 'mc', 'i', 'm', tag='gmp_predecessor_transport_range_entry')}) /\\ "
        f"(({_strictly_below_term('0', 'm', tag='predecessor_transport_positive', variables=('mb', 'mc', 'rb', 'rc', 'H', 'l', 'i', 'r', 'm'))}) /\\ "
        f"({_weakly_below_term('m', 'H', tag='predecessor_transport_bounded', variables=('mb', 'mc', 'rb', 'rc', 'H', 'l', 'i', 'r', 'm'))}))"
    )
    transport_finite_range_entry = (
        "exists m. "
        f"({beta_at('mb', 'mc', 'i', 'm', tag='gmp_predecessor_transport_finite_range_entry')}) /\\ "
        f"(({_strictly_below_term('0', 'm', tag='predecessor_transport_finite_positive', variables=('mb', 'mc', 'rb', 'rc', 'l', 'i', 'r', 'm'))}) /\\ "
        f"({_weakly_below_term('m', 'l', tag='predecessor_transport_finite_bounded', variables=('mb', 'mc', 'rb', 'rc', 'l', 'i', 'r', 'm'))}))"
    )
    transport_bounded_result = bounded_prefix(
        "rb", "rc", "l", tag="predecessor_transport_bounded_result"
    )
    transport_magnitude_injective = injective_prefix(
        "mb", "mc", "l", tag="predecessor_transport_magnitude_injective"
    )
    transport_target_injective = injective_prefix(
        "rb", "rc", "l", tag="predecessor_transport_target_injective"
    )
    transport_target_surjective = surjective_prefix(
        "rb", "rc", "l", tag="predecessor_transport_target_surjective"
    )

    return (
        spec(
            "gauss_signed_half_magnitude_range",
            "forall p h a b c mb mc sb sc l. "
            f"({signed_prefix}) -> ({magnitude_range})",
            (),
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
                "intro l",
                "intro hprefix",
                "intro i",
                "intro hi",
                f"have hentry : {signed_entry_i}",
                "specialize hprefix i",
                "apply hprefix",
                "exact hi",
                "cases hentry",
                "cases hentry_witness",
                "cases hentry_witness_witness",
                "cases hentry_witness_witness_witness",
                "cases hentry_witness_witness_witness_right",
                "cases hentry_witness_witness_witness_right_right",
                "cases hentry_witness_witness_witness_right_right_right",
                "cases hentry_witness_witness_witness_right_right_right_right",
                "exists x1",
                "split",
                "exact hentry_witness_witness_witness_right_left",
                "split",
                "exact hentry_witness_witness_witness_right_right_right_left",
                "exact hentry_witness_witness_witness_right_right_right_right_left",
            ),
            "Every decoded signed-prefix magnitude lies constructively in 1,...,h.",
        ),
        spec(
            "prime_scaled_same_target_unique",
            "forall p a x y t. "
            f"({prime_p}) -> ({multiplier_nondivisor}) -> "
            f"({x_bound}) -> ({y_bound}) -> ({ax_target}) -> ({ay_target}) -> x = y",
            (
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
                "intro t",
                "intro hp",
                "intro hnotdiv",
                "intro hxbound",
                "intro hybound",
                "intro hxtarget",
                "intro hytarget",
                f"have hreverse : {target_reverse}",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm (a * y)",
                "specialize mod_eq_symm t",
                "apply mod_eq_symm",
                "exact hytarget",
                f"have hscaled : {scaled_xy}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans (a * x)",
                "specialize mod_eq_trans t",
                "specialize mod_eq_trans (a * y)",
                "apply mod_eq_trans",
                "exact hxtarget",
                "exact hreverse",
                f"have hcanceled : {canceled_xy}",
                "specialize prime_mod_cancel p",
                "specialize prime_mod_cancel a",
                "specialize prime_mod_cancel x",
                "specialize prime_mod_cancel y",
                "apply prime_mod_cancel",
                "exact hp",
                "exact hnotdiv",
                "exact hscaled",
                "specialize mod_eq_bounded_unique p",
                "specialize mod_eq_bounded_unique x",
                "specialize mod_eq_bounded_unique y",
                "apply mod_eq_bounded_unique",
                "exact hxbound",
                "exact hybound",
                "exact hcanceled",
            ),
            "A nonzero prime residue multiplier is injective when two bounded sources have one modular target.",
        ),
        spec(
            "gauss_same_sign_scaled_source_unique",
            "forall p h a x y m. "
            f"({prime_p}) -> ({multiplier_nondivisor}) -> "
            f"({x_bound}) -> ({y_bound}) -> ({same_sign_cases}) -> x = y",
            ("prime_scaled_same_target_unique",),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro x",
                "intro y",
                "intro m",
                "intro hp",
                "intro hnotdiv",
                "intro hxbound",
                "intro hybound",
                "intro hsame",
                "cases hsame",
                "cases hsame_left",
                "specialize prime_scaled_same_target_unique p",
                "specialize prime_scaled_same_target_unique a",
                "specialize prime_scaled_same_target_unique x",
                "specialize prime_scaled_same_target_unique y",
                "specialize prime_scaled_same_target_unique m",
                "apply prime_scaled_same_target_unique",
                "exact hp",
                "exact hnotdiv",
                "exact hxbound",
                "exact hybound",
                "exact hsame_left_left",
                "exact hsame_left_right",
                "cases hsame_right",
                "specialize prime_scaled_same_target_unique p",
                "specialize prime_scaled_same_target_unique a",
                "specialize prime_scaled_same_target_unique x",
                "specialize prime_scaled_same_target_unique y",
                f"specialize prime_scaled_same_target_unique {reflected_target}",
                "apply prime_scaled_same_target_unique",
                "exact hp",
                "exact hnotdiv",
                "exact hxbound",
                "exact hybound",
                "exact hsame_right_left",
                "exact hsame_right_right",
            ),
            "Equal lower signs or equal reflected signs force equality of the bounded source residues.",
        ),
        spec(
            "gauss_mixed_sign_scaled_source_impossible",
            "forall p h a x y m. p = 2 * h + 1 -> "
            f"({prime_p}) -> ({multiplier_nondivisor}) -> ({sum_bound}) -> "
            f"~(x + y = 0) -> ({mixed_ax_lower}) -> ({mixed_ay_reflected}) -> false",
            (
                "mod_eq_add",
                "mul_add",
                "mul_succ_left",
                "add_comm",
                "dvd_to_mod_zero",
                "mod_eq_trans",
                "prime_mod_cancel",
                "prime_nonzero",
                "one_le_of_ne_zero",
                "mod_eq_bounded_unique",
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro x",
                "intro y",
                "intro m",
                "intro hpodd",
                "intro hp",
                "intro hnotdiv",
                "intro hsum_bound",
                "intro hsum_nonzero",
                "intro hxlower",
                "intro hyreflected",
                f"have hadd : {added_congruence}",
                "specialize mod_eq_add p",
                "specialize mod_eq_add (a * x)",
                "specialize mod_eq_add m",
                "specialize mod_eq_add (a * y)",
                f"specialize mod_eq_add {reflected_target}",
                "apply mod_eq_add",
                "exact hxlower",
                "exact hyreflected",
                "cases hadd",
                "cases hadd_witness",
                f"have hscaled_multiple : {scaled_sum_multiple}",
                "exists x1",
                "exists x2",
                "trans (a * x + a * y) + p * x1",
                "congr",
                "apply mul_add",
                "refl",
                "trans (m + (2 * h) * m) + p * x2",
                "exact hadd_witness_witness",
                "congr",
                "rewrite hpodd",
                "simp [mul_succ_left, add_comm]",
                "refl",
                f"have hmultiple_zero : {multiple_zero}",
                "specialize dvd_to_mod_zero p",
                "specialize dvd_to_mod_zero (p * m)",
                "apply dvd_to_mod_zero",
                "exists m",
                "refl",
                f"have hscaled_zero : {scaled_sum_zero}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans (a * (x + y))",
                "specialize mod_eq_trans (p * m)",
                "specialize mod_eq_trans 0",
                "apply mod_eq_trans",
                "exact hscaled_multiple",
                "exact hmultiple_zero",
                "cases hscaled_zero",
                "cases hscaled_zero_witness",
                f"have hscaled_factor_zero : {scaled_sum_factor_zero}",
                "exists x3",
                "exists x4",
                "trans 0 + p * x4",
                "exact hscaled_zero_witness_witness",
                "congr",
                "simp",
                "refl",
                f"have hsum_zero_mod : {sum_zero_mod}",
                "specialize prime_mod_cancel p",
                "specialize prime_mod_cancel a",
                "specialize prime_mod_cancel (x + y)",
                "specialize prime_mod_cancel 0",
                "apply prime_mod_cancel",
                "exact hp",
                "exact hnotdiv",
                "exact hscaled_factor_zero",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                f"have hzero_bound : {zero_bound}",
                "specialize one_le_of_ne_zero p",
                "apply one_le_of_ne_zero",
                "exact hp0",
                "have hsum_zero : x + y = 0",
                "specialize mod_eq_bounded_unique p",
                "specialize mod_eq_bounded_unique (x + y)",
                "specialize mod_eq_bounded_unique 0",
                "apply mod_eq_bounded_unique",
                "exact hsum_bound",
                "exact hzero_bound",
                "exact hsum_zero_mod",
                "apply hsum_nonzero",
                "exact hsum_zero",
            ),
            "Opposite signed representatives cannot share one magnitude when their positive source sum is below p.",
        ),
        spec(
            "gauss_signed_half_magnitude_injective",
            "forall p h a b c mb mc sb sc. p = 2 * h + 1 -> "
            f"({prime_p}) -> ({multiplier_nondivisor}) -> "
            f"({injective_half_range}) -> ({injective_signed_prefix}) -> "
            f"({injective_result})",
            (
                "beta_at_unique",
                "beta_half_range_entry_bounds",
                "beta_range_entry_eq",
                "add_succ_left",
                "zero_add",
                "add_le_add_right",
                "add_le_add_left",
                "le_trans",
                "mul_succ_left",
                "mul_zero_left",
                "lt_of_le_of_lt",
                "add_eq_zero_left",
                "add_comm",
                "gauss_same_sign_scaled_source_unique",
                "gauss_mixed_sign_scaled_source_impossible",
                "beta_range_injective",
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
                "intro hpodd",
                "intro hp",
                "intro hnotdiv",
                "intro hrange",
                "intro hprefix",
                "intro i",
                "intro j",
                "intro m",
                "intro hi",
                "intro hj",
                "intro hmi",
                "intro hmj",
                f"have hentryi : {injective_entry_i}",
                "specialize hprefix i",
                "apply hprefix",
                "exact hi",
                "cases hentryi",
                "cases hentryi_witness",
                "cases hentryi_witness_witness",
                "cases hentryi_witness_witness_witness",
                "cases hentryi_witness_witness_witness_right",
                "cases hentryi_witness_witness_witness_right_right",
                "cases hentryi_witness_witness_witness_right_right_right",
                "cases hentryi_witness_witness_witness_right_right_right_right",
                "cases hentryi_witness_witness_witness_right_right_right_right_right",
                f"have hentryj : {injective_entry_j}",
                "specialize hprefix j",
                "apply hprefix",
                "exact hj",
                "cases hentryj",
                "cases hentryj_witness",
                "cases hentryj_witness_witness",
                "cases hentryj_witness_witness_witness",
                "cases hentryj_witness_witness_witness_right",
                "cases hentryj_witness_witness_witness_right_right",
                "cases hentryj_witness_witness_witness_right_right_right",
                "cases hentryj_witness_witness_witness_right_right_right_right",
                "cases hentryj_witness_witness_witness_right_right_right_right_right",
                "have hmagi : m = x1",
                "specialize beta_at_unique mb",
                "specialize beta_at_unique mc",
                "specialize beta_at_unique i",
                "specialize beta_at_unique m",
                "specialize beta_at_unique x1",
                "apply beta_at_unique",
                "exact hmi",
                "exact hentryi_witness_witness_witness_right_left",
                "have hmagj : m = x4",
                "specialize beta_at_unique mb",
                "specialize beta_at_unique mc",
                "specialize beta_at_unique j",
                "specialize beta_at_unique m",
                "specialize beta_at_unique x4",
                "apply beta_at_unique",
                "exact hmj",
                "exact hentryj_witness_witness_witness_right_left",
                "rewrite <- hmagi at hentryi_witness_witness_witness_right_right_right_right_right_right",
                "rewrite <- hmagi at hentryi_witness_witness_witness_right_right_right_right_right_right",
                "rewrite <- hmagj at hentryj_witness_witness_witness_right_right_right_right_right_right",
                "rewrite <- hmagj at hentryj_witness_witness_witness_right_right_right_right_right_right",
                f"have hisigned : {injective_i_signed}",
                "exact hentryi_witness_witness_witness_right_right_right_right_right_right",
                f"have hjsigned : {injective_j_signed}",
                "exact hentryj_witness_witness_witness_right_right_right_right_right_right",
                f"have hxbounds : (~(x = 0) /\\ ({injective_x_bound}))",
                "specialize beta_half_range_entry_bounds p",
                "specialize beta_half_range_entry_bounds h",
                "specialize beta_half_range_entry_bounds b",
                "specialize beta_half_range_entry_bounds c",
                "specialize beta_half_range_entry_bounds i",
                "specialize beta_half_range_entry_bounds x",
                "apply beta_half_range_entry_bounds",
                "exact hpodd",
                "exact hrange",
                "exact hi",
                "exact hentryi_witness_witness_witness_left",
                f"have hybounds : (~(x3 = 0) /\\ ({injective_y_bound}))",
                "specialize beta_half_range_entry_bounds p",
                "specialize beta_half_range_entry_bounds h",
                "specialize beta_half_range_entry_bounds b",
                "specialize beta_half_range_entry_bounds c",
                "specialize beta_half_range_entry_bounds j",
                "specialize beta_half_range_entry_bounds x3",
                "apply beta_half_range_entry_bounds",
                "exact hpodd",
                "exact hrange",
                "exact hj",
                "exact hentryj_witness_witness_witness_left",
                "cases hxbounds",
                "cases hybounds",
                "have hxvalue : x = 1 + i",
                "specialize beta_range_entry_eq b",
                "specialize beta_range_entry_eq c",
                "specialize beta_range_entry_eq 1",
                "specialize beta_range_entry_eq h",
                "specialize beta_range_entry_eq i",
                "specialize beta_range_entry_eq x",
                "apply beta_range_entry_eq",
                "exact hrange",
                "exact hi",
                "exact hentryi_witness_witness_witness_left",
                "have hyvalue : x3 = 1 + j",
                "specialize beta_range_entry_eq b",
                "specialize beta_range_entry_eq c",
                "specialize beta_range_entry_eq 1",
                "specialize beta_range_entry_eq h",
                "specialize beta_range_entry_eq j",
                "specialize beta_range_entry_eq x3",
                "apply beta_range_entry_eq",
                "exact hrange",
                "exact hj",
                "exact hentryj_witness_witness_witness_left",
                "have honei : 1 + i = S i",
                "trans S (0 + i)",
                "specialize add_succ_left 0",
                "specialize add_succ_left i",
                "exact add_succ_left",
                "congr",
                "specialize zero_add i",
                "exact zero_add",
                "have honej : 1 + j = S j",
                "trans S (0 + j)",
                "specialize add_succ_left 0",
                "specialize add_succ_left j",
                "exact add_succ_left",
                "congr",
                "specialize zero_add j",
                "exact zero_add",
                f"have hxle : {injective_x_le_half}",
                "rewrite hxvalue",
                "rewrite honei",
                "exact hi",
                f"have hyle : {injective_y_le_half}",
                "rewrite hyvalue",
                "rewrite honej",
                "exact hj",
                f"have hsum_first : {injective_sum_first}",
                "specialize add_le_add_right x",
                "specialize add_le_add_right h",
                "specialize add_le_add_right x3",
                "apply add_le_add_right",
                "exact hxle",
                f"have hsum_second : {injective_sum_second}",
                "specialize add_le_add_left x3",
                "specialize add_le_add_left h",
                "specialize add_le_add_left h",
                "apply add_le_add_left",
                "exact hyle",
                f"have hsum_le_double : {injective_sum_le_double}",
                "specialize le_trans (x + x3)",
                "specialize le_trans (h + x3)",
                "specialize le_trans (h + h)",
                "apply le_trans",
                "exact hsum_first",
                "exact hsum_second",
                f"have hdouble_below : {injective_double_below}",
                "exists 0",
                "rewrite hpodd",
                "simp [mul_succ_left, mul_zero_left, zero_add, add_succ_left]",
                f"have hsum_bound : {injective_sum_bound}",
                "specialize lt_of_le_of_lt (x + x3)",
                "specialize lt_of_le_of_lt (h + h)",
                "specialize lt_of_le_of_lt p",
                "apply lt_of_le_of_lt",
                "exact hsum_le_double",
                "exact hdouble_below",
                "have hsum_nonzero : ~(x + x3 = 0)",
                "intro hsumzero",
                "apply hxbounds_left",
                "specialize add_eq_zero_left x",
                "specialize add_eq_zero_left x3",
                "apply add_eq_zero_left",
                "exact hsumzero",
                "have hsumcomm : x3 + x = x + x3",
                "specialize add_comm x3",
                "specialize add_comm x",
                "exact add_comm",
                f"have hreverse_sum_bound : {injective_reverse_sum_bound}",
                "rewrite hsumcomm",
                "exact hsum_bound",
                "have hreverse_sum_nonzero : ~(x3 + x = 0)",
                "intro hreversezero",
                "apply hsum_nonzero",
                "trans x3 + x",
                "symm",
                "exact hsumcomm",
                "exact hreversezero",
                "have hsourceeq : x = x3",
                "cases hisigned",
                "cases hisigned_left",
                "cases hjsigned",
                "cases hjsigned_left",
                "specialize gauss_same_sign_scaled_source_unique p",
                "specialize gauss_same_sign_scaled_source_unique h",
                "specialize gauss_same_sign_scaled_source_unique a",
                "specialize gauss_same_sign_scaled_source_unique x",
                "specialize gauss_same_sign_scaled_source_unique x3",
                "specialize gauss_same_sign_scaled_source_unique m",
                "apply gauss_same_sign_scaled_source_unique",
                "exact hp",
                "exact hnotdiv",
                "exact hxbounds_right",
                "exact hybounds_right",
                "left",
                "split",
                "exact hisigned_left_right",
                "exact hjsigned_left_right",
                "cases hjsigned_right",
                "exfalso",
                "specialize gauss_mixed_sign_scaled_source_impossible p",
                "specialize gauss_mixed_sign_scaled_source_impossible h",
                "specialize gauss_mixed_sign_scaled_source_impossible a",
                "specialize gauss_mixed_sign_scaled_source_impossible x",
                "specialize gauss_mixed_sign_scaled_source_impossible x3",
                "specialize gauss_mixed_sign_scaled_source_impossible m",
                "apply gauss_mixed_sign_scaled_source_impossible",
                "exact hpodd",
                "exact hp",
                "exact hnotdiv",
                "exact hsum_bound",
                "exact hsum_nonzero",
                "exact hisigned_left_right",
                "exact hjsigned_right_right",
                "cases hisigned_right",
                "cases hjsigned",
                "cases hjsigned_left",
                "exfalso",
                "specialize gauss_mixed_sign_scaled_source_impossible p",
                "specialize gauss_mixed_sign_scaled_source_impossible h",
                "specialize gauss_mixed_sign_scaled_source_impossible a",
                "specialize gauss_mixed_sign_scaled_source_impossible x3",
                "specialize gauss_mixed_sign_scaled_source_impossible x",
                "specialize gauss_mixed_sign_scaled_source_impossible m",
                "apply gauss_mixed_sign_scaled_source_impossible",
                "exact hpodd",
                "exact hp",
                "exact hnotdiv",
                "exact hreverse_sum_bound",
                "exact hreverse_sum_nonzero",
                "exact hjsigned_left_right",
                "exact hisigned_right_right",
                "cases hjsigned_right",
                "specialize gauss_same_sign_scaled_source_unique p",
                "specialize gauss_same_sign_scaled_source_unique h",
                "specialize gauss_same_sign_scaled_source_unique a",
                "specialize gauss_same_sign_scaled_source_unique x",
                "specialize gauss_same_sign_scaled_source_unique x3",
                "specialize gauss_same_sign_scaled_source_unique m",
                "apply gauss_same_sign_scaled_source_unique",
                "exact hp",
                "exact hnotdiv",
                "exact hxbounds_right",
                "exact hybounds_right",
                "right",
                "split",
                "exact hisigned_right_right",
                "exact hjsigned_right_right",
                "specialize beta_range_injective b",
                "specialize beta_range_injective c",
                "specialize beta_range_injective 1",
                "specialize beta_range_injective h",
                "specialize beta_range_injective i",
                "specialize beta_range_injective j",
                "specialize beta_range_injective x",
                "specialize beta_range_injective x3",
                "apply beta_range_injective",
                "exact hrange",
                "exact hi",
                "exact hj",
                "exact hentryi_witness_witness_witness_left",
                "exact hentryj_witness_witness_witness_left",
                "exact hsourceeq",
            ),
            "The positive signed-half magnitude prefix is injective over the full beta-coded half range.",
        ),
        spec(
            "beta_magnitude_predecessor_recode_exists",
            "forall mb mc H l. "
            f"({recode_range}) -> ({recode_result})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "le_succ",
                "le_refl",
                "ne_zero_of_one_le",
                "nonzero_is_succ",
                "finite_lt_succ_eq_or_lt",
                "beta_at_unique",
                "succ_injective",
                "beta_prefix_extend",
            ),
            (
                "intro mb",
                "intro mc",
                "intro H",
                "induction l",
                "intro hrange",
                "exists 0",
                "exists 0",
                "intro i",
                "intro r",
                "intro hi",
                "intro hsource",
                "exfalso",
                "cases hi",
                "have hsi : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hsi",
                "intro hrange",
                f"have hprevious_range : {recode_previous_range}",
                "intro i",
                "intro hi",
                "specialize hrange i",
                "apply hrange",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                f"have hprevious : {recode_previous_result}",
                "apply IH",
                "exact hprevious_range",
                "cases hprevious",
                "cases hprevious_witness",
                f"have hlast : {recode_last}",
                "specialize hrange l",
                "apply hrange",
                "specialize le_refl (S l)",
                "exact le_refl",
                "cases hlast",
                "cases hlast_witness",
                "cases hlast_witness_right",
                "have hlast0 : ~(x2 = 0)",
                "intro hlastzero",
                "specialize ne_zero_of_one_le x2",
                "apply ne_zero_of_one_le",
                "exact hlast_witness_right_left",
                "exact hlastzero",
                "have hlast_predecessor : exists r. x2 = S r",
                "specialize nonzero_is_succ x2",
                "apply nonzero_is_succ",
                "exact hlast0",
                "cases hlast_predecessor",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend x",
                "specialize beta_prefix_extend x1",
                "specialize beta_prefix_extend x3",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x4",
                "exists x5",
                "intro i",
                "intro r",
                "intro hi",
                "intro hsource",
                "have hsplit : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "have hsource_value : S r = x2",
                "specialize beta_at_unique mb",
                "specialize beta_at_unique mc",
                "specialize beta_at_unique l",
                "specialize beta_at_unique (S r)",
                "specialize beta_at_unique x2",
                "apply beta_at_unique",
                "rewrite hsplit_left at hsource",
                "rewrite hsplit_left at hsource",
                "exact hsource",
                "exact hlast_witness_left",
                "have hrvalue : r = x3",
                "specialize succ_injective r",
                "specialize succ_injective x3",
                "apply succ_injective",
                "trans x2",
                "exact hsource_value",
                "exact hlast_predecessor_witness",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hrvalue",
                "rewrite hrvalue",
                "exact beta_prefix_extend_witness_witness_left",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right r",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "specialize hprevious_witness_witness i",
                "specialize hprevious_witness_witness r",
                "apply hprevious_witness_witness",
                "exact hsplit_right",
                "exact hsource",
            ),
            "Every positive bounded beta prefix can be recoded pointwise by removing one successor from each value.",
        ),
        spec(
            "gauss_signed_half_predecessor_recode_exists",
            "forall p h a b c mb mc sb sc. "
            f"({injective_signed_prefix}) -> ({signed_recode_result})",
            (
                "gauss_signed_half_magnitude_range",
                "beta_magnitude_predecessor_recode_exists",
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
                "intro hprefix",
                f"have hrange : {signed_recode_range}",
                "specialize gauss_signed_half_magnitude_range p",
                "specialize gauss_signed_half_magnitude_range h",
                "specialize gauss_signed_half_magnitude_range a",
                "specialize gauss_signed_half_magnitude_range b",
                "specialize gauss_signed_half_magnitude_range c",
                "specialize gauss_signed_half_magnitude_range mb",
                "specialize gauss_signed_half_magnitude_range mc",
                "specialize gauss_signed_half_magnitude_range sb",
                "specialize gauss_signed_half_magnitude_range sc",
                "specialize gauss_signed_half_magnitude_range h",
                "apply gauss_signed_half_magnitude_range",
                "exact hprefix",
                "specialize beta_magnitude_predecessor_recode_exists mb",
                "specialize beta_magnitude_predecessor_recode_exists mc",
                "specialize beta_magnitude_predecessor_recode_exists h",
                "specialize beta_magnitude_predecessor_recode_exists h",
                "apply beta_magnitude_predecessor_recode_exists",
                "exact hrange",
            ),
            "The signed-half magnitude prefix admits a beta code of its 0,...,h-1 predecessors.",
        ),
        spec(
            "beta_magnitude_predecessor_recode_reflect",
            "forall mb mc rb rc H l i r. "
            f"({transport_range}) -> ({transport_recode}) -> "
            f"({transport_index_bound}) -> ({transport_target_entry}) -> "
            f"({transport_source_entry})",
            (
                "ne_zero_of_one_le",
                "nonzero_is_succ",
                "beta_at_unique",
            ),
            (
                "intro mb",
                "intro mc",
                "intro rb",
                "intro rc",
                "intro H",
                "intro l",
                "intro i",
                "intro r",
                "intro hrange",
                "intro hrecode",
                "intro hi",
                "intro htarget",
                f"have hentry : {transport_range_entry}",
                "specialize hrange i",
                "apply hrange",
                "exact hi",
                "cases hentry",
                "cases hentry_witness",
                "cases hentry_witness_right",
                "have hx0 : ~(x = 0)",
                "intro hxzero",
                "specialize ne_zero_of_one_le x",
                "apply ne_zero_of_one_le",
                "exact hentry_witness_right_left",
                "exact hxzero",
                "have hxpredecessor : exists q. x = S q",
                "specialize nonzero_is_succ x",
                "apply nonzero_is_succ",
                "exact hx0",
                "cases hxpredecessor",
                f"have hsource_predecessor : {_beta_at_term('mb', 'mc', 'i', 'S x1', tag='predecessor_transport_source_predecessor', variables=('mb', 'mc', 'rb', 'rc', 'H', 'l', 'i', 'r', 'x', 'x1'))}",
                "rewrite <- hxpredecessor_witness",
                "rewrite <- hxpredecessor_witness",
                "exact hentry_witness_left",
                f"have htarget_predecessor : {beta_at('rb', 'rc', 'i', 'x1', tag='gmp_predecessor_transport_target_predecessor')}",
                "specialize hrecode i",
                "specialize hrecode x1",
                "apply hrecode",
                "exact hi",
                "exact hsource_predecessor",
                "have hrx : r = x1",
                "specialize beta_at_unique rb",
                "specialize beta_at_unique rc",
                "specialize beta_at_unique i",
                "specialize beta_at_unique r",
                "specialize beta_at_unique x1",
                "apply beta_at_unique",
                "exact htarget",
                "exact htarget_predecessor",
                "have hxsr : x = S r",
                "trans S x1",
                "exact hxpredecessor_witness",
                "congr",
                "symm",
                "exact hrx",
                "rewrite hxsr at hentry_witness_left",
                "rewrite hxsr at hentry_witness_left",
                "exact hentry_witness_left",
            ),
            "Unique target decoding reflects every predecessor-code entry back to its source successor magnitude.",
        ),
        spec(
            "beta_magnitude_predecessor_recode_bounded",
            "forall mb mc rb rc l. "
            f"({transport_finite_range}) -> ({transport_recode}) -> "
            f"({transport_bounded_result})",
            (
                "ne_zero_of_one_le",
                "nonzero_is_succ",
            ),
            (
                "intro mb",
                "intro mc",
                "intro rb",
                "intro rc",
                "intro l",
                "intro hrange",
                "intro hrecode",
                "intro i",
                "intro hi",
                f"have hentry : {transport_finite_range_entry}",
                "specialize hrange i",
                "apply hrange",
                "exact hi",
                "cases hentry",
                "cases hentry_witness",
                "cases hentry_witness_right",
                "have hx0 : ~(x = 0)",
                "intro hxzero",
                "specialize ne_zero_of_one_le x",
                "apply ne_zero_of_one_le",
                "exact hentry_witness_right_left",
                "exact hxzero",
                "have hxpredecessor : exists q. x = S q",
                "specialize nonzero_is_succ x",
                "apply nonzero_is_succ",
                "exact hx0",
                "cases hxpredecessor",
                "exists x1",
                "split",
                "specialize hrecode i",
                "specialize hrecode x1",
                "apply hrecode",
                "exact hi",
                "rewrite <- hxpredecessor_witness",
                "rewrite <- hxpredecessor_witness",
                "exact hentry_witness_left",
                "rewrite hxpredecessor_witness at hentry_witness_right_right",
                "exact hentry_witness_right_right",
            ),
            "Removing one successor turns the positive 1,...,l range bound into the finite 0,...,l-1 bound.",
        ),
        spec(
            "beta_magnitude_predecessor_recode_injective",
            "forall mb mc rb rc l. "
            f"({transport_finite_range}) -> ({transport_magnitude_injective}) -> "
            f"({transport_recode}) -> ({transport_target_injective})",
            ("beta_magnitude_predecessor_recode_reflect",),
            (
                "intro mb",
                "intro mc",
                "intro rb",
                "intro rc",
                "intro l",
                "intro hrange",
                "intro hsource_injective",
                "intro hrecode",
                "intro i",
                "intro j",
                "intro r",
                "intro hi",
                "intro hj",
                "intro htarget_i",
                "intro htarget_j",
                f"have hsource_i : {_beta_at_term('mb', 'mc', 'i', 'S r', tag='predecessor_injective_source_i', variables=('mb', 'mc', 'rb', 'rc', 'l', 'i', 'j', 'r'))}",
                "specialize beta_magnitude_predecessor_recode_reflect mb",
                "specialize beta_magnitude_predecessor_recode_reflect mc",
                "specialize beta_magnitude_predecessor_recode_reflect rb",
                "specialize beta_magnitude_predecessor_recode_reflect rc",
                "specialize beta_magnitude_predecessor_recode_reflect l",
                "specialize beta_magnitude_predecessor_recode_reflect l",
                "specialize beta_magnitude_predecessor_recode_reflect i",
                "specialize beta_magnitude_predecessor_recode_reflect r",
                "apply beta_magnitude_predecessor_recode_reflect",
                "exact hrange",
                "exact hrecode",
                "exact hi",
                "exact htarget_i",
                f"have hsource_j : {_beta_at_term('mb', 'mc', 'j', 'S r', tag='predecessor_injective_source_j', variables=('mb', 'mc', 'rb', 'rc', 'l', 'i', 'j', 'r'))}",
                "specialize beta_magnitude_predecessor_recode_reflect mb",
                "specialize beta_magnitude_predecessor_recode_reflect mc",
                "specialize beta_magnitude_predecessor_recode_reflect rb",
                "specialize beta_magnitude_predecessor_recode_reflect rc",
                "specialize beta_magnitude_predecessor_recode_reflect l",
                "specialize beta_magnitude_predecessor_recode_reflect l",
                "specialize beta_magnitude_predecessor_recode_reflect j",
                "specialize beta_magnitude_predecessor_recode_reflect r",
                "apply beta_magnitude_predecessor_recode_reflect",
                "exact hrange",
                "exact hrecode",
                "exact hj",
                "exact htarget_j",
                "specialize hsource_injective i",
                "specialize hsource_injective j",
                "specialize hsource_injective (S r)",
                "apply hsource_injective",
                "exact hi",
                "exact hj",
                "exact hsource_i",
                "exact hsource_j",
            ),
            "Injectivity of positive magnitudes transports to their uniquely decoded predecessor code.",
        ),
        spec(
            "beta_magnitude_predecessor_recode_surjective",
            "forall mb mc rb rc l. "
            f"({transport_finite_range}) -> ({transport_magnitude_injective}) -> "
            f"({transport_recode}) -> ({transport_target_surjective})",
            (
                "beta_magnitude_predecessor_recode_bounded",
                "beta_magnitude_predecessor_recode_injective",
                "finite_bounded_injective_surjective",
            ),
            (
                "intro mb",
                "intro mc",
                "intro rb",
                "intro rc",
                "intro l",
                "intro hrange",
                "intro hsource_injective",
                "intro hrecode",
                f"have hbounded : {transport_bounded_result}",
                "specialize beta_magnitude_predecessor_recode_bounded mb",
                "specialize beta_magnitude_predecessor_recode_bounded mc",
                "specialize beta_magnitude_predecessor_recode_bounded rb",
                "specialize beta_magnitude_predecessor_recode_bounded rc",
                "specialize beta_magnitude_predecessor_recode_bounded l",
                "apply beta_magnitude_predecessor_recode_bounded",
                "exact hrange",
                "exact hrecode",
                f"have hinjective : {transport_target_injective}",
                "specialize beta_magnitude_predecessor_recode_injective mb",
                "specialize beta_magnitude_predecessor_recode_injective mc",
                "specialize beta_magnitude_predecessor_recode_injective rb",
                "specialize beta_magnitude_predecessor_recode_injective rc",
                "specialize beta_magnitude_predecessor_recode_injective l",
                "apply beta_magnitude_predecessor_recode_injective",
                "exact hrange",
                "exact hsource_injective",
                "exact hrecode",
                "specialize finite_bounded_injective_surjective l",
                "specialize finite_bounded_injective_surjective rb",
                "specialize finite_bounded_injective_surjective rc",
                "apply finite_bounded_injective_surjective",
                "exact hbounded",
                "exact hinjective",
            ),
            "The predecessor code covers every value 0,...,l-1 by constructive finite pigeonhole.",
        ),
    )


__all__ = [
    "magnitude_range_prefix",
    "make_gauss_magnitude_permutation_candidate_theorems",
    "predecessor_recode_prefix",
]
