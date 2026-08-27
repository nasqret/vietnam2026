"""Exact candidate closure, unchanged bounds and no admitting shortcut."""

from dataclasses import replace
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import pytest

from peano_lab.kernel.formulas import And, Bot
from peano_lab.kernel.proofs import AndIntro, EqRefl, Hyp
from peano_lab.kernel.terms import Zero
from peano_lab.library import campaign_priority_layer_closure as closure
from peano_lab.library.campaign_lower_layer_closure import LowerLayerError
from peano_lab.library.proof_bundle import BundleNode, ProofBundle, ProofBundleError, decode_proof_bundle, encode_proof_bundle
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
G010 = ("squarefree_perfect_power",)


def _clear_caches():
    closure._factory_specs.cache_clear()
    closure.priority_layer_specs.cache_clear()
    closure.priority_layer_plan.cache_clear()


def test_exact_v28_parent_and_all_historical_provider_bytes():
    snapshot = closure.parent_snapshot()
    assert len(snapshot.specs) == closure.PARENT_COUNT == 2764
    assert closure._specs_digest(snapshot.specs) == closure.PARENT_SPECS_SHA256
    assert sha256((ROOT/closure.PARENT_CATALOG).read_bytes()).hexdigest() == closure.PARENT_CATALOG_SHA256
    assert len(snapshot.documents) == 18
    assert tuple(d.bytes for d in snapshot.documents) == tuple(sorted(d.bytes for d in snapshot.documents))
    assert closure.validate_parent_provider_bytes() == snapshot.documents


def test_all_registered_candidates_are_explicitly_frozen_source_bytes():
    assert closure.validate_candidate_source_bytes() == closure.FACTORIES
    assert all(len(f.source_sha256)==64 and f.rfc.endswith("-rfc-v1.md") for f in closure.FACTORIES)


@pytest.mark.parametrize("campaign,count,shared",[("squarefree_perfect_power",73,True),("odd_prime_lte",58,True),("euler_totient",104,True),("continued_fraction_approximation",83,False)])
def test_branch_selection_automatically_closes_the_actual_shared_factory_dependencies(campaign,count,shared):
    plan = closure.priority_layer_plan((campaign,))
    assert len(plan.frontier_names) == count
    assert plan.campaigns == (("prime_valuation_support",campaign) if shared else (campaign,))
    seen = set()
    for i,row in enumerate(plan.rows):
        assert row.node_id == i and set(row.dependencies) <= seen
        seen.add(row.name)
    assert set(plan.frontier_names) <= seen
    pending,reachable = list(plan.root_names),set()
    rows = {r.name:r for r in plan.rows}
    while pending:
        name = pending.pop()
        if name not in reachable:
            reachable.add(name)
            pending.extend(rows[name].dependencies)
    assert reachable == seen


def test_exact_g010_dependency_cone_not_a_count_only_or_partial_bundle():
    plan = closure.priority_layer_plan(G010)
    assert len(plan.frontier_names)==73 and len(plan.rows)==285 and len(plan.root_names)==8
    assert plan.dependency_edge_count == 741
    assert plan.ordered_names_sha256 == "cb3742f2e75f1d373c974f0af068128b5e927f99a36b741055af69b9f86ba5b7"
    assert {"prime_valuation_support_exists","squarefree_decomposition_exists_unique",
            "perfect_power_profile_exists","positive_squarefree_kernel_and_power_profile"} <= set(plan.frontier_names)
    assert "positive_squarefree_kernel_and_power_profile" in plan.root_names


def test_combined_first_four_campaigns_follow_requested_order_and_close_all_real_edges():
    plan = closure.priority_layer_plan()
    assert plan.campaigns == ("prime_valuation_support","continued_fraction_approximation",
                             "euler_totient","squarefree_perfect_power","odd_prime_lte")
    assert len(plan.frontier_names)==278 and len(plan.rows)==565 and len(plan.root_names)==29
    assert plan.dependency_edge_count==1661
    assert plan.ordered_names_sha256=="ce8ccc0cbbd5cac4fd5b24187c4c865f43c2a5080fd1cfdc2234ececb26bb47b"
    assert len(set(plan.frontier_names))==278
    assert all(row.campaign is None or row.name in plan.frontier_names for row in plan.rows)


