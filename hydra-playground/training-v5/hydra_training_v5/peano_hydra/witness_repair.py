"""CPU-only witness-notation fixtures and a deliberately partial dataset audit.

This is NOT another admitted posttraining source. Historical V1/V2 preparations,
V4 prompts, model weights and matched-search policies remain unchanged. The
fixtures are authored after exposed evaluation failures; coverage is not model
improvement, semantic independence, or permission to train.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Callable

from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
from peano_lab.kernel.formulas import (
    And, Bot, Eq, Exists, Forall, Imp, Or, _as_le,
    parse_formula_with_names, pretty_formula,
)
from peano_lab.kernel.terms import _TokenStream
from peano_lab.ui.prove import SurfaceCapabilities
from hydra_training_v5.peano_hydra import composition as _native
from hydra_training_v5.peano_hydra.curriculum import TRANSITION_SCHEMA as _HISTORICAL_TRANSITION_SCHEMA
from hydra_training_v5.peano_hydra.protocol import validate_statement
from hydra_training_v5.peano_policy.authority import (
    AUTHORITY_PRIMITIVE_PROFILE, authority_contract_record,
    authority_profile_record, validate_authority_tactic,
)
from hydra_training_v5.peano_policy.contract import (
    MODEL_V3_HELD_OUT_POLICY_GOALS, authority_prompt_environment,
)
from hydra_training_v5.peano_policy.prompt import (
    COMPLETION_SUFFIX, CapabilityIdentity, ProofExample, parse_prompt,
    render_prompt, validate_completion,
)
from hydra_training_v5.peano_policy.search import state_sha256


ROOT = Path(__file__).resolve().parents[2]
PLAN_SCHEMA = "peano-hydra-witness-repair-plan-v1"
SOURCE_SCHEMA = "peano-hydra-witness-repair-source-v1"
TRANSITION_SCHEMA = "peano-hydra-witness-repair-transition-v1"
COVERAGE_SCHEMA = "peano-hydra-witness-principal-coverage-v1"
AUDIT_SCHEMA = "peano-hydra-witness-preparation-audit-v1"
SOURCE_FILENAMES = ("plan.json", "sft.jsonl", "proofs.json", "coverage.json", "manifest.json")
MAX_ROUTES = 16
MAX_ROUTE_DECISIONS = 6
MAX_TRANSITIONS = 64
MAX_TRACE_BYTES = 128 * 1024
MAX_OUTPUT_BYTES = 2 * 1024**2
MAX_INPUT_FILE_BYTES = 64 * 1024**2
MAX_INPUT_TOTAL_BYTES = 192 * 1024**2
MAX_INPUT_ROWS = 32768
MAX_LINE_BYTES = 128 * 1024
MAX_GOAL_BYTES = 16384
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_FAMILIES = (
    ("closed_le_witness", "train", 4),
    ("universal_le_witness", "train", 4),
    ("universal_explicit_witness", "train", 4),
    ("assumed_le_unpack", "dev", 4),
)
_CLAIMS = {
    "authorship": "explicit-corrective-teachers-after-public-2026-08-28-failures",
    "public_and_correlated": True,
    "family_groups_are_independent_mathematical_components": False,
    "posttrain_admitted": False,
    "epoch_enrolled": False,
    "model_trained": False,
    "model_generation_performed": False,
    "model_weights_repaired": False,
    "autonomous_improvement_verified": False,
    "eligible_for_unseen_model_comparison": False,
    "research_claim_eligible": False,
    "training_authorized": False,
    "semantic_equivalence_complete": False,
}
_PREPARATION_FILES = {"config.toml", "train.jsonl", "dev.jsonl", "quarantine.jsonl",
                      "preferences.jsonl", "discovery.jsonl", "manifest.json"}
_ORIGINAL_SOURCE_FILES = {"epoch.json", "manifest.json", "sft.jsonl", "preferences.jsonl", "discovery.jsonl"}
_SOURCE_DIGEST_FIELDS = {
    "epoch.json": "epoch_file_sha256", "manifest.json": "manifest_sha256",
    "sft.jsonl": "sft_sha256", "preferences.jsonl": "preferences_sha256",
    "discovery.jsonl": "discovery_sha256",
}
_EXAMPLE_FIELDS = {
    "schema", "epoch_sha256", "edition_identity_sha256", "theorem_name",
    "theorem_statement_sha256", "lineage_sha256", "split", "source_split",
    "source_transition_sha256", "state_sha256", "action", "prompt", "completion",
    "environment_sha256", "kernel_checked", "transition",
}


class WitnessRepairError(ValueError):
    """The bounded fixture or its explicitly limited coverage audit failed."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise WitnessRepairError(message)


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _pretty(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2) + "\n").encode()


