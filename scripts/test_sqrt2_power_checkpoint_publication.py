"""Publication and provenance checks, not substitutes for proof replay."""
import ast
from copy import deepcopy
import gzip
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import pytest

import publish_sqrt2_power_checkpoint as p


def test_frozen_inventory_is_exact_and_honest():
    r=p.load_index()
    assert len(r['rows'])==246 and r['unique_statements']==245
    assert r['library_admissions']==r['IR_parents_closed']==0
    assert {row['case'] for row in r['rows']}>={'AP095','AP094','CV102','SQ010'}
    assert len({row['target_ast_sha256'] for row in r['rows']})==245


def test_modified_index_is_rejected(tmp_path,monkeypatch):
    bad=tmp_path/'index.json';r=json.loads(p.INDEX.read_bytes());r['unique_statements']=999
    bad.write_bytes(p.encode(r));monkeypatch.setattr(p,'INDEX',bad)
    with pytest.raises(ValueError,match='digest'):p.load_index()


@pytest.mark.parametrize('field,value',[('bytes',1),('sha256','0'*64),('path','../outside')])
def test_changed_evidence_pin_fails_before_proof_processing(field,value):
    item=deepcopy(p.load_index()['rows'][-1]['ha']);item[field]=value
    with pytest.raises(ValueError):p.pinned(item)


def test_ap095_conservative_notation_matches_original_target():
    from run_sqrt2_power_wave import target_for
    r=next(r for r in p.load_index()['rows'] if r['case']=='AP095')
    _,ha=p.pinned(r['ha']);target=target_for('AP095')
    source,defs,uses=p.notation('AP095',ha['results']['generation']['diagnostics'],target,p.case_modules())
    assert 'NatSqrt2ExpSample(n+8,' in source and len(defs)==23
    assert len(set(defs))==len(defs) and uses
    seen=set()
    for key,d in defs.items():
        assert set(d['dependencies'])<=seen
        assert len(d['parameters'])==len(set(d['parameters']))
        seen.add(key)


def test_changed_named_formula_rejected():
    from run_sqrt2_power_wave import target_for
    with pytest.raises(ValueError,match='Named statement differs'):
        p.notation('AP095',{'source':'0=0'},target_for('AP095'),p.case_modules())


def test_cached_archive_reader_preserves_existing_exact_bindings():
    from check_sqrt2_power_fresh_lean import exact_bundle
    row=next(r for r in p.load_index()['rows'] if r['case']=='AP095')
    folder=(p.ROOT/row['ha']['path']).parent
    actual=p.authenticated_bundle(folder)
    assert actual==exact_bundle(folder)
    assert p.authenticated_bundle(folder)==actual
    assert len(p._VERIFIED_SNAPSHOTS)<=4096


def test_warm_snapshot_cache_cannot_mask_changed_archived_bytes(tmp_path):
    row=next(r for r in p.load_index()['rows'] if r['case']=='RF001')
    folder=(p.ROOT/row['ha']['path']).parent
    p.authenticated_bundle(folder)
    report=json.loads((folder/'report.json').read_bytes())
    for name in ('report.json',*(r['path'] for r in report['process_records'].values())):
        (tmp_path/name).write_bytes((folder/name).read_bytes())
    source=next(iter(report['source_pins']))
    archived=report['source_snapshots'][source]
    destination=tmp_path/archived;destination.parent.mkdir(parents=True)
    data=gzip.decompress((folder/archived).read_bytes())
    destination.write_bytes(gzip.compress(bytes([data[0]^1])+data[1:],mtime=0))
    with pytest.raises(ValueError,match='Changed archived source'):
        p.authenticated_bundle(tmp_path)


def test_registered_legacy_rows_keep_exact_stdout_root_binding():
    legacy=set()
    for row in p.load_index()['rows']:
        _,report=p.pinned(row['lean'])
        check=next(c for c in report['checks'] if c['case']==row['case'] and c['report_sha256']==row['ha']['sha256'])
        if 'root' not in check:
            legacy.add(row['case'])
            assert '\troot=' in check['process']['stdout']
    assert legacy==p.LEGACY_LEAN_ROWS


def test_shell_preserves_canonical_visual_anchors_and_honest_status():
    html=p.shell('Example','<section class="release-note">Body</section>').decode()
    for token in ('family-page sqrt2-power-page','family-hero','shell family-main','/proofs/assets/proofs.css',
                  'IR072/G121','remains open','Alpha v35','4,318','Research, not Alpha admission'):
        assert token in html
    assert 'Build in Lean' not in html
    assert (p.ROOT/'_deploy/proofs-v35/assets/proofs.css').is_file()


def test_notation_graph_never_invents_proof_dependencies():
    rows=[dict(case='AP095',target_ast_sha256='x',title='Test',coverage='test',statement='Test(x)',uses_definitions=['ND0001'])]
    defs={'ND0001':dict(id='ND0001',name='Test',parameters=['x'],dependencies=[])}
    graph,html=p.notation_graph(rows,defs)
    assert graph['proof_edge_count']==0
    assert graph['edges']==[dict(source='AP095',target='ND0001',kind='uses_definition',occurrence_count=1,statement_occurrences=1,local_proposition_occurrences=0)]
    assert b'window.PA_DEFINED_GRAPH' in html and b'data-graph-svg' in html
    assert b'/proofs/assets/defined-explorer.js' in html
    assert b'not a proof-dependency map' in html


def test_html_text_is_escaped():
    assert b'&lt;script&gt;' in p.shell('<script>','')


