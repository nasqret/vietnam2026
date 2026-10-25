#!/usr/bin/env python3
"""CPU-only admission/reference/countermodel preflight, never model evidence."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
EVALUATION = OUT.parent
EXPECTED_SHA = "4e0c7e0a23385275814ce98142927a264c9c66bf35d0730879473c682653ace0"
sys.path.insert(0, str(ROOT / "hydra-playground"))
from sequential_native import NativeHost, authorized_spawn


def fingerprint(path):
    raw = Path(path).read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def save(path, data):
    with Path(path).open("x") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    return fingerprint(path)


def audit(event, args):
    if event.startswith("socket."):
        raise PermissionError("Native preflight is offline")
    if event == "import" and str(args[0]).split(".")[0] in {"torch", "transformers", "peft", "tokenizers", "mlx", "mlx_lm", "tensorflow", "jax"}:
        raise PermissionError("Native preflight cannot import a model framework")
    if event == "subprocess.Popen":
        assert authorized_spawn(*args), "Only exact fresh native replay may spawn"
    elif event.startswith("subprocess.") or event in {"os.system", "os.fork", "os.forkpty", "os.posix_spawn", "os.exec"}:
        raise PermissionError("Only exact fresh native replay may spawn")


def alarm(*_):
    raise TimeoutError("Native preflight120-second hard limit")


def check_countermodel(formula, assignment):
    from peano_lab.kernel.formulas import And, Bot, Eq, Exists, Forall, Imp, Or
    from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
    # None means an arbitrary unknown natural, not zero. This evaluator only
    # decides quantifiers when their body is independent of that unknown, or
    # proves an existential with the explicit witness zero. No finite search is
    # passed off as a universal proof or existential refutation.
    def term(node, env):
        if type(node) is Zero:
            return 0
        if type(node) is Var:
            return env[node.index]
        if type(node) is Succ:
            value = term(node.term, env)
            return None if value is None else value + 1
        if type(node) in (Add, Mul):
            a, b = term(node.left, env), term(node.right, env)
            return None if a is None or b is None else (a+b if type(node) is Add else a*b)
        raise TypeError(type(node).__name__)
    def truth(node, env):
        if type(node) is Bot:
            return False
        if type(node) is Eq:
            a, b = term(node.left, env), term(node.right, env)
            return None if a is None or b is None else a == b
        if type(node) in (And, Or, Imp):
            a, b = truth(node.left, env), truth(node.right, env)
            if type(node) is Imp:
                return True if a is False or b is True else b if a is True else None
            if type(node) is And:
                return False if a is False or b is False else True if a is b is True else None
            return True if a is True or b is True else False if a is b is False else None
        if type(node) is Forall:
            # A definite value with an arbitrary unknown binder holds uniformly.
            return truth(node.body, [None] + env)
        if type(node) is Exists:
            return True if truth(node.body, [0] + env) is True else None
        raise TypeError(type(node).__name__)
    import re
    names = re.findall(r"∀\s+([A-Za-z][A-Za-z0-9_]*)\.", formula)
    # Only strip the leading forall prefix; inner quantifiers are evaluated by
    # the conservative three-valued semantics above.
    target, free = host._batch.parse_formula_with_names(formula)
    assert not free
    leading = []
    while type(target) is Forall:
        leading.append(names[len(leading)])
        target = target.body
    assert set(assignment) == set(leading)
    env = [assignment[name] for name in reversed(leading)]
    premises = []
    while type(target) is Imp:
        premises.append(truth(target.left, env))
        target = target.right
    conclusion = truth(target, env)
    assert premises and all(value is True for value in premises) and conclusion is False
    return {"method": "standard-natural-number counterassignment; exact three-valued AST evaluation with arbitrary universal binders and explicit existential witness0",
            "assignment": assignment, "premises": premises, "conclusion": conclusion,
            "finite_bound_used_to_decide_universal_quantifier": False,
            "is_native_proof_of_negation": False}


assert sys.flags.isolated and sys.dont_write_bytecode
sys.addaudithook(audit)
signal.signal(signal.SIGALRM, alarm)
signal.setitimer(signal.ITIMER_REAL, 120)
started = time.monotonic()
private_path = EVALUATION / "PRIVATE_EXPECTATIONS.json"
assert fingerprint(private_path)["sha256"] == EXPECTED_SHA
private = json.loads(private_path.read_text())
host = NativeHost(ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831")
report = {"schema": "hydra-precommitted-panel-native-preflight-v1", "native_only": True,
          "fresh_model_calls": 0, "model_frameworks_imported": [], "native_identity": host.identity,
          "private_expectations": fingerprint(private_path), "script": fingerprint(__file__),
          "admissions": [], "reference_scripts": [], "countermodels": []}
for case in private["primary_cases"] + private["regression_cases"]:
    admission = host.admit(case["theorem"], deadline=time.monotonic()+30)
    assert admission["input_theorem"] == case["theorem"]
    report["admissions"].append({"id": case["id"], "canonical_unchanged": admission["theorem"] == case["theorem"],
                                  "admission": admission})
    if "reference_actions_proposed" in case:
        actions = case["reference_actions_proposed"]
        deadline = time.monotonic()+30
        native = host.run_prefix(case["theorem"], actions, deadline=deadline)
        row = {"id": case["id"], "actions": actions, "action_count": len(actions), "native_result": native,
               "proved": False, "model_evidence": False}
        if native["kernel_checked"]:
            replay = host.independent_replay(case["theorem"], actions, deadline=deadline)
            fields = ("step", "goals_before", "focus", "tactic", "goals_after", "status", "error")
            projection = lambda result: [{k:r.get(k) for k in fields} for r in result["trace"] if "v" in r]
            assert replay["kernel_checked"] and projection(native) == projection(replay)
            assert native["proof_nodes"] == replay["proof_nodes"] and replay["trace"][-1]["qed"]
            row.update(proved=True, independent_replay=replay, independent_replay_evidence=host.last_replay_evidence)
        name = case["id"] + "-reference.json"
        saved = save(OUT / name, row)
        report["reference_scripts"].append({"id": case["id"], "proved": row["proved"], "action_count": len(actions),
                                            "status": native["status"], "failed_step": native.get("failed_step"),
                                            "error": native.get("error"), "path": name, **saved})
    if "countermodel" in case:
        report["countermodels"].append({"id": case["id"], "expected": case["expected"],
            **check_countermodel(case["theorem"], case["countermodel"]["assignment"])})
host.verify_sources()
assert fingerprint(private_path)["sha256"] == EXPECTED_SHA
report.update(status="completed", wall_seconds=time.monotonic()-started,
              admitted_count=len(report["admissions"]),
              references_proved=sum(r["proved"] for r in report["reference_scripts"]),
              countermodels_checked=len(report["countermodels"]))
saved = save(OUT / "receipt.json", report)
print(json.dumps({"path": str(OUT / "receipt.json"), **saved, "admitted": report["admitted_count"],
                  "references_proved": report["references_proved"], "countermodels_checked": report["countermodels_checked"],
                  "reference_summaries": report["reference_scripts"]}, ensure_ascii=False))
