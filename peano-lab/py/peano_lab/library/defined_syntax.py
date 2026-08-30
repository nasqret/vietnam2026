"""Conservative, opt-in defined predicate syntax for Peano Lab.

The kernel language remains unchanged.  This module recognizes a small,
versioned registry of calls of the form ``Name(term, ...)`` and expands them
immediately to the existing first-order PA formula and term constructors.
The ordinary :mod:`peano_lab.kernel.formulas` parse APIs deliberately do not
enable these definitions.

Definitions are templates over de Bruijn parameter slots.  Instantiation is
simultaneous and binder-aware: actual arguments are lifted when copied under
a template binder, so neither template binders nor names chosen by the user
can capture them.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import Mapping

from peano_lab.library.finite_factorial_theorems import factorial_relation
from peano_lab.library.finite_fold_surface import (
    all_bits,
    beta_at,
    bit_count,
    power_relation,
    product_relation,
    range_relation,
    repeat_relation,
    sum_relation,
)
from peano_lab.library.finite_permutation_theorems import (
    bounded_prefix,
    contains_prefix,
    injective_prefix,
    permutation_prefix,
    surjective_prefix,
)
from peano_lab.library.quadratic_residue_surface import (
    bounded_quadratic_residue,
    congruent_mod,
    quadratic_residue,
)

from peano_lab.kernel.formulas import (
    And,
    Bot,
    Eq,
    Exists,
    Forall,
    Formula,
    Imp,
    Or,
    _FormulaParser,
    parse_formula_in_context,
)
from peano_lab.kernel.terms import (
    Add,
    Mul,
    ParseError,
    Succ,
    Term,
    Var,
    Zero,
    _is_identifier,
    _parse_term_from,
)


DEFINED_SYNTAX_REGISTRY_ID = "peano-lab.defined-predicates"
DEFINED_SYNTAX_VERSION = 2
DEFAULT_EXPANSION_BUDGET = 32_768


@dataclass(frozen=True, slots=True)
class DefinitionSpec:
    """Immutable metadata and core template for one surface definition."""

    stable_id: str
    name: str
    parameters: tuple[str, ...]
    template_source: str
    template_formula: Formula
    summary: str
    category: str
    priority: str = "P0"
    conceptual_dependencies: tuple[str, ...] = ()

    @property
    def arity(self) -> int:
        return len(self.parameters)


def _definition(
    *,
    stable_id: str,
    name: str,
    parameters: tuple[str, ...],
    template_source: str,
    summary: str,
    category: str,
    priority: str = "P0",
    conceptual_dependencies: tuple[str, ...] = (),
) -> DefinitionSpec:
    if not stable_id or not isinstance(stable_id, str):
        raise ValueError("definition stable_id must be non-empty text")
    if not _is_identifier(name):
        raise ValueError("definition name must be a Peano identifier")
    if (
        not parameters
        or not all(_is_identifier(parameter) for parameter in parameters)
        or len(set(parameters)) != len(parameters)
    ):
        raise ValueError("definition parameters must be distinct Peano identifiers")
    if not summary or not category:
        raise ValueError("definition summary and category must be non-empty")
    if priority not in {"P0", "P1", "P2", "adjacent"}:
        raise ValueError("definition priority must be P0, P1, P2, or adjacent")
    template_formula = parse_formula_in_context(template_source, list(parameters))
    return DefinitionSpec(
        stable_id=stable_id,
        name=name,
        parameters=parameters,
        template_source=template_source,
        template_formula=template_formula,
        summary=summary,
        category=category,
        priority=priority,
        conceptual_dependencies=conceptual_dependencies,
    )


def _all_prime_source(code: str, scale: str, length: str) -> str:
    """Return the canonical expanded AllPrime prefix convention."""

    entry = beta_at(code, scale, "dp_i", "dp_p", tag="defined_all_prime_entry")
    return (
        f"forall dp_i. (exists dp_gap. dp_gap + S dp_i = {length}) -> "
        f"exists dp_p. (({entry}) /\\ (~(dp_p = 1) /\\ "
        "forall dp_a dp_d. dp_p = dp_a * dp_d -> "
        "dp_a = 1 \\/ dp_d = 1))"
    )


def _beta_at_term_source(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand BetaAt for audited internal terms, including successor indices."""

    modulus = f"S ((S ({index})) * {scale})"
    return (
        f"((exists dp_beta_h_{tag}. dp_beta_h_{tag} + S ({value}) = {modulus}) /\\ "
        f"exists dp_beta_q_{tag}. {code} = "
        f"dp_beta_q_{tag} * {modulus} + ({value}))"
    )


