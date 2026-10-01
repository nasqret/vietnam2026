#!/usr/bin/env python3
"""Bounded classical solver HINTS for exact closed HA arithmetic formulas.

Supported input is precisely Eq/Bot/And/Or/Imp/Forall/Exists over the existing
Zero/Succ/Add/Mul/Var kernel AST. Surface <= is its existing existential sugar.
No real, rational, exponentiation, induction schema, library lookup, or opaque
definition is added. Signed/rational campaign leaves must first be elaborated
by their owner into this natural-number language with all premises explicit.

SMT uses guarded integer arithmetic. TPTP uses guarded FOF with nat closure and
the six actual kernel arithmetic axioms, but NO induction. These are classical
search encodings, not a verified HA interpretation or a proof reconstruction.
Even a complete external proof log never grants HA certificate authority.

No installation, downloads, shell invocation, output file, or model search.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
from threading import Lock
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "peano-lab/py") not in sys.path:
    sys.path.insert(0, str(ROOT / "peano-lab/py"))
from peano_lab.kernel.formulas import (  # noqa: E402
    And, Bot, Eq, Exists, Forall, Formula, Imp, Or,
    parse_formula_with_names, pretty_formula,
)
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero  # noqa: E402

SCHEMA = "sqrt2-power-classical-hint-export-v1"
MAX_SOURCE_BYTES = 32768
MAX_AST_NODES = 8192
MAX_AST_DEPTH = 128
MAX_PREMISES = 16
MAX_EXPORT_BYTES = 2 * 1024**2
MAX_CPU_SECONDS = 30
MAX_RSS_BYTES = 512 * 1024**2
SOLVERS = ("z3", "eprover", "vampire")
_WORKER_LOCK = Lock()
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}\Z")
_ROW_KEYS = {"source", "source_sha256", "ast", "ast_sha256"}
_KEYS = {"schema", "format", "fragment", "target", "premises", "background",
         "natural_guard_policy", "induction_included", "ha_translation_verified",
         "authority", "input", "input_bytes", "input_sha256", "export_sha256"}


class ExportError(ValueError):
    """Unsupported or changed input; no solver or proof claim is authorized."""


def canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, allow_nan=False,
                          sort_keys=True, separators=(",", ":")).encode()
    except (ValueError, TypeError, RecursionError, UnicodeError) as exc:
        raise ExportError("noncanonical or oversized logical record") from exc


def _hash(raw):
    return sha256(raw).hexdigest()


def canonical_ast(formula):
    """Bounded exact constructor data; reject free variables and foreign types."""
    pending, active = [0], set()

    def visit(node, scope, depth, term=False):
        pending[0] += 1
        if pending[0] > MAX_AST_NODES or depth > MAX_AST_DEPTH or id(node) in active:
            raise ExportError("AST exceeds node/depth bound or contains a cycle")
        kind = type(node)
        active.add(id(node))
        try:
            if term:
                if kind is Var:
                    if type(node.index) is not int or not 0 <= node.index < scope:
                        raise ExportError("free, negative, or noninteger de Bruijn variable")
                    return ["Var", node.index]
                if kind is Zero:
                    return ["Zero"]
                if kind is Succ:
                    return ["Succ", visit(node.term, scope, depth + 1, True)]
                if kind in (Add, Mul):
                    return [kind.__name__, visit(node.left, scope, depth + 1, True),
                            visit(node.right, scope, depth + 1, True)]
            else:
                if kind is Bot:
                    return ["Bot"]
                if kind is Eq:
                    return ["Eq", visit(node.left, scope, depth + 1, True),
                            visit(node.right, scope, depth + 1, True)]
                if kind in (And, Or, Imp):
                    return [kind.__name__, visit(node.left, scope, depth + 1),
                            visit(node.right, scope, depth + 1)]
                if kind in (Forall, Exists):
                    return [kind.__name__, visit(node.body, scope + 1, depth + 1)]
            raise ExportError("unsupported exact kernel constructor")
        except AttributeError as exc:
            raise ExportError("incomplete kernel AST") from exc
        finally:
            active.remove(id(node))

    return visit(formula, 0, 0)


def ast_sha256(formula):
    return _hash(canonical(canonical_ast(formula)))


def _formula(value):
    if type(value) is str:
        try:
            if not value or len(value.encode()) > MAX_SOURCE_BYTES:
                raise ExportError("source exceeds its exact byte bound")
            formula, free = parse_formula_with_names(value)
            if free:
                raise ExportError("only closed formulas are exported")
        except (ValueError, RecursionError, UnicodeError) as exc:
            raise ExportError("unsupported or excessive HA source syntax") from exc
        source = value
    elif type(value) in (Eq, Bot, And, Or, Imp, Forall, Exists):
        formula = value
        canonical_ast(formula)  # Bound before calling the recursive printer.
        source = pretty_formula(formula, [])
        if len(source.encode()) > MAX_SOURCE_BYTES:
            raise ExportError("printed source exceeds byte bound")
        reparsed, free = parse_formula_with_names(source)
        if free or canonical_ast(reparsed) != canonical_ast(formula):
            raise ExportError("exact kernel AST did not round-trip")
    else:
        raise ExportError("expected exact kernel Formula or bounded source string")
    ast = canonical_ast(formula)
    return {"source": source, "source_sha256": _hash(source.encode()),
            "ast": ast, "ast_sha256": _hash(canonical(ast))}


def _emit(ast, format, variables=()):
    kind = ast[0]
    if kind == "Var":
        return variables[ast[1]]
    if kind == "Zero":
        return "0" if format == "smt2" else "zero"
    if kind == "Succ":
        term = _emit(ast[1], format, variables)
        return f"(+ {term} 1)" if format == "smt2" else f"s({term})"
    if kind in (Add.__name__, Mul.__name__, "Eq", "And", "Or", "Imp"):
        left, right = (_emit(child, format, variables) for child in ast[1:])
        if format == "smt2":
            symbol = {"Add": "+", "Mul": "*", "Eq": "=", "And": "and",
                      "Or": "or", "Imp": "=>"}[kind]
            return f"({symbol} {left} {right})"
        if kind in ("Add", "Mul"):
            return f"{kind.lower()}({left},{right})"
        symbol = {"Eq": "=", "And": "&", "Or": "|", "Imp": "=>"}[kind]
        return f"({left} {symbol} {right})"
    if kind == "Bot":
        return "false" if format == "smt2" else "$false"
    if kind in ("Forall", "Exists"):
        name = ("v" if format == "smt2" else "V") + str(len(variables))
        body = _emit(ast[1], format, (name, *variables))
        universal = kind == "Forall"
        if format == "smt2":
            connective = "=>" if universal else "and"
            return (f"({'forall' if universal else 'exists'} (({name} Int)) "
                    f"({connective} (>= {name} 0) {body}))")
        connective = "=>" if universal else "&"
        return f"({'!' if universal else '?'} [{name}] : (nat({name}) {connective} {body}))"
    raise ExportError("unsupported internal AST")


def export_problem(target, premises=(), *, format="smt2"):
    """Produce detached classical search data; premises confer no proof authority."""
    if type(format) is not str or format not in ("smt2", "tptp"):
        raise ExportError("only smt2 and guarded tptp FOF are supported")
    if type(premises) is not tuple or len(premises) > MAX_PREMISES:
        raise ExportError("premises must be a bounded ordered tuple")
    target_row = _formula(target)
    rows, names = [], set()
    for index, pair in enumerate(premises):
        if (type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str
                or _NAME.fullmatch(pair[0]) is None or pair[0] in names):
            raise ExportError("premise names must be distinct bounded identifiers")
        names.add(pair[0])
        rows.append({"name": pair[0], "export_name": f"p{index:03d}", **_formula(pair[1])})
    background = []
    if format == "smt2":
        lines = ["; Untrusted classical hint, never an HA certificate.",
                 "(set-option :produce-proofs true)", "(set-logic ALL)"]
        for row in rows:
            lines.append(f"(assert (! {_emit(row['ast'], format)} :named {row['export_name']}))")
        lines.extend((f"(assert (! (not {_emit(target_row['ast'], format)}) :named negated_target))",
                      "(check-sat)", "(get-proof)"))
        guard = "every universal Int variable is >=0 guarded; every existential conjoins >=0"
    else:
        from peano_lab.kernel.checker import axiom_formula
        lines = ["% Untrusted guarded classical FOF hint; NO induction schema."]
        closures = (
            ("nat_zero", "nat(zero)"),
            ("nat_succ", "(! [X] : (nat(X) => nat(s(X))))"),
            ("nat_add", "(! [X,Y] : ((nat(X) & nat(Y)) => nat(add(X,Y))))"),
            ("nat_mul", "(! [X,Y] : ((nat(X) & nat(Y)) => nat(mul(X,Y))))"),
        )
        for name, text in closures:
            background.append({"name": name, "kind": "natural_domain_closure", "formula": text})
            lines.append(f"fof({name},axiom,{text}).")
        for name in ("PA1", "PA2", "PA3", "PA4", "PA5", "PA6"):
            row = {"name": name.lower(), "kind": "actual_kernel_arithmetic_axiom",
                   **_formula(axiom_formula(name))}
            background.append(row)
            lines.append(f"fof({name.lower()},axiom,{_emit(row['ast'], format)}).")
        for row in rows:
            lines.append(f"fof({row['export_name']},hypothesis,{_emit(row['ast'], format)}).")
        lines.append(f"fof(target,conjecture,{_emit(target_row['ast'], format)}).")
        guard = "each FOF quantifier restricts to nat; explicit zero/succ/add/mul closure; PA1-PA6 only"
    text = "\n".join(lines) + "\n"
    if len(text.encode()) > MAX_EXPORT_BYTES:
        raise ExportError("export exceeds byte bound")
    result = {"schema": SCHEMA, "format": format,
        "fragment": "closed first-order equality arithmetic: Eq Bot And Or Imp Forall Exists; Zero Succ Add Mul Var",
        "target": target_row, "premises": rows, "background": background,
        "natural_guard_policy": guard, "induction_included": False,
        "ha_translation_verified": False, "authority": "untrusted_classical_search_hint_only",
        "input": text, "input_bytes": len(text.encode()), "input_sha256": _hash(text.encode())}
    result["export_sha256"] = _hash(canonical(result))
    return result


def _same_json(left, right):
    """Exact JSON types, walking only the freshly rebuilt bounded structure."""
    if type(left) is not type(right):
        return False
    if type(right) is dict:
        return (set(left) == set(right)
                and all(_same_json(left[key], value) for key, value in right.items()))
    if type(right) is list:
        return len(left) == len(right) and all(_same_json(a, b) for a, b in zip(left, right))
    return left == right


def validate_problem(problem):
    """Re-elaborate from original sources; reject extra fields or resealed edits."""
    if type(problem) is not dict or set(problem) != _KEYS:
        raise ExportError("unexpected exported problem fields")
    target, premises = problem["target"], problem["premises"]
    if (type(target) is not dict or set(target) != _ROW_KEYS
            or type(premises) is not list or len(premises) > MAX_PREMISES):
        raise ExportError("invalid original target/premise mapping")
    for row in premises:
        if type(row) is not dict or set(row) != _ROW_KEYS | {"name", "export_name"}:
            raise ExportError("unexpected premise fields")
    rebuilt = export_problem(target["source"], tuple((row["name"], row["source"]) for row in premises),
                             format=problem["format"])
    try:
        if not _same_json(problem, rebuilt):
            raise ExportError("export no longer matches its exact original HA formulas")
    except RecursionError as exc:
        raise ExportError("excessive exported structure") from exc
    return rebuilt


def validate_export(problem, target, premises=()):
    """Public replay binding to the caller's ORIGINAL target, not receipt text."""
    rebuilt = validate_problem(problem)
    expected = export_problem(target, premises, format=rebuilt["format"])
    if (rebuilt["target"]["ast_sha256"] != expected["target"]["ast_sha256"]
            or [(r["name"], r["ast_sha256"]) for r in rebuilt["premises"]]
            != [(r["name"], r["ast_sha256"]) for r in expected["premises"]]):
        raise ExportError("export changed the independently supplied target or premises")
    return rebuilt


