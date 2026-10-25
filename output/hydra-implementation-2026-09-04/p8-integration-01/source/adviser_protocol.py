"""Untrusted adviser messages and one finite, shared external-work ledger.

No tactic, kernel check, subprocess, solver import, or theorem acceptance occurs
here.  All goals and the caller's versioned authority are part of a request.
The existing Vampire supervisor can use ``external_request`` + ``lease`` and
``record_external`` without replacing its already reviewed child lifecycle.
"""
from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
import json
import math
import re
import threading
import time


POLICY = "hydra-shared-advisers-deep-v1"
SCHEMA = "hydra-adviser-request-v1"
RESPONSE_SCHEMA = "hydra-adviser-response-v1"
BACKENDS = frozenset({"vampire", "sympy", "cvc5", "egg", "e"})
MAX_INPUT = 64 * 1024
MAX_OUTPUT = 256 * 1024
MAX_REQUESTS = 12
MAX_EXTERNAL_WALL = 60.0
COMPLETION_RESERVE = 12.0
MAX_AST_NODES = 4096
MAX_AST_DEPTH = 112
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_NAME = re.compile(r"[A-Za-z_][A-Za-z_0-9]{0,63}\Z")


class ProtocolError(ValueError):
    pass


class BudgetStop(ProtocolError):
    pass


def _require(condition, message):
    if not condition:
        raise ProtocolError(message)


def limits_for(backend):
    _require(type(backend) is str and backend in BACKENDS, "Unknown adviser backend.")
    small = backend in {"sympy", "egg"}
    return {"policy": POLICY, "profile": "deep", "cpu_seconds": 1 if small else 6,
            "wall_seconds": 2 if small else 8, "sampled_stop_bytes": 384 * 1024**2,
            "parent_sampled_rss_bytes": 512 * 1024**2, "sample_interval_seconds": 0.02,
            "input_bytes": MAX_INPUT, "output_bytes": MAX_OUTPUT,
            "cleanup_seconds": 0.5, "completion_reserve_seconds": COMPLETION_RESERVE}


def canonical_json(value, maximum=MAX_INPUT):
    """Bound JSON work before encoding; no floats, custom objects, or NaN."""
    stack = [(value, 0)]
    work = text_bytes = 0
    while stack:
        item, depth = stack.pop()
        work += 1
        _require(work <= 32768 and depth <= 128, "JSON structure exceeds its bound.")
        if item is None or type(item) is bool:
            continue
        if type(item) is int:
            _require(abs(item) < 2**63, "JSON integer exceeds its bound.")
        elif type(item) is str:
            _require(len(item) <= maximum, "JSON string exceeds its bound.")
            try:
                text_bytes += len(item.encode("utf-8"))
            except UnicodeError as error:
                raise ProtocolError("Invalid JSON Unicode.") from error
            _require(text_bytes <= maximum, "JSON text exceeds its byte bound.")
        elif type(item) in (list, tuple):
            _require(len(item) <= 32768, "JSON array exceeds its bound.")
            stack.extend((child, depth + 1) for child in item)
        elif type(item) is dict:
            _require(len(item) <= 1024 and all(type(key) is str for key in item),
                     "JSON object exceeds its bound or has non-string keys.")
            stack.extend((child, depth + 1) for pair in item.items() for child in pair)
        else:
            raise ProtocolError("Only non-executable JSON data is allowed.")
    raw = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
                     allow_nan=False).encode("utf-8")
    _require(0 < len(raw) <= maximum, "Encoded JSON exceeds its byte bound.")
    return raw


def read_json(raw, maximum=MAX_OUTPUT):
    _require(type(raw) is bytes and 0 < len(raw) <= maximum, "Invalid bounded JSON input.")

    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "Duplicate JSON key.")
            result[key] = value
        return result

    def integer(value):
        _require(len(value) <= 20, "JSON integer is too long.")
        result = int(value)
        _require(abs(result) < 2**63, "JSON integer exceeds its bound.")
        return result

    def no_float(_):
        raise ProtocolError("Floating-point or non-finite JSON values are unsupported.")

    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_int=integer,
                           parse_float=no_float, parse_constant=no_float)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ProtocolError("Malformed bounded JSON response.") from error
    canonical_json(value, maximum)
    return value


def _name(value):
    _require(type(value) is str and _NAME.fullmatch(value), "Unsupported native surface name.")
    return value


