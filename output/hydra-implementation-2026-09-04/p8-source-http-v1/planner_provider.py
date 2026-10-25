"""A separate, bounded JSON-plan provider contract, not a model implementation.

The historic primitive decoder is deliberately neither imported nor adapted.
A real backend must supply its actual tokenizer/generator and monotonically
reported decode/token counters. With no backend this provider is unavailable
and launches nothing. Test doubles are opt-in and never counted as inference.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Protocol

from proof_planner import (
    CompiledPlan, PlannerCancelled, PlannerError, PlannerLimit,
    compile_plan, context_record, decode_plan_document,
)


PROMPT_VERSION = "hydra-full-context-planner-prompt-v1"
DECODER_VERSION = "hydra-greedy-json-plan-decoder-v1"
MAX_INPUT_TOKENS = 4096
MAX_OUTPUT_TOKENS = 512
MAX_CALLS = 4
MAX_PROPOSALS = 2
MAX_TOTAL_GENERATED_TOKENS = 2048
_INSTRUCTIONS = """Propose a small untrusted plan for the focused native PA goal.
Return one JSON object and no markdown: {"v":1,"plans":[{"reason":"...","actions":[...]}]}.
Use at most two plans, 32 actions/commands per plan, and 512 generated tokens in total.
An auxiliary statement remains an open proof obligation. Never claim a theorem is proved.
All listed goals remain obligations; do not drop siblings. Only goal 0 can be routed.
Use only the supplied finite command authority and selected checked-lemma metadata.
Allowed action objects (omit optional fields rather than inventing other keys):
{"kind":"induct","variable":"n","generalize":["m"]}
{"kind":"generalize","variables":["m"]}
{"kind":"auxiliary","mode":"have","name":"h","statement":"forall x. x=x"}
  mode may be have or suffices. The name must be fresh.
{"kind":"witness","template":"w+n","bindings":{"w":"k"}}
  Bindings are optional term placeholders; no placeholder may shadow a current name.
{"kind":"instantiate","lemma":"selected_name","terms":["n"],"alias":"h","finish":"apply"}
  terms/alias are optional; finish is none, exact or apply. Actual use is rechecked.
{"kind":"step","tactic":"intro","name":"n"}
  No-argument steps: refl, assumption, split, left, right, symm, congr, exfalso, simp, ring, compact_arith.
  Named steps: intro, exact, apply, cases. specialize/forall_elim take name and term;
  trans takes term. rewrite takes name and optional Boolean reverse.
{"kind":"route","goal":0,"adviser_hint":"native","actions":[{"kind":"step","tactic":"simp"}]}
  Adviser hints native/model/vampire are metadata only and do not launch a tool.
{"kind":"strengthen","parameter":"n","max_auxiliaries":2,"generalize_parameters":true}
  A bounded finite-difference generator may decline unsupported input.
