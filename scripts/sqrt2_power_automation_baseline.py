#!/usr/bin/env python3
"""Small non-LLM substrate demonstration, never an irrationality admission.

Without --run, probe installed tools only. --run additionally regenerates three
ordinary HA arithmetic certificates and requests an UNTRUSTED Z3 parity proof.
All child processes use the existing supervisor. The complete invocation has a
30-second alarm, with two seconds reserved for reporting and cleanup. No solver
proof reconstruction, theorem admission, installation, or catalogue replay occurs.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import fields, is_dataclass
from hashlib import sha256
import importlib.util
import json
import math
from pathlib import Path
import shutil
import signal
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "research/arithmetic-library/sqrt2-power/automation-baseline.json"
SCHEMA = "sqrt2-power-automation-substrate-baseline-v1"
TOTAL_WALL_SECONDS = 30
NATIVE_FORMULAS = (
    "forall n. n + 1 = S n",
    "forall n. n + 2 = S (S n)",
    "forall m. forall n. m * (n + 1) = m * n + m",
)
Z3_INPUT = (
    "(set-option :produce-proofs true)\n"
    "(set-logic QF_LIA)\n"
    "(declare-const m Int)\n(declare-const n Int)\n"
    "(assert (>= m 0))\n(assert (>= n 0))\n"
    "(assert (= (* 2 m) (+ (* 2 n) 1)))\n"
    "(check-sat)\n(get-proof)\n"
)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      sort_keys=True, separators=(",", ":")).encode()


def digest(value):
    return sha256(value).hexdigest()


def runtime():
    """Load only the stdlib supervisor, not Hydra's package/policy imports."""
    name = "_sqrt2_baseline_review_runtime"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            name, ROOT / "training/peano_hydra/review_runtime.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def source_pins():
    paths = {Path(__file__).resolve(),
             ROOT / "scripts/hydra_bounded_exec.py",
             ROOT / "training/peano_hydra/review_runtime.py",
             ROOT / "peano-lab/py/peano_lab/__init__.py"}
    for directory in ("kernel", "engine"):
        paths.update((ROOT / "peano-lab/py/peano_lab" / directory).glob("*.py"))
    return {str(path.relative_to(ROOT)): runtime().hash_file(path)
            for path in sorted(paths)}


class BudgetExhausted(TimeoutError):
    pass


@contextmanager
def total_budget(seconds=TOTAL_WALL_SECONDS):
    if type(seconds) is not int or not 1 <= seconds <= TOTAL_WALL_SECONDS:
        raise ValueError("invalid total wall budget")
    # Do not silently replace another controller's deadline.
    if signal.getitimer(signal.ITIMER_REAL)[0]:
        raise ValueError("an outer alarm already owns this process")
    previous = signal.getsignal(signal.SIGALRM)

    def expired(_signum, _frame):
        raise BudgetExhausted("the complete baseline reached its 30-second ceiling")

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield time.monotonic() + seconds - 2
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def bounded(command, *, deadline, seconds, input_bytes=b""):
    remaining = min(seconds, math.floor(deadline - time.monotonic()))
    if remaining < 1:
        return None
    supervisor = runtime()
    limits = supervisor.ProcessLimits(wall_seconds=remaining,
        cpu_seconds=remaining, rss_bytes=512 * 1024**2, output_bytes=1024**2)
    return supervisor.run_bounded(tuple(command), cwd=ROOT, limits=limits,
                                  input_bytes=input_bytes)


def successful(record):
    return (type(record) is dict and record.get("reason") == "exited"
            and type(record.get("returncode")) is int and record["returncode"] == 0
            and record.get("output_truncated") is False)


def probe_tools(deadline):
    result = {}
    for name in ("python", "vampire", "eprover", "z3"):
        found = sys.executable if name == "python" else shutil.which(name)
        if not found:
            result[name] = {"status": "unavailable_on_PATH", "path": None}
            continue
        path = Path(found).resolve(strict=True)
        pin = runtime().hash_file(path)
        record = bounded((str(path), "-version" if name == "z3" else "--version"),
                         deadline=deadline, seconds=2)
        unchanged = runtime().hash_file(path) == pin
        result[name] = {"status": "available" if successful(record) and unchanged
                       else "version_probe_failed_or_budget_exhausted",
                       "path": str(path), "binary": pin, "version_probe": record,
                       "binary_unchanged": unchanged}
    return result


def _tree(value):
    if is_dataclass(value):
        return {"type": type(value).__name__, "fields":
                {item.name: _tree(getattr(value, item.name)) for item in fields(value)}}
    if type(value) in (str, int) or value is None:
        return value
    raise ValueError("unexpected native certificate field")


def native_worker():
    """Fresh proofs of the exact universally closed inputs; no library import."""
    sys.path.insert(0, str(ROOT / "peano-lab/py"))
    from peano_lab.engine.compact_arith import CompactArithLimits, prove_compact_equation
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Bot, Forall, parse_formula
    from peano_lab.kernel.proofs import ForallIntro
    rows = []
    for source in NATIVE_FORMULAS:
        started = time.monotonic()
        original = parse_formula(source)
        equation, binders = original, 0
        while type(equation) is Forall:
            equation, binders = equation.body, binders + 1
        generated = prove_compact_equation(equation, limits=CompactArithLimits(max_seconds=3.0))
        certificate = generated.certificate
        for _ in range(binders):
            certificate = ForallIntro(certificate)
        checked = check((), certificate, original)
        rejects_false = not check((), certificate, Bot())
        if not checked or not rejects_false:
            raise ValueError("ordinary HA rejected the exact native certificate")
        tree = _tree(certificate)
        rows.append({"formula": source, "formula_sha256": digest(source.encode()),
            "formula_ast_sha256": digest(canonical(_tree(original))),
            "status": "ordinary_HA_checked", "empty_context": True,
            "classical": False, "method": "compact_arith", "ha_checked": checked,
            "false_goal_rejected": rejects_false, "certificate": tree,
            "certificate_sha256": digest(canonical(tree)),
            "body_proof_nodes": generated.proof_nodes, "forall_introductions": binders,
            "work_units": generated.work_units, "wall_seconds": time.monotonic() - started})
    return {"schema": SCHEMA, "scope": "substrate_demonstration", "rows": rows,
            "source_pins": source_pins(), "model_proof_search_calls": 0,
            "external_solver_calls": 0, "IR_obligations_closed": 0}


