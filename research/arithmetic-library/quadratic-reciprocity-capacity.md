# Quadratic-reciprocity certificate capacity

## Decision

The campaign uses a dual live-certificate budget:

| resource | bound |
|---|---:|
| structural proof occurrences | 500,000 |
| distinct in-memory proof objects | 100,000 |
| proof depth | 256 |

The structural ceiling is deliberately larger than the object ceiling. A
certificate assembled from immutable, shared dependency objects can mention
the same object through several `Cut` branches. The historical tree metric
charges every occurrence. The object metric charges each reachable Python
proof object once. Both checks are untrusted availability policy; neither
changes what the independent kernel accepts.

This replaces the earlier single 100,000-occurrence gate. It does **not**
increase the worst-case number of distinct proof objects admitted to a live
session, and it leaves the depth boundary unchanged. Exact-boundary and
one-past-boundary tests cover all three dimensions transactionally.

The complete genuine quadratic-reciprocity root has since passed all three
unchanged proof-envelope limits: **54,870 structural proof occurrences,
35,052 distinct proof objects, and depth 129**. Its measured complete replay
peaked at **843,087,872 bytes** under the explicit 1,536 MiB workstation guard.
The separate canonical Lean-verified proof DAG contains all 557 real bodies and
1,787 dependency edges. Earlier scaffold figures below remain useful
historical capacity predictions, not substitutes for this actual
[independently checked closure receipt](quadratic-reciprocity-closure-receipt.md).

## Reproducible evidence

Run:

```console
python3 scripts/profile_peano_certificate_capacity.py \
  fundamental_theorem_of_arithmetic
```

On the 247-theorem pre-campaign snapshot, the checked FTA endpoint measured:

| metric | value |
|---|---:|
| structural occurrences | 73,767 |
| structural depth | 99 |
| distinct proof objects | 8,701 |
| proof-object edges | 9,077 |
| reused object references | 377 |
| structural/distinct ratio | 8.478 |
| cold replay and check | 51.358 seconds |
| process maximum RSS on the measured macOS run | 121,569,280 bytes |

The wall time and RSS are machine observations, not release invariants. The
certificate metrics are deterministic for the pinned theorem source. The
profiler checks the theorem through ordinary library replay and has no theorem
authority of its own.

## Expanded-source ceiling

The interactive source-line limit is 8,192 characters in the Python driver,
proof UI, batch importer and browser paste validator. It was raised from
4,000 only after the checked `pow_successor_pair_mul` and
`pow_mod_congruent` contracts measured 5,706 and 4,274 characters. Their
certificates are modest—the latter has 10,671 structural occurrences, 1,748
distinct objects and depth 68—so this was a serialization constraint, not a
proof-resource constraint. Exact-boundary and one-past-boundary tests keep the
Python and browser values synchronized.

The subsequent `pow_add` and `pow_mul_exp` contracts measure 7,131 and 7,127
characters, validating the chosen headroom without another increase.
`pow_mul_exp` is independently substantial as a certificate—70,463
occurrences, 5,786 objects, depth 91—but remains comfortably inside the
separate proof budgets.

## Sharing through interactive QED

The resource policy is useful only if finalization preserves the immutable
sharing it measures. An audit composed two references to the same checked FTA
certificate. Before normalization the conjunction had 147,539 structural
occurrences, depth 101, and 8,704 distinct proof objects. The former recursive
normalizer rebuilt a fresh copy along many incoming edges, producing 109,150
distinct objects and incorrectly rejecting the otherwise shared certificate.

Proof substitution and cut normalization now memoize by input object identity
for each invocation, retaining strong references during the pass. The same
end-to-end interactive finalization yields 139,203 structural occurrences,
depth 99, and 8,274 distinct objects; a second finalization preserves those
8,274 objects, and the independent kernel accepts the result. Compact
regressions exercise this route under a patched 100-object ceiling, while the
real two-FTA reproducer records the campaign-scale measurement. Memoization is
an availability correction only: it neither skips normalization nor bypasses
the final kernel check.

## Why this is preferable to an unrestricted cap increase

A flat 500,000-node limit would also admit a certificate containing 500,000
distinct dataclass objects. That is not justified by the FTA evidence and
would enlarge the browser-memory attack surface. The dual gate grants headroom
only where immutable sharing is observable while preserving the previous
100,000-object ceiling.

The higher occurrence limit can still cost checker time because the current
kernel follows every incoming edge. The exact optimized QR graph makes that
cost concrete: 557 specifications and 1,787 direct edges occupy 45 layers
with root depth 44, but recursive closure produces 191,648 theorem
occurrences. The [static hotspot audit](quadratic-reciprocity-closure-hotspots.md)
charges only one body node per occurrence, the forced dependency Cuts, and
recorded leading theorem-level introductions. This already yields a rigorous
731,423-node lower bound. No WMI run can make that recursive proof tree fit
the 500,000-node structural policy.

The remedy is not another cap increase. The preferred
[layered `Cut` bundle](layered-cut-bundle.md) places every dependency-curried
body once in one of 45 balanced conjunction packages. Later uses are existing
`AndElimL`/`AndElimR` projections, and 45 existing contextual Cuts introduce
the packages. The output remains an ordinary proof checked by
`check((), certificate, QR)` with no kernel, grammar, theorem-authority, or
hash-authority change. A 20-node synthetic fixture measures 274 nodes/depth
16 in layered form versus 3,643 nodes/depth 20 under recursive expansion.

Exact-topology static checks refine the estimate without replaying real
theorems. Distinct one-node dummy bodies compile all 557 blueprint nodes to a
13,705-node/depth-56 scaffold, of which 13,148 nodes are fixed glue; the
balanced package formulas contain 144,197 structural occurrences at maximum
depth 68. The dummy proof is rejected, as required. Replacing every real
target by a unique shallow reflexive marker derived from its local-ID bits and
using curried `EqRefl` bodies preserves all 1,787 edges, dependency orders,
projections, and context indices. Each such body additionally contains one
existing Cut per direct dependency, checking that dependency's exact target
against the matching `Hyp(k-1)`. The unchanged kernel therefore checks every
real projection ID/direction and declared dependency order, accepting the
strong surrogate at 19,066 nodes/depth 74 with package-formula cost
19,297 occurrences/depth 18. These are compiler-scaffold measurements, not QR
proof or admission evidence.

Accordingly, every quadratic-reciprocity milestone records structural,
identity, formula, depth, time, and memory metrics. The campaign gates remain:

1. generic finite `Sum`/`Count` endpoints should remain below 35,000
   structural occurrences individually;
2. the Euler/Gauss package should remain below 100,000 distinct objects and
   preferably below 250,000 structural occurrences;
3. the reciprocity endpoint must remain below 500,000 occurrences, 100,000
   objects, and depth 256;
4. the final artifact must pass cold CPython replay, independent mutation
   checks, and cold Pyodide/browser replay.

If the layered artifact fails the third or fourth gate, the next architectural
step is the reviewed [self-contained proof-DAG](closed-proof-dag.md) fallback.
A trusted theorem name, external hash lookup, or unchecked cache is not an
acceptable shortcut.

## Scope

The capacity change adds no term, formula, proof rule, axiom, classical
principle, or theorem authority. It changes only preflight resource policy and
diagnostic accounting. The kernel continues to receive the entire
self-contained certificate and the original target.
