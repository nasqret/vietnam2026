"""Source/inert boundary tests for v34, never successful proof substitutes.

The isolated fixture compiles selected *actual* production definitions without
loading edition metadata or running a proof worker. Its fake audit class has
only a rejecting method. No public release capability is minted by these tests.
"""
from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "scripts/verify_peano_library_channels_v34.py"
BUILDER = ROOT / "scripts/build_peano_library_channels_v34.py"


def _selected(path, names, namespace):
    tree = ast.parse(path.read_text())
    chosen = [node for node in tree.body
              if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    assert {node.name for node in chosen} == set(names)
    exec(compile(ast.Module(body=chosen, type_ignores=[]), str(path), "exec"), namespace)
    return SimpleNamespace(**namespace)


def _compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      allow_nan=False, separators=(",", ":")).encode()


@pytest.fixture
def pure():
    class RejectOnlyAudit:
        def require_unchanged(self):
            raise ValueError("unissued audit: deliberately no proof authority")
    namespace = {"sha256": sha256, "json": json, "Path": Path,
                 "builder": SimpleNamespace(compact=_compact),
                 "proof_audit": SimpleNamespace(FreshProofAudit=RejectOnlyAudit),
                 "_LIVE_RELEASE": object()}
    return _selected(VERIFIER, ("ReleaseError", "_same", "_content_digest",
        "_ordered_root", "_require", "_verify_capacity", "_require_actual_audit",
        "_verify_public_identity_fields", "LiveReleaseContext"), namespace)


CAPACITY = {"schema": "peano-library-logical-capacity-v34",
            "previous_max_rows": 4096, "max_rows": 8192,
            "proof_limits_changed": False}


def test_actual_capacity_contract(pure):
    pure._verify_capacity(dict(CAPACITY))


@pytest.mark.parametrize("value", [None, [], (), False, 8192, "8192", {},
    {**CAPACITY, "extra": True}, {k: v for k, v in CAPACITY.items() if k != "schema"}])
def test_capacity_rejects_foreign_shape(pure, value):
    with pytest.raises(pure.ReleaseError):
        pure._verify_capacity(value)


@pytest.mark.parametrize("key,bad", [
    ("schema", "peano-library-logical-capacity-v33"), ("schema", None),
    ("previous_max_rows", 4096.0), ("previous_max_rows", True),
    ("previous_max_rows", 8192), ("max_rows", 4096), ("max_rows", 8193),
    ("max_rows", 8192.0), ("max_rows", "8192"), ("max_rows", False),
    ("proof_limits_changed", True), ("proof_limits_changed", 0),
    ("proof_limits_changed", None), ("proof_limits_changed", "false")])
def test_capacity_rejects_value_or_exact_type_drift(pure, key, bad):
    with pytest.raises(pure.ReleaseError):
        pure._verify_capacity({**CAPACITY, key: bad})


def _identity():
    return {"source_binding_sha256": "1" * 64, "catalog_sha256": "2" * 64,
            "revision": "2" * 12, "promoted_names": ("first", "second")}


def _check_identity(pure, value):
    pure._verify_public_identity_fields(value, source_binding_sha256="1" * 64,
        catalog_sha256="2" * 64, promoted_names=("first", "second"))


def test_public_identity_exact(pure):
    _check_identity(pure, _identity())


@pytest.mark.parametrize("key,bad", [
    ("source_binding_sha256", "0" * 64), ("source_binding_sha256", None),
    ("catalog_sha256", "3" * 64), ("catalog_sha256", 2),
    ("revision", "3" * 12), ("revision", "2" * 64),
    ("promoted_names", ["first", "second"]), ("promoted_names", ("second", "first")),
    ("promoted_names", ("first",)), ("promoted_names", ("first", "second", "second")),
    ("promoted_names", (True, "second")), ("promoted_names", None)])
def test_public_identity_rejects_mutation(pure, key, bad):
    with pytest.raises(pure.ReleaseError):
        _check_identity(pure, {**_identity(), key: bad})