def _sorted_source(code: str, scale: str, length: str) -> str:
    """Return the canonical expanded adjacent nondecreasing convention."""

    left = beta_at(code, scale, "dp_i", "dp_p", tag="defined_sorted_left")
    right = _beta_at_term_source(
        code,
        scale,
        "S dp_i",
        "dp_q",
        tag="defined_sorted_right",
    )
    return (
        f"forall dp_i. (exists dp_gap. dp_gap + S (S dp_i) = {length}) -> "
        f"exists dp_p dp_q. (({left}) /\\ (({right}) /\\ "
        "(exists dp_le. dp_le + dp_p = dp_q)))"
    )


def _canonical_pf_source(
    code: str, scale: str, length: str, value: str
) -> str:
    """Return Product together with prime, sorted factor metadata."""

    product = product_relation(
        code, scale, length, value, tag="defined_canonical_pf_product"
    )
    all_prime = _all_prime_source(code, scale, length)
    sorted_prefix = _sorted_source(code, scale, length)
    return f"(({product}) /\\ (({all_prime}) /\\ ({sorted_prefix})))"


def _unit_residue_source(modulus: str, value: str) -> str:
    return (
        f"(~(({value}) = 0) /\\ "
        f"(exists dp_gap. dp_gap + S ({value}) = {modulus}))"
    )


def _scaled_inverse_source(
    modulus: str, target: str, left: str, right: str
) -> str:
    left_unit = _unit_residue_source(modulus, left)
    right_unit = _unit_residue_source(modulus, right)
    congruence = (
        f"exists dp_u dp_v. ({left}) * ({right}) + {modulus} * dp_u = "
        f"({target}) + {modulus} * dp_v"
    )
    return f"(({left_unit}) /\\ (({right_unit}) /\\ ({congruence})))"


def _balanced_inverse_source(modulus: str, value: str, inverse: str) -> str:
    return (
        f"exists dp_u dp_v. ({value}) * ({inverse}) + {modulus} * dp_u = "
        f"1 + {modulus} * dp_v"
    )


def _bounded_nonzero_inverse_source(modulus: str, value: str) -> str:
    inverse = "dp_inverse"
    return (
        f"exists {inverse}. (~({inverse} = 0) /\\ "
        f"((exists dp_bound. dp_bound + S {inverse} = {modulus}) /\\ "
        f"({_balanced_inverse_source(modulus, value, inverse)})))"
    )


def _scaled_fixed_point_source(modulus: str, target: str, value: str) -> str:
    unit = _unit_residue_source(modulus, value)
    square = congruent_mod(
        modulus,
        "dp_square",
        target,
        tag="defined_scaled_fixed_point",
    )
    if square.count("dp_square") != 1:
        raise AssertionError("unexpected scaled-fixed-point congruence expansion")
    square = square.replace("dp_square", f"({value}) * ({value})")
    return f"(({unit}) /\\ ({square}))"


def _successor_inverse_source(modulus: str, left: str, right: str) -> str:
    return (
        f"exists dp_u dp_v. (S {left}) * S {right} + {modulus} * dp_u = "
        f"1 + {modulus} * dp_v"
    )


def _inverse_index_source(
    modulus: str, length: str, left: str, right: str
) -> str:
    left_bound = f"exists dp_left_gap. dp_left_gap + S {left} = {length}"
    right_bound = f"exists dp_right_gap. dp_right_gap + S {right} = {length}"
    inverse = _successor_inverse_source(modulus, left, right)
    return f"(({left_bound}) /\\ (({right_bound}) /\\ ({inverse})))"


def _inverse_prefix_source(
    modulus: str, bound: str, code: str, scale: str, length: str
) -> str:
    entry = beta_at(
        code,
        scale,
        "dp_i",
        "dp_j",
        tag="defined_inverse_prefix_entry",
    )
    relation = _inverse_index_source(modulus, bound, "dp_i", "dp_j")
    return (
        f"forall dp_i. (exists dp_prefix_gap. "
        f"dp_prefix_gap + S dp_i = {length}) -> exists dp_j. "
        f"(({entry}) /\\ ({relation}))"
    )


def _scaled_inverse_index_source(
    modulus: str, target: str, bound: str, index: str, mate: str
) -> str:
    index_bound = f"exists dp_index_gap. dp_index_gap + S {index} = {bound}"
    scaled = _scaled_inverse_source(modulus, target, f"S {index}", mate)
    return f"(({index_bound}) /\\ ({scaled}))"


