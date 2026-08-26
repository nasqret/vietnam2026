# HA-FRONTIER-PROMOTION-1 — bounded Lucas and Lagrange closure planning

Status: executable dependency-slice planning and actual bounded
empty-context-certificate construction. No Alpha or Stable edition is changed;
no theorem is promoted or granted checked-use authority by this tranche.

Immutable parent: Alpha v13, ordered-enrollment identity
`6b223edfe6a2e02dc09576671f4fc5f5a41aaf4156f829164222dd3e494da22f`, edition
identity `a010e0ee5dece0d3325e8ec084c1f8769ef8e9ca47e2de891d344e54c1b439d1`,
1,543 enrolled specifications, 570 checked-use entries, and the unchanged
432-row Stable edition.

Implementation:
[`frontier_promotion.py`](../../peano-lab/py/peano_lab/library/frontier_promotion.py).
Focused executable audit:
[`test_frontier_promotion.py`](../../peano-lab/py/tests/test_frontier_promotion.py).

## Exact dependency-closed promotion slices

| Root selection | Total specifications | Stable-closed | Alpha-closed | Parent body-only | v13 body-only | Total needing closure | Edges |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `lucas_theorem` | 213 | 138 | 1 | 30 | 44 | 74 | 617 |
| `four_square_lagrange` | 390 | 166 | 5 | 23 | 196 | 219 | 1,187 |
| Both roots | 481 | 183 | 5 | 53 | 240 | 293 | 1,537 |

The 30 Lucas and 23 Lagrange unchecked parent prerequisites are disjoint.
Neither slice includes the pending quadratic-reciprocity capstone or the known
oversized valuation-existence theorems. Planning preserves exact sealed
statements, hashes, source release, original enrollment origin, dependencies,
and Alpha-v13 order. Pending-layered, unknown, cyclic, reordered, or mutated
inputs fail closed.

Pinned exact-surface SHA-256 receipts:

```text
Lucas:    21232d244a2d416f2ee1465d55e5d2a025b86fb61778f6316785ca917d7a7728
Lagrange: 8a92bf2d6fd4c716112d1a84994725589f696c6289e6a33d1729ea33235759d5
Union:    c780df8c7855c09f5f2db6f0fe43a3deef80a6b527934c0ed29f6825fae8e92a
```

## Immutable kernel and resource boundaries

Every proof constructor uses the existing first-order arithmetic statement,
unchanged tactic script, existing intuitionistic proof grammar, and unchanged
independent kernel. A dependency-curried body, receipt, source digest,
matching theorem name, or claimed hash is never accepted in place of an
actual empty-context `Proof` object. Classical `DNE` is rejected explicitly.

Hard workstation limits are never relaxed:

```text
at most 16 newly constructed proof bodies per microbatch
at most 125,000 aggregate structural proof nodes
at most 25,000 aggregate retained proof objects
existing kernel proof-depth, annotation, and envelope limits unchanged
```

Already checked Stable/Alpha dependencies are obtained through their existing
checked-use release boundary. Every body-only direct dependency must be
provided as an actual independently checked closed certificate. Oversized
direct-premise sums are rejected *before* attempting to replay or materialize
the dependent proof.

An optional shared-layer constructor replays selected proof bodies as ordinary
dependency-curried implications and invokes the existing, unchanged
`layered_replay` compiler. Its output must still be an ordinary first-order
`Cut` certificate accepted from the empty context under the same 125,000-node
and 25,000-object limits. Sharing is an optimization, never a new proof rule
or an evidence transition. A separate subprocess CLI provides genuine cold
kernel replay; its returned metrics are diagnostics, not checked authority.

## Actual independently checked initial certificates

One bounded Lucas parent microbatch proves:

```text
le_mul_of_one_le_right             141 nodes
prime_two_le                       125 nodes
succ_le_mul_of_two_le_right        316 nodes
choose_out_of_range_zero            95 nodes
choose_upper_eq_transport           52 nodes
factorial_length_eq_transport       26 nodes
factorial_weighted_product_combine 382 nodes
total                            1,137 nodes; 993 proof objects
```

A separate bounded Lagrange parent microbatch proves:

```text
bounded_nonzero_not_divides       140 nodes
pair_order_double_succ_length      46 nodes
odd_half_strictly_below_modulus   315 nodes
even_to_mod_two_zero               55 nodes
odd_to_mod_two_one                115 nodes
mul_le_mul                        521 nodes
two_mul_eq_add_self               275 nodes
square_lt_successor_square        592 nodes
mul_le_cancel_left_nonzero        679 nodes
```

Additional individual Lucas certificates close all 16 initially ready parent
dependencies and the existence/uniqueness/recurrence chains. Representative
independently checked empty-context sizes are:

