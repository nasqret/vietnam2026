"""Conservative working divisibility definition and the combined source DAG.

All 398 predecessor definition objects are preserved. ND0342 expands only to
canonical target coefficients, an actual Q*D, and formal output equivalence.
This source map performs no proof acceptance, admission or publication.
"""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import MappingProxyType

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
INDUCTION_DIRECTORY = HERE.parent / 'prime-field-associativity-induction-v1'
if str(INDUCTION_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(INDUCTION_DIRECTORY))

import working_induction_notation as previous

shift = previous.shift
NotationError = shift.NotationError
SOURCE = HERE / 'prime_field_polynomial_divisibility_candidate.py'
SOURCES = {
    **previous.SOURCES,
    INDUCTION_DIRECTORY / 'working_induction_notation.py':
        (3979, '92b2c3bc4fcdae9368b6ed67ff341e3a47be9783697f528323b75ecd7481b8dd'),
    INDUCTION_DIRECTORY / 'test_working_induction_notation.py':
        (5696, 'acbaa17c1eaa7c8db96c399d5ccd47774bee31698c81646d7ea6b958d1a66f7b'),
    SOURCE: (15168, 'f544adedd3ce963e4a773e8582efcb0f91ba7491207c9792d477d452e854f2b8'),
    HERE / 'test_prime_field_polynomial_divisibility_candidate.py':
        (20043, '82460849735222acb22c120004226a9e0a91c0231f8ab960cc3657f0767400e3'),
}
DIVISIBILITY_SPECS_SHA256 = '2ee9efd3344ef213b2170f080ff541ca0a7a45a018ace9f2f7912cd301bc8bce'
SCHEMA = 'working-polynomial-right-divisibility-notation-audit-v1'
_NAME = re.compile(r'[A-Za-z][A-Za-z0-9_]*\Z')


def require_sources():
    records = {}
    for path, (size, digest) in SOURCES.items():
        if path.is_symlink() or not path.is_file():
            raise NotationError('a frozen divisibility-map input is not an ordinary file')
        raw = path.read_bytes()
        if len(raw) != size or sha256(raw).hexdigest() != digest:
            raise NotationError('a frozen divisibility-map source or independent test changed')
        records[path.relative_to(ROOT).as_posix()] = {'bytes': size, 'sha256': digest}
    return records


require_sources()
_specification = importlib.util.spec_from_file_location('working_divisibility_notation_source_v1', SOURCE)
if _specification is None or _specification.loader is None:
    raise NotationError('the exact divisibility source has no loader')
_candidate = importlib.util.module_from_spec(_specification)
_specification.loader.exec_module(_candidate)
PARAMETERS = ('p', 'db', 'dc', 'D', 'ab', 'ac', 'L')
RIGHT_DIVIDES = shift._definition(
    stable_id='ND0342', name='FpPolynomialRightDivides', parameters=PARAMETERS,
    template_source=_candidate.prime_field_polynomial_right_divides_relation(
        *PARAMETERS, tag='working_right_divides_definition', variables=PARAMETERS),
    summary='The target A is canonical and there are actual quotient and product triples Q,P '
            'such that Q*D=P and P is formally coefficient-equivalent to A. D is the right '
            'factor. Product lengths and beta encodings are independent; field evaluations '
            'or raw code equality do not replace formal equivalence. Primality, gcd existence '
            'and Bezout witnesses are not definition clauses.',
    category='constructive_polynomial_divisibility', priority='P2',
    conceptual_dependencies=('BetaPrefixInto', 'FpPolyProduct', 'PolynomialEquivalent'),
)
if (len(shift.DEFINITIONS) != 398 or RIGHT_DIVIDES.name in shift.DEFINITIONS
        or RIGHT_DIVIDES.stable_id in {row.stable_id for row in shift.DEFINITIONS.values()}):
    raise NotationError('divisibility notation shadows an inherited identity')
DEFINITIONS = MappingProxyType({**shift.DEFINITIONS, RIGHT_DIVIDES.name: RIGHT_DIVIDES})
REGISTRIES = (*shift.REGISTRIES, ('polynomial-divisibility', (RIGHT_DIVIDES,)))


