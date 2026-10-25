"""PROPOSED, NOT ACTIVATED: one fresh Qwen3 KV cache per literal tactic.

This is an untrusted suggestion backend, not a model loader or proof checker.
The caller must use the authenticated fixed-depth-one model, existing exact
prompt/authority/EOS validators, and all existing provider and worker budgets.
No MLX import, model load, inference, or runtime registration occurs on import.

Integration boundary (future, separately versioned provider): construct a NEW
backend for each fresh CandidatePolicy.propose call; close it in finally. Never
reuse a cache across native steps, proof states, requests, models, or adapters.
"""
from __future__ import annotations

POLICY = "hydra-proposed-per-tactic-kv-v1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


class PerTacticKVBackend:
    model_vocab_size = 151936

    def __init__(self, model, mx, *, kind="latent_compact_v3", max_context_tokens=6144,
                 max_new_tokens=128):
        require(kind in {"latent_compact_v3", "historical_primitive_v4"}, "Unsupported decoder kind")
        require(type(max_context_tokens) is int and 1 < max_context_tokens <= 6144,
                "Invalid context budget")
        require(type(max_new_tokens) is int and 0 < max_new_tokens <= 128, "Invalid decision budget")
        require(model.model_type == "qwen3" and len(model.layers) == 28,
                "Cache proposal supports only the authenticated 28-layer Qwen3 vanilla model")
        require(model.args.num_key_value_heads == 8 and model.args.head_dim == 128
                and model.args.tie_word_embeddings is True, "Unexpected Qwen3 cache/head geometry")
        self.model, self.mx, self.kind = model, mx, kind
        self.max_context_tokens, self.max_new_tokens = max_context_tokens, max_new_tokens
        self._cache = None
        self._sequence = None
        self._last_decision = None
        self._closed = False
        self._poisoned = False
        self._forward_attempts = 0
        self._forward_passes = 0
        self._decisions = 0
        self._prefill_tokens = 0
        self._decode_input_tokens = 0
        self._attempted_prefill_tokens = 0
        self._attempted_decode_input_tokens = 0
        self._peak_cache_bytes = 0
        # Conservative float32 allocation bound, including standard KVCache's
        # 256-token allocation blocks. No quantized/rotating/truncated cache.
        capacity = ((max_context_tokens + 255) // 256) * 256
        self.cache_byte_ceiling = 2 * 28 * 8 * 128 * capacity * 4

    def _cache_bytes(self):
        return sum(item.keys.nbytes + item.values.nbytes for item in self._cache)

    def next_token(self, sequence, allowed_ids, *, forward_started, forward_completed):
        require(not self._closed and not self._poisoned, "Closed or failed tactic cache cannot be reused")
        require(self._decisions < self.max_new_tokens, "Decision budget exhausted")
        require(type(sequence) is list and 0 < len(sequence) <= self.max_context_tokens
                and all(type(token) is int and 0 <= token < self.model_vocab_size for token in sequence),
                "Invalid bounded input token sequence")
        require((allowed_ids is None) is (self.kind == "latent_compact_v3"),
                "Newest model requires unmasked argmax; historical model retains its authority mask")
        if allowed_ids is not None:
            require(bool(allowed_ids) and all(type(t) is int and 0 <= t < self.model_vocab_size for t in allowed_ids),
                    "Invalid authority-token set")
        exact_sequence = tuple(sequence)
        first = self._sequence is None
        if first:
            token_input = sequence
        else:
            # CandidatePolicy provides the full prompt plus previous decisions.
            # An exact one-token extension is the ONLY permitted continuation.
            require(exact_sequence == self._sequence + (self._last_decision,),
                    "Input is not the exact previous prompt plus the last emitted token")
            require(all(item.offset == len(self._sequence) for item in self._cache),
                    "Cache offsets disagree with the previously consumed sequence")
            token_input = sequence[-1:]
        mx = self.mx
        try:
            if first:
                from mlx_lm.models.cache import KVCache
                self._cache = [KVCache() for _ in self.model.layers]
            tokens = mx.array([token_input], dtype=mx.int32)
            # The callback performs the unchanged deadline/cancellation check
            # and charges this actual forward attempt to the candidate policy.
            forward_started()
            self._forward_attempts += 1
            if first:
                self._attempted_prefill_tokens += len(token_input)
            else:
                self._attempted_decode_input_tokens += len(token_input)
            hidden = self.model.model(tokens, cache=self._cache)[:, -1:, :]
            logits = self.model.model.embed_tokens.as_linear(hidden)[:, -1, :].astype(mx.float32)
            # Evaluate both logits and retained K/V before counting completion.
            mx.eval(logits, [item.state for item in self._cache])
            self._forward_passes += 1
            # Completed input work is charged even if subsequent numerical or
            # cache validation rejects the logits and emits no decision token.
            if first:
                self._prefill_tokens += len(token_input)
            else:
                self._decode_input_tokens += len(token_input)
            forward_completed()
            require(tuple(logits.shape) == (1, self.model_vocab_size)
                    and bool(mx.all(mx.isfinite(logits)).item()), "Malformed or non-finite MLX logits")
            require(all(item.offset == len(sequence) for item in self._cache),
                    "Cache failed to consume the exact token input")
            require(all(item.keys.dtype in (mx.float16, mx.bfloat16, mx.float32)
                        and item.values.dtype == item.keys.dtype for item in self._cache),
                    "Unexpected KV dtype")
            cache_bytes = self._cache_bytes()
            self._peak_cache_bytes = max(self._peak_cache_bytes, cache_bytes)
            require(cache_bytes <= self.cache_byte_ceiling, "KV cache allocation exceeded its context bound")
            if allowed_ids is None:
                token = int(mx.argmax(logits, axis=-1).item())
            else:
                indices = mx.array(sorted(set(allowed_ids)), dtype=mx.int32)
                token = int(indices[mx.argmax(logits[0, indices])].item())
            self._sequence, self._last_decision = exact_sequence, token
            self._decisions += 1
            # Preserve the existing numerical-work metadata contract. A cache
            # changes tokens processed, not the number of layers/heads called.
            return token, {"depth": 1, "block_calls": 28, "head_calls": 1, "gate_calls": 0, "readouts": 1}
        except BaseException:
            self._poisoned = True
            self._cache = None
            raise

    def report(self):
        return {"policy": POLICY, "experimental_not_validated": True,
                "fresh_cache_scope": "one_propose_call", "kind": self.kind,
                "forward_attempts": self._forward_attempts, "forward_passes": self._forward_passes,
                "decision_tokens": self._decisions, "prefill_input_tokens": self._prefill_tokens,
                "incremental_input_tokens": self._decode_input_tokens,
                "attempted_prefill_input_tokens": self._attempted_prefill_tokens,
                "attempted_incremental_input_tokens": self._attempted_decode_input_tokens,
                "peak_allocated_kv_bytes": self._peak_cache_bytes,
                "kv_byte_ceiling": self.cache_byte_ceiling,
                "closed": self._closed, "poisoned": self._poisoned,
                "kernel_checked": False}

    def close(self):
        # Drop this tactic's K/V tensors. Do not alter the authenticated model,
        # global device, allocator limit, or another worker's state.
        self._cache = None
        self._sequence = None
        self._last_decision = None
        self._closed = True

    def __enter__(self):
        require(not self._closed and self._sequence is None, "Backend is not a fresh tactic context")
        return self

    def __exit__(self, *_):
        self.close()