def _decode(raw: bytes) -> dict[str, object]:
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "duplicate JSON field")
            result[key] = value
        return result

    def nonfinite(value):
        raise WitnessRepairError(f"non-finite JSON value: {value}")

    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise WitnessRepairError("invalid bounded JSON object") from error
    _require(type(value) is dict, "expected one JSON object")
    return value


def _directory(path: Path, *, fresh: bool = False) -> Path:
    _require(isinstance(path, Path), "directory must be an explicit Path")
    path = path.absolute()
    _require(not any(part == ".." for part in path.parts), "parent traversal is not allowed")
    _require(not path.is_symlink() and not any(parent.is_symlink() for parent in path.parents),
             "directory and ancestors must not be symlinks")
    if fresh:
        _require(not path.exists(), "output already exists; fresh output is required")
    else:
        _require(path.is_dir(), "input must be a real directory")
    return path


def _inventory(path: Path, names: set[str]) -> None:
    seen = set()
    with os.scandir(path) as entries:
        for entry in entries:
            _require(entry.name in names and entry.is_file(follow_symlinks=False)
                     and not entry.is_symlink(), "directory inventory contains an unexpected or unsafe entry")
            seen.add(entry.name)
    _require(seen == names, "directory inventory is incomplete")


def _signature(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)


def _scan(path: Path, visitor: Callable[[dict[str, object]], None] | None = None) -> dict[str, object]:
    """Bounded streaming read: do not retain a large preparation in memory."""
    digest, count, total = hashlib.sha256(), 0, 0
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        _require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                 and before.st_size <= MAX_INPUT_FILE_BYTES, "input is not a bounded single-link regular file")
        jsonl = path.suffix == ".jsonl"
        while True:
            raw = stream.readline(MAX_LINE_BYTES + 1) if jsonl else stream.read(1024 * 1024)
            if not raw:
                break
            total += len(raw)
            _require(total <= MAX_INPUT_FILE_BYTES, "input exceeds byte bound")
            digest.update(raw)
            if jsonl:
                _require(len(raw) <= MAX_LINE_BYTES and raw.endswith(b"\n") and raw != b"\n",
                         "JSONL line exceeds its bound or is blank/truncated")
                row = _decode(raw)
                _require(_canonical(row) + b"\n" == raw, "JSONL is not exact canonical text")
                count += 1
                _require(count <= MAX_INPUT_ROWS, "JSONL exceeds row bound")
                if visitor is not None:
                    visitor(row)
        after = os.fstat(stream.fileno())
    _require(total == before.st_size and _signature(before) == _signature(after)
             and _signature(before) == _signature(path.lstat()), "input changed during streaming audit")
    result = {"bytes": total, "sha256": digest.hexdigest()}
    if path.suffix == ".jsonl":
        result["rows"] = count
    return result


def _source_identity() -> dict[str, object]:
    files = dict(_native._source_identity()["files"])
    for name in ("training/peano_hydra/witness_repair.py", "scripts/prepare_peano_hydra_witness_repair.py",
                 "training/peano_hydra/comparison.py", "training/peano_hydra/protocol.py",
                 "training/peano_policy/manifest.py", "training/peano_hydra/review_runtime.py",
                 "scripts/hydra_bounded_exec.py"):
        files[name] = hashlib.sha256(_native._read(ROOT / name, maximum=2 * 1024**2)).hexdigest()
    files = dict(sorted(files.items()))
    return {"files": files, "source_files_sha256": _digest(files),
            "coverage": "listed fixture, prompt, exclusion, publication and native replay sources; not whole-repository attestation"}