def _runtime():
    name = "_sqrt2_external_review_runtime"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / "training/peano_hydra/review_runtime.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def source_pins():
    paths = [Path(__file__).resolve(), ROOT / "training/peano_hydra/review_runtime.py",
             ROOT / "scripts/hydra_bounded_exec.py", ROOT / "peano-lab/py/peano_lab/__init__.py"]
    paths.extend(sorted((ROOT / "peano-lab/py/peano_lab/kernel").glob("*.py")))
    return {str(path.relative_to(ROOT)): _runtime().hash_file(path) for path in paths}


class ExternalBudget:
    """One sequential portfolio's aggregate resource reservation, not authority.

    CPU reservation includes each child's OS hard-limit extra second. Reservations
    are never refunded. Calls share a <=30s wall deadline and 512MiB RSS ceiling.
    The outer pilot must also budget its native workers separately.
    """
    def __init__(self, cpu_seconds=MAX_CPU_SECONDS, wall_seconds=30):
        if (type(cpu_seconds) is not int or not 2 <= cpu_seconds <= MAX_CPU_SECONDS
                or type(wall_seconds) is not int or not 1 <= wall_seconds <= 30):
            raise ExportError("external aggregate budget exceeds reviewed bounds")
        self._cpu_limit = cpu_seconds
        self._reserved = 0
        self._deadline = time.monotonic() + wall_seconds
        self._records = []
        self._capabilities = {}

    def snapshot(self):
        return {"cpu_hard_limit_reserved_seconds": self._reserved,
                "cpu_hard_limit_ceiling_seconds": self._cpu_limit,
                "rss_ceiling_bytes": MAX_RSS_BYTES, "max_workers": 1,
                "process_count": len(self._records),
                "measured_child_cpu_seconds": sum(r["resources"]["cpu_seconds"] for r in self._records)}

    def _run(self, command, seconds, input_bytes=b""):
        if type(seconds) is not int or not 1 <= seconds <= 10:
            raise ExportError("one external call must reserve 1..10 CPU seconds")
        if not _WORKER_LOCK.acquire(blocking=False):
            raise ExportError("only one external worker may run at a time")
        try:
            if self._reserved + seconds + 1 > self._cpu_limit:
                return None
            wall = min(seconds + 1, math.floor(self._deadline - time.monotonic()))
            if wall < seconds:
                return None
            self._reserved += seconds + 1
            supervisor = _runtime()
            limits = supervisor.ProcessLimits(wall_seconds=wall, cpu_seconds=seconds,
                rss_bytes=MAX_RSS_BYTES, output_bytes=MAX_EXPORT_BYTES)
            record = supervisor.run_bounded(tuple(command), cwd=ROOT, limits=limits,
                                             input_bytes=input_bytes)
            supervisor.validate_process_record(record, command=tuple(command), limits=limits,
                                               input_bytes=input_bytes)
            self._records.append(deepcopy(record))
            return record
        finally:
            _WORKER_LOCK.release()


