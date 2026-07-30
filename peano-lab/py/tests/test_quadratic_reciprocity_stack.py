"""Static audit for the production-neutral quadratic-reciprocity stack."""

from __future__ import annotations

import ast
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from types import MappingProxyType

import pytest

from peano_lab.library.quadratic_reciprocity_stack import (
    QR_CANDIDATE_FACTORY_MANIFEST,
    QR_FINAL_DIRECT_DEPENDENCIES,
    QR_ROOT_NAME,
    _assemble_quadratic_reciprocity_stack,
    build_quadratic_reciprocity_stack,
)
from peano_lab.library.quadratic_reciprocity_stack_runtime import (
    build_quadratic_reciprocity_stack as build_runtime_stack,
    quadratic_reciprocity_stack,
)
from peano_lab.library.quadratic_residue_surface import (
    QUADRATIC_RECIPROCITY_COMBINED,
)
from peano_lab.library.theorems import TheoremSpec, _specs_by_name


EXPECTED_FACTORY_COUNT = 84
EXPECTED_FACTORY_OUTPUT_COUNT = 346
EXPECTED_CANDIDATE_ANCESTOR_COUNT = 317
EXPECTED_PUBLIC_ANCESTOR_COUNT = 240
EXPECTED_TOTAL_GRAPH_COUNT = 557
EXPECTED_DEPENDENCY_LAYER_COUNT = 45
EXPECTED_GRAPH_SHA256 = (
    "2b31288720415a10ac954916dc48144c6c6d2333fb551e5e4daac382cd9bbc39"
)
EXPECTED_SOURCE_SHA256 = (
    "141bfb8db2b7267c27e0254b2edde24d633c8d6d75f49ffdc35d46e732ad58b5"
)
EXPECTED_FINAL_SURFACE_SHA256 = (
    "2a95f83a5a21a5e21e482d5de8a19d55ee1843f676f086438f8a9853b6a97070"
)
EXPECTED_LAYER_PROFILE_SHA256 = (
    "b1cb69926bf5e2b7044fd27dd9795c667925b171261cb44af7794798a878d33f"
)


def _spec(
    name: str, dependencies: tuple[str, ...] = ()
) -> TheoremSpec:
    return TheoremSpec(name, "0 = 0", dependencies, ("refl",), "test")


def test_qr_stack_manifest_is_explicit_exact_and_includes_singular_reindex() -> None:
    source = Path(
        build_quadratic_reciprocity_stack.__code__.co_filename
    ).resolve()
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    imported_candidate_modules = tuple(
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.level == 1
        and node.module is not None
        and node.module.endswith("_candidate")
    )
    manifest_modules = tuple(
        entry.module_name for entry in QR_CANDIDATE_FACTORY_MANIFEST
    )
    manifest_keys = tuple(
        (entry.module_name, entry.factory_name)
        for entry in QR_CANDIDATE_FACTORY_MANIFEST
    )

    assert len(QR_CANDIDATE_FACTORY_MANIFEST) == EXPECTED_FACTORY_COUNT
    assert manifest_keys == tuple(sorted(manifest_keys))
    assert len(set(manifest_keys)) == len(manifest_keys)
    assert imported_candidate_modules == manifest_modules
    assert manifest_keys.count(
        (
            "finite_product_reindex_candidate",
            "make_finite_product_reindex_candidate",
        )
    ) == 1


