"""Registration and fail-closed controls, never substitute proof evidence.

The ``test_production_*`` cases require actual final source/spec/artifact
registration. They fail, rather than skip or synthesize seals, until that
registration exists. Before sealing, the remaining cases can be run with
``-k 'not production'``; that is explicitly a partial test result.

Neither cohort imports current Alpha metadata, decodes a proof artifact,
executes Lean, or replays a candidate. Production tests authenticate actual
bytes and ninety ordinary specifications only. Complete original-HA,
same-byte Lean and ordinary-principal checks remain separate requirements.
"""

import ast
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys

import pytest

# Observe this module's own imports and operations, not other CI modules.
_WATCHED_MODULE_ROOTS = ('peano_lab.library.editions_v31',)


def _tracked_module_identities(modules=None):
    modules = sys.modules if modules is None else modules
    return {name:module for name,module in modules.items()
            if any(name == root or name.startswith(root+'.') for root in _WATCHED_MODULE_ROOTS)}


def _assert_tracked_modules_unchanged(before,modules=None):
    after = _tracked_module_identities(modules)
    assert after.keys() == before.keys(), 'authority module inventory changed'
    assert all(after[name] is module for name,module in before.items()), 'authority module identity changed'


@pytest.fixture(autouse=True)
def _authority_module_baseline():
    before = _tracked_module_identities()
    yield before
    _assert_tracked_modules_unchanged(before)


_PROJECT_IMPORT_MODULES_BEFORE = _tracked_module_identities()

import constructive_g009_support as support
import constructive_g009_checkpoints as checkpoints
import check_constructive_g009 as driver
import export_constructive_g009 as exporter
from peano_lab.library.theorems import TheoremSpec


EXPECTED_FACTORIES = (
    ('arithmetic_multiplicative_candidate',11,10836,'f4374450ec543f69093b98367c90f67f09ac15daacd1df2f90961d7b6ece4a7e'),
    ('coprime_divisor_decomposition_candidate',8,14805,'de19bb61543f5d7ab3a1d1b675c96ae4b31c7c96b58d6107904e7188973a2e1c'),
    ('divisor_pair_index_candidate',4,6642,'fc6a5a555fdee62cf5f54365163f32c4acfee10b8f416b811bb69debdbcf62a0'),
    ('signed_block_sum_candidate',7,14390,'0597b3806fec32b8eb117f5d0f6be2304c754aa8078df6f50de9dd4d12a2c18f'),
    ('signed_cartesian_product_candidate',20,33563,'d7dbe1d9a82ee5b91e33d6a4624d3e7f05b20d4618045ecab8e753eee6c7e351'),
    ('signed_support_reindex_candidate',25,44258,'db91e38ca5e671adf88e3bf70396b1a242f9c760d6f2c52c4785e6a63316339e'),
    ('dirichlet_multiplicative_entry_candidate',5,10482,'d7f55b8f25e56f8b9c5bc3f6c4b83698d5f1ad770e1e4ed77c53f12a602bd897'),
    ('dirichlet_multiplicative_support_candidate',6,19151,'56e9f8ccaa7c795e42b33984bc2346182ba3a1f820883ba884e571b89091d4a5'),
    ('dirichlet_multiplicative_candidate',4,9345,'bb1342735115781fd8f0107d3876c95098e0b6dc459f31981ffb2c16432eab77'),
)
EXPECTED_SPECS_SHA256 = '25086b5c317b7dddd47cc06b0d9ad5639b6a5d88b6ede323cf7aa1124fa9dba7'
EXPECTED_PRINCIPALS = (
    'signed_support_reindex_sum_equal',
    'signed_cartesian_product_sums_exists',
    'coprime_divisor_factor_pair_exists_unique',
    'dirichlet_convolution_multiplicative_values',
    'dirichlet_convolution_multiplicative_table',
    'dirichlet_convolution_multiplicative_exists_unique',
)