@pytest.mark.parametrize("value", [None, [], {}, {**_identity(), "accepted": True}])
def test_public_identity_rejects_missing_or_extra_fields(pure, value):
    with pytest.raises(pure.ReleaseError):
        _check_identity(pure, value)


@pytest.mark.parametrize("value", [None, {}, {"all_verified": True},
    SimpleNamespace(binding="0" * 64, report={"all_verified": True}), object()])
def test_receipt_or_lookalike_is_not_live_audit(pure, value):
    with pytest.raises(pure.ReleaseError):
        pure._require_actual_audit(value)


def test_exact_but_unissued_audit_still_rejects(pure):
    with pytest.raises(ValueError, match="no proof authority"):
        pure._require_actual_audit(pure.proof_audit.FreshProofAudit())


@pytest.mark.parametrize("token", [None, False, {}, object()])
def test_context_constructor_rejects_foreign_token(pure, token):
    with pytest.raises(pure.ReleaseError):
        pure.LiveReleaseContext(token, pure.proof_audit.FreshProofAudit(), {}, {}, {}, ())


def test_context_cannot_mint_from_unissued_exact_audit(pure):
    with pytest.raises(ValueError, match="no proof authority"):
        pure.LiveReleaseContext(pure._LIVE_RELEASE, pure.proof_audit.FreshProofAudit(), {}, {}, {}, ())


@pytest.mark.parametrize("origin", [False, True])
def test_ordered_root_stream_matches_original_separator_contract(pure, origin):
    entries = tuple(SimpleNamespace(enrollment_origin=SimpleNamespace(value="ha"),
        spec=SimpleNamespace(name=name, statement=statement, dependencies=deps, script=script))
        for name, statement, deps, script in (
            ("a", "forall x. x = x", (), ("intro x", "refl")),
            ("b", "0 = 0", ("a",), ("apply a",))))
    expected = []
    for item in entries:
        fields = [item.spec.name, item.spec.statement,
                  "\x1e".join(item.spec.dependencies), "\x1e".join(item.spec.script)]
        if origin:
            fields.insert(0, "ha")
        expected.append("\x1f".join(fields))
    wanted = sha256("\x1c".join(expected).encode()).hexdigest()
    assert pure._ordered_root(entries, include_origin=origin) == wanted
    assert pure._ordered_root(entries[::-1], include_origin=origin) != wanted


@pytest.mark.parametrize("value", [{"nested": [1, False, "λ"]}, [], {}, {"a": 1, "z": None}])
def test_streamed_content_hash_matches_canonical_json(pure, value):
    assert pure._content_digest(value) == sha256(_compact(value)).hexdigest()


def test_exact_v33_parent_hashes_and_evidence_inventory():
    tree = ast.parse(BUILDER.read_text())
    pins = next(node.value for node in tree.body if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "EXPECTED_PARENT_PINS" for t in node.targets))
    paths = {"catalog": "alpha/catalog-v33.json", "catalog_delta": "alpha/catalog-v33-delta.json",
             "catalog_base": "alpha/catalog-v30.json", "metrics": "alpha/metrics-v33.json",
             "dependency_graph": "alpha/dependency-graph-v33.mmd", "channels": "channels-v33.json"}
    assert {ast.literal_eval(key) for key in pins.keys} == set(paths)
    for key, value in zip(pins.keys, pins.values, strict=True):
        path = ROOT / "artifacts/peano-library" / paths[ast.literal_eval(key)]
        # Stream one immutable source at a time; never import a catalogue runtime.
        hasher = sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(block)
        assert hasher.hexdigest() == ast.literal_eval(value.elts[1])
    parent = json.loads((ROOT / "artifacts/peano-library/alpha/catalog-v33.json").read_text())
    assert parent["metadata"]["theorem_count"] == 4092
    assert len(parent["metadata"]["evidence_documents"]) == 1020
    assert parent["delta"]["row_count"] == 870


def test_sources_preserve_explicit_parent_and_no_capacity_mutation():
    for path in (BUILDER, VERIFIER):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                assert not any(isinstance(target, ast.Attribute) and target.attr == "MAX_ROWS"
                               for target in targets)
    source = VERIFIER.read_text()
    assert 'delta["theorems"][:870]' in source
    assert 'rows[:4092]' in source
    assert 'previous_v31_metadata' in source and 'previous_v32_metadata' in source
    assert 'previous_v33_metadata' in source
    assert 'check((), result.certificate, result.formula)' in source


