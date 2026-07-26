# Peano Lab proof-trace release v1

This directory is the deterministic M9 learning-data release. It contains **13,152** clean,
deduplicated version-1 tactic transitions from **1,596** generated proof sessions:

| Artifact | Role | Records | SHA-256 |
|---|---|---:|---|
| `train.jsonl` | learning split | 12,540 | `f63921b6d9209cdfe16517e23b57bdd633c9a256751a999f0dbb6a40ab10d4e4` |
| `val.jsonl` | exact-theorem-group validation split | 612 | `aa378bf63a2d4b16908fc6114396bf655c50b7a3699ee27b3cdad65bf5e3592d` |
| `stats.json` | split, deduplication, outcome, and tactic statistics | — | `f83a975c71f5fd4cab216870743b30faa7a5ec133a03d0982d99a8ab1369013f` |
| `generation-manifest.json` | configuration, source fingerprints, and per-session provenance | — | `35dcab429330d7586a04d0d2f637df8678b844ec6692c1615bcb99e3c36a7f8e` |

The source stream contained 11,556 successful and 1,596 deliberately failing, transactional
applications, for a labeled failure ratio of `0.12135036496350365`. Every one of the 1,596 sessions
reached QED through the production proof engine and was independently finalized against its
owner-held original theorem. The released rows themselves are transitions—not certificates—and
their `status` or manifest metadata is never proof authority.

## Leakage boundary

The release contains 1,500 seeded alpha-renamed reflexive-arithmetic conjunctions and 96 seeded
addition-commutativity variants. Both `ladder_auto` and `ladder_scripts` are disabled in the
manifest. Consequently none of the four fixed evaluation families (`le_trans`, `le_antisymm`,
`le_total`, `mul_eq_zero`) or their authored ladder scripts enters these files. The exact-theorem
split is deterministic and semantic duplicates cannot cross it; logically equivalent near
duplicates still require the family-level manifest audit described in
[`docs/PEANO_LLM.md`](../../docs/PEANO_LLM.md).

Validation is intentionally a small pipeline check, not the final research claim: its one exact
formula group is an addition-commutativity orientation related to a training group. Report model
quality only on the fixed, separately kernel-judged held-out ladder families.

## Reproduce

From the repository root, using the exact checked-out generator and kernel:

```console
make peano-corpus
```

The byte-identical release above used CPython 3.10.0, recorded in the manifest;
the Make target checks this and accepts `PEANO_CORPUS_PYTHON=/path/to/python3.10`
when that interpreter is not the ambient `python3`.

That target first writes the replayable raw session stream to
`/tmp/peano-lab-release-raw.jsonl`, then strictly validates, globally deduplicates, and exports it.
The raw intermediate is not committed because it duplicates the split payload, but the manifest
records its exact size (`6,157,395` UTF-8 bytes) and SHA-256
`61a4f2497e4e71f31fd995da118a35c2fc1f72a6597cfd4873088a6e4e21f9e3`.
It also fingerprints `scripts/generate_peano_traces.py`, the trusted checker, and the complete
Peano Lab Python source tree. Because the Python runtime participates in the run fingerprint and
session IDs, changing that runtime changes the raw byte hash even when every session-agnostic
semantic transition remains the same.

To exercise honest bounded `auto` attempts and checked authored replays for all twenty ladder
entries without contaminating the release, run:

```console
make peano-corpus-smoke
```

Those acceptance artifacts stay under `/tmp`. The data pipeline, corpus, and this README are
released under the repository's MIT License.
