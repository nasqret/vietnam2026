"""Exact constructive G082 closure, unchanged limits and hostile-proof audits."""

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import pytest

from peano_lab.kernel.formulas import And, Bot, Imp
from peano_lab.kernel.proofs import AndIntro, EqRefl, Hyp
from peano_lab.kernel.terms import Zero
from peano_lab.library import campaign_gaussian_factorization_closure as closure
from peano_lab.library.campaign_lower_layer_closure import LowerLayerError
from peano_lab.library.proof_bundle import BundleNode, ProofBundle, ProofBundleError, decode_proof_bundle, encode_proof_bundle
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = Path(__file__).resolve().parents[3]
G082 = ("gaussian_factorization",)
PRINCIPAL_STATEMENT_SHA256 = {
    "gaussian_gcd_bezout_exists":"67d09aa8ff5c895839b29eb5f9f44d9d91087f8f2316698b47530795b800f981",
    "gaussian_irreducible_dvd_product":"e2fb26736c7080feea9c73498dc0609b2e08cfdd89bdf16857afd0e6a9eb7620",
    "gaussian_irreducible_iff_prime":"aa8c5f0706fbabf6c9069ae0fd2a7f7b3ecf9651b30bad9d7b4483fbd6d2689e",
    "gaussian_prime_factorization_exists":"86d207a622593e87fc60e4c852a6aabb8e6b1057b960cbadc7e2ac736aae827b",
    "gaussian_unique_prime_factorization":"57abdbebab6835ebe1fecb15f4229f2eee579b7d67c22638345cc0deb6e20219",
}
FACTORY_COUNTS = (
    ("gaussian_ring_candidate",65),
    ("gaussian_divisibility_candidate",29),
    ("gaussian_gcd_candidate",14),
    ("gaussian_factor_search_candidate",23),
    ("gaussian_factorization_candidate",28),
    ("gaussian_product_reindex_candidate",3),
    ("gaussian_factor_permutation_candidate",18),
)


def _clear_caches():
    closure._factory_specs.cache_clear()
    closure.gaussian_factorization_specs.cache_clear()
    closure.gaussian_factorization_plan.cache_clear()


def test_exact_v29_parent_and_all_historical_provider_bytes():
    snapshot=closure.parent_snapshot()
    assert len(snapshot.specs)==closure.PARENT_COUNT==3042
    assert closure._specs_digest(snapshot.specs)==closure.PARENT_SPECS_SHA256
    assert sha256((ROOT/closure.PARENT_CATALOG).read_bytes()).hexdigest()==closure.PARENT_CATALOG_SHA256
    assert len(snapshot.documents)==19
    assert tuple(d.bytes for d in snapshot.documents)==tuple(sorted(d.bytes for d in snapshot.documents))
    assert closure.validate_parent_provider_bytes()==snapshot.documents
    assert any(d.path.endswith("alpha-v29-priority-layer-proof-bundle-v1.json") for d in snapshot.documents)


def test_all_seven_registered_factories_are_exact_frozen_sources_in_real_topological_order():
    assert closure.validate_candidate_source_bytes()==closure.FACTORIES
    assert tuple((f.module,len(closure._factory_specs(f))) for f in closure.FACTORIES)==FACTORY_COUNTS
    assert all(f.campaign=="gaussian_factorization" and len(f.source_sha256)==64 and f.rfc.endswith("-rfc-v1.md") for f in closure.FACTORIES)
    rows=closure.gaussian_factorization_specs()
    assert len(rows)==180 and sum(len(r.dependencies) for r in rows)==673
    assert sum(len(r.script) for r in rows)==7859
    assert closure.selected_factories(G082)==closure.selected_factories()