def reviewed_registry():
    require_sources()
    records, order, layers = shift._registry(REGISTRIES)
    if (len(records) != 399 or sum(len(row['dependencies']) for row in records.values()) != 870
            or any(records[name]['id'] != item.stable_id for name, item in DEFINITIONS.items())):
        raise NotationError('the exact 399-definition/870-expansion working inventory changed')
    for name in RIGHT_DIVIDES.conceptual_dependencies:
        reading = shift._FormulaCompactor((DEFINITIONS[name],)).compact(RIGHT_DIVIDES.template_source)
        if DEFINITIONS[name].stable_id not in reading['statement_definition_uses']:
            raise NotationError('a declared divisibility expansion parent has no actual occurrence')
    return records, order, layers


def definition_closure(names):
    if type(names) is not tuple or any(type(name) is not str or not name for name in names):
        raise NotationError('definition names must be an exact tuple of nonempty text')
    seen, active, output = set(), set(), []

    def visit(name):
        if name in seen:
            return
        if name in active or name not in DEFINITIONS:
            raise NotationError('unknown or cyclic divisibility definition')
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
    new = _candidate.make_prime_field_polynomial_divisibility_candidate_theorems(shift.TheoremSpec)
    if (len(new) != 7 or sum(len(row.dependencies) for row in new) != 20
            or sum(len(row.script) for row in new) != 487 or specs_digest(new) != DIVISIBILITY_SPECS_SHA256):
        raise NotationError('the exact seven divisibility specifications changed')
    rows = (*previous.source_rows(), *new)
    if (len(rows) != 44 or sum(len(row.dependencies) for row in rows) != 199
            or sum(len(row.script) for row in rows) != 4790 or require_sources() != before):
        raise NotationError('the exact combined44 source inventory changed')
    return rows


def audit_rows(rows):
    """Only exact syntax; paths ignore all definition arrows and external nodes."""
    before = require_sources()
    if type(rows) is not tuple or not rows or any(type(row) is not shift.TheoremSpec for row in rows):
        raise NotationError('an exact nonempty tuple of theorem specifications is required')
    if any(type(row.name) is not str or _NAME.fullmatch(row.name) is None for row in rows):
        raise NotationError('theorem names must be distinct identifiers')
    names = {row.name for row in rows}
    if len(names) != len(rows):
        raise NotationError('theorem names must be distinct identifiers')
    records, order, _layers = reviewed_registry()
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
    selected = {item.name for item in definition_closure(tuple(sorted(used)))}
    definitions = []
    for name in order:
        if name in selected:
            record = dict(records[name])
            record['dependencies'] = [DEFINITIONS[parent].stable_id for parent in record['dependencies']]
            record['authority'] = 'conservative-abbreviation-only'
            definitions.append(record)
    expansion_edges = [{'kind': 'definition_uses_definition', 'source': record['id'], 'target': parent}
                       for record in definitions for parent in record['dependencies']]
    if require_sources() != before:
        raise NotationError('divisibility-map bytes changed during source compaction')
    return {
        'schema': SCHEMA, 'authority': 'source-syntax-only', 'proof_acceptance_performed': False,
        'admission_performed': False, 'publication_performed': False,
        'registry_definition_count': 399, 'registry_expansion_edge_count': 870,
        'additional_definitions_beyond_shift': 1, 'nodes': nodes, 'definitions': definitions,
        'external_dependencies': sorted(external), 'external_dependencies_resolved': False,
        'edges': proof_edges + usage_edges + expansion_edges,
        'proof_dependency_count': len(proof_edges), 'definition_use_count': len(usage_edges),
        'definition_expansion_count': len(expansion_edges),
        'proof_layers': layers, 'proof_paths': paths, 'path_policy': 'proof_dependency_edges_only',
        'proof_path_scope': 'supplied_theorems_only; external prerequisites unresolved',
        'ordered_specs_sha256': specs_digest(rows), 'source_pins': before,
        'full_induction_included': any(row.name == 'prime_field_polynomial_convolution_associative_equivalent'
                                       for row in rows),
        'associativity_proved': False, 'divisibility_proved': False, 'gcd_bezout_proved': False,
    }


def audit():
    return audit_rows(source_rows())


if __name__ == '__main__':
    print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True))
