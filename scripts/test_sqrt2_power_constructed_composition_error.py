"""One constructed normalized finite composition has both rational errors."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_constructed_composition_error as composition


CHECKED_ARCHIVE = dict(case="CV085",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-constructed-composition-error-v3/generation-process.json.gz",
    bytes=164608,sha256="ab70934fe3c50e6066221def46792f7e562a8c36f73f6ccfeccbb870895254eb",
    raw_bytes=4445230,raw_sha256="2478e36cc37c7a009816086b73be5922ffb203f7e9ac31655139dda3e3ae3e5c",
    bundle_bytes=2727157,bundle_sha256="c2e9f924a90d6c5c2580db4e5dc7d18a89a02f6936f3c0dff0ebc0d566b2d833",
    nodes=435,root=434,target_ast_sha256="390079559204a44746d65722e27b386315e6b9830542df520c3ed5acd50b4d58")


def test_exact_unconditional_construction_and_exported_fields():
    from sqrt2_power_native import strip_target
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=composition.frozen_constructed_composition_error_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==1 and not premises and type(conclusion) is Exists
    assert len(composition.OUTPUTS)==len(set(composition.OUTPUTS))==20
    assert len(composition.PARTS)==26
    assert len(composition.canonical(encode_formula(target)))==27128
    for _ in composition.OUTPUTS:
        assert type(conclusion) is Exists
        conclusion=conclusion.body
    fields=[]
    for _ in range(25):
        assert type(conclusion) is And
        fields.append(conclusion.left);conclusion=conclusion.right
    fields.append(conclusion)
    names=tuple(reversed(("K",)+composition.OUTPUTS));registry=composition.definition_registry()
    assert fields==[parse_named(p,names,registry) for p in composition.PARTS]
    c=composition.source_contract()
    assert c["same_actual_input_and_factorial_weights_for_all_parts"] is c["all_rational_denominators_proved_nonzero"] is True
    assert c["actual_input_value_scaling_powers_row_products_and_sum_constructed"] is True
    assert c["geometric_pattern_or_tail_bound_assumed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_existing_definition_DAG_no_assumed_errors_or_new_definitions():
    from sqrt2_power_same_table_composition import definition_registry
    assert composition.definition_registry()==definition_registry()
    assert composition.source_contract()["new_definition_ids"]==[]
    assert composition.source_contract()["definition_admissions"]==composition.source_contract()["IR_parents_closed"]==0
    assert composition.source_contract()["checked_construction_and_evaluation_stages_separated"] is True


def test_changed_same_table_normalization_power_or_errors_are_rejected():
    original=composition.NAMED_SOURCE
    for source in (original.replace("BetaAt(wb,wc,0,z)","BetaAt(wc,wb,0,z)"),
                   original.replace("z=fn*pn","z=fn+pn"),
                   original.replace("Pow(3,k,p3)","Pow(3,S k,p3)"),
                   original.replace("IRatLe(es,0,z*ev,2*ep+9*a2,0,ep)","IRatLe(es,0,ev,2*ep+9*a2,0,ep)"),
                   original.replace("IRatLe(2,0,1,es*p3+z*ev,0,(z*ev)*p3)","IRatLe(3,0,1,es*p3+z*ev,0,(z*ev)*p3)")):
        assert source!=original
        with patch.object(composition,"NAMED_SOURCE",source),pytest.raises(ValueError):
            composition.frozen_constructed_composition_error_target()


def test_owned_actual_component_bodies_and_pinned_stage_formulas():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=composition.definition_registry();found=set()
    for pin in composition.ARCHIVES:
        rows=composition.read_mixed_archive(pin)
        for name,source in composition.ENDPOINT_SOURCES.items():
            if composition.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            composition.read_mixed_archive(altered)
    assert found==composition.ENDPOINT_SOURCES.keys()
    for name,source in composition.HELPER_SOURCES.items():
        assert composition.json_hash(encode_formula(parse_named(source,registry=registry)))==composition.HELPER_TARGET_SHA256[name]
    assert composition.source_contract()["intermediate_CV080_root_replayed"] is False
    assert composition.source_contract()["actual_reachable_component_bodies_fully_replayed"] is True


def test_finite_model_same_weighted_sum_and_both_rational_bounds():
    from fractions import Fraction
    from math import factorial,lcm
    def horner(A):
        value=0
        for a in A:
            value=3*value+a
        return value
    def conv(A,B,H):
        return [sum(A[j]*B[i-j] for j in range(len(A)) if 0<=i-j<len(B)) for i in range(H)]
    for N in range(2,6):
        for scale in (1,2,5):
            k=N-1;d=scale*lcm(*range(1,N,2));A=[2*d//i if i%2 else 0 for i in range(N)]
            W=[factorial(N)//factorial(j)*d**(N-j) for j in range(N+1)]
            z=W[0];J=(N+1)*N;H=J+1;x=horner(A);ep=3**N;ev=3**J
            rows=[];current=[1]+[0]*J
            for _ in range(N+1):
                rows.append(current);current=conv(A,current,H)
            values=[horner(row) for row in rows];terms=[W[j]*values[j] for j in range(N+1)]
            s=sum(terms);p3=3**k;a2=2**N
            assert all(ep**j*values[j]==ev*3**j*x**j for j in range(N+1))
            assert all((W[j]*factorial(j))*d**j==z for j in range(N+1))
            assert min(d,z,ep,ev,p3,z*ev,z*ev*p3)>0
            assert Fraction(s,z*ev)==sum((Fraction(3*x,d*ep)**j/Fraction(factorial(j)) for j in range(N+1)),Fraction(0))
            assert Fraction(s,z*ev)<=Fraction(2*ep+9*a2,ep)
            assert 2<=Fraction(s*p3+z*ev,z*ev*p3)


def _archived_bundle():
    from peano_lab.library.proof_bundle import decode_proof_bundle
    from sqrt2_power_binary_dag import BinaryDAGLimits
    rows=composition.read_mixed_archive(CHECKED_ARCHIVE);root=CHECKED_ARCHIVE["root"]
    limits=BinaryDAGLimits().bundle_limits()
    bundle,target=decode_proof_bundle(composition.canonical(["peano-lab-bundle-v1",root,rows[root][1],rows]).decode()+"\n",limits=limits)
    assert target==composition.frozen_constructed_composition_error_target()
    return bundle,target,limits


def test_full_ordinary_archive_replay_and_failed_observations_retained():
    import json
    from peano_lab.library.proof_bundle import check_proof_bundle
    bundle,target,limits=_archived_bundle();receipt=check_proof_bundle(bundle,target,limits=limits)
    assert receipt.target==target and receipt.node_count==435 and receipt.total_body_nodes==42054
    observations=composition.ROOT/"research/arithmetic-library/sqrt2-power/observations"
    for version in (1,2):
        report=json.loads((observations/f"shared-wave-constructed-composition-error-v{version}/report.json").read_bytes())
        assert report["status"]=="not_checked"
    report=json.loads((observations/"shared-wave-constructed-composition-error-v3/report.json").read_bytes())
    assert report["status"]=="fresh_ordinary_HA_checked"


def test_forged_root_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from run_sqrt2_power_wave import check_forged_root_rejection
    bundle,target,limits=_archived_bundle()
    check_forged_root_rejection(bundle)
    with pytest.raises(ProofBundleError):
        check_proof_bundle(bundle,Bot(),limits=limits)


def test_forged_actual_power_uniqueness_body_is_rejected():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    bundle,target,limits=_archived_bundle()
    ancestor=parse_named(composition.ENDPOINT_SOURCES["power_unique"],registry=composition.definition_registry())
    matches=[n.node_id for n in bundle.nodes if n.target==ancestor];assert len(matches)==1
    forged=replace(bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==matches[0] else n for n in bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,target,limits=limits)