@pytest.mark.parametrize("campaign,rows,roots,edges,digest",[
    ("odd_prime_lte",263,2,772,"b8bf47e11f016b09f1fb14b0c02e4fb7ceb3f8d45558951e2d483334abf0453a"),
    ("euler_totient",351,12,980,"3f819d37cc6e67ad78b42052be5dadb6ba7d1a3a9c59fe5f35ac11948f6aa55f"),
    ("continued_fraction_approximation",216,8,549,"cbccffee03e7b20f69cb6b8bd1ffd9fcb65b0171eea6f58d77f1b28db3487b42"),
])
def test_other_frozen_branches_have_exact_dependency_cones(campaign,rows,roots,edges,digest):
    plan=closure.priority_layer_plan((campaign,))
    assert len(plan.rows)==rows and len(plan.root_names)==roots
    assert plan.dependency_edge_count==edges and plan.ordered_names_sha256==digest


def test_proof_provider_does_not_eagerly_import_editions_or_enroll_anything():
    program = (
        "import sys; from peano_lab.library.campaign_priority_layer_closure import priority_layer_plan; "
        "priority_layer_plan(('squarefree_perfect_power',)); "
        "assert not any(n.startswith('peano_lab.library.editions') for n in sys.modules); "
        "assert not any(n.startswith('peano_lab.library.alpha_enrollment') for n in sys.modules)"
    )
    subprocess.run([sys.executable,"-c",program],cwd=ROOT,env=dict(os.environ,PYTHONPATH=str(ROOT/"peano-lab/py")),check=True,timeout=45)
    assert closure.PRIORITY_LAYER_ARTIFACT_FILENAME=="alpha-v29-priority-layer-proof-bundle-v1.json"
    assert not hasattr(closure,"checked_priority_layer_bundle")


def test_explicit_parent_specs_need_no_catalogue_or_provider_file_read(monkeypatch):
    specs = closure.parent_snapshot().specs
    expected = closure.priority_layer_plan(G010)
    monkeypatch.setattr(closure,"parent_snapshot",lambda:pytest.fail("metadata planning read a parent file"))
    assert closure.priority_layer_plan(G010,parent_specs=specs) == expected


def test_short_browser_import_path_and_supplied_parent_work_without_admitting(monkeypatch):
    module = ModuleType("peano_lab.library._priority_short_path_test")
    module.__file__ = "/lab/peano_lab/library/campaign_priority_layer_closure.py"
    module.__package__ = "peano_lab.library"
    monkeypatch.setitem(sys.modules,module.__name__,module)
    source = (ROOT/"peano-lab/py/peano_lab/library/campaign_priority_layer_closure.py").read_text()
    exec(compile(source,module.__file__,"exec"),module.__dict__)
    assert module.ROOT == Path("/lab")
    assert module.priority_layer_plan(G010,parent_specs=closure.parent_snapshot().specs).frontier_names == closure.priority_layer_plan(G010).frontier_names


@pytest.mark.parametrize("mutation",["count","order","statement","script","summary","name","type"])
def test_supplied_parent_is_exact_and_fail_closed(mutation):
    specs = closure.parent_snapshot().specs
    if mutation == "count":
        changed = specs[:-1]
    elif mutation == "order":
        changed = tuple(reversed(specs))
    elif mutation == "type":
        changed = list(specs)
    else:
        change = {"statement":"0 = 1","script":("intro bad",),"summary":"altered","name":"altered"}[mutation]
        changed = (replace(specs[0],**{mutation:change}),)+specs[1:]
    with pytest.raises(closure.PriorityLayerError):
        closure._parent_specs(changed)


def test_microbatch_limits_are_the_unchanged_existing_policy():
    from peano_lab.library import campaign_lower_layer_closure as previous
    for field in ("MAX_BATCH_ROWS","MAX_BATCH_PROOF_NODES","MAX_BATCH_PROOF_OBJECTS"):
        assert getattr(closure,field) == getattr(previous,field)
    assert closure.DEFAULT_LAYERED_REPLAY_LIMITS is previous.DEFAULT_LAYERED_REPLAY_LIMITS


@pytest.mark.parametrize("selection",[["squarefree_perfect_power"],("unknown",),("odd_prime_lte","odd_prime_lte"),(1,),None])
def test_unknown_ambiguous_or_malformed_selection_rejected(selection):
    with pytest.raises(closure.PriorityLayerError):
        closure.selected_factories(selection)