def _forbid_authority_access(monkeypatch):
    """Only rejecting sentinels: no synthetic successful verifier return."""
    def forbidden(*_args,**_kwargs):
        pytest.fail('this metadata/negative test must not reach proof authority')
    for module,names in (
        (support,('current_parent_specs','parent_seed_paths','select_support')),
        (support.closure,('check_bottom_layer_bundle','replay_bottom_layer_theorem',
                         'assemble_bottom_layer_bundle')),
        (checkpoints,('decode_proof_bundle','check')),
        (checkpoints.independent,('_lean_check','_check_lean_binary')),
        (driver,('run_worker',)),
    ):
        for name in names:
            monkeypatch.setattr(module,name,forbidden)


def row(name,deps=()):
    # Syntax-only fixtures. They never reach a checker or acceptance API.
    return TheoremSpec(name,'0=0',deps,('refl',),'synthetic topology fixture')


def test_inventory_is_exact_nine_factories_ninety_rows_not_an_admission():
    assert tuple((item.module,item.count) for item in support.FACTORIES) == tuple(
        (module,count) for module,count,_size,_digest in EXPECTED_FACTORIES)
    assert len({item.module for item in support.FACTORIES}) == 9
    assert sum(item.count for item in support.FACTORIES) == support.EXPECTED_NEW_COUNT == 90
    assert support.PARENT_COUNT == 3796 and support.PARENT_STABLE_COUNT == 432
    assert checkpoints.PRINCIPAL_ROOTS == EXPECTED_PRINCIPALS
    assert len(set(checkpoints.PRINCIPAL_ROOTS)) == 6


@pytest.mark.parametrize('function',(
    support.require_final_source_pins,checkpoints.require_final_inventory,
    checkpoints.verify_checkpoint,driver.verify_in_fresh_windows,
))
@pytest.mark.parametrize('field,absent',(
    ('MATH_SOURCE_PINS',()),('PARENT_CONTROL_PINS',()),('NEW_SPECS_SHA256',''),
))
def test_all_final_entrypoints_fail_closed_when_a_source_seal_is_removed(monkeypatch,function,field,absent):
    _forbid_authority_access(monkeypatch)
    monkeypatch.setattr(support,field,absent)
    with pytest.raises(support.G009Error,match='not sealed'):
        function()


@pytest.mark.parametrize('name',checkpoints.PRINCIPAL_ROOTS)
def test_even_valid_principals_fail_closed_when_math_pins_are_removed(monkeypatch,name):
    _forbid_authority_access(monkeypatch)
    monkeypatch.setattr(support,'MATH_SOURCE_PINS',())
    with pytest.raises(support.G009Error,match='not sealed'):
        checkpoints.verify_principal_root(name)


@pytest.mark.parametrize('name',('', 'unknown', '0=0', None, 1))
def test_unregistered_principals_fail_before_any_artifact(name):
    with pytest.raises(support.G009Error,match='exact G009 principal'):
        checkpoints.verify_principal_root(name)


@pytest.mark.parametrize('argv',(
    ('--through','1'),('--seed','old.json'),('--seed-only',),
    ('--read-report','receipt.json'),('--receipt','receipt.json'),('--artifact','prefix.json'),
))
def test_final_cli_has_no_partial_seed_or_saved_receipt_acceptance_mode(argv):
    with pytest.raises(SystemExit) as error:
        driver.main(list(argv))
    assert error.value.code == 2


def test_exact_dependency_cone_keeps_parent_rows_inherited_and_cross_support_separate():
    parent = (row('p0'),row('p1',('p0',)),row('unrelated_parent'))
    new = (row('cross',('p1',)),row('owned',('cross',)),row('unrelated_new'))
    actual = support.dependency_cone(parent,new,('owned',))
    assert tuple(item.name for item in actual) == ('p0','p1','cross','owned')
    selected = support.SupportSelection((new[1],),('cross',),('p0','p1'),(),None,actual)
    assert selected.role('p0') == selected.role('p1') == 'inherited_alpha_v31'
    assert selected.role('cross') == 'new_cross_track_support'
    assert selected.role('owned') == 'new_owned_theorem'
    with pytest.raises(support.G009Error):
        selected.role('unrelated_parent')


