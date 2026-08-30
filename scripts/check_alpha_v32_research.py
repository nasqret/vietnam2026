#!/usr/bin/env python3
"""Fresh, bounded proof gates for the two-family additive Alpha-v32 release.

Every family is checked from its real ordinary HA bodies and from exactly the
same bytes by the independently compiled Lean verifier. Principal certificates
run in separate unchanged proof windows. A saved report is never an input.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import gc
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path
import re
import resource
import secrets
import signal
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve()
for directory in (ROOT / "peano-lab/py", ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import check_constructive_lower_continuation as transport
from check_constructive_bottom_layers import authoring_rss_bytes
import constructive_bottom_layer_checkpoints as independent
import check_alpha_v31_completed_lower as previous_audit
import peano_catalog_shards as parent_catalog


CPU_LIMITS = (170, 175)
WALL_SECONDS = 180
PARENT_TIMEOUT_SECONDS = 185
MAX_RSS_BYTES = 1536 * 1024 * 1024
MAX_STDOUT_BYTES = 128 * 1024
MAX_STDERR_BYTES = 8 * 1024
WORKER_SCHEMA = "peano-alpha-v32-live-proof-worker-v1"
AUDIT_SCHEMA = "peano-alpha-v32-research-proof-audit-v1"
EXPECTED_INVENTORY = (
    ("multiplicative-convolution", 90),
    ("polynomial-division-prerequisites", 85),
)
EXPECTED_JOB_COUNT = 15
PARENT_PATH = "artifacts/peano-library/alpha/catalog-v31.json"
PARENT_BYTES = 293_294
PARENT_SHA256 = "6c9ebfb3c37e42aefab200b710f78e7693dc5826c80f053544deea41caf44aab"
PARENT_EVIDENCE_PINS = (
    ("artifacts/peano-library/alpha/metrics-v31.json", 587038,
     "85db8daf0cdbd6610fa20e311a361d4f3c2def3e34ea0d8d7b6c9444904f15a2"),
    ("artifacts/peano-library/alpha/dependency-graph-v31.mmd", 999176,
     "ce3a1b903be4076aea5e93ac91ec74a799496bd9e0f4b895852a7350c72fd530"),
    ("artifacts/peano-library/channels-v31.json", 9117,
     "63851a20e4befd4d6a8fa9d60c9203a06babfbfc7743516d6f72a059f1aed696"),
    ("artifacts/peano-library/catalog-v1.json", 1310134,
     "87fca4ab6e66d01f728ada1d9c6442f1167b8f2a8fe51cd6ec5eda901b3daffd"),
)
CONTROL_SOURCES = (
    *previous_audit.CONTROL_SOURCES,
    "scripts/check_alpha_v32_research.py",
    "scripts/build_peano_library_channels_v32.py",
    "scripts/verify_peano_library_channels_v32.py",
    "scripts/peano_catalog_shards_v32.py",
    "scripts/constructive_g009_support.py",
    "scripts/constructive_g009_checkpoints.py",
    "scripts/check_constructive_g009.py",
    "scripts/constructive_polynomial_division_support.py",
    "scripts/constructive_polynomial_division_checkpoints.py",
    "scripts/check_constructive_polynomial_division.py",
    "peano-lab/py/peano_lab/library/alpha_enrollment_v32.py",
    "peano-lab/py/peano_lab/library/editions_v32.py",
    "peano-lab/py/peano_lab/library/campaign_research_v32_closure.py",
    "research/arithmetic-library/alpha-v32-research-promotion-rfc-v1.md",
    "research/arithmetic-library/g009-multiplicative-convolution-rfc-v1.md",
    "research/arithmetic-library/prime-field-polynomial-division-prerequisites-rfc-v1.md",
)

if any(getattr(transport, key) != globals()[key] for key in (
    "CPU_LIMITS", "WALL_SECONDS", "PARENT_TIMEOUT_SECONDS", "MAX_RSS_BYTES",
    "MAX_STDOUT_BYTES", "MAX_STDERR_BYTES",
)) or transport.ROOT != ROOT:
    raise RuntimeError("the inherited bounded worker transport changed")

AuditError = transport.AuditWorkerError
canonical = transport._canonical
_LIVE_AUDIT = object()


def registry():
    """Exact provider ownership; a registration never accepts a proof."""
    from peano_lab.library import campaign_research_v32_closure as research
    research.validate_research_metadata()
    result = tuple(independent.Checkpoint(
        slug=family.slug,
        modules=tuple(independent.ModulePin(module, research.FACTORY_BY_MODULE[module].source_sha256)
                      for module in family.modules),
        artifact=family.artifact, artifact_bytes=family.artifact_bytes,
        artifact_sha256=family.artifact_sha256, frontier_count=family.count,
        principal_roots=family.principal_roots, rfc=family.rfc,
        frontier_specs_sha256=family.specs_sha256,
    ) for family in research.RESEARCH_FAMILIES)
    if (tuple((item.slug, item.frontier_count) for item in result) != EXPECTED_INVENTORY
            or len({item.artifact for item in result}) != 2
            or sum(item.frontier_count for item in result) != 175
            or tuple(len(item.principal_roots) for item in result) != (6, 6)
            or 1 + len(result) + sum(len(item.principal_roots) for item in result) != EXPECTED_JOB_COUNT):
        raise AuditError("the exact two-family promotion inventory changed")
    return result


def module_test_path(module):
    """Literal test provenance, including the shared final G009 test file."""
    from peano_lab.library import campaign_research_v32_closure as research
    research.validate_research_metadata()
    if type(module) is not str or module not in research.FACTORY_BY_MODULE:
        raise AuditError("unknown exact v32 source module")
    return research.FACTORY_BY_MODULE[module].test


def _edition():
    from peano_lab.library import editions_v32
    editions_v32.require_research_seal()
    if (len(editions_v32.ALPHA_ENTRIES) != 3971
            or len(editions_v32.FRONTIER_NEW_NAMES) != 175
            or len(editions_v32.STABLE_ENTRIES) != 432):
        raise AuditError("the exact additive release partition changed")
    return editions_v32


def _owned(item):
    """Compare exact source factories with the independently sealed new edition."""
    from peano_lab.library.theorems import TheoremSpec
    from peano_lab.library.campaign_bottom_layer_closure import _specs_digest
    rows = []
    for pin in item.modules:
        independent._source_bytes(pin)
        module = import_module("peano_lab.library." + pin.module)
        expected_path = ROOT / pin.path
        factory = getattr(module, pin.factory, None)
        if (not isinstance(getattr(module, "__file__", None), str)
                or not Path(module.__file__).samefile(expected_path)
                or not callable(factory) or getattr(factory, "__module__", None) != module.__name__):
            raise AuditError("a cached source module or factory identity changed")
        rows.extend(factory(TheoremSpec))
    rows = tuple(rows)
    edition = _edition()
    if (len(rows) != item.frontier_count or _specs_digest(rows) != item.frontier_specs_sha256
            or not set(item.principal_roots) <= {row.name for row in rows}
            or any(edition.ALPHA_EDITION.by_name.get(row.name) is None
                   or edition.ALPHA_EDITION.by_name[row.name].spec != row for row in rows)):
        raise AuditError("literal research ownership differs from the new sealed specifications")
    return rows


def _inventory_rows():
    rows = tuple(row for item in registry() for row in _owned(item))
    if tuple(row.name for row in rows) != _edition().FRONTIER_NEW_NAMES:
        raise AuditError("the exact ordered additive frontier changed")
    return rows


def _relative_path(path):
    """Stable repository identity; never normalize a foreign path into scope."""
    if not isinstance(path, Path):
        raise AuditError("a proof source path must be a Path")
    try:
        relative = path.relative_to(ROOT)
    except ValueError as error:
        raise AuditError("a proof source is outside the repository") from error
    if (not relative.parts or any(part in ("", ".", "..") for part in relative.parts)
            or "\\" in relative.as_posix()):
        raise AuditError("an unsafe proof source identity was supplied")
    return relative.as_posix()


def _file_digest(relative, maximum, *, expected_bytes=None, expected_sha256=None):
    """Strict no-follow, size-first streaming authentication; no large buffer."""
    if (type(relative) is not str or not relative or "\\" in relative
            or relative.startswith("/") or any(part in ("", ".", "..") for part in relative.split("/"))
            or type(maximum) is not int or not 0 < maximum <= parent_catalog.MAX_CATALOG_BYTES
            or expected_bytes is not None and (type(expected_bytes) is not int
                                               or not 0 < expected_bytes <= maximum)
            or expected_sha256 is not None and (type(expected_sha256) is not str
                                                or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None)):
        raise AuditError("invalid bounded repository source")
    path = ROOT / relative
    if _relative_path(path) != relative:
        raise AuditError("a source identity was normalized")
    owner = parent_catalog._owner(None)
    try:
        with parent_catalog._opened(path, owner, expected_bytes) as (descriptor, before):
            if before.size > maximum:
                raise AuditError("a source exceeds its original input ceiling")
            digest = sha256()
            consumed = 0
            while consumed < before.size:
                block = os.read(descriptor, min(1024 * 1024, before.size - consumed))
                if not block:
                    raise AuditError("a proof source was truncated")
                consumed += len(block)
                digest.update(block)
            if os.read(descriptor, 1):
                raise AuditError("a proof source grew during hashing")
            if parent_catalog._fingerprint(path, os.fstat(descriptor)) != before:
                raise AuditError("an open proof source changed during hashing")
        if parent_catalog._stat_file(path, owner, expected_bytes) != before:
            raise AuditError("a proof source path changed during hashing")
    except (OSError, ValueError) as error:
        raise AuditError("an ordinary bounded proof source could not be authenticated: " + relative) from error
    actual = digest.hexdigest()
    if expected_sha256 is not None and actual != expected_sha256:
        raise AuditError("literal proof source bytes changed: " + relative)
    return before.size, actual


def _runtime_source_paths():
    """Bind actual implementation inputs, not an unrestricted metadata wildcard."""
    directory = ROOT / "peano-lab/py/peano_lab"
    result = [_relative_path(path) for path in sorted(directory.rglob("*.py"))]
    if not result or len(result) != len(set(result)):
        raise AuditError("the actual runtime source inventory is malformed")
    return tuple(result)


def source_binding():
    """Bind current bytes; neither hash checks nor old receipts prove a theorem."""
    from peano_lab.library import campaign_research_v32_closure as research
    families = registry()
    controls = {path: _file_digest(path, independent.MAX_SOURCE_BYTES)[1]
                for path in dict.fromkeys((*CONTROL_SOURCES, *_runtime_source_paths()))}
    research.validate_research_source_bytes()
    for item in families:
        for pin in item.modules:
            independent._source_bytes(pin)
            if controls[pin.path] != pin.sha256:
                raise AuditError("the source changed between its live and literal checks")
        _file_digest(item.artifact, parent_catalog.MAX_CATALOG_BYTES,
                     expected_bytes=item.artifact_bytes, expected_sha256=item.artifact_sha256)
    parent = parent_catalog.verify_catalog_bindings(ROOT / PARENT_PATH, expected_sha256=PARENT_SHA256)
    if parent.manifest.bytes != PARENT_BYTES or parent.manifest.row_count != 3796:
        raise AuditError("the immutable v31 parent manifest changed")
    parent_inputs = [
        {"role": item.role, "path": _relative_path(item.path), "bytes": item.bytes,
         "sha256": item.sha256, "schema": item.schema, "row_count": item.row_count}
        for item in (parent.manifest, parent.parent, parent.delta)
    ]
    for path, size, digest in PARENT_EVIDENCE_PINS:
        _file_digest(path, parent_catalog.MAX_CATALOG_BYTES,
                     expected_bytes=size, expected_sha256=digest)
    independent._check_lean_binary()
    return sha256(canonical({
        "controls": controls, "families": [asdict(item) for item in families],
        "parent": parent_inputs,
        "parent_evidence": PARENT_EVIDENCE_PINS,
        "lean": [independent.LEAN_BINARY_BYTES, independent.LEAN_BINARY_SHA256],
    })).hexdigest()


def _family_syntax_report(item, bundle, receipt, positions):
    from peano_lab.engine.state import proof_identity_metrics, proof_metrics
    owned = _owned(item)
    rows = []
    for spec in owned:
        node_id = positions[spec.name]
        body = bundle.nodes[node_id].body
        nodes, depth = proof_metrics(body)
        objects, edges, reused = proof_identity_metrics(body)
        rows.append({"name": spec.name, "node_id": node_id,
                     "statement_sha256": sha256(spec.statement.encode()).hexdigest(),
                     "proof_nodes": nodes, "proof_depth": depth, "proof_objects": objects,
                     "proof_edges": edges, "reused_objects": reused})
    return {
        "slug": item.slug, "new_theorem_count": len(owned),
        "specs_sha256": item.frontier_specs_sha256,
        "owned_node_ids": {spec.name: positions[spec.name] for spec in owned},
        "rows": rows,
        "bundle": {
            "path": item.artifact, "bytes": item.artifact_bytes, "sha256": item.artifact_sha256,
            "nodes_including_packaging_root": len(bundle.nodes),
            "dependency_edges_including_packaging": receipt.dependency_edges,
            "body_proof_nodes": receipt.total_body_nodes, "packaging_root_id": bundle.root,
            "kernel_calls": receipt.kernel_calls,
            "original_ha_checked": True, "independent_lean_checked": True,
        },
        "principal_roots": [],
    }


def _family(item):
    from peano_lab.library import campaign_research_v32_closure as research
    edition = _edition()
    bundle, receipt, positions = edition.checked_research_bundle(item.slug)
    payload = research.read_research_bundle_bytes(item.slug, ROOT / item.artifact)
    independent._lean_check(item, receipt.node_count, bundle.root, payload)
    if receipt.kernel_calls != len(bundle.nodes):
        raise AuditError("not every actual body reached the original HA kernel")
    return _family_syntax_report(item, bundle, receipt, positions)


def _root(item, name):
    from peano_lab.kernel.checker import check
    from peano_lab.library.theorems import _closed_formula
    rows = {row.name: row for row in _owned(item)}
    if name not in item.principal_roots:
        raise AuditError("unregistered ordinary principal")
    edition = _edition()
    result = edition.replay(name, edition="alpha")
    exact = _closed_formula(rows[name].statement)
    if result.spec != rows[name] or result.formula != exact or not check((), result.certificate, exact):
        raise AuditError("the returned ordinary empty-context certificate failed original HA")
    _, _, positions = edition.checked_research_bundle(item.slug)
    return {"slug": item.slug, "name": name, "node_id": positions[name],
            "statement_sha256": sha256(rows[name].statement.encode()).hexdigest(),
            "complete_ordinary_ha_checked": True, "ordinary_certificate_nodes": result.proof_nodes}


def _novelty():
    from peano_lab.library.formula_dag import FormulaArena
    from peano_lab.library.theorems import _closed_formula
    rows = _inventory_rows()
    index = {}
    duplicates = []
    # Exact canonical FormulaDAG bytes decide equality; hashes only index them.
    for spec in rows:
        encoded = FormulaArena().freeze(_closed_formula(spec.statement)).to_json()
        fingerprint = sha256(encoded.encode()).digest()
        duplicates.extend((spec.name, old) for old, other in index.get(fingerprint, ()) if encoded == other)
        index.setdefault(fingerprint, []).append((spec.name, encoded))
    for spec in _edition().v31.ALPHA_CHECKED_SPECS:
        encoded = FormulaArena().freeze(_closed_formula(spec.statement)).to_json()
        fingerprint = sha256(encoded.encode()).digest()
        duplicates.extend((name, spec.name) for name, other in index.get(fingerprint, ()) if encoded == other)
    if duplicates:
        raise AuditError(f"exact duplicate promoted statements: {duplicates!r}")
    return {"new_theorems": 175, "prior_theorems": 3796, "duplicates": [],
            "exact_ast_novelty_checked": True,
            "ordered_names_sha256": sha256("\n".join(row.name for row in rows).encode()).hexdigest()}


def _validate_family_report(report, item):
    """Exact identities and bounded observational metrics from the live worker."""
    from peano_lab.library.campaign_research_v32_closure import research_plan
    from peano_lab.library.proof_bundle import DEFAULT_BUNDLE_LIMITS as limits
    rows = _owned(item)
    plan = research_plan(item.slug)
    sealed = plan.family
    if (type(report) is not dict or set(report) != {
            "slug", "new_theorem_count", "specs_sha256", "owned_node_ids", "rows", "bundle", "principal_roots"}
            or report["slug"] != item.slug or type(report["new_theorem_count"]) is not int
            or report["new_theorem_count"] != len(rows)
            or report["specs_sha256"] != item.frontier_specs_sha256
            or report["principal_roots"] != []):
        raise AuditError("wrong exact family report")
    bundle = report["bundle"]
    if type(bundle) is not dict or set(bundle) != {
            "path", "bytes", "sha256", "nodes_including_packaging_root",
            "dependency_edges_including_packaging", "body_proof_nodes", "packaging_root_id",
            "kernel_calls", "original_ha_checked", "independent_lean_checked"}:
        raise AuditError("malformed actual bundle report")
    if (bundle["path"] != item.artifact or type(bundle["bytes"]) is not int
            or bundle["bytes"] != item.artifact_bytes or bundle["sha256"] != item.artifact_sha256
            or bundle["original_ha_checked"] is not True or bundle["independent_lean_checked"] is not True):
        raise AuditError("changed actual bundle identity or skipped independent proof gate")
    for key, exact in (("nodes_including_packaging_root", sealed.node_count),
                       ("dependency_edges_including_packaging", sealed.bundle_edges),
                       ("body_proof_nodes", sealed.body_nodes),
                       ("packaging_root_id", sealed.node_count - 1),
                       ("kernel_calls", sealed.node_count)):
        if type(bundle[key]) is not int or bundle[key] != exact:
            raise AuditError("actual proof metrics differ from the independently sealed artifact")
    for key, maximum in (("nodes_including_packaging_root", limits.max_nodes),
                         ("dependency_edges_including_packaging", limits.max_edges),
                         ("body_proof_nodes", limits.max_total_body_nodes),
                         ("kernel_calls", limits.max_nodes)):
        if type(bundle[key]) is not int or not 0 < bundle[key] <= maximum:
            raise AuditError("invalid bounded actual bundle metrics")
    count = bundle["nodes_including_packaging_root"]
    if (type(bundle["packaging_root_id"]) is not int or bundle["packaging_root_id"] != count - 1
            or bundle["kernel_calls"] != count):
        raise AuditError("changed packaging root or omitted original-kernel calls")
    if (type(report["owned_node_ids"]) is not dict
            or set(report["owned_node_ids"]) != {spec.name for spec in rows}
            or type(report["rows"]) is not list or len(report["rows"]) != len(rows)):
        raise AuditError("missing, duplicate or unrelated owned proof rows")
    positions = []
    for spec, actual in zip(rows, report["rows"], strict=True):
        if (type(actual) is not dict or set(actual) != {
                "name", "node_id", "statement_sha256", "proof_nodes", "proof_depth",
                "proof_objects", "proof_edges", "reused_objects"}
                or actual["name"] != spec.name
                or actual["statement_sha256"] != sha256(spec.statement.encode()).hexdigest()
                or type(actual["node_id"]) is not int or not 0 <= actual["node_id"] < count - 1
                or actual["node_id"] != plan.positions[spec.name]
                or type(report["owned_node_ids"][spec.name]) is not int
                or report["owned_node_ids"][spec.name] != actual["node_id"]):
            raise AuditError("changed exact owned statement or local proof identity")
        positions.append(actual["node_id"])
        for key, minimum, maximum in (
            ("proof_nodes", 1, limits.max_body_nodes), ("proof_depth", 1, limits.max_body_depth),
            ("proof_objects", 1, limits.max_body_nodes), ("proof_edges", 0, limits.max_body_nodes * 2),
            ("reused_objects", 0, limits.max_body_nodes),
        ):
            if type(actual[key]) is not int or not minimum <= actual[key] <= maximum:
                raise AuditError("invalid bounded actual body metrics")
        if (actual["proof_objects"] > actual["proof_nodes"]
                or actual["proof_depth"] > actual["proof_nodes"]
                or not actual["proof_objects"] - 1 <= actual["proof_edges"] <= actual["proof_nodes"] - 1
                or actual["reused_objects"] != actual["proof_edges"] - (actual["proof_objects"] - 1)):
            raise AuditError("inconsistent actual body metrics")
    if positions != sorted(set(positions)):
        raise AuditError("duplicate or reordered owned local proof nodes")
    return report


def _validate_report(report, *, kind, item=None, name=None, family=None):
    if kind == "novelty":
        expected = {"new_theorems": 175, "prior_theorems": 3796, "duplicates": [],
                    "exact_ast_novelty_checked": True,
                    "ordered_names_sha256": sha256("\n".join(_edition().FRONTIER_NEW_NAMES).encode()).hexdigest()}
        if canonical(report) != canonical(expected):
            raise AuditError("changed exact whole-release novelty audit")
    elif kind == "family":
        _validate_family_report(report, item)
    elif kind == "root":
        from peano_lab.library.layered_replay import DEFAULT_LAYERED_REPLAY_LIMITS
        spec = _edition().ALPHA_EDITION.by_name[name].spec
        count = report.get("ordinary_certificate_nodes") if type(report) is dict else None
        if type(count) is not int or not 1 < count <= DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_occurrences:
            raise AuditError("invalid bounded ordinary-certificate count")
        expected = {"slug": item.slug, "name": name, "node_id": family["owned_node_ids"][name],
                    "statement_sha256": sha256(spec.statement.encode()).hexdigest(),
                    "complete_ordinary_ha_checked": True, "ordinary_certificate_nodes": count}
        if canonical(report) != canonical(expected):
            raise AuditError("changed exact ordinary principal report")
    else:
        raise AuditError("unknown proof job kind")


def _validate_message(payload, *, kind, slug, nonce, binding, item=None, name=None, family=None):
    value = transport._decode_message(payload)
    expected = {"schema": WORKER_SCHEMA, "kind": kind, "slug": slug, "nonce": nonce,
                "binding_sha256": binding,
                "limits": {"cpu": list(CPU_LIMITS), "wall_seconds": WALL_SECONDS, "max_rss_bytes": MAX_RSS_BYTES}}
    if set(value) != {*expected, "peak_rss_bytes", "report"} or canonical({k: value[k] for k in expected}) != canonical(expected):
        raise AuditError("stale, foreign or incorrectly limited proof worker response")
    peak = value["peak_rss_bytes"]
    if type(peak) is not int or not 0 < peak <= MAX_RSS_BYTES:
        raise AuditError("actual proof worker exceeded the unchanged RSS ceiling")
    _validate_report(value["report"], kind=kind, item=item, name=name, family=family)
    return value["report"], peak


def _run_worker(kind, binding, *, item=None, name=None, family=None):
    slug = item.slug if item else "all"
    nonce = secrets.token_hex(32)
    command = [sys.executable, str(SCRIPT), "--worker", kind, "--slug", slug,
               "--nonce", nonce, "--binding", binding]
    if name is not None:
        command.extend(("--root", name))
    environment = os.environ.copy()
    environment.update(PYTHONPATH=os.pathsep.join((str(ROOT / "peano-lab/py"), str(ROOT / "scripts"))),
                       PYTHONMALLOC="pymalloc", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1")
    label = f"{kind}: {slug}" + (f" / {name}" if name else "")
    print(f"Checking {label}", file=sys.stderr, flush=True)
    payload = transport._capture_bounded(command, environment)
    report, peak = _validate_message(payload, kind=kind, slug=slug, nonce=nonce, binding=binding,
                                     item=item, name=name, family=family)
    print(f"Verified {label}; peak RSS {peak} bytes", file=sys.stderr, flush=True)
    return report, peak


def _worker(kind, slug, nonce, binding, root):
    resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)
    signal.alarm(WALL_SECONDS)
    if (re.fullmatch(r"[0-9a-f]{64}", nonce or "") is None
            or re.fullmatch(r"[0-9a-f]{64}", binding or "") is None or source_binding() != binding):
        raise AuditError("invalid or stale private proof worker invocation")
    gc.collect()
    if kind == "novelty" and slug == "all" and root is None:
        report = _novelty()
    else:
        items = [item for item in registry() if item.slug == slug]
        if len(items) != 1:
            raise AuditError("unknown exact proof family")
        if kind == "family" and root is None:
            report = _family(items[0])
        elif kind == "root" and root in items[0].principal_roots:
            report = _root(items[0], root)
        else:
            raise AuditError("unknown or incorrectly scoped proof job")
    gc.collect()
    if source_binding() != binding:
        raise AuditError("actual proof sources changed during verification")
    value = {"schema": WORKER_SCHEMA, "kind": kind, "slug": slug, "nonce": nonce,
             "binding_sha256": binding, "report": report, "peak_rss_bytes": authoring_rss_bytes(),
             "limits": {"cpu": list(resource.getrlimit(resource.RLIMIT_CPU)), "wall_seconds": WALL_SECONDS,
                        "max_rss_bytes": MAX_RSS_BYTES}}
    payload = canonical(value)
    if len(payload) > MAX_STDOUT_BYTES:
        raise AuditError("actual proof report exceeds its unchanged protocol size")
    authoring_rss_bytes()
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()
    return 0


class FreshProofAudit:
    """An in-process capability minted only after this invocation's proof jobs."""

    __slots__ = ("_token", "_binding", "_report_bytes", "peak_rss_bytes")

    def __init__(self, token, binding, report, peak):
        if token is not _LIVE_AUDIT:
            raise AuditError("a saved report cannot instantiate a live proof audit")
        self._token, self._binding = token, binding
        self._report_bytes = canonical(report)
        self.peak_rss_bytes = peak

    @property
    def binding(self):
        return self._binding

    @property
    def report(self):
        return json.loads(self._report_bytes)

    def require_unchanged(self):
        if type(self) is not FreshProofAudit or self._token is not _LIVE_AUDIT or source_binding() != self._binding:
            raise AuditError("proof sources changed or no live proof audit is present")


