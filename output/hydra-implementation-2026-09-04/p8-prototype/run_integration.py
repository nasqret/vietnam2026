"""One predeclared P8 gate; no model, HTTP, search sweep, or automatic retry.

Run only after the owner grants the native/solver slot. Two real backend
proposals get independent complete native replay. Two additional fixed-helper
launches test cancellation/deadline cleanup; they are not solver benchmarks.
"""
from pathlib import Path
import hashlib
import json
import resource
import signal
import sys
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
APP = HERE / "app"
LIVE = ROOT / "hydra-playground"
OUTPUT = HERE.parent / "p8-integration-01"
SOURCES = ("adviser_protocol.py", "adviser_polynomials.py", "adviser_process.py", "adviser_worker.py",
           "sympy_bridge.py", "smt_bridge.py", "vampire_process.py", "vampire_limits.py")
CASES = (
    {"id": "sympy_variable_divisor", "backend": "sympy",
     "theorem": "forall a. exists w. (a + S 0) * w = a * a + a", "prefix": ("intro a",),
     "negative": "forall a. exists w. (a + S 0) * w = S (a * a + a)"},
    {"id": "cvc5_affine_context_witness", "backend": "cvc5",
     "theorem": "forall a b. a + a = b -> exists w. w + w = b",
     "prefix": ("intro a", "intro b", "intro H"),
     "negative": "forall a b. a + a = b -> exists w. w + w = S b"},
)


