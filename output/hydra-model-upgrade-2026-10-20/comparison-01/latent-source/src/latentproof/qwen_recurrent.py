"""Pretrained Qwen3 depth retrofit; execute numerical work only on SLURM.

Audited upstream interface: transformers 4.53.3, Qwen3ForCausalLM, optionally
wrapped by PEFT LoRA. The original module is retained as ``base_model``. This
module installs no adapters and never changes the pretrained parameter values.

Labels follow Hugging Face's UNSHIFTED convention: hidden position t predicts
labels[t + 1]. Labels equal to -100 are omitted before the vocabulary projection.
There is no KV cache. At r=1 the original decoder and head are used unchanged.
All reported call counts are logical FORWARD calls, excluding backward
checkpoint recomputation. Readouts include every coda layer and final RMSNorm.
"""
from __future__ import annotations

import math
from collections.abc import Iterator, Mapping
from typing import Any

import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.checkpoint import checkpoint
import transformers
from transformers.models.qwen3.modeling_qwen3 import (
    create_causal_mask,
    create_sliding_window_causal_mask,
)


def halting_weights(hazards: torch.Tensor) -> torch.Tensor:
    """Map [..., R-1] hazards to [..., R] masses, with forced final survival.

    The final axis is increasing depth, starting at 1. No normalization or
    clipping changes the supplied hazards; an empty axis gives unit mass at 1.
    """
    if hazards.ndim < 1:
        raise ValueError("hazards require a final depth axis")
    if not bool(torch.isfinite(hazards).all()) or bool(((hazards < 0) | (hazards > 1)).any()):
        raise ValueError("hazards must be finite probabilities in [0, 1]")
    if hazards.shape[-1] == 0:
        return torch.ones((*hazards.shape[:-1], 1), device=hazards.device, dtype=hazards.dtype)
    # Explicit products avoid the nondeterministic CUDA cumulative-sum kernel
    # used by cumprod's backward in PyTorch 2.5.1. Keep the graph through every
    # survival factor; this is algebraically the same residual-mass recursion.
    survival = torch.ones_like(hazards[..., 0])
    masses = []
    for depth in range(hazards.shape[-1]):
        masses.append(survival * hazards[..., depth])
        survival = survival * (1 - hazards[..., depth])
    return torch.stack([*masses, survival], dim=-1)


def distribution_features(logits: torch.Tensor, previous_log_probs: torch.Tensor | None = None):
    """Return normalized entropy, KL(previous || current), and FP32 log p.

    Shape is [..., V] -> (..., ..., [..., V]). The first-depth KL is +infinity,
    indicating an absent previous distribution; a KL stopping rule cannot halt
    there. The gate maps that sentinel to its bounded maximum KL feature.
    This pure helper retains autograd; callers detach controller features.
    """
    if logits.ndim < 1 or logits.shape[-1] < 2:
        raise ValueError("logits require a vocabulary axis of size at least two")
    if not bool(torch.isfinite(logits).all()):
        raise ValueError("nonfinite logits")
    logp = logits.float().log_softmax(-1)
    entropy = -(logp.exp() * logp).sum(-1) / math.log(logits.shape[-1])
    if previous_log_probs is None:
        kl = torch.full_like(entropy, float("inf"))
    else:
        if previous_log_probs.shape != logits.shape or not bool(torch.isfinite(previous_log_probs).all()):
            raise ValueError("previous log probabilities must be finite and aligned")
        previous_log_probs = previous_log_probs.float()
        kl = (previous_log_probs.exp() * (previous_log_probs - logp)).sum(-1).clamp_min(0)
    return entropy, kl, logp


def position_ids_from_attention_mask(attention_mask: torch.Tensor) -> torch.Tensor:
    """Explicit padding-aware positions for both this wrapper and its HF oracle.

    Raw HF forward defaults to arange, which this wrapper also preserves. Supply
    this helper's output explicitly when a padded batch should restart each
    sequence at position zero. Masked positions are assigned zero.
    """
    if attention_mask.ndim != 2 or bool(((attention_mask != 0) & (attention_mask != 1)).any()):
        raise ValueError("attention_mask must be a binary [batch, time] tensor")
    positions = attention_mask.long().cumsum(-1) - 1
    return positions.masked_fill(attention_mask == 0, 0)


