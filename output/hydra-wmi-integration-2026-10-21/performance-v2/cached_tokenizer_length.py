"""Read-only tokenizer facade with one authenticated full-vocabulary length.

The host authenticates and loads the original tokenizer BEFORE wrapping it.
Every encode/decode/vocabulary operation is delegated unchanged. Only __len__
uses a cached integer; no model, numerical decoder, prompt or authority changes.
Run verify_unchanged() at each case boundary and final custody. The original
tokenizer must not be mutated or shared with an external mutator while in use.
"""
from __future__ import annotations

import copy
import hashlib
import json

POLICY = "hydra-immutable-tokenizer-length-v1"


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class _ReadOnly:
    __slots__ = ()

    def __setattr__(self, _name, _value):
        raise TypeError("Authenticated tokenizer view is immutable")

    def __delattr__(self, _name):
        raise TypeError("Authenticated tokenizer view is immutable")


class _DecoderView(_ReadOnly):
    __slots__ = ("__decoder",)

    def __init__(self, decoder):
        object.__setattr__(self, "_DecoderView__decoder", decoder)

    def __getstate__(self):
        return self.__decoder.__getstate__()


class _BackendView(_ReadOnly):
    __slots__ = ("__backend",)

    def __init__(self, backend):
        object.__setattr__(self, "_BackendView__backend", backend)

    def to_str(self, *args, **kwargs):
        return self.__backend.to_str(*args, **kwargs)

    @property
    def decoder(self):
        return _DecoderView(self.__backend.decoder)


class ImmutableTokenizerLength(_ReadOnly):
    __slots__ = ("__tokenizer", "__length", "__identity", "__len_reads")
    _READ_ATTRIBUTES = frozenset({"eos_token_id", "pad_token_id", "bos_token_id", "unk_token_id",
        "eos_token", "pad_token", "bos_token", "unk_token", "all_special_ids", "all_special_tokens",
        "special_tokens_map", "vocab_size", "is_fast", "name_or_path", "model_max_length"})

    def __init__(self, tokenizer):
        if isinstance(tokenizer, ImmutableTokenizerLength):
            raise ValueError("Do not wrap a cached tokenizer again")
        length = len(tokenizer)
        if type(length) is not int or length <= 0 or length > 151936:
            raise ValueError("Unexpected original tokenizer vocabulary size")
        object.__setattr__(self, "_ImmutableTokenizerLength__tokenizer", tokenizer)
        object.__setattr__(self, "_ImmutableTokenizerLength__length", length)
        object.__setattr__(self, "_ImmutableTokenizerLength__len_reads", 0)
        object.__setattr__(self, "_ImmutableTokenizerLength__identity", self._snapshot(length))

    def _snapshot(self, length):
        tokenizer = self.__tokenizer
        return {"length": length,
                "backend_sha256": hashlib.sha256(tokenizer.backend_tokenizer.to_str().encode()).hexdigest(),
                "added_vocab_sha256": _digest(tokenizer.get_added_vocab()),
                "special_ids_sha256": _digest(list(tokenizer.all_special_ids)),
                "special_tokens_map_sha256": _digest(tokenizer.special_tokens_map),
                "eos_token_id": tokenizer.eos_token_id, "pad_token_id": tokenizer.pad_token_id,
                "bos_token_id": tokenizer.bos_token_id}

    def __len__(self):
        object.__setattr__(self, "_ImmutableTokenizerLength__len_reads", self.__len_reads + 1)
        return self.__length

    def __bool__(self):
        return True

    def __getattr__(self, name):
        if name in self._READ_ATTRIBUTES:
            return copy.deepcopy(getattr(self.__tokenizer, name))
        raise AttributeError("Tokenizer view exposes read operations only: " + name)

    @property
    def backend_tokenizer(self):
        return _BackendView(self.__tokenizer.backend_tokenizer)

    def encode(self, *args, **kwargs):
        return self.__tokenizer.encode(*args, **kwargs)

    def decode(self, *args, **kwargs):
        return self.__tokenizer.decode(*args, **kwargs)

    def get_vocab(self, *args, **kwargs):
        return self.__tokenizer.get_vocab(*args, **kwargs)

    def get_added_vocab(self, *args, **kwargs):
        return self.__tokenizer.get_added_vocab(*args, **kwargs)

    def convert_ids_to_tokens(self, *args, **kwargs):
        return self.__tokenizer.convert_ids_to_tokens(*args, **kwargs)

    def convert_tokens_to_ids(self, *args, **kwargs):
        return self.__tokenizer.convert_tokens_to_ids(*args, **kwargs)

    def report(self):
        return {"policy": POLICY, "cached_length": self.__length,
                "cached_len_reads": self.__len_reads, "identity": copy.deepcopy(self.__identity),
                "model_or_decoder_changed": False, "kernel_checked": False}

    def verify_unchanged(self):
        # Deliberately uncached. Approximately one full-vocabulary query plus
        # serialization per case boundary replaces hundreds of queries/step.
        current = self._snapshot(len(self.__tokenizer))
        if current != self.__identity:
            raise ValueError("Authenticated tokenizer changed after its length was captured")
        return {**self.report(), "custody_status": "verified", "uncached_length": current["length"]}


def install_cached_length(authenticated_tokenizer):
    """Return the view; the host explicitly assigns policy.tokenizer = view.

Do not replace policy.backend. One wrapper is shared with that loaded policy's
fresh cases so the original authority vocabulary memoization remains effective.
"""
    return ImmutableTokenizerLength(authenticated_tokenizer)
