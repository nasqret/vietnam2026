#!/usr/bin/env python3
"""Run two fresh-process cold closures for the exact Alpha-v3 Bertrand append.

This harness does not alter the Alpha-v3 catalog, promote evidence, or submit a
cluster job.  Its explicit local-diagnostic mode is permanently ineligible for
admission.  WMI mode separates declared upload provenance from observed Git
facts, binds the actual Slurm allocation, and is the only admission-eligible
mode.  The 902-row v2 prefix, complete v3 artifact family, exact 21 target
surfaces and factory-source bytes are checked before either worker starts.  A
final report appears atomically only when two distinct fresh interpreters
produce identical kernel-checked, zero-DNE proof receipts.
"""

from __future__ import annotations

import argparse
from dataclasses import fields
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
from peano_lab.library import editions_v3 as v3
from peano_lab.library.alpha_enrollment_v3 import BERTRAND_START_INDEX
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay as replay_stable,
)


FORMAT = "peano-bertrand-alpha-v3-cold-closure-v2"
WORKER_FORMAT = "peano-bertrand-alpha-v3-cold-worker-v2"
SCHEMA_VERSION = 2
EXPECTED_PASSES = 2
EXPECTED_PYTHONHASHSEED = "20260809"
MAX_WORKER_REPORT_BYTES = 32 * 1024 * 1024
REPORT_SCHEMA_PATH = (
    "schemas/peano-bertrand-alpha-v3-cold-closure-v2.schema.json"
)
EXPECTED_REPORT_SCHEMA_SHA256 = (
    "49385ea44ce059b6d3543b3d68f5ae67a3a0155fb8d1f219fed118eba783fa69"
)

LOCAL_DIAGNOSTIC_MODE = "local-diagnostic"
WMI_SLURM_MODE = "wmi-slurm"
EXECUTION_MODES = (LOCAL_DIAGNOSTIC_MODE, WMI_SLURM_MODE)
LOCAL_OPT_IN = "PEANO_BERTRAND_ALLOW_LOCAL_DIAGNOSTIC"
EXPECTED_WMI_JOB_NAME = "peano-bertrand-v3"
SAFE_TEXT_PATTERN = re.compile(r"[^\x00-\x1f\x7f]{1,1000}\Z")
SLURM_JOB_ID_PATTERN = re.compile(r"[1-9][0-9]*\Z")

EXPECTED_ALPHA_V3_COUNT = 923
EXPECTED_ALPHA_V3_EDGE_COUNT = 2_730
EXPECTED_ALPHA_V3_LAYER_COUNT = 45
EXPECTED_ALPHA_V3_CHECKED_USE_COUNT = 570
EXPECTED_ALPHA_V3_ENROLLMENT_SHA256 = (
    "4507736cde37301ecf3369540d6cc686de860b07b101f2afb60f850f86aeebd4"
)
EXPECTED_ALPHA_V3_IDENTITY_SHA256 = (
    "e20eefac839fb2bcd3e696989c091a5f6837de04824f94e1073723851a471a2f"
)
EXPECTED_ALPHA_V3_SPEC_ROOT_SHA256 = (
    "e38c7bc29c8bfbf39ca1aec51ca33820570082ce1fa1386f324ffb4cec7a5537"
)
EXPECTED_ALPHA_V3_MEMBERSHIP_ROOT_SHA256 = (
    "6137eba6d84e846ffb8cc5db31d2bd07044224714a61b9468ba342e692b777a3"
)
EXPECTED_ALPHA_V3_EVIDENCE_ROOT_SHA256 = (
    "04f89ce222abdaccec2760f6e617c4b26f1da5445b4ac6566b270288c68977f4"
)
EXPECTED_ALPHA_V3_ARTIFACTS = {
    "catalog": {
        "path": "artifacts/peano-library/alpha/catalog-v3.json",
        "sha256": "1cd6b31379737efb3d889318e1c40beffcc14f77432a1b18cb74e80a5d29d199",
    },
    "channels": {
        "path": "artifacts/peano-library/channels-v3.json",
        "sha256": "cd1618b8056abd22348dfac70d8a1686eecd5c6f875319c803d487c414f656ab",
    },
    "dependency_graph": {
        "path": "artifacts/peano-library/alpha/dependency-graph-v3.mmd",
        "sha256": "180ff8ddeccc9fafbc3607aa10b0587cbe2144cf4943621df52c2da5f26dbec7",
    },
    "metrics": {
        "path": "artifacts/peano-library/alpha/metrics-v3.json",
        "sha256": "50f5a2dab17fffa6b2ad0e936138bc197297caf066218e4054f8bc8b0e5ccd73",
    },
}
EXPECTED_SOURCE_SHA256 = {
    "peano-lab/py/peano_lab/library/bertrand_prime_interval_candidate.py": (
        "6b9263ffd4aa39130ff4cee9ae3f3449e4aadbc544363900f7f2289ffc701a97"
    ),
    "peano-lab/py/peano_lab/library/bertrand_power_order_candidate.py": (
        "50b07e3b40b81966a37bc07cbb44b93498a86efa76aabcbb4af94b17c1eb17e6"
    ),
    "peano-lab/py/peano_lab/library/bertrand_power_growth_candidate.py": (
        "41584397a149b7af19891bdd7b0f6b6366f6412c4c636508921af85d7220bfab"
    ),
    "peano-lab/py/peano_lab/library/bertrand_power_valuation_candidate.py": (
        "e1d7177ba713425dd3545fa7de2d78dae73ce155e09fabcfe6cd46fcf562fd57"
    ),
}

