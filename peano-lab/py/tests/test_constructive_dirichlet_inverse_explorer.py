"""Fresh inverse evidence and actual canonical reader/graph interactions.

Positive pages come only from this run's thirteen proof workers and bounded
renderer. These tests do not accept an old receipt or mock a proof checker.
The established actual-JavaScript hostile-SVG harness is retained; it is
not described as an available visual browser.
"""

from __future__ import annotations

import ast
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
import inspect
import json
from pathlib import Path
import posixpath
import subprocess
import sys
from types import FunctionType, SimpleNamespace
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import build_constructive_dirichlet_inverse_explorer as builder
import constructive_dirichlet_inverse_checkpoints as checkpoints
import constructive_bottom_layer_checkpoints as previous
from constructive_dirichlet_inverse_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_with_names
from tests import test_constructive_dirichlet_explorer as old_tests


SLUGS = ("dirichlet-signed-units", "dirichlet-triangular", "dirichlet-inverses")
EXPECTED_COUNTS = dict(zip(SLUGS, (9, 10, 21), strict=True))
EXPECTED_PREFIXES = dict(zip(SLUGS, ("ZU", "DT", "IV"), strict=True))
ROOT_TAGS = {
    "dirichlet-signed-units": {"dirichlet_signed_unit_product_classification": "ZU0002",
                              "dirichlet_signed_unit_affine_solve": "ZU0008", "dirichlet_signed_unit_affine_unique": "ZU0009"},
    "dirichlet-triangular": {"dirichlet_convolution_first_input_append_step": "DT0008",
                            "dirichlet_convolution_at_one_iff": "DT000A", "dirichlet_convolution_strict_prefix_exists": "DT0006"},
    "dirichlet-inverses": {"dirichlet_unit_equation_construct": "IV0009", "dirichlet_inverse_criterion": "IV0013",
                          "dirichlet_inverse_exists_positive_unique": "IV0015"},
}
PRINCIPAL_CONTRACTS = (
    (SLUGS[0], "dirichlet_signed_unit_product_classification",
     "forall a b. SignedMul(a,b,2) -> (a=2 /\\ b=2) \\/ (a=1 /\\ b=1)"),
    (SLUGS[0], "dirichlet_signed_unit_affine_solve",
     "forall r u e. SignedUnit(u) -> exists x y. SignedMul(x,u,y) /\\ SignedAdd(r,y,e)"),
    (SLUGS[0], "dirichlet_signed_unit_affine_unique",
     "forall r u e a b c d. SignedUnit(u) -> SignedMul(a,u,b) -> SignedAdd(r,b,e) -> SignedMul(c,u,d) -> SignedAdd(r,d,e) -> a=c /\\ b=d"),
    (SLUGS[1], "dirichlet_convolution_first_input_append_step",
     "forall k G F M r H x u y e. DirichletPrefix(G,F,S k,k,M) -> SignedPrefixSum(M,S k,r) -> ArithExtend(G,H,S k,x) -> ArithAt(F,1,u) -> SignedMul(x,u,y) -> SignedAdd(r,y,e) -> DirichletSum(H,F,S k,e)"),
    (SLUGS[1], "dirichlet_convolution_at_one_iff",
     "forall F G a b z. ArithAt(F,1,a) -> ArithAt(G,1,b) -> (DirichletSum(F,G,1,z) -> SignedMul(a,b,z)) /\\ (SignedMul(a,b,z) -> DirichletSum(F,G,1,z))"),
    (SLUGS[1], "dirichlet_convolution_strict_prefix_exists",
     "forall N k F G. ArithTable(N,F) -> ArithTable(k,G) -> exists M r. DirichletPrefix(G,F,S k,k,M) /\\ SignedPrefixSum(M,S k,r)"),
    (SLUGS[2], "dirichlet_unit_equation_construct",
     "forall N F T u w. ArithTable(N,F) -> ArithTable(N,T) -> ArithAt(F,1,u) -> SignedUnit(u) -> exists G. DirichletTable(N,G,F,T) /\\ ArithAt(G,0,w)"),
    (SLUGS[2], "dirichlet_inverse_criterion",
     "forall N F. ArithTable(N,F) -> ((exists G. DirichletInverse(N,F,G)) -> (N=0 \\/ DirichletUnitAtOne(F))) /\\ ((N=0 \\/ DirichletUnitAtOne(F)) -> exists G. DirichletInverse(N,F,G))"),
    (SLUGS[2], "dirichlet_inverse_exists_positive_unique",
     "forall N F w. ArithTable(N,F) -> (N=0 \\/ DirichletUnitAtOne(F)) -> exists G. DirichletInverse(N,F,G) /\\ (ArithAt(G,0,w) /\\ (forall H. DirichletInverse(N,F,H) -> ArithPositiveEqual(G,H,N)))"),
)


