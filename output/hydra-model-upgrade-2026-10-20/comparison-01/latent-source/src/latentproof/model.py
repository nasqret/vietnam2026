"""Tiny educational depth-recurrent and conventional decoder language models.

UNVALIDATED DRAFT: execute only in an authorized Helios/WMI SLURM job.
This is an independent teaching implementation, NOT a Huginn reproduction or
checkpoint loader. Reference: arXiv:2502.05171v2; official implementation commit
1ea7220ec7eb42d13e89db0663df254d0bcdc28e (2025-12-29).

Kept: causal RoPE attention, Q/K-only biases, SwiGLU, sandwich RMSNorm, input
reinjection, shared core, tied embeddings, truncated depth backpropagation.
Simplified: tiny widths, no KV cache, no padding/packing masks, no distributed
execution, no optimizer/EMA recipe, no kernel fusion/checkpointing, no learned
halting. The same full sequence is recomputed during generation. No HA checker
is supplied here and generated strings are not proofs.

The shared terminal RMSNorm is applied AFTER the complete recurrent loop and
again after the coda, matching the pinned executable source. It is not applied
as an extra operation at each iteration. Each core transformer layer still has
its own four sandwich norms. A different placement is a separate ablation.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

import torch
from torch import Tensor, nn
from torch.nn import functional as F


@dataclass(frozen=True)
class ModelConfig:
    vocab_size: int = 256
    width: int = 128
    heads: int = 4
    mlp_width: int = 384
    prelude_layers: int = 1
    core_layers: int = 2
    coda_layers: int = 1
    reference_recurrence: int = 4
    max_sequence_length: int = 512
    rope_base: float = 50000.0
    norm_eps: float = 1e-6
    state_std: float = math.sqrt(2.0 / 5.0)

    def __post_init__(self) -> None:
        positive = (self.vocab_size, self.width, self.heads, self.mlp_width,
                    self.core_layers, self.reference_recurrence,
                    self.max_sequence_length)
        if any(x <= 0 for x in positive):
            raise ValueError("Model dimensions, core depth and reference depth must be positive")
        if self.prelude_layers < 0 or self.coda_layers < 0:
            raise ValueError("Prelude/coda depth must be nonnegative")
        if self.width % self.heads or (self.width // self.heads) % 2:
            raise ValueError("width must divide by heads with an even RoPE head dimension")
        if self.norm_eps <= 0 or self.rope_base <= 1 or self.state_std < 0:
            raise ValueError("Invalid norm, rotary base or initial-state scale")


class RMSNorm(nn.Module):
    def __init__(self, width: int, eps: float):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(width))
        self.eps = eps

    def forward(self, x: Tensor) -> Tensor:
        # Keep reduction in float32, retaining the activation dtype afterwards.
        y = x.float()
        y = y * torch.rsqrt(y.square().mean(dim=-1, keepdim=True) + self.eps)
        return y.to(x.dtype) * self.weight.to(x.dtype)


class CausalAttention(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.heads = cfg.heads
        self.head_dim = cfg.width // cfg.heads
        self.qkv = nn.Linear(cfg.width, 3 * cfg.width, bias=False)
        self.q_bias = nn.Parameter(torch.zeros(cfg.width))
        self.k_bias = nn.Parameter(torch.zeros(cfg.width))
        self.out = nn.Linear(cfg.width, cfg.width, bias=False)
        inv_freq = cfg.rope_base ** (
            -torch.arange(0, self.head_dim, 2, dtype=torch.float32) / self.head_dim
        )
        self.register_buffer("inv_freq", inv_freq, persistent=False)

    def _rope(self, x: Tensor) -> Tensor:
        # x has shape [batch, heads, sequence, head_dim]; adjacent pairs rotate.
        positions = torch.arange(x.shape[-2], device=x.device, dtype=torch.float32)
        theta = positions[:, None] * self.inv_freq.float()[None, :]
        cos, sin = theta.cos().to(x.dtype), theta.sin().to(x.dtype)
        a, b = x[..., 0::2], x[..., 1::2]
        return torch.stack((a * cos - b * sin, a * sin + b * cos), dim=-1).flatten(-2)

    def forward(self, x: Tensor) -> Tensor:
        batch, sequence, width = x.shape
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        q = q + self.q_bias.to(q.dtype)
        k = k + self.k_bias.to(k.dtype)
        q, k, v = [
            y.reshape(batch, sequence, self.heads, self.head_dim).transpose(1, 2)
            for y in (q, k, v)
        ]
        y = F.scaled_dot_product_attention(
            self._rope(q), self._rope(k), v, dropout_p=0.0, is_causal=True
        )
        return self.out(y.transpose(1, 2).reshape(batch, sequence, width))


class GatedMLP(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.gate_value = nn.Linear(cfg.width, 2 * cfg.mlp_width, bias=False)
        self.out = nn.Linear(cfg.mlp_width, cfg.width, bias=False)

    def forward(self, x: Tensor) -> Tensor:
        gate, value = self.gate_value(x).chunk(2, dim=-1)
        return self.out(F.silu(gate) * value)


class TransformerBlock(nn.Module):
    def __init__(self, cfg: ModelConfig, norm_style: Literal["sandwich", "pre"] = "sandwich"):
        super().__init__()
        if norm_style not in ("sandwich", "pre"):
            raise ValueError("norm_style must be sandwich or pre")
        self.norm_style = norm_style
        self.n1 = RMSNorm(cfg.width, cfg.norm_eps)
        self.n3 = RMSNorm(cfg.width, cfg.norm_eps)
        self.n2 = RMSNorm(cfg.width, cfg.norm_eps) if norm_style == "sandwich" else nn.Identity()
        self.n4 = RMSNorm(cfg.width, cfg.norm_eps) if norm_style == "sandwich" else nn.Identity()
        self.attention = CausalAttention(cfg)
        self.mlp = GatedMLP(cfg)

    def forward(self, x: Tensor) -> Tensor:
        x = self.n2(x + self.attention(self.n1(x)))
        return self.n4(x + self.mlp(self.n3(x)))


def _initialize(model: nn.Module, cfg: ModelConfig, reference_depth: int) -> None:
    """Small teaching version of the paper's scale-sensitive initialization."""
    base_std = math.sqrt(2.0 / (5.0 * cfg.width))
    out_std = math.sqrt(1.0 / (5.0 * cfg.width * reference_depth))
    for module in model.modules():
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.trunc_normal_(module.weight, std=base_std,
                                  a=-3.0 * base_std, b=3.0 * base_std)
    for module in model.modules():
        if isinstance(module, (CausalAttention, GatedMLP)):
            nn.init.trunc_normal_(module.out.weight, std=out_std,
                                  a=-3.0 * out_std, b=3.0 * out_std)


