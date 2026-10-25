"""Equivalent V4 token masks with bounded batched host transfers and GPU caches.

The frozen authority.py remains the training-bound reference implementation.
This execution-only implementation retains its token ordering, EOS rules and
whole-line postflight. It does not repair, retry, sample or execute a tactic.
No model framework is imported until a logits tensor is actually processed.
"""

from __future__ import annotations

from collections import OrderedDict
from functools import lru_cache
from threading import RLock
from typing import Any

from .authority import (
    AuthorityTokenConstraint, MAX_AUTHORITY_NEW_TOKENS, MAX_VOCABULARY, _environment,
)
from .prompt import PromptEnvironment

RUNTIME_VERSION = "peano-authority-batched-masks-v1"
MAX_TEMPLATE_CACHE = 2
MAX_MASK_CACHE = 32
MAX_TOKEN_SELECTION_CACHE = 64
MAX_BEAMS = 64
MAX_MASK_ELEMENT_BYTES = 8


def authority_runtime_record() -> dict[str, object]:
    return {
        "implementation": RUNTIME_VERSION,
        "reference": "training/peano_policy/authority.py",
        "authority_semantics_changed": False,
        "host_transfer": "one bounded suffix-only batch per decoding step",
        "template_cache_size": MAX_TEMPLATE_CACHE,
        "mask_cache_size_per_template": MAX_MASK_CACHE,
        "token_selection_cache_size_per_template": MAX_TOKEN_SELECTION_CACHE,
        "maximum_beams": MAX_BEAMS,
        "maximum_mask_element_bytes": MAX_MASK_ELEMENT_BYTES,
        "maximum_cached_mask_bytes": (
            MAX_TEMPLATE_CACHE * MAX_MASK_CACHE * MAX_VOCABULARY * MAX_MASK_ELEMENT_BYTES
        ),
        "model_weights_or_outputs_cached": False,
    }