def _reuse_test(function):
    """Reuse actual DOM assertions/drivers, without historical fixture calls."""
    scoped = FunctionType(function.__code__, globals(), function.__name__, function.__defaults__, function.__closure__)
    scoped.__kwdefaults__ = None if function.__kwdefaults__ is None else dict(function.__kwdefaults__)
    return scoped


_drivers = _reuse_test(old_tests._drivers)


def test_principal_contracts_match_frozen_sources_before_any_rendering():
    from export_constructive_dirichlet_inverse import authoring_rows
    table = {row.name: row for row in authoring_rows()}
    assert len(table) == 40 and len(PRINCIPAL_CONTRACTS) == 9
    for _, name, contract in PRINCIPAL_CONTRACTS:
        parser = _LocalDefinedParser(contract, DEFINITIONS)
        assert parser.parse() == parse_formula_with_names(table[name].statement)[0], name
        assert not parser.free


@pytest.fixture(scope="module")
def drivers():
    return _drivers()


@pytest.fixture(scope="module")
def families():
    result = builder.families()
    assert tuple(item.slug for item in result) == SLUGS
    assert {item.slug: item.prefix for item in result} == EXPECTED_PREFIXES
    return {item.slug: item for item in result}


@pytest.fixture(scope="module")
def files(pytestconfig):
    supplied = getattr(pytestconfig, "_dirichlet_inverse_fresh_snapshot", None)
    if supplied is None:
        before = builder._immutable_test_state()
        result = builder.build_files()
    else:
        assert type(supplied) is builder._FreshSnapshotTests
        assert supplied.binding == builder._assert_snapshot_binding(supplied.files)
        before, result = supplied.immutable_before, supplied.files
    assert builder._immutable_test_state() == before
    builder.model.write_or_check(result, output=builder.OUTPUT, check=True)
    return result


@pytest.fixture(scope="module")
def corpora(files):
    return {slug: json.loads(files[slug + "/api/corpus.json"]) for slug in SLUGS}


@pytest.fixture(scope="module")
def theorem_table():
    return {row.name: row for row in (*builder.closure.parent_snapshot().specs,
                                     *builder.previous_rows(), *checkpoints.all_new_rows())}


def test_exact_40_inventory_preserves_all_four_non_admitted_generations(files, corpora):
    inventory = json.loads(files["checkpoints.json"])
    expected = checkpoints.all_new_rows()
    assert inventory["schema"] == builder.SCHEMA and inventory["publication_scope"] == "local-only-checkpoint"
    assert inventory["published"] is inventory["alpha_admission_performed"] is inventory["stable_admission_performed"] is False
    assert inventory["inherited_support_counted_as_new"] is False
    assert inventory["previous_research_theorems"] == 534
    assert inventory["previous_research_generations"] == [170, 126, 125, 113]
    assert inventory["prior_theorem_count_for_exact_ast_novelty_check"] == 3756
    assert inventory["parent"] == {"alpha_version": "v30", "alpha_checked_use_count": 3222, "stable_count": 432,
                                   "catalog_sha256": "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"}
    assert inventory["navigation_revision"] == "ac7111ec14ff"
    assert inventory["new_theorems"] == sum(row["node_count"] for row in corpora.values()) == len(expected) == 40
    assert sum(len(row.dependencies) for row in expected) == 132
    assert sum(len(row.script) for row in expected) == 1712
    assert {slug: row["node_count"] for slug, row in corpora.items()} == EXPECTED_COUNTS
    assert Counter(row["name"] for corpus in corpora.values() for row in corpus["nodes"]) == Counter(row.name for row in expected)
    assert inventory["statement_asts_distinct_from_all_3756_prior_and_each_other"] is True


