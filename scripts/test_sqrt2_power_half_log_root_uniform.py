"""Uniform independent half-log samples compared with an actual dyadic root."""
import ast
import gzip
import json
from hashlib import sha256
from math import isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_half_log_root_uniform as uniform


def test_actual_root_is_chosen_before_all_later_independent_tables():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    registry=uniform.definition_registry();n,premises,out=strip_target(uniform.frozen_half_log_root_uniform_target(_registry=registry))
    assert n==1 and not premises and type(out) is Exists and type(out.body) is Exists
    body=out.body.body;names=('s','r','n')
    assert body.left==parse_named('Pow(2,n,r)',names,registry)
    assert body.right.left==parse_named('~r=0',names,registry)
    assert body.right.right.left==parse_named('DyadicSqrt2(n,r,s)',names,registry)
    assert body.right.right.right==parse_named(uniform.UNIFORM_SOURCE,names,registry)
    k,guards,conclusion=strip_target(body.right.right.right)
    context=tuple(reversed(uniform.FINE_PARAMETERS))+names
    assert k==11 and len(guards)==7 and guards==[parse_named(p,context,registry) for p in uniform.FINE_PREMISES]
    assert conclusion==parse_named(uniform.FINE_CONCLUSION,context,registry)
    assert not any('Le(' in p for p in uniform.FINE_PREMISES)
    c=uniform.source_contract()
    assert c['actual_reference_and_dyadic_root_chosen_before_all_later_independent_tables'] is True
    assert c['upper_error_components']==[7,1]
    assert c['analytic_half_log_sqrt2_identity_claimed'] is c['analytic_limit_claimed'] is c['closes_IR072'] is False


def test_nineteen_exact_definitions_retain_all_existing_metadata_and_dependencies():
    registry=uniform.definition_registry();original=uniform.recursive_definition_registry_for_audit();seen=set();ids=set()
    assert len(registry)==19 and dict(registry)==dict(original)
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert {'FloorSqrt','DyadicSqrt2','NatExpWeightTable','Factorial'}<=seen
    assert 'IRatLe' not in seen and uniform.source_contract()['new_definition_ids']==[]


