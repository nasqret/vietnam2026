#!/usr/bin/env python3
"""Source-pinned, sequential proof-DAG/reconstruction observations, not admissions.

Each target is rebound independently in a fresh ordinary HA replay process.
Artifacts are lossless and append-only. Run under the reviewed OS supervisor;
no kernel limits, axioms, parent campaign status, or deployed files are changed.
"""
from dataclasses import replace
from hashlib import sha256
import argparse
import gzip
import json
from pathlib import Path
import sys
import time

from run_sqrt2_power_pilot import (
    ROOT, LeafBudget, controller_deadline, successful, save_new,
)
from sqrt2_power_automation_baseline import runtime
from sqrt2_power_pilot_contracts import canonical
from sqrt2_power_binary_dag import BinaryDAGLimits, formula_sha256
from peano_lab.kernel.formulas import Bot
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library.proof_bundle import (
    BundleNode, ProofBundle, ProofBundleError, check_proof_bundle,
    decode_proof_bundle, encode_proof_bundle,
)

SCHEMA = "sqrt2-power-shared-proof-wave-v1"
SCRIPT = Path(__file__).resolve()
FOUNDATION_CASES = dict(RF001="irat_eq_reflexive", RF002="irat_eq_symmetric",
    RF003="irat_eq_transitive", RF004="irat_eq_scale_nonzero",
    RF005="irat_eq_numerator_shift", RF006="irat_eq_negation_compatible")
CHUNK_CASES = tuple(f"P04-C{i:02d}" for i in range(16))
CASES = ("P10", "P08-eprover", "P08-vampire", "P04-ground", "P04-soundness", "IR016",
         "SN001", "NG001", "SN002", "SN003", "CV001", "RN001", "RN002", "SI001",
         "QN001", "QF001", *FOUNDATION_CASES, *CHUNK_CASES)
LIMITS = BinaryDAGLimits().bundle_limits()


def pins(identifier):
    from sqrt2_power_solver_hints import source_pins
    result = source_pins()
    for name in (SCRIPT.name, "run_sqrt2_power_pilot.py", "sqrt2_power_binary_dag.py",
                 "sqrt2_power_pilot_instances.py"):
        path = ROOT / "scripts" / name
        result[str(path.relative_to(ROOT))] = runtime().hash_file(path)
    if identifier.startswith("P04-"):
        path = ROOT / "scripts/sqrt2_power_formal_composition.py"
        result[str(path.relative_to(ROOT))] = runtime().hash_file(path)
    if identifier in CHUNK_CASES:
        path = ROOT / "scripts/sqrt2_power_composition_chunks.py"
        result[str(path.relative_to(ROOT))] = runtime().hash_file(path)
    if identifier in FOUNDATION_CASES:
        from sqrt2_power_rational_foundations import source_pins as foundation_pins
        result.update(foundation_pins())
    if identifier == "IR016":
        from sqrt2_power_even_square import FERMAT_ARTIFACT, FERMAT_SOURCE_PATH
        for path in (ROOT / "scripts/sqrt2_power_even_square.py", FERMAT_ARTIFACT, ROOT / FERMAT_SOURCE_PATH):
            result[str(path.relative_to(ROOT))] = runtime().hash_file(path)
    if identifier == "SN001":
        from sqrt2_power_signed_norm import signed_norm_source_pins
        result.update(signed_norm_source_pins())
    if identifier in ("NG001", "SN002"):
        from sqrt2_power_norm_separation import norm_separation_source_pins
        result.update(norm_separation_source_pins())
    if identifier == "SN003":
        from sqrt2_power_quadratic_norm_product import norm_product_source_pins
        result.update(norm_product_source_pins())
    if identifier == "CV001":
        from sqrt2_power_convolution_vanishing import convolution_source_pins
        result.update(convolution_source_pins())
    if identifier == "RN002":
        from sqrt2_power_rational_norm_product import rational_norm_product_source_pins
        result.update(rational_norm_product_source_pins())
    if identifier == "SI001":
        from sqrt2_power_signed_product_nonzero import signed_product_nonzero_source_pins
        result.update(signed_product_nonzero_source_pins())
    if identifier == "RN001":
        from sqrt2_power_rational_norm_transport import rational_norm_transport_source_pins
        result.update(rational_norm_transport_source_pins())
    if identifier == "QN001":
        from sqrt2_power_quadratic_nonzero import quadratic_nonzero_source_pins
        result.update(quadratic_nonzero_source_pins())
    if identifier == "QF001":
        from sqrt2_power_quadratic_product_trace import quadratic_product_trace_source_pins
        result.update(quadratic_product_trace_source_pins())
    return result