@pytest.mark.parametrize("batch",[0,-1,17,True,"1",None])
def test_invalid_batch_rejected_before_any_source_read_or_replay(monkeypatch,batch):
    monkeypatch.setattr(closure,"validate_candidate_source_bytes",lambda *_:pytest.fail("invalid batch read sources"))
    with pytest.raises(closure.PriorityLayerError):
        closure.assemble_priority_layer_proof_bundle(batch_size=batch)


@pytest.mark.parametrize("seeds",[["seed.json"],(False,),(None,),"seed.json",("seed.json","./seed.json")])
def test_seed_selection_must_be_explicit_distinct_paths_before_any_replay(monkeypatch,seeds):
    monkeypatch.setattr(closure,"validate_candidate_source_bytes",lambda *_:pytest.fail("invalid seeds read sources"))
    with pytest.raises(closure.PriorityLayerError,match="seed"):
        closure.assemble_priority_layer_proof_bundle(seed_bundles=seeds)


@pytest.fixture
def tiny_inventory(monkeypatch):
    parent = TheoremSpec("base","0 = 0",(),("refl",),"Reflexivity.")
    candidates = [TheoremSpec("left","0 = 0",("base",),("exact base",),"Actual prerequisite."),
                  TheoremSpec("right","forall n. n = n",(),("intro n","refl"),"Universal reflexivity.")]
    _clear_caches()
    monkeypatch.setattr(closure,"parent_snapshot",lambda:closure.ParentSnapshot((parent,),()))
    monkeypatch.setattr(closure,"FACTORIES",(closure.PriorityLayerFactory("tiny","tiny","factory","tiny-rfc-v1.md","0"*64),))
    monkeypatch.setattr(closure,"import_module",lambda *args,**kwargs:SimpleNamespace(factory=lambda spec:tuple(candidates)))
    monkeypatch.setattr(closure,"validate_candidate_source_bytes",lambda *_:closure.FACTORIES)
    yield parent,candidates
    _clear_caches()


def test_every_actual_body_and_maximal_root_reaches_original_kernel(tiny_inventory):
    result = closure.assemble_priority_layer_proof_bundle(report=lambda text:None)
    assert result.receipt.kernel_calls == result.receipt.node_count == 4
    assert result.receipt.dependency_edges == 3 and isinstance(result.target,And)
    assert result.bundle.nodes[-1].dependencies == (1,2)
    assert result.origins == (("base","parent_script",None),("left","new_script",None),("right","new_script",None))


@pytest.mark.parametrize("mutation",["root","target","edge","packaging","body","inventory"])
def test_forged_targets_edges_bodies_or_packaging_cannot_pass(tiny_inventory,mutation):
    result = closure.assemble_priority_layer_proof_bundle(report=lambda text:None)
    nodes = list(result.bundle.nodes)
    if mutation == "root":
        bundle = replace(result.bundle,root=0)
    else:
        if mutation == "target":
            nodes[1] = replace(nodes[1],target=Bot())
        elif mutation == "edge":
            nodes[1] = replace(nodes[1],dependencies=())
        elif mutation == "packaging":
            nodes[-1] = replace(nodes[-1],body=Hyp(0))
        elif mutation == "body":
            nodes[0] = replace(nodes[0],body=Hyp(0))
        else:
            nodes.pop(1)
        bundle = replace(result.bundle,nodes=tuple(nodes))
    with pytest.raises((closure.PriorityLayerError,ProofBundleError)):
        closure.check_priority_layer_proof_bundle(bundle,result.target)


@pytest.mark.parametrize("mutation",["duplicate","missing","forward","duplicate_edge","implicit","empty","classical"])
def test_bad_specifications_cannot_hide_missing_or_untrusted_proofs(tiny_inventory,mutation):
    parent,rows = tiny_inventory
    if mutation == "duplicate":
        rows[0] = replace(rows[0],name=parent.name)
    elif mutation == "missing":
        rows[0] = replace(rows[0],dependencies=("nonexistent",))
    elif mutation == "forward":
        rows[0] = replace(rows[0],dependencies=("right",))
    elif mutation == "duplicate_edge":
        rows[0] = replace(rows[0],dependencies=("base","base"))
    elif mutation == "implicit":
        rows[0] = replace(rows[0],script=("use unverified",))
    elif mutation == "classical":
        rows[0] = replace(rows[0],script=("DNE",))
    else:
        rows[0] = replace(rows[0],script=())
    with pytest.raises(closure.PriorityLayerError):
        closure.priority_layer_plan()


