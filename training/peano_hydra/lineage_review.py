"""Fail-closed component allocation proposals, never an approved data split.

The frozen public DEV benchmark remains unchanged.  This planner adds the
catalog components that do not contain a DEV goal, retains every original
alias/descendant mask, and compares archived audit receipts with fresh bounded
audits of their original preparation bytes.  Component allocation is explicit:
no theorem, family, or seed can be split out of its component to improve a
holdout score.  All outputs still require later independent human review.

No entry point writes a dataset, loads a model, replays the training corpus,
supplies a human acknowledgment, or grants training/evaluation authority.
"""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from training.peano_hydra.benchmark import (
    AUDIT_SCHEMA,
    HydraBenchmarkError,
    audit_preparation,
    build_development_benchmark,
    validate_benchmark,
)
from training.peano_hydra.curriculum import _lineage_index
from training.peano_hydra.epoch import HydraEpoch
from training.peano_hydra.frontier import SOURCE_FILES
from training.peano_hydra.protocol import validate_statement


INVENTORY_SCHEMA = "peano-hydra-lineage-review-inventory-v1"
REVIEW_SCHEMA = "peano-hydra-lineage-review-proposal-v1"
MAX_THEOREMS = 4_096
MAX_AUDITS = 4
MAX_AUDIT_BYTES = 4 * 1_024 * 1_024
MAX_SUPPLEMENTAL_ROW_REFERENCES = 32_768
MAX_REVIEW_BYTES = 24 * 1_024 * 1_024
MAX_SOURCE_FILE_BYTES = 2 * 1_024 * 1_024
MAX_GIT_COMMAND_SECONDS = 2
ROOT = Path(__file__).resolve().parents[2]
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_SPLITS = frozenset({"train", "dev", "quarantine", "unassigned"})


class LineageReviewError(ValueError):
    """A proposed review lost its frozen identity or explicit allocation scope."""


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise LineageReviewError(f"review evidence is not strict JSON: {error}") from None


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _detach(value: object) -> Any:
    return json.loads(_canonical(value))


def _sha256(value: object, description: str) -> str:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        raise LineageReviewError(f"{description} must be one lowercase SHA-256 digest")
    return value


def _read_source(relative: str) -> bytes:
    path = ROOT / relative
    if path.is_symlink() or not path.is_file():
        raise LineageReviewError(f"source is not a regular non-symlink file: {relative}")
    if path.stat().st_size > MAX_SOURCE_FILE_BYTES:
        raise LineageReviewError(f"source exceeds its byte bound: {relative}")
    raw = path.read_bytes()
    if len(raw) > MAX_SOURCE_FILE_BYTES:
        raise LineageReviewError(f"source exceeds its byte bound: {relative}")
    return raw


def _validate_original_source(record: object) -> dict[str, object] | None:
    if record is None:
        return None
    if type(record) is not dict or set(record) != {
        "files", "files_sha256", "git_commit", "git_dirty",
    }:
        raise LineageReviewError("original source must preserve the exact frozen source record")
    files = record["files"]
    commit = record["git_commit"]
    if (
        type(files) is not dict or set(files) != set(SOURCE_FILES)
        or record["git_dirty"] is not False
        or type(commit) is not str or _COMMIT.fullmatch(commit) is None
        or record["files_sha256"] != _digest(files)
    ):
        raise LineageReviewError("original source changed its exact clean commit/file inventory")
    for relative in sorted(files):
        expected = _sha256(files[relative], "recorded source file")
        if hashlib.sha256(_read_source(relative)).hexdigest() != expected:
            raise LineageReviewError(f"frozen source differs from the workspace: {relative}")
        # Binding to a real local immutable Git object prevents a rehashed
        # made-up commit string from masquerading as execution provenance.
        object_name = f"{commit}:{relative}"
        try:
            size = subprocess.run(
                ["git", "cat-file", "-s", object_name], cwd=ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                timeout=MAX_GIT_COMMAND_SECONDS,
            ).stdout.strip()
            if not size.isdigit() or int(size) > MAX_SOURCE_FILE_BYTES:
                raise LineageReviewError("recorded Git source object exceeds its byte bound")
            historical = subprocess.run(
                ["git", "cat-file", "blob", object_name], cwd=ROOT,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                timeout=MAX_GIT_COMMAND_SECONDS,
            ).stdout
        except (OSError, subprocess.SubprocessError) as error:
            raise LineageReviewError("recorded source commit cannot be authenticated from local Git") from error
        if len(historical) != int(size) or hashlib.sha256(historical).hexdigest() != expected:
            raise LineageReviewError(f"recorded source commit changed its file identity: {relative}")
    return _detach(record)


