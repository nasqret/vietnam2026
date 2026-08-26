"""Matched, verifier-backed evaluation of one frozen Hydra Alpha epoch.

Planning is intentionally model-free. A preparation directory is accepted only
after its immutable Alpha identities, every artifact byte, historical held-out
contract, and entire quarantined proof lineages agree. Unavailable or merely
declared models never produce invented success rates.

Actual inference is a separate explicit operation. It loads the pinned Qwen
base and the newly trained Alpha LoRA *sequentially* on one CUDA device, gives
both lanes the same goals, capability authority, decode policy and search
budget, and accepts a proof only after Hydra's independent original-goal
kernel replay. This remains product evidence, not a sealed H0/H1 claim.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
import gc
import hashlib
import json
from pathlib import Path
import random
import re
from typing import Any

from peano_lab.batch import MODEL_V1_COMMANDS
from peano_lab.kernel.formulas import ParseError, parse_formula_with_names, pretty_formula
from training.peano_hydra.curriculum import _lineage_index
from training.peano_hydra.epoch import HydraEpoch, HydraEpochError, freeze_epoch
from training.peano_hydra.policy import (
    FixedCandidatePolicy,
    HydraCandidatePolicy,
    PolicyHead,
)
from training.peano_hydra.posttrain import (
    MAX_OPTIMIZER_STEPS,
    RUNTIME_LOCK_SCHEMA,
    _config as posttraining_config,
)
from training.peano_hydra.runner import HydraRunnerError, policy_environment, run_hydra
from training.peano_policy.contract import (
    MODEL_V3_HELD_OUT_POLICY_GOALS,
    canonical_held_out_formulas,
    held_out_contract_sha256,
    prompt_environment,
)
from training.peano_policy.pretrained_baseline import (
    EXPECTED_BASE_MODEL_ID,
    EXPECTED_BASE_MODEL_REVISION,
)
from training.peano_policy.evaluation_replay import (
    EvaluationReplayError,
    _validate_runtime_identity,
)
from training.peano_policy.manifest import (
    require_safetensors_adapter,
    verify_artifact_directory,
)
from training.peano_policy.objective import completion_objective_record
from training.peano_policy.prompt import (
    PEANO_PROMPT_V3,
    CapabilityIdentity,
    ProofExample,
    parse_prompt,
)
from training.peano_policy.search import MAX_SEARCH_DEPTH, SearchLimits
from training.peano_policy.training_evidence import (
    TrainingEvidenceError,
    _finite_metrics,
    _validate_adapter_update,
    _validate_gradients,
    _validate_runtime,
)


EVALUATION_SCHEMA = "peano-hydra-posttrain-matched-evaluation-v1"
PREPARATION_SCHEMA = "peano-hydra-posttrain-preparation-v1"
EXAMPLE_SCHEMA = "peano-hydra-posttrain-example-v1"
QUARANTINE_SCHEMA = "peano-hydra-posttrain-quarantine-v1"
ADAPTER_SCHEMA = "peano-hydra-posttrain-adapter-v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PREPARATION_FILENAMES = (
    "train.jsonl",
    "dev.jsonl",
    "preferences.jsonl",
    "discovery.jsonl",
    "quarantine.jsonl",
    "config.toml",
)
MAX_MANIFEST_BYTES = 4 * 1_024 * 1_024
MAX_DATASET_BYTES = 64 * 1_024 * 1_024
MAX_TOTAL_DATASET_BYTES = 96 * 1_024 * 1_024
MAX_DATASET_ROWS = 16_384
MAX_EVALUATION_GOALS = 8
MAX_BEAM_WIDTH = 16
MAX_CANDIDATES_PER_STATE = 8
MAX_MODEL_CALLS_PER_GOAL = 64
MAX_MODEL_CALLS_PER_LANE = 256
MAX_SEARCH_STATES = 2_048
MAX_NEW_TOKENS = 128
MAX_ADAPTER_FILE_BYTES = 512 * 1_024 * 1_024
MAX_GOAL_EVIDENCE_BYTES = 1_024 * 1_024
MAX_LANE_EVIDENCE_BYTES = 8 * 1_024 * 1_024
DEFAULT_MAX_NEW_TOKENS = 64
DEFAULT_SEED = 20260826
DEFAULT_LIMITS = SearchLimits(
    max_depth=16,
    beam_width=4,
    candidates_per_state=4,
    max_model_calls=32,
    max_states=128,
)
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_REVISION = re.compile(r"[0-9a-f]{40}\Z")
_RELATION = re.compile(r"<=|≤|=")
_MULTIPLICATION = re.compile(r"[*·]")
_ADDITION = re.compile(r"\+")
_CONNECTIVE = re.compile(r"->|→|/\\|\\/|[∧∨¬~]")
_SAFE_SYMBOLIC_CANDIDATES = (
    "norm_num",
    "simp",
    "intro n",
    "exists 5",
    "induction n",
    "refl",
    "assumption",
    "simp [IH]",
)
_QUARANTINE_FORBIDDEN_FIELDS = frozenset(
    {
        "theorem",
        "statement",
        "commands",
        "action",
        "completion",
        "prompt",
        "goals_before",
        "goals_after",
        "transition",
        "proof",
        "certificate",
    }
)


class HydraEvaluationError(ValueError):
    """The prepared comparison lost an identity, holdout, or resource bound."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise HydraEvaluationError(f"duplicate JSON field {key!r}")
        result[key] = value
    return result


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise HydraEvaluationError(f"evaluation evidence is not strict JSON: {error}") from None


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _sha256(value: object, *, field: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise HydraEvaluationError(f"{field} must be one lowercase SHA-256 digest")
    return value


def _read_regular(path: Path, *, maximum: int, description: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise HydraEvaluationError(f"{description} must be a regular non-symlink file")
    try:
        if path.stat().st_size > maximum:
            raise HydraEvaluationError(f"{description} exceeds its {maximum}-byte limit")
        payload = path.read_bytes()
    except OSError as error:
        raise HydraEvaluationError(f"cannot read {description}: {error}") from None
    if len(payload) > maximum:
        raise HydraEvaluationError(f"{description} exceeds its {maximum}-byte limit")
    return payload


def _json_object(raw: bytes, *, description: str) -> dict[str, object]:
    try:
        result = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=lambda item: (_ for _ in ()).throw(
                HydraEvaluationError(f"{description} contains non-finite number {item!r}")
            ),
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise HydraEvaluationError(f"{description} is malformed: {error}") from None
    if type(result) is not dict:
        raise HydraEvaluationError(f"{description} must contain exactly one JSON object")
    return result


def _jsonl(raw: bytes, *, filename: str) -> tuple[dict[str, object], ...]:
    if raw and not raw.endswith(b"\n"):
        raise HydraEvaluationError(f"{filename} contains a truncated JSONL record")
    lines = raw.splitlines()
    if len(lines) > MAX_DATASET_ROWS:
        raise HydraEvaluationError(f"{filename} exceeds its exact row-count boundary")
    if any(not line for line in lines):
        raise HydraEvaluationError(f"{filename} contains a blank JSONL record")
    return tuple(
        _json_object(line, description=f"{filename} row {index}")
        for index, line in enumerate(lines, 1)
    )


@lru_cache(maxsize=8_192)
def _canonical_formula(source: str) -> str:
    if type(source) is not str or not source or source.splitlines() != [source]:
        raise HydraEvaluationError("evaluation theorem must be one complete source line")
    try:
        formula, names = parse_formula_with_names(source)
    except (ParseError, RecursionError, TypeError, ValueError) as error:
        raise HydraEvaluationError(f"evaluation theorem is not a PA formula: {error}") from None
    if names:
        raise HydraEvaluationError("evaluation theorem must be closed")
    return pretty_formula(formula, list(names))


def _formula_signature(source: str) -> tuple[int, int, int, bool]:
    """A sound cheap negative filter, including the expansion of ``<=``.

    Every current historical heldout is a single quantified equation. A
    surface ``a <= b`` expands to one existential, one addition and one
    equation; counting that added ``+`` avoids dropping a genuinely equivalent
    alias. Binder spellings, Unicode operators and parentheses are irrelevant.
    Only surviving candidates undergo exact kernel-parser canonicalization.
    """

    relations = _RELATION.findall(source)
    return (
        len(relations),
        len(_MULTIPLICATION.findall(source)),
        len(_ADDITION.findall(source))
        + sum(relation in {"<=", "≤"} for relation in relations),
        _CONNECTIVE.search(source) is not None,
    )


def _limits_record(limits: SearchLimits) -> dict[str, int]:
    if type(limits) is not SearchLimits:
        raise TypeError("matched evaluation requires exact SearchLimits")
    bounds = {
        "max_depth": MAX_SEARCH_DEPTH,
        "beam_width": MAX_BEAM_WIDTH,
        "candidates_per_state": MAX_CANDIDATES_PER_STATE,
        "max_model_calls": MAX_MODEL_CALLS_PER_GOAL,
        "max_states": MAX_SEARCH_STATES,
    }
    record = {name: getattr(limits, name) for name in bounds}
    for field, maximum in bounds.items():
        if type(record[field]) is not int or not 1 <= record[field] <= maximum:
            raise HydraEvaluationError(
                f"matched evaluation {field} must lie between 1 and {maximum}"
            )
    return record


def _model_record(value: object) -> dict[str, str]:
    if type(value) is not dict:
        raise HydraEvaluationError("post-training manifest does not pin a base model")
    model_id = value.get("model_id")
    revision = value.get("revision")
    if (
        model_id != EXPECTED_BASE_MODEL_ID
        or type(revision) is not str
        or _REVISION.fullmatch(revision) is None
        or revision != EXPECTED_BASE_MODEL_REVISION
    ):
        raise HydraEvaluationError("matched lanes must use the identical pinned Qwen base revision")
    return {"model_id": model_id, "revision": revision}


def _load_preparation(
    directory: Path,
) -> tuple[Path, dict[str, object], str, dict[str, tuple[dict[str, object], ...]]]:
    if not isinstance(directory, Path):
        raise TypeError("preparation directory must be a pathlib.Path")
    root = directory.expanduser().absolute()
    if root.is_symlink() or not root.is_dir():
        raise HydraEvaluationError("post-training preparation must be a real dedicated directory")
    raw = _read_regular(
        root / "manifest.json",
        maximum=MAX_MANIFEST_BYTES,
        description="post-training preparation manifest",
    )
    manifest = _json_object(raw, description="post-training preparation manifest")
    if manifest.get("schema") != PREPARATION_SCHEMA:
        raise HydraEvaluationError("post-training preparation manifest has an unsupported schema")
    files = manifest.get("files")
    if type(files) is not dict or set(files) != set(PREPARATION_FILENAMES):
        raise HydraEvaluationError("post-training preparation does not declare its exact file inventory")
    rows: dict[str, tuple[dict[str, object], ...]] = {}
    total_bytes = 0
    for filename in PREPARATION_FILENAMES:
        descriptor = files.get(filename)
        if type(descriptor) is not dict:
            raise HydraEvaluationError(f"post-training artifact {filename!r} has no exact identity")
        data = _read_regular(
            root / filename,
            maximum=MAX_DATASET_BYTES,
            description=f"post-training artifact {filename!r}",
        )
        total_bytes += len(data)
        if total_bytes > MAX_TOTAL_DATASET_BYTES:
            raise HydraEvaluationError("post-training artifact inventory exceeds its whole-run byte limit")
        if (
            type(descriptor.get("bytes")) is not int
            or descriptor.get("bytes") != len(data)
            or _sha256(descriptor.get("sha256"), field=f"{filename} digest")
            != hashlib.sha256(data).hexdigest()
        ):
            raise HydraEvaluationError(
                f"post-training artifact {filename!r} changed from its exact prepared bytes"
            )
        if filename.endswith(".jsonl"):
            records = _jsonl(data, filename=filename)
            if type(descriptor.get("rows")) is not int or descriptor.get("rows") != len(records):
                raise HydraEvaluationError(f"post-training artifact {filename!r} changed its row count")
            rows[filename] = records
    return root, manifest, hashlib.sha256(raw).hexdigest(), rows


def _heldout_goals(epoch: HydraEpoch) -> tuple[dict[str, object], ...]:
    canonical = canonical_held_out_formulas(PEANO_PROMPT_V3)
    expected = {
        _formula_signature(source)
        for _, source in MODEL_V3_HELD_OUT_POLICY_GOALS
    }
    aliases: dict[str, list[str]] = {formula: [] for formula in canonical}
    for theorem in epoch.theorems:
        if _formula_signature(theorem.statement) not in expected:
            continue
        formula = _canonical_formula(theorem.statement)
        if formula in aliases:
            aliases[formula].append(theorem.name)
    return tuple(
        {
            "name": name,
            "source": source,
            "statement": formula,
            "statement_sha256": hashlib.sha256(formula.encode("utf-8")).hexdigest(),
            "frozen_catalog_aliases": aliases[formula],
        }
        for (name, source), formula in zip(
            MODEL_V3_HELD_OUT_POLICY_GOALS,
            canonical,
            strict=True,
        )
    )


def _reject_secret_payload(value: object, *, location: str) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if key in _QUARANTINE_FORBIDDEN_FIELDS:
                raise HydraEvaluationError(
                    f"{location} exposed held-out proof or training payload {key!r}"
                )
            _reject_secret_payload(item, location=f"{location}.{key}")
    elif type(value) is list:
        for index, item in enumerate(value):
            _reject_secret_payload(item, location=f"{location}[{index}]")


@lru_cache(maxsize=16_384)
def _canonical_goal_target(rendered: str) -> str | None:
    if type(rendered) is not str:
        raise HydraEvaluationError("checked transition goal must be canonical text")
    _, marker, source = rendered.rpartition("⊢")
    source = source.strip()
    if not marker or not source:
        raise HydraEvaluationError("checked transition goal has no canonical turnstile")
    if "?" in source:
        return None
    try:
        formula, names = parse_formula_with_names(source)
    except (ParseError, RecursionError, TypeError, ValueError) as error:
        raise HydraEvaluationError(f"checked transition goal target is malformed: {error}") from None
    if names:
        return None
    return pretty_formula(formula, list(names))


def _validated_example(
    row: dict[str, object],
    *,
    epoch: HydraEpoch,
    split: str,
    forbidden_formulas: frozenset[str],
    lineages: dict[str, str],
) -> tuple[str, str]:
    if (
        row.get("schema") != EXAMPLE_SCHEMA
        or row.get("epoch_sha256") != epoch.epoch_sha256
        or row.get("edition_identity_sha256") != epoch.edition_identity_sha256
        or row.get("split") != split
        or row.get("kernel_checked") is not True
    ):
        raise HydraEvaluationError(f"{split} example lost its exact checked epoch or split authority")
    transition = row.get("transition")
    if type(transition) is not dict:
        raise HydraEvaluationError(f"{split} example does not contain its exact checked transition")
    if _sha256(
        row.get("source_transition_sha256"),
        field=f"{split} source transition digest",
    ) != _digest(transition):
        raise HydraEvaluationError(f"{split} example changed its independently checked source transition")
    fields = (
        "epoch_sha256",
        "theorem_name",
        "lineage_sha256",
        "state_sha256",
        "action",
        "prompt",
        "completion",
        "environment_sha256",
        "kernel_checked",
    )
    if any(row.get(field) != transition.get(field) for field in fields):
        raise HydraEvaluationError(f"{split} example differs from its exact checked transition fields")
    if row.get("source_split") != transition.get("split"):
        raise HydraEvaluationError(f"{split} example changed its original frozen source split")
    theorem = _canonical_formula(transition.get("theorem"))
    digest = hashlib.sha256(theorem.encode("utf-8")).hexdigest()
    if row.get("theorem_statement_sha256") != digest:
        raise HydraEvaluationError(f"{split} example changed its canonical theorem identity")
    if theorem in forbidden_formulas:
        raise HydraEvaluationError(f"{split} examples contain a historical held-out theorem alias")
    name = row.get("theorem_name")
    if type(name) is not str or not name:
        raise HydraEvaluationError(f"{split} example has no exact theorem name")
    enrolled = epoch.theorem(name)
    if enrolled is not None:
        if _canonical_formula(enrolled.statement) != theorem:
            raise HydraEvaluationError(f"{split} example changed its enrolled theorem statement")
        if row.get("lineage_sha256") != lineages[name]:
            raise HydraEvaluationError(f"{split} example changed its full frozen theorem-DAG component")
    lineage = _sha256(row.get("lineage_sha256"), field=f"{split} theorem lineage")
    parsed = parse_prompt(row.get("prompt"))
    if (
        parsed.surface != epoch.surface_label
        or parsed.environment_sha256 != row.get("environment_sha256")
        or tuple(transition.get("goals_before", ())) != parsed.goals
    ):
        raise HydraEvaluationError(f"{split} example changed its exact Alpha prompt authority")
    ProofExample(
        example_id=f"hydra-evaluation:{name}:{row.get('state_sha256')}",
        prompt=row["prompt"],
        completion=row["completion"],
        environment_sha256=row["environment_sha256"],
    )
    for field in ("goals_before", "goals_after"):
        goals = transition.get(field)
        if type(goals) is not list:
            raise HydraEvaluationError(f"{split} checked transition lacks canonical {field}")
        if any(_canonical_goal_target(item) in forbidden_formulas for item in goals):
            raise HydraEvaluationError(
                f"{split} examples expose a historical held-out formula as a proof goal"
            )
    return name, lineage


def _verify_holdout(
    manifest: dict[str, object],
    rows: dict[str, tuple[dict[str, object], ...]],
    *,
    epoch: HydraEpoch,
    goals: tuple[dict[str, object], ...],
) -> dict[str, object]:
    contract = manifest.get("held_out")
    if type(contract) is not dict:
        raise HydraEvaluationError("post-training preparation has no historical held-out contract")
    names = [goal["name"] for goal in goals]
    digests = [goal["statement_sha256"] for goal in goals]
    if (
        contract.get("historical_v3_contract_sha256")
        != held_out_contract_sha256(PEANO_PROMPT_V3)
        or contract.get("excluded_goal_names") != names
        or contract.get("excluded_goal_statement_sha256s") != digests
        or contract.get("training_contamination_count") != 0
        or contract.get("development_contamination_count") != 0
    ):
        raise HydraEvaluationError("post-training preparation changed its exact historical held-out contract")
    formulas = frozenset(goal["statement"] for goal in goals)
    goal_by_digest = {goal["statement_sha256"]: goal["name"] for goal in goals}
    component_lineages = _lineage_index(epoch)
    catalog_alias_lineages = {
        component_lineages[name]
        for goal in goals
        for name in goal["frozen_catalog_aliases"]
    }
    declared_quarantine = contract.get("quarantined_lineages")
    if (
        type(declared_quarantine) is not list
        or any(_SHA256.fullmatch(item) is None for item in declared_quarantine if type(item) is str)
        or any(type(item) is not str for item in declared_quarantine)
        or declared_quarantine != sorted(set(declared_quarantine))
    ):
        raise HydraEvaluationError("post-training quarantine must contain sorted unique lineage digests")
    quarantined_lineages = set(declared_quarantine)
    if not catalog_alias_lineages <= quarantined_lineages:
        raise HydraEvaluationError("a frozen theorem-DAG heldout-alias component escaped quarantine")
    quarantine_records = rows["quarantine.jsonl"]
    quarantine_rows = 0
    actual_quarantined: set[str] = set()
    matched_source: set[str] = set()
    for index, record in enumerate(quarantine_records, 1):
        _reject_secret_payload(record, location=f"quarantine.jsonl[{index}]")
        lineage = _sha256(record.get("lineage_sha256"), field="quarantined theorem lineage")
        count = record.get("rows")
        matched = record.get("matched_goal_names")
        reasons = record.get("reasons")
        theorem_name = record.get("theorem_name")
        statement = _sha256(
            record.get("theorem_statement_sha256"),
            field="quarantined theorem statement",
        )
        if (
            record.get("schema") != QUARANTINE_SCHEMA
            or record.get("epoch_sha256") != epoch.epoch_sha256
            or type(theorem_name) is not str
            or not theorem_name
            or type(count) is not int
            or count < 1
            or type(matched) is not list
            or not matched
            or not set(matched) <= set(names)
            or type(reasons) is not list
            or not reasons
        ):
            raise HydraEvaluationError("held-out quarantine row lost its exact aggregate identity")
        direct = goal_by_digest.get(statement)
        if direct is not None and direct not in matched:
            raise HydraEvaluationError("quarantined theorem hid its canonical held-out formula alias")
        actual_quarantined.add(lineage)
        matched_source.add(theorem_name)
        quarantine_rows += count
    if actual_quarantined != quarantined_lineages:
        raise HydraEvaluationError("held-out quarantine does not cover its exact complete lineage set")
    if contract.get("quarantine_rows") != quarantine_rows:
        raise HydraEvaluationError("held-out quarantine changed its aggregate source-row accounting")
    for index, record in enumerate(rows["discovery.jsonl"], 1):
        _reject_secret_payload(record, location=f"discovery.jsonl[{index}]")

    split_records: dict[str, dict[str, object]] = {}
    for split in ("train", "dev"):
        split_rows = rows[f"{split}.jsonl"]
        theorem_names: set[str] = set()
        split_lineages: set[str] = set()
        for record in split_rows:
            name, lineage = _validated_example(
                record,
                epoch=epoch,
                split=split,
                forbidden_formulas=formulas,
                lineages=component_lineages,
            )
            if lineage in quarantined_lineages:
                raise HydraEvaluationError(
                    f"{split} examples contain a quarantined historical held-out lineage"
                )
            theorem_names.add(name)
            split_lineages.add(lineage)
        split_records[split] = {
            "rows": len(split_rows),
            "lineages": sorted(split_lineages),
            "theorems": sorted(theorem_names),
        }
        declared = manifest.get("splits")
        if type(declared) is not dict or declared.get(split) != split_records[split]:
            raise HydraEvaluationError(f"prepared {split} split differs from its exact checked inventory")
        contract_field = "training_lineages" if split == "train" else "development_lineages"
        if contract.get(contract_field) != sorted(split_lineages):
            raise HydraEvaluationError(f"held-out contract changed its exact {split} lineage inventory")
    if set(split_records["train"]["lineages"]) & set(split_records["dev"]["lineages"]):
        raise HydraEvaluationError("one whole theorem-DAG lineage leaked across train and development")
    for index, preference in enumerate(rows["preferences.jsonl"], 1):
        lineage = _sha256(preference.get("lineage_sha256"), field="preference theorem lineage")
        if (
            preference.get("epoch_sha256") != epoch.epoch_sha256
            or lineage in quarantined_lineages
            or lineage not in split_records["train"]["lineages"]
        ):
            raise HydraEvaluationError(
                f"preferences.jsonl row {index} escaped its checked unquarantined training lineage"
            )
    return {
        "historical_v3_contract_sha256": held_out_contract_sha256(PEANO_PROMPT_V3),
        "goal_count": len(goals),
        "catalog_alias_count": sum(len(goal["frozen_catalog_aliases"]) for goal in goals),
        "catalog_alias_lineages": sorted(catalog_alias_lineages),
        "matched_source_theorems": sorted(matched_source),
        "quarantined_lineages": sorted(quarantined_lineages),
        "quarantine_rows": quarantine_rows,
        "training_contamination_count": 0,
        "development_contamination_count": 0,
        "split_lineages": {
            "train": split_records["train"]["lineages"],
            "dev": split_records["dev"]["lineages"],
        },
    }


@dataclass(frozen=True, slots=True)
class MatchedEvaluationPlan:
    """One immutable comparison authority; no loaded model is retained."""

    epoch: HydraEpoch
    preparation_directory: Path
    preparation_manifest_sha256: str
    model: dict[str, str]
    goals: tuple[dict[str, object], ...]
    held_out: dict[str, object]
    limits: SearchLimits
    seed: int
    max_new_tokens: int
    trained_adapter: dict[str, object] | None

    @property
    def capabilities(self) -> object:
        return self.epoch.alpha_capabilities(
            allowed_commands=MODEL_V1_COMMANDS,
            allowed_theorems=frozenset(),
        )

    @property
    def environment(self) -> dict[str, object]:
        return policy_environment(self.capabilities)

    @property
    def goal_set_sha256(self) -> str:
        return _digest(self.goals)

    @property
    def matched_budget(self) -> dict[str, object]:
        return {
            **_limits_record(self.limits),
            "goal_count": len(self.goals),
            "max_model_calls_per_lane": len(self.goals) * self.limits.max_model_calls,
            "max_new_tokens": self.max_new_tokens,
            "seed": self.seed,
            "sampling": "deterministic batched candidate beam search",
        }

    def to_dict(self) -> dict[str, object]:
        theorem_authority = {
            "allowed_theorems": [],
            "allowed_theorem_count": 0,
            "allowed_theorems_sha256": _digest([]),
            "held_out_alias_imports_allowed": False,
            "descendant_imports_allowed": False,
            "promoted_bundle_imports_allowed": False,
        }
        shared = {
            "epoch_sha256": self.epoch.epoch_sha256,
            "surface_label": self.epoch.surface_label,
            "environment_sha256": self.environment["environment_sha256"],
            "goal_set_sha256": self.goal_set_sha256,
            "model": dict(self.model),
            "matched_budget": self.matched_budget,
            "theorem_authority": theorem_authority,
        }
        unavailable = self.trained_adapter is None
        lanes = {
            "pretrained": {
                **shared,
                "role": "pinned_pretrained_base",
                "adapter_attached": False,
                "status": "not_executed",
            },
            "trained": {
                **shared,
                "role": "epoch_compatible_posttrained_lora",
                "adapter_attached": True,
                "status": "unavailable" if unavailable else "not_executed",
                "adapter": None if unavailable else dict(self.trained_adapter),
            },
        }
        record: dict[str, object] = {
            "schema": EVALUATION_SCHEMA,
            "development_only": True,
            "research_claim_eligible": False,
            "sealed_benchmark": False,
            "version": self.epoch.version,
            "epoch_sha256": self.epoch.epoch_sha256,
            "edition_identity_sha256": self.epoch.edition_identity_sha256,
            "theorem_dag_sha256": self.epoch.theorem_dag_sha256,
            "reviewed_definition_dag_sha256": self.epoch.reviewed_definition_dag_sha256,
            "preparation_manifest_sha256": self.preparation_manifest_sha256,
            "model": dict(self.model),
            "environment": self.environment,
            "theorem_authority": theorem_authority,
            "held_out": dict(self.held_out),
            "goals": [dict(goal) for goal in self.goals],
            "goal_set_sha256": self.goal_set_sha256,
            "matched_budget": self.matched_budget,
            "lanes": lanes,
            "comparison": {
                "status": "unmeasured",
                "reason": (
                    "no completed epoch-compatible trained Alpha adapter is available"
                    if unavailable
                    else "matched pretrained and trained model inference has not been executed"
                ),
                "model_metrics": None,
                "research_claim_eligible": False,
            },
        }
        record["plan_sha256"] = _digest(record)
        return record


def _default_adapter_manifest(epoch: HydraEpoch) -> Path:
    return (
        REPOSITORY_ROOT
        / "results"
        / "peano-hydra"
        / f"qwen3-1.7b-alpha-{epoch.version}-{epoch.epoch_sha256[:12]}"
        / "manifest.json"
    )


def _adapter_path(value: Path) -> Path:
    return value / "manifest.json" if value.is_dir() else value


def _validated_execution_provenance(record: dict[str, object]) -> dict[str, object]:
    """Validate saved GPU/source/lock evidence without probing this machine."""

    runtime = _validate_runtime_identity(record.get("runtime"), "Alpha training runtime")
    deployment = record.get("deployment")
    job = record.get("job")
    lock = record.get("requirements_verification")
    if (
        type(deployment) is not dict
        or deployment.get("mode") not in {"local", "slurm"}
        or type(job) is not dict
        or job.get("deployment") != deployment
        or type(lock) is not dict
        or lock.get("schema") != RUNTIME_LOCK_SCHEMA
        or lock.get("requirements") != runtime.get("requirements")
    ):
        raise HydraEvaluationError("trained Alpha runtime/source/job provenance is incomplete")
    requirements = lock.get("requirements")
    if (
        type(requirements) is not dict
        or type(requirements.get("path")) is not str
        or re.fullmatch(
            r"training/peano_policy/requirements-[A-Za-z0-9._-]{1,80}\.lock",
            requirements["path"],
        ) is None
    ):
        raise HydraEvaluationError("trained Alpha requirements identity is malformed")
    lock_bytes = _read_regular(
        REPOSITORY_ROOT / requirements["path"],
        maximum=64 * 1_024,
        description="recorded Alpha training requirements lock",
    )
    if requirements.get("sha256") != hashlib.sha256(lock_bytes).hexdigest():
        raise HydraEvaluationError("trained Alpha requirements lock differs from recorded source")
    packages = runtime["packages"]
    if any(
        type(name) is not str or not name or (version is not None and (type(version) is not str or not version))
        for name, version in packages.items()
    ):
        raise HydraEvaluationError("trained Alpha installed package inventory is malformed")
    normalized = {re.sub(r"[-_.]+", "-", name).lower(): version for name, version in packages.items()}
    if len(normalized) != len(packages) or any(
        type(normalized.get(name)) is not str for name in ("torch", "transformers", "peft")
    ):
        raise HydraEvaluationError("trained Alpha runtime lost its actual model packages")
    accelerator = runtime.get("accelerator")
    if (
        type(accelerator) is not dict
        or accelerator.get("cuda_available") is not True
        or accelerator.get("bf16_supported") is not True
        or type(accelerator.get("torch")) is not str
        or accelerator["torch"].split("+", 1)[0] != normalized["torch"].split("+", 1)[0]
    ):
        raise HydraEvaluationError("trained Alpha runtime lacks its recorded BF16 CUDA identity")
    if lock.get("status") == "verified":
        from packaging.requirements import Requirement

        marker_environment = {
            "python_version": ".".join(runtime["python"].split(".")[:2]),
            "python_full_version": runtime["python"],
            "platform_python_implementation": runtime["implementation"],
            "implementation_name": runtime["implementation"].lower(),
            "platform_machine": runtime["machine"],
        }
        expected_packages: dict[str, str] = {}
        for line in lock_bytes.decode("utf-8").replace("\\\n", " ").splitlines():
            line = line.partition("#")[0].strip()
            if not line:
                continue
            line = re.sub(r"\s+--hash=sha256:[0-9a-f]{64}(?=\s|$)", "", line)
            requirement = Requirement(line)
            if requirement.marker is not None and not requirement.marker.evaluate(marker_environment):
                continue
            specifiers = tuple(requirement.specifier)
            if (
                requirement.url is not None
                or requirement.extras
                or len(specifiers) != 1
                or specifiers[0].operator != "=="
                or "*" in specifiers[0].version
            ):
                raise HydraEvaluationError("recorded Alpha requirements are not exact version pins")
            name = re.sub(r"[-_.]+", "-", requirement.name).lower()
            if name in expected_packages:
                raise HydraEvaluationError("recorded Alpha requirements repeat an active package")
            expected_packages[name] = specifiers[0].version
        checked = lock.get("packages")
        if (
            type(checked) is not dict
            or not checked
            or checked != expected_packages
            or lock.get("packages_sha256") != _digest(checked)
            or any(
                type(name) is not str
                or not name
                or type(version) is not str
                or not version
                or normalized.get(name) != version
                for name, version in checked.items()
            )
        ):
            raise HydraEvaluationError("trained Alpha verified lock disagrees with installed packages")
    elif lock.get("status") != "not-required-local" or deployment["mode"] != "local":
        raise HydraEvaluationError("scheduled Alpha training lacks verified package-lock evidence")
    if deployment["mode"] == "local":
        if job.get("scheduler") != "none":
            raise HydraEvaluationError("local Alpha training changed its scheduler identity")
    else:
        source = deployment.get("source_sync")
        script = deployment.get("job_script")
        submission = job.get("submission")
        ledger = job.get("ledger")
        if (
            job.get("scheduler") != "slurm"
            or type(job.get("job_id")) is not str
            or re.fullmatch(r"[0-9]+", job["job_id"]) is None
            or type(source) is not dict
            or source.get("status") != "synced"
            or source.get("path") != ".peano-source-provenance.tsv"
            or source.get("git_dirty") is not False
            or type(source.get("git_commit")) is not str
            or _REVISION.fullmatch(source["git_commit"]) is None
            or type(source.get("synced_at")) is not str
            or not source["synced_at"]
            or type(script) is not dict
            or script.get("status") != "declared"
            or type(submission) is not dict
            or submission.get("job_id") != job["job_id"]
            or submission.get("git_commit") != source["git_commit"]
            or submission.get("git_dirty") != "false"
            or submission.get("sync_timestamp") != source["synced_at"]
            or submission.get("script") != script.get("path")
            or submission.get("script_sha256") != script.get("sha256")
            or type(ledger) is not dict
            or ledger.get("path") != "logs/submissions.tsv"
            or ledger.get("row_sha256") != _digest(submission)
        ):
            raise HydraEvaluationError("scheduled Alpha training lost its clean source/submission binding")
        _sha256(source.get("sha256"), field="Alpha source synchronization hash")
        _sha256(script.get("sha256"), field="Alpha training job script hash")
    return {name: record[name] for name in ("runtime", "deployment", "job", "requirements_verification")}


def _validated_training_evidence(
    record: dict[str, object],
    *,
    epoch: HydraEpoch,
    preparation_directory: Path,
    preparation_manifest: dict[str, object],
) -> dict[str, object]:
    """Check the Alpha executor's actual evidence, independently of model-v3.

    A matching pair of self-declared step counts does not establish that the
    prepared run finished. Derive its schedule from the exact prepared TOML
    and clean row inventory, then require every finite optimizer observation
    and the changed, finite adapter population emitted by the Alpha trainer.
    """

    try:
        config_raw, config = posttraining_config(epoch, output=preparation_directory)
        descriptor = preparation_manifest["files"]["config.toml"]
        if (
            descriptor.get("bytes") != len(config_raw)
            or descriptor.get("sha256") != hashlib.sha256(config_raw).hexdigest()
        ):
            raise HydraEvaluationError(
                "trained Alpha evidence changed its exact reviewed training configuration"
            )
        train_rows = preparation_manifest["splits"]["train"]["rows"]
        dev_rows = preparation_manifest["splits"]["dev"]["rows"]
        if (
            type(train_rows) is not int
            or train_rows < 1
            or type(dev_rows) is not int
            or dev_rows < 1
        ):
            raise HydraEvaluationError("trained Alpha evidence requires nonempty clean splits")
        batch_size = config.trainer.per_device_train_batch_size
        accumulation = config.trainer.gradient_accumulation_steps
        batches = (train_rows + batch_size - 1) // batch_size
        expected_steps = (batches + accumulation - 1) // accumulation
        if not 1 <= expected_steps <= MAX_OPTIMIZER_STEPS:
            raise HydraEvaluationError("trained Alpha evidence exceeds its optimizer-step bound")
        metrics = record.get("metrics")
        if type(metrics) is not dict or any(
            type(metrics.get(name)) is not int or metrics.get(name) != expected
            for name, expected in (
                ("expected_optimizer_steps", expected_steps),
                ("actual_optimizer_steps", expected_steps),
                ("training_rows", train_rows),
                ("development_rows", dev_rows),
            )
        ):
            raise HydraEvaluationError(
                "trained Alpha metrics differ from the exact prepared rows or optimizer schedule"
            )
        if record.get("objective") != completion_objective_record():
            raise HydraEvaluationError("trained Alpha evidence changed its completion-only objective")
        train_metrics = _finite_metrics(metrics.get("train"), "train_loss", "Alpha training metrics")
        dev_metrics = _finite_metrics(metrics.get("dev"), "eval_loss", "Alpha development metrics")
        runtime = _validate_runtime(record.get("trainer_runtime"))
        if runtime["configured_trainer_gradient_accumulation_steps"] != accumulation:
            raise HydraEvaluationError(
                "trained Alpha runtime changed its prepared gradient accumulation"
            )
        gradients = _validate_gradients(record.get("finite_gradient_audit"), expected_steps)
        update = _validate_adapter_update(record.get("adapter_update"), gradients=gradients)
        provenance = _validated_execution_provenance(record)
    except (KeyError, TypeError, TrainingEvidenceError, EvaluationReplayError) as error:
        raise HydraEvaluationError(f"trained Alpha completion evidence is invalid: {error}") from error
    return {
        "expected_optimizer_steps": expected_steps,
        "actual_optimizer_steps": expected_steps,
        "training_rows": train_rows,
        "development_rows": dev_rows,
        "objective_sha256": _digest(record["objective"]),
        "trainer_runtime_sha256": _digest(runtime),
        "finite_gradient_audit_sha256": _digest(gradients),
        "adapter_update_sha256": _digest(update),
        "execution_provenance_sha256": _digest(provenance),
        "train_metrics": train_metrics,
        "development_metrics": dev_metrics,
    }


def _validated_adapter(
    requested: Path | None,
    *,
    epoch: HydraEpoch,
    preparation_directory: Path,
    preparation_manifest: dict[str, object],
    preparation_manifest_sha256: str,
    model: dict[str, str],
) -> dict[str, object] | None:
    path = _default_adapter_manifest(epoch) if requested is None else _adapter_path(requested)
    if not path.exists():
        if requested is None:
            return None
        raise HydraEvaluationError("the requested trained Alpha adapter manifest is unavailable")
    raw = _read_regular(
        path,
        maximum=MAX_MANIFEST_BYTES,
        description="trained Hydra Alpha adapter manifest",
    )
    record = _json_object(raw, description="trained Hydra Alpha adapter manifest")
    preparation = record.get("preparation")
    if (
        record.get("schema") != ADAPTER_SCHEMA
        or record.get("version") != epoch.version
        or record.get("epoch_sha256") != epoch.epoch_sha256
        or record.get("edition_identity_sha256") != epoch.edition_identity_sha256
        or record.get("theorem_dag_sha256") != epoch.theorem_dag_sha256
        or record.get("reviewed_definition_dag_sha256")
        != epoch.reviewed_definition_dag_sha256
        or record.get("surface_label") != epoch.surface_label
        or record.get("preparation_manifest_sha256") != preparation_manifest_sha256
        or type(preparation) is not dict
        or preparation.get("manifest_sha256") != preparation_manifest_sha256
        or preparation.get("files") != preparation_manifest.get("files")
        or record.get("held_out") != preparation_manifest.get("held_out")
        or record.get("model_trained") is not True
        or record.get("research_claim_eligible") is not False
        or record.get("alpha_admitted") is not False
        or record.get("sealed_benchmark") is not False
        or _model_record(record.get("model")) != model
    ):
        raise HydraEvaluationError(
            "trained Alpha adapter differs from its exact frozen epoch, preparation, or base model"
        )
    evidence = _validated_training_evidence(
        record,
        epoch=epoch,
        preparation_directory=preparation_directory,
        preparation_manifest=preparation_manifest,
    )
    return {
        "manifest_path": str(path),
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "epoch_sha256": epoch.epoch_sha256,
        "preparation_manifest_sha256": preparation_manifest_sha256,
        "model": dict(model),
        "training_evidence": evidence,
    }


def build_matched_evaluation_plan(
    preparation_directory: Path,
    *,
    limits: SearchLimits = DEFAULT_LIMITS,
    seed: int = DEFAULT_SEED,
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
    trained_adapter: Path | None = None,
    repository_root: Path = REPOSITORY_ROOT,
) -> MatchedEvaluationPlan:
    """Validate one exact heldout-clean epoch without loading a model runtime."""

    _limits_record(limits)
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise HydraEvaluationError("evaluation seed must be an integer in [0, 2^63)")
    if type(max_new_tokens) is not int or not 1 <= max_new_tokens <= MAX_NEW_TOKENS:
        raise HydraEvaluationError(
            f"matched evaluation max_new_tokens must lie between 1 and {MAX_NEW_TOKENS}"
        )
    if trained_adapter is not None and not isinstance(trained_adapter, Path):
        raise TypeError("trained adapter must be a pathlib.Path")
    directory, manifest, manifest_sha256, records = _load_preparation(preparation_directory)
    epoch = freeze_epoch(repository_root)
    if (
        manifest.get("epoch_sha256") != epoch.epoch_sha256
        or manifest.get("edition_identity_sha256") != epoch.edition_identity_sha256
        or manifest.get("theorem_dag_sha256") != epoch.theorem_dag_sha256
        or manifest.get("reviewed_definition_dag_sha256")
        != epoch.reviewed_definition_dag_sha256
        or manifest.get("surface_label") != epoch.surface_label
        or manifest.get("version") != epoch.version
        or manifest.get("research_claim_eligible") is not False
        or manifest.get("alpha_admitted") is not False
        or manifest.get("sealed_benchmark") is not False
        or manifest.get("model_trained") is not False
    ):
        raise HydraEvaluationError("post-training preparation escaped the exact frozen Alpha epoch")
    model = _model_record(manifest.get("model"))
    goals = _heldout_goals(epoch)
    if not 1 <= len(goals) <= MAX_EVALUATION_GOALS:
        raise HydraEvaluationError("historical held-out goal inventory exceeds its reviewed bound")
    if len(goals) * limits.max_model_calls > MAX_MODEL_CALLS_PER_LANE:
        raise HydraEvaluationError("matched model lane exceeds its whole-run physical-call reservation")
    held_out = _verify_holdout(manifest, records, epoch=epoch, goals=goals)
    adapter = _validated_adapter(
        trained_adapter,
        epoch=epoch,
        preparation_directory=directory,
        preparation_manifest=manifest,
        preparation_manifest_sha256=manifest_sha256,
        model=model,
    )
    return MatchedEvaluationPlan(
        epoch,
        directory,
        manifest_sha256,
        model,
        goals,
        held_out,
        limits,
        seed,
        max_new_tokens,
        adapter,
    )


def run_symbolic_controls(plan: MatchedEvaluationPlan) -> dict[str, object]:
    """Run checked fixed-candidate controls, never a model capability proxy."""

    if type(plan) is not MatchedEvaluationPlan:
        raise TypeError("symbolic controls require one exact matched evaluation plan")
    environment = plan.environment
    results: list[dict[str, object]] = []
    for goal in plan.goals:
        fixed = FixedCandidatePolicy(
            _SAFE_SYMBOLIC_CANDIDATES,
            name="hydra-matched-fixed-symbolic-v1",
            policy_environment=environment,
            provider_identity={
                "kind": "fixed-human-selected-symbolic-control-v1",
                "model_generated": False,
                "research_claim_eligible": False,
            },
        )
        portfolio = HydraCandidatePolicy(
            (
                PolicyHead(
                    "matched-fixed-symbolic",
                    "symbolic",
                    plan.limits.candidates_per_state,
                    fixed,
                ),
            ),
            name=f"hydra-symbolic-{goal['name']}",
        )
        result = run_hydra(
            goal["source"],
            portfolio,
            capabilities=plan.capabilities,
            limits=plan.limits,
            label=f"hydra-symbolic-control-{goal['name']}",
        )
        if result.proved and (
            result.replay is None
            or result.replay.kernel_checked is not True
            or result.replay.theorem != goal["statement"]
        ):
            raise HydraEvaluationError("symbolic control lost its independent original-goal replay")
        results.append(
            {
                "goal": goal["name"],
                "status": result.status,
                "kernel_checked": bool(result.replay and result.replay.kernel_checked),
                "tactic_decisions": len(result.commands),
                "proof_nodes": None if result.replay is None else result.replay.proof_nodes,
                "model_calls": 0,
                "symbolic_state_expansions": result.search.model_calls,
            }
        )
    return {
        "status": "executed",
        "provider": "fixed-human-selected-symbolic-control-v1",
        "model_generated": False,
        "research_claim_eligible": False,
        "goals": results,
        "kernel_checked_proofs": sum(row["kernel_checked"] for row in results),
    }


def _verify_trained_artifacts(
    plan: MatchedEvaluationPlan,
) -> tuple[Path, Path, dict[str, object]]:
    if plan.trained_adapter is None:
        raise HydraEvaluationError("actual matched inference requires a completed trained Alpha adapter")
    manifest_path = Path(plan.trained_adapter["manifest_path"])
    raw = _read_regular(
        manifest_path,
        maximum=MAX_MANIFEST_BYTES,
        description="trained Hydra Alpha adapter manifest",
    )
    if hashlib.sha256(raw).hexdigest() != plan.trained_adapter["manifest_sha256"]:
        raise HydraEvaluationError("trained Alpha adapter manifest changed after comparison planning")
    record = _json_object(raw, description="trained Hydra Alpha adapter manifest")
    root = manifest_path.parent
    adapter_identity = record.get("adapter")
    tokenizer_identity = record.get("tokenizer")
    if type(adapter_identity) is not dict or type(tokenizer_identity) is not dict:
        raise HydraEvaluationError(
            "trained Alpha adapter must bind complete closed adapter and tokenizer artifact trees"
        )
    try:
        require_safetensors_adapter(adapter_identity)
        adapter_directory = verify_artifact_directory(root, adapter_identity, "adapter")
        tokenizer_directory = verify_artifact_directory(root, tokenizer_identity, "tokenizer")
    except (OSError, TypeError, ValueError) as error:
        raise HydraEvaluationError(
            f"trained Alpha adapter or tokenizer differs from its exact saved bytes: {error}"
        ) from error
    if "adapter/adapter_config.json" not in adapter_identity.get("files", {}):
        raise HydraEvaluationError("trained Alpha adapter did not bind its exact PEFT configuration")
    for filename in ("adapter_config.json", "adapter_model.safetensors"):
        path = adapter_directory / filename
        if path.stat().st_size > MAX_ADAPTER_FILE_BYTES:
            raise HydraEvaluationError("trained Alpha adapter exceeds its explicit byte boundary")
    return (
        adapter_directory,
        tokenizer_directory,
        {
            "adapter": adapter_identity,
            "tokenizer": tokenizer_identity,
        },
    )


def _model_runtime() -> tuple[Any, Any, Any]:
    try:
        import torch
        import transformers
        import peft
    except ImportError as error:
        raise HydraEvaluationError(
            "actual matched inference requires the prepared CUDA torch/transformers/peft runtime"
        ) from error
    if not torch.cuda.is_available():
        raise HydraEvaluationError("actual matched inference requires one available CUDA GPU")
    if torch.cuda.device_count() != 1:
        raise HydraEvaluationError("actual matched inference requires exactly one visible CUDA GPU")
    return torch, transformers, peft


def _reset_seed(torch: Any, transformers: Any, seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    transformers.set_seed(seed)


def _release_gpu(torch: Any) -> None:
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.synchronize()


def _load_base_model(torch: Any, transformers: Any, model: dict[str, str]) -> Any:
    result = transformers.AutoModelForCausalLM.from_pretrained(
        model["model_id"],
        revision=model["revision"],
        torch_dtype=torch.bfloat16,
        attn_implementation="sdpa",
        trust_remote_code=False,
        use_safetensors=True,
        local_files_only=True,
    )
    loaded_revision = getattr(getattr(result, "config", None), "_commit_hash", None)
    if loaded_revision not in {None, model["revision"]}:
        raise HydraEvaluationError("loaded Qwen base resolved to a different pinned revision")
    return result


def _run_model_lane(
    plan: MatchedEvaluationPlan,
    *,
    model: Any,
    tokenizer: Any,
    lane: str,
    provider: dict[str, object],
) -> dict[str, object]:
    from training.peano_policy.generate import (
        PeanoPolicyAdapter,
        PeanoPolicyCandidateAdapter,
        PeanoPretrainedBasePolicy,
    )

    identity = CapabilityIdentity.from_record(plan.environment["capabilities"])
    environment = prompt_environment(False, identity)
    if environment.sha256 != plan.environment["environment_sha256"]:
        raise HydraEvaluationError("matched model lane changed its exact frozen Alpha prompt authority")
    results: list[dict[str, object]] = []
    total_calls = 0
    evidence_bytes = 0
    for goal in plan.goals:
        goal_seed = int.from_bytes(
            hashlib.sha256(_canonical([plan.seed, goal["name"]])).digest()[:8],
            "big",
        ) & (2**63 - 1)
        policy_type = PeanoPretrainedBasePolicy if lane == "pretrained" else PeanoPolicyAdapter
        base_policy = policy_type(
            model=model,
            tokenizer=tokenizer,
            environment=environment,
            name=f"hydra-alpha-{lane}-{goal['name']}",
            max_new_tokens=plan.max_new_tokens,
            do_sample=False,
            temperature=1.0,
            top_p=1.0,
            provenance=provider,
        )
        candidate = PeanoPolicyCandidateAdapter(
            base_policy,
            seed=goal_seed,
            name=f"hydra-alpha-candidate-{lane}-{goal['name']}",
        )
        portfolio = HydraCandidatePolicy(
            (
                PolicyHead(
                    f"matched-{lane}-model",
                    "control",
                    plan.limits.candidates_per_state,
                    candidate,
                ),
            ),
            name=f"hydra-alpha-portfolio-{lane}-{goal['name']}",
        )
        result = run_hydra(
            goal["source"],
            portfolio,
            capabilities=plan.capabilities,
            limits=plan.limits,
            label=f"hydra-alpha-eval-{lane}-{goal['name']}",
        )
        if result.degraded:
            raise HydraEvaluationError(
                f"matched {lane} provider degraded instead of executing its exact model lane"
            )
        provenance = candidate.generation_provenance
        actual_calls = provenance["model_generate_calls"]
        if (
            type(actual_calls) is not int
            or actual_calls != result.search.model_calls
            or actual_calls > plan.limits.max_model_calls
            or provenance["candidate_sequences_requested"]
            != actual_calls * plan.limits.candidates_per_state
        ):
            raise HydraEvaluationError(
                f"matched {lane} lane changed its physical model-call or candidate reservation"
            )
        if result.proved and (
            result.replay is None
            or result.replay.kernel_checked is not True
            or result.replay.theorem != goal["statement"]
        ):
            raise HydraEvaluationError(
                f"matched {lane} lane lost its independent original-goal kernel replay"
            )
        total_calls += actual_calls
        evidence = result.to_dict(include_trace=True)
        encoded_evidence = _canonical(evidence)
        evidence_bytes += len(encoded_evidence)
        if (
            len(encoded_evidence) > MAX_GOAL_EVIDENCE_BYTES
            or evidence_bytes > MAX_LANE_EVIDENCE_BYTES
        ):
            raise HydraEvaluationError(
                f"matched {lane} replay/proposal evidence exceeds its retained-byte bound"
            )
        results.append(
            {
                "goal": goal["name"],
                "status": result.status,
                "kernel_checked": bool(result.replay and result.replay.kernel_checked),
                "tactic_decisions": len(result.commands),
                "proof_nodes": None if result.replay is None else result.replay.proof_nodes,
                "commands_sha256": result.commands_sha256,
                "model_generate_calls": actual_calls,
                "generation": provenance,
                "policy_identity": result.policy_identity,
                "evidence": evidence,
                "evidence_sha256": hashlib.sha256(encoded_evidence).hexdigest(),
                "research_claim_eligible": False,
            }
        )
    if total_calls > MAX_MODEL_CALLS_PER_LANE:
        raise HydraEvaluationError(f"matched {lane} lane exceeded its whole-run CUDA-call bound")
    return {
        "status": "executed",
        "lane": lane,
        "model": dict(plan.model),
        "adapter_attached": lane == "trained",
        "epoch_sha256": plan.epoch.epoch_sha256,
        "environment_sha256": plan.environment["environment_sha256"],
        "goal_set_sha256": plan.goal_set_sha256,
        "matched_budget": plan.matched_budget,
        "provider": provider,
        "goals": results,
        "kernel_checked_proofs": sum(item["kernel_checked"] for item in results),
        "model_generate_calls": total_calls,
        "retained_evidence_bytes": evidence_bytes,
        "research_claim_eligible": False,
    }


def execute_model_comparison(plan: MatchedEvaluationPlan) -> dict[str, object]:
    """Execute genuine matched base/LoRA inference sequentially on one GPU."""

    if type(plan) is not MatchedEvaluationPlan:
        raise TypeError("matched model execution requires one exact validated plan")
    adapter_directory, tokenizer_directory, artifact_identity = _verify_trained_artifacts(plan)
    torch, transformers, peft = _model_runtime()
    _reset_seed(torch, transformers, plan.seed)
    tokenizer = transformers.AutoTokenizer.from_pretrained(
        str(tokenizer_directory),
        trust_remote_code=False,
        use_fast=True,
        local_files_only=True,
    )
    if tokenizer.pad_token_id is None:
        if tokenizer.eos_token_id is None:
            raise HydraEvaluationError("matched tokenizer has no reviewed EOS/padding identity")
        tokenizer.pad_token_id = tokenizer.eos_token_id
    runtime = {
        "torch_version": getattr(torch, "__version__", "unknown"),
        "transformers_version": getattr(transformers, "__version__", "unknown"),
        "peft_version": getattr(peft, "__version__", "unknown"),
        "visible_cuda_devices": 1,
        "cuda_device": torch.cuda.get_device_name(0),
        "dtype": "bfloat16",
        "attention": "sdpa",
        "local_files_only": True,
        "model_loading": "sequential-pretrained-unload-then-trained-lora",
    }
    results: dict[str, dict[str, object]] = {}
    for lane in ("pretrained", "trained"):
        _verify_trained_artifacts(plan)
        _reset_seed(torch, transformers, plan.seed)
        model = None
        try:
            model = _load_base_model(torch, transformers, plan.model)
            if lane == "trained":
                model = peft.PeftModel.from_pretrained(
                    model,
                    str(adapter_directory),
                    is_trainable=False,
                )
            model.to("cuda:0")
            model.eval()
            provider = {
                "kind": (
                    "pinned-pretrained-base-no-peft"
                    if lane == "pretrained"
                    else "epoch-compatible-pinned-alpha-lora"
                ),
                "adapter_attached": lane == "trained",
                "base_model": dict(plan.model),
                "trained_adapter_manifest_sha256": plan.trained_adapter["manifest_sha256"],
                "trained_adapter_artifacts": artifact_identity,
                "runtime": runtime,
                "research_claim_eligible": False,
            }
            results[lane] = _run_model_lane(
                plan,
                model=model,
                tokenizer=tokenizer,
                lane=lane,
                provider=provider,
            )
        finally:
            del model
            _release_gpu(torch)
    _verify_trained_artifacts(plan)
    pretrained = results["pretrained"]
    trained = results["trained"]
    paired_fields = ("model", "epoch_sha256", "environment_sha256", "goal_set_sha256", "matched_budget")
    if any(pretrained.get(field) != trained.get(field) for field in paired_fields):
        raise HydraEvaluationError("pretrained and trained lanes lost their exact matched authority")
    metrics = {
        "goal_count": len(plan.goals),
        "pretrained_kernel_checked_proofs": pretrained["kernel_checked_proofs"],
        "trained_kernel_checked_proofs": trained["kernel_checked_proofs"],
        "kernel_checked_proof_delta": (
            trained["kernel_checked_proofs"] - pretrained["kernel_checked_proofs"]
        ),
        "pretrained_model_generate_calls": pretrained["model_generate_calls"],
        "trained_model_generate_calls": trained["model_generate_calls"],
        "research_claim_eligible": False,
    }
    return {
        "status": "executed",
        "lanes": results,
        "model_metrics": metrics,
        "provider_runtime": runtime,
        "claim_boundary": (
            "actual matched product evaluation with independently checked proofs; "
            "not a sealed H0/H1 research claim"
        ),
        "research_claim_eligible": False,
    }


__all__ = [
    "ADAPTER_SCHEMA",
    "DEFAULT_LIMITS",
    "DEFAULT_MAX_NEW_TOKENS",
    "DEFAULT_SEED",
    "EVALUATION_SCHEMA",
    "HydraEvaluationError",
    "MatchedEvaluationPlan",
    "build_matched_evaluation_plan",
    "execute_model_comparison",
    "run_symbolic_controls",
]