def test_no_source_fixture_issues_successful_proof_capability():
    source = Path(__file__).read_text()
    tree = ast.parse(source)
    rejecting = next(node for node in ast.walk(tree)
                     if isinstance(node, ast.ClassDef) and node.name == "RejectOnlyAudit")
    method = rejecting.body[0]
    assert isinstance(method, ast.FunctionDef)
    assert len(method.body) == 1 and isinstance(method.body[0], ast.Raise)


@pytest.fixture(scope="module")
def private_row():
    """Actual older math/receipt projected privately, explicitly NOT v34 evidence.

    This runs only the row formatter and independent row validator. No edition,
    complete builder, live-audit factory, writer or publication API is called.
    """
    py = str(ROOT / "peano-lab/py")
    inserted = py not in sys.path
    if inserted:
        sys.path.insert(0, py)
    try:
        module = import_module("peano_lab.library.prime_field_polynomial_convolution_triangular_candidate")
        def make_spec(name, statement, dependencies, script, summary):
            return SimpleNamespace(name=name, statement=statement, dependencies=dependencies,
                                   script=script, summary=summary)
        spec = module.make_prime_field_polynomial_convolution_triangular_candidate_theorems(make_spec)[0]
    finally:
        if inserted:
            sys.path.remove(py)
    assert not any(name.startswith("peano_lab.library.editions") for name in sys.modules)
    manifest = json.loads((ROOT / "artifacts/peano-library/alpha/catalog-v33.json").read_text())
    docs = {row["path"]: row for row in manifest["metadata"]["evidence_documents"]}
    receipt = "research/arithmetic-library/artifacts/alpha-v33-research-receipt-v1.json"
    family = json.loads((ROOT / receipt).read_text())["families"][0]
    observed = next(row for row in family["rows"] if row["name"] == spec.name)
    assert observed["statement_sha256"] == sha256(spec.statement.encode()).hexdigest()
    source = "peano-lab/py/peano_lab/library/prime_field_polynomial_convolution_triangular_candidate.py"
    test = "peano-lab/py/tests/test_campaign_research_v33_closure.py"
    rfc = "research/arithmetic-library/prime-field-polynomial-euclidean-division-rfc-v1.md"
    artifact = "research/arithmetic-library/artifacts/prime-field-polynomial-euclidean-division-proof-bundle-v1.json"
    parent = "artifacts/peano-library/alpha/catalog-v32.json"
    # The older receipt is not in its own manifest until publication has added it.
    for path in (receipt, source, test, rfc, artifact, parent):
        assert path in docs
    item = SimpleNamespace(slug=family["slug"], artifact=artifact,
        artifact_sha256=docs[artifact]["sha256"], rfc=rfc,
        modules=(SimpleNamespace(path=source, module=module.__name__.rsplit(".", 1)[-1]),))
    entry = SimpleNamespace(spec=spec, source_module=source,
                            enrollment_origin=SimpleNamespace(value="ha"))
    def digest(value):
        return sha256(value.encode() if type(value) is str else value).hexdigest()
    def logical(value):
        return digest(_compact({"name": value.name, "statement": value.statement,
                                "dependencies": list(value.dependencies), "script": list(value.script)}))
    audit = SimpleNamespace(module_test_path=lambda name: test,
                            PARENT_PATH=parent, PARENT_SHA256=docs[parent]["sha256"])
    common = {"digest": digest, "compact": _compact, "base": SimpleNamespace(_logical_spec_sha256=logical),
        "_audit_module": lambda: audit, "DEFAULT_RECEIPT": ROOT / receipt,
        "PARENT_ALPHA": ROOT / parent,
        "EXPECTED_PARENT_PINS": {"catalog": (ROOT / parent, docs[parent]["sha256"])},
        "relative": lambda path: Path(path).relative_to(ROOT).as_posix()}
    formatting = _selected(BUILDER, ("_frontier_row",), common)
    row = formatting._frontier_row(entry, 4092, item, family, docs)
    checking = _selected(VERIFIER, ("ReleaseError", "_require", "_same", "_row"),
        {"builder": formatting, "base": common["base"], "proof_audit": audit})
    checking._row(row, entry, 4092, family, item, docs)
    return checking, row, entry, family, item, docs