class _Union:
    def __init__(self, names: set[str]) -> None:
        self.parent = {name: name for name in names}
        self.edges: set[tuple[str, str, str]] = set()

    def root(self, name: str) -> str:
        while self.parent[name] != name:
            self.parent[name] = self.parent[self.parent[name]]
            name = self.parent[name]
        return name

    def join(self, a: str, b: str, relation: str) -> None:
        self.edges.add((min(a, b), max(a, b), relation))
        a, b = self.root(a), self.root(b)
        if a != b:
            self.parent[max(a, b)] = min(a, b)


def build_lineage_inventory(
    epoch: HydraEpoch,
    *,
    benchmark: dict[str, object] | None = None,
) -> dict[str, object]:
    """Retain the original DEV components and complete the catalog partition.

    Supplemental components are structural review candidates only. Their
    absence from a bounded canonical mask is not semantic novelty, complete
    derivation provenance, independent authorship, or an unseen-model claim.
    """

    if type(epoch) is not HydraEpoch or len(epoch.theorems) > MAX_THEOREMS:
        raise LineageReviewError("lineage review requires one bounded exact HydraEpoch")
    try:
        frozen = build_development_benchmark(epoch) if benchmark is None else validate_benchmark(benchmark, epoch)
    except (HydraBenchmarkError, TypeError) as error:
        raise LineageReviewError(f"original benchmark authentication failed: {error}") from error
    names = {item.name for item in epoch.theorems}
    catalog = {item.name: item for item in epoch.theorems}
    union = _Union(names)
    canonical_by_name: dict[str, str] = {}
    first_alias: dict[str, str] = {}
    unresolved: set[str] = set()
    for theorem in epoch.theorems:
        for dependency in theorem.dependencies:
            union.join(theorem.name, dependency, "checked_dependency")
        try:
            canonical = validate_statement(theorem.statement)
        except (ValueError, TypeError, RecursionError):
            unresolved.add(theorem.name)
            continue
        statement_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        canonical_by_name[theorem.name] = statement_sha256
        first = first_alias.setdefault(statement_sha256, theorem.name)
        if first != theorem.name:
            union.join(first, theorem.name, "bounded_canonical_alias")
    if sorted(unresolved) != frozen["catalog_alias_audit"]["unresolved_theorems"]:
        raise LineageReviewError("catalog canonicalization differs from the original frozen mask")

    original_components = frozen["components"]
    original_by_id = {component["id"]: component for component in original_components}
    for component in original_components:
        members = component["catalog_members"]
        for name in members[1:]:
            union.join(members[0], name, "retained_development_component")
    groups: dict[str, list[str]] = defaultdict(list)
    for name in sorted(names):
        groups[union.root(name)].append(name)
    retained_group_ids: dict[str, str] = {}
    for component in original_components:
        members = component["catalog_members"]
        if members:
            group = union.root(members[0])
            if groups[group] != members or group in retained_group_ids:
                raise LineageReviewError("catalog completion changed or merged an original DEV component")
            retained_group_ids[group] = component["id"]

    masks: dict[str, dict[str, object]] = {}
    goal_masks: list[dict[str, str]] = []
    all_masked: set[str] = set()
    for goal in frozen["goals"]:
        masked = goal["masked_theorems"]
        digest = goal["mask_sha256"]
        if digest != _digest(masked):
            raise LineageReviewError("original goal mask lost its complete exact names")
        previous = masks.setdefault(digest, {"masked_theorems": list(masked), "goal_ids": []})
        if previous["masked_theorems"] != masked:
            raise LineageReviewError("a mask identity aliases different theorem inventories")
        previous["goal_ids"].append(goal["id"])
        goal_masks.append({"goal_id": goal["id"], "mask_sha256": digest})
        all_masked.update(masked)
    if not unresolved <= all_masked:
        raise LineageReviewError("unresolved original canonicalization escaped the retained masks")
    lineages = _lineage_index(epoch)
    component_rows: list[dict[str, object]] = []

    def append_component(identifier: str, members: list[str], original: dict[str, object] | None) -> None:
        masked = sorted(set(members) & all_masked)
        unparsed = sorted(set(members) & unresolved)
        reasons = []
        if original is not None:
            reasons.append("public_development_component")
        if masked:
            reasons.append("retained_benchmark_theorem_mask")
        if unparsed:
            reasons.append("unresolved_canonicalization")
        component_rows.append(
            {
                "component_id": identifier,
                "origin": "retained-development-component" if original is not None else "additional-frozen-catalog-component",
                "original_component_sha256": None if original is None else _digest(original),
                "catalog_members": members,
                "catalog_member_count": len(members),
                "catalog_members_sha256": _digest(members),
                "catalog_lineage_sha256s": sorted({lineages[name] for name in members}),
                "goal_ids": [] if original is None else list(original["goal_ids"]),
                "families": [] if original is None else list(original["families"]),
                "masked_catalog_members": masked,
                "unresolved_canonical_members": unparsed,
                "allocation_restrictions": reasons,
                "structural_candidate_only": bool(members) and not reasons,
                "semantic_equivalence_complete": False,
                "eligible_for_unseen_model_comparison": False,
                "review_status": "not-reviewed",
            }
        )

    for group, members in sorted(groups.items()):
        original_id = retained_group_ids.get(group)
        identifier = original_id or _digest(
            {
                "kind": "additional-frozen-catalog-review-component-v1",
                "epoch_sha256": epoch.epoch_sha256,
                "benchmark_manifest_sha256": frozen["manifest_sha256"],
                "catalog_members": members,
                "canonical_statement_sha256s": {name: canonical_by_name.get(name) for name in members},
            }
        )
        append_component(identifier, members, original_by_id.get(original_id))
    for component in original_components:
        if not component["catalog_members"]:
            append_component(component["id"], [], component)
    component_rows.sort(key=lambda row: row["component_id"])
    if len({row["component_id"] for row in component_rows}) != len(component_rows):
        raise LineageReviewError("review component identities are not unique")
    inventory_members = [name for row in component_rows for name in row["catalog_members"]]
    if sorted(inventory_members) != sorted(names):
        raise LineageReviewError("review components do not cover every frozen theorem exactly once")
    candidate_names = sorted(
        name for row in component_rows if row["structural_candidate_only"]
        for name in row["catalog_members"]
    )
    component_for_name = {
        name: row["component_id"] for row in component_rows for name in row["catalog_members"]
    }
    canonical_index: dict[str, dict[str, object]] = {}
    for name, statement_sha256 in sorted(canonical_by_name.items()):
        record = canonical_index.setdefault(
            statement_sha256,
            {"component_id": component_for_name[name], "catalog_names": []},
        )
        if record["component_id"] != component_for_name[name]:
            raise LineageReviewError("bounded canonical aliases were split across review components")
        record["catalog_names"].append(name)
    result: dict[str, object] = {
        "schema": INVENTORY_SCHEMA,
        "epoch_sha256": epoch.epoch_sha256,
        "edition_identity_sha256": epoch.edition_identity_sha256,
        "theorem_dag_sha256": epoch.theorem_dag_sha256,
        "reviewed_definition_dag_sha256": epoch.reviewed_definition_dag_sha256,
        "benchmark_manifest_sha256": frozen["manifest_sha256"],
        "profile_sha256": frozen["profile_sha256"],
        "original_lineage_graph_sha256": frozen["lineage_graph_sha256"],
        "catalog_completion_edges_sha256": _digest(sorted(union.edges)),
        "catalog_completion_edge_count": len(union.edges),
        "components": component_rows,
        "canonical_catalog_index": canonical_index,
        "canonical_catalog_index_sha256": _digest(canonical_index),
        "component_count": len(component_rows),
        "original_development_component_ids": sorted(original_by_id),
        "catalog_theorem_count": len(names),
        "resource_bounds": {"max_catalog_theorems": MAX_THEOREMS, "max_evidence_bytes": MAX_REVIEW_BYTES},
        "complete_catalog_partition": True,
        "retained_mask_inventory": masks,
        "original_goal_mask_bindings": goal_masks,
        "all_original_masks_retained": True,
        "masked_catalog_theorem_count": len(all_masked),
        "unresolved_canonical_theorem_count": len(unresolved),
        "structural_candidate_component_count": sum(row["structural_candidate_only"] for row in component_rows),
        "structural_candidate_theorem_count": len(candidate_names),
        "candidate_statements_for_review": [
            {
                "name": name,
                "source": catalog[name].statement,
                "statement_sha256": catalog[name].statement_sha256,
                "canonical_statement_sha256": canonical_by_name[name],
                "script_sha256": catalog[name].script_sha256,
                "membership": catalog[name].membership,
            }
            for name in candidate_names
        ],
        "semantic_equivalence_complete": False,
        "independent_authorship_reviewed": False,
        "review_status": "not-reviewed",
        "sealed_benchmark": False,
        "eligible_for_unseen_model_comparison": False,
        "claim_boundary": (
            "Complete catalog partition under retained declared dependencies, families and bounded "
            "canonical aliases only. Mask-complement components are structural review candidates, "
            "not unseen examples, semantically independent lineages, or approved model data."
        ),
    }
    result["inventory_sha256"] = _digest(result)
    if len(_canonical(result)) > MAX_REVIEW_BYTES:
        raise LineageReviewError("complete review inventory exceeds its evidence byte bound")
    return result


