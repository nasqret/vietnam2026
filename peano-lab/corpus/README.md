# Peano Lab proof-trace release v1

This directory is the deterministic learning-data release whose provenance follows the checked
theorem catalog. Its semantic families remain the M13 set, while the theorem ladder has grown
into the final 247-theorem M20 source tree. It has its own fresh fingerprints rather than reusing
either parent branch's hashes. The release contains
**13,344** clean, deduplicated version-1 tactic transitions from **1,692** generated proof
sessions:

| Artifact | Role | Records | SHA-256 |
|---|---|---:|---|
| `train.jsonl` | learning split | 13,326 | `44794fa75477cc3f8a4271f19a79f632e02f5fbca1f243173c2ceca9ab8762ca` |
| `val.jsonl` | exact-theorem-group validation split | 18 | `ddf0b14e44f89afff34775f5002ae79c6867ec6438e5024430534430dd471f68` |
| `stats.json` | split, deduplication, outcome, and tactic statistics | — | `538a437ab23e9305bf3f822cf3433947929e415ef0df73241cc129462918d221` |
| `generation-manifest.json` | configuration, source fingerprints, and per-session provenance | — | `327f734431e4b5c74c2d59b8df438aeba20a5622dc3a37cc9311a8101967a0d8` |

The deterministic run fingerprint is
`5b41aae76a1980c768fdf815f1ffc531fa86ebcdecf9bfae39de2dceb608f81c`.
The complete 32-file semantic source-tree fingerprint is
`eee28177d1fce902330fabb721a22fef8b3cfa69963c8e12c92fd1d6ace10b5d`.

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
`fc696f3d94136a8c414c54d411e4f8a6c94f7e0ac78785cddb7798005525749d`.
It also fingerprints `scripts/generate_peano_traces.py`, the trusted checker, and the complete
Peano Lab Python source tree. Because the Python runtime participates in the run fingerprint and
session IDs, changing that runtime changes the raw byte hash even when every session-agnostic
semantic transition remains the same.

To exercise one-node/depth-one bounded `auto` plumbing attempts and checked authored replays for
every entry in the resolved ladder without contaminating the release, run:

```console
make peano-corpus-smoke
```

The current 247-entry smoke has 494 sessions, 9,235 raw transitions, 9,232
unique transitions, and all 247 authored-script kernel QEDs. Its deterministic run fingerprint
is `72657457dfa567d0748d5275a227e5316271bd19350012a44e6e4802851e59ef`;
the 97,730,404-byte raw stream hashes to
`95c6681c6bee84f080905acccbc4fb9774fdfb60347630f74265ef470ab418dc`.
After removing three semantic duplicates, the temporary acceptance export contains 8,154 train
rows in 444 sessions (`a351be8db2965454353f38de888f60b6f3435ad9862bd1aef81a0921b6e27fc3`)
and 1,078 validation rows in 50 sessions
(`aa710a97576e532db251f4682b1909ab84d34c4e25c26759be720289656ae010`).
The temporary generation manifest and export statistics hash to
`e5f1e1514f4b1f2505069f176a7a24474fcbce47a53811f4fd0009c403c5d813` and
`f095277577cd8392a2e610057046bf3ea3de6c63dfab54a8608c78bd1211ce79`,
respectively.

Those acceptance artifacts stay under `/tmp`. The data pipeline, corpus, and this README are
released under the repository's MIT License.