def test_exact_g082_dependency_cone_is_complete_not_a_count_only_or_partial_claim():
    plan=closure.gaussian_factorization_plan()
    assert plan.campaigns==G082 and plan==closure.gaussian_factorization_plan(G082)
    assert len(plan.frontier_names)==180 and len(plan.rows)==452 and len(plan.root_names)==18
    assert plan.dependency_edge_count==1430
    assert plan.ordered_names_sha256=="fe63423af323582ebbe7f05c2bd3848a3717ac5b83bb0de35913789c517ac35f"
    assert len(set(plan.frontier_names))==180
    assert set(PRINCIPAL_STATEMENT_SHA256)<=set(plan.frontier_names)
    assert "gaussian_unique_prime_factorization" in plan.root_names
    seen=set()
    for index,row in enumerate(plan.rows):
        assert row.node_id==index and set(row.dependencies)<=seen
        assert row.campaign is None or row.name in plan.frontier_names
        seen.add(row.name)
    pending,reachable=list(plan.root_names),set()
    rows={r.name:r for r in plan.rows}
    while pending:
        name=pending.pop()
        if name not in reachable:
            reachable.add(name)
            pending.extend(rows[name].dependencies)
    assert reachable==seen and set(plan.frontier_names)<=seen


@pytest.mark.parametrize("name,digest",tuple(PRINCIPAL_STATEMENT_SHA256.items()))
def test_exact_principal_object_level_targets_are_pinned_independently(name,digest):
    assert sha256(closure._table(())[name].statement.encode()).hexdigest()==digest


def test_proof_provider_does_not_import_editions_or_enroll_anything():
    program=(
        "import sys; from peano_lab.library.campaign_gaussian_factorization_closure import gaussian_factorization_plan; "
        "gaussian_factorization_plan(); "
        "assert not any(n.startswith('peano_lab.library.editions') for n in sys.modules); "
        "assert not any(n.startswith('peano_lab.library.alpha_enrollment') for n in sys.modules)"
    )
    subprocess.run([sys.executable,"-c",program],cwd=ROOT,env=dict(os.environ,PYTHONPATH=str(ROOT/"peano-lab/py")),check=True,timeout=45)
    assert closure.GAUSSIAN_FACTORIZATION_ARTIFACT_FILENAME=="alpha-v30-gaussian-factorization-proof-bundle-v1.json"
    assert not hasattr(closure,"checked_gaussian_factorization_bundle")


def test_explicit_parent_specs_need_no_catalogue_or_provider_file_read(monkeypatch):
    specs = closure.parent_snapshot().specs
    expected = closure.gaussian_factorization_plan(G082)
    monkeypatch.setattr(closure,"parent_snapshot",lambda:pytest.fail("metadata planning read a parent file"))
    assert closure.gaussian_factorization_plan(G082,parent_specs=specs) == expected


def test_short_browser_import_path_and_supplied_parent_work_without_admitting(monkeypatch):
    module = ModuleType("peano_lab.library._gaussian_factorization_short_path_test")
    module.__file__ = "/lab/peano_lab/library/campaign_gaussian_factorization_closure.py"
    module.__package__ = "peano_lab.library"
    monkeypatch.setitem(sys.modules,module.__name__,module)
    source = (ROOT/"peano-lab/py/peano_lab/library/campaign_gaussian_factorization_closure.py").read_text()
    exec(compile(source,module.__file__,"exec"),module.__dict__)
    assert module.ROOT == Path("/lab")
    assert module.gaussian_factorization_plan(G082,parent_specs=closure.parent_snapshot().specs).frontier_names == closure.gaussian_factorization_plan(G082).frontier_names


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
    with pytest.raises(closure.GaussianFactorizationError):
        closure._parent_specs(changed)


def test_microbatch_limits_are_the_unchanged_existing_policy():
    from peano_lab.library import campaign_lower_layer_closure as previous
    for field in ("MAX_BATCH_ROWS","MAX_BATCH_PROOF_NODES","MAX_BATCH_PROOF_OBJECTS"):
        assert getattr(closure,field) == getattr(previous,field)
    assert closure.DEFAULT_LAYERED_REPLAY_LIMITS is previous.DEFAULT_LAYERED_REPLAY_LIMITS


