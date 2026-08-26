"""WMI-only trust gate for the exact native quadratic-reciprocity closure.

The final three quadratic-reciprocity candidates are intentionally absent
from the public theorem registry.  This module assembles their complete
dependency closure from an explicit source/factory manifest, closes every
dependency with a kernel ``Cut``, and checks the exact combined public
surface.  Two cold passes provide deterministic discovery evidence.

The recursive tests in this file are WMI-only.  Laptop validation is limited
to collection and the two static manifest/graph tests; do not call
``_discovery_runs`` on a workstation.
"""

from __future__ import annotations

import gc
import os
import resource
from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Callable, Iterator

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Formula, Imp, parse_formula
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, ImpIntro, Proof
from peano_lab.kernel.terms import Zero
from peano_lab.library.quadratic_residue_surface import (
    QUADRATIC_RECIPROCITY_COMBINED,
)
from peano_lab.library.quadratic_reciprocity_stack import (
    QR_CANDIDATE_FACTORY_MANIFEST,
    QR_FINAL_DIRECT_DEPENDENCIES,
    QR_ROOT_NAME,
    QuadraticReciprocityStack,
)
from peano_lab.library.quadratic_reciprocity_stack_runtime import (
    build_quadratic_reciprocity_stack,
)
from peano_lab.library.theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
    replay,
)


ROOT_NAME = QR_ROOT_NAME
EXPECTED_FINAL_DIRECT_DEPENDENCIES = QR_FINAL_DIRECT_DEPENDENCIES
FACTORY_MANIFEST: tuple[tuple[str, str], ...] = tuple(
    (entry.module_name, entry.factory_name)
    for entry in QR_CANDIDATE_FACTORY_MANIFEST
)

EXPECTED_FACTORY_COUNT = 84
EXPECTED_FACTORY_OUTPUT_COUNT = 346
EXPECTED_CANDIDATE_ANCESTOR_COUNT = 316
EXPECTED_PUBLIC_ANCESTOR_COUNT = 241
EXPECTED_TOTAL_GRAPH_COUNT = 557

# Filled from the lightweight static audit.  Both cover theorem statements,
# scripts, ordered dependencies, and (for the latter) every isolated source.
EXPECTED_GRAPH_SHA256 = (
    "26017364ea943c4ed51a4a83f63ff0cd56b0de3686f0e0b458e7548ee84b1253"
)
EXPECTED_SOURCE_SHA256 = (
    "23fd18aaff26e2c6b428949c35ab3658252c9a4c6fd3b4825a6ccd547f454db1"
)

_SOURCE_ROOT = Path(__file__).resolve().parents[1] / "peano_lab" / "library"
_REGISTRY_SOURCE = _SOURCE_ROOT / "theorems.py"


_Manifest = QuadraticReciprocityStack


def _require_recursive_diagnostic_suite() -> None:
    if os.environ.get("PEANO_QR_SUITE") != (
        "quadratic-reciprocity-recursive-diagnostic"
    ):
        import pytest

        pytest.skip("recursive QR closure is a WMI-only diagnostic")


@dataclass(frozen=True)
class _Checked:
    formula: Formula
    certificate: Proof


@dataclass(frozen=True)
class _PassReceipt:
    duration_seconds: float
    peak_rss_kib: int
    peak_rss_growth_kib: int
    nodes: int
    depth: int
    objects: int
    edges: int
    reused: int
    cut_objects: int
    proof_sha256: str
    graph_sha256: str
    source_sha256: str


def _build_manifest() -> _Manifest:
    return build_quadratic_reciprocity_stack()


@lru_cache(maxsize=1)
def _manifest() -> _Manifest:
    return _build_manifest()


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk_unique(proof: Proof) -> Iterator[Proof]:
    pending = [proof]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        yield node
        pending.extend(_proof_children(node))


def _proof_dag_digest(proof: Proof) -> str:
    """Hash proof content bottom-up while charging shared objects once."""

    digests: dict[int, str] = {}
    pending: list[tuple[Proof, bool]] = [(proof, False)]
    while pending:
        node, expanded = pending.pop()
        identity = id(node)
        if identity in digests:
            continue
        children = _proof_children(node)
        if not expanded:
            pending.append((node, True))
            pending.extend(
                (child, False)
                for child in children
                if id(child) not in digests
            )
            continue
        payload = [type(node).__name__]
        for item in fields(node):
            value = getattr(node, item.name)
            payload.append(
                digests[id(value)] if isinstance(value, Proof) else repr(value)
            )
        digests[identity] = sha256("\x1f".join(payload).encode()).hexdigest()
    return digests[id(proof)]


