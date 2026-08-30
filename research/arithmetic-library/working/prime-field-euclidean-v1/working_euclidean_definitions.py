"""Working-only conservative notation for representation and actual division.

The 390 inherited definitions, their identifiers and their routes are literal
predecessors. These seven aliases describe data, not proof conclusions. They
neither enroll the working theorems nor change the current public registry.
"""

from collections.abc import Mapping
from types import MappingProxyType

import constructive_polynomial_division_definitions as previous
from peano_lab.library.defined_syntax import DefinitionSpec, _definition
import prime_field_polynomial_representation_candidate as representation
import prime_field_polynomial_division_candidate as division


HISTORICAL_DEFINITIONS_BY_NAME = previous.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME


def _construct(identifier, name, parameters, builder, summary, dependencies):
    return _definition(
        stable_id=f"ND{identifier:04d}", name=name, parameters=parameters,
        template_source=builder(*parameters, tag="working_euclidean_definition", variables=parameters),
        summary=summary, category="constructive_polynomial_euclidean", priority="P2",
        conceptual_dependencies=dependencies,
    )


EUCLIDEAN_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(334, "PolynomialLeftPad", ("b", "c", "L", "t", "d", "e"),
        representation.prime_field_polynomial_left_pad_relation,
        "The target has t actual leading zero entries and then copies the L decoded source entries. It has annotated length t+L. This is left padding in highest-degree-first order, not right padding or multiplication by X. Canonical coefficients, a field modulus and formal polynomial equality are not assumptions of this graph.",
        ("Lt", "BetaAt")),
    _construct(335, "PolynomialPowerCoefficient", ("b", "c", "L", "k", "a"),
        representation.prime_field_polynomial_power_coefficient_relation,
        "The actual coefficient of X^k is decoded at the index i with i+S k=L, or is zero when L<=k. Empty representations therefore have every formal coefficient zero. This is a coefficient of a formal polynomial, not its value at a field element.",
        ("BetaAt", "Le")),
    _construct(336, "PolynomialEquivalent", ("b", "c", "L", "d", "e", "M"),
        representation.prime_field_polynomial_equivalent_relation,
        "At every natural power, every actual decoded coefficient of the two length-annotated polynomials agrees. Different representation lengths and beta encodings are allowed. This does not identify polynomials merely because their evaluations agree over a finite field; coefficient existence and equivalence laws are separate theorems.",
        ("PolynomialPowerCoefficient",)),
    _construct(337, "FpPolynomialQuotientStep", ("p", "k", "ab", "ac", "bb", "bc", "M", "qb", "qc", "i", "q"),
        division.prime_field_polynomial_quotient_step_relation,
        "Read the actual input coefficient a, compute the convolution coefficient c using only the already-built length-i quotient prefix, choose the actual field difference s with c+s=a, and record q=k*s. The supplied k need not yet be an inverse. Correctness of the resulting coefficient cancellation is a proved consequence, not a clause of this execution step.",
        ("BetaAt", "FpConvolutionCoefficient", "FpAdd", "FpMul")),
    _construct(338, "FpPolynomialQuotientPrefix", ("p", "k", "ab", "ac", "bb", "bc", "M", "qb", "qc", "N"),
        division.prime_field_polynomial_quotient_prefix_relation,
        "Each actual quotient entry at i<N satisfies the genuine triangular execution step using only its earlier quotient prefix. The empty execution is meaningful for every encoding and modulus. Construction, canonical bounds, functionality and coefficient recovery are not graph premises.",
        ("Lt", "BetaAt", "FpPolynomialQuotientStep")),
    _construct(339, "PolynomialQuotientLength", ("L", "d", "q"),
        division.prime_field_polynomial_quotient_length_relation,
        "The representation length q is zero with L<=d, or q is nonzero with q+d=L. Here the divisor has length S d. This specifies max(L-d,0) without a subtraction function and says nothing about the resulting polynomial degree or a quotient identity.",
        ("Le",)),
    _construct(340, "FpPolynomialDivisionExecution", ("p", "ab", "ac", "L", "bb", "bc", "d", "qb", "qc", "q", "rb", "rc", "R"),
        division.prime_field_polynomial_division_execution_relation,
        "Canonical input coefficients, the quotient representation length, an actual inverse of the decoded divisor head, and an actual quotient execution are recorded. An ambient length-L convolution prefix P is constructed, the actual aligned difference A-P is formed, and its leading zeros are trimmed to the remainder. Neither A=Q*B+R nor a remainder-degree bound is assumed; both require separate proof. Primality is an existence hypothesis, not a definition clause. Empty quotients and empty remainders are retained.",
        ("BetaPrefixInto", "PolynomialQuotientLength", "BetaAt", "FpInv",
         "FpPolynomialQuotientPrefix", "FpConvolutionPrefix", "FpCoefficientSubtraction", "FpPolynomialTrim")),
)


_known = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_identifiers = {item.stable_id for item in _known.values()}
if len(_known) != 390 or len(_identifiers) != 390:
    raise ValueError("the exact 390-definition predecessor registry changed")
if tuple(item.stable_id for item in EUCLIDEAN_DEFINITIONS) != tuple(f"ND{i:04d}" for i in range(334, 341)):
    raise ValueError("the seven working Euclidean identity positions changed")
for item in EUCLIDEAN_DEFINITIONS:
    if item.name in _known or item.stable_id in _identifiers:
        raise ValueError("working Euclidean notation shadows an inherited identity")
    if (len(item.conceptual_dependencies) != len(set(item.conceptual_dependencies))
            or not set(item.conceptual_dependencies) <= _known.keys()):
        raise ValueError("repeated, forward or missing Euclidean expansion dependency")
    _known[item.name] = item
    _identifiers.add(item.stable_id)

ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(_known)
EUCLIDEAN_REGISTRIES = (("polynomial-euclidean-division", EUCLIDEAN_DEFINITIONS),)


def definition_closure(names: tuple[str, ...]) -> tuple[DefinitionSpec, ...]:
    """Topological expansion prerequisites only, never theorem proof parents."""
    if type(names) is not tuple or any(type(name) is not str or not name for name in names):
        raise ValueError("definition names must be an exact tuple of nonempty text")
    ordered, visited, active = [], set(), set()

    def visit(name):
        if name in visited:
            return
        if name in active or name not in ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME:
            raise ValueError("unknown or cyclic Euclidean notation: " + name)
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


__all__ = ("EUCLIDEAN_DEFINITIONS", "EUCLIDEAN_REGISTRIES",
           "ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME", "definition_closure")
