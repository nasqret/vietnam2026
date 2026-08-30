"""Conservative G009 notation over the exact 372 inherited identities.

Only eleven independently defined public graphs receive new identities.
Neither a named graph nor an expansion arrow establishes a theorem, a full
campaign milestone, Alpha eligibility, Stable membership, or publication.
The blueprint's one-argument Multiplicative(f) is deliberately not an alias
for the normalized, nonempty two-argument MultiplicativePrefix(N,F).
"""

from __future__ import annotations

from collections.abc import Mapping
import importlib.util
from pathlib import Path
import sys
from types import MappingProxyType


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if HERE != ROOT / 'scripts' or not (ROOT / 'peano-lab/py/peano_lab').is_dir():
    raise RuntimeError('G009 definitions must reside in their repository scripts directory')
sys.path[:0] = [str(ROOT / 'peano-lab/py'), str(ROOT / 'scripts')]
MATH_DIRECTORY = ROOT / 'peano-lab/py/peano_lab/library'

from constructive_dirichlet_inverse_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME,
)
from peano_lab.library.defined_syntax import DefinitionSpec, _definition


def _load_new_module(name):
    """Load only additive source modules; never load an edition or factory rows.

    Scratch files retain their eventual package-qualified imports. The old
    package path, imported historical modules, proof caches and registries
    are not modified. Compiling the bounded source bytes avoids stale pyc.
    """
    path = MATH_DIRECTORY / (name + '.py')
    if not path.is_file() or path.is_symlink() or not 0 < path.stat().st_size <= 2*1024*1024:
        raise ValueError('G009 notation needs a bounded regular mathematical source')
    with path.open('rb') as stream:
        raw = stream.read(2*1024*1024+1)
    if not 0 < len(raw) <= 2*1024*1024:
        raise ValueError('G009 mathematical source exceeded the unchanged source bound')
    qualified = 'peano_lab.library.' + name
    existing = sys.modules.get(qualified)
    if existing is not None and Path(getattr(existing, '__file__', '')).resolve() != path.resolve():
        raise ValueError('a G009 package name shadows a different mathematical source')
    spec = importlib.util.spec_from_file_location(qualified, path)
    if spec is None or spec.loader is None:
        raise ValueError('G009 mathematical source is not loadable')
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


# Dependency order, not a proof dependency list. The block module supplies
# Cartesian syntax helpers but introduces no new public relation identity.
multiplicative = _load_new_module('arithmetic_multiplicative_candidate')
pairs = _load_new_module('coprime_divisor_decomposition_candidate')
index_map = _load_new_module('divisor_pair_index_candidate')
_block = _load_new_module('signed_block_sum_candidate')
cartesian = _load_new_module('signed_cartesian_product_candidate')
support_reindex = _load_new_module('signed_support_reindex_candidate')
product_data = _load_new_module('dirichlet_multiplicative_support_candidate')


def _construct(identifier, name, parameters, builder, summary, dependencies):
    return _definition(
        stable_id=f'ND{identifier:04d}', name=name, parameters=parameters,
        template_source=builder(*parameters, tag='g009_definition', variables=parameters),
        summary=summary, category='constructive_g009_multiplicativity', priority='P2',
        conceptual_dependencies=dependencies,
    )


