"""Constructive binary-exponentiation prerequisites and bounded concrete traces.

Every named formal relation below expands into the existing first-order
Heyting-arithmetic language.  In particular powers are the already checked
beta-coded relational ``Pow`` graph, residues use balanced natural
congruence, and binary steps are actual square/optional-multiply operations.

The exact grand-campaign goal G102 is deliberately *not* claimed here: its
unbounded beta-coded execution trace, formal ``BitLen`` totality, and formal
logarithmic step bound remain outstanding.  The executable certificates are
useful auditable examples, not formal proof or release-admission authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import factorial
from typing import Any, Callable

from .finite_fold_surface import _binders, _identifier, _variables, power_relation
from .power_algebra_theorems import _power_terms


BINARY_MODULUS_NONTRIVIAL_NONZERO = "binary_modulus_nontrivial_nonzero"
BINARY_CANONICAL_RESIDUE_EXISTS = "binary_canonical_residue_exists"
BINARY_CANONICAL_RESIDUE_FUNCTIONAL = "binary_canonical_residue_functional"
BINARY_CANONICAL_RESIDUE_EXISTS_UNIQUE = "binary_canonical_residue_exists_unique"
BINARY_EXPONENT_SPLIT_EXISTS = "binary_exponent_split_exists"
BINARY_EXPONENT_DOUBLED_POWER = "binary_exponent_doubled_power"
BINARY_EXPONENT_ODD_POWER = "binary_exponent_odd_power"
BINARY_MODULAR_SQUARE_CONGRUENCE = "binary_modular_square_congruence"
BINARY_MODULAR_MULTIPLY_CONGRUENCE = "binary_modular_multiply_congruence"
BINARY_MODULAR_SQUARE_RESIDUE_EXISTS = "binary_modular_square_residue_exists"
BINARY_MODULAR_MULTIPLY_RESIDUE_EXISTS = "binary_modular_multiply_residue_exists"
BINARY_MODULAR_STEP_EXISTS = "binary_modular_step_exists"
BINARY_MODULAR_STEP_FUNCTIONAL = "binary_modular_step_functional"
BINARY_MODULAR_EXPONENTIATION_RESULT_EXISTS = (
    "binary_modular_exponentiation_result_exists"
)
BINARY_MODULAR_EXPONENTIATION_RESULT_FUNCTIONAL = (
    "binary_modular_exponentiation_result_functional"
)
BINARY_MODULAR_EXPONENTIATION_RESULT_EXISTS_UNIQUE = (
    "binary_modular_exponentiation_result_exists_unique"
)

MAX_BINARY_BASE_BITS = 16_384
MAX_BINARY_EXPONENT_BITS = 4_096
MAX_BINARY_MODULUS_BITS = 4_096
MAX_BINARY_BETA_TRACE_ENTRIES = 128
MAX_BINARY_BETA_ENTRY_BITS = 256
MAX_BINARY_BETA_CODE_BITS = 65_536


class BinaryModularExponentiationError(ValueError):
    """A conservative relation or bounded concrete binary certificate failed."""


def _context(*labelled: tuple[str, str]) -> tuple[str, ...]:
    try:
        return tuple(dict.fromkeys(_variables(*labelled)))
    except ValueError as error:
        raise BinaryModularExponentiationError(str(error)) from error


def _safe_tag(tag: str) -> str:
    try:
        return _identifier(tag, "binary exponentiation binder tag")
    except ValueError as error:
        raise BinaryModularExponentiationError(str(error)) from error


def _congruence_terms(
    modulus: str,
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand balanced congruence for audited module-owned compound terms."""

    try:
        first, second = _binders(
            f"binary_{_safe_tag(tag)}", variables, ("left", "right")
        )
    except ValueError as error:
        raise BinaryModularExponentiationError(str(error)) from error
    return (
        f"exists {first} {second}. ({left}) + {modulus} * {first} = "
        f"({right}) + {modulus} * {second}"
    )