@pytest.mark.parametrize("mutation",["digest","bytes","target","forged_body","none"])
def test_historical_provider_is_reuse_only_not_proof_authority(tiny_inventory,monkeypatch,tmp_path,mutation):
    parent,_ = tiny_inventory
    target = _closed_formula(parent.statement)
    body = closure._reconstruct_body(parent,{parent.name:parent})
    node = BundleNode(0,target,(),body)
    if mutation == "target":
        node = replace(node,target=Bot())
    elif mutation == "forged_body":
        node = replace(node,body=Hyp(0))
    provider = ProofBundle((node,),0)
    payload = encode_proof_bundle(provider,node.target).encode()
    path = tmp_path/"provider.json"
    path.write_bytes(payload)
    document = closure.ParentDocument(path.name,len(payload)+(mutation=="bytes"),"0"*64 if mutation=="digest" else sha256(payload).hexdigest())
    monkeypatch.setattr(closure,"ROOT",tmp_path)
    monkeypatch.setattr(closure,"parent_snapshot",lambda:closure.ParentSnapshot((parent,),(document,)))
    if mutation in {"digest","bytes","forged_body"}:
        with pytest.raises((closure.PriorityLayerError,ProofBundleError)):
            closure.assemble_priority_layer_proof_bundle(report=lambda text:None)
    else:
        result = closure.assemble_priority_layer_proof_bundle(report=lambda text:None)
        assert result.receipt.kernel_calls == 4
        assert result.origins[0][1] == ("parent_script" if mutation=="target" else path.name)


@pytest.mark.parametrize("dependency_ids",[(0,1),(1,0),(0,)])
def test_provider_reuse_matches_every_ordered_prerequisite_target(tiny_inventory,monkeypatch,tmp_path,dependency_ids):
    a = TheoremSpec("first","0 = 0",(),("refl",),"First.")
    b = TheoremSpec("second","1 = 1",(),("refl",),"Second.")
    parent = TheoremSpec("base","2 = 2",(a.name,b.name),("refl",),"Both premises.")
    tiny_inventory[1][0] = replace(tiny_inventory[1][0],statement=parent.statement)
    table = {r.name:r for r in (a,b,parent)}
    nodes = tuple(BundleNode(i,_closed_formula(r.statement),deps,closure._reconstruct_body(r,table)) for i,(r,deps) in enumerate(((a,()),(b,()),(parent,dependency_ids))))
    target,body = closure._packaging_root(tuple(n.target for n in nodes))
    provider = ProofBundle(nodes+(BundleNode(3,target,(0,1,2),body),),3)
    payload = encode_proof_bundle(provider,target).encode()
    path = tmp_path/"provider.json"
    path.write_bytes(payload)
    document = closure.ParentDocument(path.name,len(payload),sha256(payload).hexdigest())
    monkeypatch.setattr(closure,"ROOT",tmp_path)
    monkeypatch.setattr(closure,"parent_snapshot",lambda:closure.ParentSnapshot((a,b,parent),(document,)))
    result = closure.assemble_priority_layer_proof_bundle(report=lambda text:None)
    assert result.receipt.kernel_calls == 6
    assert result.origins[2][1] == (path.name if dependency_ids==(0,1) else "parent_script")


def test_candidate_seed_checks_every_node_then_reuses_exact_bodies_without_rebuilding(tiny_inventory,monkeypatch,tmp_path):
    first=closure.assemble_priority_layer_proof_bundle(report=lambda text:None)
    path=tmp_path/"actual-seed.json"
    path.write_text(encode_proof_bundle(first.bundle,first.target))
    observations=[]
    checker=closure.check_proof_bundle
    def checked(bundle,target):
        result=checker(bundle,target)
        observations.append(result.kernel_calls)
        return result
    monkeypatch.setattr(closure,"check_proof_bundle",checked)
    monkeypatch.setattr(closure,"_reconstruct_body",lambda *_:pytest.fail("an exact checked seed body was unnecessarily rebuilt"))
    second=closure.assemble_priority_layer_proof_bundle(seed_bundles=(path,),report=lambda text:None)
    assert observations==[4,4]
    assert second.bundle==first.bundle and second.receipt==first.receipt
    assert second.origins==tuple((row.name,str(path),row.node_id) for row in closure.priority_layer_plan().rows)


