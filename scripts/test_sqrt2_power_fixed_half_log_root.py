"""AP090: preserve the actual root and computations through index transport."""
import ast
import gzip
import json
from hashlib import sha256
from math import isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_fixed_half_log_root as fixed
from test_sqrt2_power_half_log_root_uniform import _assert_case_source_binding,_selected_phase_allocation

REPORT_SHA256='d97afbf151e451450e0551b8d49e8c0e0f6ac074c43c42d44b716d6f685ebf86'
BUNDLE_SHA256='603a7c00633d251a1f6b4476247eb6e48a8d13d47b47b4dbf75b5eab5747ef8c'
BUNDLE_NODE_COUNT=585


def test_actual_root_precedes_all_later_fixed_schedule_computations():
    from peano_lab.kernel.formulas import Exists
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    registry=fixed.definition_registry();n,premises,out=strip_target(fixed.frozen_fixed_half_log_root_target(_registry=registry))
    assert n==1 and not premises and type(out) is Exists and type(out.body) is Exists
    body=out.body.body;names=('s','r','n')
    assert body.left==parse_named('Pow(2,n,r)',names,registry)
    assert body.right.left==parse_named('~r=0',names,registry)
    assert body.right.right.left==parse_named('DyadicSqrt2(n,r,s)',names,registry)
    assert body.right.right.right==parse_named(fixed.LATER_SOURCE,names,registry)
    m,guards,conclusion=strip_target(body.right.right.right);context=tuple(reversed(fixed.PARAMETERS))+names
    assert m==10 and len(guards)==8 and guards==[parse_named(p,context,registry) for p in fixed.PREMISES]
    assert conclusion==parse_named(fixed.CONCLUSION,context,registry)
    contract=fixed.source_contract()
    assert contract['actual_root_chosen_before_all_later_computations'] is True
    assert contract['fixed_logarithm_prefix_length']=='2*k+1' and contract['fixed_exp_degree']=='k+2'
    assert contract['root_quotient_accuracy_claimed'] is contract['analytic_limit_claimed'] is contract['closes_IR072'] is False


def test_nineteen_existing_definitions_and_all_metadata_are_unchanged():
    import sqrt2_power_half_log_root_uniform as uniform
    registry=fixed.definition_registry();seen=set();ids=set()
    assert len(registry)==19 and dict(registry)==dict(uniform.definition_registry())
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert {'DyadicSqrt2','NatAtanhPrefix','NatHornerValue','NatScaledExpRecurrence','Sum'}<=seen
    assert fixed.source_contract()['new_definition_ids']==[]


