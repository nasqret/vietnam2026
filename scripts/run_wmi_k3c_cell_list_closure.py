#!/usr/bin/env python3
"""Produce two cold empty-context closure passes for the Alpha v2 K3C rows.

This is a capacity and admission-receipt harness, not an admission or
submission action.  It accepts only the frozen 17-row K3C tranche and starts
one fresh worker interpreter for each of exactly two passes.  Each worker
closes the selection over the checked-use subset of the exact Alpha v2
parent.  The parent writes a new report only after the two independently
kernel-checked deterministic receipts agree exactly.
"""

from __future__ import annotations

import argparse
import gc
from dataclasses import dataclass, fields
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import re
import secrets
import subprocess
import sys
from typing import Iterable, Sequence

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula, Imp
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library import editions as v1
from peano_lab.library import editions_v2 as v2
from peano_lab.library.alpha_enrollment_v2 import K3C_START_INDEX
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay as replay_stable,
)


FORMAT = "peano-k3c-cell-list-cold-closure-v1"
WORKER_FORMAT = "peano-k3c-cell-list-cold-worker-v1"
EXPECTED_PASSES = 2
EXPECTED_PYTHONHASHSEED = "20260809"
MAX_WORKER_REPORT_BYTES = 16 * 1024 * 1024
EXPECTED_ALPHA_V2_COUNT = 902
EXPECTED_ALPHA_V2_EDGE_COUNT = 2_674
EXPECTED_ALPHA_V2_LAYER_COUNT = 45
EXPECTED_ALPHA_V2_CHECKED_USE_COUNT = 570
EXPECTED_ALPHA_V2_ENROLLMENT_SHA256 = (
    "00f1a70a0911c44acd6b784f2b121b2c351ae626a0f18bb08b5a829496ad40fe"
)
EXPECTED_ALPHA_V2_IDENTITY_SHA256 = (
    "aadf99c0e411fcefe34285c8396ff0652f590e6990f0d55c3e6c7b728f9b43a4"
)
EXPECTED_TARGET_EDGE_COUNT = 33
EXPECTED_TARGET_GRAPH_SHA256 = (
    "b1dd6e67e085817c41a4608c12b176c7bdeab7e785d4e9a35592626f5a53fb1c"
)
EXPECTED_TARGET_SURFACE_SHA256 = (
    "448b1e07315f2d9e8430f049fa89760223b2e838ff203daeeda87410ed76a338"
)


@dataclass(frozen=True, slots=True)
class TargetSurface:
    """Frozen source-facing identity for one K3C target."""

    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]