def _fresh_replayer() -> tuple[_Manifest, TheoremSpec, Callable[[str], _Checked]]:
    manifest = _build_manifest()
    core = _specs_by_name()
    local = manifest.candidate_by_name
    root = local[ROOT_NAME]

    @lru_cache(maxsize=None)
    def run(name: str) -> _Checked:
        if name in core:
            checked = replay(name)
            return _Checked(checked.formula, checked.certificate)

        spec = local[name]
        formula = _closed_formula(spec.statement)
        target = formula
        dependency_specs = tuple(
            local.get(name) or core[name] for name in spec.dependencies
        )
        for dependency_spec in reversed(dependency_specs):
            target = Imp(_closed_formula(dependency_spec.statement), target)

        state = start(target)
        for dependency in spec.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in spec.script:
            tactic, args = _primitive(command)
            state = apply_tactic(state, tactic, args)
        certificate = checked_final(state, target)

        body = certificate
        for _ in spec.dependencies:
            assert type(body) is ImpIntro
            body = body.body
        for dependency in reversed(spec.dependencies):
            checked_dependency = run(dependency)
            body = Cut(
                checked_dependency.formula,
                formula,
                checked_dependency.certificate,
                body,
            )
        return _Checked(formula, body)

    return manifest, root, run


def _cold_closure() -> tuple[_Checked, _PassReceipt]:
    started = perf_counter()
    starting_peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    replay.cache_clear()
    _specs_by_name.cache_clear()
    manifest, _, run = _fresh_replayer()
    theorem = run(ROOT_NAME)

    assert theorem.formula == parse_formula(QUADRATIC_RECIPROCITY_COMBINED)
    assert check((), theorem.certificate, theorem.formula)
    unique_nodes = tuple(_walk_unique(theorem.certificate))
    assert not any(type(node) is DNE for node in unique_nodes)
    nodes, depth = proof_metrics(theorem.certificate)
    objects, edges, reused = proof_identity_metrics(theorem.certificate)
    assert objects == len(unique_nodes)
    proof_sha256 = _proof_dag_digest(theorem.certificate)
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    receipt = _PassReceipt(
        duration_seconds=perf_counter() - started,
        peak_rss_kib=peak_rss,
        peak_rss_growth_kib=max(0, peak_rss - starting_peak_rss),
        nodes=nodes,
        depth=depth,
        objects=objects,
        edges=edges,
        reused=reused,
        cut_objects=sum(type(node) is Cut for node in unique_nodes),
        proof_sha256=proof_sha256,
        graph_sha256=manifest.graph_sha256,
        source_sha256=manifest.source_sha256,
    )
    return theorem, receipt


@lru_cache(maxsize=1)
def _discovery_runs() -> tuple[_Checked, tuple[_PassReceipt, _PassReceipt]]:
    first_theorem, first_receipt = _cold_closure()
    del first_theorem
    replay.cache_clear()
    _specs_by_name.cache_clear()
    gc.collect()
    second_theorem, second_receipt = _cold_closure()
    assert (
        first_receipt.nodes,
        first_receipt.depth,
        first_receipt.objects,
        first_receipt.edges,
        first_receipt.reused,
        first_receipt.cut_objects,
        first_receipt.proof_sha256,
        first_receipt.graph_sha256,
        first_receipt.source_sha256,
    ) == (
        second_receipt.nodes,
        second_receipt.depth,
        second_receipt.objects,
        second_receipt.edges,
        second_receipt.reused,
        second_receipt.cut_objects,
        second_receipt.proof_sha256,
        second_receipt.graph_sha256,
        second_receipt.source_sha256,
    )
    return second_theorem, (first_receipt, second_receipt)


def _mutate_direct_cut(certificate: Proof, index: int) -> Proof:
    assert type(certificate) is Cut
    if index == 0:
        zero = Zero()
        return replace(
            certificate,
            proposition=Eq(zero, zero),
            lemma=EqRefl(zero),
        )
    return replace(
        certificate,
        body=_mutate_direct_cut(certificate.body, index - 1),
    )