@pytest.mark.parametrize('parent,new,owned',(
    ((row('p'),),(row('n',('absent',)),),('n',)),
    ((row('p'),),(row('n',('later',)),row('later')),('n',)),
    ((row('p'),),(row('n',('n',)),),('n',)),
    ((row('p'),),(row('p'),),('p',)),
    ((row('p'),),(row('n'),row('n')),('n',)),
    ((row('p',('absent',)),),(row('n'),),('n',)),
    ((row('p'),),(row('n',('p','p')),),('n',)),
    ((row('p'),),(replace(row('n'),dependencies=['p']),),('n',)),
    ((row('p'),),(row('n'),),('p',)),
    ((row('p'),),(row('n'),),('n','n')),
    ((row('p'),),(row('n'),),()),
    ((row('p'),),(row('n'),),(['n'],)),
))
def test_missing_forward_cyclic_duplicate_or_recounted_inputs_rejected(parent,new,owned):
    with pytest.raises(support.G009Error):
        support.dependency_cone(parent,new,owned)


def test_bounded_regular_file_and_exact_byte_pin(tmp_path):
    path = tmp_path/'fixture'
    path.write_bytes(b'only test data')
    pin = support.FilePin('fixture',14,sha256(b'only test data').hexdigest())
    assert support.bounded_bytes(path,14) == b'only test data'
    support.check_pin(pin,tmp_path,14)
    path.write_bytes(b'other contents')
    with pytest.raises(support.G009Error):
        support.check_pin(pin,tmp_path,14)


@pytest.mark.parametrize('mode',('oversized','empty','symlink','directory','missing'))
def test_invalid_bounded_sources_rejected_before_parse(tmp_path,mode):
    path = tmp_path/'source'
    if mode == 'oversized': path.write_bytes(b'x'*33)
    elif mode == 'empty': path.write_bytes(b'')
    elif mode == 'symlink':
        target = tmp_path/'target'; target.write_bytes(b'x'); path.symlink_to(target)
    elif mode == 'directory': path.mkdir()
    with pytest.raises(support.G009Error):
        support.bounded_bytes(path,32)


def _read_fixture(path,kind,raw=b'bounded file fixture',maximum=None):
    if maximum is None:
        maximum = len(raw)
    if kind == 'bytes':
        return support.bounded_bytes(path,maximum)
    return support.check_pin(support.FilePin(path.name,len(raw),sha256(raw).hexdigest()),path.parent,maximum)


@pytest.mark.parametrize('kind',('bytes','pin'))
@pytest.mark.parametrize('maximum',(None,True,0,-1,1.5,64*1024*1024+1))
def test_both_readers_enforce_the_unchanged_strict_maximum(kind,maximum,tmp_path):
    path = tmp_path/'file';path.write_bytes(b'x')
    with pytest.raises(support.G009Error):
        if kind == 'bytes':
            support.bounded_bytes(path,maximum)
        else:
            support.check_pin(support.FilePin('file',1,sha256(b'x').hexdigest()),tmp_path,maximum)


@pytest.mark.parametrize('kind',('bytes','pin'))
def test_symlink_ancestor_is_rejected_even_with_the_exact_authenticated_bytes(kind,tmp_path):
    actual = tmp_path/'actual';actual.mkdir()
    raw = b'bounded file fixture';(actual/'file').write_bytes(raw)
    alias = tmp_path/'alias';alias.symlink_to(actual,target_is_directory=True)
    with pytest.raises(support.G009Error,match='ancestor'):
        _read_fixture(alias/'file',kind,raw)


@pytest.mark.parametrize('kind',('bytes','pin'))
def test_non_directory_ancestor_fails_before_any_leaf_read(kind,tmp_path):
    parent = tmp_path/'not_directory';parent.write_bytes(b'not a directory')
    with pytest.raises(support.G009Error):
        _read_fixture(parent/'file',kind)