G009_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(316, 'MultiplicativePrefix', ('N','F'),
        multiplicative.signed_multiplicative_prefix_relation,
        'An actual nonempty signed prefix, N>0, has F(1)=+1 (canonical code 2) and the signed product law for positive coprime a,b with a*b<=N. F(0) and values outside that window remain unrestricted. Signed-unit codes plus or minus one are not this normalization; the one-argument planning notation Multiplicative(f) is not an alias.',
        ('ArithTable','ArithAt','Le','Coprime','SignedMul')),
    _construct(317, 'DivisorFactorPair', ('m','n','d','a','b'),
        pairs.divisor_factor_pair_relation,
        'Actual positive a,b divide m,n respectively and d=a*b. Coprimality of m,n, coordinate bounds, gcd recovery, existence and uniqueness are separate hypotheses or proved consequences, not clauses of this relation.',
        ('Dvd',)),
    _construct(318, 'DivisorPairIndexMap', ('V','L','r','s'),
        index_map.divisor_pair_index_map_relation,
        'Positive width V and native beta codes record d*e whenever i<L, e<V and i=V*d+e. L may be zero. No row bound, target bound, injectivity, signed value or sum identity is assumed; inactive images may collide.',
        ('Lt','BetaAt')),
    _construct(319, 'SignedCartesianProduct', ('F','G','T','m','n'),
        cartesian.signed_cartesian_product_relation,
        'Actual signed tables satisfy T[n*i+j]=F[i]*G[j] for i<m and j<n, with the genuine signed multiplication graph. Zero dimensions are allowed. T separately certifies its unused endpoint m*n; no product-of-sums or flattening identity is a definition premise.',
        ('ArithTable','Lt','ArithAt','SignedMul')),
    _construct(320, 'SignedSupportReindex', ('A','B','r','s','L','M'),
        support_reindex.signed_support_reindex_relation,
        'Actual tables and a native beta map preserve nonzero source values at bounded target indices, are injective only on nonzero source support, and cover every nonzero target value. Unequal or empty windows and inactive collisions are allowed. This is not a whole-window permutation and contains no sum equality.',
        ('ArithTable','Lt','ArithAt','BetaAt')),
    _construct(321, 'SignedIncidenceEntry', ('A','r','s','i','j','z'),
        support_reindex.signed_support_incidence_entry_relation,
        'Read the actual signed source value at i and its actual native beta image. The cell equals that value when j is the image and equals zero otherwise. No reindexing, table-construction or sum conclusion is assumed.',
        ('ArithAt','BetaAt')),
    _construct(322, 'SignedIncidenceFlatEntry', ('A','r','s','M','k','z'),
        support_reindex.signed_support_incidence_flat_entry_relation,
        'Witness actual quotient/remainder coordinates k=(S M)*i+j with j<S M, then read the independently defined incidence cell. Physical stride S M remains positive when M=0; this graph has no upper row bound.',
        ('Lt','SignedIncidenceEntry')),
    _construct(323, 'SignedIncidenceFlatPrefix', ('A','r','s','M','l','T'),
        support_reindex.signed_support_incidence_flat_prefix_relation,
        'An actual signed table T stores incidence flat entries at every inclusive index k<=l. Its construction by genuine finite beta-prefix extension and its later finite-fold properties are separate theorems.',
        ('ArithTable','Le','ArithAt','SignedIncidenceFlatEntry')),
    _construct(324, 'SignedSupportIncidence', ('A','r','s','L','M','T'),
        support_reindex.signed_support_incidence_relation,
        'An actual signed incidence table uses physical stride S M and cells i<L,j<M. T is valid through L*(S M); the padding column j=M and final endpoint are unused. The source is an actual table, but no target, support bijection or Fubini equality is part of this graph.',
        ('ArithTable','Lt','ArithAt','SignedIncidenceEntry')),
    _construct(325, 'DirichletCoprimeProductData', ('N','F','G','m','n','A','B','T','Q','r','s'),
        product_data.dirichlet_coprime_product_data_relation,
        'Two normalized multiplicative prefixes, positive coprime m,n with m*n<=N, three actual convolution-entry prefixes, an actual Cartesian product table and a native beta coordinate-product map. Neither the support reindexing conclusion nor any signed sum or multiplicativity result is built into this data.',
        ('MultiplicativePrefix','Le','Coprime','DirichletPrefix','SignedCartesianProduct','DivisorPairIndexMap')),
    _construct(326, 'DirichletDivisorGridWitness', ('F','G','m','n','i','z','d','e','a','b'),
        product_data.dirichlet_divisor_grid_witness_relation,
        'Actual bounded positive divisor coordinates d,e have i=(S n)*d+e, independently defined Dirichlet summands a,b and SignedMul(a,b,z). The signed values a,b,z need not be nonzero. No factorization oracle, target summand or convolution closure is assumed.',
        ('Lt','DivisorFactorPair','DirichletEntry','SignedMul')),
)


_known = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_identifiers = {item.stable_id for item in _known.values()}
if len(_known) != 372 or len(_identifiers) != 372:
    raise ValueError('the frozen 372-definition registry changed')
if tuple(item.stable_id for item in G009_DEFINITIONS) != tuple(f'ND{i:04d}' for i in range(316,327)):
    raise ValueError('the additive G009 definition identity order changed')
for item in G009_DEFINITIONS:
    if item.name in _known or item.stable_id in _identifiers:
        raise ValueError('G009 notation shadows an inherited identity')
    if (len(item.conceptual_dependencies) != len(set(item.conceptual_dependencies))
            or not set(item.conceptual_dependencies) <= _known.keys()):
        raise ValueError('repeated, forward or missing G009 expansion dependency')
    _known[item.name] = item
    _identifiers.add(item.stable_id)

ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str,DefinitionSpec] = MappingProxyType(_known)
G009_REGISTRIES = (('multiplicative-convolution',G009_DEFINITIONS),)


def definition_closure(names: tuple[str,...]) -> tuple[DefinitionSpec,...]:
    """Return only actual transitive expansion prerequisites, in stable order."""
    if type(names) is not tuple or any(type(name) is not str or not name for name in names):
        raise ValueError('definition names must be an exact tuple of nonempty text')
    ordered,visited,active = [],set(),set()

    def visit(name):
        if name in visited:
            return
        if name in active or name not in ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME:
            raise ValueError('unknown or cyclic G009 notation: '+name)
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


__all__ = ('G009_DEFINITIONS','G009_REGISTRIES',
           'ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME','definition_closure')
