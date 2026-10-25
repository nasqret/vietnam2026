"""Prepared two-backend native gate. Run only when the parent schedules it.

Exactly one egg and one E request; no retry, model, HTTP, full proof search,
Vampire, SymPy, or cvc5. Every positive comes from the actual backend output.
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
OUTPUT = HERE.parent / "p9-integration-01"
SOURCES = ("adviser_protocol.py", "adviser_process.py", "adviser_worker.py", "p9_bridge_common.py",
           "egraph_bridge.py", "e_bridge.py", "vampire_bridge.py", "vampire_process.py", "vampire_limits.py")
CASES = (
    {"id": "egg_congruence_distribution", "backend": "egg",
     "theorem": "forall a b c. S (a * (b + c)) = S (a * b + a * c)",
     "negative": "forall a b c. S (a * (b + c)) = S (S (a * b + a * c))",
     "prefix": ["intro a", "intro b", "intro c"]},
    {"id": "e_equality_chain", "backend": "e",
     "theorem": "forall a b c. a = b -> b = c -> a = c",
     "negative": "forall a b c. a = b -> b = c -> a = S c",
     "prefix": ["intro a", "intro b", "intro c", "intro H", "intro K"]},
)


def pin(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def write(name, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if len(raw) > 1024**2:
        raise ValueError("P9 gate record exceeds one MiB.")
    with (OUTPUT / name).open("xb") as stream:
        stream.write(raw)


def main():
    signal.alarm(90)
    resource.setrlimit(resource.RLIMIT_CPU, (75, 75))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic()
    before = {name: pin(APP / name) for name in SOURCES}
    manifest = pin(APP / ".runtime/advisers/p9-native-01/manifest.json")
    write("plan.json", {"schema": "hydra-p9-real-integration-plan-v1", "cases": CASES,
        "source_pins": before, "native_package_manifest": manifest,
        "actual_helper_launch_ceiling": 2, "per_backend_requests": 1,
        "cpu_seconds": 75, "wall_seconds": 90,
        "max_native_candidate_attempts_per_backend": 12,
        "independent_original_theorem_replay": True, "negative_replay": True,
        "automatic_retry": False, "model_calls": 0, "proof_search_runs": 0, "http_requests": 0})
    sys.path[:0] = [str(ROOT / "hydra-playground"), str(APP)]
    import worker
    validate_statement, run_proof, SurfaceCapabilities, _, _ = worker.load_kernel()
    sys.path.insert(0, str(APP))
    from adviser_protocol import AdviserSession, canonical_json
    from adviser_process import AdviserRunner
    from egraph_bridge import EGraphAdvisor
    from e_bridge import EAdvisor
    from peano_lab.engine.state import start
    from peano_lab.engine.tactics import apply_tactic
    from peano_lab.kernel.formulas import parse_formula_with_names

    class RecordingRunner(AdviserRunner):
        def __call__(self, lease):
            result = super().__call__(lease)
            (OUTPUT / (self.backend + ".stdin")).write_bytes(lease.request.data)
            (OUTPUT / (self.backend + ".stdout")).write_bytes(result["stdout"])
            (OUTPUT / (self.backend + ".stderr")).write_bytes(result["stderr"])
            return result

    capabilities = SurfaceCapabilities(label="p9-real-native-gate-v1", allowed_commands=frozenset(
        {"intro", "trans", "congr", "ring", "refl", "rewrite", "exact", "apply", "assumption", "symm", "exfalso"}),
        allowed_theorems=frozenset())
    authority = hashlib.sha256(canonical_json({"kernel": worker.KERNEL_PINS,
        "commands": sorted(capabilities.allowed_commands), "theorems": [], "resolver": "none"})).hexdigest()
    worker_pin = pin(Path(worker.__file__))
    write("native-authority.json", {"native_kernel_pins": worker.KERNEL_PINS,
        "worker_source": worker_pin, "authority_identity": authority,
        "commands": sorted(capabilities.allowed_commands), "theorems": [], "resolver": "none",
        "classical": False})
    session = AdviserSession(deadline=started + 80, max_requests=2)
    results = []
    for spec in CASES:
        theorem = validate_statement(spec["theorem"])
        target, names = parse_formula_with_names(theorem)
        state = start(target, names)
        for command in spec["prefix"]:
            tactic, _, arguments = command.partition(" ")
            state = apply_tactic(state, tactic, arguments)
        runner = RecordingRunner(spec["backend"])
        constructor = EGraphAdvisor if spec["backend"] == "egg" else EAdvisor
        adviser = constructor(session, runner, capabilities=capabilities, authority_identity=authority)
        advice = adviser.advise(state)
        record = {"id": spec["id"], "backend": spec["backend"], "theorem": theorem, "advice": advice,
            "runner_records": runner.records, "adviser_report": adviser.report(), "kernel_checked": False,
            "independent_replay_checked": False, "negative_rejected": False, "native_candidate_attempts": []}
        if advice["status"] == "advisory_candidate" and runner.calls == 1:
            for index, candidate in enumerate(advice["candidates"][:12]):
                commands = tuple(spec["prefix"]) + tuple(candidate)
                first = run_proof(theorem, commands, request_id=f"p9-{spec['backend']}-candidate-{index}",
                                  classical=False, on_error="stop", capabilities=capabilities)
                record["native_candidate_attempts"].append(first.to_dict(include_trace=False))
                if not first.kernel_checked or first.theorem != theorem:
                    continue
                second = run_proof(theorem, commands, request_id=f"p9-{spec['backend']}-independent",
                                   classical=False, on_error="stop", capabilities=capabilities)
                negative = run_proof(validate_statement(spec["negative"]), commands,
                                    request_id=f"p9-{spec['backend']}-negative", classical=False,
                                    on_error="stop", capabilities=capabilities)
                record.update(commands=commands, kernel_checked=True,
                    independent_replay_checked=second.kernel_checked and second.theorem == theorem,
                    negative_rejected=not negative.kernel_checked,
                    independent=second.to_dict(include_trace=False), negative=negative.to_dict(include_trace=False))
                break
        record["status"] = "complete" if all(record[name] is True for name in
            ("kernel_checked", "independent_replay_checked", "negative_rejected")) else "failed"
        write(spec["id"] + ".json", record)
        results.append(record)
        print(json.dumps({"backend": spec["backend"], "status": record["status"], "advice_status": advice["status"],
                          "actual_helper_launches": runner.calls}), flush=True)
    after = {name: pin(APP / name) for name in SOURCES}
    write("source-pins-after.json", after)
    ledger = session.report()
    success = (all(record["status"] == "complete" for record in results) and before == after
               and manifest == pin(APP / ".runtime/advisers/p9-native-01/manifest.json")
               and ledger["requests"] == ledger["actual_launches"] == 2 and ledger["active_request"] is None
               and all(row["runner_records"][0]["quiescent"] for row in results)
               and all(row["adviser_report"]["confirmed_backend_executions"] == 1 for row in results)
               and worker_pin == pin(Path(worker.__file__)))
    result = {"schema": "hydra-p9-real-integration-result-v1", "status": "complete" if success else "failed",
        "cases": [{key: row[key] for key in ("id", "backend", "status", "kernel_checked", "independent_replay_checked", "negative_rejected")} for row in results],
        "shared_ledger": ledger, "native_package_manifest": manifest, "source_pins_unchanged": before == after,
        "elapsed_seconds": time.monotonic() - started,
        "worker_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "model_calls": 0, "proof_search_runs": 0, "http_requests": 0, "other_solver_launches": 0}
    write("result.json", result)
    print(json.dumps({"status": result["status"], "actual_helper_launches": ledger["actual_launches"],
                      "elapsed_seconds": result["elapsed_seconds"]}), flush=True)
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