def test_candidate_seed_invalid_unused_node_is_not_ignored(tiny_inventory,tmp_path):
    first=closure.assemble_priority_layer_proof_bundle(report=lambda text:None)
    # The invalid theorem is outside the requested candidate dependency cone,
    # but remains reachable from the seed's own complete packaging root.
    target,body=closure._packaging_root((first.target,Bot()))
    broken=ProofBundle(first.bundle.nodes+(BundleNode(4,Bot(),(),Hyp(0)),
                       BundleNode(5,target,(3,4),body)),5)
    path=tmp_path/"unused-forgery.json"
    path.write_text(encode_proof_bundle(broken,target))
    with pytest.raises(ProofBundleError):
        closure.assemble_priority_layer_proof_bundle(seed_bundles=(path,),report=lambda text:None)


@pytest.mark.parametrize("dependency_ids",[(0,1),(1,0),(0,)])
def test_candidate_seed_reuse_requires_exact_ordered_prerequisite_targets(tiny_inventory,monkeypatch,tmp_path,dependency_ids):
    a=TheoremSpec("first","0 = 0",(),("refl",),"First.")
    b=TheoremSpec("second","1 = 1",(),("refl",),"Second.")
    parent=TheoremSpec("base","2 = 2",(a.name,b.name),("refl",),"Both premises.")
    tiny_inventory[1][0]=replace(tiny_inventory[1][0],statement=parent.statement)
    table={r.name:r for r in (a,b,parent)}
    actual_parent=replace(parent,dependencies=tuple((a,b)[i].name for i in dependency_ids))
    nodes=(BundleNode(0,_closed_formula(a.statement),(),closure._reconstruct_body(a,table)),
           BundleNode(1,_closed_formula(b.statement),(),closure._reconstruct_body(b,table)),
           BundleNode(2,_closed_formula(parent.statement),dependency_ids,closure._reconstruct_body(actual_parent,table)))
    target,body=closure._packaging_root(tuple(n.target for n in nodes))
    seed=ProofBundle(nodes+(BundleNode(3,target,(0,1,2),body),),3)
    path=tmp_path/"ordered-seed.json"
    path.write_text(encode_proof_bundle(seed,target))
    monkeypatch.setattr(closure,"parent_snapshot",lambda:closure.ParentSnapshot((a,b,parent),()))
    result=closure.assemble_priority_layer_proof_bundle(seed_bundles=(path,),report=lambda text:None)
    assert result.receipt.kernel_calls==6
    assert result.origins[2][1]==(str(path) if dependency_ids==(0,1) else "parent_script")


def test_candidate_seed_with_unrelated_valid_target_does_not_change_requested_theorems(tiny_inventory,tmp_path):
    unrelated=TheoremSpec("other","3 = 3",(),("refl",),"Unrelated reflexivity.")
    target=_closed_formula(unrelated.statement)
    seed=ProofBundle((BundleNode(0,target,(),closure._reconstruct_body(unrelated,{"other":unrelated})),),0)
    path=tmp_path/"unrelated-seed.json"
    path.write_text(encode_proof_bundle(seed,target))
    result=closure.assemble_priority_layer_proof_bundle(seed_bundles=(path,),report=lambda text:None)
    assert result.origins==(("base","parent_script",None),("left","new_script",None),("right","new_script",None))


def test_candidate_seed_payload_uses_existing_byte_limit_before_reading(tiny_inventory,monkeypatch,tmp_path):
    path=tmp_path/"oversized.json"
    path.write_text("not a proof")
    original=Path.stat
    def stat(actual,*args,**kwargs):
        if actual==path:
            return SimpleNamespace(st_size=closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes+1)
        return original(actual,*args,**kwargs)
    monkeypatch.setattr(Path,"stat",stat)
    with pytest.raises(closure.PriorityLayerError,match="unchanged bundle byte limit"):
        closure.assemble_priority_layer_proof_bundle(seed_bundles=(path,),report=lambda text:None)


def test_empty_packaging_is_not_a_theorem():
    with pytest.raises(LowerLayerError,match="empty"):
        closure._packaging_root(())


