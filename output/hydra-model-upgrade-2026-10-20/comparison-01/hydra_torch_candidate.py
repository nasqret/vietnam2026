"""Standalone next-tactic bridge; not installed in the live Hydra runtime.

No model, native checker, network or Torch import occurs on module import.
The host owns authenticated local loading, source pins and process supervision.
Returned strings are untrusted suggestions, never proof certificates.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import copy
import hashlib
import json
import math
import os
import sys
import time


EXECUTION_SHA256 = "ac5efc6260bd7aa706ee02f943c30c8fa4acc413a1be246722b2163a21688a87"
EXECUTION_COMMANDS = tuple(sorted((
    "apply", "assumption", "cases", "compact_arith", "congr", "exact", "exfalso",
    "exists", "forall_elim", "have", "induction", "intro", "left", "norm_num",
    "refl", "rewrite", "right", "ring", "simp", "specialize", "split", "suffices",
    "symm", "trans", "use",
)))
KINDS = {"historical_primitive_v4", "latent_compact_v3"}
FIXED_VANILLA = {"kind": "fixed", "depth": 1}


class BindingError(ValueError):
    """A configuration or numerical receipt is inconsistent; fail closed."""


def require(ok, message):
    if not ok:
        raise BindingError(message)


def object_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def sha256(value):
    return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


@dataclass(frozen=True)
class Limits:
    max_calls: int = 16
    max_new_tokens: int = 128
    max_total_decision_tokens: int = 4096
    max_context_tokens: int = 6144
    provider_seconds: float = 30.0

    def __post_init__(self):
        for key, maximum in (("max_calls", 128), ("max_new_tokens", 128),
                             ("max_total_decision_tokens", 16384), ("max_context_tokens", 6144)):
            require(type(getattr(self, key)) is int and 0 < getattr(self, key) <= maximum,
                    f"invalid bounded {key}")
        require(type(self.provider_seconds) in (int, float)
                and math.isfinite(self.provider_seconds) and 0 < self.provider_seconds <= 30,
                "provider time must be finite, positive and at most 30 seconds")


class _Prefix:
    """The authority callback needs only a one-dimensional .tolist() view."""
    def __init__(self, ids):
        self.ids = ids

    def tolist(self):
        return list(self.ids)


class TorchGreedyBackend:
    """One CUDA forward per decision, full prefix, no cache or sampling.

    Construct only after the host verifies local base/checkpoint/source pins and
    loads/freeze/evals the model. There is deliberately no from_pretrained/load
    method, fallback to another device, or checkpoint deserialization here.
    """
    def __init__(self, model, *, kind):
        require(kind in KINDS, "unknown model backend")
        require(sys.platform == "linux" and bool(os.environ.get("SLURM_JOB_ID")),
                "numerical inference requires the host's authorized Linux SLURM job")
        require(os.environ.get("HF_HUB_OFFLINE") == "1"
                and os.environ.get("TRANSFORMERS_OFFLINE") == "1", "offline loading must be explicit")
        import torch
        require(torch.cuda.is_available(), "no CPU/Mac fallback")
        require(not model.training, "loaded model must already be in evaluation mode")
        parameters = list(model.parameters())
        require(parameters and all(not p.requires_grad and p.device.type == "cuda" for p in parameters),
                "inference model must be frozen and entirely on CUDA")
        self.torch, self.model, self.kind = torch, model, kind
        self.causal_lm = model.causal_lm if kind == "latent_compact_v3" else model
        self.model_vocab_size = int(self.causal_lm.config.vocab_size)

    def next_token(self, sequence, allowed_ids, *, forward_started, forward_completed):
        torch = self.torch
        require(allowed_ids is None or bool(allowed_ids), "empty allowed token set")
        tokens = torch.tensor([sequence], dtype=torch.long, device="cuda")
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            forward_started()
            if self.kind == "latent_compact_v3":
                require(allowed_ids is None, "latent training protocol has no primitive-v4 token mask")
                output = self.model.next_logits(input_ids=tokens, policy=dict(FIXED_VANILLA))
                forward_completed()
                logits = output["logits"]
                metadata = {key: int(output[key]) for key in
                            ("depth", "block_calls", "head_calls", "gate_calls", "readouts")}
                require(metadata["depth"] == 1 and metadata["gate_calls"] == 0,
                        "vanilla backend unexpectedly used recurrence or a gate")
            else:
                output = self.model(input_ids=tokens, attention_mask=torch.ones_like(tokens),
                                    use_cache=False, logits_to_keep=1)
                forward_completed()
                logits = output.logits[:, -1, :]
                metadata = {"depth": 1, "block_calls": int(self.model.config.num_hidden_layers),
                            "head_calls": 1, "gate_calls": 0, "readouts": 1}
            require(tuple(logits.shape) == (1, self.model_vocab_size), "unexpected output vocabulary/shape")
            require(bool(torch.isfinite(logits).all().item()), "non-finite model logits")
            if allowed_ids is None:
                token = int(logits.argmax(-1).item())
            else:
                require(all(type(t) is int and 0 <= t < self.model_vocab_size for t in allowed_ids),
                        "constraint returned invalid token IDs")
                # Sorted IDs retain ordinary argmax's lowest-ID tie break.
                indices = torch.tensor(sorted(set(allowed_ids)), dtype=torch.long, device=logits.device)
                token = int(indices[logits[0, indices].argmax()].item())
        return token, metadata


class CandidatePolicy:
    """Hydra CandidateProvider: propose(tuple_of_goals, max_candidates=4).

    render_prompt, strict_generation, check_prompt_binding and validate_tactic
    must be the host-authenticated original functions, not repaired substitutes.
    Both arms use greedy width one. max_candidates is a ceiling, never a request
    to fabricate/repeat candidates. The historical arm preserves its token mask;
    the latent arm preserves its exact trained full-library conditioning prompt.
    Both execute solely under the same original Hydra no-import authority.
    """
    def __init__(self, *, backend, tokenizer, kind, environment, provenance,
                 render_prompt, strict_generation, check_prompt_binding, validate_tactic,
                 constraint_factory=None, limits=Limits(), should_stop=lambda: False,
                 deadline_monotonic=None, clock=time.monotonic):
        require(kind in KINDS and backend.kind == kind, "conditioning/backend mismatch")
        caps = environment.capabilities
        require(environment.prompt_version == 4 and environment.classical is False
                and caps.label == "hydra-authority-no-imports-v1"
                and tuple(caps.allowed_theorems) == ()
                and tuple(caps.allowed_commands) == EXECUTION_COMMANDS
                and not environment.library, "current restricted Hydra execution authority is required")
        require(type(provenance) is dict, "missing externally authenticated provenance")
        for key in ("checkpoint_sha256", "tokenizer_identity_sha256", "source_inventory_sha256"):
            require(sha256(provenance.get(key)), f"invalid {key}")
        require(type(provenance.get("run_id")) is str and provenance["run_id"], "missing run ID")
        require(provenance.get("policy") == FIXED_VANILLA, "only the depth-one vanilla policy is implemented")
        require(type(provenance.get("model_vocab_size")) is int
                and provenance["model_vocab_size"] == backend.model_vocab_size >= len(tokenizer),
                "model/tokenizer vocabulary binding mismatch")
        require((constraint_factory is not None) is (kind == "historical_primitive_v4"),
                "historical model needs its authority mask; latent must retain its unmasked decoder")
        require(type(tokenizer.eos_token_id) is int and 0 <= tokenizer.eos_token_id < len(tokenizer),
                "missing real tokenizer EOS")
        require(deadline_monotonic is None or
                (type(deadline_monotonic) in (int, float) and math.isfinite(deadline_monotonic)),
                "invalid outer deadline")
        self.backend, self.tokenizer, self.kind, self.environment = backend, tokenizer, kind, environment
        self.provenance = copy.deepcopy(provenance)
        self.render_prompt, self.strict_generation = render_prompt, strict_generation
        self.check_prompt_binding, self.validate_tactic = check_prompt_binding, validate_tactic
        self.constraint_factory, self.limits = constraint_factory, limits
        self.should_stop, self.outer_deadline, self.clock = should_stop, deadline_monotonic, clock
        self.calls = self.forward_attempts = self.forward_passes = self.generated_tokens = 0
        self.provider_seconds = 0.0
        self.attempts = []
        self._busy = False
        self.evaluation_identity = {
            "kind": "untrusted-torch-next-tactic", "conditioning": kind,
            "conditioning_authority": "model-v3 full library 247/247" if kind == "latent_compact_v3"
                                      else "hydra-authority-no-imports-v1",
            "execution_authority": "hydra-authority-no-imports-v1",
            "execution_environment_sha256": EXECUTION_SHA256,
            "scope": "transfer to Hydra restricted authority", "limits": asdict(limits),
            "max_candidates": 1, "sampling": False, "repair": False, "use_cache": False,
            "kernel_checked": False, "checkpoint_authenticated_by": "host driver, not this adapter",
            "provenance": copy.deepcopy(provenance),
        }

    def _check_stop(self, deadline):
        if self.should_stop() or self.clock() >= deadline:
            raise TimeoutError("provider cancelled or its wall-time budget expired")

    def propose(self, goals_before, *, max_candidates):
        require(not self._busy, "provider is not reentrant")
        require(type(max_candidates) is int and 1 <= max_candidates <= 4, "invalid candidate ceiling")
        require(type(goals_before) is tuple and 0 < len(goals_before) <= 64
                and all(type(g) is str and g.strip() for g in goals_before)
                and sum(len(g.encode()) for g in goals_before) <= 128 * 1024,
                "complete bounded ordered native goals are required")
        require(self.calls < self.limits.max_calls
                and self.generated_tokens < self.limits.max_total_decision_tokens, "provider work budget exhausted")
        started = self.clock()
        deadline = started + max(0.0, self.limits.provider_seconds - self.provider_seconds)
        if self.outer_deadline is not None:
            deadline = min(deadline, self.outer_deadline)
        attempt = {"attempt": len(self.attempts) + 1, "status": "started", "candidate_count": 0,
                   "forward_attempts": 0, "forward_passes": 0, "decision_ids": []}
        self.attempts.append(attempt)
        self._busy = True
        try:
            self._check_stop(deadline)
            if self.kind == "latent_compact_v3":
                prompt = self.render_prompt(list(goals_before), library_prefix_length=247, focus=0)
            else:
                prompt = self.render_prompt(goals=goals_before, focus=0, environment=self.environment)
            require(type(prompt) is str and prompt, "renderer returned no exact prompt")
            sequence = self.tokenizer.encode(prompt, add_special_tokens=False)
            require(type(sequence) is list and sequence
                    and all(type(t) is int and 0 <= t < len(self.tokenizer) for t in sequence),
                    "prompt did not encode as exact tokenizer IDs")
            prompt_length = len(sequence)
            attempt.update(prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), prompt_tokens=prompt_length)
            effective = min(self.limits.max_new_tokens,
                            self.limits.max_total_decision_tokens - self.generated_tokens,
                            self.limits.max_context_tokens - prompt_length)
            if effective <= 0:
                attempt.update(status="rejected", rejection_reasons=["prompt_exceeds_context"])
                return ()
            constraint = (self.constraint_factory(self.tokenizer, self.environment,
                          prompt_length=prompt_length, max_new_tokens=effective)
                          if self.constraint_factory else None)
            record = {"format": "latent-qwen-bpe-generation-v1",
                      "model_vocab_size": self.backend.model_vocab_size,
                      "prompt_sha256": attempt["prompt_sha256"], "prompt_tokens": prompt_length,
                      "max_context_tokens": self.limits.max_context_tokens, "max_new_tokens": effective,
                      "decision_ids": attempt["decision_ids"], "stop_reason": "token_budget", "eos": False,
                      "recurrence_depths": [], "block_calls": [], "head_calls": [], "gate_calls": [],
                      "readouts": [], "policy": dict(FIXED_VANILLA), "provenance": self.provenance}
            attempt["generation"] = record

            def forward_started():
                self._check_stop(deadline)
                if attempt["forward_attempts"] == 0:
                    self.calls += 1
                attempt["forward_attempts"] += 1
                self.forward_attempts += 1

            def forward_completed():
                attempt["forward_passes"] += 1
                self.forward_passes += 1

            special_ids = set(self.tokenizer.all_special_ids)
            for _ in range(effective):
                self._check_stop(deadline)
                allowed = None if constraint is None else constraint(0, _Prefix(sequence))
                token, metadata = self.backend.next_token(sequence, allowed,
                    forward_started=forward_started, forward_completed=forward_completed)
                require(type(token) is int and 0 <= token < self.backend.model_vocab_size,
                        "backend returned an invalid actual decision")
                record["decision_ids"].append(token)
                self.generated_tokens += 1
                for source, target in (("depth", "recurrence_depths"), ("block_calls", "block_calls"),
                                       ("head_calls", "head_calls"), ("gate_calls", "gate_calls"), ("readouts", "readouts")):
                    value = metadata[source]
                    require(type(value) is int and value >= 0, "invalid numerical work counter")
                    record[target].append(value)
                require(metadata["depth"] == 1 and metadata["gate_calls"] == 0, "unexpected non-vanilla computation")
                if token == self.tokenizer.eos_token_id:
                    record.update(stop_reason="eos", eos=True)
                elif token in special_ids or token >= len(self.tokenizer):
                    record["stop_reason"] = "invalid_special_token"
                self._check_stop(deadline)  # Late EOS is counted, but never accepted.
                if record["stop_reason"] != "token_budget":
                    break
                sequence.append(token)
            record["seconds"] = self.clock() - started
            self.check_prompt_binding(record, prompt, self.tokenizer, effective,
                                      max_context_tokens=self.limits.max_context_tokens)
            checked = self.strict_generation(record, self.tokenizer, effective,
                                             expected_provenance=self.provenance)
            attempt["strict_generation"] = checked
            if not checked["valid_action"]:
                attempt.update(status="rejected", rejection_reasons=checked["rejection_reasons"])
                return ()
            action = checked["action"]
            if len(action.encode()) > 512 or action.split(maxsplit=1)[0] == "use":
                attempt.update(status="rejected", rejection_reasons=["restricted_authority_or_tactic_size"])
                return ()
            try:
                literal = self.validate_tactic(action, self.environment)
            except (ValueError, TypeError) as error:
                attempt.update(status="rejected", rejection_reasons=["native_authority_postflight"],
                               authority_error_type=type(error).__name__)
                return ()
            require(literal == action, "authority validator repaired the generated action")
            self._check_stop(deadline)
            attempt.update(status="suggested", candidate_count=1, action=action)
            return (action,)
        except BaseException as error:
            attempt.update(status="failed", error_type=type(error).__name__, error=str(error)[:512])
            # A partial/error record is evidence only, never a valid generation.
            if isinstance(error, TimeoutError) and "generation" in attempt:
                attempt["generation"]["budget_expired"] = True
            raise
        finally:
            elapsed = max(0.0, self.clock() - started)
            self.provider_seconds += elapsed
            attempt["provider_seconds"] = elapsed
            self._busy = False

    def report(self):
        return copy.deepcopy({"identity": self.evaluation_identity, "actual_model_calls": self.calls,
            "forward_attempts": self.forward_attempts, "forward_passes": self.forward_passes,
            "generated_token_slots": self.generated_tokens, "provider_seconds": self.provider_seconds,
            "attempts": self.attempts, "kernel_checked": False})