def _supplemental_row_exposure(
    directory: Path,
    receipt: dict[str, object],
    inventory: dict[str, object],
) -> dict[str, object]:
    """Inspect exact authenticated rows for aliases outside the old DEV goals.

    The historical audit checks its own goals and all catalog proof roots, but
    does not enumerate every other catalog alias occurring in intermediate
    closed goals.  This pass adds that exposure without changing its receipt.
    Original audit regeneration has already applied every parser input guard.
    """

    from training.peano_hydra import evaluation
    from training.peano_policy.prompt import parse_prompt

    try:
        _, manifest, manifest_sha256, rows = evaluation._load_preparation(directory)
    except (ValueError, TypeError, OSError) as error:
        raise LineageReviewError(f"supplemental exposure could not authenticate original bytes: {error}") from error
    if (
        manifest_sha256 != receipt["preparation_manifest_sha256"]
        or manifest["files"] != receipt["authenticated_files"]
    ):
        raise LineageReviewError("preparation changed between audit and supplemental exposure inspection")
    aliases = inventory["canonical_catalog_index"]
    groups: dict[tuple[str, str], dict[str, object]] = {}
    open_targets = 0
    closed_targets = 0
    reference_count = 0
    retained_bytes = 0
    for filename, split in (("train.jsonl", "train"), ("dev.jsonl", "dev"), ("preferences.jsonl", "train")):
        for number, row in enumerate(rows[filename], 1):
            transition = row if filename == "preferences.jsonl" else row["transition"]
            formulas: list[tuple[str, str]] = [("theorem", evaluation._canonical_formula(transition["theorem"]))]
            goal_lists = (
                (("prompt_goals", parse_prompt(row["prompt"]).goals),)
                if filename == "preferences.jsonl" else
                ((field, transition[field]) for field in ("goals_before", "goals_after"))
            )
            for field, goals in goal_lists:
                for rendered in goals:
                    canonical = evaluation._canonical_goal_target(rendered)
                    if canonical is None:
                        open_targets += 1
                    else:
                        closed_targets += 1
                        formulas.append((field, canonical))
            matches: dict[str, dict[str, set[str]]] = {}
            for field, canonical in formulas:
                digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                alias = aliases.get(digest)
                if alias is None:
                    continue
                match = matches.setdefault(alias["component_id"], {"catalog_names": set(), "kinds": set(), "statements": set()})
                match["catalog_names"].update(alias["catalog_names"])
                match["kinds"].add(field)
                match["statements"].add(digest)
            if not matches:
                continue
            row_sha256 = _digest(row)
            for identifier, match in sorted(matches.items()):
                reference = {
                    "file": filename,
                    "row": number,
                    "source_row_sha256": row_sha256,
                    "occurrence_kinds": sorted(match["kinds"]),
                    "canonical_statement_sha256s": sorted(match["statements"]),
                }
                reference_count += 1
                retained_bytes += len(_canonical(reference))
                if reference_count > MAX_SUPPLEMENTAL_ROW_REFERENCES or retained_bytes > MAX_AUDIT_BYTES:
                    raise LineageReviewError("supplemental exposure exceeds its complete retained row-reference bound")
                group = groups.setdefault(
                    (identifier, split),
                    {"component_id": identifier, "split": split, "catalog_names": set(), "row_references": []},
                )
                group["catalog_names"].update(match["catalog_names"])
                group["row_references"].append(reference)
    components = []
    for _, record in sorted(groups.items()):
        record["catalog_names"] = sorted(record["catalog_names"])
        record["row_reference_count"] = len(record["row_references"])
        record["row_references_sha256"] = _digest(record["row_references"])
        components.append(record)
    result: dict[str, object] = {
        "schema": "peano-hydra-lineage-supplemental-exposure-v1",
        "original_audit_sha256": receipt["audit_sha256"],
        "preparation_manifest_sha256": manifest_sha256,
        "inventory_sha256": inventory["inventory_sha256"],
        "canonical_catalog_index_sha256": inventory["canonical_catalog_index_sha256"],
        "components": components,
        "retained_row_references": reference_count,
        "closed_goal_occurrences_checked": closed_targets,
        "open_or_meta_goal_occurrences_not_closed": open_targets,
        "all_authenticated_exposure_rows_inspected": True,
        "catalog_alias_scope": "bounded canonical index; unresolved catalog entries retain their original masks",
        "unresolved_catalog_theorems_still_masked": inventory["unresolved_canonical_theorem_count"],
        "open_goal_semantic_closure_complete": False,
        "semantic_equivalence_complete": False,
        "training_corpus_replayed": False,
    }
    result["exposure_sha256"] = _digest(result)
    if len(_canonical(result)) > MAX_AUDIT_BYTES:
        raise LineageReviewError("supplemental exposure exceeds its final evidence byte bound")
    return result


