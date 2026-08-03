"""Static, isolated residue-map recoding candidates for the Fermat route.

Nothing in this module is imported by the public theorem registry.  Every
surface helper expands to the unchanged first-order Peano language, and every
script remains a candidate until a content-addressed WMI discovery replay and
a separate receipt-pinned admission replay both pass.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at


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
    names = tuple(f"frm_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Fermat-map binder captures an argument")
    return names


def strictly_below(left: str, right: str, *, tag: str) -> str:
    """Expand the witness-defined strict order ``left < right``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "lower term"), (right, "upper term"))
    )
    (gap,) = _binders(tag, variables, ("gap",))
    return f"exists {gap}. {gap} + S {left} = {right}"


def at_most(left: str, right: str, *, tag: str) -> str:
    """Expand the witness-defined weak order ``left <= right``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "lower term"), (right, "upper term"))
    )
    (gap,) = _binders(tag, variables, ("weak_gap",))
    return f"exists {gap}. {gap} + {left} = {right}"


def prime(value: str, *, tag: str) -> str:
    """Expand primality through the nonunit factor-pair definition."""

    variable = _identifier(value, "prime candidate")
    left, right = _binders(tag, (variable,), ("prime_left", "prime_right"))
    return (
        f"(~({value} = 1) /\\ forall {left} {right}. "
        f"{value} = {left} * {right} -> {left} = 1 \\/ {right} = 1)"
    )


def not_divides(divisor: str, value: str, *, tag: str) -> str:
    """Expand negated divisibility ``~(divisor | value)``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in ((divisor, "divisor"), (value, "dividend"))
    )
    (factor,) = _binders(tag, variables, ("factor",))
    return f"~(exists {factor}. {value} = {divisor} * {factor})"


def scaled_successor_mod(
    modulus: str,
    multiplier: str,
    index: str,
    residue_predecessor: str,
    *,
    tag: str,
) -> str:
    """Expand ``multiplier*S(index) == S(residue) (mod modulus)``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (modulus, "modulus"),
            (multiplier, "multiplier"),
            (index, "index"),
            (residue_predecessor, "residue predecessor"),
        )
    )
    left_witness, right_witness = _binders(
        tag,
        variables,
        ("mod_left", "mod_right"),
    )
    return (
        f"exists {left_witness} {right_witness}. "
        f"{multiplier} * S {index} + {modulus} * {left_witness} = "
        f"S {residue_predecessor} + {modulus} * {right_witness}"
    )


def index_map_at(
    code: str,
    scale: str,
    index: str,
    bound: str,
    modulus: str,
    multiplier: str,
    *,
    tag: str,
) -> str:
    """Expand one output witness of the zero-based multiplication map."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (code, "map code"),
            (scale, "map scale"),
            (index, "map index"),
            (bound, "residue bound"),
            (modulus, "modulus"),
            (multiplier, "multiplier"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    (residue,) = _binders(safe_tag, variables, ("residue",))
    residue_bound = strictly_below(
        residue,
        bound,
        tag=f"{safe_tag}_residue_bound",
    )
    decoded = beta_at(
        code,
        scale,
        index,
        residue,
        tag=f"frm_{safe_tag}_decoded",
    )
    congruence = scaled_successor_mod(
        modulus,
        multiplier,
        index,
        residue,
        tag=f"{safe_tag}_congruence",
    )
    return f"exists {residue}. ({residue_bound}) /\\ (({decoded}) /\\ ({congruence}))"


def index_map(
    code: str,
    scale: str,
    length: str,
    bound: str,
    modulus: str,
    multiplier: str,
    *,
    tag: str,
) -> str:
    """Expand a finite map of canonical nonzero multiplication residues."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (code, "map code"),
            (scale, "map scale"),
            (length, "map length"),
            (bound, "residue bound"),
            (modulus, "modulus"),
            (multiplier, "multiplier"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    (index,) = _binders(safe_tag, variables, ("index",))
    index_bound = strictly_below(
        index,
        length,
        tag=f"{safe_tag}_index_bound",
    )
    result = index_map_at(
        code,
        scale,
        index,
        bound,
        modulus,
        multiplier,
        tag=f"{safe_tag}_result",
    )
    return f"forall {index}. ({index_bound}) -> ({result})"


def beta_at_successor_value(
    code: str,
    scale: str,
    index: str,
    predecessor: str,
    *,
    tag: str,
) -> str:
    """Expand ``BetaAt(code,scale,index,S predecessor)`` hygienically."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "code"),
            (scale, "scale"),
            (index, "index"),
            (predecessor, "value predecessor"),
        )
    )
    height, quotient = _binders(tag, variables, ("height", "quotient"))
    modulus = f"S ((S ({index})) * {scale})"
    return (
        f"((exists {height}. {height} + S (S {predecessor}) = {modulus}) /\\ "
        f"exists {quotient}. {code} = {quotient} * {modulus} + (S {predecessor}))"
    )


