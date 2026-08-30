"""Seven conservative polynomial-operation graphs over 383 inherited identities.

These are exact abbreviations for actual coefficient lookups, field
operations and finite executions.  Definition expansion establishes no
polynomial-division theorem, field extension, G091 closure or admission.
The existing canonical-coefficient identity is BetaPrefixInto; no renamed
coefficient, addition or scaling aliases are introduced.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

import constructive_g009_definitions as previous
from peano_lab.library.defined_syntax import DefinitionSpec, _definition
from peano_lab.library import prime_field_polynomial_subtraction_candidate as subtraction
from peano_lab.library import prime_field_polynomial_trim_candidate as trim
from peano_lab.library import prime_field_polynomial_monic_candidate as monic
from peano_lab.library import prime_field_polynomial_synthetic_candidate as synthetic


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if HERE != ROOT/'scripts' or not (ROOT/'peano-lab/py/peano_lab').is_dir():
    raise RuntimeError('polynomial-division definitions must reside in repository scripts')
MATH_DIRECTORY = ROOT/'peano-lab/py/peano_lab/library'
HISTORICAL_DEFINITIONS_BY_NAME = previous.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME


def _construct(identifier, name, parameters, builder, summary, dependencies):
    return _definition(
        stable_id=f'ND{identifier:04d}',name=name,parameters=parameters,
        template_source=builder(*parameters,tag='polynomial_division_definition',variables=parameters),
        summary=summary,category='constructive_polynomial_division',priority='P2',
        conceptual_dependencies=dependencies,
    )


POLYNOMIAL_DIVISION_DEFINITIONS: tuple[DefinitionSpec,...] = (
    _construct(327,'FpCoefficientNegation',('p','ab','ac','rb','rc','L'),
        subtraction.prime_field_polynomial_negate_relation,
        'At each strict index i<L, actual beta source and result coefficients satisfy FpNeg(p,a,r), namely bounded field addition a+r=0. The common representation length and highest-degree-first order are retained. Empty prefixes impose no coefficient condition, even at p=0; existence for canonical prime-field inputs is a separate theorem.',
        ('Lt','BetaAt','FpNeg')),
    _construct(328,'FpCoefficientSubtraction',('p','ab','ac','bb','bc','rb','rc','L'),
        subtraction.prime_field_polynomial_subtract_relation,
        'At each aligned i<L, actual source entries a,b and result entry r satisfy FpAdd(p,b,r,a). All values are the inherited canonical natural field representatives. The graph assumes no subtraction identity, output construction, degree or equality of raw beta codes. Empty prefixes remain vacuous at every modulus.',
        ('Lt','BetaAt','FpAdd')),
    _construct(329,'PolynomialSuffix',('b','c','t','d','e','M'),
        trim.prime_field_polynomial_suffix_relation,
        'For every i<M and actual source value at t+i, the target beta prefix records that same value at i. No coefficient bound, primality, total input length, zero-prefix condition or suffix construction is assumed. The affine-slice construction theorem is not itself a definition-expansion edge.',
        ('Lt','BetaAt')),
    _construct(330,'FpPolynomialTrim',('p','b','c','L','t','d','e','M'),
        trim.prime_field_polynomial_trim_relation,
        'The actual input has canonical coefficients and length L=t+M, its first t coefficients are zero, and an actual suffix code has length M. The suffix is empty or its decoded head is nonzero. Primality, a claimed degree, length uniqueness and an output-code uniqueness law are not definition clauses.',
        ('BetaPrefixInto','Lt','BetaAt','PolynomialSuffix')),
    _construct(331,'FpMonic',('p','b','c','L'),
        monic.prime_field_polynomial_monic_relation,
        'A nonempty canonical coefficient prefix has actual leading coefficient natural 1. Its length is still a representation annotation, not a degree definition; the empty zero polynomial is excluded. Natural field one is not signed code 2, and primality is not included in this graph.',
        ('BetaPrefixInto','BetaAt')),
    _construct(332,'FpMonicNormalization',('p','k','ab','ac','bb','bc','L'),
        monic.prime_field_polynomial_monic_normalization_relation,
        'For nonempty length L, k is an actual inherited field inverse of the decoded source leading coefficient, and the result is its actual coefficientwise FpPolyScale action. Result monicity, degree preservation and represented-value uniqueness are separate conclusions, not premises. A recorded inverse can also exist at a composite modulus.',
        ('BetaAt','FpInv','FpPolyScale')),
    _construct(333,'FpSyntheticDivision',('p','b','c','a','n','qb','qc','r'),
        synthetic.prime_field_polynomial_synthetic_division_relation,
        'An actual FpHornerTrace processes S n highest-degree-first coefficients at the canonical argument a and ends at r. An actual MatrixAffineSlice with offset 1 and stride 1 records n quotient coefficients from that same history; constants therefore have an empty quotient. The coefficient recurrence and division identity are not graph premises. This is not arbitrary-divisor Euclidean division or G091.',
        ('FpHornerTrace','MatrixAffineSlice')),
)


_known = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_identifiers = {item.stable_id for item in _known.values()}
if len(_known) != 383 or len(_identifiers) != 383:
    raise ValueError('the frozen 383-definition predecessor registry changed')
if tuple(item.stable_id for item in POLYNOMIAL_DIVISION_DEFINITIONS) != tuple(f'ND{i:04d}' for i in range(327,334)):
    raise ValueError('the seven polynomial-division identity positions changed')
for item in POLYNOMIAL_DIVISION_DEFINITIONS:
    if item.name in _known or item.stable_id in _identifiers:
        raise ValueError('polynomial-division notation shadows an inherited identity')
    if (len(item.conceptual_dependencies) != len(set(item.conceptual_dependencies))
            or not set(item.conceptual_dependencies) <= _known.keys()):
        raise ValueError('repeated, forward or missing polynomial expansion dependency')
    _known[item.name] = item
    _identifiers.add(item.stable_id)

ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str,DefinitionSpec] = MappingProxyType(_known)
POLYNOMIAL_DIVISION_REGISTRIES = (('polynomial-division-prerequisites',POLYNOMIAL_DIVISION_DEFINITIONS),)


def definition_closure(names: tuple[str,...]) -> tuple[DefinitionSpec,...]:
    """Return actual transitive expansion prerequisites, never proof parents."""
    if type(names) is not tuple or any(type(name) is not str or not name for name in names):
        raise ValueError('definition names must be an exact tuple of nonempty text')
    ordered,visited,active = [],set(),set()

    def visit(name):
        if name in visited:
            return
        if name in active or name not in ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME:
            raise ValueError('unknown or cyclic polynomial-division notation: '+name)
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


__all__ = ('POLYNOMIAL_DIVISION_DEFINITIONS','POLYNOMIAL_DIVISION_REGISTRIES',
           'ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME','definition_closure')
