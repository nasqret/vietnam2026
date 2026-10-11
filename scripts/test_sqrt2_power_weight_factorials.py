"""Exact factorial interpretation and hostile mixed-archive regression checks."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_weight_factorials as weights


def test_exact_constructed_factorial_target_and_honest_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = weights.frozen_weight_factorials_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==2 and not premises and type(conclusion) is Exists
    assert weights.json_hash(encode_formula(target))==weights.TARGET_SHA256
    assert len(weights.canonical(encode_formula(target)))==8949
    c = weights.source_contract()
    assert c["weights_and_initial_value_constructed"] is True
    assert c["actual_factorial_and_power_values_constructed"] is True
    assert c["all_in_range_weights_interpreted"] is True
    assert c["terminal_normalization_proved"] is True
    assert c["zero_d_allowed"] is c["nonvanishing_keeps_nonzero_d_premise"] is True
    assert c["raw_archive_metadata_is_authority"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_historical_factorial_power_definitions_are_exact_and_hygienic():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = weights.definition_registry()
    assert weights.source_contract()["new_definition_ids"]==[]
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()
    for name,(identifier,digest) in weights.EXISTING_DEFINITIONS.items():
        assert r[name].stable_id==identifier
        assert weights.json_hash(encode_formula(r[name].template_formula))==digest
    names = ("b","c")
    assert parse_named("Factorial(b,c)",names,r)==parse_named(
        "exists u v. Range(u,v,1,b) /\\ Product(u,v,b,c)",names,r)


def test_changed_factorial_identity_or_nonvanishing_boundary_is_rejected():
    for source in (weights.NAMED_SOURCE.replace("w0=f*p","w0=f+p"),
                   weights.NAMED_SOURCE.replace("~d=0 -> ","")):
        assert source!=weights.NAMED_SOURCE
        with patch.object(weights,"NAMED_SOURCE",source),pytest.raises(ValueError):
            weights.frozen_weight_factorials_target()


def test_helpers_and_owned_actual_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = weights.definition_registry()
    assert {name:weights.json_hash(encode_formula(parse_named(source,registry=r)))
        for name,source in weights.HELPER_SOURCES.items()}==weights.HELPER_TARGET_SHA256
    found = set()
    for pin in weights.ARCHIVES:
        rows = weights.read_mixed_archive(pin)
        for name,source in weights.ENDPOINT_SOURCES.items():
            if weights.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==weights.ENDPOINT_SOURCES.keys()


def test_mixed_archive_envelope_forgeries_and_unknown_formats_are_rejected():
    for original in weights.ARCHIVES:
        fields = ("sha256","target_ast_sha256")
        for name in fields:
            changed = dict(original);changed[name] = "0"*64
            with pytest.raises(ValueError):
                weights.read_mixed_archive(changed)
    for change in ({"root":0},{"nodes":214},{"format":"assumed-theorem"},{"bytes":8*1024**2+1}):
        with pytest.raises(ValueError):
            weights.read_mixed_archive(dict(weights.LUCAS_ARCHIVE,**change))


def test_raw_reader_checks_canonical_encoding_and_ordered_dependencies(tmp_path):
    import json
    from hashlib import sha256
    original = json.loads((weights.ROOT/weights.LUCAS_ARCHIVE["path"]).read_bytes())
    path = tmp_path/"changed.json"
    variants = []
    variants.append(weights.canonical(original)+b"\n\n")
    original[3][1][2] = [1]
    variants.append(weights.canonical(original)+b"\n")
    for raw in variants:
        path.write_bytes(raw)
        pin = dict(weights.LUCAS_ARCHIVE,bytes=len(raw),sha256=sha256(raw).hexdigest())
        with pytest.raises(ValueError):
            weights.read_mixed_archive(pin,archive_path=path)


def test_missing_or_unknown_endpoint_owners_are_not_accepted():
    for owners in ({},dict(weights.ENDPOINT_OWNERS,factorial_exists="untrusted-name")):
        with patch.object(weights,"ENDPOINT_OWNERS",owners),pytest.raises(ValueError,match="explicit actual archive owner"):
            weights.prove_weight_factorials()


def test_finite_factorial_model_including_zero_denominator_boundary():
    from math import factorial
    for d in range(5):
        for N in range(9):
            w = [1]*(N+1)
            for j in range(N-1,-1,-1):
                w[j] = ((j+1)*d)*w[j+1]
            assert w[0]==factorial(N)*d**N
            assert all(w[j]*factorial(j)*d**j==w[0] for j in range(N+1))
            assert not d or all(x>0 for x in w)
    assert 0**0==1 and 0**1==0


def test_guarded_proof_replays_factorial_bodies_and_rejects_ancestor_forgery():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = weights.prove_weight_factorials()
    assert result.receipt.target==weights.frozen_weight_factorials_target()
    assert len(result.bundle.nodes)==130
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==6558
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    assert result.provenance["endpoint_archive_selection"]["factorial_exists"]["original_node"]==132
    factorial = parse_named(weights.ENDPOINT_SOURCES["factorial_exists"],registry=weights.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==factorial]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