def target_for(identifier):
    if type(identifier) is not str or identifier not in CASES:
        raise ValueError("unknown exact wave target")
    if identifier == "QN001":
        from sqrt2_power_quadratic_nonzero import frozen_quadratic_nonzero_target
        return frozen_quadratic_nonzero_target()
    if identifier == "QF001":
        from sqrt2_power_quadratic_product_trace import frozen_quadratic_product_trace_target
        return frozen_quadratic_product_trace_target()
    if identifier == "RN001":
        from sqrt2_power_rational_norm_transport import frozen_rational_norm_transport_target
        return frozen_rational_norm_transport_target()
    if identifier == "SI001":
        from sqrt2_power_signed_product_nonzero import frozen_signed_product_nonzero_target
        return frozen_signed_product_nonzero_target()
    if identifier == "RN002":
        from sqrt2_power_rational_norm_product import frozen_rational_norm_product_target
        return frozen_rational_norm_product_target()
    if identifier == "CV001":
        from sqrt2_power_convolution_vanishing import frozen_convolution_vanishing_target
        return frozen_convolution_vanishing_target()
    if identifier in ("NG001", "SN002"):
        from sqrt2_power_norm_separation import frozen_natural_gap_target, frozen_norm_separation_target
        return frozen_natural_gap_target() if identifier == "NG001" else frozen_norm_separation_target()
    if identifier == "SN003":
        from sqrt2_power_quadratic_norm_product import frozen_quadratic_norm_product_target
        return frozen_quadratic_norm_product_target()
    if identifier == "SN001":
        from sqrt2_power_signed_norm import frozen_signed_norm_target
        return frozen_signed_norm_target()
    if identifier == "IR016":
        from sqrt2_power_even_square import frozen_ir016_target
        return frozen_ir016_target()
    if identifier == "P10":
        from sqrt2_power_binary_dag import frozen_p10_targets
        return frozen_p10_targets()[0]
    if identifier in ("P08-eprover", "P08-vampire"):
        from sqrt2_power_solver_hints import P08_SOURCE
        from sqrt2_power_native import closed_formula
        return closed_formula(P08_SOURCE)
    if identifier in CHUNK_CASES:
        from sqrt2_power_composition_chunks import chunk_contract
        from sqrt2_power_native import closed_formula
        return closed_formula(chunk_contract(identifier)["source"])
    if identifier.startswith("P04-"):
        from sqrt2_power_formal_composition import contracts
        from sqrt2_power_native import closed_formula
        kind = "ground_instance" if identifier == "P04-ground" else "trace_soundness"
        return closed_formula(next(r for r in contracts() if r["target_kind"] == kind)["source"])
    if identifier in FOUNDATION_CASES:
        from sqrt2_power_rational_foundations import foundation_target
        return foundation_target(FOUNDATION_CASES[identifier])
    raise ValueError("unknown exact wave target")