def _authority():
    caps = SurfaceCapabilities(label=_native.NATIVE_AUTHORITY_LABEL, allowed_commands=MODEL_V1_COMMANDS,
                               allowed_theorems=frozenset())
    identity = CapabilityIdentity(caps.label, tuple(sorted(MODEL_V1_COMMANDS)), ())
    environment = authority_prompt_environment(False, identity)
    authority = {"capabilities": identity.to_record(), "environment_sha256": environment.sha256, "classical": False}
    return caps, environment, authority


def excluded_targets() -> tuple[dict[str, str], ...]:
    from hydra_training_v5.peano_hydra.comparison import comparison_goals
    rows = [{"name": row["name"], "statement": row["statement"], "cohort": row["cohort"]}
            for row in comparison_goals()]
    _require(len(rows) == 96, "public comparison exclusion inventory changed")
    rows += [{"name": name, "statement": validate_statement(source), "cohort": "historical-four"}
             for name, source in MODEL_V3_HELD_OUT_POLICY_GOALS]
    _require(len(rows) == 100 and len({row["name"] for row in rows}) == 100,
             "exact public/historical exclusion inventory changed")
    return tuple(rows)


def _route(family: str, seed: int) -> tuple[str, tuple[str, ...]]:
    k = seed + 1
    if family == "closed_le_witness":
        witness = (0, 1, 2, 4)[seed]
        return f"exists w. w + 4 = {4 + witness}", (f"exists {witness}", "norm_num")
    if family == "universal_le_witness":
        return f"forall a. a <= {k} + a", ("intro a", f"exists {k}", "refl")
    if family == "universal_explicit_witness":
        return (f"forall a. exists w. (w + a = {k} + a /\\ w = {k})",
                ("intro a", f"exists {k}", "split", "refl", "refl"))
    if family == "assumed_le_unpack":
        return (f"forall a b. a <= b + {k} -> a <= b + {k}",
                ("intro a", "intro b", "intro h", "cases h", "exists x", "exact h_witness"))
    raise WitnessRepairError("undeclared corrective family")


def build_witness_repair_plan() -> dict[str, object]:
    """Declare all 16 fixtures; no QED, dataset reload, epoch freeze, or model."""
    _, environment, authority = _authority()
    excluded = excluded_targets()
    forbidden = {row["statement"] for row in excluded}
    families, routes = [], []
    for family, split, count in _FAMILIES:
        declaration = {"name": family, "split": split, "seeds": list(range(count))}
        lineage = _digest({"authorship": _CLAIMS["authorship"], "family": declaration})
        families.append({**declaration, "lineage_sha256": lineage})
        for seed in range(count):
            source, commands = _route(family, seed)
            statement = validate_statement(source)
            _require(statement not in forbidden, "fixture is an excluded exact original goal")
            _require(1 <= len(commands) <= MAX_ROUTE_DECISIONS, "fixture exceeds decision bound")
            for command in commands:
                validate_authority_tactic(command, environment)
            routes.append({"name": f"hydra_witness_repair_{family}_{seed:02d}", "family": family,
                           "split": split, "generator_seed": seed, "lineage_sha256": lineage,
                           "source": source, "statement": statement,
                           "statement_sha256": hashlib.sha256(statement.encode()).hexdigest(),
                           "commands": list(commands), "commands_sha256": _digest(list(commands))})
    _require(len(routes) == MAX_ROUTES and len({row["statement"] for row in routes}) == MAX_ROUTES,
             "corrective inventory is incomplete or has duplicate canonical goals")
    _require(sum(len(row["commands"]) for row in routes) == MAX_TRANSITIONS,
             "corrective transition reservation changed")
    result = {"schema": PLAN_SCHEMA, "authority_profile": AUTHORITY_PRIMITIVE_PROFILE,
              "authority": authority, "prompt_contract": authority_contract_record(),
              "decoder_profile": authority_profile_record(environment), "source_identity": _source_identity(),
              "epoch_binding": "none: standalone native fixtures, not an enrolled or posttraining corpus",
              "families": families, "routes": routes, "route_count": len(routes),
              "transition_count": MAX_TRANSITIONS, "split_policy": "whole-corrective-families-exposed-v1",
              "excluded_targets": list(excluded), "excluded_targets_sha256": _digest(excluded),
              "claims": dict(_CLAIMS), "kernel_checked": False,
              "limits": {"routes": MAX_ROUTES, "route_decisions": MAX_ROUTE_DECISIONS,
                         "transitions": MAX_TRANSITIONS, "trace_bytes": MAX_TRACE_BYTES,
                         "output_bytes": MAX_OUTPUT_BYTES}}
    return {**result, "plan_sha256": _digest(result)}


