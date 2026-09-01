"""Conservative source-only notation for 95 Euclidean-algebra source rows.

All 402 predecessor definition objects and 876 expansion arrows are reused
unchanged. ND0346 is a grouped pair of actual right-divisibility relations;
ND0347 is an actual pair of proper products and an aligned sum. Neither
definition asserts existence of a gcd, greatestness, or an algebraic law.

This module checks exact source/AST data only. Proof prerequisites, actual
definition occurrences, and conservative expansion arrows stay distinct.
No proof checker, Alpha catalogue, saved receipt, or live capability is used.
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
WORKING = HERE.parent
PRIOR_DIRECTORY = WORKING / 'prime-field-aligned-notation-v1'
PRIOR_SOURCE = PRIOR_DIRECTORY / 'working_aligned_notation.py'
PRIOR_PIN = (15828, '5b414d103a74652f8f0389140cf48c30d07593a02d89a7e7e0418ee69554b706')
PRIOR_TEST = PRIOR_DIRECTORY / 'test_working_aligned_notation.py'
PRIOR_TEST_PIN = (19072, '2a10495e8bf87064e4f65ce488884fee2bacd658e0826919f4c9cb210306f63f')
PRIOR_SPECS_SHA256 = '03d800eaddc4ef197ddb09781e1dd3d707602e4de5ee37a1d53129013df773c1'
SCHEMA = 'working-polynomial-euclidean-notation-audit-v1'
_NAME = re.compile(r'[A-Za-z][A-Za-z0-9_]*\Z')


def _pin(path, expected):
    if path.is_symlink() or not path.is_file():
        raise ValueError('a Euclidean-notation input is not an ordinary file')
    raw = path.read_bytes()
    if (len(raw), sha256(raw).hexdigest()) != expected:
        raise ValueError('an exact Euclidean-notation source or independent test changed')
    return {'bytes': expected[0], 'sha256': expected[1]}


def _load_source(path, private_name):
    """Execute actual source without creating or replacing a module alias."""
    previous_owner = sys.modules.get(private_name)
    had_owner = private_name in sys.modules
    specification = importlib.util.spec_from_file_location(private_name, path)
    if specification is None or specification.loader is None:
        raise ValueError('an exact Euclidean-notation source has no loader')
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    if (private_name in sys.modules) != had_owner or sys.modules.get(private_name) is not previous_owner:
        raise ValueError('a private source loader changed a foreign module owner')
    return module


_pin(PRIOR_SOURCE, PRIOR_PIN)
_pin(PRIOR_TEST, PRIOR_TEST_PIN)
previous = _load_source(PRIOR_SOURCE, '_working_euclidean_notation_prior68')
shift = previous.shift
NotationError = previous.NotationError
TheoremSpec = previous.TheoremSpec

# label, directory, module, factory, rows, direct edges, commands, source pin,
# exact ordered specifications. These are syntax identities, not proof pins.
FACTORIES = (
    ('algebra', 'prime-field-aligned-algebra-v1', 'prime_field_polynomial_aligned_algebra_candidate',
     'make_prime_field_polynomial_aligned_algebra_candidate_theorems', 4, 29, 947,
     (16013, 'a68de84439afb5f6dd87f1d47449c0bce8dd53a66346c00cc1b7645fb80b2390'),
     '0db1ddc08762db5e207469343143a7ead24de983e8f9a21473592a8d6c97d6f4'),
    ('identity', 'prime-field-euclidean-identity-v1', 'prime_field_polynomial_euclidean_identity_candidate',
     'make_prime_field_polynomial_euclidean_identity_candidate_theorems', 2, 14, 236,
     (11235, '8efdcd2abf2143891b79edcb3fc90d7126ae69507c1c631ed33b497172ffdb77'),
     'f992bc15fd84b7f3ba9b0f28c0219cb97a53c47c669a9563b087e7a3c535ab27'),
    ('distributivity', 'prime-field-aligned-distributivity-v1', 'prime_field_polynomial_aligned_distributivity_candidate',
     'make_prime_field_polynomial_aligned_distributivity_candidate_theorems', 2, 10, 389,
     (8518, '7d535939e24fe6d82158c485533b2ff6934f4d897b6141fde6c50b4fec9788ba'),
     '22b9e7ed76b79f0210eee74433a965db62cc5a4b688c3ab2cf0f236b1dca5719'),
    ('left_constant', 'prime-field-left-constant-v1', 'prime_field_polynomial_left_constant_candidate',
     'make_prime_field_polynomial_left_constant_candidate_theorems', 6, 32, 470,
     (17620, '9a7a4de30f5f389bcabc2e6267a0d2cc5dc5f061059dcea303a0a03dab58509a'),
     '736cd0d7d21f33ac50a189f66a7457909042c83917d9e9cfc2d4932c6fe06836'),
    ('normalization', 'prime-field-euclidean-normalization-v1', 'prime_field_polynomial_euclidean_normalization_candidate',
     'make_prime_field_polynomial_euclidean_normalization_candidate_theorems', 5, 25, 385,
     (16401, 'd2cddfe42dc0d22104dc4e85e95116222914df11ac840d2082a4ff2e462f146f'),
     '815b67478a8c42bd854002317e31ab5e77739551f19516dfc923b7fe66d0ce74'),
    ('transport', 'prime-field-euclidean-transport-v1', 'prime_field_polynomial_euclidean_transport_candidate',
     'make_prime_field_polynomial_euclidean_transport_candidate_theorems', 5, 32, 739,
     (18256, '9a589d1749eb38d30d1a24364bc4d66f7df0efb59247527f7831f97557da9c30'),
     'aba201eca067048dc65b5a2f7f6affd415c6ebd639c35bc613503227a65059b8'),
    ('bezout', 'prime-field-bezout-backward-v1', 'prime_field_polynomial_bezout_backward_candidate',
     'make_prime_field_polynomial_bezout_backward_candidate_theorems', 3, 20, 729,
     (18747, 'c3903482000c957ac77f84a43a85d135e4caa19e4484328035f91b82cbf3a702'),
     'bbab74ad9d4ecfe3b01e97ab75dccd532fc23e22a5cb275a68963f15dbf57564'),
)
SOURCES = {
    **previous.SOURCES,
    PRIOR_SOURCE: PRIOR_PIN,
    PRIOR_TEST: PRIOR_TEST_PIN,
    **{WORKING / directory / (module + '.py'): pin
       for _label, directory, module, _factory, _count, _edges, _commands, pin, _digest in FACTORIES},
    WORKING / 'prime-field-aligned-algebra-v1/test_prime_field_polynomial_aligned_algebra_candidate.py':
        (10321, '11f096addd3afb6301e98d61cf359b833754b29eebd7abf61a9e85b3da06d073'),
    WORKING / 'prime-field-aligned-algebra-v1/test_prime_field_polynomial_aligned_algebra_contracts.py':
        (12694, '09c34419021d60ad8c78ea5b0430bc17a595fb2b3d97469e1e375a5f55697b2d'),
    WORKING / 'prime-field-euclidean-identity-v1/test_prime_field_polynomial_euclidean_identity_candidate.py':
        (31004, 'e7225749330ccd9392e584196057ab3a2547856764d25296bee775f9eb62e2c0'),
    WORKING / 'prime-field-aligned-distributivity-v1/test_prime_field_polynomial_aligned_distributivity_candidate.py':
        (22358, '5fa4ff32894dcbe7f2010ae526731e88cbe4c2307e1043b56da326c487c26039'),
    WORKING / 'prime-field-euclidean-transport-v1/test_prime_field_polynomial_transport_models.py':
        (25634, '0c814915ee8b8f6ecc8ffb945699cd4888fa4c4cf86e6b4cb077063407f5cfab'),
    WORKING / 'prime-field-left-constant-v1/test_prime_field_polynomial_left_constant_candidate.py':
        (27847, 'cc93a6d0b8d1ff3eae9bc0b16527936301a7a15e13e7baae3cf818a919cc6a60'),
    WORKING / 'prime-field-euclidean-normalization-v1/test_prime_field_polynomial_euclidean_normalization_candidate.py':
        (29037, 'e291538321e9d078a8b0044bacfb50d46b5eea59b2126001a2129c69de342791'),
}


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
CANDIDATES = {
    label: _load_source(WORKING / directory / (module + '.py'), '_working_euclidean_notation_' + label)
    for label, directory, module, _factory, _count, _edges, _commands, _pin_value, _digest in FACTORIES
}
COMMON_PARAMETERS = ('p', 'db', 'dc', 'D', 'ab', 'ac', 'L', 'bb', 'bc', 'M')
BEZOUT_PARAMETERS = ('p', 'ab', 'ac', 'A', 'bb', 'bc', 'B', 'gb', 'gc', 'G',
                     'ub', 'uc', 'U', 'vb', 'vc', 'V')


def _new_definition(identifier, name, parameters, builder, summary, parents):
    return shift._definition(
        stable_id=identifier, name=name, parameters=parameters,
        template_source=builder(*parameters, tag='working_euclidean_definition', variables=parameters),
        summary=summary, category='constructive_polynomial_euclidean_transport', priority='P2',
        conceptual_dependencies=parents,
    )


COMMON_RIGHT_DIVISOR = _new_definition(
    'ND0346', 'FpPolynomialCommonRightDivisor', COMMON_PARAMETERS,
    CANDIDATES['transport'].prime_field_polynomial_common_right_divisor_relation,
    'D is an actual right divisor of both canonical targets A and B, using two '
    'independent quotient/product witness sets. The two RightDivides clauses '
    'form one literal conjunction. Existence of a common divisor, greatestness, '
    'primality and a gcd theorem are not definition clauses.',
    ('FpPolynomialRightDivides',),
)
BEZOUT_REPRESENTATION = _new_definition(
    'ND0347', 'FpPolynomialBezoutRepresentation', BEZOUT_PARAMETERS,
    CANDIDATES['bezout'].prime_field_polynomial_bezout_representation_relation,
    'There are actual proper products U*A=P and V*B=Q, and an actual aligned '
    'sum P+Q=G. Codes and all five original representation lengths remain '
    'independent. This is representation data, not a Bezout-existence theorem, '
    'a gcd or greatestness result, evaluation equality, or equality of raw codes.',
    ('FpPolyProduct', 'FpPolynomialAlignedAdd'),
)
NEW_DEFINITIONS = (COMMON_RIGHT_DIVISOR, BEZOUT_REPRESENTATION)
_known = dict(previous.DEFINITIONS)
_identifiers = {item.stable_id for item in _known.values()}
if len(_known) != 402 or len(_identifiers) != 402:
    raise NotationError('the exact 402-definition predecessor changed')
for _item in NEW_DEFINITIONS:
    if (_item.name in _known or _item.stable_id in _identifiers
            or len(_item.conceptual_dependencies) != len(set(_item.conceptual_dependencies))
            or not set(_item.conceptual_dependencies) <= _known.keys()):
        raise NotationError('Euclidean notation shadows an identity or has a non-prior parent')
    _known[_item.name] = _item
    _identifiers.add(_item.stable_id)
DEFINITIONS = MappingProxyType(_known)
REGISTRIES = (*previous.REGISTRIES, ('polynomial-euclidean-transport', NEW_DEFINITIONS))


def reviewed_registry():
    require_sources()
    records, order, layers = shift._registry(REGISTRIES)
    if (len(records) != 404 or sum(len(row['dependencies']) for row in records.values()) != 879
            or any(records[name]['id'] != item.stable_id for name, item in DEFINITIONS.items())
            or any(DEFINITIONS[name] is not item for name, item in previous.DEFINITIONS.items())
            or sum(len(item.conceptual_dependencies) for item in previous.DEFINITIONS.values()) != 876):
        raise NotationError('the exact 404-definition/879-expansion inventory changed')
    for definition in NEW_DEFINITIONS:
        for parent in definition.conceptual_dependencies:
            reading = shift._FormulaCompactor((DEFINITIONS[parent],)).compact(definition.template_source)
            if DEFINITIONS[parent].stable_id not in reading['statement_definition_uses']:
                raise NotationError('a declared Euclidean parent has no literal AST occurrence')
    return records, order, layers


def definition_closure(names):
    if type(names) is not tuple or any(type(name) is not str or not name for name in names):
        raise NotationError('definition roots must be an exact tuple of nonempty names')
    seen, active, output = set(), set(), []

    def visit(name):
        if name in seen:
            return
        if name in active or name not in DEFINITIONS:
            raise NotationError('unknown or cyclic Euclidean definition')
        active.add(name)
        for parent in DEFINITIONS[name].conceptual_dependencies:
            visit(parent)
        active.remove(name)
        seen.add(name)
        output.append(DEFINITIONS[name])

    for name in names:
        visit(name)
    return tuple(output)


specs_digest = previous.specs_digest


def source_rows():
    before = require_sources()
    prior = previous.source_rows()
    if len(prior) != 68 or specs_digest(prior) != PRIOR_SPECS_SHA256:
        raise NotationError('the exact inherited68 specification prefix changed')
    rows = list(prior)
    for label, _directory, _module, factory, count, edges, commands, _source_pin, digest in FACTORIES:
        actual = getattr(CANDIDATES[label], factory)(TheoremSpec)
        if (type(actual) is not tuple or len(actual) != count
                or any(type(row) is not TheoremSpec for row in actual)
                or sum(len(row.dependencies) for row in actual) != edges
                or sum(len(row.script) for row in actual) != commands
                or specs_digest(actual) != digest):
            raise NotationError('an exact Euclidean component specification inventory changed')
        rows.extend(actual)
    result = tuple(rows)
    if (len(result) != 95 or sum(len(row.dependencies) for row in result) != 436
            or sum(len(row.script) for row in result) != 10062 or require_sources() != before):
        raise NotationError('the exact combined95 source inventory changed')
    return result


def audit_rows(rows):
    """Exact conservative compaction, with every external prerequisite open."""
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
        raise NotationError('theorem names cannot shadow definition identities')
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
    # Keep every reviewed new alias visible without inventing occurrence
    # edges when deterministic compaction chooses an equivalent older name.
    selected = {item.name for item in definition_closure(tuple(sorted(
        used | {item.name for item in NEW_DEFINITIONS} | {item.name for item in previous.NEW_DEFINITIONS})))}
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
        raise NotationError('Euclidean-map inputs changed during exact source compaction')
    return {
        'schema': SCHEMA, 'authority': 'source-syntax-only', 'proof_acceptance_performed': False,
        'admission_performed': False, 'publication_performed': False,
        'registry_definition_count': 404, 'registry_expansion_edge_count': 879,
        'inherited_definition_count': 402, 'inherited_expansion_edge_count': 876,
        'new_definition_count': 2, 'nodes': nodes, 'definitions': definitions,
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
        'euclidean_algorithm_constructed': False, 'G091_closed': False,
    }


def audit():
    return audit_rows(source_rows())


if __name__ == '__main__':
    print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True))
