"""WMI-only full layered admission experiment for native quadratic reciprocity.

Laptop execution is limited to the three static/synthetic tests.  The body
replay, two cold compiles, unchanged-kernel checks, mutations, and capacity
gate are selected only by the dedicated WMI runner suite.
"""

from __future__ import annotations

import ast
from copy import deepcopy
import gc
import os
import resource
from dataclasses import dataclass, fields, replace
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from peano_lab.engine.state import proof_identity_metrics, proof_metrics, start
from peano_lab.engine.tactics import (
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from peano_lab.experimental.quadratic_reciprocity_layered import (
    QuadraticReciprocityLayeredBlueprint,
    attach_quadratic_reciprocity_bodies,
    quadratic_reciprocity_layered_blueprint,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Eq, Formula, Imp
from peano_lab.kernel.proofs import Cut, DNE, EqRefl, Hyp, ImpIntro, Proof
from peano_lab.kernel.terms import Add, Mul, Succ, Zero
from peano_lab.library.quadratic_reciprocity_stack import (
    QR_ROOT_NAME,
)
from peano_lab.library.layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayCandidate,
    LayeredReplayNode,
    compile_layered_replay,
)
from peano_lab.library.quadratic_reciprocity_stack_runtime import (
    quadratic_reciprocity_stack,
)
from peano_lab.library.quadratic_residue_surface import (
    QUADRATIC_RECIPROCITY_COMBINED,
)
from peano_lab.library.theorems import (
    _closed_formula,
    _primitive,
    _specs_by_name,
)


EXPECTED_NODE_COUNT = 557
EXPECTED_LAYER_COUNT = 45
EXPECTED_GRAPH_SHA256 = (
    "98a36450cfe1de29c20be67a1c5f65c8064e9f9eec5368ab769065f910008698"
)
EXPECTED_SOURCE_SHA256 = (
    "23fd18aaff26e2c6b428949c35ab3658252c9a4c6fd3b4825a6ccd547f454db1"
)
EXPECTED_SURFACE_SHA256 = (
    "2a95f83a5a21a5e21e482d5de8a19d55ee1843f676f086438f8a9853b6a97070"
)


@dataclass(frozen=True)
class _BodyReceipt:
    body_count: int
    script_command_count: int
    proof_occurrences: int
    proof_objects: int
    maximum_proof_depth: int
    body_sha256: str


@dataclass(frozen=True)
class _PassReceipt:
    wall_time_seconds: float
    body_build_seconds: float
    compile_seconds: float
    kernel_check_seconds: float
    peak_rss_kib: int
    peak_rss_growth_kib: int
    body: _BodyReceipt
    proof_nodes: int
    proof_depth: int
    proof_objects: int
    proof_edges: int
    reused_objects: int
    proof_annotation_occurrences: int
    proof_envelope_depth: int
    package_formula_occurrences: int
    maximum_package_formula_depth: int
    layer_count: int
    layer_profile_sha256: str
    package_formula_sha256: str
    proof_dag_sha256: str
    graph_sha256: str
    source_sha256: str
    dne_objects: int
    kernel_accepted: bool


@dataclass(frozen=True)
class _Outcome:
    blueprint: QuadraticReciprocityLayeredBlueprint
    bundle: LayeredReplayBundle
    compilation: LayeredReplayCandidate
    target: Formula


_PARTIAL_DISCOVERY_RECEIPT: dict[str, object] = {
    "status": "not_started",
    "phase": "not_started",
    "error": None,
    "passes": [],
}


def _reset_partial_discovery_receipt() -> None:
    global _PARTIAL_DISCOVERY_RECEIPT
    _PARTIAL_DISCOVERY_RECEIPT = {
        "status": "running",
        "phase": "first_pass",
        "error": None,
        "passes": [],
    }


def _begin_partial_pass(pass_index: int, peak_rss_kib: int) -> None:
    passes = _PARTIAL_DISCOVERY_RECEIPT["passes"]
    if not isinstance(passes, list) or len(passes) != pass_index - 1:
        raise AssertionError("layered QR partial receipt pass order is invalid")
    passes.append(
        {
            "pass_index": pass_index,
            "status": "running",
            "phase": "body_build",
            "error": None,
            "wall_time_seconds": 0.0,
            "peak_rss_kib": peak_rss_kib,
            "peak_rss_growth_kib": 0,
            "body_build_seconds": None,
            "compile_seconds": None,
            "kernel_check_seconds": None,
            "body": None,
            "compilation": None,
            "kernel_accepted": None,
        }
    )


def _update_partial_pass(pass_index: int, **updates: object) -> None:
    passes = _PARTIAL_DISCOVERY_RECEIPT["passes"]
    if not isinstance(passes, list) or len(passes) < pass_index:
        raise AssertionError("layered QR partial receipt pass is missing")
    row = passes[pass_index - 1]
    if not isinstance(row, dict) or row.get("pass_index") != pass_index:
        raise AssertionError("layered QR partial receipt pass identity changed")
    row.update(updates)


def _partial_discovery_snapshot() -> dict[str, object]:
    return deepcopy(_PARTIAL_DISCOVERY_RECEIPT)


def _require_wmi_heavy_suite() -> None:
    if os.environ.get("PEANO_QR_SUITE") not in {
        "full",
        "quadratic-reciprocity-layered",
    }:
        import pytest

        pytest.skip("full layered QR replay is WMI-only")


def _proof_children(proof: Proof) -> tuple[Proof, ...]:
    return tuple(
        child
        for item in fields(proof)
        if isinstance((child := getattr(proof, item.name)), Proof)
    )


def _walk_unique(proof: Proof):
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


def _build_dependency_curried_bodies(
    blueprint: QuadraticReciprocityLayeredBlueprint,
) -> tuple[dict[str, Proof], _BodyReceipt]:
    stack = quadratic_reciprocity_stack()
    if tuple(spec.name for spec in stack.admission_order) != blueprint.names:
        raise AssertionError("QR blueprint and admission stack names disagree")

    bodies: dict[str, Proof] = {}
    receipt_rows: list[str] = []
    total_commands = 0
    total_occurrences = 0
    total_objects = 0
    maximum_depth = 0
    for node_id, spec in enumerate(stack.admission_order):
        if spec.name in bodies:
            raise AssertionError(f"duplicate body replay for {spec.name!r}")
        target = blueprint.targets[node_id]
        for dependency_id in reversed(blueprint.dependencies[node_id]):
            target = Imp(blueprint.targets[dependency_id], target)
        state = start(target)
        for dependency in spec.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in spec.script:
            tactic, args = _primitive(command)
            if tactic == "use":
                raise AssertionError(
                    f"{spec.name!r} delegates proof authority through use"
                )
            state = apply_tactic(state, tactic, args)
        body = checked_final(state, target)
        bodies[spec.name] = body
        occurrences, depth = proof_metrics(body)
        objects, _edges, _reused = proof_identity_metrics(body)
        total_commands += len(spec.script)
        total_occurrences += occurrences
        total_objects += objects
        maximum_depth = max(maximum_depth, depth)
        receipt_rows.append(
            "\x1f".join(
                (
                    spec.name,
                    str(len(spec.dependencies)),
                    str(len(spec.script)),
                    str(occurrences),
                    str(depth),
                    str(objects),
                    _proof_dag_digest(body),
                )
            )
        )
    if len(bodies) != len(blueprint.names):
        raise AssertionError("QR body replay did not cover the exact blueprint")
    return bodies, _BodyReceipt(
        body_count=len(bodies),
        script_command_count=total_commands,
        proof_occurrences=total_occurrences,
        proof_objects=total_objects,
        maximum_proof_depth=maximum_depth,
        body_sha256=sha256("\x1c".join(receipt_rows).encode()).hexdigest(),
    )


def _cold_layered_admission(
    pass_index: int,
) -> tuple[_Outcome, _PassReceipt]:
    started = perf_counter()
    starting_peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    _begin_partial_pass(pass_index, starting_peak_rss)
    _PARTIAL_DISCOVERY_RECEIPT["phase"] = f"pass_{pass_index}_body_build"
    phase = "body_build"
    body_started: float | None = None
    compile_started: float | None = None
    check_started: float | None = None
    try:
        quadratic_reciprocity_stack.cache_clear()
        _specs_by_name.cache_clear()

        blueprint = quadratic_reciprocity_layered_blueprint()
        target = _closed_formula(QUADRATIC_RECIPROCITY_COMBINED)
        if blueprint.targets[blueprint.root] != target:
            raise AssertionError(
                "QR blueprint root does not match the exact surface"
            )

        body_started = perf_counter()
        bodies, body_receipt = _build_dependency_curried_bodies(blueprint)
        body_build_seconds = perf_counter() - body_started
        _update_partial_pass(
            pass_index,
            phase="compile",
            body_build_seconds=body_build_seconds,
            body={
                "body_count": body_receipt.body_count,
                "script_command_count": body_receipt.script_command_count,
                "proof_occurrences": body_receipt.proof_occurrences,
                "proof_objects": body_receipt.proof_objects,
                "maximum_proof_depth": body_receipt.maximum_proof_depth,
                "body_sha256": body_receipt.body_sha256,
            },
        )
        phase = "compile"
        _PARTIAL_DISCOVERY_RECEIPT["phase"] = f"pass_{pass_index}_compile"
        bundle = attach_quadratic_reciprocity_bodies(blueprint, bodies)
        del bodies

        compile_started = perf_counter()
        compilation = compile_layered_replay(
            bundle,
            target,
            limits=DEFAULT_LAYERED_REPLAY_LIMITS,
        )
        compile_seconds = perf_counter() - compile_started
        compilation_metrics = None
        if compilation is not None:
            compilation_metrics = {
                "proof_nodes": compilation.proof_nodes,
                "proof_depth": compilation.proof_depth,
                "proof_objects": compilation.proof_objects,
                "proof_edges": compilation.proof_edges,
                "reused_objects": compilation.reused_objects,
                "proof_annotation_occurrences": (
                    compilation.proof_annotation_occurrences
                ),
                "proof_envelope_depth": compilation.proof_envelope_depth,
                "package_formula_occurrences": (
                    compilation.package_formula_occurrences
                ),
                "maximum_package_formula_depth": (
                    compilation.maximum_package_formula_depth
                ),
                "layer_count": len(compilation.layers),
            }
        if compilation is None:
            _update_partial_pass(
                pass_index,
                compile_seconds=compile_seconds,
                compilation=None,
            )
            raise AssertionError(
                "layered QR compiler rejected the exact 557-node bundle"
            )

        _update_partial_pass(
            pass_index,
            phase="kernel_check",
            compile_seconds=compile_seconds,
            compilation=compilation_metrics,
        )
        phase = "kernel_check"
        _PARTIAL_DISCOVERY_RECEIPT["phase"] = (
            f"pass_{pass_index}_kernel_check"
        )
        check_started = perf_counter()
        kernel_accepted = check((), compilation.certificate, target)
        kernel_check_seconds = perf_counter() - check_started
        _update_partial_pass(
            pass_index,
            kernel_check_seconds=kernel_check_seconds,
            kernel_accepted=kernel_accepted,
        )
        if not kernel_accepted:
            raise AssertionError(
                "unchanged kernel rejected layered QR certificate"
            )

        phase = "receipt_finalize"
        _update_partial_pass(pass_index, phase=phase)
        _PARTIAL_DISCOVERY_RECEIPT["phase"] = (
            f"pass_{pass_index}_receipt_finalize"
        )
        unique_nodes = tuple(_walk_unique(compilation.certificate))
        proof_sha256 = _proof_dag_digest(compilation.certificate)
        package_sha256 = sha256(
            "\x1c".join(
                repr(item) for item in compilation.package_formulas
            ).encode()
        ).hexdigest()
        layer_profile_sha256 = sha256(
            ",".join(str(len(layer)) for layer in compilation.layers).encode()
        ).hexdigest()
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        receipt = _PassReceipt(
            wall_time_seconds=perf_counter() - started,
            body_build_seconds=body_build_seconds,
            compile_seconds=compile_seconds,
            kernel_check_seconds=kernel_check_seconds,
            peak_rss_kib=peak_rss,
            peak_rss_growth_kib=max(0, peak_rss - starting_peak_rss),
            body=body_receipt,
            proof_nodes=compilation.proof_nodes,
            proof_depth=compilation.proof_depth,
            proof_objects=compilation.proof_objects,
            proof_edges=compilation.proof_edges,
            reused_objects=compilation.reused_objects,
            proof_annotation_occurrences=(
                compilation.proof_annotation_occurrences
            ),
            proof_envelope_depth=compilation.proof_envelope_depth,
            package_formula_occurrences=(
                compilation.package_formula_occurrences
            ),
            maximum_package_formula_depth=(
                compilation.maximum_package_formula_depth
            ),
            layer_count=len(compilation.layers),
            layer_profile_sha256=layer_profile_sha256,
            package_formula_sha256=package_sha256,
            proof_dag_sha256=proof_sha256,
            graph_sha256=blueprint.graph_sha256,
            source_sha256=blueprint.source_sha256,
            dne_objects=sum(type(node) is DNE for node in unique_nodes),
            kernel_accepted=kernel_accepted,
        )
        _update_partial_pass(
            pass_index,
            status="passed",
            phase="complete",
            wall_time_seconds=receipt.wall_time_seconds,
            peak_rss_kib=receipt.peak_rss_kib,
            peak_rss_growth_kib=receipt.peak_rss_growth_kib,
        )
        return _Outcome(blueprint, bundle, compilation, target), receipt
    except BaseException as exc:
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        phase_metrics: dict[str, object] = {}
        if phase == "body_build" and body_started is not None:
            phase_metrics["body_build_seconds"] = perf_counter() - body_started
        elif phase == "compile" and compile_started is not None:
            phase_metrics["compile_seconds"] = perf_counter() - compile_started
        elif phase == "kernel_check" and check_started is not None:
            phase_metrics["kernel_check_seconds"] = (
                perf_counter() - check_started
            )
        _update_partial_pass(
            pass_index,
            status="failed",
            phase=phase,
            error=f"{type(exc).__name__}: {exc}",
            wall_time_seconds=perf_counter() - started,
            peak_rss_kib=peak_rss,
            peak_rss_growth_kib=max(0, peak_rss - starting_peak_rss),
            **phase_metrics,
        )
        _PARTIAL_DISCOVERY_RECEIPT["status"] = "failed"
        _PARTIAL_DISCOVERY_RECEIPT["error"] = (
            f"{type(exc).__name__}: {exc}"
        )
        raise


def _deterministic_payload(receipt: _PassReceipt) -> tuple[object, ...]:
    return (
        receipt.body,
        receipt.proof_nodes,
        receipt.proof_depth,
        receipt.proof_objects,
        receipt.proof_edges,
        receipt.reused_objects,
        receipt.proof_annotation_occurrences,
        receipt.proof_envelope_depth,
        receipt.package_formula_occurrences,
        receipt.maximum_package_formula_depth,
        receipt.layer_count,
        receipt.layer_profile_sha256,
        receipt.package_formula_sha256,
        receipt.proof_dag_sha256,
        receipt.graph_sha256,
        receipt.source_sha256,
        receipt.dne_objects,
        receipt.kernel_accepted,
    )


@lru_cache(maxsize=1)
def _discovery_runs() -> tuple[_Outcome, tuple[_PassReceipt, _PassReceipt]]:
    _reset_partial_discovery_receipt()
    try:
        first_outcome, first_receipt = _cold_layered_admission(1)
        del first_outcome
        quadratic_reciprocity_stack.cache_clear()
        _specs_by_name.cache_clear()
        gc.collect()
        _PARTIAL_DISCOVERY_RECEIPT["phase"] = "second_pass"
        second_outcome, second_receipt = _cold_layered_admission(2)
        _PARTIAL_DISCOVERY_RECEIPT["phase"] = "determinism_check"
        if _deterministic_payload(first_receipt) != _deterministic_payload(
            second_receipt
        ):
            raise AssertionError("cold layered QR passes are not deterministic")
    except BaseException as exc:
        _PARTIAL_DISCOVERY_RECEIPT["status"] = "failed"
        _PARTIAL_DISCOVERY_RECEIPT["error"] = (
            f"{type(exc).__name__}: {exc}"
        )
        raise
    _PARTIAL_DISCOVERY_RECEIPT["status"] = "passed"
    _PARTIAL_DISCOVERY_RECEIPT["phase"] = "complete"
    _PARTIAL_DISCOVERY_RECEIPT["error"] = None
    return second_outcome, (first_receipt, second_receipt)


def _swap_outer_layers(certificate: Proof, target: Formula) -> Proof:
    if type(certificate) is not Cut or type(certificate.body) is not Cut:
        raise AssertionError("layered QR certificate lacks two package Cuts")
    first = certificate
    second = certificate.body
    return Cut(
        second.proposition,
        target,
        second.lemma,
        Cut(first.proposition, target, first.lemma, second.body),
    )


@lru_cache(maxsize=1)
def _mutation_audit() -> dict[str, object]:
    started = perf_counter()
    starting_peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    outcome, _passes = _discovery_runs()
    certificate = outcome.compilation.certificate
    zero = Zero()
    one = Succ(zero)

    false_target = And(outcome.target, Eq(zero, one))
    false_target_rejected = not check((), certificate, false_target)

    if type(certificate) is not Cut:
        raise AssertionError("layered QR certificate has no package Cut")
    bad_package = replace(certificate, lemma=EqRefl(one))
    package_mutation_rejected = not check((), bad_package, outcome.target)

    swapped_layers = _swap_outer_layers(certificate, outcome.target)
    layer_order_mutation_rejected = not check(
        (), swapped_layers, outcome.target
    )

    first_node = outcome.bundle.nodes[0]
    cyclic_first = replace(
        first_node,
        dependencies=(outcome.bundle.root,),
        body=ImpIntro(first_node.body),
    )
    cyclic_bundle = replace(
        outcome.bundle,
        nodes=(cyclic_first,) + outcome.bundle.nodes[1:],
    )
    layer_cycle_rejected = (
        compile_layered_replay(
            cyclic_bundle,
            outcome.target,
            limits=DEFAULT_LAYERED_REPLAY_LIMITS,
        )
        is None
    )

    root_node = outcome.bundle.nodes[outcome.bundle.root]
    bad_root_body: Proof = EqRefl(zero)
    for _dependency in root_node.dependencies:
        bad_root_body = ImpIntro(bad_root_body)
    body_nodes = list(outcome.bundle.nodes)
    body_nodes[outcome.bundle.root] = replace(root_node, body=bad_root_body)
    bad_body_bundle = replace(outcome.bundle, nodes=tuple(body_nodes))
    bad_body_compilation = compile_layered_replay(
        bad_body_bundle,
        outcome.target,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    body_mutation_rejected = bad_body_compilation is not None and not check(
        (), bad_body_compilation.certificate, outcome.target
    )

    rows = {
        "false_target_rejected": false_target_rejected,
        "package_mutation_rejected": package_mutation_rejected,
        "layer_order_mutation_rejected": layer_order_mutation_rejected,
        "layer_cycle_rejected": layer_cycle_rejected,
        "body_mutation_rejected": body_mutation_rejected,
    }
    return {
        **rows,
        "all_mutations_rejected": all(rows.values()),
        "wall_time_seconds": perf_counter() - started,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "peak_rss_growth_kib": max(
            0,
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            - starting_peak_rss,
        ),
    }


def _receipt_json(receipt: _PassReceipt) -> dict[str, object]:
    limits = {
        "nodes": MAX_USE_CERTIFICATE_NODES,
        "objects": MAX_USE_CERTIFICATE_OBJECTS,
        "depth": MAX_USE_PROOF_DEPTH,
        "annotations": (
            DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_annotation_occurrences
        ),
        "envelope_depth": (
            DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_envelope_depth
        ),
    }
    within = {
        "nodes": receipt.proof_nodes <= limits["nodes"],
        "objects": receipt.proof_objects <= limits["objects"],
        "depth": receipt.proof_depth <= limits["depth"],
        "annotations": (
            receipt.proof_annotation_occurrences <= limits["annotations"]
        ),
        "envelope_depth": (
            receipt.proof_envelope_depth <= limits["envelope_depth"]
        ),
    }
    return {
        "wall_time_seconds": receipt.wall_time_seconds,
        "body_build_seconds": receipt.body_build_seconds,
        "compile_seconds": receipt.compile_seconds,
        "kernel_check_seconds": receipt.kernel_check_seconds,
        "peak_rss_kib": receipt.peak_rss_kib,
        "peak_rss_growth_kib": receipt.peak_rss_growth_kib,
        "body_count": receipt.body.body_count,
        "script_command_count": receipt.body.script_command_count,
        "body_proof_occurrences": receipt.body.proof_occurrences,
        "body_proof_objects": receipt.body.proof_objects,
        "maximum_body_proof_depth": receipt.body.maximum_proof_depth,
        "body_sha256": receipt.body.body_sha256,
        "proof_nodes": receipt.proof_nodes,
        "proof_depth": receipt.proof_depth,
        "proof_objects": receipt.proof_objects,
        "proof_edges": receipt.proof_edges,
        "reused_objects": receipt.reused_objects,
        "proof_annotation_occurrences": (
            receipt.proof_annotation_occurrences
        ),
        "proof_envelope_depth": receipt.proof_envelope_depth,
        "package_formula_occurrences": receipt.package_formula_occurrences,
        "maximum_package_formula_depth": receipt.maximum_package_formula_depth,
        "layer_count": receipt.layer_count,
        "layer_profile_sha256": receipt.layer_profile_sha256,
        "package_formula_sha256": receipt.package_formula_sha256,
        "proof_dag_sha256": receipt.proof_dag_sha256,
        "graph_sha256": receipt.graph_sha256,
        "source_sha256": receipt.source_sha256,
        "dne_objects": receipt.dne_objects,
        "kernel_accepted": receipt.kernel_accepted,
        "current_use_limits": limits,
        "within_current_use_limits": within,
        "within_current_use_policy": all(within.values()),
    }


def _static_wmi_receipt_metadata() -> dict[str, object]:
    blueprint = quadratic_reciprocity_layered_blueprint()
    return {
        "root": QR_ROOT_NAME,
        "node_count": len(blueprint.names),
        "layer_count": len(blueprint.layers),
        "dependency_edge_count": sum(
            len(item) for item in blueprint.dependencies
        ),
        "root_node_id": blueprint.root,
        "graph_sha256": blueprint.graph_sha256,
        "source_sha256": blueprint.source_sha256,
        "surface_sha256": sha256(
            QUADRATIC_RECIPROCITY_COMBINED.encode()
        ).hexdigest(),
        "input_limits": {
            item.name: getattr(DEFAULT_LAYERED_REPLAY_LIMITS, item.name)
            for item in fields(DEFAULT_LAYERED_REPLAY_LIMITS)
        },
    }


def wmi_receipt_metadata() -> dict[str, object]:
    """Expose strict JSON without retrying a failed heavy discovery."""

    _require_wmi_heavy_suite()
    payload = _static_wmi_receipt_metadata()
    if _discovery_runs.cache_info().currsize == 0:
        return {
            **payload,
            "discovery_receipt_cached": False,
            "discovery_status": "failed_before_receipt_cache",
            "passes": [],
            "mutation_audit_cached": False,
            "mutation_audit": None,
            "partial_discovery": _partial_discovery_snapshot(),
        }

    _outcome, passes = _discovery_runs()
    mutation_cached = _mutation_audit.cache_info().currsize != 0
    return {
        **payload,
        "discovery_receipt_cached": True,
        "discovery_status": "cached",
        "passes": [
            {"pass_index": index, **_receipt_json(receipt)}
            for index, receipt in enumerate(passes, start=1)
        ],
        "mutation_audit_cached": mutation_cached,
        "mutation_audit": _mutation_audit() if mutation_cached else None,
        "partial_discovery": _partial_discovery_snapshot(),
    }


def test_qr_layered_wmi_contract_is_exact_static_and_unregistered() -> None:
    blueprint = quadratic_reciprocity_layered_blueprint()
    stack = quadratic_reciprocity_stack()
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=__file__)
    public = _specs_by_name()

    assert len(blueprint.names) == EXPECTED_NODE_COUNT
    assert len(blueprint.layers) == EXPECTED_LAYER_COUNT
    assert blueprint.names[blueprint.root] == QR_ROOT_NAME
    assert blueprint.targets[blueprint.root] == _closed_formula(
        QUADRATIC_RECIPROCITY_COMBINED
    )
    assert blueprint.graph_sha256 == EXPECTED_GRAPH_SHA256
    assert blueprint.source_sha256 == EXPECTED_SOURCE_SHA256
    assert sha256(QUADRATIC_RECIPROCITY_COMBINED.encode()).hexdigest() == (
        EXPECTED_SURFACE_SHA256
    )
    assert (
        MAX_USE_CERTIFICATE_NODES,
        MAX_USE_CERTIFICATE_OBJECTS,
        MAX_USE_PROOF_DEPTH,
    ) == (500_000, 100_000, 256)
    assert (
        DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_annotation_occurrences,
        DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_envelope_depth,
    ) == (5_000_000, 256)
    assert QR_ROOT_NAME not in public
    assert all(
        _primitive(command)[0] != "use"
        for spec in stack.admission_order
        for command in spec.script
    )
    assert "from peano_lab.library.theorems import" in source
    assert all(
        not (
            isinstance(node.func, ast.Name) and node.func.id == "replay"
        )
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    )


def test_qr_layered_actual_targets_dummy_body_scaffold_metrics_are_pinned() -> None:
    blueprint = quadratic_reciprocity_layered_blueprint()
    zero = Zero()
    bodies = {name: EqRefl(zero) for name in blueprint.names}
    bundle = attach_quadratic_reciprocity_bodies(blueprint, bodies)
    target = _closed_formula(QUADRATIC_RECIPROCITY_COMBINED)
    compiled = compile_layered_replay(
        bundle,
        target,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )

    assert compiled is not None
    assert compiled.layers == blueprint.layers
    assert compiled.package_formula_occurrences == 144_197
    assert compiled.maximum_package_formula_depth == 68
    assert (
        compiled.proof_nodes,
        compiled.proof_depth,
        compiled.proof_objects,
        compiled.proof_edges,
        compiled.reused_objects,
    ) == (13_705, 56, 13_705, 13_704, 0)
    assert (
        compiled.proof_annotation_occurrences,
        compiled.proof_envelope_depth,
    ) == (157_579, 92)
    assert not check((), compiled.certificate, target)


def test_qr_layered_exact_topology_distinct_target_scaffold_kernel_checks() -> None:
    blueprint = quadratic_reciprocity_layered_blueprint()
    zero = Zero()
    targets: list[Formula] = []
    for node_id in range(len(blueprint.names)):
        marker = Succ(zero)
        # ``S 0`` encodes the leading binary one; the remaining bits choose
        # distinct shallow constructors without inflating the proof topology.
        for bit in f"{node_id + 1:b}"[1:]:
            marker = Add(marker, zero) if bit == "0" else Mul(marker, zero)
        targets.append(Eq(marker, marker))

    nodes: list[LayeredReplayNode] = []
    for node_id, dependencies in enumerate(blueprint.dependencies):
        node_target = targets[node_id]
        marker = node_target.left
        body: Proof = EqRefl(marker)
        # These Cuts consume every declared hypothesis at its exact formula.
        # Earlier nested Cuts shift the context, so Hyp(k-1) selects the next
        # dependency when the declared edges are wrapped in reverse order.
        for dependency in reversed(dependencies):
            body = Cut(
                targets[dependency],
                node_target,
                Hyp(len(dependencies) - 1),
                body,
            )
        for _dependency in dependencies:
            body = ImpIntro(body)
        nodes.append(
            LayeredReplayNode(node_id, node_target, dependencies, body)
        )
    bundle = LayeredReplayBundle(tuple(nodes), blueprint.root)
    root_target = nodes[blueprint.root].target
    compiled = compile_layered_replay(
        bundle,
        root_target,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )

    assert sum(len(item) for item in blueprint.dependencies) == 1_787
    assert len(set(targets)) == EXPECTED_NODE_COUNT
    assert compiled is not None
    assert compiled.layers == blueprint.layers
    assert compiled.package_formula_occurrences == 19_297
    assert compiled.maximum_package_formula_depth == 18
    assert (
        compiled.proof_nodes,
        compiled.proof_depth,
        compiled.proof_objects,
        compiled.proof_edges,
        compiled.reused_objects,
    ) == (19_066, 74, 19_066, 19_065, 0)
    assert (
        compiled.proof_annotation_occurrences,
        compiled.proof_envelope_depth,
    ) == (142_134, 84)
    assert check((), compiled.certificate, root_target)

    swapped_nodes = list(nodes)
    assert blueprint.names[5] == "beta_range_empty"
    assert swapped_nodes[5].dependencies == (3, 4)
    swapped_nodes[5] = replace(swapped_nodes[5], dependencies=(4, 3))
    swapped_bundle = replace(bundle, nodes=tuple(swapped_nodes))
    swapped = compile_layered_replay(
        swapped_bundle,
        root_target,
        limits=DEFAULT_LAYERED_REPLAY_LIMITS,
    )
    assert swapped is not None
    assert not check((), swapped.certificate, root_target)


def test_qr_layered_builds_each_dependency_curried_body_once_per_cold_pass() -> None:
    _require_wmi_heavy_suite()
    _outcome, passes = _discovery_runs()
    assert all(receipt.body.body_count == EXPECTED_NODE_COUNT for receipt in passes)
    assert passes[0].body == passes[1].body


def test_qr_layered_full_certificate_kernel_checks_twice_deterministically() -> None:
    _require_wmi_heavy_suite()
    outcome, passes = _discovery_runs()
    assert outcome.target == _closed_formula(QUADRATIC_RECIPROCITY_COMBINED)
    assert all(receipt.kernel_accepted for receipt in passes)
    assert all(receipt.dne_objects == 0 for receipt in passes)
    assert _deterministic_payload(passes[0]) == _deterministic_payload(passes[1])
    for index, receipt in enumerate(passes, start=1):
        row = _receipt_json(receipt)
        print(
            "WMI QR LAYERED ADMISSION RECEIPT "
            f"pass={index} wall_time_seconds={receipt.wall_time_seconds:.6f} "
            f"body_build_seconds={receipt.body_build_seconds:.6f} "
            f"compile_seconds={receipt.compile_seconds:.6f} "
            f"kernel_check_seconds={receipt.kernel_check_seconds:.6f} "
            f"peak_rss_kib={receipt.peak_rss_kib} "
            f"proof_nodes={receipt.proof_nodes} depth={receipt.proof_depth} "
            f"objects={receipt.proof_objects} edges={receipt.proof_edges} "
            f"annotations={receipt.proof_annotation_occurrences} "
            f"envelope_depth={receipt.proof_envelope_depth} "
            f"package_formula_occurrences={receipt.package_formula_occurrences} "
            f"maximum_package_formula_depth={receipt.maximum_package_formula_depth} "
            f"proof_dag_sha256={receipt.proof_dag_sha256} "
            f"within_current_use_policy={row['within_current_use_policy']}",
            flush=True,
        )


def test_qr_layered_false_target_layer_package_and_body_mutations_fail_closed() -> None:
    _require_wmi_heavy_suite()
    audit = _mutation_audit()
    assert audit["false_target_rejected"]
    assert audit["package_mutation_rejected"]
    assert audit["layer_order_mutation_rejected"]
    assert audit["layer_cycle_rejected"]
    assert audit["body_mutation_rejected"]
    assert audit["all_mutations_rejected"]


def test_qr_layered_certificate_meets_current_use_capacity_policy() -> None:
    _require_wmi_heavy_suite()
    assert (
        MAX_USE_CERTIFICATE_NODES,
        MAX_USE_CERTIFICATE_OBJECTS,
        MAX_USE_PROOF_DEPTH,
    ) == (500_000, 100_000, 256)
    assert (
        DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_annotation_occurrences,
        DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_envelope_depth,
    ) == (5_000_000, 256)
    _outcome, passes = _discovery_runs()
    latest = _receipt_json(passes[-1])
    assert latest["within_current_use_policy"], (
        "the unchanged kernel accepts the layered QR certificate, but it "
        f"exceeds the unchanged use policy: {latest}"
    )
