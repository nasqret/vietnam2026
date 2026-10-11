"""AP095: original precision and requested error, with actual proof replay."""
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from math import factorial,isqrt,lcm
from unittest.mock import patch

import pytest
import sqrt2_power_requested_half_transport as p

BUNDLE_SHA256='07d48fca1276244b05d415dc9c46a505b1fd357dc8178abea55a624e7347ff7e'
BODY_HASHES={'constant_bound':'8a85f32a4f9dd943aba616ca3a33b534da82731b85563c5567f7a1ec7f64e24a',
    'AP095':'ae587c19b63b2a1e4959ce160c69a6fb88a20e28f86785b94b8cfdd526f5cd79'}
NODE_COUNT=231
FOLDER=p.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-requested-half-transport-v1'
LEAN_FOLDER=p.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-requested-half-transport-lean-wmi-v1'


def test_original_shift_degree_and_independent_heads_are_explicit():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    n,premises,out=strip_target(p.frozen_requested_half_transport_target())
    names=tuple(reversed(p.PARAMETERS));r=p.definition_registry()
    assert n==20 and len(premises)==6 and premises==[parse_named(s,names,r) for s in p.PREMISES]
    assert type(out) is Exists and out==parse_named('exists r. '+p._and(p.PARTS),names,r)
    assert len(p.PARTS)==7 and p.PREMISES[1].startswith('NatSqrt2ExpSample(n+8,')
    assert p.PREMISES[3].endswith(',jb,jc,(n+8)+2)') and p.PREMISES[-1]=='Sum(jb,jc,S((n+8)+2),z)'
    assert p.PREMISES[2]=='~v=0' and p.PREMISES[4]=='BetaAt(jb,jc,0,v)'


def test_exact_definition_DAG_adds_no_accuracy_or_analytic_assumption():
    from sqrt2_power_supplied_exp_sample import definition_registry
    r=p.definition_registry();assert r==definition_registry() and len(r)==23
    seen=set();ids=set()
    for name,spec in r.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    contract=p.source_contract()
    assert contract['new_definition_ids']==[] and contract['new_induction_count']==0
    assert contract['actual_AP015_scale_cancellation_body_replayed'] is True
    assert not any(contract[k] for k in ('original_approximation_program_changed','analytic_identity_claimed',
        'analytic_limit_claimed','closes_IR072'))


def test_target_mutations_cannot_change_precision_heads_or_requested_error():
    source=p.NAMED_SOURCE
    for wrong in (source.replace('~D=0 -> ',''),source.replace('~v=0 -> ',''),
            source.replace('n+8','n+7'),source.replace(',jb,jc,(n+8)+2)',',jb,jc,(n+8)+3)'),
            source.replace('S((n+8)+2),z','S((n+8)+1),z'),source.replace(p.Z,'((D*p)*d)'),
            source.replace('BetaAt(jb,jc,0,v)','BetaAt(jb,jc,0,w0)'),
            source.replace('+(w0*v)','+0'),source.replace('Pow(2,n,r)','Pow(2,n+1,r)'),
            source.replace('Le(w0*z,v*y)','Le(v*y,w0*z)')):
        assert wrong!=source
        with patch.object(p,'NAMED_SOURCE',wrong),pytest.raises(ValueError):p.frozen_requested_half_transport_target()


def test_reused_scale_arithmetic_requires_the_factor_threshold_and_nonzero_guard():
    checked=0
    for r,shift,x,y,h in product(range(4),(18,19,29,256),range(5),range(5),range(4)):
        d=r*shift
        if d*x<=d*y+18*h:
            assert r*x<=r*y+h;checked+=1
    assert checked>1000
    # A shift below the required 18 is insufficient for these arithmetic premises.
    d=r=shift=1;x=18;y=0;h=1
    assert d==r*shift and d*x<=d*y+18*h and not r*x<=r*y+h
    # Omitting either positivity or the actual factor equality is unsound.
    for d,r,shift in ((0,1,0),(0,1,18)):
        x,y,h=1,0,0
        assert d*x<=d*y+18*h and not r*x<=r*y+h


