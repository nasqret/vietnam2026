"""Original native checker with explicit bounded input admission.

No model is imported. The caller supplies the preserved source root, so the same
host runs on macOS and Linux. In-process calls check deadlines cooperatively;
the caller MUST put the complete model case under an external process watchdog.
Final proof replay always uses a fresh isolated, offline child with a hard wall
timeout. This module never changes the older public worker/profile.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from contextvars import ContextVar
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time
import unicodedata

SOURCE_COMMIT = "dca88930b59e3147a95d0234d804076ccf757a74"
SOURCE_MANIFEST_SHA256 = "8208f41172a375b59592f916836a229a9e784c05d3f9de8d4f7e7e260f62fdf3"
ENVIRONMENT_SHA256 = "8edaaffa8edf1f6d8b187ba3ada5e87c8219374ef556031afbc103948619b69f"
PROFILE = "hydra-sequential-native-v1"
MAX_TRACE_BYTES = 2 * 1024**2
MAX_RESULT_BYTES = 4 * 1024**2
_ACTIVE_REPLAY = ContextVar("hydra_sequential_native_replay", default=None)


def authorized_spawn(executable, args, cwd, env):
    """Narrow Popen audit permission, only during this host's actual replay call."""
    active = _ACTIVE_REPLAY.get()
    return (active is not None and type(args) in (list, tuple) and tuple(args) == active
            and executable == active[0] and cwd is None and env is None)


def authorized_pipe_write(fd):
    """Permit Popen's writable anonymous stdin FD, never a path/regular file."""
    return (_ACTIVE_REPLAY.get() is not None and type(fd) is int
            and stat.S_ISFIFO(os.fstat(fd).st_mode))


class NativeAdmissionError(ValueError):
    """Input is outside the explicit host profile, not a disproof."""


class NativeBudgetExceeded(TimeoutError):
    """No completion after a budget/cancellation boundary can count as proof."""


class NativeIntegrityError(RuntimeError):
    """Source or subprocess proof evidence does not match its identity."""


def _require(condition, message, error=NativeIntegrityError):
    if not condition:
        raise error(message)


def _json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _strict_json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            _require(key not in out, "Duplicate JSON key")
            out[key] = value
        return out

    def bad_constant(_):
        raise NativeIntegrityError("Non-finite JSON number")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad_constant)


@dataclass(frozen=True)
class NativeLimits:
    max_binders: int = 64
    max_ast_nodes: int = 1024
    max_ast_depth: int = 128
    max_formula_bytes: int = 4096
    max_actions: int = 128
    max_action_bytes: int = 512
    max_numeral: int = 64
    max_goals: int = 64
    max_state_bytes: int = 128 * 1024
    trace_bytes: int = 2 * 1024**2
    native_call_seconds: float = 30.0

    def __post_init__(self):
        caps = {"max_binders": 64, "max_ast_nodes": 1024, "max_ast_depth": 128,
                "max_formula_bytes": 4096, "max_actions": 128, "max_action_bytes": 512,
                "max_numeral": 64, "max_goals": 64, "max_state_bytes": 128 * 1024,
                "trace_bytes": 2 * 1024**2}
        for key, cap in caps.items():
            value = getattr(self, key)
            _require(type(value) is int and 0 < value <= cap, "Invalid " + key, ValueError)
        _require(type(self.native_call_seconds) in (int, float)
                 and math.isfinite(self.native_call_seconds) and 0 < self.native_call_seconds <= 30,
                 "Invalid native call wall budget", ValueError)


def _safe_text(value, maximum, *, formula=False):
    _require(type(value) is str and value.strip() and len(value.encode("utf-8")) <= maximum,
             "Expected bounded nonempty UTF-8 text", NativeAdmissionError)
    text = value.replace("\r", " ").replace("\n", " ").replace("\t", " ").strip() if formula else value
    _require(formula or text == text.strip(), "Literal tactic has surrounding whitespace", NativeAdmissionError)
    _require(not any(unicodedata.category(c) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for c in text),
             "Invisible/control characters are not admitted", NativeAdmissionError)
    return text


def _audit_ast(root, limits):
    from peano_lab.kernel.formulas import And, Bot, Eq, Exists, Forall, Imp, Or
    from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
    stack, count, deepest, most_binders = [(root, 1, 0)], 0, 0, 0
    while stack:
        node, depth, binders = stack.pop()
        count += 1
        deepest = max(deepest, depth)
        _require(count <= limits.max_ast_nodes and depth <= limits.max_ast_depth,
                 "Formula exceeds the AST node/depth limits", NativeAdmissionError)
        kind = type(node)
        if kind is Var:
            _require(type(node.index) is int and 0 <= node.index < binders,
                     "Formula has an unbound variable", NativeAdmissionError)
            children = ()
        elif kind in (Zero, Bot):
            children = ()
        elif kind is Succ:
            children = (node.term,)
        elif kind in (Add, Mul, Eq, And, Or, Imp):
            children = (node.left, node.right)
        elif kind in (Exists, Forall):
            binders += 1
            _require(binders <= limits.max_binders, "Formula exceeds the binder limit", NativeAdmissionError)
            children = (node.body,)
        else:
            raise NativeAdmissionError("Unsupported native AST constructor")
        most_binders = max(most_binders, binders)
        stack.extend((child, depth + 1, binders) for child in children)
    return {"ast_nodes": count, "ast_depth": deepest, "maximum_bound_variables": most_binders}


