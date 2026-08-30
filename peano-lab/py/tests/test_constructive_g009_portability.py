"""Pure G009 production-portability regressions; no proof acceptance.

Only source ASTs, physical reads of explicitly non-proof temporary files,
fingerprint fragments, path guards and object lifetimes are exercised here.
No candidate factory, proof checker, audit worker, catalogue, reader build,
publication entry point or successful proof report is imported or simulated.
The 277 mandatory same-live reader case IDs remain in a separate suite;
three approved graph instances now include compact and narrow-link checks.
"""

from __future__ import annotations

import ast
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
import gc
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit
import weakref

import pytest


HERE = Path(__file__).resolve().parent
# This source-only suite can run beside the isolated production copies or
# after adoption in peano-lab/py/tests. It never imports either script tree.
SCRIPTS = HERE if (HERE/'constructive_g009_support.py').is_file() else HERE.parents[2]/'scripts'
ORIGINAL_CALLABLE_AST_SHA256 = {
    "build_constructive_g009_explorer.py": "663865c7bb2d215ef112fbad62961d105525a1036ea77d281de26c7e4d0ee645",
    "check_constructive_g009.py": "ad32e05749cb6aae4758dff758ad5e3bd290db5601d8be558e9b4fb02e398615",
    "constructive_g009_checkpoints.py": "f35b2396496012b906c83da812a7bf19fa3dd9739e8fa5a7df296b939595bb1b",
    "constructive_g009_definition_graph.py": "229c4b76644ef21d8989012bc45737b0dc7c24c91962d0d98dfd1bc89ed6f764",
    "constructive_g009_definitions.py": "a5ab9295078b75a0cf157556dc83ef0f1cbd3ceb7cfa05179b7bd47b77819906",
    "constructive_g009_support.py": "9921b624ed424691478cbe92040e347a39f0078d3bc9a535e69acef33286801d",
    "export_constructive_g009.py": "cc2c7335db2845c2b12727d6b652e81ffe8e4b842eb95187c6752f1ca05ece66",
    "extend_constructive_g009_campaign.py": "2e23e3f1d1d8ff1ab34380fbe9dad666e87ef900bfc5ee8988fc0cdaa3ecf2f1",
    "profile_constructive_g009_presentation.py": "dc997828862c6ca4dd51ecca9057bbc7dc11af6a5f7209cb7dcbaf8000be3168",
    "stage_constructive_g009_publication.py": "63f843aa5850a5640c46b19c3dcfe6fadfef363a84a0c6c99574e5f4deab397f",
    "test_constructive_g009_explorer.py": "603425b1a92a0912887b6f8cb12d899ab43aec5bfd1a7c5279175431b7b53fd0"
}


def _source_path(name):
    return HERE/name if name.startswith('test_') else SCRIPTS/name


def _tree(name):
    return ast.parse(_source_path(name).read_bytes(), filename=name)


def _function(name, function):
    return next(node for node in _tree(name).body
                if isinstance(node, ast.FunctionDef) and node.name == function)


def _assigned_names(node):
    if not isinstance(node, ast.Assign):
        return set()
    return {item.id for target in node.targets for item in ast.walk(target)
            if isinstance(item, ast.Name)}


def _name_call(node, name):
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name


def _attribute_call(node, owner, attribute):
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == owner and node.func.attr == attribute)


def _physical_helpers(root):
    """Extract only real byte/path helpers; there is no verifier in this scope."""
    wanted = {'G009Error', 'FilePin', 'canonical', '_repository_path',
              '_file_identity', '_bounded_stream', 'bounded_bytes', 'check_pin'}
    nodes = [deepcopy(node) for node in _tree('constructive_g009_support.py').body
             if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in wanted]
    assert {node.name for node in nodes} == wanted
    namespace = {'__name__': __name__, 'ROOT': root, 'Path': Path,
                 'contextmanager': contextmanager, 'dataclass': dataclass,
                 'sha256': sha256, 'json': json, 'os': os, 're': re, 'stat': stat,
                 'MAX_CATALOG_COMPONENT_BYTES': 64*1024*1024}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<physical helpers only>', 'exec'), namespace)
    return SimpleNamespace(**namespace)


def _layout(tmp_path, name):
    root = tmp_path.resolve()/name
    (root/'scripts').mkdir(parents=True)
    (root/'peano-lab/py/peano_lab/library').mkdir(parents=True)
    (root/'peano-lab/py/tests').mkdir(parents=True)
    (root/'research/arithmetic-library/artifacts').mkdir(parents=True)
    paths = ('scripts/control.py', 'research/arithmetic-library/artifacts/provider.json',
             'peano-lab/py/tests/reader_test.py', 'research/arithmetic-library/reader.md')
    for index, relative in enumerate(paths):
        (root/relative).write_bytes(('TRANSPORT INPUT ONLY; NOT A PROOF: '+str(index)+'\n').encode())
    return root, paths


@pytest.mark.parametrize('split_layout', (False, True))
def test_source_reader_uses_the_actual_test_directory_after_adoption(tmp_path, split_layout):
    root, _ = _layout(tmp_path, 'layout')
    tests = root/'peano-lab/py/tests' if split_layout else root/'scripts'
    scripts = root/'scripts'
    test_name = 'test_constructive_g009_explorer.py'
    script_name = 'check_constructive_g009.py'
    (tests/test_name).write_bytes(b'UI_INPUT_ONLY = True\n')
    (scripts/script_name).write_bytes(b'CONTROL_INPUT_ONLY = True\n')
    if split_layout:
        (scripts/test_name).write_bytes(b'THIS IS THE WRONG DIRECTORY AND IS NOT PYTHON\n')
    own_tree = ast.parse(Path(__file__).read_bytes())
    nodes = [deepcopy(node) for node in own_tree.body if isinstance(node, ast.FunctionDef)
             and node.name in {'_source_path', '_tree'}]
    assert len(nodes) == 2
    namespace = {'HERE': tests, 'SCRIPTS': scripts, 'ast': ast}
    exec(compile(ast.Module(body=nodes,type_ignores=[]), '<split-layout source reads only>', 'exec'), namespace)
    assert namespace['_source_path'](test_name) == tests/test_name
    assert namespace['_source_path'](script_name) == scripts/script_name
    assert namespace['_tree'](test_name).body[0].targets[0].id == 'UI_INPUT_ONLY'
    assert namespace['_tree'](script_name).body[0].targets[0].id == 'CONTROL_INPUT_ONLY'


def _fragments(root, controls, providers, display):
    """Execute only the three actual fingerprint expressions on physical bytes.

    This is intentionally not state_binding(), _render_binding(), a verified
    state, a proof report, or a reader-producing path.
    """
    physical = _physical_helpers(root)
    state = _function('constructive_g009_support.py', 'state_binding')
    append = next(node for node in ast.walk(state)
                  if isinstance(node, ast.Expr) and _attribute_call(node.value, 'controls', 'append'))
    dictionary = next(node for node in ast.walk(state) if isinstance(node, ast.Dict)
                      and any(isinstance(key, ast.Constant) and key.value == 'provider_paths'
                              for key in node.keys))
    provider_value = next(value for key, value in zip(dictionary.keys, dictionary.values)
                          if isinstance(key, ast.Constant) and key.value == 'provider_paths')
    render = _function('build_constructive_g009_explorer.py', '_render_binding')
    extend = next(node for node in ast.walk(render)
                  if isinstance(node, ast.Expr) and _attribute_call(node.value, 'records', 'extend'))
    environment = {
        '_repository_path': physical._repository_path,
        'support': SimpleNamespace(_repository_path=physical._repository_path),
        'sha256': sha256, '_digest': lambda raw: sha256(raw).hexdigest(),
        '_source': lambda path: physical.bounded_bytes(path, 4096),
        'controls': [], 'records': [], 'providers': providers, 'paths': display,
    }
    for path in controls:
        environment.update(path=path, raw=physical.bounded_bytes(path, 4096))
        exec(compile(ast.Module(body=[deepcopy(append)], type_ignores=[]),
                     '<control-label expression only>', 'exec'), environment)
    provider_labels = eval(compile(ast.Expression(body=deepcopy(provider_value)),
                                   '<provider-label expression only>', 'eval'), environment)
    exec(compile(ast.Module(body=[deepcopy(extend)], type_ignores=[]),
                 '<display-label expression only>', 'exec'), environment)
    return physical.canonical({'controls': environment['controls'],
                               'provider_paths': provider_labels,
                               'inputs': environment['records']})


def test_actual_three_fingerprint_fragments_are_relocation_stable(tmp_path):
    first, names = _layout(tmp_path, 'first-repository')
    second, same_names = _layout(tmp_path, 'relocated repository')
    assert same_names == names
    first_value = _fragments(first, (first/names[0],), (first/names[1],),
                             tuple(first/name for name in names[2:]))
    second_value = _fragments(second, (second/names[0],), (second/names[1],),
                              tuple(second/name for name in names[2:]))
    assert first_value == second_value
    assert sha256(first_value).digest() == sha256(second_value).digest()
    value = json.loads(first_value)
    assert value['controls'][0][0] == names[0]
    assert value['provider_paths'] == [names[1]]
    assert [row[0] for row in value['inputs']] == list(names[2:])
    assert str(first).encode() not in first_value and str(second).encode() not in second_value


@pytest.mark.parametrize('site', ('control', 'display'))
def test_relative_identity_still_fingerprints_each_actual_byte(tmp_path, site):
    first, names = _layout(tmp_path, 'one')
    second, _ = _layout(tmp_path, 'two')
    selected = names[0] if site == 'control' else names[2]
    (second/selected).write_bytes(b'CHANGED TRANSPORT BYTES, STILL NOT A PROOF\n')
    values = [_fragments(root, (root/names[0],), (root/names[1],),
                         tuple(root/name for name in names[2:])) for root in (first, second)]
    assert values[0] != values[1]


@pytest.mark.parametrize('site', ('control', 'provider', 'display'))
def test_each_actual_label_site_rejects_a_foreign_existing_file(tmp_path, site):
    root, names = _layout(tmp_path, 'root')
    foreign, _ = _layout(tmp_path, 'root-sibling')
    controls, providers, display = (root/names[0],), (root/names[1],), (root/names[2],)
    if site == 'control':
        controls = (foreign/names[0],)
    elif site == 'provider':
        providers = (foreign/names[1],)
    else:
        display = (foreign/names[2],)
    with pytest.raises(ValueError, match='outside the repository'):
        _fragments(root, controls, providers, display)


@pytest.mark.parametrize('case', ('relative', 'root', 'parent', 'prefix-sibling',
                                  'lexical-parent', 'absolute-root', 'string',
                                  'boolean', 'integer', 'none'))
def test_repository_labels_fail_closed_for_foreign_or_nonfile_inputs(tmp_path, case):
    root, _ = _layout(tmp_path, 'root')
    physical = _physical_helpers(root)
    cases = {
        'relative': Path('scripts/control.py'),
        'root': root, 'parent': root.parent,
        'prefix-sibling': root.with_name(root.name+'-other')/'scripts/control.py',
        'lexical-parent': root/'scripts/..'/'control.py',
        'absolute-root': Path('/'), 'string': str(root/'scripts/control.py'),
        'boolean': True, 'integer': 1, 'none': None,
    }
    with pytest.raises(physical.G009Error):
        physical._repository_path(cases[case])


@pytest.mark.parametrize('case', ('leaf-symlink', 'ancestor-symlink', 'missing', 'directory'))
def test_a_relative_label_never_replaces_the_original_physical_read_guard(tmp_path, case):
    root, names = _layout(tmp_path, 'root')
    physical = _physical_helpers(root)
    if case == 'leaf-symlink':
        path = root/'scripts/linked.py'
        path.symlink_to(root/names[0])
    elif case == 'ancestor-symlink':
        (root/'linked').symlink_to(root/'scripts', target_is_directory=True)
        path = root/'linked/control.py'
    elif case == 'missing':
        path = root/'scripts/missing.py'
    else:
        path = root/'scripts'
    assert physical._repository_path(path) == path.relative_to(root).as_posix()
    with pytest.raises(physical.G009Error):
        physical.bounded_bytes(path, 4096)


def test_provider_byte_authentication_survives_relative_labeling(tmp_path):
    first, names = _layout(tmp_path, 'one')
    second, _ = _layout(tmp_path, 'two')
    payload = (first/names[1]).read_bytes()
    for root in (first, second):
        physical = _physical_helpers(root)
        pin = physical.FilePin(names[1], len(payload), sha256(payload).hexdigest())
        physical.check_pin(pin, root, 4096)
    (second/names[1]).write_bytes(b'X'*len(payload))
    physical = _physical_helpers(second)
    pin = physical.FilePin(names[1], len(payload), sha256(payload).hexdigest())
    assert physical._repository_path(second/names[1]) == names[1]
    with pytest.raises(physical.G009Error, match='bytes changed'):
        physical.check_pin(pin, second, 4096)


