"""Ten exact conservative polynomial identities for the v34 current reader.

The397 inherited definition objects remain identical; all407 meanings and884
expansion arrows match the reviewed working graph. No definition proves a law.
Only canonical mathematical sources are imported, never working controllers.
"""
from types import MappingProxyType
import constructive_polynomial_euclidean_definitions as previous
from peano_lab.library.defined_syntax import DefinitionSpec, _definition
from peano_lab.library import prime_field_polynomial_shift_candidate as shift_candidate
from peano_lab.library import prime_field_polynomial_divisibility_candidate as divisibility
from peano_lab.library import prime_field_polynomial_alignment_candidate as alignment
from peano_lab.library import prime_field_polynomial_aligned_add_candidate as aligned_add
from peano_lab.library import prime_field_polynomial_euclidean_transport_candidate as _transport
from peano_lab.library import prime_field_polynomial_bezout_backward_candidate as bezout
from peano_lab.library.prime_field_polynomial_monic_candidate import _monic

HISTORICAL_DEFINITIONS_BY_NAME = previous.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME

PARAMETERS = ("b", "c", "L", "d", "e")

SHIFT = _definition(
    stable_id="ND0341", name="PolynomialShift", parameters=PARAMETERS,
    template_source=shift_candidate.prime_field_polynomial_shift_relation(
        *PARAMETERS, tag="working_shift_definition", variables=PARAMETERS),
    summary="Copy the actual length-L decoded prefix and append a genuine zero at index L. "
            "The target length is S L. This is multiplication by X, not harmless leading-zero padding. "
            "Primality, canonical bounds, covariance and formal equivalence are not clauses of this graph. "
            "Raw beta codes and later entries remain unrestricted.",
    category="constructive_polynomial_shift", priority="P2",
    conceptual_dependencies=("BetaPrefixEqual", "BetaAt"),
)

PARAMETERS = ('p', 'db', 'dc', 'D', 'ab', 'ac', 'L')

RIGHT_DIVIDES = _definition(
    stable_id='ND0342', name='FpPolynomialRightDivides', parameters=PARAMETERS,
    template_source=divisibility.prime_field_polynomial_right_divides_relation(
        *PARAMETERS, tag='working_right_divides_definition', variables=PARAMETERS),
    summary='The target A is canonical and there are actual quotient and product triples Q,P '
            'such that Q*D=P and P is formally coefficient-equivalent to A. D is the right '
            'factor. Product lengths and beta encodings are independent; field evaluations '
            'or raw code equality do not replace formal equivalence. Primality, gcd existence '
            'and Bezout witnesses are not definition clauses.',
    category='constructive_polynomial_divisibility', priority='P2',
    conceptual_dependencies=('BetaPrefixInto', 'FpPolyProduct', 'PolynomialEquivalent'),
)

COMMON_PARAMETERS = ('ab', 'ac', 'L', 'bb', 'bc', 'M', 'ub', 'uc', 'vb', 'vc', 'K')

ALIGNED_PARAMETERS = ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'M', 'rb', 'rc', 'N')

def _aligned_definition(identifier, name, parameters, builder, summary, parents):
    return _definition(
        stable_id=identifier, name=name, parameters=parameters,
        template_source=builder(*parameters, tag='working_aligned_definition', variables=parameters),
        summary=summary, category='constructive_polynomial_alignment', priority='P2',
        conceptual_dependencies=parents,
    )

COMMON_REPRESENTATIVES = _aligned_definition(
    'ND0343', 'CommonRepresentatives', COMMON_PARAMETERS,
    alignment.prime_field_polynomial_common_representatives_relation,
    'A_L is formally coefficient-equivalent to U_K and B_M to V_K. The two '
    'equivalences form one literal grouped conjunction. No coefficient bound, '
    'prime modulus, upper bound on the original lengths, existence witness, '
    'raw-code equality or field-evaluation equality is a clause. Legitimate '
    'shorter representatives and independent beta encodings are allowed.',
    ('PolynomialEquivalent',),
)

ALIGNED_ADD = _aligned_definition(
    'ND0344', 'FpPolynomialAlignedAdd', ALIGNED_PARAMETERS,
    aligned_add.prime_field_polynomial_aligned_add_relation,
    'All three originals A_L, B_M and R_N have canonical coefficients. There '
    'exist actual common-length representatives U_K,V_K and a true coefficient '
    'sum T_K, with CommonRepresentatives(A,B,U,V,K), FpPolyAdd(U,V,T,K), and '
    'formal coefficient equivalence T_K~R_N. Primality, existence, uniqueness '
    'and algebraic laws are separate theorem statements, not definition clauses.',
    ('BetaPrefixInto', 'CommonRepresentatives', 'FpPolyAdd', 'PolynomialEquivalent'),
)

ALIGNED_SUBTRACT = _aligned_definition(
    'ND0345', 'FpPolynomialAlignedSubtract', ALIGNED_PARAMETERS,
    aligned_add.prime_field_polynomial_aligned_subtract_relation,
    'The literal argument permutation FpPolynomialAlignedAdd(p,B_M,R_N,A_L): '
    'B+R=A with all three original coefficient guards and actual sum witnesses. '
    'This is not an additional subtraction oracle or a proved subtraction law.',
    ('FpPolynomialAlignedAdd',),
)

COMMON_PARAMETERS = ('p', 'db', 'dc', 'D', 'ab', 'ac', 'L', 'bb', 'bc', 'M')

BEZOUT_PARAMETERS = ('p', 'ab', 'ac', 'A', 'bb', 'bc', 'B', 'gb', 'gc', 'G',
                     'ub', 'uc', 'U', 'vb', 'vc', 'V')

