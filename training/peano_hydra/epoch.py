"""Freeze Hydra against one sealed theorem DAG and one reviewed definition DAG.

The current campaign selects the edition; a newer file lying in the repository
never silently enlarges an active run.  Alpha theorem membership, statement and
script identities, the Stable parent, and conservative reviewed definitions are
all authenticated before an opt-in execution capability can be constructed.

This is product-preparation evidence, not a sealed H1 research benchmark.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from peano_lab.ui.prove import SurfaceCapabilities


EPOCH_SCHEMA = "peano-hydra-development-epoch-v1"
MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
MAX_THEOREMS = 32_768
MAX_DEFINITIONS = 8_192
_VERSION = re.compile(r"v[1-9][0-9]{0,3}\Z")
_IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,127}\Z")
_DEFINITION_ID = re.compile(r"[PN]D[0-9A-Z]{4}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class HydraEpochError(ValueError):
    """A proposed training epoch is not a complete sealed product snapshot."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise HydraEpochError(f"duplicate JSON field {key!r}")
        value[key] = item
    return value


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _safe_digest(field: str, value: object) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise HydraEpochError(f"{field} must be one exact SHA-256 digest")
    return value


def _artifact(root: Path, relative: str) -> tuple[dict[str, Any], str]:
    if type(relative) is not str or not relative or "\\" in relative:
        raise HydraEpochError("artifact path must be a safe repository-relative path")
    requested = Path(relative)
    if requested.is_absolute() or ".." in requested.parts:
        raise HydraEpochError("artifact path escapes the reviewed repository")
    path = root / requested
    if path.is_symlink() or not path.is_file():
        raise HydraEpochError(f"sealed artifact {relative!r} is not a regular file")
    try:
        if path.stat().st_size > MAX_ARTIFACT_BYTES:
            raise HydraEpochError(f"sealed artifact {relative!r} exceeds its byte limit")
        payload = path.read_bytes()
        if len(payload) > MAX_ARTIFACT_BYTES:
            raise HydraEpochError(f"sealed artifact {relative!r} exceeds its byte limit")
        document = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=lambda item: (_ for _ in ()).throw(
                HydraEpochError(f"non-finite JSON constant {item!r}")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise HydraEpochError(f"sealed artifact {relative!r} is malformed: {error}") from error
    if type(document) is not dict:
        raise HydraEpochError(f"sealed artifact {relative!r} must contain a JSON object")
    return document, _digest(payload)


@dataclass(frozen=True, slots=True)
class EpochTheorem:
    """One dependency-ordered, checked theorem in the frozen Alpha inventory."""

    name: str
    statement: str
    statement_sha256: str
    script: tuple[str, ...]
    script_sha256: str
    dependencies: tuple[str, ...]
    membership: str
    enrollment_index: int

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "statement": self.statement,
            "statement_sha256": self.statement_sha256,
            "script_sha256": self.script_sha256,
            "dependencies": list(self.dependencies),
            "membership": self.membership,
            "enrollment_index": self.enrollment_index,
        }


@dataclass(frozen=True, slots=True)
class EpochDefinition:
    """One genuinely reviewed conservative abbreviation, not a blueprint alias."""

    identifier: str
    name: str
    dependencies: tuple[str, ...]
    expansion_sha256: str
    topological_layer: int

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.identifier,
            "name": self.name,
            "dependencies": list(self.dependencies),
            "expansion_sha256": self.expansion_sha256,
            "topological_layer": self.topological_layer,
        }


