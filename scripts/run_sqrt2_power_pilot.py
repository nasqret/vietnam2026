#!/usr/bin/env python3
"""Bounded, source-pinned native/solver pilot; no promotion or theorem admission.

External logs are preserved as classical hints. A solver hit may trigger an
independent native reproof, not a claim of generic TSTP/SMT proof translation.
Canonical certificate bytes must pass another fresh ordinary-HA process.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import signal
import sys
import time

from sqrt2_power_automation_baseline import runtime, source_pins as base_pins
from sqrt2_power_native import ROOT, BASIS_NAMES, Basis, closed_formula, prove_leaf
from sqrt2_power_pilot_contracts import canonical, contracts
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Bot
from peano_lab.kernel.proofs import AndIntro, EqRefl, Hyp, ImpIntro
from peano_lab.kernel.terms import Zero
from peano_lab.library.proof_bundle import (
    BundleLimits, BundleNode, ProofBundle, ProofBundleError,
    check_proof_bundle, decode_proof_bundle, encode_proof_bundle,
)

SCHEMA = "sqrt2-power-bounded-pilot-v1"
SCRIPT = Path(__file__).resolve()
LIMITS = BundleLimits(max_nodes=32, max_body_nodes=100000,
    max_total_body_nodes=200000, max_payload_bytes=8*1024**2)
TOTAL_WALL = 1200


def pins():
    result = base_pins()
    for name in ("sqrt2_power_native.py", "sqrt2_power_campaign_spec.py",
                 "sqrt2_power_pilot_contracts.py", "run_sqrt2_power_pilot.py",
                 "sqrt2_power_external.py"):
        path = ROOT / "scripts" / name
        result[str(path.relative_to(ROOT))] = runtime().hash_file(path)
    path = ROOT / "peano-lab/py/peano_lab/library/theorems.py"
    result[str(path.relative_to(ROOT))] = runtime().hash_file(path)
    for name in ("__init__.py", "proof_bundle.py"):
        path = ROOT / "peano-lab/py/peano_lab/library" / name
        result[str(path.relative_to(ROOT))] = runtime().hash_file(path)
    return result


def by_id(identifier):
    if identifier == "basis":
        basic = Basis()
        parts = [{"name": name, "source": basic.specs[name][1]} for name in sorted(BASIS_NAMES)]
        return dict(pilot_id="basis", coverage="regenerated_existing_basis", dispatchable=True,
                    parts=parts, contract_sha256=sha256(canonical(parts)).hexdigest())
    for row in contracts():
        if row["pilot_id"] == identifier:
            return row
    raise ValueError("unknown pilot id")


def basis_target(row):
    formulas = [closed_formula(p["source"]) for p in row["parts"]]
    target = formulas[-1]
    for f in reversed(formulas[:-1]):
        target = And(f, target)
    return target


def native_worker(identifier):
    row = by_id(identifier)
    before = pins()
    result = dict(schema=SCHEMA, pilot_id=identifier, contract_sha256=row["contract_sha256"],
                  source_pins=before, coverage=row["coverage"],
                  model_proof_search_calls=0, IR_parents_closed=0,
                  independent_lean_checked=False)
    if not row["dispatchable"]:
        return dict(result, status="unelaborated", reason=row["reason"])
    basis = Basis()
    try:
        if identifier == "basis":
            basic = [basis.get(p["name"]) for p in row["parts"]]
            target = basis_target(row)
            proof = Hyp(0)
            for i in range(1, len(basic)):
                proof = AndIntro(Hyp(i), proof)
            for _ in basic:
                proof = ImpIntro(proof)
            nodes = [BundleNode(i, b.formula, (), b.certificate) for i,b in enumerate(basic)]
            nodes.append(BundleNode(len(basic), target, tuple(range(len(basic))), proof))
            bundle = ProofBundle(tuple(nodes), len(basic))
        else:
            target, proof = prove_leaf(row, basis)
            bundle = ProofBundle((BundleNode(0, target, (), proof),), 0)
        receipt = check_proof_bundle(bundle, target, limits=LIMITS)
        payload = encode_proof_bundle(bundle, target, limits=LIMITS)
        if check((), proof, Bot()):
            raise ValueError("certificate was accepted against false")
        result.update(status="native_generated", basis=basis.manifest(), bundle=payload,
                      bundle_sha256=sha256(payload.encode()).hexdigest(),
                      proof_nodes=receipt.total_body_nodes, kernel_calls=receipt.kernel_calls,
                      original_target_checked=True, false_target_rejected=True)
    except Exception as exc:
        result.update(status="native_unresolved", error_type=type(exc).__name__, reason=str(exc)[:1500])
    if before != pins():
        raise ValueError("proof producer inputs changed during execution")
    return result


def replay_worker(identifier, value):
    row = by_id(identifier)
    if (type(value) is not dict or value.get("schema") != SCHEMA or
        value.get("pilot_id") != identifier or value.get("contract_sha256") != row["contract_sha256"] or
        value.get("source_pins") != pins() or value.get("status") != "native_generated"):
        raise ValueError("changed or unbound worker response")
    payload = value.get("bundle")
    if type(payload) is not str or sha256(payload.encode()).hexdigest() != value.get("bundle_sha256"):
        raise ValueError("altered certificate bytes")
    bundle, decoded = decode_proof_bundle(payload, limits=LIMITS)
    target = basis_target(row) if identifier == "basis" else closed_formula(row["source"])
    if decoded != target:
        raise ValueError("certificate proves a different original formula")
    receipt = check_proof_bundle(bundle, target, limits=LIMITS)
    bad = ProofBundle(tuple(replace(n, body=EqRefl(Zero())) if n.node_id == bundle.root else n
                           for n in bundle.nodes), bundle.root)
    try:
        check_proof_bundle(bad, target, limits=LIMITS)
    except ProofBundleError:
        pass
    else:
        raise ValueError("forged certificate mutation was accepted")
    try:
        check_proof_bundle(bundle, Bot(), limits=LIMITS)
    except ProofBundleError:
        pass
    else:
        raise ValueError("accepted root/cone passed the false-target mutation")
    return dict(schema=SCHEMA, status="fresh_ordinary_HA_checked",
        pilot_id=identifier, contract_sha256=row["contract_sha256"],
        bundle_sha256=value["bundle_sha256"], proof_nodes=receipt.total_body_nodes,
        kernel_calls=receipt.kernel_calls, original_target_checked=True,
        false_target_rejected=True, forged_body_rejected=True,
        empty_context=True, classical=False, IR_parents_closed=0,
        independent_lean_checked=False)


def successful(record):
    return (isinstance(record, dict) and record.get("reason") == "exited" and
            type(record.get("returncode")) is int and record["returncode"] == 0 and
            record.get("output_truncated") is False)


class LeafBudget:
    def __init__(self, aggregate_deadline):
        self.deadline = min(aggregate_deadline, time.monotonic()+90)
        self.reserved_cpu = 0
        self.records = []

    def run(self, argv, *, cpu, wall, input_bytes=b""):
        remaining = int(self.deadline-time.monotonic())
        effective_wall = min(wall, remaining)
        if effective_wall < cpu or self.reserved_cpu+cpu+1 > 60:
            return None
        self.reserved_cpu += cpu+1  # include the guard's hard-limit margin
        limits = runtime().ProcessLimits(cpu_seconds=cpu, wall_seconds=effective_wall,
            rss_bytes=768*1024**2, output_bytes=8*1024**2)
        result = runtime().run_bounded(tuple(argv), cwd=ROOT, limits=limits, input_bytes=input_bytes)
        runtime().validate_process_record(result, command=tuple(argv), limits=limits, input_bytes=input_bytes)
        self.records.append(result)
        return result


def concise_process(record):
    if record is None:
        return None
    # Keep the supervisor's original byte counts, hash and raw-byte metadata;
    # decoded retained text is not the full stream after truncation/UTF-8 errors.
    return {k: v for k, v in record.items() if k != "stdout"}


class ControllerDeadline(TimeoutError):
    pass


@contextmanager
def controller_deadline(deadline):
    """Unix controller wall guard, including Python exports/JSON/hashing.

