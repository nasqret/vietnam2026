"""Campaign-2 adaptive depth. Execute numerical work only inside SLURM.

The pilot implementation stays frozen. This is a separate experimental objective,
not a reproduction of ACT/PonderNet. Training evaluates every depth; generation
actually exits the loop. A gate never certifies mathematical correctness.
"""
from __future__ import annotations

import math
import torch
from torch import nn
from torch.nn import functional as F

from .model import RecurrentLM


def halting_weights(hazards: torch.Tensor) -> torch.Tensor:
    """Last dimension contains hazards for eligible non-final depths.

    Return one extra final depth containing all surviving probability mass.
    No clipping/renormalization: callers must supply probabilities in [0,1].
    """
    if hazards.ndim < 1:
        raise ValueError("hazards need a depth axis")
    if not bool(torch.isfinite(hazards).all()) or bool(((hazards < 0) | (hazards > 1)).any()):
        raise ValueError("hazards must be finite probabilities")
    survival = torch.cumprod(1 - hazards, dim=-1)
    before = torch.cat((torch.ones_like(hazards[..., :1]), survival[..., :-1]), -1)
    if hazards.shape[-1] == 0:
        return torch.ones((*hazards.shape[:-1], 1), device=hazards.device, dtype=hazards.dtype)
    return torch.cat((hazards * before, survival[..., -1:]), -1)


def distribution_features(logits, previous_log_probs=None):
    if logits.ndim < 1 or logits.shape[-1] < 2 or not bool(torch.isfinite(logits).all()):
        raise ValueError("logits must be finite with vocabulary size at least two")
    if previous_log_probs is not None and (previous_log_probs.shape != logits.shape
                                           or not bool(torch.isfinite(previous_log_probs).all())):
        raise ValueError("previous log probabilities must be finite and aligned")
    logp = logits.float().log_softmax(-1)
    p = logp.exp()
    entropy = -(p * logp).sum(-1) / math.log(logits.shape[-1])
    if previous_log_probs is None:
        kl = torch.full_like(entropy, float("inf"))
    else:
        # KL(previous || current), with rounding-only negative values clamped.
        kl = (previous_log_probs.exp() * (previous_log_probs - logp)).sum(-1).clamp_min(0)
    return entropy, kl, logp