def test_changed_root_quantifier_half_argument_or_error_is_rejected():
    source=uniform.NAMED_SOURCE;registry=uniform.definition_registry()
    for changed in (source.replace('exists r s.','forall r. exists s.'),source.replace('exists r s.','exists r. forall s.'),
                    source.replace('DyadicSqrt2(n,r,s)','DyadicSqrt2(n,s,r)'),source.replace('18*r','18'),
                    source.replace('NatAtanhPrefix(e,','NatAtanhPrefix(2*e,'),
                    source.replace('NatScaledExpRecurrence(2*(e*q),','NatScaledExpRecurrence(e*q,'),
                    source.replace('(S(S(S(18*r))))+N','(S(S(18*r)))+N'),source.replace('s*b+8*b','s*b+7*b')):
        assert changed!=source
        with patch.object(uniform,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            uniform.frozen_half_log_root_uniform_target(_registry=registry)


def _premises(r,s,h,u,b,v):
    return (r*(u*r)<=r*(s*h)+7*(h*r) and r*(s*h)<=r*(u*r)+h*r
        and b*u<=h*v and r*(h*v)<=r*(b*u)+h*b)


def test_arithmetic_models_require_both_positive_factors_and_the_eighth_allowance():
    examples=0;strict=0;zero_fine=0;unequal=0
    for r in range(1,6):
        for s in range(5):
            for h in range(1,4):
                for u in range(12):
                    for b in range(4):
                        for v in range(16):
                            if not _premises(r,s,h,u,b,v):continue
                            assert r*v<=s*b+8*b and s*b<=r*v+b
                            assert max(r*h*v,r*b*u+h*b).bit_length()<=128
                            examples+=1;strict+=h*v>b*u;zero_fine+=b==0;unequal+=h!=b
    assert examples>1000 and strict and zero_fine and unequal
    assert _premises(0,2,1,0,1,0) and not 2<=0+1  # r cannot be cancelled when zero.
    assert _premises(1,3,0,0,1,0) and not 3<=0+1  # Nor can h.
    assert _premises(1,1,1,8,1,9) and 9<=1+8 and not 9<=1+7
    # These are finite arithmetic-helper models, not evaluations of the
    # complete M=18*2^n+2 half-exponential tables.


def test_actual_dyadic_roots_and_exact_reference_restriction_indices():
    examples=0
    for n in range(9):
        r=2**n;s=isqrt(2*r*r);M=18*r+2;H=(M+1)+M
        assert r>0 and s*s<=2*r*r<(s+1)*(s+1)
        assert (M+1)+M==H and M<=H
        for l in range(3):
            for N in range(3):
                assert M+l>=M and M+1+N>M
                assert max(2*r*r,(s+1)*(s+1),H,M+1+N).bit_length()<=128
                examples+=1
    assert examples==81
    assert len(uniform.REFERENCE_OUTPUTS)==len(set(uniform.REFERENCE_OUTPUTS))==16
    assert not set(uniform.FINE_PARAMETERS)&set(uniform.REFERENCE_OUTPUTS)


def test_thirteen_exact_endpoints_have_actual_unambiguous_archive_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=uniform.definition_registry();found={}
    for pin in uniform.ARCHIVES:
        rows=uniform.read_mixed_archive(pin)
        for name,source in uniform.ENDPOINT_SOURCES.items():
            if uniform.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==13 and found['reference']==('AP050',559) and found['refinement']==('AP088',239)
    assert found['restrict']==('CV101',186) and found['power_exists']==('AP010',110)
    with pytest.raises(ValueError):uniform.read_mixed_archive(dict(uniform.REFERENCE_ARCHIVE,bundle_sha256='0'*64))


def test_optimized_inputs_match_recursive_source_closure_and_reject_mutations():
    from copy import deepcopy
    current=uniform.half_log_root_uniform_source_pins();recursive=uniform.recursive_source_pins_for_audit()
    assert {name:pin for name,pin in current.items() if name!=uniform.INPUT_SNAPSHOT}==recursive
    assert len(current)==354
    for pin in uniform.ARCHIVES:assert current[pin['path']]['sha256']==pin['sha256']
    with patch.object(uniform,'INPUT_SNAPSHOT_SHA256','0'*64),pytest.raises(ValueError):uniform.definition_registry()
    snapshot=deepcopy(uniform._input_snapshot());snapshot['definitions'][0]['template_ast_sha256']='0'*64
    with patch.object(uniform,'_input_snapshot',return_value=snapshot),pytest.raises(ValueError):uniform.definition_registry()


def test_solver_observation_precedes_native_factories_with_unchanged_frozen_contract():
    from observe_sqrt2_power_tail_steps import target_for
    from sqrt2_power_definitions import parse_named
    target,digest,_=target_for('AP089-arithmetic')
    assert target==parse_named(uniform.HELPER_SOURCES['arithmetic'],registry=uniform.definition_registry())
    assert digest==uniform.HELPER_TARGET_SHA256['arithmetic']
    base=uniform.ROOT/'research/arithmetic-library/sqrt2-power/observations'
    observed=json.loads((base/'half-log-root-uniform-solvers-v1.json').read_bytes())
    name='scripts/sqrt2_power_half_log_root_uniform.py';pin=observed['producer_source_pins'][name]
    with gzip.open(base/'half-log-root-uniform-preconstruction-source-v1.py.gz','rb') as f:old=f.read(pin['bytes']+1)
    assert len(old)==pin['bytes'] and sha256(old).hexdigest()==pin['sha256']
    before=ast.parse(old);now=ast.parse((uniform.ROOT/name).read_bytes())
    assert [ast.dump(n,include_attributes=False) for n in before.body]==[ast.dump(n,include_attributes=False) for n in now.body[:len(before.body)]]
    assert [n.name for n in now.body[len(before.body):]]==['_arithmetic','_root','prove_half_log_root_uniform']
    current=uniform.half_log_root_uniform_source_pins()
    assert all(current[key]==value for key,value in observed['producer_source_pins'].items() if key!=name)
    assert observed['target_ast_sha256']==digest and observed['solver_proofs_reconstructed']==0
    assert observed['authority']=='untrusted_classical_hints_only' and observed['original_HA_checked'] is False
    with patch.dict(uniform.HELPER_TARGET_SHA256,arithmetic='0'*64),pytest.raises(ValueError):target_for('AP089-arithmetic')


def _selected_phase_allocation(function,case):
    """Read only the controller's literal, side-effect-free phase grammar."""
    def condition(node):
        assert (isinstance(node,ast.Compare) and isinstance(node.left,ast.Name)
            and node.left.id=='identifier' and len(node.ops)==len(node.comparators)==1
            and isinstance(node.ops[0],ast.Eq) and isinstance(node.comparators[0],ast.Constant)
            and type(node.comparators[0].value) is str)
        return node.comparators[0].value==case
    def value(node):
        if isinstance(node,ast.IfExp):return value(node.body if condition(node.test) else node.orelse)
        result=ast.literal_eval(node)
        assert type(result) is tuple and len(result)==2 and all(type(v) is int and v>0 for v in result)
        return result
    for node in function.body:
        if isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and type(node.value.value) is str:continue
        if isinstance(node,ast.If):
            assert not node.orelse and len(node.body)==1 and isinstance(node.body[0],ast.Return)
            allocation=value(node.body[0].value)
            if condition(node.test):return allocation
        else:
            assert isinstance(node,ast.Return)
            return value(node.value)
    raise AssertionError('missing literal phase allocation')


def _assert_case_source_binding(report,folder):
    """Allow unrelated dispatch additions, never altered proof/checker code.

    The authenticated historical driver is compared by the exact case
    dispatch and unchanged full acceptance functions. A literal-only reader
    checks that this case's phase limits also remain the same. No archived
    Python code is executed and no historical proof receipt is a premise.
    """
    import run_sqrt2_power_wave as wave
    case=report['case'];driver='scripts/run_sqrt2_power_wave.py';current=wave.pins(case)
    assert current.keys()==report['source_pins'].keys()
    assert all(current[name]==pin for name,pin in report['source_pins'].items() if name!=driver)
    pin=report['source_pins'][driver]
    assert report['source_snapshots'][driver]=='sources/'+driver+'.gz'
    with gzip.open(folder/report['source_snapshots'][driver],'rb') as stream:raw=stream.read(pin['bytes']+1)
    assert len(raw)==pin['bytes'] and sha256(raw).hexdigest()==pin['sha256']
    def functions(source):return {n.name:n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
    old=functions(raw);now=functions(wave.SCRIPT.read_bytes())
    for name in ('run','replay','check_forged_root_rejection','generation_phase_limits'):
        assert ast.dump(old[name])==ast.dump(now[name]),name
    def branch(function):
        result=[]
        for node in ast.walk(function):
            if not isinstance(node,ast.If) or not isinstance(node.test,ast.Compare):continue
            test=node.test
            if (isinstance(test.left,ast.Name) and test.left.id=='identifier' and len(test.ops)==len(test.comparators)==1
                    and isinstance(test.ops[0],ast.Eq) and isinstance(test.comparators[0],ast.Constant)
                    and test.comparators[0].value==case):result.append([ast.dump(n) for n in node.body])
        assert len(result)==1
        return result[0]
    for name in ('pins','target_for','worker'):assert branch(old[name])==branch(now[name]),name
    assert _selected_phase_allocation(old['replay_phase_limits'],case)==_selected_phase_allocation(now['replay_phase_limits'],case)


def _current_checked_bundle():
    """Bind the actual v3 bytes to current inputs; hashes are not proof authority.

    V3 already has complete, single-process ordinary HA replay and same-byte
    fresh Lean checking. The regression below rechecks every actual body in
    three disjoint allocator lifetimes, rather than regenerating and replaying
    the entire ancestor graph twice in 25-second test processes. No kernel,
    proof source, positive acceptance gate or resource ceiling is changed.
    """
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from peano_lab.library.proof_bundle import decode_proof_bundle
    folder=uniform.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-half-log-root-uniform-v3'
    report_raw=(folder/'report.json').read_bytes()
    assert sha256(report_raw).hexdigest()=='a5eb1412a33abb5f92bd79dc4085c9a76888e5d6af1a183556c79f3860c04800'
    report=json.loads(report_raw)
    assert report['case']=='AP089' and report['status']=='fresh_ordinary_HA_checked'
    _assert_case_source_binding(report,folder)
    record=report['process_records']['generation']
    assert record['path']=='generation-process.json.gz'
    with gzip.open(folder/record['path'],'rb') as stream:raw=stream.read(8*1024**2+1)
    assert len(raw)<=8*1024**2 and sha256(raw).hexdigest()==record['raw_sha256']
    process=json.loads(raw)
    assert process['reason']=='exited' and process['returncode']==0 and process['output_truncated'] is False
    assert sha256(process['stdout'].encode()).hexdigest()==process['stdout_sha256']
    producer=json.loads(process['stdout'])
    assert producer['case']=='AP089' and producer['status']=='native_generated'
    assert producer['source_pins']==report['source_pins']
    assert producer['target_ast_sha256']==uniform.TARGET_SHA256
    payload=producer['bundle']
    assert sha256(payload.encode()).hexdigest()==producer['bundle_sha256']=='40a9356ff0ed241d51a10a9948e73f850ff7b8cd979cb9ca1531a692fa238b49'
    bundle,target=decode_proof_bundle(payload,limits=BinaryDAGLimits().bundle_limits())
    assert target==uniform.frozen_half_log_root_uniform_target()
    assert len(bundle.nodes)==583 and bundle.root==582
    assert tuple(node.node_id for node in bundle.nodes)==tuple(range(583))
    return bundle,producer['diagnostics']


def test_native_factories_match_checked_bytes_without_new_induction_or_axioms():
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Imp
    from peano_lab.library.proof_bundle import encode_proof
    from sqrt2_power_definitions import parse_named
    bundle,provenance=_current_checked_bundle();registry=uniform.definition_registry()
    assert provenance['new_induction_count']==0 and provenance['new_axioms']==[]
    assert provenance['existing_checked_cut_nodes_introduced']==2
    assert provenance['independent_lean_checked'] is False
    assert provenance['helper_bundle_indices']=={'arithmetic':581,'AP089':582}
    sources=uniform.ENDPOINT_SOURCES|uniform.HELPER_SOURCES
    for name,index,factory in (('arithmetic',581,uniform._arithmetic),('AP089',582,uniform._root)):
        body=uniform.introduce(uniform.Scope(),(),uniform.HELPER_DEPENDENCIES[name],lambda s:factory(s,registry))
        node=bundle.nodes[index]
        assert encode_proof(body)==encode_proof(node.body)
        goal=node.target
        assert tuple(bundle.nodes[d].target for d in node.dependencies)==tuple(
            parse_named(sources[d],registry=registry) for d in uniform.HELPER_DEPENDENCIES[name])
        for dependency in reversed(node.dependencies):goal=Imp(bundle.nodes[dependency].target,goal)
        assert check((),body,goal)
        pending=[encode_proof(body)];cuts=0
        while pending:
            value=pending.pop()
            if type(value) is list:
                assert value[0]!='ind'
                cuts+=value[0]=='cut';pending.extend(v for v in value[1:] if type(v) is list)
        assert cuts==(2 if name=='AP089' else 0)


def _recheck_body_partition(partition):
    """Ordinary empty-context checks, with exactly the full checker's goals.

    Decoding performs the unchanged complete DAG, closure, fuel, size and
    canonical-byte analysis. All three partitions must pass. This does not
    issue a bundle receipt or replace the full positive HA/Lean acceptance.
    """
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Imp
    bundle,_=_current_checked_bundle()
    partitions=tuple(tuple(range(offset,len(bundle.nodes),3)) for offset in range(3))
    assert tuple(map(len,partitions))==(195,194,194)
    assert sorted(i for part in partitions for i in part)==list(range(len(bundle.nodes)))
    for index in partitions[partition]:
        node=bundle.nodes[index];goal=node.target
        assert all(d<index for d in node.dependencies)
        for dependency in reversed(node.dependencies):goal=Imp(bundle.nodes[dependency].target,goal)
        assert check((),node.body,goal),index


def test_every_actual_body_rechecked_partition_zero():
    _recheck_body_partition(0)


def test_every_actual_body_rechecked_partition_one():
    _recheck_body_partition(1)


def test_every_actual_body_rechecked_partition_two():
    _recheck_body_partition(2)


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    bundle,_=_current_checked_bundle()
    with pytest.raises(ProofBundleError):check_proof_bundle(bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(bundle)
