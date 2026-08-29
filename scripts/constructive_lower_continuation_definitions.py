"""Conservative notation for involutions, finite Fubini and polynomial products.

All 337 historical identities remain unchanged. These graphs describe real
finite data, not the identities to be proved. No notation or DAG edge grants
proof authority or silently closes either G007 or G091.
"""

from collections.abc import Mapping
from types import MappingProxyType

from constructive_lower_tier_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME,
)
from constructive_bottom_layer_definitions import _contextual
from peano_lab.library.defined_syntax import DefinitionSpec, _definition
from peano_lab.library import divisor_involution_candidate as divisor
from peano_lab.library import mobius_divisor_cancellation_candidate as toggle
from peano_lab.library import signed_rectangular_slice_candidate as slices
from peano_lab.library import signed_rectangular_sums_candidate as rectangles
from peano_lab.library import prime_field_polynomial_convolution_candidate as products
from peano_lab.library import prime_field_polynomial_degree_candidate as degrees


def _construct(identifier, name, parameters, builder, summary, dependencies):
    return _definition(stable_id=f"ND{identifier:04d}", name=name, parameters=parameters,
        template_source=_contextual(builder)(*parameters, tag="lowercontinuation"),
        summary=summary, category="constructive_lower_continuation", priority="P2",
        conceptual_dependencies=dependencies)


CONTINUATION_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(281, "DivisorComplement", ("n", "d", "q"), divisor.positive_divisor_complement_relation,
        "At a positive divisor d, a genuine product witness n=d*q specifies the complementary quotient. Zero and nondivisors are fixed. For n>0, totality, reversibility and bounds are proved separately, not assumed in this graph.", ("Dvd",)),
    _construct(282, "DivisorComplementPrefix", ("n", "b", "c", "l"), divisor.divisor_complement_prefix_relation,
        "An actual beta prefix records complementary-divisor outputs at every i<l. For n>0 such prefixes exist at every length; the prefix of length S n is proved a permutation.",
        ("Lt", "BetaAt", "DivisorComplement")),
    _construct(283, "PrimeFactorToggle", ("p", "d", "e"), toggle.prime_factor_toggle_relation,
        "Add a fresh factor p, remove a single factor p with p-free quotient, or fix a multiple of p squared. The graph contains no Möbius sign or cancellation hypothesis.", ("Dvd",)),
    _construct(284, "DivisorPrimeToggle", ("n", "p", "d", "e"), toggle.divisor_prime_toggle_relation,
        "Apply the actual prime-factor toggle at positive divisors of n and fix zero and nondivisors. Closure in the divisor set and involutivity are proved under Prime(p), n>0 and Dvd(p,n).",
        ("Dvd", "PrimeFactorToggle")),
    _construct(285, "DivisorPrimeTogglePrefix", ("n", "p", "b", "c", "l"), toggle.divisor_prime_toggle_prefix_relation,
        "A real finite beta map witnesses each divisor-prime-toggle output on i<l. No finite-choice, permutation or sum identity is assumed.",
        ("Lt", "BetaAt", "DivisorPrimeToggle")),
    _construct(286, "ArithNegate", ("F", "G", "l"), toggle.signed_arithmetic_table_negation_relation,
        "Every pair of actual represented signed values at the same i<l are opposite. Genuine table validity is a separate hypothesis; arbitrary codes and component streams need not agree.",
        ("Lt", "ArithAt", "SignedNegate")),
    _construct(287, "ArithSlice", ("F", "G", "o", "s", "l"), slices.signed_rectangular_slice_relation,
        "Actual signed tables with witnessed values G(i)=F(o+s*i) for i<l. The output is constructed by real beta-stream recoding; its separately certified endpoint is unused.",
        ("ArithTable", "Lt", "ArithAt")),
    _construct(288, "SignedSliceSum", ("F", "o", "s", "l", "z"), slices.signed_rectangular_slice_sum_relation,
        "An actually constructed affine slice followed by its genuine signed prefix sum. Both zero length and zero stride are meaningful; no sum oracle is part of the graph.",
        ("ArithSlice", "SignedPrefixSum")),
    _construct(289, "ArithRowSums", ("F", "R", "o", "s", "t", "m", "n"), rectangles.signed_rectangular_row_sums_relation,
        "An actual row table R contains, at i<m, the signed sum of the n entries F((o+s*i)+t*j). Source and row-table packings are explicit, including empty dimensions.",
        ("ArithTable", "Lt", "ArithAt", "SignedSliceSum")),
    _construct(290, "SignedRectangularSum", ("F", "o", "s", "t", "m", "n", "z"), rectangles.signed_rectangular_sum_relation,
        "Construct an actual row-sum table and take its actual m-entry signed sum. Equality after swapping strides and dimensions is the independently proved finite Fubini theorem.",
        ("ArithRowSums", "SignedPrefixSum")),
    _construct(291, "BetaZeroExtend", ("b", "c", "L", "i", "a"), products.prime_field_polynomial_zero_extended_entry_relation,
        "Decode the genuine beta entry when i<L and return zero when L<=i. This explicitly length-annotated zero extension imposes no false condition on raw beta values beyond the represented prefix.",
        ("Lt", "Le", "BetaAt")),
    _construct(292, "PolynomialDiagonalTerm", ("ab", "ac", "L", "bb", "bc", "M", "i", "j", "t"), products.prime_field_polynomial_diagonal_term_relation,
        "Witness k with j+k=i and multiply the two actual zero-extended coefficients. These are natural products in a highest-degree-first antidiagonal, before reduction modulo the field prime.",
        ("BetaZeroExtend",)),
    _construct(293, "PolynomialDiagonalPrefix", ("ab", "ac", "L", "bb", "bc", "M", "i", "db", "dc", "l"), products.prime_field_polynomial_diagonal_prefix_relation,
        "A real beta table contains the actual antidiagonal products for j<l. The full window l=S i is constructed, so every complementary index is natural.",
        ("Lt", "BetaAt", "PolynomialDiagonalTerm")),
    _construct(294, "FpConvolutionCoefficient", ("p", "ab", "ac", "L", "bb", "bc", "M", "i", "r"), products.prime_field_polynomial_convolution_coefficient_relation,
        "Build the S i antidiagonal terms, take their actual natural Sum, then take its canonical residue r modulo p. No evaluation-product identity or degree assertion is assumed.",
        ("PolynomialDiagonalPrefix", "Sum", "CanonicalModularResidue")),
    _construct(295, "FpConvolutionPrefix", ("p", "ab", "ac", "L", "bb", "bc", "M", "cb", "cc", "l"), products.prime_field_polynomial_convolution_prefix_relation,
        "Every output coefficient at i<l is the independently defined actual antidiagonal sum residue. The finite output beta table is constructed rather than postulated.",
        ("Lt", "BetaAt", "FpConvolutionCoefficient")),
    _construct(296, "PolynomialProductLength", ("L", "M", "N"), products.prime_field_polynomial_product_length_relation,
        "The proper product representation is empty if either input is empty; otherwise L+M=S N. This is a representation-length relation, not a claim that a possibly zero-leading polynomial has that degree.", ()),
    _construct(297, "FpPolyProduct", ("p", "ab", "ac", "L", "bb", "bc", "M", "cb", "cc", "N"), products.prime_field_polynomial_convolution_relation,
        "Canonical input prefixes, the proper product length, and a genuine convolution output prefix. Terms beyond this length vanish by a separate support theorem, not by assuming the discarded tail is zero.",
        ("BetaPrefixInto", "PolynomialProductLength", "FpConvolutionPrefix")),
    _construct(298, "FpRepresentedDegree", ("p", "b", "c", "L", "d"), degrees.prime_field_polynomial_represented_degree_relation,
        "A length-annotated canonical coefficient prefix has L=S d and an actually decoded nonzero leading coefficient. This does not assign degree to zero or normalize arbitrary leading-zero representations.",
        ("BetaPrefixInto", "BetaAt")),
    _construct(299, "MobiusPositiveValues", ("N", "F"), toggle.mobius_positive_table_values_relation,
        "Every actual positive entry through N agrees with the independently defined Möbius function. Table validity is separate and F(0) is unrestricted; the historical MobiusTable zero convention remains unchanged.",
        ("Le", "ArithAt", "Mobius")),
)