def _euclidean_definition(identifier, name, parameters, builder, summary, parents):
    return _definition(
        stable_id=identifier, name=name, parameters=parameters,
        template_source=builder(*parameters, tag='working_euclidean_definition', variables=parameters),
        summary=summary, category='constructive_polynomial_euclidean_transport', priority='P2',
        conceptual_dependencies=parents,
    )

COMMON_RIGHT_DIVISOR = _euclidean_definition(
    'ND0346', 'FpPolynomialCommonRightDivisor', COMMON_PARAMETERS,
    _transport.prime_field_polynomial_common_right_divisor_relation,
    'D is an actual right divisor of both canonical targets A and B, using two '
    'independent quotient/product witness sets. The two RightDivides clauses '
    'form one literal conjunction. Existence of a common divisor, greatestness, '
    'primality and a gcd theorem are not definition clauses.',
    ('FpPolynomialRightDivides',),
)

BEZOUT_REPRESENTATION = _euclidean_definition(
    'ND0347', 'FpPolynomialBezoutRepresentation', BEZOUT_PARAMETERS,
    bezout.prime_field_polynomial_bezout_representation_relation,
    'There are actual proper products U*A=P and V*B=Q, and an actual aligned '
    'sum P+Q=G. Codes and all five original representation lengths remain '
    'independent. This is representation data, not a Bezout-existence theorem, '
    'a gcd or greatestness result, evaluation equality, or equality of raw codes.',
    ('FpPolyProduct', 'FpPolynomialAlignedAdd'),
)

def _normal(p, gb, gc, G, tag):
    return f'({G})=0 \\/ (' + _monic(p, gb, gc, G, tag + '_monic') + ')'

def _gcd(p, gb, gc, G, ab, ac, L, bb, bc, M, tag):
    db, dc, D = (tag + '_' + name for name in ('db', 'dc', 'D'))
    common = _transport._common_divisor
    greatest = f'forall {db} {dc} {D}. (' + common(
        p, db, dc, D, ab, ac, L, bb, bc, M, tag + '_candidate') + ') -> (' + _transport._right_divides(
        p, db, dc, D, gb, gc, G, tag + '_greatest') + ')'
    return '(' + common(p, gb, gc, G, ab, ac, L, bb, bc, M, tag + '_common') + ') /\\ (' + greatest + ')'

NORMAL_PARAMETERS = ('p', 'gb', 'gc', 'G')

GCD_PARAMETERS = (*NORMAL_PARAMETERS, 'ab', 'ac', 'L', 'bb', 'bc', 'M')

def _gcd_definition(identifier, name, parameters, source, parents, summary):
    return _definition(stable_id=identifier, name=name, parameters=parameters,
        template_source=source, conceptual_dependencies=parents, summary=summary,
        category='constructive_polynomial_gcd', priority='P2')

ZERO_OR_MONIC = _gcd_definition('ND0348', 'FpPolynomialZeroOrMonic', NORMAL_PARAMETERS,
    _normal(*NORMAL_PARAMETERS, 'gcd_definition_normal'), ('FpMonic',),
    'The representation is empty or is an actual nonempty canonical monic prefix. '
    'No primality or existence claim is included; empty codes are unrestricted.')

RIGHT_GCD = _gcd_definition('ND0349', 'FpPolynomialRightGcd', GCD_PARAMETERS,
    _gcd(*GCD_PARAMETERS, 'gcd_definition_greatest'),
    ('FpPolynomialCommonRightDivisor', 'FpPolynomialRightDivides'),
    'G is a common right divisor, and every common right divisor D right-divides G. '
    'This universally quantified property does not assert existence or uniqueness.')

NORMALIZED_GCD = _gcd_definition('ND0350', 'FpPolynomialNormalizedGcd', GCD_PARAMETERS,
    '(' + _normal(*NORMAL_PARAMETERS, 'gcd_definition_normalized_normal') + ') /\\ ('
    + _gcd(*GCD_PARAMETERS, 'gcd_definition_normalized_greatest') + ')',
    ('FpPolynomialZeroOrMonic', 'FpPolynomialRightGcd'),
    'Literal conjunction of zero-or-monic and right-gcd; no Bezout coefficients '
    'or polynomial algorithm are built into this property.')

GCD_DEFINITIONS = (SHIFT, RIGHT_DIVIDES, COMMON_REPRESENTATIVES, ALIGNED_ADD,
    ALIGNED_SUBTRACT, COMMON_RIGHT_DIVISOR, BEZOUT_REPRESENTATION,
    ZERO_OR_MONIC, RIGHT_GCD, NORMALIZED_GCD)
_known = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_identifiers = {item.stable_id for item in _known.values()}
if len(_known) != 397 or len(_identifiers) != 397:
    raise ValueError("the exact397-definition predecessor changed")
if tuple(item.stable_id for item in GCD_DEFINITIONS) != tuple(f"ND{i:04d}" for i in range(341,351)):
    raise ValueError("the ten reviewed identity positions changed")
for item in GCD_DEFINITIONS:
    if item.name in _known or item.stable_id in _identifiers:
        raise ValueError("a new identity shadows its predecessor")
    if (len(set(item.conceptual_dependencies)) != len(item.conceptual_dependencies)
            or not set(item.conceptual_dependencies) <= _known.keys()):
        raise ValueError("missing, repeated or forward definition dependency")
    _known[item.name] = item
    _identifiers.add(item.stable_id)
ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME = MappingProxyType(_known)
GCD_REGISTRIES = (("polynomial-gcd-bezout", GCD_DEFINITIONS),)

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