def worker(identifier, hint=None):
    before = pins(identifier)
    target = target_for(identifier)
    if identifier == "QN001":
        from sqrt2_power_quadratic_nonzero import prove_quadratic_nonzero
        result = prove_quadratic_nonzero()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="quadratic_integer_binary_nonzero_not_finite_IR046")
    elif identifier == "QF001":
        from sqrt2_power_quadratic_product_trace import prove_quadratic_product_trace
        result = prove_quadratic_product_trace()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="quadratic_finite_trace_nonzero_not_trace_totality_or_real_IR046")
    elif identifier == "RN001":
        from sqrt2_power_rational_norm_transport import prove_rational_norm_transport
        result = prove_rational_norm_transport()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="rational_norm_representative_transport_not_full_IR031")
    elif identifier == "SI001":
        from sqrt2_power_signed_product_nonzero import prove_signed_product_nonzero
        result = prove_signed_product_nonzero()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="signed_integer_binary_nonzero_not_quadratic_finite_IR046")
    elif identifier == "RN002":
        from sqrt2_power_rational_norm_product import prove_rational_norm_product
        result = prove_rational_norm_product()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="rational_norm_product_denominator_not_full_IR031")
    elif identifier == "CV001":
        from sqrt2_power_convolution_vanishing import prove_convolution_vanishing
        result = prove_convolution_vanishing()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="universal_natural_convolution_vanishing_not_IR079")
    elif identifier in ("NG001", "SN002"):
        from sqrt2_power_norm_separation import prove_natural_gap, prove_norm_separation
        result = prove_natural_gap() if identifier == "NG001" else prove_norm_separation()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage=("universal_natural_gap_not_full_campaign"
            if identifier == "NG001" else "signed_norm_integer_gap_not_full_IR032"))
    elif identifier == "SN003":
        from sqrt2_power_quadratic_norm_product import prove_quadratic_norm_product
        result = prove_quadratic_norm_product()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="signed_norm_multiplicativity_not_rational_IR031")
    elif identifier == "SN001":
        from sqrt2_power_signed_norm import prove_signed_norm_zero
        result = prove_signed_norm_zero()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="signed_norm_zero_core_not_IR032")
    elif identifier == "IR016":
        from sqrt2_power_even_square import prove_ir016
        result = prove_ir016()
        payload = result.payload
        diagnostics = dict(result.provenance, coverage="IR016_natural_core_not_full_irrationality")
    elif identifier == "P10":
        from sqrt2_power_binary_dag import prove_p10
        result = prove_p10()
        payload = result.payload
        diagnostics = dict(strategy="per_operation_shared_ordinary_HA_DAG",
            local_nodes=len(result.bundle.nodes), body_nodes=result.receipt.total_body_nodes,
            max_proof_depth=result.max_proof_depth, basis_names=result.basis_names,
            subleaf_node=result.subleaf_node, coverage="full_fixed_P10_not_IR064")
    elif identifier in CHUNK_CASES:
        from sqrt2_power_composition_chunks import prove_chunk
        from sqrt2_power_native import Basis
        result = prove_chunk(identifier, Basis(), expected_ast_sha256=formula_sha256(target))
        payload = result.bundle_certificate.payload
        diagnostics = result.manifest
    elif identifier.startswith("P04-"):
        from sqrt2_power_formal_composition import prove_ground_instance_dag, prove_trace_soundness
        from sqrt2_power_native import Basis
        if identifier == "P04-ground":
            result = prove_ground_instance_dag(Basis(), expected_ast_sha256=formula_sha256(target))
            payload = result.bundle_certificate.payload
            diagnostics = result.manifest
        else:
            result = prove_trace_soundness(Basis(), expected_ast_sha256=formula_sha256(target))
            payload = encode_proof_bundle(ProofBundle((BundleNode(0, target, (), result.certificate),), 0), target, limits=LIMITS)
            diagnostics = result.manifest
    elif identifier in FOUNDATION_CASES:
        from sqrt2_power_rational_foundations import prove_foundation
        actual, proof, diagnostics = prove_foundation(FOUNDATION_CASES[identifier])
        if actual != target:
            raise ValueError("foundation differs from named target")
        payload = encode_proof_bundle(ProofBundle((BundleNode(0, target, (), proof),), 0), target, limits=LIMITS)
        diagnostics = dict(diagnostics, coverage="full_named_rational_foundation_not_IR001",
            solver_role="independent_Z3_conjecture_check_not_imported_in_native_proof")
    else:
        from sqrt2_power_solver_hints import reconstruct_p08
        if type(hint) is not dict or set(hint) != {"problem", "observed", "contract"}:
            raise ValueError("actual source-bound solver hint required")
        if hint["observed"].get("solver") != identifier[4:]:
            raise ValueError("wrong solver hint")
        actual, proof, diagnostics = reconstruct_p08(hint["problem"], hint["observed"], hint["contract"])
        if actual != target:
            raise ValueError("reconstruction changed target")
        bundle = ProofBundle((BundleNode(0, target, (), proof),), 0)
        payload = encode_proof_bundle(bundle, target, limits=LIMITS)
        receipt = check_proof_bundle(bundle, target, limits=LIMITS)
        diagnostics = dict(diagnostics, body_nodes=receipt.total_body_nodes,
            coverage="P08_supporting_leaf_not_full_pilot")
    if before != pins(identifier):
        raise ValueError("sources changed during generation")
    return dict(schema=SCHEMA, case=identifier, status="native_generated",
        source_pins=before, target_ast_sha256=formula_sha256(target), bundle=payload,
        bundle_sha256=sha256(payload.encode()).hexdigest(), diagnostics=diagnostics,
        IR_parents_closed=0, model_proof_search_calls=0, independent_lean_checked=False)


