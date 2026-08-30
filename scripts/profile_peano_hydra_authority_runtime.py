#!/usr/bin/env python3
"""Bounded CPU-only token-selection profile using the already collected tokenizer.

No model, torch, transformers, GPU, downloads, corpus generation or proof search.
Timings compare token selection only, not generation or CUDA synchronization.
Run under the existing owned-process guard when collecting an audit receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "peano-lab/py"):
    sys.path.insert(0, str(directory))

TOKENIZER_SHA256 = "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4"
MAX_BYTES = 16 * 1024**2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=256)
    args = parser.parse_args()
    if not 1 <= args.iterations <= 1024:
        parser.error("--iterations must be in [1,1024]")
    if {"torch", "transformers", "peft"} & set(sys.modules):
        raise ValueError("token-only profile must start without model frameworks")
    with os.fdopen(os.open(args.tokenizer, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or not 1 <= before.st_size <= MAX_BYTES:
            raise ValueError("tokenizer must be a bounded regular file")
        raw = stream.read(MAX_BYTES + 1)
        after = os.fstat(stream.fileno())
    if (len(raw) != before.st_size or
            (before.st_size, before.st_mtime_ns, before.st_ctime_ns) !=
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns) or
            hashlib.sha256(raw).hexdigest() != TOKENIZER_SHA256):
        raise ValueError("tokenizer changed or differs from the pinned collected bytes")

    import tokenizers
    from training.peano_policy.authority import (
        AUTHORITY_PRIMITIVE_COMMANDS, AuthorityTokenConstraint, _vocabulary,
    )
    from training.peano_policy.authority_runtime import (
        RuntimeTokenConstraint, authority_runtime_record, clear_authority_runtime_cache,
    )
    from training.peano_policy.contract import authority_prompt_environment
    from training.peano_policy.prompt import CapabilityIdentity

    backend = tokenizers.Tokenizer.from_str(raw.decode("utf-8"))
    del raw

    class TokenizerOnly:
        backend_tokenizer = backend
        eos_token_id = backend.token_to_id("<|endoftext|>")
        pad_token_id = eos_token_id
        all_special_ids = [number for number, token in backend.get_added_tokens_decoder().items() if token.special]

        def get_vocab(self):
            return backend.get_vocab()

        def encode(self, text, *, add_special_tokens=False):
            return backend.encode(text, add_special_tokens=add_special_tokens).ids

        def decode(self, values, *, skip_special_tokens, clean_up_tokenization_spaces=False):
            if clean_up_tokenization_spaces is not False:
                raise ValueError("token-only profile forbids cleanup")
            return backend.decode(values, skip_special_tokens=skip_special_tokens)

    class Values(list):
        def tolist(self):
            return list(self)

    tokenizer = TokenizerOnly()
    environment = authority_prompt_environment(False, CapabilityIdentity(
        "hydra-authority-no-imports-v1", tuple(sorted(AUTHORITY_PRIMITIVE_COMMANDS)), (),
    ))
    clear_authority_runtime_cache()
    _vocabulary.cache_clear()
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    reference = AuthorityTokenConstraint(tokenizer, environment, prompt_length=4096, max_new_tokens=64)
    cold = {"wall_seconds": time.perf_counter() - start_wall, "cpu_seconds": time.process_time() - start_cpu}
    runtime = RuntimeTokenConstraint(tokenizer, environment, max_new_tokens=64)
    rows = []
    for prefix in ("", "intro", "refl", "rewrite", "intro ", "intro n",
                   "rewrite <- IH", "have h : n <", "have h : n <= n"):
        suffix = tokenizer.encode(prefix)
        padded = Values([999] * reference.prompt_length + suffix)
        expected = tuple(reference(0, padded))
        actual = runtime.allowed_tokens(suffix)
        if actual != expected:
            raise ValueError(f"token-selection parity failed for {prefix!r}")
        timings = {}
        for name, callback in (
            ("reference", lambda: reference(0, padded)),
            ("batched_runtime_selection", lambda: runtime.allowed_tokens(suffix)),
        ):
            start_wall, start_cpu = time.perf_counter(), time.process_time()
            count = 0
            for _ in range(args.iterations):
                count += len(callback())
            timings[name] = {
                "wall_seconds": time.perf_counter() - start_wall,
                "cpu_seconds": time.process_time() - start_cpu,
                "calls": args.iterations,
                "total_allowed_ids": count,
            }
        rows.append({
            "prefix": prefix, "suffix_tokens": len(suffix), "allowed_tokens": len(actual),
            "allowed_tokens_sha256": hashlib.sha256(json.dumps(
                list(actual), separators=(",", ":")).encode()).hexdigest(),
            "ordered_token_parity": True, "timings": timings,
        })
    if {"torch", "transformers", "peft"} & set(sys.modules):
        raise ValueError("token-only profile imported a model framework")
    print(json.dumps({
        "schema": "peano-hydra-authority-token-selection-profile-v1",
        "status": "passed", "python": sys.version.split()[0],
        "tokenizers_version": tokenizers.__version__,
        "tokenizer_sha256": TOKENIZER_SHA256, "runtime": authority_runtime_record(),
        "reference_prompt_tokens": 4096,
        "vocabulary_tokens": len(reference.vocabulary.known_ids),
        "safe_argument_tokens": len(reference.vocabulary.body_ids),
        "cold_reference_vocabulary_and_trie": cold, "cases": rows,
        "model_frameworks_imported": False, "model_weights_loaded": False,
        "cuda_initialized": False,
        "claim": "CPU token-selection microbenchmark only; not end-to-end inference or measured CUDA speedup",
    }, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, RuntimeError) as error:
        print(f"authority-runtime-profile: {error}", file=sys.stderr)
        raise SystemExit(2)