def make_fermat_residue_map_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered residue-map candidate tranche."""

    source_bound = strictly_below("i", "l", tag="successor_lift_bound")
    source_entry = beta_at("r", "s", "i", "j", tag="frm_successor_lift_source")
    target_entry = beta_at_successor_value(
        "z",
        "d",
        "i",
        "j",
        tag="successor_lift_target",
    )
    length_bound = at_most("l", "n", tag="index_map_length")
    prime_p = prime("p", tag="index_map_prime")
    multiplier_nonzero = not_divides("p", "a", tag="index_map_multiplier")
    map_result = index_map("r", "s", "l", "n", "p", "a", tag="result")
    previous_map = index_map("r", "s", "l", "n", "p", "a", tag="previous")
    previous_result_at_i = index_map_at(
        "x",
        "x1",
        "i",
        "n",
        "p",
        "a",
        tag="previous_at_i",
    )

    return (
        spec(
            "beta_successor_lift_exists",
            f"forall r s l. exists z d. forall i j. ({source_bound}) -> "
            f"({source_entry}) -> ({target_entry})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "finite_lt_succ_eq_or_lt",
                "beta_at_exists",
                "beta_at_unique",
                "beta_prefix_extend",
            ),
            (
                "intro r",
                "intro s",
                "induction l",
                "exists 0",
                "exists 0",
                "intro i",
                "intro j",
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
                "cases IH",
                "cases IH_witness",
                "specialize beta_at_exists r",
                "specialize beta_at_exists s",
                "specialize beta_at_exists l",
                "cases beta_at_exists",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend x",
                "specialize beta_prefix_extend x1",
                "specialize beta_prefix_extend (S x2)",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x3",
                "exists x4",
                "intro i",
                "intro j",
                "intro hi",
                "intro hsource",
                "have hsplit : i = l \\/ exists h. h + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "have hjx : j = x2",
                "specialize beta_at_unique r",
                "specialize beta_at_unique s",
                "specialize beta_at_unique l",
                "specialize beta_at_unique j",
                "specialize beta_at_unique x2",
                "apply beta_at_unique",
                "rewrite hsplit_left at hsource",
                "rewrite hsplit_left at hsource",
                "exact hsource",
                "exact beta_at_exists_witness",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hjx",
                "rewrite hjx",
                "exact beta_prefix_extend_witness_witness_left",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right (S j)",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "specialize IH_witness_witness i",
                "specialize IH_witness_witness j",
                "apply IH_witness_witness",
                "exact hsplit_right",
                "exact hsource",
            ),
            "Every decoded finite prefix can be recoded after successor-lifting its values.",
        ),
        spec(
            "prime_mul_index_map_exists_up_to",
            f"forall l n p a. ({length_bound}) -> p = S n -> ({prime_p}) -> "
            f"({multiplier_nonzero}) -> exists r s. ({map_result})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "lt_to_le",
                "succ_le_succ",
                "prime_nonzero",
                "division_remainder_exists",
                "euclid_prime_dvd_product",
                "divisor_le_nonzero",
                "lt_not_le",
                "nonzero_is_succ",
                "le_of_succ_le_succ",
                "mul_comm",
                "remainder_decomposition_to_mod_eq",
                "finite_lt_succ_eq_or_lt",
                "beta_prefix_extend",
            ),
            (
                "induction l",
                "intro n",
                "intro p",
                "intro a",
                "intro hln",
                "intro hpn",
                "intro hp",
                "intro hnotdiv",
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
                "intro n",
                "intro p",
                "intro a",
                "intro hln",
                "intro hpn",
                "intro hp",
                "intro hnotdiv",
                "have hln_prev : exists h. h + l = n",
                "specialize lt_to_le l",
                "specialize lt_to_le n",
                "apply lt_to_le",
                "exact hln",
                f"have hprev : exists r s. ({previous_map})",
                "specialize IH n",
                "specialize IH p",
                "specialize IH a",
                "apply IH",
                "exact hln_prev",
                "exact hpn",
                "exact hp",
                "exact hnotdiv",
                "cases hprev",
                "cases hprev_witness",
                "have hslp : exists h. h + S (S l) = p",
                "rewrite hpn",
                "specialize succ_le_succ (S l)",
                "specialize succ_le_succ n",
                "apply succ_le_succ",
                "exact hln",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                "have hdiv : exists q rem. a * S l = p * q + rem /\\ "
                "exists h. h + S rem = p",
                "specialize division_remainder_exists p",
                "specialize division_remainder_exists (a * S l)",
                "apply division_remainder_exists",
                "exact hp0",
                "cases hdiv",
                "cases hdiv_witness",
                "cases hdiv_witness_witness",
                "have hrem0 : ~(x3 = 0)",
                "intro hremzero",
                "have hmultiple : exists k. a * S l = p * k",
                "exists x2",
                "trans p * x2 + x3",
                "exact hdiv_witness_witness_left",
                "rewrite hremzero",
                "apply PA3",
                "have hfactor : (exists u. a = p * u) \\/ "
                "exists v. S l = p * v",
                "specialize euclid_prime_dvd_product p",
                "specialize euclid_prime_dvd_product a",
                "specialize euclid_prime_dvd_product (S l)",
                "apply euclid_prime_dvd_product",
                "exact hp",
                "exact hmultiple",
                "cases hfactor",
                "apply hnotdiv",
                "exact hfactor_left",
                "have hsl0 : ~(S l = 0)",
                "specialize succ_ne_zero l",
                "exact succ_ne_zero",
                "have hple : exists k. k + p = S l",
                "specialize divisor_le_nonzero p",
                "specialize divisor_le_nonzero (S l)",
                "apply divisor_le_nonzero",
                "exact hsl0",
                "exact hfactor_right",
                "specialize lt_not_le (S l)",
                "specialize lt_not_le p",
                "apply lt_not_le",
                "exact hslp",
                "exact hple",
                "have hrem_succ : exists j. x3 = S j",
                "specialize nonzero_is_succ x3",
                "apply nonzero_is_succ",
                "exact hrem0",
                "cases hrem_succ",
                "have hjn : exists h. h + S x4 = n",
                "specialize le_of_succ_le_succ (S x4)",
                "specialize le_of_succ_le_succ n",
                "apply le_of_succ_le_succ",
                "rewrite <- hrem_succ_witness",
                "rewrite <- hpn",
                "exact hdiv_witness_witness_right",
                "have hdecomp : a * S l = x2 * p + x3",
                "trans p * x2 + x3",
                "exact hdiv_witness_witness_left",
                "congr",
                "apply mul_comm",
                "refl",
                "have hmodrem : exists u v. a * S l + p * u = "
                "x3 + p * v",
                "specialize remainder_decomposition_to_mod_eq p",
                "specialize remainder_decomposition_to_mod_eq (a * S l)",
                "specialize remainder_decomposition_to_mod_eq x2",
                "specialize remainder_decomposition_to_mod_eq x3",
                "apply remainder_decomposition_to_mod_eq",
                "exact hdecomp",
                "have hmod : exists u v. a * S l + p * u = "
                "S x4 + p * v",
                "rewrite <- hrem_succ_witness",
                "exact hmodrem",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend x",
                "specialize beta_prefix_extend x1",
                "specialize beta_prefix_extend x4",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x5",
                "exists x6",
                "intro i",
                "intro hi",
                "have hsplit : i = l \\/ exists h. h + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "exists x4",
                "split",
                "exact hjn",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact beta_prefix_extend_witness_witness_left",
                "rewrite hsplit_left",
                "exact hmod",
                f"have hold : ({previous_result_at_i})",
                "specialize hprev_witness_witness i",
                "apply hprev_witness_witness",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "cases hold_witness_right",
                "exists x7",
                "split",
                "exact hold_witness_left",
                "split",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right x7",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_witness_right_left",
                "exact hold_witness_right_right",
            ),
            "Canonical nonzero products modulo a prime form a beta-coded index map.",
        ),
    )


__all__ = [
    "at_most",
    "beta_at_successor_value",
    "index_map",
    "index_map_at",
    "make_fermat_residue_map_candidate_theorems",
    "not_divides",
    "prime",
    "scaled_successor_mod",
    "strictly_below",
]