@dataclass(frozen=True, slots=True)
class HydraEpoch:
    """Authenticated training/search authority with separate mathematical DAGs."""

    version: str
    edition_identity_sha256: str
    alpha_catalog_sha256: str
    stable_catalog_sha256: str
    definition_artifact_sha256: str
    campaign_artifact_sha256: str
    theorem_dag_sha256: str
    reviewed_definition_dag_sha256: str
    milestone_dag_sha256: str
    theorems: tuple[EpochTheorem, ...]
    definitions: tuple[EpochDefinition, ...]
    stable_count: int
    theorem_edge_count: int
    definition_edge_count: int
    milestone_count: int
    milestone_edge_count: int
    blueprint_definition_count: int
    blueprint_definition_edge_count: int
    notation_edge_count: int

    @property
    def alpha_only_count(self) -> int:
        return len(self.theorems) - self.stable_count

    @property
    def surface_label(self) -> str:
        return f"hydra-alpha-{self.version}-{self.edition_identity_sha256}"

    @property
    def epoch_sha256(self) -> str:
        return _digest(
            _canonical(
                {
                    "schema": EPOCH_SCHEMA,
                    "version": self.version,
                    "edition_identity_sha256": self.edition_identity_sha256,
                    "alpha_catalog_sha256": self.alpha_catalog_sha256,
                    "stable_catalog_sha256": self.stable_catalog_sha256,
                    "definition_artifact_sha256": self.definition_artifact_sha256,
                    "campaign_artifact_sha256": self.campaign_artifact_sha256,
                    "theorem_dag_sha256": self.theorem_dag_sha256,
                    "reviewed_definition_dag_sha256": self.reviewed_definition_dag_sha256,
                    "milestone_dag_sha256": self.milestone_dag_sha256,
                }
            )
        )

    def theorem(self, name: str) -> EpochTheorem | None:
        if type(name) is not str:
            raise TypeError("theorem name must be text")
        return next((item for item in self.theorems if item.name == name), None)

    def alpha_capabilities(
        self,
        *,
        allowed_commands: frozenset[str],
        allowed_theorems: frozenset[str],
    ) -> SurfaceCapabilities:
        """Create finite, exact-identity, explicitly opted-in Alpha authority."""

        if type(allowed_commands) is not frozenset or not allowed_commands:
            raise HydraEpochError("Hydra Alpha execution needs a nonempty finite tactic set")
        if type(allowed_theorems) is not frozenset:
            raise HydraEpochError("Hydra Alpha execution needs an exact finite theorem set")
        names = frozenset(theorem.name for theorem in self.theorems)
        if not allowed_theorems <= names:
            raise HydraEpochError("Hydra Alpha theorem allowance escapes its frozen epoch")
        return SurfaceCapabilities(
            label=self.surface_label,
            allowed_commands=allowed_commands,
            allowed_theorems=allowed_theorems,
        )

    def to_dict(self, *, include_graphs: bool = False) -> dict[str, object]:
        result: dict[str, object] = {
            "schema": EPOCH_SCHEMA,
            "epoch_sha256": self.epoch_sha256,
            "version": self.version,
            "edition_identity_sha256": self.edition_identity_sha256,
            "surface_label": self.surface_label,
            "alpha_catalog_sha256": self.alpha_catalog_sha256,
            "stable_catalog_sha256": self.stable_catalog_sha256,
            "definition_artifact_sha256": self.definition_artifact_sha256,
            "campaign_artifact_sha256": self.campaign_artifact_sha256,
            "theorem_dag": {
                "authority": "sealed-current-alpha-checked-use",
                "edge_kind": "proof_dependency",
                "node_count": len(self.theorems),
                "edge_count": self.theorem_edge_count,
                "stable_count": self.stable_count,
                "alpha_only_count": self.alpha_only_count,
                "sha256": self.theorem_dag_sha256,
            },
            "definition_dag": {
                "authority": "reviewed-conservative-definition-registry",
                "edge_kind": "definition_uses_definition",
                "node_count": len(self.definitions),
                "edge_count": self.definition_edge_count,
                "sha256": self.reviewed_definition_dag_sha256,
            },
            "non_authoritative_projections": {
                "milestone_count": self.milestone_count,
                "milestone_dependency_count": self.milestone_edge_count,
                "milestone_dag_sha256": self.milestone_dag_sha256,
                "blueprint_definition_count": self.blueprint_definition_count,
                "blueprint_definition_edge_count": self.blueprint_definition_edge_count,
                "notation_edge_count": self.notation_edge_count,
            },
            "research_claim_eligible": False,
            "claim_boundary": (
                "frozen product-development authority only; no sealed H1 benchmark "
                "or demonstrated LLM advantage"
            ),
        }
        if include_graphs:
            result["theorem_dag"]["nodes"] = [item.to_dict() for item in self.theorems]
            result["definition_dag"]["nodes"] = [item.to_dict() for item in self.definitions]
        return result