def semantic_context(state, capabilities, *, authority_identity):
    """Serialize the original theorem and ALL ordered, scoped open obligations.

    ``authority_identity`` must identify the caller's actual native source and
    theorem resolver/library edition.  It is not inferred from a display label.
    No AST is truncated and no substitution is executed while binding context.
    """
    from peano_lab.engine.state import MetaVar, ProofState
    from peano_lab.kernel import formulas as f, terms as t
    from peano_lab.ui.prove import SurfaceCapabilities
    _require(type(state) is ProofState and 0 < len(state.goals) <= 32,
             "An adviser requires a bounded nonempty native proof state.")
    _require(type(capabilities) is SurfaceCapabilities
             and capabilities.allowed_commands is not None
             and capabilities.allowed_theorems is not None,
             "Adviser authority must be an explicit finite capability set.")
    _require(type(authority_identity) is str and _HEX.fullmatch(authority_identity),
             "Missing exact native/resolver authority identity.")
    _require(len(capabilities.allowed_commands) <= 128 and len(capabilities.allowed_theorems) <= 128,
             "Adviser capabilities exceed their bound.")
    count = 0

    def tick(depth):
        nonlocal count
        count += 1
        _require(count <= MAX_AST_NODES and depth <= MAX_AST_DEPTH,
                 "The complete adviser semantic context exceeds its AST bound.")

    def term(item, scope, depth, *, meta=False):
        tick(depth)
        if type(item) is t.Zero:
            return ["zero"]
        if type(item) is t.Var:
            _require(type(item.index) is int and 0 <= item.index < scope,
                     "A rigid variable escaped its native scope.")
            return ["var", item.index]
        if type(item) is MetaVar and meta:
            _require(type(item.id) is int and 0 <= item.id < 2**31
                     and type(item.depth) is int and 0 <= item.depth <= 64,
                     "Malformed native metavariable.")
            return ["meta", item.id, item.depth]
        if type(item) is t.Succ:
            return ["succ", term(item.term, scope, depth + 1, meta=meta)]
        if type(item) in (t.Add, t.Mul):
            return ["add" if type(item) is t.Add else "mul",
                    term(item.left, scope, depth + 1, meta=meta),
                    term(item.right, scope, depth + 1, meta=meta)]
        raise ProtocolError("Unsupported native term in adviser context.")

    def formula(item, scope, depth=0, *, meta=False):
        tick(depth)
        if type(item) is f.Bot:
            return ["bot"]
        if type(item) is f.Eq:
            return ["eq", term(item.left, scope, depth + 1, meta=meta),
                    term(item.right, scope, depth + 1, meta=meta)]
        if type(item) in (f.Imp, f.And, f.Or):
            tag = {f.Imp: "imp", f.And: "and", f.Or: "or"}[type(item)]
            return [tag, formula(item.left, scope, depth + 1, meta=meta),
                    formula(item.right, scope, depth + 1, meta=meta)]
        if type(item) in (f.Forall, f.Exists):
            return ["forall" if type(item) is f.Forall else "exists",
                    formula(item.body, scope + 1, depth + 1, meta=meta)]
        raise ProtocolError("Unsupported formula in adviser context.")

    def variables(names):
        _require(len(names) <= 32 and len(set(names)) == len(names),
                 "Malformed or oversized native variable table.")
        return [_name(name) for name in names]

    original_variables = variables(state.variables)
    original = formula(state.target, len(original_variables))
    goals = []
    for goal in state.goals:
        names = variables(goal.variables)
        _require(len(goal.context) <= 64, "Native local context exceeds its bound.")
        context = [[_name(name), formula(value, len(names), meta=True)]
                   for name, value in goal.context]
        goals.append({"variables": names, "context": context,
                      "target": formula(goal.target, len(names), meta=True)})
    _require(len(state.subst) <= 64, "Native substitution environment exceeds its bound.")
    substitutions = []
    for key in sorted(state.subst):
        _require(type(key) is int and 0 <= key < 2**31, "Invalid substitution identity.")
        # Stored substitutions have separate occurrence depths. Binding their
        # exact syntax does not claim a scope-valid instantiation or execute it.
        substitutions.append([key, term(state.subst[key], 64, 0, meta=True)])
    authority = {"identity": authority_identity, "label": capabilities.label,
                 "commands": sorted(capabilities.allowed_commands),
                 "theorems": sorted(capabilities.allowed_theorems)}
    return canonical_json({"schema": "hydra-adviser-semantic-context-v1",
        "original_target": original, "original_variables": original_variables,
        "goals": goals, "substitutions": substitutions, "authority": authority})


@dataclass(frozen=True)
class AdviserRequest:
    backend: str
    data: bytes
    context: bytes
    identity: bytes

    @property
    def input_sha256(self):
        return hashlib.sha256(self.data).hexdigest()

    @property
    def context_sha256(self):
        return hashlib.sha256(self.context).hexdigest()

    @property
    def exact_cache_key(self):
        # A future cache must use exact input AND semantics, not digest equality.
        return self.backend, self.data, self.context, self.identity


