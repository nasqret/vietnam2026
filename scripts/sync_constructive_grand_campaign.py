#!/usr/bin/env python3
"""Synchronize the portable grand-campaign explorer with its exact JSON DAG."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from constructive_definition_graph import (
    DefinitionGraphError,
    SCHEMA as DEFINITION_SCHEMA,
    build_definition_graph,
)


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "book" / "_static" / "constructive-grand-campaign" / "campaign.json"
EXPLORER = CAMPAIGN.parent / "index.html"
DEFINITION_GRAPH = CAMPAIGN.parent / "definitions.json"
OPENING = '<script type="application/json" id="campaign-data">'
CLOSING = "</script>"
ALPHA_VERSION = re.compile(r"v[1-9][0-9]*\Z")
IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
MAX_CAMPAIGN_BYTES = 8 * 1024 * 1024
MAX_CATALOG_BYTES = 64 * 1024 * 1024
HONEST_STATUSES = frozenset(
    {
        "available",
        "stable_closed",
        "alpha_closed",
        "pending_layered_closure",
        "body_checked",
        "existing_foundation",
        "existing_anchor_closure",
        "existing_anchor_extension",
        "open",
    }
)


class CampaignDagError(ValueError):
    """The checked-theorem, milestone, or conservative-definition DAG is unsafe."""


@dataclass(frozen=True, slots=True)
class CampaignDagAudit:
    """Separate deterministic identities for the product's independent DAGs."""

    alpha_version: str
    catalog_sha256: str
    theorem_count: int
    theorem_edge_count: int
    theorem_dag_sha256: str
    milestone_count: int
    milestone_proof_edge_count: int
    milestone_dag_sha256: str
    definition_count: int
    definition_edge_count: int
    definition_dag_sha256: str
    reviewed_definition_count: int
    reviewed_definition_edge_count: int
    reviewed_definition_dag_sha256: str
    milestone_usage_edge_count: int
    statement_usage_edge_count: int
    declared_notation_edge_count: int
    campaign_snapshot_sha256: str


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: object) -> str:
    return sha256(_canonical(value)).hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CampaignDagError(f"checked product artifact repeats JSON field {key!r}")
        result[key] = value
    return result


def _load_document(path: Path, *, maximum: int, context: str) -> tuple[dict[str, Any], str]:
    if path.is_symlink() or not path.is_file():
        raise CampaignDagError(f"{context} must be an ordinary repository artifact")
    if path.stat().st_size > maximum:
        raise CampaignDagError(f"{context} exceeds its safe bounded artifact size")
    payload = path.read_bytes()
    if len(payload) > maximum:
        raise CampaignDagError(f"{context} exceeds its safe bounded artifact size")

    def reject_constant(value: str) -> None:
        raise CampaignDagError(f"{context} contains non-finite JSON constant {value!r}")

    document = json.loads(
        payload.decode("utf-8"),
        object_pairs_hook=_strict_object,
        parse_constant=reject_constant,
    )
    if type(document) is not dict:
        raise CampaignDagError(f"{context} must contain one exact JSON object")
    return document, sha256(payload).hexdigest()


def _name(value: object, *, context: str) -> str:
    if type(value) is not str or IDENTIFIER.fullmatch(value) is None:
        raise CampaignDagError(f"{context} must be an exact safe identifier")
    return value


def _count(value: object, *, context: str) -> int:
    if type(value) is not int or value < 0:
        raise CampaignDagError(f"{context} must be an exact nonnegative integer")
    return value


def _projection_digest(rows: list[dict[str, Any]]) -> str:
    return _digest(rows)


