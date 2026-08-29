"""Conservative, additive notation for actual sums and coefficient tables.

All 318 earlier definition objects and identities remain literal.  Generic
beta-prefix bounds/equality are named once and reused by the polynomial
chapter; a polynomial's representation length is not silently its degree.
No abbreviation, definition edge, or blueprint label provides proof authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Callable

from constructive_bottom_layer_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME,
    _contextual,
)
from peano_lab.library.defined_syntax import DefinitionSpec, _definition
from peano_lab.library import arithmetic_table_extension_candidate as extension
from peano_lab.library import mobius_table_candidate as mobius
from peano_lab.library import divisor_mask_candidate as divisor
from peano_lab.library import signed_table_operations_candidate as signed
from peano_lab.library import signed_weighted_sum_candidate as weighted
from peano_lab.library import prime_field_polynomial_candidate as polynomial
from peano_lab.library import prime_field_polynomial_evaluation_candidate as horner


def _construct(identifier: int, name: str, parameters: tuple[str, ...],
               builder: Callable[..., str], summary: str,
               dependencies: tuple[str, ...]) -> DefinitionSpec:
    return _definition(
        stable_id=f"ND{identifier:04d}", name=name, parameters=parameters,
        template_source=builder(*parameters, tag="lowertier"),
        summary=summary, category="constructive_lower_tier", priority="P2",
        conceptual_dependencies=dependencies,
    )


def _bounded(b: str, c: str, l: str, B: str, *, tag: str) -> str:
    return polynomial.prime_field_polynomial_coefficients_relation(
        B, b, c, l, tag=tag, variables=(b, c, l, B))


LOWER_TIER_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(262, "BetaPrefixInto", ("b", "c", "l", "B"), _bounded,
               "Every actual beta entry below the strict length l has a witnessed value below B. The same generic graph describes canonical polynomial coefficients when B is the modulus; empty prefixes are allowed.",
               ("Lt", "BetaAt")),
    _construct(263, "BetaPrefixEqual", ("b", "c", "d", "e", "l"),
               _contextual(polynomial.prime_field_polynomial_equal_relation),
               "Every decoded source entry at i<l also decodes in the target. Actual beta totality and functionality make this extensional prefix equality, not equality of the two code parameters.",
               ("Lt", "BetaAt")),
    _construct(264, "ArithExtend", ("F", "G", "l", "z"),
               _contextual(extension.signed_arithmetic_table_extension_relation),
               "A genuine output signed table through l preserves the represented source values at i<l and records the prescribed signed value z at l. Existence is proved by recoding both beta streams.",
               ("ArithTable", "ArithTableEqual", "ArithAt")),
    _construct(265, "MobiusTable", ("N", "M"),
               _contextual(mobius.mobius_arithmetic_table_relation),
               "A genuine table through N records zero at index zero and the independently defined Möbius value at every positive index through N. The zero-table convention does not extend Mobius to input zero.",
               ("ArithTable", "ArithAt", "Le", "Mobius")),
    _construct(266, "ArithAdd", ("F", "G", "H", "l"),
               _contextual(signed.signed_table_pointwise_add_relation),
               "Three actual signed tables and witnessed SignedAdd entries at each i<l. The unused endpoint certified by ArithTable(l,...) is not included in the prefix sum.",
               ("ArithTable", "Lt", "ArithAt", "SignedAdd")),
    _construct(267, "ArithMul", ("F", "G", "H", "l"),
               _contextual(signed.signed_table_pointwise_multiply_relation),
               "Three actual signed tables and witnessed SignedMul entries at each i<l; neither a finite-choice principle nor a product-of-sums identity is assumed.",
               ("ArithTable", "Lt", "ArithAt", "SignedMul")),
    _construct(268, "ArithScale", ("a", "F", "G", "l"),
               _contextual(signed.signed_table_scalar_multiply_relation),
               "Actual source and output tables with witnessed multiplication of every represented entry below l by the signed scalar a. Sum distributivity is a separate theorem.",
               ("ArithTable", "Lt", "ArithAt", "SignedMul")),
    _construct(269, "FpCoefficientReduction", ("p", "b", "c", "d", "e", "l"),
               _contextual(polynomial.prime_field_polynomial_normalization_relation),
               "Actual source and target coefficient entries are related by the existing canonical-residue graph at each i<l. Normalization exists even at composite nonzero moduli; field laws require their own prime hypotheses.",
               ("Lt", "BetaAt", "CanonicalModularResidue")),
    _construct(270, "FpPolyAdd", ("p", "ab", "ac", "bb", "bc", "cb", "cc", "l"),
               _contextual(polynomial.prime_field_polynomial_add_relation),
               "Witnessed canonical addition at each aligned coefficient position. Coefficients are highest-degree-first, and l is a common representation length, not a claimed degree.",
               ("Lt", "BetaAt", "FpAdd")),
    _construct(271, "FpPolyScale", ("p", "k", "ab", "ac", "bb", "bc", "l"),
               _contextual(polynomial.prime_field_polynomial_scale_relation),
               "A scalar k<p and actual canonical field products at every coefficient index i<l. The empty polynomial retains the scalar bound and denotes zero.",
               ("Lt", "BetaAt", "FpMul")),
    _construct(272, "SignedWeightedSum", ("W", "F", "l", "z"),
               _contextual(weighted.signed_weighted_sum_relation),
               "An actual signed pointwise product table of weights W and values F, followed by its real signed prefix sum at indices i<l. No linearity, divisor cancellation or inversion is assumed in this graph.",
               ("ArithMul", "SignedPrefixSum")),
    _construct(273, "DivisorMaskEntry", ("F", "n", "d", "z"),
               _contextual(divisor.divisor_mask_entry_relation),
               "A positive d with an actual quotient n=d*q keeps the genuine input value F(d); zero and nondivisors give canonical zero. The zero branch never reads or restricts F(0).",
               ("Dvd", "ArithAt")),
    _construct(274, "DivisorMask", ("F", "n", "l", "M"),
               _contextual(divisor.divisor_mask_prefix_relation),
               "An actual signed table through the inclusive bound l satisfies the independent divisor-mask entry graph at every represented index. The construction bound l is independent of n, enabling ordinary finite induction.",
               ("ArithTable", "Le", "DivisorMaskEntry")),
    _construct(275, "DivisorSum", ("F", "n", "z"),
               _contextual(divisor.signed_divisor_sum_relation),
               "For explicitly positive n, construct a genuine mask through n and take its actual signed fold over S n entries. Index zero is masked away; neither divisor cancellation nor Möbius inversion is part of the graph.",
               ("DivisorMask", "SignedPrefixSum")),
    _construct(276, "ArithPositiveEqual", ("F", "G", "N"),
               _contextual(divisor.positive_arithmetic_table_equality_relation),
               "Equality of represented values at precisely 0<d<=N. Values at zero are unrestricted, and raw codes or positive/negative representatives are not asserted equal.",
               ("Le", "ArithAt")),
    _construct(277, "FpHornerStep", ("p", "b", "c", "x", "u", "v", "i"),
               _contextual(horner.prime_field_polynomial_horner_step_relation),
               "Actual coefficient and consecutive history entries, with witnessed FpMul followed by FpAdd. This is an execution step, not an assumed equality with a natural Horner value or its residue.",
               ("BetaAt", "FpMul", "FpAdd")),
    _construct(278, "FpHornerSteps", ("p", "b", "c", "x", "l", "u", "v"),
               _contextual(horner.prime_field_polynomial_horner_steps_relation),
               "Every step i<l in the actual history performs modular multiply-and-add with coefficient a_i. Highest-degree-first order is inherited from the existing natural Horner interpretation.",
               ("Lt", "FpHornerStep")),
    _construct(279, "FpHornerTrace", ("p", "b", "c", "x", "l", "r", "u", "v"),
               _contextual(horner.prime_field_polynomial_horner_trace_relation),
               "A canonical argument x<p and a real history starting at zero, taking l actual modular Horner steps and ending at r. The argument bound remains present even for the empty zero polynomial.",
               ("Lt", "BetaAt", "FpHornerSteps")),
    _construct(280, "FpHorner", ("p", "b", "c", "x", "l", "r"),
               _contextual(horner.prime_field_polynomial_evaluation_relation),
               "Existence of a genuine finite modular Horner trace with endpoint r. Existence, value uniqueness, re-encoding and natural-residue correctness are proved separately; l is not asserted to be the polynomial degree.",
               ("FpHornerTrace",)),
)


_known = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_identifiers = {item.stable_id for item in _known.values()}
if len(_known) != 318 or len(_identifiers) != 318:
    raise ValueError("the frozen 318-definition registry changed")
if tuple(item.stable_id for item in LOWER_TIER_DEFINITIONS) != tuple(f"ND{i:04d}" for i in range(262, 281)):
    raise ValueError("the lower-tier definition identifier order changed")
for item in LOWER_TIER_DEFINITIONS:
    if item.name in _known or item.stable_id in _identifiers:
        raise ValueError("a lower-tier definition shadows an existing identity")
    if (len(item.conceptual_dependencies) != len(set(item.conceptual_dependencies))
            or not set(item.conceptual_dependencies) <= _known.keys()):
        raise ValueError("a lower-tier definition has repeated, forward, or missing dependencies")
    _known[item.name] = item
    _identifiers.add(item.stable_id)


LOWER_TIER_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(
    {item.name: item for item in LOWER_TIER_DEFINITIONS})
ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(_known)
LOWER_TIER_REGISTRIES = (
    ("finite-prefix-data", tuple(item for item in LOWER_TIER_DEFINITIONS if item.name.startswith("BetaPrefix"))),
    ("divisor-sums", tuple(item for item in LOWER_TIER_DEFINITIONS
                            if item.name in {"ArithExtend", "MobiusTable", "ArithPositiveEqual"}
                            or item.name.startswith("Divisor"))),
    ("signed-weighted-sums", tuple(item for item in LOWER_TIER_DEFINITIONS if item.name in {"ArithAdd", "ArithMul", "ArithScale", "SignedWeightedSum"})),
    ("prime-field-polynomials", tuple(item for item in LOWER_TIER_DEFINITIONS if item.name.startswith("Fp"))),
)


def definition_closure(names: tuple[str, ...]) -> tuple[DefinitionSpec, ...]:
    ordered: list[DefinitionSpec] = []
    visited: set[str] = set()
    active: set[str] = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        if name in active or name not in ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME:
            raise ValueError(f"unknown or cyclic lower-tier notation {name!r}")
        active.add(name)
        item = ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name]
        for dependency in item.conceptual_dependencies:
            visit(dependency)
        active.remove(name)
        visited.add(name)
        ordered.append(item)

    for name in names:
        visit(name)
    return tuple(ordered)


__all__ = (
    "ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME", "LOWER_TIER_DEFINITIONS",
    "LOWER_TIER_DEFINITIONS_BY_NAME", "LOWER_TIER_REGISTRIES", "definition_closure",
)