@pytest.mark.parametrize("selection",[["gaussian_factorization"],("unknown",),("gaussian_factorization","gaussian_factorization"),(1,),None])
def test_unknown_ambiguous_or_malformed_selection_rejected(selection):
    with pytest.raises(closure.GaussianFactorizationError):
        closure.selected_factories(selection)


@pytest.mark.parametrize("batch",[0,-1,17,True,"1",None])
def test_invalid_batch_rejected_before_any_source_read_or_replay(monkeypatch,batch):
    monkeypatch.setattr(closure,"validate_candidate_source_bytes",lambda *_:pytest.fail("invalid batch read sources"))
    with pytest.raises(closure.GaussianFactorizationError):
        closure.assemble_gaussian_factorization_proof_bundle(batch_size=batch)


@pytest.mark.parametrize("seeds",[["seed.json"],(False,),(None,),"seed.json",("seed.json","./seed.json")])
def test_seed_selection_must_be_explicit_distinct_paths_before_any_replay(monkeypatch,seeds):
    monkeypatch.setattr(closure,"validate_candidate_source_bytes",lambda *_:pytest.fail("invalid seeds read sources"))
    with pytest.raises(closure.GaussianFactorizationError,match="seed"):
        closure.assemble_gaussian_factorization_proof_bundle(seed_bundles=seeds)


@pytest.fixture
def tiny_inventory(monkeypatch):
    parent = TheoremSpec("base","0 = 0",(),("refl",),"Reflexivity.")
    candidates = [TheoremSpec("left","0 = 0",("base",),("exact base",),"Actual prerequisite."),
                  TheoremSpec("right","forall n. n = n",(),("intro n","refl"),"Universal reflexivity.")]
    _clear_caches()
    monkeypatch.setattr(closure,"parent_snapshot",lambda:closure.ParentSnapshot((parent,),()))
    monkeypatch.setattr(closure,"FACTORIES",(closure.GaussianFactorizationFactory("tiny","tiny","factory","tiny-rfc-v1.md","0"*64),))
    monkeypatch.setattr(closure,"import_module",lambda *args,**kwargs:SimpleNamespace(factory=lambda spec:tuple(candidates)))
    monkeypatch.setattr(closure,"validate_candidate_source_bytes",lambda *_:closure.FACTORIES)
    yield parent,candidates
    _clear_caches()


def test_every_actual_body_and_maximal_root_reaches_original_kernel(tiny_inventory):
    result = closure.assemble_gaussian_factorization_proof_bundle(report=lambda text:None)
    assert result.receipt.kernel_calls == result.receipt.node_count == 4
    assert result.receipt.dependency_edges == 3 and isinstance(result.target,And)
    assert result.bundle.nodes[-1].dependencies == (1,2)
    assert result.origins == (("base","parent_script",None),("left","new_script",None),("right","new_script",None))


@pytest.mark.parametrize("mutation",["root","target","edge","packaging","body","inventory"])
def test_forged_targets_edges_bodies_or_packaging_cannot_pass(tiny_inventory,mutation):
    result = closure.assemble_gaussian_factorization_proof_bundle(report=lambda text:None)
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
    with pytest.raises((closure.GaussianFactorizationError,ProofBundleError)):
        closure.check_gaussian_factorization_proof_bundle(bundle,result.target)


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
    with pytest.raises(closure.GaussianFactorizationError):
        closure.gaussian_factorization_plan()


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
        with pytest.raises((closure.GaussianFactorizationError,ProofBundleError)):
            closure.assemble_gaussian_factorization_proof_bundle(report=lambda text:None)
    else:
        result = closure.assemble_gaussian_factorization_proof_bundle(report=lambda text:None)
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
    result = closure.assemble_gaussian_factorization_proof_bundle(report=lambda text:None)
    assert result.receipt.kernel_calls == 6
    assert result.origins[2][1] == (path.name if dependency_ids==(0,1) else "parent_script")