TARGET_NAMES = (
    "prime_strictly_above_decidable",
    "bounded_prime_interval_search",
    "prime_interval_exclusion_refutes_witness",
    "bounded_prime_interval_decidable",
    "mul_le_mul",
    "le_mul_of_one_le_right",
    "le_mul_of_one_le_left",
    "pow_base_monotone",
    "one_le_pow",
    "pow_nonzero_of_one_le",
    "pow_exponent_monotone",
    "power_divides_decidable",
    "power_divides_zero",
    "bounded_power_valuation_search",
    "bounded_power_valuation_exists",
    "power_valuation_exists",
    "power_valuation_functional",
    "power_valuation_power_divides",
    "power_valuation_dominates",
    "prime_power_valuation_exists",
    "prime_power_valuation_functional",
)
EXPECTED_TARGET_EDGE_COUNT = 56
EXPECTED_TARGET_GRAPH_SHA256 = (
    "9b14ced99d5a138f740ec7c99aca044a61b706e8161fa162c863f41e75f58bca"
)
EXPECTED_TARGET_SURFACE_SHA256 = (
    "16f595012facc50bab5a4790d76fc5b4c00583159b70b9178618ab24c3d9b323"
)

SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
POSITIVE_PATTERN = re.compile(r"[1-9][0-9]*\Z")
EXPECTED_RESOURCES = {
    "partition": "cpu_idle",
    "nodes": 1,
    "ntasks": 1,
    "cpus_per_task": 1,
    "memory_mib": 32_768,
    "time_limit": "06:00:00",
    "time_limit_seconds": 21_600,
}


class ClosureError(RuntimeError):
    """The parent, target surface, cold closure, or receipt is invalid."""


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _required_environment(name: str, pattern: re.Pattern[str]) -> str:
    value = os.environ.get(name, "")
    if pattern.fullmatch(value) is None:
        raise ClosureError(f"missing or malformed {name}")
    return value


def _safe_environment_text(name: str) -> str:
    return _required_environment(name, SAFE_TEXT_PATTERN)


