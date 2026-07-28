# Peano Lab proof-trace release v1

This directory is the deterministic learning-data release whose provenance follows the checked
theorem catalog. Its semantic families remain the M13 set. The current 137-theorem source tree
has its own fresh fingerprints rather than reusing either parent branch's hashes. The release contains
**13,344** clean, deduplicated version-1 tactic transitions from **1,692** generated proof
sessions:

| Artifact | Role | Records | SHA-256 |
|---|---|---:|---|
| `train.jsonl` | learning split | 13,326 | `b609e5dfd8704a6e529c0cd4761a6334bbf5b58adde88197d203dc403540e021` |
| `val.jsonl` | exact-theorem-group validation split | 18 | `2ce2a1be1d42183104c5959f0b78a8f2ade5fe602a9d299cb25a718764742edc` |
| `stats.json` | split, deduplication, outcome, and tactic statistics | — | `b3a6e59634e6ec9be0613577afff4f0350d876385734ce98e743d89c37b17c06` |
| `generation-manifest.json` | configuration, source fingerprints, and per-session provenance | — | `1d7fe18ab84bc3f1aed6e9e71abb73b654f96d3cb563ea53666d425f9dba21bb` |

The source stream contained 11,652 successful and 1,692 deliberately failing, transactional
applications, for a labeled failure ratio of `0.12679856115107913`. Every one of the 1,692 sessions
reached QED through the production proof engine and was independently finalized against its
owner-held original theorem. The released rows themselves are transitions—not certificates—and
their `status` or manifest metadata is never proof authority.

## Leakage boundary

The release contains 1,500 seeded alpha-renamed reflexive-arithmetic conjunctions, 96 seeded
addition-commutativity variants, and 96 bounded closed-coefficient `norm_num` sessions. Both
`ladder_auto` and `ladder_scripts` are disabled in the manifest. Consequently none of the four
fixed evaluation families (`le_trans`, `le_antisymm`, `le_total`, `mul_eq_zero`) or their authored
ladder scripts enters these files. The exact-theorem split is deterministic and semantic
duplicates cannot cross it; logically equivalent near duplicates still require the family-level
manifest audit described in
[`docs/PEANO_LLM.md`](../../docs/PEANO_LLM.md).

Validation is intentionally a small pipeline check, not the final research claim: deterministic
hash ranking selected nine closed-coefficient formula groups, each with its controlled syntax
failure and successful `norm_num` transition, for 18 rows total. It is entirely one generated
family and is not a cross-family generalization split. Report model quality only on the fixed,
separately kernel-judged held-out ladder families.

## Reproduce

From the repository root, using the exact checked-out generator and kernel:

```console
make peano-corpus
```

The reproducible release uses generator v2 and CPython 3.10.0, recorded in the manifest;
transition and manifest schemas remain v1. The Make target checks this and accepts
`PEANO_CORPUS_PYTHON=/path/to/python3.10`
when that interpreter is not the ambient `python3`.

That target first writes the replayable raw session stream to
`/tmp/peano-lab-release-raw.jsonl`, then strictly validates, globally deduplicates, and exports it.
The raw intermediate is not committed because it duplicates the split payload, but the manifest
records its exact UTF-8 size (6,215,711 bytes) and SHA-256
`23674d005abef7bca178948b04c376cb4c05014c41965a744d19ff8140ba1e2e`.
It also fingerprints `scripts/generate_peano_traces.py`, the trusted checker, and the complete
Peano Lab Python source tree. Because the Python runtime participates in the run fingerprint and
session IDs, changing that runtime changes the raw byte hash even when every session-agnostic
semantic transition remains the same.

To exercise one-node/depth-one bounded `auto` plumbing attempts and checked authored replays for
every entry in the resolved ladder without contaminating the release, run:

```console
make peano-corpus-smoke
```

Those acceptance artifacts stay under `/tmp`. The data pipeline, corpus, and this README are
released under the repository's MIT License.