def _target(goal: str) -> str:
    _require(type(goal) is str and 0 < len(goal.encode()) <= MAX_GOAL_BYTES
             and goal.count("⊢") == 1 and "\n" not in goal and "\r" not in goal,
             "goal is not bounded canonical one-line state text")
    prefix, separator, target = goal.partition("⊢ ")
    _require(bool(separator) and bool(target) and (not prefix or prefix.endswith(" ")),
             "goal lost its canonical turnstile")
    return target


def _formula(text: str):
    """Preflight native lexical tokens before constructing unary numerals."""
    _require(type(text) is str and len(text.encode()) <= MAX_GOAL_BYTES, "formula exceeds byte bound")
    try:
        tokens = _TokenStream(text).tokens
        _require(len(tokens) <= 4096, "formula exceeds token bound")
        depth = 0
        for token in tokens:
            value = token.text
            if value[0].isdigit():
                _require(re.fullmatch(r"[0-9]{1,7}", value) is not None
                         and int(value) <= 1_000_000, "formula numeral exceeds conservative parser bound")
            depth += (value == "(") - (value == ")")
            _require(0 <= depth <= 64, "formula exceeds parenthesis bound")
        return parse_formula_with_names(text)
    except (ValueError, RecursionError) as error:
        raise WitnessRepairError(f"cannot classify bounded native goal: {error}") from error


def _principal_formula(text: str):
    """Parse display-only ?tN leaves without interpreting their substitutions.

    Only the outer constructor is observed. The actual audit retains the
    original text and hashes; rigid fixture/exclusion parsing uses _formula
    directly and never accepts engine metavariables.
    """
    _require(type(text) is str and len(text.encode()) <= MAX_GOAL_BYTES, "formula exceeds byte bound")
    if "?" not in text:
        return _formula(text)[0], False
    prefix = "_witness_display_meta_"
    while prefix in text:
        prefix = "_" + prefix
    aliases = {}
    def replace(match):
        label = match.group(0)
        if label not in aliases:
            aliases[label] = f"{prefix}{len(aliases)}"
        return aliases[label]
    normalized = re.sub(r"(?<![\w'?])\?t[1-9][0-9]*(?![\w'?])", replace, text)
    _require(bool(aliases) and "?" not in normalized, "malformed displayed term metavariable")
    _require(len(normalized.encode()) <= MAX_GOAL_BYTES, "normalized display formula exceeds byte bound")
    try:
        tokens = _TokenStream(normalized).tokens
    except ValueError as error:
        raise WitnessRepairError(f"cannot classify bounded native display goal: {error}") from error
    _require(len(tokens) <= 4096, "formula exceeds token bound")
    bound_names, declaring = set(aliases.values()), False
    for token in tokens:
        if token.text in {"forall", "exists", "∀", "∃"}:
            declaring = True
        elif declaring and token.text == ".":
            declaring = False
        elif declaring:
            _require(token.text not in bound_names, "displayed metavariables cannot be binders")
    return _formula(normalized)[0], True


def principal_goal_form(goal: str) -> str:
    formula, has_metas = _principal_formula(_target(goal))
    if type(formula) is Exists:
        # The native engine's MetaVar renderer does not apply <= sugar.
        return "le_exists" if not has_metas and _as_le(formula) is not None else "explicit_exists"
    kinds = {Forall: "forall", Eq: "equality", And: "conjunction", Or: "disjunction",
             Imp: "implication", Bot: "false"}
    _require(type(formula) in kinds, "unrecognized native principal formula")
    return kinds[type(formula)]


def _empty_counts() -> dict[str, object]:
    return {"rows": 0, "action_heads": {}, "principal_actions": {}, "literal_witnesses": {},
            "state_contains_le_rows": 0, "focused_target_contains_le_rows": 0,
            "display_metavariable_goal_rows": 0,
            "principal_le_exists_rows": 0, "explicit_exists_exists_rows": 0,
            "forall_intro_rows": 0, "misaligned_exists_rows": 0}


