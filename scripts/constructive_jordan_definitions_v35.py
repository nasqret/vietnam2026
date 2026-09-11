"""Callable ND0371--ND0381 conservative extension, never a proof registry.

The caller supplies its existing definition map. This module does not import
or mutate the developing shared campaign registry, Alpha, or any proof data.
ND0370 stays unallocated: tuple equality reuses exact ND0121 IntegerVectorZero.
"""
from hashlib import sha256
import json
from types import MappingProxyType

from peano_lab.library.defined_syntax import DefinitionSpec, _definition
from peano_lab.kernel.formulas import parse_formula_in_context

from constructive_polynomial_gcd_definitions_v34 import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME,
)


def _sources():
    from peano_lab.library import jordan_totient_candidate as base
    from peano_lab.library import jordan_multiplicativity_candidate as rectangle
    return base, rectangle


def definitions():
    base,rectangle=_sources()
    rows=(
        (371,'JordanTupleAllDivisible',('d','b','c','k'),base._all_dvd,('Lt','BetaAt','Dvd'),
         'The natural d divides every actual decoded coordinate in the finite prefix.'),
        (372,'JordanPrimitiveTuple',('n','b','c','k'),base._primitive,('Dvd','JordanTupleAllDivisible'),
         'Every common divisor of n and all decoded coordinates equals one; boundedness is separate.'),
        (373,'JordanTupleCongruence',('n','b','c','d','e','k'),base._pointwise_mod,('Lt','BetaAt','ModEq'),
         'All paired actual decoded coordinates are congruent modulo n, without imposing a canonical range.'),
        (374,'JordanTupleEnumeration',('k','n','B','C','D','E','j'),base._enumeration,
         ('Lt','BetaAt','BetaPrefixInto','JordanPrimitiveTuple','IntegerVectorZero'),
         'Sound, complete and duplicate-free enumeration of canonical primitive tuples; both code and scale columns are actual beta data.'),
        (375,'JordanTotient',('k','n','j'),base._jordan,('JordanTupleEnumeration',),
         'Positive order and modulus with an actual tuple enumeration of length j. No product identity or existence theorem is a clause.'),
        (376,'JordanTupleListed',('b','c','k','B','C','D','E','j'),base._listed,('Lt','BetaAt','IntegerVectorZero'),
         'An actual decoded tuple occurs, up to coordinate equality, at an actual position in the two-column enumeration.'),
        (377,'JordanTupleScan',('k','n','c','limit','B','C','D','E','j'),base._scan,
         ('Lt','BetaAt','BetaPrefixInto','JordanPrimitiveTuple','IntegerVectorZero','JordanTupleListed'),
         'A duplicate-free partial enumeration covers precisely the primitive bounded tuples tested by the finite code scan.'),
        (378,'JordanTupleRepresentatives',('k','n','c','T'),base._representatives,
         ('Lt','BetaPrefixInto','IntegerVectorZero'),
         'Every bounded tuple has a coordinate-equal representative with common scale c and code below T.'),
        (379,'JordanTupleCRT',('m','n','b','c','d','e','f','g','k'),base._crt_tuple,
         ('Lt','BetaAt','ModEq'),
         'Actual output coordinates satisfy both component congruences. Neither coprimality nor canonicality is implicit.'),
        (380,'JordanCanonicalTupleCRT',('m','n','b','c','d','e','f','g','k'),base._canonical_crt,
         ('BetaPrefixInto','JordanTupleCongruence'),
         'The output tuple is bounded by m*n and congruent to each actual input tuple at its component modulus.'),
        (381,'JordanRectangleCRT',('m','n','k','A','B','C','D','u','E','F','G','H','v','P','Q','R','T','q'),rectangle._rect,
         ('Lt','BetaAt','JordanCanonicalTupleCRT','JordanPrimitiveTuple'),
         'At each flat rectangle index below q the output has actual entries giving a canonical primitive CRT tuple of the actual source entries.'),
    )
    result=[]
    for number,name,parameters,builder,parents,summary in rows:
        source=builder(*parameters,'definition_jordan')
        definition=_definition(stable_id=f'ND{number:04d}',name=name,parameters=parameters,
            template_source=source,summary=summary,category='constructive_jordan_totient',priority='P2',
            conceptual_dependencies=parents)
        renamed=tuple('argument'+str(i) for i in range(len(parameters)))
        if definition.template_formula!=parse_formula_in_context(builder(*renamed,'other_jordan'),list(renamed)):
            raise ValueError('Jordan definition builder captures parameters')
        result.append(definition)
    return tuple(result)


def registry_digest(registry):
    rows=[(d.stable_id,d.name,d.parameters,d.template_source,d.conceptual_dependencies)
          for d in registry.values()]
    return sha256(json.dumps(rows,ensure_ascii=True,separators=(',',':')).encode()).hexdigest()