TARGET_SURFACES: tuple[TargetSurface, ...] = (
    TargetSurface(
        "cell_list_valid_nil",
        "5ec6b2e7ef6f193917b42834c4b0c51cfde4af18da2975e43f574ee0379458ec",
        ("cell_history_nil",),
    ),
    TargetSurface(
        "cell_list_valid_cell_intro",
        "59a76ea4ba8f61e3b872d777eacac869254eef33709905018c644e658b74c649",
        ("cell_list_succ_iff_cell",),
    ),
    TargetSurface(
        "cell_list_valid_cases",
        "8945d1b66d00c6fba46c1671873f6f597e7673480550962700f94623837eb287",
        ("cell_list_zero_iff_nil", "cell_list_succ_iff_cell"),
    ),
    TargetSurface(
        "cell_list_valid_cell_elim",
        "ee10fcc3b285e1f794211a3d4970d2fc057da18fcf5ec06c6f6270b32896c153",
        ("cell_list_valid_cases", "nil_not_cell", "cell_functional"),
    ),
    TargetSurface(
        "list_at_implies_cell_list_valid",
        "71299df15dfee548ac46ba9e42ebcd01f48fb2b1f42c346d64de75215c42d1d1",
        ("list_at_domain",),
    ),
    TargetSurface(
        "list_member_implies_cell_list_valid",
        "a281b55116f652714259c898542a85cd24941be57d14b45ef7c9902463dd04b9",
        ("list_at_implies_cell_list_valid",),
    ),
    TargetSurface(
        "list_member_nil_false",
        "24674ce7d90e8f21eae002ce1c8edf78ef091d96c1d29f9e2c77312fd4582018",
        (
            "list_at_domain",
            "cell_list_zero_iff_nil",
            "cell_list_length_functional",
            "add_eq_zero_right",
            "succ_ne_zero",
        ),
    ),
    TargetSurface(
        "list_member_cell_intro_head",
        "6a65cbdf21e84f6e4816ad3907b7d03a8c4471d02770b72f54448cec75de9ad9",
        ("list_at_head_iff",),
    ),
    TargetSurface(
        "list_member_cell_intro_tail",
        "25b0fdd45f0b5c7b3a7d3b7c91474f22de2697c61046d749d151733bc1e2b7f5",
        ("list_at_succ_iff",),
    ),
    TargetSurface(
        "list_member_cell_elim",
        "55ebbef79b611124c4640f827011260ecc1484648456893f9a35df3896de613f",
        ("list_at_head_iff", "list_at_succ_iff", "cell_functional"),
    ),
    TargetSurface(
        "list_member_cell_iff",
        "9fa08a27b5a2d3aa21411924525736961a131fe83fd96c4526adf8ab13596ad4",
        (
            "list_member_cell_elim",
            "list_member_cell_intro_head",
            "list_member_cell_intro_tail",
        ),
    ),
    TargetSurface(
        "list_member_pointwise_transport",
        "2cec4de0dc94ada411ad0884d093baffdb8c3fba5297629251bca2a83c57b0e2",
        ("list_at_external_bound", "list_at_exists"),
    ),
    TargetSurface(
        "list_at_exists_unique",
        "59f950707e749b1e9354d352881d8653c33cc55dde26fb8c2de03648963bbb19",
        ("list_at_exists", "list_at_functional"),
    ),
    TargetSurface(
        "cell_list_nonempty_iff_head_exists",
        "26d902cb638d60a8fe06fe2a15848764c21830bd021aab0314ed9277f1ae0e95",
        ("list_at_head_iff", "cell_list_succ_iff_cell"),
    ),
    TargetSurface(
        "cell_list_code_eq_lookup_values",
        "cafd660a805a10d988458c61a3ba4b8e6b8c35e02e89f19f625eee4557afd7eb",
        ("list_at_functional",),
    ),
    TargetSurface(
        "cell_list_code_eq_iff_pointwise",
        "ff28e1e269f7309a68bec117518ae6c520b36295e40404eb8a0630e3fec8b6bb",
        ("cell_list_code_eq_lookup_values", "cell_list_extensional"),
    ),
    TargetSurface(
        "cell_list_decompose_unique",
        "74d498c91cdf9dac58e09c6167920d2d58f01aa7419dc28c7d388f348b991ccb",
        ("cell_list_succ_iff_cell", "cell_functional"),
    ),
)
TARGET_NAMES = tuple(item.name for item in TARGET_SURFACES)

SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
POSITIVE_PATTERN = re.compile(r"[1-9][0-9]*")
EXPECTED_RESOURCES = {
    "partition": "cpu_idle",
    "nodes": 1,
    "ntasks": 1,
    "cpus_per_task": 1,
    "memory_mib": 32_768,
    "time_limit": "04:00:00",
    "time_limit_seconds": 14_400,
}


class ClosureError(RuntimeError):
    """The parent, target graph, closure, or receipt failed validation."""


def _required_environment(name: str, pattern: re.Pattern[str]) -> str:
    value = os.environ.get(name, "")
    if pattern.fullmatch(value) is None:
        raise ClosureError(f"missing or malformed {name}")
    return value


def _provenance() -> dict[str, object]:
    dirty = os.environ.get("PEANO_K3C_LOCAL_DIRTY", "")
    if dirty not in {"true", "false"}:
        raise ClosureError("PEANO_K3C_LOCAL_DIRTY must be true or false")
    return {
        "local_commit": _required_environment(
            "PEANO_K3C_LOCAL_COMMIT", COMMIT_PATTERN
        ),
        "local_dirty": dirty == "true",
        "payload_sha256": _required_environment(
            "PEANO_K3C_PAYLOAD_SHA256", SHA256_PATTERN
        ),
    }


