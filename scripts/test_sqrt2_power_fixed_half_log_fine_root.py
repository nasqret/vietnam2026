"""AP092: exact fine-root interface, ordinary bodies and independent checks."""
from hashlib import sha256
from itertools import product
import json
from unittest.mock import patch

import pytest
import sqrt2_power_fixed_half_log_fine_root as fine

BUNDLE_SHA256='c9cabc5640c33f87f1fe31817ab71b04bfb0b43896488e79b8da6b69d62e232c'
BODY_HASHES={'arithmetic':'061de9d24eb17065d5fd14d90ff35e58e6763ee2dd558445ea9816b43145894e',
    'AP092':'93e0b25b49f2f3919261e0027e9cc35b0f09644ed872e662223e1a1bac3809ee'}
NODE_COUNT=595
FOLDER=fine.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-fine-root-v1'
LEAN_FOLDER=fine.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-fine-root-lean-wmi-v1'


def test_power_precedes_all_supplied_fine_roots_and_actual_samples():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    registry=fine.definition_registry();n,premises,out=strip_target(fine.frozen_fixed_half_log_fine_root_target())
    assert n==1 and not premises and type(out) is Exists
    body=out.body;names=('r','n')
    assert body.left==parse_named('Pow(2,n,r)',names,registry)
    assert body.right.left==parse_named('~r=0',names,registry)
    assert body.right.right==parse_named(fine.LATER_SOURCE,names,registry)
    count,guards,actual=strip_target(body.right.right);scope=('t','e','l')+names
    assert count==3 and guards==[parse_named(s,scope,registry) for s in ('DyadicSqrt2(n+l,e,t)','Le(S(S(18*r)),n+l)')]
    count=0
    while type(actual) is Exists:count+=1;actual=actual.body
    assert count==13 and len(fine.PARTS)==23
    assert actual==parse_named(fine.conjoin(fine.PARTS),tuple(reversed(fine.OUTPUTS))+scope,registry)


def test_definition_DAG_is_exactly_the_existing_21_definition_cone():
    from sqrt2_power_fixed_half_log_root_witness import definition_registry
    r=fine.definition_registry();assert r==definition_registry() and len(r)==21
    seen=set();ids=set()
    for name,spec in r.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    c=fine.source_contract()
    assert c['new_definition_ids']==[] and c['new_induction_count']==0
    assert not any(c[k] for k in ('analytic_limit_claimed','root_quotient_accuracy_claimed','fixed_approximation_program_changed','closes_IR072'))


def test_target_mutations_cannot_weaken_actual_roots_horizons_or_error_constants():
    source=fine.NAMED_SOURCE;r=fine.definition_registry()
    for wrong in (source.replace('exists r.','forall r.'),source.replace('DyadicSqrt2(n+l,e,t)','DyadicSqrt2(n,e,t)'),
            source.replace('18*r','18'),source.replace('S(2*(n+l))','S(n+l)'),source.replace('2*(d*p)','d*p'),
            source.replace('~h=0','h=0'),source.replace('h=f*q','h=f+q'),source.replace('8*(e*h)','7*(e*h)'),
            source.replace('2*(e*h)','e*h')):
        assert wrong!=source
        with patch.object(fine,'NAMED_SOURCE',wrong),pytest.raises(ValueError):fine.frozen_fixed_half_log_fine_root_target(_registry=r)


def test_transfer_arithmetic_including_zero_cases_and_sharp_hostile_bounds():
    checked=0
    for r,s,e,t,h,y in product(range(5),repeat=6):
        if r*y<=s*h+8*h and s*h<=r*y+h and s*e<=t*r and t*r<=s*e+e:
            assert r*(e*y)<=r*(t*h)+8*(e*h)
            assert r*(t*h)<=r*(e*y)+2*(e*h)
            checked+=1
    assert checked>500
    # These are helper-level counterexamples, not fabricated DyadicSqrt2 data.
    for r,s,e,t,h,y,forward in ((1,0,1,0,1,8,True),(1,1,1,2,1,0,False)):
        assert r*y<=s*h+8*h and s*h<=r*y+h and s*e<=t*r and t*r<=s*e+e
        assert r*(e*y)>r*(t*h)+7*(e*h) if forward else r*(t*h)>r*(e*y)+(e*h)


def test_each_endpoint_has_one_exact_owned_body_and_wrong_archive_is_rejected():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r=fine.definition_registry();seen={}
    for pin in fine.ARCHIVES:
        rows=fine.read_mixed_archive(pin)
        for name,source in fine.ENDPOINT_SOURCES.items():
            if fine.ENDPOINT_OWNERS[name]!=pin['case']:continue
            target=encode_formula(parse_named(source,registry=r));matches=[i for i,row in enumerate(rows) if row[1]==target]
            assert len(matches)==1 and rows[matches[0]][3];seen[name]=(pin['case'],matches[0])
    assert len(seen)==12 and seen['witnesses']==('AP091',585) and seen['modulus']==('SQ008',135)
    assert seen['mul_left_mono']==('CV071',149)
    with pytest.raises(ValueError):fine.read_mixed_archive(dict(fine.WITNESS_ARCHIVE,raw_sha256='0'*64))