def test_candidate_seed_checks_every_node_then_reuses_exact_bodies_without_rebuilding(tiny_inventory,monkeypatch,tmp_path):
    first=closure.assemble_gaussian_factorization_proof_bundle(report=lambda text:None)
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
    second=closure.assemble_gaussian_factorization_proof_bundle(seed_bundles=(path,),report=lambda text:None)
    assert observations==[4,4]
    assert second.bundle==first.bundle and second.receipt==first.receipt
    assert second.origins==tuple((row.name,str(path),row.node_id) for row in closure.gaussian_factorization_plan().rows)


def test_candidate_seed_invalid_unused_node_is_not_ignored(tiny_inventory,tmp_path):
    first=closure.assemble_gaussian_factorization_proof_bundle(report=lambda text:None)
    # The invalid theorem is outside the requested candidate dependency cone,
    # but remains reachable from the seed's own complete packaging root.
    target,body=closure._packaging_root((first.target,Bot()))
    broken=ProofBundle(first.bundle.nodes+(BundleNode(4,Bot(),(),Hyp(0)),
                       BundleNode(5,target,(3,4),body)),5)
    path=tmp_path/"unused-forgery.json"
    path.write_text(encode_proof_bundle(broken,target))
    with pytest.raises(ProofBundleError):
        closure.assemble_gaussian_factorization_proof_bundle(seed_bundles=(path,),report=lambda text:None)


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
    result=closure.assemble_gaussian_factorization_proof_bundle(seed_bundles=(path,),report=lambda text:None)
    assert result.receipt.kernel_calls==6
    assert result.origins[2][1]==(str(path) if dependency_ids==(0,1) else "parent_script")


def test_candidate_seed_with_unrelated_valid_target_does_not_change_requested_theorems(tiny_inventory,tmp_path):
    unrelated=TheoremSpec("other","3 = 3",(),("refl",),"Unrelated reflexivity.")
    target=_closed_formula(unrelated.statement)
    seed=ProofBundle((BundleNode(0,target,(),closure._reconstruct_body(unrelated,{"other":unrelated})),),0)
    path=tmp_path/"unrelated-seed.json"
    path.write_text(encode_proof_bundle(seed,target))
    result=closure.assemble_gaussian_factorization_proof_bundle(seed_bundles=(path,),report=lambda text:None)
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
    with pytest.raises(closure.GaussianFactorizationError,match="unchanged bundle byte limit"):
        closure.assemble_gaussian_factorization_proof_bundle(seed_bundles=(path,),report=lambda text:None)


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
    closure.assemble_gaussian_factorization_proof_bundle(batch_size=3,report=lambda text:None)
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
    with pytest.raises(closure.GaussianFactorizationError,match="historical proof bytes changed"):
        closure.validate_parent_provider_bytes()


def test_candidate_export_never_overwrites_existing_artifacts(monkeypatch,tmp_path):
    path = tmp_path/"existing.json"
    path.write_text("preserve")
    monkeypatch.setattr(closure,"assemble_gaussian_factorization_proof_bundle",lambda **_:pytest.fail("existing artifact triggered replay"))
    with pytest.raises(closure.GaussianFactorizationError,match="never overwrites"):
        closure.export_gaussian_factorization_proof_bundle(path)
    assert path.read_text() == "preserve"


def test_candidate_export_is_explicit_and_self_contained(tiny_inventory,tmp_path,capsys):
    path = tmp_path/"tiny-candidate-proof-bundle-v1.json"
    result = closure.export_gaussian_factorization_proof_bundle(path,batch_size=2)
    bundle,target = decode_proof_bundle(path.read_text())
    assert closure.check_gaussian_factorization_proof_bundle(bundle,target) == result.receipt
    assert "NON-ADMITTING" in capsys.readouterr().out


