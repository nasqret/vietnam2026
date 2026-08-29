#!/usr/bin/env python3
"""Fresh sequential HA/Lean/ordinary-root windows; never reuse audit receipts.

Each family and the full-tranche novelty audit gets a fresh process with the
unchanged 170/175 CPU, 180 wall-second and 1536 MiB limits. The controller only
authenticates inventory, validates bounded worker messages, and formats the
same deterministic report. Its derived scheduling deadline is not a larger
proof window. A success sidecar is written only after all five jobs succeed.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import gc
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import resource
import secrets
import selectors
import signal
import subprocess
import sys
import time

from check_constructive_bottom_layers import authoring_rss_bytes, canonical_report, check_receipt_bytes
import constructive_lower_continuation_checkpoints as checkpoints
import constructive_lower_continuation_support as support
from peano_lab.engine.state import proof_metrics
from peano_lab.library.proof_bundle import decode_proof_bundle


ROOT = checkpoints.ROOT
SCRIPT = Path(__file__).resolve()
RECEIPT = ROOT / "research/arithmetic-library/artifacts/lower-continuation-checkpoints-v1.json"
WORKER_SCHEMA = "peano-lab-lower-continuation-fresh-worker-v1"
CPU_LIMITS = (170, 175)
WALL_SECONDS = 180
PARENT_TIMEOUT_SECONDS = 185
MAX_RSS_BYTES = 1536 * 1024 * 1024
MAX_STDOUT_BYTES = 128 * 1024
MAX_STDERR_BYTES = 8 * 1024
EXPECTED_INVENTORY = (
    ("divisor-involutions", 12), ("mobius-divisor-cancellation", 28),
    ("rectangular-sums", 32), ("polynomial-products", 53),
)
CONTROLLER_WALL_SECONDS = (len(EXPECTED_INVENTORY) + 1) * PARENT_TIMEOUT_SECONDS + WALL_SECONDS
CONTROL_SOURCES = (
    "scripts/check_constructive_lower_continuation.py",
    "scripts/constructive_lower_continuation_checkpoints.py",
    "scripts/constructive_lower_continuation_support.py",
    "scripts/check_constructive_bottom_layers.py",
    "scripts/constructive_bottom_layer_checkpoints.py",
    "scripts/constructive_lower_tier_checkpoints.py",
    "scripts/constructive_lower_tier_support.py",
    "peano-lab/py/peano_lab/library/campaign_bottom_layer_closure.py",
)


class AuditWorkerError(RuntimeError):
    """An actual worker failed or its exact bounded protocol was invalid."""


def _canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _inventory():
    if (tuple((item.slug, item.frontier_count) for item in checkpoints.CHECKPOINTS) != EXPECTED_INVENTORY
            or checkpoints.EXPECTED_FAMILIES != {name for name, _ in EXPECTED_INVENTORY}):
        raise AuditWorkerError("the exact four-family continuation inventory changed")
    rows = checkpoints.all_new_rows()
    if len(rows) != 125 or len({row.name for row in rows}) != 125:
        raise AuditWorkerError("the exact 125 new statements changed")
    return rows


def _binding():
    """Bind this invocation to actual source/spec/parent/checker inventories.

    A digest is a worker-consistency check, not proof authority. All ordinary
    bodies are still checked in each family worker. Recompute before and after
    work, so a stale imported factory or concurrent source change fails closed.
    """
    rows = _inventory()
    previous = support.previous_rows()
    if len(previous) != 296:
        raise AuditWorkerError("the two exact inherited research generations changed")
    controls = []
    for relative in CONTROL_SOURCES:
        path = ROOT / relative
        maximum = checkpoints.original.MAX_SOURCE_BYTES
        if not path.is_file() or path.is_symlink() or not 0 < path.stat().st_size <= maximum:
            raise AuditWorkerError("an audit control source is not a bounded regular file")
        with path.open("rb") as stream:
            payload = stream.read(maximum + 1)
        if not 0 < len(payload) <= maximum:
            raise AuditWorkerError("an audit control source changed during its read")
        controls.append({"path": relative, "sha256": sha256(payload).hexdigest()})
    closure = checkpoints.closure
    closure._read_pinned(ROOT / closure.PARENT_CATALOG, closure.PARENT_CATALOG_BYTES,
                         closure.PARENT_CATALOG_SHA256)
    for item in (*checkpoints.original.CHECKPOINTS, *support.lower.CHECKPOINTS, *checkpoints.CHECKPOINTS):
        closure._read_pinned(ROOT / item.artifact, item.artifact_bytes, item.artifact_sha256)
    checkpoints.original._check_lean_binary()
    value = {
        "controls": controls, "checkpoints": [asdict(item) for item in checkpoints.CHECKPOINTS],
        "prior_checkpoints": [asdict(item) for item in (*checkpoints.original.CHECKPOINTS, *support.lower.CHECKPOINTS)],
        "current_specs_sha256": closure._specs_digest(rows),
        "previous_specs_sha256": closure._specs_digest(previous),
        "parent": [closure.PARENT_CATALOG, closure.PARENT_CATALOG_BYTES, closure.PARENT_CATALOG_SHA256],
        "checker": [checkpoints.LEAN_BINARY_BYTES, checkpoints.LEAN_BINARY_SHA256],
    }
    return sha256(_canonical(value)).hexdigest()


def _expected_family_report(checkpoint):
    """Independently derive exact message metadata, without claiming a proof."""
    rows = _inventory()
    owned = checkpoints.load_rows(checkpoint)
    selected = support.select_support(rows, tuple(row.name for row in owned))
    closure = checkpoints.closure
    payload = closure._read_pinned(ROOT / checkpoint.artifact, checkpoint.artifact_bytes, checkpoint.artifact_sha256)
    bundle, _ = decode_proof_bundle(payload.decode("utf-8"))
    positions = {row.name: row.node_id for row in selected.plan.rows}
    by_name = {row.name: row for row in owned}
    result = {
        "slug": checkpoint.slug, "membership": "local_non_admitting_checkpoint",
        "admitted_to_alpha": False, "alpha_checked_use": False, "stable_member": False,
        "new_theorem_count": len(owned),
        "ordered_new_names_sha256": sha256("\n".join(row.name for row in owned).encode()).hexdigest(),
        "new_specs_sha256": checkpoint.frontier_specs_sha256,
        "complete_non_alpha_specs_sha256": selected.plan.frontier_specs_sha256,
        "new_theorem_dependency_edges": sum(len(row.dependencies) for row in owned),
        "new_theorem_tactic_commands": sum(len(row.script) for row in owned),
        "sources": [{"path": pin.path, "sha256": pin.sha256, "factory": pin.factory} for pin in checkpoint.modules],
        "rfc": checkpoint.rfc,
        "support": {
            "prior_bottom_layer_theorems": list(selected.bottom_support),
            "prior_lower_tier_theorems": list(selected.lower_support),
            "current_cross_track_theorems": list(selected.current_support),
            "prior_bottom_layer_count": len(selected.bottom_support),
            "prior_lower_tier_count": len(selected.lower_support),
            "published_non_admitted_count": len(selected.published_support),
            "current_cross_track_count": len(selected.current_support),
            "alpha_v30_count": len(selected.plan.rows) - len(selected.frontier),
            "counted_as_new_owned_theorems": False,
        },
        "bundle": {
            "path": checkpoint.artifact, "bytes": checkpoint.artifact_bytes, "sha256": checkpoint.artifact_sha256,
            "nodes_including_packaging_root": len(bundle.nodes),
            "dependency_edges_including_packaging": sum(len(node.dependencies) for node in bundle.nodes),
            "body_proof_nodes": sum(proof_metrics(node.body)[0] for node in bundle.nodes),
            "packaging_root_id": bundle.root, "original_ha_checked": True, "independent_lean_checked": True,
        },
        "all_maximal_owned_roots": list(selected.plan.root_names),
        "principal_roots": [{"name": name, "node_id": positions[name],
                             "statement_sha256": sha256(by_name[name].statement.encode()).hexdigest(),
                             "complete_ordinary_ha_checked": True} for name in checkpoint.principal_roots],
    }
    del bundle, payload, selected
    gc.collect()
    return result


def _expected_novelty_report():
    rows = _inventory()
    return {"new_theorems": 125, "prior_theorems": 3518,
            "ordered_specs_sha256": checkpoints.closure._specs_digest(rows),
            "duplicates": [], "exact_ast_novelty_checked": True}


def _validate_report(report, expected, *, family):
    # Counts are observational output of the actual checked compiler. Everything
    # identifying a theorem, premise, source, support role, or bundle is exact.
    if family:
        if not isinstance(report, dict) or not isinstance(report.get("principal_roots"), list):
            raise AuditWorkerError("missing ordinary-root reports")
        roots = report["principal_roots"]
        if len(roots) != len(expected["principal_roots"]):
            raise AuditWorkerError("missing or additional ordinary-root reports")
        maximum = checkpoints.closure.DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_occurrences
        expected = {**expected, "principal_roots": [dict(item) for item in expected["principal_roots"]]}
        for actual, wanted in zip(roots, expected["principal_roots"], strict=True):
            count = actual.get("ordinary_certificate_nodes") if isinstance(actual, dict) else None
            if type(count) is not int or not 1 < count <= maximum:
                raise AuditWorkerError("invalid bounded ordinary-certificate size")
            wanted["ordinary_certificate_nodes"] = count
    if _canonical(report) != _canonical(expected):
        raise AuditWorkerError("worker report does not match the exact pinned proof inventory")


def _decode_message(payload):
    if type(payload) is not bytes or not 0 < len(payload) <= MAX_STDOUT_BYTES:
        raise AuditWorkerError("worker output is missing or oversized")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def constant(_):
        raise ValueError("non-finite JSON number")
    try:
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
        if not isinstance(value, dict) or _canonical(value) != payload:
            raise ValueError("noncanonical JSON protocol")
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        raise AuditWorkerError("malformed or noncanonical worker output") from error
    return value


def _validate_message(payload, *, kind, slug, nonce, binding, expected):
    value = _decode_message(payload)
    keys = {"schema", "kind", "slug", "nonce", "binding_sha256", "limits", "peak_rss_bytes", "report"}
    if set(value) != keys:
        raise AuditWorkerError("worker envelope fields changed")
    limits = {"cpu": list(CPU_LIMITS), "wall_seconds": WALL_SECONDS, "max_rss_bytes": MAX_RSS_BYTES}
    wanted = {"schema": WORKER_SCHEMA, "kind": kind, "slug": slug, "nonce": nonce,
              "binding_sha256": binding, "limits": limits}
    if _canonical({key: value[key] for key in wanted}) != _canonical(wanted):
        raise AuditWorkerError("stale, foreign, or incorrectly limited worker response")
    peak = value["peak_rss_bytes"]
    if type(peak) is not int or not 0 < peak <= MAX_RSS_BYTES:
        raise AuditWorkerError("worker exceeded the original RSS ceiling")
    _validate_report(value["report"], expected, family=kind == "family")
    return value["report"], peak


def _capture_bounded(command, environment, *, timeout=PARENT_TIMEOUT_SECONDS):
    """Drain both pipes incrementally; never buffer unbounded subprocess output."""
    process = subprocess.Popen(command, cwd=ROOT, env=environment, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    streams = selectors.DefaultSelector()
    output, errors = bytearray(), bytearray()
    deadline = time.monotonic() + timeout
    finished = False
    try:
        streams.register(process.stdout, selectors.EVENT_READ, (output, MAX_STDOUT_BYTES))
        streams.register(process.stderr, selectors.EVENT_READ, (errors, MAX_STDERR_BYTES))
        while streams.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AuditWorkerError("fresh proof worker exceeded its fixed timeout")
            for key, _ in streams.select(min(remaining, 1.0)):
                chunk = os.read(key.fd, 16 * 1024)
                if not chunk:
                    streams.unregister(key.fileobj)
                    continue
                destination, maximum = key.data
                if len(destination) + len(chunk) > maximum:
                    raise AuditWorkerError("fresh proof worker output exceeded its fixed byte bound")
                destination.extend(chunk)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AuditWorkerError("fresh proof worker exceeded its fixed timeout")
        try:
            status = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as error:
            raise AuditWorkerError("fresh proof worker exceeded its fixed timeout") from error
        if status != 0 or errors:
            diagnostic = bytes(errors).decode("utf-8", errors="replace")[:2048]
            raise AuditWorkerError(f"fresh proof worker failed (status {status}): {diagnostic}")
        finished = True
        return bytes(output)
    finally:
        if not finished:
            # Only the private process group created above is terminated,
            # including a descendant that outlives its failed group leader.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=5)
        streams.close()
        process.stdout.close()
        process.stderr.close()


def _run_worker(kind, slug, binding, expected):
    nonce = secrets.token_hex(32)
    command = [sys.executable, str(SCRIPT), "--worker", kind, "--slug", slug,
               "--nonce", nonce, "--binding", binding]
    environment = os.environ.copy()
    environment.update(PYTHONPATH=os.pathsep.join((str(ROOT / "peano-lab/py"), str(ROOT / "scripts"))),
                       PYTHONMALLOC="malloc", PYTHONNOUSERSITE="1")
    payload = _capture_bounded(command, environment)
    return _validate_message(payload, kind=kind, slug=slug, nonce=nonce, binding=binding, expected=expected)


def _worker(kind, slug, nonce, binding):
    resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)
    signal.alarm(WALL_SECONDS)
    if re.fullmatch(r"[0-9a-f]{64}", nonce or "") is None or re.fullmatch(r"[0-9a-f]{64}", binding or "") is None:
        raise AuditWorkerError("invalid private worker invocation")
    if _binding() != binding:
        raise AuditWorkerError("worker source or inventory differs from its controller")
    if kind == "family":
        selected = [item for item in checkpoints.CHECKPOINTS if item.slug == slug]
        if len(selected) != 1:
            raise AuditWorkerError("unknown exact family worker")
        evidence = checkpoints.verify_checkpoint(selected[0], ordinary_roots=True)
        report = evidence.report
        del evidence
        gc.collect()
    elif kind == "novelty" and slug == "all":
        rows = _inventory()
        duplicates = support.statement_duplicates(rows)
        if duplicates:
            raise AuditWorkerError(f"the exact tranche contains duplicate statements: {duplicates!r}")
        report = _expected_novelty_report()
    else:
        raise AuditWorkerError("unknown exact audit job")
    if _binding() != binding:
        raise AuditWorkerError("sources or inventory changed during actual verification")
    envelope = {"schema": WORKER_SCHEMA, "kind": kind, "slug": slug, "nonce": nonce,
                "binding_sha256": binding, "report": report,
                "limits": {"cpu": list(resource.getrlimit(resource.RLIMIT_CPU)),
                           "wall_seconds": WALL_SECONDS, "max_rss_bytes": MAX_RSS_BYTES},
                "peak_rss_bytes": authoring_rss_bytes()}
    payload = _canonical(envelope)
    if len(payload) > MAX_STDOUT_BYTES:
        raise AuditWorkerError("the actual worker report exceeded its protocol bound")
    envelope["peak_rss_bytes"] = authoring_rss_bytes()
    payload = _canonical(envelope)
    authoring_rss_bytes()
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()
    authoring_rss_bytes()  # A late resource failure makes the exit nonzero.
    return 0


def verify_in_fresh_windows():
    """Only live worker execution, never a stored success report, grants PASS."""
    binding = _binding()
    _, peak = _run_worker("novelty", "all", binding, _expected_novelty_report())
    reports = []
    for item in checkpoints.CHECKPOINTS:
        expected = _expected_family_report(item)
        report, worker_peak = _run_worker("family", item.slug, binding, expected)
        peak = max(peak, worker_peak)
        reports.append(report)
    if _binding() != binding:
        raise AuditWorkerError("sources or inventory changed across fresh audit windows")
    return checkpoints._aggregate_reports(reports), max(peak, authoring_rss_bytes())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    parser.add_argument("--worker", choices=("family", "novelty"), help=argparse.SUPPRESS)
    parser.add_argument("--slug", help=argparse.SUPPRESS)
    parser.add_argument("--nonce", help=argparse.SUPPRESS)
    parser.add_argument("--binding", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        if args.check or args.write or not all((args.slug, args.nonce, args.binding)):
            parser.error("private workers cannot read or write audit receipts")
        return _worker(args.worker, args.slug, args.nonce, args.binding)
    if any((args.slug, args.nonce, args.binding)):
        parser.error("private worker arguments require an exact worker mode")
    resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)
    signal.alarm(CONTROLLER_WALL_SECONDS)
    report, workers_peak = verify_in_fresh_windows()
    encoded = canonical_report(report)
    if args.check:
        check_receipt_bytes(RECEIPT, encoded)
    authoring_rss_bytes()
    if args.write:
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        with RECEIPT.open("x", encoding="utf-8") as stream:
            stream.write(encoded)
    peak = max(workers_peak, authoring_rss_bytes())
    for item in report["checkpoints"]:
        print(f"{item['slug']}: {item['new_theorem_count']} new theorems; complete HA, independent Lean, ordinary roots PASS")
    print(f"Exact AST novelty: {report['new_theorems']} new statements distinct from all 3518 prior rows and each other.")
    print(f"Peak RSS {peak} bytes across fresh bounded windows; Alpha 3222 / Stable 432 unchanged; no admission or publication.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