def _theorems(
    catalog: dict[str, Any], *, version: str, channel: dict[str, Any]
) -> tuple[tuple[EpochTheorem, ...], int, int, str]:
    if (
        catalog.get("schema") != f"peano-library-alpha-snapshot-{version}"
        or catalog.get("channel") != "alpha"
    ):
        raise HydraEpochError("Alpha catalog schema does not match the selected edition")
    expected_count = catalog.get("theorem_count")
    rows = catalog.get("theorems")
    if (
        type(expected_count) is not int
        or not 1 <= expected_count <= MAX_THEOREMS
        or type(rows) is not list
        or len(rows) != expected_count
        or catalog.get("checked_use_count") != expected_count
        or channel.get("theorem_count") != expected_count
        or channel.get("checked_use_count") != expected_count
    ):
        raise HydraEpochError("Alpha inventory must contain only its exact checked-use theorem count")
    observed: set[str] = set()
    result: list[EpochTheorem] = []
    proof_edges = 0
    stable = 0
    for index, item in enumerate(rows):
        if type(item) is not dict:
            raise HydraEpochError("Alpha theorem row is not an object")
        name = item.get("name")
        if type(name) is not str or _IDENTIFIER.fullmatch(name) is None or name in observed:
            raise HydraEpochError("Alpha theorem names must be safe, unique, and ordered")
        statement = item.get("statement")
        if type(statement) is not str or not statement:
            raise HydraEpochError(f"Alpha theorem {name!r} lacks its exact statement")
        statement_sha256 = _safe_digest("theorem statement_sha256", item.get("statement_sha256"))
        if _digest(statement.encode("utf-8")) != statement_sha256:
            raise HydraEpochError(f"Alpha theorem {name!r} changed its sealed statement")
        script = item.get("script")
        if type(script) is not list or not script or not all(type(line) is str and line for line in script):
            raise HydraEpochError(f"Alpha theorem {name!r} lacks its exact nonempty proof script")
        script_sha256 = _safe_digest("theorem script_sha256", item.get("script_sha256"))
        if _digest(("\n".join(script) + "\n").encode("utf-8")) != script_sha256:
            raise HydraEpochError(f"Alpha theorem {name!r} changed its sealed proof script")
        dependencies = item.get("dependencies")
        if (
            type(dependencies) is not list
            or any(type(dependency) is not str for dependency in dependencies)
            or len(set(dependencies)) != len(dependencies)
            or not set(dependencies) <= observed
        ):
            raise HydraEpochError(f"Alpha theorem {name!r} has a cyclic, duplicate, or unavailable proof dependency")
        membership = item.get("membership")
        closure = item.get("empty_context_closure")
        if (
            membership not in {"stable", "alpha_only"}
            or item.get("checked_use") is not True
            or item.get("body_checked") is not True
            or type(closure) is not dict
            or closure.get("status") != "checked"
            or item.get("evidence_status")
            != ("stable_closed" if membership == "stable" else "alpha_closed")
        ):
            raise HydraEpochError(f"Alpha theorem {name!r} lacks checked Stable/Alpha authority")
        if item.get("enrollment_index") != index:
            raise HydraEpochError(f"Alpha theorem {name!r} changed its enrollment order")
        observed.add(name)
        proof_edges += len(dependencies)
        stable += membership == "stable"
        result.append(
            EpochTheorem(
                name,
                statement,
                statement_sha256,
                tuple(script),
                script_sha256,
                tuple(dependencies),
                membership,
                index,
            )
        )
    if catalog.get("edge_count") != proof_edges:
        raise HydraEpochError("Alpha proof-dependency edge count does not match its actual theorem DAG")
    projection = [
        {"name": item.name, "dependencies": list(item.dependencies)}
        for item in result
    ]
    return tuple(result), proof_edges, stable, _digest(_canonical(projection))