def _increment(mapping: dict, key: str) -> None:
    mapping[key] = mapping.get(key, 0) + 1


def _observe(counts: dict, row: dict[str, object]) -> None:
    before, focus, action = row.get("goals_before"), row.get("focus"), row.get("action")
    _require(type(before) is list and 0 < len(before) <= 64 and all(type(x) is str for x in before)
             and type(focus) is int and 0 <= focus < len(before)
             and type(action) is str and bool(action) and action.strip() == action,
             "transition has invalid focused state/action")
    goal = before[focus]
    form = principal_goal_form(goal)
    head = action.split()[0]
    counts["rows"] += 1
    _increment(counts["action_heads"], head)
    _increment(counts["principal_actions"].setdefault(form, {}), head)
    counts["state_contains_le_rows"] += int(any("≤" in x for x in before))
    counts["focused_target_contains_le_rows"] += int("≤" in _target(goal))
    counts["display_metavariable_goal_rows"] += int("?" in _target(goal))
    counts["principal_le_exists_rows"] += int(form == "le_exists" and head == "exists")
    counts["explicit_exists_exists_rows"] += int(form == "explicit_exists" and head == "exists")
    counts["forall_intro_rows"] += int(form == "forall" and head == "intro")
    counts["misaligned_exists_rows"] += int(head == "exists" and form not in {"le_exists", "explicit_exists"})
    if re.fullmatch(r"exists [0-9]+", action):
        _increment(counts["literal_witnesses"], action)


def _coverage(splits: dict[str, dict]) -> dict[str, object]:
    train = splits["train"]
    needed = ("principal_le_exists_rows", "explicit_exists_exists_rows", "forall_intro_rows")
    missing = [key for key in needed if train[key] == 0]
    if train["misaligned_exists_rows"]:
        missing.append("misaligned_exists_labels")
    result = {"schema": COVERAGE_SCHEMA, "splits": splits,
              "principal_parser_scope": "bounded native outer-constructor parsing; displayed ?tN term leaves use transient fresh names only, no unification, substitution or native proof verification",
              "gate": {"scope": "TRAIN principal-form/action presence only, not a model readiness claim",
                       "status": "blocked" if missing else "covered", "missing": missing,
                       "minimum_rows_per_required_pair": 1,
                       "required_pairs": ["le_exists -> exists", "explicit_exists -> exists", "forall -> intro"]},
              "claims": dict(_CLAIMS)}
    return {**result, "coverage_sha256": _digest(result)}


def _check_intermediates(rows: tuple[dict, ...], forbidden: set[str]) -> None:
    for row in rows:
        for goal in (*row["goals_before"], *row["goals_after"]):
            formula, names = _formula(_target(goal))
            if not names:
                _require(pretty_formula(formula, list(names)) not in forbidden,
                         "fixture exposes an excluded closed intermediate goal")


@dataclass(frozen=True, slots=True)
class WitnessRepairSource:
    plan: dict[str, object]
    manifest: dict[str, object]
    rows: tuple[dict[str, object], ...]
    payloads: dict[str, bytes]


