"""Actual finite tails for arbitrary natural bounds on rational arguments."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_large_argument_tail as tail


def test_exact_tail_statement_retains_slice_ratio_head_and_sum():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    registry=tail.definition_registry();target=tail.frozen_exp_large_argument_tail_target(_registry=registry)
    n,premises,conclusion=strip_target(target)
    assert n==7 and len(premises)==4 and type(conclusion) is Exists
    assert len(tail.canonical(encode_formula(target)))==4325
    for _ in tail.OUTPUTS:assert type(conclusion) is Exists;conclusion=conclusion.body
    fields=[]
    for _ in range(5):assert type(conclusion) is And;fields.append(conclusion.left);conclusion=conclusion.right
    fields.append(conclusion);names=tuple(reversed(tail.PARAMETERS+tail.OUTPUTS))
    assert fields==[parse_named(part,names,registry) for part in tail.PARTS]
    c=tail.source_contract();assert c['actual_head_and_sum_constructed'] is True
    assert c['infinite_tail_or_exponential_claimed'] is c['closes_IR072'] is False


def test_seven_existing_definitions_have_the_exact_dependency_dag():
    registry=tail.definition_registry();source=tail.source_registry();seen=set();ids=set()
    assert len(registry)==7
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert tail.source_contract()['new_definition_ids']==[]


def test_changed_tail_cutoff_code_head_horizon_or_bound_is_rejected():
    source=tail.NAMED_SOURCE;registry=tail.definition_registry()
    for changed in (source.replace('Le(2*L,M)','Le(L,M)'),source.replace('tb,tc,M,1,ub,uc','tb,tc,M,2,ub,uc'),
                    source.replace('NatRatioBoundPrefix(ub,uc,1','NatRatioBoundPrefix(ub,uc,2'),
                    source.replace('BetaAt(ub,uc,0,a)','BetaAt(ub,uc,1,a)'),source.replace('tb,tc,M+N','tb,tc,N'),
                    source.replace('Le(s,2*a)','Le(s,a)')):
        assert changed!=source
        with patch.object(tail,'NAMED_SOURCE',changed),pytest.raises(ValueError):tail.frozen_exp_large_argument_tail_target(_registry=registry)


def test_exact_finite_exponential_models_include_zero_and_large_arguments():
    from fractions import Fraction
    from math import factorial
    examples=0
    for d in (1,2,3):
        for L in range(4):
            for x in range(L*d+1):
                for M in (2*L,2*L+1):
                    for N in (0,2,5):
                        values=[Fraction(x,d)**j/factorial(j) for j in range(M+N+1)]
                        shifted=values[M:];assert len(shifted)==N+1
                        assert all(2*shifted[j+1]<=shifted[j] for j in range(N))
                        assert sum(shifted)<=2*shifted[0]
                        examples+=1
    assert examples>100


def test_every_named_endpoint_resolves_to_one_actual_owned_body():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=tail.definition_registry();found={}
    for pin in tail.ARCHIVES:
        rows=tail.read_mixed_archive(pin)
        for name,source in tail.ENDPOINT_SOURCES.items():
            if tail.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==14 and found['ratio']==('AP051',22) and found['sum_ratio']==('CV068',111)
    with pytest.raises(ValueError):tail.read_mixed_archive(dict(tail.STEP_ARCHIVE,sha256='0'*64))


def test_source_and_archive_bytes_are_bound():
    pins=tail.exp_large_argument_tail_source_pins();assert len(pins)==343
    for pin in tail.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']


def test_complete_actual_tail_certificate_without_new_induction():
    result=tail.prove_exp_large_argument_tail()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=tail.prove_exp_large_argument_tail()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
