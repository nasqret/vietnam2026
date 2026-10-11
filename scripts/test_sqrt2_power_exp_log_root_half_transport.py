"""AP094: unchanged original sample, independent heads and finite exp error."""
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from math import factorial,isqrt,lcm
from unittest.mock import patch

import pytest
import sqrt2_power_exp_log_root_half_transport as p

BUNDLE_SHA256='b234e8883d2975dd2cb5ab32133703fb623196946051fffc74181f9e8a7d3f6c'
BODY_HASHES={'eighteen':'9c88aed964cd522c22b61c66474d3f6bd34bb7bd67427314f30e87b71da854fa',
    'arithmetic':'e27202e9d8fc4f65da859ba644d5cd23c2f0e0b06bf0fd7cfc89cf450cec04b3',
    'AP094':'ccb2a44f1c6b5f621ceae6e3ee062c5cd7a31179574e7d35e6bb491ece40b43e'}
NODE_COUNT=214
FOLDER=p.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-log-root-half-transport-v1'
LEAN_FOLDER=p.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-log-root-half-transport-lean-wmi-v1'


def test_original_sample_degree_and_independent_positive_head_are_explicit():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    n,premises,out=strip_target(p.frozen_exp_log_root_half_transport_target())
    names=tuple(reversed(p.PARAMETERS));r=p.definition_registry()
    assert n==20 and len(premises)==6 and premises==[parse_named(s,names,r) for s in p.PREMISES]
    assert len(p.PARTS)==7 and out==parse_named(p._and(p.PARTS),names,r)
    assert p.PREMISES[1]==p.ORIGINAL_GRAPH and p.PREMISES[2]=='~v=0'
    assert p.PREMISES[3].endswith(',jb,jc,k+2)') and p.PREMISES[-1]=='Sum(jb,jc,S(k+2),z)'


def test_exact_reused_definition_DAG_adds_no_accuracy_or_analytic_assumption():
    from sqrt2_power_supplied_exp_sample import definition_registry
    from sqrt2_power_log_root_half_argument import definition_registry as argument_registry
    r=p.definition_registry();assert r==definition_registry() and len(r)==23
    assert all(r[name]==spec for name,spec in argument_registry().items())
    seen=set();ids=set()
    for name,spec in r.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    contract=p.source_contract()
    assert contract['new_definition_ids']==[] and contract['new_induction_count']==0
    assert contract['tiny_ground_evaluator_max_value']==32
    assert not any(contract[k] for k in ('original_approximation_program_changed','analytic_identity_claimed',
        'analytic_limit_claimed','closes_IR072'))


def test_target_mutations_cannot_identify_heads_or_change_degrees_and_errors():
    source=p.NAMED_SOURCE
    for wrong in (source.replace('~D=0 -> ',''),source.replace('~v=0 -> ',''),
            source.replace(p.ORIGINAL_GRAPH,p.ORIGINAL_GRAPH.replace('(k,','(k+1,')),
            source.replace(',jb,jc,k+2)',',jb,jc,k+3)'),source.replace('S(k+2),z','S(k+1),z'),
            source.replace(p.Z,'((D*p)*d)'),source.replace('BetaAt(jb,jc,0,v)','BetaAt(jb,jc,0,w0)'),
            source.replace('18*(w0*v)','17*(w0*v)'),source.replace('Le(w0*z,v*y)','Le(v*y,w0*z)')):
        assert wrong!=source
        with patch.object(p,'NAMED_SOURCE',wrong),pytest.raises(ValueError):p.frozen_exp_log_root_half_transport_target()


def test_cancellation_arithmetic_and_guards_including_zero_heads():
    checked=zero=0
    for d,V,Z,a,b,u,v in product(range(1,4),range(1,4),range(1,4),range(4),range(4),range(4),range(4)):
        Q=V*Z
        if d*(Q*(a*v))<=d*(Q*(b*u))+9*(0*(a*b)) and d*(Q*(b*u))<=d*(Q*(a*v))+9*((2*Q)*(a*b)):
            assert a*v<=b*u and d*(b*u)<=d*(a*v)+18*(a*b)
            checked+=1;zero+=a==0 or b==0
    assert checked>1000 and zero>100
    # Cancellation fails if any required positive multiplier is zero.
    for d,V,Z in ((0,1,1),(1,0,1),(1,1,0)):
        a,b,u,v=1,0,0,1;Q=V*Z
        assert d*(Q*(a*v))<=d*(Q*(b*u)) and d*(Q*(b*u))<=d*(Q*(a*v))+18*Q*a*b
        assert not a*v<=b*u
    # Sharp for this helper's premises, not an actual exponential table.
    d=V=Z=a=b=1;u=18;v=0
    assert a*v<=b*u and d*(b*u)<=d*(a*v)+18*a*b and not d*(b*u)<=d*(a*v)+17*a*b