@pytest.mark.parametrize("name",["base","left","right"])
def test_materialization_really_replays_one_ordinary_empty_context_theorem(tiny_inventory,name):
    from peano_lab.kernel.checker import check
    result = closure.assemble_gaussian_factorization_proof_bundle(report=lambda text:None)
    actual = closure.replay_gaussian_factorization_theorem(name,result.bundle,result.target)
    assert check((),actual.certificate,actual.formula)


def test_unknown_materialized_name_is_not_a_trusted_lookup(tiny_inventory):
    result = closure.assemble_gaussian_factorization_proof_bundle(report=lambda text:None)
    with pytest.raises(closure.GaussianFactorizationError,match="unknown"):
        closure.replay_gaussian_factorization_theorem("missing",result.bundle,result.target)


def _hoisting_fixture():
    from peano_lab.kernel.formulas import Eq, Forall
    from peano_lab.kernel.proofs import ForallElim, ForallIntro, ImpIntro
    from peano_lab.kernel.terms import Succ, Var
    zero,one=Zero(),Succ(Zero())
    universal=Forall(Eq(Var(0),Var(0)))
    a,b=Eq(zero,zero),Eq(one,one)
    target=And(a,b)
    nodes=(
        closure.LayeredReplayNode(0,universal,(),ForallIntro(EqRefl(Var(0)))),
        closure.LayeredReplayNode(1,a,(0,),ImpIntro(ForallElim(Hyp(0),zero))),
        closure.LayeredReplayNode(2,b,(0,),ImpIntro(ForallElim(Hyp(0),one))),
        closure.LayeredReplayNode(3,target,(1,2),ImpIntro(ImpIntro(AndIntro(Hyp(1),Hyp(0))))),
    )
    # A smaller existing fan-in bound also forces two independent arguments.
    limits=replace(closure.DEFAULT_LAYERED_REPLAY_LIMITS,max_dependencies_per_node=2)
    return closure.LayeredReplayBundle(nodes,3),target,limits


def test_hoisting_is_untrusted_ordinary_syntax_and_preserves_empty_context_conclusion(monkeypatch):
    from peano_lab.kernel.checker import check
    graph,target,limits=_hoisting_fixture()
    monkeypatch.setattr(closure,"check",lambda *_:pytest.fail("untrusted compiler invoked proof authority"))
    actual=closure.compile_gaussian_factorization_replay(graph,target,limits=limits)
    assert actual is not None and actual.target==target
    assert check((),actual.certificate,target)
    assert actual.layers==((0,),(1,2),(3,))
    assert actual.graph_formula_occurrences==30
    assert actual.package_formula_occurrences==22 and actual.maximum_package_formula_depth==4
    assert actual.conditional_formula_occurrences==41
    assert actual.argument_formula_occurrences==(13,30)
    assert actual.argument_formula_depths==(5,7)
    assert (actual.proof_nodes,actual.proof_objects,actual.proof_depth,
        actual.proof_annotation_occurrences,actual.proof_envelope_depth)==(46,46,11,139,11)
    metrics=closure._proof_envelope_metrics_bounded(actual.certificate,
        max_proof_occurrences=limits.max_candidate_proof_occurrences,
        max_proof_objects=limits.max_candidate_proof_objects,
        max_proof_depth=limits.max_candidate_proof_depth,
        max_annotation_occurrences=limits.max_candidate_annotation_occurrences,
        max_annotation_depth=limits.max_formula_depth,
        max_envelope_depth=limits.max_candidate_envelope_depth,label="independent full envelope")
    assert metrics==(46,46,11,139,11)


@pytest.mark.parametrize("mutation",("conclusion","omitted_argument","open_argument",
    "open_body","swapped_body_premises","reversed_edges","miswired_projection"))
