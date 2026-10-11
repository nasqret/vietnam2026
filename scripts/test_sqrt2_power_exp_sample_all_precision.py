"""All precision increments include equal values with independent encodings."""
from dataclasses import replace
from fractions import Fraction
from itertools import product
from math import factorial,isqrt,lcm
from unittest.mock import patch

import pytest
import sqrt2_power_exp_sample_all_precision as precision


def test_exact_all_precision_contract_includes_zero_increment():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    target=precision.frozen_exp_sample_all_precision_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==32 and len(premises)==4 and type(conclusion) is And
    assert "NatSqrt2ExpSample(k+l," in precision.NAMED_SOURCE
    c=precision.source_contract()
    assert c["all_precision_indices_and_increments_including_zero"] is c["equal_precision_uses_actual_value_independence"] is True
    assert c["uniform_two_sided_error"]=="((9*3)+2)/d"
    assert c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_exact_computation_definition_dag_has_no_added_accuracy_clause():
    from sqrt2_power_exp_sample_uniform_error import definition_registry
    before=definition_registry();after=precision.definition_registry();seen=set();ids=set()
    assert len(after)==23 and dict(before)==dict(after)
    for name,spec in after.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert precision.source_contract()["new_definition_ids"]==[]


def test_target_rejects_lost_zero_case_guard_or_changed_error():
    source=precision.NAMED_SOURCE
    for changed in (source.replace("~D=0 -> ",""),source.replace("~E=0 -> ",""),
                    source.replace("NatSqrt2ExpSample(k+l,","NatSqrt2ExpSample(k+S l,"),
                    source.replace("((9*3)+2)*(w0*v0)","0")):
        assert changed!=source
        with patch.object(precision,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            precision.frozen_exp_sample_all_precision_target()


def test_actual_independence_strict_bound_and_constructive_case_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=precision.definition_registry();found=set()
    for pin in precision.ARCHIVES:
        rows=precision.read_mixed_archive(pin)
        for name,source in precision.ENDPOINT_SOURCES.items():
            if precision.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry));matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            precision.read_mixed_archive(bad)
    assert found==precision.ENDPOINT_SOURCES.keys()


def test_models_zero_and_successor_increments_with_distinct_heads():
    def computation(k,scale):
        M=2*k+1;D=scale*(lcm(*range(1,M,2)) if k else 1);x=0
        for i in range(M):
            x=3*x+(0 if i%2==0 else 2*D//i)
        d=2**k;s=isqrt(2*d*d);p=3**M;U=3*x*d;V=D*p*s;N=k+2
        head=factorial(N)*V**N
        return d,head,sum(head*U**j//(factorial(j)*V**j) for j in range(N+1))
    directions=set();same=0
    for k,l in product(range(6),range(5)):
        d,w0,y=computation(k,1);q,v0,o=computation(k+l,2)
        assert d>0 and w0>0 and v0>0
        assert d*(w0*o)<=d*(v0*y)+29*(w0*v0)
        assert d*(v0*y)<=d*(w0*o)+29*(w0*v0)
        delta=Fraction(o,v0)-Fraction(y,w0)
        assert abs(delta)<=Fraction(29,d)
        if l==0:
            assert v0*y==w0*o and w0!=v0
            same+=1
        directions.add((delta>0)-(delta<0))
    assert directions=={-1,0,1} and same==6
    for d,x,h in product(range(4),repeat=3):
        assert d*x<=d*x+29*h


def test_complete_all_precision_replay_without_new_induction_or_axioms():
    result=precision.prove_exp_sample_all_precision()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_equal_case_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=precision.prove_exp_sample_all_precision();node=result.provenance["helper_bundle_indices"]["equal_bounds"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