def _successful(record):
    return (type(record) is dict and record.get("reason") == "exited"
            and type(record.get("returncode")) is int and record["returncode"] == 0
            and record.get("output_truncated") is False)


def probe_solver(solver, *, budget, executable=None):
    """Probe PATH or ONE explicitly configured path; never install or broad-scan."""
    if solver not in SOLVERS or type(solver) is not str or type(budget) is not ExternalBudget:
        raise ExportError("unknown solver or foreign budget")
    if executable is not None and (not isinstance(executable, (str, Path))
                                   or not Path(executable).is_absolute()):
        raise ExportError("configured executable must be one absolute path")
    found = str(executable) if executable is not None else shutil.which(solver)
    if found is None or not Path(found).is_file():
        return {"solver": solver, "status": "unavailable", "path": found,
                "discovery": "explicit_path" if executable is not None else "PATH"}
    path = Path(found).resolve(strict=True)
    if not os.access(path, os.X_OK):
        raise ExportError("configured solver is not executable")
    pin = _runtime().hash_file(path, maximum=256 * 1024**2)
    key = (solver, str(path), pin["sha256"])
    if key in budget._capabilities:
        result = deepcopy(budget._capabilities[key])
        result["version_probe_reused_same_binary"] = True
        return result
    args = (str(path), "-version" if solver == "z3" else "--version")
    process = budget._run(args, 1)
    if _runtime().hash_file(path, maximum=256 * 1024**2) != pin:
        raise ExportError("solver binary changed during its version probe")
    result = {"solver": solver, "status": "available" if _successful(process) else "probe_failed_or_budget_exhausted",
              "path": str(path), "binary": pin, "version_probe": process,
              "version_probe_reused_same_binary": False,
              "interface": "version_observed; proof interface must still succeed in the actual bounded call"}
    if result["status"] == "available":
        budget._capabilities[key] = deepcopy(result)
    return result