def test_source_closure_and_historical_AP091_case_binding_remain_exact():
    from sqrt2_power_fixed_half_log_root_witness import fixed_half_log_root_witness_source_pins
    from test_sqrt2_power_half_log_root_uniform import _assert_case_source_binding
    pins=fine.fixed_half_log_fine_root_source_pins()
    assert all(pins[name]==pin for name,pin in fixed_half_log_root_witness_source_pins().items())
    old=fine.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-witness-v1'
    _assert_case_source_binding(json.loads((old/'report.json').read_bytes()),old)
    with patch.dict(fine.WITNESS_ARCHIVE,sha256='0'*64),pytest.raises(ValueError):fine.fixed_half_log_fine_root_source_pins()


def checked_bundle():
    from check_sqrt2_power_fresh_lean import exact_bundle
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from peano_lab.library.proof_bundle import decode_proof_bundle
    import run_sqrt2_power_wave as wave
    raw,info=exact_bundle(FOLDER);report=json.loads((FOLDER/'report.json').read_bytes())
    assert info['case']=='AP092' and info['bundle_sha256']==BUNDLE_SHA256 and info['nodes']==NODE_COUNT
    assert report['source_pins']==wave.pins('AP092')
    bundle,target=decode_proof_bundle(raw.decode(),limits=BinaryDAGLimits().bundle_limits())
    assert target==fine.frozen_fixed_half_log_fine_root_target() and bundle.root==NODE_COUNT-1
    return bundle,json.loads(raw)


def test_complete_AP091_prefix_and_both_native_bodies_are_preserved():
    from peano_lab.library.proof_bundle import encode_proof
    bundle,tree=checked_bundle()
    assert tree[3][:586]==fine.read_mixed_archive(fine.WITNESS_ARCHIVE)
    assert tuple(node.node_id for node in bundle.nodes)==tuple(range(NODE_COUNT))
    assert all(all(d<node.node_id for d in node.dependencies) for node in bundle.nodes)
    factories=fine.factories(fine.definition_registry())
    for index,name in ((593,'arithmetic'),(594,'AP092')):
        body=fine.introduce(fine.Scope(),(),fine.HELPER_DEPENDENCIES[name],factories[name]);encoded=encode_proof(body)
        assert encoded==encode_proof(bundle.nodes[index].body) and fine.json_hash(encoded)==BODY_HASHES[name]
        pending=[encoded]
        while pending:
            item=pending.pop()
            if type(item) is list:assert item[0]!='ind';pending.extend(x for x in item[1:] if type(x) is list)


def recheck_partition(which):
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Imp
    bundle,_=checked_bundle();parts=[list(range(i,NODE_COUNT,3)) for i in range(3)]
    assert sorted(i for part in parts for i in part)==list(range(NODE_COUNT))
    for i in parts[which]:
        node=bundle.nodes[i];goal=node.target
        for dep in reversed(node.dependencies):goal=Imp(bundle.nodes[dep].target,goal)
        assert check((),node.body,goal),i


def test_every_actual_body_rechecked_partition_zero():recheck_partition(0)
def test_every_actual_body_rechecked_partition_one():recheck_partition(1)
def test_every_actual_body_rechecked_partition_two():recheck_partition(2)


def test_false_target_and_forged_root_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    bundle,_=checked_bundle()
    with pytest.raises(ProofBundleError):check_proof_bundle(bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(bundle)


def test_fresh_Lean_checked_the_same_certificate_and_both_negative_controls():
    from check_sqrt2_power_fresh_lean import MODULES,AUDIT_OUTPUT
    report=json.loads((LEAN_FOLDER/'report.json').read_bytes())
    assert report['status']=='fresh_lean_checked' and tuple(r['module'] for r in report['compilation'])==MODULES
    assert report['axiom_audit']['stdout']==AUDIT_OUTPUT
    assert len(report['checks'])==1
    row=report['checks'][0]
    assert row['case']=='AP092' and row['independent_lean_checked'] is True and row['bundle_sha256']==BUNDLE_SHA256
    assert row['target_ast_sha256']==fine.TARGET_SHA256 and row['report_sha256']==sha256((FOLDER/'report.json').read_bytes()).hexdigest()
    assert len(report['negative_controls'])==2 and all(r['rejected'] for r in report['negative_controls'])


def test_solver_observation_is_exact_target_evidence_without_proof_authority():
    from observe_sqrt2_power_tail_steps import target_for
    target,digest,_=target_for('AP092-arithmetic')
    observed=json.loads((fine.ROOT/'research/arithmetic-library/sqrt2-power/observations/fixed-half-log-fine-root-solvers-v1.json').read_bytes())
    assert observed['case']=='AP092-arithmetic' and observed['target_ast_sha256']==digest==fine.HELPER_TARGET_SHA256['arithmetic']
    assert observed['authority']=='untrusted_classical_hints_only' and observed['solver_proofs_reconstructed']==0
    assert observed['original_HA_checked'] is False and observed['independent_lean_checked'] is False
    assert observed['budget']['measured_child_cpu_seconds']<=observed['budget']['cpu_hard_limit_reserved_seconds']<=18
    assert [o['observation']['capability']['status'] for o in observed['observations']]==['available','available','unavailable']
    assert [o['observation']['process']['reason'] for o in observed['observations'][:2]]==['cpu_limit','cpu_limit']
    with patch.dict(fine.HELPER_TARGET_SHA256,arithmetic='0'*64),pytest.raises(ValueError):target_for('AP092-arithmetic')