@pytest.mark.parametrize("slug", SLUGS)
def test_all_seven_inventory_roles_actual_bytes_and_principal_roots(slug, files, corpora, families, theorem_table):
    corpus = corpora[slug]
    checkpoint = next(row for row in checkpoints.CHECKPOINTS if row.slug == slug)
    owned = checkpoints.load_rows(checkpoint)
    report = json.loads(files[slug + "/api/checkpoint.json"])
    assert report == corpus["checkpoint_report"]
    assert report["new_theorem_count"] == len(owned) == corpus["node_count"] == corpus["new_theorem_count"]
    assert corpus["previous_research_generations"] == [170, 126, 125, 113]
    assert report["membership"] == "local_non_admitting_checkpoint"
    assert report["bundle"]["original_ha_checked"] is report["bundle"]["independent_lean_checked"] is True
    payload = files["checkpoints/" + Path(checkpoint.artifact).name]
    assert payload == (ROOT / checkpoint.artifact).read_bytes()
    assert len(payload) == checkpoint.artifact_bytes and sha256(payload).hexdigest() == checkpoint.artifact_sha256
    assert tuple(root["name"] for root in report["principal_roots"]) == checkpoint.principal_roots
    assert len(report["principal_roots"]) == 3
    assert all(root["complete_ordinary_ha_checked"] is True and type(root["ordinary_certificate_nodes"]) is int
               and 1 < root["ordinary_certificate_nodes"] <= builder.closure.DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_occurrences
               for root in report["principal_roots"])
    assert corpus["render_evidence_provenance"] == "projection_of_fresh_nonce_authenticated_workers_and_exact_pinned_proof_data"
    assert {row["name"] for row in corpus["nodes"]} == {row.name for row in owned}
    for record in (corpus, *corpus["nodes"]):
        assert builder.render._status(record) == builder.render.STATUS
        assert all(record[key] is False for key in builder.render.FORBIDDEN_ADMISSION_FIELDS)
        assert "alpha_edition_version" not in record and "alpha_first_enrolled_version" not in record
    assert all(row["inventory_role"] == "new_owned_theorem" for row in corpus["nodes"])
    assert corpus["alpha_enrolled_node_count"] == corpus["alpha_checked_use_node_count"] == corpus["stable_admitted_node_count"] == 0
    support = report["support"]
    assert support["published_non_admitted_count"] == support["prior_bottom_layer_count"] + support["prior_lower_tier_count"]
    assert support["local_non_admitted_count"] == support["prior_lower_continuation_count"] + support["prior_dirichlet_count"]
    assert support["counted_as_new_owned_theorems"] is False
    assert (support["published_non_admitted_count"] + support["local_non_admitted_count"] + support["current_cross_track_count"]
            + support["alpha_v30_count"] + len(owned) + 1) == report["bundle"]["nodes_including_packaging_root"]
    for external in corpus["external_dependencies"]:
        name = external["name"]
        assert external["counted_as_new_owned_theorem"] is False
        assert external["statement"] == theorem_table[name].statement
        assert external["statement_sha256"] == sha256(theorem_table[name].statement.encode()).hexdigest()
        admitted = external["inventory_role"] == "inherited_alpha_v30"
        assert external["admitted_to_alpha"] is external["alpha_checked_use"] is external["enrolled_in_alpha"] is admitted
        if not admitted:
            assert external["parent_alpha_version"] is None
            expected_role = ("inherited_published_bottom_layer_checkpoint" if name in support["prior_bottom_layer_theorems"] else
                             "inherited_published_lower_tier_checkpoint" if name in support["prior_lower_tier_theorems"] else
                             "inherited_local_lower_continuation_checkpoint" if name in support["prior_lower_continuation_theorems"] else
                             "inherited_local_dirichlet_checkpoint" if name in support["prior_dirichlet_theorems"] else "new_cross_track_support")
            assert external["inventory_role"] == expected_role
    assert corpus["root_names"] == list(families[slug].roots)
    assert {name: corpus["tags"][name] for name in corpus["root_names"]} == ROOT_TAGS[slug]