def test_duplicate_e_v_target_not_double_counted():
    rows={r['case']:r for r in p.load_index()['rows']}
    assert rows['P08-eprover']['target_ast_sha256']==rows['P08-vampire']['target_ast_sha256']


def test_build_cannot_overwrite_existing_tree(tmp_path):
    with pytest.raises(ValueError,match='New output'):p.build(tmp_path)


def test_source_contains_no_proof_generation_or_admission_calls():
    tree=ast.parse(Path(p.__file__).read_bytes())
    calls={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
    assert not calls & {'prove_requested_half_transport','check_proof_bundle','replay','eval','exec'}


def test_activation_scope_is_additive_and_pinned():
    import activate_sqrt2_power_checkpoint as a
    assert a.RELEASE==p.RELEASE
    assert a.NAMESPACES==[p.NAMESPACE,str(Path(p.RELEASE).parent)]
    assert len(a.ENTRANCES)==3 and a.PARENTS[-1]['sha256']==p.OLD_SHA


def test_new_public_parents_work_under_private_umask(tmp_path,monkeypatch):
    import os
    import stat
    import activate_sqrt2_power_checkpoint as a
    monkeypatch.setattr(a,'PUBLIC',tmp_path)
    old_mode=stat.S_IMODE(tmp_path.stat().st_mode)
    previous=os.umask(0o077)
    try:a.make_public_parents(tmp_path/'sqrt2-power'/'checkpoints')
    finally:os.umask(previous)
    assert stat.S_IMODE((tmp_path/'sqrt2-power').stat().st_mode)==0o755
    assert stat.S_IMODE((tmp_path/'sqrt2-power/checkpoints').stat().st_mode)==0o755
    assert stat.S_IMODE(tmp_path.stat().st_mode)==old_mode
    with pytest.raises(ValueError):a.make_public_parents(tmp_path.parent/'outside')


def test_pending_navigation_is_readable_but_never_overwrites(tmp_path):
    import os
    import stat
    import activate_sqrt2_power_checkpoint as a
    path=tmp_path/'index.pending'
    previous=os.umask(0o077)
    try:a.write_public_pending(path,b'authenticated navigation')
    finally:os.umask(previous)
    assert path.read_bytes()==b'authenticated navigation'
    assert stat.S_IMODE(path.stat().st_mode)==0o644
    with pytest.raises(FileExistsError):a.write_public_pending(path,b'changed')
    assert path.read_bytes()==b'authenticated navigation'


def test_sealed_old_manifest_is_unchanged():
    import stage_sqrt2_power_checkpoint as s
    assert sha256((s.OLD/p.OLD_RELEASE).read_bytes()).hexdigest()==p.OLD_SHA


def test_staged_current_entrances_link_the_current_inventory(tmp_path):
    import stage_sqrt2_power_checkpoint as s
    staged=tmp_path/'payload'
    s.stage(p.OUTPUT,staged)
    hub=(staged/'index.html').read_text()
    assert '245 distinct HA/Lean' in hub
    assert p.RELEASE in hub and p.OLD_RELEASE not in hub
    assert p.NAMESPACE+'/definition-map.html' in hub
    assert p.NAMESPACE+'/definitions.html' in hub
    manifest=json.loads((staged/p.RELEASE).read_bytes())
    assert set(manifest['replaced_navigation'])==set(s.ENTRANCES)
    assert manifest['new_library_admissions']==0


@pytest.mark.parametrize('focus_kind',['theorem','definition'])
def test_actual_shared_graph_javascript_with_getter_only_svg(focus_kind):
    """Unit-test a synthetic DOM, not a connected-browser visual test."""
    path=p.OUTPUT/'api/corpus.json'
    if not path.is_file():pytest.skip('Complete snapshot is generated in the integration pass')
    corpus=json.loads(path.read_bytes())
    graph,_=p.notation_graph(corpus['rows'],{d['id']:d for d in corpus['definitions']})
    source=ast.parse((p.ROOT/'peano-lab/py/tests/test_constructive_next_layer_explorer.py').read_bytes())
    function=next(n for n in source.body if isinstance(n,ast.FunctionDef)
        and n.name=='test_actual_shared_graph_renders_each_checked_family_and_firefox_svg_links')
    strings=[n.value for n in ast.walk(function) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
    driver=next(s for s in strings if s.startswith('\nconst svgAnchors = []'))
    report=next(s for s in strings if s.startswith('\nconst svgHref ='))
    root=next(r for r in corpus['rows'] if r['case']=='AP095')
    focus='AP095' if focus_kind=='theorem' else root['uses_definitions'][0]
    javascript=(p.ROOT/'_deploy/proofs-v35/assets/defined-explorer.js').read_text()
    program='const payload='+json.dumps(graph)+';const selectedTarget="AP095";const selectedFocus='+json.dumps(focus)+';'+driver+javascript+report
    run=subprocess.run(['node','-'],input=program,text=True,capture_output=True,timeout=20,check=True)
    result=json.loads(run.stdout)
    node=next(n for n in graph['nodes'] if n['id']==focus)
    assert result['sidebarHref']==node['href']
    assert result['title']==focus+' · '+node['name']
    assert result['getterOnlySvgHref'] and result['viewportRendered'] and result['svgAnchorCount']>0


@pytest.mark.parametrize('name',['../escape','/absolute','bad//path','bad/../path','a b','a\\b'])
def test_delivery_paths_reject_escapes(tmp_path,name):
    with pytest.raises(ValueError):p.safe_path(tmp_path,name)