def external_request(backend, data, context, identity):
    """Bind a trusted runner's existing exact stdin, including Vampire TPTP."""
    limits_for(backend)
    _require(type(data) is bytes and 0 < len(data) <= MAX_INPUT and b"\0" not in data,
             "External adviser stdin exceeds its bound.")
    parsed_context = read_json(context, MAX_INPUT)
    _require(type(parsed_context) is dict
             and parsed_context.get("schema") == "hydra-adviser-semantic-context-v1",
             "An external request needs a complete bound semantic context.")
    _require(type(identity) is dict and identity.get("backend") == backend
             and identity.get("profile") == "deep" and type(identity.get("version")) is str,
             "Missing fixed backend/version/profile identity.")
    return AdviserRequest(backend, data, context, canonical_json(identity, 4096))


def prepare_request(backend, payload, context, identity):
    data = canonical_json({"schema": SCHEMA, "backend": backend, "identity": identity,
                           "policy": POLICY, "semantic_context": read_json(context, MAX_INPUT),
                           "payload": payload})
    return external_request(backend, data, context, identity)


class RequestLease:
    def __init__(self, owner, request, number, started):
        self._owner = owner
        self.request = request
        self.number = number
        self.started = started
        self.deadline = min(owner.deadline - COMPLETION_RESERVE,
                            started + limits_for(request.backend)["wall_seconds"])
        self.completed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        if not self.completed:
            self._owner._abandoned(self, "unrecorded_external_attempt")
        return False

    def record_external(self, execution, *, cache_hit=False, quiescent):
        return self._owner.record_external(self, execution, cache_hit=cache_hit,
                                           quiescent=quiescent)


