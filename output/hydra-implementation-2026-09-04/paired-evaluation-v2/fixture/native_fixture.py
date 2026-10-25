"""Two nonreserved CPU compatibility cases; never a study or GPU reservation.

Preparation only hashes files. Running requires a separate one-use fixture
authorization. The first child must prove and replay equality symmetry; the
false second case must remain unproved before an intentional owned-child kill.
Neither path enters the study controller or relaxes its Slurm admission.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.abc
import json
import os
from pathlib import Path
import platform
import resource
import secrets
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
CONTROL = HERE.parent
sys.path.insert(0, str(CONTROL))
import paired_common as common
import paired_controller as controller

SCHEMA = "hydra-nonreserved-cpu-fixture-authorization-v1"
CASES = ("forall a b. a=b -> b=a", "forall a b. a=b -> S b=a")
CASES_SHA = sha256(common.canonical(CASES)).hexdigest()
LIMITS = {"cases": 2, "child_wall_seconds": 12, "child_cpu_seconds": 10,
          "parent_wall_seconds": 35, "parent_cpu_seconds": 10,
          "child_address_bytes": 2 * 1024**3, "parent_address_bytes": 512 * 1024**2,
          "sampled_rss_bytes": 2 * 1024**3, "sample_seconds": 0.05,
          "cleanup_seconds": 3, "stdout_stderr_bytes": 128 * 1024,
          "case_file_bytes": 4 * 1024**2, "case_artifact_bytes": 8 * 1024**2}
WORK = {"max_depth": 16, "max_states": 128, "max_tactic_attempts": 192,
        "max_expansions": 24, "max_frontier": 32, "candidates_per_state": 16,
        "max_macro_steps": 8, "closure_steps": 8, "heuristic_burst": 4,
        "max_model_calls": 0, "max_vampire_calls": 0, "wall_seconds": 2}
CONTROL_PINS = {
    "paired_common.py": "395849fde6e363a96a67aab3fbb7c8f5f82e2a8a6919eb123009ff108800a16d",
    "paired_controller.py": "fc60ec1eb71747c22052c7f433a3c87492dde41b217224bf848d32c35e106e28",
    "paired_case_worker.py": "da5df82dea0c1c5c0eaa5228c77fa75cd88d36e59e91e55efc68e4b3da1cff80",
    "paired_summary.py": "9fc2da301232b1591837da4c63902c139e3b2657897ba671b4e0bc521bcb7fcd",
    "remote_provider_smoke.py": "cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4",
}
FORBIDDEN_IMPORTS = {"torch", "transformers", "mlx", "numpy", "sympy", "cvc5",
                     "jax", "tensorflow", "experimental_model", "model_runtime"}


def fixture_sources(app):
    """Executable sources only: never open or parse the held-out case files."""
    app = Path(app).resolve(strict=True)
    legacy = app.parent / common.ORIGINAL / "training"
    common.require(all((legacy / name).is_file() for name in ("peano_policy/search.py", "peano_hydra/protocol.py")),
                   "Missing exact legacy training/search sources; package the attested ORIGINAL tree, not a training-v5 alias.")
    files = set(app.glob("*.py"))
    for base in (app / "native-v7/peano_lab", app / "training-v5/hydra_training_v5",
                 app.parent / common.ORIGINAL / "training"):
        for path in base.rglob("*.py"):
            files.add(path)
            common.require(len(files) <= 1200, "Fixture source inventory exceeded its bound.")
    files.update(app / name for name in ("native-v7/manifest.json", "training-v5/BASELINE.json",
                                        "experimental-models/qwen3-base-v1.json"))
    common.require(500 <= len(files) <= 1200, "Missing or oversized native compatibility sources.")
    result, total = {}, 0
    for path in sorted(files):
        common.require(path.resolve(strict=True) == path and path.is_relative_to(app.parent),
                       "A fixture source escaped through a symlink.")
        item = common.pin(path)
        total += item["bytes"]
        common.require(total <= 48 * 1024**2, "Fixture source bytes exceeded their bound.")
        result["source/" + str(path.relative_to(app.parent))] = item
    for name, expected in CONTROL_PINS.items():
        item = common.pin(CONTROL / name)
        common.require(item["sha256"] == expected, "The reviewed paired control changed: " + name)
        result["control/" + name] = item
    result["fixture/native_fixture.py"] = common.pin(__file__)
    for name, expected in (("experimental_model.py", common.PROVIDER_SHA),
                           ("native-v7/manifest.json", common.NATIVE_MANIFEST_SHA),
                           ("experimental-models/qwen3-base-v1.json", common.REGISTRY_SHA)):
        common.require(result["source/" + app.name + "/" + name]["sha256"] == expected,
                       "The frozen native/provider metadata changed.")
    return result


def runtime_record():
    common.require(platform.system() == "Linux" and sys.implementation.name == "cpython"
                   and sys.version_info[:2] == (3, 11), "Fixture requires Linux CPython 3.11, not the GPU study runtime.")
    common.require(not sys.flags.ignore_environment and os.environ.get("PYTHONHASHSEED") == "0",
                   "Set PYTHONHASHSEED=0 before launching the fixture; do not use -I/-E.")
    common.require(signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL
                   and all(hasattr(os, name) for name in ("waitid", "P_PID", "WEXITED", "WNOHANG", "WNOWAIT")),
                   "Exclusive non-reaping Linux child ownership is required.")
    executable = Path(sys.executable).resolve(strict=True)
    return {"python": platform.python_version(), "implementation": "cpython", "system": "Linux",
            "machine": platform.machine(), "executable": str(executable),
            "executable_sha256": common.pin(executable, 64 * 1024**2)["sha256"]}


def authorization_spec(value):
    fields = {"schema", "purpose", "nonce", "uid", "app_root", "output", "runtime",
              "source_pins_sha256", "cases_sha256", "limits", "native_work",
              "expected_slurm_job_id", "scheduler_validated", "gpu_allocation_claim",
              "automatic_retry", "resume"}
    common.require(type(value) is dict and set(value) == fields and value["schema"] == SCHEMA
                   and value["purpose"] == "nonreserved_native_lifecycle_compatibility",
                   "Only a separate CPU fixture authorization is accepted.")
    common.require(type(value["uid"]) is int and value["uid"] == os.getuid()
                   and type(value["nonce"]) is str and len(value["nonce"]) == 32
                   and all(char in "0123456789abcdef" for char in value["nonce"]), "Wrong fixture owner/nonce.")
    for name in ("app_root", "output"):
        common.require(type(value[name]) is str and 0 < len(value[name].encode()) <= 4096
                       and "\x00" not in value[name] and Path(value[name]).is_absolute(), "Explicit fixture paths are required.")
    common.require(value["cases_sha256"] == CASES_SHA and common.valid_sha(value["source_pins_sha256"])
                   and common.canonical(value["limits"]) == common.canonical(LIMITS)
                   and common.canonical(value["native_work"]) == common.canonical(WORK),
                   "Fixture inputs or finite limits changed.")
    job = value["expected_slurm_job_id"]
    common.require(job is None or (type(job) is str and job.isascii() and job.isdigit() and 1 <= len(job) <= 20),
                   "An optional observed CPU job ID must be explicit and finite.")
    common.require(all(value[name] is False for name in ("scheduler_validated", "gpu_allocation_claim",
                   "automatic_retry", "resume")), "A fixture cannot claim allocation admission, retry, or resume.")
    return value


def read_authorization(path, expected_sha, *, live):
    raw = common.ordinary(path, 65536)
    common.require(common.valid_sha(expected_sha) and sha256(raw).hexdigest() == expected_sha,
                   "Fixture authorization bytes changed.")
    value = authorization_spec(common.strict_json(raw))
    common.require(value["runtime"] == runtime_record(), "The bound CPU interpreter/runtime changed.")
    if live:
        common.require(os.environ.get("SLURM_JOB_ID") == value["expected_slurm_job_id"],
                       "Fixture entered a different CPU job or unexpectedly claimed a job.")
        common.require(not os.environ.get("CUDA_VISIBLE_DEVICES") and not os.environ.get("SLURM_JOB_GPUS"),
                       "Run this compatibility fixture without a GPU allocation.")
    return value


def claim_authorization(path, expected_sha, value):
    common.require(common.pin(path, 65536)["sha256"] == expected_sha, "Authorization changed before consumption.")
    claim = Path(path).with_name(Path(path).name + ".claimed")
    common.save(claim, {"schema": "hydra-cpu-fixture-consumption-v1", "authorization_sha256": expected_sha,
        "pid": os.getpid(), "uid": os.getuid(), "host": os.uname().nodename,
        "output": value["output"], "nonce": value["nonce"], "automatic_retry": False})
    return claim


def case_request_spec(request, parent_pid):
    common.require(type(request) is dict and set(request) == {"schema", "authorization",
        "authorization_sha256", "controller_pid", "case_index", "theorem"}
        and request["schema"] == "hydra-cpu-fixture-case-request-v1"
        and type(request["controller_pid"]) is int and request["controller_pid"] == parent_pid,
        "CPU child lacks its exact owning controller.")
    index = request["case_index"]
    common.require(type(index) is int and 0 <= index < len(CASES) and request["theorem"] == CASES[index],
                   "Only the two fixed nonreserved theorem inputs are allowed.")
    return index


def prepare(args):
    app = args.app_root.resolve(strict=True)
    output = args.output.absolute()
    common.require(output.resolve() == output and not output.exists(), "Select a fresh non-symlink output path.")
    sources = fixture_sources(app)
    value = {"schema": SCHEMA, "purpose": "nonreserved_native_lifecycle_compatibility",
        "nonce": secrets.token_hex(16), "uid": os.getuid(), "app_root": str(app), "output": str(output),
        "runtime": runtime_record(), "source_pins_sha256": sha256(common.canonical(sources)).hexdigest(),
        "cases_sha256": CASES_SHA, "limits": LIMITS, "native_work": WORK,
        "expected_slurm_job_id": args.job_id, "scheduler_validated": False,
        "gpu_allocation_claim": False, "automatic_retry": False, "resume": False}
    authorization_spec(value)
    common.save(args.authorization, value)
    print(common.canonical({"authorization": str(args.authorization),
        "authorization_sha256": common.pin(args.authorization)["sha256"], "source_files": len(sources),
        "source_pins_sha256": value["source_pins_sha256"], "prepared_only": True}).decode(), flush=True)
    return 0


def install_child_guard(blocked):
    class NoFramework(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split(".", 1)[0] in FORBIDDEN_IMPORTS:
                blocked.append("import:" + fullname)
                raise RuntimeError("A CPU fixture cannot import a model or solver framework.")
            return None
    def audit(event, args):
        forbidden = event in {"subprocess.Popen", "os.system", "os.fork", "os.forkpty",
            "os.posix_spawn", "os.exec", "os.kill", "os.killpg",
            "socket.connect", "socket.connect_ex", "socket.bind"}
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
            forbidden |= Path(os.fsdecode(args[0])).name in {"evaluation-holdout.json", "paired-slice-reservation.json"}
        if forbidden:
            blocked.append(event)
            raise RuntimeError("The fixture forbids subprocess/network/reserved-input access.")
    sys.meta_path.insert(0, NoFramework())
    sys.addaudithook(audit)


def child(args):
    began = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (LIMITS["child_cpu_seconds"], LIMITS["child_cpu_seconds"] + 1))
    resource.setrlimit(resource.RLIMIT_AS, (LIMITS["child_address_bytes"], LIMITS["child_address_bytes"]))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (LIMITS["case_file_bytes"], LIMITS["case_file_bytes"]))
    def expired(*_):
        raise TimeoutError("CPU compatibility child reached its finite wall ceiling.")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, LIMITS["child_wall_seconds"] - 1)
    blocked = []
    install_child_guard(blocked)
    raw = common.ordinary(args.request, 65536)
    common.require(sha256(raw).hexdigest() == args.request_sha256, "Child request bytes changed.")
    request = common.strict_json(raw)
    index = case_request_spec(request, os.getppid())
    value = read_authorization(request["authorization"], request["authorization_sha256"], live=True)
    claim_path = Path(request["authorization"]).with_name(Path(request["authorization"]).name + ".claimed")
    claim = common.strict_json(common.ordinary(claim_path, 65536))
    directory = args.request.absolute().parent
    common.require(directory == Path(value["output"]) / f"case-{index:02d}" and directory.resolve() == directory
        and claim.get("schema") == "hydra-cpu-fixture-consumption-v1"
        and claim.get("pid") == os.getppid() and claim.get("uid") == os.getuid()
        and claim.get("host") == os.uname().nodename and claim.get("output") == value["output"]
        and claim.get("nonce") == value["nonce"]
        and claim.get("authorization_sha256") == request["authorization_sha256"], "Unbound or repeated CPU child.")
    app = Path(value["app_root"])
    before = fixture_sources(app)
    common.require(sha256(common.canonical(before)).hexdigest() == value["source_pins_sha256"], "CPU source binding changed.")
    common.save(directory / "case-started.json", {"request_sha256": args.request_sha256,
        "pid": os.getpid(), "parent_pid": os.getppid(), "case_index": index})
    search_result = replay = None
    status, error, kernel, counters, original = "infrastructure_failure", None, None, None, None
    try:
        kernel = common.native_identity(app)
        os.chdir(app.parent)
        sys.path[:0] = [str(app), str(app / "native-v7"), str(app.parent / common.ORIGINAL)]
        from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
        from peano_lab.ui.prove import SurfaceCapabilities
        from training.peano_hydra.protocol import validate_statement
        from hybrid_search import HybridLimits, search
        common.require(Path(sys.modules["peano_lab.batch"].__file__).resolve().is_relative_to(app / "native-v7")
            and Path(sys.modules["training.peano_hydra.protocol"].__file__).resolve().is_relative_to(app.parent / common.ORIGINAL)
            and Path(sys.modules["hybrid_search"].__file__).resolve() == app / "hybrid_search.py", "Wrong native import origins.")
        original = validate_statement(request["theorem"])
        capabilities = SurfaceCapabilities(label="hydra-authority-no-imports-v1",
            allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())
        search_result = search(original, capabilities=capabilities, model_policy=None,
            vampire_advisor=None, external_advisors=(), planner_enabled=False, planner_provider=None,
            branch_ranker=None, limits=HybridLimits(**WORK))
        counters = common.validate_counts(search_result, None, None)
        for actual, cap in (("depth_reached", "max_depth"), ("states_discovered", "max_states"),
                            ("states_expanded", "max_expansions"), ("tactic_attempts", "max_tactic_attempts")):
            common.require(search_result[actual] <= WORK[cap], "Fixture native-work bound exceeded.")
        if search_result["status"] == "proof":
            replay = run_proof(original, tuple(search_result["commands"]), request_id="cpu-fixture-independent-original",
                classical=False, on_error="stop", capabilities=capabilities).to_dict(include_trace=False)
        proved = common.proof_acceptance(search_result, replay, original)
        common.require(not (index == 1 and proved), "Unexpected checked proof of the false nonreserved case.")
        common.require(not blocked, "An unexpected execution/import was attempted.")
        status = "proved" if proved else "unknown"
    except BaseException as failure:
        error = {"type": type(failure).__name__, "detail": str(failure)[:1000]}
        status = "resource_stop" if isinstance(failure, (TimeoutError, MemoryError)) else "infrastructure_failure"
    try:
        after = fixture_sources(app)
        common.require(after == before, "CPU fixture sources changed during search/replay.")
    except BaseException as failure:
        after = None
        status, error = "infrastructure_failure", {"type": type(failure).__name__, "detail": str(failure)[:1000]}
    record = {"schema": "hydra-nonreserved-cpu-case-result-v1", "status": status,
        "request_sha256": args.request_sha256, "source_pins_sha256": value["source_pins_sha256"],
        "sources_unchanged": before == after, "original_input_theorem": request["theorem"],
        "canonical_theorem": original, "kernel_identity": kernel, "search": search_result,
        "independent_original_replay": replay, "actual_counters": counters, "error": error,
        "native_checked": status == "proved", "blocked_execution_attempts": blocked,
        "elapsed_seconds": time.monotonic() - began,
        "host_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        "optimizer_updates": 0, "scheduler_calls": 0, "external_solver_calls": 0,
        "reserved_cases_accessed": False, "benchmark_claim": False}
    common.save(directory / "case-result.json", record)
    if index == 1 and status == "unknown":
        common.save(directory / "cleanup-ready.json", {"request_sha256": args.request_sha256,
            "pid": os.getpid(), "parent_pid": os.getppid(), "status": "unknown"})
        while True:
            signal.pause()  # Deliberately killed by this exact owning parent, never another search.
    signal.setitimer(signal.ITIMER_REAL, 0)
    return 0 if status in {"proved", "unknown"} else (3 if status == "resource_stop" else 2)


def artifact_limit(directory):
    entries = list(directory.iterdir())
    if len(entries) > 8 or any(path.is_symlink() or not path.is_file() for path in entries):
        return "case_artifact_inventory_error"
    if sum(path.stat().st_size for path in entries) > LIMITS["case_artifact_bytes"]:
        return "case_artifact_limit"
    return None


def expected_case_outcome(index, theorem, execution, result, request_sha, source_sha):
    status = controller.classify_case(execution, result)
    bound = (type(result) is dict and result.get("request_sha256") == request_sha
        and result.get("source_pins_sha256") == source_sha and result.get("sources_unchanged") is True
        and result.get("original_input_theorem") == theorem and result.get("blocked_execution_attempts") == [])
    if not bound:
        return status, False
    try:
        common.require(result.get("actual_counters") == common.validate_counts(result["search"], None, None),
                       "Returned zero-model/native accounting differs.")
        proved = common.proof_acceptance(result["search"], result.get("independent_original_replay"),
                                         result["canonical_theorem"])
    except (KeyError, TypeError, ValueError):
        return status, False
    expected = ((index == 0 and status == "proved" and proved and result.get("native_checked") is True)
        or (index == 1 and status == "cancelled" and not proved and execution["exit_code"] == -signal.SIGKILL
            and execution.get("forced_cleanup_ready") is True and execution["rss_samples"] >= 1
            and result.get("status") == "unknown" and result.get("native_checked") is False
            and result.get("independent_original_replay") is None))
    return status, expected


def require_scheduler_transport(raw, code):
    common.require(type(code) is int and code == 0, "The CPU scheduler query did not return actual exit 0.")
    common.require(type(raw) is str and len(raw.encode()) <= 65536,
                   "The CPU scheduler query returned malformed or oversized output.")


def supervise(request_path, request_sha, index, stop):
    directory = request_path.parent
    env = {key: value for key, value in os.environ.items() if key in {"PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "SLURM_JOB_ID"}}
    env.update(PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", CUDA_VISIBLE_DEVICES="")
    argv = [sys.executable, "-B", "-s", str(Path(__file__).resolve()), "child",
            "--request", str(request_path), "--request-sha256", request_sha]
    began = time.monotonic()
    process, reason, start, peak, samples, accounting = None, None, None, 0, 0, True
    forced_cleanup_ready = False
    cleanup = {"exit_code": None, "quiescent": True, "leader_reaped": False}
    with (directory / "stdout").open("xb") as stdout, (directory / "stderr").open("xb") as stderr:
        try:
            process = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL,
                stdout=stdout, stderr=stderr, start_new_session=True)
            common.require(os.getpgid(process.pid) == process.pid, "CPU child lacks its owned group.")
            while not controller.peek_owned_exit(process):
                if stop():
                    reason = "cancelled"; break
                if time.monotonic() - began >= LIMITS["child_wall_seconds"]:
                    reason = "case_wall_limit"; break
                if os.fstat(stdout.fileno()).st_size + os.fstat(stderr.fileno()).st_size > LIMITS["stdout_stderr_bytes"]:
                    reason = "stdout_stderr_limit"; break
                limit = artifact_limit(directory)
                if limit is not None:
                    reason = limit; break
                try:
                    # Empty scheduler executable/job are deliberately impossible here:
                    # no descendant can satisfy the unchanged sampler's scheduler rule.
                    observed = controller.sample_owned(process, "", "", start)
                    common.require(not observed["descendants"], "CPU fixture spawned a child process.")
                except (OSError, ValueError) as failure:
                    if controller.peek_owned_exit(process):
                        break
                    accounting = False
                    reason = "owned_process_accounting_error: " + str(failure)[:256]; break
                start, peak, samples = observed["start_ticks"], max(peak, observed["rss_bytes"]), samples + 1
                if observed["rss_bytes"] > LIMITS["sampled_rss_bytes"]:
                    reason = "host_sampled_rss_limit"; break
                ready_path = directory / "cleanup-ready.json"
                if ready_path.exists():
                    ready = common.strict_json(common.ordinary(ready_path, 4096))
                    common.require(index == 1 and ready == {"request_sha256": request_sha,
                        "pid": process.pid, "parent_pid": os.getpid(), "status": "unknown"}, "Wrong forced-cleanup handoff.")
                    forced_cleanup_ready = True
                    reason = "cancelled"; break
                time.sleep(LIMITS["sample_seconds"])
        except BaseException as failure:
            accounting = False
            reason = "controller_error: " + type(failure).__name__ + ": " + str(failure)[:256]
        finally:
            if process is not None:
                cleanup = controller.terminate_owned(process, seconds=LIMITS["cleanup_seconds"], accounting_ok=accounting)
        try:
            reason = artifact_limit(directory) or reason
        except OSError as failure:
            reason = "case_artifact_inventory_error: " + str(failure)[:256]
        if os.fstat(stdout.fileno()).st_size + os.fstat(stderr.fileno()).st_size > LIMITS["stdout_stderr_bytes"]:
            reason = "stdout_stderr_limit"
    record = {"schema": "hydra-cpu-fixture-owned-execution-v1", "argv": argv,
        "helper_launches": int(process is not None), "pid": None if process is None else process.pid,
        "request_sha256": request_sha, "termination_reason": reason or "process_exit",
        "forced_cleanup_ready": forced_cleanup_ready,
        "peak_sampled_host_rss_bytes": peak, "rss_samples": samples,
        "sampled_memory_can_overshoot": True, "elapsed_seconds": time.monotonic() - began,
        "limits": LIMITS, **cleanup}
    common.save(directory / "execution.json", record)
    return record


def run(args):
    began = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (LIMITS["parent_cpu_seconds"], LIMITS["parent_cpu_seconds"] + 1))
    # The child may raise its inherited soft limit to the already declared
    # 2 GiB hard limit; the parent itself retains its 512 MiB soft limit.
    resource.setrlimit(resource.RLIMIT_AS, (LIMITS["parent_address_bytes"], LIMITS["child_address_bytes"]))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (LIMITS["case_file_bytes"], LIMITS["case_file_bytes"]))
    value = read_authorization(args.authorization, args.authorization_sha256, live=True)
    app, output = Path(value["app_root"]), Path(value["output"])
    common.require(output.resolve() == output and not output.exists(), "Fixture output is not fresh or escapes a link.")
    before = fixture_sources(app)
    common.require(sha256(common.canonical(before)).hexdigest() == value["source_pins_sha256"], "Fixture sources changed before launch.")
    output.mkdir(exist_ok=False)
    claim_authorization(args.authorization, args.authorization_sha256, value)
    cancelled = [False]
    handlers = {sig: signal.signal(sig, lambda *_: cancelled.__setitem__(0, True)) for sig in (signal.SIGINT, signal.SIGTERM)}
    rows, executions, error, after, query = [], [], None, None, None
    try:
        common.save(output / "request.json", {"authorization": value, "authorization_sha256": args.authorization_sha256,
            "source_pins_before": before, "nonreserved_cases": list(CASES), "allocation_admission_claim": False})
        if value["expected_slurm_job_id"] is not None:
            query = {"job_id": value["expected_slurm_job_id"], "attempts": 1,
                "elapsed_seconds": None, "output_bytes": None, "actual_exit_code": None,
                "scope": "One read_scontrol transport check of this bound CPU job; no GPU reservation parsing.",
                "error": None}
            query_began = time.monotonic()
            try:
                raw, code = controller.scheduler_helpers().read_scontrol(value["expected_slurm_job_id"])
                query.update(output_bytes=len(raw.encode()), actual_exit_code=code,
                             output_sha256=sha256(raw.encode()).hexdigest())
                require_scheduler_transport(raw, code)
            except BaseException as failure:
                query["error"] = {"type": type(failure).__name__, "detail": str(failure)[:1000]}
                raise
            finally:
                query["elapsed_seconds"] = time.monotonic() - query_began
                common.save(output / "scheduler-transport.json", query)
        for index, theorem in enumerate(CASES):
            common.require(not cancelled[0] and time.monotonic() + LIMITS["child_wall_seconds"] + LIMITS["cleanup_seconds"]
                           < began + LIMITS["parent_wall_seconds"], "No full bounded child/cleanup time remains.")
            directory = output / f"case-{index:02d}"; directory.mkdir(exist_ok=False)
            request = {"schema": "hydra-cpu-fixture-case-request-v1", "authorization": str(args.authorization.absolute()),
                "authorization_sha256": args.authorization_sha256, "controller_pid": os.getpid(),
                "case_index": index, "theorem": theorem}
            path = directory / "case-request.json"; common.save(path, request)
            request_sha = common.pin(path)["sha256"]
            execution = supervise(path, request_sha, index,
                lambda: cancelled[0] or time.monotonic() >= began + LIMITS["parent_wall_seconds"] - LIMITS["cleanup_seconds"])
            executions.append(execution)
            result_path = directory / "case-result.json"
            result = common.strict_json(common.ordinary(result_path)) if result_path.exists() else None
            status, expected = expected_case_outcome(index, theorem, execution, result, request_sha,
                                                      value["source_pins_sha256"])
            row = {"case_index": index, "theorem": theorem, "status": status, "expected_fixture_outcome": expected,
                "execution": execution, "result_pin": common.pin(result_path) if result is not None else None}
            rows.append(row)
            common.save(directory / "case-summary.json", row)
            common.require(expected and execution["quiescent"] and execution["leader_reaped"], "CPU native/lifecycle fixture failed.")
    except BaseException as failure:
        error = {"type": type(failure).__name__, "detail": str(failure)[:1000]}
    finally:
        for sig, old in handlers.items():
            signal.signal(sig, old)
        try:
            after = fixture_sources(app)
            common.require(after == before, "Fixture sources changed during the run.")
        except BaseException as failure:
            after = None
            if error is None:
                error = {"type": type(failure).__name__, "detail": str(failure)[:1000]}
        complete = not cancelled[0] and error is None and len(rows) == 2 and before == after
        record = {"schema": "hydra-nonreserved-cpu-fixture-completion-v1", "passed": complete,
            "cases": rows, "error": error, "cancelled": cancelled[0], "sources_unchanged": before == after,
            "source_pins_sha256": value["source_pins_sha256"], "source_pins_after": after,
            "authorization_sha256": args.authorization_sha256, "runtime": value["runtime"],
            "elapsed_seconds": time.monotonic() - began,
            "native_child_launches": sum(item["helper_launches"] for item in executions),
            "owned_native_executions": executions, "scheduler_transport": query,
            "model_calls": 0, "scheduler_query_attempts": 0 if query is None else query["attempts"],
            "optimizer_updates": 0,
            "reserved_case_executions": 0, "gpu_allocation_claim": False,
            "study_or_gpu_runtime_validation": False, "benchmark_claim": False,
            "automatic_retry": False, "resume": False}
        common.save(output / "completion.json", record)
        print(common.canonical({"passed": complete, "cases": len(rows), "error": error,
                               "elapsed_seconds": record["elapsed_seconds"]}).decode(), flush=True)
    return 0 if complete else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    metadata = commands.add_parser("prepare")
    metadata.add_argument("--app-root", type=Path, required=True)
    metadata.add_argument("--output", type=Path, required=True)
    metadata.add_argument("--authorization", type=Path, required=True)
    metadata.add_argument("--job-id")
    owned = commands.add_parser("run")
    owned.add_argument("--authorization", type=Path, required=True)
    owned.add_argument("--authorization-sha256", required=True)
    worker = commands.add_parser("child")
    worker.add_argument("--request", type=Path, required=True)
    worker.add_argument("--request-sha256", required=True)
    args = parser.parse_args()
    try:
        return {"prepare": prepare, "run": run, "child": child}[args.command](args)
    except BaseException as failure:
        print(common.canonical({"status": "failed", "type": type(failure).__name__,
                               "detail": str(failure)[:1000], "automatic_retry": False}).decode(), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