def test_qr_stack_pins_exact_ancestors_hashes_surface_and_topology() -> None:
    public = _specs_by_name()
    first = quadratic_reciprocity_stack()
    second = build_quadratic_reciprocity_stack(
        spec_type=TheoremSpec,
        public_by_name=MappingProxyType(dict(public)),
    )
    third = build_runtime_stack()

    assert len(first.all_candidates) == EXPECTED_FACTORY_OUTPUT_COUNT
    assert len(first.all_candidate_by_name) == EXPECTED_FACTORY_OUTPUT_COUNT
    assert len(first.candidate_by_name) == EXPECTED_CANDIDATE_ANCESTOR_COUNT
    assert len(first.candidate_order) == EXPECTED_CANDIDATE_ANCESTOR_COUNT
    assert len(first.public_order) == EXPECTED_PUBLIC_ANCESTOR_COUNT
    assert len(first.combined_order) == EXPECTED_TOTAL_GRAPH_COUNT
    assert len(first.admission_order) == EXPECTED_TOTAL_GRAPH_COUNT
    assert len(first.dependency_depth_by_name) == EXPECTED_TOTAL_GRAPH_COUNT
    assert len(first.dependency_layers) == EXPECTED_DEPENDENCY_LAYER_COUNT
    assert first == second == third
    assert first.graph_sha256 == EXPECTED_GRAPH_SHA256
    assert first.source_sha256 == EXPECTED_SOURCE_SHA256
    assert first.source_rows == second.source_rows
    assert len(first.source_rows) == EXPECTED_FACTORY_COUNT

    assert first.admission_order == first.public_order + first.candidate_order
    positions = {
        spec.name: index for index, spec in enumerate(first.admission_order)
    }
    for spec in first.admission_order:
        assert all(
            positions[dependency] < positions[spec.name]
            for dependency in spec.dependencies
        )
        assert all(
            first.dependency_depth_by_name[dependency]
            < first.dependency_depth_by_name[spec.name]
            for dependency in spec.dependencies
        )
    layered_specs = tuple(
        spec for layer in first.dependency_layers for spec in layer
    )
    assert len(layered_specs) == len(set(spec.name for spec in layered_specs))
    assert set(layered_specs) == set(first.admission_order)
    for depth, layer in enumerate(first.dependency_layers):
        assert layer
        assert all(first.dependency_depth_by_name[spec.name] == depth for spec in layer)
    layer_profile = ",".join(
        str(len(layer)) for layer in first.dependency_layers
    )
    assert sha256(layer_profile.encode()).hexdigest() == (
        EXPECTED_LAYER_PROFILE_SHA256
    )
    assert all(spec.name in public for spec in first.public_order)
    assert all(spec.name not in public for spec in first.candidate_order)
    assert len(first.all_candidates) - len(first.candidate_order) == 29

    root = first.candidate_by_name[QR_ROOT_NAME]
    assert first.candidate_order[-1] == root
    assert root.statement == QUADRATIC_RECIPROCITY_COMBINED
    assert len(root.statement) == 1_520
    assert sha256(root.statement.encode()).hexdigest() == (
        EXPECTED_FINAL_SURFACE_SHA256
    )
    assert root.dependencies == QR_FINAL_DIRECT_DEPENDENCIES
    assert first.dependency_depth_by_name[QR_ROOT_NAME] == (
        EXPECTED_DEPENDENCY_LAYER_COUNT - 1
    )


def test_qr_stack_rejects_duplicate_conflicting_unknown_and_cyclic_specs() -> None:
    root = _spec("root")
    with pytest.raises(ValueError, match="duplicate QR candidate theorem 'root'"):
        _assemble_quadratic_reciprocity_stack(
            all_candidates=(root, root),
            owner_by_name={"root": "candidate"},
            source_rows=(),
            public_by_name={},
            root_name="root",
        )

    with pytest.raises(ValueError, match="conflict with public"):
        _assemble_quadratic_reciprocity_stack(
            all_candidates=(root,),
            owner_by_name={"root": "candidate"},
            source_rows=(),
            public_by_name={"root": root},
            root_name="root",
        )

    unknown = _spec("root", ("missing",))
    with pytest.raises(ValueError, match="unknown QR dependency 'missing'"):
        _assemble_quadratic_reciprocity_stack(
            all_candidates=(unknown,),
            owner_by_name={"root": "candidate"},
            source_rows=(),
            public_by_name={},
            root_name="root",
        )

    cyclic = _spec("root", ("root",))
    with pytest.raises(ValueError, match="cycle in QR dependency graph"):
        _assemble_quadratic_reciprocity_stack(
            all_candidates=(cyclic,),
            owner_by_name={"root": "candidate"},
            source_rows=(),
            public_by_name={},
            root_name="root",
        )


def test_qr_stack_is_nonregistering_nonreplaying_and_immutable() -> None:
    public_before = dict(_specs_by_name())
    stack = build_runtime_stack()
    public_after = dict(_specs_by_name())
    source = Path(
        build_quadratic_reciprocity_stack.__code__.co_filename
    ).read_text(encoding="utf-8")
    runtime_source = Path(
        build_runtime_stack.__code__.co_filename
    ).read_text(encoding="utf-8")

    assert public_after == public_before
    assert QR_ROOT_NAME not in public_after
    assert "theorems" not in {
        node.module
        for node in ast.parse(source).body
        if isinstance(node, ast.ImportFrom)
    }
    assert "_specs_by_name" not in source
    assert "from .theorems import THEOREMS, TheoremSpec" in runtime_source
    for forbidden in (
        "apply_tactic(",
        "checked_final(",
        "replay(",
        "_THEOREMS",
        "Cut(",
    ):
        assert forbidden not in source
    with pytest.raises(TypeError):
        stack.all_candidate_by_name["fabricated"] = _spec("fabricated")
    with pytest.raises(TypeError):
        stack.candidate_by_name["fabricated"] = _spec("fabricated")
    with pytest.raises(TypeError):
        stack.owner_by_name["fabricated"] = "fabricated_candidate"
    with pytest.raises(TypeError):
        stack.dependency_depth_by_name["fabricated"] = 0


