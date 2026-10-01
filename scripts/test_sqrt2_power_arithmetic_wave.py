"""Independent archive/presentation bindings; never generate or admit a proof."""
from hashlib import sha256
import json
import sys

import pytest

from check_sqrt2_power_fresh_lean import exact_bundle
from index_sqrt2_power_wave import BASE, index_entry
from run_sqrt2_power_wave import target_for
from sqrt2_power_arithmetic_page import arithmetic_contracts, build_arithmetic_files
from sqrt2_power_binary_dag import formula_sha256
from sqrt2_power_definitions import DEFINITIONS, PARENT, parse_named
from sqrt2_power_quadratic_definitions import QUADRATIC_DEFINITIONS, quadratic_definition_manifest
from sqrt2_power_wave_page import evidence_section, signed_norm_files
from sqrt2_power_wave_results import wave_results


ATTEMPTS = (("shared-wave-ir016-v1", "IR016"), ("shared-wave-signed-norm-v1", "SN001"),
    ("shared-wave-natural-gap-v1", "NG001"), ("shared-wave-norm-separation-v1", "SN002"),
    ("shared-wave-norm-product-v1", "SN003"), ("shared-wave-convolution-vanishing-v3", "CV001"),
    ("shared-wave-rational-norm-transport-v1", "RN001"), ("shared-wave-rational-norm-product-v1", "RN002"),
    ("shared-wave-signed-product-nonzero-v1", "SI001"),
    ("shared-wave-quadratic-nonzero-v1", "QN001"), ("shared-wave-quadratic-product-trace-v1", "QF001"))
LEAN = ("fresh-lean-ir016-v1", "fresh-lean-signed-norm-v1", "fresh-lean-norm-separation-v1",
        "fresh-lean-norm-product-v1", "fresh-lean-convolution-vanishing-v1", "fresh-lean-rational-norm-wave-v1",
        "fresh-lean-quadratic-products-v1")


def observations():
    return wave_results(dict(schema="sqrt2-power-wave-evidence-index-v1",
        reports=[index_entry(folder, case) for folder, case in ATTEMPTS],
        lean_reports=[index_entry(folder) for folder in LEAN]))


def plain_page(title, body, revision, **kwargs):
    return (title+body).encode()


def test_two_aliases_are_conservative_and_have_no_hidden_premises_or_collisions():
    from peano_lab.kernel.formulas import Eq
    before = dict(DEFINITIONS)
    historical = json.loads(PARENT.read_bytes())["reviewed_definitions"]
    used_ids = {d["id"] for d in historical} | {d.stable_id for d in DEFINITIONS.values()}
    used_names = {d["name"] for d in historical} | set(DEFINITIONS)
    data = quadratic_definition_manifest()
    assert data["authority"] == "local_conservative_templates_not_Alpha_admissions"
    assert data["edges"] == []
    assert {d.stable_id for d in QUADRATIC_DEFINITIONS.values()} == {"ND0388", "ND0389"}
    for name, d in QUADRATIC_DEFINITIONS.items():
        assert name not in used_names and d.stable_id not in used_ids
        assert d.arity == 10 and len(set(d.parameters)) == 10
        assert type(d.template_formula) is Eq and d.conceptual_dependencies == ()
    assert dict(DEFINITIONS) == before
    with pytest.raises(TypeError):
        QUADRATIC_DEFINITIONS["invented"] = object()
    assert "peano_lab.library.theorems" not in sys.modules


def test_quadratic_alias_compound_arguments_do_not_capture_names():
    parameters = ("ap", "an", "bp", "bn", "cp", "cn", "dp", "dn", "rp", "rn")
    from peano_lab.kernel.formulas import parse_formula_in_context
    source = ("rp+(((ap+S an)*cn+an*cp)+(S(S 0))*(bp*dn+bn*dp))="
              "(((ap+S an)*cp+an*cn)+(S(S 0))*(bp*dp+bn*dn))+rn")
    actual = parse_named("IQuadProductReal(ap+S an,an,bp,bn,cp,cn,dp,dn,rp,rn)", parameters,
                         QUADRATIC_DEFINITIONS)
    assert actual == parse_formula_in_context(source, list(parameters))
    with pytest.raises(ValueError):
        parse_named("IQuadProductReal(ap,an,bp,bn,cp,cn,dp,dn,rp)", parameters, QUADRATIC_DEFINITIONS)