def _git_command(*arguments: str) -> bytes:
    try:
        completed = subprocess.run(
            ("git", "-C", str(_repository_root()), *arguments),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise ClosureError(f"cannot inspect Git repository: {exc}") from exc
    if completed.returncode != 0:
        diagnostic = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ClosureError(
            f"Git observation failed for {arguments!r}: {diagnostic[-1000:]}"
        )
    return completed.stdout


def _observed_repository() -> dict[str, object]:
    root = _repository_root().resolve()
    marker = root / ".git"
    if marker.is_symlink():
        raise ClosureError("repository .git marker must not be a symlink")
    if not marker.exists():
        return {"availability": "payload_without_git"}
    top_level_raw = _git_command("rev-parse", "--show-toplevel")
    try:
        top_level_text = top_level_raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise ClosureError("Git top-level path is not UTF-8") from exc
    if not top_level_text or Path(top_level_text).resolve() != root:
        raise ClosureError("Git top-level does not match the repository root")
    head_raw = _git_command("rev-parse", "--verify", "HEAD^{commit}")
    try:
        head = head_raw.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise ClosureError("Git HEAD is not ASCII") from exc
    if COMMIT_PATTERN.fullmatch(head) is None:
        raise ClosureError("Git HEAD is malformed")
    status = _git_command(
        "status", "--porcelain=v1", "-z", "--untracked-files=all"
    )
    return {
        "availability": "git",
        "clean": not status,
        "head": head,
        "status_entries": status.count(b"\0"),
        "status_sha256": sha256(status).hexdigest(),
        "top_level_matches_repository": True,
    }


def _source_provenance(execution_mode: str) -> dict[str, object]:
    observed = _observed_repository()
    if execution_mode == LOCAL_DIAGNOSTIC_MODE:
        return {"declared_upload": None, "observed_repository": observed}
    if execution_mode != WMI_SLURM_MODE:
        raise ClosureError(f"unknown execution mode {execution_mode!r}")
    dirty = os.environ.get("PEANO_BERTRAND_LOCAL_DIRTY", "")
    if dirty != "false":
        raise ClosureError(
            "PEANO_BERTRAND_LOCAL_DIRTY must be false for WMI admission"
        )
    declared = {
        "local_commit": _required_environment(
            "PEANO_BERTRAND_LOCAL_COMMIT", COMMIT_PATTERN
        ),
        "local_dirty": False,
        "payload_sha256": _required_environment(
            "PEANO_BERTRAND_PAYLOAD_SHA256", SHA256_PATTERN
        ),
    }
    if observed["availability"] == "git":
        if not observed["clean"]:
            raise ClosureError("observed WMI Git worktree is dirty")
        if observed["head"] != declared["local_commit"]:
            raise ClosureError("declared upload commit differs from observed Git HEAD")
    return {"declared_upload": declared, "observed_repository": observed}


def _requested_resources(execution_mode: str) -> dict[str, object] | None:
    if execution_mode == LOCAL_DIAGNOSTIC_MODE:
        leaked = sorted(
            name
            for name in os.environ
            if name.startswith("PEANO_BERTRAND_REQUESTED_")
        )
        if leaked:
            raise ClosureError(
                f"local diagnostic cannot claim Slurm resources: {leaked!r}"
            )
        return None
    if execution_mode != WMI_SLURM_MODE:
        raise ClosureError(f"unknown execution mode {execution_mode!r}")
    observed: dict[str, object] = {
        "partition": _required_environment(
            "PEANO_BERTRAND_REQUESTED_PARTITION",
            re.compile(r"[A-Za-z0-9_-]+\Z"),
        ),
        "nodes": int(
            _required_environment("PEANO_BERTRAND_REQUESTED_NODES", POSITIVE_PATTERN)
        ),
        "ntasks": int(
            _required_environment("PEANO_BERTRAND_REQUESTED_NTASKS", POSITIVE_PATTERN)
        ),
        "cpus_per_task": int(
            _required_environment(
                "PEANO_BERTRAND_REQUESTED_CPUS_PER_TASK", POSITIVE_PATTERN
            )
        ),
        "memory_mib": int(
            _required_environment(
                "PEANO_BERTRAND_REQUESTED_MEMORY_MIB", POSITIVE_PATTERN
            )
        ),
        "time_limit": _required_environment(
            "PEANO_BERTRAND_REQUESTED_TIME_LIMIT",
            re.compile(r"(?:[0-9]+-)?[0-9]{2}:[0-9]{2}:[0-9]{2}\Z"),
        ),
        "time_limit_seconds": int(
            _required_environment(
                "PEANO_BERTRAND_REQUESTED_TIME_LIMIT_SECONDS", POSITIVE_PATTERN
            )
        ),
    }
    if observed != EXPECTED_RESOURCES:
        raise ClosureError(
            f"resource profile mismatch: {observed!r} != {EXPECTED_RESOURCES!r}"
        )
    return observed


def _execution_receipt(execution_mode: str) -> dict[str, object]:
    host = platform.node()
    if SAFE_TEXT_PATTERN.fullmatch(host) is None:
        raise ClosureError("execution host is empty or contains unsafe text")
    if execution_mode == LOCAL_DIAGNOSTIC_MODE:
        if os.environ.get(LOCAL_OPT_IN) != "true":
            raise ClosureError(
                f"{LOCAL_OPT_IN}=true is required for local diagnostics"
            )
        leaked = sorted(name for name in os.environ if name.startswith("SLURM_"))
        if leaked:
            raise ClosureError(
                f"local diagnostic inherited scheduler identity: {leaked!r}"
            )
        if os.environ.get("PEANO_CLUSTER_BACKEND") not in {None, "local"}:
            raise ClosureError("local diagnostic has a non-local cluster backend")
        return {
            "admission_eligible": False,
            "host": host,
            "mode": LOCAL_DIAGNOSTIC_MODE,
            "observed_allocation": None,
            "proof_execution": "native-two-fresh-processes",
            "scheduler": {"kind": "none"},
            "synthetic": False,
        }
    if execution_mode != WMI_SLURM_MODE:
        raise ClosureError(f"unknown execution mode {execution_mode!r}")
    if os.environ.get("PEANO_CLUSTER_BACKEND") != "wmi":
        raise ClosureError("WMI execution requires PEANO_CLUSTER_BACKEND=wmi")
    job_id = _required_environment("SLURM_JOB_ID", SLURM_JOB_ID_PATTERN)
    job_name = _safe_environment_text("SLURM_JOB_NAME")
    if job_name != EXPECTED_WMI_JOB_NAME:
        raise ClosureError(f"unexpected Slurm job name {job_name!r}")
    partition = _safe_environment_text("SLURM_JOB_PARTITION")
    cluster = _safe_environment_text("SLURM_CLUSTER_NAME")
    node_list = _safe_environment_text("SLURM_JOB_NODELIST")
    submit_dir = Path(_safe_environment_text("SLURM_SUBMIT_DIR"))
    if submit_dir.resolve() != _repository_root().resolve():
        raise ClosureError("SLURM_SUBMIT_DIR differs from the repository root")
    allocation = {
        "cpus_per_task": int(
            _required_environment("SLURM_CPUS_PER_TASK", POSITIVE_PATTERN)
        ),
        "memory_mib": int(
            _required_environment("SLURM_MEM_PER_NODE", POSITIVE_PATTERN)
        ),
        "node_list": node_list,
        "nodes": int(
            _required_environment("SLURM_JOB_NUM_NODES", POSITIVE_PATTERN)
        ),
        "ntasks": int(_required_environment("SLURM_NTASKS", POSITIVE_PATTERN)),
        "partition": partition,
    }
    expected_allocation = {
        "cpus_per_task": EXPECTED_RESOURCES["cpus_per_task"],
        "memory_mib": EXPECTED_RESOURCES["memory_mib"],
        "nodes": EXPECTED_RESOURCES["nodes"],
        "ntasks": EXPECTED_RESOURCES["ntasks"],
        "partition": EXPECTED_RESOURCES["partition"],
    }
    actual_comparable = {
        key: allocation[key] for key in expected_allocation
    }
    if actual_comparable != expected_allocation:
        raise ClosureError(
            f"observed Slurm allocation mismatch: {actual_comparable!r} != "
            f"{expected_allocation!r}"
        )
    return {
        "admission_eligible": True,
        "host": host,
        "mode": WMI_SLURM_MODE,
        "observed_allocation": allocation,
        "proof_execution": "native-two-fresh-processes",
        "scheduler": {
            "cluster": cluster,
            "job_id": job_id,
            "job_name": job_name,
            "kind": "slurm",
            "submit_dir_matches_repository": True,
        },
        "synthetic": False,
    }


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _strict_json(path: Path) -> dict[str, object]:
    def pairs(values: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in values:
            if key in result:
                raise ClosureError(f"duplicate JSON key {key!r} in {path}")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ClosureError(f"cannot read strict JSON {path}: {exc}") from exc
    if type(value) is not dict:
        raise ClosureError(f"JSON root is not an object: {path}")
    return value


def _report_schema_receipt() -> dict[str, str]:
    path = _repository_root() / REPORT_SCHEMA_PATH
    observed = _sha256_file(path)
    if observed != EXPECTED_REPORT_SCHEMA_SHA256:
        raise ClosureError("cold-closure report schema bytes changed")
    schema = _strict_json(path)
    if schema.get("$id") != FORMAT or schema.get("title") != FORMAT:
        raise ClosureError("cold-closure report schema identity changed")
    return {"path": REPORT_SCHEMA_PATH, "sha256": observed}


def _parent_receipt() -> dict[str, object]:
    observed_runtime = {
        "checked_use_count": len(v3.ALPHA_CHECKED_SPECS),
        "edge_count": v3.ALPHA_EDITION.edge_count,
        "enrollment_sha256": v3.ALPHA_V3_ENROLLMENT_SHA256,
        "identity_sha256": v3.ALPHA_V3_IDENTITY_SHA256,
        "layer_count": v3.ALPHA_EDITION.layer_count,
        "theorem_count": len(v3.ALPHA_ENTRIES),
    }
    expected_runtime = {
        "checked_use_count": EXPECTED_ALPHA_V3_CHECKED_USE_COUNT,
        "edge_count": EXPECTED_ALPHA_V3_EDGE_COUNT,
        "enrollment_sha256": EXPECTED_ALPHA_V3_ENROLLMENT_SHA256,
        "identity_sha256": EXPECTED_ALPHA_V3_IDENTITY_SHA256,
        "layer_count": EXPECTED_ALPHA_V3_LAYER_COUNT,
        "theorem_count": EXPECTED_ALPHA_V3_COUNT,
    }
    if observed_runtime != expected_runtime:
        raise ClosureError(
            f"Alpha v3 runtime mismatch: {observed_runtime!r} != {expected_runtime!r}"
        )

    root = _repository_root()
    observed_artifacts: dict[str, dict[str, str]] = {}
    for name, expected in EXPECTED_ALPHA_V3_ARTIFACTS.items():
        path = root / expected["path"]
        digest = _sha256_file(path)
        observed_artifacts[name] = {"path": expected["path"], "sha256": digest}
    if observed_artifacts != EXPECTED_ALPHA_V3_ARTIFACTS:
        raise ClosureError("Alpha v3 artifact-family byte binding changed")

    catalog = _strict_json(
        root / EXPECTED_ALPHA_V3_ARTIFACTS["catalog"]["path"]
    )
    expected_catalog = {
        "checked_use_count": EXPECTED_ALPHA_V3_CHECKED_USE_COUNT,
        "edge_count": EXPECTED_ALPHA_V3_EDGE_COUNT,
        "edition_identity_sha256": EXPECTED_ALPHA_V3_IDENTITY_SHA256,
        "evidence_root_sha256": EXPECTED_ALPHA_V3_EVIDENCE_ROOT_SHA256,
        "layer_count": EXPECTED_ALPHA_V3_LAYER_COUNT,
        "membership_root_sha256": EXPECTED_ALPHA_V3_MEMBERSHIP_ROOT_SHA256,
        "ordered_enrollment_root_sha256": EXPECTED_ALPHA_V3_ENROLLMENT_SHA256,
        "ordered_spec_root_sha256": EXPECTED_ALPHA_V3_SPEC_ROOT_SHA256,
        "schema": "peano-library-alpha-snapshot-v3",
        "theorem_count": EXPECTED_ALPHA_V3_COUNT,
    }
    actual_catalog = {key: catalog.get(key) for key in expected_catalog}
    if actual_catalog != expected_catalog:
        raise ClosureError("Alpha v3 catalog roots or counts changed")
    return {
        "alpha_v3_artifacts": observed_artifacts,
        "alpha_v3_evidence_root_sha256": EXPECTED_ALPHA_V3_EVIDENCE_ROOT_SHA256,
        "alpha_v3_membership_root_sha256": EXPECTED_ALPHA_V3_MEMBERSHIP_ROOT_SHA256,
        "alpha_v3_ordered_spec_root_sha256": EXPECTED_ALPHA_V3_SPEC_ROOT_SHA256,
        "alpha_v3_runtime": observed_runtime,
    }


def _target_graph_sha256(specs: Sequence[TheoremSpec]) -> str:
    rows = (
        "\x1f".join((item.name, "\x1e".join(item.dependencies)))
        for item in specs
    )
    return sha256("\x1c".join(rows).encode()).hexdigest()


def _target_surface_sha256(
    entries: Sequence[v3.EditionEntry],
) -> str:
    root = _repository_root()
    rows = (
        "\x1f".join(
            (
                entry.spec.name,
                sha256(entry.spec.statement.encode()).hexdigest(),
                "\x1e".join(entry.spec.dependencies),
                entry.source_module,
                _sha256_file(root / entry.source_module),
            )
        )
        for entry in entries
    )
    return sha256("\x1c".join(rows).encode()).hexdigest()


def _local_specs() -> dict[str, TheoremSpec]:
    _parent_receipt()
    entries = v3.ALPHA_ENTRIES[BERTRAND_START_INDEX:]
    if tuple(entry.spec.name for entry in entries) != TARGET_NAMES:
        raise ClosureError("Alpha v3 Bertrand target order drifted")
    if len(entries) != 21:
        raise ClosureError("Alpha v3 Bertrand target count drifted")

    catalog = _strict_json(
        _repository_root() / EXPECTED_ALPHA_V3_ARTIFACTS["catalog"]["path"]
    )
    rows = catalog.get("theorems")
    if type(rows) is not list or len(rows) != EXPECTED_ALPHA_V3_COUNT:
        raise ClosureError("Alpha v3 catalog theorem table changed")
    target_rows = rows[BERTRAND_START_INDEX:]

    specs: list[TheoremSpec] = []
    allowed_origins = {
        v3.EnrollmentOrigin.BERTRAND_B0_INTERVAL,
        v3.EnrollmentOrigin.BERTRAND_B1_POWER_ORDER,
        v3.EnrollmentOrigin.BERTRAND_B1_POWER_GROWTH,
        v3.EnrollmentOrigin.BERTRAND_B2_BOUNDED_VALUATION,
    }
    for entry, raw in zip(entries, target_rows, strict=True):
        item = entry.spec
        if type(item) is not TheoremSpec or type(raw) is not dict:
            raise ClosureError(f"invalid Bertrand target row {item!r}")
        if (
            entry.membership is not v3.Membership.ALPHA_ONLY
            or entry.evidence is not v3.EvidenceStatus.BODY_CHECKED
            or entry.checked_use
            or entry.enrollment_origin not in allowed_origins
            or entry.provenance != (entry.enrollment_origin,)
        ):
            raise ClosureError(f"Bertrand metadata drifted for {item.name!r}")
        source_sha256 = _sha256_file(_repository_root() / entry.source_module)
        if EXPECTED_SOURCE_SHA256.get(entry.source_module) != source_sha256:
            raise ClosureError(f"Bertrand source bytes drifted for {item.name!r}")
        exact_runtime = (
            item.name,
            item.statement,
            item.dependencies,
            item.script,
            item.summary,
            entry.source_module,
        )
        exact_catalog = (
            raw.get("name"),
            raw.get("statement"),
            tuple(raw.get("dependencies", ())),
            tuple(raw.get("script", ())),
            raw.get("summary"),
            raw.get("source", {}).get("path"),
        )
        if exact_runtime != exact_catalog:
            raise ClosureError(f"Bertrand catalog/runtime drifted for {item.name!r}")
        if raw.get("source", {}).get("sha256") != source_sha256:
            raise ClosureError(f"Bertrand catalog source drifted for {item.name!r}")
        if any("DNE" in command for command in item.script):
            raise ClosureError(f"Bertrand script {item.name!r} contains DNE")
        _closed_formula(item.statement)
        specs.append(item)

    if sum(len(item.dependencies) for item in specs) != EXPECTED_TARGET_EDGE_COUNT:
        raise ClosureError("Bertrand direct dependency edge count drifted")
    if _target_graph_sha256(specs) != EXPECTED_TARGET_GRAPH_SHA256:
        raise ClosureError("Bertrand dependency graph identity drifted")
    if _target_surface_sha256(entries) != EXPECTED_TARGET_SURFACE_SHA256:
        raise ClosureError("Bertrand statement/dependency/source identity drifted")
    return {item.name: item for item in specs}


def _public_specs() -> dict[str, TheoremSpec]:
    table = {item.name: item for item in v3.ALPHA_CHECKED_SPECS}
    if len(table) != EXPECTED_ALPHA_V3_CHECKED_USE_COUNT:
        raise ClosureError("Alpha v3 checked-use table contains duplicates")
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
            f"body-only Bertrand rows crossed checked use: {sorted(overlap)!r}"
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
            raise ClosureError(f"unknown Bertrand target {name!r}")
        visit(name)
    return tuple(sorted(complete))


def _clear_replay_caches() -> None:
    v3.replay.cache_clear()
    v2.replay.cache_clear()
    v1._replay_alpha_closed.cache_clear()
    replay_stable.cache_clear()
    _specs_by_name.cache_clear()


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
            checked = v3.replay(name, edition=v3.EditionName.ALPHA)
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
            raise ClosureError(f"kernel rejected empty-context closure {name!r}")
        active.remove(name)
        result = (formula, body)
        closed[name] = result
        return result

    try:
        receipts: dict[str, dict[str, object]] = {}
        for index, name in enumerate(selected, start=1):
            print(
                f"BERTRAND CLOSE {index}/{len(selected)} {name}",
                flush=True,
            )
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
            entry = v3.ALPHA_EDITION.by_name[name]
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
                "source_path": entry.source_module,
                "source_sha256": _sha256_file(
                    _repository_root() / entry.source_module
                ),
                "statement_characters": len(item.statement),
                "statement_sha256": sha256(item.statement.encode()).hexdigest(),
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
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ClosureError(f"refusing to overwrite report {path}")
    encoded = _canonical_json_bytes(payload)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary_created = False
    try:
        with temporary.open("xb") as handle:
            temporary_created = True
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise ClosureError(f"refusing to overwrite report {path}") from exc
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except FileExistsError as exc:
        raise ClosureError(f"refusing existing temporary report {temporary}") from exc
    finally:
        if temporary_created:
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
    execution: dict[str, object],
    source_provenance: dict[str, object],
    resources: dict[str, object] | None,
    schema: dict[str, str],
    results: dict[str, dict[str, object]],
) -> dict[str, object]:
    return {
        "environment": _environment_receipt(),
        "execution": execution,
        "parent": parent,
        "report_schema": schema,
        "requested_resources": resources,
        "results": results,
        "selected_theorems": list(selected),
        "source_provenance": source_provenance,
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
        "schema_version": SCHEMA_VERSION,
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
    execution = _execution_receipt(args.execution_mode)
    source_provenance = _source_provenance(args.execution_mode)
    resources = _requested_resources(args.execution_mode)
    schema = _report_schema_receipt()
    if os.environ.get("PYTHONHASHSEED") != EXPECTED_PYTHONHASHSEED:
        raise ClosureError(
            f"PYTHONHASHSEED must be exactly {EXPECTED_PYTHONHASHSEED}"
        )
    results = _close_pass(selected)
    receipt = _deterministic_receipt(
        selected,
        parent,
        execution,
        source_provenance,
        resources,
        schema,
        results,
    )
    payload = _worker_payload(
        args.worker_pass_index, args.worker_parent_pid, receipt
    )
    _write_report(args.worker_report, payload)
    print(
        f"BERTRAND WORKER PASS {args.worker_pass_index}/{EXPECTED_PASSES} "
        f"pid={os.getpid()}",
        flush=True,
    )
    return 0


def _worker_environment() -> dict[str, str]:
    environment = os.environ.copy()
    repository = _repository_root()
    peano_python = str(repository / "peano-lab" / "py")
    inherited = environment.get("PYTHONPATH", "")
    entries = tuple(item for item in inherited.split(os.pathsep) if item)
    if peano_python not in entries:
        environment["PYTHONPATH"] = os.pathsep.join((peano_python,) + entries)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.pop("PYTHONOPTIMIZE", None)
    return environment


def _worker_command(
    pass_index: int,
    parent_pid: int,
    execution_mode: str,
    selected: tuple[str, ...],
    worker_report: Path,
) -> list[str]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--passes",
        str(EXPECTED_PASSES),
        "--execution-mode",
        execution_mode,
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


def _result_keys() -> set[str]:
    return {
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
        "source_path",
        "source_sha256",
        "statement_characters",
        "statement_sha256",
    }


def _validate_result_receipts(
    results: object,
    selected: tuple[str, ...],
) -> None:
    if type(results) is not dict or set(results) != set(selected):
        raise ClosureError("worker result target set mismatch")
    local = _local_specs()
    public = _public_specs()
    for name in selected:
        result = results.get(name)
        if type(result) is not dict or set(result) != _result_keys():
            raise ClosureError(f"worker result schema mismatch for {name!r}")
        item = local[name]
        entry = v3.ALPHA_EDITION.by_name[name]
        if result["direct_dependencies"] != list(item.dependencies):
            raise ClosureError(f"worker dependencies drifted for {name!r}")
        exact_digests = {
            "statement_sha256": sha256(item.statement.encode()).hexdigest(),
            "script_sha256": sha256("\n".join(item.script).encode()).hexdigest(),
            "source_sha256": EXPECTED_SOURCE_SHA256[entry.source_module],
        }
        for field_name, expected in exact_digests.items():
            if result[field_name] != expected:
                raise ClosureError(f"worker {field_name} drifted for {name!r}")
        if result["source_path"] != entry.source_module:
            raise ClosureError(f"worker source path drifted for {name!r}")
        target_closure = _dependency_closure((name,), local, public)
        exact_scalars = {
            "dependency_closure_count": len(target_closure),
            "dependency_closure_sha256": sha256(
                "\n".join(target_closure).encode()
            ).hexdigest(),
            "script_commands": len(item.script),
            "statement_characters": len(item.statement),
        }
        for field_name, expected in exact_scalars.items():
            if result[field_name] != expected:
                raise ClosureError(f"worker {field_name} drifted for {name!r}")
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
            "source_sha256",
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
        or payload["schema_version"] != SCHEMA_VERSION
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
    if type(payload) is not dict or _canonical_json_bytes(payload) != raw:
        raise ClosureError("worker receipt JSON is not canonical")
    return payload, sha256(raw).hexdigest()


def _run_worker(
    pass_index: int,
    execution_mode: str,
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
        pass_index, parent_pid, execution_mode, selected, worker_report
    )
    print(
        f"BERTRAND COLD PROCESS {pass_index}/{EXPECTED_PASSES}: "
        f"{','.join(selected)}",
        flush=True,
    )
    try:
        completed = subprocess.run(
            command,
            check=False,
            env=_worker_environment(),
            stdout=None,
            stderr=subprocess.PIPE,
            text=True,
        )
        if completed.returncode != 0:
            diagnostic = (completed.stderr or "").strip()[-4000:]
            raise ClosureError(
                f"cold worker {pass_index} failed with exit "
                f"{completed.returncode}: {diagnostic}"
            )
        payload, payload_sha256 = _read_worker_payload(worker_report)
        validated = _validate_worker_payload(
            payload, pass_index, parent_pid, selected, expected_receipt
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
        help="target to close; repeat to select several (default: all 21)",
    )
    parser.add_argument(
        "--passes",
        type=int,
        default=EXPECTED_PASSES,
        help="must remain exactly two cold passes",
    )
    parser.add_argument(
        "--execution-mode",
        choices=EXECUTION_MODES,
        help="required authority boundary: diagnostic laptop or WMI Slurm",
    )
    parser.add_argument("--report", type=Path, help="new JSON receipt path")
    parser.add_argument(
        "--list-theorems",
        action="store_true",
        help="print the frozen target order and exit",
    )
    parser.add_argument("--worker-report", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--worker-pass-index", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--worker-parent-pid", type=int, help=argparse.SUPPRESS)
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
        raise ClosureError(f"unknown Bertrand target(s): {sorted(unknown)!r}")
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
    if args.execution_mode is None:
        raise ClosureError("--execution-mode is required")
    if args.report is None:
        raise ClosureError("--report is required")
    if args.passes != EXPECTED_PASSES:
        raise ClosureError("Bertrand admission requires exactly two cold passes")

    selected = _selected(args.theorem)
    parent = _parent_receipt()
    execution = _execution_receipt(args.execution_mode)
    source_provenance = _source_provenance(args.execution_mode)
    resources = _requested_resources(args.execution_mode)
    schema = _report_schema_receipt()
    if os.environ.get("PYTHONHASHSEED") != EXPECTED_PYTHONHASHSEED:
        raise ClosureError(
            f"PYTHONHASHSEED must be exactly {EXPECTED_PYTHONHASHSEED}"
        )

    final_report = Path(os.path.abspath(args.report))
    final_report.parent.mkdir(parents=True, exist_ok=True)
    if final_report.exists() or final_report.is_symlink():
        raise ClosureError(f"refusing to overwrite report {final_report}")
    expected_receipt = _deterministic_receipt(
        selected,
        parent,
        execution,
        source_provenance,
        resources,
        schema,
        {},
    )
    cold_passes = tuple(
        _run_worker(
            index,
            args.execution_mode,
            selected,
            final_report,
            expected_receipt,
        )
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
        "admission_eligible": execution["admission_eligible"],
        "cold_passes": list(cold_passes),
        "deterministic_across_passes": True,
        "environment": common["environment"],
        "execution": execution,
        "format": FORMAT,
        "parent": parent,
        "passes": EXPECTED_PASSES,
        "report_schema": schema,
        "requested_resources": resources,
        "results": common["results"],
        "schema_version": SCHEMA_VERSION,
        "selected_theorems": list(selected),
        "source_provenance": source_provenance,
        "status": "passed",
        "target_graph_sha256": EXPECTED_TARGET_GRAPH_SHA256,
        "target_surface_sha256": EXPECTED_TARGET_SURFACE_SHA256,
    }
    _write_report(final_report, payload)
    print(f"BERTRAND PASS report={final_report}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