def _authenticate_audits(
    epoch: HydraEpoch,
    benchmark: dict[str, object],
    audit_receipts: tuple[dict[str, object], ...],
    preparation_dirs: tuple[Path, ...],
    inventory: dict[str, object],
) -> list[dict[str, object]]:
    if (
        type(audit_receipts) is not tuple or type(preparation_dirs) is not tuple
        or len(audit_receipts) != len(preparation_dirs) or len(audit_receipts) > MAX_AUDITS
    ):
        raise LineageReviewError("audit receipts and original preparation paths must be exact paired bounded tuples")
    paths: set[Path] = set()
    manifests: set[str] = set()
    accepted: list[dict[str, object]] = []
    for receipt, directory in zip(audit_receipts, preparation_dirs, strict=True):
        if type(receipt) is not dict or len(_canonical(receipt)) > MAX_AUDIT_BYTES:
            raise LineageReviewError("exposure receipt exceeds its complete bounded object contract")
        digest = _sha256(receipt.get("audit_sha256"), "exposure audit")
        if (
            receipt.get("schema") != AUDIT_SCHEMA
            or digest != _digest({key: value for key, value in receipt.items() if key != "audit_sha256"})
            or receipt.get("epoch_sha256") != epoch.epoch_sha256
            or receipt.get("benchmark_manifest_sha256") != benchmark["manifest_sha256"]
            or receipt.get("profile_sha256") != benchmark["profile_sha256"]
        ):
            raise LineageReviewError("exposure receipt changed its frozen epoch, benchmark, profile or digest")
        manifest = _sha256(receipt.get("preparation_manifest_sha256"), "preparation manifest")
        if not isinstance(directory, Path):
            raise LineageReviewError("original preparation paths must be pathlib.Path objects")
        path = directory.expanduser().absolute()
        if path.is_symlink() or not path.is_dir():
            raise LineageReviewError("original preparation must be a real non-symlink directory")
        resolved = path.resolve()
        if resolved in paths or manifest in manifests:
            raise LineageReviewError("duplicate original preparation or exposure receipt")
        paths.add(resolved)
        manifests.add(manifest)
        try:
            regenerated = audit_preparation(benchmark, path, epoch=epoch)
        except (HydraBenchmarkError, OSError, TypeError, ValueError) as error:
            raise LineageReviewError(f"original preparation could not be reauthenticated: {error}") from error
        if _canonical(regenerated) != _canonical(receipt):
            raise LineageReviewError("exposure receipt differs from the regenerated original preparation audit")
        try:
            label = str(resolved.relative_to(ROOT))
        except ValueError:
            label = str(resolved)
        supplemental = _supplemental_row_exposure(path, regenerated, inventory)
        accepted.append({"preparation_directory": label, "audit": _detach(regenerated), "supplemental_exposure": supplemental})
    return sorted(accepted, key=lambda item: item["audit"]["preparation_manifest_sha256"])