def _resources() -> dict[str, object]:
    observed: dict[str, object] = {
        "partition": _required_environment(
            "PEANO_K3C_REQUESTED_PARTITION", re.compile(r"[A-Za-z0-9_-]+")
        ),
        "nodes": int(
            _required_environment(
                "PEANO_K3C_REQUESTED_NODES", POSITIVE_PATTERN
            )
        ),
        "ntasks": int(
            _required_environment(
                "PEANO_K3C_REQUESTED_NTASKS", POSITIVE_PATTERN
            )
        ),
        "cpus_per_task": int(
            _required_environment(
                "PEANO_K3C_REQUESTED_CPUS_PER_TASK", POSITIVE_PATTERN
            )
        ),
        "memory_mib": int(
            _required_environment(
                "PEANO_K3C_REQUESTED_MEMORY_MIB", POSITIVE_PATTERN
            )
        ),
        "time_limit": _required_environment(
            "PEANO_K3C_REQUESTED_TIME_LIMIT",
            re.compile(r"(?:[0-9]+-)?[0-9]{2}:[0-9]{2}:[0-9]{2}"),
        ),
        "time_limit_seconds": int(
            _required_environment(
                "PEANO_K3C_REQUESTED_TIME_LIMIT_SECONDS", POSITIVE_PATTERN
            )
        ),
    }
    if observed != EXPECTED_RESOURCES:
        raise ClosureError(
            f"resource profile mismatch: {observed!r} != "
            f"{EXPECTED_RESOURCES!r}"
        )
    return observed


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for field in fields(proof)
        if isinstance((child := getattr(proof, field.name)), Proof)
    )


def _walk_unique(proof: Proof) -> Iterable[Proof]:
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        yield node
        pending.extend(_proof_children(node))


def _proof_dag_sha256(proof: Proof) -> str:
    """Merkle-hash a proof DAG iteratively, without Python recursion."""

    digests: dict[int, str] = {}
    pending: list[tuple[Proof, bool]] = [(proof, False)]
    while pending:
        node, expanded = pending.pop()
        identity = id(node)
        if identity in digests:
            continue
        children = _proof_children(node)
        if not expanded:
            pending.append((node, True))
            pending.extend(
                (child, False)
                for child in children
                if id(child) not in digests
            )
            continue
        payload = [type(node).__name__]
        for field in fields(node):
            value = getattr(node, field.name)
            if isinstance(value, Proof):
                child_digest = digests.get(id(value))
                if child_digest is None:
                    raise ClosureError("cyclic or malformed proof object graph")
                payload.append(child_digest)
            else:
                payload.append(repr(value))
        digests[identity] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def _target_graph_sha256(specs: Sequence[TheoremSpec]) -> str:
    rows = (
        "\x1f".join((item.name, "\x1e".join(item.dependencies)))
        for item in specs
    )
    return sha256("\x1c".join(rows).encode()).hexdigest()


def _target_surface_sha256(specs: Sequence[TheoremSpec]) -> str:
    rows = (
        "\x1f".join(
            (
                item.name,
                sha256(item.statement.encode()).hexdigest(),
                "\x1e".join(item.dependencies),
            )
        )
        for item in specs
    )
    return sha256("\x1c".join(rows).encode()).hexdigest()


def _parent_receipt() -> dict[str, object]:
    observed = {
        "alpha_v2_checked_use_count": len(v2.ALPHA_CHECKED_SPECS),
        "alpha_v2_edge_count": v2.ALPHA_EDITION.edge_count,
        "alpha_v2_enrollment_sha256": v2.ALPHA_V2_ENROLLMENT_SHA256,
        "alpha_v2_identity_sha256": v2.ALPHA_V2_IDENTITY_SHA256,
        "alpha_v2_layer_count": v2.ALPHA_EDITION.layer_count,
        "alpha_v2_theorem_count": len(v2.ALPHA_ENTRIES),
    }
    expected = {
        "alpha_v2_checked_use_count": EXPECTED_ALPHA_V2_CHECKED_USE_COUNT,
        "alpha_v2_edge_count": EXPECTED_ALPHA_V2_EDGE_COUNT,
        "alpha_v2_enrollment_sha256": EXPECTED_ALPHA_V2_ENROLLMENT_SHA256,
        "alpha_v2_identity_sha256": EXPECTED_ALPHA_V2_IDENTITY_SHA256,
        "alpha_v2_layer_count": EXPECTED_ALPHA_V2_LAYER_COUNT,
        "alpha_v2_theorem_count": EXPECTED_ALPHA_V2_COUNT,
    }
    if observed != expected:
        raise ClosureError(
            f"Alpha v2 parent mismatch: {observed!r} != {expected!r}"
        )
    return observed


