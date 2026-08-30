"""Isolated beta-coded signed-half prefix candidates for Gauss's lemma.

This module is an untrusted authoring layer.  It packages the already authored
pointwise signed-half representative into two beta prefixes: one prefix stores
positive magnitudes at most ``h`` and the other stores a zero/one reflection
bit.  Nothing here is imported by the public theorem registry.  The scripts
remain candidates until a content-addressed WMI replay checks their closed
certificates from the empty kernel context.

All helpers expand immediately to the unchanged first-order language of Peano
arithmetic.  In particular, there is no list, function, subtraction, quotient,
remainder, sign, or congruence primitive in the kernel-facing contracts.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import all_bits, beta_at, bit_count


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
    names = tuple(f"gsp_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated signed-prefix binder captures an argument")
    return names


def _strictly_below_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, variables, ("lt_gap",))
    return f"exists {gap}. {gap} + S {left} = {right}"


def _weakly_below_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, variables, ("le_gap",))
    return f"exists {gap}. {gap} + {left} = {right}"


def _balanced_mod_term(
    modulus: str,
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    mod_left, mod_right = _binders(
        tag,
        variables,
        ("mod_left", "mod_right"),
    )
    return (
        f"exists {mod_left} {mod_right}. ({left}) + {modulus} * {mod_left} = "
        f"({right}) + {modulus} * {mod_right}"
    )


def _beta_at_term(
    code: str,
    scale: str,
    index_term: str,
    value_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    height, quotient = _binders(tag, variables, ("beta_height", "beta_quotient"))
    modulus = f"S ((S ({index_term})) * {scale})"
    return (
        f"((exists {height}. {height} + S ({value_term}) = {modulus}) /\\ "
        f"exists {quotient}. {code} = {quotient} * {modulus} + ({value_term}))"
    )


def prime(value: str, *, tag: str) -> str:
    """Expand primality through the native nonunit factor-pair definition."""

    variable = _identifier(value, "prime candidate")
    left, right = _binders(tag, (variable,), ("prime_left", "prime_right"))
    return (
        f"(~({value} = 1) /\\ forall {left} {right}. "
        f"{value} = {left} * {right} -> {left} = 1 \\/ {right} = 1)"
    )


def not_divides(divisor: str, value: str, *, tag: str) -> str:
    """Expand negated divisibility without introducing a relation symbol."""

    variables = tuple(
        _identifier(item, label)
        for item, label in ((divisor, "divisor"), (value, "dividend"))
    )
    (factor,) = _binders(tag, variables, ("divisor_factor",))
    return f"~(exists {factor}. {value} = {divisor} * {factor})"


def half_range(code: str, scale: str, half: str, *, tag: str) -> str:
    """Expand the beta prefix ``1, 2, ..., half``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (code, "half-range code"),
            (scale, "half-range scale"),
            (half, "half-range length"),
        )
    )
    (index,) = _binders(tag, variables, ("range_index",))
    owned = variables + (index,)
    bound = _strictly_below_term(
        index,
        half,
        tag=f"{tag}_range_bound",
        variables=owned,
    )
    entry = _beta_at_term(
        code,
        scale,
        index,
        f"1 + {index}",
        tag=f"{tag}_range_entry",
        variables=owned,
    )
    return f"forall {index}. ({bound}) -> ({entry})"