def _bootstrap(name, filename, root):
    selected = []
    names = {'HERE', 'ROOT', 'MATH_DIRECTORY', 'IN_REPOSITORY',
             'OUTPUT', 'TEST_FILE', 'CAMPAIGN_TEST_FILE', 'RFC', 'READER'}
    for node in _tree(name).body:
        if _assigned_names(node) & names:
            selected.append(deepcopy(node))
        elif (isinstance(node, ast.If)
              and any(isinstance(part, ast.Constant) and isinstance(part.value, str)
                      and 'must reside in' in part.value for part in ast.walk(node))):
            selected.append(deepcopy(node))
    environment = {'__file__': str(filename), 'Path': Path,
                   'support': SimpleNamespace(ROOT=root)}
    exec(compile(ast.Module(body=selected, type_ignores=[]), '<path bootstrap only>', 'exec'),
         environment)
    return environment


@pytest.mark.parametrize('name', ('constructive_g009_support.py', 'constructive_g009_definitions.py',
                                  'build_constructive_g009_explorer.py',
                                  'stage_constructive_g009_publication.py',
                                  'test_constructive_g009_explorer.py'))
def test_production_path_bootstrap_uses_only_its_actual_repository(tmp_path, name):
    root, _ = _layout(tmp_path, 'relocated-root')
    directory = root/'peano-lab/py/tests' if name.startswith('test_') else root/'scripts'
    environment = _bootstrap(name, directory/name, root)
    assert environment['ROOT'] == root
    if 'MATH_DIRECTORY' in environment:
        assert environment['MATH_DIRECTORY'] == root/'peano-lab/py/peano_lab/library'
    if 'OUTPUT' in environment:
        assert environment['OUTPUT'] == root/'book/_static/constructive-g009-explorer'
        assert environment['TEST_FILE'] == root/'peano-lab/py/tests/test_constructive_g009_explorer.py'
        assert environment['CAMPAIGN_TEST_FILE'] == root/'peano-lab/py/tests/test_constructive_g009_campaign.py'
        assert environment['RFC'] == root/'research/arithmetic-library/g009-multiplicative-convolution-rfc-v1.md'
    if 'READER' in environment:
        assert environment['READER'] == root/'book/_static/constructive-g009-explorer'


@pytest.mark.parametrize('name', ('constructive_g009_support.py', 'constructive_g009_definitions.py',
                                  'build_constructive_g009_explorer.py',
                                  'stage_constructive_g009_publication.py',
                                  'test_constructive_g009_explorer.py'))
def test_production_path_bootstrap_rejects_scratch_placement(tmp_path, name):
    root, _ = _layout(tmp_path, 'repository')
    other = tmp_path.resolve()/'scratch'
    other.mkdir()
    with pytest.raises(RuntimeError, match='must reside'):
        _bootstrap(name, other/name, root)


@pytest.mark.parametrize('case', ('foreign-module', 'foreign-here', 'scratch', 'nonboolean'))
def test_profile_guard_rejects_foreign_or_unsealed_scratch_reader_metadata(tmp_path, case):
    """Guard fragment only: no profile, actual reader or acceptance is called."""
    root, _ = _layout(tmp_path, 'repo')
    profile = _function('profile_constructive_g009_presentation.py', 'profile')
    assignment = next(node for node in profile.body if 'expected_reader' in _assigned_names(node))
    index = profile.body.index(assignment)
    guard = profile.body[index+1]
    assert isinstance(guard, ast.If)
    reader = SimpleNamespace(__file__=str(root/'scripts/build_constructive_g009_explorer.py'),
                             HERE=root/'scripts', ROOT=root, IN_REPOSITORY=True)
    if case == 'foreign-module':
        reader.__file__ = str(root/'foreign/build_constructive_g009_explorer.py')
    elif case == 'foreign-here':
        reader.HERE = root/'elsewhere'
    elif case == 'scratch':
        reader.IN_REPOSITORY = False
    else:
        reader.IN_REPOSITORY = 1
    environment = {'__file__': str(root/'scripts/profile_constructive_g009_presentation.py'),
                   'Path': Path, 'reader': reader, 'ProfileError': RuntimeError}
    with pytest.raises(RuntimeError, match='exact production sibling'):
        exec(compile(ast.Module(body=deepcopy([assignment, guard]), type_ignores=[]),
                     '<diagnostic path guard only>', 'exec'), environment)


def _memory_probe(*, discard_target):
    """Run the actual decode/delete/GC expressions on non-proof objects only."""
    function = _function('build_constructive_g009_explorer.py', '_render_files')
    decode = next(node for node in function.body if isinstance(node, ast.Assign)
                  and _name_call(node.value, 'decode_proof_bundle'))
    discard = next(node for node in function.body if isinstance(node, ast.Delete)
                   and any(isinstance(target, ast.Name) and target.id == 'bundle'
                           for target in node.targets))
    collect = next(node for node in function.body if isinstance(node, ast.Expr)
                   and _attribute_call(node.value, 'gc', 'collect'))
    body = deepcopy([decode, discard, collect])
    if not discard_target:
        # Deliberately reproduce the old memory-only defect, never a proof path.
        body[1].targets = [ast.Name(id='bundle', ctx=ast.Del())]
    body.append(ast.Return(value=ast.Call(func=ast.Name(id='after_release', ctx=ast.Load()),
                                         args=[], keywords=[])))
    wrapper = ast.parse('def memory_only(decode_proof_bundle, payload, gc, after_release):\n    pass\n')
    wrapper.body[0].body = body
    ast.fix_missing_locations(wrapper)
    namespace = {}
    exec(compile(wrapper, '<non-proof memory-only expressions>', 'exec'), namespace)
    references = {}

    class NonProofMemoryObject:
        pass

    def objects_only(_text):
        target = NonProofMemoryObject()
        target.cycle = target
        bundle = NonProofMemoryObject()
        bundle.target = target
        bundle.cycle = bundle
        references.update(bundle=weakref.ref(bundle), target=weakref.ref(target))
        return bundle, target

    result = namespace['memory_only'](objects_only, b'NOT PROOF DATA', gc,
                                     lambda: tuple(references[key]() is None
                                                   for key in ('bundle', 'target')))
    gc.collect()
    return result


def test_both_decoded_objects_are_released_before_the_catalogue_phase():
    function = _function('build_constructive_g009_explorer.py', '_render_files')
    body = function.body
    decoded = next(index for index, node in enumerate(body) if isinstance(node, ast.Assign)
                   and _name_call(node.value, 'decode_proof_bundle'))
    corpus = next(index for index, node in enumerate(body) if isinstance(node, ast.Assign)
                  and _name_call(node.value, '_corpus'))
    discarded = next(index for index, node in enumerate(body) if isinstance(node, ast.Delete))
    collected = next(index for index, node in enumerate(body) if isinstance(node, ast.Expr)
                     and _attribute_call(node.value, 'gc', 'collect'))
    atlas = next(index for index, node in enumerate(body)
                 if any(isinstance(part, ast.Attribute) and part.attr == 'build_files_for_verified_reader'
                        for part in ast.walk(node)))
    assert decoded < corpus < discarded < collected < atlas
    assert {node.id for node in body[discarded].targets} == {'bundle', 'target'}
    assert _memory_probe(discard_target=True) == (True, True)


def test_lifetime_regression_detects_the_old_target_reference_leak():
    assert _memory_probe(discard_target=False) == (True, False)


_LIFETIME_FUNCTIONS = {
    ('check_constructive_g009.py', 'worker'),
    ('constructive_g009_checkpoints.py', 'verify_principal_root'),
}
_INITIAL_WORKER_BINDING = """if binding() != source_binding:
    raise support.G009Error('worker input differs from its live controller')
"""
_FINAL_WORKER_BINDING = """if binding() != source_binding:
    raise support.G009Error('exact source/artifact bytes changed during verification')
"""
_PARTIAL_PRINCIPAL_GUARD = """if len(selected.owned) != 90 or selected.current_support or len(bundle.nodes) != pin.nodes:
    raise support.G009Error('a partial bundle cannot supply a final principal')
"""
_ORIGINAL_REPLAY_ASSIGNMENT = (
    'proof = support.closure.replay_bottom_layer_theorem(selected.frontier,name,bundle,target)'
)
_ORIGINAL_EXACT_SPEC_ASSIGNMENT = (
    'exact_spec = next(row for row in selected.owned if row.name == name)'
)


def _exact_statement_index(body, source):
    expected = ast.dump(ast.parse(source).body[0], include_attributes=False)
    indexes = [index for index, node in enumerate(body)
               if ast.dump(node, include_attributes=False) == expected]
    assert len(indexes) == 1, ('one unchanged original anchor required', source)
    return indexes[0]


def _assert_exact_cleanup(body, start, source):
    expected = ast.parse(source).body
    actual = body[start:start+len(expected)]
    assert len(actual) == len(expected)
    assert [ast.dump(node, include_attributes=False) for node in actual] == [
        ast.dump(node, include_attributes=False) for node in expected]
    return start, start+len(expected)


def _lifetime_cleanup_ranges(filename, function):
    """Recognize only the approved cleanup blocks, at exact original boundaries.

    This function inspects syntax only. It never executes a worker, replay,
    checker, report-producing function or altered mathematical input.
    """
    assert (filename, function.name) in _LIFETIME_FUNCTIONS
    body = function.body
    if filename == 'check_constructive_g009.py':
        guard = _exact_statement_index(body, _INITIAL_WORKER_BINDING)
        cleanup = _assert_exact_cleanup(body, guard+1, 'gc.collect()')
        dispatch = body[cleanup[1]]
        assert isinstance(dispatch, ast.If)
        assert ast.dump(dispatch.test) == ast.dump(ast.parse(
            "kind == 'bundle' and root is None", mode='eval').body)
        return (cleanup,)
    guard = _exact_statement_index(body, _PARTIAL_PRINCIPAL_GUARD)
    before = _assert_exact_cleanup(body, guard+1, 'del state, payload\ngc.collect()')
    replay = _exact_statement_index(body, _ORIGINAL_REPLAY_ASSIGNMENT)
    assert before[1] == replay
    after = _assert_exact_cleanup(body, replay+1, 'del bundle, target\ngc.collect()')
    assert after[1] == _exact_statement_index(body, _ORIGINAL_EXACT_SPEC_ASSIGNMENT)
    return before, after


_STREAMED_LEGACY_AUTHENTICATION = """legacy = closure.parent_snapshot().documents
for document in legacy:
    check_pin(FilePin(document.path,document.bytes,document.sha256),ROOT,
              closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)
"""
_STREAMED_CURRENT_AUTHENTICATION = """registered = completed.completed_lower_family(family.slug)
check_pin(FilePin(family.artifact,registered.artifact_bytes,registered.artifact_sha256),ROOT,
          closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes)
"""


def _streamed_provider_ranges(function):
    assert function.name == 'parent_seed_paths'
    body = function.body
    legacy = _exact_statement_index(body, 'legacy = closure.parent_snapshot().documents')
    assert _assert_exact_cleanup(body, legacy, _STREAMED_LEGACY_AUTHENTICATION) == (legacy, legacy+2)
    loops = [index for index, node in enumerate(body) if isinstance(node, ast.For)
             and isinstance(node.target, ast.Name) and node.target.id == 'family'
             and ast.dump(node.iter) == ast.dump(ast.parse(
                 'completed.COMPLETED_LOWER_FAMILIES', mode='eval').body)]
    assert len(loops) == 1
    current = loops[0]
    loop = body[current]
    assert _exact_statement_index(loop.body, 'path = ROOT / family.artifact') == 0
    assert _assert_exact_cleanup(loop.body, 1, _STREAMED_CURRENT_AUTHENTICATION) == (1, 3)
    assert _exact_statement_index(loop.body, 'paths.append(path)') == 3
    assert len(loop.body) == 4
    assert _exact_statement_index(body, 'current_parent_specs()') < legacy
    assert _exact_statement_index(body, 'completed.validate_completed_lower_source_bytes()') < legacy
    assert _exact_statement_index(body, 'paths = [ROOT / pin.path for pin in legacy]') == legacy+2
    assert current == legacy+3
    return legacy, current