def accept_native(record, pins):
    """Validate the owned fresh worker transcript, never a saved receipt gate."""
    if not successful(record):
        return None
    value = json.loads(record["stdout"])
    if (value.get("schema") != SCHEMA or value.get("scope") != "substrate_demonstration"
            or value.get("source_pins") != pins
            or value.get("model_proof_search_calls") != 0
            or value.get("external_solver_calls") != 0
            or value.get("IR_obligations_closed") != 0
            or type(value.get("rows")) is not list
            or len(value["rows"]) != len(NATIVE_FORMULAS)):
        raise ValueError("native demonstration transcript changed")
    for row, formula in zip(value["rows"], NATIVE_FORMULAS, strict=True):
        if (row.get("formula") != formula or row.get("formula_sha256") != digest(formula.encode())
                or row.get("ha_checked") is not True or row.get("empty_context") is not True
                or row.get("classical") is not False or row.get("false_goal_rejected") is not True
                or row.get("status") != "ordinary_HA_checked" or row.get("method") != "compact_arith"
                or row.get("certificate_sha256") != digest(canonical(row.get("certificate")))):
            raise ValueError("native proof result or original formula changed")
    return value


def classify_z3(record):
    """Proof-shaped output is an observation, explicitly not a checked proof."""
    observed = successful(record) and record["stdout"].startswith("unsat\n")
    proof_shaped = bool(observed and "(proof" in record["stdout"])
    return {"status": "external_unsat_with_unchecked_proof" if proof_shaped
            else "unknown_or_no_proof", "solver_reported_unsat": bool(observed),
            "proof_shaped_output_present": proof_shaped, "proof_checked": False,
            "ha_checked": False, "solver_proofs_reconstructed": 0,
            "IR_obligations_closed": 0, "input": Z3_INPUT,
            "input_sha256": digest(Z3_INPUT.encode()), "process": record}


def baseline(*, run, deadline):
    started = time.monotonic()
    pins = source_pins()
    tools = probe_tools(deadline)
    native_record, native, z3_record = None, None, None
    if run and tools["python"]["status"] == "available":
        native_record = bounded((tools["python"]["path"], "-B", str(Path(__file__).resolve()),
                                 "--native-worker"), deadline=deadline, seconds=15)
        native = accept_native(native_record, pins)
    if run and tools["z3"]["status"] == "available":
        z3_record = bounded((tools["z3"]["path"], "-in", "-smt2", "-T:2", "-memory:128"),
                            deadline=deadline, seconds=3, input_bytes=Z3_INPUT.encode())
    if source_pins() != pins:
        raise ValueError("baseline implementation changed during the run")
    for tool in tools.values():
        if tool.get("path") and runtime().hash_file(Path(tool["path"])) != tool["binary"]:
            raise ValueError("a probed executable changed during the run")
    return {"schema": SCHEMA, "scope": "substrate_demonstration_not_IR_obligation_closure",
        "status": "completed" if run and native is not None else "probe_only" if not run else "incomplete",
        "total_wall_budget_seconds": TOTAL_WALL_SECONDS,
        "wall_seconds_before_report_serialization": time.monotonic() - started,
        "source_pins": pins, "tools": tools,
        "native": {"inputs": [{"formula": formula, "sha256": digest(formula.encode())}
                               for formula in NATIVE_FORMULAS],
                   "process": native_record, "checked_worker_result": native},
        "z3": classify_z3(z3_record),
        "counts": {"native_substrate_HA_checks": len(native["rows"]) if native else 0,
            "solver_proofs_reconstructed": 0, "model_proof_search_calls": 0,
            "external_solver_proof_search_calls": int(z3_record is not None),
            "new_campaign_theorems": 0, "IR_obligations_closed": 0},
        "limitations": ["No solver proof reconstruction or theorem admission.",
            "No irrationality or real-exponentiation result is claimed.",
            "Native demonstrations regenerate existing elementary identities, not new discoveries.",
            "RSS is sampled on macOS, not an instantaneous hard cap.",
            "CPU instructions and energy remain null where not measured."]}


def write_report(path, report):
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise ValueError("refusing to overwrite a previous report")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2,
                                allow_nan=False).encode() + b"\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--native-worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.native_worker:
        if args.run or args.output:
            parser.error("private native worker accepts no other options")
        print(canonical(native_worker()).decode())
        return 0
    if args.output and not args.run:
        parser.error("--output requires --run")
    with total_budget() as deadline:
        report = baseline(run=args.run, deadline=deadline)
        if args.run:
            write_report(args.output or DEFAULT_OUTPUT, report)
        print(json.dumps({"schema": SCHEMA, "status": report["status"],
                          "counts": report["counts"], "tools": {
                              name: value["status"] for name, value in report["tools"].items()}},
                         sort_keys=True))
    return 0 if report["status"] != "incomplete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