@pytest.mark.parametrize('kind',('bytes','pin'))
def test_unrelated_ancestor_contents_can_change_without_invalidating_a_file(kind,tmp_path,monkeypatch):
    path = tmp_path/'file';raw = b'bounded file fixture';path.write_bytes(raw)
    opened = os.open
    def create_unrelated(name,flags,*args,**kwargs):
        if Path(name) == path:
            (tmp_path/'unrelated').write_bytes(b'an unrelated new file')
        return opened(name,flags,*args,**kwargs)
    monkeypatch.setattr(support.os,'open',create_unrelated)
    actual = _read_fixture(path,kind,raw)
    assert actual == (raw if kind == 'bytes' else None)


@pytest.mark.parametrize('kind',('bytes','pin'))
@pytest.mark.parametrize('swap',('same_bytes_new_inode','symlink','fifo'))
def test_leaf_swap_between_lstat_and_open_cannot_change_the_descriptor(kind,swap,tmp_path,monkeypatch):
    path = tmp_path/'file';raw = b'bounded file fixture';path.write_bytes(raw)
    other = tmp_path/'other';other.write_bytes(raw)
    opened = os.open
    calls = []
    def swap_before_open(name,flags,*args,**kwargs):
        if Path(name) == path:
            calls.append(flags)
            assert flags & os.O_NOFOLLOW and flags & os.O_CLOEXEC and flags & os.O_NONBLOCK
            path.rename(tmp_path/'old-file')
            if swap == 'same_bytes_new_inode':
                path.write_bytes(raw)
            elif swap == 'symlink':
                path.symlink_to(other)
            else:
                os.mkfifo(path)
        return opened(name,flags,*args,**kwargs)
    monkeypatch.setattr(support.os,'open',swap_before_open)
    with pytest.raises(support.G009Error):
        _read_fixture(path,kind,raw)
    assert len(calls) == 1


def _intercept_first_read(monkeypatch,hook):
    original_fdopen = os.fdopen
    class Stream:
        def __init__(self,stream):
            self.stream,self.called = stream,False
        def __enter__(self):
            self.stream.__enter__()
            return self
        def __exit__(self,*args):
            return self.stream.__exit__(*args)
        def fileno(self):
            return self.stream.fileno()
        def read(self,size):
            result = self.stream.read(size)
            if not self.called:
                self.called = True
                hook()
            return result
    monkeypatch.setattr(support.os,'fdopen',lambda *args,**kwargs:Stream(original_fdopen(*args,**kwargs)))


@pytest.mark.parametrize('kind',('bytes','pin'))
@pytest.mark.parametrize('change',('same_length','grow','shrink','new_inode','symlink','mode'))
def test_in_read_changes_are_rejected_after_the_actual_descriptor_read(kind,change,tmp_path,monkeypatch):
    path = tmp_path/'file';raw = b'bounded file fixture';path.write_bytes(raw)
    def mutate():
        if change == 'same_length': path.write_bytes(b'!' + raw[1:])
        elif change == 'grow': path.write_bytes(raw + b'!')
        elif change == 'shrink': path.write_bytes(raw[:-1])
        elif change == 'mode': path.chmod(path.stat().st_mode ^ 0o100)
        else:
            path.rename(tmp_path/'original-file')
            if change == 'new_inode': path.write_bytes(raw)
            else: path.symlink_to(tmp_path/'original-file')
    _intercept_first_read(monkeypatch,mutate)
    with pytest.raises(support.G009Error):
        _read_fixture(path,kind,raw)