# The actual canonical assertions and JavaScript drivers are reused with the
# new real corpus, not synthetic evidence or a second graph implementation.
test_every_statement_tactic_and_local_proposition_is_the_exact_owned_proof = pytest.mark.parametrize("slug", SLUGS)(
    _reuse_test(old_tests.test_every_statement_tactic_and_local_proposition_is_the_exact_owned_proof))
test_exact_conservative_definition_dag_and_proof_only_paths = pytest.mark.parametrize("slug", SLUGS)(
    _reuse_test(old_tests.test_exact_conservative_definition_dag_and_proof_only_paths))
test_independently_written_principal_contract_is_the_exact_displayed_statement = pytest.mark.parametrize("slug,name,contract", PRINCIPAL_CONTRACTS)(
    _reuse_test(old_tests.test_independently_written_principal_contract_is_the_exact_displayed_statement))
test_canonical_qr_landing_and_exact_defined_page_topology = pytest.mark.parametrize("slug", SLUGS)(
    _reuse_test(old_tests.test_canonical_qr_landing_and_exact_defined_page_topology))
test_all_five_historical_assets_are_byte_identical = _reuse_test(old_tests.test_all_five_historical_assets_are_byte_identical)
test_actual_canonical_mixed_graph_with_getter_only_svg_hrefs = pytest.mark.parametrize("slug", SLUGS)(
    pytest.mark.parametrize("focus_kind", ("theorem", "definition"))(
        _reuse_test(old_tests.test_actual_canonical_mixed_graph_with_getter_only_svg_hrefs)))
test_actual_three_filters_and_hash_highlighting = pytest.mark.parametrize("slug", SLUGS)(
    pytest.mark.parametrize("ready,canonical_first", (("loading", True), ("complete", False)))(
        _reuse_test(old_tests.test_actual_three_filters_and_hash_highlighting)))
test_manifest_is_deterministic_and_covers_every_literal_file = _reuse_test(old_tests.test_manifest_is_deterministic_and_covers_every_literal_file)


def test_actual_inverse_definitions_do_not_assume_the_criterion_or_code_uniqueness(corpora):
    import constructive_dirichlet_definitions as old
    assert len(old.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME) == 369
    assert all(DEFINITIONS[name] is item for name, item in old.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME.items())
    inverse = {row["name"]: row for row in corpora[SLUGS[2]]["definitions"]}
    for name, parameters, edges in (("SignedUnit", ["u"], []), ("DirichletUnitAtOne", ["F"], ["ArithAt"]),
                                     ("DirichletInverse", ["N", "F", "G"], ["KroneckerDeltaTable", "DirichletTable"])):
        row = inverse[name]
        assert row["parameters"] == parameters and row["dependency_names"] == edges
        assert row["id"] == DEFINITIONS[name].stable_id and row["expanded_template"] == DEFINITIONS[name].template_source
    assert "SignedUnit" not in inverse["DirichletUnitAtOne"]["dependency_names"]
    assert "DirichletUnitAtOne" not in inverse["DirichletInverse"]["dependency_names"]
    assert "ArithPositiveEqual" in inverse
    support = corpora[SLUGS[2]]["checkpoint_report"]["support"]
    assert "dirichlet_convolution_associative" in support["prior_dirichlet_theorems"]
    assert "dirichlet_delta_left_table" in support["prior_dirichlet_theorems"]
    assert "dirichlet_signed_unit_affine_solve" in support["current_cross_track_theorems"]
    assert "dirichlet_convolution_first_input_append_step" in support["current_cross_track_theorems"]