def _check_tokens(tokens: Tensor, cfg: ModelConfig) -> None:
    if tokens.ndim != 2 or tokens.dtype != torch.long:
        raise ValueError("tokens must be a [batch, sequence] torch.long tensor")
    if tokens.shape[0] < 1 or not (1 <= tokens.shape[1] <= cfg.max_sequence_length):
        raise ValueError("Empty batch or sequence outside configured limit")


class RecurrentLM(nn.Module):
    def __init__(self, cfg: ModelConfig):
        super().__init__()
        self.cfg = cfg
        self.embedding = nn.Embedding(cfg.vocab_size, cfg.width)
        self.prelude = nn.ModuleList(TransformerBlock(cfg) for _ in range(cfg.prelude_layers))
        self.adapter = nn.Linear(2 * cfg.width, cfg.width, bias=False)
        self.core = nn.ModuleList(TransformerBlock(cfg) for _ in range(cfg.core_layers))
        self.coda = nn.ModuleList(TransformerBlock(cfg) for _ in range(cfg.coda_layers))
        self.final_norm = RMSNorm(cfg.width, cfg.norm_eps)
        # F.linear below uses embedding.weight directly; no second Parameter exists.
        _initialize(self, cfg, self.block_evaluations(cfg.reference_recurrence))

    def block_evaluations(self, recurrence: int) -> int:
        return self.cfg.prelude_layers + recurrence * self.cfg.core_layers + self.cfg.coda_layers

    def encode(self, tokens: Tensor) -> Tensor:
        _check_tokens(tokens, self.cfg)
        e = self.embedding(tokens) * math.sqrt(self.cfg.width)
        for block in self.prelude:
            e = block(e)
        return e

    def core_step(self, state: Tensor, embedding: Tensor) -> Tensor:
        state = self.adapter(torch.cat((state, embedding), dim=-1))
        for block in self.core:
            state = block(state)
        return state

    def initial_state(self, embedding: Tensor) -> Tensor:
        if self.cfg.state_std == 0:
            return torch.zeros_like(embedding)
        state = torch.empty_like(embedding)
        return nn.init.trunc_normal_(state, std=self.cfg.state_std,
                                     a=-3 * self.cfg.state_std, b=3 * self.cfg.state_std)

    def forward(
        self,
        tokens: Tensor,
        recurrence: int,
        *,
        backprop_depth: int | None = None,
        initial_state: Tensor | None = None,
        return_trace: bool = False,
    ) -> dict[str, Tensor | int | None]:
        if recurrence < 1:
            raise ValueError("recurrence must be at least one")
        if backprop_depth is not None and backprop_depth < 1:
            raise ValueError("backprop_depth must be positive or None for full gradients")
        e = self.encode(tokens)
        state = self.initial_state(e) if initial_state is None else initial_state
        if state.shape != e.shape or state.device != e.device or state.dtype != e.dtype:
            raise ValueError("initial_state must match encoded sequence shape, device and dtype")
        k = recurrence if backprop_depth is None else min(backprop_depth, recurrence)
        warmup = recurrence - k
        trace: list[Tensor] = []
        # Keep e attached: the last k injections must update the prelude.
        with torch.no_grad():
            for _ in range(warmup):
                state = self.core_step(state, e)
                if return_trace:
                    trace.append(state.detach().clone())
        for _ in range(k):
            state = self.core_step(state, e)
            if return_trace:
                trace.append(state.detach().clone())
        latent = self.final_norm(state)
        out = latent
        for block in self.coda:
            out = block(out)
        out = self.final_norm(out)
        logits = F.linear(out, self.embedding.weight)
        return {"logits": logits, "latent": latent,
                "trace": torch.stack(trace, dim=0) if return_trace else None,
                "recurrence": recurrence, "backprop_depth": k}


