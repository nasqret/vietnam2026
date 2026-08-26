"""Bounded evidence adapter for fresh-process Alpha-v25 native replay.

This module neither schedules workers nor grants a cold/full-library claim.
The controller must authenticate the epoch and source, reserve OS resources,
start a fresh process for each frozen batch, retain failures, and compare both full
ordered passes. Public replay may load a prepared ordinary proof bundle or
regenerate a historical script; this is not an all-script-regeneration claim.
No Lean companion, model, external solver, or cache-flushing operation is used.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from peano_lab.kernel.proofs import Proof
    from training.peano_hydra.epoch import EpochTheorem, HydraEpoch


COLD_PLAN_SCHEMA = "peano-hydra-cold-library-plan-v1"
COLD_TARGET_SCHEMA = "peano-hydra-cold-library-target-v1"
COLD_REPLAY_SCHEMA = "peano-hydra-cold-library-replay-v1"
CERTIFICATE_SCHEMA = "peano-hydra-native-certificate-merkle-v1"
ALPHA_V25_COUNT = 2_080
ALPHA_V25_IDENTITY = "3516d4730428c79fc73aa6fbdbabc43d93921471941bb2f144ea3d29e0af5b28"
MAX_PLAN_BYTES = 32 * 1024 * 1024
MAX_TARGET_BYTES = 1024 * 1024
MAX_STATEMENT_BYTES = 128 * 1024
MAX_SCRIPT_BYTES = 512 * 1024
MAX_SCRIPT_COMMANDS = 1024
MAX_DEPENDENCIES = 128
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,127}\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")


class ColdReplayError(ValueError):
    """Missing, changed, rejected or over-budget evidence is not a proof."""


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _bytes(value: object, label: str, maximum: int) -> bytes:
    if type(value) is not str or not value or len(value) > maximum:
        raise ColdReplayError(f"{label} must be bounded nonempty text")
    try:
        raw = value.encode("utf-8")
    except UnicodeError:
        raise ColdReplayError(f"{label} is not valid UTF-8") from None
    if len(raw) > maximum:
        raise ColdReplayError(f"{label} exceeds its byte reservation")
    return raw


@dataclass(frozen=True, slots=True)
class CertificateLimits:
    """Finite fingerprint work, separate from the host's CPU/wall/RSS guard."""

    max_proof_objects: int = 100_000
    max_syntax_objects: int = 1_000_000
    max_proof_nodes: int = 500_000
    max_annotation_nodes: int = 5_000_000
    max_proof_depth: int = 256
    max_envelope_depth: int = 512

    def __post_init__(self) -> None:
        ceilings = {"max_proof_objects": 1_000_000, "max_syntax_objects": 2_000_000,
                    "max_proof_nodes": 5_000_000, "max_annotation_nodes": 20_000_000,
                    "max_proof_depth": 1024, "max_envelope_depth": 2048}
        for name, ceiling in ceilings.items():
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= ceiling:
                raise ColdReplayError(f"invalid certificate bound: {name}")

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def _target_checked(target: object) -> dict[str, object]:
    required = {"schema", "name", "enrollment_index", "membership", "statement", "statement_sha256",
                "script", "script_sha256", "dependencies", "dependencies_sha256", "target_sha256"}
    if type(target) is not dict or set(target) != required or target["schema"] != COLD_TARGET_SCHEMA:
        raise ColdReplayError("cold replay target schema differs")
    if (type(target["name"]) is not str or _NAME.fullmatch(target["name"]) is None
        or type(target["enrollment_index"]) is not int or not 0 <= target["enrollment_index"] < ALPHA_V25_COUNT
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
    epoch: HydraEpoch, *, limits: CertificateLimits = CertificateLimits(), batch_size: int = 1,
) -> dict[str, object]:
    """Plan all 2080 targets, never a selected slice presented as full replay.

    The caller supplies an epoch authenticated by freeze_epoch. No proof is
    loaded, regenerated, checked or marked successful during planning.
    """
    from training.peano_hydra.epoch import HydraEpoch
    if (type(epoch) is not HydraEpoch or epoch.version != "v25"
        or epoch.edition_identity_sha256 != ALPHA_V25_IDENTITY
        or len(epoch.theorems) != ALPHA_V25_COUNT or epoch.stable_count != 432
        or epoch.theorem_edge_count != 6_633 or type(limits) is not CertificateLimits):
        raise ColdReplayError("cold replay requires the complete immutable Alpha-v25 epoch")
    if type(batch_size) is not int or not 1 <= batch_size <= 16:
        raise ColdReplayError("cold replay batch size must lie in [1,16]")
    targets = []
    seen: set[str] = set()
    for index, theorem in enumerate(epoch.theorems):
        record = cold_target_record(theorem)
        if (record["enrollment_index"] != index or record["name"] in seen
            or not set(record["dependencies"]) <= seen):
            raise ColdReplayError("cold replay changed the complete dependency-topological target order")
        seen.add(record["name"])
        targets.append(record)
    projection = [{"name": row["name"], "dependencies": row["dependencies"]} for row in targets]
    if (sum(len(row["dependencies"]) for row in targets) != epoch.theorem_edge_count
        or _digest(projection) != epoch.theorem_dag_sha256
        or sum(row["membership"] == "stable" for row in targets) != epoch.stable_count):
        raise ColdReplayError("cold replay target partition or dependency count differs")
    batches = [[row["enrollment_index"] for row in targets[start:start + batch_size]]
               for start in range(0, len(targets), batch_size)]
    record = {"schema": COLD_PLAN_SCHEMA, "status": "planned", "scope": "full-alpha-v25",
              "epoch": epoch.to_dict(), "epoch_sha256": epoch.epoch_sha256,
              "edition_identity_sha256": epoch.edition_identity_sha256,
              "target_count": len(targets), "targets": targets, "targets_sha256": _digest(targets),
              "passes": 2, "certificate_limits": limits.to_dict(), "batch_size": batch_size,
              "batches": batches, "batch_count": len(batches), "batches_sha256": _digest(batches),
              "cache_scope": "one-frozen-batch", "fresh_process_per_batch_required": True,
              "fresh_process_per_target_required": batch_size == 1, "parallel_workers": 1,
              "parent_resource_guard_required": True,
              "replay_mode": "public-native-runtime-certificate-replay",
              "all_scripts_regenerated": False, "lean_companion_required": False,
              "proofs_checked": 0, "research_claim_eligible": False}
    record["plan_sha256"] = _digest(record)
    if len(_canonical(record)) > MAX_PLAN_BYTES:
        raise ColdReplayError("cold replay plan exceeds its 32-MiB reservation")
    return record