ROW_KEYS = (
    "body_checked", "body_receipt", "checked_use", "dependencies", "dependencies_sha256",
    "empty_context_closure", "enrollment_index", "enrollment_origin", "evidence_links", "evidence_status",
    "frontier_campaign", "logical_spec_sha256", "membership", "name", "proof_tag", "provenance",
    "script", "script_sha256", "source", "statement", "statement_sha256", "summary", "summary_sha256",
    "alpha_v34_frontier_enrollment")


@pytest.mark.parametrize("key", ROW_KEYS)
def test_private_actual_source_row_rejects_missing_field(private_row, key):
    checking, original, entry, family, item, docs = private_row
    changed = deepcopy(original)
    del changed[key]
    with pytest.raises(checking.ReleaseError):
        checking._row(changed, entry, 4092, family, item, docs)


@pytest.mark.parametrize("path,bad", [
    (("checked_use",), 1), (("body_checked",), 1), (("name",), "invented_theorem"),
    (("statement",), "0 = 1"), (("script",), ["admit"]), (("dependencies",), []),
    (("enrollment_index",), 4091), (("enrollment_origin",), "pa"),
    (("membership",), "stable"), (("proof_tag",), "STABLE0001"),
    (("source", "sha256"), "0" * 64), (("source", "path"), "foreign.py"),
    (("body_receipt", "proof_nodes"), 0), (("body_receipt", "proof_depth"), 999),
    (("body_receipt", "status"), "unverified"),
    (("empty_context_closure", "bundle_node_id"), 0),
    (("empty_context_closure", "bundle_node_count"), 493),
    (("empty_context_closure", "certificate_sha256"), "f" * 64),
    (("empty_context_closure", "kernel_mode"), "classical"),
    (("empty_context_closure", "node_statement_sha256"), "a" * 64),
    (("alpha_v34_frontier_enrollment", "first_enrolled_version"), "v33"),
    (("alpha_v34_frontier_enrollment", "parent_catalog_sha256"), "b" * 64),
    (("alpha_v34_frontier_enrollment", "bundle_node_id"), 1),
    (("alpha_v34_frontier_enrollment", "body_receipt_sha256"), "c" * 64),
    (("evidence_links", 3, "selector"), "nodes[id=0]"),
    (("evidence_links", 4, "kind"), "saved_report_authorizes_proof")])
def test_private_actual_source_row_rejects_forged_metrics_identity_or_evidence(private_row, path, bad):
    checking, original, entry, family, item, docs = private_row
    changed = deepcopy(original)
    target = changed
    for key in path[:-1]:
        target = target[key]
    assert target[path[-1]] != bad or type(target[path[-1]]) is not type(bad)
    target[path[-1]] = bad
    with pytest.raises(checking.ReleaseError):
        checking._row(changed, entry, 4092, family, item, docs)


@pytest.mark.parametrize("relative", (
    "peano-lab/py/peano_lab/library/research_source_plan_v34.py",
    "peano-lab/py/tests/test_research_source_plan_v34.py",
    "peano-lab/py/tests/test_library_editions_v34_cold_import.py",
))
def test_actual_source_plan_and_cold_import_evidence_is_explicit(relative):
    tree = ast.parse(BUILDER.read_text())
    assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == "CONTROL_DOCUMENTS"
                              for target in node.targets))
    records = {key.value: value.value for key, value in zip(assignment.value.keys, assignment.value.values)
               if isinstance(key, ast.Constant)}
    assert relative in records and type(records[relative]) is str and records[relative]
    raw = (ROOT / relative).read_bytes()
    assert raw and not (ROOT / relative).is_symlink()