def test_actual_identity_counts_not_occurrence_counts_are_charged_per_microbatch(tiny_inventory,monkeypatch):
    parent,rows = tiny_inventory
    parent = replace(parent,statement="0 = 0 /\\ 0 = 0",script=("split","refl","refl"))
    rows[0] = replace(rows[0],statement=parent.statement)
    monkeypatch.setattr(closure,"parent_snapshot",lambda:closure.ParentSnapshot((parent,),()))
    reconstruct = closure._reconstruct_body
    def shared_body(row,table):
        if row.name == "base":
            proof = EqRefl(Zero())
            return AndIntro(proof,proof)
        return reconstruct(row,table)
    monkeypatch.setattr(closure,"_reconstruct_body",shared_body)
    original = closure._proof_envelope_metrics_bounded
    observations = []
    def record(body,**limits):
        result = original(body,**limits)
        observations.append((limits,result))
        return result
    monkeypatch.setattr(closure,"_proof_envelope_metrics_bounded",record)
    closure.assemble_priority_layer_proof_bundle(batch_size=3,report=lambda text:None)
    nodes = objects = 0
    for limits,result in observations:
        assert limits["max_proof_occurrences"] == closure.MAX_BATCH_PROOF_NODES-nodes
        assert limits["max_proof_objects"] == closure.MAX_BATCH_PROOF_OBJECTS-objects
        nodes += result[0]
        objects += result[1]
    assert any(result[0] != result[1] for limits,result in observations)


def test_unused_provider_byte_mutation_still_fails_closed(tiny_inventory,monkeypatch,tmp_path):
    parent,_ = tiny_inventory
    path = tmp_path/"unused.json"
    path.write_bytes(b"mutated")
    document = closure.ParentDocument(path.name,1,"0"*64)
    monkeypatch.setattr(closure,"ROOT",tmp_path)
    monkeypatch.setattr(closure,"parent_snapshot",lambda:closure.ParentSnapshot((parent,),(document,)))
    with pytest.raises(closure.PriorityLayerError,match="historical proof bytes changed"):
        closure.validate_parent_provider_bytes()


def test_candidate_export_never_overwrites_existing_artifacts(monkeypatch,tmp_path):
    path = tmp_path/"existing.json"
    path.write_text("preserve")
    monkeypatch.setattr(closure,"assemble_priority_layer_proof_bundle",lambda **_:pytest.fail("existing artifact triggered replay"))
    with pytest.raises(closure.PriorityLayerError,match="never overwrites"):
        closure.export_priority_layer_proof_bundle(path)
    assert path.read_text() == "preserve"


def test_candidate_export_is_explicit_and_self_contained(tiny_inventory,tmp_path,capsys):
    path = tmp_path/"tiny-candidate-proof-bundle-v1.json"
    result = closure.export_priority_layer_proof_bundle(path,batch_size=2)
    bundle,target = decode_proof_bundle(path.read_text())
    assert closure.check_priority_layer_proof_bundle(bundle,target) == result.receipt
    assert "NON-ADMITTING" in capsys.readouterr().out


@pytest.mark.parametrize("name",["base","left","right"])
def test_materialization_really_replays_one_ordinary_empty_context_theorem(tiny_inventory,name):
    from peano_lab.kernel.checker import check
    result = closure.assemble_priority_layer_proof_bundle(report=lambda text:None)
    actual = closure.replay_priority_layer_theorem(name,result.bundle,result.target)
    assert check((),actual.certificate,actual.formula)


def test_unknown_materialized_name_is_not_a_trusted_lookup(tiny_inventory):
    result = closure.assemble_priority_layer_proof_bundle(report=lambda text:None)
    with pytest.raises(closure.PriorityLayerError,match="unknown"):
        closure.replay_priority_layer_theorem("missing",result.bundle,result.target)


def _canonical_bundle():
    artifact = ROOT/"research/arithmetic-library/artifacts"/closure.PRIORITY_LAYER_ARTIFACT_FILENAME
    raw = artifact.read_bytes()
    assert len(raw)==4200971 and sha256(raw).hexdigest()=="4fcb3cd45e83448776abb9e33692496a7acfa98a051cae15761826a0b15fda44"
    return decode_proof_bundle(raw.decode())


