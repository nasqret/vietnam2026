"""Static integration of the layered compiler with the shared QR stack API."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import pytest

from peano_lab.experimental.quadratic_reciprocity_layered import (
    attach_quadratic_reciprocity_bodies,
    quadratic_reciprocity_layered_blueprint,
)
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)
from peano_lab.library.gauss_signed_half_candidate import (
    make_gauss_signed_half_candidate_theorems,
)
from peano_lab.library.layered_replay import (
    LayeredReplayBundle,
    LayeredReplayNode,
)
from peano_lab.library.quadratic_reciprocity_stack import (
    QR_ROOT_NAME,
)
from peano_lab.library.quadratic_reciprocity_stack_runtime import (
    quadratic_reciprocity_stack,
)
from peano_lab.library.quadratic_residue_surface import (
    QUADRATIC_RECIPROCITY_COMBINED,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _specs_by_name,
)


def _unused_dependency_curried_edges(
    spec: TheoremSpec,
    public: dict[str, TheoremSpec],
) -> tuple[str, ...]:
    """Detect edges whose false contract still permits the checked body.

    Each replay leaves all dependencies as ordinary hypotheses; it neither
    closes a dependency nor constructs the full quadratic-reciprocity proof.
    This bounded audit distinguishes a genuinely live hypothesis from the
    historical redundant edge that passed ordinary dependency-curried replay.
    """

    replay_candidate_bodies((spec,), core=public)
    unused: list[str] = []
    for dependency in spec.dependencies:
        poisoned = dict(public)
        poisoned[dependency] = replace(
            public[dependency],
            statement="0 = 1",
        )
        try:
            replay_candidate_bodies((spec,), core=poisoned)
        except CandidateBodyError:
            continue
        unused.append(dependency)
    return tuple(unused)


def test_blueprint_uses_exact_shared_557_node_45_layer_qr_stack() -> None:
    stack = quadratic_reciprocity_stack()
    blueprint = quadratic_reciprocity_layered_blueprint()

    assert len(blueprint.names) == 557
    assert len(blueprint.layers) == 45
    assert max(map(len, blueprint.layers)) == 63
    assert max(map(len, blueprint.dependencies)) == 16
    assert blueprint.names[blueprint.root] == QR_ROOT_NAME
    assert blueprint.root == len(blueprint.names) - 1
    assert blueprint.targets[blueprint.root] == _closed_formula(
        QUADRATIC_RECIPROCITY_COMBINED
    )
    assert blueprint.graph_sha256 == stack.graph_sha256
    assert blueprint.source_sha256 == stack.source_sha256
    assert tuple(
        tuple(blueprint.names[node_id] for node_id in layer)
        for layer in blueprint.layers
    ) == tuple(tuple(spec.name for spec in layer) for layer in stack.dependency_layers)
    assert tuple(
        blueprint.dependencies[index] for index in range(len(blueprint.names))
    ) == tuple(
        tuple(
            blueprint.names.index(dependency)
            for dependency in spec.dependencies
        )
        for spec in stack.admission_order
    )


def test_blueprint_provenance_hashes_are_not_bodies_or_authority() -> None:
    blueprint = quadratic_reciprocity_layered_blueprint()

    assert len(blueprint.graph_sha256) == 64
    assert len(blueprint.source_sha256) == 64
    assert sha256(QUADRATIC_RECIPROCITY_COMBINED.encode()).hexdigest() == (
        "2a95f83a5a21a5e21e482d5de8a19d55ee1843f676f086438f8a9853b6a97070"
    )
    with pytest.raises(ValueError, match="must match the exact stack"):
        attach_quadratic_reciprocity_bodies(blueprint, {})

    bodies = {name: EqRefl(Zero()) for name in blueprint.names}
    bundle = attach_quadratic_reciprocity_bodies(blueprint, bodies)
    assert type(bundle) is LayeredReplayBundle
    assert len(bundle.nodes) == len(blueprint.names)
    assert all(type(node) is LayeredReplayNode for node in bundle.nodes)


def test_previous_wmi_reflection_failure_has_only_live_dependency_edges() -> None:
    blueprint = quadratic_reciprocity_layered_blueprint()
    public = dict(_specs_by_name())
    reflection = make_gauss_signed_half_candidate_theorems(TheoremSpec)[0]
    expected = (
        "add_assoc",
        "add_comm",
        "mul_succ_left",
        "mul_zero_left",
        "zero_add",
        "add_right_cancel",
    )

    assert reflection.name == "odd_upper_remainder_reflection"
    assert reflection.dependencies == expected
    reflection_id = blueprint.names.index(reflection.name)
    assert tuple(
        blueprint.names[dependency]
        for dependency in blueprint.dependencies[reflection_id]
    ) == expected
    assert _unused_dependency_curried_edges(reflection, public) == ()

    historical_failure = replace(
        reflection,
        dependencies=expected + ("add_succ_left",),
    )
    assert _unused_dependency_curried_edges(historical_failure, public) == (
        "add_succ_left",
    )
