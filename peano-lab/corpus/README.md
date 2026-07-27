# Peano Lab proof-trace release v1 (M15 provenance refresh)

This directory is the deterministic learning-data release whose provenance was refreshed for M15
after the proof-owner API changed. Its semantic families remain the M13 set. It contains
**13,344** clean, deduplicated version-1 tactic transitions from **1,692** generated proof
sessions:

| Artifact | Role | Records | SHA-256 |
|---|---|---:|---|
| `train.jsonl` | learning split | 13,326 | `2ffcb61bde1debf1c3b12ac69e7fafa419340f6818bebc5a5155c3501d5b950a` |
| `val.jsonl` | exact-theorem-group validation split | 18 | `c6f0ca5e3c31a559e4a7f886f06cdf291c0267e566c6fdd8236e458df4cd244b` |
| `stats.json` | split, deduplication, outcome, and tactic statistics | — | `7bdd211de0f2f618c10d329fb9331fe1a9dd2e19f04aea59ad040721bb740991` |
| `generation-manifest.json` | configuration, source fingerprints, and per-session provenance | — | `47fe87023e9c7e7a56402aba4e76a7f7cf549fa32948fbbd981f3c7d690777b2` |

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
`18172333190fbdf56438bc5eb4973a3ba7daa491d515c4c54346441a49defe2e`.
It also fingerprints `scripts/generate_peano_traces.py`, the trusted checker, and the complete
Peano Lab Python source tree. Because the Python runtime participates in the run fingerprint and
session IDs, changing that runtime changes the raw byte hash even when every session-agnostic
semantic transition remains the same.

To exercise honest bounded `auto` attempts and checked authored replays for all twenty-three ladder
entries without contaminating the release, run:

```console
make peano-corpus-smoke
```

Those acceptance artifacts stay under `/tmp`. The data pipeline, corpus, and this README are
released under the repository's MIT License.