def _canonical_terms(
    modulus: str,
    value: str,
    residue: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    try:
        (gap,) = _binders(f"binary_{_safe_tag(tag)}", variables, ("gap",))
    except ValueError as error:
        raise BinaryModularExponentiationError(str(error)) from error
    congruence = _congruence_terms(
        modulus,
        value,
        residue,
        tag=f"{tag}_congruence",
        variables=variables,
    )
    return f"((exists {gap}. {gap} + S ({residue}) = {modulus}) /\\ ({congruence}))"


def binary_modulus_relation(modulus: str, *, tag: str) -> str:
    """Expand the exact constructive guard ``1 < modulus`` hygienically."""

    variables = _context((modulus, "binary exponentiation modulus"))
    try:
        (gap,) = _binders(
            f"binary_{_safe_tag(tag)}", variables, ("modulus_gap",)
        )
    except ValueError as error:
        raise BinaryModularExponentiationError(str(error)) from error
    return f"exists {gap}. {gap} + S 1 = {modulus}"


def binary_exponent_split(
    exponent: str,
    half: str,
    bit: str,
    *,
    tag: str,
) -> str:
    """Expand the exact natural binary decomposition ``e=2*half+bit``."""

    variables = _context(
        (exponent, "binary exponent"),
        (half, "binary quotient"),
        (bit, "binary digit"),
    )
    try:
        _binders(f"binary_{_safe_tag(tag)}", variables, ())
    except ValueError as error:
        raise BinaryModularExponentiationError(str(error)) from error
    return f"((({bit} = 0) \\/ ({bit} = 1)) /\\ {exponent} = ({half} + {half}) + {bit})"


def canonical_modular_residue(
    modulus: str,
    value: str,
    residue: str,
    *,
    tag: str,
) -> str:
    """Expand ``residue<modulus`` and actual balanced congruence to ``value``."""

    variables = _context(
        (modulus, "canonical modulus"),
        (value, "unreduced natural value"),
        (residue, "canonical natural residue"),
    )
    return _canonical_terms(modulus, value, residue, tag=tag, variables=variables)


def binary_doubled_power(
    base: str,
    half: str,
    even_exponent: str,
    half_value: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand the exact even-power prerequisite ``a^(2h)=(a^h)^2``."""

    _context(
        (base, "power base"),
        (half, "halved exponent"),
        (even_exponent, "doubled exponent"),
        (half_value, "halved power value"),
        (result, "doubled power value"),
    )
    safe_tag = _safe_tag(tag)
    lower = power_relation(base, half, half_value, tag=f"binary_{safe_tag}_half")
    full = power_relation(
        base, even_exponent, result, tag=f"binary_{safe_tag}_full"
    )
    return f"(({even_exponent} = {half} + {half}) /\\ (({lower}) /\\ ({full})))"


def binary_odd_power(
    base: str,
    half: str,
    odd_exponent: str,
    half_value: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand the exact odd-power prerequisite ``a^(2h+1)=(a^h)^2*a``."""

    _context(
        (base, "power base"),
        (half, "halved exponent"),
        (odd_exponent, "odd exponent"),
        (half_value, "halved power value"),
        (result, "odd power value"),
    )
    safe_tag = _safe_tag(tag)
    lower = power_relation(base, half, half_value, tag=f"binary_{safe_tag}_half")
    full = power_relation(
        base, odd_exponent, result, tag=f"binary_{safe_tag}_full"
    )
    return f"(({odd_exponent} = S ({half} + {half})) /\\ (({lower}) /\\ ({full})))"


def binary_modular_step(
    modulus: str,
    input_value: str,
    base: str,
    bit: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand one exact MSB-first modular square/optional-multiply step."""

    variables = _context(
        (modulus, "binary-step modulus"),
        (input_value, "binary-step accumulator"),
        (base, "binary-step base"),
        (bit, "binary-step digit"),
        (result, "binary-step reduced result"),
    )
    safe_tag = _safe_tag(tag)
    squared = _canonical_terms(
        modulus,
        f"{input_value} * {input_value}",
        result,
        tag=f"{safe_tag}_square",
        variables=variables,
    )
    multiplied = _canonical_terms(
        modulus,
        f"({input_value} * {input_value}) * {base}",
        result,
        tag=f"{safe_tag}_multiply",
        variables=variables,
    )
    return f"((({bit} = 0) /\\ ({squared})) \\/ (({bit} = 1) /\\ ({multiplied})))"


def binary_modular_power(
    base: str,
    exponent: str,
    modulus: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand an exact canonical residue of the existing beta-coded power."""

    variables = _context(
        (base, "modular power base"),
        (exponent, "modular power exponent"),
        (modulus, "modular power modulus"),
        (result, "modular power residue"),
    )
    safe_tag = _safe_tag(tag)
    try:
        (power,) = _binders(f"binary_{safe_tag}", variables, ("power",))
    except ValueError as error:
        raise BinaryModularExponentiationError(str(error)) from error
    full_power = power_relation(
        base, exponent, power, tag=f"binary_{safe_tag}_value"
    )
    reduced = _canonical_terms(
        modulus,
        power,
        result,
        tag=f"{safe_tag}_residue",
        variables=(*variables, power),
    )
    return f"exists {power}. (({full_power}) /\\ ({reduced}))"


def make_binary_modular_exponentiation_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the genuine dependency-curried G102 prerequisite layer."""

    modulus = binary_modulus_relation("m", tag="guard")
    residue = canonical_modular_residue("m", "n", "r", tag="value")
    other_residue = canonical_modular_residue("m", "n", "s", tag="other")
    split = binary_exponent_split("e", "h", "b", tag="split")
    doubled = binary_doubled_power("a", "h", "e", "x", "y", tag="double")
    odd = binary_odd_power("a", "h", "e", "x", "z", tag="odd")
    half_power = power_relation("a", "h", "x", tag="binary_half")
    double_power = power_relation("a", "d", "y", tag="binary_double")
    odd_power = power_relation("a", "e", "z", tag="binary_odd")
    square_source = _congruence_terms(
        "m", "x", "r", tag="square_source", variables=("m", "x", "r")
    )
    square_result = _congruence_terms(
        "m", "x * x", "r * r", tag="square_result", variables=("m", "x", "r")
    )
    multiply_left = _congruence_terms(
        "m", "x", "r", tag="multiply_left", variables=("m", "x", "r", "y", "s")
    )
    multiply_right = _congruence_terms(
        "m", "y", "s", tag="multiply_right", variables=("m", "x", "r", "y", "s")
    )
    multiply_result = _congruence_terms(
        "m", "x * y", "r * s", tag="multiply_result", variables=("m", "x", "r", "y", "s")
    )
    squared_residue = _canonical_terms(
        "m", "x * x", "r", tag="squared", variables=("m", "x", "r")
    )
    product_residue = _canonical_terms(
        "m", "x * y", "r", tag="product", variables=("m", "x", "y", "r")
    )
    step = binary_modular_step("m", "x", "a", "b", "r", tag="step")
    other_step = binary_modular_step("m", "x", "a", "b", "s", tag="step_other")
    power_result = binary_modular_power("a", "e", "m", "r", tag="result")
    other_power_result = binary_modular_power("a", "e", "m", "s", tag="other")

    return (
        spec(
            BINARY_MODULUS_NONTRIVIAL_NONZERO,
            f"forall m. ({modulus}) -> ~(m = 0)",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro m", "intro hmodulus", "intro hzero", "cases hmodulus",
                "rewrite hzero at hmodulus_witness",
                "have hsuccessor : S 1 = 0",
                "specialize add_eq_zero_right x", "specialize add_eq_zero_right (S 1)",
                "apply add_eq_zero_right", "exact hmodulus_witness",
                "specialize succ_ne_zero 1", "apply succ_ne_zero", "exact hsuccessor",
            ),
            "Every explicitly guarded modulus m>1 is constructively nonzero.",
        ),
        spec(
            BINARY_CANONICAL_RESIDUE_EXISTS,
            f"forall m n. ({modulus}) -> exists r. ({residue})",
            (
                BINARY_MODULUS_NONTRIVIAL_NONZERO,
                "division_remainder_exists",
                "mul_comm",
                "remainder_decomposition_to_mod_eq",
            ),
            (
                "intro m", "intro n", "intro hmodulus",
                "have hnonzero : ~(m = 0)", "intro hzero",
                f"specialize {BINARY_MODULUS_NONTRIVIAL_NONZERO} m",
                f"apply {BINARY_MODULUS_NONTRIVIAL_NONZERO}", "exact hmodulus",
                "exact hzero",
                "have hdivision : exists q r. n = m * q + r /\\ exists gap. gap + S r = m",
                "specialize division_remainder_exists m",
                "specialize division_remainder_exists n",
                "apply division_remainder_exists", "exact hnonzero",
                "cases hdivision", "cases hdivision_witness",
                "cases hdivision_witness_witness",
                "have hdecomposition : n = x * m + x1",
                "trans m * x + x1", "exact hdivision_witness_witness_left",
                "congr", "apply mul_comm", "refl",
                "exists x1", "split", "exact hdivision_witness_witness_right",
                "specialize remainder_decomposition_to_mod_eq m",
                "specialize remainder_decomposition_to_mod_eq n",
                "specialize remainder_decomposition_to_mod_eq x",
                "specialize remainder_decomposition_to_mod_eq x1",
                "apply remainder_decomposition_to_mod_eq", "exact hdecomposition",
            ),
            "Every value has a witnessed canonical residue below every modulus m>1.",
        ),
        spec(
            BINARY_CANONICAL_RESIDUE_FUNCTIONAL,
            f"forall m n r s. ({residue}) -> ({other_residue}) -> r = s",
            ("mod_eq_symm", "mod_eq_trans", "mod_eq_bounded_unique"),
            (
                "intro m", "intro n", "intro r", "intro s",
                "intro hr", "intro hs", "cases hr", "cases hs",
                f"have hreverse : {_congruence_terms('m', 'r', 'n', tag='functional_reverse', variables=('m','n','r','s'))}",
                "specialize mod_eq_symm m", "specialize mod_eq_symm n",
                "specialize mod_eq_symm r", "apply mod_eq_symm", "exact hr_right",
                f"have hrelated : {_congruence_terms('m', 'r', 's', tag='functional_related', variables=('m','n','r','s'))}",
                "specialize mod_eq_trans m", "specialize mod_eq_trans r",
                "specialize mod_eq_trans n", "specialize mod_eq_trans s",
                "apply mod_eq_trans", "exact hreverse", "exact hs_right",
                "specialize mod_eq_bounded_unique m",
                "specialize mod_eq_bounded_unique r",
                "specialize mod_eq_bounded_unique s",
                "apply mod_eq_bounded_unique", "exact hr_left", "exact hs_left",
                "exact hrelated",
            ),
            "Two canonical residues of the same natural and modulus are equal.",
        ),
        spec(
            BINARY_CANONICAL_RESIDUE_EXISTS_UNIQUE,
            f"forall m n. ({modulus}) -> exists r. (({residue}) /\\ forall s. ({other_residue}) -> r = s)",
            (BINARY_CANONICAL_RESIDUE_EXISTS, BINARY_CANONICAL_RESIDUE_FUNCTIONAL),
            (
                "intro m", "intro n", "intro hmodulus",
                f"specialize {BINARY_CANONICAL_RESIDUE_EXISTS} m",
                f"specialize {BINARY_CANONICAL_RESIDUE_EXISTS} n",
                f"have hexists : exists r. ({residue})",
                f"apply {BINARY_CANONICAL_RESIDUE_EXISTS}", "exact hmodulus",
                "cases hexists", "exists x", "split", "exact hexists_witness",
                "intro s", "intro hs",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} m",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} n",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} x",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} s",
                f"apply {BINARY_CANONICAL_RESIDUE_FUNCTIONAL}",
                "exact hexists_witness", "exact hs",
            ),
            "Each guarded modulus admits exactly one actual bounded residue.",
        ),
        spec(
            BINARY_EXPONENT_SPLIT_EXISTS,
            f"forall e. exists h b. ({split})",
            ("parity_cases", "two_mul_eq_add_self"),
            (
                "intro e", "specialize parity_cases e", "cases parity_cases",
                "cases parity_cases_witness",
                "exists x", "exists 0", "split", "left", "refl",
                "trans 2 * x", "exact parity_cases_witness_left",
                "trans x + x", "apply two_mul_eq_add_self",
                "simp",
                "exists x", "exists 1", "split", "right", "refl",
                "trans 2 * x + 1", "exact parity_cases_witness_right",
                "congr", "apply two_mul_eq_add_self", "refl",
            ),
            "Every exponent has an exact half and a witnessed zero-or-one binary digit.",
        ),
        spec(
            BINARY_EXPONENT_DOUBLED_POWER,
            f"forall a h e x y. ({doubled}) -> y = x * x",
            ("pow_add",),
            (
                "intro a", "intro h", "intro e", "intro x", "intro y",
                "intro hdouble", "cases hdouble", "cases hdouble_right",
                "specialize pow_add a", "specialize pow_add h", "specialize pow_add h",
                "specialize pow_add e", "specialize pow_add x", "specialize pow_add x",
                "specialize pow_add y", "apply pow_add", "exact hdouble_left",
                "exact hdouble_right_left", "exact hdouble_right_left",
                "exact hdouble_right_right",
            ),
            "The relational power at an even exponent is the square of its half power.",
        ),
        spec(
            BINARY_EXPONENT_ODD_POWER,
            f"forall a h e x z. ({odd}) -> z = (x * x) * a",
            ("pow_exists", BINARY_EXPONENT_DOUBLED_POWER, "pow_successor_pair_mul"),
            (
                "intro a", "intro h", "intro e", "intro x", "intro z",
                "intro hodd", "cases hodd", "cases hodd_right",
                f"have hdouble : exists y. ({_power_terms('a', 'h + h', 'y', tag='binary_odd_double')})",
                "specialize pow_exists a", "specialize pow_exists (h + h)",
                "exact pow_exists", "cases hdouble",
                "have hsquare : x1 = x * x",
                f"specialize {BINARY_EXPONENT_DOUBLED_POWER} a",
                f"specialize {BINARY_EXPONENT_DOUBLED_POWER} h",
                f"specialize {BINARY_EXPONENT_DOUBLED_POWER} (h + h)",
                f"specialize {BINARY_EXPONENT_DOUBLED_POWER} x",
                f"specialize {BINARY_EXPONENT_DOUBLED_POWER} x1",
                f"apply {BINARY_EXPONENT_DOUBLED_POWER}", "split", "refl",
                "split", "exact hodd_right_left", "exact hdouble_witness",
                "have hsuccessor : z = x1 * a",
                "specialize pow_successor_pair_mul a",
                "specialize pow_successor_pair_mul (h + h)",
                "specialize pow_successor_pair_mul e",
                "specialize pow_successor_pair_mul x1",
                "specialize pow_successor_pair_mul z",
                "apply pow_successor_pair_mul", "exact hodd_left",
                "exact hdouble_witness", "exact hodd_right_right",
                "trans x1 * a", "exact hsuccessor", "congr", "exact hsquare", "refl",
            ),
            "The relational power at an odd exponent is its squared half power times the base.",
        ),
        spec(
            BINARY_MODULAR_SQUARE_CONGRUENCE,
            f"forall m x r. ({square_source}) -> ({square_result})",
            ("mod_eq_mul",),
            (
                "intro m", "intro x", "intro r", "intro hcongruence",
                "specialize mod_eq_mul m", "specialize mod_eq_mul x",
                "specialize mod_eq_mul r", "specialize mod_eq_mul x",
                "specialize mod_eq_mul r", "apply mod_eq_mul",
                "exact hcongruence", "exact hcongruence",
            ),
            "Squaring preserves witnessed balanced natural congruence.",
        ),
        spec(
            BINARY_MODULAR_MULTIPLY_CONGRUENCE,
            f"forall m x r y s. ({multiply_left}) -> ({multiply_right}) -> ({multiply_result})",
            ("mod_eq_mul",),
            (
                "intro m", "intro x", "intro r", "intro y", "intro s",
                "intro hleft", "intro hright", "specialize mod_eq_mul m",
                "specialize mod_eq_mul x", "specialize mod_eq_mul r",
                "specialize mod_eq_mul y", "specialize mod_eq_mul s",
                "apply mod_eq_mul", "exact hleft", "exact hright",
            ),
            "Multiplication preserves both witnessed modular factors.",
        ),
        spec(
            BINARY_MODULAR_SQUARE_RESIDUE_EXISTS,
            f"forall m x. ({modulus}) -> exists r. ({squared_residue})",
            (BINARY_CANONICAL_RESIDUE_EXISTS,),
            (
                "intro m", "intro x", "intro hmodulus",
                f"specialize {BINARY_CANONICAL_RESIDUE_EXISTS} m",
                f"specialize {BINARY_CANONICAL_RESIDUE_EXISTS} (x * x)",
                f"apply {BINARY_CANONICAL_RESIDUE_EXISTS}", "exact hmodulus",
            ),
            "Every squaring step has an actual canonical modular residue.",
        ),
        spec(
            BINARY_MODULAR_MULTIPLY_RESIDUE_EXISTS,
            f"forall m x y. ({modulus}) -> exists r. ({product_residue})",
            (BINARY_CANONICAL_RESIDUE_EXISTS,),
            (
                "intro m", "intro x", "intro y", "intro hmodulus",
                f"specialize {BINARY_CANONICAL_RESIDUE_EXISTS} m",
                f"specialize {BINARY_CANONICAL_RESIDUE_EXISTS} (x * y)",
                f"apply {BINARY_CANONICAL_RESIDUE_EXISTS}", "exact hmodulus",
            ),
            "Every multiplication step has an actual canonical modular residue.",
        ),
        spec(
            BINARY_MODULAR_STEP_EXISTS,
            f"forall m x a b. ({modulus}) -> (b = 0 \\/ b = 1) -> exists r. ({step})",
            (BINARY_CANONICAL_RESIDUE_EXISTS,),
            (
                "intro m", "intro x", "intro a", "intro b", "intro hmodulus",
                "intro hbit", "cases hbit",
                f"have hsquare : exists r. ({_canonical_terms('m','x * x','r',tag='step_square_witness',variables=('m','x','a','b','r'))})",
                f"specialize {BINARY_CANONICAL_RESIDUE_EXISTS} m",
                f"specialize {BINARY_CANONICAL_RESIDUE_EXISTS} (x * x)",
                f"apply {BINARY_CANONICAL_RESIDUE_EXISTS}", "exact hmodulus",
                "cases hsquare", "exists x1", "left", "split", "exact hbit_left",
                "exact hsquare_witness",
                f"have hproduct : exists r. ({_canonical_terms('m','(x * x) * a','r',tag='step_product_witness',variables=('m','x','a','b','r'))})",
                f"specialize {BINARY_CANONICAL_RESIDUE_EXISTS} m",
                f"specialize {BINARY_CANONICAL_RESIDUE_EXISTS} ((x * x) * a)",
                f"apply {BINARY_CANONICAL_RESIDUE_EXISTS}", "exact hmodulus",
                "cases hproduct", "exists x1", "right", "split", "exact hbit_right",
                "exact hproduct_witness",
            ),
            "Every guarded square-and-optional-multiply binary transition has a canonical result.",
        ),
        spec(
            BINARY_MODULAR_STEP_FUNCTIONAL,
            f"forall m x a b r s. ({step}) -> ({other_step}) -> r = s",
            (BINARY_CANONICAL_RESIDUE_FUNCTIONAL,),
            (
                "intro m", "intro x", "intro a", "intro b", "intro r", "intro s",
                "intro hr", "intro hs", "cases hr", "cases hr_left", "cases hs",
                "cases hs_left",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} m",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} (x * x)",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} r",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} s",
                f"apply {BINARY_CANONICAL_RESIDUE_FUNCTIONAL}",
                "exact hr_left_right", "exact hs_left_right",
                "cases hs_right", "rewrite hr_left_left at hs_right_left",
                "exfalso", "apply PA1", "symm", "exact hs_right_left",
                "cases hr_right", "cases hs", "cases hs_left",
                "rewrite hs_left_left at hr_right_left", "exfalso", "apply PA1",
                "symm", "exact hr_right_left",
                "cases hs_right",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} m",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} ((x * x) * a)",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} r",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} s",
                f"apply {BINARY_CANONICAL_RESIDUE_FUNCTIONAL}",
                "exact hr_right_right", "exact hs_right_right",
            ),
            "A fixed binary digit and state determine exactly one modular transition result.",
        ),
        spec(
            BINARY_MODULAR_EXPONENTIATION_RESULT_EXISTS,
            f"forall a e m. ({modulus}) -> exists r. ({power_result})",
            ("pow_exists", BINARY_CANONICAL_RESIDUE_EXISTS),
            (
                "intro a", "intro e", "intro m", "intro hmodulus",
                "specialize pow_exists a", "specialize pow_exists e",
                "cases pow_exists",
                f"have hresidue : exists r. ({canonical_modular_residue('m','x','r',tag='power_exists')})",
                f"specialize {BINARY_CANONICAL_RESIDUE_EXISTS} m",
                f"specialize {BINARY_CANONICAL_RESIDUE_EXISTS} x",
                f"apply {BINARY_CANONICAL_RESIDUE_EXISTS}", "exact hmodulus",
                "cases hresidue", "exists x1", "exists x", "split",
                "exact pow_exists_witness", "exact hresidue_witness",
            ),
            "Every a,e and every modulus m>1 have an exact bounded residue of the relational power a^e.",
        ),
        spec(
            BINARY_MODULAR_EXPONENTIATION_RESULT_FUNCTIONAL,
            f"forall a e m r s. ({power_result}) -> ({other_power_result}) -> r = s",
            ("pow_functional", BINARY_CANONICAL_RESIDUE_FUNCTIONAL),
            (
                "intro a", "intro e", "intro m", "intro r", "intro s",
                "intro hr", "intro hs", "cases hr", "cases hr_witness",
                "cases hs", "cases hs_witness",
                "have hpower : x = x1", "specialize pow_functional a",
                "specialize pow_functional e", "specialize pow_functional x",
                "specialize pow_functional x1", "apply pow_functional",
                "exact hr_witness_left", "exact hs_witness_left",
                "rewrite <- hpower at hs_witness_right",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} m",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} x",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} r",
                f"specialize {BINARY_CANONICAL_RESIDUE_FUNCTIONAL} s",
                f"apply {BINARY_CANONICAL_RESIDUE_FUNCTIONAL}",
                "exact hr_witness_right", "exact hs_witness_right",
            ),
            "Any two exact bounded residues of the same relational power are equal.",
        ),
        spec(
            BINARY_MODULAR_EXPONENTIATION_RESULT_EXISTS_UNIQUE,
            f"forall a e m. ({modulus}) -> exists r. (({power_result}) /\\ forall s. ({other_power_result}) -> r = s)",
            (
                BINARY_MODULAR_EXPONENTIATION_RESULT_EXISTS,
                BINARY_MODULAR_EXPONENTIATION_RESULT_FUNCTIONAL,
            ),
            (
                "intro a", "intro e", "intro m", "intro hmodulus",
                f"specialize {BINARY_MODULAR_EXPONENTIATION_RESULT_EXISTS} a",
                f"specialize {BINARY_MODULAR_EXPONENTIATION_RESULT_EXISTS} e",
                f"specialize {BINARY_MODULAR_EXPONENTIATION_RESULT_EXISTS} m",
                f"have hresult : exists r. ({power_result})",
                f"apply {BINARY_MODULAR_EXPONENTIATION_RESULT_EXISTS}", "exact hmodulus",
                "cases hresult", "exists x", "split", "exact hresult_witness",
                "intro s", "intro hs",
                f"specialize {BINARY_MODULAR_EXPONENTIATION_RESULT_FUNCTIONAL} a",
                f"specialize {BINARY_MODULAR_EXPONENTIATION_RESULT_FUNCTIONAL} e",
                f"specialize {BINARY_MODULAR_EXPONENTIATION_RESULT_FUNCTIONAL} m",
                f"specialize {BINARY_MODULAR_EXPONENTIATION_RESULT_FUNCTIONAL} x",
                f"specialize {BINARY_MODULAR_EXPONENTIATION_RESULT_FUNCTIONAL} s",
                f"apply {BINARY_MODULAR_EXPONENTIATION_RESULT_FUNCTIONAL}",
                "exact hresult_witness", "exact hs",
            ),
            "Every guarded modular exponentiation has exactly one actual canonical natural result.",
        ),
    )


@dataclass(frozen=True, slots=True)
class BinaryModularStep:
    """One exact most-significant-bit-first square-and-multiply transition."""

    index: int
    bit: int
    prefix: int
    previous: int
    squared: int
    result: int


@dataclass(frozen=True, slots=True)
class BinaryModularExecution:
    """Bounded concrete execution; it never substitutes for a formal proof."""

    base: int
    exponent: int
    modulus: int
    base_residue: int
    bit_length: int
    operation_count: int
    result: int
    steps: tuple[BinaryModularStep, ...]


@dataclass(frozen=True, slots=True)
class BinaryModularTraceCode:
    """An independently checkable concrete Gödel-beta execution encoding."""

    code: int
    scale: int
    entries: tuple[int, ...]


def execute_binary_modular_exponentiation(
    base: int,
    exponent: int,
    modulus: int,
) -> BinaryModularExecution:
    """Return an actual bounded MSB-first trace with the promised step budget."""

    if type(base) is not int or base < 0:
        raise BinaryModularExponentiationError("the base must be a natural integer")
    if type(exponent) is not int or exponent < 0:
        raise BinaryModularExponentiationError("the exponent must be a natural integer")
    if type(modulus) is not int or modulus <= 1:
        raise BinaryModularExponentiationError("the modulus must be an integer greater than one")
    if base.bit_length() > MAX_BINARY_BASE_BITS:
        raise BinaryModularExponentiationError("the base exceeds the reviewed bit budget")
    if exponent.bit_length() > MAX_BINARY_EXPONENT_BITS:
        raise BinaryModularExponentiationError("the exponent exceeds the reviewed binary trace budget")
    if modulus.bit_length() > MAX_BINARY_MODULUS_BITS:
        raise BinaryModularExponentiationError("the modulus exceeds the reviewed bit budget")

    base_residue = base % modulus
    result = 1 % modulus
    prefix = 0
    operations = 2
    rows: list[BinaryModularStep] = []
    for index in range(exponent.bit_length() - 1, -1, -1):
        digit = (exponent >> index) & 1
        previous = result
        squared = (result * result) % modulus
        result = (squared * base_residue) % modulus if digit else squared
        prefix = 2 * prefix + digit
        operations += 2 + digit
        rows.append(
            BinaryModularStep(
                index=len(rows),
                bit=digit,
                prefix=prefix,
                previous=previous,
                squared=squared,
                result=result,
            )
        )
    bit_length = max(1, exponent.bit_length())
    if operations > 3 * bit_length + 2:
        raise AssertionError("the reviewed binary step budget was exceeded")
    return BinaryModularExecution(
        base=base,
        exponent=exponent,
        modulus=modulus,
        base_residue=base_residue,
        bit_length=bit_length,
        operation_count=operations,
        result=result,
        steps=tuple(rows),
    )


def verify_binary_modular_execution(receipt: BinaryModularExecution) -> bool:
    """Fail closed on omitted, reordered, forged, oversized, or bool-valued steps."""

    if type(receipt) is not BinaryModularExecution or type(receipt.steps) is not tuple:
        return False
    if len(receipt.steps) > MAX_BINARY_EXPONENT_BITS:
        return False
    if any(type(row) is not BinaryModularStep for row in receipt.steps):
        return False
    if any(
        type(value) is not int
        for value in (
            receipt.base,
            receipt.exponent,
            receipt.modulus,
            receipt.base_residue,
            receipt.bit_length,
            receipt.operation_count,
            receipt.result,
        )
    ):
        return False
    if any(
        type(value) is not int
        for row in receipt.steps
        for value in (
            row.index,
            row.bit,
            row.prefix,
            row.previous,
            row.squared,
            row.result,
        )
    ):
        return False
    try:
        expected = execute_binary_modular_exponentiation(
            receipt.base, receipt.exponent, receipt.modulus
        )
    except (BinaryModularExponentiationError, OverflowError, TypeError, ValueError):
        return False
    return receipt == expected and receipt.result == pow(
        receipt.base, receipt.exponent, receipt.modulus
    )


def encode_binary_modular_execution(
    receipt: BinaryModularExecution,
) -> BinaryModularTraceCode:
    """Encode a small *actual* execution as an independently checkable beta pair."""

    if not verify_binary_modular_execution(receipt):
        raise BinaryModularExponentiationError("the execution certificate is invalid")
    entries = (
        receipt.base_residue,
        receipt.exponent,
        receipt.modulus,
        receipt.result,
        *(value for row in receipt.steps for value in (
            row.bit, row.prefix, row.previous, row.squared, row.result
        )),
    )
    if len(entries) > MAX_BINARY_BETA_TRACE_ENTRIES:
        raise BinaryModularExponentiationError("execution exceeds the bounded beta-trace length")
    if max((value.bit_length() for value in entries), default=0) > MAX_BINARY_BETA_ENTRY_BITS:
        raise BinaryModularExponentiationError("execution exceeds the bounded beta-entry bit budget")
    scale = factorial(len(entries)) * (max(entries) + 1)
    projected_bits = sum(
        (1 + (index + 1) * scale).bit_length()
        for index in range(len(entries))
    )
    if projected_bits > MAX_BINARY_BETA_CODE_BITS:
        raise BinaryModularExponentiationError("execution exceeds the bounded beta-code bit budget")
    code = 0
    previous_modulus = 1
    for index, value in enumerate(entries):
        modulus = 1 + (index + 1) * scale
        correction = ((value - code) * pow(previous_modulus, -1, modulus)) % modulus
        code += previous_modulus * correction
        previous_modulus *= modulus
    if code.bit_length() > MAX_BINARY_BETA_CODE_BITS:
        raise BinaryModularExponentiationError("the encoded beta trace exceeded its bit budget")
    return BinaryModularTraceCode(code=code, scale=scale, entries=entries)


def verify_binary_modular_trace_code(
    receipt: BinaryModularExecution,
    encoded: BinaryModularTraceCode,
) -> bool:
    """Reject malformed, mismatched, noncanonical, or forged concrete beta codes."""

    if type(encoded) is not BinaryModularTraceCode or type(encoded.entries) is not tuple:
        return False
    if type(encoded.code) is not int or type(encoded.scale) is not int:
        return False
    if encoded.code < 0 or encoded.scale <= 0:
        return False
    if (
        len(encoded.entries) > MAX_BINARY_BETA_TRACE_ENTRIES
        or encoded.code.bit_length() > MAX_BINARY_BETA_CODE_BITS
        or encoded.scale.bit_length() > MAX_BINARY_BETA_CODE_BITS
    ):
        return False
    if any(type(value) is not int or value < 0 for value in encoded.entries):
        return False
    if any(value.bit_length() > MAX_BINARY_BETA_ENTRY_BITS for value in encoded.entries):
        return False
    try:
        expected = encode_binary_modular_execution(receipt)
    except (BinaryModularExponentiationError, OverflowError, TypeError, ValueError):
        return False
    return encoded == expected and all(
        encoded.code % (1 + (index + 1) * encoded.scale) == value
        for index, value in enumerate(encoded.entries)
    )


__all__ = [
    "BINARY_CANONICAL_RESIDUE_EXISTS",
    "BINARY_CANONICAL_RESIDUE_EXISTS_UNIQUE",
    "BINARY_CANONICAL_RESIDUE_FUNCTIONAL",
    "BINARY_EXPONENT_DOUBLED_POWER",
    "BINARY_EXPONENT_ODD_POWER",
    "BINARY_EXPONENT_SPLIT_EXISTS",
    "BINARY_MODULAR_EXPONENTIATION_RESULT_EXISTS",
    "BINARY_MODULAR_EXPONENTIATION_RESULT_EXISTS_UNIQUE",
    "BINARY_MODULAR_EXPONENTIATION_RESULT_FUNCTIONAL",
    "BINARY_MODULAR_MULTIPLY_CONGRUENCE",
    "BINARY_MODULAR_MULTIPLY_RESIDUE_EXISTS",
    "BINARY_MODULAR_SQUARE_CONGRUENCE",
    "BINARY_MODULAR_SQUARE_RESIDUE_EXISTS",
    "BINARY_MODULAR_STEP_EXISTS",
    "BINARY_MODULAR_STEP_FUNCTIONAL",
    "BINARY_MODULUS_NONTRIVIAL_NONZERO",
    "BinaryModularExecution",
    "BinaryModularExponentiationError",
    "BinaryModularStep",
    "BinaryModularTraceCode",
    "MAX_BINARY_BASE_BITS",
    "MAX_BINARY_BETA_CODE_BITS",
    "MAX_BINARY_BETA_ENTRY_BITS",
    "MAX_BINARY_BETA_TRACE_ENTRIES",
    "MAX_BINARY_EXPONENT_BITS",
    "MAX_BINARY_MODULUS_BITS",
    "binary_doubled_power",
    "binary_exponent_split",
    "binary_modular_power",
    "binary_modular_step",
    "binary_modulus_relation",
    "binary_odd_power",
    "canonical_modular_residue",
    "encode_binary_modular_execution",
    "execute_binary_modular_exponentiation",
    "make_binary_modular_exponentiation_candidate_theorems",
    "verify_binary_modular_execution",
    "verify_binary_modular_trace_code",
]