def test_canonical_first_four_artifact_contains_every_actual_body_and_dependency():
    bundle,target=_canonical_bundle()
    receipt=closure.check_priority_layer_proof_bundle(bundle,target)
    assert receipt.node_count==receipt.kernel_calls==566
    assert receipt.root==565 and receipt.dependency_edges==1690 and receipt.total_body_nodes==38443
    assert set(closure.priority_layer_plan().frontier_names)<=closure._table(()).keys()
    assert closure.priority_layer_bundle()[1]==receipt


@pytest.mark.parametrize("campaign,size,digest,nodes,edges,body_nodes",[
    ("squarefree_perfect_power",1652169,
     "c4d239b9d699fb0dda942e6a2c2015333def7cde45497a7effe8e1cf2ccd785f",286,749,15492),
    ("odd_prime_lte",1336410,
     "5046b29281227227bfd011c60fa8f1a0451ae6e57ab523c00511ea862fa420ff",264,774,15576),
    ("euler_totient",2086863,
     "1a39b9b9d94fd0bb1d8f91f769dc4fd971f11d31bf090d06b962c5c81b161e23",352,992,19448),
    ("continued_fraction_approximation",1160452,
     "2e3e28bcd78d8b5a10fd35c7d8364603c1baef29e7869d594370c045ef3e7ccc",217,557,15298),
])
def test_each_original_candidate_branch_is_reconstructible_from_only_the_canonical_bundle(campaign,size,digest,nodes,edges,body_nodes):
    full,full_target=_canonical_bundle()
    closure.check_priority_layer_proof_bundle(full,full_target)
    positions={r.name:r.node_id for r in closure.priority_layer_plan().rows}
    plan=closure.priority_layer_plan((campaign,))
    local_positions={r.name:r.node_id for r in plan.rows}
    local=[]
    for row in plan.rows:
        original=full.nodes[positions[row.name]]
        local.append(BundleNode(row.node_id,original.target,
                     tuple(local_positions[d] for d in row.dependencies),original.body))
    target,body=closure._packaging_root(tuple(local[local_positions[name]].target for name in plan.root_names))
    local.append(BundleNode(len(local),target,tuple(local_positions[name] for name in plan.root_names),body))
    bundle=ProofBundle(tuple(local),len(local)-1)
    receipt=closure.check_priority_layer_proof_bundle(bundle,target,campaigns=(campaign,))
    assert receipt.node_count==receipt.kernel_calls==nodes and receipt.root==nodes-1
    assert receipt.dependency_edges==edges and receipt.total_body_nodes==body_nodes
    raw=encode_proof_bundle(bundle,target).encode()
    assert len(raw)==size and sha256(raw).hexdigest()==digest


def test_full_g010_materializes_as_one_checked_ordinary_empty_context_proof():
    bundle,target = _canonical_bundle()
    result = closure.replay_priority_layer_theorem("positive_squarefree_kernel_and_power_profile",bundle,target)
    assert result.spec.name == "positive_squarefree_kernel_and_power_profile"
    assert result.proof_nodes == 19750
    assert sha256(result.spec.statement.encode()).hexdigest() == "d90dd7d83bf94f698c6fde0134034eed5e89b5bae73c2caf58b6cdc788313949"


@pytest.mark.parametrize("field",[
    "EXPECTED_PRIORITY_LAYER_FRONTIER_COUNT","EXPECTED_PRIORITY_LAYER_THEOREM_COUNT",
    "EXPECTED_PRIORITY_LAYER_ROOT_COUNT","EXPECTED_PRIORITY_LAYER_DEPENDENCY_EDGE_COUNT",
    "EXPECTED_PRIORITY_LAYER_ORDERED_NAMES_SHA256","EXPECTED_PRIORITY_LAYER_BUNDLE_NODE_COUNT",
    "EXPECTED_PRIORITY_LAYER_BUNDLE_EDGE_COUNT","EXPECTED_PRIORITY_LAYER_BUNDLE_BODY_PROOF_NODES",
    "EXPECTED_PRIORITY_LAYER_BUNDLE_BYTES","EXPECTED_PRIORITY_LAYER_BUNDLE_SHA256",
])
def test_no_unsealed_provider_pin_can_authorize_checked_use(monkeypatch,field):
    monkeypatch.setattr(closure,field,"" if field.endswith("SHA256") else 0)
    with pytest.raises(closure.PriorityLayerError,match="not sealed for checked use"):
        closure.checked_priority_layer_proof_bundle()