def verify_in_fresh_windows():
    """Run exactly 15 real jobs: novelty, two HA/Lean bundles, twelve ordinary roots."""
    _inventory_rows()
    binding = source_binding()
    novelty, peak = _run_worker("novelty", binding)
    families = []
    for item in registry():
        report, observed = _run_worker("family", binding, item=item)
        peak = max(peak, observed)
        principals = []
        for name in item.principal_roots:
            root, observed = _run_worker("root", binding, item=item, name=name, family=report)
            peak = max(peak, observed)
            principals.append({key: value for key, value in root.items() if key != "slug"})
        families.append({**report, "principal_roots": principals})
        gc.collect()
    if source_binding() != binding:
        raise AuditError("proof inputs changed across the live release gates")
    report = {"schema": AUDIT_SCHEMA, "source_binding_sha256": binding,
              "parent": {"path": PARENT_PATH, "bytes": PARENT_BYTES, "sha256": PARENT_SHA256,
                         "theorem_count": 3796},
              "new_theorems": 175, "alpha_theorem_count": 3971, "stable_theorem_count": 432,
              "families": families, "novelty": novelty,
              "ordinary_principal_count": sum(len(item.principal_roots) for item in registry()),
              "limits": {"cpu": list(CPU_LIMITS), "wall_seconds": WALL_SECONDS, "max_rss_bytes": MAX_RSS_BYTES}}
    return FreshProofAudit(_LIVE_AUDIT, binding, report, max(peak, authoring_rss_bytes()))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("family", "root", "novelty"), help=argparse.SUPPRESS)
    for name in ("slug", "nonce", "binding", "root"):
        parser.add_argument("--" + name, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        if not all((args.slug, args.nonce, args.binding)) or (args.worker == "root") != (args.root is not None):
            parser.error("invalid private proof worker arguments")
        return _worker(args.worker, args.slug, args.nonce, args.binding, args.root)
    if any((args.slug, args.nonce, args.binding, args.root)):
        parser.error("private proof arguments require an exact worker mode")
    resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)
    jobs = 1 + len(registry()) + sum(len(item.principal_roots) for item in registry())
    if jobs != EXPECTED_JOB_COUNT:
        raise AuditError("the exact fifteen-window schedule changed")
    signal.alarm(jobs * PARENT_TIMEOUT_SECONDS + WALL_SECONDS)
    audit = verify_in_fresh_windows()
    print(f"Fresh Alpha-v32 proof gates PASS: 175 new theorems; 2 complete HA/Lean bundles; "
          f"{audit.report['ordinary_principal_count']} ordinary principals; peak RSS {audit.peak_rss_bytes} bytes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