def test_all_actual_links_and_fragments_preserve_four_generations_and_cross_tracks(files, drivers):
    Document = drivers["Document"]
    documents = {name: Document(payload) for name, payload in files.items() if name.endswith(".html")}
    old_documents, used = {}, Counter()
    roots = ("constructive-bottom-layer-explorer", "constructive-lower-tier-explorer",
             "constructive-lower-continuation-explorer", "constructive-dirichlet-explorer", "constructive-gaussian-campaign")
    for name, document in documents.items():
        assert len(document.ids) == len(set(document.ids)), name
        for tag, attrs in document.tags:
            for key in ("href", "src"):
                if key not in attrs: continue
                url = urlsplit(attrs[key])
                assert not url.scheme and not url.netloc and not url.path.startswith("/"), (name, attrs[key])
                target = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(url.path))) if url.path else name
                if url.path.endswith("/"): target = posixpath.normpath(target + "/index.html")
                if target.startswith("../"):
                    directory = target.split("/")[1]
                    assert directory in roots, (name, attrs[key])
                    path = builder.OUTPUT / target
                    assert path.is_file(), (name, attrs[key])
                    used[directory] += 1
                    if url.fragment:
                        if target not in old_documents: old_documents[target] = Document(path.read_bytes())
                        assert unquote(url.fragment) in old_documents[target].ids
                else:
                    assert target in files, (name, attrs[key], target)
                    if target.split("/", 1)[0] in SLUGS and target.split("/", 1)[0] != name.split("/", 1)[0]: used["cross"] += 1
                    if url.fragment: assert unquote(url.fragment) in documents[target].ids, (name, attrs[key])
                if url.path:
                    asset = Path(url.path).name
                    expected = builder.ASSET_DIGESTS[asset][:12] if tag in {"script", "link"} and asset in builder.render.ASSET_DIGESTS else builder.HTML_REVISION
                    assert parse_qs(url.query).get("v") == [expected], (name, attrs[key])
    assert all(used[key] > 0 for key in (*roots, "cross"))


def test_every_inline_script_parses_and_actual_graph_payload_equals_api(files, drivers):
    scripts = []
    for name, payload in files.items():
        if not name.endswith(".html"): continue
        for attrs, source in drivers["Document"](payload).scripts:
            if attrs.get("type", "").lower() in {"application/json", "application/ld+json"}: drivers["_strict_json"](source)
            elif "src" not in attrs: scripts.append({"name": name, "source": source})
            if attrs.get("id") == "pa-defined-graph-data":
                assert source.startswith("window.PA_DEFINED_GRAPH=") and source.endswith(";")
                graph = drivers["_strict_json"](source[len("window.PA_DEFINED_GRAPH="):-1])
                assert graph == drivers["_strict_json"](files[name.replace("graph.html", "api/graph.json")])
    program = 'const vm=require("node:vm"),rows=JSON.parse(require("node:fs").readFileSync(0,"utf8"));rows.forEach(x=>new vm.Script(x.source,{filename:x.name}));process.stdout.write(String(rows.length));'
    result = subprocess.run(["node", "-e", program], input=json.dumps(scripts), text=True, capture_output=True, check=True, timeout=20)
    assert int(result.stdout) == len(scripts) == 11