def _milestone_dag(
    campaign: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    rows = campaign.get("nodes")
    families = campaign.get("families")
    layers = campaign.get("layers")
    metadata = campaign.get("meta")
    if type(rows) is not list or not rows:
        raise CampaignDagError("campaign milestone DAG needs a nonempty ordered node list")
    if type(families) is not list or not families:
        raise CampaignDagError("campaign milestone DAG needs its mathematical families")
    if type(layers) is not list or not layers or type(metadata) is not dict:
        raise CampaignDagError("campaign milestone DAG needs exact layers and metadata")

    families_by_id: dict[str, dict[str, Any]] = {}
    family_slugs: set[str] = set()
    for family in families:
        if type(family) is not dict:
            raise CampaignDagError("campaign contains a malformed mathematical family")
        identifier = _name(family.get("id"), context="campaign family identifier")
        if identifier in families_by_id:
            raise CampaignDagError(f"campaign repeats mathematical family {identifier!r}")
        slug = family.get("slug")
        if type(slug) is not str or re.fullmatch(r"[a-z][a-z0-9-]*", slug) is None:
            raise CampaignDagError(f"campaign family {identifier!r} has an unsafe route")
        if slug in family_slugs:
            raise CampaignDagError(f"campaign repeats family route {slug!r}")
        families_by_id[identifier] = family
        family_slugs.add(slug)

    layer_numbers: list[int] = []
    for layer in layers:
        if type(layer) is not dict:
            raise CampaignDagError("campaign contains a malformed dependency layer")
        layer_numbers.append(_count(layer.get("number"), context="campaign layer number"))
    if layer_numbers != list(range(len(layer_numbers))):
        raise CampaignDagError("campaign dependency layers must be contiguous and ordered")

    by_id: dict[str, dict[str, Any]] = {}
    kinds: Counter[str] = Counter()
    goals_by_family: dict[str, list[str]] = {identifier: [] for identifier in families_by_id}
    for row in rows:
        if type(row) is not dict:
            raise CampaignDagError("campaign contains a malformed theorem/tool/anchor node")
        identifier = _name(row.get("id"), context="campaign milestone identifier")
        if identifier in by_id:
            raise CampaignDagError(f"campaign milestone {identifier!r} is duplicated")
        kind = row.get("kind")
        if kind not in {"tool", "anchor", "goal"}:
            raise CampaignDagError(f"campaign milestone {identifier!r} has an invalid kind")
        if not identifier.startswith({"tool": "T", "anchor": "A", "goal": "G"}[kind]):
            raise CampaignDagError(f"campaign milestone {identifier!r} has the wrong namespace")
        if _count(row.get("layer"), context=f"campaign milestone {identifier!r} layer") not in (
            layer_numbers
        ):
            raise CampaignDagError(f"campaign milestone {identifier!r} has an unknown layer")
        for field in ("title", "statement"):
            value = row.get(field)
            if type(value) is not str or not value.strip():
                raise CampaignDagError(f"campaign milestone {identifier!r} needs a real {field}")
        if row.get("status") not in HONEST_STATUSES:
            raise CampaignDagError(f"campaign milestone {identifier!r} has an unreviewed status")
        family = row.get("family")
        if family is not None and family not in families_by_id:
            raise CampaignDagError(f"campaign milestone {identifier!r} has an unknown family")
        if kind == "goal":
            if family is None:
                raise CampaignDagError(f"campaign goal {identifier!r} has no mathematical family")
            goals_by_family[family].append(identifier)
        by_id[identifier] = row
        kinds[kind] += 1

    if _count(metadata.get("node_count"), context="campaign node count") != len(rows):
        raise CampaignDagError("campaign milestone node count disagrees with the actual DAG")
    if _count(metadata.get("max_layer"), context="campaign maximum layer") != len(layers) - 1:
        raise CampaignDagError("campaign maximum layer disagrees with the actual DAG")
    for kind in ("tool", "anchor", "goal"):
        if _count(metadata.get(f"{kind}_count"), context=f"campaign {kind} count") != kinds[kind]:
            raise CampaignDagError(f"campaign {kind} count disagrees with the actual DAG")
    for identifier, family in families_by_id.items():
        expected = goals_by_family[identifier]
        observed = family.get("goal_ids")
        if type(observed) is not list or observed != expected:
            raise CampaignDagError(f"campaign family {identifier!r} has stale goal membership")

    edge_count = 0
    projection: list[dict[str, Any]] = []
    for identifier, row in by_id.items():
        dependencies = row.get("deps")
        if type(dependencies) is not list:
            raise CampaignDagError(f"campaign milestone {identifier!r} has invalid proof prerequisites")
        direct: set[str] = set()
        for dependency in dependencies:
            dependency = _name(
                dependency,
                context=f"campaign milestone {identifier!r} proof prerequisite",
            )
            if dependency in direct:
                raise CampaignDagError(f"campaign milestone {identifier!r} repeats a proof edge")
            if dependency not in by_id:
                raise CampaignDagError(
                    f"campaign milestone {identifier!r} has missing proof prerequisite {dependency!r}"
                )
            if by_id[dependency]["layer"] >= row["layer"]:
                raise CampaignDagError(
                    f"campaign proof dependency {dependency!r} -> {identifier!r} "
                    "is reversed, circular, or not strictly layered"
                )
            direct.add(dependency)

        conceptual = row.get("conceptual_refs", [])
        if type(conceptual) is not list:
            raise CampaignDagError(f"campaign milestone {identifier!r} has invalid conceptual links")
        seen_conceptual: set[str] = set()
        for reference in conceptual:
            reference = _name(
                reference,
                context=f"campaign milestone {identifier!r} conceptual connection",
            )
            if reference not in by_id or reference == identifier or reference in seen_conceptual:
                raise CampaignDagError(
                    f"campaign milestone {identifier!r} has a missing, repeated, "
                    "or self-referential conceptual connection"
                )
            if reference in direct:
                raise CampaignDagError(
                    f"campaign milestone {identifier!r} conflates a conceptual link "
                    "with a proof prerequisite"
                )
            seen_conceptual.add(reference)

        edge_count += len(dependencies)
        projection.append({"id": identifier, "deps": dependencies, "layer": row["layer"]})
    return projection, edge_count


def _definition_dags(
    campaign: Mapping[str, Any],
    graph: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, int, int, int, int]:
    if type(graph) is not dict or graph.get("schema") != DEFINITION_SCHEMA:
        raise CampaignDagError("conservative definition artifact has an invalid schema")
    snapshot = _digest(campaign)
    if graph.get("campaign_snapshot_sha256") != snapshot:
        raise CampaignDagError("conservative definition DAG belongs to a different campaign")

    rows = graph.get("definitions")
    reviewed = graph.get("reviewed_definitions")
    raw = campaign.get("definitions")
    if type(rows) is not list or type(reviewed) is not list or type(raw) is not dict:
        raise CampaignDagError("conservative definition DAG has an invalid node inventory")
    if _count(graph.get("definition_count"), context="blueprint definition count") != len(rows):
        raise CampaignDagError("blueprint definition count disagrees with its DAG")
    if _count(graph.get("reviewed_definition_count"), context="reviewed definition count") != len(
        reviewed
    ):
        raise CampaignDagError("reviewed definition count disagrees with its DAG")

    def inspect(
        entries: list[dict[str, Any]],
        *,
        reviewed_registry: bool,
    ) -> tuple[list[dict[str, Any]], int, list[dict[str, str]]]:
        names: set[str] = set()
        stable_ids: set[str] = set()
        layers: dict[str, int] = {}
        projection: list[dict[str, Any]] = []
        edges: list[dict[str, str]] = []
        for row in entries:
            if type(row) is not dict:
                raise CampaignDagError("conservative definition DAG contains a malformed node")
            name = _name(row.get("name"), context="conservative definition name")
            if name in names:
                raise CampaignDagError(f"conservative definition {name!r} is duplicated")
            dependencies = row.get("dependencies")
            if type(dependencies) is not list:
                raise CampaignDagError(f"conservative definition {name!r} has invalid dependencies")
            direct: set[str] = set()
            for dependency in dependencies:
                dependency = _name(
                    dependency,
                    context=f"conservative definition {name!r} prerequisite",
                )
                if dependency in direct:
                    raise CampaignDagError(f"conservative definition {name!r} repeats a dependency")
                if dependency not in names:
                    raise CampaignDagError(
                        f"conservative definition {name!r} has a missing, forward, "
                        "or circular dependency"
                    )
                direct.add(dependency)
                if not reviewed_registry:
                    edges.append(
                        {
                            "kind": "definition_uses_definition",
                            "source": name,
                            "target": dependency,
                        }
                    )
            expected_layer = max((layers[dependency] + 1 for dependency in dependencies), default=0)
            if _count(
                row.get("topological_layer"),
                context=f"conservative definition {name!r} topological layer",
            ) != expected_layer:
                raise CampaignDagError(f"conservative definition {name!r} changed its DAG layer")
            expansion = row.get("expansion_sha256")
            if type(expansion) is not str or DIGEST.fullmatch(expansion) is None:
                raise CampaignDagError(
                    f"conservative definition {name!r} has no exact expansion SHA-256"
                )
            if not reviewed_registry:
                blueprint = raw.get(name)
                if type(blueprint) is not dict or row.get("expansion") != blueprint.get("expansion"):
                    raise CampaignDagError(
                        f"blueprint definition {name!r} disagrees with its campaign expansion"
                    )
                if sha256(row["expansion"].encode("utf-8")).hexdigest() != expansion:
                    raise CampaignDagError(
                        f"blueprint definition {name!r} changed its expansion SHA-256"
                    )
            names.add(name)
            layers[name] = expected_layer
            record: dict[str, Any] = {"name": name, "dependencies": dependencies}
            if reviewed_registry:
                identifier = _name(row.get("id"), context=f"reviewed definition {name!r} ID")
                if identifier in stable_ids:
                    raise CampaignDagError(f"reviewed definition identifier {identifier!r} is reused")
                stable_ids.add(identifier)
                record = {"id": identifier, **record}
            projection.append(record)
        return projection, sum(len(row["dependencies"]) for row in entries), edges

    definitions, definition_edge_count, expected_edges = inspect(rows, reviewed_registry=False)
    checked, reviewed_edge_count, _ = inspect(reviewed, reviewed_registry=True)
    if {row["name"] for row in definitions} != set(raw):
        raise CampaignDagError("blueprint definition DAG disagrees with the campaign vocabulary")
    if graph.get("topological_order") != [row["name"] for row in definitions]:
        raise CampaignDagError("blueprint definition DAG has a stale topological order")
    if _count(graph.get("definition_edge_count"), context="blueprint definition edge count") != (
        definition_edge_count
    ):
        raise CampaignDagError("blueprint definition edge count disagrees with its DAG")
    if _count(
        graph.get("reviewed_definition_edge_count"), context="reviewed definition edge count"
    ) != reviewed_edge_count:
        raise CampaignDagError("reviewed definition edge count disagrees with its DAG")
    if graph.get("definition_edges") != expected_edges:
        raise CampaignDagError(
            "definition-dependency edges must have only definition endpoints "
            "and the definition_uses_definition category"
        )

    milestone_ids = {row["id"] for row in campaign["nodes"]}
    definition_names = {row["name"] for row in definitions}
    usage = graph.get("milestone_usage_edges")
    if type(usage) is not list:
        raise CampaignDagError("milestone-to-definition notation edges are malformed")
    observed_kinds: Counter[str] = Counter()
    observed_edges: set[tuple[str, str, str]] = set()
    for edge in usage:
        if type(edge) is not dict:
            raise CampaignDagError("milestone notation graph contains a malformed edge")
        kind, source, target = edge.get("kind"), edge.get("source"), edge.get("target")
        if kind not in {"statement_uses_definition", "declared_notation"}:
            raise CampaignDagError("milestone notation cannot masquerade as a theorem proof edge")
        if source not in milestone_ids or target not in definition_names:
            raise CampaignDagError("milestone notation edge crosses the wrong graph namespaces")
        identity = (kind, source, target)
        if identity in observed_edges:
            raise CampaignDagError("milestone notation graph contains a duplicate edge")
        observed_edges.add(identity)
        observed_kinds[kind] += 1

    statement_count = _count(
        graph.get("statement_usage_edge_count"), context="statement notation edge count"
    )
    declared_count = _count(
        graph.get("declared_notation_edge_count"), context="declared notation edge count"
    )
    usage_count = _count(
        graph.get("milestone_usage_edge_count"), context="milestone notation edge count"
    )
    if (
        usage_count != len(usage)
        or statement_count != observed_kinds["statement_uses_definition"]
        or declared_count != observed_kinds["declared_notation"]
        or usage_count != statement_count + declared_count
    ):
        raise CampaignDagError("milestone notation counts disagree with their distinct edge kinds")
    return (
        definitions,
        checked,
        definition_edge_count,
        reviewed_edge_count,
        usage_count,
        statement_count,
        declared_count,
    )


def _milestone_authority(
    campaign: Mapping[str, Any],
    *,
    theorem_membership: Mapping[str, str],
) -> None:
    """Never promote a research milestone merely because a component is proved."""

    for row in campaign["nodes"]:
        identifier = row["id"]
        status = row["status"]
        evidence = row.get("evidence")
        if status in {"alpha_closed", "stable_closed"}:
            if type(evidence) is not dict or evidence.get("checked_use") is not True:
                raise CampaignDagError(
                    f"closed campaign milestone {identifier!r} has no checked theorem authority"
                )
            if status == "stable_closed" and evidence.get("stable_member") is not True:
                raise CampaignDagError(
                    f"campaign milestone {identifier!r} falsely claims Stable admission"
                )
            if status == "alpha_closed" and evidence.get("stable_member") is True:
                raise CampaignDagError(
                    f"campaign milestone {identifier!r} conflates Alpha and Stable membership"
                )
        elif status == "open" and type(evidence) is dict:
            if evidence.get("checked_use") is True:
                raise CampaignDagError(
                    f"open campaign milestone {identifier!r} falsely claims checked closure"
                )
            if evidence.get("partial_component_checked_use") is True:
                component = evidence.get("partial_theorem_name")
                if type(component) is not str or component not in theorem_membership:
                    raise CampaignDagError(
                        f"open campaign milestone {identifier!r} lacks its checked partial theorem"
                    )

        if type(evidence) is not dict:
            continue
        for field in ("theorem_name", "partial_theorem_name"):
            name = evidence.get(field)
            if name is not None and (
                type(name) is not str or name not in theorem_membership
            ):
                raise CampaignDagError(
                    f"campaign milestone {identifier!r} cites unavailable checked theorem {name!r}"
                )
            if (
                status == "stable_closed"
                and field == "theorem_name"
                and name is not None
                and theorem_membership[name] != "stable"
            ):
                raise CampaignDagError(
                    f"campaign milestone {identifier!r} claims a non-Stable theorem as Stable"
                )
        for field in (
            "theorem_names",
            "checked_theorem_names",
            "alternative_checked_theorem_names",
        ):
            names = evidence.get(field)
            if names is None:
                continue
            if type(names) is not list:
                raise CampaignDagError(
                    f"campaign milestone {identifier!r} has malformed checked theorem references"
                )
            seen: set[str] = set()
            for name in names:
                if type(name) is not str or name not in theorem_membership or name in seen:
                    raise CampaignDagError(
                        f"campaign milestone {identifier!r} has a repeated or unavailable "
                        "checked theorem reference"
                    )
                seen.add(name)


def validate_campaign_dags(
    campaign: Mapping[str, Any],
    *,
    definition_graph: Mapping[str, Any] | None = None,
    catalog: Mapping[str, Any] | None = None,
    catalog_sha256: str | None = None,
) -> CampaignDagAudit:
    """Validate the single checked-theorem DAG and independent definition DAGs.

    The campaign's milestone-planning DAG and both notation-edge categories are
    audited separately.  None can enter checked-theorem reachability, promotion,
    post-training examples, or proof-optimization decisions.
    """

    if type(campaign) is not dict or campaign.get("schema") != "constructive-grand-campaign-v1":
        raise CampaignDagError("grand-campaign JSON has an invalid schema")
    metadata = campaign.get("meta")
    if type(metadata) is not dict:
        raise CampaignDagError("grand campaign has no current Alpha release metadata")
    version = metadata.get("current_alpha_version")
    if type(version) is not str or ALPHA_VERSION.fullmatch(version) is None:
        raise CampaignDagError("grand campaign has an unsafe current Alpha release version")

    boundaries = campaign.get("ambitious_boundaries")
    release = (
        boundaries.get(f"alpha_{version}_edition") if type(boundaries) is dict else None
    )
    if type(release) is not dict or release.get("role") != "current_immutable_release":
        raise CampaignDagError("grand campaign does not identify its current immutable Alpha release")
    sealed = release.get("catalog_sha256")
    if type(sealed) is not str or DIGEST.fullmatch(sealed) is None:
        raise CampaignDagError("current Alpha release has no sealed catalog SHA-256")

    if catalog is None:
        if catalog_sha256 is not None:
            raise CampaignDagError("a catalog digest cannot be supplied without its catalog")
        source = ROOT / "artifacts" / "peano-library" / "alpha" / f"catalog-{version}.json"
        catalog, catalog_sha256 = _load_document(
            source,
            maximum=MAX_CATALOG_BYTES,
            context="current Alpha theorem catalog",
        )
    elif catalog_sha256 is None:
        catalog_sha256 = sealed
    if type(catalog_sha256) is not str or DIGEST.fullmatch(catalog_sha256) is None:
        raise CampaignDagError("current Alpha catalog SHA-256 has an unsafe format")
    if catalog_sha256 != sealed:
        raise CampaignDagError("current Alpha catalog disagrees with its immutable sealed digest")
    if type(catalog) is not dict or catalog.get("schema") != f"peano-library-alpha-snapshot-{version}":
        raise CampaignDagError("current Alpha theorem catalog has an invalid or stale schema")
    if catalog.get("channel") != "alpha":
        raise CampaignDagError("the checked-theorem DAG must belong to the Alpha channel")

    rows = catalog.get("theorems")
    if type(rows) is not list or not rows:
        raise CampaignDagError("checked-theorem DAG needs a nonempty dependency-ordered inventory")
    expected_count = _count(catalog.get("theorem_count"), context="Alpha theorem count")
    checked_count = _count(catalog.get("checked_use_count"), context="Alpha checked-use count")
    if (
        expected_count != len(rows)
        or checked_count != len(rows)
        or _count(
            metadata.get("current_alpha_checked_use_count"), context="campaign checked-use count"
        )
        != len(rows)
        or _count(release.get("theorem_count"), context="sealed Alpha theorem count") != len(rows)
        or _count(release.get("checked_use_count"), context="sealed Alpha checked-use count")
        != len(rows)
    ):
        raise CampaignDagError("current Alpha checked-theorem counts disagree across product surfaces")

    known: set[str] = set()
    theorem_membership: dict[str, str] = {}
    theorem_projection: list[dict[str, Any]] = []
    theorem_edge_count = 0
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise CampaignDagError("checked-theorem DAG contains a malformed theorem")
        name = _name(row.get("name"), context="checked theorem name")
        if name in known:
            raise CampaignDagError(f"checked theorem {name!r} is duplicated")
        if _count(row.get("enrollment_index"), context=f"checked theorem {name!r} index") != index:
            raise CampaignDagError(f"checked theorem {name!r} changed its immutable enrollment order")
        if row.get("checked_use") is not True or row.get("body_checked") is not True:
            raise CampaignDagError(f"unchecked theorem {name!r} entered the checked-use DAG")
        closure = row.get("empty_context_closure")
        if type(closure) is not dict or closure.get("status") != "checked":
            raise CampaignDagError(f"theorem {name!r} lacks a checked empty-context closure")
        membership = row.get("membership")
        status = row.get("evidence_status")
        if (membership, status) not in {
            ("stable", "stable_closed"),
            ("alpha_only", "alpha_closed"),
        }:
            raise CampaignDagError(f"theorem {name!r} conflates Stable and Alpha proof authority")
        for field in ("statement_sha256", "script_sha256", "logical_spec_sha256"):
            value = row.get(field)
            if type(value) is not str or DIGEST.fullmatch(value) is None:
                raise CampaignDagError(f"checked theorem {name!r} has an invalid {field}")
        statement = row.get("statement")
        if type(statement) is not str or not statement:
            raise CampaignDagError(f"checked theorem {name!r} has no exact statement")
        if sha256(statement.encode("utf-8")).hexdigest() != row["statement_sha256"]:
            raise CampaignDagError(f"checked theorem {name!r} changed its sealed statement")
        script = row.get("script")
        if type(script) is not list or not script or any(type(line) is not str or not line for line in script):
            raise CampaignDagError(f"checked theorem {name!r} has no exact proof script")
        if sha256(("\n".join(script) + "\n").encode("utf-8")).hexdigest() != row["script_sha256"]:
            raise CampaignDagError(f"checked theorem {name!r} changed its sealed proof script")
        dependencies = row.get("dependencies")
        if type(dependencies) is not list:
            raise CampaignDagError(f"checked theorem {name!r} has invalid proof dependencies")
        direct: set[str] = set()
        for dependency in dependencies:
            dependency = _name(dependency, context=f"checked theorem {name!r} proof dependency")
            if dependency in direct:
                raise CampaignDagError(f"checked theorem {name!r} repeats a proof dependency")
            if dependency not in known:
                raise CampaignDagError(
                    f"checked theorem {name!r} has a missing, forward, or circular proof dependency"
                )
            direct.add(dependency)
        theorem_projection.append({"name": name, "dependencies": dependencies})
        theorem_edge_count += len(dependencies)
        known.add(name)
        theorem_membership[name] = membership
    if (
        _count(catalog.get("edge_count"), context="Alpha theorem proof-edge count")
        != theorem_edge_count
        or _count(release.get("dependency_edge_count"), context="sealed Alpha proof-edge count")
        != theorem_edge_count
        or _count(
            release.get("checked_dependency_edge_count"), context="sealed Alpha checked proof-edge count"
        )
        != theorem_edge_count
    ):
        raise CampaignDagError("current Alpha theorem proof-edge count disagrees with the actual DAG")

    milestone_projection, milestone_edges = _milestone_dag(campaign)
    _milestone_authority(campaign, theorem_membership=theorem_membership)
    graph = build_definition_graph(campaign) if definition_graph is None else definition_graph
    (
        definitions,
        reviewed,
        definition_edges,
        reviewed_edges,
        usage_edges,
        statement_edges,
        declared_edges,
    ) = _definition_dags(campaign, graph)
    return CampaignDagAudit(
        alpha_version=version,
        catalog_sha256=catalog_sha256,
        theorem_count=len(theorem_projection),
        theorem_edge_count=theorem_edge_count,
        theorem_dag_sha256=_projection_digest(theorem_projection),
        milestone_count=len(milestone_projection),
        milestone_proof_edge_count=milestone_edges,
        milestone_dag_sha256=_projection_digest(milestone_projection),
        definition_count=len(definitions),
        definition_edge_count=definition_edges,
        definition_dag_sha256=_projection_digest(definitions),
        reviewed_definition_count=len(reviewed),
        reviewed_definition_edge_count=reviewed_edges,
        reviewed_definition_dag_sha256=_projection_digest(reviewed),
        milestone_usage_edge_count=usage_edges,
        statement_usage_edge_count=statement_edges,
        declared_notation_edge_count=declared_edges,
        campaign_snapshot_sha256=_digest(campaign),
    )


def _artifacts() -> tuple[str, bytes, CampaignDagAudit]:
    document, _campaign_sha256 = _load_document(
        CAMPAIGN,
        maximum=MAX_CAMPAIGN_BYTES,
        context="constructive grand-campaign source",
    )
    if type(document) is not dict or document.get("schema") != "constructive-grand-campaign-v1":
        raise ValueError("grand-campaign JSON has an invalid schema")
    payload = json.dumps(document, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    if "</script" in payload.lower():
        raise ValueError("grand-campaign JSON cannot contain a closing script element")
    graph = build_definition_graph(document)
    audit = validate_campaign_dags(document, definition_graph=graph)
    artifact = (
        json.dumps(
            graph,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    return payload, artifact, audit


def _expected(source: str, snapshot: str) -> tuple[str, str]:
    start = source.find(OPENING)
    if start < 0 or source.find(OPENING, start + len(OPENING)) >= 0:
        raise ValueError("grand-campaign explorer needs exactly one embedded JSON snapshot")
    start += len(OPENING)
    finish = source.find(CLOSING, start)
    if finish < 0:
        raise ValueError("grand-campaign explorer has an unterminated JSON snapshot")
    return source[start:finish], source[:start] + snapshot + source[finish:]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without rewriting HTML")
    parser.add_argument(
        "--json",
        action="store_true",
        help="print exact separate checked-theorem, milestone, and definition DAG identities",
    )
    arguments = parser.parse_args()
    try:
        snapshot, graph, audit = _artifacts()
        source = EXPLORER.read_text(encoding="utf-8")
        observed, expected = _expected(source, snapshot)
        graph_current = DEFINITION_GRAPH.is_file() and DEFINITION_GRAPH.read_bytes() == graph
        if observed == snapshot and graph_current:
            if arguments.json:
                print(json.dumps(asdict(audit), ensure_ascii=False, sort_keys=True))
            else:
                print(
                    "Constructive grand-campaign embedded snapshot verified; definition DAG verified; "
                    f"checked-theorem DAG verified ({audit.theorem_count:,} theorems, "
                    f"{audit.theorem_edge_count:,} proof edges); "
                    f"milestone DAG verified ({audit.milestone_count:,} nodes, "
                    f"{audit.milestone_proof_edge_count:,} proof edges)"
                )
            return 0
        if arguments.check:
            stale = []
            if observed != snapshot:
                stale.append("embedded snapshot")
            if not graph_current:
                stale.append("definition DAG")
            print("Constructive grand-campaign " + " and ".join(stale) + " is stale")
            return 1
        if observed != snapshot:
            EXPLORER.write_text(expected, encoding="utf-8")
        if not graph_current:
            DEFINITION_GRAPH.write_bytes(graph)
        if arguments.json:
            print(json.dumps(asdict(audit), ensure_ascii=False, sort_keys=True))
        else:
            print(
                "Constructive grand-campaign embedded snapshot and definition DAG updated; "
                f"checked-theorem DAG verified ({audit.theorem_count:,} theorems, "
                f"{audit.theorem_edge_count:,} proof edges)"
            )
        return 0
    except (OSError, UnicodeError, ValueError, DefinitionGraphError) as error:
        print(f"Cannot synchronize constructive grand-campaign snapshot: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