def _reverse_exact_provider_streaming(function):
    """Reverse only equivalent byte-authentication scheduling for old AST pins."""
    legacy, current = _streamed_provider_ranges(function)
    function.body[current].body[1:3] = ast.parse(
        'completed.read_completed_lower_bundle_bytes(family.slug,path)').body
    function.body[legacy:legacy+2] = ast.parse(
        'legacy = closure.validate_parent_provider_bytes()').body
    return function


_PYMALLOC_WORKER_ENVIRONMENT = """environment.update(
    PYTHONPATH=os.pathsep.join((str(support.HERE),str(support.ROOT/'peano-lab/py'),
                               str(support.ROOT/'scripts'))),
    PYTHONMALLOC='pymalloc',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1')
"""


def _allocator_environment_index(function):
    """Require the exact new allocator policy at its only permitted location."""
    assert function.name == 'run_worker'
    copied = _exact_statement_index(function.body, 'environment = os.environ.copy()')
    updated = _exact_statement_index(function.body, _PYMALLOC_WORKER_ENVIRONMENT)
    assert updated == copied+1
    capture = _exact_statement_index(function.body,
        'payload = transport._capture_bounded(command,environment)')
    assert updated < capture
    allocator_keywords = [keyword for node in ast.walk(function) if isinstance(node, ast.Call)
                          for keyword in node.keywords if keyword.arg == 'PYTHONMALLOC']
    assert len(allocator_keywords) == 1
    assert isinstance(allocator_keywords[0].value, ast.Constant)
    assert type(allocator_keywords[0].value.value) is str
    assert allocator_keywords[0].value.value == 'pymalloc'
    return updated


def _reverse_exact_allocator_policy(function):
    updated = _allocator_environment_index(function)
    keyword = next(item for item in function.body[updated].value.keywords
                   if item.arg == 'PYTHONMALLOC')
    keyword.value = ast.Constant(value='malloc')
    return function



_BUILD_SNAPSHOT_MODE_GUARD = """if type(return_snapshot) is not bool:
    raise ExplorerError('the private snapshot return mode must be an exact Boolean')
"""
_BUILD_SNAPSHOT_RETURN = """if return_snapshot:
    final_check()
    return result.files,report['peak_rss_bytes'],result.peak_rss_bytes,retained[0]
"""
_LIVE_SNAPSHOT_FALLBACK = """if plugin is None:
    plugin = reader.fresh_test_snapshot()
"""
_NEW_DEFINITION_NAMESPACE = """new = {row['name']:row for row in corpus['definitions']
    if row['id'].startswith('ND') and row['id'] >= 'ND0316'}
"""
_NEW_DEFINITION_ID_SET = """assert {row['id'] for row in new.values()} == {
    'ND'+str(index).zfill(4) for index in range(316,327)}
"""
_FRESH_TEST_SNAPSHOT_SOURCE = '''def fresh_test_snapshot():
    """Bootstrap ordinary pytest through the real eight-job/277-test build.

    The retained syntax and immutable report bytes are returned only by the
    completed build. No file, receipt, caller-supplied report or proof flag
    can supply this fixture; the nested suite receives its own real plugin.
    """
    with TemporaryDirectory(prefix='.g009-test-snapshot-',dir=OUTPUT.parent) as directory:
        files,worker_peak,render_peak,retained = _build_verified(
            output=Path(directory).resolve()/'files',return_snapshot=True)
        if (type(retained) is not tuple or len(retained) != 3
                or type(retained[0]) is not support.CandidateState
                or type(retained[1]) is not support.SupportSelection
                or type(retained[2]) is not bytes):
            raise ExplorerError('the completed fresh build did not return its actual syntax projection')
        state,selected,payload = retained
        report = proof_audit.transport._decode_message(payload)
        if type(report) is not dict or proof_audit.canonical_message(report) != payload:
            raise ExplorerError('the completed fresh report bytes are not exact and canonical')
        if (type(files) is not dict
                or any(type(name) is not str or type(value) is not bytes for name,value in files.items())
                or type(worker_peak) is not int or worker_peak != report['peak_rss_bytes']
                or type(render_peak) is not int or not 0 < render_peak <= proof_audit.MAX_RSS_BYTES):
            raise ExplorerError('the completed fresh build returned changed files or resource observations')
        files = dict(files)
        presented = proof_audit.canonical_message(_presentation_report(report))
        if any(files.get(path) != presented for path in ('proof-audit.json',SLUG+'/api/checkpoint.json')):
            raise ExplorerError('the returned byte tree differs from its actual fresh report')
        _validate_live_report(report,state,selected)
        binding = _assert_snapshot_binding(files)
        checkpoints.peak_rss_bytes()
        return _FreshSnapshotTests(files,binding,state,selected,report)
'''


def _reverse_exact_snapshot_return(function):
    """Remove only the Boolean-only, post-commit return-mode addition."""
    assert function.name == '_build_verified'
    assert [argument.arg for argument in function.args.kwonlyargs] == [
        'output', 'check', 'return_snapshot']
    assert function.args.kw_defaults[0] is None
    assert ast.literal_eval(function.args.kw_defaults[1]) is False
    assert ast.literal_eval(function.args.kw_defaults[2]) is False
    assert _exact_statement_index(function.body, _BUILD_SNAPSHOT_MODE_GUARD) == 0
    assert _exact_statement_index(function.body,
        'destination = _preflight_output(output,check=check)') == 1
    returned = _exact_statement_index(function.body, _BUILD_SNAPSHOT_RETURN)
    assert returned == len(function.body)-2
    transaction = function.body[returned-1]
    assert isinstance(transaction, ast.With)
    assert _exact_statement_index(transaction.body,
        '_commit_tree(staged,destination,result.files,check=check,final_check=final_check)') == len(transaction.body)-1
    assert _exact_statement_index(function.body,
        "return result.files,report['peak_rss_bytes'],result.peak_rss_bytes") == returned+1
    del function.body[returned]
    del function.body[0]
    function.args.kwonlyargs.pop()
    function.args.kw_defaults.pop()
    return function


def _assert_exact_fresh_snapshot_helper(function):
    expected = ast.parse(_FRESH_TEST_SNAPSHOT_SOURCE).body[0]
    assert ast.dump(function, include_attributes=False) == ast.dump(expected, include_attributes=False)


def _reverse_exact_fixture_bootstrap(function):
    assert function.name == 'live'
    assigned = _exact_statement_index(function.body,
        "plugin = getattr(pytestconfig,'_g009_fresh_snapshot',None)")
    fallback = _exact_statement_index(function.body, _LIVE_SNAPSHOT_FALLBACK)
    assert fallback == assigned+1
    assert _exact_statement_index(function.body,
        "assert type(plugin) is reader._FreshSnapshotTests, 'run the actual fresh builder with --test; saved receipts are not fixtures'") == fallback+1
    del function.body[fallback]
    return function


def _reverse_exact_definition_namespace(function):
    assert function.name == 'test_same_live_conservative_definitions_three_typed_edges_and_proof_only_paths'
    selected = _exact_statement_index(function.body, _NEW_DEFINITION_NAMESPACE)
    assert _exact_statement_index(function.body,
        "assert set(new) == {row.name for row in reader.G009_DEFINITIONS}") == selected+1
    assert _exact_statement_index(function.body, 'assert len(new) == 11') == selected+2
    ids = _exact_statement_index(function.body, _NEW_DEFINITION_ID_SET)
    assert ids == selected+3
    function.body[selected] = ast.parse(
        "new = {row['name']:row for row in corpus['definitions'] if row['id'] >= 'ND0316'}").body[0]
    del function.body[ids]
    return function


class _OriginalBodyNormalization(ast.NodeTransformer):
    """Reverse only the listed non-authority edits for the frozen AST audit."""

    def __init__(self, filename):
        self.filename = filename
        self.current = None

    def visit_FunctionDef(self, node):
        previous, self.current = self.current, node.name
        if self.filename == 'build_constructive_g009_explorer.py' and node.name == '_build_verified':
            node = _reverse_exact_snapshot_return(node)
        if self.filename == 'build_constructive_g009_explorer.py' and node.name == 'fresh_test_snapshot':
            _assert_exact_fresh_snapshot_helper(node)
            self.current = previous
            return None
        if self.filename == 'test_constructive_g009_explorer.py' and node.name == 'live':
            node = _reverse_exact_fixture_bootstrap(node)
        if (self.filename == 'test_constructive_g009_explorer.py'
                and node.name == 'test_same_live_conservative_definitions_three_typed_edges_and_proof_only_paths'):
            node = _reverse_exact_definition_namespace(node)
        if self.filename == 'check_constructive_g009.py' and node.name == 'run_worker':
            node = _reverse_exact_allocator_policy(node)
        if self.filename == 'constructive_g009_support.py' and node.name == 'parent_seed_paths':
            node = _reverse_exact_provider_streaming(node)
        if (self.filename, node.name) in _LIFETIME_FUNCTIONS:
            # Reverse only the three new, precisely placed lifetime blocks.
            # Every pre-existing statement is still checked by its old hash.
            for start, stop in reversed(_lifetime_cleanup_ranges(self.filename, node)):
                del node.body[start:stop]
        if self.filename == 'constructive_g009_support.py' and node.name == '_repository_path':
            self.current = previous
            return None
        if self.filename == 'test_constructive_g009_explorer.py' and node.name in {
                '_expected_graph_selection', '_assert_graph_observation',
                'test_same_live_actual_graph_handles_getter_only_svg_links_and_focus',
                'test_same_live_actual_graph_definition_visibility_and_three_edge_kinds'}:
            # These two UI case bodies have a separately tested compact-aware
            # observation change; their names/parameters remain pinned below.
            self.current = previous
            return None
        if self.filename == 'profile_constructive_g009_presentation.py' and node.name == 'profile':
            position = next(index for index, part in enumerate(node.body)
                            if 'expected_reader' in _assigned_names(part))
            assert isinstance(node.body[position+1], ast.If)
            del node.body[position:position+2]
        node = self.generic_visit(node)
        self.current = previous
        return node

    def visit_Call(self, node):
        node = self.generic_visit(node)
        if ((self.filename == 'constructive_g009_support.py' and self.current == 'state_binding'
             and _name_call(node, '_repository_path'))
                or (self.filename == 'build_constructive_g009_explorer.py'
                    and self.current == '_render_binding'
                    and _attribute_call(node, 'support', '_repository_path'))):
            node.func = ast.Name(id='str', ctx=ast.Load())
        if (self.filename == 'test_constructive_g009_explorer.py'
                and self.current == '_atlas_test_module' and _name_call(node, 'import_module')):
            assert len(node.args) == 1 and node.args[0].value == 'tests.test_constructive_g009_campaign'
            node.args[0].value = 'test_constructive_g009_campaign'
        return node

    def visit_Assign(self, node):
        node = self.generic_visit(node)
        if (self.filename == 'build_constructive_g009_explorer.py'
                and self.current == '_render_binding' and _assigned_names(node) == {'paths'}):
            additions = {ast.dump(ast.parse(source, mode='eval').body) for source in (
                "ROOT/'conftest.py'", "ROOT/'pytest.ini'", "ROOT/'peano-lab/py/tests/conftest.py'")}
            assert isinstance(node.value, ast.Tuple)
            removed = [part for part in node.value.elts if ast.dump(part) in additions]
            assert len(removed) == 3
            node.value.elts = [part for part in node.value.elts if ast.dump(part) not in additions]
            names = {'constructive_historical_graph_test_support.py', 'test_constructive_historical_publication_v31.py'}
            seen = set()
            for part in node.value.elts:
                if isinstance(part, ast.Starred) and isinstance(part.value, ast.GeneratorExp):
                    for generator in part.value.generators:
                        if isinstance(generator.iter, ast.Tuple):
                            seen.update(value.value for value in generator.iter.elts
                                        if isinstance(value, ast.Constant) and value.value in names)
                            generator.iter.elts = [value for value in generator.iter.elts
                                                  if not isinstance(value, ast.Constant) or value.value not in names]
            assert seen == names
        if (self.filename == 'export_constructive_g009.py'
                and self.current == 'export_authoring_bundle' and _assigned_names(node) == {'allowed'}):
            node.value = ast.parse("support.ROOT/'research/arithmetic-library/artifacts' "
                                   "if support.HERE == support.ROOT/'scripts' else support.HERE",
                                   mode='eval').body
        if (self.filename == 'build_constructive_g009_explorer.py'
                and self.current == '_render_files' and _name_call(node.value, 'decode_proof_bundle')):
            assert len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple)
            assert [part.id for part in node.targets[0].elts] == ['bundle', 'target']
            node.targets[0].elts[1].id = '_'
        return node

    def visit_Delete(self, node):
        if self.filename == 'build_constructive_g009_explorer.py' and self.current == '_render_files':
            assert [part.id for part in node.targets] == ['bundle', 'target']
            node.targets = node.targets[:1]
        return self.generic_visit(node)