def _scaled_inverse_prefix_source(
    modulus: str,
    target: str,
    bound: str,
    code: str,
    scale: str,
    length: str,
) -> str:
    entry = beta_at(
        code,
        scale,
        "dp_i",
        "dp_y",
        tag="defined_scaled_inverse_prefix_entry",
    )
    relation = _scaled_inverse_index_source(
        modulus,
        target,
        bound,
        "dp_i",
        "dp_y",
    )
    return (
        f"forall dp_i. (exists dp_prefix_gap. "
        f"dp_prefix_gap + S dp_i = {length}) -> exists dp_y. "
        f"(({entry}) /\\ ({relation}))"
    )


def _division_prefix_source(
    modulus: str,
    source_code: str,
    source_scale: str,
    quotient_code: str,
    quotient_scale: str,
    remainder_code: str,
    remainder_scale: str,
    length: str,
) -> str:
    source = beta_at(
        source_code,
        source_scale,
        "dp_i",
        "dp_x",
        tag="defined_division_prefix_source",
    )
    quotient = beta_at(
        quotient_code,
        quotient_scale,
        "dp_i",
        "dp_q",
        tag="defined_division_prefix_quotient",
    )
    remainder = beta_at(
        remainder_code,
        remainder_scale,
        "dp_i",
        "dp_r",
        tag="defined_division_prefix_remainder",
    )
    return (
        f"forall dp_i. (exists dp_index_gap. "
        f"dp_index_gap + S dp_i = {length}) -> exists dp_x dp_q dp_r. "
        f"({source}) /\\ (({quotient}) /\\ (({remainder}) /\\ "
        f"(dp_x = {modulus} * dp_q + dp_r /\\ "
        f"(exists dp_remainder_gap. dp_remainder_gap + S dp_r = {modulus}))))"
    )


DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _definition(
        stable_id="PD0001",
        name="Le",
        parameters=("a", "b"),
        template_source="exists h. h + a = b",
        summary="Witness-defined non-strict order on natural numbers.",
        category="order",
    ),
    _definition(
        stable_id="PD0002",
        name="Lt",
        parameters=("a", "b"),
        template_source="exists h. h + S a = b",
        summary="Witness-defined strict order on natural numbers.",
        category="order",
    ),
    _definition(
        stable_id="PD0003",
        name="Dvd",
        parameters=("d", "n"),
        template_source="exists k. n = d * k",
        summary="The natural number d divides n.",
        category="divisibility",
    ),
    _definition(
        stable_id="PD0004",
        name="Prime",
        parameters=("p",),
        template_source=(
            "~(p = 1) /\\ forall a b. p = a * b -> a = 1 \\/ b = 1"
        ),
        summary="p is nonunit and every factorization of p has a unit factor.",
        category="primes",
    ),
    _definition(
        stable_id="PD0005",
        name="Coprime",
        parameters=("a", "b"),
        template_source=(
            "forall d. (exists x. a = d * x) -> "
            "(exists y. b = d * y) -> d = 1"
        ),
        summary="Every common divisor of a and b is one.",
        category="gcd_coprime",
        conceptual_dependencies=("Dvd",),
    ),
    _definition(
        stable_id="PD0006",
        name="IsGCD",
        parameters=("g", "a", "b"),
        template_source=(
            "((exists x. a = g * x) /\\ (exists y. b = g * y)) /\\ "
            "forall d. (exists u. a = d * u) -> "
            "(exists v. b = d * v) -> exists w. g = d * w"
        ),
        summary="g is a common divisor divisible by every common divisor.",
        category="gcd_coprime",
        conceptual_dependencies=("Dvd",),
    ),
    _definition(
        stable_id="PD0007",
        name="DivRem",
        parameters=("n", "d", "q", "r"),
        template_source="n = d * q + r /\\ exists h. h + S r = d",
        summary="q and r are a quotient and a strict remainder for n by d.",
        category="division",
        conceptual_dependencies=("Lt",),
    ),
    _definition(
        stable_id="PD0008",
        name="ModEq",
        parameters=("m", "a", "b"),
        template_source="exists u v. a + m * u = b + m * v",
        summary="Balanced-natural congruence modulo m.",
        category="congruence",
    ),
    _definition(
        stable_id="PD0009",
        name="Even",
        parameters=("n",),
        template_source="exists h. n = 2 * h",
        summary="n has an even decomposition.",
        category="parity",
        priority="P1",
    ),
    _definition(
        stable_id="PD0010",
        name="Odd",
        parameters=("n",),
        template_source="exists h. n = 2 * h + 1",
        summary="n has an odd decomposition.",
        category="parity",
        priority="P1",
    ),
    _definition(
        stable_id="PD0011",
        name="Mod4One",
        parameters=("n",),
        template_source="exists h. n = 4 * h + 1",
        summary="n is one modulo four by an explicit quotient.",
        category="small_residues",
        priority="P1",
    ),
    _definition(
        stable_id="PD0012",
        name="Mod4Three",
        parameters=("n",),
        template_source="exists h. n = 4 * h + 3",
        summary="n is three modulo four by an explicit quotient.",
        category="small_residues",
        priority="P1",
    ),
    _definition(
        stable_id="PD0013",
        name="BetaAt",
        parameters=("b", "c", "i", "x"),
        template_source=beta_at("b", "c", "i", "x", tag="defined_beta_at"),
        summary="x is the bounded beta-decoded value at index i.",
        category="finite_coding",
    ),
    _definition(
        stable_id="PD0014",
        name="Product",
        parameters=("b", "c", "l", "z"),
        template_source=product_relation(
            "b", "c", "l", "z", tag="defined_product"
        ),
        summary="z is the product of a beta-coded prefix of length l.",
        category="finite_folds",
        conceptual_dependencies=("Lt", "BetaAt"),
    ),
    _definition(
        stable_id="PD0015",
        name="Sum",
        parameters=("b", "c", "l", "z"),
        template_source=sum_relation("b", "c", "l", "z", tag="defined_sum"),
        summary="z is the sum of a beta-coded prefix of length l.",
        category="finite_folds",
        conceptual_dependencies=("Lt", "BetaAt"),
    ),
    _definition(
        stable_id="PD0016",
        name="AllBits",
        parameters=("b", "c", "l"),
        template_source=all_bits("b", "c", "l", tag="defined_all_bits"),
        summary="Every decoded entry below l is zero or one.",
        category="finite_folds",
        priority="P1",
        conceptual_dependencies=("Lt", "BetaAt"),
    ),
    _definition(
        stable_id="PD0017",
        name="BitCount",
        parameters=("b", "c", "l", "z"),
        template_source=bit_count(
            "b", "c", "l", "z", tag="defined_bit_count"
        ),
        summary="z is the sum of a beta-coded all-bit prefix.",
        category="finite_folds",
        priority="P1",
        conceptual_dependencies=("Sum", "AllBits"),
    ),
    _definition(
        stable_id="PD0018",
        name="Range",
        parameters=("b", "c", "a", "l"),
        template_source=range_relation(
            "b", "c", "a", "l", tag="defined_range"
        ),
        summary="The decoded prefix is a,a+1,...,a+l-1.",
        category="finite_coding",
        priority="P1",
        conceptual_dependencies=("Lt", "BetaAt"),
    ),
    _definition(
        stable_id="PD0019",
        name="Repeat",
        parameters=("b", "c", "a", "l"),
        template_source=repeat_relation(
            "b", "c", "a", "l", tag="defined_repeat"
        ),
        summary="The decoded prefix repeats a for l positions.",
        category="finite_coding",
        priority="P1",
        conceptual_dependencies=("Lt", "BetaAt"),
    ),
    _definition(
        stable_id="PD0020",
        name="Pow",
        parameters=("a", "e", "z"),
        template_source=power_relation("a", "e", "z", tag="defined_power"),
        summary="z is the relational e-th power of a.",
        category="finite_folds",
        priority="P1",
        conceptual_dependencies=("Product", "Repeat"),
    ),
    _definition(
        stable_id="PD0021",
        name="QRes",
        parameters=("m", "a"),
        template_source=quadratic_residue("m", "a", tag="defined_qres"),
        summary="a has a square root modulo m.",
        category="quadratic_residues",
        priority="P1",
        conceptual_dependencies=("ModEq",),
    ),
    _definition(
        stable_id="PD0022",
        name="BoundedQRes",
        parameters=("m", "a"),
        template_source=bounded_quadratic_residue(
            "m", "a", tag="defined_bounded_qres"
        ),
        summary="a has a square root strictly below m modulo m.",
        category="quadratic_residues",
        priority="P1",
        conceptual_dependencies=("Lt", "ModEq"),
    ),
    _definition(
        stable_id="PD0023",
        name="Factorial",
        parameters=("n", "z"),
        template_source=factorial_relation("n", "z", tag="defined_factorial"),
        summary="z is the relational factorial of n.",
        category="finite_folds",
        priority="P1",
        conceptual_dependencies=("Product", "Range"),
    ),
    _definition(
        stable_id="PD0024",
        name="BoundedPrefix",
        parameters=("b", "c", "l"),
        template_source=bounded_prefix(
            "b", "c", "l", tag="defined_bounded_prefix"
        ),
        summary="Every decoded entry below l is itself below l.",
        category="finite_permutations",
        priority="P1",
        conceptual_dependencies=("Lt", "BetaAt"),
    ),
    _definition(
        stable_id="PD0025",
        name="InjectivePrefix",
        parameters=("b", "c", "l"),
        template_source=injective_prefix(
            "b", "c", "l", tag="defined_injective_prefix"
        ),
        summary="Equal decoded values below l have equal indices.",
        category="finite_permutations",
        priority="P1",
        conceptual_dependencies=("Lt", "BetaAt"),
    ),
    _definition(
        stable_id="PD0026",
        name="SurjectivePrefix",
        parameters=("b", "c", "l"),
        template_source=surjective_prefix(
            "b", "c", "l", tag="defined_surjective_prefix"
        ),
        summary="Every value below l occurs at an index below l.",
        category="finite_permutations",
        priority="P1",
        conceptual_dependencies=("Lt", "BetaAt"),
    ),
    _definition(
        stable_id="PD0027",
        name="ContainsPrefix",
        parameters=("b", "c", "l", "x"),
        template_source=contains_prefix(
            "b", "c", "l", "x", tag="defined_contains_prefix"
        ),
        summary="x occurs in the decoded prefix below l.",
        category="finite_permutations",
        priority="P1",
        conceptual_dependencies=("Lt", "BetaAt"),
    ),
    _definition(
        stable_id="PD0028",
        name="AllPrime",
        parameters=("b", "c", "l"),
        template_source=_all_prime_source("b", "c", "l"),
        summary="Every decoded factor below l is prime.",
        category="factorization",
        priority="P1",
        conceptual_dependencies=("Lt", "Prime", "BetaAt"),
    ),
    _definition(
        stable_id="PD0029",
        name="Sorted",
        parameters=("b", "c", "l"),
        template_source=_sorted_source("b", "c", "l"),
        summary="Adjacent decoded entries form a nondecreasing prefix.",
        category="factorization",
        priority="P1",
        conceptual_dependencies=("Le", "Lt", "BetaAt"),
    ),
    _definition(
        stable_id="PD0030",
        name="UnitResidue",
        parameters=("m", "a"),
        template_source=_unit_residue_source("m", "a"),
        summary="a is nonzero and strictly below m.",
        category="modular_units",
        priority="P1",
        conceptual_dependencies=("Lt",),
    ),
    _definition(
        stable_id="PD0031",
        name="BalancedInverse",
        parameters=("m", "a", "b"),
        template_source=_balanced_inverse_source("m", "a", "b"),
        summary="a times b is congruent to one modulo m.",
        category="modular_units",
        priority="P1",
        conceptual_dependencies=("ModEq",),
    ),
    _definition(
        stable_id="PD0032",
        name="BoundedNonzeroInverse",
        parameters=("m", "a"),
        template_source=_bounded_nonzero_inverse_source("m", "a"),
        summary="a has a nonzero inverse strictly below m.",
        category="modular_units",
        priority="P1",
        conceptual_dependencies=("Lt", "BalancedInverse"),
    ),
    _definition(
        stable_id="PD0033",
        name="ScaledInverse",
        parameters=("m", "t", "a", "b"),
        template_source=_scaled_inverse_source("m", "t", "a", "b"),
        summary="a and b are bounded units whose product is t modulo m.",
        category="modular_units",
        priority="P2",
        conceptual_dependencies=("ModEq", "UnitResidue"),
    ),
    _definition(
        stable_id="PD0034",
        name="ScaledFixedPoint",
        parameters=("m", "t", "a"),
        template_source=_scaled_fixed_point_source("m", "t", "a"),
        summary="a is a bounded unit whose square is t modulo m.",
        category="modular_units",
        priority="P2",
        conceptual_dependencies=("ModEq", "UnitResidue"),
    ),
    _definition(
        stable_id="PD0035",
        name="SuccessorInverse",
        parameters=("m", "i", "j"),
        template_source=_successor_inverse_source("m", "i", "j"),
        summary="The successor residues of i and j multiply to one modulo m.",
        category="modular_involutions",
        priority="P2",
        conceptual_dependencies=("ModEq",),
    ),
    _definition(
        stable_id="PD0036",
        name="InverseIndex",
        parameters=("m", "l", "i", "j"),
        template_source=_inverse_index_source("m", "l", "i", "j"),
        summary="i and j are bounded zero-based modular inverse indices.",
        category="modular_involutions",
        priority="P2",
        conceptual_dependencies=("Lt", "SuccessorInverse"),
    ),
    _definition(
        stable_id="PD0037",
        name="InversePrefix",
        parameters=("m", "l", "b", "c", "k"),
        template_source=_inverse_prefix_source("m", "l", "b", "c", "k"),
        summary="A beta prefix decodes a bounded modular inverse map.",
        category="modular_involutions",
        priority="P2",
        conceptual_dependencies=("Lt", "BetaAt", "InverseIndex"),
    ),
    _definition(
        stable_id="PD0038",
        name="ScaledInverseIndex",
        parameters=("m", "t", "l", "i", "y"),
        template_source=_scaled_inverse_index_source("m", "t", "l", "i", "y"),
        summary="i indexes a bounded unit mapped to y by scaled inversion.",
        category="modular_involutions",
        priority="P2",
        conceptual_dependencies=("Lt", "ScaledInverse"),
    ),
    _definition(
        stable_id="PD0039",
        name="ScaledInversePrefix",
        parameters=("m", "t", "l", "b", "c", "k"),
        template_source=_scaled_inverse_prefix_source(
            "m", "t", "l", "b", "c", "k"
        ),
        summary="A beta prefix decodes a scaled inverse map.",
        category="modular_involutions",
        priority="P2",
        conceptual_dependencies=("Lt", "BetaAt", "ScaledInverseIndex"),
    ),
    _definition(
        stable_id="PD0040",
        name="DivisionPrefix",
        parameters=("m", "b", "c", "qb", "qc", "rb", "rc", "l"),
        template_source=_division_prefix_source(
            "m", "b", "c", "qb", "qc", "rb", "rc", "l"
        ),
        summary="Beta prefixes encode pointwise quotients and strict remainders.",
        category="finite_division",
        priority="P2",
        conceptual_dependencies=("Lt", "DivRem", "BetaAt"),
    ),
)


