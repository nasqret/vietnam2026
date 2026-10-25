"""The one justified SymPy-only follow-up; never runs cvc5 or a model."""
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
OUTPUT = HERE.parent / "p8-sympy-followup-01"
OLD = HERE.parent / "p8-integration-01"
SOURCES = ("adviser_protocol.py", "adviser_polynomials.py", "adviser_process.py", "adviser_worker.py",
           "sympy_bridge.py", "smt_bridge.py", "vampire_process.py", "vampire_limits.py")


def pin(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write(name, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if len(raw) > 1024**2:
        raise ValueError("Follow-up result exceeded 1 MiB.")
    (OUTPUT / name).write_bytes(raw)


def main():
    signal.alarm(60)
    resource.setrlimit(resource.RLIMIT_CPU, (45, 45))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    OUTPUT.mkdir(exist_ok=False)
    before = {name: pin(APP / name) for name in SOURCES}
    previous = json.loads((OLD / "plan.json").read_bytes())["cases"][0]
    failure = json.loads((OLD / "sympy_variable_divisor.json").read_bytes())
    if previous["backend"] != "sympy" or failure["runner_records"][0]["exit_code"] != -signal.SIGXCPU:
        raise ValueError("This follow-up only addresses the observed one-second SymPy CPU stop.")
    package_pin = pin(APP / ".runtime/advisers/cp311-precompiled-01/manifest.json")
    write("plan.json", {"schema": "hydra-p8-sympy-bytecode-followup-plan-v1", "case": previous,
        "previous_cpu_stop": pin(OLD / "sympy_variable_divisor.json"),
        "package_manifest": package_pin, "source_pins": before, "actual_helper_launch_ceiling": 1,
        "helper_cpu_seconds": 1, "helper_wall_seconds": 2,
        "helper_sampled_stop_bytes": 384 * 1024**2, "parent_ceiling_bytes": 512 * 1024**2,
        "outer_wall_seconds": 60, "outer_cpu_seconds": 45,
        "diagnosis_and_change": "Use exact source-bound, checked-hash CPython3.11.12 bytecode instead of compiling pinned dependency source during every new child.",
        "no_cap_increase": True, "automatic_retry": False,
        "cvc5_launches": 0, "model_calls": 0, "searches": 0})
    sys.path[:0] = [str(ROOT / "hydra-playground"), str(APP)]
    import worker
    validate_statement, run_proof, SurfaceCapabilities, _, _ = worker.load_kernel()
    sys.path.insert(0, str(APP))
    from adviser_protocol import AdviserSession, canonical_json
    from adviser_process import AdviserRunner
    from sympy_bridge import SympyAdvisor
    from peano_lab.engine.state import start
    from peano_lab.engine.tactics import apply_tactic
    from peano_lab.kernel.formulas import parse_formula_with_names

    class RecordingRunner(AdviserRunner):
        def __call__(self, lease):
            value = super().__call__(lease)
            (OUTPUT / "solver.stdout").write_bytes(value["stdout"])
            (OUTPUT / "solver.stderr").write_bytes(value["stderr"])
            return value

    capabilities = SurfaceCapabilities(label="p8-real-native-gate-v1",
        allowed_commands=frozenset({"intro", "exists", "ring", "trans", "rewrite", "symm", "refl"}),
        allowed_theorems=frozenset())
    authority = hashlib.sha256(canonical_json({"kernel": worker.KERNEL_PINS,
        "commands": sorted(capabilities.allowed_commands), "theorems": [], "resolver": "none"})).hexdigest()
    theorem = validate_statement(previous["theorem"])
    target, names = parse_formula_with_names(theorem)
    state = start(target, names)
    for command in previous["prefix"]:
        tactic, _, arguments = command.partition(" ")
        state = apply_tactic(state, tactic, arguments)
    started = time.monotonic()
    session = AdviserSession(deadline=started + 55)
    runner = RecordingRunner("sympy")
    advisor = SympyAdvisor(session, runner, capabilities=capabilities, authority_identity=authority)
    advice = advisor.advise(state)
    result = {"schema": "hydra-p8-sympy-bytecode-followup-result-v1", "theorem": theorem,
              "advice": advice, "runner_records": runner.records, "kernel_checked": False,
              "independent_replay_checked": False, "negative_rejected": False}
    if advice["status"] == "advisory_candidate" and runner.calls == 1:
        commands = tuple(previous["prefix"]) + tuple(advice["candidates"][0])
        first = run_proof(theorem, commands, request_id="p8-sympy-bytecode-first", classical=False,
                          on_error="stop", capabilities=capabilities)
        second = run_proof(theorem, commands, request_id="p8-sympy-bytecode-independent", classical=False,
                          on_error="stop", capabilities=capabilities)
        negative = run_proof(validate_statement(previous["negative"]), commands,
                            request_id="p8-sympy-bytecode-negative", classical=False,
                            on_error="stop", capabilities=capabilities)
        result.update(commands=commands, first=first.to_dict(include_trace=False),
            independent=second.to_dict(include_trace=False), negative=negative.to_dict(include_trace=False),
            kernel_checked=first.kernel_checked and first.theorem == theorem,
            independent_replay_checked=second.kernel_checked and second.theorem == theorem,
            negative_rejected=not negative.kernel_checked)
    after = {name: pin(APP / name) for name in SOURCES}
    write("source-pins-after.json", after)
    ledger = session.report()
    success = all(result[key] is True for key in ("kernel_checked", "independent_replay_checked", "negative_rejected"))
    success &= (before == after and ledger["requests"] == ledger["actual_launches"] == 1
                and ledger["active_request"] is None and runner.records[0]["quiescent"] is True)
    result.update(status="complete" if success else "failed", source_pins_unchanged=before == after,
        shared_ledger=ledger, package_manifest=package_pin, elapsed_seconds=time.monotonic() - started,
        worker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        cvc5_launches=0, model_calls=0, searches=0)
    write("result.json", result)
    print(json.dumps({"status": result["status"], "advice_status": advice["status"],
        "kernel_checked": result["kernel_checked"], "independent_replay_checked": result["independent_replay_checked"],
        "actual_launches": ledger["actual_launches"], "elapsed_seconds": result["elapsed_seconds"]}), flush=True)
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