def extend_registry(previous):
    """Return a new immutable map; every supplied historical object is reused."""
    snapshot=tuple(previous.items());before=registry_digest(previous)
    known=dict(snapshot);ids=set()
    for name,d in snapshot:
        if type(d) is not DefinitionSpec or name!=d.name or d.stable_id in ids:
            raise ValueError('malformed or duplicate parent identity')
        ids.add(d.stable_id)
    base,_=_sources()
    equal=known.get('IntegerVectorZero')
    parameters=('b','c','d','e','k')
    if (equal is None or equal.stable_id!='ND0121' or equal.arity!=5 or
            equal.template_formula!=parse_formula_in_context(base._equal(*parameters,'reuse_check'),list(parameters))):
        raise ValueError('historical ND0121 tuple-equality argument mapping differs')
    if 'ND0370' in ids:raise ValueError('reserved ND0370 must remain unallocated')
    added=definitions()
    for definition in added:
        if definition.name in known or definition.stable_id in ids:
            raise ValueError('Jordan definition shadows an existing identity')
        parents=definition.conceptual_dependencies
        if len(parents)!=len(set(parents)) or not set(parents)<=known.keys():
            raise ValueError('missing, repeated, forward or cyclic definition parent')
        if any(d.arity==definition.arity and d.template_formula==definition.template_formula for d in known.values()):
            raise ValueError('an equivalent definition already has an identity')
        known[definition.name]=definition;ids.add(definition.stable_id)
    if tuple(previous.items())!=snapshot or registry_digest(previous)!=before:
        raise ValueError('caller registry changed during extension')
    if not all(known[n] is d for n,d in snapshot):raise ValueError('historical objects not reused')
    return MappingProxyType(known)


def definition_edges(additions=None):
    """Typed syntax arrows only; these are never proof-dependency edges."""
    if additions is None:additions=definitions()
    return tuple(dict(source=parent,target=d.name,kind='definition_uses_definition')
                 for d in additions for parent in d.conceptual_dependencies)


ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME = extend_registry(HISTORICAL_DEFINITIONS_BY_NAME)
JORDAN_DEFINITIONS = tuple(ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name] for name in
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME if name not in HISTORICAL_DEFINITIONS_BY_NAME)
JORDAN_REGISTRIES = (("jordan-totient", JORDAN_DEFINITIONS),)
if len(HISTORICAL_DEFINITIONS_BY_NAME) != 407 or len(ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME) != 418:
    raise ValueError("the exact407+11 conservative definition extension changed")


def definition_closure(names):
    """Topological syntax prerequisites; these are never proof assumptions."""
    if type(names) is not tuple or any(type(name) is not str or not name for name in names):
        raise ValueError("expected an exact tuple of definition names")
    ordered, visited, active = [], set(), set()
    def visit(name):
        if name in visited:
            return
        if name in active or name not in ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME:
            raise ValueError("unknown or cyclic conservative definition: " + name)
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


def build_definition_graph(campaign):
    from constructive_polynomial_gcd_definition_graph_v34 import (
        DEFAULT_REGISTRIES, REVIEWED_BLUEPRINT_ALIASES, build_definition_graph as build,
    )
    graph = build(campaign, registries=DEFAULT_REGISTRIES + JORDAN_REGISTRIES,
                  aliases=REVIEWED_BLUEPRINT_ALIASES)
    # The historical blueprint says Jordan(k,n,t), the reviewed identity
    # JordanTotient(k,n,j). Preserve both vocabularies and explicitly audit
    # the harmless free-parameter rename; no alias identity is allocated.
    parameters = tuple(campaign["definitions"]["Jordan"]["parameters"])
    definition = ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME["JordanTotient"]
    if parameters != ("k", "n", "t") or definition.parameters != ("k", "n", "j"):
        raise ValueError("the reviewed Jordan argument roles changed")
    if parse_formula_in_context(_sources()[0]._jordan(*parameters, "blueprint_jordan"), list(parameters)) != definition.template_formula:
        raise ValueError("Jordan argument renaming changed the exact conservative AST")
    row = next(row for row in graph["definitions"] if row["name"] == "Jordan")
    if row["reviewed_match"] is not None or row["reviewed_incompatibility"] is not None:
        raise ValueError("the historical blueprint already has a competing Jordan identity")
    match = dict(blueprint_name="Jordan", reviewed_name="JordanTotient", reviewed_id="ND0375",
        route="jordan-totient", kind="explicit-alias", blueprint_parameters=list(parameters),
        reviewed_parameters=list(definition.parameters), reviewed_argument_blueprint_positions=[0, 1, 2],
        reviewed_expansion_sha256=sha256(definition.template_source.encode()).hexdigest(),
        free_parameter_renaming={"t": "j"}, exact_renaming_ast_verified=True,
        blueprint_expansion_is_kernel_checked=False)
    row["reviewed_match"] = match
    graph["compatible_reviewed_matches"].append(match)
    graph["compatible_reviewed_matches"].sort(key=lambda row: row["blueprint_name"])
    graph["compatible_reviewed_match_count"] += 1
    graph["explicit_alias_reviewed_match_count"] += 1
    return graph
