"""Conservative gcd vocabulary; caller-supplied rows carry no proof authority.

The 404 predecessor objects are reused, never edited.  This adapter neither
loads the developing gcd candidates nor asserts that their existence or
uniqueness claims have been checked.
"""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import MappingProxyType

from peano_lab.library.prime_field_polynomial_monic_candidate import _monic

HERE = Path(__file__).resolve().parent
PRIOR_SOURCE = HERE.parent / 'prime-field-euclidean-notation-v1/working_euclidean_notation.py'
PRIOR_TEST = PRIOR_SOURCE.with_name('test_working_euclidean_notation.py')
PRIOR_PINS = {
    PRIOR_SOURCE: (18993, 'b2c5c2aa09a49f6c9d9ae0e46ed89c2deac5c8c3fdfeebb41d168bea0c976941'),
    PRIOR_TEST: (22591, '4d55b58da49b1f369a420af0089f5eeb7f9c59aa6078acd2c0c98179d22c340a'),
}


def _pin(path, expected):
    if path.is_symlink() or not path.is_file():
        raise ValueError('notation input must be an ordinary file')
    raw = path.read_bytes()
    if (len(raw), sha256(raw).hexdigest()) != expected:
        raise ValueError('frozen notation input changed')
    return {'bytes': len(raw), 'sha256': expected[1]}


for _path, _expected in PRIOR_PINS.items():
    _pin(_path, _expected)
_private = '_working_gcd_notation_prior95'
_owners = dict(sys.modules)
_spec = importlib.util.spec_from_file_location(_private, PRIOR_SOURCE)
previous = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(previous)
if sys.modules.get(_private) is not _owners.get(_private) or (_private in sys.modules) != (_private in _owners):
    raise ValueError('private loader changed module ownership')
shift = previous.shift
NotationError = previous.NotationError
TheoremSpec = previous.TheoremSpec
specs_digest = previous.specs_digest
_transport = previous.CANDIDATES['transport']


def require_sources():
    return {**previous.require_sources(), **{
        str(path.relative_to(previous.ROOT)): _pin(path, pin)
        for path, pin in PRIOR_PINS.items()}}


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


def _definition(identifier, name, parameters, source, parents, summary):
    return shift._definition(stable_id=identifier, name=name, parameters=parameters,
        template_source=source, conceptual_dependencies=parents, summary=summary,
        category='constructive_polynomial_gcd', priority='P2')


ZERO_OR_MONIC = _definition('ND0348', 'FpPolynomialZeroOrMonic', NORMAL_PARAMETERS,
    _normal(*NORMAL_PARAMETERS, 'gcd_definition_normal'), ('FpMonic',),
    'The representation is empty or is an actual nonempty canonical monic prefix. '
    'No primality or existence claim is included; empty codes are unrestricted.')
RIGHT_GCD = _definition('ND0349', 'FpPolynomialRightGcd', GCD_PARAMETERS,
    _gcd(*GCD_PARAMETERS, 'gcd_definition_greatest'),
    ('FpPolynomialCommonRightDivisor', 'FpPolynomialRightDivides'),
    'G is a common right divisor, and every common right divisor D right-divides G. '
    'This universally quantified property does not assert existence or uniqueness.')
NORMALIZED_GCD = _definition('ND0350', 'FpPolynomialNormalizedGcd', GCD_PARAMETERS,
    '(' + _normal(*NORMAL_PARAMETERS, 'gcd_definition_normalized_normal') + ') /\\ ('
    + _gcd(*GCD_PARAMETERS, 'gcd_definition_normalized_greatest') + ')',
    ('FpPolynomialZeroOrMonic', 'FpPolynomialRightGcd'),
    'Literal conjunction of zero-or-monic and right-gcd; no Bezout coefficients '
    'or polynomial algorithm are built into this property.')
NEW_DEFINITIONS = (ZERO_OR_MONIC, RIGHT_GCD, NORMALIZED_GCD)
_known = dict(previous.DEFINITIONS)
for _item in NEW_DEFINITIONS:
    if (_item.name in _known or _item.stable_id in {x.stable_id for x in _known.values()}
            or not set(_item.conceptual_dependencies) <= _known.keys()):
        raise NotationError('definition collision or non-prior parent')
    _known[_item.name] = _item
DEFINITIONS = MappingProxyType(_known)
REGISTRIES = (*previous.REGISTRIES, ('polynomial-gcd', NEW_DEFINITIONS))


def _registry_digest(definitions):
    rows = [(x.stable_id, x.name, x.parameters, x.template_source, x.conceptual_dependencies)
            for x in definitions.values()]
    return sha256(json.dumps(rows, ensure_ascii=True, separators=(',', ':')).encode()).hexdigest()


PRIOR_OBJECTS = tuple(previous.DEFINITIONS.items())
PRIOR_REGISTRY_SHA256 = _registry_digest(previous.DEFINITIONS)