def _local_specs() -> dict[str, TheoremSpec]:
    _parent_receipt()
    entries = v2.ALPHA_ENTRIES[K3C_START_INDEX:]
    if tuple(item.spec.name for item in entries) != TARGET_NAMES:
        raise ClosureError("Alpha v2 K3C target order drifted")
    if len(entries) != len(TARGET_SURFACES):
        raise ClosureError("Alpha v2 K3C target count drifted")

    specs: list[TheoremSpec] = []
    for expected, entry in zip(TARGET_SURFACES, entries, strict=True):
        item = entry.spec
        if type(item) is not TheoremSpec:
            raise ClosureError(f"invalid K3C theorem specification {item!r}")
        if (
            entry.membership is not v2.Membership.ALPHA_ONLY
            or entry.evidence is not v2.EvidenceStatus.BODY_CHECKED
            or entry.enrollment_origin is not v2.EnrollmentOrigin.K3C
            or entry.provenance != (v2.EnrollmentOrigin.K3C,)
        ):
            raise ClosureError(f"K3C metadata drifted for {item.name!r}")
        statement_sha256 = sha256(item.statement.encode()).hexdigest()
        if (
            item.name != expected.name
            or statement_sha256 != expected.statement_sha256
            or item.dependencies != expected.dependencies
        ):
            raise ClosureError(f"K3C surface drifted for {expected.name!r}")
        if any("DNE" in command for command in item.script):
            raise ClosureError(f"K3C script {item.name!r} contains DNE")
        _closed_formula(item.statement)
        specs.append(item)

    if sum(len(item.dependencies) for item in specs) != EXPECTED_TARGET_EDGE_COUNT:
        raise ClosureError("K3C direct dependency edge count drifted")
    if _target_graph_sha256(specs) != EXPECTED_TARGET_GRAPH_SHA256:
        raise ClosureError("K3C dependency graph identity drifted")
    if _target_surface_sha256(specs) != EXPECTED_TARGET_SURFACE_SHA256:
        raise ClosureError("K3C target surface identity drifted")
    return {item.name: item for item in specs}


def _public_specs() -> dict[str, TheoremSpec]:
    table = {item.name: item for item in v2.ALPHA_CHECKED_SPECS}
    if len(table) != EXPECTED_ALPHA_V2_CHECKED_USE_COUNT:
        raise ClosureError("Alpha v2 checked-use table contains duplicates")
    for item in table.values():
        unavailable = set(item.dependencies).difference(table)
        if unavailable:
            raise ClosureError(
                f"checked parent {item.name!r} depends on unchecked rows "
                f"{sorted(unavailable)!r}"
            )
    return table


def _dependency_closure(
    selected: tuple[str, ...],
    local: dict[str, TheoremSpec],
    public: dict[str, TheoremSpec],
) -> tuple[str, ...]:
    overlap = set(public) & set(local)
    if overlap:
        raise ClosureError(
            f"body-only K3C rows crossed checked use: {sorted(overlap)!r}"
        )
    available = dict(public)
    available.update(local)
    complete: set[str] = set()
    active: set[str] = set()

    def visit(name: str) -> None:
        if name in complete:
            return
        if name in active:
            raise ClosureError(f"dependency cycle at {name!r}")
        item = available.get(name)
        if item is None:
            raise ClosureError(f"unknown dependency {name!r}")
        active.add(name)
        for dependency in item.dependencies:
            visit(dependency)
        active.remove(name)
        complete.add(name)

    for name in selected:
        if name not in local:
            raise ClosureError(f"unknown K3C target {name!r}")
        visit(name)
    return tuple(sorted(complete))


def _clear_replay_caches() -> None:
    v2.replay.cache_clear()
    v1._replay_alpha_closed.cache_clear()
    replay_stable.cache_clear()
    _specs_by_name.cache_clear()