class AdviserSession:
    """One search's shared 12-request/60-second ledger; no per-backend refill.

    Admitted requests include unavailable, cached, failed and resource-stopped
    attempts. Refused dispatches are counted separately, without exceeding the
    admission cap. An unrecorded attempt blocks future work instead of inventing
    zero launches. Existing model token allowances are neither used nor enlarged.
    """
    def __init__(self, *, deadline, should_stop=None, clock=time.monotonic,
                 max_requests=MAX_REQUESTS, max_external_wall=MAX_EXTERNAL_WALL):
        _require(type(deadline) in (int, float) and math.isfinite(deadline), "Invalid search deadline.")
        _require(type(max_requests) is int and 1 <= max_requests <= MAX_REQUESTS,
                 "Shared request cap may only be lowered.")
        _require(type(max_external_wall) in (int, float) and math.isfinite(max_external_wall)
                 and 0 < max_external_wall <= MAX_EXTERNAL_WALL, "Shared wall cap may only be lowered.")
        self.deadline, self.should_stop, self.clock = float(deadline), should_stop, clock
        self.max_requests, self.max_external_wall = max_requests, float(max_external_wall)
        self.requests = self.actual_launches = self.cache_hits = self.refused_requests = 0
        self.external_wall_seconds = 0.0
        self.accounting_complete = True
        self.blocked_reason = None
        self.records = []
        self._active = None
        self._lock = threading.RLock()

    def cancelled(self):
        return bool(self.should_stop is not None and self.should_stop())

    def lease(self, request):
        _require(type(request) is AdviserRequest, "Expected a prepared adviser request.")
        bounds = limits_for(request.backend)
        _require(type(request.data) is bytes and 0 < len(request.data) <= MAX_INPUT
                 and type(request.context) is bytes and 0 < len(request.context) <= MAX_INPUT
                 and type(request.identity) is bytes and 0 < len(request.identity) <= 4096,
                 "A prepared request cannot bypass the fixed byte bounds.")
        with self._lock:
            now = self.clock()
            reason = (self.blocked_reason or ("external_child_busy" if self._active is not None else None)
                or ("cancelled" if self.cancelled() else None)
                or ("shared_request_limit" if self.requests >= self.max_requests else None)
                or ("shared_wall_limit" if self.external_wall_seconds + bounds["wall_seconds"]
                    + bounds["cleanup_seconds"] > self.max_external_wall else None)
                or ("deadline_reserve" if now + bounds["wall_seconds"]
                    + bounds["cleanup_seconds"] + COMPLETION_RESERVE > self.deadline else None))
            if reason:
                self.refused_requests += 1
                raise BudgetStop(reason)
            self.requests += 1
            lease = RequestLease(self, request, self.requests, now)
            self._active = lease
            return lease

    def _abandoned(self, lease, reason):
        with self._lock:
            if lease.completed or self._active is not lease:
                return
            elapsed = max(0.0, self.clock() - lease.started)
            self.external_wall_seconds += elapsed
            self.accounting_complete = False
            self.blocked_reason = reason
            lease.completed = True
            self.records.append({"request": lease.number, "backend": lease.request.backend,
                "status": reason, "actual_launches": None, "quiescent": False,
                "elapsed_seconds": elapsed, "input_sha256": lease.request.input_sha256,
                "context_sha256": lease.request.context_sha256})
            # Keep the lease occupied: an unknown child cannot authorize a next one.

    def record_external(self, lease, execution, *, cache_hit=False, quiescent):
        with self._lock:
            _require(self._active is lease and not lease.completed, "Invalid or duplicate adviser accounting.")
            try:
                _require(type(execution) is dict and type(cache_hit) is bool and type(quiescent) is bool,
                         "Malformed external execution accounting.")
                invocations = execution.get("invocations")
                if invocations is None and type(execution.get("executed")) is bool:
                    invocations = int(execution["executed"])
                _require(type(invocations) is int and invocations in (0, 1), "Unknown actual launch count.")
                if "executed" in execution:
                    _require(type(execution["executed"]) is bool
                             and invocations == int(execution["executed"]), "Conflicting actual launch counts.")
                _require(not cache_hit or invocations == 0, "A cache hit cannot be an actual launch.")
                status = execution.get("status")
                _require(type(status) is str and 0 < len(status) <= 64, "Missing external termination status.")
                reported = execution.get("elapsed_seconds")
                _require(type(reported) in (int, float) and math.isfinite(reported) and reported >= 0,
                         "Missing external wall-time accounting.")
                reported_sha = execution.get("input_sha256", execution.get("problem_sha256"))
                _require(reported_sha == lease.request.input_sha256, "Execution belongs to different exact stdin.")
                elapsed = max(reported, self.clock() - lease.started, 0.0)
                exit_code = execution.get("exit_code")
                _require(exit_code is None or type(exit_code) is int, "Invalid external process exit.")
                _require(not invocations or not quiescent or type(exit_code) is int,
                         "A completed actual process needs its real exit code.")
            except (ProtocolError, TypeError, ValueError):
                self._abandoned(lease, "invalid_external_accounting")
                raise
            self.actual_launches += invocations
            self.cache_hits += int(cache_hit)
            self.external_wall_seconds += elapsed
            record = {"request": lease.number, "backend": lease.request.backend, "status": status,
                "actual_launches": invocations, "cache_hit": cache_hit, "quiescent": quiescent,
                "exit_code": exit_code, "elapsed_seconds": elapsed,
                "input_sha256": lease.request.input_sha256,
                "context_sha256": lease.request.context_sha256,
                "identity": read_json(lease.request.identity, 4096)}
            self.records.append(record)
            lease.completed = True
            if quiescent:
                self._active = None
            else:
                self.blocked_reason = "external_child_not_reaped"
            if self.external_wall_seconds > self.max_external_wall:
                self.blocked_reason = "shared_wall_limit"
            return copy.deepcopy(record)

    def report(self):
        with self._lock:
            return {"policy": POLICY, "requests": self.requests,
                "actual_launches": self.actual_launches if self.accounting_complete else None,
                "known_actual_launches": self.actual_launches, "cache_hits": self.cache_hits,
                "refused_requests": self.refused_requests, "external_wall_seconds": self.external_wall_seconds,
                "accounting_complete": self.accounting_complete, "blocked_reason": self.blocked_reason,
                "active_request": None if self._active is None else self._active.number,
                "limits": {"requests": self.max_requests, "external_wall_seconds": self.max_external_wall,
                           "completion_reserve_seconds": COMPLETION_RESERVE},
                "tokens": {"applicable": False, "reason": "CAS/SMT/ATP transport is byte-bounded, not an LLM decoder."},
                "records": copy.deepcopy(self.records)}


def checked_response(request, execution):
    """An intact bound response is still only evidence for native suggestions."""
    _require(type(execution) is dict and execution.get("status") == "completed"
             and execution.get("executed") is True and type(execution.get("exit_code")) is int
             and execution["exit_code"] == 0 and execution.get("quiescent") is True
             and execution.get("input_sha256") == request.input_sha256,
             "Failed, cancelled, partial, or unbound external output cannot provide advice.")
    raw = execution.get("stdout")
    _require(type(raw) is bytes, "An adviser response must be bounded raw JSON bytes.")
    response = read_json(raw)
    identity = read_json(request.identity, 4096)
    _require(type(response) is dict and response.get("schema") == RESPONSE_SCHEMA
             and response.get("input_sha256") == request.input_sha256
             and response.get("context_sha256") == request.context_sha256
             and response.get("backend") == request.backend
             and response.get("identity") == identity and response.get("kernel_checked") is False,
             "Response does not bind the exact backend, input, context, and advisory authority.")
    return response
