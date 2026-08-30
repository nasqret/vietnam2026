# G091: constructive polynomial-division prerequisites

Local research continuation from `1b60b19310068a27a719d857315ca09c803c3bed`.
The current sealed editions remain Alpha v31 (3,796 theorems) and Stable
(432 theorems). The separate, checked G009 research tranche has 90 theorems.
This work does not change either edition or any existing release artifact.

## Scope and mathematical order

G091 (finite fields of every prime-power order) is the first open numbered
goal in the lowest unfinished layer. Its existing prime-field arithmetic,
canonical coefficient tables, modular Horner executions, actual convolution,
and nonzero-leading represented degree are inherited prerequisites.

This checkpoint develops the next concrete operations:

1. Aligned coefficient negation and subtraction, using actual field-operation
   graphs and constructively encoded output tables.
2. Leading-zero trimming, with an actual suffix code, a uniquely determined
   removed prefix, and a nonempty represented-degree bridge.
3. Monic normalization, using an actual inverse of the nonzero leading
   coefficient and the existing scalar-multiplication graph.
4. Synthetic division by `X-a`, extracting an actual quotient coefficient
   table from a modular Horner trace and proving its coefficient recurrence,
   remainder, value uniqueness, and degree drop.

All coefficient lists keep the established **highest-degree-first** order.
Lengths are part of polynomial representations. Leading zeros are allowed
until explicitly trimmed. Uniqueness means equality of decoded coefficients,
never equality of raw beta-code numbers. Synthetic division initially takes
a nonempty input of length `S n`; constants have an empty quotient. The
existing zero-length Horner theorem handles the empty representation.

## Exact contract discipline

The operation relations describe actual beta entries, field operations,
or existing executions. Algebraic conclusions are proved, not stored as
premises in a newly named relation. Public relation builders retain the
existing full-context binder hygiene and conservative HA expansion.

The new definitions form an additive typed DAG over the current registry.
Proof-dependency, theorem-uses-definition, and definition-expansion edges
remain distinct. The constructive-proof-explorer skill governs the local
reader, using the unchanged Quadratic Reciprocity model and assets.

## Verification and release boundaries

- Replay real candidate bodies and reject altered contracts/dependencies.
- Compare exact formula DAGs against all 3,796 Alpha predecessors, the 90
  existing G009 research statements, and this tranche itself.
- Build a dependency-closed ordinary-HA bundle from authenticated inherited
  proof data; independently check the same bytes with the pinned compiled
  Lean verifier and replay the selected complete ordinary certificates.
- Keep the existing 170/175-second CPU, 180-second wall, and 1,536-MiB memory
  gates; schedule large proof jobs serially. Do not modify kernel, compiler,
  old proof sources, caches, or resource limits to obtain acceptance.
- Build and test an additive local canonical reader only after evidence is
  available. No Alpha admission, commits, push, remote deployment, public
  worker restart, or hosting changes are included in this continuation.

## Remaining G091 work

This checkpoint does **not** close G091. General polynomial Euclidean division
by an arbitrary nonzero divisor, polynomial gcd/Bezout, constructive
irreducible-polynomial existence in every positive degree, quotient-field
construction, and its exact `p^k` cardinality remain separately accountable.
A synthetic-division execution or a prime-field substrate alone must not be
reported as a proof of those endpoints.

## Completion record

The mathematical checkpoint is complete: **85 new theorems**, supported by
207 inherited Alpha-v31 theorems. The complete bundle has 293 nodes including
its packaging root, 740 dependency edges, and 17,412 body-node occurrences.
Exact formula-DAG novelty passed against all 3,886 earlier Alpha/research
statements and the new tranche itself.

Artifact:
`research/arithmetic-library/artifacts/prime-field-polynomial-division-prerequisites-proof-bundle-v1.json`
(1,060,637 bytes; SHA-256
`fec8cf768ef2b94430d58d947daa0affada315bbc5160a03991dc4d2550dd0e9`).
Ordered new specification SHA-256:
`93663cc10d2d034fb933a60a914f1656fd0beb8d715bbbab8d8e1359c780ab11`.

All eight fresh verification workers passed: exact novelty, complete original
HA plus the pinned compiled Lean verifier on the same bundle bytes, and six
ordinary empty-context principal certificates. Their certificate sizes are:

| Principal | Ordinary HA nodes |
| --- | ---: |
| Coefficient subtraction exists | 8,402 |
| Trimming exists, with extensional uniqueness | 8,892 |
| Monic normalization exists, with extensional uniqueness | 11,187 |
| Synthetic division exists, with extensional uniqueness | 11,120 |
| Synthetic quotient represented degree | 12,385 |
| Zero synthetic remainder iff actual evaluation is zero | 8,975 |