def test_actual_family_rfcs_are_existing_repository_relative_documents():
    source = ROOT / "peano-lab/py/peano_lab/library/campaign_research_v34_closure.py"
    tree = ast.parse(source.read_text())
    families = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name) and node.func.id == "ResearchFamily"]
    assert len(families) == 2
    paths = []
    for family in families:
        fields = {entry.arg: entry.value for entry in family.keywords}
        relative = ast.literal_eval(fields["rfc"])
        assert type(relative) is str and relative.startswith("research/arithmetic-library/")
        assert ".." not in Path(relative).parts and not (ROOT / relative).is_symlink()
        assert (ROOT / relative).is_file()
        paths.append(relative)
    assert len(set(paths)) == 2


@pytest.mark.parametrize("report", ({}, {"families": []}, {"source_binding_sha256": "a" * 64}, "receipt.json"))
def test_public_builder_never_accepts_a_saved_projection_report(report):
    calls = []
    class RejectOnlyAudit:
        def require_unchanged(self):
            calls.append("unissued")
            raise ValueError("no original live proof invocation")
    def forbidden(*args):
        pytest.fail("saved report reached private formatting or a proof call")
    audit_module = SimpleNamespace(FreshProofAudit=RejectOnlyAudit, verify_in_fresh_windows=forbidden)
    actual = _selected(BUILDER, ("build_payloads",), {
        "require_scope": lambda: calls.append("scope"), "_audit_module": lambda: audit_module,
        "_project_payloads": forbidden, "preflight_inputs": forbidden})
    with pytest.raises(ValueError, match="stored report"):
        actual.build_payloads(report)
    assert calls == ["scope"]
    with pytest.raises(ValueError, match="no original live"):
        actual.build_payloads(RejectOnlyAudit())
    assert calls == ["scope", "scope", "unissued"]


def test_private_projection_has_no_writer_or_live_capability_and_public_guards_remain():
    tree = ast.parse(BUILDER.read_text())
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    private = ast.unparse(functions["_project_payloads"])
    public = ast.unparse(functions["build_payloads"])
    calls = {ast.unparse(node.func) for node in ast.walk(functions["_project_payloads"])
             if isinstance(node, ast.Call)}
    assert not any(name in calls for name in ("FreshProofAudit", "LiveReleaseContext", "check_or_write",
                                              "proof_audit.verify_in_fresh_windows"))
    assert not any("write" in name or "mkdir" in name or "open" == name for name in calls)
    assert "audit.require_unchanged" not in private
    assert public.count("audit.require_unchanged()") == 2
    assert public.index("type(audit) is not proof_audit.FreshProofAudit") < public.index("_project_payloads(audit.report)")
    assert public.index("audit.require_unchanged()") < public.index("_project_payloads(audit.report)") < public.rindex("audit.require_unchanged()")


FIXTURE_NOTICE = "NONAUTHORIZING display fixture: saved working observations and inert body inspection are not a fresh v34 proof audit"


