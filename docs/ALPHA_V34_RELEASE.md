# Alpha v34: polynomial gcd and elementary congruences

Alpha v34 is locally promoted: all 22 fresh proof jobs and all six publication
phases (171 mandatory UI cases) passed on 2026-09-02. The six reader/atlas trees
are installed, and the six previously created catalogue files were rechecked
byte-for-byte without replacement. Remote deployment remains pending.
This page describes the procedure; it is not itself proof authority. See the
[actual publisher observations](../research/arithmetic-library/working/alpha-v34-release-v1/live-release-attempt-2-observations-v1.json).

Runtime and provider/helper verification is also complete: 2,063 distinct
cases passed, including the 12 checks against the actually installed readers.
See the [installed-service observations](../research/arithmetic-library/working/alpha-v34-release-v1/installed-service-observations-v1.json).

## Exact mathematical scope

The additive release contains 131 new theorem entries: all 119 rows of the
completed polynomial gcd/Bézout checkpoint and 12 elementary congruence rows.
The accepted release has 4,223 checked-use Alpha entries, retaining all 4,092
v33 entries and their first-admission evidence. Stable remains the identical
432-entry default. The theorem DAG has 13,816 edges and 53 layers.

The polynomial chapter covers shift/scalar laws, convolution associativity,
length-aligned operations, Euclidean backward transport, normalization,
recursive gcd/Bézout existence, greatestness and normalized uniqueness.
Uniqueness means formal coefficient equivalence, not equality of beta codes
or uniqueness of Bézout coefficients. Zero inputs, leading zeros and
characteristic two are included in the proved contracts.

The congruence chapter adds gcd-reduced cancellation, the full noncoprime
solution class, a canonical representative below the reduced modulus, and an
explicit bijection between the interval below the gcd and the bounded
solutions. The finite count requires a nonzero modulus. Separate theorems
handle modulus zero and one; the all-input Fermat endpoint is also included.
See the [coverage audit](../research/arithmetic-library/alpha-v34-readiness-audit-v1.md)
for the previously admitted equivalence, operation, cancellation, residue,
inverse, solvability, CRT, Euler, Fermat and forward-Wilson theorems.

The existing atlas has no open goal in DAG layers 0–5. This does not close all
of the first two thematic families. Jordan totient G008, the additional F02
contracts G015–G020 and prime-power field construction G091 remain open.
Polynomial gcd/Bézout completes a prerequisite of G091, not G091 itself.

## Capacity and verification

Only the new versioned logical catalogue capacity changes, from 4,096 to
8,192 entries. Historical codecs retain their original bound. Transport is
still exactly three authenticated ordinary files: the v34 manifest, the
literal v30 base and one cumulative 1,001-row delta. The 870 inherited delta
rows are unchanged. All original per-file, JSON, dependency, kernel, compiler,
certificate, worker-message, CPU, wall-time and memory limits remain in force.

```sh
make alpha-v34-release
make alpha-v34-release-check
make stage-proofs-v34 PEANO_DELIVERY_PYTHON=python3.11
```

The release and check commands each require 22 fresh proof jobs: exact-AST
novelty against the complete parent, two complete original-HA and same-byte
compiled-Lean bundle checks, and 19 ordinary principal certificate replays.
Each heavy window retains CPU 170/175 seconds, wall time 180 seconds and
1,536 MiB peak RSS. Run heavy windows sequentially, never concurrently.

The delivery-only interpreter override is explicit: on this host `python3`
selects CPython 3.10, while the already-installed CPython 3.11.12 completed
the unchanged single-window stager in 164.79 seconds at 982,761,472 bytes
peak RSS. All 141 staging/hub regression cases passed under that interpreter.
The default remains `python3`; no proof, backend or historical recipe changes
interpreter. Two earlier delivery attempts reached the original wall limit
and remain recorded as failures, not accepted stages. See the
[successful staging observations](../research/arithmetic-library/working/alpha-v34-release-v1/delivery-stage-attempt-3-observations-v1.json).

Six subsequent publication phases share the genuine live verification
capability and must pass all 171 declared UI tests. Stored receipts and
private display fixtures cannot create that capability. The six catalogue
outputs are exclusive; all six reader/atlas trees are installed only after
every publication phase succeeds. If a UI phase fails after a checked
catalogue is created, fix the UI source and rerun the fresh publisher without
`--create-release` to check the existing catalogue and install missing readers.
Never overwrite an immutable release to hide a mismatch.

## Proof maps and delivery

The canonical Quadratic Reciprocity design is retained. The combined atlas
keeps 144 milestone vertices and 120 major goals, with 407 conservative
definitions and 884 definition-expansion edges. Definition edges remain
distinct from proof prerequisites. Ten new definitions, ND0341–ND0350,
connect the polynomial chapter to the existing shared definition DAG.

The five reader packages contain 68 family entrances:

- `constructive-gcd-congruence-explorer-v34`: the two new families.
- `constructive-polynomial-euclidean-explorer-v34`: the v33 division family.
- `constructive-research-explorer-v34`: two v32 families.
- `constructive-completed-lower-explorer-v34`: nineteen v31 families.
- `constructive-historical-explorers-v34`: forty-four established families.

The sixth tree, `constructive-research-campaign-v34`, supplies the combined
atlas. All first-admission versions, historical aliases, source trees and
proof bundles remain unchanged; a new display version does not grant
admission to an old alias.

Register exact delivery pins only after the live publication succeeds. The
new stage is `_deploy/proofs-v34`; the validated v33 stage is retained.
Inspect the owned faculty destinations, retain rollback entrypoints, upload
additively, compare remote hashes and activate the hub last. The intended
destinations are the existing `proofs/` and `peano-lab-next/` directories.
Peano production remains a separate protected promotion: do not waive its
cache-header gate or change hosting configuration as part of this release.

The current browser/Lean selectors may move to v34 only with the matching
module and proof-artifact inventory. A present but malformed v34 catalogue
must fail closed; it must not silently select v33. No Hydra training corpus,
training run or historical model authority is changed by this release.