class NativeHost:
    """One authenticated native source in one process; no alternate engines.

    `admit` canonicalizes a bounded closed user formula. All other methods accept
    that canonical theorem (noncanonical input is explicitly canonicalized too).
    `run_prefix` replays the entire literal prefix, preserving the native trace's
    persistent metavariable names. Never rebuild an ongoing state with a fresh
    renderer. The independent replay child is the only child this host starts.
    """
    def __init__(self, source_root, *, limits=NativeLimits(), should_stop=None, python=None):
        self.source_root = Path(source_root).resolve()
        self.limits = limits
        _require(isinstance(limits, NativeLimits), "Expected NativeLimits", TypeError)
        self.should_stop = should_stop or (lambda: False)
        self.python = str(python or sys.executable)
        manifest_path = Path(__file__).with_name("sequential_native_sources.json")
        manifest_raw = manifest_path.read_bytes()
        _require(_sha(manifest_raw) == SOURCE_MANIFEST_SHA256, "Native source inventory changed")
        self._manifest = _strict_json(manifest_raw)
        _require(self._manifest["source_commit"] == SOURCE_COMMIT, "Native source commit differs")
        self.verify_sources()
        for name, module in tuple(sys.modules.items()):
            if name == "peano_lab" or name.startswith("peano_lab."):
                location = getattr(module, "__file__", None)
                _require(location is not None and Path(location).resolve().is_relative_to(self.source_root),
                         "Cannot mix different native sources in one process")
        sys.dont_write_bytecode = True
        sys.path[:0] = [str(self.source_root / "peano-lab/py"), str(self.source_root)]
        from peano_lab import batch
        from peano_lab.engine.trace import render_goals
        from peano_lab.ui.prove import SurfaceCapabilities, oversized_numeral, surface_success_trace_tactic
        self._batch, self._render_goals = batch, render_goals
        self._oversized_numeral, self.success_label = oversized_numeral, surface_success_trace_tactic
        self._caps = SurfaceCapabilities(label="hydra-playground-native-v1",
                                         allowed_commands=batch.MODEL_V1_COMMANDS,
                                         allowed_theorems=frozenset())
        _require(batch.capability_sha256(self._caps) == ENVIRONMENT_SHA256, "Native authority changed")
        self._identity = {"profile": PROFILE, "source_commit": SOURCE_COMMIT,
                          "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
                          "environment_sha256": ENVIRONMENT_SHA256,
                          "allowed_commands": sorted(batch.MODEL_V1_COMMANDS),
                          "allowed_theorems": [], "classical": False, "limits": asdict(limits),
                          "external_case_watchdog_required": True}
        self.last_replay_evidence = None
        self._admissions = {}

    @property
    def identity(self):
        return copy.deepcopy(self._identity)

    @property
    def capabilities(self):
        return self._caps

    def verify_sources(self):
        expected = self._manifest["files"]
        actual = {str(p.relative_to(self.source_root))
                  for p in (self.source_root / "peano-lab/py/peano_lab").rglob("*.py")}
        _require(actual == set(expected), "Native source file inventory differs")
        for relative, record in expected.items():
            path = self.source_root / relative
            _require(not path.is_symlink(), "Native source may not be a symlink")
            raw = path.read_bytes()
            _require(len(raw) == record["bytes"] and _sha(raw) == record["sha256"],
                     "Native source differs: " + relative)

    def _checkpoint(self, deadline):
        _require(type(deadline) in (int, float) and math.isfinite(deadline),
                 "An absolute finite monotonic deadline is required", ValueError)
        if self.should_stop() or time.monotonic() >= deadline:
            raise NativeBudgetExceeded("Native request cancelled or deadline reached")

    def _goals(self, goals):
        _require(type(goals) in (tuple, list) and len(goals) <= self.limits.max_goals
                 and all(type(g) is str and g for g in goals)
                 and sum(len(g.encode()) for g in goals) <= self.limits.max_state_bytes,
                 "Native all-goal state exceeds the host limit", NativeAdmissionError)
        return tuple(goals)

    def admit(self, theorem, *, deadline):
        self._checkpoint(deadline)
        text = _safe_text(theorem, self.limits.max_formula_bytes, formula=True)
        if text in self._admissions:
            return {**copy.deepcopy(self._admissions[text]), "input_theorem": theorem}
        _require(self._oversized_numeral(text, maximum=self.limits.max_numeral) is None,
                 "Theorem numeral exceeds the limit", NativeAdmissionError)
        try:
            target, names = self._batch.parse_formula_with_names(text)
            _require(not names, "Quantify every free variable explicitly", NativeAdmissionError)
            metrics = _audit_ast(target, self.limits)
            canonical = self._batch.pretty_formula(target, list(names))
            _safe_text(canonical, self.limits.max_formula_bytes, formula=True)
            _require(self._oversized_numeral(canonical, maximum=self.limits.max_numeral) is None,
                     "Canonical theorem numeral exceeds the limit", NativeAdmissionError)
        except (ValueError, RecursionError) as exc:
            if isinstance(exc, NativeAdmissionError):
                raise
            raise NativeAdmissionError("Invalid native theorem: " + str(exc)) from exc
        self._checkpoint(deadline)
        result = {"input_theorem": theorem, "theorem": canonical, "profile": PROFILE,
                  "ast_metrics": metrics, "limits": asdict(self.limits)}
        # A host is per-case in production; keep even misuse bounded.
        if len(self._admissions) >= 4:
            self._admissions.clear()
        self._admissions[text] = copy.deepcopy(result)
        return result

    def initial(self, theorem, *, deadline):
        canonical = self.admit(theorem, deadline=deadline)["theorem"]
        target, names = self._batch.parse_formula_with_names(canonical)
        goals = self._goals(self._render_goals(self._batch.start(target, names)))
        self._checkpoint(deadline)
        return goals

    def initial_result(self, theorem, *, deadline):
        admission = self.admit(theorem, deadline=deadline)
        goals = list(self.initial(admission["theorem"], deadline=deadline))
        return {"status": "open", "theorem": admission["theorem"], "original_theorem": theorem,
                "goals": goals, "initial_goals": goals, "trace": [], "kernel_checked": False,
                "proof_nodes": None, "tactics_requested": 0, "tactics_applied": 0,
                "engine_steps": 0, "failed_tactics": 0, "classical": False,
                "mode": "initial-state", "surface": "hydra-playground-native-v1",
                "environment_sha256": ENVIRONMENT_SHA256, "admission": admission}

    def _request(self, theorem, actions, deadline):
        canonical = self.admit(theorem, deadline=deadline)["theorem"]
        _require(type(actions) in (tuple, list) and 0 < len(actions) <= self.limits.max_actions,
                 "Invalid literal action count", NativeAdmissionError)
        for action in actions:
            _safe_text(action, self.limits.max_action_bytes)
            _require(self._oversized_numeral(action, maximum=self.limits.max_numeral) is None,
                     "Tactic numeral exceeds the limit", NativeAdmissionError)
        return {"theorem": canonical, "actions": list(actions)}

    def run_prefix(self, theorem, actions, *, deadline):
        request = self._request(theorem, actions, deadline)
        started = time.monotonic()
        result = self._batch.run_proof(request["theorem"], request["actions"],
            request_id="hydra-sequential-" + _sha(_json_bytes(request))[:24], classical=False,
            on_error="stop", capabilities=self._caps, trace_byte_limit=self.limits.trace_bytes)
        self._checkpoint(min(deadline, started + self.limits.native_call_seconds))
        receipt = result.to_dict(include_trace=True)
        _require(receipt["theorem"] == request["theorem"] and receipt["classical"] is False
                 and receipt["environment_sha256"] == ENVIRONMENT_SHA256, "Native result binding differs")
        self._goals(receipt["goals"])
        # batch.run_proof returns the trace's persistent all-goal spelling.
        # Re-rendering the final state here would reset metavariable aliases.
        return receipt

    def independent_replay(self, theorem, actions, *, deadline):
        request = self._request(theorem, actions, deadline)
        self.last_replay_evidence = None
        self.verify_sources()
        self._checkpoint(deadline)
        seconds = min(self.limits.native_call_seconds, deadline - time.monotonic())
        payload = {**request, "limits": asdict(self.limits), "wall_seconds": seconds}
        command = [self.python, "-I", "-B", str(Path(__file__).resolve()),
                   "--replay-child", "--source-root", str(self.source_root)]
        started = time.monotonic()
        permit = _ACTIVE_REPLAY.set(tuple(command))
        try:
            completed = subprocess.run(command, input=_json_bytes(payload), stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, timeout=seconds, check=False)
        except subprocess.TimeoutExpired as exc:
            self.last_replay_evidence = {"status": "timeout", "actual_exit_code": None,
                                         "seconds": time.monotonic() - started}
            raise NativeBudgetExceeded("Independent native replay exceeded its wall budget") from exc
        finally:
            _ACTIVE_REPLAY.reset(permit)
        self.last_replay_evidence = {"status": "completed", "actual_exit_code": completed.returncode,
            "seconds": time.monotonic() - started,
            "stdout": {"bytes": len(completed.stdout), "sha256": _sha(completed.stdout)},
            "stderr": {"bytes": len(completed.stderr), "sha256": _sha(completed.stderr)}}
        self._checkpoint(deadline)
        _require(len(completed.stdout) <= 4 * 1024**2 and len(completed.stderr) <= 64 * 1024,
                 "Independent replay output exceeded its bound")
        rows = [_strict_json(line) for line in completed.stdout.splitlines()]
        _require(len(rows) == 1 and type(rows[0]) is dict, "Missing independent replay terminal event")
        event = rows[0]
        if completed.returncode != 0 or event.get("type") != "result":
            raise NativeIntegrityError("Independent replay failed: " + str(event.get("error", event)))
        _require(event.get("identity") == self.identity and event.get("request_sha256") == _sha(_json_bytes(request)),
                 "Independent replay source/request identity differs")
        _require(type(event.get("process_id")) is int and event["process_id"] != os.getpid(),
                 "Independent replay did not identify a fresh process")
        self.last_replay_evidence["child_process_id"] = event["process_id"]
        receipt = event["result"]
        _require(receipt.get("theorem") == request["theorem"] and receipt.get("classical") is False
                 and receipt.get("environment_sha256") == ENVIRONMENT_SHA256,
                 "Independent replay theorem/authority differs")
        self._goals(receipt["goals"])
        self.verify_sources()
        self._checkpoint(deadline)
        return receipt