class QwenRecurrentLM(nn.Module):
    """Reuse original P / R / C layer objects with full state BPTT.

    First pass: s1 = R(P(embed(x))). On extra passes each original core layer
    L_j is replaced by u -> u + alpha_j * (L_j(u) - u), where
    alpha_j = max_extra_pass_scale * sigmoid(damping_logits[j]). Each scalar is
    shared across repeated calls to that original layer. Set extra_pass_scale
    to None for undamped extra passes. Coda and final norm never feed recurrence.

    The 3 -> 16 -> 1 gate has 81 parameters. Its initial constant hazard is .25.
    Only ``train_gate`` and ``train_damping`` govern the NEW parameters; the
    caller controls the existing base/LoRA parameters' requires_grad flags.
    """

    def __init__(self, base_model: nn.Module, *, prelude_layers: int = 8,
                 core_layers: int = 12, max_recurrence: int = 4,
                 checkpoint_layers: bool = True, head_chunk_size: int = 64,
                 extra_pass_scale: float | None = 0.1,
                 max_extra_pass_scale: float = 0.25,
                 train_gate: bool = False, train_damping: bool = False):
        super().__init__()
        if transformers.__version__.split("+", 1)[0] != "4.53.3":
            raise RuntimeError("This source-audited retrofit requires transformers==4.53.3")
        self.base_model = base_model
        for name, value in (("prelude_layers", prelude_layers), ("core_layers", core_layers),
                            ("max_recurrence", max_recurrence), ("head_chunk_size", head_chunk_size)):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        self.prelude_layers, self.core_layers = prelude_layers, core_layers
        self.max_recurrence, self.head_chunk_size = max_recurrence, head_chunk_size
        self.checkpoint_layers = bool(checkpoint_layers)
        causal_lm = self.causal_lm
        if getattr(causal_lm.config, "model_type", None) != "qwen3":
            raise TypeError("base_model must contain a Qwen3ForCausalLM")
        self.coda_layers = len(self.decoder.layers) - prelude_layers - core_layers
        if self.coda_layers < 1:
            raise ValueError("partition must leave at least one coda layer")
        if any(getattr(layer, "gradient_checkpointing", False) for layer in self.decoder.layers):
            raise ValueError("disable HF gradient checkpointing; this wrapper checkpoints each layer itself")
        if getattr(base_model, "peft_config", None):
            for adapter in base_model.peft_config.values():
                if str(adapter.peft_type).split(".")[-1] != "LORA":
                    raise TypeError("only PEFT LoRA wrappers are supported")
        device = self.decoder.embed_tokens.weight.device
        self.halt_gate = nn.Sequential(nn.Linear(3, 16), nn.Tanh(), nn.Linear(16, 1)).to(device=device, dtype=torch.float32)
        nn.init.zeros_(self.halt_gate[-1].weight)
        nn.init.constant_(self.halt_gate[-1].bias, math.log(0.25 / 0.75))
        self.halt_gate.requires_grad_(train_gate)
        self.max_extra_pass_scale = float(max_extra_pass_scale)
        if extra_pass_scale is None:
            if train_damping:
                raise ValueError("train_damping requires an initial extra_pass_scale")
            self.register_parameter("damping_logits", None)
        else:
            if not (math.isfinite(extra_pass_scale) and math.isfinite(max_extra_pass_scale)
                    and 0 < extra_pass_scale < max_extra_pass_scale <= 1):
                raise ValueError("require 0 < extra_pass_scale < max_extra_pass_scale <= 1")
            fraction = extra_pass_scale / max_extra_pass_scale
            self.damping_logits = nn.Parameter(
                torch.full((core_layers,), math.log(fraction / (1 - fraction)), device=device, dtype=torch.float32),
                requires_grad=train_damping,
            )

    @property
    def causal_lm(self):
        """Original causal LM below an optional PEFT LoRA wrapper (no copy)."""
        return self.base_model.get_base_model() if hasattr(self.base_model, "peft_config") else self.base_model

    @property
    def decoder(self):
        return self.causal_lm.model

    @property
    def damping_scales(self):
        return None if self.damping_logits is None else self.max_extra_pass_scale * self.damping_logits.sigmoid()

    def hazard(self, entropy: torch.Tensor, kl: torch.Tensor, depth: int):
        self._check_depth(depth)
        features = torch.stack((entropy, torch.log1p(kl.clamp(min=0, max=20)) / math.log(21),
                                torch.full_like(entropy, depth / self.max_recurrence)), -1).detach()
        # Keep the small controller independent of the surrounding BF16 autocast.
        with torch.autocast(device_type=features.device.type, enabled=False):
            features = features.to(self.halt_gate[0].weight.dtype)
            return torch.sigmoid(self.halt_gate(features).squeeze(-1).float())

    def _check_depth(self, recurrence):
        if isinstance(recurrence, bool) or not isinstance(recurrence, int) or not 1 <= recurrence <= self.max_recurrence:
            raise ValueError("recurrence must be an integer in [1, max_recurrence]")

    def _prepare(self, input_ids, attention_mask, position_ids):
        if input_ids.ndim != 2 or input_ids.shape[1] == 0:
            raise ValueError("input_ids require nonempty [batch, time] shape")
        if attention_mask is not None:
            if attention_mask.shape != input_ids.shape or bool(((attention_mask != 0) & (attention_mask != 1)).any()):
                raise ValueError("attention_mask must be binary and match input_ids")
        hidden = self.decoder.embed_tokens(input_ids)
        cache_position = torch.arange(input_ids.shape[1], device=hidden.device)
        if position_ids is None:
            position_ids = cache_position.unsqueeze(0)
        if position_ids.shape not in ((1, input_ids.shape[1]), tuple(input_ids.shape)):
            raise ValueError("position_ids must have shape [1, time] or [batch, time]")
        mask_kwargs = dict(config=self.causal_lm.config, input_embeds=hidden,
                           attention_mask=attention_mask, cache_position=cache_position,
                           past_key_values=None, position_ids=position_ids)
        masks = {"full_attention": create_causal_mask(**mask_kwargs)}
        if self.decoder.has_sliding_layers:
            masks["sliding_attention"] = create_sliding_window_causal_mask(**mask_kwargs)
        context = dict(masks=masks, cache_position=cache_position,
                       position_ids=position_ids,
                       position_embeddings=self.decoder.rotary_emb(hidden, position_ids))
        return hidden, context

    def _layer(self, hidden, index, context):
        layer = self.decoder.layers[index]
        # Every invocation gets its own closure: backward never sees a later
        # loop index or a subsequent recurrence's state through late binding.
        def apply_layer(value):
            return layer(value, attention_mask=context["masks"][layer.attention_type],
                         position_ids=context["position_ids"], past_key_value=None,
                         output_attentions=False, use_cache=False,
                         cache_position=context["cache_position"],
                         position_embeddings=context["position_embeddings"])[0]
        if self.checkpoint_layers and self.training and torch.is_grad_enabled():
            return checkpoint(apply_layer, hidden, use_reentrant=False, preserve_rng_state=True)
        return apply_layer(hidden)

    def _prelude(self, hidden, context):
        for index in range(self.prelude_layers):
            hidden = self._layer(hidden, index, context)
        return hidden

    def _core(self, state, context, depth):
        scales = self.damping_scales if depth > 1 else None
        for local_index in range(self.core_layers):
            proposal = self._layer(state, self.prelude_layers + local_index, context)
            # Bypass interpolation at depth one, including its floating-point
            # arithmetic. A no-adapter r=1 pass is the upstream computation.
            if scales is None:
                state = proposal
            else:
                state = state + scales[local_index].to(state.dtype) * (proposal - state)
        return state

    def _readout_hidden(self, state, context):
        hidden = state
        for index in range(self.prelude_layers + self.core_layers, len(self.decoder.layers)):
            hidden = self._layer(hidden, index, context)
        return self.decoder.norm(hidden)

    def call_counts(self, depth: int, *, probing: bool = False, head_calls: int | None = None,
                    gate_calls: int = 0):
        self._check_depth(depth)
        readouts = depth if probing else 1
        return {"block_calls": self.prelude_layers + depth * self.core_layers + readouts * self.coda_layers,
                "prelude_calls": self.prelude_layers, "core_calls": depth * self.core_layers,
                "coda_calls": readouts * self.coda_layers, "readouts": readouts,
                "normalization_calls": readouts,
                "head_calls": readouts if head_calls is None else head_calls, "gate_calls": gate_calls}

    def fixed_forward(self, input_ids, attention_mask=None, position_ids=None, *, recurrence=1,
                      logits_to_keep=0, use_cache=False, past_key_values=None):
        """Return logits [B,T,V], or [B,k,V] for integer logits_to_keep=k.

        Intended for equivalence checks or generation. Training should use the
        chunked supervised_loss API so full-vocabulary graphs are not retained.
        """
        self._check_depth(recurrence)
        if use_cache or past_key_values is not None:
            raise ValueError("KV caches are forbidden for this recurrence retrofit")
        if isinstance(logits_to_keep, bool) or not isinstance(logits_to_keep, int) or logits_to_keep < 0:
            raise ValueError("logits_to_keep must be a nonnegative integer")
        state, context = self._prepare(input_ids, attention_mask, position_ids)
        state = self._prelude(state, context)
        for depth in range(1, recurrence + 1):
            state = self._core(state, context, depth)
        hidden = self._readout_hidden(state, context)
        logits = self.causal_lm.lm_head(hidden[:, -logits_to_keep:, :])
        return {"logits": logits, "depth": recurrence, "recurrence": recurrence,
                **self.call_counts(recurrence)}

    forward = fixed_forward

    def _supervision(self, input_ids, labels, attention_mask):
        if labels is None or labels.shape != input_ids.shape or labels.dtype != torch.long:
            raise ValueError("labels must be unshifted int64 [batch, time] matching input_ids")
        valid = labels[:, 1:] != -100
        if not bool(valid.any()):
            raise ValueError("no supervised next-token positions")
        if attention_mask is not None:
            if attention_mask.shape != input_ids.shape:
                raise ValueError("attention_mask must match input_ids")
            if bool((valid & ((attention_mask[:, :-1] == 0) | (attention_mask[:, 1:] == 0))).any()):
                raise ValueError("supervision may not predict from or into padding")
        batch_indices, positions = valid.nonzero(as_tuple=True)
        targets = labels[:, 1:][valid]
        return batch_indices, positions, targets

    def _head_statistics(self, hidden, targets, previous_log_probs):
        """Checkpoint each vocabulary projection and retain only previous log p.

        Vocabulary-sized outputs returned by the checkpoint function are
        detached. CE retains a compact graph that recomputes its head chunk in
        backward, rather than saving every depth's softmax activation.
        """
        ce_chunks, correct_chunks, entropy_chunks, kl_chunks, logp_chunks = [], [], [], [], []
        for start in range(0, targets.numel(), self.head_chunk_size):
            stop = start + self.head_chunk_size
            target_chunk = targets[start:stop]
            def project(value, target):
                logits = self.causal_lm.lm_head(value)
                entropy, _, logp = distribution_features(logits)
                ce = F.nll_loss(logp, target, reduction="none")
                return ce, (logits.argmax(-1) == target).detach(), entropy.detach(), logp.detach()
            if self.checkpoint_layers and self.training and torch.is_grad_enabled():
                ce, correct, entropy, logp = checkpoint(project, hidden[start:stop], target_chunk,
                                                        use_reentrant=False, preserve_rng_state=True)
            else:
                ce, correct, entropy, logp = project(hidden[start:stop], target_chunk)
            with torch.no_grad():
                if previous_log_probs is None:
                    kl = torch.full_like(entropy, float("inf"))
                else:
                    previous = previous_log_probs[start:stop]
                    kl = (previous.exp() * (previous - logp)).sum(-1).clamp_min(0)
            ce_chunks.append(ce)
            correct_chunks.append(correct)
            entropy_chunks.append(entropy)
            kl_chunks.append(kl)
            logp_chunks.append(logp)
        return (torch.cat(ce_chunks), torch.cat(correct_chunks), torch.cat(entropy_chunks),
                torch.cat(kl_chunks), torch.cat(logp_chunks))

    def _supervised_depths(self, input_ids, labels, attention_mask, position_ids, *, final_depth, probe_all,
                           compute_hazards):
        batch_indices, positions, targets = self._supervision(input_ids, labels, attention_mask)
        state, context = self._prepare(input_ids, attention_mask, position_ids)
        state = self._prelude(state, context)
        previous = None
        for depth in range(1, final_depth + 1):
            state = self._core(state, context, depth)
            if not probe_all and depth != final_depth:
                continue
            readout = self._readout_hidden(state, context)
            # Select predictor positions BEFORE projecting into the vocabulary.
            ce, correct, entropy, kl, previous = self._head_statistics(
                readout[batch_indices, positions], targets, previous)
            hazard = self.hazard(entropy, kl, depth) if compute_hazards and depth < self.max_recurrence else None
            yield {"depth": depth, "ce": ce, "correct": correct, "entropy": entropy,
                   "kl": kl, "hazard": hazard, "batch_indices": batch_indices,
                   "positions": positions, "targets": targets}

    def supervised_loss(self, input_ids, labels, attention_mask=None, position_ids=None, *,
                        mode="fixed", recurrence=1, auxiliary_weight=0.2, ponder_cost=0.0):
        """Scalar loss and compact statistics, with full BPTT through every pass.

        adaptive: (1-a) E_q[CE_r] + a mean_r CE_r + ponder_cost E_q[r].
        all_depth: uniform mean CE over depths 1..R. fixed: CE at recurrence.
        The adaptive objective is expected cross entropy, not mixture CE.
        """
        if mode not in {"fixed", "all_depth", "adaptive"}:
            raise ValueError("unknown supervision mode")
        self._check_depth(recurrence)
        if not math.isfinite(ponder_cost) or ponder_cost < 0 or not 0 <= auxiliary_weight <= 1:
            raise ValueError("invalid objective coefficients")
        final_depth = recurrence if mode == "fixed" else self.max_recurrence
        rows = list(self._supervised_depths(input_ids, labels, attention_mask, position_ids,
                                           final_depth=final_depth, probe_all=mode != "fixed",
                                           compute_hazards=mode == "adaptive"))
        ce = torch.stack([row["ce"] for row in rows], -1)
        depths = ce.new_tensor([row["depth"] for row in rows])
        if mode == "adaptive":
            hazards = torch.stack([row["hazard"] for row in rows[:-1]], -1) if len(rows) > 1 else ce[:, :0]
            weights = halting_weights(hazards)
        else:
            weights = torch.full_like(ce, 1 / len(rows))
        risk = (weights * ce).sum(-1).mean()
        expected_depth = (weights * depths).sum(-1).mean()
        auxiliary = ce.mean()
        loss = ((1 - auxiliary_weight) * risk + auxiliary_weight * auxiliary + ponder_cost * expected_depth
                if mode == "adaptive" else risk)
        chunks = math.ceil(ce.shape[0] / self.head_chunk_size)
        return {"loss": loss, "prediction_loss": risk, "auxiliary_loss": auxiliary,
                "mean_recurrence": expected_depth, "halting_mass": weights.mean(0).detach(),
                "depth_prediction_loss": ce.mean(0).detach(), "supervised_tokens": ce.shape[0],
                "depths": depths.detach(),
                **self.call_counts(final_depth, probing=mode != "fixed", head_calls=chunks * len(rows),
                                   gate_calls=final_depth - 1 if mode == "adaptive" else 0)}

    def iter_supervised(self, input_ids, attention_mask=None, labels=None, *, position_ids=None) -> Iterator[dict[str, Any]]:
        """Detached validation probes; positional order is IDs, mask, labels.

        Yields depth, ce/correct/entropy/kl/hazard [N] in row-major masked label
        order. At the forced final depth hazard is ones; it is NOT an extra
        learned parameter. Caller must use eval() to disable model dropout.
        """
        iterator = self._supervised_depths(input_ids, labels, attention_mask, position_ids,
                                           final_depth=self.max_recurrence, probe_all=True,
                                           compute_hazards=True)
        while True:
            # Advance under no_grad, but restore the CALLER's grad mode before
            # yielding. A context around a generator's yield would leak it.
            with torch.no_grad():
                row = next(iterator, None)
                if row is None:
                    return
                if row["hazard"] is None:
                    row["hazard"] = torch.ones_like(row["ce"])
                result = {key: value.detach() if torch.is_tensor(value) else value for key, value in row.items()}
            yield result

    def eval_supervised(self, input_ids, labels, attention_mask=None, position_ids=None):
        """Collect [N,R] scalar probes, never a [N,R,V] vocabulary tensor."""
        rows = list(self.iter_supervised(input_ids, attention_mask, labels, position_ids=position_ids))
        result = {key: torch.stack([row[key] for row in rows], -1)
                  for key in ("ce", "correct", "entropy", "kl")}
        hazards = torch.stack([row["hazard"] for row in rows[:-1]], -1) if len(rows) > 1 else result["ce"][:, :0]
        result.update(hazards=hazards, halting_mass=halting_weights(hazards),
                      depths=torch.arange(1, self.max_recurrence + 1, device=input_ids.device),
                      **{key: rows[0][key] for key in ("batch_indices", "positions", "targets")},
                      **self.call_counts(self.max_recurrence, probing=True,
                                         head_calls=len(rows) * math.ceil(rows[0]["ce"].numel() / self.head_chunk_size),
                                         gate_calls=self.max_recurrence - 1))
        result["fixed_block_calls"] = [self.call_counts(r)["block_calls"] for r in range(1, self.max_recurrence + 1)]
        result["adaptive_block_calls"] = [self.call_counts(r, probing=True)["block_calls"] for r in range(1, self.max_recurrence + 1)]
        return result

    @torch.no_grad()
    def next_logits(self, input_ids, policy: Mapping[str, Any], attention_mask=None, position_ids=None):
        """One sequence's next-token logits [1,V], with actual early exit.

        Return keys include depth (also recurrence), block_calls, head_calls,
        readouts, entropy, kl, hazard, cumulative_halting_mass, and policy.
        Each generated token must call this on its entire new causal prefix.
        """
        if input_ids.ndim != 2 or input_ids.shape[0] != 1:
            raise ValueError("next_logits supports exactly one sequence")
        kind = policy.get("kind")
        if kind not in {"fixed", "learned", "entropy", "kl", "entropy_kl"}:
            raise ValueError("unknown stopping policy")
        if kind == "fixed":
            final_depth = policy["depth"]
            self._check_depth(final_depth)
        else:
            final_depth = self.max_recurrence
        if kind == "learned" and not 0 < policy.get("quantile", 0.5) <= 1:
            raise ValueError("quantile must lie in (0,1]")
        if kind in {"entropy", "entropy_kl"} and not 0 <= policy["entropy"] <= 1:
            raise ValueError("normalized entropy threshold must lie in [0,1]")
        if kind in {"kl", "entropy_kl"} and (not math.isfinite(policy["kl"]) or policy["kl"] < 0):
            raise ValueError("KL threshold must be finite and nonnegative")
        if attention_mask is None:
            last_position = input_ids.shape[1] - 1
        else:
            real = attention_mask[0].nonzero(as_tuple=True)[0]
            if real.numel() == 0:
                raise ValueError("next_logits requires a nonpadding token")
            last_position = int(real[-1])
        state, context = self._prepare(input_ids, attention_mask, position_ids)
        state = self._prelude(state, context)
        previous, survival, last_hazard = None, 1.0, None
        for depth in range(1, final_depth + 1):
            state = self._core(state, context, depth)
            if kind == "fixed" and depth != final_depth:
                continue
            hidden = self._readout_hidden(state, context)
            logits = self.causal_lm.lm_head(hidden[:, last_position])
            entropy, kl, previous = distribution_features(logits, previous)
            stop = depth == final_depth
            if kind == "learned" and depth < self.max_recurrence:
                last_hazard = float(self.hazard(entropy, kl, depth).item())
                survival *= 1 - last_hazard
                stop |= (1 - survival) >= policy.get("quantile", 0.5)
            elif kind == "entropy":
                stop |= float(entropy.item()) <= policy["entropy"]
            elif kind == "kl":
                stop |= float(kl.item()) <= policy["kl"]
            elif kind == "entropy_kl":
                stop |= float(entropy.item()) <= policy["entropy"] and float(kl.item()) <= policy["kl"]
            if stop:
                if kind == "learned" and depth == self.max_recurrence:
                    survival, last_hazard = 0.0, 1.0
                return {"logits": logits, "depth": depth, "recurrence": depth,
                        "entropy": float(entropy.item()), "kl": float(kl.item()),
                        "hazard": last_hazard,
                        "cumulative_halting_mass": 1 - survival if kind == "learned" else None,
                        "policy": dict(policy), **self.call_counts(depth, probing=kind != "fixed",
                          gate_calls=min(depth, self.max_recurrence - 1) if kind == "learned" else 0)}
        raise AssertionError("forced maximum recurrence failed")