@pytest.mark.parametrize('name', tuple(ORIGINAL_CALLABLE_AST_SHA256))
def test_all_original_named_bodies_preserve_every_unrelated_guard_and_case(name):
    tree = _tree(name)
    tree.body = [node for node in tree.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    normalized = _OriginalBodyNormalization(name).visit(tree)
    encoded = ast.dump(normalized, include_attributes=False).encode()
    assert sha256(encoded).hexdigest() == ORIGINAL_CALLABLE_AST_SHA256[name]


def test_eight_real_jobs_six_exact_roots_and_277_mandatory_cases_remain_fixed():
    audit = _tree('check_constructive_g009.py')
    values = {next(iter(_assigned_names(node))): node.value for node in audit.body
              if len(_assigned_names(node)) == 1}
    for name, literal in {'CPU_LIMITS': '(170,175)', 'WALL_SECONDS': '180',
                          'PARENT_TIMEOUT_SECONDS': '185', 'MAX_RSS_BYTES': '1536*1024*1024',
                          'MAX_STDOUT_BYTES': '128*1024', 'MAX_STDERR_BYTES': '8*1024'}.items():
        assert ast.dump(values[name]) == ast.dump(ast.parse(literal, mode='eval').body)
    roots = next(node.value for node in _tree('constructive_g009_checkpoints.py').body
                 if 'PRINCIPAL_ROOTS' in _assigned_names(node))
    assert ast.literal_eval(roots) == (
        'signed_support_reindex_sum_equal', 'signed_cartesian_product_sums_exists',
        'coprime_divisor_factor_pair_exists_unique', 'dirichlet_convolution_multiplicative_values',
        'dirichlet_convolution_multiplicative_table', 'dirichlet_convolution_multiplicative_exists_unique')
    count = next(node.value for node in _tree('build_constructive_g009_explorer.py').body
                 if 'EXPECTED_READER_TESTS' in _assigned_names(node))
    assert ast.literal_eval(count) == 277
    build = _function('build_constructive_g009_explorer.py', '_build_verified')
    real_audit = [node for node in ast.walk(build) if _attribute_call(node, 'proof_audit', 'verify_in_fresh_windows')]
    assert len(real_audit) == 1 and {key.arg for key in real_audit[0].keywords} == {'syntax_collector'}
    render = [node for node in ast.walk(build) if _name_call(node, '_fork_render_phase')]
    assert len(render) == 1
    assert next(key.value.value for key in render[0].keywords if key.arg == 'test') is True


def test_normalization_never_resolves_aliases_or_removes_physical_checks():
    helper = _function('constructive_g009_support.py', '_repository_path')
    assert any(isinstance(node, ast.Attribute) and node.attr == 'relative_to' for node in ast.walk(helper))
    assert any(isinstance(node, ast.Attribute) and node.attr == 'as_posix' for node in ast.walk(helper))
    assert not any(isinstance(node, ast.Attribute) and node.attr == 'resolve' for node in ast.walk(helper))
    state = _function('constructive_g009_support.py', 'state_binding')
    assert any(_name_call(node, 'bounded_bytes') for node in ast.walk(state))
    assert any(_name_call(node, 'parent_seed_paths') for node in ast.walk(state))
    render = _function('build_constructive_g009_explorer.py', '_render_binding')
    assert any(_name_call(node, '_source') for node in ast.walk(render))
    assert any(_attribute_call(node, 'support', 'check_pin') for node in ast.walk(render))
    for name in ORIGINAL_CALLABLE_AST_SHA256:
        text = _source_path(name).read_text()
        assert '/Users/' not in text and '/private/tmp/' not in text


GRAPH_OBSERVATION_FIELDS = frozenset((
    'sidebarHref', 'sidebarLabel', 'title', 'summary', 'svgAnchorCount', 'firstSvgHref',
    'svgHrefIsGetterOnly', 'allSvgHrefsAreGetterOnly', 'renderedNodeIds', 'compactNodeIds',
    'nodeTransforms', 'selectedNodeIds', 'renderedArrowCount', 'currentAddress', 'viewport',
    'viewportRendered',
))


def _graph_contract_helpers():
    """Pure UI report assertions only; no observer, fixture, worker or proof."""
    wanted = {'_expected_graph_selection', '_assert_graph_observation'}
    nodes = [deepcopy(node) for node in _tree('test_constructive_g009_explorer.py').body
             if isinstance(node, ast.FunctionDef) and node.name in wanted]
    assert {node.name for node in nodes} == wanted
    namespace = {'graph_observer': SimpleNamespace(REPORT_FIELDS=GRAPH_OBSERVATION_FIELDS),
                 'parse_qs': parse_qs, 'urlsplit': urlsplit}
    exec(compile(ast.Module(body=nodes,type_ignores=[]), '<non-authority UI assertions only>', 'exec'), namespace)
    return SimpleNamespace(**namespace)


def _synthetic_ui_observation(*, compact):
    """Widget-only records, not real theorem data or a live proof report."""
    theorem_ids = ['UX'+str(index).zfill(4) for index in range(1,162)]
    nodes = [{'id': identifier, 'kind': 'theorem', 'name': 'UI-only item '+identifier,
              'href': 'ui-fixture/'+identifier+'.html'} for identifier in theorem_ids]
    nodes += [{'id': identifier, 'kind': 'definition', 'name': 'UI-only item '+identifier,
               'href': 'ui-fixture/'+identifier+'.html'} for identifier in ('UD1','UD2')]
    edges = [{'kind': 'proof_dependency', 'source': left, 'target': right}
             for left,right in zip(theorem_ids,theorem_ids[1:])]
    edges += [{'kind': 'uses_definition', 'source': theorem_ids[0], 'target': 'UD1'},
              {'kind': 'definition_uses_definition', 'source': 'UD1', 'target': 'UD2'}]
    target = theorem_ids[-1]
    graph = {'nodes': nodes, 'edges': edges,
             'proof_adjacency': {target: {'critical_root_path': theorem_ids}}}
    visible = [node['id'] for node in nodes] if compact else theorem_ids[-2:]
    node = nodes[160]
    query = ('view=corpus&definitions=visible&edges=all' if compact
             else 'view=neighborhood&definitions=selected&edges=focus')
    report = {
        'sidebarHref': node['href'], 'sidebarLabel': 'Open theorem →',
        'title': target+' · '+node['name'], 'summary': 'Synthetic UI observations only',
        'svgAnchorCount': 0 if compact else 2,
        'firstSvgHref': None if compact else nodes[159]['href'],
        'svgHrefIsGetterOnly': None if compact else True,
        'allSvgHrefsAreGetterOnly': None if compact else True,
        'renderedNodeIds': visible, 'compactNodeIds': visible[:] if compact else [],
        'nodeTransforms': ['translate(0 0)' for _ in visible],
        'selectedNodeIds': [target], 'renderedArrowCount': 162 if compact else 1,
        'currentAddress': 'https://ui.invalid/graph?target='+target+'&focus='+target+'&'+query,
        'viewport': '0 0 100 100', 'viewportRendered': True,
    }
    return graph,report,target


@pytest.mark.parametrize('compact', (False,True))
def test_pure_ui_assertions_distinguish_real_link_shape_from_compact_null_shape(compact):
    graph, report, target = _synthetic_ui_observation(compact=compact)
    helpers = _graph_contract_helpers()
    helpers._assert_graph_observation(graph,report,target,target,
        complete_family=compact,visible_definitions=compact)


@pytest.mark.parametrize('compact', (False,True))
@pytest.mark.parametrize('attack', ('missing-field', 'extra-field', 'missing-node',
                                    'duplicate-node', 'selection', 'arrows', 'boolean-arrows',
                                    'sidebar-href', 'sidebar-title', 'sidebar-label',
                                    'viewport', 'url-target', 'url-view'))
def test_pure_ui_observation_corruption_never_passes(compact, attack):
    graph, report, target = _synthetic_ui_observation(compact=compact)
    if attack == 'missing-field':
        del report['summary']
    elif attack == 'extra-field':
        report['unexpected'] = True
    elif attack == 'missing-node':
        report['renderedNodeIds'] = report['renderedNodeIds'][:-1]
    elif attack == 'duplicate-node':
        report['renderedNodeIds'] = [report['renderedNodeIds'][0]]*len(report['renderedNodeIds'])
    elif attack == 'selection':
        report['selectedNodeIds'] = ['UX0001']
    elif attack == 'arrows':
        report['renderedArrowCount'] += 1
    elif attack == 'boolean-arrows':
        report['renderedArrowCount'] = True
    elif attack == 'sidebar-href':
        report['sidebarHref'] = 'foreign.html'
    elif attack == 'sidebar-title':
        report['title'] = 'wrong node'
    elif attack == 'sidebar-label':
        report['sidebarLabel'] = 'Open definition →'
    elif attack == 'viewport':
        report['viewportRendered'] = False
    elif attack == 'url-target':
        report['currentAddress'] = report['currentAddress'].replace('target='+target,'target=UX0001')
    else:
        before,after = ('view=corpus','view=neighborhood') if compact else ('view=neighborhood','view=corpus')
        report['currentAddress'] = report['currentAddress'].replace(before,after)
    helpers = _graph_contract_helpers()
    with pytest.raises(AssertionError):
        helpers._assert_graph_observation(graph,report,target,target,
            complete_family=compact,visible_definitions=compact)


@pytest.mark.parametrize('attack', ('anchor-present', 'first-link-present', 'getter-true',
                                    'all-getters-true', 'compact-class-missing',
                                    'compact-class-duplicate'))
def test_compact_observations_cannot_claim_vacuous_getter_only_success(attack):
    graph, report, target = _synthetic_ui_observation(compact=True)
    if attack == 'anchor-present':
        report['svgAnchorCount'] = 1
    elif attack == 'first-link-present':
        report['firstSvgHref'] = graph['nodes'][0]['href']
    elif attack == 'getter-true':
        report['svgHrefIsGetterOnly'] = True
    elif attack == 'all-getters-true':
        report['allSvgHrefsAreGetterOnly'] = True
    elif attack == 'compact-class-missing':
        report['compactNodeIds'] = report['compactNodeIds'][:-1]
    else:
        report['compactNodeIds'].append(report['compactNodeIds'][0])
    with pytest.raises(AssertionError):
        _graph_contract_helpers()._assert_graph_observation(graph,report,target,target,
            complete_family=True,visible_definitions=True)


@pytest.mark.parametrize('attack', ('no-anchors', 'no-first-link', 'writable-link',
                                    'vacuous-all-getters', 'compact-class'))
def test_narrow_observations_must_retain_nonempty_actual_getter_only_link_shape(attack):
    graph, report, target = _synthetic_ui_observation(compact=False)
    if attack == 'no-anchors':
        report['svgAnchorCount'] = 0
    elif attack == 'no-first-link':
        report['firstSvgHref'] = None
    elif attack == 'writable-link':
        report['svgHrefIsGetterOnly'] = False
    elif attack == 'vacuous-all-getters':
        report['allSvgHrefsAreGetterOnly'] = None
    else:
        report['compactNodeIds'] = report['renderedNodeIds'][:]
    with pytest.raises(AssertionError):
        _graph_contract_helpers()._assert_graph_observation(graph,report,target,target,
            complete_family=False,visible_definitions=False)


@pytest.mark.parametrize('attack', ('conflated-kind', 'reversed-notation', 'duplicate-edge',
                                    'dangling-edge', 'duplicate-node'))
def test_typed_graph_selection_rejects_invented_or_conflated_relationships(attack):
    graph, report, target = _synthetic_ui_observation(compact=True)
    if attack == 'conflated-kind':
        graph['edges'][0]['kind'] = 'uses_definition'
    elif attack == 'reversed-notation':
        graph['edges'][-1]['source'] = target
    elif attack == 'duplicate-edge':
        graph['edges'].append(dict(graph['edges'][0]))
    elif attack == 'dangling-edge':
        graph['edges'][0]['source'] = 'MISSING'
    else:
        graph['nodes'].append(dict(graph['nodes'][0]))
    with pytest.raises(AssertionError):
        _graph_contract_helpers()._assert_graph_observation(graph,report,target,target,
            complete_family=True,visible_definitions=True)


def test_same_277_case_id_shapes_and_three_reviewed_graph_instances_remain():
    tree = _tree('test_constructive_g009_explorer.py')
    shape = [(node.name,ast.dump(node.args),tuple(ast.dump(item) for item in node.decorator_list))
             for node in tree.body if isinstance(node,ast.FunctionDef) and node.name.startswith('test_')]
    assert len(shape) == 59
    assert sha256(json.dumps(shape,separators=(',',':')).encode()).hexdigest() == (
        'c75713c3148d730b06adc43e19becfa17253ad17c05495e73238fb3f54cb20a4')
    selected = _function('test_constructive_g009_explorer.py',
                         'test_same_live_actual_graph_handles_getter_only_svg_links_and_focus')
    loop = next(node for node in selected.body if isinstance(node,ast.For))
    assert ast.literal_eval(loop.iter) == (True,False)
    visible = _function('test_constructive_g009_explorer.py',
                        'test_same_live_actual_graph_definition_visibility_and_three_edge_kinds')
    observations = [node for node in ast.walk(visible)
                    if _attribute_call(node,'graph_observer','observe_graph')]
    assert len(observations) == 2
    options = [{key.arg:ast.literal_eval(key.value) for key in node.keywords}
               for node in observations]
    assert options == [{'complete_family':True,'visible_definitions':True},
                       {'complete_family':False,'visible_definitions':False}]
    for function in (selected,visible):
        assert not any(_attribute_call(node,'graph_observer','check_historical_graph_case')
                       for node in ast.walk(function))
        assert not any(isinstance(node,ast.Constant) and node.value == '_graph_runtime'
                       for node in ast.walk(function))


def test_reader_binds_observer_every_consumed_frozen_input_and_pytest_configuration():
    binding = _function('build_constructive_g009_explorer.py','_render_binding')
    text = ast.unparse(binding)
    for required in ('constructive_historical_graph_test_support.py',
                     'test_constructive_historical_publication_v31.py',
                     'test_constructive_frontier_explorer.py',
                     'conftest.py', 'pytest.ini', 'peano-lab/py/tests/conftest.py'):
        assert required in text
    assert any(_attribute_call(node,'model','_assets') for node in ast.walk(binding))
    assert any(_attribute_call(node,'support','_repository_path') for node in ast.walk(binding))
    tests = _tree('test_constructive_g009_explorer.py')
    assert any(isinstance(node,ast.Import) and any(alias.name == 'constructive_historical_graph_test_support'
               and alias.asname == 'graph_observer' for alias in node.names) for node in tests.body)
    assert any(isinstance(node,ast.Assert) and 'inspect.getfile(graph_observer.observe_graph)' in ast.unparse(node)
               and 'scripts/constructive_historical_graph_test_support.py' in ast.unparse(node)
               for node in tests.body)


@pytest.mark.parametrize('filename,function_name,expected_blocks', (
    ('check_constructive_g009.py', 'worker', 1),
    ('constructive_g009_checkpoints.py', 'verify_principal_root', 2),
))
def test_lifetime_blocks_have_exact_original_guard_and_replay_neighbors(
        filename, function_name, expected_blocks):
    function = _function(filename, function_name)
    blocks = _lifetime_cleanup_ranges(filename, function)
    assert len(blocks) == expected_blocks
    for start, stop in blocks:
        assert stop > start
        assert _attribute_call(function.body[stop-1].value, 'gc', 'collect')
        assert not function.body[stop-1].value.args
        assert not function.body[stop-1].value.keywords
    if expected_blocks == 1:
        assert _exact_statement_index(function.body, _INITIAL_WORKER_BINDING) < blocks[0][0]
        assert _exact_statement_index(function.body, _FINAL_WORKER_BINDING) > blocks[0][1]
    else:
        assert [part.id for part in function.body[blocks[0][0]].targets] == ['state', 'payload']
        assert [part.id for part in function.body[blocks[1][0]].targets] == ['bundle', 'target']


def test_lifetime_cleanup_never_releases_a_later_used_owner_or_the_certificate():
    function = _function('constructive_g009_checkpoints.py', 'verify_principal_root')
    for start, stop in _lifetime_cleanup_ranges('constructive_g009_checkpoints.py', function):
        discarded = {part.id for part in function.body[start].targets}
        later_reads = {node.id for statement in function.body[stop:]
                       for node in ast.walk(statement)
                       if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)}
        assert not discarded & later_reads
        assert not discarded & {'proof', 'formula', 'selected', 'pin', 'exact_spec'}
    calls = [node for node in ast.walk(function) if _name_call(node, 'check')]
    assert len(calls) == 1
    assert ast.dump(calls[0]) == ast.dump(ast.parse(
        'check((),proof.certificate,formula)', mode='eval').body)


