"""CPU-only tokenizer metadata timing; no model/MLX/Torch import."""
import hashlib
import json
from pathlib import Path
import sys
import time

started = time.monotonic()
from tokenizers import Tokenizer

path = Path(sys.argv[1])
raw = path.read_bytes()
tokenizer = Tokenizer.from_file(str(path))
rows = []
for with_added in (False, True):
    begin = time.monotonic()
    sizes = [tokenizer.get_vocab_size(with_added_tokens=with_added) for _ in range(20)]
    seconds = time.monotonic() - begin
    rows.append({"with_added_tokens": with_added, "calls": 20, "values": sorted(set(sizes)),
                 "seconds": seconds, "seconds_per_call": seconds / 20})
length = tokenizer.get_vocab_size(with_added_tokens=True)
begin = time.monotonic()
sizes = [length for _ in range(20)]
cached_seconds = time.monotonic() - begin
for name in sys.modules:
    if name.split(".")[0] in {"mlx", "mlx_lm", "torch", "transformers"}:
        raise RuntimeError("Unexpected model framework import: " + name)
print(json.dumps({"schema": "hydra-tokenizer-size-cpu-microcheck-v1", "model_loaded": False,
    "frameworks_imported": False, "tokenizer_sha256": hashlib.sha256(raw).hexdigest(),
    "tokenizer_bytes": len(raw), "measurements": rows, "cached_local_20_reads_seconds": cached_seconds,
    "whole_seconds": time.monotonic() - started}), flush=True)