class AdaptiveRecurrentLM(RecurrentLM):
    def __init__(self, cfg, min_depth=2, max_depth=8):
        super().__init__(cfg)
        if not 1 <= min_depth <= max_depth:
            raise ValueError("invalid depth bounds")
        self.min_depth, self.max_depth = min_depth, max_depth
        self.halt_gate = nn.Sequential(nn.Linear(3, 16), nn.Tanh(), nn.Linear(16, 1))
        nn.init.zeros_(self.halt_gate[-1].weight)
        nn.init.constant_(self.halt_gate[-1].bias, -1.5)

    def readout(self, state):
        out = self.final_norm(state)
        for block in self.coda:
            out = block(out)
        return F.linear(self.final_norm(out), self.embedding.weight)

    def hazard(self, entropy, kl, depth):
        features = torch.stack((entropy, torch.log1p(kl.clamp(max=20)) / math.log(21),
                                torch.full_like(entropy, depth / self.max_depth)), -1).detach()
        return torch.sigmoid(self.halt_gate(features).squeeze(-1).float())

    def depth_logits(self, tokens, *, deterministic=True, max_depth=None):
        """Causal all-position probes. Full BPTT; no token pooling or freezing."""
        limit = self.max_depth if max_depth is None else max_depth
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= self.max_depth:
            raise ValueError("depth override outside declared bounds")
        e = self.encode(tokens)
        state = torch.zeros_like(e) if deterministic else self.initial_state(e)
        for depth in range(1, limit + 1):
            state = self.core_step(state, e)
            yield depth, self.readout(state)

    def adaptive_loss(self, tokens, labels, *, ponder_cost=0.03, auxiliary_weight=0.2):
        if labels.shape != tokens.shape:
            raise ValueError("labels must be pre-shifted and aligned with input")
        if not math.isfinite(ponder_cost) or ponder_cost < 0 or not 0 <= auxiliary_weight <= 1:
            raise ValueError("invalid objective coefficients")
        valid = labels != -100
        if not bool(valid.any()):
            raise ValueError("no supervised tokens")
        ce_values, hazards = [], []
        prev = None
        for depth, logits in self.depth_logits(tokens, deterministic=False):
            entropy, kl, logp = distribution_features(logits, prev)
            prev = logp.detach()
            if depth < self.min_depth:
                continue
            ce_values.append(F.cross_entropy(logits.float().reshape(-1, logits.shape[-1]),
                                             labels.reshape(-1), reduction="none",
                                             ignore_index=-100).reshape_as(labels))
            if depth < self.max_depth:
                hazards.append(self.hazard(entropy, kl, depth))
        ce = torch.stack(ce_values, -1)
        hz = torch.stack(hazards, -1) if hazards else ce[..., :0]
        weights = halting_weights(hz)
        depths = torch.arange(self.min_depth, self.max_depth + 1, device=ce.device)
        risk = (weights * ce).sum(-1)[valid].mean()
        expected_depth = (weights * depths).sum(-1)[valid].mean()
        auxiliary = ce.mean(-1)[valid].mean()
        loss = (1 - auxiliary_weight) * risk + auxiliary_weight * auxiliary + ponder_cost * expected_depth
        return {"loss": loss, "prediction_loss": risk, "mean_recurrence": expected_depth,
                "auxiliary_loss": auxiliary, "weights": weights, "depth_ce": ce}

    @torch.inference_mode()
    def next_logits(self, tokens, policy):
        """One sequence, one next token; early exit saves actual core evaluations.

        Entire causal prefix evolves uniformly until its LAST position halts.
        Padding/batch-max halting is deliberately excluded from this benchmark.
        """
        if tokens.shape[0] != 1:
            raise ValueError("adaptive generation requires one sequence")
        mode = policy["kind"]
        if mode == "fixed":
            r = policy["depth"]
            if isinstance(r, bool) or not isinstance(r, int) or not 1 <= r <= self.max_depth:
                raise ValueError("fixed depth outside declared bounds")
            state = torch.zeros((*tokens.shape, self.cfg.width), device=tokens.device,
                                dtype=self.embedding.weight.dtype)
            result = self(tokens, r, initial_state=state)
            return result["logits"][:, -1], r, self.block_evaluations(r)
        if mode not in {"learned", "entropy", "kl", "entropy_kl"}:
            raise ValueError("unknown stopping policy")
        if mode == "learned" and not 0 < policy.get("quantile", 0.5) <= 1:
            raise ValueError("quantile must lie in (0,1]")
        if mode in {"entropy", "entropy_kl"} and not 0 <= policy["entropy"] <= 1:
            raise ValueError("normalized entropy threshold outside [0,1]")
        if mode in {"kl", "entropy_kl"} and (not math.isfinite(policy["kl"]) or policy["kl"] < 0):
            raise ValueError("invalid KL threshold")
        e = self.encode(tokens)
        state, prev, survival = torch.zeros_like(e), None, 1.0
        for depth in range(1, self.max_depth + 1):
            state = self.core_step(state, e)
            logits = self.readout(state)[:, -1]
            entropy, kl, logp = distribution_features(logits, prev)
            prev = logp
            stop = depth == self.max_depth
            if depth >= self.min_depth and depth < self.max_depth:
                if mode == "learned":
                    survival *= 1 - float(self.hazard(entropy, kl, depth))
                    stop |= (1 - survival) >= policy.get("quantile", 0.5)
                elif mode == "entropy":
                    stop |= float(entropy) <= policy["entropy"]
                elif mode == "kl":
                    stop |= float(kl) <= policy["kl"]
                else:
                    stop |= float(entropy) <= policy["entropy"] and float(kl) <= policy["kl"]
            if stop:
                block_calls = self.cfg.prelude_layers + depth * (self.cfg.core_layers + self.cfg.coda_layers)
                return logits, depth, block_calls
        raise AssertionError("forced maximum failed")


def policy_grid(native):
    policies = [{"kind": "fixed", "depth": r} for r in (2, 4, 8)]
    if native:
        policies += [{"kind": "learned", "quantile": q} for q in (0.25, 0.5, 0.75, 0.9)]
    else:
        policies += [{"kind": "entropy", "entropy": h} for h in (0.1, 0.25, 0.5)]
        policies += [{"kind": "kl", "kl": k} for k in (0.001, 0.01, 0.05)]
        policies += [{"kind": "entropy_kl", "entropy": h, "kl": k}
                     for h, k in ((0.25, 0.01), (0.5, 0.05))]
    return policies


def policy_key(policy):
    return ":".join(str(policy[k]) for k in sorted(policy))


def select_policy(records, tolerance=0.03):
    """Validation-only selection: lowest block calls within 0.03 nat of r=8 CE."""
    reference = next(row for row in records if row["policy"] == {"kind": "fixed", "depth": 8})
    eligible = [row for row in records if row["loss"] <= reference["loss"] + tolerance]
    return min(eligible, key=lambda row: (row["mean_block_calls"], row["loss"], policy_key(row["policy"])))["policy"]
