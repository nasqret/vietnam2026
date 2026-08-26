# HA-R6-BERTRAND-PROMOTION-1 — exact dependency-closed release slices

Status: reviewed planning and executable fail-closed preflight; no theorem
evidence has been upgraded and no Stable release has been changed.

Parent: the immutable Alpha-v12 edition with enrollment SHA-256
`f763b9fc3717ad76c7e259d67c3beeadfdaca554bbaaeb3ecd2e55329edf937b` and
edition SHA-256
`bacd84f2db14bdd20c09b1ac862348fa14bca9c440099c066fc7e1201a192061`.

Execution plan:
[`PLAN/13_constructive_number_theory_frontier.md`](../../PLAN/13_constructive_number_theory_frontier.md),
stage 1C. The binding Bertrand endpoint statements and trust boundary remain
those in `HA-R6-BERTRAND-1` and its factorized-threshold amendment.

## Why endpoint certificates do not promote their ancestors

The focused BP01/BP02 tests already construct ordinary empty-context
certificates for `bertrand_closed_upper` and `bertrand_strict`. The sealed
Alpha-v12 registry nevertheless records both roots as `body_checked` and
denies checked use. Their declared dependencies transitively include hundreds
of further body-only Alpha entries, including eight that originated in the
quadratic-reciprocity campaign.

A theorem's empty-context certificate does not, by itself, supply individual
closed certificates for every declared intermediate theorem. Therefore neither
root may be marked `alpha_closed` or `stable_closed` until the entire chosen
release slice has passed the independently checked closure gates.

## Exact candidate slices

The first permissible root is `bertrand_closed_upper`:

| Quantity | Exact value |
| --- | ---: |
| Total transitive specifications | 542 |
| Already Stable and closed | 202 |
| Already Alpha-closed | 1 |
| Body-only entries requiring closure | 339 |
| Direct dependency edges in the slice | 1,909 |

Its ordered theorem-name SHA-256 is
`e1d5a915a7512f5da651604c862505ae95bb8415ead4c51a2373dd58f5366e6b`.
Its exact release-surface SHA-256 is
`2b209f904b24195886390074725502bae7341c6bde97f745d1cbb96285023ffa`.

The complete strict root is `bertrand_strict`; including both capstones yields
the identical dependency slice because the strict root already depends on the
closed-upper root:

| Quantity | Exact value |
| --- | ---: |
| Total transitive specifications | 544 |
| Already Stable and closed | 202 |
| Already Alpha-closed | 1 |
| Body-only entries requiring closure | 341 |
| Direct dependency edges in the slice | 1,917 |

Its ordered theorem-name SHA-256 is
`d0e90fb101f10684d792d9ba8a32ba2abc78a033bf18ea4c958f14a68cdd469e`.
Its exact release-surface SHA-256 is
`e4583c4630b6342cc00095bee19e109bb7cd8064b699f069b0d9eb51e61d7206`.

The eight body-only QR-origin prerequisites are:

1. `beta_product_pointwise_coprime`;
2. `beta_sum_transport_prefix`;
3. `eisenstein_initial_segment_prefix_all_bits`;
4. `eisenstein_initial_segment_decoded_choice`;
5. `beta_all_one_bit_count_exact`;
6. `eisenstein_initial_segment_bit_count_functional`;
7. `eisenstein_initial_segment_bit_count_exact`;
8. `beta_sum_pointwise_add`.

The pending root `quadratic_reciprocity_combined` is not an ancestor of either
Bertrand capstone. Its separate layered closure is therefore not a logical
prerequisite for a Bertrand promotion, although the eight listed QR-origin
bodies must each be independently closed.

## Executable preflight and trust boundary

Implementation:
[`bertrand_promotion.py`](../../peano-lab/py/peano_lab/library/bertrand_promotion.py).
Focused audit:
[`test_bertrand_promotion.py`](../../peano-lab/py/tests/test_bertrand_promotion.py).

`bertrand_promotion_plan` computes the transitive slice from exact Alpha-v12
rows without replaying proof bodies. It rejects unknown or duplicate roots,
missing/non-topological dependencies, and pending layered ancestors. Each row
preserves its source, immutable enrollment origin, exact statement digest,
release membership, existing evidence, and original Alpha index.

`check_bertrand_promotion_certificate` requires a genuine ordinary kernel
`Proof`, rejects every `DNE`, measures the proof under the unchanged live and
annotation limits, and asks the unchanged intuitionistic checker to verify
the exact sealed Alpha-v12 theorem from the empty context. A hash, receipt,
Boolean, or matching theorem name cannot substitute for a proof.