@pytest.mark.parametrize('kind',('bytes','pin'))
@pytest.mark.parametrize('moment',('open','read'))
def test_replaced_parent_is_rejected_even_when_leaf_inode_and_bytes_stay_exact(kind,moment,tmp_path,monkeypatch):
    parent = tmp_path/'parent';parent.mkdir()
    path = parent/'file';raw = b'bounded file fixture';path.write_bytes(raw)
    replacement = tmp_path/'replacement';replacement.mkdir()
    # Both directories point to the same real leaf before the first stat.
    # Moving only their parent names changes no file data or leaf identity.
    os.link(path,replacement/'file')
    before = support._file_identity(path.stat())
    def swap():
        parent.rename(tmp_path/'old-parent')
        replacement.rename(parent)
        assert support._file_identity(path.stat()) == before
    if moment == 'read':
        _intercept_first_read(monkeypatch,swap)
    else:
        opened = os.open
        def swap_parent(name,flags,*args,**kwargs):
            if Path(name) == path: swap()
            return opened(name,flags,*args,**kwargs)
        monkeypatch.setattr(support.os,'open',swap_parent)
    with pytest.raises(support.G009Error,match='ancestor changed'):
        _read_fixture(path,kind,raw)


@pytest.mark.parametrize('kind',('bytes','pin'))
def test_owned_descriptor_is_closed_after_a_failed_identity_check(kind,tmp_path,monkeypatch):
    path = tmp_path/'file';raw = b'bounded file fixture';path.write_bytes(raw)
    opened = os.open
    descriptors = []
    def record_and_swap(name,flags,*args,**kwargs):
        if Path(name) == path:
            path.rename(tmp_path/'old-file')
            path.write_bytes(raw)
        descriptor = opened(name,flags,*args,**kwargs)
        descriptors.append(descriptor)
        return descriptor
    monkeypatch.setattr(support.os,'open',record_and_swap)
    with pytest.raises(support.G009Error):
        _read_fixture(path,kind,raw)
    assert len(descriptors) == 1
    with pytest.raises(OSError):
        os.fstat(descriptors[0])


def test_large_pins_really_stream_in_at_most_one_mib_reads(tmp_path,monkeypatch):
    path = tmp_path/'artifact';raw = b'x' * (3*1024*1024+7);path.write_bytes(raw)
    original_fdopen = os.fdopen
    requests = []
    class Stream:
        def __init__(self,stream): self.stream = stream
        def __enter__(self): self.stream.__enter__();return self
        def __exit__(self,*args): return self.stream.__exit__(*args)
        def fileno(self): return self.stream.fileno()
        def read(self,size):
            requests.append(size)
            assert 0 < size <= 1024*1024
            return self.stream.read(size)
    monkeypatch.setattr(support.os,'fdopen',lambda *args,**kwargs:Stream(original_fdopen(*args,**kwargs)))
    pin = support.FilePin(path.name,len(raw),sha256(raw).hexdigest())
    assert support.check_pin(pin,tmp_path,support.MAX_CATALOG_COMPONENT_BYTES) is None
    assert len(requests) == 5 and max(requests) == 1024*1024
    assert support.MAX_CATALOG_COMPONENT_BYTES == 64*1024*1024


@pytest.mark.parametrize('pin',(
    support.FilePin('../escape',1,'0'*64),support.FilePin('/absolute',1,'0'*64),
    support.FilePin('data',True,'0'*64),support.FilePin('data',0,'0'*64),
    support.FilePin('data',33,'0'*64),support.FilePin('data',1,'bad'),
    support.FilePin('data',1,None),
))
def test_malformed_literal_file_pins_rejected(pin,tmp_path):
    with pytest.raises(support.G009Error):
        support.check_pin(pin,tmp_path,32)


@pytest.mark.parametrize('seed_only,seeds',((1,()),(False,[]),(True,())))
def test_invalid_authoring_seed_options_do_not_run_proofs(seed_only,seeds,tmp_path):
    with pytest.raises(support.G009Error):
        exporter.export_authoring_bundle(('x',),tmp_path/'never.json',seed_bundles=seeds,seed_only=seed_only)
    assert not (tmp_path/'never.json').exists()