def test_actual_exact_navigation_never_injects_missing_graph_links(files, corpora, drivers):
    cases = []
    for name, payload in files.items():
        if "/explorer/" not in name or "/defined/" in name or not name.endswith(".html"): continue
        document = drivers["Document"](payload)
        links = [attrs["href"] for tag, attrs in document.header_tags if tag == "a" and "data-graph-navigation" in attrs]
        assert len(links) == 1 and "defined/graph.html" in links[0], name
        page = next(attrs["data-page"] for tag, attrs in document.tags if tag == "body")
        cases.append({"name": name, "page": page, "href": links[0]})
    source = builder.model.ASSET_SOURCES["exact-explorer.js"].read_text()
    start = source.index("  function initializeGraphNavigation()"); end = source.index("\n  function ", start + 1)
    program = '''const vm=require("node:vm"),input=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
input.cases.forEach(row=>{const anchor={getAttribute(){return row.href;}};const header={querySelector(s){if(s==="[data-graph-navigation]")return anchor;throw Error(s);}};
const document={body:{dataset:{page:row.page}},querySelector(s){if(s===".pa-proof-header")return header;throw Error(s);},createElement(){throw Error("bad graph injection: "+row.name);}};
vm.runInNewContext(input.source+"\\ninitializeGraphNavigation();",{document});});process.stdout.write(String(input.cases.length));'''
    result = subprocess.run(["node", "-e", program], input=json.dumps({"source": source[start:end], "cases": cases}), text=True, capture_output=True, check=True, timeout=20)
    assert int(result.stdout) == len(cases) == sum(corpus["node_count"] for corpus in corpora.values()) + 3 == 43


@pytest.mark.parametrize("query", ("", "?view=goal&focus=G009", "?view=family&focus=F01", "?view=domain&focus=D01",
                                   "?view=goal&focus=G007", "?view=goal&focus=G999", "?view=unknown&focus=G009"))
def test_actual_dispatch_supports_known_scales_without_hiding_unmatched_cards(query, files, drivers):
    document = drivers["Document"](files["grand-campaign/index.html"])
    cards = [attrs for _, attrs in document.tags if "data-local-family" in attrs]
    source = document.scripts[-1][1]
    program = '''const vm=require("node:vm"),input=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
const cards=input.cards.map(attrs=>({attrs,hidden:false,getAttribute(k){return this.attrs[k];}}));
vm.runInNewContext(input.source,{URL,window:{location:{href:"file:///repo/book/_static/constructive-dirichlet-inverse-explorer/grand-campaign/"+input.query}},document:{querySelectorAll(s){if(s!=="[data-local-family]")throw Error(s);return cards;}}});
process.stdout.write(JSON.stringify(cards.filter(x=>!x.hidden).map(x=>x.attrs.id)));'''
    result = subprocess.run(["node", "-e", program], input=json.dumps({"source": source, "cards": cards, "query": query}), text=True, capture_output=True, check=True, timeout=20)
    assert json.loads(result.stdout) == list(SLUGS)


def test_full_criterion_is_the_default_root_without_claiming_broader_G009(files, families, corpora):
    family = families["dirichlet-inverses"]
    assert family.roots[-1] == "dirichlet_inverse_criterion"
    assert corpora[family.slug]["tags"][family.roots[-1]] == "IV0013"
    assert "target=IV0013" in files[family.slug + "/index.html"].decode()
    assert "target=IV0013" in files["grand-campaign/index.html"].decode()
    assert all(item.goal_scope.endswith("full_G009_open") for item in families.values())
    assert "N=0" in family.caveat and "N>0" in family.caveat and "zeroth value is arbitrary" in family.caveat
    assert "positive represented values, not table codes or zero" in family.caveat
    assert "Multiplicative-function closure" in family.caveat
    inventory = json.loads(files["checkpoints.json"])
    assert inventory["general_dirichlet_inverse_criterion_proved"] is True
    assert inventory["full_G009_dirichlet_convolution_theory_proved"] is inventory["general_G091_prime_power_fields_proved"] is False
    assert "full_G007_inversion_proved" not in inventory