ADJACENT_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _definition(
        stable_id="PA-COMPOSITE-PERMUTATION-PREFIX-v1",
        name="PermutationPrefix",
        parameters=("b", "c", "l"),
        template_source=permutation_prefix(
            "b", "c", "l", tag="defined_permutation_prefix"
        ),
        summary="A bounded beta prefix is injective and surjective.",
        category="finite_permutations",
        priority="adjacent",
        conceptual_dependencies=(
            "BoundedPrefix",
            "InjectivePrefix",
            "SurjectivePrefix",
        ),
    ),
    _definition(
        stable_id="PA-COMPOSITE-BALANCED-BEZOUT-v1",
        name="BalancedBezout",
        parameters=("d", "a", "b"),
        template_source=(
            "exists xp yp xn yn. "
            "a * xp + b * yp = d + (a * xn + b * yn)"
        ),
        summary="Four naturals encode a signed Bezout combination with result d.",
        category="gcd",
        priority="adjacent",
    ),
    _definition(
        stable_id="PA-COMPOSITE-CANONICAL-PF-v1",
        name="CanonicalPF",
        parameters=("n", "l", "b", "c"),
        template_source=_canonical_pf_source("b", "c", "l", "n"),
        summary="A sorted all-prime beta prefix has exact product n.",
        category="factorization",
        priority="adjacent",
        conceptual_dependencies=("Product", "AllPrime", "Sorted"),
    ),
)


