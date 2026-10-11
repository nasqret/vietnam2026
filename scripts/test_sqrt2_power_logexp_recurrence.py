"""Universal recurrence, exact natural table meaning and hostile boundaries."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_logexp_recurrence as recurrence


def test_exact_target_has_recurrence_bound_and_decoding_premises():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Or
    from peano_lab.library.proof_bundle import encode_formula
    target = recurrence.frozen_logexp_recurrence_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==6 and len(premises)==3 and type(conclusion) is Or
    assert recurrence.json_hash(encode_formula(target))==recurrence.TARGET_SHA256
    assert len(recurrence.canonical(encode_formula(target)))==2103
    contract = recurrence.source_contract()
    assert contract["arbitrary_length"] is True
    assert contract["actual_recurrence_required"] is True
    assert contract["positive_D_required"] is False
    assert contract["exp_composition_satisfies_recurrence"] is False
    assert contract["closes_IR072"] is contract["closes_IR080"] is False


def test_definition_dag_does_not_assume_the_solution():
    registry = recurrence.definition_registry()
    assert tuple(registry)==("Le","Lt","BetaAt","NatExpAtanhRecurrence")
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()
    definition = registry["NatExpAtanhRecurrence"]
    assert definition.stable_id=="ND0400" and definition.arity==4
    assert definition.conceptual_dependencies==("BetaAt","Lt")
    assert "w=2*D" not in recurrence.DEFINITION_SOURCE
    assert "v=2*D" not in recurrence.DEFINITION_SOURCE
    assert "Pow" not in recurrence.DEFINITION_SOURCE
    assert "forall k u v w" in recurrence.DEFINITION_SOURCE


def test_mutated_target_or_recurrence_equation_fails_before_proof_generation():
    for name,changed in (
        ("NAMED_SOURCE",recurrence.NAMED_SOURCE.replace("Lt(i,L) -> ","")),
        ("NAMED_SOURCE",recurrence.NAMED_SOURCE.replace("v=2*D","v=3*D")),
        ("DEFINITION_SOURCE",recurrence.DEFINITION_SOURCE.replace("k*u+2*v","k*u+3*v")),
        ("DEFINITION_SOURCE",recurrence.DEFINITION_SOURCE.replace("BetaAt(b,c,1,2*D)","BetaAt(b,c,1,D)")),
    ):
        with patch.object(recurrence,name,changed),pytest.raises(ValueError):
            recurrence.frozen_logexp_recurrence_target()


def test_actual_ancestor_cone_contains_nonzero_cancellation_and_decoding():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    ids,rows = recurrence.inert_recurrence_rows()
    assert len(ids)==29 and len(recurrence.canonical(rows))==34489
    assert recurrence.json_hash(rows)==recurrence.ANCESTOR_ROWS_SHA256
    assert {12,23,65,121,122}<=set(ids)
    registry,table = recurrence.definition_registry(),dict(zip(ids,rows))
    for old,source in recurrence.ENDPOINT_SOURCES.items():
        assert table[old][1]==encode_formula(parse_named(source,registry=registry))


def test_changed_ancestor_hash_or_fabricated_endpoint_is_rejected():
    with patch.object(recurrence,"V28_ARTIFACT_SHA256","0"*64),pytest.raises(ValueError):
        recurrence.inert_recurrence_rows()
    sources = dict(recurrence.ENDPOINT_SOURCES)
    sources[65] = "forall a b c. a*b=a*c -> b=c"
    with patch.object(recurrence,"ENDPOINT_SOURCES",sources),pytest.raises(ValueError):
        recurrence.inert_recurrence_rows()


def test_finite_model_all_indices_boundaries_and_necessary_initial_entry():
    def valid(values,length,D):
        return (values[0]==D and values[1]==2*D and
                all((k+2)*values[k+2]==k*values[k]+2*values[k+1]
                    for k in range(max(0,length-2))))
    for D in range(5):
        for length in range(10):
            values = [D]+[2*D]*max(1,length-1)
            assert valid(values,length,D)
            for index in range(length):
                assert (index==0 and values[index]==D) or (index>0 and values[index]==2*D)
                altered = list(values)
                altered[index] += 1
                assert not valid(altered,length,D)
    # The recurrence alone cannot determine the first positive coefficient.
    missing_first = [1,3,3,3,3]
    assert all((k+2)*missing_first[k+2]==k*missing_first[k]+2*missing_first[k+1] for k in range(3))
    assert not valid(missing_first,5,1)
    # Values outside the finite bound are genuinely unconstrained.
    assert valid([1,2,999],2,1)


def test_guarded_full_induction_replays_actual_bodies_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = recurrence.prove_logexp_recurrence()
    assert result.receipt.target==recurrence.frozen_logexp_recurrence_target()
    assert len(result.bundle.nodes)==31
    assert result.provenance["all_coefficient_indices"] is True
    assert result.provenance["root_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