def test_saved_audit_is_only_the_output_of_all_nine_live_ordinary_roots(files):
    report, inventory = json.loads(files["proof-audit.json"]), json.loads(files["checkpoints.json"])
    assert files["proof-audit.json"] == builder.audit.canonical_report(report).encode("utf-8")
    assert report["proof_authority"] == "fresh_original_ha_and_independent_compiled_lean_checks"
    assert report["stored_receipt_is_proof_authority"] is False
    assert report["published"] is report["alpha_admission_performed"] is report["stable_admission_performed"] is False
    assert report["checkpoints"] == inventory["checkpoints"]
    assert report["new_theorems"] == 40 and report["prior_theorem_count_for_exact_ast_novelty_check"] == 3756
    assert report["statement_asts_distinct_from_prior_and_within_tranche"] is True
    assert report["previous_research_generations"] == [170, 126, 125, 113]
    roots = [root for family in report["checkpoints"] for root in family["principal_roots"]]
    assert len(roots) == 9 and all(root["complete_ordinary_ha_checked"] is True for root in roots)
    assert report["general_dirichlet_inverse_criterion_proved"] is True
    assert report["full_G009_dirichlet_convolution_theory_proved"] is report["general_G091_prime_power_fields_proved"] is False
    assert inventory["render_source_binding_sha256"] == builder._render_binding()


def test_original_424_file_snapshot_and_old_scopes_are_exact_after_new_build(files):
    state, _ = builder._immutable_test_state()
    old_manifest = ROOT / builder.PRIOR_MANIFEST
    assert old_manifest.relative_to(ROOT).as_posix() in state
    assert sha256(old_manifest.read_bytes()).hexdigest() == builder.PRIOR_MANIFEST_SHA256
    manifest = json.loads(old_manifest.read_bytes())
    assert len(manifest["files"]) + 1 == 424
    assert all((old_manifest.parent / path).relative_to(ROOT).as_posix() in state for path in manifest["files"])
    assert builder._fork_render_phase.__code__ is builder.previous_model._fork_render_phase.__code__
    assert builder._fork_render_phase.__globals__ is builder.__dict__
    assert builder.previous_model._fork_render_phase.__globals__["audit"] is builder.previous_model.audit
    assert builder.audit is not builder.previous_model.audit


test_render_projection_is_not_a_fabricated_kernel_receipt = _reuse_test(old_tests.test_render_projection_is_not_a_fabricated_kernel_receipt)
test_unregistered_or_empty_tranche_cannot_generate_a_verified_site = _reuse_test(old_tests.test_unregistered_or_empty_tranche_cannot_generate_a_verified_site)
test_incomplete_or_ambiguous_checkpoint_inventory_fails_before_verification = pytest.mark.parametrize("mutation", ("partial", "duplicate", "unknown", "reordered"))(
    _reuse_test(old_tests.test_incomplete_or_ambiguous_checkpoint_inventory_fails_before_verification))
test_fake_evidence_object_is_not_accepted = _reuse_test(old_tests.test_fake_evidence_object_is_not_accepted)
test_failed_real_verification_never_proceeds_to_rendering = _reuse_test(old_tests.test_failed_real_verification_never_proceeds_to_rendering)
test_cli_does_not_report_success_after_writer_exceeds_the_memory_budget = _reuse_test(old_tests.test_cli_does_not_report_success_after_writer_exceeds_the_memory_budget)
test_cli_never_overwrites_an_existing_or_symlink_audit = pytest.mark.parametrize("kind", ("file", "directory", "live_symlink", "dangling_symlink"))(
    _reuse_test(old_tests.test_cli_never_overwrites_an_existing_or_symlink_audit))