def _close_pass(selected: tuple[str, ...]) -> dict[str, dict[str, object]]:
    _clear_replay_caches()
    local = _local_specs()
    public = _public_specs()
    closure_names = set(_dependency_closure(selected, local, public))
    closed: dict[str, tuple[Formula, Proof]] = {}
    active: set[str] = set()

    def close(name: str) -> tuple[Formula, Proof]:
        cached = closed.get(name)
        if cached is not None:
            return cached
        if name in active:
            raise ClosureError(f"recursive closure cycle at {name!r}")
        if name in public:
            checked = v2.replay(name, edition=v2.EditionName.ALPHA)
            result = (checked.formula, checked.certificate)
            closed[name] = result
            return result
        item = local.get(name)
        if item is None:
            raise ClosureError(f"cannot close unknown theorem {name!r}")

        active.add(name)
        formula = _closed_formula(item.statement)
        dependency_specs: list[TheoremSpec] = []
        for dependency in item.dependencies:
            dependency_spec = local.get(dependency) or public.get(dependency)
            if dependency_spec is None:
                raise ClosureError(
                    f"{name!r} has unknown dependency {dependency!r}"
                )
            dependency_specs.append(dependency_spec)
        target = formula
        for dependency_spec in reversed(dependency_specs):
            target = Imp(_closed_formula(dependency_spec.statement), target)

        state = start(target)
        for dependency in item.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for index, command in enumerate(item.script):
            try:
                tactic, arguments = _primitive(command)
                state = apply_tactic(state, tactic, arguments)
            except Exception as exc:
                raise ClosureError(
                    f"{name!r} failed at command {index}: {command!r}: {exc}"
                ) from exc
        body = checked_final(state, target)
        for dependency in item.dependencies:
            if type(body) is not ImpIntro:
                raise ClosureError(
                    f"{name!r} did not expose dependency {dependency!r}"
                )
            body = body.body
        for dependency in reversed(item.dependencies):
            dependency_formula, dependency_proof = close(dependency)
            body = Cut(dependency_formula, formula, dependency_proof, body)
        if not check((), body, formula):
            raise ClosureError(
                f"kernel rejected empty-context closure {name!r}"
            )
        active.remove(name)
        result = (formula, body)
        closed[name] = result
        return result

    try:
        receipts: dict[str, dict[str, object]] = {}
        for name in selected:
            formula, certificate = close(name)
            if not check((), certificate, formula):
                raise ClosureError(f"kernel rejected selected target {name!r}")
            nodes, depth = proof_metrics(certificate)
            objects, edges, reused = proof_identity_metrics(certificate)
            cuts = 0
            dne = 0
            for node in _walk_unique(certificate):
                cuts += type(node) is Cut
                dne += type(node) is DNE
            if dne != 0:
                raise ClosureError(f"{name!r} contains {dne} DNE object(s)")
            item = local[name]
            target_closure = _dependency_closure((name,), local, public)
            receipts[name] = {
                "cuts": cuts,
                "dependency_closure_count": len(target_closure),
                "dependency_closure_sha256": sha256(
                    "\n".join(target_closure).encode()
                ).hexdigest(),
                "direct_dependencies": list(item.dependencies),
                "dne_objects": dne,
                "proof_dag_sha256": _proof_dag_sha256(certificate),
                "proof_depth": depth,
                "proof_edges": edges,
                "proof_nodes": nodes,
                "proof_objects": objects,
                "reused_objects": reused,
                "script_commands": len(item.script),
                "script_sha256": sha256(
                    "\n".join(item.script).encode()
                ).hexdigest(),
                "statement_characters": len(item.statement),
                "statement_sha256": sha256(
                    item.statement.encode()
                ).hexdigest(),
            }
        if not set(selected).issubset(closed):
            raise ClosureError("selected closure was incomplete")
        if not set(closed).issubset(closure_names):
            raise ClosureError("closure escaped the audited dependency graph")
        return receipts
    finally:
        _clear_replay_caches()