def _choice_term(
    modulus: str,
    half: str,
    multiplier: str,
    source_code: str,
    source_scale: str,
    index: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    value, magnitude, sign = _binders(
        tag,
        variables,
        ("value", "magnitude", "sign"),
    )
    owned = variables + (value, magnitude, sign)
    source_entry = beta_at(
        source_code,
        source_scale,
        index,
        value,
        tag=f"gsp_{tag}_source",
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
    lower = _balanced_mod_term(
        modulus,
        f"{multiplier} * {value}",
        magnitude,
        tag=f"{tag}_lower",
        variables=owned,
    )
    reflected = _balanced_mod_term(
        modulus,
        f"{multiplier} * {value}",
        f"(2 * {half}) * {magnitude}",
        tag=f"{tag}_reflected",
        variables=owned,
    )
    signed = (
        f"(({sign} = 0 /\\ ({lower})) \\/ "
        f"({sign} = 1 /\\ ({reflected})))"
    )
    return (
        f"exists {value} {magnitude} {sign}. ({source_entry}) /\\ "
        f"(({positive}) /\\ (({bounded}) /\\ "
        f"(({sign} = 0 \\/ {sign} = 1) /\\ ({signed}))))"
    )


def signed_half_choice(
    modulus: str,
    half: str,
    multiplier: str,
    source_code: str,
    source_scale: str,
    index: str,
    *,
    tag: str,
) -> str:
    """Expand one source entry's magnitude and explicit zero/one sign choice."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (half, "half bound"),
            (multiplier, "multiplier"),
            (source_code, "source code"),
            (source_scale, "source scale"),
            (index, "source index"),
        )
    )
    return _choice_term(
        modulus,
        half,
        multiplier,
        source_code,
        source_scale,
        index,
        tag=tag,
        variables=variables,
    )


def _entry_term(
    modulus: str,
    half: str,
    multiplier: str,
    source_code: str,
    source_scale: str,
    magnitude_code: str,
    magnitude_scale: str,
    sign_code: str,
    sign_scale: str,
    index: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    value, magnitude, sign = _binders(
        tag,
        variables,
        ("value", "magnitude", "sign"),
    )
    owned = variables + (value, magnitude, sign)
    source_entry = beta_at(
        source_code,
        source_scale,
        index,
        value,
        tag=f"gsp_{tag}_source",
    )
    magnitude_entry = beta_at(
        magnitude_code,
        magnitude_scale,
        index,
        magnitude,
        tag=f"gsp_{tag}_magnitude",
    )
    sign_entry = beta_at(
        sign_code,
        sign_scale,
        index,
        sign,
        tag=f"gsp_{tag}_sign",
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
    lower = _balanced_mod_term(
        modulus,
        f"{multiplier} * {value}",
        magnitude,
        tag=f"{tag}_lower",
        variables=owned,
    )
    reflected = _balanced_mod_term(
        modulus,
        f"{multiplier} * {value}",
        f"(2 * {half}) * {magnitude}",
        tag=f"{tag}_reflected",
        variables=owned,
    )
    signed = (
        f"(({sign} = 0 /\\ ({lower})) \\/ "
        f"({sign} = 1 /\\ ({reflected})))"
    )
    return (
        f"exists {value} {magnitude} {sign}. "
        f"({source_entry}) /\\ (({magnitude_entry}) /\\ (({sign_entry}) /\\ "
        f"(({positive}) /\\ (({bounded}) /\\ "
        f"(({sign} = 0 \\/ {sign} = 1) /\\ ({signed}))))))"
    )


def _prefix_term(
    modulus: str,
    half: str,
    multiplier: str,
    source_code: str,
    source_scale: str,
    magnitude_code: str,
    magnitude_scale: str,
    sign_code: str,
    sign_scale: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (index,) = _binders(tag, variables, ("index",))
    owned = variables + (index,)
    bound = _strictly_below_term(
        index,
        length_term,
        tag=f"{tag}_index_bound",
        variables=owned,
    )
    entry = _entry_term(
        modulus,
        half,
        multiplier,
        source_code,
        source_scale,
        magnitude_code,
        magnitude_scale,
        sign_code,
        sign_scale,
        index,
        tag=f"{tag}_entry",
        variables=owned,
    )
    return f"forall {index}. ({bound}) -> ({entry})"


def signed_half_prefix(
    modulus: str,
    half: str,
    multiplier: str,
    source_code: str,
    source_scale: str,
    magnitude_code: str,
    magnitude_scale: str,
    sign_code: str,
    sign_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand aligned source, magnitude, and sign prefixes of a given length."""

    labelled = (
        (modulus, "modulus"),
        (half, "half bound"),
        (multiplier, "multiplier"),
        (source_code, "source code"),
        (source_scale, "source scale"),
        (magnitude_code, "magnitude code"),
        (magnitude_scale, "magnitude scale"),
        (sign_code, "sign code"),
        (sign_scale, "sign scale"),
        (length, "prefix length"),
    )
    variables = tuple(_identifier(value, label) for value, label in labelled)
    return _prefix_term(
        modulus,
        half,
        multiplier,
        source_code,
        source_scale,
        magnitude_code,
        magnitude_scale,
        sign_code,
        sign_scale,
        length,
        tag=tag,
        variables=variables,
    )


def signed_half_successor_prefix(
    modulus: str,
    half: str,
    multiplier: str,
    source_code: str,
    source_scale: str,
    magnitude_code: str,
    magnitude_scale: str,
    sign_code: str,
    sign_scale: str,
    predecessor: str,
    *,
    tag: str,
) -> str:
    """Expand ``SignedHalfPrefix(..., S predecessor)`` hygienically."""

    labelled = (
        (modulus, "modulus"),
        (half, "half bound"),
        (multiplier, "multiplier"),
        (source_code, "source code"),
        (source_scale, "source scale"),
        (magnitude_code, "magnitude code"),
        (magnitude_scale, "magnitude scale"),
        (sign_code, "sign code"),
        (sign_scale, "sign scale"),
        (predecessor, "prefix predecessor"),
    )
    variables = tuple(_identifier(value, label) for value, label in labelled)
    return _prefix_term(
        modulus,
        half,
        multiplier,
        source_code,
        source_scale,
        magnitude_code,
        magnitude_scale,
        sign_code,
        sign_scale,
        f"S {predecessor}",
        tag=tag,
        variables=variables,
    )


def signed_half_choices(
    modulus: str,
    half: str,
    multiplier: str,
    source_code: str,
    source_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand bounded pointwise signed choices before beta recoding."""

    labelled = (
        (modulus, "modulus"),
        (half, "half bound"),
        (multiplier, "multiplier"),
        (source_code, "source code"),
        (source_scale, "source scale"),
        (length, "choice length"),
    )
    variables = tuple(_identifier(value, label) for value, label in labelled)
    (index,) = _binders(tag, variables, ("choice_index",))
    owned = variables + (index,)
    bound = _strictly_below_term(
        index,
        length,
        tag=f"{tag}_choice_bound",
        variables=owned,
    )
    choice = _choice_term(
        modulus,
        half,
        multiplier,
        source_code,
        source_scale,
        index,
        tag=f"{tag}_choice",
        variables=owned,
    )
    return f"forall {index}. ({bound}) -> ({choice})"


def _beta_extension(
    old_code: str,
    old_scale: str,
    length: str,
    value: str,
    *,
    tag: str,
) -> str:
    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (old_code, "old code"),
            (old_scale, "old scale"),
            (length, "extension length"),
            (value, "appended value"),
        )
    )
    new_code, new_scale, index, old_value = _binders(
        tag,
        variables,
        ("new_code", "new_scale", "old_index", "old_value"),
    )
    owned = variables + (new_code, new_scale, index, old_value)
    new_last = beta_at(
        new_code,
        new_scale,
        length,
        value,
        tag=f"gsp_{tag}_new_last",
    )
    old_bound = _strictly_below_term(
        index,
        length,
        tag=f"{tag}_old_bound",
        variables=owned,
    )
    old_entry = beta_at(
        old_code,
        old_scale,
        index,
        old_value,
        tag=f"gsp_{tag}_old_entry",
    )
    new_entry = beta_at(
        new_code,
        new_scale,
        index,
        old_value,
        tag=f"gsp_{tag}_new_entry",
    )
    return (
        f"exists {new_code} {new_scale}. ({new_last}) /\\ "
        f"forall {index} {old_value}. ({old_bound}) -> "
        f"({old_entry}) -> ({new_entry})"
    )


def make_gauss_signed_prefix_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered signed-prefix candidate ladder."""

    point_source = beta_at("b", "c", "i", "x", tag="gsp_point_source")
    point_remainder_bound = _strictly_below_term(
        "r",
        "p",
        tag="point_remainder_bound",
        variables=("p", "h", "a", "b", "c", "i", "x", "q", "r"),
    )
    point_positive = _strictly_below_term(
        "0",
        "m",
        tag="point_result_positive",
        variables=("p", "h", "a", "x", "q", "r", "m"),
    )
    point_bounded = _weakly_below_term(
        "m",
        "h",
        tag="point_result_bounded",
        variables=("p", "h", "a", "x", "q", "r", "m"),
    )
    point_lower = _balanced_mod_term(
        "p",
        "a * x",
        "m",
        tag="point_result_lower",
        variables=("p", "h", "a", "x", "q", "r", "m"),
    )
    point_reflected = _balanced_mod_term(
        "p",
        "a * x",
        "(2 * h) * m",
        tag="point_result_reflected",
        variables=("p", "h", "a", "x", "q", "r", "m"),
    )
    point_representative = (
        f"exists m. ({point_positive}) /\\ (({point_bounded}) /\\ "
        f"(({point_lower}) \\/ ({point_reflected})))"
    )
    point_choice = signed_half_choice(
        "p", "h", "a", "b", "c", "i", tag="point_result"
    )

    half_prime = prime("p", tag="half_range_prime")
    half_multiplier_nondivisor = not_divides(
        "p", "a", tag="half_range_multiplier"
    )
    half_source = half_range("b", "c", "h", tag="half_range_source")
    half_source_entry_i = _beta_at_term(
        "b",
        "c",
        "i",
        "1 + i",
        tag="half_range_source_entry_i",
        variables=("p", "h", "a", "b", "c", "i"),
    )
    half_value_bound = (
        "exists gsp_half_value_bound_gap. "
        "gsp_half_value_bound_gap + S (1 + i) = p"
    )
    half_value_bounds = f"(~(1 + i = 0) /\\ ({half_value_bound}))"
    half_choices = signed_half_choices(
        "p", "h", "a", "b", "c", "h", tag="half_range_choices"
    )

    prefix_before = signed_half_prefix(
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
        tag="extend_before",
    )
    extend_choice = signed_half_choice(
        "p", "h", "a", "b", "c", "l", tag="extend_choice"
    )
    prefix_after = signed_half_successor_prefix(
        "p",
        "h",
        "a",
        "b",
        "c",
        "z",
        "d",
        "u",
        "v",
        "l",
        tag="extend_after",
    )
    magnitude_extension = _beta_extension(
        "mb", "mc", "l", "x1", tag="magnitude_extension"
    )
    sign_extension = _beta_extension(
        "sb", "sc", "l", "x2", tag="sign_extension"
    )
    previous_entry_at_i = _entry_term(
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
        tag="extend_previous_entry",
        variables=("p", "h", "a", "b", "c", "mb", "mc", "sb", "sc", "l", "i"),
    )

    choices_all = signed_half_choices(
        "p", "h", "a", "b", "c", "l", tag="exists_all"
    )
    choices_previous = signed_half_choices(
        "p", "h", "a", "b", "c", "l", tag="exists_previous"
    )
    previous_result = (
        "exists mb mc sb sc. "
        f"({signed_half_prefix('p', 'h', 'a', 'b', 'c', 'mb', 'mc', 'sb', 'sc', 'l', tag='exists_previous_result')})"
    )
    last_choice = signed_half_choice(
        "p", "h", "a", "b", "c", "l", tag="exists_last_choice"
    )
    next_result = (
        "exists mb mc sb sc. "
        f"({signed_half_successor_prefix('p', 'h', 'a', 'b', 'c', 'mb', 'mc', 'sb', 'sc', 'l', tag='exists_next_result')})"
    )
    encoded_result = (
        "exists mb mc sb sc. "
        f"({signed_half_prefix('p', 'h', 'a', 'b', 'c', 'mb', 'mc', 'sb', 'sc', 'l', tag='exists_result')})"
    )
    full_encoded_result = (
        "exists mb mc sb sc. "
        f"({signed_half_prefix('p', 'h', 'a', 'b', 'c', 'mb', 'mc', 'sb', 'sc', 'h', tag='full_half_range_result')})"
    )

    bits_prefix = signed_half_prefix(
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
        tag="bits_source",
    )
    signs_are_bits = all_bits("sb", "sc", "l", tag="gsp_signs")
    bits_entry_at_i = _entry_term(
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
        tag="bits_entry",
        variables=("p", "h", "a", "b", "c", "mb", "mc", "sb", "sc", "l", "i"),
    )
    counted_prefix = signed_half_prefix(
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
        tag="count_source",
    )
    counted_bits = all_bits("sb", "sc", "l", tag="gsp_count_bits")
    count_result = bit_count("sb", "sc", "l", "n", tag="gsp_count_result")

    return (
        spec(
            "gauss_pointwise_signed_half_choice",
            "forall p h a b c i x q r. p = 2 * h + 1 -> "
            f"({point_source}) -> a * x = q * p + r -> "
            f"({point_remainder_bound}) -> ~(r = 0) -> ({point_choice})",
            ("gauss_pointwise_signed_half_representative",),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro b",
                "intro c",
                "intro i",
                "intro x",
                "intro q",
                "intro r",
                "intro hp",
                "intro hsource",
                "intro hdecomp",
                "intro hrp",
                "intro hr0",
                f"have hrepresentative : {point_representative}",
                "specialize gauss_pointwise_signed_half_representative p",
                "specialize gauss_pointwise_signed_half_representative h",
                "specialize gauss_pointwise_signed_half_representative a",
                "specialize gauss_pointwise_signed_half_representative x",
                "specialize gauss_pointwise_signed_half_representative q",
                "specialize gauss_pointwise_signed_half_representative r",
                "apply gauss_pointwise_signed_half_representative",
                "exact hp",
                "exact hdecomp",
                "exact hrp",
                "exact hr0",
                "cases hrepresentative",
                "cases hrepresentative_witness",
                "cases hrepresentative_witness_right",
                "cases hrepresentative_witness_right_right",
                "exists x",
                "exists x1",
                "exists 0",
                "split",
                "exact hsource",
                "split",
                "exact hrepresentative_witness_left",
                "split",
                "exact hrepresentative_witness_right_left",
                "split",
                "left",
                "refl",
                "left",
                "split",
                "refl",
                "exact hrepresentative_witness_right_right_left",
                "exists x",
                "exists x1",
                "exists 1",
                "split",
                "exact hsource",
                "split",
                "exact hrepresentative_witness_left",
                "split",
                "exact hrepresentative_witness_right_left",
                "split",
                "right",
                "refl",
                "right",
                "split",
                "refl",
                "exact hrepresentative_witness_right_right_right",
            ),
            "A canonical nonzero remainder yields one explicit zero/one signed-half choice at its decoded source index.",
        ),
        spec(
            "gauss_half_range_signed_choices",
            "forall p h a b c. p = 2 * h + 1 -> "
            f"({half_prime}) -> ({half_multiplier_nondivisor}) -> "
            f"({half_source}) -> ({half_choices})",
            (
                "prime_nonzero",
                "division_remainder_exists",
                "beta_half_range_entry_bounds",
                "euclid_prime_dvd_product",
                "divisor_le_nonzero",
                "lt_not_le",
                "mul_comm",
                "gauss_pointwise_signed_half_choice",
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro b",
                "intro c",
                "intro hp",
                "intro hprime",
                "intro hnotdiv",
                "intro hrange",
                "intro i",
                "intro hi",
                f"have hsource : {half_source_entry_i}",
                "specialize hrange i",
                "apply hrange",
                "exact hi",
                f"have hbounds : {half_value_bounds}",
                "specialize beta_half_range_entry_bounds p",
                "specialize beta_half_range_entry_bounds h",
                "specialize beta_half_range_entry_bounds b",
                "specialize beta_half_range_entry_bounds c",
                "specialize beta_half_range_entry_bounds i",
                "specialize beta_half_range_entry_bounds (1 + i)",
                "apply beta_half_range_entry_bounds",
                "exact hp",
                "exact hrange",
                "exact hi",
                "exact hsource",
                "cases hbounds",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hprime",
                "exact hpzero",
                "have hdiv : exists q r. a * (1 + i) = p * q + r /\\ "
                f"({half_value_bound.replace('1 + i', 'r')})",
                "specialize division_remainder_exists p",
                "specialize division_remainder_exists (a * (1 + i))",
                "apply division_remainder_exists",
                "exact hp0",
                "cases hdiv",
                "cases hdiv_witness",
                "cases hdiv_witness_witness",
                "have hrem0 : ~(x1 = 0)",
                "intro hremzero",
                "have hmultiple : exists k. a * (1 + i) = p * k",
                "exists x",
                "trans p * x + x1",
                "exact hdiv_witness_witness_left",
                "rewrite hremzero",
                "apply PA3",
                "have hfactor : (exists u. a = p * u) \/ "
                "exists v. 1 + i = p * v",
                "specialize euclid_prime_dvd_product p",
                "specialize euclid_prime_dvd_product a",
                "specialize euclid_prime_dvd_product (1 + i)",
                "apply euclid_prime_dvd_product",
                "exact hprime",
                "exact hmultiple",
                "cases hfactor",
                "apply hnotdiv",
                "exact hfactor_left",
                "have hple : exists k. k + p = 1 + i",
                "specialize divisor_le_nonzero p",
                "specialize divisor_le_nonzero (1 + i)",
                "apply divisor_le_nonzero",
                "exact hbounds_left",
                "exact hfactor_right",
                "specialize lt_not_le (1 + i)",
                "specialize lt_not_le p",
                "apply lt_not_le",
                "exact hbounds_right",
                "exact hple",
                "have hdecomp : a * (1 + i) = x * p + x1",
                "trans p * x + x1",
                "exact hdiv_witness_witness_left",
                "congr",
                "apply mul_comm",
                "refl",
                "specialize gauss_pointwise_signed_half_choice p",
                "specialize gauss_pointwise_signed_half_choice h",
                "specialize gauss_pointwise_signed_half_choice a",
                "specialize gauss_pointwise_signed_half_choice b",
                "specialize gauss_pointwise_signed_half_choice c",
                "specialize gauss_pointwise_signed_half_choice i",
                "specialize gauss_pointwise_signed_half_choice (1 + i)",
                "specialize gauss_pointwise_signed_half_choice x",
                "specialize gauss_pointwise_signed_half_choice x1",
                "apply gauss_pointwise_signed_half_choice",
                "exact hp",
                "exact hsource",
                "exact hdecomp",
                "exact hdiv_witness_witness_right",
                "exact hrem0",
            ),
            "A prime odd half-range and a nondivisible multiplier provide a signed choice at every decoded entry.",
        ),
        spec(
            "gauss_signed_half_prefix_extend",
            "forall p h a b c mb mc sb sc l. "
            f"({prefix_before}) -> ({extend_choice}) -> "
            f"exists z d u v. ({prefix_after})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
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
                "intro hchoice",
                "cases hchoice",
                "cases hchoice_witness",
                "cases hchoice_witness_witness",
                "cases hchoice_witness_witness_witness",
                "cases hchoice_witness_witness_witness_right",
                "cases hchoice_witness_witness_witness_right_right",
                "cases hchoice_witness_witness_witness_right_right_right",
                f"have hmag_extend : {magnitude_extension}",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend mb",
                "specialize beta_prefix_extend mc",
                "specialize beta_prefix_extend x1",
                "exact beta_prefix_extend",
                "cases hmag_extend",
                "cases hmag_extend_witness",
                "cases hmag_extend_witness_witness",
                f"have hsign_extend : {sign_extension}",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend sb",
                "specialize beta_prefix_extend sc",
                "specialize beta_prefix_extend x2",
                "exact beta_prefix_extend",
                "cases hsign_extend",
                "cases hsign_extend_witness",
                "cases hsign_extend_witness_witness",
                "exists x3",
                "exists x4",
                "exists x5",
                "exists x6",
                "intro i",
                "intro hi",
                "have hsplit : i = l \/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hchoice_witness_witness_witness_left",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hmag_extend_witness_witness_left",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hsign_extend_witness_witness_left",
                "split",
                "exact hchoice_witness_witness_witness_right_left",
                "split",
                "exact hchoice_witness_witness_witness_right_right_left",
                "split",
                "exact hchoice_witness_witness_witness_right_right_right_left",
                "exact hchoice_witness_witness_witness_right_right_right_right",
                f"have hold : {previous_entry_at_i}",
                "specialize hprefix i",
                "apply hprefix",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "cases hold_witness_witness",
                "cases hold_witness_witness_witness",
                "cases hold_witness_witness_witness_right",
                "cases hold_witness_witness_witness_right_right",
                "cases hold_witness_witness_witness_right_right_right",
                "cases hold_witness_witness_witness_right_right_right_right",
                "cases hold_witness_witness_witness_right_right_right_right_right",
                "exists x7",
                "exists x8",
                "exists x9",
                "split",
                "exact hold_witness_witness_witness_left",
                "split",
                "specialize hmag_extend_witness_witness_right i",
                "specialize hmag_extend_witness_witness_right x8",
                "apply hmag_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_witness_witness_right_left",
                "split",
                "specialize hsign_extend_witness_witness_right i",
                "specialize hsign_extend_witness_witness_right x9",
                "apply hsign_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_witness_witness_right_right_left",
                "split",
                "exact hold_witness_witness_witness_right_right_right_left",
                "split",
                "exact hold_witness_witness_witness_right_right_right_right_left",
                "split",
                "exact hold_witness_witness_witness_right_right_right_right_right_left",
                "exact hold_witness_witness_witness_right_right_right_right_right_right",
            ),
            "Append one pointwise signed choice simultaneously to the magnitude and zero/one sign beta prefixes.",
        ),
        spec(
            "gauss_signed_half_prefix_exists",
            "forall p h a b c l. "
            f"({choices_all}) -> ({encoded_result})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "le_succ",
                "le_refl",
                "gauss_signed_half_prefix_extend",
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro b",
                "intro c",
                "induction l",
                "intro hchoices",
                "exists 0",
                "exists 0",
                "exists 0",
                "exists 0",
                "intro i",
                "intro hi",
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
                "intro hchoices",
                f"have hprevious_choices : {choices_previous}",
                "intro i",
                "intro hi",
                "specialize hchoices i",
                "apply hchoices",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                f"have hprevious : {previous_result}",
                "apply IH",
                "exact hprevious_choices",
                "cases hprevious",
                "cases hprevious_witness",
                "cases hprevious_witness_witness",
                "cases hprevious_witness_witness_witness",
                f"have hlast : {last_choice}",
                "specialize hchoices l",
                "apply hchoices",
                "specialize le_refl (S l)",
                "exact le_refl",
                f"have hnext : {next_result}",
                "specialize gauss_signed_half_prefix_extend p",
                "specialize gauss_signed_half_prefix_extend h",
                "specialize gauss_signed_half_prefix_extend a",
                "specialize gauss_signed_half_prefix_extend b",
                "specialize gauss_signed_half_prefix_extend c",
                "specialize gauss_signed_half_prefix_extend x",
                "specialize gauss_signed_half_prefix_extend x1",
                "specialize gauss_signed_half_prefix_extend x2",
                "specialize gauss_signed_half_prefix_extend x3",
                "specialize gauss_signed_half_prefix_extend l",
                "apply gauss_signed_half_prefix_extend",
                "exact hprevious_witness_witness_witness_witness",
                "exact hlast",
                "exact hnext",
            ),
            "Every bounded family of pointwise signed choices admits aligned beta-coded magnitude and sign prefixes.",
        ),
        spec(
            "gauss_half_range_signed_prefix_exists",
            "forall p h a b c. p = 2 * h + 1 -> "
            f"({half_prime}) -> ({half_multiplier_nondivisor}) -> "
            f"({half_source}) -> ({full_encoded_result})",
            (
                "gauss_half_range_signed_choices",
                "gauss_signed_half_prefix_exists",
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro b",
                "intro c",
                "intro hp",
                "intro hprime",
                "intro hnotdiv",
                "intro hrange",
                f"have hchoices : {half_choices}",
                "specialize gauss_half_range_signed_choices p",
                "specialize gauss_half_range_signed_choices h",
                "specialize gauss_half_range_signed_choices a",
                "specialize gauss_half_range_signed_choices b",
                "specialize gauss_half_range_signed_choices c",
                "apply gauss_half_range_signed_choices",
                "exact hp",
                "exact hprime",
                "exact hnotdiv",
                "exact hrange",
                "specialize gauss_signed_half_prefix_exists p",
                "specialize gauss_signed_half_prefix_exists h",
                "specialize gauss_signed_half_prefix_exists a",
                "specialize gauss_signed_half_prefix_exists b",
                "specialize gauss_signed_half_prefix_exists c",
                "specialize gauss_signed_half_prefix_exists h",
                "apply gauss_signed_half_prefix_exists",
                "exact hchoices",
            ),
            "The full prime odd half-range has beta-coded positive magnitudes and explicit reflection bits.",
        ),
        spec(
            "gauss_signed_half_prefix_all_bits",
            "forall p h a b c mb mc sb sc l. "
            f"({bits_prefix}) -> ({signs_are_bits})",
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
                f"have hentry : {bits_entry_at_i}",
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
                "cases hentry_witness_witness_witness_right_right_right_right_right",
                "exists x2",
                "split",
                "exact hentry_witness_witness_witness_right_right_left",
                "exact hentry_witness_witness_witness_right_right_right_right_right_left",
            ),
            "The sign projection of every encoded signed-half prefix is an AllBits prefix.",
        ),
        spec(
            "gauss_signed_half_bit_count_exists",
            "forall p h a b c mb mc sb sc l. "
            f"({counted_prefix}) -> exists n. ({count_result})",
            ("gauss_signed_half_prefix_all_bits", "bit_count_exists"),
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
                f"have hbits : {counted_bits}",
                "specialize gauss_signed_half_prefix_all_bits p",
                "specialize gauss_signed_half_prefix_all_bits h",
                "specialize gauss_signed_half_prefix_all_bits a",
                "specialize gauss_signed_half_prefix_all_bits b",
                "specialize gauss_signed_half_prefix_all_bits c",
                "specialize gauss_signed_half_prefix_all_bits mb",
                "specialize gauss_signed_half_prefix_all_bits mc",
                "specialize gauss_signed_half_prefix_all_bits sb",
                "specialize gauss_signed_half_prefix_all_bits sc",
                "specialize gauss_signed_half_prefix_all_bits l",
                "apply gauss_signed_half_prefix_all_bits",
                "exact hprefix",
                "specialize bit_count_exists sb",
                "specialize bit_count_exists sc",
                "specialize bit_count_exists l",
                "apply bit_count_exists",
                "exact hbits",
            ),
            "The encoded reflection bits have a native relational count of their ones.",
        ),
    )


__all__ = [
    "half_range",
    "make_gauss_signed_prefix_candidate_theorems",
    "not_divides",
    "prime",
    "signed_half_choice",
    "signed_half_choices",
    "signed_half_prefix",
    "signed_half_successor_prefix",
]