def test_changed_quantifiers_schedules_half_argument_and_error_are_rejected():
    source=fixed.NAMED_SOURCE;registry=fixed.definition_registry()
    changes=(source.replace('exists r s.','forall r. exists s.'),source.replace('exists r s.','exists r. forall s.'),
        source.replace('DyadicSqrt2(n,r,s)','DyadicSqrt2(n,s,r)'),source.replace('18*r','18'),
        source.replace('S(2*k)','S k'),source.replace('NatAtanhPrefix(e,','NatAtanhPrefix(2*e,'),
        source.replace('NatScaledExpRecurrence(2*(e*q),','NatScaledExpRecurrence(e*q,'),
        source.replace('eb,ec,S(S k))','eb,ec,S k)'),source.replace('Sum(eb,ec,S(S(S k)),v)','Sum(eb,ec,S(S k),v)'),
        source.replace('s*b+8*b','s*b+7*b'))
    for changed in changes:
        assert changed!=source
        with patch.object(fixed,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            fixed.frozen_fixed_half_log_root_target(_registry=registry)


def test_actual_dyadic_roots_and_both_index_transports_including_zero_gap():
    cases=0;zero_gap=0
    for n in range(9):
        r=2**n;s=isqrt(2*r*r);M=18*r+2
        assert s*s<=2*r*r<(s+1)*(s+1)
        for offset in range(16):
            k=M+offset;l=k+offset+1;N=offset+1
            assert 2*k+1==M+l and k+2==(M+1)+N and k+3==((M+1)+N)+1
            assert k+2!=(M+1)+offset and max(2*r*r,(s+1)*(s+1),M+l).bit_length()<=128
            cases+=1;zero_gap+=offset==0
    assert cases==144 and zero_gap==9
    # These are actual root/index checks, not huge exponential-table examples.
    assert fixed.source_contract()['rational_reading_requires_positive_fine_head'] is True
    assert fixed.source_contract()['zero_fine_head_allowed'] is True


def test_three_exact_endpoints_have_actual_unambiguous_archive_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=fixed.definition_registry();found={}
    for pin in fixed.ARCHIVES:
        rows=fixed.read_mixed_archive(pin)
        for name,source in fixed.ENDPOINT_SOURCES.items():
            if fixed.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found=={'uniform':('AP089',582),'indices':('AP085',511),'le_gap':('AP007',157)}
    with pytest.raises(ValueError):fixed.read_mixed_archive(dict(fixed.UNIFORM_ARCHIVE,bundle_sha256='0'*64))


def test_source_snapshot_matches_recursive_closure_and_rejects_mutations():
    current=fixed.fixed_half_log_root_source_pins();recursive=fixed.recursive_source_pins_for_audit()
    assert {name:pin for name,pin in current.items() if name!=fixed.SOURCE_SNAPSHOT}==recursive
    assert len(current)==fixed.INHERITED_SOURCE_COUNT+2==364
    for archive in fixed.ARCHIVES:assert current[archive['path']]['sha256']==archive['sha256']
    with patch.object(fixed,'SOURCE_SNAPSHOT_SHA256','0'*64),pytest.raises(ValueError):fixed.fixed_half_log_root_source_pins()
    with patch.object(fixed,'_source_snapshot',return_value={'source_pins':{'../escape':{'bytes':1,'sha256':'0'*64}}}),pytest.raises(ValueError):
        fixed.fixed_half_log_root_source_pins()


def test_reuses_exact_proved_solver_observed_indices_without_new_arithmetic_search():
    from observe_sqrt2_power_tail_steps import target_for
    from sqrt2_power_definitions import parse_named
    target,digest,_=target_for('AP085-indices')
    assert target==parse_named(fixed.ENDPOINT_SOURCES['indices'],registry=fixed.definition_registry())
    assert digest==fixed.INDEX_HASHES['indices']=='96382100568fbd357c8677f0cc92d16a6846aa7c11a301f1c0fc9345a1d2af31'
    observed=json.loads((fixed.ROOT/'research/arithmetic-library/sqrt2-power/observations/fixed-log-exp-convergence-solvers-v1.json').read_bytes())
    assert observed['case']=='AP085-indices' and observed['target_ast_sha256']==digest
    assert observed['authority']=='untrusted_classical_hints_only' and observed['solver_proofs_reconstructed']==0
    assert fixed.HELPER_SOURCES==fixed.HELPER_TARGET_SHA256=={}
    assert fixed.HELPER_DEPENDENCIES['AP090']==('uniform','le_gap','indices')
    assert fixed.source_contract()['new_solver_arithmetic_leaf_needed'] is False


def test_case_specific_source_guard_rejects_nonliteral_or_mutated_allocations():
    def function(source):return ast.parse(source).body[0]
    old=function('def replay_phase_limits(identifier):\n    if identifier=="AP089":\n        return (30,40)\n    return (26,40) if identifier=="CV085" else (20,30)')
    added=function('def replay_phase_limits(identifier):\n    if identifier=="AP089":\n        return (30,40)\n    if identifier=="AP090":\n        return (30,40)\n    return (26,40) if identifier=="CV085" else (20,30)')
    assert _selected_phase_allocation(old,'AP089')==_selected_phase_allocation(added,'AP089')==(30,40)
    assert _selected_phase_allocation(old,'AP090')==(20,30) and _selected_phase_allocation(added,'AP090')==(30,40)
    assert _selected_phase_allocation(added,'AP091')==(20,30)
    mutated=function('def replay_phase_limits(identifier):\n    if identifier=="AP089":\n        return (31,40)\n    return (20,30)')
    assert _selected_phase_allocation(mutated,'AP089')!=_selected_phase_allocation(old,'AP089')
    for source in ('def f(identifier):\n    alter_state()\n    return (30,40)',
                   'def f(identifier):\n    return compute_limit(identifier)',
                   'def f(identifier):\n    if unexpected(identifier):\n        return (30,40)\n    return (20,30)',
                   'def f(identifier):\n    return (True,40)'):
        with pytest.raises((AssertionError,ValueError)):_selected_phase_allocation(function(source),'AP090')


def _checked_bundle():
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from peano_lab.library.proof_bundle import decode_proof_bundle
    folder=fixed.ROOT/'research/arithmetic-library/sqrt2-power/observations/shared-wave-fixed-half-log-root-v1'
    raw_report=(folder/'report.json').read_bytes();assert sha256(raw_report).hexdigest()==REPORT_SHA256
    report=json.loads(raw_report)
    assert report['case']=='AP090' and report['status']=='fresh_ordinary_HA_checked'
    _assert_case_source_binding(report,folder)
    record=report['process_records']['generation'];assert record['path']=='generation-process.json.gz'
    with gzip.open(folder/record['path'],'rb') as stream:raw=stream.read(8*1024**2+1)
    assert len(raw)<=8*1024**2 and sha256(raw).hexdigest()==record['raw_sha256']
    process=json.loads(raw);assert process['reason']=='exited' and process['returncode']==0 and process['output_truncated'] is False
    assert sha256(process['stdout'].encode()).hexdigest()==process['stdout_sha256']
    producer=json.loads(process['stdout'])
    assert producer['case']=='AP090' and producer['status']=='native_generated' and producer['source_pins']==report['source_pins']
    assert producer['target_ast_sha256']==fixed.TARGET_SHA256
    assert sha256(producer['bundle'].encode()).hexdigest()==producer['bundle_sha256']==BUNDLE_SHA256
    bundle,target=decode_proof_bundle(producer['bundle'],limits=BinaryDAGLimits().bundle_limits())
    assert target==fixed.frozen_fixed_half_log_root_target() and len(bundle.nodes)==BUNDLE_NODE_COUNT
    assert tuple(node.node_id for node in bundle.nodes)==tuple(range(BUNDLE_NODE_COUNT)) and bundle.root==BUNDLE_NODE_COUNT-1
    return bundle,producer['diagnostics']


def test_native_index_transport_matches_checked_bytes_without_new_induction():
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Imp
    from peano_lab.library.proof_bundle import encode_proof
    from sqrt2_power_definitions import parse_named
    bundle,provenance=_checked_bundle();registry=fixed.definition_registry()
    assert provenance['new_induction_count']==0 and provenance['new_axioms']==[]
    assert provenance['existing_checked_cut_nodes_introduced']==1 and provenance['helper_statement_ast_sha256']=={}
    assert provenance['independent_lean_checked'] is False
    body=fixed.introduce(fixed.Scope(),(),fixed.HELPER_DEPENDENCIES['AP090'],lambda s:fixed._root(s,registry))
    node=bundle.nodes[bundle.root];assert encode_proof(body)==encode_proof(node.body)
    assert tuple(bundle.nodes[d].target for d in node.dependencies)==tuple(
        parse_named(fixed.ENDPOINT_SOURCES[d],registry=registry) for d in fixed.HELPER_DEPENDENCIES['AP090'])
    goal=node.target
    for dependency in reversed(node.dependencies):goal=Imp(bundle.nodes[dependency].target,goal)
    assert check((),body,goal)
    pending=[encode_proof(body)];cuts=0
    while pending:
        value=pending.pop()
        if type(value) is list:
            assert value[0]!='ind'
            cuts+=value[0]=='cut';pending.extend(v for v in value[1:] if type(v) is list)
    assert cuts==1


def _recheck_body_partition(partition):
    # Complete canonical decoding and DAG analysis occurs in every batch.
    # All actual bodies are additionally checked once across these batches,
    # with exactly the ordinary full checker's closed curried goals. These
    # tests never issue a receipt or replace full positive HA/Lean replay.
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Imp
    bundle,_=_checked_bundle();partitions=tuple(tuple(range(i,len(bundle.nodes),3)) for i in range(3))
    assert sorted(i for part in partitions for i in part)==list(range(len(bundle.nodes)))
    assert max(map(len,partitions))-min(map(len,partitions))<=1
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
    bundle,_=_checked_bundle()
    with pytest.raises(ProofBundleError):check_proof_bundle(bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(bundle)
