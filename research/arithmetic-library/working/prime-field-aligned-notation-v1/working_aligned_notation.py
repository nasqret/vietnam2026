"""Conservative alignment notation and a source-only 52+7+9 dependency map.

The 399 inherited definition objects and their 870 expansion edges stay
unchanged. ND0343 is the literal grouped pair of formal equivalences;
ND0344 retains canonical original coefficients and an actual common-length
addition; ND0345 is exactly the argument permutation B+R=A.

This module checks syntax and source identity, not proof acceptance. The
three kinds of arrows stay distinct, and proof paths never use notation.
No kernel alias, Alpha edition, saved receipt or proof checker is imported.
"""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
from types import MappingProxyType

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WORKING = HERE.parent
PRIOR_DIRECTORY = WORKING / 'prime-field-left-unit-v1'
PRIOR_SOURCE = PRIOR_DIRECTORY / 'working_left_unit_notation.py'
PRIOR_PIN = (3976, '1fa67cf186c81e8d61c4805804c2267268d89d22ebfad876ce74499c96356cee')
ALIGNMENT_SOURCE = WORKING / 'prime-field-alignment-v1/prime_field_polynomial_alignment_candidate.py'
ALIGNED_ADD_SOURCE = WORKING / 'prime-field-aligned-add-v1/prime_field_polynomial_aligned_add_candidate.py'
_NAME = re.compile(r'[A-Za-z][A-Za-z0-9_]*\Z')


def _pin(path, expected):
    if path.is_symlink() or not path.is_file():
        raise ValueError('a frozen notation input is not an ordinary file')
    raw = path.read_bytes()
    if (len(raw), sha256(raw).hexdigest()) != expected:
        raise ValueError('a frozen notation source or independent test changed')
    return {'bytes': expected[0], 'sha256': expected[1]}


def _load_source(path, private_name):
    """Direct file loading creates no sys.modules or peano-library alias."""
    specification = importlib.util.spec_from_file_location(private_name, path)
    if specification is None or specification.loader is None:
        raise ValueError('a frozen notation source has no loader')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


_pin(PRIOR_SOURCE, PRIOR_PIN)
previous = _load_source(PRIOR_SOURCE, '_working_aligned_notation_prior52')
shift = previous.previous.shift
NotationError = shift.NotationError
TheoremSpec = shift.TheoremSpec
SOURCES = {
    **previous.SOURCES,
    PRIOR_SOURCE: PRIOR_PIN,
    PRIOR_DIRECTORY / 'test_working_left_unit_notation.py':
        (8407, 'd8747a9bd1c14088645cc841d77eb9a2f6c195ed6287ad3bc753d8cb3af63157'),
    ALIGNMENT_SOURCE:
        (11780, 'eb16e2eb02dbd66a7706e616388182992b8cf2e0715818dc1f7748938e7d798e'),
    WORKING / 'prime-field-alignment-v1/test_prime_field_polynomial_alignment_candidate.py':
        (30676, '6adbed23a43a393a4988d6eba9323cb09a8777b62b644cb1992ebdf7c6411c8b'),
    ALIGNED_ADD_SOURCE:
        (20704, 'a05bb4f5c4230ca05f51690d3ab82e33ff4596af65176874e25fbe38cf87a0db'),
    WORKING / 'prime-field-aligned-add-v1/test_prime_field_polynomial_aligned_add_candidate.py':
        (33347, '6e67b246e1c565e44d721ad92ecb2e273c2e1330d226922af89f762630de2ed8'),
}
ALIGNMENT_SPECS_SHA256 = '76b9c342744170146fcb7898cb5a20154334147578b7e01d059f01b9015d5aec'
ALIGNED_ADD_SPECS_SHA256 = 'b8ce285a000180baef6318db67202fc4fa258ae5bd6aabecfc098236f9588339'
SCHEMA = 'working-polynomial-aligned-notation-audit-v1'


