"""Byte-tokenized compact proof-state records; no pretrained tokenizer."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import random
import torch

BOS_EOS = 256
PAD = 257
VOCAB_SIZE = 258


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_rows(path, max_length):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines()]
    if not rows or len({row["id"] for row in rows}) != len(rows):
        raise ValueError("empty or duplicate dataset")
    for row in rows:
        prompt = list(row["prompt"].encode("utf-8"))
        completion = list(row["completion"].encode("utf-8"))
        seq = [BOS_EOS] + prompt + completion + [BOS_EOS]
        if not completion or len(seq) > max_length:
            raise ValueError("unadmitted length; do not silently truncate")
        row["tokens"] = seq
        row["prompt_bytes"] = len(prompt)
    return sorted(rows, key=lambda row: row["id"])


def batch(rows, device):
    length = max(len(row["tokens"]) - 1 for row in rows)
    tokens = torch.full((len(rows), length), PAD, dtype=torch.long, device=device)
    labels = torch.full_like(tokens, -100)
    for index, row in enumerate(rows):
        seq = row["tokens"]
        tokens[index, :len(seq)-1] = torch.tensor(seq[:-1], device=device)
        start = row["prompt_bytes"]
        labels[index, start:len(seq)-1] = torch.tensor(seq[start+1:], device=device)
    return tokens, labels


class ExampleStream:
    """A permutation stream independent of initialization and recurrence RNG."""
    def __init__(self, rows, seed):
        self.rows = rows
        self.rng = random.Random(seed + 610341)
        self.order = []
        self.offset = 0

    def take(self, n):
        selected = []
        while len(selected) < n:
            if self.offset == len(self.order):
                self.order = list(range(len(self.rows)))
                self.rng.shuffle(self.order)
                self.offset = 0
            count = min(n - len(selected), len(self.order) - self.offset)
            selected.extend(self.rows[i] for i in self.order[self.offset:self.offset+count])
            self.offset += count
        return selected

    def state_dict(self):
        return {"order": self.order, "offset": self.offset, "rng": self.rng.getstate()}

    def load_state_dict(self, state):
        self.order, self.offset = state["order"], state["offset"]
        self.rng.setstate(state["rng"])


def evaluation_subset(rows, count, namespace):
    return sorted(rows, key=lambda r: hashlib.sha256((namespace + r["id"]).encode()).hexdigest())[:count]
