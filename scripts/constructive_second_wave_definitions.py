"""Conservative second-wave notation, layered over immutable v26 definitions.

These are parsed first-order abbreviations, never mathematical admission.
Every historical DefinitionSpec object and identifier is preserved unchanged.
The actual proof DAG and this explanatory definition DAG remain independent.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import sys
from types import MappingProxyType
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from constructive_first_wave_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME
from peano_lab.library.defined_syntax import DefinitionSpec, _definition
from peano_lab.library.finite_sum_theorems import _sum_trace_body
from peano_lab.library.generalized_crt_full_candidate import crt_normalized_prefix_solution, crt_prefix_gcd_congruences
from peano_lab.library.hensel_prime_power_candidate import (
    canonical_horner_lift_relation, horner_root_modulo_relation, simple_horner_root_relation,
)
from peano_lab.library.signed_hensel_lifting_candidate import (
    canonical_signed_horner_lift_relation, horner_coefficient_blend_relation,
    signed_derivative_unit_relation, signed_horner_root_relation,
    signed_horner_value_derivative_relation, signed_simple_horner_root_relation,
)
from peano_lab.library.kummer_carry_candidate import _add_carry_prefix
from peano_lab.library.multinomial_kummer_candidate import (
    beta_valuation_prefix, binary_column_carry_count, carry_count_many,
    multinomial, multinomial_binomial_prefix, multinomial_carry_prefix,
)
from peano_lab.library.prime_count_chebyshev_candidate import cutoff_bit_prefix, prime_bit_prefix, prime_count
from peano_lab.library.cornacchia_candidate import (
    cornacchia_alternating_congruences, cornacchia_euclidean_run, cornacchia_root,
    cornacchia_state_at, cornacchia_state_invariant, cornacchia_trace, cornacchia_transition_at,
)
from peano_lab.library.matrix_recursive_determinant_candidate import (
    _children, _record, _step, signed_determinant_history_relation,
    signed_determinant_node_code_relation, signed_evaluated_cofactor_relation,
    signed_recursive_determinant_relation,
)
from peano_lab.library.matrix_recursive_determinant_extensional_candidate import signed_matrix_prefix_equality_relation
from peano_lab.library.matrix_rank_finite_coding_candidate import (
    finite_matrix_selector_relation, uniform_beta_prefix_box_relation,
)
from peano_lab.library.matrix_rank_selected_minors_candidate import (
    nonzero_matrix_minor_relation, nonzero_selected_minor_relation,
    signed_selected_determinant_relation, signed_selected_submatrix_relation,
)
from peano_lab.library.matrix_rank_certificate_candidate import (
    all_signed_minors_zero_relation, rectangular_matrix_rank_relation,
)
from peano_lab.library.integer_column_span_candidate import (
    integer_column_span, integer_matrix_vector_product, integer_vector_add,
    integer_vector_equal, integer_vector_negate, integer_vector_zero,
)
from peano_lab.library.hensel_simple_root_criterion_candidate import (
    signed_derivative_nonzero_relation, signed_nonsingular_horner_root_relation,
)
from peano_lab.library.finite_modular_set_candidate import (
    modular_set_intersection_relation, modular_set_member_relation,
    modular_set_pullback_relation, modular_set_subset_relation,
    modular_set_sum_cover_relation, modular_set_sum_relation, modular_set_union_relation,
)
from peano_lab.library.cauchy_davenport_candidate import (
    cauchy_davenport_bound_relation, modular_dyson_transform_relation,
    modular_translation_boundary_relation,
)
from peano_lab.library.matrix_integer_invariance_candidate import integer_matrix_entrywise_equal_relation
from peano_lab.library.matrix_lattice_data_candidate import (
    absolute_recursive_determinant_relation, identity_matrix_selector_relation,
    positive_determinant_matrix_data_relation,
)


def _construct(identifier: int, name: str, parameters: tuple[str, ...], builder: Callable[..., str], summary: str, dependencies: tuple[str, ...] = ()) -> DefinitionSpec:
    return _definition(
        stable_id=f"ND{identifier:04d}", name=name, parameters=parameters,
        template_source=builder(*parameters, tag="secondwave"), summary=summary,
        category="constructive_second_wave", priority="P2", conceptual_dependencies=dependencies,
    )


SECOND_WAVE_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(75, "BetaSumTrace", ("b", "c", "l", "n", "sb", "sc"), _sum_trace_body,
               "Actual running-sum beta trace: zero initially, each decoded input is added once, and the terminal value is n.", ("BetaAt", "Lt")),
    _construct(76, "CRTPrefixGcdCongruences", ("b", "c", "l", "m", "u", "v"), crt_prefix_gcd_congruences,
               "The two residues agree modulo the actual gcd of each decoded prefix modulus with m.", ("BetaAt", "Lt", "IsGCD", "ModEq")),
    _construct(77, "CRTNormalizedPrefixSolution", ("r", "s", "b", "c", "l", "x", "M"), crt_normalized_prefix_solution,
               "The exact prefix LCM and an actual simultaneous solution, with x<M when M is positive; the zero-LCM case retains exact congruences rather than an impossible bound.", ("CRTPrefixLCM", "CRTPrefixSolution", "Lt")),
    _construct(78, "HornerRootModulo", ("b", "c", "a", "l", "m"), horner_root_modulo_relation,
               "An actually evaluated natural polynomial vanishes modulo m at a.", ("Horner", "ModEq")),
    _construct(79, "SimpleHornerRoot", ("b", "c", "a", "l", "m", "p"), simple_horner_root_relation,
               "An actual Horner value/derivative pair is a root modulo m with derivative coprime to p.", ("HornerDerivative", "ModEq", "Coprime")),
    _construct(80, "CanonicalHornerLift", ("b", "c", "l", "m", "a", "M", "r"), canonical_horner_lift_relation,
               "A genuine polynomial root r<M at the new modulus M, in the original residue class a modulo m.", ("Lt", "ModEq", "HornerRootModulo")),
    _construct(81, "HornerCoefficientBlend", ("pb", "pc", "nb", "nc", "gb", "gc", "h", "l"), horner_coefficient_blend_relation,
               "Every actual coefficient in the new code is the positive coefficient plus h times the negative coefficient.", ("BetaAt", "Lt")),
    _construct(82, "SignedHornerValueDerivative", ("pb", "pc", "nb", "nc", "a", "l", "vp", "dp", "vn", "dn"), signed_horner_value_derivative_relation,
               "Two actual natural Horner value/derivative pairs represent the integer value vp−vn and derivative dp−dn.", ("HornerDerivative",)),
    _construct(83, "SignedDerivativeUnit", ("p", "dp", "dn"), signed_derivative_unit_relation,
               "An actual bounded inverse of dp−dn modulo p, expressed by balanced congruence.", ("Lt", "ModEq")),
    _construct(84, "SignedHornerRoot", ("pb", "pc", "nb", "nc", "a", "l", "m"), signed_horner_root_relation,
               "The actual positive and negative polynomial values agree modulo m.", ("Horner", "ModEq")),
    _construct(85, "SignedSimpleHornerRoot", ("pb", "pc", "nb", "nc", "a", "l", "m", "p"), signed_simple_horner_root_relation,
               "An actual integer-polynomial value/derivative evaluation is a root modulo m, with a witnessed derivative inverse modulo p.", ("SignedHornerValueDerivative", "ModEq", "SignedDerivativeUnit")),
    _construct(86, "CanonicalSignedHornerLift", ("pb", "pc", "nb", "nc", "l", "m", "a", "M", "r"), canonical_signed_horner_lift_relation,
               "A bounded root of the actual integer polynomial at the higher modulus, in the original residue class.", ("Lt", "ModEq", "SignedHornerRoot")),
    _construct(87, "BetaValuationPrefix", ("p", "b", "c", "vb", "vc", "l"), beta_valuation_prefix,
               "A beta table of the exact inherited bounded power valuations of the actual decoded factors; product additivity separately requires nonzero factors.", ("BetaAt", "Lt", "PowerValuation")),
    _construct(88, "MultinomialBinomialPrefix", ("b", "c", "sb", "sc", "cb", "cc", "l"), multinomial_binomial_prefix,
               "The actual factor at each position is Choose(previous total + next part, previous total).", ("BetaAt", "Lt", "Choose")),
    _construct(89, "Multinomial", ("b", "c", "l", "n", "z"), multinomial,
               "An actual list of parts with total n, a running sum, and the finite product of its iterated binomial factors; the empty product is one.", ("BetaSumTrace", "MultinomialBinomialPrefix", "Product")),
    _construct(90, "BinaryAddCarryPrefix", ("lb", "lc", "rb", "rc", "tb", "tc", "cb", "cc", "l"),
               lambda *values, tag: _add_carry_prefix(*values, tag=tag, variables=tuple(values)),
               "Actual zero/one carry rows relate the decoded left, right, and total quotient columns.", ("BetaAt", "Lt")),
    _construct(91, "BinaryColumnCarryCount", ("p", "a", "b", "e"), binary_column_carry_count,
               "Actual base-p quotient columns, their binary addition carry bits, and the witnessed total number e of those bits.", ("PowerQuotPrefix", "BinaryAddCarryPrefix", "BitCount")),
    _construct(92, "MultinomialCarryPrefix", ("p", "b", "c", "sb", "sc", "vb", "vc", "l"), multinomial_carry_prefix,
               "An actual binary column-carry count for each successive addition of a part to its previous running total.", ("BetaAt", "Lt", "BinaryColumnCarryCount")),
    _construct(93, "CarryCountMany", ("p", "b", "c", "l", "e"), carry_count_many,
               "The sum of all actual column-carry counts in sequential addition of a finite list; this definition contains no coefficient or valuation.", ("BetaSumTrace", "MultinomialCarryPrefix", "Sum")),
    _construct(94, "PrimeBitPrefix", ("b", "c", "l"), prime_bit_prefix,
               "At each index i<l the actual bit is one exactly when S i is prime, and otherwise zero.", ("BetaAt", "Lt", "Prime")),
    _construct(95, "PrimeCount", ("x", "z"), prime_count,
               "The actual finite sum of the complete primality mask through N: exactly the number of primes at most N.", ("PrimeBitPrefix", "Sum")),
    _construct(96, "BetaCutoffPrefix", ("u", "b", "c", "d", "f", "l"), cutoff_bit_prefix,
               "Actual copied source entries at indices at least u, and zero below u; applied to a primality mask this selects primes strictly greater than u.", ("BetaAt", "Lt", "Le")),
    _construct(97, "CornacchiaRoot", ("p", "z"), cornacchia_root,
               "A prime p and an actual nonzero root z<p of z²+1 divisible by p.", ("Prime", "Lt", "Dvd")),
    _construct(98, "CornacchiaAlternatingCongruences", ("p", "z", "a", "r", "u", "t"), cornacchia_alternating_congruences,
               "The two alternating signed congruences connecting adjacent actual remainders and absolute Euclidean coefficients to the root of −1.", ("ModEq",)),
    _construct(99, "CornacchiaStateInvariant", ("p", "z", "a", "r", "u", "t"), cornacchia_state_invariant,
               "A genuine rooted Euclidean state: positive decreasing remainder, positive coefficient, p=a*t+r*u, coprime adjacent remainders, and the alternating congruences.", ("CornacchiaRoot", "Lt", "Coprime", "CornacchiaAlternatingCongruences")),
    _construct(100, "CornacchiaStateAt", ("h", "e", "i", "a", "r", "u", "t", "q"), cornacchia_state_at,
               "Decode the actual packed five-field state, including its Euclidean quotient, from a beta history.", ("BetaAt",)),
    _construct(101, "CornacchiaTransitionAt", ("p", "h", "e", "i"), cornacchia_transition_at,
               "One actual quotient/remainder and coefficient update, with strict decrease and the pre-stopping square guard.", ("CornacchiaStateAt", "Lt")),
    _construct(102, "CornacchiaEuclideanRun", ("p", "a", "r", "u", "t", "R", "T", "h", "e", "l"), cornacchia_euclidean_run,
               "A complete finite reverse-chronological Euclidean history from the supplied state to its first positive remainder with square below p; terminal quotient zero.", ("CornacchiaStateAt", "CornacchiaTransitionAt", "Lt")),
    _construct(103, "CornacchiaTrace", ("p", "z", "R", "T", "h", "e", "l"), cornacchia_trace,
               "A root of −1 and the actual complete Cornacchia execution from (p,z,0,1); the representation equation p=R²+T² is a proved conclusion, not a trace-definition premise.", ("CornacchiaRoot", "CornacchiaEuclideanRun")),
    _construct(104, "SignedDeterminantNodeCode", ("z", "d", "pb", "pc", "nb", "nc", "p", "n"), signed_determinant_node_code_relation,
               "An injective packed dimension/matrix/value record, with existential sharing of the actual intermediate pairing codes."),
    _construct(105, "SignedDeterminantNodeAt", ("b", "c", "i", "d", "pb", "pc", "nb", "nc", "p", "n"),
               lambda *values, tag: _record(*values, tag),
               "An actual determinant-node record decoded from a beta history.", ("SignedDeterminantNodeCode", "BetaAt")),
    _construct(106, "SignedDeterminantChildPrefix", ("b", "c", "limit", "pb", "pc", "nb", "nc", "q", "eb", "ec", "fb", "fc", "l"),
               lambda *values, tag: _children(*values, tag),
               "Every selected column has a genuine smaller cofactor matrix, an evaluating node strictly earlier than the parent, and its actual two determinant components.", ("Lt", "SignedDeterminantNodeAt", "SignedMatrixMinor", "BetaAt")),
    _construct(107, "SignedDeterminantLocalStep", ("b", "c", "i", "d", "pb", "pc", "nb", "nc", "p", "n"),
               lambda *values, tag: _step(*values, tag),
               "Either the exact empty value (1,0), or a complete genuine cofactor-child family and its parity-correct first-row alternating fold.", ("SignedDeterminantChildPrefix", "SignedAlternatingCofactorFold")),
    _construct(108, "SignedDeterminantHistory", ("b", "c", "l"), signed_determinant_history_relation,
               "Every node in an actual finite history satisfies its genuine strict-child determinant rule; cyclic or supplied-value evaluations are excluded.", ("Lt", "SignedDeterminantNodeAt", "SignedDeterminantLocalStep")),
    _construct(109, "SignedRecursiveDeterminant", ("pb", "pc", "nb", "nc", "d", "p", "n"), signed_recursive_determinant_relation,
               "An actual evaluating root in a finite cofactor DAG for an arbitrary-dimensional signed matrix; its mathematical value is p−n.", ("SignedDeterminantHistory", "Lt", "SignedDeterminantNodeAt")),
    _construct(110, "SignedEvaluatedCofactors", ("pb", "pc", "nb", "nc", "q", "eb", "ec", "fb", "fc"), signed_evaluated_cofactor_relation,
               "Actual determinants of every genuine first-row minor are stored in the cofactor streams, not assumed as unrelated values.", ("SignedMatrixMinor", "SignedRecursiveDeterminant", "BetaAt", "Lt")),
    _construct(111, "SignedMatrixPrefixEquality", ("pb", "pc", "nb", "nc", "qb", "qc", "rb", "rc", "d"), signed_matrix_prefix_equality_relation,
               "Pointwise equality of both actual component streams of two square matrices; this is stronger than equality only of their signed differences.", ("BetaAt", "Lt")),
    _construct(112, "UniformBetaPrefixBox", ("c", "T", "l", "B"), uniform_beta_prefix_box_relation,
               "One fixed scale c and positive finite code bound T recode every actual length-l prefix with values below B; completeness is part of the relation.", ("BetaAt", "Lt")),
    _construct(113, "FiniteMatrixSelector", ("b", "c", "l", "B"), finite_matrix_selector_relation,
               "Actual beta-decoded matrix coordinates are all below B and pairwise distinct; the list may be empty.", ("BetaAt", "Lt")),
    _construct(114, "SignedSelectedSubmatrix", ("pb", "pc", "nb", "nc", "w", "rb", "rc", "cb", "cc", "q", "ub", "uc", "vb", "vc"), signed_selected_submatrix_relation,
               "Every entry of both components of the q-by-q output is the actual row-major parent entry selected by the two coordinate streams.", ("BetaAt", "Lt")),
    _construct(115, "SignedSelectedDeterminant", ("pb", "pc", "nb", "nc", "w", "rb", "rc", "cb", "cc", "q", "p", "n"), signed_selected_determinant_relation,
               "An actual selected submatrix and its unrestricted recursive determinant, not a supplied table of purported minor values.", ("SignedSelectedSubmatrix", "SignedRecursiveDeterminant")),
    _construct(116, "NonzeroSelectedMinor", ("pb", "pc", "nb", "nc", "r", "w", "q", "rb", "rc", "cb", "cc"), nonzero_selected_minor_relation,
               "Two distinct in-range coordinate selectors and an actual selected determinant whose positive and negative components differ.", ("FiniteMatrixSelector", "SignedSelectedDeterminant")),
    _construct(117, "NonzeroMatrixMinor", ("pb", "pc", "nb", "nc", "r", "w", "q"), nonzero_matrix_minor_relation,
               "There exist genuine bounded injective row and column selectors witnessing a nonzero minor of order q.", ("NonzeroSelectedMinor",)),
    _construct(118, "AllSignedMinorsZero", ("pb", "pc", "nb", "nc", "r", "w", "q"), all_signed_minors_zero_relation,
               "Every genuine selected minor of order q has zero integer determinant, for all actual selector encodings and determinant evaluations.", ("FiniteMatrixSelector", "SignedSelectedDeterminant")),
    _construct(119, "RectangularMatrixRank", ("pb", "pc", "nb", "nc", "r", "w", "rank"), rectangular_matrix_rank_relation,
               "A rank bounded by both dimensions, an actual nonzero minor of that order, and vanishing of every higher-order minor; the empty determinant supplies rank zero.", ("Le", "Lt", "NonzeroMatrixMinor", "AllSignedMinorsZero")),
    _construct(120, "IntegerVectorEqual", ("ab", "ac", "db", "dc", "eb", "ec", "fb", "fc", "l"), integer_vector_equal,
               "Coordinatewise equality of signed differences by balanced equality; different positive/negative representations may denote the same integer vector.", ("BetaAt", "Lt")),
    _construct(121, "IntegerVectorZero", ("ab", "ac", "db", "dc", "l"), integer_vector_zero,
               "Every actual positive component equals its negative component, so each represented integer is zero.", ("BetaAt", "Lt")),
    _construct(122, "IntegerVectorAdd", ("ab", "ac", "db", "dc", "eb", "ec", "fb", "fc", "pb", "pc", "nb", "nc", "l"), integer_vector_add,
               "Actual coordinatewise addition of represented signed integers, expressed without subtraction or a preferred pair representation.", ("BetaAt", "Lt")),
    _construct(123, "IntegerVectorNegate", ("ab", "ac", "db", "dc", "pb", "pc", "nb", "nc", "l"), integer_vector_negate,
               "The target equals the vector obtained by swapping the two source components, in integer-difference equality.", ("IntegerVectorEqual",)),
    _construct(124, "IntegerMatrixVectorProduct", ("ab", "ac", "db", "dc", "eb", "ec", "fb", "fc", "w", "r", "pb", "pc", "nb", "nc"), integer_matrix_vector_product,
               "An actual coded signed matrix product of output width one, compared to the requested output by integer-vector equality.", ("SignedMatrixProduct", "IntegerVectorEqual")),
    _construct(125, "IntegerColumnSpan", ("ab", "ac", "db", "dc", "w", "r", "pb", "pc", "nb", "nc"), integer_column_span,
               "Actual finite signed coefficient codes witness the output as an integer linear combination of the matrix columns; no independence, index, or covolume is assumed.", ("IntegerMatrixVectorProduct",)),
    _construct(126, "SignedDerivativeNonzero", ("p", "dp", "dn"), signed_derivative_nonzero_relation,
               "The actual signed derivative dp−dn is not congruent to zero modulo p; no inverse is supplied.", ("ModEq",)),
    _construct(127, "SignedNonsingularHornerRoot", ("pb", "pc", "nb", "nc", "a", "l", "m", "p"), signed_nonsingular_horner_root_relation,
               "An actual integer-polynomial root modulo m whose actual signed derivative is nonzero modulo p; the prime-field inverse is a theorem conclusion.", ("SignedHornerValueDerivative", "ModEq", "SignedDerivativeNonzero")),
    _construct(128, "ModularSetMember", ("b", "c", "p", "x"), modular_set_member_relation,
               "The actual characteristic bit at the canonical residue x<p is one. Complete finite sets and their cardinalities reuse the existing BitCount identity.", ("Lt", "BetaAt")),
    _construct(129, "ModularSetSubset", ("b", "c", "d", "e", "p"), modular_set_subset_relation,
               "At every canonical residue, a one in the left characteristic code implies a one in the right code.", ("Lt", "BetaAt")),
    _construct(130, "ModularSetUnion", ("b", "c", "d", "e", "u", "v", "p"), modular_set_union_relation,
               "The output characteristic bit is one exactly when at least one actual operand bit is one.", ("Lt", "BetaAt")),
    _construct(131, "ModularSetIntersection", ("b", "c", "d", "e", "u", "v", "p"), modular_set_intersection_relation,
               "The output characteristic bit is one exactly when both actual operand bits are one.", ("Lt", "BetaAt")),
    _construct(132, "ModularSetPullback", ("b", "c", "d", "e", "p", "t"), modular_set_pullback_relation,
               "The target is the actual translated pullback A−t: its bit at i equals A's bit at the canonical residue of i+t.", ("Lt", "ModEq", "BetaAt")),
    _construct(133, "ModularSetSumCover", ("b", "c", "d", "e", "u", "v", "p"), modular_set_sum_cover_relation,
               "Every canonical modular sum of an actual left member and right member belongs to the given output set; extra output members are allowed.", ("Lt", "BetaAt", "ModEq")),
    _construct(134, "ModularSetSum", ("b", "c", "d", "e", "u", "v", "p"), modular_set_sum_relation,
               "The output consists of all and only the actual modular sums, with genuine operand witnesses for each output member.", ("Lt", "BetaAt", "ModularSetMember", "ModEq")),
    _construct(135, "ModularTranslationBoundary", ("b", "c", "p", "d", "a", "r"), modular_translation_boundary_relation,
               "An actual in-set residue a and canonical shifted residue r≡a+d outside the set witness a translation boundary.", ("ModularSetMember", "Lt", "ModEq", "BetaAt")),
    _construct(136, "ModularDysonTransform", ("b", "c", "d", "e", "ub", "uc", "vb", "vc", "p", "t"), modular_dyson_transform_relation,
               "The actual transformed sets are A∪(B+t) and B∩(A−t). Preservation of total cardinality and strict descent are proved theorems, not definition premises.", ("Lt", "BetaAt", "ModularSetMember", "ModEq")),
    _construct(137, "CauchyDavenportBound", ("p", "k", "l", "m"), cauchy_davenport_bound_relation,
               "The exact subtraction-free sharp bound: p≤m or k+l≤m+1, equivalent to m≥min(p,k+l−1) for positive input cardinalities.", ("Le",)),
    _construct(138, "IntegerMatrixEntrywiseEqual", ("ab", "ac", "bb", "bc", "eb", "ec", "fb", "fc", "r", "w"), integer_matrix_entrywise_equal_relation,
               "Genuine signed-integer equality at every actual row-major entry of two r-by-w matrices, reusing integer-vector equality at length r*w.", ("IntegerVectorEqual",)),
    _construct(139, "AbsoluteRecursiveDeterminant", ("ab", "ac", "bb", "bc", "d", "D"), absolute_recursive_determinant_relation,
               "An actual recursive signed determinant and its natural absolute difference D, with either sign orientation witnessed.", ("SignedRecursiveDeterminant",)),
    _construct(140, "PositiveDeterminantMatrixData", ("ab", "ac", "bb", "bc", "d", "D"), positive_determinant_matrix_data_relation,
               "A positive-dimensional integral square matrix with actual positive absolute determinant D. Full rank is a proved consequence; lattice index or geometric covolume equality is not asserted.", ("AbsoluteRecursiveDeterminant",)),
    _construct(141, "IdentityMatrixSelector", ("b", "c", "l"), identity_matrix_selector_relation,
               "The actual beta-decoded coordinate list 0,1,…,l−1; its boundedness, injectivity, and full-matrix selection are proved separately.", ("Lt", "BetaAt")),
)


_known = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_identifiers = {item.stable_id for item in _known.values()}
if len(_known) != 131 or len(_identifiers) != 131:
    raise ValueError("the immutable Alpha-v26 definition registry changed")
if tuple(item.stable_id for item in SECOND_WAVE_DEFINITIONS) != tuple(f"ND{index:04d}" for index in range(75,142)):
    raise ValueError("second-wave definition identifiers changed")
for item in SECOND_WAVE_DEFINITIONS:
    if item.name in _known or item.stable_id in _identifiers:
        raise ValueError("a second-wave definition overwrites a historical identity")
    if len(item.conceptual_dependencies) != len(set(item.conceptual_dependencies)) or not set(item.conceptual_dependencies) <= _known.keys():
        raise ValueError("second-wave definitions have repeated, forward, or missing dependency edges")
    _known[item.name] = item
    _identifiers.add(item.stable_id)

SECOND_WAVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType({item.name:item for item in SECOND_WAVE_DEFINITIONS})
ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(_known)
SECOND_WAVE_REGISTRIES = (
    ("multinomial-kummer", tuple(item for item in SECOND_WAVE_DEFINITIONS if item.stable_id == "ND0075" or 87 <= int(item.stable_id[2:]) <= 93)),
    ("generalized-crt", SECOND_WAVE_DEFINITIONS[1:3]),
    ("hensel-lifting", SECOND_WAVE_DEFINITIONS[3:12] + SECOND_WAVE_DEFINITIONS[51:53]),
    ("prime-count-chebyshev", SECOND_WAVE_DEFINITIONS[19:22]),
    ("cornacchia", SECOND_WAVE_DEFINITIONS[22:29]),
    ("integer-linear-algebra", SECOND_WAVE_DEFINITIONS[29:51] + SECOND_WAVE_DEFINITIONS[63:67]),
    ("cauchy-davenport", SECOND_WAVE_DEFINITIONS[53:63]),
)


def definition_closure(names: tuple[str, ...]) -> tuple[DefinitionSpec, ...]:
    """Only semantically relevant notation and its exact acyclic prerequisites."""
    ordered: list[DefinitionSpec] = []
    visited: set[str] = set()
    active: set[str] = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        if name in active or name not in ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME:
            raise ValueError(f"unknown or cyclic second-wave notation {name!r}")
        active.add(name)
        definition = ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name]
        for dependency in definition.conceptual_dependencies:
            visit(dependency)
        active.remove(name)
        visited.add(name)
        ordered.append(definition)

    for name in names:
        visit(name)
    return tuple(ordered)


__all__ = (
    "ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME", "SECOND_WAVE_DEFINITIONS",
    "SECOND_WAVE_DEFINITIONS_BY_NAME", "SECOND_WAVE_REGISTRIES", "definition_closure",
)