def test_hoisting_never_hides_an_omitted_or_miswired_logical_premise(monkeypatch,mutation):
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.proofs import ImpElim, ImpIntro
    graph,target,limits=_hoisting_fixture()
    if mutation in ("open_body","swapped_body_premises","reversed_edges"):
        root=graph.nodes[-1]
        if mutation=="reversed_edges":
            root=replace(root,dependencies=tuple(reversed(root.dependencies)))
        else:
            body=Hyp(0) if mutation=="open_body" else ImpIntro(ImpIntro(AndIntro(Hyp(0),Hyp(1))))
            root=replace(root,body=body)
        graph=replace(graph,nodes=graph.nodes[:-1]+(root,))
    if mutation=="miswired_projection":
        project=closure._project
        monkeypatch.setattr(closure,"_project",lambda index,path:project(index+1,path))
    actual=closure.compile_gaussian_factorization_replay(graph,target,limits=limits)
    assert actual is not None  # structural compilation is deliberately not authority
    proof=actual.certificate
    if mutation=="conclusion":
        target=And(target.right,target.left)
    elif mutation=="omitted_argument":
        proof=proof.function
    elif mutation=="open_argument":
        proof=ImpElim(proof.function,Hyp(0))
    assert not check((),proof,target)


@pytest.mark.parametrize("field,value",(
    ("max_nodes",3),("max_dependencies_per_node",1),("max_dependency_edges",3),
    ("max_formula_occurrences_per_target",8),("max_total_formula_occurrences",29),
    ("max_body_occurrences",4),("max_total_body_occurrences",12),
    ("max_package_formula_occurrences",21),("max_package_formula_depth",3),
    ("max_candidate_proof_occurrences",45),("max_candidate_proof_objects",45),
    ("max_candidate_proof_depth",10),("max_candidate_annotation_occurrences",138),
    ("max_candidate_envelope_depth",10),
))
def test_hoisting_charges_original_graph_and_entire_transformed_envelope_without_cap_laundering(field,value):
    graph,target,limits=_hoisting_fixture()
    assert closure.compile_gaussian_factorization_replay(graph,target,limits=limits) is not None
    assert closure.compile_gaussian_factorization_replay(graph,target,limits=replace(limits,**{field:value})) is None


@pytest.mark.parametrize("mutation",("dangling","unreachable","duplicate","wrong_root","free_target","unknown_proof","bad_limits"))
def test_hoisting_validates_the_original_graph_before_creating_any_argument(monkeypatch,mutation):
    from peano_lab.kernel.formulas import Eq
    from peano_lab.kernel.proofs import DNE
    from peano_lab.kernel.terms import Var
    graph,target,limits=_hoisting_fixture()
    if mutation=="dangling":
        graph=replace(graph,nodes=graph.nodes[:-1]+(replace(graph.nodes[-1],dependencies=(1,99)),))
    elif mutation=="unreachable":
        graph=replace(graph,nodes=graph.nodes+(closure.LayeredReplayNode(99,target,(),Hyp(0)),))
    elif mutation=="duplicate":
        graph=replace(graph,nodes=graph.nodes+(graph.nodes[0],))
    elif mutation=="wrong_root":
        graph=replace(graph,root=0)
    elif mutation=="free_target":
        graph=replace(graph,nodes=(replace(graph.nodes[0],target=Eq(Var(0),Var(0))),)+graph.nodes[1:])
    elif mutation=="unknown_proof":
        graph=replace(graph,nodes=(replace(graph.nodes[0],body=DNE(target)),)+graph.nodes[1:])
    else:
        limits=replace(limits,max_candidate_proof_occurrences=True)
    monkeypatch.setattr(closure,"_balanced_package",lambda *_:pytest.fail("invalid original graph reached hoisting"))
    assert closure.compile_gaussian_factorization_replay(graph,target,limits=limits) is None


