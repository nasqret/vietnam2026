"""AP091: actual positive witnesses, unchanged same-root order and proof DAG."""
from hashlib import sha256
import json
from math import factorial,lcm
from unittest.mock import patch

import pytest
import sqrt2_power_fixed_half_log_root_witness as fixed

BUNDLE_SHA256='ca771f818bb607d30de80c5bc19a15ee2d05a0932355fc71c7800b0ef096d67b'
BODY_SHA256='5c6256486a737358bac092da81785679a518b47da5f66dd9a76d66f3a99ee175'
NODE_COUNT=586
FOLDER=fixed.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-witness-v1'
LEAN_FOLDER=fixed.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-witness-lean-wmi-v1'


def test_one_actual_root_precedes_every_later_constructed_positive_sample():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    r=fixed.definition_registry();n,premises,out=strip_target(fixed.frozen_fixed_half_log_root_witness_target())
    assert n==1 and not premises and type(out) is Exists and type(out.body) is Exists
    body=out.body.body;names=('s','r','n')
    assert body.left==parse_named('Pow(2,n,r)',names,r)
    assert body.right.left==parse_named('~r=0',names,r)
    assert body.right.right.left==parse_named('DyadicSqrt2(n,r,s)',names,r)
    assert body.right.right.right==parse_named(fixed.LATER_SOURCE,names,r)
    k,guards,witnesses=strip_target(body.right.right.right)
    assert k==1 and guards==[parse_named('Le(S(S(18*r)),k)',('k',)+names,r)]
    count=0
    while type(witnesses) is Exists:count+=1;witnesses=witnesses.body
    assert count==13
    assert witnesses==parse_named(fixed.conjoin(fixed.PARTS),tuple(reversed(fixed.OUTPUTS))+('k',)+names,r)
    assert len(fixed.PARTS)==19 and fixed.PARTS[10]=='~h=0' and fixed.PARTS[16]==fixed.NORMALIZATION
    c=fixed.source_contract()
    assert c['actual_root_chosen_before_arbitrary_later_index'] and c['every_actual_term_factorial_normalization_retained']
    assert not any(c[k] for k in ('root_quotient_accuracy_claimed','analytic_limit_claimed','fixed_approximation_program_changed','closes_IR072'))


def test_definition_DAG_reuses_all_metadata_and_adds_no_new_definition():
    registry=fixed.definition_registry();old=fixed.fixed_registry();witness=fixed.witness_registry();seen=set();ids=set()
    assert len(registry)==21
    assert all(registry[name]==spec for name,spec in old.items())
    identity=('stable_id','name','parameters','template_source','template_formula','conceptual_dependencies')
    assert all(all(getattr(registry[name],key)==getattr(spec,key) for key in identity) for name,spec in witness.items())
    assert {name for name,spec in witness.items() if registry[name]!=spec}=={'Le','Lt'}
    assert set(registry)-set(old)=={'BetaZeroExtend','NatZeroBefore'}
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert fixed.source_contract()['new_definition_ids']==[]