def _allocations(
    inventory: dict[str, object], proposed: object,
) -> tuple[list[dict[str, object]], bool]:
    component_ids = {row["component_id"] for row in inventory["components"]}
    if proposed is None:
        return [
            {
                "component_id": row["component_id"],
                "split": "quarantine" if row["goal_ids"] else "unassigned",
                "explicitly_proposed": False,
            }
            for row in inventory["components"]
        ], True
    if type(proposed) is not list or len(proposed) > len(component_ids):
        raise LineageReviewError("allocations must be a bounded explicit JSON array of whole components")
    seen: dict[str, str] = {}
    for row in proposed:
        if type(row) is not dict or set(row) != {"component_id", "split"}:
            raise LineageReviewError("allocation rows must contain exactly component_id and split")
        component = row["component_id"]
        split = row["split"]
        if type(component) is not str or component not in component_ids:
            raise LineageReviewError("allocation names an unknown or partial component")
        if component in seen:
            raise LineageReviewError("one component was allocated more than once or across TRAIN/DEV")
        if type(split) is not str or split not in _SPLITS:
            raise LineageReviewError("allocation split must be train, dev, quarantine or unassigned")
        seen[component] = split
    return [
        {"component_id": identifier, "split": seen.get(identifier, "unassigned"), "explicitly_proposed": identifier in seen}
        for identifier in sorted(component_ids)
    ], False