def test_lifetime_cleanup_imports_plain_gc_without_old_cache_or_threshold_changes():
    for filename, _function_name in sorted(_LIFETIME_FUNCTIONS):
        tree = _tree(filename)
        imports = [alias for node in tree.body if isinstance(node, ast.Import)
                   for alias in node.names if alias.name == 'gc']
        assert len(imports) == 1 and imports[0].asname is None
        assert not any(isinstance(node, ast.Name) and node.id == 'gc'
                       and isinstance(node.ctx, (ast.Store, ast.Del)) for node in ast.walk(tree))
        assert not any(isinstance(node, ast.Attribute) and node.attr in {
            'cache_clear', 'set_threshold', 'set_debug', 'disable', 'enable', 'freeze', 'unfreeze'
        } for node in ast.walk(tree))


class _NonAuthorityLifetimeAllocation:
    """A deliberately cyclic allocation marker, never a proof or a report."""

    __slots__ = ('label', 'cycle', '__weakref__')

    def __init__(self, label):
        self.label = label
        self.cycle = self


def _cleanup_fragment_codes(*, retain=None):
    codes = {}
    for filename, function_name in sorted(_LIFETIME_FUNCTIONS):
        function = _function(filename, function_name)
        for index, (start, stop) in enumerate(_lifetime_cleanup_ranges(filename, function)):
            phase = ('after_binding' if filename == 'check_constructive_g009.py'
                     else ('before_replay', 'before_exact_check')[index])
            nodes = deepcopy(function.body[start:stop])
            if retain is not None:
                for node in nodes:
                    if isinstance(node, ast.Delete):
                        node.targets = [part for part in node.targets if part.id != retain]
            # Only the actual Delete/collect fragments are executable here.
            # There is no checker, worker, source loader or report constructor.
            assert all(isinstance(node, ast.Delete) or (
                isinstance(node, ast.Expr) and _attribute_call(node.value, 'gc', 'collect'))
                for node in nodes)
            codes[phase] = compile(ast.fix_missing_locations(ast.Module(
                body=nodes, type_ignores=[])), '<allocation cleanup only>', 'exec')
    return codes


def _probe_cleanup_fragments(phase, *, retain=None):
    codes = _cleanup_fragment_codes(retain=retain)
    namespace = {'gc': gc}
    labels = ('state', 'payload', 'bundle', 'target', 'held_output')
    for label in labels:
        namespace[label] = _NonAuthorityLifetimeAllocation(label)
    references = {label: weakref.ref(namespace[label]) for label in labels}
    temporary = _NonAuthorityLifetimeAllocation('unreachable preflight temporary')
    prior_reference = weakref.ref(temporary)
    del temporary
    # All markers have self-cycles; reference-count decrement alone is not
    # sufficient. No global GC settings, old cache, or proof API is changed.
    assert prior_reference() is not None
    try:
        if phase == 'before_exact_check':
            exec(codes['before_replay'], namespace)
        exec(codes[phase], namespace)
        return {label: reference() is not None for label, reference in references.items()}, (
            prior_reference() is not None)
    finally:
        namespace.clear()
        gc.collect()


@pytest.mark.parametrize('phase,expected_live', (
    ('after_binding', {'state', 'payload', 'bundle', 'target', 'held_output'}),
    ('before_replay', {'bundle', 'target', 'held_output'}),
    ('before_exact_check', {'held_output'}),
))
def test_actual_cleanup_fragments_collect_only_unreachable_allocation_markers(phase, expected_live):
    live, preflight_is_live = _probe_cleanup_fragments(phase)
    assert {label for label, value in live.items() if value} == expected_live
    assert preflight_is_live is False


@pytest.mark.parametrize('phase,retained', (
    ('before_replay', 'state'), ('before_replay', 'payload'),
    ('before_exact_check', 'bundle'), ('before_exact_check', 'target'),
))
def test_allocation_probe_detects_each_omitted_owner_release(phase, retained):
    live, preflight_is_live = _probe_cleanup_fragments(phase, retain=retained)
    assert live[retained] is True and live['held_output'] is True
    assert preflight_is_live is False


_LIFETIME_AST_ATTACKS = (
    'audit_missing_gc', 'audit_gc_before_binding', 'audit_gc_after_dispatch',
    'audit_missing_initial_binding', 'audit_missing_final_binding',
    'audit_accepts_mismatched_binding', 'audit_replaces_bundle_gate',
    'audit_replaces_principal_gate', 'audit_widens_cpu_limits',
    'root_missing_pre_block', 'root_missing_post_block',
    'root_missing_pre_gc', 'root_missing_post_gc',
    'root_keeps_state', 'root_keeps_payload', 'root_keeps_bundle', 'root_keeps_target',
    'root_deletes_certificate', 'root_precedes_partial_guard',
    'root_deletes_bundle_before_replay', 'root_deletes_after_exact_check',
    'root_gc_accepts_arguments', 'root_replaces_original_replay',
    'root_omits_exact_check', 'root_checks_nonempty_context',
    'root_omits_rss_gate', 'root_accepts_partial_bundle',
)


def _mutated_lifetime_control(attack):
    """Source-AST attacks only: altered verifiers are never executed."""
    assert attack in _LIFETIME_AST_ATTACKS
    audit = attack.startswith('audit_')
    filename, function_name = (('check_constructive_g009.py', 'worker') if audit
                              else ('constructive_g009_checkpoints.py', 'verify_principal_root'))
    tree = _tree(filename)
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == function_name)
    original = ast.dump(tree, include_attributes=False)
    blocks = _lifetime_cleanup_ranges(filename, function)
    body = function.body
    first, stop = blocks[0]
    if audit:
        if attack == 'audit_missing_gc':
            del body[first:stop]
        elif attack == 'audit_gc_before_binding':
            block = body.pop(first)
            body.insert(first-1, block)
        elif attack == 'audit_gc_after_dispatch':
            block = body.pop(first)
            body.insert(first+1, block)
        elif attack == 'audit_missing_initial_binding':
            del body[_exact_statement_index(body, _INITIAL_WORKER_BINDING)]
        elif attack == 'audit_missing_final_binding':
            del body[_exact_statement_index(body, _FINAL_WORKER_BINDING)]
        elif attack == 'audit_accepts_mismatched_binding':
            body[_exact_statement_index(body, _INITIAL_WORKER_BINDING)].body = [
                ast.Return(value=ast.Constant(value=0))]
        elif attack in {'audit_replaces_bundle_gate', 'audit_replaces_principal_gate'}:
            wanted = ('verify_checkpoint' if attack == 'audit_replaces_bundle_gate'
                      else 'verify_principal_root')
            assignment = next(node for node in ast.walk(function) if isinstance(node, ast.Assign)
                              and _attribute_call(node.value, 'checkpoints', wanted))
            assignment.value = ast.Dict(keys=[], values=[])
        else:
            call = next(node for node in ast.walk(function)
                        if _attribute_call(node, 'resource', 'setrlimit'))
            call.args[1] = ast.parse('(171,176)', mode='eval').body
    else:
        second, end = blocks[1]
        if attack == 'root_missing_pre_block':
            del body[first:stop]
        elif attack == 'root_missing_post_block':
            del body[second:end]
        elif attack == 'root_missing_pre_gc':
            del body[stop-1]
        elif attack == 'root_missing_post_gc':
            del body[end-1]
        elif attack.startswith('root_keeps_'):
            name = attack.removeprefix('root_keeps_')
            deletion = body[first if name in {'state', 'payload'} else second]
            deletion.targets = [part for part in deletion.targets if part.id != name]
        elif attack == 'root_deletes_certificate':
            body[second].targets.append(ast.Name(id='proof', ctx=ast.Del()))
        elif attack == 'root_precedes_partial_guard':
            block = body[first:stop]
            del body[first:stop]
            body[first-1:first-1] = block
        elif attack == 'root_deletes_bundle_before_replay':
            block = body[second:end]
            del body[second:end]
            body[second-1:second-1] = block
        elif attack == 'root_deletes_after_exact_check':
            block = body[second:end]
            del body[second:end]
            checked = next(index for index, statement in enumerate(body)
                           if isinstance(statement, ast.If) and any(
                               _name_call(node, 'check') for node in ast.walk(statement.test)))
            body[checked+1:checked+1] = block
        elif attack == 'root_gc_accepts_arguments':
            body[stop-1].value.args.append(ast.Constant(value=0))
        elif attack == 'root_replaces_original_replay':
            body[_exact_statement_index(body, _ORIGINAL_REPLAY_ASSIGNMENT)].value.func.attr = 'unchecked_replay'
        elif attack == 'root_omits_exact_check':
            guard = next(statement for statement in body if isinstance(statement, ast.If)
                         and any(_name_call(node, 'check') for node in ast.walk(statement.test)))
            assert isinstance(guard.test, ast.BoolOp) and isinstance(guard.test.op, ast.Or)
            guard.test.values.pop()
        elif attack == 'root_checks_nonempty_context':
            call = next(node for node in ast.walk(function) if _name_call(node, 'check'))
            call.args[0] = ast.Tuple(elts=[ast.Constant(value='untrusted open context')], ctx=ast.Load())
        elif attack == 'root_omits_rss_gate':
            index = next(index for index, statement in enumerate(body)
                         if isinstance(statement, ast.Expr) and _name_call(statement.value, 'peak_rss_bytes'))
            del body[index]
        else:
            body[_exact_statement_index(body, _PARTIAL_PRINCIPAL_GUARD)].test = ast.Constant(value=False)
    assert ast.dump(tree, include_attributes=False) != original
    return filename, tree


