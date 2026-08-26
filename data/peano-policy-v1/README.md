# Peano policy v1 — first attested synthetic release

This directory is the first training-scale M19 artifact.  It was generated on
2026-07-28 by the proof-first schema driver, not by accepting arbitrary model
text.  Every source session ran through `peano_lab.batch.run_proof`, produced an
ordinary Peano Lab certificate, and reached QED only after the independent
kernel checked the original theorem.

Exact release counts:

- 2,522 independently checked proof sessions and roots;
- 2,522 unique canonical statements;
- exactly 10,000 positive next-tactic transitions;
- 8,149 train, 926 validation, and 925 test rows;
- 29 schemas in five domains: logic, equality, PA recurrence, witnesses, and
  arithmetic closers; and
- zero frozen held-out target occurrences in the attestation scan.

`raw-traces.jsonl` is the unchanged binding version-1 trace stream.
`session-metadata.jsonl` contains the root genealogy and fixed capability
preimage. `source-manifest.json` binds generation sources and counts.
`manifest.json` binds the replay-compiled splits. `attestation.json` records a
second, independent rebuild from the raw sessions; all three split files were
byte-identical after replay under the current public surface and kernel.
Split components join declared genealogy, identical canonical theorem formulas,
and identical exact policy prompts, so neither duplicate statements nor duplicate
model inputs can leak across train, validation, and test through inconsistent
metadata.  The attestor independently rejects both formula and prompt overlap
and binds the complete attestor source tree that training will execute.

The fixed intuitionistic `model-v1` environment has SHA-256
`ea753147079f48c14e9bd197051264a1ab29868a0bac84bd13c420baf1b63e1f`.
The combined split digest is
`1fa98caa2e0528d39c1b9003c4ee153dfbe633cb1ee4505e8f5b28eb837465dd`.
The per-file hashes, complete capability preimage, source inventory, runtime,
schema/tactic distributions, and proof-node total are in the manifests rather
than duplicated here.

Reproduce from the repository root:

```console
make peano-policy-data PEANO_POLICY_ROWS=10000
```

The release is a pipeline and supervised-policy baseline, not a claim of broad
PA coverage.  It currently has no induction/invariant schemas, no natural-
language formalization pairs, no negative preference rows, and no hard
whole-template OOD benchmark.  Those limitations are deliberate manifest data
and next-stage work, not hidden extrapolations from 10,000 rows.