def _layouts():
    from peano_lab.kernel import formulas as f, proofs as p, terms as t
    # Exact constructors and their REAL dataclass fields, never properties,
    # object addresses, generic repr(), trusted names, or serialized receipts.
    return {
        t.Var: ("term", "var", (("index", "nat"),)), t.Zero: ("term", "zero", ()),
        t.Succ: ("term", "succ", (("term", "term"),)),
        t.Add: ("term", "add", (("left", "term"), ("right", "term"))),
        t.Mul: ("term", "mul", (("left", "term"), ("right", "term"))),
        f.Bot: ("formula", "bot", ()), f.Eq: ("formula", "eq", (("left", "term"), ("right", "term"))),
        f.And: ("formula", "and", (("left", "formula"), ("right", "formula"))),
        f.Or: ("formula", "or", (("left", "formula"), ("right", "formula"))),
        f.Imp: ("formula", "imp", (("antecedent", "formula"), ("consequent", "formula"))),
        f.Forall: ("formula", "forall", (("body", "formula"),)),
        f.Exists: ("formula", "exists", (("body", "formula"),)),
        p.Hyp: ("proof", "hyp", (("i", "nat"),)),
        p.Axiom: ("proof", "axiom", (("name", "axiom"),)),
        p.ImpIntro: ("proof", "imp_intro", (("body", "proof"),)),
        p.ImpElim: ("proof", "imp_elim", (("f", "proof"), ("a", "proof"))),
        p.Cut: ("proof", "cut", (("proposition", "formula"), ("conclusion", "formula"), ("lemma", "proof"), ("body", "proof"))),
        p.AndIntro: ("proof", "and_intro", (("left", "proof"), ("right", "proof"))),
        p.AndElimL: ("proof", "and_elim_l", (("pair", "proof"),)),
        p.AndElimR: ("proof", "and_elim_r", (("pair", "proof"),)),
        p.OrIntroL: ("proof", "or_intro_l", (("proof", "proof"),)),
        p.OrIntroR: ("proof", "or_intro_r", (("proof", "proof"),)),
        p.OrElim: ("proof", "or_elim", (("disjunction", "proof"), ("left_case", "proof"), ("right_case", "proof"))),
        p.BotElim: ("proof", "bot_elim", (("absurdity", "proof"),)),
        p.ForallIntro: ("proof", "forall_intro", (("body", "proof"),)),
        p.ForallElim: ("proof", "forall_elim", (("p", "proof"), ("t", "term"))),
        p.ExistsIntro: ("proof", "exists_intro", (("t", "term"), ("p", "proof"))),
        p.ExistsElim: ("proof", "exists_elim", (("p", "proof"), ("body", "proof"))),
        p.EqRefl: ("proof", "eq_refl", (("t", "term"),)),
        p.EqSym: ("proof", "eq_sym", (("proof", "proof"),)),
        p.EqTrans: ("proof", "eq_trans", (("first", "proof"), ("second", "proof"))),
        p.CongS: ("proof", "cong_s", (("proof", "proof"),)),
        p.CongAdd: ("proof", "cong_add", (("left", "proof"), ("right", "proof"))),
        p.CongMul: ("proof", "cong_mul", (("left", "proof"), ("right", "proof"))),
        p.EqSubst: ("proof", "eq_subst", (("motive", "formula"), ("eq_proof", "proof"), ("body_proof", "proof"))),
        p.Ind: ("proof", "ind", (("motive", "formula"), ("base", "proof"), ("step", "proof"))),
    }