`check_bertrand_promotion_batch` requires exactly one such fresh certificate
for every body-only ancestor before any proposed dependency-closed transition
can proceed. A successful batch is still not a release: independent cold
processes, mutation tests, provenance, and explicit versioned admission remain
mandatory.

`construct_bertrand_closed_candidate` makes the preflight operational for one
body-only row at a time. It replays each already-closed Stable/Alpha direct
dependency through the existing edition boundary, requires an actual checked
certificate for every body-only direct dependency, replays the exact stored
proof body, assembles ordinary `Cut` nodes, and independently checks the
result from the empty context. Its result is an isolated
`closed_checked_candidate`, not an evidence-label change or promotion.

`construct_bertrand_closed_microbatch` extends this constructor to at most
sixteen dependency-ordered rows and retains actual checked prerequisites in
memory. It additionally fails closed above 125,000 aggregate structural proof
nodes or 25,000 aggregate proof objects; these limits prevent sequential
small-row admission from silently becoming a large local closure. The focused
audit uses it to close all eight QR-origin prerequisites
independently from the empty context. Their respective structural proof-node
counts are `6748`, `59`, `25`, `1162`, `5172`, `10582`, `41170`, and `2794`.
All eight remain `body_checked` in immutable Alpha v12 until a separately
reviewed edition changes their evidence state.

A second independent eight-row microbatch closes the first Bertrand-native
interval and power prerequisites. Its exact structural node receipts are
`prime_strictly_above_decidable = 2492`,
`bounded_prime_interval_search = 2844`, `mul_le_mul = 521`,
`le_mul_of_one_le_right = 141`, `le_mul_of_one_le_left = 383`,
`pow_base_monotone = 4401`, `one_le_pow = 4049`, and
`pow_nonzero_of_one_le = 4091`. Thus sixteen rows have reproducible actual
empty-context candidate certificates; all 341 rows nevertheless retain their
original sealed Alpha-v12 body-only evidence until a new release is admitted.

`bertrand_bounded_valuation_microbatch_plan` freezes the next eight-row
Alpha dependency window and selects only six constructible rows in four
separate, dependency-ordered microbatches:

| Safe microbatch | Independently closed theorem | Structural proof nodes |
| --- | --- | ---: |
| 1 | `power_divides_decidable` | 63,931 |
| 2 | `power_divides_zero` | 61,118 |
| 3 | `bounded_power_valuation_search` | 64,301 |
| 4 | `power_valuation_functional` | 252 |
| 4 | `power_valuation_power_divides` | 21 |
| 4 | `power_valuation_dominates` | 24 |

The first two rows cannot share a batch: their combined 125,049 structural
nodes exceed the immutable 125,000-node cap by 49. The third batch consumes
the first row's actual independently checked proof as a carried prerequisite.
The final three rows have only already-closed Stable dependencies or no
dependencies; none depends transitively on either deferred existence row.

`bounded_power_valuation_exists` is explicitly deferred. Its two body-only
direct premises, `bounded_power_valuation_search` and `power_divides_zero`,
already contain 64,301 + 61,118 = 125,419 structural nodes before the target
body or remaining closed prerequisite is added. The previously audited exact
unrestricted certificate has 125,454 nodes, exceeding the unchanged cap by
454. Its successor `power_valuation_exists` inherits that obstruction and has
a previously audited unrestricted size of 125,470 nodes. Neither forbidden
certificate is constructed by the bounded focused audit.

There are consequently **22 distinct reproducible empty-context closed
candidate certificates**, including the original 16 and six safe valuation
rows, but there is not a contiguous 22-row promoted prefix: the two blocked
rows remain unclosed under the workstation policy. All 341 body-only Alpha
entries still retain their original evidence, and no Alpha or Stable edition,
identity, release, or checked-use authority changes.

## Explicit future release gates

1. Recompute and verify the exact slice against the immutable Alpha-v12
   enrollment and edition roots.
2. Construct a complete empty-context certificate for every body-only row in
   dependency order; never use the recursively expanded full graph locally.
3. Reject theorem-statement, body, dependency, certificate, and `DNE`
   mutations with the unchanged kernel.
4. Run two cold, provenance-bound WMI passes and compare their exact results.
5. Preserve Alpha v1–v12 and Stable v1 byte-for-byte.
6. Introduce a separately versioned Alpha evidence transition and, if
   deliberately selected, a separately versioned Stable release.
7. Regenerate catalog, receipt, channel, and proof-explorer artifacts from
   those accepted release facts.

No module import, plan, documentation table, or preflight digest upgrades
theorem evidence or confers checked-use authority.