ALL_DEFINITIONS: tuple[DefinitionSpec, ...] = DEFINITIONS + ADJACENT_DEFINITIONS


def _build_definition_map(
    definitions: tuple[DefinitionSpec, ...],
    *,
    dependency_universe: tuple[DefinitionSpec, ...] | None = None,
) -> Mapping[str, DefinitionSpec]:
    result: dict[str, DefinitionSpec] = {}
    stable_ids: set[str] = set()
    for definition in definitions:
        if definition.name in result:
            raise ValueError(f"duplicate definition name: {definition.name}")
        if definition.stable_id in stable_ids:
            raise ValueError(f"duplicate definition stable id: {definition.stable_id}")
        result[definition.name] = definition
        stable_ids.add(definition.stable_id)
    universe = definitions if dependency_universe is None else dependency_universe
    universe_names = {definition.name for definition in universe}
    for definition in definitions:
        unknown = set(definition.conceptual_dependencies) - universe_names
        if unknown:
            joined = ", ".join(sorted(unknown))
            raise ValueError(f"unknown conceptual dependencies for {definition.name}: {joined}")
    return MappingProxyType(result)


DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = _build_definition_map(DEFINITIONS)
ALL_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = _build_definition_map(
    ALL_DEFINITIONS,
)
DEFINITIONS_BY_ID: Mapping[str, DefinitionSpec] = MappingProxyType(
    {definition.stable_id: definition for definition in DEFINITIONS}
)
ALL_DEFINITIONS_BY_ID: Mapping[str, DefinitionSpec] = MappingProxyType(
    {definition.stable_id: definition for definition in ALL_DEFINITIONS}
)