def build_witness_repair_source() -> WitnessRepairSource:
    """Check exactly the authored microfixtures; never replay a catalog."""
    plan = build_witness_repair_plan()
    caps, environment, _ = _authority()
    rows, proofs, seen = [], [], {}
    counts = {split: _empty_counts() for split in ("train", "dev")}
    for route in plan["routes"]:
        result = run_proof(route["source"], tuple(route["commands"]), request_id=route["name"],
                           session_id=route["name"], classical=False, on_error="stop",
                           capabilities=caps, trace_byte_limit=MAX_TRACE_BYTES)
        _native._checked_result(result, route, caps=caps, environment_sha256=environment.sha256)
        for step, trace in enumerate(result.trace[:-1], 1):
            command = route["commands"][step - 1]
            _require(trace.get("status") == "ok" and trace.get("tactic") == command
                     and trace.get("step") == step and trace.get("error") is None
                     and trace.get("session") == route["name"], "fixture transition lost its exact command or trace")
            before, after, focus = trace["goals_before"], trace["goals_after"], trace["focus"]
            _require(step == 1 or before == result.trace[step - 2]["goals_after"], "fixture trace is disconnected")
            prompt = render_prompt(goals=tuple(before), focus=focus, environment=environment)
            example = ProofExample(f"{route['name']}:{step}", prompt, command + COMPLETION_SUFFIX, environment.sha256)
            row = {"schema": TRANSITION_SCHEMA, "plan_sha256": plan["plan_sha256"],
                   "theorem_name": route["name"], "theorem": route["statement"],
                   "family": route["family"], "split": route["split"], "lineage_sha256": route["lineage_sha256"],
                   "step": step, "goals_before": before, "goals_after": after, "focus": focus,
                   "state_sha256": state_sha256(tuple(before)), "action": example.tactic,
                   "action_head": command.split()[0], "prompt": prompt, "completion": example.completion,
                   "environment_sha256": environment.sha256, "commands_sha256": route["commands_sha256"],
                   "authority_profile": AUTHORITY_PRIMITIVE_PROFILE, "kernel_checked": True,
                   "proof_nodes": result.proof_nodes, "research_claim_eligible": False}
            key = (row["state_sha256"], focus, command)
            _require(key not in seen or seen[key] == route["split"], "exact state/action overlaps TRAIN and DEV")
            seen[key] = route["split"]
            _observe(counts[route["split"]], row)
            rows.append(row)
        proofs.append({"name": route["name"], "statement": route["statement"], "kernel_checked": True,
                       "commands_sha256": route["commands_sha256"], "proof_nodes": result.proof_nodes,
                       "trace_sha256": _digest(result.trace), "trace": list(result.trace)})
    _require(len(rows) == MAX_TRANSITIONS, "fixture replay did not emit every transition")
    _check_intermediates(tuple(rows), {r["statement"] for r in plan["excluded_targets"]})
    coverage = _coverage(counts)
    _require(coverage["gate"]["status"] == "covered", "corrective fixtures do not cover their declared pairs")
    payloads = {"plan.json": _pretty(plan), "sft.jsonl": b"".join(_canonical(row) + b"\n" for row in rows),
                "proofs.json": _pretty({"proofs": proofs}), "coverage.json": _pretty(coverage)}
    manifest = {"schema": SOURCE_SCHEMA, "plan_sha256": plan["plan_sha256"],
                "source_identity": plan["source_identity"], "authority": plan["authority"],
                "prompt_contract": plan["prompt_contract"], "decoder_profile": plan["decoder_profile"],
                "route_count": len(proofs), "transition_count": len(rows),
                "split_route_counts": dict(Counter(r["split"] for r in plan["routes"])),
                "split_transition_counts": {key: value["rows"] for key, value in counts.items()},
                "coverage_sha256": coverage["coverage_sha256"], "kernel_checked": True,
                "exact_original_target_overlaps": 0, "exact_closed_intermediate_overlaps": 0,
                "exact_cross_split_state_action_overlaps": 0, "claims": dict(_CLAIMS),
                "files": {name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                          for name, raw in sorted(payloads.items())}}
    payloads["manifest.json"] = _pretty(manifest)
    _require(sum(map(len, payloads.values())) <= MAX_OUTPUT_BYTES, "fixture bundle exceeds byte bound")
    _require(build_witness_repair_plan() == plan, "fixture or native source changed during replay")
    return WitnessRepairSource(plan, manifest, tuple(rows), payloads)


def publish_witness_repair_source(source: WitnessRepairSource, directory: Path) -> Path:
    """Recheck the 16 fixtures and publish atomically, never replace a directory."""
    from hydra_training_v5.peano_policy.manifest import publish_staged_directory_noreplace
    directory = _directory(directory, fresh=True)
    _require(type(source) is WitnessRepairSource, "publication requires a checked fixture source")
    fresh = build_witness_repair_source()
    _require(source == fresh, "refusing to publish altered fixture evidence")
    directory.parent.mkdir(parents=True, exist_ok=True)
    _directory(directory.parent)
    staging = Path(tempfile.mkdtemp(prefix=f".{directory.name}.partial-", dir=directory.parent))
    for name in SOURCE_FILENAMES:
        with (staging / name).open("xb") as stream:
            stream.write(fresh.payloads[name])
            stream.flush()
            os.fsync(stream.fileno())
    # Failed staging remains inspectable. No cleanup removes existing data.
    publish_staged_directory_noreplace(staging, directory)
    return directory


