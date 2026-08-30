"""Delivery-only regressions; fixtures are not proof or publication evidence.

Pure tests exercise QR formatting, metadata shapes, byte transport and rejecting
guards only. They never substitute a successful HA/Lean check, bind a synthetic
reader into the production stager, or write the repository's stage. The two
``test_actual_*`` cases require the genuinely registered reader and, separately,
the real staged overlay. They do not skip missing outputs or invent fixtures.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import asdict, replace
from hashlib import sha256
from importlib import import_module
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

import stage_constructive_g009_publication as delivery


def _forbidden(*_args,**_kwargs):
    pytest.fail('this reject-only test must stop before source import, proof access, or writes')


@pytest.fixture(scope='module')
def format_parent():
    # Literal historical QR HTML plus explicitly synthetic card descriptions.
    # render_hub is a pure formatter, not the actual v31 publication builder.
    scripts = str(delivery.ROOT/'scripts')
    if scripts not in sys.path:
        sys.path.insert(0,scripts)
    hub = import_module('build_constructive_completed_lower_hub_v31')
    source = hub.HISTORICAL_HUB.read_bytes()
    assert sha256(source).hexdigest() == '6c4738a077b2cc147ccb4393b1f3c369274b6253553a11f2bfaa5ec9f025be6b'
    families = [{'slug':slug,'title':'Formatting fixture '+slug,'theorem_count':count,
                 'goals':['G009'],'caveat':'Transport fixture, not mathematical evidence.'}
                for slug,count in hub.publication.FAMILY_COUNTS.items()]
    return hub.render_hub(source.decode(),families,delivery.REVISION)


def _manifest_fixture():
    # Bounded file-INVENTORY syntax only: no physical reader or usable proof.
    files = {
        'index.html','checkpoints.json','proof-audit.json','checkpoints/not-proof-fixture.json',
        *(delivery.SLUG+'/'+name for name in ('index.html','checkpoint.html','api/corpus.json',
            'api/checkpoint.json','api/graph.json','explorer/index.html','explorer/defined/index.html',
            'explorer/defined/graph.html','explorer/defined/api/graph.json')),
        *('grand-campaign/'+name for name in delivery.ATLAS_FILES),*delivery.ASSETS,
        *('sources/'+name for name in (*delivery.MATH_FILES,delivery.RFC)),
        *(delivery.SLUG+'/explorer/'+prefix+'tag/MX'+format(index,'04X')+'.html'
          for prefix in ('','defined/') for index in range(1,91)),
        delivery.SLUG+'/explorer/defined/definition/ND0326.html',
        delivery.SLUG+'/explorer/defined/definition/PD0001.html',
    }
    pins = {name:{'bytes':1,'sha256':delivery.ASSETS.get(name,sha256(b'x').hexdigest())} for name in files}
    return {'schema':delivery.READER_SCHEMA+'-manifest','publication_scope':'local-only-checkpoint',
            'checkpoint_digest':'a'*64,'navigation_revision':delivery.REVISION,
            'file_count_excluding_manifest':len(pins),'files':pins}


def _canonical(value):
    return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()


def _inline(raw=b'non-authority transport fixture',origin='research_g009'):
    return delivery.File(delivery.Pin(len(raw),sha256(raw).hexdigest()),origin,content=raw)


def _merge_fixture():
    # Pure path/pin algebra, never passed into source_inventory() or stage().
    parent = {name:_inline(origin='alpha_v31') for name in delivery.OVERRIDES}
    for name,digest in delivery.ASSETS.items():
        parent[name] = delivery.File(delivery.Pin(1,digest),'alpha_v31')
    parent['old-family/index.html'] = _inline(origin='alpha_v31')
    overlay = {name:_inline(b'new non-authority fixture') for name in delivery.OVERRIDES}
    for name in delivery.ASSETS:
        overlay[name] = replace(parent[name],origin='research_g009')
    overlay[delivery.SLUG+'/index.html'] = _inline()
    return parent,overlay


@pytest.fixture()
def private_stage(tmp_path,monkeypatch):
    # A private temp workspace for low-level file operations, not a fake live
    # reader or acceptance fixture. The production stage entrypoint is unused.
    root = tmp_path/'workspace'
    stage = root/'_deploy/proofs'
    stage.mkdir(parents=True)
    monkeypatch.setattr(delivery,'ROOT',root)
    monkeypatch.setattr(delivery,'STAGE',stage)
    return stage


def test_delivery_constants_preserve_alpha_stable_and_original_limits():
    assert delivery.CPU_LIMITS == (170,175) and delivery.WALL_SECONDS == 180
    assert delivery.MAX_RSS_BYTES == 1536*1024*1024
    assert len(delivery.ASSETS) == 5 and len(delivery.MATH_FILES) == 9
    assert len(delivery.PRINCIPALS) == len(set(delivery.PRINCIPALS)) == 6
    assert delivery.CATALOG_SHA256 == '6c9ebfb3c37e42aefab200b710f78e7693dc5826c80f053544deea41caf44aab'
    assert delivery.REVISION == delivery.CATALOG_SHA256[:12]
    assert delivery.OVERRIDES == {'index.html',*(f'grand-campaign/{name}' for name in (
        'index.html','campaign.json','definitions.json','dag-audit.json'))}
    assert delivery.RELOCATIONS == {name:'release-g009/'+name for name in (
        'manifest.json','checkpoints.json','proof-audit.json')}


@pytest.mark.parametrize('operation',('require','inventory','stage','check'))
def test_missing_real_registration_rejects_before_all_io_or_import(monkeypatch,operation):
    monkeypatch.setattr(delivery,'REGISTRATION',None)
    for name in ('_legacy','_pinned','_atomic_write','_stage_root'):
        monkeypatch.setattr(delivery,name,_forbidden)
    with pytest.raises(delivery.DeliveryError,match='not registered'):
        if operation == 'require': delivery.require_registration()
        elif operation == 'inventory': delivery.source_inventory()
        else: delivery.stage(check=operation == 'check')


@pytest.mark.parametrize('wrong',(None,{},True,(), 'stored successful receipt'))
def test_foreign_or_receipt_shaped_registration_is_not_a_literal_pin(monkeypatch,wrong):
    monkeypatch.setattr(delivery,'REGISTRATION',wrong)
    monkeypatch.setattr(delivery,'_pinned',_forbidden)
    with pytest.raises(delivery.DeliveryError):
        delivery.require_registration()


@pytest.mark.parametrize('bad',(
    delivery.Pin(True,'0'*64),delivery.Pin(0,'0'*64),delivery.Pin(-1,'0'*64),
    delivery.Pin(delivery.MAX_FILE_BYTES+1,'0'*64),delivery.Pin(1,'A'*64),
    delivery.Pin(1,'0'*63),delivery.Pin(1,'x'*64),delivery.Pin(1,None),
))
def test_bad_file_pins_fail_before_read(bad,monkeypatch):
    monkeypatch.setattr(delivery,'_read',_forbidden)
    with pytest.raises(delivery.DeliveryError):
        delivery._pinned(Path('/not-read'),bad,base=Path('/'))


@pytest.mark.parametrize('field,maximum',(
    ('reader_manifest',delivery.MAX_MANIFEST_BYTES),('parent_hub',delivery.MAX_HUB_BYTES),
    ('parent_lock',delivery.MAX_MANIFEST_BYTES),
))
def test_each_registration_document_keeps_its_own_bound(monkeypatch,field,maximum):
    pin = delivery.Pin(1,'0'*64)
    value = delivery.Registration(pin,pin,pin)
    monkeypatch.setattr(delivery,'REGISTRATION',replace(value,**{field:delivery.Pin(maximum+1,'0'*64)}))
    with pytest.raises(delivery.DeliveryError):
        delivery.require_registration()


def test_qr_hub_has_exact64_routes_and_all63_old_cards_are_literal(format_parent):
    result = delivery.render_public_hub(format_parent)
    old = delivery._family_links(delivery._HTML(format_parent))
    new = delivery._family_links(delivery._HTML(result))
    assert len(old) == 63 and len(new) == 64 and len(set(new)) == 64
    assert tuple(name for name in new if name != delivery.SLUG) == old
    cards = re.findall(rb'<article class="family-card\b.*?</article>',format_parent,re.S)
    assert len(cards) == 63 and all(result.count(card) == 1 for card in cards)
    for anchor in (b'class="hero"',b'class="family-grid',b'class="family-card qr-card"',
                   b'class="family-card bertrand-card"',b'assets/proofs.css?v=6c9ebfb3c37e'):
        assert anchor in result
    assert result.count(b'<style') == format_parent.count(b'<style') == 0
    assert result.count(b'<script') == format_parent.count(b'<script') == 0
    assert format_parent != result and b'data-public-research="G009"' not in format_parent


def test_hub_proof_scope_membership_and_historical_navigation_are_not_conflated(format_parent):
    text = delivery.render_public_hub(format_parent).decode()
    assert '90 independently proved research theorems; not Alpha/Stable' in text
    assert 'Alpha v31 remains 3,796 checked-use entries' in text
    assert 'unchanged 432-theorem edition' in text
    assert 'G091 remain open' in text
    assert 'six principal theorems' in text and '371 inherited Alpha-v31' in text
    assert 'F(1)=+1' in text and 'Zeroth values and table encodings remain unrestricted' in text
    assert 'Full G009 still needs multiplicative closure' not in text
    assert 'data-alpha-admitted="false"' in text and 'data-stable-admitted="false"' in text
    assert 'proof-publication-scope" content="alpha-v31-and-non-admitted-research"' in text
    assert '383 reviewed conservative definitions with 825 actual expansion arrows' in text
    assert 'checkpoints/?v=ac7111ec14ff' in text and 'checkpoints/lower-tier/?v=ac7111ec14ff' in text
    assert 'release-v31/manifest.json' in text and 'release-v31/alpha-v31-completed-lower-receipt-v1.json' in text
    assert 'release-g009/delivery.json' in text and 'release-g009/proof-audit.json' in text
    assert 'explorer/defined/tag/MX0059.html?v=6c9ebfb3c37e' in text
    assert 'Alpha v32' not in text and '3,886 checked-use' not in text


@pytest.mark.parametrize('before,after',(
    (b'quadratic-reciprocity/?v=',b'multiplicative-convolution/?v='),
    (b'bertrand-postulate/?v=',b'quadratic-reciprocity/?v='),
    (b'Full G009 still needs multiplicative closure;',b'Full G009 was already admitted;'),
    (b'The current library contains 63 proof families.',b'The current library contains 64 proof families.'),
    (b'aria-labelledby="grand-campaign-heading"',b'aria-labelledby="other-heading"'),
    (b'content="alpha-v31-checked-use"',b'content="synthetic-admission"'),
))
def test_foreign_or_already_extended_hub_is_rejected(format_parent,before,after):
    with pytest.raises(delivery.DeliveryError):
        delivery.render_public_hub(format_parent.replace(before,after,1))


def test_manifest_shape_requires_all90_hex_tags_and_all_delivery_components():
    fixture = _manifest_fixture()
    pins = delivery._manifest(_canonical(fixture))
    for index in range(1,91):
        for branch in ('','defined/'):
            assert delivery.SLUG+f'/explorer/{branch}tag/MX{index:04X}.html' in pins
    assert delivery.SLUG+'/explorer/tag/MX005A.html' in pins
    assert delivery.SLUG+'/explorer/tag/MX0090.html' not in pins
    assert {name for name in pins if name.startswith('assets/')} == set(delivery.ASSETS)
    assert len([name for name in pins if name.startswith('sources/')]) == 10


@pytest.mark.parametrize('attack',(
    'schema','scope','revision','count_bool','count_wrong','digest','missing_corpus','missing_tag',
    'decimal_tag','extra_theorem','missing_source','extra_source','missing_rfc','missing_bundle',
    'second_bundle','missing_atlas','extra_atlas','missing_asset','extra_asset','changed_asset',
    'manifest_self','unsafe_path','unknown_root','nested_definition','wrong_definition_id',
))
def test_incomplete_foreign_or_extra_manifest_is_rejected(attack):
    value = _manifest_fixture()
    pins = value['files']
    arbitrary = {'bytes':1,'sha256':'b'*64}
    if attack == 'schema': value['schema'] = 'admitted-alpha'
    elif attack == 'scope': value['publication_scope'] = 'alpha_checked_use_publication'
    elif attack == 'revision': value['navigation_revision'] = 'ac7111ec14ff'
    elif attack == 'count_bool': value['file_count_excluding_manifest'] = True
    elif attack == 'count_wrong': value['file_count_excluding_manifest'] += 1
    elif attack == 'digest': value['checkpoint_digest'] = 'not-a-digest'
    elif attack == 'missing_corpus': del pins[delivery.SLUG+'/api/corpus.json']
    elif attack == 'missing_tag': del pins[delivery.SLUG+'/explorer/defined/tag/MX0059.html']
    elif attack == 'decimal_tag': pins[delivery.SLUG+'/explorer/tag/MX0090.html'] = pins.pop(delivery.SLUG+'/explorer/tag/MX005A.html')
    elif attack == 'extra_theorem': pins[delivery.SLUG+'/explorer/tag/MX005B.html'] = arbitrary
    elif attack == 'missing_source': del pins['sources/'+delivery.MATH_FILES[0]]
    elif attack == 'extra_source': pins['sources/old-alpha-source.py'] = arbitrary
    elif attack == 'missing_rfc': del pins['sources/'+delivery.RFC]
    elif attack == 'missing_bundle': del pins['checkpoints/not-proof-fixture.json']
    elif attack == 'second_bundle': pins['checkpoints/another-fixture.json'] = arbitrary
    elif attack == 'missing_atlas': del pins['grand-campaign/dag-audit.json']
    elif attack == 'extra_atlas': pins['grand-campaign/extra.json'] = arbitrary
    elif attack == 'missing_asset': del pins['assets/proofs.css']
    elif attack == 'extra_asset': pins['assets/lean-selector.js'] = arbitrary
    elif attack == 'changed_asset': pins['assets/proofs.css'] = arbitrary
    elif attack == 'manifest_self': pins['manifest.json'] = arbitrary
    elif attack == 'unsafe_path': pins['../outside.html'] = arbitrary
    elif attack == 'unknown_root': pins['standalone-proof.html'] = arbitrary
    elif attack == 'nested_definition': pins[delivery.SLUG+'/explorer/defined/definition/extra/ND0326.html'] = arbitrary
    elif attack == 'wrong_definition_id': pins[delivery.SLUG+'/explorer/defined/definition/AXIOM.html'] = arbitrary
    if attack not in ('count_bool','count_wrong'):
        value['file_count_excluding_manifest'] = len(pins)
    with pytest.raises(delivery.DeliveryError):
        delivery._manifest(_canonical(value))


@pytest.mark.parametrize('raw',(b'',b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":Infinity}',b'\xff',b'{'))
def test_bounded_json_is_strict_and_rejects_duplicate_or_nonfinite_values(raw):
    with pytest.raises(delivery.DeliveryError):
        delivery._parse(raw)


def test_noncanonical_manifest_and_oversized_metadata_are_rejected():
    fixture = _manifest_fixture()
    with pytest.raises(delivery.DeliveryError):
        delivery._manifest(json.dumps(fixture).encode())
    with pytest.raises(delivery.DeliveryError):
        delivery._parse(b'x'*33,32)


@pytest.mark.parametrize('name',('',None,True,'/outside','../outside','x/../outside','x//file',
                                 'x/./file','x\\file','x\x00file','x?query','x#fragment',
                                 'x/%2e%2e/file','x space/file','https:outside'))
def test_unsafe_file_names_are_not_delivery_destinations(name):
    assert not delivery._safe_name(name)


@pytest.mark.parametrize('key',delivery.NO_ADMISSION)
def test_each_research_admission_flag_must_be_false(key):
    value = {**{name:False for name in delivery.NO_ADMISSION},
             **{name:True for name in ('local_checkpoint_verified','original_ha_bundle_verified','independent_lean_bundle_verified')}}
    value[key] = True
    with pytest.raises(delivery.DeliveryError,match='mislabel'):
        delivery._local_flags(value)


@pytest.mark.parametrize('key',delivery.NO_VERSION)
def test_research_cannot_invent_a_first_alpha_version(key):
    value = {**{name:False for name in delivery.NO_ADMISSION},
             **{name:True for name in ('local_checkpoint_verified','original_ha_bundle_verified','independent_lean_bundle_verified')}}
    value[key] = 'v31'
    with pytest.raises(delivery.DeliveryError):
        delivery._local_flags(value)


def test_incomplete_literal_evidence_is_rejected_not_reconstructed():
    # Not a checked reader: failure must happen before any other document.
    files = {'checkpoints.json':_inline(b'{"schema":"saved-success"}')}
    with pytest.raises(delivery.DeliveryError,match='boundary'):
        delivery._research_metadata(files,{},b'{}')


def test_merge_overrides_only_five_paths_and_preserves_parent_object_identity():
    parent,overlay = _merge_fixture()
    merged = delivery._merge(parent,overlay)
    for name in parent:
        assert merged[name] is (overlay[name] if name in delivery.OVERRIDES else parent[name])
    assert merged[delivery.SLUG+'/index.html'] is overlay[delivery.SLUG+'/index.html']
    assert len(merged) == len(parent)+1


@pytest.mark.parametrize('attack',('different_collision','identical_collision','missing_old_atlas',
                                  'missing_new_atlas','missing_old_asset','missing_new_asset','extra_asset','changed_asset'))
def test_collisions_or_missing_shared_components_fail_closed(attack):
    parent,overlay = _merge_fixture()
    if attack == 'different_collision': overlay['old-family/index.html'] = _inline(b'changed')
    elif attack == 'identical_collision': overlay['old-family/index.html'] = parent['old-family/index.html']
    elif attack == 'missing_old_atlas': del parent['grand-campaign/dag-audit.json']
    elif attack == 'missing_new_atlas': del overlay['grand-campaign/dag-audit.json']
    elif attack == 'missing_old_asset': del parent['assets/proofs.css']
    elif attack == 'missing_new_asset': del overlay['assets/proofs.css']
    elif attack == 'extra_asset': overlay['assets/new.css'] = _inline()
    elif attack == 'changed_asset': overlay['assets/proofs.css'] = _inline(b'not the original CSS')
    with pytest.raises(delivery.DeliveryError):
        delivery._merge(parent,overlay)


def test_root_hub_is_last_and_shared_assets_are_not_rewritten():
    _parent,overlay = _merge_fixture()
    overlay[delivery.DELIVERY_RECORD] = _inline()
    order = delivery._write_order(overlay)
    assert order[-1] == 'index.html'
    assert set(order) == set(overlay)-set(delivery.ASSETS)
    assert all(order.index(name) < len(order)-1 for name in delivery.OVERRIDES-{'index.html'})
    assert delivery.DELIVERY_RECORD in order


@pytest.mark.parametrize('mode',('missing','empty','oversized','directory','symlink','ancestor_symlink'))
def test_regular_bounded_reads_reject_unsafe_files_before_use(tmp_path,mode):
    path = tmp_path/'input'
    if mode == 'empty': path.write_bytes(b'')
    elif mode == 'oversized': path.write_bytes(b'x'*33)
    elif mode == 'directory': path.mkdir()
    elif mode == 'symlink':
        other = tmp_path/'other'; other.write_bytes(b'x'); path.symlink_to(other)
    elif mode == 'ancestor_symlink':
        other = tmp_path/'other'; other.mkdir(); (other/'value').write_bytes(b'x')
        path.symlink_to(other,target_is_directory=True); path /= 'value'
    with pytest.raises((delivery.DeliveryError,OSError)):
        delivery._read(path,32,base=tmp_path)


def test_exact_pinned_read_uses_no_follow_and_detects_changed_bytes(tmp_path,monkeypatch):
    path = tmp_path/'file'; path.write_bytes(b'exact fixture')
    expected = delivery.Pin(13,sha256(b'exact fixture').hexdigest())
    observed = []
    old_open = os.open
    def watch(name,flags,*args,**kwargs):
        observed.append(flags)
        return old_open(name,flags,*args,**kwargs)
    monkeypatch.setattr(delivery.os,'open',watch)
    assert delivery._pinned(path,expected,base=tmp_path) == b'exact fixture'
    required = os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK
    assert observed and all(flags&required == required for flags in observed)
    path.write_bytes(b'other fixture')
    with pytest.raises(delivery.DeliveryError):
        delivery._pinned(path,expected,base=tmp_path)


def test_same_bytes_inode_replacement_during_read_is_rejected(tmp_path,monkeypatch):
    path = tmp_path/'file'; path.write_bytes(b'x')
    next_file = tmp_path/'replacement'; next_file.write_bytes(b'x')
    old_open = os.open
    def exchange(name,flags,*args,**kwargs):
        descriptor = old_open(name,flags,*args,**kwargs)
        os.replace(next_file,path)
        return descriptor
    monkeypatch.setattr(delivery.os,'open',exchange)
    # Replacing a linked name may update the retained inode's ctime, causing
    # the even earlier open-identity guard to reject on this filesystem.
    with pytest.raises(delivery.DeliveryError,match='changed (between inspection and open|inode or bytes)'):
        delivery._read(path,1,base=tmp_path)


@pytest.mark.parametrize('kind',('symlink','fifo','same_bytes_new_inode'))
def test_leaf_swap_between_lstat_and_open_cannot_follow_or_block(tmp_path,monkeypatch,kind):
    path = tmp_path/'file'; path.write_bytes(b'x')
    other = tmp_path/'other'; other.write_bytes(b'x')
    original = tmp_path/'original'
    old_open = os.open
    def swap(name,flags,*args,**kwargs):
        required = os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK
        assert flags&required == required  # Do not risk blocking even if a regression occurs.
        path.rename(original)
        if kind == 'symlink': path.symlink_to(other)
        elif kind == 'fifo': os.mkfifo(path)
        else: other.rename(path)
        return old_open(name,flags,*args,**kwargs)
    monkeypatch.setattr(delivery.os,'open',swap)
    with pytest.raises(delivery.DeliveryError):
        delivery._read(path,1,base=tmp_path)


@pytest.mark.parametrize('above_base',(False,True))
def test_changed_ancestor_is_detected_even_when_leaf_is_same_inode(tmp_path,monkeypatch,above_base):
    parent = tmp_path/'parent'; alternate = tmp_path/'alternate'
    base = parent/'reader' if above_base else parent
    other_base = alternate/'reader' if above_base else alternate
    base.mkdir(parents=True); other_base.mkdir(parents=True)
    path = base/'file'; path.write_bytes(b'x')
    os.link(path,other_base/'file')  # Establish identical leaf identity before inspection.
    old_open = os.open
    def swap(name,flags,*args,**kwargs):
        descriptor = old_open(name,flags,*args,**kwargs)
        parent.rename(tmp_path/'retained-parent')
        alternate.rename(parent)
        return descriptor
    monkeypatch.setattr(delivery.os,'open',swap)
    with pytest.raises(delivery.DeliveryError,match='ancestor changed'):
        delivery._read(path,1,base=base)


def test_ancestor_above_base_cannot_be_a_symlink(tmp_path):
    actual = tmp_path/'actual'; (actual/'reader').mkdir(parents=True)
    (actual/'reader/value').write_bytes(b'x')
    linked = tmp_path/'linked'; linked.symlink_to(actual,target_is_directory=True)
    with pytest.raises(delivery.DeliveryError,match='ancestor'):
        delivery._read(linked/'reader/value',1,base=linked/'reader')


def test_unrelated_directory_entry_changes_do_not_break_exact_reads(tmp_path,monkeypatch):
    path = tmp_path/'file'; path.write_bytes(b'x')
    old_open = os.open
    def sibling(name,flags,*args,**kwargs):
        descriptor = old_open(name,flags,*args,**kwargs)
        (tmp_path/'unrelated').write_bytes(b'unrelated fixture')
        return descriptor
    monkeypatch.setattr(delivery.os,'open',sibling)
    assert delivery._read(path,1,base=tmp_path) == b'x'


@pytest.mark.parametrize('payload',(b'',b'xx'))
def test_read_must_equal_observed_size_not_merely_fit_outer_limit(tmp_path,monkeypatch,payload):
    path = tmp_path/'file'; path.write_bytes(b'x')
    old_fdopen = os.fdopen
    class Stream:
        def __init__(self,stream): self.stream = stream
        def __enter__(self): self.stream.__enter__(); return self
        def __exit__(self,*args): return self.stream.__exit__(*args)
        def fileno(self): return self.stream.fileno()
        def read(self,limit):
            assert limit == 2
            return payload
    monkeypatch.setattr(delivery.os,'fdopen',lambda *args,**kwargs:Stream(old_fdopen(*args,**kwargs)))
    with pytest.raises(delivery.DeliveryError,match='exact observed byte bound'):
        delivery._read(path,32,base=tmp_path)


@pytest.mark.parametrize('maximum',(None,True,0,-1,delivery.MAX_FILE_BYTES+1))
def test_read_limit_type_and_ceiling_are_unchanged(tmp_path,monkeypatch,maximum):
    monkeypatch.setattr(delivery.os,'open',_forbidden)
    with pytest.raises(delivery.DeliveryError,match='bounded-file limit'):
        delivery._read(tmp_path/'never-read',maximum,base=tmp_path)


def test_foreign_owned_stage_files_are_rejected(tmp_path,monkeypatch):
    path = tmp_path/'file'; path.write_bytes(b'x')
    original_uid = os.getuid()
    monkeypatch.setattr(delivery.os,'getuid',lambda:original_uid+1)
    with pytest.raises(delivery.DeliveryError,match='owned'):
        delivery._read(path,1,base=tmp_path,owned=True)


@pytest.mark.parametrize('kind',('foreign','parent','symlink','directory_file'))
def test_stage_cannot_widen_or_follow_an_unsafe_destination(private_stage,tmp_path,kind):
    if kind == 'foreign':
        with pytest.raises(delivery.DeliveryError): delivery._destination(tmp_path,'file',create=True)
    elif kind == 'parent':
        with pytest.raises(delivery.DeliveryError): delivery._destination(private_stage,'../outside',create=True)
    elif kind == 'symlink':
        outside = tmp_path/'outside'; outside.mkdir()
        (private_stage/'sources').symlink_to(outside,target_is_directory=True)
        with pytest.raises(delivery.DeliveryError): delivery._preflight_destination(private_stage,'sources/file')
        assert not list(outside.iterdir())
    else:
        (private_stage/'sources').write_bytes(b'user fixture')
        with pytest.raises(delivery.DeliveryError): delivery._preflight_destination(private_stage,'sources/file')


def test_preflight_does_not_create_missing_directories(private_stage):
    delivery._preflight_destination(private_stage,'new/child/value.txt')
    assert not (private_stage/'new').exists()


def test_low_level_atomic_copy_preserves_source_and_cleans_only_its_temporary(private_stage,tmp_path):
    source = tmp_path/'source'; source.write_bytes(b'literal source fixture')
    item = delivery.File(delivery.Pin(source.stat().st_size,sha256(source.read_bytes()).hexdigest()),
                         'research_g009',source=source,base=tmp_path)
    delivery._atomic_write(private_stage,'family/value.txt',item)
    assert (private_stage/'family/value.txt').read_bytes() == source.read_bytes() == b'literal source fixture'
    assert not list(private_stage.rglob('.g009-delivery-*'))
    assert not (delivery.ROOT/'deploy/proofs/index.html').exists()


def test_atomic_replace_failure_does_not_remove_an_existing_user_file(private_stage,monkeypatch):
    target = private_stage/'value'; target.write_bytes(b'preserve me')
    def refuse(*_args,**_kwargs):
        raise PermissionError('test-only denied replacement')
    monkeypatch.setattr(delivery.os,'replace',refuse)
    with pytest.raises(PermissionError):
        delivery._atomic_write(private_stage,'value',_inline(b'new fixture'))
    assert target.read_bytes() == b'preserve me'
    assert not list(private_stage.glob('.g009-delivery-*'))


def _selector_fixture():
    # The real unchanged formatter, not a fabricated acceptance receipt.
    scripts = str(delivery.ROOT/'scripts')
    if scripts not in sys.path: sys.path.insert(0,scripts)
    module = import_module('stage_public_lean_selector')
    return module._overlay(module._api_url(''))


def test_only_original_selector_at_original_head_position_can_be_ignored():
    source = b'<html><head><title>fixture</title></head><body>exact</body></html>'
    pin = delivery.Pin(len(source),sha256(source).hexdigest())
    selector = _selector_fixture()
    changed = source.replace(b'</head>',selector+b'</head>')
    assert delivery._normalized_public_bytes(source,pin,selector=selector) == source
    assert delivery._normalized_public_bytes(changed,pin,selector=selector) == source
    with pytest.raises(delivery.DeliveryError):
        delivery._normalized_public_bytes(changed,pin,selector=None)


@pytest.mark.parametrize('attack',('duplicate','body','before_title','wrong_config','changed_math','extra_space'))
def test_selector_or_math_mutations_are_not_normalized_away(attack):
    source = b'<html><head><title>fixture</title></head><body>exact</body></html>'
    pin = delivery.Pin(len(source),sha256(source).hexdigest())
    selector = _selector_fixture()
    raw = source.replace(b'</head>',selector+b'</head>')
    if attack == 'duplicate': raw = raw.replace(selector,selector+selector)
    elif attack == 'body': raw = source.replace(b'</body>',selector+b'</body>')
    elif attack == 'before_title': raw = source.replace(b'<title>',selector+b'<title>')
    elif attack == 'wrong_config': raw = raw.replace(b'<script defer ',b'<script async ')
    elif attack == 'changed_math': raw = raw.replace(b'>exact<',b'>forged<')
    elif attack == 'extra_space': raw += b' '
    with pytest.raises(delivery.DeliveryError):
        delivery._normalized_public_bytes(raw,pin,selector=selector)


@pytest.mark.parametrize('page,link,expected',(
    ('index.html','multiplicative-convolution/?v=6c9ebfb3c37e',('multiplicative-convolution/index.html','')),
    ('multiplicative-convolution/checkpoint.html','../checkpoints/proof.json',('checkpoints/proof.json','')),
    ('multiplicative-convolution/explorer/defined/tag/MX0059.html','../../../../grand-campaign/?view=goal&focus=G009',('grand-campaign/index.html','')),
    ('grand-campaign/index.html','../index.html?v=6c9ebfb3c37e',('index.html','')),
    ('x/index.html','#proof-line-0001',('x/index.html','proof-line-0001')),
    ('x/index.html','./?v=1',('x/index.html','')),
    ('index.html','/proofs/release-g009/manifest.json',('release-g009/manifest.json','')),
    ('index.html','https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/',('index.html','')),
    ('x/index.html','../y/index.html#%CE%BC',('y/index.html','μ')),
))
def test_relative_public_and_fragment_routes_resolve_exactly(page,link,expected):
    assert delivery._link_target(page,link) == expected


@pytest.mark.parametrize('link',('../outside','%2e%2e/outside','x%5cy','javascript:alert(1)',
                                 'data:text/plain,fixture','file:///private/data',None))
def test_escaping_or_nonweb_links_are_rejected(link):
    with pytest.raises(delivery.DeliveryError):
        delivery._link_target('index.html',link)


@pytest.mark.parametrize('link',('https://example.org/paper','mailto:reader@example.org','/peano-lab/'))
def test_other_applications_and_external_sources_are_not_local_delivery_targets(link):
    assert delivery._link_target('index.html',link) is None


def test_static_link_checker_uses_actual_fragments_and_preserves_supplement_targets(tmp_path):
    supplement = tmp_path/'checkpoints/history.html'; supplement.parent.mkdir(); supplement.write_bytes(b'<p id="old">old fixture</p>')
    files = {'index.html':_inline(b'<a href="family/">family</a><a href="checkpoints/history.html#old">history</a>'),
             'family/index.html':_inline(b'<p id="target">fixture</p><a href="../index.html">home</a><a href="#target">self</a>')}
    result = delivery.check_internal_links(files,tmp_path)
    assert result == {'html_files':2,'local_links':4,'local_fragments':2,'existing_supplement_targets':1}
    assert supplement.read_bytes() == b'<p id="old">old fixture</p>'


@pytest.mark.parametrize('attack',('missing_file','missing_id','duplicate_id','base','relocated_record','research_selector'))
def test_bad_internal_routes_or_new_lean_overlay_fail_before_staging(tmp_path,attack):
    body = b'<p id="target">fixture</p>'
    if attack == 'missing_file': body += b'<a href="missing.html">broken</a>'
    elif attack == 'missing_id': body += b'<a href="#absent">broken</a>'
    elif attack == 'duplicate_id': body += b'<span id="target">duplicate</span>'
    elif attack == 'base': body += b'<base href="https://example.org/">'
    elif attack == 'relocated_record': body += b'<a href="proof-audit.json">wrong old location</a>'
    elif attack == 'research_selector': body += _selector_fixture()
    files = {'index.html':_inline(body)}
    with pytest.raises((delivery.DeliveryError,OSError)):
        delivery.check_internal_links(files,tmp_path)


@pytest.mark.parametrize('argument',('--deploy','--remote','--receipt','--skip-verify','--bundle','--seed-only'))
def test_cli_cannot_load_a_receipt_or_expand_into_remote_or_partial_publication(argument):
    with pytest.raises(SystemExit) as error:
        delivery.main([argument])
    assert error.value.code == 2


def test_source_has_no_kernel_or_remote_execution_and_no_ancestor_mutation(_authority_module_baseline):
    source = Path(delivery.__file__).read_text()
    tree = ast.parse(source)
    imports = [node for node in ast.walk(tree) if isinstance(node,(ast.Import,ast.ImportFrom))]
    imported = [node.module for node in imports if isinstance(node,ast.ImportFrom)]
    imported += [entry.name for node in imports if isinstance(node,ast.Import) for entry in node.names]
    assert not any(name and name.startswith(('peano_lab','subprocess','socket','requests','paramiko')) for name in imported)
    assert not any(isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
                   and node.func.attr in {'system','rmtree','rmdir','cache_clear'} for node in ast.walk(tree))
    unlinks = [node for node in ast.walk(tree) if isinstance(node,ast.Call)
               and isinstance(node.func,ast.Attribute) and node.func.attr == 'unlink']
    assert len(unlinks) == 1 and ast.unparse(unlinks[0].func.value) == 'temporary'
    _assert_tracked_modules_unchanged(_authority_module_baseline)


def test_actual_registered_reader_and_parent_delivery_bytes_are_exact(_authority_module_baseline):
    # Deliberately fails if outputs/pins have not genuinely been installed.
    original = delivery.PARENT_HUB.read_bytes()
    plan = delivery.source_inventory()
    assert len(plan.parent) > 11000 and len(plan.merged) > len(plan.parent)
    assert plan.metadata['family_count'] == 64 and plan.metadata['new_research_theorem_count'] == 90
    assert plan.metadata['alpha_checked_use_count'] == 3796 and plan.metadata['stable_count'] == 432
    assert plan.metadata['alpha_admission_performed'] is False and plan.metadata['stable_admission_performed'] is False
    assert set(plan.parent)&set(plan.overlay) == delivery.OVERRIDES|set(delivery.ASSETS)
    for name,item in plan.overlay.items():
        if name not in ('index.html',delivery.DELIVERY_RECORD):
            assert delivery._file_bytes(item) == item.source.read_bytes()
    assert delivery.PARENT_HUB.read_bytes() == original
    _assert_tracked_modules_unchanged(_authority_module_baseline)


def test_actual_staged_overlay_has_all_merged_bytes_links_and_no_research_selector():
    # Read-only; parent owns real staging. There is no fixture fallback.
    result = delivery.stage(check=True,api_url=os.environ.get('PEANO_LEAN_PUBLIC_API',''))
    assert result['check_only'] is True and result['delivery_metadata_only'] is True
    assert result['family_count'] == 64 and result['files'] > 11000
    assert result['local_links'] > 0 and result['local_fragments'] > 0
    assert result['alpha_admission_performed'] is False and result['stable_admission_performed'] is False
    for path in (delivery.STAGE/delivery.SLUG).rglob('*.html'):
        assert delivery.SELECTOR_MARKER not in path.read_bytes()


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
