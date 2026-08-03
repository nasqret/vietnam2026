"""Thin QR-stack adapter for the production-neutral layered replay builder.

The reviewed production-neutral stack remains the single source of dependency
metadata.  This module only assigns bundle-local integer IDs and parses exact
targets.  Human theorem names and provenance hashes are not part of the
resulting ``LayeredReplayBundle`` and grant no proof authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..kernel.formulas import Formula
from ..kernel.proofs import Proof
from ..library.layered_replay import LayeredReplayBundle, LayeredReplayNode
from ..library.quadratic_reciprocity_stack import (
    QR_ROOT_NAME,
)
from ..library.quadratic_reciprocity_stack_runtime import (
    quadratic_reciprocity_stack,
)
from ..library.theorems import _closed_formula


@dataclass(frozen=True, slots=True)
class QuadraticReciprocityLayeredBlueprint:
    """Untrusted deterministic local-ID view of the reviewed QR stack."""

    names: tuple[str, ...]
    targets: tuple[Formula, ...]
    dependencies: tuple[tuple[int, ...], ...]
    layers: tuple[tuple[int, ...], ...]
    root: int
    graph_sha256: str
    source_sha256: str


def quadratic_reciprocity_layered_blueprint(
) -> QuadraticReciprocityLayeredBlueprint:
    """Derive local IDs directly from ``QuadraticReciprocityStack`` metadata."""

    stack = quadratic_reciprocity_stack()
    names = tuple(spec.name for spec in stack.admission_order)
    positions = {name: index for index, name in enumerate(names)}
    if len(positions) != len(names) or QR_ROOT_NAME not in positions:
        raise ValueError("QR stack does not have unique names and its exact root")
    targets = tuple(_closed_formula(spec.statement) for spec in stack.admission_order)
    dependencies = tuple(
        tuple(positions[dependency] for dependency in spec.dependencies)
        for spec in stack.admission_order
    )
    layers = tuple(
        tuple(positions[spec.name] for spec in layer)
        for layer in stack.dependency_layers
    )
    flattened = tuple(node_id for layer in layers for node_id in layer)
    if len(flattened) != len(names) or set(flattened) != set(range(len(names))):
        raise ValueError("QR stack layers are not an exact partition")
    for layer_index, layer in enumerate(layers):
        for node_id in layer:
            if stack.dependency_depth_by_name[names[node_id]] != layer_index:
                raise ValueError("QR stack depth and layer metadata disagree")
            if any(
                stack.dependency_depth_by_name[names[dependency]] >= layer_index
                for dependency in dependencies[node_id]
            ):
                raise ValueError("QR stack dependency does not precede its layer")
    return QuadraticReciprocityLayeredBlueprint(
        names=names,
        targets=targets,
        dependencies=dependencies,
        layers=layers,
        root=positions[QR_ROOT_NAME],
        graph_sha256=stack.graph_sha256,
        source_sha256=stack.source_sha256,
    )


def attach_quadratic_reciprocity_bodies(
    blueprint: QuadraticReciprocityLayeredBlueprint,
    bodies_by_name: Mapping[str, Proof],
) -> LayeredReplayBundle:
    """Attach ordinary modular bodies and discard every human-readable name.

    The result is still untrusted compiler input.  The layered certificate has
    authority only after the unchanged kernel checks the final ordinary proof.
    """

    if type(blueprint) is not QuadraticReciprocityLayeredBlueprint:
        raise TypeError("expected an exact QR layered blueprint")
    if not isinstance(bodies_by_name, Mapping):
        raise TypeError("QR modular bodies must be a name-to-Proof mapping")
    keys = set(bodies_by_name)
    expected = set(blueprint.names)
    if keys != expected:
        missing = sorted(expected - keys)
        extra = sorted(keys - expected)
        raise ValueError(
            "QR body mapping must match the exact stack; "
            f"missing={missing[:3]!r}, extra={extra[:3]!r}"
        )
    nodes: list[LayeredReplayNode] = []
    for node_id, name in enumerate(blueprint.names):
        body = bodies_by_name[name]
        if not isinstance(body, Proof):
            raise TypeError(f"QR body {name!r} is not an ordinary Proof")
        nodes.append(
            LayeredReplayNode(
                node_id,
                blueprint.targets[node_id],
                blueprint.dependencies[node_id],
                body,
            )
        )
    return LayeredReplayBundle(tuple(nodes), blueprint.root)


__all__ = [
    "QuadraticReciprocityLayeredBlueprint",
    "quadratic_reciprocity_layered_blueprint",
    "attach_quadratic_reciprocity_bodies",
]