def solver_argv(solver, executable, seconds):
    if type(seconds) is not int or not 1 <= seconds <= 10:
        raise ExportError("invalid fixed solver time limit")
    if not Path(executable).is_absolute():
        raise ExportError("solver path must be absolute")
    if solver == "z3":
        return (str(executable), "-in", "-smt2", f"-T:{seconds}", "-memory:512")
    if solver == "eprover":
        return (str(executable), "--auto", "--proof-object", "--tptp3-format",
                f"--cpu-limit={seconds}", "--memory-limit=512")
    if solver == "vampire":
        # Default Vampire mode is single process; NEVER --mode portfolio/casc.
        return (str(executable), "--input_syntax", "tptp", "--proof", "tptp", "-t", str(seconds))
    raise ExportError("unknown solver")


def _observation(record, solver):
    if not _successful(record):
        return {"solver_status": "unknown_or_process_failure", "proof_shaped_output_present": False}
    output = record["stdout"]
    if solver == "z3":
        first = output.splitlines()[0] if output else ""
        status = first if first in ("unsat", "sat", "unknown") else "unrecognized"
        proof = status == "unsat" and "(proof" in output
    else:
        statuses = re.findall(r"^[%#]\s*SZS status ([A-Za-z]+)\b", output, flags=re.MULTILINE)
        status = statuses[0] if len(set(statuses)) == 1 else "unrecognized"
        proof = (status in ("Theorem", "Unsatisfiable", "ContradictoryAxioms")
                 and re.search(r"^[%#]\s*SZS output start (?:Proof|CNFRefutation)\b", output, re.MULTILINE) is not None)
    return {"solver_status": status, "proof_shaped_output_present": bool(proof)}