def test_authoring_output_cannot_escape_the_task_or_overwrite(tmp_path,monkeypatch):
    outside = tmp_path/'outside.json'
    with pytest.raises(support.G009Error,match='task artifact directory'):
        exporter.export_authoring_bundle(('x',),outside)
    assert not outside.exists()
    # Private filesystem data only. Exercise the real production-directory
    # branch and reject the existing file before any proof/source access.
    fixture_root = tmp_path/'owned-repository'
    artifact_directory = fixture_root/'research/arithmetic-library/artifacts'
    artifact_directory.mkdir(parents=True)
    existing = artifact_directory/'existing.json'
    existing.write_bytes(b'non-authority overwrite fixture; not proof data\n')
    monkeypatch.setattr(support,'ROOT',fixture_root)
    monkeypatch.setattr(support,'HERE',fixture_root/'scripts')
    with pytest.raises(support.G009Error,match='never overwritten'):
        exporter.export_authoring_bundle(('x',),existing)


def _protocol_fixture():
    # Pure IPC bytes, deliberately not a mathematical success report.
    expected = {'synthetic_transport_fixture':True}
    value = {'schema':driver.SCHEMA,'kind':'bundle','slug':checkpoints.SLUG,'root':None,
        'nonce':'a'*64,'binding_sha256':'b'*64,'limits':{'cpu':[170,175],'wall_seconds':180,
        'max_rss_bytes':1536*1024*1024},'peak_rss_bytes':1024,'report':expected}
    return value,expected


def test_unchanged_canonical_transport_parser_only(monkeypatch):
    _forbid_authority_access(monkeypatch)
    value,expected = _protocol_fixture()
    report,peak = driver.validate_message(driver.canonical_message(value),kind='bundle',root=None,
        nonce='a'*64,source_binding='b'*64,expected=expected)
    assert report == expected and peak == 1024


def test_wire_codec_is_exact_unchanged_newline_terminated_canonical_json():
    assert driver.canonical_message is driver.transport._canonical
    assert driver.canonical_message({'z':False,'a':'μ'}) == '{"a":"μ","z":false}\n'.encode('utf-8')
    with pytest.raises(ValueError):
        driver.canonical_message({'not_finite':float('nan')})


@pytest.mark.parametrize('ending',(b'',b'\n\n'))
def test_valid_wire_message_with_missing_or_extra_terminator_rejected(ending):
    envelope,expected = _protocol_fixture()
    payload = driver.canonical_message(envelope)[:-1]+ending
    with pytest.raises(driver.transport.AuditWorkerError,match='noncanonical'):
        driver.validate_message(payload,kind='bundle',root=None,nonce='a'*64,
                                source_binding='b'*64,expected=expected)


@pytest.mark.parametrize('field,value',(
    ('schema','foreign'),('kind','root'),('slug','other'),('root','foreign_root'),
    ('nonce','c'*64),('binding_sha256','c'*64),('peak_rss_bytes',True),
    ('peak_rss_bytes',0),('peak_rss_bytes',1536*1024*1024+1),('report',{'saved_success':True}),
    ('limits',{'cpu':[171,175],'wall_seconds':180,'max_rss_bytes':1536*1024*1024}),
))
def test_stale_foreign_forged_or_relaxed_transport_rejected(field,value):
    envelope,expected = _protocol_fixture();envelope[field] = value
    with pytest.raises((support.G009Error,driver.transport.AuditWorkerError)):
        driver.validate_message(driver.canonical_message(envelope),kind='bundle',root=None,
            nonce='a'*64,source_binding='b'*64,expected=expected)


@pytest.mark.parametrize('payload',(b'',b'{"x":1,"x":2}',b'{"x":NaN}',b'[]',b'{ "x": 1 }',b'x'*(128*1024+1)))
def test_malformed_oversized_noncanonical_transport_rejected(payload):
    with pytest.raises(driver.transport.AuditWorkerError):
        driver.validate_message(payload,kind='bundle',root=None,nonce='a'*64,
                                source_binding='b'*64,expected={})