def reviewed_registry():
    require_sources()
    if (len(previous.DEFINITIONS) != 404
            or _registry_digest(previous.DEFINITIONS) != PRIOR_REGISTRY_SHA256
            or any(previous.DEFINITIONS[n] is not x or DEFINITIONS[n] is not x for n, x in PRIOR_OBJECTS)):
        raise NotationError('predecessor registry changed')
    records, order, layers = shift._registry(REGISTRIES)
    if len(records) != 407 or sum(len(r['dependencies']) for r in records.values()) != 884:
        raise NotationError('gcd registry inventory changed')
    for item in NEW_DEFINITIONS:
        for parent in item.conceptual_dependencies:
            reading = shift._FormulaCompactor((DEFINITIONS[parent],)).compact(item.template_source)
            if DEFINITIONS[parent].stable_id not in reading['statement_definition_uses']:
                raise NotationError('declared parent lacks a literal occurrence')
    return records, order, layers


def audit_rows(rows):
    """Render exact supplied source only; definition edges never imply proofs."""
    before = require_sources()
    if type(rows) is not tuple or not rows or any(type(r) is not TheoremSpec for r in rows):
        raise NotationError('expected an exact nonempty tuple of TheoremSpec')
    valid = lambda n: type(n) is str and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', n)
    names = {r.name for r in rows}
    ids = {d.stable_id: d.name for d in DEFINITIONS.values()}
    if len(names) != len(rows) or any(not valid(n) for n in names) or names.intersection((*DEFINITIONS, *ids)):
        raise NotationError('invalid, duplicated or shadowing theorem name')
    records, order, _ = reviewed_registry()
    compactor = shift._FormulaCompactor(tuple(DEFINITIONS.values()))
    nodes, proof, uses = [], [], []
    seen, external, used = set(), set(), set()
    layers, paths = {}, {}
    for row in rows:
        deps = row.dependencies
        if (type(deps) is not tuple or any(not valid(n) for n in deps)
                or len(set(deps)) != len(deps) or set(deps).intersection((*DEFINITIONS, *ids))):
            raise NotationError('invalid proof prerequisites')
        parents = [n for n in deps if n in names]
        if not set(parents) <= seen:
            raise NotationError('forward or cyclic proof prerequisite')
        compact = compactor.compact(row.statement)
        if compact['free_names'] or compact['exact_ast_equivalence'] is not True:
            raise NotationError('source statement must be closed and AST-exact')
        shift._compact_script(row, compactor, compact)
        used.update(ids[n] for n in compact['definition_uses'])
        layers[row.name] = max((layers[n] + 1 for n in parents), default=0)
        longest = max(parents, key=lambda n: len(paths[n]), default=None)
        paths[row.name] = ([] if longest is None else paths[longest]) + [row.name]
        nodes.append(dict(id=row.name, name=row.name, statement=row.statement,
            dependencies=list(deps), script=list(row.script), summary=row.summary,
            defined=compact, authority='source-syntax-only', proof_acceptance_performed=False))
        proof.extend(dict(kind='proof_dependency', source=n, target=row.name) for n in deps)
        uses.extend(dict(kind='uses_definition', source=row.name, target=n, occurrence_count=count)
                    for n, count in compact['definition_uses'].items())
        external.update(set(deps) - names)
        seen.add(row.name)
    selected = used | {d.name for d in NEW_DEFINITIONS}
    for name in reversed(order):
        if name in selected:
            selected.update(records[name]['dependencies'])
    definitions = [dict(records[n], dependencies=[DEFINITIONS[p].stable_id for p in records[n]['dependencies']],
                        authority='conservative-abbreviation-only', used_in_supplied_formulas=n in used)
                   for n in order if n in selected]
    expansion = [dict(kind='definition_uses_definition', source=d['id'], target=p)
                 for d in definitions for p in d['dependencies']]
    if require_sources() != before:
        raise NotationError('source changed during rendering')
    return dict(schema='working-polynomial-gcd-notation-v1', authority='source-syntax-only',
        proof_acceptance_performed=False, admission_performed=False, publication_performed=False,
        complete_dependency_cone_claimed=False, gcd_bezout_proved=False,
        registry_definition_count=407, registry_expansion_edge_count=884,
        prior_registry_sha256=PRIOR_REGISTRY_SHA256, nodes=nodes, definitions=definitions,
        edges=proof + uses + expansion, proof_layers=layers, proof_paths=paths,
        path_policy='proof_dependency_edges_only', external_dependencies=sorted(external),
        external_dependencies_resolved=False, source_pins=before,
        ordered_specs_sha256=specs_digest(rows))


def audit(additional_rows=()):
    """Append caller supplied, explicitly unverified rows to the frozen95 map."""
    if type(additional_rows) is not tuple:
        raise NotationError('additional rows must be an exact tuple')
    return audit_rows(previous.source_rows() + additional_rows)


def audit_complete_rows(rows):
    """Render a supplied dependency-complete SOURCE cone, never certify it."""
    document = audit_rows(rows)
    if document['external_dependencies']:
        raise NotationError('a complete source map cannot omit named prerequisites')
    document['source_dependencies_complete'] = True
    return document
