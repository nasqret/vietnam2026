"""AP093: actual quotient, explicit residual, native bodies and Lean evidence."""
from hashlib import sha256
from itertools import product
import json
from math import isqrt,lcm
from unittest.mock import patch

import pytest
import sqrt2_power_log_root_half_argument as p

BUNDLE_SHA256='d8a884f082830521daf08ad2866919f91894adbf5dcff76af374cdc6049f2ec5'
BODY_HASHES={'arithmetic':'eec17e6eb437cacfee5f6d24facb41fbae9a20cd97a13cbb53518349c29fd111',
    'AP093':'18e8491aa09b0a1cb363002a0041766fd4a45fa6f8d5d9295738ea4282db1b69'}
NODE_COUNT=69
FOLDER=p.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-log-root-half-argument-v1'
LEAN_FOLDER=p.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-log-root-half-argument-lean-wmi-v1'


def test_original_supplied_graph_and_positive_scale_are_the_only_premises():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    n,premises,out=strip_target(p.frozen_log_root_half_argument_target())
    names=tuple(reversed(p.PARAMETERS));r=p.definition_registry()
    assert n==8 and premises==[parse_named(s,names,r) for s in ('~D=0',p.GRAPH)]
    assert len(p.PARTS)==10 and out==parse_named(p._and(p.PARTS),names,r)
    assert p.U=='((3*x)*d)' and p.V=='((D*p)*s)'
    assert p.W=='((3*x)*s)' and p.Z=='(2*((D*p)*d))'


def test_definition_DAG_reuses_exactly_the_existing_sixteen_definitions():
    from sqrt2_power_log_root_argument import definition_registry
    r=p.definition_registry();assert r==definition_registry() and len(r)==16
    seen=set();ids=set()
    for name,spec in r.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    contract=p.source_contract()
    assert contract['new_definition_ids']==[] and contract['new_induction_count']==0
    assert not any(contract[k] for k in ('finite_equality_claimed','original_approximation_program_changed',
        'analytic_identity_claimed','analytic_limit_claimed','closes_IR072'))


def test_target_mutations_cannot_remove_guards_or_replace_the_original_quotient():
    source=p.NAMED_SOURCE
    for wrong in (source.replace('~D=0 -> ',''),source.replace('NatSqrt2LogArgument(k,','NatSqrt2LogArgument(k+1,'),
            source.replace(p.U,'((3*x)*s)'),source.replace(p.V,'((D*p)*d)'),source.replace(p.Z,'((D*p)*d)'),
            source.replace('~p=0','p=0'),source.replace('2*('+p.V+'*'+p.Z+')','1*('+p.V+'*'+p.Z+')')):
        assert wrong!=source
        with patch.object(p,'NAMED_SOURCE',wrong),pytest.raises(ValueError):p.frozen_log_root_half_argument_target()


def test_arithmetic_with_zero_numerator_and_hostile_residual_counterexamples():
    checked=zero=0
    for A,B,d,s in product(range(8),repeat=4):
        if B and d and s and d<=s<=2*d and A<=B and s*s<=2*d*d<=s*s+4*d:
            U,V,W,Z=A*d,B*s,A*s,2*B*d
            assert V and Z and U<=V and W<=Z and V*W<=Z*U
            assert d*(Z*U)<=d*(V*W)+2*(V*Z)
            checked+=1;zero+=A==0
    assert checked>100 and zero>10
    # Helper-level examples, not fabricated DyadicSqrt2 computation codes.
    A=B=1;d=s=3;U,V,W,Z=A*d,B*s,A*s,2*B*d
    assert s*s<=2*d*d<=s*s+4*d and d*(Z*U)>d*(V*W)+V*Z
    d=s=5;U,V,W,Z=A*d,B*s,A*s,2*B*d
    assert not 2*d*d<=s*s+4*d and d*(Z*U)>d*(V*W)+2*(V*Z)