def _audit_example(row: dict, *, split: str, manifest: dict, source_rows: set[str], used: set[str]) -> dict:
    authority = manifest["schema"] == "peano-hydra-posttrain-preparation-v2"
    expected = _EXAMPLE_FIELDS | ({"authority_profile", "family"} if authority else set())
    _require(set(row) == expected and row.get("schema") == f"peano-hydra-posttrain-example-v{2 if authority else 1}",
             "preparation example fields or schema changed")
    transition = row["transition"]
    _require(type(transition) is dict and row["kernel_checked"] is True and transition.get("kernel_checked") is True,
             "example lacks its source transition or historical checked flag")
    _require(transition.get("schema") == _HISTORICAL_TRANSITION_SCHEMA
             and transition.get("epoch_sha256") == row["epoch_sha256"]
             and transition.get("research_claim_eligible") is False,
             "example changed its historical transition identity")
    identity = _digest(transition)
    _require(row["source_transition_sha256"] == identity and identity in source_rows and identity not in used,
             "example source membership is changed or duplicated")
    used.add(identity)
    _require(row["split"] == split and row["source_split"] == transition.get("split"), "example split changed")
    for field in ("epoch_sha256", "edition_identity_sha256"):
        _require(row[field] == manifest.get(field), "example changed its preparation epoch identity")
    for field in ("theorem_name", "lineage_sha256", "state_sha256", "action", "prompt", "completion", "environment_sha256"):
        _require(row[field] == transition.get(field), "example wrapper differs from its exact source transition")
    _require(type(transition.get("theorem")) is str and type(row["theorem_statement_sha256"]) is str
             and hashlib.sha256(transition["theorem"].encode()).hexdigest() == row["theorem_statement_sha256"],
             "example statement digest differs from its canonical source statement")
    parsed = parse_prompt(row["prompt"])
    _require(validate_completion(row["completion"]) == row["action"]
             and parsed.environment_sha256 == row["environment_sha256"]
             and list(parsed.goals) == transition.get("goals_before") and parsed.focus == transition.get("focus")
             and state_sha256(parsed.goals) == row["state_sha256"], "example prompt/state/action binding changed")
    if authority:
        _, environment, expected_authority = _authority()
        _require(row["authority_profile"] == AUTHORITY_PRIMITIVE_PROFILE
                 and row["family"] == transition.get("family") and row["source_split"] == split
                 and manifest.get("authority") == expected_authority
                 and parsed.prompt_version == 4 and parsed.environment_sha256 == environment.sha256,
                 "V4 authority or whole-family split changed")
        validate_authority_tactic(row["action"], environment)
    else:
        _require(parsed.prompt_version == 1, "legacy audit requires its original V1 prompt")
    return transition