def _receipt_json(receipt: _PassReceipt) -> dict[str, object]:
    limits = {
        "nodes": MAX_USE_CERTIFICATE_NODES,
        "depth": MAX_USE_PROOF_DEPTH,
        "objects": MAX_USE_CERTIFICATE_OBJECTS,
    }
    within = {
        "nodes": receipt.nodes <= limits["nodes"],
        "depth": receipt.depth <= limits["depth"],
        "objects": receipt.objects <= limits["objects"],
    }
    return {
        "duration_seconds": receipt.duration_seconds,
        "peak_rss_kib": receipt.peak_rss_kib,
        "peak_rss_growth_kib": receipt.peak_rss_growth_kib,
        "structural_nodes": receipt.nodes,
        "proof_depth": receipt.depth,
        "distinct_objects": receipt.objects,
        "distinct_object_edges": receipt.edges,
        "reused_object_references": receipt.reused,
        "distinct_cut_objects": receipt.cut_objects,
        "proof_dag_sha256": receipt.proof_sha256,
        "graph_sha256": receipt.graph_sha256,
        "source_sha256": receipt.source_sha256,
        "current_use_limits": limits,
        "within_current_use_limits": within,
        "within_current_use_policy": all(within.values()),
    }


@lru_cache(maxsize=1)
def _mutation_audit() -> dict[str, object]:
    theorem, _ = _discovery_runs()
    root = _manifest().candidate_by_name[ROOT_NAME]
    false_contract = parse_formula(f"({root.statement}) /\\ 0 = 1")
    assert false_contract != theorem.formula
    false_contract_rejected = not check(
        (), theorem.certificate, false_contract
    )
    direct_edges = []
    for index, dependency in enumerate(root.dependencies):
        mutated = _mutate_direct_cut(theorem.certificate, index)
        direct_edges.append(
            {
                "dependency": dependency,
                "cut_index": index,
                "rejected": not check((), mutated, theorem.formula),
            }
        )
    return {
        "false_contract_rejected": false_contract_rejected,
        "direct_dependency_cut_mutations": direct_edges,
        "all_mutations_rejected": false_contract_rejected
        and all(bool(row["rejected"]) for row in direct_edges),
    }


def _static_wmi_receipt_metadata() -> dict[str, object]:
    """Return source/graph evidence without constructing a recursive proof."""

    manifest = _manifest()
    return {
        "root": ROOT_NAME,
        "factory_count": len(FACTORY_MANIFEST),
        "factory_output_count": len(manifest.all_candidates),
        "candidate_ancestor_count": len(manifest.candidate_order),
        "public_ancestor_count": len(manifest.public_order),
        "total_graph_count": len(manifest.combined_order),
        "recursive_graph_names": [
            spec.name for _, spec in manifest.combined_order
        ],
        "recursive_graph_scopes": [
            scope for scope, _ in manifest.combined_order
        ],
        "candidate_graph_names": [spec.name for spec in manifest.candidate_order],
        "graph_sha256": manifest.graph_sha256,
        "source_sha256": manifest.source_sha256,
        "candidate_source_sha256": {
            module: digest for module, _, digest in manifest.source_rows
        },
        "candidate_sources": [
            {
                "module": module,
                "factory": factory,
                "sha256": digest,
            }
            for module, factory, digest in manifest.source_rows
        ],
    }


def wmi_receipt_metadata() -> dict[str, object]:
    """Expose recursive evidence only for the explicit diagnostic suite."""

    payload = _static_wmi_receipt_metadata()
    if os.environ.get("PEANO_QR_SUITE") != (
        "quadratic-reciprocity-recursive-diagnostic"
    ):
        return {
            **payload,
            "recursive_discovery_executed": False,
            "recursive_discovery_status": "not_selected",
        }

    if _discovery_runs.cache_info().currsize == 0:
        return {
            **payload,
            "recursive_discovery_executed": False,
            "recursive_discovery_status": "failed_before_receipt_cache",
        }
    _, passes = _discovery_runs()
    mutation_cached = _mutation_audit.cache_info().currsize != 0
    return {
        **payload,
        "recursive_discovery_executed": True,
        "recursive_discovery_status": "cached",
        "closure_passes": [
            {"pass_index": index, **_receipt_json(receipt)}
            for index, receipt in enumerate(passes, start=1)
        ],
        "mutation_audit_cached": mutation_cached,
        "mutation_audit": _mutation_audit() if mutation_cached else None,
    }