_known = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_identifiers = {item.stable_id for item in _known.values()}
if len(_known) != 337 or len(_identifiers) != 337:
    raise ValueError("the frozen 337-definition registry changed")
if tuple(item.stable_id for item in CONTINUATION_DEFINITIONS) != tuple(f"ND{i:04d}" for i in range(281, 300)):
    raise ValueError("continuation definition identifier order changed")
for item in CONTINUATION_DEFINITIONS:
    if item.name in _known or item.stable_id in _identifiers:
        raise ValueError("continuation notation shadows an existing identity")
    if (len(item.conceptual_dependencies) != len(set(item.conceptual_dependencies))
            or not set(item.conceptual_dependencies) <= _known.keys()):
        raise ValueError("repeated, forward or missing continuation definition dependency")
    _known[item.name] = item
    _identifiers.add(item.stable_id)

ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(_known)
CONTINUATION_REGISTRIES = (
    ("divisor-involutions", CONTINUATION_DEFINITIONS[:2]),
    ("mobius-divisor-cancellation", CONTINUATION_DEFINITIONS[2:6] + CONTINUATION_DEFINITIONS[18:]),
    ("rectangular-sums", CONTINUATION_DEFINITIONS[6:10]),
    ("polynomial-products", CONTINUATION_DEFINITIONS[10:18]),
)


def definition_closure(names: tuple[str, ...]) -> tuple[DefinitionSpec, ...]:
    ordered, visited, active = [], set(), set()
    def visit(name):
        if name in visited:
            return
        if name in active or name not in ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME:
            raise ValueError("unknown or cyclic continuation notation: " + name)
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