def test_actual_original_samples_meet_the_requested_bound_with_unequal_heads():
    for n in range(4):
        k=n+8;r=2**n;d=2**k;s=isqrt(2*d*d);D=lcm(*range(1,2*k+1));M=2*k+1;N=k+2
        coefficients=[2*D//j if j%2 else 0 for j in range(M)]
        x=sum(a*3**(M-1-j) for j,a in enumerate(coefficients));B=D*3**M;A=3*x
        U,V,W,Z=A*d,B*s,A*s,2*B*d
        w0=factorial(N)*V**N;v=3*factorial(N)*Z**N
        first=w0*sum((Fraction(U,V)**j/Fraction(factorial(j)) for j in range(N+1)),Fraction(0))
        second=v*sum((Fraction(W,Z)**j/Fraction(factorial(j)) for j in range(N+1)),Fraction(0))
        assert first.denominator==second.denominator==1
        y,z=first.numerator,second.numerator
        assert d==r*2**8 and r and w0 and v and w0!=v
        assert w0*z<v*y and r*(v*y)<=r*(w0*z)+w0*v


def test_owned_endpoints_reuse_the_actual_AP015_arithmetic_body():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r=p.definition_registry();seen={}
    for archive in p.ARCHIVES:
        rows=p.read_mixed_archive(archive)
        for name,source in p.ENDPOINT_SOURCES.items():
            if p.ENDPOINT_OWNERS[name]!=archive['case']:continue
            target=encode_formula(parse_named(source,registry=r));matches=[i for i,row in enumerate(rows) if row[1]==target]
            assert len(matches)==1 and rows[matches[0]][3];seen[name]=(archive['case'],matches[0])
    assert len(seen)==8 and seen['transport']==('AP094',213)
    assert seen['scale_arithmetic']==('AP015',301) and seen['threshold']==('AP015',300)
    assert p.json_hash(encode_formula(parse_named(p.ENDPOINT_SOURCES['scale_arithmetic'],registry=r)))==p.source_contract()['reused_scale_arithmetic_ast_sha256']
    with pytest.raises(ValueError):p.read_mixed_archive(dict(p.TRANSPORT_ARCHIVE,raw_sha256='0'*64))


def test_current_source_closure_and_historical_AP094_case_are_bound():
    from test_sqrt2_power_half_log_root_uniform import _assert_case_source_binding
    pins=p.requested_half_transport_source_pins()
    assert all(pins[name]==pin for name,pin in p.exp_log_root_half_transport_source_pins().items())
    assert all(pins[name]==pin for name,pin in p.approximation_record_error_source_pins().items())
    old=p.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-exp-log-root-half-transport-v1'
    _assert_case_source_binding(json.loads((old/'report.json').read_bytes()),old)
    with patch.dict(p.TRANSPORT_ARCHIVE,sha256='0'*64),pytest.raises(ValueError):p.requested_half_transport_source_pins()


def checked_bundle():
    from check_sqrt2_power_fresh_lean import exact_bundle
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from peano_lab.library.proof_bundle import decode_proof_bundle
    from test_sqrt2_power_half_log_root_uniform import _assert_case_source_binding
    raw,info=exact_bundle(FOLDER);report=json.loads((FOLDER/'report.json').read_bytes())
    assert info['case']=='AP095' and info['bundle_sha256']==BUNDLE_SHA256 and info['nodes']==NODE_COUNT
    _assert_case_source_binding(report,FOLDER)
    bundle,target=decode_proof_bundle(raw.decode(),limits=BinaryDAGLimits().bundle_limits())
    assert target==p.frozen_requested_half_transport_target() and bundle.root==NODE_COUNT-1
    return bundle,json.loads(raw)


def test_actual_AP094_prefix_reused_scale_body_and_new_bodies_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_proof,encode_formula
    bundle,tree=checked_bundle();r=p.definition_registry()
    assert tree[3][:214]==p.read_mixed_archive(p.TRANSPORT_ARCHIVE)
    assert tuple(node.node_id for node in bundle.nodes)==tuple(range(NODE_COUNT))
    assert all(all(d<node.node_id for d in node.dependencies) for node in bundle.nodes)
    target=encode_formula(parse_named(p.ENDPOINT_SOURCES['scale_arithmetic'],registry=r))
    rows=[row for row in tree[3] if row[1]==target]
    assert len(rows)==1 and rows[0][3]==p.read_mixed_archive(p.ERROR_ARCHIVE)[301][3]
    factories=p.factories(r)
    for index,name in ((229,'constant_bound'),(230,'AP095')):
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
    assert row['case']=='AP095' and row['independent_lean_checked'] is True and row['bundle_sha256']==BUNDLE_SHA256
    assert row['target_ast_sha256']==p.TARGET_SHA256 and row['report_sha256']==sha256((FOLDER/'report.json').read_bytes()).hexdigest()
    assert len(report['negative_controls'])==2 and all(r['rejected'] for r in report['negative_controls'])


def test_tiny_ground_proof_is_bounded_deterministic_and_not_a_solver_admission():
    from peano_lab.kernel.terms import parse_term
    contract=p.source_contract()
    assert contract['tiny_ground_evaluator_max_value']==32 and contract['new_solver_arithmetic_leaf'] is None
    assert contract['deterministic_proof_constructor'] and not contract['solver_hints_are_proof_authority']
    for left,right in (('18','29'),('33','33'),('x','x')):
        with pytest.raises(ValueError):p._ground_equal(parse_term(left),parse_term(right))
    with patch.object(p,'TARGET_SHA256','0'*64),pytest.raises(ValueError):p.frozen_requested_half_transport_target()
