#!/usr/bin/env python3
"""Cold, empty-context closure receipts for the private K3B list seed.

This runner is intentionally separate from pytest and from the public theorem
registry.  It closes the five initial CellHistory/list-equation candidates,
RFC deliverables 8--10, and the first prefix-preserving lookup-support row over
the minimum private strict-cell support plus the reviewed public library.  It
is a WMI capacity/admission experiment, not an admission action.
"""

from __future__ import annotations

import argparse
import gc
from dataclasses import fields
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import re
import sys
from typing import Callable, Iterable

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import apply_tactic, checked_final
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula, Imp
from peano_lab.kernel.proofs import Cut, DNE, ImpIntro, Proof
from peano_lab.library.ha_cell_bounds_candidate import (
    make_ha_cell_bounds_candidate_theorems,
)
from peano_lab.library.ha_cell_functional_candidate import (
    make_ha_cell_functional_candidate_theorems,
)
from peano_lab.library.ha_cell_history_candidate import (
    make_ha_cell_history_candidate_theorems,
)
from peano_lab.library.ha_cell_history_prefix_preservation_candidate import (
    make_ha_cell_history_prefix_preservation_candidate_theorems,
)
from peano_lab.library.ha_cell_list_equations_candidate import (
    make_ha_cell_list_equations_candidate_theorems,
)
from peano_lab.library.ha_cell_list_length_bound_candidate import (
    make_ha_cell_list_length_bound_candidate_theorems,
)
from peano_lab.library.ha_cell_list_length_functional_candidate import (
    make_ha_cell_list_length_functional_candidate_theorems,
)
from peano_lab.library.ha_cell_list_length_total_candidate import (
    make_ha_cell_list_length_total_candidate_theorems,
)
from peano_lab.library.ha_pair_cell_seed_candidate import (
    make_ha_pair_cell_seed_candidate_theorems,
)
from peano_lab.library.ha_pair_injective_candidate import (
    make_ha_pair_injective_candidate_theorems,
)
from peano_lab.library.ha_pair_shell_candidate import (
    make_ha_pair_shell_candidate_theorems,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


FORMAT = "peano-k3b-cell-history-cold-closure-v2"
TARGET_NAMES = (
    "cell_history_nil",
    "cell_history_extend",
    "cell_history_succ_elim",
    "cell_history_extend_preserves_prefix",
    "cell_list_zero_iff_nil",
    "cell_list_succ_iff_cell",
    "cell_list_length_functional",
    "cell_list_length_le_code",
    "cell_list_length_total",
)
Factory = Callable[[type[TheoremSpec]], tuple[TheoremSpec, ...]]
SUPPORT_FACTORIES: tuple[Factory, ...] = (
    make_ha_pair_cell_seed_candidate_theorems,
    make_ha_pair_shell_candidate_theorems,
    make_ha_pair_injective_candidate_theorems,
    make_ha_cell_functional_candidate_theorems,
    make_ha_cell_bounds_candidate_theorems,
)
TARGET_FACTORIES: tuple[Factory, ...] = (
    make_ha_cell_history_candidate_theorems,
    make_ha_cell_history_prefix_preservation_candidate_theorems,
    make_ha_cell_list_equations_candidate_theorems,
    make_ha_cell_list_length_functional_candidate_theorems,
    make_ha_cell_list_length_bound_candidate_theorems,
    make_ha_cell_list_length_total_candidate_theorems,
)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
POSITIVE_PATTERN = re.compile(r"[1-9][0-9]*")
EXPECTED_RESOURCES = {
    "partition": "cpu_idle",
    "nodes": 1,
    "ntasks": 1,
    "cpus_per_task": 1,
    "memory_mib": 32768,
    "time_limit": "04:00:00",
    "time_limit_seconds": 14400,
}


class ClosureError(RuntimeError):
    """The frozen graph, closure, kernel check, or receipt is invalid."""


def _required_environment(name: str, pattern: re.Pattern[str]) -> str:
    value = os.environ.get(name, "")
    if pattern.fullmatch(value) is None:
        raise ClosureError(f"missing or malformed {name}")
    return value


def _provenance() -> dict[str, object]:
    dirty = os.environ.get("PEANO_K3B_LOCAL_DIRTY", "")
    if dirty not in {"true", "false"}:
        raise ClosureError("PEANO_K3B_LOCAL_DIRTY must be true or false")
    return {
        "local_commit": _required_environment(
            "PEANO_K3B_LOCAL_COMMIT", COMMIT_PATTERN
        ),
        "local_dirty": dirty == "true",
        "payload_sha256": _required_environment(
            "PEANO_K3B_PAYLOAD_SHA256", SHA256_PATTERN
        ),
    }


def _resources() -> dict[str, object]:
    observed: dict[str, object] = {
        "partition": _required_environment(
            "PEANO_K3B_REQUESTED_PARTITION", re.compile(r"[A-Za-z0-9_-]+")
        ),
        "nodes": int(_required_environment(
            "PEANO_K3B_REQUESTED_NODES", POSITIVE_PATTERN
        )),
        "ntasks": int(_required_environment(
            "PEANO_K3B_REQUESTED_NTASKS", POSITIVE_PATTERN
        )),
        "cpus_per_task": int(_required_environment(
            "PEANO_K3B_REQUESTED_CPUS_PER_TASK", POSITIVE_PATTERN
        )),
        "memory_mib": int(_required_environment(
            "PEANO_K3B_REQUESTED_MEMORY_MIB", POSITIVE_PATTERN
        )),
        "time_limit": _required_environment(
            "PEANO_K3B_REQUESTED_TIME_LIMIT",
            re.compile(r"(?:[0-9]+-)?[0-9]{2}:[0-9]{2}:[0-9]{2}"),
        ),
        "time_limit_seconds": int(_required_environment(
            "PEANO_K3B_REQUESTED_TIME_LIMIT_SECONDS", POSITIVE_PATTERN
        )),
    }
    if observed != EXPECTED_RESOURCES:
        raise ClosureError(
            f"resource profile mismatch: {observed!r} != {EXPECTED_RESOURCES!r}"
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
                (child, False) for child in children if id(child) not in digests
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


def _local_specs() -> dict[str, TheoremSpec]:
    table: dict[str, TheoremSpec] = {}
    targets: list[str] = []
    for factory in SUPPORT_FACTORIES + TARGET_FACTORIES:
        rows = factory(TheoremSpec)
        if not isinstance(rows, tuple):
            raise ClosureError(f"{factory.__name__} did not return a tuple")
        for item in rows:
            if type(item) is not TheoremSpec or item.name in table:
                raise ClosureError(f"invalid or duplicate private row {item!r}")
            _closed_formula(item.statement)
            table[item.name] = item
            if factory in TARGET_FACTORIES:
                targets.append(item.name)
    if tuple(targets) != TARGET_NAMES:
        raise ClosureError(f"K3B target order drifted: {targets!r}")
    return table


def _dependency_closure(
    selected: tuple[str, ...],
    local: dict[str, TheoremSpec],
    public: dict[str, TheoremSpec],
) -> tuple[str, ...]:
    available = dict(public)
    overlap = set(available) & set(local)
    if overlap:
        raise ClosureError(f"private rows unexpectedly entered registry: {sorted(overlap)!r}")
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
        visit(name)
    return tuple(sorted(complete))


def _close_pass(selected: tuple[str, ...]) -> dict[str, dict[str, object]]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    public = dict(_specs_by_name())
    local = _local_specs()
    closure_names = _dependency_closure(selected, local, public)
    closed: dict[str, tuple[Formula, Proof]] = {}
    active: set[str] = set()

    def close(name: str) -> tuple[Formula, Proof]:
        cached = closed.get(name)
        if cached is not None:
            return cached
        if name in active:
            raise ClosureError(f"recursive closure cycle at {name!r}")
        if name in public:
            checked = replay(name)
            result = (checked.formula, checked.certificate)
            closed[name] = result
            return result
        item = local.get(name)
        if item is None:
            raise ClosureError(f"cannot close unknown theorem {name!r}")
        active.add(name)
        formula = _closed_formula(item.statement)
        dependency_specs = []
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
            raise ClosureError(f"kernel rejected empty-context closure {name!r}")
        active.remove(name)
        result = (formula, body)
        closed[name] = result
        return result

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
            "statement_characters": len(item.statement),
            "statement_sha256": sha256(item.statement.encode()).hexdigest(),
        }
    if not set(selected).issubset(closed):
        raise ClosureError("selected closure was incomplete")
    if not set(closed).issubset(set(closure_names)):
        raise ClosureError("closure escaped the audited dependency graph")
    replay.cache_clear()
    _specs_by_name.cache_clear()
    return receipts


def _write_report(path: Path, payload: dict[str, object]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ClosureError(f"refusing to overwrite report {path}")
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ) + "\n"
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--theorem",
        action="append",
        choices=TARGET_NAMES,
        help="target to close; repeat to select several (default: all nine)",
    )
    parser.add_argument(
        "--passes", type=int, default=2,
        help="number of genuinely cold passes, 1--16 (default: 2)",
    )
    parser.add_argument("--report", type=Path, help="new JSON receipt path")
    parser.add_argument(
        "--list-theorems", action="store_true", help="print target names and exit"
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    if args.list_theorems:
        print("\n".join(TARGET_NAMES))
        return 0
    if args.report is None:
        raise ClosureError("--report is required")
    if not 1 <= args.passes <= 16:
        raise ClosureError("--passes must be between 1 and 16")
    requested = args.theorem or list(TARGET_NAMES)
    if len(requested) != len(set(requested)):
        raise ClosureError("duplicate --theorem selection")
    selected = tuple(name for name in TARGET_NAMES if name in set(requested))
    provenance = _provenance()
    resources = _resources()
    if os.environ.get("PYTHONHASHSEED") != "20260804":
        raise ClosureError("PYTHONHASHSEED must be exactly 20260804")

    pass_receipts: list[dict[str, dict[str, object]]] = []
    for index in range(args.passes):
        print(f"K3B COLD PASS {index + 1}/{args.passes}: {','.join(selected)}", flush=True)
        receipt = _close_pass(selected)
        if pass_receipts and receipt != pass_receipts[0]:
            raise ClosureError(f"cold pass {index + 1} was nondeterministic")
        pass_receipts.append(receipt)
        gc.collect()

    payload: dict[str, object] = {
        "deterministic_across_passes": all(
            item == pass_receipts[0] for item in pass_receipts
        ),
        "environment": {
            "python_executable": sys.executable,
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "pythonhashseed": os.environ["PYTHONHASHSEED"],
        },
        "format": FORMAT,
        "passes": args.passes,
        "provenance": provenance,
        "requested_resources": resources,
        "results": pass_receipts[0],
        "schema_version": 1,
        "selected_theorems": list(selected),
        "status": "passed",
    }
    _write_report(args.report, payload)
    print(f"K3B PASS report={args.report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