def _definitions(document: dict[str, Any]) -> tuple[tuple[EpochDefinition, ...], int, str]:
    if document.get("schema") != "constructive-number-theory-definition-dag-v1":
        raise HydraEpochError("reviewed definition artifact has an unrecognized schema")
    rows = document.get("reviewed_definitions")
    expected = document.get("reviewed_definition_count")
    if (
        type(rows) is not list
        or type(expected) is not int
        or not 1 <= expected <= MAX_DEFINITIONS
        or len(rows) != expected
    ):
        raise HydraEpochError("reviewed definition inventory changed its exact count")
    seen_names: set[str] = set()
    seen_ids: set[str] = set()
    layers: dict[str, int] = {}
    result: list[EpochDefinition] = []
    edge_count = 0
    for item in rows:
        if type(item) is not dict:
            raise HydraEpochError("reviewed definition row is not an object")
        identifier = item.get("id")
        name = item.get("name")
        if (
            type(identifier) is not str
            or _DEFINITION_ID.fullmatch(identifier) is None
            or identifier in seen_ids
            or type(name) is not str
            or _IDENTIFIER.fullmatch(name) is None
            or name in seen_names
        ):
            raise HydraEpochError("reviewed definitions need unique stable IDs and safe names")
        dependencies = item.get("dependencies")
        if (
            type(dependencies) is not list
            or any(type(dependency) is not str for dependency in dependencies)
            or len(set(dependencies)) != len(dependencies)
            or not set(dependencies) <= seen_names
        ):
            raise HydraEpochError(f"reviewed definition {name!r} has an invalid dependency DAG")
        layer = item.get("topological_layer")
        expected_layer = max((layers[dependency] + 1 for dependency in dependencies), default=0)
        if type(layer) is not int or layer != expected_layer:
            raise HydraEpochError(f"reviewed definition {name!r} changed its topological layer")
        expansion = _safe_digest("reviewed definition expansion_sha256", item.get("expansion_sha256"))
        seen_ids.add(identifier)
        seen_names.add(name)
        layers[name] = layer
        edge_count += len(dependencies)
        result.append(EpochDefinition(identifier, name, tuple(dependencies), expansion, layer))
    if document.get("reviewed_definition_edge_count") != edge_count:
        raise HydraEpochError("reviewed definition-dependency edge count changed")
    projection = [
        {"id": item.identifier, "name": item.name, "dependencies": list(item.dependencies)}
        for item in result
    ]
    return tuple(result), edge_count, _digest(_canonical(projection))