@pytest.mark.parametrize("folder,case", ATTEMPTS[2:])
def test_exact_new_statements_and_bytes_have_fresh_HA_and_Lean_evidence(folder, case):
    payload, intake = exact_bundle(BASE/folder)
    view, downloads = observations()
    row = next(r for r in view["rows"] if r["case"] == case)
    assert row["status"] == "fresh_ordinary_HA_checked" and row["independent_lean_checked"]
    assert row["target_ast_sha256"] == intake["target_ast_sha256"] == formula_sha256(target_for(case))
    assert sha256(payload).hexdigest() == row["bundle_sha256"]
    assert row["proof_download"] in downloads
    assert row["scope"] == "supporting_leaf"
    assert view["IR_parents_closed"] == view["library_admissions"] == 0


def test_named_statements_keep_exact_premises_and_reject_another_receipt():
    view, downloads = observations()
    rows = {r["case"]: r for r in view["rows"]}
    contracts, registry = arithmetic_contracts(rows)
    for case, contract in contracts.items():
        assert parse_named(contract["named"], registry=registry) == target_for(case)
        assert formula_sha256(contract["target"]) == rows[case]["target_ast_sha256"]
    altered = {**rows, "SN003": dict(rows["SN003"], target_ast_sha256=rows["SN002"]["target_ast_sha256"])}
    with pytest.raises(ValueError, match="evidence targets another statement"):
        build_arithmetic_files(altered, downloads, plain_page, "test", evidence_section)


def test_checked_DAG_uses_actual_root_edges_not_shared_notation_or_planning():
    view, downloads = observations()
    rows = {r["case"]: r for r in view["rows"]}
    pages = build_arithmetic_files(rows, downloads, plain_page, "test", evidence_section)
    data = json.loads(pages["api/checked-arithmetic-dag.json"])
    actual = {(e["source"], e["target"]) for e in data["edges"] if e["kind"] == "proof_dependency"}
    assert actual == {("IR016", "SN001"), ("SN001", "SN002"), ("NG001", "SN002"), ("SN003", "RN002"),
                      ("SN001", "QN001"), ("SN003", "QN001"), ("SI001", "QN001"), ("QN001", "QF001")}
    assert not any(e["source"] == "SN001" and e["target"] == "SN003" for e in data["edges"])
    planned = {(e["source"], e["target"]) for e in data["edges"] if e["kind"] == "planned_support_not_closure"}
    assert ("SN002", "IR032") in planned and ("SN003", "IR031") in planned
    assert {("RN001","IR031"),("RN002","IR031"),("SI001","IR046"),("QN001","IR046"),("QF001","IR046")} <= planned
    assert data["IR_parents_closed"] == 0
    assert "Solid arrows are actual direct root dependencies" in pages["arithmetic-frontier.html"].decode()
    assert "IR072 is still open" in pages["arithmetic-frontier.html"].decode()


def test_named_pages_link_exact_existing_and_new_local_definitions():
    view, downloads = observations()
    rows = {r["case"]: r for r in view["rows"]}
    pages = build_arithmetic_files(rows, downloads, plain_page, "test", evidence_section)
    for case in ("NG001", "SN002", "SN003", "CV001", "RN001", "RN002", "SI001", "QN001", "QF001"):
        html = pages[f"checked/{case}.html"].decode()
        assert "Named statement" in html and "IR072 remains open" in html
        assert "Fresh HA and independently compiled Lean checks" in html
        assert 'href="../arithmetic-frontier.html"' in html
    html = pages["checked/SN003.html"].decode()
    assert 'href="../reused-definitions/ND0157.html"' in html
    assert 'href="../quadratic-definitions.html#ND0388"' in html
    assert 'href="../quadratic-definitions.html#ND0389"' in html
    assert 'href="../local-definitions.html#ND0383"' in pages["checked/RN001.html"].decode()
    assert 'href="../local-definitions.html#ND0385"' in pages["checked/RN002.html"].decode()
    signed = signed_norm_files(rows["SN001"], plain_page, "test", users=("SN001", "SN002", "SN003", "RN001", "RN002"))
    assert json.loads(signed["api/reused-signed-square-definition.json"])["used_by"] == ["SN001", "SN002", "SN003", "RN001", "RN002"]
    for invalid in ((), ("RN001","RN001"), ("SI001",), ("invented",)):
        with pytest.raises(ValueError,match="unknown or duplicate"):
            signed_norm_files(rows["SN001"],plain_page,"test",users=invalid)
    uses = json.loads(pages["api/local-quadratic-definitions.json"])["theorem_uses"]
    assert {r["definition"] for r in uses} == {"ND0157", "ND0388", "ND0389"}
    assert all(r["kind"] == "theorem_uses_definition" for r in uses)
    assert {r["theorem"] for r in uses} >= {"SN003","RN001","RN002"}
    convolution = json.loads(pages["api/reused-convolution-definitions.json"])
    assert len(convolution["nodes"]) == 8
    assert {r["id"] for r in convolution["nodes"]} == {"PD0001", "PD0002", "PD0013", "PD0015", "PD0019", "ND0291", "ND0292", "ND0293"}
    assert all(e["kind"] == "definition_uses_definition" for e in convolution["edges"])
    assert len(convolution["edges"]) == 11
    for node in convolution["nodes"]:
        assert 'id="convolution-graph-'+node["id"]+'"' in pages["convolution-definitions.html"].decode()
    assert 'href="../convolution-definitions.html#ND0293"' in pages["checked/CV001.html"].decode()