def _canonical_bundle():
    path=ROOT/"research/arithmetic-library/artifacts"/closure.GAUSSIAN_FACTORIZATION_ARTIFACT_FILENAME
    raw=path.read_bytes()
    assert len(raw)==closure.EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BYTES==6143166
    assert sha256(raw).hexdigest()==closure.EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_SHA256=="e0e10f11c5b12b411843054000a77be22ede7db53602814f9532e3e7c8daa270"
    return decode_proof_bundle(raw.decode())


def test_canonical_g082_bundle_contains_every_actual_body_and_ordered_dependency():
    bundle,target=_canonical_bundle()
    receipt=closure.check_gaussian_factorization_proof_bundle(bundle,target)
    assert receipt.node_count==receipt.kernel_calls==453 and receipt.root==452
    assert receipt.dependency_edges==1448
    assert receipt.total_body_nodes==closure.EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BODY_PROOF_NODES==39423
    assert closure.gaussian_factorization_bundle()[1]==receipt


@pytest.mark.parametrize("prefix,last_rows,frontier,size,digest,nodes,edges,body_nodes",(
    (2,0,94,2917840,"9e507e3af8c9b2315a8394cd8efbe7e45dd4b623245ce392e75b2e39d7843aac",272,780,24402),
    (4,0,131,4012681,"48c236d01895aab546984ae0f5a7e7dea45cb470525d657e41035bb2d469f428",322,979,27898),
    (5,0,159,5404477,"a10b30285d5f491b0e38116bd57c03ac54fd0a3bb86c9e3ac9492c5e2eb95aef",410,1267,33681),
    (6,0,162,5561076,"b6ce6cc10f7aa2c9496bb74d610f17db08fe47a24793435c5530c252eab2a162",414,1293,34336),
    (7,12,174,6112729,"5237738a4e95fe1705e1fe4fb8fd5b472d59b473a661c272d3549a9e54bb8de6",447,1421,38237),
))
def test_each_bounded_authoring_checkpoint_is_reconstructible_from_only_canonical_proof_data(
        monkeypatch,prefix,last_rows,frontier,size,digest,nodes,edges,body_nodes):
    full,full_target=_canonical_bundle()
    closure.check_gaussian_factorization_proof_bundle(full,full_target)
    positions={r.name:r.node_id for r in closure.gaussian_factorization_plan().rows}
    monkeypatch.setattr(closure,"FACTORIES",closure.FACTORIES[:prefix])
    _clear_caches()
    if last_rows:
        actual_factory=closure._factory_specs
        final_factory=closure.FACTORIES[-1]
        @lru_cache(maxsize=32)
        def selected_rows(owner):
            actual=actual_factory(owner)
            return actual[:last_rows] if owner==final_factory else actual
        monkeypatch.setattr(closure,"_factory_specs",selected_rows)
    try:
        plan=closure.gaussian_factorization_plan()
        assert len(plan.frontier_names)==frontier
        local_positions={r.name:r.node_id for r in plan.rows}
        projected=[]
        for row in plan.rows:
            original=full.nodes[positions[row.name]]
            projected.append(BundleNode(row.node_id,original.target,
                tuple(local_positions[d] for d in row.dependencies),original.body))
        target,body=closure._packaging_root(tuple(projected[local_positions[n]].target for n in plan.root_names))
        projected.append(BundleNode(len(projected),target,tuple(local_positions[n] for n in plan.root_names),body))
        bundle=ProofBundle(tuple(projected),len(projected)-1)
        receipt=closure.check_gaussian_factorization_proof_bundle(bundle,target)
        assert receipt.node_count==receipt.kernel_calls==nodes and receipt.root==nodes-1
        assert receipt.dependency_edges==edges and receipt.total_body_nodes==body_nodes
        raw=encode_proof_bundle(bundle,target).encode()
        assert len(raw)==size and sha256(raw).hexdigest()==digest
    finally:
        _clear_caches()