def _private_fixture_write(path, value):
    """Write only a newly owned, explicitly unissued scratch observation."""
    import os
    path = Path(path)
    assert path.is_absolute() and path.name.startswith("NONAUTHORIZING-")
    assert path.parent.is_dir() and path.is_relative_to(Path("/private/tmp"))
    assert not any(parent.is_symlink() for parent in path.parents)
    assert value["proof_authority"] is value["admission_performed"] is False
    assert value["fixture_notice"] == FIXTURE_NOTICE
    raw = _compact(value)
    assert 0 < len(raw) <= 64 * 1024 * 1024
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
    return {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def _private_fixture_read(path):
    path = Path(path)
    assert path.is_absolute() and path.name.startswith("NONAUTHORIZING-")
    assert path.is_relative_to(Path("/private/tmp")) and not path.is_symlink()
    assert 0 < path.stat().st_size <= 64 * 1024 * 1024
    value = json.loads(path.read_bytes())
    assert value["proof_authority"] is value["admission_performed"] is False
    assert value["fixture_notice"] == FIXTURE_NOTICE
    return value


def _observed_family(item):
    """Actual byte/body inspection, never check/replay/Lean or a live receipt."""
    import check_alpha_v34_research as audit
    from peano_lab.engine.state import proof_identity_metrics, proof_metrics
    from peano_lab.library import campaign_research_v34_closure as research
    from peano_lab.library.proof_bundle import decode_proof_bundle
    from peano_lab.library.theorems import _closed_formula
    if item.slug == "polynomial-gcd-bezout":
        directory = ROOT / "research/arithmetic-library/working/prime-field-gcd-closure-v1"
        whole = json.loads((directory / "final-gate-02-bundle-observations-v1.json").read_bytes())
        assert whole["exit_code"] == 0
        roots = [json.loads((directory / f"final-gate-{index:02d}-root-observations-v1.json").read_bytes())
                 for index in range(3, 17)]
    else:
        value = json.loads((ROOT / "research/arithmetic-library/working/linear-congruence-classification-v1/final-verification-observations-v1.json").read_bytes())
        whole, *roots = value["gates"]
    assert whole["exit_code"] == 0 and all(row["exit_code"] == 0 for row in roots)
    observed = whole["report"]
    sealed = research.research_family(item.slug)
    assert observed["artifact_sha256"] == item.artifact_sha256
    assert observed["original_ha_checked"] is observed["independent_same_byte_lean_checked"] is True
    assert (observed["nodes"], observed["edges"], observed["body_nodes"], observed["kernel_calls"]) == (
        sealed.node_count, sealed.bundle_edges, sealed.body_nodes, sealed.node_count)
    payload = research.read_research_bundle_bytes(item.slug, ROOT / item.artifact)
    bundle, _target = decode_proof_bundle(payload.decode())
    assert len(bundle.nodes) == sealed.node_count and bundle.root == sealed.theorem_count
    assert sum(len(node.dependencies) for node in bundle.nodes) == observed["edges"]
    assert sum(proof_metrics(node.body)[0] for node in bundle.nodes) == observed["body_nodes"]
    positions = {name: index for index, name in enumerate(sealed.ordered_cone_names)}
    rows = []
    for spec in audit._owned(item):
        node = bundle.nodes[positions[spec.name]]
        assert node.node_id == positions[spec.name] and node.target == _closed_formula(spec.statement)
        assert node.dependencies == tuple(positions[name] for name in spec.dependencies)
        nodes, depth = proof_metrics(node.body)
        objects, edges, reused = proof_identity_metrics(node.body)
        rows.append({"name": spec.name, "node_id": node.node_id,
            "statement_sha256": sha256(spec.statement.encode()).hexdigest(), "proof_nodes": nodes,
            "proof_depth": depth, "proof_objects": objects, "proof_edges": edges, "reused_objects": reused})
    family = {"slug": item.slug, "new_theorem_count": len(rows), "specs_sha256": item.frontier_specs_sha256,
        "owned_node_ids": {row["name"]: row["node_id"] for row in rows}, "rows": rows,
        "bundle": {"path": item.artifact, "bytes": len(payload), "sha256": sha256(payload).hexdigest(),
            "nodes_including_packaging_root": observed["nodes"], "dependency_edges_including_packaging": observed["edges"],
            "body_proof_nodes": observed["body_nodes"], "packaging_root_id": bundle.root,
            "kernel_calls": observed["kernel_calls"], "original_ha_checked": observed["original_ha_checked"],
            "independent_lean_checked": observed["independent_same_byte_lean_checked"]}, "principal_roots": []}
    audit._validate_family_report(family, item)
    reports = {entry["report"]["name"]: entry["report"] for entry in roots}
    assert len(reports) == len(roots) == len(item.principal_roots) and set(reports) == set(item.principal_roots)
    for name in item.principal_roots:
        report = reports[name]
        assert report["artifact_sha256"] == item.artifact_sha256 and report["node_id"] == positions[name]
        principal = {key: report[key] for key in ("name", "node_id", "statement_sha256",
                                                "complete_ordinary_ha_checked", "ordinary_certificate_nodes")}
        audit._validate_report({"slug": item.slug, **principal}, kind="root", item=item, name=name, family=family)
        family["principal_roots"].append(principal)
    return family


def _prepare_display_report_fixture(path):
    """Scheduled body-inspection worker; reports are explicitly not authority."""
    import gc
    import check_alpha_v34_research as audit
    families = []
    for item in audit.registry():
        families.append(_observed_family(item))
        gc.collect()
    assert not any("editions_v" in name or "alpha_enrollment_v" in name for name in sys.modules)
    record = {"proof_authority": False, "admission_performed": False, "fixture_notice": FIXTURE_NOTICE,
        "families": families, "fresh_v34_proof_invocations": 0}
    return _private_fixture_write(path, record)


def _actual_projection_preflight(report_path, output_path):
    """Scheduled full-metadata private check; never a public release operation."""
    import build_peano_library_channels_v34 as builder
    import verify_peano_library_channels_v34 as verifier
    import check_alpha_v34_research as audit
    value = _private_fixture_read(report_path)
    binding = audit.source_binding()
    report = {"schema": audit.AUDIT_SCHEMA, "source_binding_sha256": binding,
        "parent": {"path": audit.PARENT_PATH, "bytes": audit.PARENT_BYTES, "sha256": audit.PARENT_SHA256,
                   "theorem_count": 4092}, "new_theorems": 131, "alpha_theorem_count": 4223,
        "stable_theorem_count": 432, "families": value["families"], "ordinary_principal_count": 19,
        "novelty": {"observation_only": True, "no_fresh_v34_novelty_gate": True},
        "limits": {"cpu": [170, 175], "wall_seconds": 180, "max_rss_bytes": 1536 * 1024 * 1024}}
    observation = SimpleNamespace(report=report, proof_authority=False)
    with pytest.raises(ValueError):
        builder.build_payloads(observation)
    payloads = builder._project_payloads(report)
    with pytest.raises(verifier.ReleaseError):
        verifier.verify_candidate_payloads(payloads, observation)
    artifacts = verifier._ReleaseArtifacts(payloads)
    parent = builder._load_parent()
    manifest = builder.strict_json(payloads[builder.DEFAULT_ALPHA])
    delta = builder.strict_json(payloads[builder.DEFAULT_DELTA])
    builder.codec._metadata_header(manifest["metadata"])
    builder.codec._previous_metadata(manifest["previous_v33_metadata"])
    assert builder.codec._content_digest(delta["theorems"][:870]) == builder.codec.INHERITED_DELTA_SHA256
    assert len(delta["theorems"]) == delta["row_count"] == 1001
    catalog = {**manifest["metadata"], "theorems": [*parent["theorems"][:3222], *delta["theorems"]]}
    documents = verifier._documents(catalog, parent, observation, artifacts)
    rows, families = verifier._verify_rows(catalog, parent, observation, documents)
    metrics = builder.strict_json(payloads[builder.DEFAULT_METRICS])
    channels = builder.strict_json(payloads[builder.DEFAULT_CHANNELS])
    catalog_hash = sha256(payloads[builder.DEFAULT_ALPHA]).hexdigest()
    verifier._verify_metadata(catalog, metrics, channels, parent, families, observation, catalog_hash, artifacts)
    assert len(rows) == 4223 and rows[:4092] == parent["theorems"]
    assert audit.source_binding() == binding
    base_path, base_sha = builder.EXPECTED_PARENT_PINS["catalog_base"]
    # Keep the original per-file64MiB ceiling: the logical catalogue combines
    # multiple bounded files and must not be collapsed into one oversized file.
    return _private_fixture_write(output_path, {"proof_authority": False, "admission_performed": False,
        "fixture_notice": FIXTURE_NOTICE, "catalog_metadata": manifest["metadata"],
        "delta_rows": delta["theorems"], "parent_base": {"path": builder.relative(base_path),
            "bytes": base_path.stat().st_size, "sha256": base_sha},
        "channels": channels, "families": families,
        "catalog_sha256": catalog_hash, "revision": catalog_hash[:12], "source_binding_sha256": binding,
        "promoted_names": [row["name"] for row in rows[4092:]],
        "payload_identities_only_not_installed": {builder.relative(path): {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
                                                for path, raw in payloads.items()}})