def replay(identifier, value):
    before = pins(identifier)
    target = target_for(identifier)
    if (type(value) is not dict or value.get("schema") != SCHEMA
        or value.get("case") != identifier or value.get("source_pins") != before
        or value.get("status") != "native_generated"
        or value.get("target_ast_sha256") != formula_sha256(target)):
        raise ValueError("changed or unbound producer output")
    payload = value.get("bundle")
    if type(payload) is not str or sha256(payload.encode()).hexdigest() != value.get("bundle_sha256"):
        raise ValueError("changed certificate bytes")
    bundle, encoded_target = decode_proof_bundle(payload, limits=LIMITS)
    if encoded_target != target:
        raise ValueError("bundle does not prove exact independently bound target")
    receipt = check_proof_bundle(bundle, target, limits=LIMITS)
    corrupt = replace(bundle, nodes=tuple(replace(n, body=EqRefl(Zero()))
        if n.node_id == bundle.root else n for n in bundle.nodes))
    for candidate, claimed in ((bundle, Bot()), (corrupt, target)):
        try:
            check_proof_bundle(candidate, claimed, limits=LIMITS)
        except ProofBundleError:
            pass
        else:
            raise ValueError("false target or forged root accepted")
    if before != pins(identifier):
        raise ValueError("sources changed during fresh replay")
    return dict(schema=SCHEMA, case=identifier, status="fresh_ordinary_HA_checked",
        target_ast_sha256=formula_sha256(target), bundle_sha256=value["bundle_sha256"],
        source_pins=before, local_nodes=len(bundle.nodes), proof_nodes=receipt.total_body_nodes,
        kernel_calls=receipt.kernel_calls, original_target_checked=True,
        empty_context=True, false_target_rejected=True, forged_body_rejected=True,
        IR_parents_closed=0, library_admissions=0, independent_lean_checked=False)


