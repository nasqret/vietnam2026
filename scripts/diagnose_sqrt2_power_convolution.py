#!/usr/bin/env python3
"""Versioned CV001-v2 diagnostic; run only in the root's bounded worker.

Recreate the exact failed tactic state, then profile the UNMODIFIED original
checker on its normally compiled dependency-curried body. This writes no proof
artifact, accepts no new theorem, checks no ancestor proof, and changes neither
the producer nor any checker function. Returned events are diagnostic evidence.

External supervisor: one worker, CPU <= 15s, wall <= 20s, RSS <= 768MiB,
output <= 64KiB. Internal phase/event guards are additional, not replacements.
"""
from __future__ import annotations

from dataclasses import fields
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

import sqrt2_power_convolution_vanishing as cv
from peano_lab.engine.proof_reduction import compile_local_cuts
from peano_lab.engine.state import final_certificate, start
from peano_lab.engine.tactics import apply_tactic
from peano_lab.kernel import checker
from peano_lab.kernel.formulas import Imp
from peano_lab.kernel.proofs import Proof
from peano_lab.library.proof_bundle import encode_formula

SCHEMA = "sqrt2-power-convolution-v2-checker-diagnostic-v1"
PINS = {
    "scripts/sqrt2_power_convolution_vanishing.py": "7a0d84e8511ee6aa2afb5ce6cece2d912f46ed0ecf9949f05d6840ee7015b953",
    "peano-lab/py/peano_lab/kernel/checker.py": "d7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe",
    "peano-lab/py/peano_lab/engine/proof_reduction.py": "deb17a5a0d5562f73248d6fbaa8db46b923c7bab07e491f37cb98e5e19a8251f",
}
MAX_SECONDS = 15
MAX_EVENTS = 200000
MAX_FAILURES = 8
MAX_OUTPUT_BYTES = 64 * 1024


class DiagnosticBudget(RuntimeError):
    pass


def _pins():
    result = cv.convolution_source_pins()
    for path, digest in PINS.items():
        raw = cv._read(cv.ROOT / path, 2 * 1024**2, digest=digest)
        result[path] = {"bytes": len(raw), "sha256": digest}
    path = Path(__file__).resolve()
    raw = cv._read(path, 64 * 1024)
    result[str(path.relative_to(cv.ROOT))] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    return result


def _proof_children(value):
    return [(field.name, child) for field in fields(value)
            if isinstance((child := getattr(value, field.name)), Proof)]


def _structure(value):
    # The traversal is bounded before compilation too, including LocalHave.
    nodes, deepest, counts, pending = 0, 0, {}, [(value, 1)]
    while pending:
        node, depth = pending.pop()
        nodes += 1
        if nodes > 200000 or depth > 256:
            raise DiagnosticBudget("ordinary structure cap reached")
        deepest = max(deepest, depth)
        name = type(node).__name__
        counts[name] = counts.get(name, 0) + 1
        pending.extend((child, depth + 1) for _, child in _proof_children(node))
    return dict(nodes=nodes, depth=deepest, constructors=counts)


def _paths(proof, wanted):
    result, pending, visits = {}, [(proof, "root")], 0
    while pending and len(result) < len(wanted):
        node, path = pending.pop()
        visits += 1
        if visits > 200000:
            raise DiagnosticBudget("proof path traversal cap reached")
        if id(node) in wanted and id(node) not in result:
            result[id(node)] = path
        pending.extend((child, path + "." + name) for name, child in reversed(_proof_children(node)))
    return result


def _formula_record(formula):
    if formula is None:
        return None
    tree = encode_formula(formula)
    raw = cv._canonical(tree)
    if len(raw) > 32768:
        return dict(type=type(formula).__name__, sha256=sha256(raw).hexdigest(), bytes=len(raw))
    return dict(type=type(formula).__name__, sha256=sha256(raw).hexdigest(), ast=tree)


