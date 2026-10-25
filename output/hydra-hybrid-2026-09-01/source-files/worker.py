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
    "tactics": 64,
    "tactic_bytes": 512,
    "numeral": 64,
    "manual": {"wall_seconds": 45, "cpu_seconds": 30, "rss_bytes": 1024**3},
    "search": {"wall_seconds": 180, "cpu_seconds": 300, "rss_bytes": 8 * 1024**3},
    "vampire": {"wall_seconds": 3, "cpu_seconds": 2, "sampled_rss_bytes": 256 * 1024**2,
                "max_simultaneous_children": 1},
    "result_bytes": MAX_RESULT_BYTES,
    "trace_bytes": MAX_TRACE_BYTES,
    "one_active_computation": True,
    "automatic_retry": False,
    "rss_measurement": "sampled process RSS, not an instantaneous hard cap",
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
    require(set(value) == expected or (mode == "search" and set(value) == expected | {"search_mode"}),
            "Request fields do not match the endpoint.")
    theorem = _text(value["theorem"], "Theorem", LIMITS["theorem_bytes"], formula=True)
    if mode == "replay":
        commands = value["tactics"]
        require(type(commands) is list and len(commands) <= LIMITS["tactics"], "At most 64 tactic lines are allowed.")
        return {"theorem": theorem, "tactics": [_text(line, "Tactic", LIMITS["tactic_bytes"]) for line in commands]}
    require(type(value["max_model_calls"]) is int and value["max_model_calls"] in (8, 16),
            "Model-call budget must be 8 or 16.")
    require(type(value["beam_width"]) is int and value["beam_width"] in (1, 4), "Beam width must be 1 or 4.")
    search_mode = value.get("search_mode", "model")
    require(type(search_mode) is str and search_mode in {"model", "heuristic", "symbolic", "hybrid"},
            "Search mode must be model, heuristic, symbolic, or hybrid.")
    return {"theorem": theorem, "max_model_calls": value["max_model_calls"],
            "beam_width": value["beam_width"], "search_mode": search_mode}


def kernel_status() -> dict:
    """Check the pinned entrypoints without importing or running the kernel."""
    for name, expected in KERNEL_PINS.items():
        path = SOURCE / name
        require(path.is_file() and not path.is_symlink(), "The preserved kernel source is unavailable.")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, "The preserved kernel entrypoints changed.")
    return {"kernel": "ready", "kernel_source": str(SOURCE), "kernel_commit": SOURCE_COMMIT}


def load_kernel():
    kernel_status()
    sys.dont_write_bytecode = True
    sys.pycache_prefix = "/dev/null"
    sys.path[:0] = [str(SOURCE), str(SOURCE / "peano-lab/py")]
    from training.peano_hydra.protocol import validate_statement
    from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
    from peano_lab.ui.prove import SurfaceCapabilities, oversized_numeral
    return validate_statement, run_proof, SurfaceCapabilities, MODEL_V1_COMMANDS, oversized_numeral


def replay(request: dict) -> dict:
    validate_statement, run_proof, capabilities_type, commands, oversized_numeral = load_kernel()
    canonical = validate_statement(request["theorem"])
    for line in request["tactics"]:
        require(oversized_numeral(line, maximum=LIMITS["numeral"]) is None, "Tactic numeral exceeds 64.")
    capabilities = capabilities_type(label="hydra-playground-native-v1", allowed_commands=commands,
                                     allowed_theorems=frozenset())
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
        checked = run_proof(canonical, tuple(request["tactics"]), request_id="playground",
                            classical=False, on_error="stop", capabilities=capabilities,
                            trace_byte_limit=MAX_TRACE_BYTES)
        result = checked.to_dict(include_trace=True)
    result.update(kind="manual", original_theorem=request["theorem"], commands=request["tactics"],
                  kernel_source_commit=SOURCE_COMMIT, model_used=False)
    return result


def install_guard(mode: str, *, allow_vampire=False) -> None:
    forbidden = {"torch", "transformers", "peft", "tokenizers", "accelerate", "tensorflow", "jax", "flax", "mlx", "mlx_lm"}
    if allow_vampire:
        import vampire_process

    def audit(event, args):
        if event.startswith("socket."):
            # A denied urllib3 IPv6 capability probe may fall back to False.
            # No socket is created and no network access is permitted.
            raise OSError("Playground workers are offline; network access is disabled.")
        if event == "subprocess.Popen" and allow_vampire and vampire_process.authorized_spawn(*args):
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
                if allow_vampire and type(args[0]) is int and stat.S_ISFIFO(os.fstat(args[0]).st_mode):
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
    limits = LIMITS["manual" if args.mode == "replay" else "search"]
    resource.setrlimit(resource.RLIMIT_CPU, (limits["cpu_seconds"], limits["cpu_seconds"]))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_RESULT_BYTES, MAX_RESULT_BYTES))
    started = time.monotonic()

    def deadline(*_):
        raise TimeoutError("The request reached its wall-time limit.")

    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, limits["wall_seconds"])
    try:
        require(sys.flags.isolated and sys.dont_write_bytecode, "Worker requires isolated Python with bytecode disabled.")
        request = validate_request(args.mode, decode_json(sys.stdin.buffer.read(MAX_BODY_BYTES + 1)))
        sys.path.insert(0, str(APP))
        install_guard(args.mode, allow_vampire=args.mode == "search"
                      and request.get("search_mode") in {"symbolic", "hybrid"})
        if args.mode == "replay":
            result = replay(request)
        else:
            validate_statement, *_ = load_kernel()
            request["theorem"] = validate_statement(request["theorem"])
            sys.path.insert(0, str(APP))
            selected_mode = request.pop("search_mode")
            if selected_mode == "model":
                import model_runtime
                result = model_runtime.run_search(request, lambda event: emit("progress", event))
            else:
                import hybrid_runtime
                result = hybrid_runtime.run_search({**request, "search_mode": selected_mode},
                                                   lambda event: emit("progress", event))
            require(type(result) is dict and result.get("kind") == selected_mode, "Search runtime returned an invalid result.")
            require(result.get("theorem") == request["theorem"], "Model result changed the original theorem.")
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