class _Templates:
    def __init__(self, tokenizer: Any, environment: PromptEnvironment) -> None:
        self.reference = AuthorityTokenConstraint(
            tokenizer, environment, prompt_length=0,
            max_new_tokens=MAX_AUTHORITY_NEW_TOKENS,
        )
        self.vocabulary = self.reference.vocabulary
        self.maximum_token_id = max(self.vocabulary.known_ids)
        self.body_with_eos = self.vocabulary.body_ids + (self.vocabulary.eos,)
        self.tokens: OrderedDict[tuple[str, int], tuple[int, ...]] = OrderedDict()
        self.masks: OrderedDict[tuple[object, ...], Any] = OrderedDict()
        self.lock = RLock()

    def key(self, suffix: list[int] | tuple[int, ...]) -> tuple[str, int]:
        # Deliberately mirror the frozen reference's state machine. Differential
        # tests compare every returned token and each rejected prefix.
        node = 0
        mode = None
        body: list[str] = []
        for index, token in enumerate(suffix):
            if mode == "body":
                if token == self.vocabulary.eos and body and not body[-1][-1].isspace() and not body[-1].endswith("<"):
                    if any(rest != self.vocabulary.eos for rest in suffix[index:]):
                        raise ValueError("non-EOS token follows completed authority output")
                    return ("eos", 0)
                piece = self.vocabulary.pieces.get(token)
                if piece is None:
                    raise ValueError("generated token is outside the safe primitive argument alphabet")
                if body and body[-1].endswith("<") and not piece.startswith(("-", "=")):
                    raise ValueError("less-than token can continue only as <- or <=, never markup")
                body.append(piece)
            elif token in self.reference.nodes[node]:
                node = self.reference.nodes[node][token]
                mode = self.reference.terminal.get(node)
            elif token == self.vocabulary.eos and mode in {"end", "end-or-args"}:
                if any(rest != self.vocabulary.eos for rest in suffix[index:]):
                    raise ValueError("non-EOS token follows completed authority output")
                return ("eos", 0)
            elif mode in {"args", "end-or-args"}:
                piece = self.vocabulary.pieces.get(token)
                if piece is None or not piece.startswith(" "):
                    raise ValueError("primitive arguments must start with an ASCII space")
                mode = "body"
                body.append(piece)
            else:
                raise ValueError("generated prefix is outside the exact primitive authority trie")
        if mode == "body":
            if body and body[-1].endswith("<"):
                return ("less", 0)
            return ("body", int(bool(body and not body[-1][-1].isspace())))
        return ("head", node)

    def allowed(self, key: tuple[str, int]) -> tuple[int, ...]:
        kind, node = key
        if kind == "body":
            return self.body_with_eos if node else self.vocabulary.body_ids
        if kind == "less":
            return self.vocabulary.less_ids
        if kind == "eos":
            return (self.vocabulary.eos,)
        if kind != "head":
            raise ValueError("unknown authority token-mask state")
        with self.lock:
            cached = self.tokens.get(key)
            if cached is not None:
                self.tokens.move_to_end(key)
                return cached
            mode = self.reference.terminal.get(node)
            result = tuple(sorted(self.reference.nodes[node]))
            if mode in {"args", "end-or-args"}:
                result += self.vocabulary.space_ids
            if mode in {"end", "end-or-args"}:
                result += (self.vocabulary.eos,)
            if not result:
                raise ValueError("authority decoder reached an impossible prefix")
            self.tokens[key] = result
            while len(self.tokens) > MAX_TOKEN_SELECTION_CACHE:
                self.tokens.popitem(last=False)
            return result

    def mask(self, scores: Any, key: tuple[str, int], torch: Any) -> Any:
        width = scores.shape[1]
        cache_key = (str(scores.device), str(scores.dtype), width, *key)
        with self.lock:
            cached = self.masks.get(cache_key)
            if cached is not None:
                self.masks.move_to_end(cache_key)
                return cached
            allowed = self.allowed(key)
            if not allowed:
                raise ValueError("authority decoder reached an impossible prefix")
            mask = scores.new_full((width,), float("-inf"))
            indices = torch.tensor(allowed, dtype=torch.long, device=scores.device)
            mask.index_fill_(0, indices, 0.0)
            self.masks[cache_key] = mask
            while len(self.masks) > MAX_MASK_CACHE:
                self.masks.popitem(last=False)
            return mask


@lru_cache(maxsize=MAX_TEMPLATE_CACHE)
def _templates(tokenizer: Any, environment: PromptEnvironment) -> _Templates:
    return _Templates(tokenizer, environment)


def clear_authority_runtime_cache() -> None:
    """Release cached token templates and mask tensors, never model state."""
    _templates.cache_clear()


def authority_runtime_cache_info() -> dict[str, int]:
    info = _templates.cache_info()
    return {"hits": info.hits, "misses": info.misses,
            "size": info.currsize, "maximum": info.maxsize}


class RuntimeTokenConstraint:
    """Model-free immutable token selection, equivalent to the frozen callback."""

    def __init__(self, tokenizer: Any, environment: PromptEnvironment, *,
                 max_new_tokens: int = 64) -> None:
        _environment(environment)
        if type(max_new_tokens) is not int or not 1 <= max_new_tokens <= MAX_AUTHORITY_NEW_TOKENS:
            raise ValueError("authority max_new_tokens must be an integer in [1,128]")
        self.max_new_tokens = max_new_tokens
        self.templates = _templates(tokenizer, environment)
        self.vocabulary = self.templates.vocabulary

    def mask_key(self, suffix: list[int] | tuple[int, ...]) -> tuple[str, int]:
        if type(suffix) not in {list, tuple}:
            raise ValueError("authority callback requires a complete one-dimensional prompt prefix")
        if len(suffix) > self.max_new_tokens or any(type(token) is not int for token in suffix):
            raise ValueError("authority prefix exceeds its generation bound")
        return self.templates.key(suffix)

    def allowed_tokens(self, suffix: list[int] | tuple[int, ...]) -> tuple[int, ...]:
        return self.templates.allowed(self.mask_key(suffix))