def diagnose():
    start_time, before = time.monotonic(), _pins()
    deadline = start_time + MAX_SECONDS
    def guard():
        if time.monotonic() >= deadline:
            raise DiagnosticBudget("diagnostic wall guard reached")
    target = cv.frozen_convolution_vanishing_target()
    source_data = cv.convolution_cone_data()
    curried = target
    for name, _, _ in reversed(cv.ROOT_PINS):
        curried = Imp(cv.closed_formula(source_data["root_sources"][name][1]), curried)
    state = start(curried)
    commands = tuple("intro " + name for name, _, _ in cv.ROOT_PINS) + cv._script(cv.convolution_definitions())
    for index, command in enumerate(commands):
        guard()
        tactic, _, argument = command.partition(" ")
        try:
            state = apply_tactic(state, tactic, argument)
        except Exception as error:
            return dict(schema=SCHEMA, status="tactic_failed", command_index=index,
                        command=command, exception_type=type(error).__name__, source_pins=before)
    if state.goals or state.target != curried:
        raise DiagnosticBudget("completed state does not carry exact original curried target")
    raw_proof = final_certificate(state)
    if raw_proof is None:
        raise DiagnosticBudget("unfinished certificate after all exact commands")
    raw_structure = _structure(raw_proof)
    guard()
    compiled = compile_local_cuts(raw_proof)
    compiled_structure = _structure(compiled)
    cv._row_preflight(curried, compiled, cv.BinaryDAGLimits())
    guard()
    failed_checks, failed_strict_inferences, event_count = [], [], 0
    check_code, infer_code = checker._check.__code__, checker._infer.__code__
    strict_parents = {"EqSubst", "EqSym", "EqTrans", "CongS", "CongAdd", "CongMul",
                      "AndElimL", "AndElimR", "ForallElim", "ImpElim"}

    def profile(frame, event, result):
        nonlocal event_count
        if event != "return" or frame.f_code not in (check_code, infer_code):
            return
        event_count += 1
        if event_count > MAX_EVENTS or (event_count % 256 == 0 and time.monotonic() >= deadline):
            raise DiagnosticBudget("original checker diagnostic event/time cap reached")
        local = frame.f_locals
        if frame.f_code is check_code and result is False and len(failed_checks) < MAX_FAILURES:
            failed_checks.append((local["proof"], local["target"], len(local["ctx"])))
        parent = frame.f_back
        if (frame.f_code is infer_code and result is None and parent is not None
                and parent.f_code is infer_code and len(failed_strict_inferences) < MAX_FAILURES):
            owner = parent.f_locals.get("proof")
            if type(owner).__name__ in strict_parents:
                failed_strict_inferences.append((local["proof"], owner, len(local["ctx"])))

    if sys.getprofile() is not None:
        raise DiagnosticBudget("an existing profiler already owns this process")
    try:
        sys.setprofile(profile)
        accepted = checker.check((), compiled, curried)
    finally:
        sys.setprofile(None)
    guard()
    wanted = {id(p) for p, _, _ in failed_checks}
    wanted.update(id(p) for pair in failed_strict_inferences for p in pair[:2])
    paths = _paths(compiled, wanted)
    if before != _pins():
        raise DiagnosticBudget("diagnostic inputs changed during observation")
    return dict(schema=SCHEMA, status="diagnostic_complete", source_pins=before,
        original_target_ast_sha256=cv.TARGET_SHA256,
        dependency_curried_target_ast_sha256=cv.formula_sha256(curried),
        tactic_commands=len(commands), raw_structure=raw_structure, compiled_structure=compiled_structure,
        original_dependency_curried_body_accepted=accepted, original_checker_events=event_count,
        first_failed_checks=[dict(proof_type=type(proof).__name__, path=paths.get(id(proof)),
            context_length=context, target=_formula_record(formula),
            children={name: type(child).__name__ for name, child in _proof_children(proof)})
            for proof, formula, context in failed_checks],
        failed_strict_synthesis=[dict(proof_type=type(proof).__name__, parent_type=type(parent).__name__,
            path=paths.get(id(proof)), parent_path=paths.get(id(parent)), context_length=context,
            parent_children={name: type(child).__name__ for name, child in _proof_children(parent)})
            for proof, parent, context in failed_strict_inferences],
        wall_seconds=time.monotonic() - start_time,
        ancestor_proofs_checked=0, kernel_mutations=0, producer_mutations=0,
        proof_artifacts_written=0, IR_parents_closed=0, library_admissions=0,
        limits=dict(vars(cv.BinaryDAGLimits())),
        authority="diagnostic_only_not_a_closed_convolution_proof")


def main():
    try:
        result = diagnose()
    except Exception as error:
        result = dict(schema=SCHEMA, status="diagnostic_failed", exception_type=type(error).__name__,
                      proof_artifacts_written=0, IR_parents_closed=0, library_admissions=0)
        if isinstance(error, DiagnosticBudget):
            result["detail"] = str(error)
    raw = cv._canonical(result)
    if len(raw) > MAX_OUTPUT_BYTES:
        raw = cv._canonical(dict(schema=SCHEMA, status="diagnostic_output_cap", bytes=len(raw),
                                 proof_artifacts_written=0, IR_parents_closed=0, library_admissions=0))
    print(raw.decode())
    return 0 if result.get("status") == "diagnostic_complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