def _fingerprint(root: object, kind: str, limits: CertificateLimits) -> dict[str, object]:
    if type(limits) is not CertificateLimits:
        raise ColdReplayError("certificate fingerprint needs exact finite limits")
    layouts = _layouts()
    memo: dict[int, tuple[object, str, int, int, int, int]] = {}
    active: set[int] = set()
    pending = [(root, kind, False, 1)]
    objects = proof_objects = proof_edges = 0
    while pending:
        node, expected_kind, finished, path_depth = pending.pop()
        layout = layouts.get(type(node))
        if layout is None or layout[0] != expected_kind:
            raise ColdReplayError("certificate contains a foreign/classical or incorrectly typed constructor")
        if path_depth > limits.max_envelope_depth:
            raise ColdReplayError("certificate exceeds its envelope depth reservation")
        identity = id(node)
        if identity in memo:
            continue
        domain, tag, fields = layout
        if not finished:
            if identity in active:
                raise ColdReplayError("certificate contains cyclic native syntax")
            objects += 1
            proof_objects += int(domain == "proof")
            if objects > limits.max_syntax_objects or proof_objects > limits.max_proof_objects:
                raise ColdReplayError("certificate exceeds its distinct-object reservation")
            active.add(identity)
            pending.append((node, expected_kind, True, path_depth))
            children = []
            for field, field_kind in fields:
                value = getattr(node, field)
                if field_kind == "nat":
                    if type(value) is not int or not 0 <= value <= 2**31 - 1:
                        raise ColdReplayError("certificate has an invalid native natural field")
                elif field_kind == "axiom":
                    if type(value) is not str or value not in {"PA1", "PA2", "PA3", "PA4", "PA5", "PA6"}:
                        raise ColdReplayError("certificate has an unknown native arithmetic axiom")
                else:
                    children.append((value, field_kind, False, path_depth + 1))
                    proof_edges += int(domain == "proof" and field_kind == "proof")
            pending.extend(reversed(children))
            continue
        active.remove(identity)
        payload, child_stats, proof_child_depths = [], [], []
        for field, field_kind in fields:
            value = getattr(node, field)
            if field_kind in ("nat", "axiom"):
                payload.append([field, field_kind, value])
            else:
                child = memo.get(id(value))
                if child is None or child[0] is not value:
                    raise ColdReplayError("certificate changed during fingerprinting")
                payload.append([field, field_kind, child[1]])
                child_stats.append(child)
                if field_kind == "proof":
                    proof_child_depths.append(child[3])
        proof_nodes = int(domain == "proof") + sum(child[2] for child in child_stats)
        proof_depth = 1 + max(proof_child_depths, default=0) if domain == "proof" else 0
        annotation_nodes = int(domain != "proof") + sum(child[4] for child in child_stats)
        envelope_depth = 1 + max((child[5] for child in child_stats), default=0)
        if (proof_nodes > limits.max_proof_nodes or proof_depth > limits.max_proof_depth
            or annotation_nodes > limits.max_annotation_nodes or envelope_depth > limits.max_envelope_depth):
            raise ColdReplayError("certificate exceeds its structural proof/annotation reservation")
        memo[identity] = (node, _digest([CERTIFICATE_SCHEMA, domain, tag, payload]),
                          proof_nodes, proof_depth, annotation_nodes, envelope_depth)
    result = memo[id(root)]
    return {"schema": CERTIFICATE_SCHEMA, "sha256": result[1], "proof_nodes": result[2],
            "proof_depth": result[3], "annotation_nodes": result[4], "envelope_depth": result[5],
            "proof_objects": proof_objects, "proof_edges": proof_edges, "syntax_objects": objects,
            "sharing_independent_digest": True, "dne_objects": 0}