class AuthorityLogitsProcessor:
    """Same zero/-infinity masks, avoiding per-beam vocabulary-sized transfers.

    Use as a normal Hugging Face logits processor, without also installing the
    old prefix callback. No softmax, score adjustment, beam reordering, token
    filtering change, or extra generation call is introduced.
    """

    def __init__(self, tokenizer: Any, environment: PromptEnvironment, *,
                 prompt_length: int, max_new_tokens: int) -> None:
        if type(prompt_length) is not int or prompt_length < 0:
            raise ValueError("prompt_length must be a nonnegative integer")
        self.prompt_length = prompt_length
        self.constraint = RuntimeTokenConstraint(
            tokenizer, environment, max_new_tokens=max_new_tokens,
        )

    def __call__(self, input_ids: Any, scores: Any) -> Any:
        import torch

        shape = tuple(input_ids.shape)
        score_shape = tuple(scores.shape)
        if (len(shape) != 2 or len(score_shape) != 2 or
                not 1 <= shape[0] <= MAX_BEAMS or score_shape[0] != shape[0] or
                shape[1] < self.prompt_length):
            raise ValueError("authority logits processor requires matching bounded two-dimensional beams")
        if shape[1] - self.prompt_length > self.constraint.max_new_tokens:
            raise ValueError("authority prefix exceeds its generation bound")
        if (not scores.is_floating_point() or
                not 1 <= score_shape[1] <= MAX_VOCABULARY or
                self.constraint.templates.maximum_token_id >= score_shape[1] or
                scores.element_size() > MAX_MASK_ELEMENT_BYTES):
            raise ValueError("authority logits vocabulary or score dtype differs")
        # A single GPU -> CPU synchronization; the (potentially large) prompt
        # never crosses this boundary. Every beam still gets independent checks.
        suffixes = input_ids[:, self.prompt_length:].tolist()
        if type(suffixes) is not list or len(suffixes) != shape[0]:
            raise ValueError("authority logits processor lost its complete beam suffixes")
        keys = [self.constraint.mask_key(suffix) for suffix in suffixes]
        masks = [self.constraint.templates.mask(scores, key, torch) for key in keys]
        return scores + torch.stack(masks, dim=0)


def generation_constraints(model: Any, tokenizer: Any, environment: PromptEnvironment, *,
                           prompt_length: int, max_new_tokens: int) -> dict[str, Any]:
    """Optimize the ordinary pinned configuration without reordering overrides.

    Hugging Face installs custom processors after several optional overrides.
    Models enabling those overrides keep the exact original prefix processor
    in its original position. This selects an equivalent implementation, never
    an extra model call, candidate repair, or alternative proof policy.
    """
    configuration = getattr(model, "generation_config", None)
    ordered_overrides = (
        "forced_bos_token_id", "forced_eos_token_id", "exponential_decay_length_penalty",
        "suppress_tokens", "begin_suppress_tokens",
    )
    if configuration is not None and (
        any(getattr(configuration, name, None) is not None for name in ordered_overrides)
        or getattr(configuration, "remove_invalid_values", False) is True
    ):
        return {"prefix_allowed_tokens_fn": AuthorityTokenConstraint(
            tokenizer, environment, prompt_length=prompt_length, max_new_tokens=max_new_tokens,
        )}
    return {"logits_processor": [AuthorityLogitsProcessor(
        tokenizer, environment, prompt_length=prompt_length, max_new_tokens=max_new_tokens,
    )]}


__all__ = [
    "RUNTIME_VERSION", "RuntimeTokenConstraint", "AuthorityLogitsProcessor",
    "authority_runtime_record", "authority_runtime_cache_info",
    "clear_authority_runtime_cache", "generation_constraints",
]