def test_full_g082_materializes_as_one_checked_ordinary_empty_context_theorem(monkeypatch):
    observed=[]
    compile_actual=closure.compile_gaussian_factorization_replay
    def record(*args,**kwargs):
        candidate=compile_actual(*args,**kwargs)
        observed.append(candidate)
        return candidate
    monkeypatch.setattr(closure,"compile_gaussian_factorization_replay",record)
    bundle,target=_canonical_bundle()
    result=closure.replay_gaussian_factorization_theorem("gaussian_unique_prime_factorization",bundle,target)
    assert result.spec.name=="gaussian_unique_prime_factorization"
    assert result.proof_nodes==52094
    assert sha256(result.spec.statement.encode()).hexdigest()==PRINCIPAL_STATEMENT_SHA256[result.spec.name]
    assert len(observed)==1
    actual=observed[0]
    assert sum(len(layer) for layer in actual.layers)==429
    assert actual.graph_formula_occurrences==285867
    assert actual.package_formula_occurrences==278584
    assert actual.maximum_package_formula_depth==65
    assert actual.conditional_formula_occurrences==759299
    assert actual.argument_formula_occurrences==(42977,497487,219261)
    assert actual.argument_formula_depths==(52,72,87)
    assert (actual.proof_nodes,actual.proof_objects,actual.proof_depth,
        actual.proof_annotation_occurrences,actual.proof_envelope_depth)==(52094,35123,118,2215215,118)


@pytest.mark.parametrize("mutation",("none","reverse_premises","missing_premise","false_target"))
def test_largest_induction_body_is_a_real_closed_implication_with_exact_ordered_premises(mutation):
    bundle,_=_canonical_bundle()
    positions={r.name:r.node_id for r in closure.gaussian_factorization_plan().rows}
    node=bundle.nodes[positions["gaussian_irreducible_products_associate_unique"]]
    assert len(node.dependencies)==24
    dependencies=node.dependencies
    if mutation=="reverse_premises":
        dependencies=tuple(reversed(dependencies))
    elif mutation=="missing_premise":
        dependencies=dependencies[:-1]
    target=Bot() if mutation=="false_target" else node.target
    for dependency in reversed(dependencies):
        target=Imp(bundle.nodes[dependency].target,target)
    ordinary=ProofBundle((BundleNode(0,target,(),node.body),),0)
    if mutation=="none":
        encoded=encode_proof_bundle(ordinary,target)
        assert len(encoded.encode())==877945
        assert sha256(encoded.encode()).hexdigest()=="ad9953dcb6df071521d83630c46fb4ccff7b30bd7d18cbde814fb16a484a8e07"
        decoded,decoded_target=decode_proof_bundle(encoded)
        receipt=closure.check_proof_bundle(decoded,decoded_target)
        assert receipt.kernel_calls==receipt.node_count==1
        assert receipt.dependency_edges==0 and receipt.total_body_nodes==827
    else:
        with pytest.raises(ProofBundleError,match="kernel rejected"):
            closure.check_proof_bundle(ordinary,target)


@pytest.mark.parametrize("field",[
    "EXPECTED_GAUSSIAN_FACTORIZATION_FRONTIER_COUNT","EXPECTED_GAUSSIAN_FACTORIZATION_THEOREM_COUNT",
    "EXPECTED_GAUSSIAN_FACTORIZATION_ROOT_COUNT","EXPECTED_GAUSSIAN_FACTORIZATION_DEPENDENCY_EDGE_COUNT",
    "EXPECTED_GAUSSIAN_FACTORIZATION_ORDERED_NAMES_SHA256","EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_NODE_COUNT",
    "EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_EDGE_COUNT","EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BODY_PROOF_NODES",
    "EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BYTES","EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_SHA256",
])
def test_no_unsealed_provider_pin_can_authorize_checked_use(monkeypatch,field):
    monkeypatch.setattr(closure,field,"" if field.endswith("SHA256") else 0)
    with pytest.raises(closure.GaussianFactorizationError,match="not sealed for checked use"):
        closure.checked_gaussian_factorization_proof_bundle()