class StandardTransformerLM(nn.Module):
    """Untied finite-depth baseline using the same attention/MLP and tokenizer.

    Default sandwich norms isolate the macroscopic recurrence difference.
    norm_style='pre' adds a conventional pre-norm comparator; its changed
    normalization must be reported as a separate ablation. Depth and unique
    parameter count are explicit, not silently advertised as matched.
    """

    def __init__(self, cfg: ModelConfig, layers: int,
                 norm_style: Literal["sandwich", "pre"] = "sandwich",
                 initialization_depth: int | None = None):
        super().__init__()
        if layers < 1:
            raise ValueError("layers must be positive")
        self.cfg = cfg
        self.embedding = nn.Embedding(cfg.vocab_size, cfg.width)
        self.layers = nn.ModuleList(TransformerBlock(cfg, norm_style) for _ in range(layers))
        self.final_norm = RMSNorm(cfg.width, cfg.norm_eps)
        init_depth = layers if initialization_depth is None else initialization_depth
        if init_depth < 1:
            raise ValueError("initialization_depth must be positive")
        _initialize(self, cfg, init_depth)

    def forward(self, tokens: Tensor) -> dict[str, Tensor]:
        _check_tokens(tokens, self.cfg)
        x = self.embedding(tokens) * math.sqrt(self.cfg.width)
        for block in self.layers:
            x = block(x)
        x = self.final_norm(x)
        return {"logits": F.linear(x, self.embedding.weight)}


def sample_recurrence(rate_mean: float, *, log_rate_std: float = 0.5,
                      generator: torch.Generator | None = None) -> int:
    """Poisson-lognormal+1; E[result]=rate_mean+1, not rate_mean.

    This CPU sampler is for a SLURM training process. In distributed use the
    caller must sample once and broadcast or synchronize the generator. It has
    no hidden cap; pre-register any bounded alternative and log its distinct law.
    """
    if (not math.isfinite(rate_mean) or not math.isfinite(log_rate_std)
            or rate_mean <= 0 or log_rate_std < 0):
        raise ValueError("Invalid Poisson rate mean or log-rate standard deviation")
    mu = math.log(rate_mean) - 0.5 * log_rate_std ** 2
    z = torch.randn((), generator=generator)
    rate = torch.exp(mu + log_rate_std * z)
    return int(torch.poisson(rate, generator=generator).item()) + 1


def next_token_loss(logits: Tensor, tokens: Tensor) -> Tensor:
    """Explicit shift: logits at position t predict token t+1, without padding."""
    if logits.ndim != 3 or logits.shape[:2] != tokens.shape or tokens.shape[1] < 2:
        raise ValueError("Need aligned [batch, sequence, vocab] logits and at least two tokens")
    return F.cross_entropy(logits[:, :-1].float().reshape(-1, logits.shape[-1]),
                           tokens[:, 1:].reshape(-1))


def unique_parameter_count(model: nn.Module) -> int:
    """Parameters stored once; independent of the chosen recurrent depth."""
    return sum(p.numel() for p in model.parameters())
