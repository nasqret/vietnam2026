# Peano Lab proof-trace release v1 (M19 provenance refresh)

This directory is the deterministic learning-data release whose provenance was refreshed for M19
after the compact headless adapter extended and hardened the untrusted tactic surface. Its semantic
families remain the M13 set. It contains
**13,344** clean, deduplicated version-1 tactic transitions from **1,692** generated proof
sessions:

| Artifact | Role | Records | SHA-256 |
|---|---|---:|---|
| `train.jsonl` | learning split | 13,326 | `56ab6d0716125d6cb54a2a5dd9cb1ad1c7007d202dc4042bc50679e7ec4cf2f4` |
| `val.jsonl` | exact-theorem-group validation split | 18 | `70142bb83c03c0512ac3f4f4b25bbb678e75a79ce957b77af562daa71ae62dfb` |
| `stats.json` | split, deduplication, outcome, and tactic statistics | — | `6c52b60c159edab1d3d86a6837bfb46e99373851b1149e5a55a15a5b35836d20` |
| `generation-manifest.json` | configuration, source fingerprints, and per-session provenance | — | `8a5cf40f6d676f08a161d41cb15c05ce72c93539ba45f3505bdec6471ae6224e` |

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
`4703a96b986449352469bb91715cdb3fb9fbe5cc5e7fe14bb80c83a93952e93e`.
It also fingerprints `scripts/generate_peano_traces.py`, the trusted checker, and the complete
Peano Lab Python source tree. Because the Python runtime participates in the run fingerprint and
session IDs, changing that runtime changes the raw byte hash even when every session-agnostic
semantic transition remains the same.

To exercise one-node/depth-one `auto` plumbing attempts and checked authored replays for all 63
ladder entries without contaminating the release, run:

```console
make peano-corpus-smoke
```

That smoke covers the complete public catalog, whose ordered root is
`d0f9070a2677a03eeca8ce2d1b83bcee04df3c907ef8cec2f797ab5ef99e5db0`; it is not the narrower
model-v2 import authority. Model-v2 excludes the reverse-dependency closure of its four benchmark
goals—seven imports total—and binds the remaining 56 records under
`3ce83721f4517f2d5f2e734da1fbeae086473c4d1b8abb45d875a52769096439`.

Those acceptance artifacts stay under `/tmp`. The data pipeline, corpus, and this README are
released under the repository's MIT License.
