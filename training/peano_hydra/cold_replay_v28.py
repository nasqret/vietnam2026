"""Alpha-v28 metadata plans and bounded native calibration, separate from v25.

All 2,764 complete declarations contribute to the pinned target root. The plan
stores compact descriptors instead of raising the inherited 32-MiB plan cap.
Only selected, individually in-profile bodies can enter a native worker.
Full-library execution and independent human/research readiness are not granted.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import TYPE_CHECKING

from .cold_replay import (
    CERTIFICATE_SCHEMA, CertificateLimits, ColdReplayError, _fingerprint,
    fingerprint_certificate,
)
if TYPE_CHECKING:
    from .epoch import EpochTheorem, HydraEpoch

COLD_PLAN_SCHEMA = "peano-hydra-cold-library-plan-v28-v1"
COLD_TARGET_SCHEMA = "peano-hydra-cold-library-target-v28-v1"
COLD_REPLAY_SCHEMA = "peano-hydra-cold-library-replay-v28-v1"
ALPHA_V28_COUNT = 2764
ALPHA_V28_IDENTITY = "4936d155e8d2a39409a4e83beb4ac5cb2481948d8b6eeecf1c7571161786646b"
ALPHA_V28_EPOCH = "f64b5f100c9c9bc77049ea627f13e641be83ac72aaa474216682076679a468ad"
ALPHA_V28_TARGETS = "8c78b236606b5e0979d90c2b6cf94e67c40af549417411dc67c845689d512ed9"
MAX_PLAN_BYTES = 32 * 1024**2
MAX_TARGET_BYTES = 1024**2
MAX_STATEMENT_BYTES = 128 * 1024
MAX_SCRIPT_BYTES = 512 * 1024
MAX_SCRIPT_COMMANDS = 1024
MAX_DEPENDENCIES = 128
HOTSPOT_NAMES = ("central_binom_upper_support_package", "three_mod_four_good_prime_exclusive")
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,127}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _bytes(value, label, maximum):
    if type(value) is not str:
        raise ColdReplayError(f"{label} must be text")
    try:
        raw = value.encode("utf-8")
    except UnicodeError as error:
        raise ColdReplayError(f"{label} is not UTF-8") from error
    if not 1 <= len(raw) <= maximum:
        raise ColdReplayError(f"{label} exceeds its byte reservation")
    return raw


def _target_checked(target: object) -> dict[str, object]:
    required = {"schema", "name", "enrollment_index", "membership", "statement", "statement_sha256",
                "script", "script_sha256", "dependencies", "dependencies_sha256", "target_sha256"}
    if type(target) is not dict or set(target) != required or target["schema"] != COLD_TARGET_SCHEMA:
        raise ColdReplayError("cold replay target schema differs")
    if (type(target["name"]) is not str or _NAME.fullmatch(target["name"]) is None
        or type(target["enrollment_index"]) is not int or not 0 <= target["enrollment_index"] < ALPHA_V28_COUNT
        or target["membership"] not in ("stable", "alpha_only")):
        raise ColdReplayError("cold replay target has an invalid enrollment identity")
    statement = _bytes(target["statement"], "original theorem statement", MAX_STATEMENT_BYTES)
    script, dependencies = target["script"], target["dependencies"]
    if type(script) is not list or not 1 <= len(script) <= MAX_SCRIPT_COMMANDS:
        raise ColdReplayError("cold replay script exceeds its command reservation")
    script_bytes = 0
    for command in script:
        script_bytes += len(_bytes(command, "original script command", MAX_STATEMENT_BYTES)) + 1
        if script_bytes > MAX_SCRIPT_BYTES:
            raise ColdReplayError("cold replay script exceeds its byte reservation")
    if (type(dependencies) is not list or len(dependencies) > MAX_DEPENDENCIES
        or any(type(name) is not str or _NAME.fullmatch(name) is None for name in dependencies)
        or len(dependencies) != len(set(dependencies))):
        raise ColdReplayError("cold replay dependencies must be bounded exact names")
    for key in ("statement_sha256", "script_sha256", "dependencies_sha256", "target_sha256"):
        if type(target[key]) is not str or _SHA.fullmatch(target[key]) is None:
            raise ColdReplayError("cold replay target has a malformed digest")
    if (hashlib.sha256(statement).hexdigest() != target["statement_sha256"]
        or hashlib.sha256(("\n".join(script) + "\n").encode()).hexdigest() != target["script_sha256"]
        or hashlib.sha256(("\n".join(dependencies) + "\n").encode()).hexdigest() != target["dependencies_sha256"]):
        raise ColdReplayError("cold replay statement/script/dependency digest differs")
    unsigned = {key: value for key, value in target.items() if key != "target_sha256"}
    if _digest(unsigned) != target["target_sha256"]:
        raise ColdReplayError("cold replay target digest differs")
    raw = _canonical(target)
    if len(raw) > MAX_TARGET_BYTES:
        raise ColdReplayError("cold replay target exceeds its one-MiB reservation")
    return json.loads(raw)


def cold_target_record(theorem: EpochTheorem) -> dict[str, object]:
    """Preserve the complete source route; EpochTheorem.to_dict omits scripts."""
    from training.peano_hydra.epoch import EpochTheorem
    if type(theorem) is not EpochTheorem:
        raise ColdReplayError("cold planning requires exact frozen theorem records")
    record = {"schema": COLD_TARGET_SCHEMA, **theorem.to_dict(), "script": list(theorem.script),
              "dependencies_sha256": hashlib.sha256(("\n".join(theorem.dependencies) + "\n").encode()).hexdigest()}
    record["target_sha256"] = _digest(record)
    return _target_checked(record)


def build_cold_replay_plan(
    epoch: HydraEpoch, *, limits: CertificateLimits = CertificateLimits(),
    batch_size: int = 1, selected_names: tuple[str, ...] = (),
) -> dict[str, object]:
    """Bind the complete actual v28 declarations without loading native proofs.

    Descriptors cover every original statement, script and dependency. Oversize
    statements remain in the full inventory and are explicitly marked ineligible
    under the unchanged replay profile; they are never omitted from the root.
    """
    from .epoch import HydraEpoch
    if (type(epoch) is not HydraEpoch or epoch.version != "v28"
        or epoch.epoch_sha256 != ALPHA_V28_EPOCH
        or epoch.edition_identity_sha256 != ALPHA_V28_IDENTITY
        or len(epoch.theorems) != ALPHA_V28_COUNT or epoch.stable_count != 432
        or epoch.theorem_edge_count != 8984 or len(epoch.definitions) != 233
        or epoch.definition_edge_count != 441 or type(limits) is not CertificateLimits):
        raise ColdReplayError("cold planning requires the exact complete Alpha-v28 epoch")
    if type(batch_size) is not int or not 1 <= batch_size <= 16:
        raise ColdReplayError("cold replay batch size must lie in [1,16]")
    if (type(selected_names) is not tuple or len(selected_names) > 16
        or any(type(name) is not str for name in selected_names)
        or len(set(selected_names)) != len(selected_names)):
        raise ColdReplayError("selected bodies require at most 16 distinct exact names")
    targets, full, selected, outside, seen = [], [], {}, [], set()
    for index, theorem in enumerate(epoch.theorems):
        # This is bounded metadata, not a relaxed worker admission policy.
        row = {"schema": COLD_TARGET_SCHEMA, **theorem.to_dict(), "script": list(theorem.script),
               "dependencies_sha256": hashlib.sha256(("\n".join(theorem.dependencies) + "\n").encode()).hexdigest()}
        row["target_sha256"] = _digest(row)
        if (type(row["name"]) is not str or _NAME.fullmatch(row["name"]) is None
            or row["enrollment_index"] != index or row["name"] in seen
            or not set(row["dependencies"]) <= seen or len(_canonical(row)) > MAX_TARGET_BYTES):
            raise ColdReplayError("v28 target metadata changed its bounded complete order")
        seen.add(row["name"])
        full.append(row)
        statement_bytes = len(row["statement"].encode("utf-8"))
        script_bytes = sum(len(command.encode("utf-8")) + 1 for command in row["script"])
        reasons = []
        for count, maximum, reason in (
            (statement_bytes, MAX_STATEMENT_BYTES, "statement-byte-limit"),
            (script_bytes, MAX_SCRIPT_BYTES, "script-byte-limit"),
            (len(row["script"]), MAX_SCRIPT_COMMANDS, "script-command-limit"),
            (len(row["dependencies"]), MAX_DEPENDENCIES, "dependency-count-limit"),
        ):
            if count > maximum:
                reasons.append(reason)
        if any(len(command.encode("utf-8")) > MAX_STATEMENT_BYTES for command in row["script"]):
            reasons.append("script-command-byte-limit")
        descriptor = {key: row[key] for key in (
            "name", "enrollment_index", "membership", "statement_sha256", "script_sha256",
            "dependencies", "dependencies_sha256", "target_sha256")}
        descriptor.update(statement_bytes=statement_bytes, script_bytes=script_bytes,
                          script_commands=len(row["script"]), target_bytes=len(_canonical(row)),
                          replay_profile_eligible=not reasons)
        targets.append(descriptor)
        if reasons:
            outside.append({"name": row["name"], "enrollment_index": index,
                            "target_sha256": row["target_sha256"], "reasons": reasons})
        if row["name"] in selected_names:
            selected[str(index)] = _target_checked(row)
    if set(selected_names) != {row["name"] for row in selected.values()}:
        raise ColdReplayError("a selected native target is absent or outside the replay profile")
    projection = [{"name": row["name"], "dependencies": row["dependencies"]} for row in targets]
    if (_digest(full) != ALPHA_V28_TARGETS or _digest(projection) != epoch.theorem_dag_sha256
        or sum(len(row["dependencies"]) for row in targets) != 8984
        or sum(row["membership"] == "stable" for row in targets) != 432):
        raise ColdReplayError("v28 complete target statement/script/dependency identity changed")
    batches = [list(range(start, min(len(targets), start + batch_size)))
               for start in range(0, len(targets), batch_size)]
    record = {"schema": COLD_PLAN_SCHEMA, "status": "planned", "scope": "full-alpha-v28",
              "epoch": epoch.to_dict(), "epoch_sha256": epoch.epoch_sha256,
              "edition_identity_sha256": epoch.edition_identity_sha256,
              "target_count": len(targets), "targets": targets, "targets_sha256": _digest(targets),
              "full_target_records_sha256": ALPHA_V28_TARGETS,
              "selected_targets": selected, "selected_targets_sha256": _digest(selected),
              "outside_replay_profile": outside,
              "passes": 2, "certificate_limits": limits.to_dict(), "batch_size": batch_size,
              "batches": batches, "batch_count": len(batches), "batches_sha256": _digest(batches),
              "cache_scope": "one-frozen-batch", "fresh_process_per_batch_required": True,
              "fresh_process_per_target_required": batch_size == 1, "parallel_workers": 1,
              "parent_resource_guard_required": True,
              "replay_mode": "public-native-runtime-certificate-replay",
              "all_scripts_regenerated": False, "lean_companion_required": False,
              "proofs_checked": 0, "research_claim_eligible": False,
              "full_execution_authorized": False, "full_execution_envelope": None}
    record["plan_sha256"] = _digest(record)
    if len(_canonical(record)) > MAX_PLAN_BYTES:
        raise ColdReplayError("cold replay plan exceeds its unchanged 32-MiB reservation")
    return record


def _runtime():
    # Lazy import: parent planning/adapter import never initializes Alpha.
    from peano_lab.library import editions_v28
    return editions_v28


def replay_cold_target(
    target: dict[str, object], *, epoch_sha256: str, edition_identity_sha256: str,
    limits: CertificateLimits = CertificateLimits(),
) -> dict[str, object]:
    """Replay one exact target of a host-owned bounded, fresh-process batch.

    No full catalog/epoch JSON is loaded here. Public source declarations bind
    the complete selected specification; the parent authenticates their source
    bytes and the epoch. The manifest fixes batch size/order; dependencies may
    be cached within that batch, but not between batches or cold passes. An
    exception or killed process has no positive receipt for this target.
    """
    record = _target_checked(target)
    if (epoch_sha256 != ALPHA_V28_EPOCH
        or edition_identity_sha256 != ALPHA_V28_IDENTITY or type(limits) is not CertificateLimits):
        raise ColdReplayError("cold replay epoch or fingerprint policy differs")
    runtime = _runtime()
    if (runtime.ALPHA_V28_IDENTITY_SHA256 != edition_identity_sha256
        or len(runtime.ALPHA_EDITION.entries) != ALPHA_V28_COUNT):
        raise ColdReplayError("public native runtime changed its full Alpha-v28 identity")
    entry = runtime.ALPHA_EDITION.entries[record["enrollment_index"]]
    spec = entry.spec
    if (entry.checked_use is not True or entry.membership.value != record["membership"]
        or spec.name != record["name"] or spec.statement != record["statement"]
        or list(spec.script) != record["script"] or list(spec.dependencies) != record["dependencies"]):
        raise ColdReplayError("selected target differs from its exact public native declaration")
    from peano_lab.kernel.formulas import parse_formula_with_names
    from peano_lab.kernel.checker import check
    from peano_lab.library.theorems import CheckedTheorem
    original, free_names = parse_formula_with_names(record["statement"])
    if free_names:
        raise ColdReplayError("cold replay original theorem must be closed")
    original_fingerprint = _fingerprint(original, "formula", limits)
    checked = runtime.replay(record["name"], edition="alpha")
    if (type(checked) is not CheckedTheorem or checked.spec != spec
        or _fingerprint(checked.formula, "formula", limits)["sha256"] != original_fingerprint["sha256"]):
        raise ColdReplayError("public replay returned a different theorem")
    fingerprint = fingerprint_certificate(checked.certificate, limits=limits)
    if type(checked.proof_nodes) is not int or checked.proof_nodes != fingerprint["proof_nodes"]:
        raise ColdReplayError("public replay certificate size differs from the actual syntax")
    if not check((), checked.certificate, original):
        raise ColdReplayError("independent intuitionistic kernel rejected the original theorem")
    receipt = {"schema": COLD_REPLAY_SCHEMA, "status": "checked", "kernel_checked": True,
               "epoch_sha256": epoch_sha256, "edition_identity_sha256": edition_identity_sha256,
               "target_sha256": record["target_sha256"], "name": record["name"],
               "enrollment_index": record["enrollment_index"], "membership": record["membership"],
               "statement_sha256": record["statement_sha256"], "script_sha256": record["script_sha256"],
               "dependencies_sha256": record["dependencies_sha256"],
               "original_formula_sha256": original_fingerprint["sha256"], "certificate": fingerprint,
               "certificate_limits": limits.to_dict(), "kernel_mode": "intuitionistic",
               "empty_context": True, "independent_recheck_calls": 1,
               "runtime_internal_kernel_calls": None, "all_scripts_regenerated": False,
               "lean_companion_invoked": False, "model_calls": 0, "solver_calls": 0,
               "research_claim_eligible": False}
    receipt["receipt_sha256"] = _digest(receipt)
    return receipt