def _canonical_json_bytes(payload: dict[str, object]) -> bytes:
    return (
        json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _write_report(path: Path, payload: dict[str, object]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ClosureError(f"refusing to overwrite report {path}")
    encoded = _canonical_json_bytes(payload)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _environment_receipt() -> dict[str, str]:
    return {
        "python_executable": sys.executable,
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "pythonhashseed": os.environ["PYTHONHASHSEED"],
    }


def _deterministic_receipt(
    selected: tuple[str, ...],
    parent: dict[str, object],
    provenance: dict[str, object],
    resources: dict[str, object],
    results: dict[str, dict[str, object]],
) -> dict[str, object]:
    return {
        "environment": _environment_receipt(),
        "parent": parent,
        "provenance": provenance,
        "requested_resources": resources,
        "results": results,
        "selected_theorems": list(selected),
        "target_graph_sha256": EXPECTED_TARGET_GRAPH_SHA256,
        "target_surface_sha256": EXPECTED_TARGET_SURFACE_SHA256,
    }


def _worker_payload(
    pass_index: int,
    parent_pid: int,
    receipt: dict[str, object],
) -> dict[str, object]:
    return {
        "format": WORKER_FORMAT,
        "pass_index": pass_index,
        "process": {
            "parent_pid": parent_pid,
            "pid": os.getpid(),
            "process_nonce": secrets.token_hex(16),
        },
        "receipt": receipt,
        "schema_version": 1,
        "status": "passed",
    }


def _worker_main(args: argparse.Namespace) -> int:
    if args.worker_report is None:
        raise ClosureError("worker report path is required")
    if args.worker_pass_index not in {1, 2}:
        raise ClosureError("worker pass index must be 1 or 2")
    if args.worker_parent_pid is None or args.worker_parent_pid <= 0:
        raise ClosureError("worker parent PID is required")
    if os.getppid() != args.worker_parent_pid:
        raise ClosureError("worker was not launched by the attested parent")
    if args.report is not None or args.list_theorems:
        raise ClosureError("worker mode cannot write the final report")
    if args.passes != EXPECTED_PASSES:
        raise ClosureError("worker requires the frozen two-pass profile")

    selected = _selected(args.theorem)
    parent = _parent_receipt()
    provenance = _provenance()
    resources = _resources()
    if os.environ.get("PYTHONHASHSEED") != EXPECTED_PYTHONHASHSEED:
        raise ClosureError(
            f"PYTHONHASHSEED must be exactly {EXPECTED_PYTHONHASHSEED}"
        )
    results = _close_pass(selected)
    gc.collect()
    receipt = _deterministic_receipt(
        selected, parent, provenance, resources, results
    )
    payload = _worker_payload(
        args.worker_pass_index, args.worker_parent_pid, receipt
    )
    _write_report(args.worker_report, payload)
    print(
        f"K3C WORKER PASS {args.worker_pass_index}/{EXPECTED_PASSES} "
        f"pid={os.getpid()}",
        flush=True,
    )
    return 0


def _worker_environment() -> dict[str, str]:
    environment = os.environ.copy()
    repository = Path(__file__).resolve().parents[1]
    peano_python = str(repository / "peano-lab" / "py")
    inherited = environment.get("PYTHONPATH", "")
    entries = tuple(item for item in inherited.split(os.pathsep) if item)
    if peano_python not in entries:
        environment["PYTHONPATH"] = os.pathsep.join(
            (peano_python,) + entries
        )
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.pop("PYTHONOPTIMIZE", None)
    return environment


def _worker_command(
    pass_index: int,
    parent_pid: int,
    selected: tuple[str, ...],
    worker_report: Path,
) -> list[str]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--passes",
        str(EXPECTED_PASSES),
        "--worker-report",
        str(worker_report),
        "--worker-pass-index",
        str(pass_index),
        "--worker-parent-pid",
        str(parent_pid),
    ]
    for name in selected:
        command.extend(("--theorem", name))
    return command


def _validate_result_receipts(
    results: object,
    selected: tuple[str, ...],
) -> None:
    if type(results) is not dict or set(results) != set(selected):
        raise ClosureError("worker result target set mismatch")
    local = _local_specs()
    expected_keys = {
        "cuts",
        "dependency_closure_count",
        "dependency_closure_sha256",
        "direct_dependencies",
        "dne_objects",
        "proof_dag_sha256",
        "proof_depth",
        "proof_edges",
        "proof_nodes",
        "proof_objects",
        "reused_objects",
        "script_commands",
        "script_sha256",
        "statement_characters",
        "statement_sha256",
    }
    for name in selected:
        result = results.get(name)
        if type(result) is not dict or set(result) != expected_keys:
            raise ClosureError(f"worker result schema mismatch for {name!r}")
        item = local[name]
        if result["direct_dependencies"] != list(item.dependencies):
            raise ClosureError(f"worker dependencies drifted for {name!r}")
        if result["statement_sha256"] != sha256(
            item.statement.encode()
        ).hexdigest():
            raise ClosureError(f"worker statement drifted for {name!r}")
        if result["script_sha256"] != sha256(
            "\n".join(item.script).encode()
        ).hexdigest():
            raise ClosureError(f"worker script drifted for {name!r}")
        if result["dne_objects"] != 0:
            raise ClosureError(f"worker found DNE in {name!r}")
        for field_name in (
            "cuts",
            "dependency_closure_count",
            "proof_depth",
            "proof_edges",
            "proof_nodes",
            "proof_objects",
            "reused_objects",
            "script_commands",
            "statement_characters",
        ):
            value = result[field_name]
            if type(value) is not int or value < 0:
                raise ClosureError(
                    f"invalid worker metric {field_name!r} for {name!r}"
                )
        for field_name in (
            "dependency_closure_sha256",
            "proof_dag_sha256",
            "script_sha256",
            "statement_sha256",
        ):
            value = result[field_name]
            if type(value) is not str or SHA256_PATTERN.fullmatch(value) is None:
                raise ClosureError(
                    f"invalid worker digest {field_name!r} for {name!r}"
                )


def _validate_worker_payload(
    payload: object,
    pass_index: int,
    parent_pid: int,
    selected: tuple[str, ...],
    expected_receipt: dict[str, object],
) -> dict[str, object]:
    if type(payload) is not dict or set(payload) != {
        "format",
        "pass_index",
        "process",
        "receipt",
        "schema_version",
        "status",
    }:
        raise ClosureError("worker payload schema mismatch")
    if (
        payload["format"] != WORKER_FORMAT
        or payload["schema_version"] != 1
        or payload["status"] != "passed"
        or payload["pass_index"] != pass_index
    ):
        raise ClosureError("worker payload header mismatch")
    process = payload["process"]
    if type(process) is not dict or set(process) != {
        "parent_pid",
        "pid",
        "process_nonce",
    }:
        raise ClosureError("worker process receipt schema mismatch")
    if process["parent_pid"] != parent_pid:
        raise ClosureError("worker parent PID mismatch")
    if type(process["pid"]) is not int or process["pid"] <= 0:
        raise ClosureError("worker PID is invalid")
    nonce = process["process_nonce"]
    if type(nonce) is not str or re.fullmatch(r"[0-9a-f]{32}", nonce) is None:
        raise ClosureError("worker process nonce is invalid")

    receipt = payload["receipt"]
    if type(receipt) is not dict or set(receipt) != set(expected_receipt):
        raise ClosureError("worker deterministic receipt schema mismatch")
    static = dict(receipt)
    results = static.pop("results", None)
    expected_static = dict(expected_receipt)
    expected_static.pop("results", None)
    if static != expected_static:
        raise ClosureError("worker deterministic receipt metadata mismatch")
    _validate_result_receipts(results, selected)
    return payload


def _read_worker_payload(path: Path) -> tuple[dict[str, object], str]:
    if path.is_symlink() or not path.is_file():
        raise ClosureError("worker did not create a regular receipt file")
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_WORKER_REPORT_BYTES or not raw.endswith(b"\n"):
        raise ClosureError("worker receipt byte envelope is invalid")
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosureError("worker receipt is not canonical JSON") from exc
    if _canonical_json_bytes(payload) != raw:
        raise ClosureError("worker receipt JSON is not canonically encoded")
    if type(payload) is not dict:
        raise ClosureError("worker receipt root must be an object")
    return payload, sha256(raw).hexdigest()


def _run_worker(
    pass_index: int,
    selected: tuple[str, ...],
    final_report: Path,
    expected_receipt: dict[str, object],
) -> dict[str, object]:
    parent_pid = os.getpid()
    token = secrets.token_hex(8)
    worker_report = final_report.parent / (
        f".{final_report.name}.pass-{pass_index}.{parent_pid}.{token}.json"
    )
    if worker_report.exists() or worker_report.is_symlink():
        raise ClosureError("refusing an existing worker receipt path")
    command = _worker_command(
        pass_index, parent_pid, selected, worker_report
    )
    print(
        f"K3C COLD PROCESS {pass_index}/{EXPECTED_PASSES}: "
        f"{','.join(selected)}",
        flush=True,
    )
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            env=_worker_environment(),
            text=True,
        )
        if completed.returncode != 0:
            diagnostic = (completed.stderr or completed.stdout).strip()[-4000:]
            raise ClosureError(
                f"cold worker {pass_index} failed with exit "
                f"{completed.returncode}: {diagnostic}"
            )
        payload, payload_sha256 = _read_worker_payload(worker_report)
        validated = _validate_worker_payload(
            payload,
            pass_index,
            parent_pid,
            selected,
            expected_receipt,
        )
        return {
            "worker_payload": validated,
            "worker_payload_sha256": payload_sha256,
        }
    finally:
        worker_report.unlink(missing_ok=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--theorem",
        action="append",
        choices=TARGET_NAMES,
        help="target to close; repeat to select several (default: all 17)",
    )
    parser.add_argument(
        "--passes",
        type=int,
        default=EXPECTED_PASSES,
        help="must remain exactly two cold passes",
    )
    parser.add_argument("--report", type=Path, help="new JSON receipt path")
    parser.add_argument(
        "--list-theorems",
        action="store_true",
        help="print the frozen target order and exit",
    )
    parser.add_argument(
        "--worker-report", type=Path, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--worker-pass-index", type=int, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--worker-parent-pid", type=int, help=argparse.SUPPRESS
    )
    return parser


