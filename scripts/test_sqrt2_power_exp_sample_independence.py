"""Equal sample values do not require equal normalizing heads or code numbers."""
from dataclasses import replace
from fractions import Fraction
from math import factorial,isqrt,lcm
from unittest.mock import patch

import pytest
import sqrt2_power_exp_sample_independence as independence


def test_exact_rational_output_identity_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=independence.frozen_exp_sample_independence_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==31 and len(premises)==4 and type(conclusion) is And
    assert len(independence.canonical(encode_formula(target)))==31628
    c=independence.source_contract()
    assert c["independent_table_codes_scales_and_output_heads_allowed"] is c["both_output_denominators_proved_nonzero"] is True
    assert c["natural_identity"]=="v0*y=w0*o" and c["exact_rational_output_value_identity"] is True
    assert c["canonical_PR_approximation_algorithm_claim"] is c["analytic_identity_claim"] is c["closes_IR072"] is False


def test_definition_graphs_are_preserved_without_extra_accuracy_clauses():
    from sqrt2_power_exp_sample import definition_registry
    assert independence.definition_registry is definition_registry
    assert independence.source_contract()["new_definition_ids"]==[]
    assert independence.source_contract()["definition_admissions"]==0


def test_missing_scale_wrong_precision_or_output_identity_is_rejected():
    source=independence.NAMED_SOURCE
    for altered in (source.replace("~D=0 -> ",""),source.replace("~E=0 -> ",""),
                    source.replace("NatSqrt2ExpSample(k,e","NatSqrt2ExpSample(S k,e"),
                    source.replace("v0*y=w0*o","w0*y=v0*o"),source.replace("~v0=0","v0=0")):
        assert source!=altered
        with patch.object(independence,"NAMED_SOURCE",altered),pytest.raises(ValueError):
            independence.frozen_exp_sample_independence_target()


def test_all_required_supplied_graph_and_continuity_endpoints_have_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=independence.definition_registry();found=set()
    for pin in independence.ARCHIVES:
        rows=independence.read_mixed_archive(pin)
        for name,source in independence.ENDPOINT_SOURCES.items():
            if independence.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches=[r for r in rows if r[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            independence.read_mixed_archive(altered)
    assert found==independence.ENDPOINT_SOURCES.keys()


def test_independent_positive_scales_change_heads_but_not_rational_values():
    for k in range(7):
        d=2**k;s=isqrt(2*d*d);N=2*k+1;degree=k+2
        common=lcm(*range(1,N,2)) if k else 1
        outputs=[]
        for scale in (1,2,3):
            D=scale*common;x=0
            for i in range(N):
                x=3*x+(0 if i%2==0 else 2*D//i)
            v=D*(3**N)*s;u=3*x*d;head=factorial(degree)*v**degree
            value=sum(((factorial(degree)//factorial(j))*v**(degree-j)*u**j for j in range(degree+1)))
            outputs.append((value,head))
        assert outputs[0][1]!=outputs[1][1]
        for y,w0 in outputs:
            for o,v0 in outputs:
                assert w0>0 and v0>0 and v0*y==w0*o
                assert Fraction(y,w0)==Fraction(o,v0)


def test_complete_output_independence_replay_without_new_induction_or_axioms():
    result=independence.prove_exp_sample_independence()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_zero_gap_continuity_bridge_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=independence.prove_exp_sample_independence();node=result.provenance["helper_bundle_indices"]["same_value"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