def run(identifier, output, vampire=None):
    if output.exists() or output.is_symlink():
        raise ValueError("observation path must be new")
    before = pins(identifier)
    started = time.monotonic()
    deadline = started + 90
    records, results = {}, {}
    report = dict(schema=SCHEMA, case=identifier, source_pins=before,
        authority="local_observation_not_library_admission", source_snapshots={},
        status="not_checked", IR_parents_closed=0, library_admissions=0,
        independent_lean_checked=False, model_proof_search_calls=0)
    with controller_deadline(deadline):
        budget = LeafBudget(deadline)
        worker_input = b""
        if identifier.startswith("P08-"):
            from sqrt2_power_external import ExternalBudget, export_problem, invoke_solver
            from sqrt2_power_pilot_contracts import contracts
            contract = next(r for r in contracts() if r["pilot_id"] == "P08")
            solver = identifier[4:]
            problem = export_problem(contract["source"], tuple((r["name"], r["source"])
                for r in contract["allowed_external_premises"]), format="tptp")
            external_budget = ExternalBudget(cpu_seconds=6, wall_seconds=8)
            observed = invoke_solver(problem, solver, budget=external_budget, seconds=2,
                executable=vampire if solver == "vampire" else None)
            # Same outer case budget; no reservation refund after a fast solver.
            budget.reserved_cpu += external_budget.snapshot()["cpu_hard_limit_reserved_seconds"]
            hint = dict(problem=problem, observed=observed, contract=contract)
            worker_input = canonical(hint)
            save_new(output / "live-solver-input-and-observation.json.gz", gzip.compress(worker_input, mtime=0))
            report["live_external"] = dict(solver=solver, status=observed["observation"],
                binary=observed["capability"].get("binary"), budget=external_budget.snapshot(),
                observation_sha256=sha256(worker_input).hexdigest(), HA_authority=False)
        elif identifier in FOUNDATION_CASES or identifier in ("NG001", "RN001", "RN002", "SI001"):
            from sqrt2_power_external import ExternalBudget, export_problem, invoke_solver
            from peano_lab.kernel.formulas import pretty_formula
            problem = export_problem(pretty_formula(target_for(identifier), []), format="smt2")
            external_budget = ExternalBudget(cpu_seconds=6, wall_seconds=8)
            observed = invoke_solver(problem, "z3", budget=external_budget, seconds=2)
            budget.reserved_cpu += external_budget.snapshot()["cpu_hard_limit_reserved_seconds"]
            raw_external = canonical(dict(problem=problem, observed=observed))
            save_new(output / "live-solver-input-and-observation.json.gz", gzip.compress(raw_external, mtime=0))
            report["live_external"] = dict(solver="z3", status=observed["observation"],
                binary=observed["capability"].get("binary"), budget=external_budget.snapshot(),
                observation_sha256=sha256(raw_external).hexdigest(), HA_authority=False,
                role="independent_conjecture_check_not_used_for_reconstruction")
        generated = budget.run((sys.executable, "-B", str(SCRIPT), "--worker", identifier),
            cpu=28, wall=40, input_bytes=worker_input)
        records["generation"] = generated
        if successful(generated):
            value = json.loads(generated["stdout"])
            if value.get("source_pins") != before:
                raise ValueError("producer did not use controller sources")
            results["generation"] = {k:v for k,v in value.items() if k != "bundle"}
            checked = budget.run((sys.executable, "-B", str(SCRIPT), "--replay", identifier),
                cpu=20, wall=30, input_bytes=canonical(value))
            records["fresh_replay"] = checked
            if successful(checked):
                accepted = json.loads(checked["stdout"])
                if (accepted.get("status") != "fresh_ordinary_HA_checked"
                    or accepted.get("source_pins") != before
                    or accepted.get("bundle_sha256") != value.get("bundle_sha256")):
                    raise ValueError("unexpected fresh replay result")
                results["fresh_replay"] = accepted
                report["status"] = "fresh_ordinary_HA_checked"
        if pins(identifier) != before:
            raise ValueError("controller inputs changed before archival")
        for name, pin in before.items():
            raw = (ROOT / name).read_bytes()
            if sha256(raw).hexdigest() != pin["sha256"] or len(raw) != pin["bytes"]:
                raise ValueError("changed source snapshot")
            stored = "sources/" + name + ".gz"
            save_new(output / stored, gzip.compress(raw, mtime=0))
            report["source_snapshots"][name] = stored
        for phase, process in records.items():
            raw = canonical(process)
            save_new(output / (phase + "-process.json.gz"), gzip.compress(raw, mtime=0))
        report.update(results=results, process_records={phase: dict(path=phase+"-process.json.gz",
            raw_sha256=sha256(canonical(process)).hexdigest(), reason=process["reason"],
            returncode=process["returncode"], resources=process["resources"])
            for phase, process in records.items() if process is not None},
            elapsed_wall_seconds=time.monotonic()-started,
            budget=dict(cpu_seconds=60, wall_seconds=90, max_workers=1, rss_bytes=768*1024**2,
                note="CPU reservations include each worker's one-second hard-limit margin"))
        save_new(output / "report.json", json.dumps(report, sort_keys=True, indent=2).encode()+b"\n")
    return {key: report[key] for key in ("case", "status", "elapsed_wall_seconds", "process_records")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--worker", choices=CASES)
    group.add_argument("--replay", choices=CASES)
    group.add_argument("--run", choices=CASES)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--vampire", type=Path)
    args = parser.parse_args()
    if args.worker:
        hint = None
        if args.worker.startswith("P08-"):
            raw = sys.stdin.buffer.read(8*1024**2+1)
            if len(raw) > 8*1024**2:
                raise ValueError("solver hint input exceeds bound")
            hint = json.loads(raw)
        value = worker(args.worker, hint)
    elif args.replay:
        raw = sys.stdin.buffer.read(8*1024**2+1)
        if len(raw) > 8*1024**2:
            raise ValueError("replay input exceeds bound")
        value = replay(args.replay, json.loads(raw))
    else:
        if args.output is None:
            parser.error("--run requires --output")
        value = run(args.run, args.output, args.vampire)
    if "peano_lab.library.theorems" in sys.modules:
        raise ValueError("worker unexpectedly imported full theorem registry")
    print(canonical(value).decode(), flush=True)