def freeze_epoch(root: Path | None = None) -> HydraEpoch:
    """Authenticate the edition selected by the current public campaign."""

    repository = (
        Path(__file__).resolve().parents[2]
        if root is None
        else Path(root).resolve()
    )
    campaign, campaign_sha256 = _artifact(
        repository,
        "book/_static/constructive-grand-campaign/campaign.json",
    )
    if campaign.get("schema") != "constructive-grand-campaign-v1":
        raise HydraEpochError("grand campaign does not declare its reviewed schema")
    metadata = campaign.get("meta")
    if type(metadata) is not dict:
        raise HydraEpochError("grand campaign has no current Alpha release metadata")
    version = metadata.get("current_alpha_version")
    if type(version) is not str or _VERSION.fullmatch(version) is None:
        raise HydraEpochError("grand campaign does not identify one safe current Alpha release")
    boundaries = campaign.get("ambitious_boundaries")
    release = (
        boundaries.get(f"alpha_{version}_edition")
        if type(boundaries) is dict
        else None
    )
    if type(release) is not dict or release.get("role") != "current_immutable_release":
        raise HydraEpochError("grand campaign does not identify one current sealed Alpha release")
    channels, _ = _artifact(repository, f"artifacts/peano-library/channels-{version}.json")
    if channels.get("schema") != f"peano-library-channels-{version}":
        raise HydraEpochError("selected release channel does not match the current campaign")
    channel_map = channels.get("channels")
    if type(channel_map) is not dict:
        raise HydraEpochError("selected release has no Stable/Alpha channels")
    alpha = channel_map.get("alpha")
    stable = channel_map.get("stable")
    if type(alpha) is not dict or type(stable) is not dict:
        raise HydraEpochError("selected release must contain separate Stable and Alpha channels")
    alpha_path = f"artifacts/peano-library/alpha/catalog-{version}.json"
    if alpha.get("artifact_path") != alpha_path:
        raise HydraEpochError("Alpha release channel does not bind its exact versioned catalog")
    catalog, catalog_sha256 = _artifact(repository, alpha_path)
    if _safe_digest("Alpha channel artifact_sha256", alpha.get("artifact_sha256")) != catalog_sha256:
        raise HydraEpochError("current Alpha catalog differs from its sealed release bytes")
    if _safe_digest("campaign Alpha catalog_sha256", release.get("catalog_sha256")) != catalog_sha256:
        raise HydraEpochError("campaign Alpha release does not bind its exact sealed catalog")
    stable_path = stable.get("artifact_path")
    if stable_path != "artifacts/peano-library/catalog-v1.json":
        raise HydraEpochError("Stable release no longer names its immutable catalog")
    stable_catalog, stable_sha256 = _artifact(repository, stable_path)
    if _safe_digest("Stable channel artifact_sha256", stable.get("artifact_sha256")) != stable_sha256:
        raise HydraEpochError("Stable catalog differs from its sealed immutable bytes")
    identity = _safe_digest("Alpha edition_identity_sha256", alpha.get("edition_identity_sha256"))
    if catalog.get("edition_identity_sha256") != identity:
        raise HydraEpochError("Alpha release and theorem catalog disagree about edition identity")
    theorems, theorem_edges, stable_count, theorem_digest = _theorems(
        catalog, version=version, channel=alpha
    )
    if (
        release.get("theorem_count") != len(theorems)
        or release.get("checked_use_count") != len(theorems)
        or release.get("dependency_edge_count") != theorem_edges
        or release.get("checked_dependency_edge_count") != theorem_edges
    ):
        raise HydraEpochError("current Alpha campaign boundary changed its checked theorem DAG")
    if (
        stable.get("theorem_count") != stable_count
        or stable.get("checked_use_count") != stable_count
        or stable_catalog.get("theorem_count") != stable_count
    ):
        raise HydraEpochError("Alpha release changed its immutable Stable theorem membership")
    stable_rows = stable_catalog.get("theorems")
    if type(stable_rows) is not list or len(stable_rows) != stable_count:
        raise HydraEpochError("immutable Stable catalog changed its exact theorem inventory")
    stable_names = {
        row.get("name")
        for row in stable_rows
        if type(row) is dict and type(row.get("name")) is str
    }
    observed_stable = {
        theorem.name for theorem in theorems if theorem.membership == "stable"
    }
    if len(stable_names) != stable_count or stable_names != observed_stable:
        raise HydraEpochError("Alpha release changed its immutable Stable theorem names")
    stable_by_name = {row["name"]: row for row in stable_rows}
    for theorem in theorems:
        if theorem.membership != "stable":
            continue
        immutable = stable_by_name[theorem.name]
        if (
            immutable.get("statement") != theorem.statement
            or immutable.get("statement_sha256") != theorem.statement_sha256
            or immutable.get("script_sha256") != theorem.script_sha256
            or immutable.get("dependencies") != list(theorem.dependencies)
            or immutable.get("index") != theorem.enrollment_index
        ):
            raise HydraEpochError(
                f"Alpha release changed immutable Stable theorem {theorem.name!r}"
            )
    if metadata.get("current_alpha_checked_use_count") != len(theorems):
        raise HydraEpochError("grand campaign and checked Alpha theorem inventory disagree")
    definitions, definitions_sha256 = _artifact(
        repository,
        "book/_static/constructive-grand-campaign/definitions.json",
    )
    campaign_snapshot = _digest(_canonical(campaign))
    if definitions.get("campaign_snapshot_sha256") != campaign_snapshot:
        raise HydraEpochError(
            "reviewed definition snapshot does not match the exact current campaign; "
            "synchronize its separate DAG before freezing Hydra authority"
        )
    blueprint_definitions = campaign.get("definitions")
    if (
        type(blueprint_definitions) is not dict
        or definitions.get("definition_count") != len(blueprint_definitions)
    ):
        raise HydraEpochError("campaign blueprint notation and its definition DAG disagree")
    reviewed, definition_edges, definition_digest = _definitions(definitions)
    nodes = campaign.get("nodes")
    if type(nodes) is not list or len(nodes) != metadata.get("node_count"):
        raise HydraEpochError("grand campaign changed its exact milestone inventory")
    milestone_projection = [
        {"id": item["id"], "deps": item["deps"], "layer": item["layer"]}
        for item in nodes
        if type(item) is dict
        and type(item.get("id")) is str
        and type(item.get("deps")) is list
        and type(item.get("layer")) is int
    ]
    if len(milestone_projection) != len(nodes):
        raise HydraEpochError("grand campaign contains an invalid conceptual milestone")
    return HydraEpoch(
        version=version,
        edition_identity_sha256=identity,
        alpha_catalog_sha256=catalog_sha256,
        stable_catalog_sha256=stable_sha256,
        definition_artifact_sha256=definitions_sha256,
        campaign_artifact_sha256=campaign_sha256,
        theorem_dag_sha256=theorem_digest,
        reviewed_definition_dag_sha256=definition_digest,
        milestone_dag_sha256=_digest(_canonical(milestone_projection)),
        theorems=theorems,
        definitions=reviewed,
        stable_count=stable_count,
        theorem_edge_count=theorem_edges,
        definition_edge_count=definition_edges,
        milestone_count=len(nodes),
        milestone_edge_count=sum(len(item["deps"]) for item in nodes),
        blueprint_definition_count=definitions.get("definition_count"),
        blueprint_definition_edge_count=definitions.get("definition_edge_count"),
        notation_edge_count=definitions.get("milestone_usage_edge_count"),
    )
