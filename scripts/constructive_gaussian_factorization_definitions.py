"""Additive conservative notation for actual Gaussian unique factorization.

All 264 historical definition objects are reused literally.  Gaussian
divisibility, units, association, irreducibility, prime divisors, genuine
product histories and actual index bijections remain separate graphs.
This notation registry does not grant mathematical or Alpha authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import sys
from types import MappingProxyType
from typing import Callable


ROOT=Path(__file__).resolve().parents[1]
if str(ROOT/'peano-lab/py') not in sys.path:
    sys.path.insert(0,str(ROOT/'peano-lab/py'))

from constructive_priority_layer_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME
from peano_lab.library.defined_syntax import DefinitionSpec,_definition
from peano_lab.library import gaussian_ring_candidate as ring
from peano_lab.library import gaussian_gcd_candidate as gcd
from peano_lab.library import gaussian_factor_search_candidate as search
from peano_lab.library import gaussian_factorization_candidate as factor
from peano_lab.library import gaussian_factor_permutation_candidate as permutation


def _contextual(builder: Callable[...,str]) -> Callable[...,str]:
    def expand(*values: str,tag: str) -> str:
        return builder(*values,tag=tag,variables=tuple(values))
    return expand


def _private_contextual(builder: Callable[...,str]) -> Callable[...,str]:
    def expand(*values: str,tag: str) -> str:
        return ring._definition(builder,tuple(values),tag=tag,variables=tuple(values))
    return expand


def _product_step(b: str,c: str,h: str,e: str,i: str,tag: str) -> str:
    a,P,Q=ring._names(tag,'step_factor','step_before','step_after')
    return f"exists {a} {P} {Q}. "+ring._and(
        factor._at(b,c,i,a,tag+'factor'),factor._at(h,e,i,P,tag+'before'),
        factor._at(h,e,f'S ({i})',Q,tag+'after'),ring._mul(P,a,Q,tag+'multiply'))


def _construct(identifier: int,name: str,parameters: tuple[str,...],builder: Callable[...,str],summary: str,dependencies: tuple[str,...]) -> DefinitionSpec:
    return _definition(
        stable_id=f'ND{identifier:04d}',name=name,parameters=parameters,
        template_source=builder(*parameters,tag='gaussianfactorization'),summary=summary,
        category='constructive_gaussian_factorization',priority='P2',conceptual_dependencies=dependencies,
    )


GAUSSIAN_FACTORIZATION_DEFINITIONS: tuple[DefinitionSpec,...]=(
    _construct(208,'GDvd',('d','z'),_contextual(ring.gaussian_divides_relation),
               'An actual Gaussian quotient q satisfies GMul(d,q,z). The argument codes are not multiplied as natural numbers.',('GMul',)),
    _construct(209,'GUnit',('z',),_contextual(ring.gaussian_unit_relation),
               'An actual Gaussian inverse multiplies z to canonical Gaussian identity code 6. Natural code 1 is not this identity.',('GDvd',)),
    _construct(210,'GAssociate',('a','b'),_contextual(ring.gaussian_associate_relation),
               'A genuinely witnessed Gaussian unit u satisfies GMul(u,a,b). Associated factor codes need not be literally equal.',('GUnit','GMul')),
    _construct(211,'GIrreducible',('z',),_contextual(ring.gaussian_irreducible_relation),
               'A valid nonzero Gaussian nonunit whose every actual factorization has a unit factor. No prime-divisor property is assumed.',('ZPairValid','GUnit','GMul')),
    _construct(212,'GPrime',('z',),_contextual(ring.gaussian_prime_relation),
               'A valid nonzero Gaussian nonunit dividing an actual product only if it divides a factor. Equivalence with irreducibility is proved, not part of either definition.',('ZPairValid','GUnit','GMul','GDvd')),
    _construct(213,'GBezout',('g','a','b','u','v'),_contextual(gcd.gaussian_bezout_relation),
               'Actual product codes for a*u and b*v have actual signed-pair sum g. The signed Gaussian coefficients are explicit witnesses.',('GMul','ZPairAdd')),
    _construct(214,'GGcd',('g','a','b'),_contextual(gcd.gaussian_gcd_relation),
               'g actually divides a and b, and every actual common Gaussian divisor divides g. Literal uniqueness or normalization is not assumed.',('GDvd',)),
    _construct(215,'GNormBoundedCoordinates',('z','N'),_contextual(search.gaussian_norm_bounded_coordinates_relation),
               'The actual canonical pair coordinates of z are each at most 2N. This finite search box does not assert that N is a norm.',('NaturalPair','Le')),
    _construct(216,'GProperNormDivisor',('d','z','N'),_contextual(search.gaussian_proper_norm_divisor_relation),
               'd is an actual nonunit divisor of z and has a witnessed actual Gaussian norm strictly below N. This is not a supplied factorization oracle.',('GUnit','GDvd','GNorm','Lt')),
    _construct(217,'GStrictNonunitFactorization',('z','N','a','b','A','B'),_contextual(search.gaussian_strict_nonunit_factorization_relation),
               'An actual Gaussian product a*b=z, two actual factor norms A,B, nonunit factors, and both strict norm bounds below N. Its existence is a proved search outcome.',('GMul','GNorm','GUnit','Lt')),
    _construct(218,'GProductStep',('b','c','h','e','i'),_private_contextual(_product_step),
               'At index i, decode the factor and the adjacent cumulative values from actual beta codes, then multiply using the actual Gaussian graph.',('BetaAt','GMul')),
    _construct(219,'GProductSteps',('b','c','h','e','l'),_private_contextual(factor._steps),
               'Every index i<l has an actual Gaussian multiplication step in the same beta-coded cumulative history.',('Lt','GProductStep')),
    _construct(220,'GProduct',('b','c','l','P'),_contextual(factor.gaussian_product_relation),
               'A real beta multiplication history begins at Gaussian identity code 6, performs the stated l factor steps, and ends at P. No prime or uniqueness conclusion is included.',('BetaAt','GProductSteps')),
    _construct(221,'GAllIrreducible',('b','c','l'),_contextual(factor.gaussian_all_irreducible_relation),
               'Every actual decoded entry of the finite beta prefix is a Gaussian irreducible; repeated or associated factors remain distinct occurrences.',('Lt','BetaAt','GIrreducible')),
    _construct(222,'GAllPrime',('b','c','l'),_contextual(factor.gaussian_all_prime_relation),
               'Every actual decoded entry of the finite prefix satisfies the full Gaussian prime-divisor graph.',('Lt','BetaAt','GPrime')),
    _construct(223,'GIrreducibleFactorization',('z','u','b','c','l'),_contextual(factor.gaussian_irreducible_factorization_relation),
               'The actual unit u times an actual beta product of l irreducible Gaussian entries equals z. It does not assume sorted order, existence or uniqueness.',('GUnit','GAllIrreducible','GProduct','GMul')),
    _construct(224,'GPrimeFactorization',('z','u','b','c','l'),_contextual(factor.gaussian_prime_factorization_relation),
               'An actual unit and actual finite RingPrime Gaussian factor list reconstruct z through a genuine multiplication trace. Zero is excluded by theorem, not a hidden extra premise here.',('GUnit','GAllPrime','GProduct','GMul')),
    _construct(225,'GFactorAssociateMatching',('b','c','d','e','u','v','l'),_contextual(permutation.gaussian_factor_associate_matching_relation),
               'Every actual decoded source factor and its decoded image factor are related by an actual multiplicative unit witness. This graph alone does not assert that the map is bijective.',('Lt','BetaAt','GAssociate')),
    _construct(226,'GMatchedFactors',('b','c','d','e','u','v','l'),_private_contextual(permutation._matched),
               'An actual bounded, injective, surjective beta index map matches all source and target factor occurrences by witnessed Gaussian units.',('PermutationPrefix','GFactorAssociateMatching')),
    _construct(227,'GFactorPermutation',('b','c','l','d','e','m','u','v'),_contextual(permutation.gaussian_factor_permutation_relation),
               'The two actual lengths are equal and the given beta map is a genuine unit-matching finite permutation. No identical factor-code or leading-unit claim is made.',('GMatchedFactors',)),
)


_known=dict(HISTORICAL_DEFINITIONS_BY_NAME)
_identifiers={item.stable_id for item in _known.values()}
if len(_known)!=264 or len(_identifiers)!=264:
    raise ValueError('the immutable Alpha-v29 definition registry changed')
if tuple(item.stable_id for item in GAUSSIAN_FACTORIZATION_DEFINITIONS)!=tuple(f'ND{i:04d}' for i in range(208,228)):
    raise ValueError('Gaussian factorization definition identifiers changed')
for item in GAUSSIAN_FACTORIZATION_DEFINITIONS:
    if item.name in _known or item.stable_id in _identifiers:
        raise ValueError('a Gaussian factorization definition overwrites a historical identity')
    if len(item.conceptual_dependencies)!=len(set(item.conceptual_dependencies)) or not set(item.conceptual_dependencies)<=_known.keys():
        raise ValueError('Gaussian definitions have repeated, forward or missing dependency edges')
    _known[item.name]=item
    _identifiers.add(item.stable_id)


GAUSSIAN_FACTORIZATION_DEFINITIONS_BY_NAME: Mapping[str,DefinitionSpec]=MappingProxyType({item.name:item for item in GAUSSIAN_FACTORIZATION_DEFINITIONS})
ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str,DefinitionSpec]=MappingProxyType(_known)
GAUSSIAN_FACTORIZATION_REGISTRIES=(('gaussian-factorization',GAUSSIAN_FACTORIZATION_DEFINITIONS),)


def definition_closure(names: tuple[str,...]) -> tuple[DefinitionSpec,...]:
    """Relevant exact notation and its acyclic historical prerequisites only."""
    ordered: list[DefinitionSpec]=[]
    visited: set[str]=set()
    active: set[str]=set()

    def visit(name: str) -> None:
        if name in visited:
            return
        if name in active or name not in ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME:
            raise ValueError(f'unknown or cyclic Gaussian factorization notation {name!r}')
        active.add(name)
        item=ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name]
        for dependency in item.conceptual_dependencies:
            visit(dependency)
        active.remove(name)
        visited.add(name)
        ordered.append(item)

    for name in names:
        visit(name)
    return tuple(ordered)


__all__=('ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME','GAUSSIAN_FACTORIZATION_DEFINITIONS','GAUSSIAN_FACTORIZATION_DEFINITIONS_BY_NAME','GAUSSIAN_FACTORIZATION_REGISTRIES','definition_closure')