def test_actual_finite_numeric_values_keep_a_residual_instead_of_false_equality():
    unequal=0
    for k in range(7):
        d=2**k;s=isqrt(2*d*d);D=lcm(*range(1,2*k+1)) if k else 1;N=2*k+1
        coefficients=[2*D//j if j%2 else 0 for j in range(N)]
        x=sum(a*3**(N-1-j) for j,a in enumerate(coefficients));power=3**N
        A=3*x;B=D*power;U,V,W,Z=A*d,B*s,A*s,2*B*d
        assert A+3*D<=B and d<=s<2*d and s*s<=2*d*d<=s*s+4*d
        assert V and Z and U<=V and W<=Z and V*W<=Z*U
        assert d*(Z*U)<=d*(V*W)+2*(V*Z)
        unequal+=V*W!=Z*U
    assert unequal==6


def test_each_dependency_has_one_exact_owned_archived_body():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r=p.definition_registry();seen={}
    for archive in p.ARCHIVES:
        rows=p.read_mixed_archive(archive)
        for name,source in p.ENDPOINT_SOURCES.items():
            if p.ENDPOINT_OWNERS[name]!=archive['case']:continue
            target=encode_formula(parse_named(source,registry=r));matches=[i for i,row in enumerate(rows) if row[1]==target]
            assert len(matches)==1 and rows[matches[0]][3];seen[name]=(archive['case'],matches[0])
    assert len(seen)==14 and seen['inner_bound']==('AP001',154) and seen['square']==('SQ009',52)
    assert seen['mul_left_mono']==('CV071',149)
    with pytest.raises(ValueError):p.read_mixed_archive(dict(p.SQUARE_ARCHIVE,raw_sha256='0'*64))


def test_source_closure_and_historical_AP092_case_are_unchanged():
    from test_sqrt2_power_half_log_root_uniform import _assert_case_source_binding
    pins=p.log_root_half_argument_source_pins()
    assert all(pins[name]==pin for name,pin in p.log_root_independence_source_pins().items())
    old=p.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-fine-root-v1'
    _assert_case_source_binding(json.loads((old/'report.json').read_bytes()),old)
    with patch.dict(p.SQUARE_ARCHIVE,sha256='0'*64),pytest.raises(ValueError):p.log_root_half_argument_source_pins()


def checked_bundle():
    from check_sqrt2_power_fresh_lean import exact_bundle
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from peano_lab.library.proof_bundle import decode_proof_bundle
    from test_sqrt2_power_half_log_root_uniform import _assert_case_source_binding
    raw,info=exact_bundle(FOLDER);report=json.loads((FOLDER/'report.json').read_bytes())
    assert info['case']=='AP093' and info['bundle_sha256']==BUNDLE_SHA256 and info['nodes']==NODE_COUNT
    _assert_case_source_binding(report,FOLDER)
    bundle,target=decode_proof_bundle(raw.decode(),limits=BinaryDAGLimits().bundle_limits())
    assert target==p.frozen_log_root_half_argument_target() and bundle.root==NODE_COUNT-1
    return bundle,json.loads(raw)


def test_exact_native_bodies_and_topological_DAG_have_no_new_induction():
    from peano_lab.library.proof_bundle import encode_proof
    bundle,tree=checked_bundle()
    assert tuple(node.node_id for node in bundle.nodes)==tuple(range(NODE_COUNT))
    assert all(all(d<node.node_id for d in node.dependencies) for node in bundle.nodes)
    factories=p.factories(p.definition_registry())
    for index,name in ((67,'arithmetic'),(68,'AP093')):
        body=p.introduce(p.Scope(),(),p.HELPER_DEPENDENCIES[name],factories[name]);encoded=encode_proof(body)
        assert encoded==encode_proof(bundle.nodes[index].body) and p.json_hash(encoded)==BODY_HASHES[name]
        pending=[encoded]
        while pending:
            item=pending.pop()
            if type(item) is list:assert item[0]!='ind';pending.extend(x for x in item[1:] if type(x) is list)


def recheck_partition(which):
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Imp
    bundle,_=checked_bundle();parts=[list(range(i,NODE_COUNT,2)) for i in range(2)]
    assert sorted(i for part in parts for i in part)==list(range(NODE_COUNT))
    for i in parts[which]:
        node=bundle.nodes[i];goal=node.target
        for dep in reversed(node.dependencies):goal=Imp(bundle.nodes[dep].target,goal)
        assert check((),node.body,goal),i


def test_every_actual_body_rechecked_partition_zero():recheck_partition(0)
def test_every_actual_body_rechecked_partition_one():recheck_partition(1)


def test_false_target_and_forged_root_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    bundle,_=checked_bundle()
    with pytest.raises(ProofBundleError):check_proof_bundle(bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(bundle)


def test_fresh_Lean_checks_the_same_bytes_and_rejects_both_hostile_controls():
    from check_sqrt2_power_fresh_lean import MODULES,AUDIT_OUTPUT
    report=json.loads((LEAN_FOLDER/'report.json').read_bytes())
    assert report['status']=='fresh_lean_checked' and tuple(r['module'] for r in report['compilation'])==MODULES
    assert report['axiom_audit']['stdout']==AUDIT_OUTPUT and len(report['checks'])==1
    row=report['checks'][0]
    assert row['case']=='AP093' and row['independent_lean_checked'] is True and row['bundle_sha256']==BUNDLE_SHA256
    assert row['target_ast_sha256']==p.TARGET_SHA256 and row['report_sha256']==sha256((FOLDER/'report.json').read_bytes()).hexdigest()
    assert len(report['negative_controls'])==2 and all(r['rejected'] for r in report['negative_controls'])


def test_solver_observation_binds_only_the_frozen_leaf_without_proof_authority():
    from observe_sqrt2_power_tail_steps import target_for
    _,digest,_=target_for('AP093-arithmetic')
    report=json.loads((p.ROOT/'research/arithmetic-library/sqrt2-power/observations/log-root-half-argument-solvers-v1.json').read_bytes())
    assert report['case']=='AP093-arithmetic' and report['target_ast_sha256']==digest==p.HELPER_TARGET_SHA256['arithmetic']
    assert report['authority']=='untrusted_classical_hints_only' and report['solver_proofs_reconstructed']==0
    assert report['original_HA_checked'] is False and report['independent_lean_checked'] is False
    assert report['budget']['measured_child_cpu_seconds']<=report['budget']['cpu_hard_limit_reserved_seconds']<=18
    assert [o['observation']['capability']['status'] for o in report['observations']]==['available','available','unavailable']
    with patch.dict(p.HELPER_TARGET_SHA256,arithmetic='0'*64),pytest.raises(ValueError):target_for('AP093-arithmetic')