def require_sources():
    previous.require_sources()
    records = {}
    for path, expected in SOURCES.items():
        try:
            records[path.relative_to(ROOT).as_posix()] = _pin(path, expected)
        except ValueError as error:
            raise NotationError(str(error)) from error
    return records


require_sources()
alignment = _load_source(ALIGNMENT_SOURCE, '_working_aligned_notation_alignment')
aligned_add = _load_source(ALIGNED_ADD_SOURCE, '_working_aligned_notation_add')
COMMON_PARAMETERS = ('ab', 'ac', 'L', 'bb', 'bc', 'M', 'ub', 'uc', 'vb', 'vc', 'K')
ALIGNED_PARAMETERS = ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'M', 'rb', 'rc', 'N')


def _new_definition(identifier, name, parameters, builder, summary, parents):
    return shift._definition(
        stable_id=identifier, name=name, parameters=parameters,
        template_source=builder(*parameters, tag='working_aligned_definition', variables=parameters),
        summary=summary, category='constructive_polynomial_alignment', priority='P2',
        conceptual_dependencies=parents,
    )


COMMON_REPRESENTATIVES = _new_definition(
    'ND0343', 'CommonRepresentatives', COMMON_PARAMETERS,
    alignment.prime_field_polynomial_common_representatives_relation,
    'A_L is formally coefficient-equivalent to U_K and B_M to V_K. The two '
    'equivalences form one literal grouped conjunction. No coefficient bound, '
    'prime modulus, upper bound on the original lengths, existence witness, '
    'raw-code equality or field-evaluation equality is a clause. Legitimate '
    'shorter representatives and independent beta encodings are allowed.',
    ('PolynomialEquivalent',),
)
ALIGNED_ADD = _new_definition(
    'ND0344', 'FpPolynomialAlignedAdd', ALIGNED_PARAMETERS,
    aligned_add.prime_field_polynomial_aligned_add_relation,
    'All three originals A_L, B_M and R_N have canonical coefficients. There '
    'exist actual common-length representatives U_K,V_K and a true coefficient '
    'sum T_K, with CommonRepresentatives(A,B,U,V,K), FpPolyAdd(U,V,T,K), and '
    'formal coefficient equivalence T_K~R_N. Primality, existence, uniqueness '
    'and algebraic laws are separate theorem statements, not definition clauses.',
    ('BetaPrefixInto', 'CommonRepresentatives', 'FpPolyAdd', 'PolynomialEquivalent'),
)
ALIGNED_SUBTRACT = _new_definition(
    'ND0345', 'FpPolynomialAlignedSubtract', ALIGNED_PARAMETERS,
    aligned_add.prime_field_polynomial_aligned_subtract_relation,
    'The literal argument permutation FpPolynomialAlignedAdd(p,B_M,R_N,A_L): '
    'B+R=A with all three original coefficient guards and actual sum witnesses. '
    'This is not an additional subtraction oracle or a proved subtraction law.',
    ('FpPolynomialAlignedAdd',),
)
NEW_DEFINITIONS = (COMMON_REPRESENTATIVES, ALIGNED_ADD, ALIGNED_SUBTRACT)
_known = dict(previous.DEFINITIONS)
_identifiers = {item.stable_id for item in _known.values()}
if len(_known) != 399 or len(_identifiers) != 399:
    raise NotationError('the exact 399-definition predecessor changed')
for _item in NEW_DEFINITIONS:
    if (_item.name in _known or _item.stable_id in _identifiers
            or len(_item.conceptual_dependencies) != len(set(_item.conceptual_dependencies))
            or not set(_item.conceptual_dependencies) <= _known.keys()):
        raise NotationError('alignment notation shadows an identity or has a non-prior parent')
    _known[_item.name] = _item
    _identifiers.add(_item.stable_id)
DEFINITIONS = MappingProxyType(_known)
REGISTRIES = (*previous.REGISTRIES, ('polynomial-length-alignment', NEW_DEFINITIONS))