def audit_witness_coverage(preparation_dir: Path, *, source_directory: Path,
                          expected_manifest_sha256: str | None = None) -> dict[str, object]:
    """Hash/row-join coverage audit, NOT native source or preparation verification.

    The explicit source directory supports preserved historical locations;
    its bytes must match the original preparation. No current epoch is frozen,
    no original teacher is replayed, and no source/profile is relabelled.
    """
    preparation = _directory(preparation_dir)
    source = _directory(source_directory)
    _inventory(preparation, _PREPARATION_FILES)
    _inventory(source, _ORIGINAL_SOURCE_FILES)
    implementation = _source_identity()
    raw = _native._read(preparation / "manifest.json", maximum=4 * 1024**2)
    raw_sha = hashlib.sha256(raw).hexdigest()
    if expected_manifest_sha256 is not None:
        _require(type(expected_manifest_sha256) is str and _SHA.fullmatch(expected_manifest_sha256) is not None
                 and raw_sha == expected_manifest_sha256, "preparation differs from the caller-pinned manifest SHA")
    manifest = _decode(raw)
    _require(manifest.get("schema") in {"peano-hydra-posttrain-preparation-v1", "peano-hydra-posttrain-preparation-v2"},
             "unsupported preparation schema; corrective fixture is not a posttraining preparation")
    files, declared_source = manifest.get("files"), manifest.get("source")
    _require(type(files) is dict and set(files) == _PREPARATION_FILES - {"manifest.json"}
             and type(declared_source) is dict, "preparation artifact inventory changed")
    if manifest["schema"].endswith("v2"):
        _require(manifest.get("authority_profile") == AUTHORITY_PRIMITIVE_PROFILE,
                 "authority preparation profile changed")
    source_rows, used = set(), set()
    inputs, total = {}, len(raw)

    def remember(row):
        identity = _digest(row)
        _require(identity not in source_rows, "duplicate exact source transition")
        source_rows.add(identity)

    for name in sorted(_ORIGINAL_SOURCE_FILES):
        record = _scan(source / name, remember if name == "sft.jsonl" else None)
        _require(record["sha256"] == declared_source.get(_SOURCE_DIGEST_FIELDS[name]), "original source file SHA differs")
        inputs["source/" + name] = record
        total += record["bytes"]
        _require(total <= MAX_INPUT_TOTAL_BYTES, "audit inputs exceed aggregate byte bound")
    counts = {split: _empty_counts() for split in ("train", "dev")}
    family_splits = {}
    for name in sorted(files):
        split = name[:-6] if name in {"train.jsonl", "dev.jsonl"} else None

        def visit(row):
            transition = _audit_example(row, split=split, manifest=manifest, source_rows=source_rows, used=used)
            if "family" in row:
                family = row["family"]
                _require(type(family) is str and family and family_splits.get(family, split) == split,
                         "one teacher family was assigned across splits")
                family_splits[family] = split
            _observe(counts[split], transition)

        record = _scan(preparation / name, visit if split is not None else None)
        _require(_canonical(record) == _canonical(files[name]), "preparation file bytes/rows/SHA changed")
        inputs["preparation/" + name] = record
        total += record["bytes"]
        _require(total <= MAX_INPUT_TOTAL_BYTES, "audit inputs exceed aggregate byte bound")
    inputs["preparation/manifest.json"] = {"bytes": len(raw), "sha256": raw_sha}
    # Re-read every input before returning. This detects changed final bytes;
    # it is not filesystem/hardware attestation or protection against a hostile
    # writer that changes and restores bytes between observations.
    for relative, expected in inputs.items():
        directory, name = relative.split("/", 1)
        actual = _scan((preparation if directory == "preparation" else source) / name)
        _require(actual == expected, "audit input changed before publication")
    _inventory(preparation, _PREPARATION_FILES)
    _inventory(source, _ORIGINAL_SOURCE_FILES)
    _require(_source_identity() == implementation, "audit implementation changed during execution")
    coverage = _coverage(counts)
    result = {"schema": AUDIT_SCHEMA, "status": "partial-byte-binding-and-principal-coverage-audit",
              "preparation_directory": str(preparation), "source_directory": str(source),
              "preparation_manifest_sha256": raw_sha, "caller_manifest_pin_checked": expected_manifest_sha256 is not None,
              "original_preparation_schema": manifest["schema"], "original_source_identity": declared_source,
              "epoch_sha256": manifest.get("epoch_sha256"), "source_identity": implementation,
              "inputs": inputs, "inputs_sha256": _digest(inputs), "source_transition_rows": len(source_rows),
              "selected_unique_transition_rows": len(used), "coverage": coverage, "claims": dict(_CLAIMS),
              "native_preparation_verification_performed": False, "original_source_proofs_replayed": False,
              "training_configuration_revalidated": False, "model_or_adapter_artifacts_verified": False,
              "historical_checked_flags_are_not_new_proof_checks": True}
    return {**result, "audit_sha256": _digest(result)}


__all__ = ["PLAN_SCHEMA", "SOURCE_SCHEMA", "TRANSITION_SCHEMA", "COVERAGE_SCHEMA", "AUDIT_SCHEMA",
           "WitnessRepairError", "WitnessRepairSource", "build_witness_repair_plan",
           "build_witness_repair_source", "publish_witness_repair_source", "principal_goal_form",
           "audit_witness_coverage", "excluded_targets"]