def test_quadratic_reciprocity_closure_manifest_is_exact_deterministic_and_source_isolated() -> None:
    first = _manifest()
    second = _build_manifest()
    assert len(FACTORY_MANIFEST) == EXPECTED_FACTORY_COUNT
    assert FACTORY_MANIFEST == tuple(sorted(FACTORY_MANIFEST))
    assert len(set(FACTORY_MANIFEST)) == len(FACTORY_MANIFEST)
    assert len(first.all_candidates) == EXPECTED_FACTORY_OUTPUT_COUNT
    assert first.all_candidates == second.all_candidates
    assert first.owner_by_name == second.owner_by_name
    assert first.source_rows == second.source_rows
    assert first.source_sha256 == second.source_sha256 == EXPECTED_SOURCE_SHA256

    registry_source = _REGISTRY_SOURCE.read_text(encoding="utf-8")
    core = _specs_by_name()
    assert all(spec.name not in core for spec in first.candidate_order)
    migrated_name = "bounded_mod_inverse_unique"
    migrated_owner = "wilson_inverse_point_candidate"
    assert first.all_candidate_by_name[migrated_name] == core[migrated_name]
    assert first.owner_by_name[migrated_name] == migrated_owner
    assert migrated_name not in first.candidate_by_name
    assert migrated_name in {spec.name for spec in first.public_order}
    assert {
        module_name
        for module_name, _ in FACTORY_MANIFEST
        if module_name in registry_source
    } == {migrated_owner}
    assert {
        first.owner_by_name[spec.name] for spec in first.candidate_order
    } == {module_name for module_name, _ in FACTORY_MANIFEST}


def test_quadratic_reciprocity_closure_graph_is_exact_acyclic_and_closed_over_dependencies() -> None:
    manifest = _manifest()
    core = _specs_by_name()
    assert len(manifest.candidate_order) == EXPECTED_CANDIDATE_ANCESTOR_COUNT
    assert len(manifest.public_order) == EXPECTED_PUBLIC_ANCESTOR_COUNT
    assert len(manifest.combined_order) == EXPECTED_TOTAL_GRAPH_COUNT
    assert manifest.graph_sha256 == EXPECTED_GRAPH_SHA256
    assert manifest.candidate_order[-1].name == ROOT_NAME
    assert manifest.candidate_by_name[ROOT_NAME].statement == (
        QUADRATIC_RECIPROCITY_COMBINED
    )
    assert manifest.candidate_by_name[ROOT_NAME].dependencies == (
        EXPECTED_FINAL_DIRECT_DEPENDENCIES
    )

    positions = {
        (scope, spec.name): index
        for index, (scope, spec) in enumerate(manifest.combined_order)
    }
    for scope, spec in manifest.combined_order:
        assert _closed_formula(spec.statement) == parse_formula(spec.statement)
        assert all(
            fragment not in command
            for command in spec.script
            for fragment in ("DNE", "by_contra", "classical", "sorry")
        )
        for dependency in spec.dependencies:
            dependency_key = (
                ("candidate", dependency)
                if dependency in manifest.candidate_by_name
                and dependency not in core
                else ("public", dependency)
            )
            assert dependency_key in positions
            assert positions[dependency_key] < positions[(scope, spec.name)]


def test_quadratic_reciprocity_full_recursive_cut_closure_replays_twice_deterministically() -> None:
    _require_recursive_diagnostic_suite()
    theorem, passes = _discovery_runs()
    assert theorem.formula == parse_formula(QUADRATIC_RECIPROCITY_COMBINED)
    for index, receipt in enumerate(passes, start=1):
        metadata = _receipt_json(receipt)
        print(
            "WMI QUADRATIC RECIPROCITY FULL CLOSURE RECEIPT "
            f"pass={index} duration_seconds={receipt.duration_seconds:.6f} "
            f"peak_rss_kib={receipt.peak_rss_kib} "
            f"peak_rss_growth_kib={receipt.peak_rss_growth_kib} "
            f"nodes={receipt.nodes} depth={receipt.depth} "
            f"objects={receipt.objects} edges={receipt.edges} "
            f"reused={receipt.reused} cut_objects={receipt.cut_objects} "
            f"proof_dag_sha256={receipt.proof_sha256} "
            f"graph_sha256={receipt.graph_sha256} "
            f"source_sha256={receipt.source_sha256} "
            f"within_current_use_policy={metadata['within_current_use_policy']}",
            flush=True,
        )


def test_quadratic_reciprocity_full_closure_rejects_false_contract_and_every_direct_dependency_cut_mutation() -> None:
    _require_recursive_diagnostic_suite()
    audit = _mutation_audit()
    assert audit["false_contract_rejected"]
    rows = audit["direct_dependency_cut_mutations"]
    assert isinstance(rows, list)
    assert [row["dependency"] for row in rows] == list(
        EXPECTED_FINAL_DIRECT_DEPENDENCIES
    )
    assert all(bool(row["rejected"]) for row in rows)
    assert audit["all_mutations_rejected"]


def test_quadratic_reciprocity_full_closure_meets_current_use_capacity_policy() -> None:
    _require_recursive_diagnostic_suite()
    _, passes = _discovery_runs()
    latest = _receipt_json(passes[-1])
    assert latest["within_current_use_policy"], (
        "the exact native QR closure is kernel-valid but exceeds the unchanged "
        f"use policy: {latest}"
    )