def reviewed_registry():
    require_sources()
    records, order, layers = shift._registry(REGISTRIES)
    if (len(records) != 402 or sum(len(row['dependencies']) for row in records.values()) != 876
            or any(records[name]['id'] != item.stable_id for name, item in DEFINITIONS.items())
            or any(DEFINITIONS[name] is not item for name, item in previous.DEFINITIONS.items())
            or sum(len(item.conceptual_dependencies) for item in previous.DEFINITIONS.values()) != 870):
        raise NotationError('the exact 402-definition/876-edge conservative inventory changed')
    for definition in NEW_DEFINITIONS:
        for parent in definition.conceptual_dependencies:
            reading = shift._FormulaCompactor((DEFINITIONS[parent],)).compact(definition.template_source)
            if DEFINITIONS[parent].stable_id not in reading['statement_definition_uses']:
                raise NotationError('a declared alignment parent has no literal AST occurrence')
    return records, order, layers


def definition_closure(names):
    if type(names) is not tuple or any(type(name) is not str or not name for name in names):
        raise NotationError('definition names must be an exact tuple of nonempty text')
    seen, active, output = set(), set(), []

    def visit(name):
        if name in seen:
            return
        if name in active or name not in DEFINITIONS:
            raise NotationError('unknown or cyclic alignment definition')
        active.add(name)
        for parent in DEFINITIONS[name].conceptual_dependencies:
            visit(parent)
        active.remove(name)
        seen.add(name)
        output.append(DEFINITIONS[name])

    for name in names:
        visit(name)
    return tuple(output)


def specs_digest(rows):
    digest = sha256()
    for row in rows:
        payload = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        digest.update((json.dumps(payload, ensure_ascii=True, separators=(',', ':')) + '\n').encode())
    return digest.hexdigest()


def source_rows():
    before = require_sources()
    common = alignment.make_prime_field_polynomial_alignment_candidate_theorems(TheoremSpec)
    addition = aligned_add.make_prime_field_polynomial_aligned_add_candidate_theorems(TheoremSpec)
    if (len(common) != 7 or sum(len(row.dependencies) for row in common) != 10
            or sum(len(row.script) for row in common) != 258
            or specs_digest(common) != ALIGNMENT_SPECS_SHA256
            or len(addition) != 9 or sum(len(row.dependencies) for row in addition) != 30
            or sum(len(row.script) for row in addition) != 653
            or specs_digest(addition) != ALIGNED_ADD_SPECS_SHA256):
        raise NotationError('the exact frozen seven common/nine aligned-add specifications changed')
    rows = (*previous.source_rows(), *common, *addition)
    if (len(rows) != 68 or sum(len(row.dependencies) for row in rows) != 274
            or sum(len(row.script) for row in rows) != 6167 or require_sources() != before):
        raise NotationError('the exact combined68 source inventory changed')
    return rows