def _arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return _parser().parse_args(argv)


def _selected(requested: Sequence[str] | None) -> tuple[str, ...]:
    if not requested:
        return TARGET_NAMES
    if len(requested) != len(set(requested)):
        raise ClosureError("duplicate --theorem selection")
    unknown = set(requested).difference(TARGET_NAMES)
    if unknown:
        raise ClosureError(f"unknown K3C target(s): {sorted(unknown)!r}")
    wanted = set(requested)
    return tuple(name for name in TARGET_NAMES if name in wanted)


def main(argv: Sequence[str] | None = None) -> int:
    args = _arguments(argv)
    worker_arguments = (
        args.worker_report,
        args.worker_pass_index,
        args.worker_parent_pid,
    )
    if any(value is not None for value in worker_arguments):
        if not all(value is not None for value in worker_arguments):
            raise ClosureError("incomplete cold-worker invocation")
        return _worker_main(args)
    if args.list_theorems:
        print("\n".join(TARGET_NAMES))
        return 0
    if args.report is None:
        raise ClosureError("--report is required")
    if args.passes != EXPECTED_PASSES:
        raise ClosureError("K3C admission requires exactly two cold passes")

    selected = _selected(args.theorem)
    parent = _parent_receipt()
    provenance = _provenance()
    resources = _resources()
    if os.environ.get("PYTHONHASHSEED") != EXPECTED_PYTHONHASHSEED:
        raise ClosureError(
            f"PYTHONHASHSEED must be exactly {EXPECTED_PYTHONHASHSEED}"
        )

    final_report = args.report.resolve()
    final_report.parent.mkdir(parents=True, exist_ok=True)
    if final_report.exists() or final_report.is_symlink():
        raise ClosureError(f"refusing to overwrite report {final_report}")
    expected_receipt = _deterministic_receipt(
        selected, parent, provenance, resources, {}
    )
    cold_passes = tuple(
        _run_worker(index, selected, final_report, expected_receipt)
        for index in range(1, EXPECTED_PASSES + 1)
    )
    worker_payloads = tuple(item["worker_payload"] for item in cold_passes)
    receipts = tuple(item["receipt"] for item in worker_payloads)
    if receipts[0] != receipts[1]:
        raise ClosureError("fresh cold-process receipts were nondeterministic")
    processes = tuple(item["process"] for item in worker_payloads)
    worker_pids = tuple(item["pid"] for item in processes)
    process_nonces = tuple(item["process_nonce"] for item in processes)
    if (
        len(set(worker_pids)) != EXPECTED_PASSES
        or os.getpid() in worker_pids
        or len(set(process_nonces)) != EXPECTED_PASSES
    ):
        raise ClosureError("cold passes did not use distinct fresh processes")
    common = receipts[0]

    payload: dict[str, object] = {
        "cold_passes": list(cold_passes),
        "deterministic_across_passes": True,
        "environment": common["environment"],
        "format": FORMAT,
        "parent": parent,
        "passes": EXPECTED_PASSES,
        "provenance": provenance,
        "requested_resources": resources,
        "results": common["results"],
        "schema_version": 1,
        "selected_theorems": list(selected),
        "status": "passed",
        "target_graph_sha256": EXPECTED_TARGET_GRAPH_SHA256,
        "target_surface_sha256": EXPECTED_TARGET_SURFACE_SHA256,
    }
    _write_report(final_report, payload)
    print(f"K3C PASS report={final_report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
