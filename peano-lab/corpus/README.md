# Peano Lab proof-trace release v1

This directory is the deterministic M9 learning-data release. It contains **13,152** clean,
deduplicated version-1 tactic transitions from **1,596** generated proof sessions:

| Artifact | Role | Records | SHA-256 |
|---|---|---:|---|
| `train.jsonl` | learning split | 12,540 | `6f7aaf54c08a54d7c057052532e24e5977990943ac4b255a145841d7ab419dca` |
| `val.jsonl` | exact-theorem-group validation split | 612 | `306dcb76e82a04281806bebbff697db5a2a19cbdf58ecf69c0b0b77baacccc49` |
| `stats.json` | split, deduplication, outcome, and tactic statistics | — | `a4111bcb8a9df3564e277f01909c19966ba94e15281ff141ef7c13023c309673` |
| `generation-manifest.json` | configuration, source fingerprints, and per-session provenance | — | `9b1f24322586b4bc4f69428460d65f6b413041038bbe5efc2cafad019e52f302` |

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
`c7a13059f6666410e3e79d8748cee6ea1a871c7bd39e61e67b9c9193a567e5fe`.
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