def test_original_limits_separate_jobs_and_no_old_global_or_cache_patches():
    assert driver.CPU_LIMITS == exporter.CPU_LIMITS == (170,175)
    assert driver.WALL_SECONDS == exporter.WALL_SECONDS == 180
    assert driver.MAX_RSS_BYTES == 1536*1024*1024
    assert driver.CONTROLLER_WALL_SECONDS == 8*185+180
    sources = (support,checkpoints,driver,exporter)
    for module in sources:
        source = Path(module.__file__).read_text()
        tree = ast.parse(source)
        calls = [node for node in ast.walk(tree) if isinstance(node,ast.Call)]
        assert not any(isinstance(call.func,ast.Attribute) and call.func.attr == 'cache_clear' for call in calls)
        assert not any(isinstance(call.func,ast.Name) and call.func.id == 'setattr' for call in calls)
    assert 'assemble_bottom_layer_bundle' in Path(exporter.__file__).read_text()
    assert 'check_bottom_layer_bundle' in Path(checkpoints.__file__).read_text()
    assert 'replay_bottom_layer_theorem' in Path(checkpoints.__file__).read_text()
    assert 'independent._lean_check(checkpoint,receipt.node_count,bundle.root,payload)' in Path(checkpoints.__file__).read_text()
    assert 'check((),proof.certificate,formula)' in Path(checkpoints.__file__).read_text()


def test_this_scaffold_suite_never_imported_current_alpha_metadata(_authority_module_baseline):
    _assert_tracked_modules_unchanged(_authority_module_baseline)


def test_production_registers_exact_nine_frozen_source_identities():
    expected = tuple(support.FilePin(
        'peano-lab/py/peano_lab/library/'+module+'.py',size,digest,
    ) for module,_count,size,digest in EXPECTED_FACTORIES)
    assert support.MATH_SOURCE_PINS == expected, 'final nine-source registration is required'
    assert support.NEW_SPECS_SHA256 == EXPECTED_SPECS_SHA256
    for module,_count,size,digest in EXPECTED_FACTORIES:
        raw = support.bounded_bytes(support.MATH_DIRECTORY/(module+'.py'),support.MAX_SOURCE_BYTES)
        assert len(raw) == size and sha256(raw).hexdigest() == digest


def test_production_parent_control_and_catalog_registration_authenticate_actual_bytes(monkeypatch,_authority_module_baseline):
    _forbid_authority_access(monkeypatch)
    expected_paths = tuple(str(path.relative_to(support.ROOT)) for path in support.parent_control_paths())
    assert expected_paths and len(expected_paths) == len(set(expected_paths))
    assert tuple(pin.path for pin in support.PARENT_CONTROL_PINS) == expected_paths
    assert tuple((pin.path,pin.bytes,pin.sha256) for pin in support.PARENT_CATALOG_PINS) == (
        ('artifacts/peano-library/alpha/catalog-v31.json',293294,
         '6c9ebfb3c37e42aefab200b710f78e7693dc5826c80f053544deea41caf44aab'),
        ('artifacts/peano-library/alpha/catalog-v30.json',66503303,
         'ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7'),
        ('artifacts/peano-library/alpha/catalog-v31-delta.json',27237393,
         'fb334cc28a234c3d5d6d65b417b7a10a2af19a5377f57f4dedb4ca65276f185e'),
    )
    # This runs the real bounded source and physical-component byte checks.
    # It neither expands the logical catalogue nor imports its Alpha runtime.
    support.require_final_source_pins()
    _assert_tracked_modules_unchanged(_authority_module_baseline)