@pytest.mark.parametrize('attack', _LIFETIME_AST_ATTACKS)
def test_lifetime_normalization_rejects_bad_placement_or_changed_original_gates(attack):
    filename, tree = _mutated_lifetime_control(attack)
    tree.body = [node for node in tree.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    with pytest.raises(AssertionError):
        normalized = _OriginalBodyNormalization(filename).visit(tree)
        encoded = ast.dump(normalized, include_attributes=False).encode()
        assert sha256(encoded).hexdigest() == ORIGINAL_CALLABLE_AST_SHA256[filename]


def _provider_byte_fixture(tmp_path, *, large=False):
    """Twenty plus nineteen tiny NON-PROOF files for byte transport only."""
    root = tmp_path.resolve()/'provider-transport-only'
    directory = root/'research/arithmetic-library/artifacts'
    directory.mkdir(parents=True)
    legacy, families = [], []
    for index in range(39):
        prior = index < 20
        local = index if prior else index-20
        label = ('legacy' if prior else 'current')+'-'+str(local).zfill(2)
        relative = 'research/arithmetic-library/artifacts/'+label+'.json'
        count = 2*1024*1024+17 if large and index == 19 else 1+index
        payload = b'UNTRUSTED TRANSPORT BYTES ONLY; NOT A PROOF\n'+b'x'*count
        (root/relative).write_bytes(payload)
        digest = sha256(payload).hexdigest()
        if prior:
            legacy.append(SimpleNamespace(path=relative, bytes=len(payload), sha256=digest))
        else:
            families.append(SimpleNamespace(slug=label, artifact=relative,
                artifact_bytes=len(payload), artifact_sha256=digest))
    return root, tuple(legacy), tuple(families)


def _provider_authentication_fragment(root, legacy, families, *, trace=None, fail_family=None):
    """Execute only actual path/pin loops with actual strict physical reads.

    The surrounding current-parent/source-seal calls are AST-pinned, NOT
    mocked into success here. No production parent_seed_paths(), catalogue,
    proof verifier or successful report-producing entry point is invoked.
    Fixture records describe only the explicitly labelled temporary bytes.
    """
    trace = {'reads': [], 'lookups': []} if trace is None else trace
    physical = _physical_helpers(root)
    original_stream = physical.check_pin.__globals__['_bounded_stream']

    @contextmanager
    def observed_stream(path, maximum, *, exact_size=None):
        with original_stream(path, maximum, exact_size=exact_size) as (stream, size):
            class ReadObservation:
                def read(self, count):
                    trace['reads'].append((path, count))
                    return stream.read(count)
            yield ReadObservation(), size

    # This is an isolated copy of file helpers, not a production module or
    # proof function; the observer delegates every actual read unchanged.
    physical.check_pin.__globals__['_bounded_stream'] = observed_stream
    by_slug = {family.slug: family for family in families}

    def fixture_metadata_lookup(slug):
        trace['lookups'].append(slug)
        if slug == fail_family:
            raise ValueError('NON-AUTHORITY metadata fixture rejection')
        return by_slug[slug]

    function = _function('constructive_g009_support.py', 'parent_seed_paths')
    first, _current = _streamed_provider_ranges(function)
    assert isinstance(function.body[-1], ast.Return)
    nodes = deepcopy(function.body[first:-1])
    assert not any(_name_call(node, 'current_parent_specs')
                   or _attribute_call(node, 'completed', 'validate_completed_lower_source_bytes')
                   for statement in nodes for node in ast.walk(statement))
    namespace = {'ROOT': root, 'FilePin': physical.FilePin,
        'check_pin': physical.check_pin, 'G009Error': physical.G009Error,
        'closure': SimpleNamespace(parent_snapshot=lambda: SimpleNamespace(documents=legacy),
            DEFAULT_BUNDLE_LIMITS=SimpleNamespace(max_payload_bytes=64*1024*1024)),
        'completed': SimpleNamespace(COMPLETED_LOWER_FAMILIES=families,
            completed_lower_family=fixture_metadata_lookup)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 '<provider byte loops only; no parent or proof seal>', 'exec'), namespace)
    return tuple(namespace['paths']), trace, physical


def test_provider_streaming_preserves_all_39_paths_order_family_lookups_and_chunk_bound(tmp_path):
    root, legacy, families = _provider_byte_fixture(tmp_path, large=True)
    paths, trace, _physical = _provider_authentication_fragment(root, legacy, families)
    assert len(legacy) == 20 and len(families) == 19 and len(paths) == 39
    assert paths == tuple(root/item.path for item in legacy)+tuple(root/item.artifact for item in families)
    assert trace['lookups'] == [item.slug for item in families]
    assert {path for path, _count in trace['reads']} == set(paths)
    assert all(0 < count <= 1024*1024 for _path, count in trace['reads'])
    assert any(count == 1024*1024 for _path, count in trace['reads'])


@pytest.mark.parametrize('changed', range(39))
def test_provider_streaming_authenticates_each_even_unused_literal_file(tmp_path, changed):
    root, legacy, families = _provider_byte_fixture(tmp_path)
    paths = tuple(root/item.path for item in legacy)+tuple(root/item.artifact for item in families)
    path = paths[changed]
    raw = path.read_bytes()
    path.write_bytes(raw[:-1]+b'!')
    with pytest.raises(ValueError, match='literal file bytes changed'):
        _provider_authentication_fragment(root, legacy, families)


@pytest.mark.parametrize('generation,field,bad', (
    ('legacy', 'bytes', True), ('current', 'artifact_bytes', True),
    ('legacy', 'sha256', '0'*64), ('current', 'artifact_sha256', '0'*64),
    ('legacy', 'path', '../outside.json'), ('current', 'artifact', '../outside.json'),
    ('legacy', 'bytes', 64*1024*1024+1), ('current', 'artifact_bytes', 64*1024*1024+1),
    ('legacy', 'sha256', 'not-a-digest'), ('current', 'artifact_sha256', 'not-a-digest'),
))
def test_provider_streaming_rejects_malformed_or_substituted_pins(tmp_path, generation, field, bad):
    root, legacy, families = _provider_byte_fixture(tmp_path)
    record = legacy[0] if generation == 'legacy' else families[0]
    setattr(record, field, bad)
    with pytest.raises(ValueError):
        _provider_authentication_fragment(root, legacy, families)


@pytest.mark.parametrize('attack', ('missing_legacy', 'missing_current', 'duplicate_legacy'))
def test_provider_streaming_keeps_the_exact_39_distinct_inventory_guard(tmp_path, attack):
    root, legacy, families = _provider_byte_fixture(tmp_path)
    if attack == 'missing_legacy':
        legacy = legacy[:-1]
    elif attack == 'missing_current':
        families = families[:-1]
    else:
        legacy = (*legacy[:-1], legacy[0])
    with pytest.raises(ValueError, match='exact 20\\+19 inherited proof-provider inventory changed'):
        _provider_authentication_fragment(root, legacy, families)


@pytest.mark.parametrize('failed', (0, 18))
def test_provider_family_metadata_rejection_precedes_its_physical_read(tmp_path, failed):
    root, legacy, families = _provider_byte_fixture(tmp_path)
    trace = {'reads': [], 'lookups': []}
    with pytest.raises(ValueError, match='NON-AUTHORITY metadata fixture rejection'):
        _provider_authentication_fragment(root, legacy, families, trace=trace,
                                          fail_family=families[failed].slug)
    assert trace['lookups'] == [item.slug for item in families[:failed+1]]
    touched = {path for path, _count in trace['reads']}
    assert touched == {root/item.path for item in legacy}|{
        root/item.artifact for item in families[:failed]}
    assert root/families[failed].artifact not in touched


_PROVIDER_AST_ATTACKS = (
    'skip_parent_seal', 'skip_completed_sources', 'alternate_snapshot',
    'skip_legacy_authentication', 'wrong_legacy_pin', 'wrong_legacy_limit',
    'skip_family_metadata', 'skip_current_authentication', 'wrong_current_pin',
    'wrong_current_limit', 'reverse_paths', 'allow_missing_provider',
)


@pytest.mark.parametrize('attack', _PROVIDER_AST_ATTACKS)
def test_provider_streaming_normalization_rejects_removed_or_substituted_gates(attack):
    filename = 'constructive_g009_support.py'
    tree = _tree(filename)
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == 'parent_seed_paths')
    original = ast.dump(tree, include_attributes=False)
    legacy, current = _streamed_provider_ranges(function)
    body = function.body
    if attack == 'skip_parent_seal':
        del body[_exact_statement_index(body, 'current_parent_specs()')]
    elif attack == 'skip_completed_sources':
        del body[_exact_statement_index(body, 'completed.validate_completed_lower_source_bytes()')]
    elif attack == 'alternate_snapshot':
        body[legacy].value.value.func.attr = 'unsealed_snapshot'
    elif attack == 'skip_legacy_authentication':
        del body[legacy+1]
    elif attack == 'wrong_legacy_pin':
        body[legacy+1].body[0].value.args[0].args[2] = ast.Constant(value='0'*64)
    elif attack == 'wrong_legacy_limit':
        body[legacy+1].body[0].value.args[2] = ast.Constant(value=128*1024*1024)
    elif attack == 'skip_family_metadata':
        del body[current].body[1]
    elif attack == 'skip_current_authentication':
        del body[current].body[2]
    elif attack == 'wrong_current_pin':
        body[current].body[2].value.args[0].args[2] = ast.Constant(value='0'*64)
    elif attack == 'wrong_current_limit':
        body[current].body[2].value.args[2] = ast.Constant(value=128*1024*1024)
    elif attack == 'reverse_paths':
        body[-1].value.args[0] = ast.Call(func=ast.Name(id='reversed', ctx=ast.Load()),
                                        args=[ast.Name(id='paths', ctx=ast.Load())], keywords=[])
    else:
        guard = next(node for node in body if isinstance(node, ast.If))
        guard.test = ast.Constant(value=False)
    assert ast.dump(tree, include_attributes=False) != original
    tree.body = [node for node in tree.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    with pytest.raises(AssertionError):
        normalized = _OriginalBodyNormalization(filename).visit(tree)
        assert sha256(ast.dump(normalized, include_attributes=False).encode()).hexdigest() == (
            ORIGINAL_CALLABLE_AST_SHA256[filename])


def _assert_allocator_numeric_contract(tree):
    expected = {'CPU_LIMITS': '(170,175)', 'WALL_SECONDS': '180',
        'PARENT_TIMEOUT_SECONDS': '185', 'MAX_RSS_BYTES': '1536*1024*1024',
        'MAX_STDOUT_BYTES': '128*1024', 'MAX_STDERR_BYTES': '8*1024',
        'CONTROLLER_WALL_SECONDS': '(2+len(checkpoints.PRINCIPAL_ROOTS))*PARENT_TIMEOUT_SECONDS+WALL_SECONDS'}
    for name, value in expected.items():
        assignments = [node for node in tree.body if _assigned_names(node) == {name}]
        assert len(assignments) == 1
        assert ast.dump(assignments[0].value) == ast.dump(ast.parse(value, mode='eval').body)


def test_new_allocator_policy_is_one_literal_keyword_only_in_the_new_launcher():
    tree = _tree('check_constructive_g009.py')
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == 'run_worker')
    updated = _allocator_environment_index(function)
    assert [keyword.arg for keyword in function.body[updated].value.keywords] == [
        'PYTHONPATH', 'PYTHONMALLOC', 'PYTHONNOUSERSITE', 'PYTHONDONTWRITEBYTECODE']
    locations = [(node.name, keyword.value.value)
                 for node in tree.body if isinstance(node, ast.FunctionDef)
                 for call in ast.walk(node) if isinstance(call, ast.Call)
                 for keyword in call.keywords if keyword.arg == 'PYTHONMALLOC']
    assert locations == [('run_worker', 'pymalloc')]