The first final verification peaked at 1,247,805,440 bytes. Authoring peaked
at 1,597,997,056 bytes, below the unchanged 1,610,612,736-byte gate. An initial
attempt to recheck all 39 historical providers hit the original CPU limit
and wrote nothing. The successful authoring run explicitly selected the
polynomial, prime-field, v21, v27, v29 and v26 bundles; every selected bundle
was checked in full. No kernel, compiler, cache, or limit was changed.

Focused mathematical suites passed 372 subtraction, 362 trimming, 421 monic,
and 288 synthetic-division cases (1,443 distinct cases). Conservative
definition tests passed 140 cases: exactly seven new identities ND0327–333,
390 total definitions, and 844 expansion edges. Checkpoint boundary tests
passed 168 cases. These tests supplement, rather than replace, the actual
dependency-closed proof checks.

The combined 1,443-case mathematical run passed in 81.007 seconds at
370,835,456 bytes peak RSS. The combined 429-case definition, checkpoint and
atlas suite passed in 27.012 seconds at 173,588,480 bytes peak RSS. Both kept
the original per-process resource gates.

Local packaging and regression maintenance:

- The four new source modules were added by the existing inventory generator.
  The new local browser manifest selects `a-d33dd94cc45d`, BUILD
  `2026-08-30b`; all 20 browser-shell tests pass. Runtime logic, admitted proof
  providers, immutable old releases, deployed selectors and the running
  public Lean worker are unchanged.
- Three historical grand-campaign assertions expected v28 despite the HEAD
  readers already using v30. They now authenticate the actual v30 catalog
  while retaining the exact v23 first-admission/proof checks. All 66 cases
  pass. All 129 historical definition-DAG tests and 28 existing public-site
  tests also pass.
- The previous G009 reader's full source binding remains exactly
  `74fb4adc5f899346a86d4791ae19675fd9adf4bdf193bcf09d84915ae6856b76`.

The canonical reader and additive campaign atlas are complete at
`book/_static/constructive-polynomial-division-explorer/`. The final build
repeated all eight fresh proof workers, passed all **351 mandatory same-live
reader tests** in 12.28 seconds, and only then installed 226 files
(12,295,466 bytes). All five canonical CSS/JS assets are reused unchanged.
The family has 85 exact and definition-aware theorem pages, 28 relevant
definition pages, typed mixed graphs, and links to the additive global atlas.
G091 remains open; all earlier goal statuses and G009 research evidence are
preserved. The seven new conservative definitions extend the reviewed global
registry to 390 definitions and 844 definition-expansion edges.

Reader identities:

- Manifest SHA-256:
  `754c4b665f568fc21ce8f810bda24430199f572a4c3f1edd9e08e633d43b6afe`
  (41,433 bytes; authenticates all 225 other files).
- Bound rendering inputs SHA-256:
  `71cb6c71a1b0d4c86993be08121f39965a4dc84b7f66080977fa6fd9e86c56ee`.
- Checkpoint digest:
  `02aaa68b0af58f2373414908119d171e5890ef9b6926231df07109fab6e49c86`.
- Navigation revision: `6c9ebfb3c37e`, the sealed Alpha-v31 catalog prefix.

The final pre-commit build took 288.521 seconds across serial bounded workers.
Worker and controller peak RSS were 1,224,982,528 bytes; rendering peaked at
298,532,864 bytes. Every worker remained inside the unchanged resource gates.
The byte-map, source binding and original live report are checked again after
the reader tests, before installation. Stored presentation receipts are not
accepted as proof authority.

Across the mathematical, definition, checkpoint, atlas, reader, browser-shell
and relevant historical regression suites, **2,466 distinct tests passed**.
No Alpha or Stable admission, commit, push, staging, remote deployment, public
worker restart, or hosting change was performed during the research checkpoint.
The subsequent authorized release starts by removing two extra EOF blank lines
from the check/export launchers and repeating all eight fresh proof jobs and
351 same-live reader tests. The identities and timings above identify that
pre-commit rebuild; mathematical sources and the proof bundle are unchanged.

## Reproduction commands

From the repository root, with the existing pinned native Lean verifier:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONMALLOC=pymalloc PYTHONPATH=scripts:peano-lab/py python3 scripts/check_constructive_polynomial_division.py
PYTHONDONTWRITEBYTECODE=1 PYTHONMALLOC=pymalloc PYTHONPATH=scripts:peano-lab/py python3 scripts/build_constructive_polynomial_division_explorer.py --check
```

The reader command without `--check` creates a new local tree only when its
destination is absent. It always runs fresh proof workers and every mandatory
same-live reader test; there is no render-only, saved-report, or test-skipping
mode. `--check` repeats the real checks and compares the existing local tree
without overwriting it. Neither command promotes or deploys anything.