The existing subprocess supervisor cleans its owned process group on every
BaseException, so an alarm cannot orphan the currently supervised worker.
An expired controller cannot emit a successful final-run receipt.
"""
    started = time.monotonic()
    remaining = deadline-started
    if remaining <= 0:
        raise ControllerDeadline("controller wall budget exhausted")
    old_handler = signal.getsignal(signal.SIGALRM)
    old_timer = signal.getitimer(signal.ITIMER_REAL)
    if old_timer[1]:
        raise ValueError("refusing to replace an existing periodic timer")
    def expired(_signum, _frame):
        raise ControllerDeadline("controller wall budget exhausted")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, min(remaining, old_timer[0]) if old_timer[0] else remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
        if old_timer[0]:
            signal.setitimer(signal.ITIMER_REAL, max(0.000001, old_timer[0]-(time.monotonic()-started)))


def save_new(path, data):
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise ValueError("refusing to overwrite evidence: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def native_arm(row, budget, folder, arm):
    proc = budget.run((sys.executable, "-B", str(SCRIPT), "--worker", row["pilot_id"]), cpu=12, wall=18)
    result = dict(arm=arm, generation_process=concise_process(proc), status="process_failed_or_budget_exhausted")
    if not successful(proc):
        return result
    value = json.loads(proc["stdout"])
    if value.get("contract_sha256") != row["contract_sha256"] or value.get("source_pins") != pins():
        raise ValueError("native result does not match the frozen contract/source")
    result["generation"] = {k:v for k,v in value.items() if k not in ("bundle", "source_pins")}
    result["status"] = value["status"]
    if value["status"] != "native_generated":
        return result
    payload = value["bundle"].encode()
    replay = budget.run((sys.executable, "-B", str(SCRIPT), "--replay", row["pilot_id"]),
                        cpu=8, wall=12, input_bytes=canonical(value))
    result["fresh_replay_process"] = concise_process(replay)
    if not successful(replay):
        result["status"] = "fresh_replay_failed"
        return result
    checked = json.loads(replay["stdout"])
    if (checked.get("status") != "fresh_ordinary_HA_checked" or
        checked.get("bundle_sha256") != sha256(payload).hexdigest() or
        checked.get("contract_sha256") != row["contract_sha256"]):
        raise ValueError("invalid fresh replay response")
    relative = f"certificates/{row['pilot_id']}-{arm}.json"
    save_new(folder / relative, payload)
    result.update(status="fresh_ordinary_HA_checked", fresh_replay=checked,
                  certificate_path=relative)
    return result


def attempt_leaf(row, entry, budget, folder, vampire):
    from sqrt2_power_external import ExternalBudget, export_problem, invoke_solver, validate_export
    entry["native_only"] = native_arm(row, budget, folder, "native")
    remaining = int(budget.deadline-time.monotonic())
    if remaining >= 2:
        ext_budget = ExternalBudget(cpu_seconds=15, wall_seconds=min(30, remaining))
        premises = tuple((p["name"], p["source"]) for p in row["allowed_external_premises"])
        try:
            for solver in ("z3", "eprover", "vampire"):
                problem = export_problem(row["source"], premises, format="smt2" if solver == "z3" else "tptp")
                validate_export(problem, row["source"], premises)
                observed = invoke_solver(problem, solver, budget=ext_budget, seconds=2,
                                         executable=vampire if solver == "vampire" else None)
                save_new(folder / "solver-inputs" / f"{row['pilot_id']}-{solver}.json", canonical(problem)+b"\n")
                entry["external"].append(observed)
        finally:
            budget.reserved_cpu += ext_budget.snapshot()["cpu_hard_limit_reserved_seconds"]
    hit = any(x["observation"]["solver_status"] in ("unsat", "Theorem", "Unsatisfiable") for x in entry["external"])
    if hit:
        entry["solver_gated_reproof"] = native_arm(row, budget, folder, "solver-gated")
    else:
        entry["solver_gated_reproof"] = dict(status="not_attempted_no_solver_hit")
    entry["status"] = "attempted"


def run_pilot(folder, *, selected=None, vampire=None):
    started = time.monotonic()
    deadline = started + TOTAL_WALL
    with controller_deadline(deadline):
        return _run_pilot(folder, selected=selected, vampire=vampire, started=started, deadline=deadline)


def _run_pilot(folder, *, selected, vampire, started, deadline):
    if folder.exists() or folder.is_symlink():
        raise ValueError("pilot output directory must be new")
    before = pins()
    frozen = contracts()
    if selected and not set(selected) <= {row["pilot_id"] for row in frozen}:
        raise ValueError("unknown selected pilot; refusing an empty success")
    save_new(folder / "contracts.json", canonical(frozen)+b"\n")
    report = dict(schema=SCHEMA, authority="bounded_local_pilot_not_library_admission",
        source_pins=before, rows=[], model_proof_search_calls=0,
        model_planning_and_engineering_tokens=None, IR_parents_closed=0,
        independent_lean_checked=False, solver_proof_logs_translated=0,
        limits=dict(aggregate_wall_seconds=1200, per_leaf_wall_seconds=90,
                    per_leaf_cpu_seconds=60, max_workers=1, rss_mib=768,
                    output_mib=8, retries_without_change=0),
        comparison="Native-only versus solver-gated independent native reproof. This is not a proof-log translator or an LLM search run.")
    # Existing premises are regenerated and freshly replayed before ANY export.
    # This is the separate <=30-second setup smoke, not an assumed library oracle.
    preparation = LeafBudget(min(deadline, time.monotonic()+30))
    with controller_deadline(preparation.deadline):
        report["checked_basis"] = native_arm(by_id("basis"), preparation, folder, "native")
    if report["checked_basis"]["status"] != "fresh_ordinary_HA_checked":
        raise ValueError("cannot export arithmetic premises: fresh basis verification failed")
    for row in frozen:
        if selected and row["pilot_id"] not in selected:
            continue
        if time.monotonic() >= deadline:
            report["stop_reason"] = "aggregate_deadline"
            break
        entry = dict(contract=row, status="unelaborated", external=[])
        if not row["dispatchable"]:
            report["rows"].append(entry)
            continue
        budget = LeafBudget(deadline)
        try:
            with controller_deadline(budget.deadline):
                attempt_leaf(row, entry, budget, folder, vampire)
        except ControllerDeadline:
            entry["status"] = "controller_wall_budget_exhausted"
            entry.setdefault("native_only", dict(status="controller_wall_budget_exhausted"))
            entry.setdefault("solver_gated_reproof", dict(status="controller_wall_budget_exhausted"))
        entry["reserved_cpu_seconds"] = budget.reserved_cpu
        report["rows"].append(entry)
        print(json.dumps({"pilot":row["pilot_id"], "native":entry["native_only"]["status"],
            "solvers":{r["solver"]:r["observation"]["solver_status"] for r in entry["external"]},
            "reproof":entry["solver_gated_reproof"]["status"]}), flush=True)
    if before != pins():
        raise ValueError("implementation changed during the pilot; refusing a stable-run receipt")
    accepted = [r for r in report["rows"] if r.get("native_only",{}).get("status") == "fresh_ordinary_HA_checked"]
    report.update(wall_seconds=time.monotonic()-started,
        counts=dict(fully_checked_pilot_contracts=sum(r["contract"]["coverage"] == "full_pilot_contract" for r in accepted),
            checked_supporting_subleaves=sum(r["contract"]["coverage"] == "supporting_subleaf_only" for r in accepted),
            native_checked_leaves=len(accepted), IR_parents_closed=0,
            solver_gated_reproofs=sum(r.get("solver_gated_reproof",{}).get("status") == "fresh_ordinary_HA_checked" for r in report["rows"])))
    save_new(folder / "report.json", json.dumps(report, sort_keys=True, indent=2, allow_nan=False).encode()+b"\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--worker")
    group.add_argument("--replay")
    group.add_argument("--run", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--only", action="append")
    parser.add_argument("--vampire", type=Path)
    args = parser.parse_args()
    if args.worker:
        value = native_worker(args.worker)
        if "peano_lab.library.theorems" in sys.modules:
            raise ValueError("fresh worker unexpectedly imported the full theorem registry")
        print(canonical(value).decode())
    elif args.replay:
        raw = sys.stdin.buffer.read(8*1024**2+1)
        if len(raw) > 8*1024**2:
            raise ValueError("replay input exceeds the proof byte budget")
        value = replay_worker(args.replay, json.loads(raw))
        if "peano_lab.library.theorems" in sys.modules:
            raise ValueError("fresh verifier unexpectedly imported the full theorem registry")
        print(canonical(value).decode())
    else:
        if not args.output:
            parser.error("--run requires a new --output directory")
        result = run_pilot(args.output, selected=args.only, vampire=args.vampire)
        print(json.dumps({"counts":result["counts"], "wall_seconds":result["wall_seconds"], "output":str(args.output)}))


if __name__ == "__main__":
    main()