def test_allocator_normalization_changes_only_the_exact_one_literal():
    function = _function('check_constructive_g009.py', 'run_worker')
    source = ast.unparse(function)
    assert source.count("PYTHONMALLOC='pymalloc'") == 1
    expected = ast.parse(source.replace("PYTHONMALLOC='pymalloc'", "PYTHONMALLOC='malloc'", 1)).body[0]
    actual = _reverse_exact_allocator_policy(deepcopy(function))
    assert ast.dump(actual, include_attributes=False) == ast.dump(expected, include_attributes=False)
    assert "PYTHONNOUSERSITE='1'" in ast.unparse(actual)
    assert "PYTHONDONTWRITEBYTECODE='1'" in ast.unparse(actual)


def test_allocator_policy_never_replaces_a_proof_resource_or_protocol_gate():
    tree = _tree('check_constructive_g009.py')
    _assert_allocator_numeric_contract(tree)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name != 'run_worker':
            assert not any(isinstance(item, ast.Constant) and item.value in {
                'PYTHONMALLOC', 'malloc', 'pymalloc'
            } for item in ast.walk(node))
    function = _function('check_constructive_g009.py', 'run_worker')
    assert _exact_statement_index(function.body,
        'payload = transport._capture_bounded(command,environment)') > _allocator_environment_index(function)
    assert ast.dump(function.body[-1]) == ast.dump(ast.parse(
        'return validate_message(payload,kind=kind,root=root,nonce=nonce,source_binding=source_binding,expected=expected)').body[0])


_ALLOCATOR_AST_ATTACKS = (
    'missing_keyword', 'duplicate_keyword', 'malloc', 'default', 'pymalloc_debug',
    'boolean', 'none', 'inherited_expression', 'wrong_receiver', 'before_copy',
    'after_capture', 'missing_copy', 'changed_pythonpath', 'enabled_usersite',
    'enabled_bytecode', 'misplaced_keyword', 'other_function_keyword',
    'missing_capture', 'missing_validation', 'changed_cpu', 'changed_wall', 'changed_rss',
)