def pin(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write(name, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if len(raw) > 1024 * 1024:
        raise ValueError("Bounded diagnostic record exceeded 1 MiB.")
    (OUTPUT / name).write_bytes(raw)


def main():
    signal.alarm(90)
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    OUTPUT.mkdir(exist_ok=False)
    before = {name: pin(APP / name) for name in SOURCES}
    write("source-pins-before.json", before)
    write("plan.json", {"schema": "hydra-p8-real-integration-plan-v1", "cases": list(CASES),
        "actual_backend_launch_ceiling": 4, "shared_requests": 12, "shared_external_wall_seconds": 60,
        "outer_wall_seconds": 90, "outer_cpu_seconds": 60, "native_model_calls": 0,
        "automatic_retry": False, "native_certificate_limits": "unchanged original kernel",
        "lifecycle_checks": ["cancel immediately after real fixed-helper launch",
                             "expire an admitted deadline immediately after real fixed-helper launch"],
        "source_pins": before, "package_manifest": pin(APP / ".runtime/advisers/manifest.json")})
    sys.path[:0] = [str(LIVE), str(APP)]
    import worker
    validate_statement, run_proof, SurfaceCapabilities, _, _ = worker.load_kernel()
    sys.path.insert(0, str(APP))
    from adviser_protocol import AdviserSession, canonical_json, prepare_request, semantic_context
    from adviser_polynomials import focus_problem
    import adviser_process
    from adviser_process import AdviserRunner
    from sympy_bridge import SympyAdvisor
    from smt_bridge import SmtAdvisor
    from peano_lab.engine.state import start
    from peano_lab.engine.tactics import apply_tactic
    from peano_lab.kernel.formulas import parse_formula_with_names

    class RecordingRunner(AdviserRunner):
        def __init__(self, backend, label):
            super().__init__(backend)
            self.label = label

        def __call__(self, lease):
            result = super().__call__(lease)
            (OUTPUT / (self.label + ".stdout")).write_bytes(result["stdout"])
            (OUTPUT / (self.label + ".stderr")).write_bytes(result["stderr"])
            return result
    capabilities = SurfaceCapabilities(label="p8-real-native-gate-v1",
        allowed_commands=frozenset({"intro", "exists", "ring", "trans", "rewrite", "symm", "refl"}),
        allowed_theorems=frozenset())
    authority = hashlib.sha256(canonical_json({"kernel": worker.KERNEL_PINS,
        "commands": sorted(capabilities.allowed_commands), "theorems": [], "resolver": "none"})).hexdigest()
    started = time.monotonic()
    session = AdviserSession(deadline=started + 85)
    cases, controls, successful = [], [], True
    saved_state = None
    for description in CASES:
        case_started = time.monotonic()
        theorem = validate_statement(description["theorem"])
        target, names = parse_formula_with_names(theorem)
        state = start(target, names)
        for command in description["prefix"]:
            tactic, _, arguments = command.partition(" ")
            state = apply_tactic(state, tactic, arguments)
        saved_state = state
        runner = RecordingRunner(description["backend"], description["id"])
        cls = SympyAdvisor if description["backend"] == "sympy" else SmtAdvisor
        advisor = cls(session, runner, capabilities=capabilities, authority_identity=authority)
        advice = advisor.advise(state)
        result = {"case_id": description["id"], "backend": description["backend"], "theorem": theorem,
                  "advice": advice, "runner_records": runner.records, "advisor": advisor.report(),
                  "kernel_checked": False, "independent_replay_checked": False, "negative_rejected": False}
        if advice["status"] == "advisory_candidate" and runner.calls == 1:
            commands = tuple(description["prefix"]) + tuple(advice["candidates"][0])
            first = run_proof(theorem, commands, request_id=description["id"] + "-first",
                classical=False, on_error="stop", capabilities=capabilities)
            second = run_proof(theorem, commands, request_id=description["id"] + "-independent",
                classical=False, on_error="stop", capabilities=capabilities)
            negative = run_proof(validate_statement(description["negative"]), commands,
                request_id=description["id"] + "-negative", classical=False,
                on_error="stop", capabilities=capabilities)
            result.update(commands=commands, first=first.to_dict(include_trace=False),
                          independent=second.to_dict(include_trace=False),
                          negative=negative.to_dict(include_trace=False),
                          kernel_checked=first.kernel_checked and first.theorem == theorem,
                          independent_replay_checked=second.kernel_checked and second.theorem == theorem,
                          negative_rejected=not negative.kernel_checked)
        result["elapsed_seconds"] = time.monotonic() - case_started
        successful &= all(result[key] is True for key in
                          ("kernel_checked", "independent_replay_checked", "negative_rejected"))
        cases.append(result)
        write(description["id"] + ".json", result)
        print(json.dumps({"case_id": result["case_id"], "status": advice["status"],
                          "kernel_checked": result["kernel_checked"],
                          "independent_replay_checked": result["independent_replay_checked"],
                          "actual_launches": runner.calls}), flush=True)
    # The two lifecycle checks deliberately stop actual owned fixed helpers
    # before useful work. No fake child, arbitrary CLI, altered helper, solver
    # time increase, or claimed actual checkSat/factorization is involved.
    for mode in ("cancel", "deadline"):
        runner = RecordingRunner("cvc5", "lifecycle-" + mode)
        context = semantic_context(saved_state, capabilities, authority_identity=authority)
        problem = focus_problem(saved_state, "cvc5")
        request = prepare_request("cvc5", problem.payload, context, runner.identity)
        session.should_stop = (lambda: runner.calls > 0) if mode == "cancel" else None
        original_popen = adviser_process.subprocess.Popen
        with session.lease(request) as lease:
            if mode == "deadline":
                def expire_after_actual_spawn(*args, **kwargs):
                    child = original_popen(*args, **kwargs)
                    lease.deadline = time.monotonic()
                    return child
                adviser_process.subprocess.Popen = expire_after_actual_spawn
            try:
                execution = runner(lease)
                lease.record_external(execution, quiescent=execution["quiescent"])
            finally:
                adviser_process.subprocess.Popen = original_popen
                session.should_stop = None
        expected = "cancelled" if mode == "cancel" else "timeout"
        passed = (runner.calls == 1 and execution["status"] == expected
                  and execution["quiescent"] is True and type(execution["exit_code"]) is int)
        control = {"kind": mode, "passed": passed, "runner_records": runner.records,
                   "stdout_bytes": len(execution["stdout"]), "stderr_bytes": len(execution["stderr"]),
                   "actual_helper_launches": runner.calls, "backend_operation_completed": False}
        controls.append(control)
        successful &= passed
        write("lifecycle-" + mode + ".json", control)
    after = {name: pin(APP / name) for name in SOURCES}
    write("source-pins-after.json", after)
    successful &= before == after
    ledger = session.report()
    successful &= ledger["requests"] == 4 and ledger["actual_launches"] == 4 and ledger["active_request"] is None
    summary = {"schema": "hydra-p8-real-integration-result-v1", "status": "complete" if successful else "failed",
        "cases": [{key: row[key] for key in ("case_id", "backend", "kernel_checked",
                  "independent_replay_checked", "negative_rejected", "elapsed_seconds")} for row in cases],
        "lifecycle": controls, "shared_ledger": ledger, "source_pins_unchanged": before == after,
        "native_model_calls": 0, "native_searches": 0, "elapsed_seconds": time.monotonic() - started,
        "worker_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "package_manifest": pin(APP / ".runtime/advisers/manifest.json")}
    write("result.json", summary)
    print(json.dumps({"status": summary["status"], "requests": ledger["requests"],
                      "actual_launches": ledger["actual_launches"], "elapsed_seconds": summary["elapsed_seconds"]}), flush=True)
    return 0 if successful else 2


if __name__ == "__main__":
    raise SystemExit(main())