def _offline_child_guard():
    forbidden = {"torch", "transformers", "peft", "tokenizers", "mlx", "mlx_lm", "tensorflow", "jax"}

    def audit(event, args):
        if event.startswith("socket.") or event.startswith("subprocess.") or event in {
                "os.system", "os.fork", "os.forkpty", "os.posix_spawn", "os.exec"}:
            raise PermissionError("Native replay is offline and cannot spawn children")
        if event == "import" and str(args[0]).split(".")[0] in forbidden:
            raise PermissionError("Native replay cannot import model frameworks")
        if event == "open":
            mode, flags = args[1], args[2]
            if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                    isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
                raise PermissionError("Native replay cannot write files")
        if event in {"os.remove", "os.rename", "os.rmdir", "os.mkdir", "os.symlink", "os.link", "os.chmod", "os.chown", "os.utime", "os.truncate"}:
            raise PermissionError("Native replay cannot modify files")
    sys.addaudithook(audit)


def _child_main(source_root):
    import resource
    _require(sys.flags.isolated and sys.dont_write_bytecode, "Replay child requires isolated Python")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    resource.setrlimit(resource.RLIMIT_FSIZE, (4 * 1024**2, 4 * 1024**2))

    def timeout(*_):
        raise NativeBudgetExceeded("Independent replay hard wall limit")
    signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, 5.0)
    try:
        raw = sys.stdin.buffer.read(128 * 1024 + 1)
        _require(len(raw) <= 128 * 1024, "Replay input too large")
        value = _strict_json(raw)
        _require(set(value) == {"theorem", "actions", "limits", "wall_seconds"}, "Unexpected replay fields")
        limits = NativeLimits(**value["limits"])
        seconds = value["wall_seconds"]
        _require(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= limits.native_call_seconds,
                 "Invalid replay child deadline")
        deadline = time.monotonic() + seconds
        signal.setitimer(signal.ITIMER_REAL, seconds)
        _offline_child_guard()
        host = NativeHost(source_root, limits=limits)
        request = host._request(value["theorem"], value["actions"], deadline)
        _require(request["theorem"] == value["theorem"], "Independent replay must receive the canonical original theorem")
        receipt = host.run_prefix(request["theorem"], request["actions"], deadline=deadline)
        host.verify_sources()
        host._checkpoint(deadline)
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
        _require(peak <= 2 * 1024**3, "Replay child exceeded observed RSS limit")
        output = _json_bytes({"type": "result", "identity": host.identity, "process_id": os.getpid(),
                              "request_sha256": _sha(_json_bytes(request)), "result": receipt})
        _require(len(output) <= 4 * 1024**2, "Replay output too large")
        sys.stdout.buffer.write(output + b"\n")
        return 0
    except Exception as exc:
        print(json.dumps({"type": "error", "error_type": type(exc).__name__, "error": str(exc)[:2048]}))
        return 2
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--replay-child", required=True, action="store_true")
    parser.add_argument("--source-root", required=True)
    arguments = parser.parse_args()
    raise SystemExit(_child_main(arguments.source_root))