def _registry_sha256() -> str:
    def definition_record(definition: DefinitionSpec) -> dict[str, object]:
        return {
            "stable_id": definition.stable_id,
            "name": definition.name,
            "parameters": definition.parameters,
            "template_source": definition.template_source,
            "summary": definition.summary,
            "category": definition.category,
            "priority": definition.priority,
            "conceptual_dependencies": definition.conceptual_dependencies,
        }

    registry_record = {
        "registry_id": DEFINED_SYNTAX_REGISTRY_ID,
        "version": DEFINED_SYNTAX_VERSION,
        "definitions": [
            definition_record(definition) for definition in DEFINITIONS
        ],
        "adjacent_definitions": [
            definition_record(definition) for definition in ADJACENT_DEFINITIONS
        ],
    }
    payload = json.dumps(
        registry_record,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


DEFINED_SYNTAX_REGISTRY_SHA256 = _registry_sha256()


class _ExpansionCounter:
    __slots__ = ("limit", "used")

    def __init__(self, limit: int):
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise ValueError("expansion_budget must be a positive integer")
        self.limit = limit
        self.used = 0

    def node(self, definition: DefinitionSpec, column: int) -> None:
        self.used += 1
        if self.used > self.limit:
            raise ParseError(
                f"defined-syntax expansion exceeds the {self.limit}-node budget "
                f"while expanding {definition.name!r} at column {column}"
            )


def _copy_shifted_argument(
    term: Term,
    by: int,
    counter: _ExpansionCounter,
    definition: DefinitionSpec,
    column: int,
) -> Term:
    counter.node(definition, column)
    if isinstance(term, Var):
        return Var(term.index + by)
    if isinstance(term, Zero):
        return term
    if isinstance(term, Succ):
        return Succ(_copy_shifted_argument(term.term, by, counter, definition, column))
    if isinstance(term, Add):
        return Add(
            _copy_shifted_argument(term.left, by, counter, definition, column),
            _copy_shifted_argument(term.right, by, counter, definition, column),
        )
    if isinstance(term, Mul):
        return Mul(
            _copy_shifted_argument(term.left, by, counter, definition, column),
            _copy_shifted_argument(term.right, by, counter, definition, column),
        )
    raise TypeError("expected a PA term")


def _instantiate_term(
    term: Term,
    arguments: tuple[Term, ...],
    depth: int,
    counter: _ExpansionCounter,
    definition: DefinitionSpec,
    column: int,
) -> Term:
    if isinstance(term, Var):
        if term.index < depth:
            counter.node(definition, column)
            return term
        parameter_index = term.index - depth
        if parameter_index >= len(arguments):
            raise ValueError(
                f"definition {definition.name!r} template has an unbound variable slot"
            )
        return _copy_shifted_argument(
            arguments[parameter_index], depth, counter, definition, column
        )
    counter.node(definition, column)
    if isinstance(term, Zero):
        return term
    if isinstance(term, Succ):
        return Succ(
            _instantiate_term(
                term.term, arguments, depth, counter, definition, column
            )
        )
    if isinstance(term, Add):
        return Add(
            _instantiate_term(
                term.left, arguments, depth, counter, definition, column
            ),
            _instantiate_term(
                term.right, arguments, depth, counter, definition, column
            ),
        )
    if isinstance(term, Mul):
        return Mul(
            _instantiate_term(
                term.left, arguments, depth, counter, definition, column
            ),
            _instantiate_term(
                term.right, arguments, depth, counter, definition, column
            ),
        )
    raise TypeError("expected a PA term")


def _instantiate_formula(
    formula: Formula,
    arguments: tuple[Term, ...],
    depth: int,
    counter: _ExpansionCounter,
    definition: DefinitionSpec,
    column: int,
) -> Formula:
    counter.node(definition, column)
    if isinstance(formula, Eq):
        return Eq(
            _instantiate_term(
                formula.left, arguments, depth, counter, definition, column
            ),
            _instantiate_term(
                formula.right, arguments, depth, counter, definition, column
            ),
        )
    if isinstance(formula, Bot):
        return formula
    if isinstance(formula, Imp):
        return Imp(
            _instantiate_formula(
                formula.left, arguments, depth, counter, definition, column
            ),
            _instantiate_formula(
                formula.right, arguments, depth, counter, definition, column
            ),
        )
    if isinstance(formula, And):
        return And(
            _instantiate_formula(
                formula.left, arguments, depth, counter, definition, column
            ),
            _instantiate_formula(
                formula.right, arguments, depth, counter, definition, column
            ),
        )
    if isinstance(formula, Or):
        return Or(
            _instantiate_formula(
                formula.left, arguments, depth, counter, definition, column
            ),
            _instantiate_formula(
                formula.right, arguments, depth, counter, definition, column
            ),
        )
    if isinstance(formula, Forall):
        return Forall(
            _instantiate_formula(
                formula.body, arguments, depth + 1, counter, definition, column
            )
        )
    if isinstance(formula, Exists):
        return Exists(
            _instantiate_formula(
                formula.body, arguments, depth + 1, counter, definition, column
            )
        )
    raise TypeError("expected a PA formula")


class _DefinedFormulaParser(_FormulaParser):
    def __init__(self, source: str, expansion_budget: int):
        super().__init__(source)
        self.expansion_counter = _ExpansionCounter(expansion_budget)

    def _atom(self) -> Formula:
        token = self.stream.peek()
        position = self.stream.position
        has_open_parenthesis = (
            position + 1 < len(self.stream.tokens)
            and self.stream.tokens[position + 1].text == "("
        )
        # S(...) remains ordinary successor-term syntax.  Every other
        # identifier followed immediately by '(' is a predicate call in this
        # opt-in grammar, so misspellings receive a direct, positioned error.
        if _is_identifier(token) and token != "S" and has_open_parenthesis:
            column = self.stream.column()
            name = self.stream.take()
            definition = ALL_DEFINITIONS_BY_NAME.get(name)
            if definition is None:
                raise ParseError(
                    f"unknown defined predicate {name!r} at column {column}"
                )
            self.stream.expect("(")
            arguments: list[Term] = []
            if self.stream.accept(")") is None:
                while True:
                    arguments.append(
                        _parse_term_from(self.stream, self.bound, self.free)
                    )
                    if self.stream.accept(")") is not None:
                        break
                    self.stream.expect(",")
            if len(arguments) != definition.arity:
                suffix = "argument" if definition.arity == 1 else "arguments"
                raise ParseError(
                    f"defined predicate {name!r} expects {definition.arity} {suffix}, "
                    f"got {len(arguments)} at column {column}"
                )
            return _instantiate_formula(
                definition.template_formula,
                tuple(arguments),
                0,
                self.expansion_counter,
                definition,
                column,
            )
        return super()._atom()


def parse_defined_formula_with_names(
    src: str,
    *,
    expansion_budget: int = DEFAULT_EXPANSION_BUDGET,
) -> tuple[Formula, tuple[str, ...]]:
    """Parse opt-in defined syntax and return its surface free-name table."""

    parser = _DefinedFormulaParser(src, expansion_budget)
    return parser.parse(), tuple(parser.free)


def parse_defined_formula_in_context(
    src: str,
    names: list[str],
    *,
    expansion_budget: int = DEFAULT_EXPANSION_BUDGET,
) -> Formula:
    """Parse defined syntax in an exact free-variable context."""

    if (
        not isinstance(names, list)
        or not all(isinstance(name, str) and _is_identifier(name) for name in names)
        or len(set(names)) != len(names)
    ):
        raise ValueError("context names must be distinct surface identifiers")
    parser = _DefinedFormulaParser(src, expansion_budget)
    parser.free = list(names)
    formula = parser.parse()
    if len(parser.free) != len(names):
        unknown = ", ".join(parser.free[len(names) :])
        raise ParseError(f"unknown term variable(s): {unknown}")
    return formula


def parse_defined_formula(
    src: str,
    *,
    expansion_budget: int = DEFAULT_EXPANSION_BUDGET,
) -> Formula:
    """Parse a formula with the fixed defined-predicate registry enabled."""

    return parse_defined_formula_with_names(
        src, expansion_budget=expansion_budget
    )[0]


__all__ = [
    "DefinitionSpec",
    "DEFINED_SYNTAX_REGISTRY_ID",
    "DEFINED_SYNTAX_VERSION",
    "DEFINED_SYNTAX_REGISTRY_SHA256",
    "DEFAULT_EXPANSION_BUDGET",
    "DEFINITIONS",
    "DEFINITIONS_BY_NAME",
    "DEFINITIONS_BY_ID",
    "ADJACENT_DEFINITIONS",
    "ALL_DEFINITIONS",
    "ALL_DEFINITIONS_BY_NAME",
    "ALL_DEFINITIONS_BY_ID",
    "parse_defined_formula",
    "parse_defined_formula_with_names",
    "parse_defined_formula_in_context",
]
