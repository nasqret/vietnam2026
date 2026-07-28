# Peano Lab proof-trace release v1

This directory is the deterministic learning-data release whose provenance follows the checked
theorem catalog. Its semantic families remain the M13 set. The current 183-theorem source tree
has its own fresh fingerprints rather than reusing either parent branch's hashes. The release contains
**13,344** clean, deduplicated version-1 tactic transitions from **1,692** generated proof
sessions:

| Artifact | Role | Records | SHA-256 |
|---|---|---:|---|
| `train.jsonl` | learning split | 13,326 | `d39720bfeeeb159d0f8ca9f331294b6c6135ea36f0585b46efa0768945f953bb` |
| `val.jsonl` | exact-theorem-group validation split | 18 | `d8986e2b260907c909ed1c2b0926fd02a9aa0df748a37656bcdf820c591299fd` |
| `stats.json` | split, deduplication, outcome, and tactic statistics | — | `2bfd4d68ed205d67e0aedf6acb349cfdc7880adcc3b0cf2f41be557b2cee6c58` |
| `generation-manifest.json` | configuration, source fingerprints, and per-session provenance | — | `5c50e4afd0e41272ed8781e7d43bf6d4c985a2eee11b1c33953f016b8f808211` |

The deterministic run fingerprint is
`d0649a05ab1a88396d2d3046bc10a814e374cb3cf5ad8df225c9e15e91ff0df6`.

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
`ee804b6a6ff0b497df192806a99bc6d975d775a84879189aa1251178aa865556`.
It also fingerprints `scripts/generate_peano_traces.py`, the trusted checker, and the complete
Peano Lab Python source tree. Because the Python runtime participates in the run fingerprint and
session IDs, changing that runtime changes the raw byte hash even when every session-agnostic
semantic transition remains the same.

To exercise one-node/depth-one bounded `auto` plumbing attempts and checked authored replays for
every entry in the resolved ladder without contaminating the release, run:

```console
make peano-corpus-smoke
```

The current 183-entry smoke has 366 sessions, 4,992 raw transitions, 4,989
unique transitions, and all 183 authored-script kernel QEDs.

Those acceptance artifacts stay under `/tmp`. The data pipeline, corpus, and this README are
released under the repository's MIT License.