def invoke_solver(problem, solver="z3", *, budget, seconds=3, executable=None):
    """Run exactly one source-bound solver; result is NEVER HA evidence."""
    checked = validate_problem(problem)
    if solver not in SOLVERS or type(solver) is not str:
        raise ExportError("unknown solver")
    if checked["format"] != ("smt2" if solver == "z3" else "tptp"):
        raise ExportError("solver and export format disagree")
    if type(seconds) is not int or not 1 <= seconds <= 10:
        raise ExportError("invalid solver reservation")
    before = source_pins()
    capability = probe_solver(solver, budget=budget, executable=executable)
    record, argv = None, None
    if capability["status"] == "available":
        argv = solver_argv(solver, capability["path"], seconds)
        record = budget._run(argv, seconds, checked["input"].encode())
        if _runtime().hash_file(Path(capability["path"]), maximum=256 * 1024**2) != capability["binary"]:
            raise ExportError("solver binary changed during actual execution")
    if source_pins() != before or validate_problem(problem) != checked:
        raise ExportError("export or adapter inputs changed during execution")
    return {"schema": SCHEMA, "authority": "untrusted_classical_search_hint_only",
        "solver": solver, "capability": capability, "argv": list(argv) if argv else None,
        "target_ast_sha256": checked["target"]["ast_sha256"],
        "premises": [{"name": r["name"], "ast_sha256": r["ast_sha256"]} for r in checked["premises"]],
        "input_sha256": checked["input_sha256"], "export_sha256": checked["export_sha256"],
        "source_pins": before, "process": record, "observation": _observation(record, solver),
        "ha_checked": False, "proof_log_checked": False, "ha_translation_verified": False,
        "solver_proofs_reconstructed": 0, "model_proof_search_calls": 0,
        "IR_obligations_closed": 0, "budget": budget.snapshot()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", choices=SOLVERS)
    parser.add_argument("--executable", type=Path)
    parser.add_argument("--target")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args(argv)
    if args.executable and not args.solver:
        parser.error("--executable requires --solver")
    if args.run and (not args.target or not args.solver):
        parser.error("--run requires --target and --solver")
    budget = ExternalBudget()
    if args.target:
        format = "tptp" if args.solver in ("eprover", "vampire") else "smt2"
        result = export_problem(args.target, format=format)
        if args.run:
            result = invoke_solver(result, args.solver, budget=budget, executable=args.executable)
    else:
        result = {name: probe_solver(name, budget=budget, executable=args.executable)
                  for name in ((args.solver,) if args.solver else SOLVERS)}
    print(canonical(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