def test_mutated_root_order_half_argument_positivity_and_bounds_are_rejected():
    source=fixed.NAMED_SOURCE;r=fixed.definition_registry()
    for changed in (source.replace('exists r s.','forall r. exists s.'),source.replace('DyadicSqrt2(n,r,s)','DyadicSqrt2(n,s,r)'),
            source.replace('18*r','18'),source.replace('S(2*k)','S k'),source.replace('2*(d*p)','d*p'),
            source.replace('~h=0','h=0'),source.replace('h=f*q','h=f+q'),
            source.replace('Pow(3*x,j,xj)','Pow(x,j,xj)'),source.replace('s*h+8*h','s*h+7*h')):
        assert changed!=source
        with patch.object(fixed,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            fixed.frozen_fixed_half_log_root_witness_target(_registry=r)


def test_small_actual_half_log_factorial_terms_are_positive_and_normalized():
    examples=terms_count=recurrences=0
    for k in range(3):
        for scale in (1,2):
            d=scale*lcm(*(j for j in range(1,2*k+1,2)));x=0
            for j in range(2*k+1):x=3*x+(0 if j%2==0 else 2*d//j)
            p=3**(2*k+1);den=2*(d*p);X=3*x;N=k+2;f=factorial(N);q=den**N;h=f*q
            weights=[f//factorial(j)*den**(N-j) for j in range(N+1)]
            terms=[weights[j]*X**j for j in range(N+1)];y=sum(terms)
            assert d>0 and p>0 and den>0 and h==weights[0]==terms[0] and h>0
            for j,a in enumerate(terms):
                assert (a*factorial(j))*den**j==h*X**j
                assert max((a*factorial(j))*den**j,h*X**j,y).bit_length()<=128
                terms_count+=1
            for j in range(N):
                assert (j+1)*den*terms[j+1]==X*terms[j];recurrences+=1
            examples+=1
    assert (examples,terms_count,recurrences)==(6,24,18)
    # Actual subcomputations only: the full quantified threshold starts at k=20.


def test_eight_dependencies_have_unique_actual_bodies_in_the_AP090_archive():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r=fixed.definition_registry();rows=fixed.read_mixed_archive(fixed.FIXED_ARCHIVE);found={}
    for name,source in fixed.ENDPOINT_SOURCES.items():
        formula=encode_formula(parse_named(source,registry=r));matches=[i for i,row in enumerate(rows) if row[1]==formula]
        assert len(matches)==1 and rows[matches[0]][3];found[name]=matches[0]
    assert len(found)==8 and found['fixed']==584 and set(fixed.ENDPOINT_OWNERS.values())=={'AP090'}
    with pytest.raises(ValueError):fixed.read_mixed_archive(dict(fixed.FIXED_ARCHIVE,raw_sha256='0'*64))


def test_source_closure_binds_both_existing_cones_and_the_exact_parent_bytes():
    current=fixed.fixed_half_log_root_witness_source_pins()
    for inherited in (fixed.fixed_half_log_root_source_pins(),fixed.fixed_log_exp_witness_source_pins()):
        assert all(current[name]==pin for name,pin in inherited.items())
    assert current[fixed.FIXED_ARCHIVE['path']]['sha256']==fixed.FIXED_ARCHIVE['sha256']
    with patch.dict(fixed.FIXED_ARCHIVE,sha256='0'*64),pytest.raises(ValueError):fixed.fixed_half_log_root_witness_source_pins()
    assert not fixed.source_contract()['new_solver_arithmetic_leaf_needed']
    assert fixed.HELPER_SOURCES==fixed.HELPER_TARGET_SHA256=={}


def _checked_bundle():
    from check_sqrt2_power_fresh_lean import exact_bundle
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from peano_lab.library.proof_bundle import decode_proof_bundle
    import run_sqrt2_power_wave as wave
    raw,info=exact_bundle(FOLDER);report=json.loads((FOLDER/'report.json').read_bytes())
    assert info['case']=='AP091' and info['bundle_sha256']==BUNDLE_SHA256 and info['nodes']==NODE_COUNT
    assert report['source_pins']==wave.pins('AP091')
    bundle,target=decode_proof_bundle(raw.decode(),limits=BinaryDAGLimits().bundle_limits())
    assert target==fixed.frozen_fixed_half_log_root_witness_target() and bundle.root==NODE_COUNT-1
    assert tuple(n.node_id for n in bundle.nodes)==tuple(range(NODE_COUNT))
    return bundle,json.loads(raw)


def test_all_parent_rows_are_preserved_and_the_added_DAG_is_topological():
    bundle,tree=_checked_bundle()
    assert tree[3][:-1]==fixed.read_mixed_archive(fixed.FIXED_ARCHIVE)
    assert all(all(d<node.node_id for d in node.dependencies) for node in bundle.nodes)
    assert 584 in bundle.nodes[-1].dependencies and len(bundle.nodes[-1].dependencies)==8


def test_native_body_matches_actual_certificate_with_no_induction_or_axiom():
    from peano_lab.library.proof_bundle import encode_proof
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Imp
    body=fixed.introduce(fixed.Scope(),(),fixed.HELPER_DEPENDENCIES['AP091'],fixed._root)
    bundle,_=_checked_bundle();root=bundle.nodes[-1];encoded=encode_proof(body)
    assert encoded==encode_proof(root.body) and fixed.json_hash(encoded)==BODY_SHA256
    goal=root.target
    for dependency in reversed(root.dependencies):goal=Imp(bundle.nodes[dependency].target,goal)
    assert check((),body,goal)
    pending=[encoded]
    while pending:
        item=pending.pop()
        if type(item) is list:
            assert item[0]!='ind';pending.extend(x for x in item[1:] if type(x) is list)


def _recheck_partition(partition):
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Imp
    bundle,_=_checked_bundle();parts=[list(range(i,len(bundle.nodes),3)) for i in range(3)]
    assert sorted(i for part in parts for i in part)==list(range(len(bundle.nodes)))
    for index in parts[partition]:
        node=bundle.nodes[index];goal=node.target
        for dependency in reversed(node.dependencies):goal=Imp(bundle.nodes[dependency].target,goal)
        assert check((),node.body,goal),index


def test_every_actual_body_rechecked_partition_zero():
    _recheck_partition(0)


def test_every_actual_body_rechecked_partition_one():
    _recheck_partition(1)


def test_every_actual_body_rechecked_partition_two():
    _recheck_partition(2)


def test_false_target_and_forged_root_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    bundle,_=_checked_bundle()
    with pytest.raises(ProofBundleError):check_proof_bundle(bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(bundle)


def test_fresh_Lean_and_both_negative_controls_bind_the_same_actual_bytes():
    from check_sqrt2_power_fresh_lean import MODULES,AUDIT_OUTPUT
    report=json.loads((LEAN_FOLDER/'report.json').read_bytes())
    assert report['status']=='fresh_lean_checked' and tuple(r['module'] for r in report['compilation'])==MODULES
    assert report['axiom_audit']['stdout']==AUDIT_OUTPUT and report['axiom_audit']['returncode']==0
    assert len(report['checks'])==1
    row=report['checks'][0]
    assert row['case']=='AP091' and row['independent_lean_checked'] is True and row['bundle_sha256']==BUNDLE_SHA256
    assert row['target_ast_sha256']==fixed.TARGET_SHA256 and row['report_sha256']==sha256((FOLDER/'report.json').read_bytes()).hexdigest()
    assert len(report['negative_controls'])==2 and all(r['rejected'] for r in report['negative_controls'])