def test_production_actual_ninety_ordered_specs_match_literal_digest(monkeypatch,_authority_module_baseline):
    _forbid_authority_access(monkeypatch)
    state = support.load_candidate_state(final=True)
    assert len(state.rows) == len({item.name for item in state.rows}) == 90
    assert state.sources == support.MATH_SOURCE_PINS
    digest = sha256()
    for item in state.rows:
        assert type(item) is TheoremSpec
        assert type(item.dependencies) is tuple and type(item.script) is tuple and item.script
        record = [item.name,item.statement,list(item.dependencies),list(item.script),item.summary]
        digest.update((json.dumps(record,ensure_ascii=True,separators=(',',':'))+'\n').encode('utf-8'))
    assert digest.hexdigest() == state.specs_sha256 == support.NEW_SPECS_SHA256 == EXPECTED_SPECS_SHA256
    assert set(EXPECTED_PRINCIPALS) <= {item.name for item in state.rows}
    _assert_tracked_modules_unchanged(_authority_module_baseline)


def test_production_actual_complete_artifact_is_registered_not_a_prefix(monkeypatch,_authority_module_baseline):
    _forbid_authority_access(monkeypatch)
    pin = checkpoints.require_final_inventory()
    assert type(pin) is checkpoints.ArtifactPin
    # The independently inspected complete plan is 371 inherited +90 owned;
    # its one packaging node is not a ninety-first mathematical result.
    assert pin.nodes == 371+90+1
    assert type(pin.bytes) is int and 0 < pin.bytes <= support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes
    assert type(pin.edges) is int and pin.edges >= pin.nodes-1
    assert type(pin.body_nodes) is int and pin.body_nodes >= pin.nodes
    assert re.fullmatch(r'[0-9a-f]{64}',pin.sha256)
    assert not Path(pin.path).is_absolute() and '..' not in Path(pin.path).parts
    # require_final_inventory has just authenticated the actual bounded file.
    # Its registration is data identity only; no successful proof is claimed.
    _assert_tracked_modules_unchanged(_authority_module_baseline)


@pytest.mark.parametrize('entrypoint',('inventory','bundle','controller','principal'))
def test_production_missing_artifact_is_rejected_before_any_proof_access(monkeypatch,entrypoint):
    _forbid_authority_access(monkeypatch)
    support.require_final_source_pins()  # Real prerequisite, never an accepting stub.
    assert type(checkpoints.FINAL_ARTIFACT) is checkpoints.ArtifactPin, 'register the actual complete artifact first'
    monkeypatch.setattr(checkpoints,'FINAL_ARTIFACT',None)
    with pytest.raises(support.G009Error,match='no actual complete G009 artifact'):
        if entrypoint == 'inventory':
            checkpoints.require_final_inventory()
        elif entrypoint == 'bundle':
            checkpoints.verify_checkpoint()
        elif entrypoint == 'controller':
            driver.verify_in_fresh_windows()
        else:
            checkpoints.verify_principal_root(EXPECTED_PRINCIPALS[-1])


@pytest.mark.parametrize('module_name',_WATCHED_MODULE_ROOTS)
@pytest.mark.parametrize('initial,mutation',(
    ('absent','unchanged'),('preloaded','unchanged'),('absent','insert'),
    ('absent','insert_none'),('preloaded','remove'),('preloaded','replace'),
    ('preloaded','extra_entry'),
))
def test_authority_module_identity_observation_is_exact(module_name,initial,mutation):
    # Private cache-shaped data only: never insert a fabricated edition into
    # sys.modules, call a proof gate, or supply an accepting authority fixture.
    modules = {'unrelated.cached.module':object()}
    if initial == 'preloaded': modules[module_name] = object()
    before = _tracked_module_identities(modules)
    if mutation == 'insert': modules[module_name] = object()
    elif mutation == 'insert_none': modules[module_name] = None
    elif mutation == 'remove': del modules[module_name]
    elif mutation == 'replace': modules[module_name] = object()
    elif mutation == 'extra_entry': modules[module_name+'.unexpected'] = object()
    if mutation == 'unchanged':
        _assert_tracked_modules_unchanged(before,modules)
    else:
        with pytest.raises(AssertionError,match='authority module'):
            _assert_tracked_modules_unchanged(before,modules)


# Collection itself must not add/remove/replace any watched authority module.
_assert_tracked_modules_unchanged(_PROJECT_IMPORT_MODULES_BEFORE)