def audit_rows(rows):
    """Conservative compaction only; external theorem prerequisites stay open."""
    before = require_sources()
    if type(rows) is not tuple or not rows or any(type(row) is not TheoremSpec for row in rows):
        raise NotationError('an exact nonempty tuple of theorem specifications is required')
    if any(type(row.name) is not str or _NAME.fullmatch(row.name) is None for row in rows):
        raise NotationError('theorem names must be distinct identifiers')
    names = {row.name for row in rows}
    if len(names) != len(rows):
        raise NotationError('theorem names must be distinct identifiers')
    records, order, _definition_layers = reviewed_registry()
    compactor = shift._FormulaCompactor(tuple(DEFINITIONS.values()))
    by_id = {item.stable_id: item.name for item in DEFINITIONS.values()}
    if names.intersection(by_id) or names.intersection(DEFINITIONS):
        raise NotationError('theorem names cannot shadow definition identifiers')
    nodes, proof_edges, usage_edges = [], [], []
    seen, used, external = set(), set(), set()
    paths, layers = {}, {}
    for row in rows:
        if (type(row.dependencies) is not tuple
                or any(type(name) is not str or _NAME.fullmatch(name) is None for name in row.dependencies)
                or len(row.dependencies) != len(set(row.dependencies))
                or set(row.dependencies).intersection(by_id) or set(row.dependencies).intersection(DEFINITIONS)):
            raise NotationError('proof prerequisites must be distinct named specifications')
        parents = [name for name in row.dependencies if name in names]
        if not set(parents) <= seen:
            raise NotationError('a supplied proof prerequisite is forward or cyclic')
        if type(row.statement) is not str or not row.statement:
            raise NotationError('an actual nonempty core statement is required')
        compact = compactor.compact(row.statement)
        if compact['free_names'] or compact['exact_ast_equivalence'] is not True:
            raise NotationError('a theorem must be closed and re-expand to its exact core AST')
        shift._compact_script(row, compactor, compact)
        used.update(by_id[identifier] for identifier in compact['definition_uses'])
        layers[row.name] = max((layers[name] + 1 for name in parents), default=0)
        longest = max(parents, key=lambda name: len(paths[name]), default=None)
        paths[row.name] = ([] if longest is None else paths[longest]) + [row.name]
        nodes.append({'id': row.name, 'name': row.name, 'statement': row.statement,
                      'dependencies': list(row.dependencies), 'script': list(row.script),
                      'summary': row.summary, 'defined': compact,
                      'authority': 'source-syntax-only', 'proof_acceptance_performed': False})
        proof_edges.extend({'kind': 'proof_dependency', 'source': name, 'target': row.name}
                           for name in row.dependencies)
        external.update(name for name in row.dependencies if name not in names)
        usage_edges.extend({'kind': 'uses_definition', 'source': row.name, 'target': identifier,
                            'occurrence_count': count} for identifier, count in compact['definition_uses'].items())
        seen.add(row.name)
    # The literal subtraction permutation is intentionally displayed even if
    # deterministic compaction chooses AlignedAdd. Never synthesize a usage.
    selected = {item.name for item in definition_closure(
        tuple(sorted(used | {item.name for item in NEW_DEFINITIONS})))}
    definitions = []
    for name in order:
        if name in selected:
            record = dict(records[name])
            record['dependencies'] = [DEFINITIONS[parent].stable_id for parent in record['dependencies']]
            record['authority'] = 'conservative-abbreviation-only'
            record['used_in_supplied_formulas'] = name in used
            definitions.append(record)
    expansion_edges = [{'kind': 'definition_uses_definition', 'source': record['id'], 'target': parent}
                       for record in definitions for parent in record['dependencies']]
    if require_sources() != before:
        raise NotationError('alignment-map inputs changed during exact source compaction')
    return {
        'schema': SCHEMA, 'authority': 'source-syntax-only', 'proof_acceptance_performed': False,
        'admission_performed': False, 'publication_performed': False,
        'registry_definition_count': 402, 'registry_expansion_edge_count': 876,
        'inherited_definition_count': 399, 'inherited_expansion_edge_count': 870,
        'new_definition_count': 3, 'nodes': nodes, 'definitions': definitions,
        'new_definition_ids': [item.stable_id for item in NEW_DEFINITIONS],
        'external_dependencies': sorted(external), 'external_dependencies_resolved': False,
        'edges': proof_edges + usage_edges + expansion_edges,
        'proof_dependency_count': len(proof_edges), 'definition_use_count': len(usage_edges),
        'definition_expansion_count': len(expansion_edges), 'used_definition_count': len(used),
        'proof_layers': layers, 'proof_paths': paths, 'path_policy': 'proof_dependency_edges_only',
        'proof_path_scope': 'supplied_theorems_only; external prerequisites unresolved',
        'subtraction_render_policy': 'literal permutation alias; unchanged compactor prefers prior AlignedAdd',
        'ordered_specs_sha256': specs_digest(rows), 'source_pins': before,
        'complete_dependency_cone_claimed': False, 'gcd_bezout_proved': False,
    }


def audit():
    return audit_rows(source_rows())


if __name__ == '__main__':
    print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True))