@pytest.mark.parametrize('attack', _ALLOCATOR_AST_ATTACKS)
def test_allocator_policy_normalization_rejects_absent_misplaced_or_weakened_contracts(attack):
    # Only source ASTs are mutated. No altered worker or accepted proof report
    # is executed, and no process allocator setting is changed by these tests.
    filename = 'check_constructive_g009.py'
    tree = _tree(filename)
    function = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == 'run_worker')
    original = ast.dump(tree, include_attributes=False)
    updated = _allocator_environment_index(function)
    update = function.body[updated].value
    keyword = next(item for item in update.keywords if item.arg == 'PYTHONMALLOC')
    if attack == 'missing_keyword':
        update.keywords.remove(keyword)
    elif attack == 'duplicate_keyword':
        update.keywords.append(deepcopy(keyword))
    elif attack in {'malloc', 'default', 'pymalloc_debug', 'boolean', 'none'}:
        keyword.value = ast.Constant(value={'boolean': True, 'none': None}.get(attack, attack))
    elif attack == 'inherited_expression':
        keyword.value = ast.parse("os.environ.get('PYTHONMALLOC')", mode='eval').body
    elif attack == 'wrong_receiver':
        update.func.value.id = 'other_environment'
    elif attack == 'before_copy':
        statement = function.body.pop(updated)
        function.body.insert(updated-1, statement)
    elif attack == 'after_capture':
        statement = function.body.pop(updated)
        captured = _exact_statement_index(function.body,
            'payload = transport._capture_bounded(command,environment)')
        function.body.insert(captured+1, statement)
    elif attack == 'missing_copy':
        del function.body[updated-1]
    elif attack in {'changed_pythonpath', 'enabled_usersite', 'enabled_bytecode'}:
        name = {'changed_pythonpath': 'PYTHONPATH', 'enabled_usersite': 'PYTHONNOUSERSITE',
                'enabled_bytecode': 'PYTHONDONTWRITEBYTECODE'}[attack]
        next(item for item in update.keywords if item.arg == name).value = ast.Constant(value='0')
    elif attack == 'misplaced_keyword':
        update.keywords.remove(keyword)
        next(node for node in ast.walk(function) if _name_call(node, 'print')).keywords.append(keyword)
    elif attack == 'other_function_keyword':
        other = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'binding')
        next(node for node in ast.walk(other) if _attribute_call(
            node, 'support', 'load_candidate_state')).keywords.append(deepcopy(keyword))
    elif attack == 'missing_capture':
        del function.body[_exact_statement_index(function.body,
            'payload = transport._capture_bounded(command,environment)')]
    elif attack == 'missing_validation':
        function.body[-1] = ast.Return(value=ast.Name(id='payload', ctx=ast.Load()))
    else:
        name, value = {'changed_cpu': ('CPU_LIMITS', '(171,176)'),
                       'changed_wall': ('WALL_SECONDS', '181'),
                       'changed_rss': ('MAX_RSS_BYTES', '1537*1024*1024')}[attack]
        assignment = next(node for node in tree.body if _assigned_names(node) == {name})
        assignment.value = ast.parse(value, mode='eval').body
    assert ast.dump(tree, include_attributes=False) != original
    with pytest.raises(AssertionError):
        _assert_allocator_numeric_contract(tree)
        tree.body = [node for node in tree.body
                     if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        normalized = _OriginalBodyNormalization(filename).visit(tree)
        assert sha256(ast.dump(normalized, include_attributes=False).encode()).hexdigest() == (
            ORIGINAL_CALLABLE_AST_SHA256[filename])



def _assert_original_callable_digest(filename, tree):
    tree.body = [node for node in tree.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    normalized = _OriginalBodyNormalization(filename).visit(tree)
    assert sha256(ast.dump(normalized, include_attributes=False).encode()).hexdigest() == (
        ORIGINAL_CALLABLE_AST_SHA256[filename])


def test_private_snapshot_mode_is_postcommit_and_preserves_the_default_return():
    function = _function('build_constructive_g009_explorer.py', '_build_verified')
    normalized = _reverse_exact_snapshot_return(deepcopy(function))
    assert [argument.arg for argument in normalized.args.kwonlyargs] == ['output', 'check']
    assert _exact_statement_index(function.body, _BUILD_SNAPSHOT_MODE_GUARD) == 0
    returned = _exact_statement_index(function.body, _BUILD_SNAPSHOT_RETURN)
    assert isinstance(function.body[returned-1], ast.With)
    assert ast.dump(function.body[-1], include_attributes=False) == ast.dump(
        normalized.body[-1], include_attributes=False)
    assert ast.unparse(function.body[returned].body[-1].value.elts[-1]) == 'retained[0]'


def test_no_argument_bootstrap_owns_temporary_bytes_and_keeps_both_report_copies_exact():
    function = _function('build_constructive_g009_explorer.py', 'fresh_test_snapshot')
    _assert_exact_fresh_snapshot_helper(function)
    assert not function.args.args and not function.args.posonlyargs
    assert not function.args.kwonlyargs and function.args.vararg is function.args.kwarg is None
    transaction = function.body[1]
    assert isinstance(transaction, ast.With)
    assert ast.unparse(transaction.items[0].context_expr) == (
        "TemporaryDirectory(prefix='.g009-test-snapshot-', dir=OUTPUT.parent)")
    calls = [node for node in ast.walk(function) if _name_call(node, '_build_verified')]
    assert len(calls) == 1 and {keyword.arg for keyword in calls[0].keywords} == {'output', 'return_snapshot'}
    assert ast.unparse(next(keyword.value for keyword in calls[0].keywords
                            if keyword.arg == 'output')) == "Path(directory).resolve() / 'files'"
    assert ast.literal_eval(next(keyword.value for keyword in calls[0].keywords
                                 if keyword.arg == 'return_snapshot')) is True
    body = transaction.body
    assert _exact_statement_index(body, 'files = dict(files)') < _exact_statement_index(body,
        'binding = _assert_snapshot_binding(files)')
    assert _exact_statement_index(body, '_validate_live_report(report,state,selected)')+1 == (
        _exact_statement_index(body, 'binding = _assert_snapshot_binding(files)'))
    assert _exact_statement_index(body, 'checkpoints.peak_rss_bytes()') == len(body)-2
    assert ast.unparse(body[-1]) == 'return _FreshSnapshotTests(files, binding, state, selected, report)'
    strings = {node.value for node in ast.walk(function)
               if isinstance(node, ast.Constant) and type(node.value) is str}
    assert 'proof-audit.json' in strings and '/api/checkpoint.json' in strings
    forbidden = {'read_bytes', 'read_text', 'open', 'load', 'loads',
                 'pytest_configure', 'register', 'alarm', 'setrlimit', 'setattr'}
    assert not any(isinstance(node, ast.Attribute) and node.attr in forbidden
                   or isinstance(node, ast.Name) and node.id in forbidden
                   for node in ast.walk(function))


def test_outer_fixture_only_bootstraps_when_the_real_nested_plugin_is_absent():
    function = _function('test_constructive_g009_explorer.py', 'live')
    fallback = _exact_statement_index(function.body, _LIVE_SNAPSHOT_FALLBACK)
    assert fallback == 2
    assert [ast.unparse(item) for item in function.body[fallback+1:]] == [
        "assert type(plugin) is reader._FreshSnapshotTests, 'run the actual fresh builder with --test; saved receipts are not fixtures'",
        'assert reader._assert_snapshot_binding(plugin.files) == plugin.binding',
        'reader._validate_live_report(plugin.report, plugin.state, plugin.selected)',
        'return plugin']
    assert not any(isinstance(node, ast.Attribute) and node.attr in {
        'register', 'pytest_configure', 'skip', 'xfail', 'alarm', 'setrlimit'
    } for node in ast.walk(function))
    source = ast.unparse(_function('build_constructive_g009_explorer.py', '_run_snapshot_tests'))
    assert 'plugins=[plugin]' in source
    assert 'fresh_test_snapshot' not in source


class _BootstrapDenied(RuntimeError):
    """An always-rejecting gate; it never produces a proof or a reader."""


def _isolated_function(filename, function, namespace):
    node = deepcopy(_function(filename, function))
    node.decorator_list = []
    exec(compile(ast.Module(body=[node], type_ignores=[]),
                 '<source-only bootstrap rejection boundary>', 'exec'), namespace)
    return namespace[function]


@pytest.mark.parametrize('mode', (None, 0, 1, '', 'true', (), {}, object()))
def test_nonboolean_snapshot_modes_fail_before_any_output_or_proof_action(tmp_path, mode):
    calls = []
    def reject(*args, **kwargs):
        calls.append((args, kwargs))
        raise _BootstrapDenied('no proof or output action is permitted')
    namespace = {'ExplorerError': ValueError, '_preflight_output': reject}
    build = _isolated_function('build_constructive_g009_explorer.py', '_build_verified', namespace)
    with pytest.raises(ValueError, match='exact Boolean'):
        build(output=tmp_path/'never-created', return_snapshot=mode)
    assert calls == [] and not tuple(tmp_path.iterdir())


@pytest.mark.parametrize('mode', (False, True))
def test_both_boolean_modes_still_reach_the_unchanged_always_rejecting_preflight(tmp_path, mode):
    calls = []
    def reject(output, *, check):
        calls.append((output, check))
        raise _BootstrapDenied('the actual preflight slot is still first')
    namespace = {'ExplorerError': ValueError, '_preflight_output': reject}
    build = _isolated_function('build_constructive_g009_explorer.py', '_build_verified', namespace)
    with pytest.raises(_BootstrapDenied, match='still first'):
        build(output=tmp_path/'never-created', return_snapshot=mode)
    assert calls == [(tmp_path/'never-created', False)]
    assert not tuple(tmp_path.iterdir())


@pytest.mark.parametrize('exception_type', (RuntimeError, KeyboardInterrupt, SystemExit))
def test_bootstrap_propagates_always_rejecting_build_and_cleans_its_owned_temporary_directory(
        tmp_path, exception_type):
    from tempfile import TemporaryDirectory
    observed = []
    def reject(*, output, return_snapshot):
        assert type(return_snapshot) is bool and return_snapshot is True
        assert output.name == 'files' and output.parent.parent == tmp_path.resolve()
        assert output.is_absolute() and not output.exists()
        observed.append(output)
        # Non-proof bytes left by an always-raising transport fixture only.
        output.mkdir()
        (output/'TRANSPORT-ONLY.txt').write_bytes(b'No proof, report or reader was accepted.\n')
        raise exception_type('the fresh build did not succeed')
    namespace = {'Path': Path, 'TemporaryDirectory': TemporaryDirectory,
                 'OUTPUT': tmp_path/'public-output', '_build_verified': reject}
    bootstrap = _isolated_function('build_constructive_g009_explorer.py', 'fresh_test_snapshot', namespace)
    with pytest.raises(exception_type, match='did not succeed'):
        bootstrap()
    assert len(observed) == 1
    assert not observed[0].exists() and not observed[0].parent.exists()
    assert not tuple(tmp_path.iterdir())


@pytest.mark.parametrize('present', (False, True))
def test_absent_or_none_plugin_reaches_only_the_always_rejecting_fresh_bootstrap(present):
    calls = []
    def reject():
        calls.append('real fresh bootstrap required')
        raise _BootstrapDenied('no fixture was manufactured')
    reader = SimpleNamespace(fresh_test_snapshot=reject)
    live = _isolated_function('test_constructive_g009_explorer.py', 'live', {'reader': reader})
    config = SimpleNamespace(**({'_g009_fresh_snapshot': None} if present else {}))
    with pytest.raises(_BootstrapDenied, match='manufactured'):
        live(config)
    assert calls == ['real fresh bootstrap required']


@pytest.mark.parametrize('invalid', (False, 0, '', {}, object()))
def test_present_invalid_plugin_is_rejected_without_replacing_it_with_a_bootstrap(invalid):
    calls = []
    def reject():
        calls.append('unexpected bootstrap')
        raise _BootstrapDenied('an invalid supplied fixture must not be replaced')
    class NeverInstantiatedSnapshot:
        pass
    reader = SimpleNamespace(fresh_test_snapshot=reject, _FreshSnapshotTests=NeverInstantiatedSnapshot)
    live = _isolated_function('test_constructive_g009_explorer.py', 'live', {'reader': reader})
    with pytest.raises(AssertionError, match='saved receipts are not fixtures'):
        live(SimpleNamespace(_g009_fresh_snapshot=invalid))
    assert calls == []


_BOOTSTRAP_RETURN_MUTATIONS = (
    'default_true', 'missing_mode_guard', 'permissive_mode_guard', 'mode_guard_after_preflight',
    'return_before_audit', 'return_before_commit', 'missing_final_check', 'mutable_report_return',
    'foreign_retained_return', 'changed_default_return', 'missing_real_audit',
    'optional_inner_tests', 'missing_commit', 'changed_worker_count',
)


@pytest.mark.parametrize('attack', _BOOTSTRAP_RETURN_MUTATIONS)
def test_snapshot_return_normalization_rejects_misplaced_or_weakened_fresh_gates(attack):
    filename = 'build_constructive_g009_explorer.py'
    tree = _tree(filename)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_build_verified')
    original = ast.dump(tree, include_attributes=False)
    returned = _exact_statement_index(function.body, _BUILD_SNAPSHOT_RETURN)
    if attack == 'default_true':
        function.args.kw_defaults[-1] = ast.Constant(value=True)
    elif attack == 'missing_mode_guard':
        del function.body[0]
    elif attack == 'permissive_mode_guard':
        function.body[0].test = ast.parse('not isinstance(return_snapshot, (bool, int))', mode='eval').body
    elif attack == 'mode_guard_after_preflight':
        function.body.insert(1, function.body.pop(0))
    elif attack == 'return_before_audit':
        function.body.insert(2, function.body.pop(returned))
    elif attack == 'return_before_commit':
        addition = function.body.pop(returned)
        function.body[returned-1].body.insert(-1, addition)
    elif attack == 'missing_final_check':
        del function.body[returned].body[0]
    elif attack == 'mutable_report_return':
        function.body[returned].body[-1].value.elts[-1] = ast.Name(id='report', ctx=ast.Load())
    elif attack == 'foreign_retained_return':
        function.body[returned].body[-1].value.elts[-1] = ast.Tuple(elts=[], ctx=ast.Load())
    elif attack == 'changed_default_return':
        function.body[-1].value.elts.append(ast.Name(id='retained', ctx=ast.Load()))
    elif attack == 'missing_real_audit':
        call = next(node for node in ast.walk(function) if _attribute_call(node, 'proof_audit', 'verify_in_fresh_windows'))
        call.func.attr = 'read_saved_report'
    elif attack == 'optional_inner_tests':
        call = next(node for node in ast.walk(function) if _name_call(node, '_fork_render_phase'))
        next(keyword for keyword in call.keywords if keyword.arg == 'test').value = ast.Constant(value=False)
    elif attack == 'missing_commit':
        function.body[returned-1].body.pop()
    else:
        actual_audit = next(node for node in ast.walk(function)
                            if _attribute_call(node, 'proof_audit', 'verify_in_fresh_windows'))
        actual_audit.keywords.append(ast.keyword(arg='jobs', value=ast.Constant(value=7)))
    assert ast.dump(tree, include_attributes=False) != original
    with pytest.raises(AssertionError):
        _assert_original_callable_digest(filename, tree)


_BOOTSTRAP_HELPER_MUTATIONS = (
    ("def fresh_test_snapshot():", "def fresh_test_snapshot(report=None):"),
    ("return_snapshot=True", "return_snapshot=False"),
    ("Path(directory).resolve() / 'files'", "Path(directory)"),
    ("type(retained) is not tuple", "False"),
    ("type(retained[0]) is not support.CandidateState", "False"),
    ("type(retained[1]) is not support.SupportSelection", "False"),
    ("type(retained[2]) is not bytes", "False"),
    ("proof_audit.transport._decode_message(payload)", "json.loads(payload)"),
    ("proof_audit.canonical_message(report) != payload", "False"),
    ("type(files) is not dict", "False"),
    ("type(value) is not bytes", "False"),
    ("worker_peak != report['peak_rss_bytes']", "False"),
    ("not 0 < render_peak <= proof_audit.MAX_RSS_BYTES", "False"),
    ("files = dict(files)", "files = files"),
    ("'proof-audit.json', SLUG + '/api/checkpoint.json'", "'proof-audit.json', 'proof-audit.json'"),
    ("_validate_live_report(report, state, selected)", "pass"),
    ("binding = _assert_snapshot_binding(files)", "binding = 'not-current'"),
    ("checkpoints.peak_rss_bytes()", "pass"),
)


@pytest.mark.parametrize('old,new', _BOOTSTRAP_HELPER_MUTATIONS)
def test_fresh_helper_normalization_rejects_every_weakened_type_byte_scope_or_resource_boundary(old, new):
    filename = 'build_constructive_g009_explorer.py'
    tree = _tree(filename)
    index = next(index for index, node in enumerate(tree.body)
                 if isinstance(node, ast.FunctionDef) and node.name == 'fresh_test_snapshot')
    source = ast.unparse(tree.body[index])
    assert source.count(old) == 1
    tree.body[index] = ast.parse(source.replace(old, new, 1)).body[0]
    with pytest.raises(AssertionError):
        _assert_original_callable_digest(filename, tree)


@pytest.mark.parametrize('attack', ('truthy_fallback', 'fallback_for_any_invalid', 'missing_type_guard',
                                   'missing_binding_guard', 'missing_report_guard', 'register_outer_plugin'))
def test_fixture_bootstrap_normalization_rejects_invalid_plugin_fallback_or_missing_final_guards(attack):
    filename = 'test_constructive_g009_explorer.py'
    tree = _tree(filename)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'live')
    fallback = _exact_statement_index(function.body, _LIVE_SNAPSHOT_FALLBACK)
    if attack == 'truthy_fallback':
        function.body[fallback].test = ast.parse('not plugin', mode='eval').body
    elif attack == 'fallback_for_any_invalid':
        function.body[fallback].test = ast.parse(
            'type(plugin) is not reader._FreshSnapshotTests', mode='eval').body
    elif attack == 'missing_type_guard':
        del function.body[fallback+1]
    elif attack == 'missing_binding_guard':
        del function.body[fallback+2]
    elif attack == 'missing_report_guard':
        del function.body[fallback+3]
    else:
        function.body.insert(-1, ast.parse('pytestconfig.pluginmanager.register(plugin)').body[0])
    with pytest.raises(AssertionError):
        _assert_original_callable_digest(filename, tree)


def _definition_namespace_only(rows):
    """Execute only actual label filtering/count assertions, with no proof input."""
    function = _function('test_constructive_g009_explorer.py',
        'test_same_live_conservative_definitions_three_typed_edges_and_proof_only_paths')
    position = _exact_statement_index(function.body, _NEW_DEFINITION_NAMESPACE)
    nodes = deepcopy(function.body[position:position+4])
    expected = tuple(SimpleNamespace(name='definition_'+str(index)) for index in range(316, 327))
    namespace = {'corpus': {'definitions': rows},
                 'reader': SimpleNamespace(G009_DEFINITIONS=expected)}
    exec(compile(ast.Module(body=nodes, type_ignores=[]),
                 '<definition namespace labels only; no theorem evidence>', 'exec'), namespace)
    return namespace['new']


def _definition_namespace_rows():
    return [{'id': 'ND'+str(index).zfill(4), 'name': 'definition_'+str(index)}
            for index in range(316, 327)]


@pytest.mark.parametrize('outside', ('PD0316', 'PD0999', 'PD9999', 'XD0316', 'ND0315', 'ND0001'))
def test_definition_namespace_does_not_confuse_other_registries_or_prior_nd_rows(outside):
    rows = _definition_namespace_rows()+[{'id': outside, 'name': 'unrelated_definition'}]
    result = _definition_namespace_only(rows)
    assert len(result) == 11
    assert {row['id'] for row in result.values()} == {'ND'+str(index).zfill(4) for index in range(316,327)}


@pytest.mark.parametrize('attack', ('missing_first', 'missing_last', 'wrong_namespace', 'below_window',
                                   'above_window', 'duplicate_id', 'noncanonical_width', 'nonnumeric_suffix'))
def test_definition_namespace_requires_every_exact_nd0316_through_nd0326_identity(attack):
    rows = _definition_namespace_rows()
    if attack == 'missing_first':
        rows.pop(0)
    elif attack == 'missing_last':
        rows.pop()
    else:
        rows[0]['id'] = {
            'wrong_namespace': 'PD0316', 'below_window': 'ND0315',
            'above_window': 'ND0327', 'duplicate_id': 'ND0317',
            'noncanonical_width': 'ND316', 'nonnumeric_suffix': 'ND0316x',
        }[attack]
    with pytest.raises(AssertionError):
        _definition_namespace_only(rows)


@pytest.mark.parametrize('attack', ('no_namespace', 'or_namespace', 'wrong_namespace', 'wrong_lower_bound',
                                   'missing_id_set', 'wider_id_set', 'id_set_before_count'))
def test_definition_namespace_normalization_does_not_mask_bad_or_misplaced_predicates(attack):
    filename = 'test_constructive_g009_explorer.py'
    tree = _tree(filename)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'test_same_live_conservative_definitions_three_typed_edges_and_proof_only_paths')
    assignment = _exact_statement_index(function.body, _NEW_DEFINITION_NAMESPACE)
    ids = _exact_statement_index(function.body, _NEW_DEFINITION_ID_SET)
    predicate = function.body[assignment].value.generators[0].ifs[0]
    if attack == 'no_namespace':
        function.body[assignment].value.generators[0].ifs = [predicate.values[1]]
    elif attack == 'or_namespace':
        predicate.op = ast.Or()
    elif attack == 'wrong_namespace':
        predicate.values[0].args[0].value = 'PD'
    elif attack == 'wrong_lower_bound':
        predicate.values[1].comparators[0].value = 'ND0315'
    elif attack == 'missing_id_set':
        del function.body[ids]
    elif attack == 'wider_id_set':
        call = next(node for node in ast.walk(function.body[ids]) if _name_call(node, 'range'))
        call.args[1].value = 328
    else:
        function.body.insert(ids-1, function.body.pop(ids))
    with pytest.raises(AssertionError):
        _assert_original_callable_digest(filename, tree)