```text
beta_pascal_zero_row_extend       29,310 nodes
beta_pascal_zero_row_exists       29,361 nodes
beta_pascal_row_step_extend       29,808 nodes
beta_pascal_row_step_exists       29,863 nodes
beta_pascal_table_prefix_extend   88,848 nodes
beta_pascal_table_prefix_exists   88,909 nodes
choose_exists                     89,492 nodes
choose_functional                  4,535 nodes
choose_succ_succ                   8,602 nodes
choose_weighted_vertical         102,493 nodes; 8,429 objects
```

Thus **29 of the 30 old Lucas dependencies have actual individually checked
closed candidates**, including the shared-layer factorial bridge below. These
are reproducible certificate constructions, not a
versioned release or changed Alpha-v13 evidence.

## Exact remaining ordinary-Cut obstruction

The sealed `choose_factorial_bridge` row separately depends on both
`choose_exists` and `choose_weighted_vertical`, even though the latter
already uses `choose_exists`. Its five body-only direct prerequisites require:

```text
choose_exists                      89,492 nodes
choose_weighted_vertical          102,493 nodes
choose_self_of_eq                   2,236 nodes
factorial_length_eq_transport          26 nodes
factorial_weighted_product_combine    382 nodes
minimum                           194,629 nodes
```

Therefore ordinary independently closed direct-premise cuts exceed the
immutable **125,000** structural-node cap by at least **69,629 nodes before
the bridge body or its Stable-closed premises are counted**. The constructor
rejects this before materialization.

The new shared-layer constructor avoids the duplicated `choose_exists` proof:
it packages that closed premise **once**, replays the unchanged
`choose_weighted_vertical` and `choose_factorial_bridge` scripts as two
dependency-curried local proof bodies, and composes them with ordinary
existing layered `Cut` constructors. The unchanged intuitionistic kernel then
independently verifies the exact sealed bridge statement from the empty
context with the genuine observed envelope:

```text
choose_factorial_bridge
  structural proof nodes 109,841
  retained proof objects   9,535
  proof depth                104
```

This is strictly below the unchanged **125,000-node / 25,000-object** caps;
neither the theorem statement nor its declared dependencies are changed.
`choose_prime_divides_between` remains the one currently unresolved Lucas
parent body. The strongest attempted package inlines the maximum **sixteen**
allowed proof bodies, including the complete Choose functionality/recurrence
chain, both factorial-prime lemmas, the weighted identity, the factorial
bridge, and the final target. This leaves only three unchecked external proof
objects:

```text
choose_exists                       89,492 nodes
factorial_length_eq_transport           26 nodes
factorial_weighted_product_combine     382 nodes
unchecked leaf total                89,900 nodes
```

However the unchanged exact proof bodies also require **29 distinct already
Stable-closed leaf theorems**. Their sealed existing empty-context certificates
contain **76,923** structural nodes in total, dominated by the existing Stable
`factorial_exists` certificate at **59,841** nodes. Thus the maximal permitted
shared package has the independently audited pre-compilation lower bound:

```text
29 exact Stable-closed leaves       76,923 nodes
3 exact body-only closed leaves     89,900 nodes
minimum external leaf budget       166,823 nodes
unchanged hard limit               125,000 nodes
unavoidable measured excess         41,823 nodes
```

Indeed `factorial_exists` and `choose_exists` alone contain **149,333**
structural nodes, exceeding the hard cap by **24,333** before any other leaf
or selected proof body. The 16-row constructor rejects this deterministically
*before* building the oversized candidate. The sealed Stable factorial proof
itself depends on `beta_range_exists` (29,328 nodes) and
`beta_product_exists` (30,487 nodes), so naively inlining only that proof does
not remove the duplication. Any future workaround requires a genuinely
smaller independently checked exact proof, deeper shared treatment of both
factorial and Choose-prefix ancestry, or a separately approved execution
environment; it must never silently widen either resource cap or change a
sealed theorem surface. Until such a certificate exists, the sole final
parent remains body-only and the complete Lucas root has no checked use.

## Future release gates

1. Recompute the exact sealed Alpha-v13 slice and immutable source provenance.
2. Construct every required missing empty-context certificate in actual
   dependency order, respecting all hard workstation limits.
3. Reject false statements, altered dependencies/scripts, fake certificates,
   classical `DNE`, changed resource caps, and forged cold-replay receipts.
4. Independently kernel-check every selected closed certificate and repeat the
   accepted campaign in a fresh process.
5. Introduce an explicitly reviewed, separately versioned evidence transition
   only after all certificates exist; preserve existing Alpha and Stable bytes.
6. Regenerate catalogs, evidence receipts, channels, and proof explorers from
   the accepted new release facts. Stable promotion remains a separate decision.