@pytest.mark.parametrize("bad", ({}, None, [], {"checkpoints": [], "general_dirichlet_inverse_criterion_proved": False}))
def test_partial_or_unverified_audit_cannot_enter_render_projection(bad):
    with pytest.raises(builder.ExplorerError, match="complete fresh audit"):
        builder._validate_fresh_audit(bad)


def test_cli_retains_each_proof_and_render_bound_with_derived_scheduler_deadline(monkeypatch):
    calls = []
    monkeypatch.setattr(builder.resource, "setrlimit", lambda key, value: calls.append(("cpu", key, value)))
    monkeypatch.setattr(builder.signal, "alarm", lambda seconds: calls.append(("wall", seconds)))
    monkeypatch.setattr(builder, "_build_verified", lambda **_: (_ for _ in ()).throw(RuntimeError("over budget")))
    monkeypatch.setattr(builder.model, "write_or_check", lambda *_a, **_k: pytest.fail("over-budget write"))
    with pytest.raises(RuntimeError, match="over budget"): builder.main([])
    assert calls == [("cpu", builder.resource.RLIMIT_CPU, (170, 175)), ("wall", 2770)]
    assert builder.audit.CONTROLLER_WALL_SECONDS == 13 * 185 + 180 == 2585
    assert builder.CONTROLLER_WALL_SECONDS == 2770
    assert builder.RENDER_WALL_SECONDS == builder.audit.WALL_SECONDS == 180
    assert builder.audit.CPU_LIMITS == (170, 175) and builder.audit.MAX_RSS_BYTES == 1536 * 1024 * 1024


def test_inverse_display_rejects_real_bundle_without_separate_ordinary_evidence(files):
    from peano_lab.library.proof_bundle import decode_proof_bundle
    checkpoint = next(row for row in checkpoints.CHECKPOINTS if row.slug == "dirichlet-inverses")
    report = json.loads(files["dirichlet-inverses/api/checkpoint.json"])
    for root in report["principal_roots"]:
        root["complete_ordinary_ha_checked"] = False
        del root["ordinary_certificate_nodes"]
    bundle, _ = decode_proof_bundle(files["checkpoints/" + Path(checkpoint.artifact).name].decode("utf-8"))
    rejected = builder._FreshRenderEvidence(checkpoint, None, bundle, report)
    family = next(item for item in builder.families() if item.slug == checkpoint.slug)
    with pytest.raises(builder.ExplorerError, match="ordinary principal"):
        builder.family_corpus(family, rejected)


def test_same_in_memory_files_are_passed_to_ui_tests_without_receipt_input(files, monkeypatch):
    calls = []
    def record(args, *, plugins):
        calls.append((args, plugins)); return 17
    monkeypatch.setattr(pytest, "main", record)  # Scheduling only, never proof acceptance.
    before = builder._immutable_test_state()
    assert builder._run_snapshot_tests(files, before) == 17
    arguments, plugins = calls.pop()
    assert arguments == ["-q", str(ROOT / "peano-lab/py/tests/test_constructive_dirichlet_inverse_explorer.py")]
    assert len(plugins) == 1 and type(plugins[0]) is builder._FreshSnapshotTests
    assert plugins[0].files is files and plugins[0].immutable_before == before
    assert plugins[0].binding == builder._assert_snapshot_binding(files)
    config = SimpleNamespace(); plugins[0].pytest_configure(config)
    assert config._dirichlet_inverse_fresh_snapshot is plugins[0]
    assert not calls


def test_in_memory_handoff_is_accepted_by_the_real_pytest_plugin_manager():
    from _pytest.config import PytestPluginManager
    plugin = builder._FreshSnapshotTests({}, "scheduling-only", ({}, ()))
    manager = PytestPluginManager()
    assert manager.register(plugin, "inverse-fresh-snapshot") == "inverse-fresh-snapshot"
    config = SimpleNamespace(addinivalue_line=lambda *_args: None)
    manager.hook.pytest_configure.call_historic(kwargs={"config": config})
    assert config._dirichlet_inverse_fresh_snapshot is plugin
