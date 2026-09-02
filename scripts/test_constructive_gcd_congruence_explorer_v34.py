"""Bounded source-only v34 QR reader tests; no live capability is manufactured."""
import ast
from dataclasses import fields, is_dataclass
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
for path in (ROOT/"scripts",ROOT/"peano-lab/py"):
    if str(path) not in sys.path:sys.path.insert(0,str(path))
import build_constructive_gcd_congruence_explorer_v34 as reader

def _source_compaction_preflight():
    """Explicit separately scheduled syntax check; never proof authority."""
    from tests.test_constructive_research_publication_v34 import _assert_reading, _parse_defined, _same_ast
    summaries=[]
    for slug in reader.SLUGS:
        rows=reader.specs(slug)
        readings,definitions=reader._source_only_syntax(slug)
        assert len(readings)==len(rows)
        for row,reading in zip(rows,readings,strict=True):
            _assert_reading(row,reading)
        for definition in definitions:
            actual=reader.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[definition["name"]]
            _same_ast(_parse_defined(definition["defined_template"],actual.parameters),actual.template_formula)
        summaries.append({"slug":slug,"rows":len(rows),"commands":sum(len(row.script) for row in rows),
                          "definitions":len(definitions),"specs_sha256":reader._specs_digest(rows)})
    assert [row["rows"] for row in summaries]==[119,12]
    assert not any("editions_v" in name or "alpha_enrollment_v" in name for name in sys.modules)
    return {"proof_authority":False,"admission_performed":False,
            "scope":"source-only exact AST and local-statement compaction, not proof replay",
            "families":summaries}


def _private_render_preflight(path):
    """Scheduled in-memory QR observation; no renderer capability or install."""
    from types import SimpleNamespace
    from test_verify_peano_library_channels_v34 import _private_fixture_read
    from tests import test_constructive_research_publication_v34 as ui
    import constructive_research_publication_v34 as publication
    value=_private_fixture_read(path)
    pin=value["parent_base"]
    assert pin["path"]=="artifacts/peano-library/alpha/catalog-v30.json"
    base=publication.strict_json(publication.read_pinned(ROOT/pin["path"],pin["bytes"],pin["sha256"]))
    assert len(base["theorems"])==3222 and len(value["delta_rows"])==1001
    catalog={**value["catalog_metadata"],"theorems":[*base["theorems"],*value["delta_rows"]]}
    del base
    assert set(value["families"])==set(reader.SLUGS)
    ordered_families={slug:value["families"][slug] for slug in reader.SLUGS}
    context=SimpleNamespace(catalog=catalog,families=ordered_families,**{key:value[key] for key in ("channels",
        "catalog_sha256","revision","source_binding_sha256")},
        promoted_names=tuple(value["promoted_names"]),proof_authority=False,
        render_source_binding_sha256=publication.require_render_inputs())
    with pytest.raises(publication.PublicationError):reader.build_files_from_live(context)
    corpora=tuple(reader._corpus(context,slug) for slug in reader.SLUGS)
    files=reader._render_files(context,corpora)
    reader._assert_published_content(files,context)
    runtime=ui.drivers()
    actual={"phase":"gcd-congruence","context":context}
    for slug in reader.SLUGS:
        ui._exact_family_content(actual,slug,first_version="v34",files=files)
        ui._dashboard(slug,actual,runtime,reader.family(slug),files=files)
        ui.graph_support.assert_graph_views(reader.strict_json(files[slug+"/api/graph.json"]))
    ui._javascript_and_navigation(actual,runtime,2,files=files)
    assert not any("editions_v" in name or "alpha_enrollment_v" in name for name in sys.modules)
    return {"proof_authority":False,"admission_performed":False,"scope":"private in-memory QR render and content observations",
        "file_count":len(files),"html_count":sum(name.endswith(".html") for name in files),
        "total_bytes":sum(map(len,files.values())),"families":list(reader.SLUGS)}

def test_family_descriptor_is_a_real_immutable_source_only_value():
    assert is_dataclass(reader.Family)
    names=tuple(field.name for field in fields(reader.Family))
    assert names==("slug","prefix","title","kicker","description","formula","domain","family_id",
                   "milestones","roots","definition_route","extra_definitions","caveat","goal_scope")
    descriptor=reader.Family(*("source-only" for _ in names))
    assert descriptor.slug=="source-only"
    with pytest.raises(AttributeError):descriptor.slug="changed"

def test_exact_old_qr_assets_and_new_alias_inventory():
    for name,pin in reader.TEMPLATE_PINS.items():reader._source(name,expected=pin)
    assert len(reader.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME)==407
    assert reader.SLUGS==("polynomial-gcd-bezout","congruence-arithmetic")
    assert reader.OUTPUT_NAME=="constructive-gcd-congruence-explorer-v34"

@pytest.mark.parametrize("bad",[None,{},[],"unknown","polynomial-euclidean-division",True])
def test_unregistered_family_rejected_before_any_proof(bad):
    with pytest.raises(reader.ExplorerError):reader.registration(bad)

def test_source_public_builder_guards_before_and_after_rendering():
    tree=ast.parse(Path(reader.__file__).read_text())
    fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="build_files_from_live")
    calls=[ast.unparse(n.func) for n in ast.walk(fun) if isinstance(n,ast.Call)]
    assert calls.count("publication.require_live")==2
    assert "_render_files" in calls
    assert not any("FreshProofAudit" in call or "LiveReleaseContext" in call for call in calls)

def test_source_reachability_separate_from_literal_artifact_order():
    tree=ast.parse(Path(reader.__file__).read_text())
    fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_validate_data")
    text=ast.unparse(fun)
    assert "visit(dependency)" in text and "complete.append(row)" in text
    assert "record.ordered_cone_names" in text
    assert "record.ordered_cone_names_sha256" in text
    assert "_validate_principal_records" in text

def test_typed_graph_edges_and_no_goal_overclaim():
    text=Path(reader.__file__).read_text()
    for kind in ("proof_dependency","uses_definition","definition_uses_definition"):
        assert '"'+kind+'"' in text
    assert '"current_G091_prime_power_fields_proved": False' in text
    assert '"path_policy": "proof_dependency_edges_only"' in text

def test_no_source_only_test_imported_edition():
    assert not any(name.startswith("peano_lab.library.editions") for name in sys.modules)
