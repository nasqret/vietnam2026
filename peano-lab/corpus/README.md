# Peano Lab proof-trace release v1 (M19 provenance refresh)

This directory is the deterministic learning-data release whose provenance was refreshed for M19
after the compact headless adapter extended and hardened the untrusted tactic surface. Its semantic
families remain the M13 set. It contains
**13,344** clean, deduplicated version-1 tactic transitions from **1,692** generated proof
sessions:

| Artifact | Role | Records | SHA-256 |
|---|---|---:|---|
| `train.jsonl` | learning split | 13,326 | `89e199b7a1c40a5c2ef15a2ef5224b3e19381ffa310b9bd67fec2ef320be52d2` |
| `val.jsonl` | exact-theorem-group validation split | 18 | `61b758a7db5711ca5fc73a27352177f8047d18fb7f6fb603c12a25c99d17a274` |
| `stats.json` | split, deduplication, outcome, and tactic statistics | — | `bb216ae7765909730d8942188ceda9233652096911691ea8f2061d5316b21860` |
| `generation-manifest.json` | configuration, source fingerprints, and per-session provenance | — | `82715b85e464fdcd0e7fb1eaed7c55297fea5693a6d7b3fc30f292cbb852b5f0` |

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

The byte-identical release above used generator v2 and CPython 3.10.0, recorded in the manifest;
transition and manifest schemas remain v1. The Make target checks this and accepts
`PEANO_CORPUS_PYTHON=/path/to/python3.10`
when that interpreter is not the ambient `python3`.

That target first writes the replayable raw session stream to
`/tmp/peano-lab-release-raw.jsonl`, then strictly validates, globally deduplicates, and exports it.
The raw intermediate is not committed because it duplicates the split payload, but the manifest
records its exact size (`6,215,711` UTF-8 bytes) and SHA-256
`d3f863f670d40c2a48a2f74a5b72a76b8d6ef37852b83d1ab69b32a81ff2731d`.
It also fingerprints `scripts/generate_peano_traces.py`, the trusted checker, and the complete
Peano Lab Python source tree. Because the Python runtime participates in the run fingerprint and
session IDs, changing that runtime changes the raw byte hash even when every session-agnostic
semantic transition remains the same.

To exercise one-node/depth-one `auto` plumbing attempts and checked authored replays for all 49
ladder entries without contaminating the release, run:

```console
make peano-corpus-smoke
```

Those acceptance artifacts stay under `/tmp`. The data pipeline, corpus, and this README are
released under the repository's MIT License.