def build_lineage_review(
    epoch: HydraEpoch,
    *,
    benchmark: dict[str, object],
    audit_receipts: tuple[dict[str, object], ...],
    preparation_dirs: tuple[Path, ...],
    allocations: list[dict[str, str]] | None = None,
    original_source: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a review-ready, still unauthorized whole-component split proposal.

    Source identity is checked against workspace bytes and the recorded local
    Git commit. Each supplied audit must exactly match a fresh bounded audit of
    its original files. Missing source/audits/allocations remain blocked; a
    structurally consistent explicit proposal is only ``not-reviewed``.
    """

    benchmark = _detach(benchmark)
    inventory = build_lineage_inventory(epoch, benchmark=benchmark)
    proposal, defaulted = _allocations(inventory, allocations)
    source = _validate_original_source(original_source)
    audits = _authenticate_audits(epoch, benchmark, audit_receipts, preparation_dirs, inventory)
    components = {row["component_id"]: row for row in inventory["components"]}
    theorem_component = {
        name: row["component_id"] for row in inventory["components"] for name in row["catalog_members"]
    }
    exposure: dict[str, list[dict[str, object]]] = defaultdict(list)
    unresolved_exposure: list[dict[str, object]] = []
    for accepted in audits:
        audit = accepted["audit"]
        for split in ("train", "dev"):
            grouped: dict[str, list[str]] = defaultdict(list)
            for name in audit["exposed_theorem_roots"][split]:
                identifier = theorem_component.get(name)
                if identifier is None:
                    unresolved_exposure.append({"audit_sha256": audit["audit_sha256"], "split": split, "theorem_name": name})
                else:
                    grouped[identifier].append(name)
            for identifier, names in sorted(grouped.items()):
                exposure[identifier].append(
                    {
                        "kind": "authenticated_catalog_proof_roots",
                        "audit_sha256": audit["audit_sha256"],
                        "preparation_manifest_sha256": audit["preparation_manifest_sha256"],
                        "split": split,
                        "theorem_roots": sorted(names),
                    }
                )
        for supplemental in accepted["supplemental_exposure"]["components"]:
            exposure[supplemental["component_id"]].append(
                {
                    "kind": "authenticated_closed_row_aliases",
                    "audit_sha256": audit["audit_sha256"],
                    "preparation_manifest_sha256": audit["preparation_manifest_sha256"],
                    "supplemental_exposure_sha256": accepted["supplemental_exposure"]["exposure_sha256"],
                    "split": supplemental["split"],
                    "catalog_aliases": supplemental["catalog_names"],
                    "row_reference_count": supplemental["row_reference_count"],
                    "row_references_sha256": supplemental["row_references_sha256"],
                }
            )
        for name in audit["unresolved_uncataloged_exposure_roots"]:
            if not any(item["audit_sha256"] == audit["audit_sha256"] and item["theorem_name"] == name for item in unresolved_exposure):
                unresolved_exposure.append({"audit_sha256": audit["audit_sha256"], "split": "unknown", "theorem_name": name})

    conflicts: list[dict[str, object]] = []

    def conflict(code: str, component: str | None = None, **detail: object) -> None:
        record: dict[str, object] = {"code": code, "component_id": component, **detail}
        record["conflict_id"] = _digest(record)
        conflicts.append(record)

    if source is None:
        conflict("original_source_provenance_missing")
    if not audits:
        conflict("authenticated_preparation_exposure_missing")
    if unresolved_exposure:
        conflict("uncataloged_exposure_derivations_unresolved", exposures=unresolved_exposure)
    assigned: dict[str, list[str]] = {split: [] for split in _SPLITS}
    for row in proposal:
        identifier = row["component_id"]
        split = row["split"]
        component = components[identifier]
        assigned[split].append(identifier)
        if split == "unassigned":
            conflict("component_allocation_missing_or_unassigned", identifier)
        elif split in {"train", "dev"}:
            if component["allocation_restrictions"]:
                conflict(
                    "component_conflicts_with_retained_benchmark_masks", identifier,
                    split=split, restrictions=component["allocation_restrictions"],
                    masked_catalog_members=component["masked_catalog_members"],
                    original_goal_ids=component["goal_ids"],
                )
            if not component["catalog_members"]:
                conflict("component_has_no_catalog_proof_roots", identifier, split=split)
            if split == "dev" and exposure.get(identifier):
                conflict("development_component_already_exposed", identifier, exposure=exposure[identifier])
    for split in ("train", "dev"):
        if not assigned[split]:
            conflict(f"required_{split}_component_missing")
    structural = [row["component_id"] for row in inventory["components"] if row["structural_candidate_only"]]
    unexposed = (
        [identifier for identifier in structural if not exposure.get(identifier)]
        if audits and not unresolved_exposure else []
    )
    structural_possible = bool(audits) and not unresolved_exposure and any(
        training != development for training in structural for development in unexposed
    )
    if audits and not unresolved_exposure and not structural_possible:
        conflict(
            "no_disjoint_train_dev_allocation_under_retained_graph",
            structural_candidate_component_ids=structural,
            unexposed_structural_component_ids=unexposed,
            exposure_audit_sha256s=sorted(item["audit"]["audit_sha256"] for item in audits),
        )
    conflicts.sort(key=lambda row: (row["code"], row["component_id"] or "", row["conflict_id"]))
    result: dict[str, object] = {
        "schema": REVIEW_SCHEMA,
        "status": "blocked" if conflicts else "not-reviewed",
        "review_status": "not-reviewed",
        "epoch_sha256": epoch.epoch_sha256,
        "edition_identity_sha256": epoch.edition_identity_sha256,
        "benchmark_manifest_sha256": benchmark["manifest_sha256"],
        "profile_sha256": benchmark["profile_sha256"],
        "original_source": source,
        "original_source_workspace_and_git_authenticated": source is not None,
        "planner_source": {
            "path": "training/peano_hydra/lineage_review.py",
            "sha256": hashlib.sha256(_read_source("training/peano_hydra/lineage_review.py")).hexdigest(),
        },
        "inventory": inventory,
        "audits": audits,
        "resource_bounds": {
            "max_audits": MAX_AUDITS,
            "max_audit_or_supplemental_bytes": MAX_AUDIT_BYTES,
            "max_supplemental_row_references_per_preparation": MAX_SUPPLEMENTAL_ROW_REFERENCES,
            "max_review_bytes": MAX_REVIEW_BYTES,
            "max_git_command_seconds": MAX_GIT_COMMAND_SECONDS,
            "model_calls": 0,
            "solver_calls": 0,
            "corpus_replay": False,
        },
        "audit_authentication": "exact regeneration from original preparation bytes; not self-hash-only",
        "exposure_interpretation": (
            "Exposure in every supplied prepared corpus; not an assertion that model weights "
            "consumed each corpus. Narrowing that scope requires separately reviewed provenance."
        ),
        "complete_model_exposure_history_attested": False,
        "allocations": proposal,
        "default_unassigned_template": defaulted,
        "allocation_sha256": _digest(proposal),
        "conflicts": conflicts,
        "conflict_count": len(conflicts),
        "component_exposure": [
            {"component_id": identifier, "exposure": exposure.get(identifier, [])}
            for identifier in sorted(components)
        ],
        "unresolved_exposure": unresolved_exposure,
        "model_facing_proposal": {
            "train_component_ids": sorted(assigned["train"]),
            "dev_component_ids": sorted(assigned["dev"]),
            "quarantine_component_ids": sorted(assigned["quarantine"]),
            "unassigned_component_ids": sorted(assigned["unassigned"]),
            "approved_train_rows": 0,
            "approved_dev_rows": 0,
            "data_written": False,
        },
        "feasibility": {
            "scope": "declared graph and retained masks only; not semantic or unseen feasibility",
            "structural_candidate_component_ids": structural,
            "structural_candidate_component_count": len(structural),
            "unexposed_structural_component_ids": unexposed,
            "unexposed_structural_component_count": len(unexposed),
            "unexposed_structural_theorem_count": sum(len(components[identifier]["catalog_members"]) for identifier in unexposed),
            "distinct_train_dev_components_exist_under_declared_relations": structural_possible,
            "current_eight_development_families_unseen": False,
            "current_development_component_is_approved_for_train_or_dev": False,
            "semantic_feasibility_established": False,
            "recommendation": (
                "Review the listed whole-component structural candidates and authorship provenance; "
                "do not infer semantic independence or reuse the public DEV families as unseen."
                if structural_possible else
                "No disjoint TRAIN/DEV allocation is established from these authenticated exposures "
                "under the retained masks. New reviewed lineages or stronger provenance are required."
            ),
        },
        "review_requirements": [
            {"requirement": "independent_human_component_and_authorship_review", "status": "not-reviewed"},
            {"requirement": "H0_semantic_reference_and_cold_replay_checks", "status": "not-reviewed"},
            {"requirement": "separate_independent_H1_final_set_ownership_and_sealing", "status": "not-reviewed"},
            {"requirement": "explicit_later_authorization_for_model_data_and_execution", "status": "not-reviewed"},
        ],
        "human_review_acknowledgment": None,
        "independent_human_review_granted": False,
        "model_training_authorized": False,
        "model_comparison_authorized": False,
        "eligible_for_unseen_model_comparison": False,
        "semantic_equivalence_complete": False,
        "sealed_benchmark": False,
        "research_claim_eligible": False,
        "training_corpus_replayed": False,
        "model_calls": 0,
        "solver_calls": 0,
        "claim_boundary": (
            "An auditable allocation proposal, not an approved split, unseen benchmark, human "
            "review acknowledgment, H0/H1 completion, or authority to create data or train a model."
        ),
    }
    result["review_sha256"] = _digest(result)
    if len(_canonical(result)) > MAX_REVIEW_BYTES:
        raise LineageReviewError("complete lineage review exceeds its retained evidence byte bound")
    return result


__all__ = [
    "INVENTORY_SCHEMA", "REVIEW_SCHEMA", "LineageReviewError",
    "build_lineage_inventory", "build_lineage_review",
]