def test_actual_finite_exp_values_keep_independent_positive_normalizations():
    unequal=0
    for k in range(6):
        d=2**k;s=isqrt(2*d*d);D=lcm(*range(1,2*k+1)) if k else 1;M=2*k+1;N=k+2
        coefficients=[2*D//j if j%2 else 0 for j in range(M)]
        x=sum(a*3**(M-1-j) for j,a in enumerate(coefficients));B=D*3**M;A=3*x
        U,V,W,Z=A*d,B*s,A*s,2*B*d
        w0=factorial(N)*V**N;v=3*factorial(N)*Z**N
        first=w0*sum((Fraction(U,V)**j/Fraction(factorial(j)) for j in range(N+1)),Fraction(0))
        second=v*sum((Fraction(W,Z)**j/Fraction(factorial(j)) for j in range(N+1)),Fraction(0))
        assert first.denominator==second.denominator==1
        y,z=first.numerator,second.numerator
        assert d and w0 and v and w0*z<=v*y and d*(v*y)<=d*(w0*z)+18*(w0*v)
        unequal+=w0*z!=v*y
    assert unequal==5


def test_unique_owned_endpoints_and_changed_archive_are_checked():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r=p.definition_registry();seen={}
    for archive in p.ARCHIVES:
        rows=p.read_mixed_archive(archive)
        for name,source in p.ENDPOINT_SOURCES.items():
            if p.ENDPOINT_OWNERS[name]!=archive['case']:continue
            target=encode_formula(parse_named(source,registry=r));matches=[i for i,row in enumerate(rows) if row[1]==target]
            assert len(matches)==1 and rows[matches[0]][3];seen[name]=(archive['case'],matches[0])
    assert len(seen)==9 and seen['arguments']==('AP093',68) and seen['continuity']==('AP007',163)
    assert seen['mul_le_cancel']==('AP008',36) and seen['supplied']==('AP004',151)
    with pytest.raises(ValueError):p.read_mixed_archive(dict(p.ARGUMENT_ARCHIVE,raw_sha256='0'*64))


def test_current_source_closure_and_historical_AP093_case_are_bound():
    from test_sqrt2_power_half_log_root_uniform import _assert_case_source_binding
    pins=p.exp_log_root_half_transport_source_pins()
    assert all(pins[name]==pin for name,pin in p.log_root_half_argument_source_pins().items())
    old=p.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-log-root-half-argument-v1'
    _assert_case_source_binding(json.loads((old/'report.json').read_bytes()),old)
    with patch.dict(p.ARGUMENT_ARCHIVE,sha256='0'*64),pytest.raises(ValueError):p.exp_log_root_half_transport_source_pins()


def checked_bundle():
    from check_sqrt2_power_fresh_lean import exact_bundle
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from peano_lab.library.proof_bundle import decode_proof_bundle
    from test_sqrt2_power_half_log_root_uniform import _assert_case_source_binding
    raw,info=exact_bundle(FOLDER);report=json.loads((FOLDER/'report.json').read_bytes())
    assert info['case']=='AP094' and info['bundle_sha256']==BUNDLE_SHA256 and info['nodes']==NODE_COUNT
    _assert_case_source_binding(report,FOLDER)
    bundle,target=decode_proof_bundle(raw.decode(),limits=BinaryDAGLimits().bundle_limits())
    assert target==p.frozen_exp_log_root_half_transport_target() and bundle.root==NODE_COUNT-1
    return bundle,json.loads(raw)


def test_original_AP093_prefix_and_three_native_bodies_are_exact():
    from peano_lab.library.proof_bundle import encode_proof
    bundle,tree=checked_bundle()
    assert tree[3][:69]==p.read_mixed_archive(p.ARGUMENT_ARCHIVE)
    assert tuple(node.node_id for node in bundle.nodes)==tuple(range(NODE_COUNT))
    assert all(all(d<node.node_id for d in node.dependencies) for node in bundle.nodes)
    factories=p.factories(p.definition_registry())
    for index,name in ((211,'eighteen'),(212,'arithmetic'),(213,'AP094')):
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


def test_fresh_Lean_verifies_identical_bytes_and_both_negative_controls():
    from check_sqrt2_power_fresh_lean import MODULES,AUDIT_OUTPUT
    report=json.loads((LEAN_FOLDER/'report.json').read_bytes())
    assert report['status']=='fresh_lean_checked' and tuple(r['module'] for r in report['compilation'])==MODULES
    assert report['axiom_audit']['stdout']==AUDIT_OUTPUT and len(report['checks'])==1
    row=report['checks'][0]
    assert row['case']=='AP094' and row['independent_lean_checked'] is True and row['bundle_sha256']==BUNDLE_SHA256
    assert row['target_ast_sha256']==p.TARGET_SHA256 and row['report_sha256']==sha256((FOLDER/'report.json').read_bytes()).hexdigest()
    assert len(report['negative_controls'])==2 and all(r['rejected'] for r in report['negative_controls'])


def test_frozen_solver_leaf_is_not_mistaken_for_HA_or_Lean_proof_authority():
    from observe_sqrt2_power_tail_steps import target_for
    _,digest,_=target_for('AP094-arithmetic')
    report=json.loads((p.ROOT/'research/arithmetic-library/sqrt2-power/observations/exp-log-root-half-transport-solvers-v1.json').read_bytes())
    assert report['case']=='AP094-arithmetic' and report['target_ast_sha256']==digest==p.HELPER_TARGET_SHA256['arithmetic']
    assert report['authority']=='untrusted_classical_hints_only' and report['solver_proofs_reconstructed']==0
    assert report['original_HA_checked'] is False and report['independent_lean_checked'] is False
    assert report['budget']['measured_child_cpu_seconds']<=report['budget']['cpu_hard_limit_reserved_seconds']<=18
    assert [o['observation']['capability']['status'] for o in report['observations']]==['available','available','unavailable']
    with patch.dict(p.HELPER_TARGET_SHA256,arithmetic='0'*64),pytest.raises(ValueError):target_for('AP094-arithmetic')