def fingerprint_certificate(
    proof: Proof, *, limits: CertificateLimits = CertificateLimits(),
) -> dict[str, object]:
    """Hash every exact native constructor field, without expanding DAG sharing.

    The digest represents the structural tree independent of Python identity
    sharing. Occurrence counts charge repeated references; object counts do
    not. This fingerprint alone is never evidence that the proof type-checks.
    """
    return _fingerprint(proof, "proof", limits)


def _runtime():
    # Lazy import: parent planning/adapter import never initializes Alpha.
    from peano_lab.library import editions_v25
    return editions_v25


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
    if (type(epoch_sha256) is not str or _SHA.fullmatch(epoch_sha256) is None
        or edition_identity_sha256 != ALPHA_V25_IDENTITY or type(limits) is not CertificateLimits):
        raise ColdReplayError("cold replay epoch or fingerprint policy differs")
    runtime = _runtime()
    if (runtime.ALPHA_V25_IDENTITY_SHA256 != edition_identity_sha256
        or len(runtime.ALPHA_EDITION.entries) != ALPHA_V25_COUNT):
        raise ColdReplayError("public native runtime changed its full Alpha-v25 identity")
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


__all__ = [
    "ALPHA_V25_COUNT", "ALPHA_V25_IDENTITY", "CERTIFICATE_SCHEMA", "COLD_PLAN_SCHEMA",
    "COLD_REPLAY_SCHEMA", "COLD_TARGET_SCHEMA", "MAX_PLAN_BYTES", "MAX_TARGET_BYTES",
    "CertificateLimits", "ColdReplayError", "build_cold_replay_plan", "cold_target_record",
    "fingerprint_certificate", "replay_cold_target",
]