def test_qr_pure_builder_snapshots_explicit_public_input_and_rechecks_conflicts() -> None:
    public = dict(_specs_by_name())
    first = build_quadratic_reciprocity_stack(
        spec_type=TheoremSpec,
        public_by_name=public,
    )
    first_public_names = tuple(spec.name for spec in first.public_order)

    # Mutating the caller's dictionary after return cannot alter the stack.
    # A fresh build sees the changed snapshot and must perform conflict checks
    # again; the pure builder has no hidden registry or cache.
    public[QR_ROOT_NAME] = first.candidate_by_name[QR_ROOT_NAME]
    assert tuple(spec.name for spec in first.public_order) == first_public_names
    assert QR_ROOT_NAME not in first_public_names
    with pytest.raises(ValueError, match="conflict with public"):
        build_quadratic_reciprocity_stack(
            spec_type=TheoremSpec,
            public_by_name=public,
        )

    with pytest.raises(TypeError, match="spec_type"):
        build_quadratic_reciprocity_stack(
            spec_type="TheoremSpec",  # type: ignore[arg-type]
            public_by_name={},
        )
    with pytest.raises(TypeError, match="explicit theorem mapping"):
        build_quadratic_reciprocity_stack(
            spec_type=TheoremSpec,
            public_by_name=(),  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="has type object"):
        build_quadratic_reciprocity_stack(
            spec_type=TheoremSpec,
            public_by_name={"wrong": object()},  # type: ignore[dict-item]
        )
    with pytest.raises(ValueError, match="does not match specification name"):
        build_quadratic_reciprocity_stack(
            spec_type=TheoremSpec,
            public_by_name={"wrong": _spec("right")},
        )


def test_qr_runtime_accessor_cache_is_optional_and_deterministic() -> None:
    quadratic_reciprocity_stack.cache_clear()
    first = quadratic_reciprocity_stack()
    assert quadratic_reciprocity_stack() is first

    quadratic_reciprocity_stack.cache_clear()
    second = quadratic_reciprocity_stack()
    assert second is not first
    assert second == first


def _fresh_import_receipt(prefix: str) -> dict[str, object]:
    py_root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    existing_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        str(py_root)
        if not existing_path
        else str(py_root) + os.pathsep + existing_path
    )
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    common = """
import json
from peano_lab.library.quadratic_reciprocity_stack_runtime import quadratic_reciprocity_stack
from peano_lab.library.theorems import THEOREMS
stack = quadratic_reciprocity_stack()
print(json.dumps({
    "factories": len(stack.source_rows),
    "outputs": len(stack.all_candidates),
    "candidates": len(stack.candidate_order),
    "public_ancestors": len(stack.public_order),
    "graph": len(stack.combined_order),
    "layers": len(stack.dependency_layers),
    "graph_sha256": stack.graph_sha256,
    "source_sha256": stack.source_sha256,
    "registry_count": len(THEOREMS),
    "root_public": any(spec.name == "quadratic_reciprocity_combined" for spec in THEOREMS),
}, sort_keys=True))
"""
    result = subprocess.run(
        [sys.executable, "-c", prefix + common],
        cwd=py_root,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=55,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_qr_fresh_process_import_orders_are_identical_and_acyclic() -> None:
    stack_first = _fresh_import_receipt(
        """
import sys
import peano_lab.library.quadratic_reciprocity_stack
assert "peano_lab.library.theorems" not in sys.modules
"""
    )
    registry_first = _fresh_import_receipt(
        """
import peano_lab.library.theorems
import peano_lab.library.quadratic_reciprocity_stack
"""
    )
    candidate_first = _fresh_import_receipt(
        """
import sys
import peano_lab.library.quadratic_reciprocity_candidate
assert "peano_lab.library.theorems" not in sys.modules
import peano_lab.library.quadratic_reciprocity_stack
assert "peano_lab.library.theorems" not in sys.modules
"""
    )

    assert stack_first == registry_first == candidate_first
    assert stack_first == {
        "candidates": EXPECTED_CANDIDATE_ANCESTOR_COUNT,
        "factories": EXPECTED_FACTORY_COUNT,
        "graph": EXPECTED_TOTAL_GRAPH_COUNT,
        "graph_sha256": EXPECTED_GRAPH_SHA256,
        "layers": EXPECTED_DEPENDENCY_LAYER_COUNT,
        "outputs": EXPECTED_FACTORY_OUTPUT_COUNT,
        "public_ancestors": EXPECTED_PUBLIC_ANCESTOR_COUNT,
        "registry_count": len(_specs_by_name()),
        "root_public": False,
        "source_sha256": EXPECTED_SOURCE_SHA256,
    }