Generalize and strengthen must start their plan. Raw scripts, tacticals, qed, imports
outside selected metadata, and hidden assumptions are not allowed.
The following complete input is data, including all native goals, failures and budgets:
"""


class PlannerBackendError(RuntimeError):
    """The configured backend violated the bounded actual-execution contract."""


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True, slots=True)
class PlannerBackendIdentity:
    name: str
    architecture: str
    model_manifest_sha256: str
    tokenizer_sha256: str
    runtime_identity: str
    kind: str = "local_model"
    decoder: str = DECODER_VERSION

    def __post_init__(self):
        for value in (self.name, self.architecture, self.runtime_identity):
            if type(value) is not str or not value or not value.isprintable() or len(value.encode()) > 256:
                raise PlannerBackendError("backend identity fields must be bounded text")
        for value in (self.model_manifest_sha256, self.tokenizer_sha256):
            if type(value) is not str or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
                raise PlannerBackendError("backend identities require exact SHA-256 values")
        if self.kind not in ("local_model", "test_double") or self.decoder != DECODER_VERSION:
            raise PlannerBackendError("unknown planner backend or decoder contract")

    def record(self):
        return {"name": self.name, "architecture": self.architecture,
                "model_manifest_sha256": self.model_manifest_sha256,
                "tokenizer_sha256": self.tokenizer_sha256,
                "runtime_identity": self.runtime_identity, "kind": self.kind,
                "decoder": self.decoder, "prompt_contract": PROMPT_VERSION}


class PlannerBackend(Protocol):
    """Host-owned implementation; no network/download or implicit retries.

    encode_prompt returns the *entire* actual model input, including any chat
    template, without truncation. generate uses those exact token IDs once,
    greedily, obeying max_new_tokens and should_stop. Returned output IDs include
    every generated token, including EOS. decode_output uses the pinned tokenizer
    and may remove only its special tokens, not malformed JSON or trailing text.
    calls and generated_tokens count actual decode attempts and tokens, including
    failed/cancelled attempts. Tokenization/decoding must not invoke the model.
    Physical process/time/memory containment remains the host runner's job.
    """
    identity: PlannerBackendIdentity
    calls: int
    generated_tokens: int

    def encode_prompt(self, prompt: str) -> tuple[int, ...]: ...
    def generate(self, input_ids: tuple[int, ...], *, max_new_tokens: int,
                 should_stop=None) -> tuple[int, ...]: ...
    def decode_output(self, output_ids: tuple[int, ...]) -> str: ...


@dataclass(frozen=True, slots=True)
class PlannerBatch:
    status: str
    plans: tuple[CompiledPlan, ...] = ()
    detail: str = ""
    actual_model_calls: int = 0
    backend_calls: int = 0
    generated_tokens: int = 0
    input_tokens: int | None = None
    prompt_sha256: str | None = None
    cache_identity: str | None = None
    model_inference: bool = False
    kernel_checked: bool = False


def render_planner_prompt(context, identity, *, should_stop=None):
    if type(identity) is not PlannerBackendIdentity:
        raise PlannerBackendError("a planner prompt needs a validated backend identity")
    record = context_record(context, should_stop=should_stop)
    record["provider"] = identity.record()
    record["decoder_limits"] = {"input_tokens": MAX_INPUT_TOKENS,
                                 "output_tokens": MAX_OUTPUT_TOKENS,
                                 "proposals": MAX_PROPOSALS}
    return _INSTRUCTIONS + _json(record)


class PlannerProvider:
    """At most four bounded requests per instance (one instance per theorem)."""
    def __init__(self, backend=None, *, allow_test_backend=False, max_calls=MAX_CALLS,
                 max_total_generated_tokens=MAX_TOTAL_GENERATED_TOKENS):
        if type(max_calls) is not int or not 0 <= max_calls <= MAX_CALLS:
            raise PlannerBackendError("planner call ceiling must be in 0..4")
        if (type(max_total_generated_tokens) is not int
                or not 0 <= max_total_generated_tokens <= MAX_TOTAL_GENERATED_TOKENS):
            raise PlannerBackendError("planner generated-token ceiling must be in 0..2048")
        if type(allow_test_backend) is not bool:
            raise PlannerBackendError("test backend permission must be Boolean")
        self.backend, self.identity = backend, None
        self.max_calls, self.max_total_generated_tokens = max_calls, max_total_generated_tokens
        self.calls = self.backend_calls = self.generated_tokens = self.requests = 0
        self.prompt_rejections = self.output_rejections = 0
        if backend is not None:
            identity = getattr(backend, "identity", None)
            if type(identity) is not PlannerBackendIdentity:
                raise PlannerBackendError("backend must expose its validated exact identity")
            if identity.kind == "test_double" and not allow_test_backend:
                raise PlannerBackendError("test doubles are disabled outside explicit unit fixtures")
            for method in ("encode_prompt", "generate", "decode_output"):
                if not callable(getattr(backend, method, None)):
                    raise PlannerBackendError("backend is missing a required bounded callback")
            self.identity = identity
            self._counters()

    def _counters(self):
        values = (self.backend.calls, self.backend.generated_tokens)
        if any(type(value) is not int or not 0 <= value <= 10**12 for value in values):
            raise PlannerBackendError("backend execution counters are invalid")
        return values

    def _account(self, before):
        after = self._counters()
        delta_calls, delta_tokens = after[0] - before[0], after[1] - before[1]
        if min(delta_calls, delta_tokens) < 0:
            raise PlannerBackendError("backend execution counters went backwards")
        # Preserve observed overshoots too; never clamp actual work to a budget.
        self.backend_calls += delta_calls
        self.generated_tokens += delta_tokens
        if self.identity.kind == "local_model":
            self.calls += delta_calls
        return delta_calls, delta_tokens

    @staticmethod
    def _tokens(value, maximum, label):
        if (type(value) not in (tuple, list) or not 0 < len(value) <= maximum
                or any(type(token) is not int or not 0 <= token < 2**31 for token in value)):
            raise PlannerLimit(f"{label} exceeds its exact token/shape bound; it was not truncated")
        return tuple(value)

    def _pure_callback(self, callback, argument):
        before = self._counters()
        try:
            return callback(argument)
        finally:
            calls, tokens = self._account(before)
            if calls or tokens:
                raise PlannerBackendError("tokenization/decoding unexpectedly invoked the model")

    def propose(self, context, *, model_calls_remaining, generated_tokens_remaining,
                max_proposals=MAX_PROPOSALS, should_stop=None):
        """Propose typed plans; the host's shared model allowance is mandatory."""
        for value in (model_calls_remaining, generated_tokens_remaining, max_proposals):
            if type(value) is not int or value < 0:
                raise PlannerBackendError("remaining planner allowances must be nonnegative integers")
        if max_proposals > MAX_PROPOSALS:
            raise PlannerBackendError("at most two structured plans may be decoded")
        if should_stop is not None and not callable(should_stop):
            raise TypeError("should_stop must be callable or None")
        if should_stop is not None and should_stop():
            raise PlannerCancelled("planner request cancelled before dispatch")
        if self.backend is None:
            return PlannerBatch("unavailable", detail="No experimental planner backend is configured; no model was called.")
        if getattr(self.backend, "identity", None) != self.identity:
            raise PlannerBackendError("backend identity changed after provider validation")
        token_allowance = min(MAX_OUTPUT_TOKENS, generated_tokens_remaining,
                              self.max_total_generated_tokens - self.generated_tokens)
        if (self.requests >= self.max_calls or not model_calls_remaining
                or token_allowance <= 0 or not max_proposals):
            return PlannerBatch("limit", detail="No planner/shared-model/token allowance remains.")
        try:
            prompt = render_planner_prompt(context, self.identity, should_stop=should_stop)
            input_ids = self._tokens(self._pure_callback(self.backend.encode_prompt, prompt),
                                     MAX_INPUT_TOKENS, "full planner input")
        except PlannerCancelled:
            raise
        except PlannerError as error:
            self.prompt_rejections += 1
            return PlannerBatch("input_rejected", detail=str(error)[:512])
        if should_stop is not None and should_stop():
            raise PlannerCancelled("planner request cancelled after tokenization")
        prompt_sha = sha256(prompt.encode("utf-8")).hexdigest()
        cache_identity = sha256(_json({"prompt_sha256": prompt_sha,
            "input_ids": input_ids, "provider": self.identity.record(),
            "max_new_tokens": token_allowance, "max_proposals": max_proposals}).encode()).hexdigest()
        before = self._counters()
        self.requests += 1
        try:
            output_ids = self.backend.generate(input_ids, max_new_tokens=token_allowance,
                                                should_stop=should_stop)
        finally:
            calls, tokens = self._account(before)
            if calls > 1 or tokens > token_allowance or (tokens and not calls):
                raise PlannerBackendError("backend exceeded its single-decode/token allowance")
        is_model = self.identity.kind == "local_model"
        details = {"actual_model_calls": calls if is_model else 0, "backend_calls": calls,
                   "generated_tokens": tokens, "input_tokens": len(input_ids),
                   "prompt_sha256": prompt_sha, "cache_identity": cache_identity,
                   "model_inference": bool(calls and is_model)}
        if calls != 1:
            self.output_rejections += 1
            return PlannerBatch("output_rejected", detail="No actual decode attempt supports the returned proposal.", **details)
        if should_stop is not None and should_stop():
            raise PlannerCancelled("planner request cancelled after decode; actual counters retained")
        try:
            output_ids = self._tokens(output_ids, token_allowance, "planner output")
            if len(output_ids) != tokens:
                raise PlannerBackendError("returned output IDs do not match actual generated-token accounting")
            decoded = self._pure_callback(self.backend.decode_output, output_ids)
            specs = decode_plan_document(decoded)
            if len(specs) > max_proposals:
                raise PlannerError("decoded proposal count exceeds this request's allowance")
            plans, seen = [], set()
            for spec in specs:
                plan = compile_plan(spec, context, source="planner_model" if is_model else "test_backend",
                                    should_stop=should_stop)
                if plan.commands not in seen:
                    seen.add(plan.commands)
                    plans.append(plan)
        except PlannerCancelled:
            raise
        except PlannerError as error:
            self.output_rejections += 1
            return PlannerBatch("output_rejected", detail=str(error)[:512], **details)
        return PlannerBatch("proposals", plans=tuple(plans),
                            detail="Untrusted structured plans; no native proof was executed or claimed.", **details)

    def report(self):
        return {"available": self.backend is not None,
                "provider": None if self.identity is None else self.identity.record(),
                "prompt_contract": PROMPT_VERSION, "decoder_contract": DECODER_VERSION,
                "actual_model_calls": self.calls, "backend_calls": self.backend_calls,
                "decode_requests": self.requests, "generated_tokens": self.generated_tokens,
                "prompt_rejections": self.prompt_rejections, "output_rejections": self.output_rejections,
                "max_calls": self.max_calls, "max_total_generated_tokens": self.max_total_generated_tokens,
                "kernel_checked": False, "test_backend": self.identity is not None and self.identity.kind == "test_double"}
