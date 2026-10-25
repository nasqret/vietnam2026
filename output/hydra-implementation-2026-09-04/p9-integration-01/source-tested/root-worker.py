#!/usr/bin/env python3
"""One bounded playground request; the original kernel remains read-only.

Only JSON is read from stdin. Manual replay never imports the model runtime.
The HTTP parent owns cancellation, process cleanup and live RSS observation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import stat
import sys
import time
import unicodedata

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP))
from search_settings import profile as search_profile, public_profiles, validate_selection

SOURCE = APP.parent / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
SOURCE_COMMIT = "dca88930b59e3147a95d0234d804076ccf757a74"
KERNEL_PINS = {
    "training/peano_hydra/protocol.py": "79de9339f485df973e22ee2876d286328fa757896a13d97d74d37207fca4a1bd",
    "peano-lab/py/peano_lab/batch.py": "362d0c502058836fd4793acb068938fc419ed49e39cc5dd7880fd312d65459ef",
    "peano-lab/py/peano_lab/ui/prove.py": "092bfc0a8303af35021f05c016c1a1cd50d223bfeaca68403b905ef872ec569f",
    "peano-lab/py/peano_lab/engine/state.py": "368aa1a6d8e57b48396c0f17d124c280c7ebf5cfdbe8086bc053940af5f72e68",
    "peano-lab/py/peano_lab/engine/trace.py": "d9a7b2aa789fefd8d0da8d6ce6b6ae37b925f92a3e611e0809b02cd5e9173df7",
    "peano-lab/py/peano_lab/kernel/__init__.py": "e4d6cd30f2468de77d6e02fb71bf84394ff8330d264602bb9398df1ad194bc84",
    "peano-lab/py/peano_lab/kernel/checker.py": "d7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe",
    "peano-lab/py/peano_lab/kernel/formulas.py": "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645",
    "peano-lab/py/peano_lab/kernel/proofs.py": "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
    "peano-lab/py/peano_lab/kernel/subst.py": "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3",
    "peano-lab/py/peano_lab/kernel/terms.py": "f49313e209a8861918e3aaca38ddfb27f147f824308af699ab5cc1aafbb6dff5",
}
MAX_BODY_BYTES = 64 * 1024
MAX_RESULT_BYTES = 1024 * 1024
MAX_PROGRESS_BYTES = 4096
MAX_TRACE_BYTES = 512 * 1024
LIMITS = {
    "body_bytes": MAX_BODY_BYTES,
    "theorem_bytes": 4096,
    "tactics": 160,
    "tactic_bytes": 512,
    "numeral": 64,
    "manual": {"wall_seconds": 120, "cpu_seconds": 120, "rss_bytes": 2 * 1024**3},
    "search": {"wall_seconds": 180, "cpu_seconds": 300, "rss_bytes": 8 * 1024**3},
    "vampire": {"wall_seconds": 3, "cpu_seconds": 2, "sampled_rss_bytes": 256 * 1024**2,
                "max_simultaneous_children": 1},
    "result_bytes": MAX_RESULT_BYTES,
    "trace_bytes": MAX_TRACE_BYTES,
    "one_active_computation": True,
    "automatic_retry": False,
    "rss_measurement": "sampled process RSS, not an instantaneous hard cap",
    "profiles": public_profiles(),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def decode_json(raw: bytes) -> dict:
    require(type(raw) is bytes and 0 < len(raw) <= MAX_BODY_BYTES, "Request exceeds the 64 KiB limit.")

    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, "Duplicate JSON keys are not allowed.")
            value[key] = item
        return value

    def invalid(_):
        raise ValueError("Non-finite JSON numbers are not allowed.")

    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (UnicodeError, RecursionError, json.JSONDecodeError) as error:
        raise ValueError("Invalid JSON request.") from error
    require(type(value) is dict, "Request must be a JSON object.")
    return value


def _text(value: object, label: str, maximum: int, *, formula=False) -> str:
    require(type(value) is str and bool(value.strip()), f"{label} must be non-empty text.")
    require(len(value.encode("utf-8")) <= maximum, f"{label} exceeds {maximum} UTF-8 bytes.")
    if formula:
        value = value.replace("\r\n", " ").replace("\r", " ").replace("\n", " ").replace("\t", " ")
    require(not any(unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for char in value),
            f"{label} must be a single line without control characters.")
    return value.strip()


def validate_request(mode: str, value: dict) -> dict:
    """Cheap transport validation only; formula parsing happens in the child."""
    require(mode in ("replay", "search") and type(value) is dict, "Unknown request mode.")
    expected = {"theorem", "tactics"} if mode == "replay" else {"theorem", "max_model_calls", "beam_width"}
    require(expected <= set(value) <= expected | {"experimental"} if mode == "replay" else
            expected <= set(value) <= expected | {"search_mode", "search_profile", "experimental"},
            "Request fields do not match the endpoint.")
    theorem = _text(value["theorem"], "Theorem", LIMITS["theorem_bytes"], formula=True)
    if mode == "replay":
        from experimental_runtime import selection
        experimental = selection(value.get("experimental"), mode=mode)
        commands = value["tactics"]
        require(type(commands) is list and len(commands) <= LIMITS["tactics"],
                f"At most {LIMITS['tactics']} tactic lines are allowed.")
        normalized = {"theorem": theorem, "tactics": [_text(line, "Tactic", LIMITS["tactic_bytes"]) for line in commands]}
        if experimental is not None:
            require(sum(line.split(maxsplit=1)[0] == "use" for line in normalized["tactics"]) <= 8,
                    "An experimental replay admits at most eight checked imports.")
            normalized["experimental"] = experimental
        return normalized
    search_mode = value.get("search_mode", "model")
    require(type(search_mode) is str and search_mode in {"model", "heuristic", "symbolic", "hybrid"},
            "Search mode must be model, heuristic, symbolic, or hybrid.")
    selected_profile = value.get("search_profile", "standard")
    validate_selection(search_mode, selected_profile, value["max_model_calls"], value["beam_width"])
    from experimental_runtime import selection
    experimental = selection(value.get("experimental"), mode=mode, search_mode=search_mode)
    normalized = {"theorem": theorem, "max_model_calls": value["max_model_calls"],
            "beam_width": value["beam_width"], "search_mode": search_mode,
            "search_profile": selected_profile}
    if experimental is not None:
        require(selected_profile in {"standard", "deep"},
                "The first experimental runtime supports only Standard and Deep limits.")
        require(not experimental.get("advisers") or selected_profile=="deep",
                "The new shared external advisers require the fixed Deep profile.")
        normalized["experimental"] = experimental
    return normalized


def resource_limits(mode: str, request: dict) -> dict:
    if mode == "replay":
        return dict(LIMITS["manual"])
    require(mode == "search", "Unknown resource mode.")
    return search_profile(request.get("search_profile", "standard"))["worker"]


def solver_limits(request: dict) -> dict:
    from vampire_limits import solver_limits as selected_solver_limits
    return selected_solver_limits(request.get("search_profile", "standard"))


def kernel_status() -> dict:
    """Check the pinned entrypoints without importing or running the kernel."""
    for name, expected in KERNEL_PINS.items():
        path = SOURCE / name
        require(path.is_file() and not path.is_symlink(), "The preserved kernel source is unavailable.")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, "The preserved kernel entrypoints changed.")
    return {"kernel": "ready", "kernel_source": str(SOURCE), "kernel_commit": SOURCE_COMMIT}


def load_kernel(experimental=None):
    kernel_status()
    sys.dont_write_bytecode = True
    sys.pycache_prefix = "/dev/null"
    if experimental is None:
        sys.path[:0] = [str(SOURCE), str(SOURCE / "peano-lab/py")]
    else:
        from experimental_runtime import activate_native
        activate_native()
    from training.peano_hydra.protocol import validate_statement
    from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
    from peano_lab.ui.prove import SurfaceCapabilities, oversized_numeral
    return validate_statement, run_proof, SurfaceCapabilities, MODEL_V1_COMMANDS, oversized_numeral


def replay(request: dict) -> dict:
    experimental = request.get("experimental")
    validate_statement, run_proof, capabilities_type, commands, oversized_numeral = load_kernel(experimental)
    canonical = validate_statement(request["theorem"])
    for line in request["tactics"]:
        require(oversized_numeral(line, maximum=LIMITS["numeral"]) is None, "Tactic numeral exceeds 64.")
    capabilities = capabilities_type(label="hydra-playground-native-v1", allowed_commands=commands,
                                     allowed_theorems=frozenset())
    library_source = None
    if experimental is not None:
        import experimental_runtime
        capabilities, library_source = experimental_runtime.authority(canonical,experimental,commands,capabilities_type)
    if not request["tactics"]:
        # The genuine batch API requires at least one tactic. Inspect the
        # genuine initial state instead; do not invent a batch trace/footer
        # or run a dummy tactic merely to obtain a goal.
        from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
        from peano_lab.engine.state import start
        from peano_lab.engine.trace import render_goals
        target, names = parse_formula_with_names(canonical)
        require(not names, "Quantify all free variables explicitly.")
        goals = render_goals(start(target, names))
        result = {"status": "open", "theorem": pretty_formula(target, list(names)),
                  "goals": goals, "initial_goals": goals, "kernel_checked": False,
                  "proof_nodes": None, "trace": [], "mode": "initial-state",
                  "tactics_requested": 0, "tactics_applied": 0, "engine_steps": 0,
                  "classical": False, "error": None}
    else:
        from contextlib import nullcontext
        budget = getattr(capabilities,"import_budget",None)
        phase = budget.phase("manual") if budget is not None else nullcontext()
        with phase:
            checked = run_proof(canonical, tuple(request["tactics"]), request_id="playground",
                                classical=False, on_error="stop", capabilities=capabilities,
                                trace_byte_limit=MAX_TRACE_BYTES)
        result = checked.to_dict(include_trace=True)
    if experimental is not None:
        experimental_runtime.native_snapshot()
        if library_source is not None:
            require(experimental_runtime.library_snapshot() == library_source["manifest"],
                    "The library changed during manual replay.")
        budget = getattr(capabilities,"import_budget",None)
        result["experimental"] = {"profile":experimental_runtime.PROFILE, **experimental,
            "native_source_sha256":experimental_runtime.NATIVE_MANIFEST_SHA256,
            "library_source":library_source,"imports":None if budget is None else budget.report()}
    result.update(kind="manual", original_theorem=request["theorem"], commands=request["tactics"],
                  kernel_source_commit=SOURCE_COMMIT, model_used=False)
    return result


def install_guard(mode: str, *, allow_vampire=False, vampire_profile="standard",allowed_advisers=()) -> None:
    forbidden = {"torch", "transformers", "peft", "tokenizers", "accelerate", "tensorflow", "jax", "flax", "mlx", "mlx_lm"}
    if allow_vampire:
        import vampire_process
    if allowed_advisers:
        require(mode=="search" and vampire_profile=="deep" and type(allowed_advisers) in (tuple,list)
                and all(name in {"sympy","cvc5"} for name in allowed_advisers),
                "Only selected fixed Deep adviser helpers may be admitted.")
        import adviser_process

    def audit(event, args):
        if event.startswith("socket."):
            # A denied urllib3 IPv6 capability probe may fall back to False.
            # No socket is created and no network access is permitted.
            raise OSError("Playground workers are offline; network access is disabled.")
        if event == "subprocess.Popen" and allow_vampire and vampire_process.authorized_spawn(
                *args, profile=vampire_profile):
            return
        if event=="subprocess.Popen" and any(adviser_process.authorized_spawn(*args,backend=name)
                                             for name in allowed_advisers):
            return
        if event.startswith("subprocess.") or event in {"os.system", "os.fork", "os.forkpty", "os.posix_spawn", "os.exec", "os.setsid", "os.setpgid"}:
            raise RuntimeError("Playground workers may not start additional processes.")
        if event == "open":
            file_mode, flags = args[1], args[2]
            if (isinstance(file_mode, str) and any(char in file_mode for char in "wax+")) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            ):
                # Popen wraps its anonymous stdin pipe in a writable FileIO.
                # Permit only an existing pipe FD, never a path or regular file.
                if (allow_vampire or allowed_advisers) and type(args[0]) is int and stat.S_ISFIFO(os.fstat(args[0]).st_mode):
                    return
                raise PermissionError("Playground workers cannot write files.")
        if event in {"os.remove", "os.rename", "os.rmdir", "os.mkdir", "os.symlink", "os.link", "os.chmod", "os.chown", "os.utime", "os.truncate"}:
            raise PermissionError("Playground workers cannot modify files.")
        if mode == "replay" and event == "import" and str(args[0]).split(".")[0] in forbidden:
            raise RuntimeError("Manual proof checking cannot import model frameworks.")

    sys.addaudithook(audit)


def emit(kind: str, value: dict) -> None:
    require(type(value) is dict, "Worker event must be an object.")
    raw = json_bytes({"type": kind, kind: value}) + b"\n"
    maximum = MAX_PROGRESS_BYTES if kind == "progress" else MAX_RESULT_BYTES
    require(len(raw) <= maximum, "Worker output exceeded its byte limit.")
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--mode", required=True, choices=("replay", "search"))
    args = parser.parse_args()
    # The short admission timer bounds stdin/JSON work before the selected
    # finite profile is known. After validation, lower the CPU hard limit.
    resource.setrlimit(resource.RLIMIT_CPU, (1200, 1200))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_RESULT_BYTES, MAX_RESULT_BYTES))
    started = time.monotonic()

    def deadline(*_):
        raise TimeoutError("The request reached its wall-time limit.")

    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, 10.0)
    try:
        require(sys.flags.isolated and sys.dont_write_bytecode, "Worker requires isolated Python with bytecode disabled.")
        request = validate_request(args.mode, decode_json(sys.stdin.buffer.read(MAX_BODY_BYTES + 1)))
        limits = resource_limits(args.mode, request)
        resource.setrlimit(resource.RLIMIT_CPU, (limits["cpu_seconds"], limits["cpu_seconds"]))
        signal.setitimer(signal.ITIMER_REAL, max(0.001, limits["wall_seconds"] - (time.monotonic() - started)))
        sys.path.insert(0, str(APP))
        install_guard(args.mode, allow_vampire=args.mode == "search"
                      and request.get("search_mode") in {"symbolic", "hybrid"},
                      vampire_profile=request.get("search_profile", "standard"),
                      allowed_advisers=request.get("experimental",{}).get("advisers",()) if args.mode=="search" else ())
        if args.mode == "replay":
            result = replay(request)
        else:
            validate_statement, *_ = load_kernel(request.get("experimental"))
            request["theorem"] = validate_statement(request["theorem"])
            sys.path.insert(0, str(APP))
            selected_mode = request.pop("search_mode")
            if selected_mode == "model":
                import model_runtime
                # The original model runtime and its exact three-field input
                # contract are preserved byte for byte.
                original_request = {key: request[key] for key in ("theorem", "max_model_calls", "beam_width")}
                result = model_runtime.run_search(original_request, lambda event: emit("progress", event))
            else:
                import hybrid_runtime
                result = hybrid_runtime.run_search({**request, "search_mode": selected_mode},
                                                   lambda event: emit("progress", event))
            require(type(result) is dict and result.get("kind") == selected_mode, "Search runtime returned an invalid result.")
            require(result.get("theorem") == request["theorem"], "Model result changed the original theorem.")
            result["settings_profile"] = request.get("search_profile", "standard")
        usage = resource.getrusage(resource.RUSAGE_SELF)
        peak = usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024)
        require(time.monotonic() - started < limits["wall_seconds"] and peak <= limits["rss_bytes"],
                "The request exceeded its resource limit.")
        emit("result", result)
        return 0
    except (Exception, KeyboardInterrupt) as error:
        message = " ".join(str(error).split())[:2048] or type(error).__name__
        emit("error", {"message": message, "kind": type(error).__name__})
        return 2
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == "__main__":
    raise SystemExit(main())