def test_trace_definition_DAG_exposes_actual_witnesses_and_separate_nonzero_hypothesis():
    view, downloads = observations()
    rows = {r["case"]: r for r in view["rows"]}
    pages = build_arithmetic_files(rows, downloads, plain_page, "test", evidence_section)
    data = json.loads(pages["api/quadratic-trace-definitions.json"])
    assert {n["id"] for n in data["nodes"] if n["new_local"]} == {"ND0390","ND0391","ND0392","ND0393"}
    assert {n["id"] for n in data["nodes"] if not n["new_local"]} == {"PD0013","PD0002","ND0388","ND0389"}
    edges = {(e["source"],e["target"]) for e in data["edges"]}
    assert edges == {("PD0013","ND0390"),("ND0390","ND0391"),("ND0388","ND0391"),
        ("ND0389","ND0391"),("ND0390","ND0392"),("ND0391","ND0392"),("PD0002","ND0392"),
        ("ND0390","ND0393"),("PD0002","ND0393")}
    assert all(e["kind"] == "definition_uses_definition" for e in data["edges"])
    assert {(r["definition"],r["theorem"]) for r in data["theorem_uses"]} == {
        ("ND0390","QF001"),("ND0392","QF001"),("ND0393","QF001")}
    assert all('id="trace-graph-'+n["id"]+'"' in pages["quadratic-trace-definitions.html"].decode() for n in data["nodes"])
    html = pages["checked/QF001.html"].decode()
    assert 'href="../quadratic-trace-definitions.html#ND0392"' in html
    assert "Trace existence" in html and "separate open obligations" in html
    assert "trace does not assume" in pages["quadratic-trace-definitions.html"].decode()


def test_natural_gap_Z3_record_is_separate_from_proof_authority():
    view, _ = observations()
    row = next(r for r in view["rows"] if r["case"] == "NG001")
    assert row["live_external"]["solver"] == "z3"
    assert row["live_external"]["HA_authority"] is False
    assert row["live_external"]["role"] == "independent_conjecture_check_not_used_for_reconstruction"


@pytest.mark.parametrize("case", ("RN001","RN002","SI001"))
def test_new_Z3_checks_are_exact_but_not_trusted_certificate_imports(case):
    view,_ = observations()
    row = next(r for r in view["rows"] if r["case"] == case)
    assert row["live_external"]["solver"] == "z3"
    assert row["live_external"]["status"]["solver_status"] == "unsat"
    assert row["live_external"]["HA_authority"] is False
    assert row["scope"] == "supporting_leaf"


def test_failed_convolution_attempts_do_not_inherit_the_repaired_certificate():
    index = dict(schema="sqrt2-power-wave-evidence-index-v1",
        reports=[index_entry("shared-wave-convolution-vanishing-v"+str(version), "CV001") for version in (1,2,3)],
        lean_reports=[index_entry("fresh-lean-convolution-vanishing-v1")])
    view, _ = wave_results(index)
    assert [row["status"] for row in view["rows"]] == ["not_checked", "not_checked", "fresh_ordinary_HA_checked"]
    assert [row["independent_lean_checked"] for row in view["rows"]] == [False, False, True]
    assert not any("proof_download" in row for row in view["rows"][:2])
    assert view["counts"]["unique_HA_statements"] == 1
