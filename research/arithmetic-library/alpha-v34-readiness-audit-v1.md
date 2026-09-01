# First-layer and congruence release-readiness audit

Date: 2026-09-02. This is a source, catalogue and byte-identity audit, not a new
proof replay, Alpha admission or publication receipt.

## Verified checkpoint and release boundary

The complete 119-row working polynomial gcd/Bézout checkpoint is committed as
`be320ec67696aa16deb7f7221fd025046b685b0d`. The commit preserves the earlier
95-row checkpoint and its evidence. It adds 185 previously untracked files;
the cumulative 119 rows include 52 rows already committed earlier, not 119
new rows on top of those 52.

The [completed checkpoint](working/prime-field-gcd-closure-v1/README.md)
records original HA and same-byte independent Lean verification, 14 ordinary
principal replays, and the separate focused tests. This audit freshly checked
58 file pins, 14 documentation links, and consistency of all 16 recorded final
gates. Those checks do not replace fresh admission gates.

Current Alpha remains v33: **4,092 checked-use entries**. Stable remains the
unchanged default **432-entry** channel. The 119 working rows are not admitted.
The original catalogue codec has a logical `MAX_ROWS = 4096`, inherited by v33
for theorem counts, membership counts and enrollment indices. Adding 119
requires **4,211 entries**, exceeding that boundary by 115 before any additional
congruence admissions. Splitting files does not evade this logical limit.

Promotion is paused for an explicit decision on a separately reviewed
catalogue-capacity design. Neither the historical codecs nor their limits were
changed. Proof CPU/wall/RSS/depth limits and protected deployment gates remain
unchanged. No new Alpha release or website deployment is claimed here.

One already-recorded cosmetic blank-at-EOF warning at
`working/prime-field-euclidean-normalization-v1/README.md:106` was preserved
with its exact archival bytes. Ignored Python caches were neither committed
nor deleted.

## What the first level actually contains

Use the [current v33 campaign](../../book/_static/constructive-research-campaign-v33/campaign.json),
not the immutable older `constructive-grand-campaign/campaign.json` v28 snapshot.

| Interpretation | Audited state |
| --- | --- |
| Literal DAG layer 1 | T04 beta coding, T05 bounded search, T06 division and T15 strong induction/descent are available tools. Their schematic descriptions are not newly proved universal theorem rows. |
| DAG layers 0–5 | 40 vertices, including 19 goals: 18 Alpha-closed and one Stable-closed; no open goal. |
| PLAN14 thematic Layer 1 | Division, gcd/lcm, signed Bézout, prime extraction/factorization, coprime cancellation and Euclidean descent have existing endpoints. |
| PLAN14 first execution wave | All 24 named items recorded complete; G077/G078 were the final new v26 milestones. |
| First family F01 | Not wholly complete: G008, Jordan-totient multiplicativity, remains open. |
| Congruence family F02 | G011–G014 are closed; G015–G020 remain open. |

The [v28 lower-layer receipt](alpha-v28-lower-layer-receipt.md) gives the exact
core contracts: G001 unique division for nonzero divisor; G002 actual signed
Bézout and unique gcd including `(0,0)`; G003 coprime-product cancellation with
a quotient witness; G004 actual prime-factor-list existence; G005 an actual
bijection between arbitrary unordered factor lists; G021 an unbounded prime
witness. G101 supplies actual coded Euclidean execution with a bit-length bound.

The earliest open DAG goal is **G091, layer 6**: prime-power finite-field
construction. The new polynomial gcd/Bézout theorem is a prerequisite, not a
proof of arbitrary-degree irreducible existence or of a field of size `p^k`.

## Standard congruence coverage

Names below are actual entries in the authenticated 4,092-row v33 catalogue,
not conclusions inferred merely from candidate filenames. They retain their
historical Stable/Alpha and first-admission evidence.

| Topic | Existing admitted endpoints |
| --- | --- |
| Equivalence and ring operations | `mod_eq_refl`, `mod_eq_symm`, `mod_eq_trans`, `mod_eq_add`, `mod_eq_mul_left`, `mod_eq_mul_right`, `mod_eq_mul` |
| Powers and finite folds | `pow_mod_congruent`, `beta_sum_pointwise_mod_congruent`, `beta_product_pointwise_mod_congruent` |
| Valid cancellation | `mod_eq_cancel_coprime`, `prime_mod_cancel`, `mod_eq_add_cancel_left`, `mod_eq_add_cancel_right`, `mod_eq_unscale_nonzero` |
| Modulus reduction and zero | `mod_eq_of_mod_eq_multiple`, `mod_eq_scale`, `mod_eq_zero_iff_eq`, `mod_eq_lcm_iff_pair` |
| Residues and decision | `canonical_remainder_exists_unique`, `canonical_remainders_characterize_mod_eq`, `canonical_remainder_zero_impossible`, `mod_eq_decidable` |
| Inverses | `coprime_mod_inverse`, `coprime_bounded_mod_inverse`, `mod_inverse_implies_coprime`, `bounded_mod_inverse_unique`, `coprime_iff_unique_bounded_mod_inverse` |
| Linear solvability | `linear_congruence_all_moduli_solvable_iff_gcd_divides`, `linear_congruence_solvable_iff_gcd_divides`, `linear_congruence_certified_decision`, `linear_congruence_coprime_bounded_solution_unique` |
| Binary CRT | `binary_crt`, `generalized_binary_crt_solvable_iff`, `generalized_binary_crt_canonical_boundary`, `generalized_binary_crt_total_decision` |
| Finite-list CRT | `crt_pairwise_coprime_prefix_canonical_exists_unique`, `crt_pairwise_compatible_prefix_normalized_exists_unique`, `crt_pairwise_compatible_prefix_solvable_iff`, `crt_normalized_prefix_solution_class_iff_lcm` |
| Fermat and Wilson | `fermat_predecessor_exponent_mod_one`, `prime_factorial_wilson_congruence` |
| Euler | `euler_coprime_totient_power_value`, `euler_coprime_totient_power`, `euler_theorem_for_units` |

Primary source locations under `peano-lab/py/peano_lab/library/` include
`theorems.py`, `power_congruence_theorems.py`, `finite_congruence_theorems.py`,
`ha_canonical_congruence_candidate.py`, `ha_generalized_crt_congruence_candidate.py`,
`ha_modular_inverse_candidate.py`, `linear_congruence_complete_candidate.py`,
`generalized_crt_full_candidate.py`, `fermat_endpoints_candidate.py`, and
`euler_units_candidate.py`. The linear-solvability endpoints are admitted via
the v19 frontier bundle; complete finite-list CRT via v24/v27; Fermat and
Wilson via quadratic reciprocity; Euler via the v2 Euler-units bundle.

Euler's positive-modulus endpoint includes modulus one. The more restrictive
G014 unit wrapper is not the only available Euler theorem. A forward Wilson
congruence is not a converse primality criterion.

## Actual remaining elementary congruence tranche

The general noncoprime solution-class and exact-count results are not supplied
by the nine existing linear-solvability rows. Let `ME(m,x,y)` denote the
existing balanced congruence; use actual natural cofactor equations, not a
new primitive quotient operation. For `m != 0`, `IsGCD(g,a,m)`,
`a = g*A`, `m = g*M`, implement:

1. Derive reduced coprimality and prove
   `ME(m,a*x,a*y) <-> ME(M,x,y)`.
2. Given an actual solution `ME(m,a*x0,b)`, prove the complete solution class
   `ME(m,a*x,b) <-> ME(M,x,x0)` for every natural `x`.
3. From `g | b`, construct a solution `x0 < M`, not merely `x0 < m`.
4. Prove the exact bounded parametrization
   `x < m /\ ME(m,a*x,b) <-> exists t < g. x = x0 + M*t`,
   including parameter uniqueness and injectivity. This supplies exactly
   `g` distinct solutions below `m`; an encoded list/count wrapper must
   construct its actual list if one is advertised.
5. Verify and admit the existing `fermat_little_all_inputs` candidate, whose
   exact contract is `Prime(p) -> Pow(a,p,A) -> ME(p,A,a)`. Its candidate body
   exists, but its name is absent from the v33 catalogue. Do not reclassify
   it as already admitted or rewrite Fermat unnecessarily.

Reuse `is_gcd_quotients_coprime_nonzero`, `mod_eq_unscale_nonzero`,
`mod_eq_cancel_coprime`, `mod_eq_scale`, existing remainder totality and
linear solvability. None of the intended conclusions may be smuggled into
a premise or definition.

Keep the boundary cases explicit: congruence modulo zero is equality, so
the finite positive-modulus count does not apply there; `(a,b)=(0,0)` then
has every natural as a solution. Modulus one has exactly one bounded residue.
No unrestricted multiplicative cancellation is asserted.

This bounded tranche is not all of F02. Orders/minimal periods, Carmichael's
exponent, primitive roots of odd prime powers, cyclic-unit classification,
exponential congruences and simultaneous polynomial congruences retain their
separate open contracts G015–G020. A claim of 'all standard theorems' requires
an explicit coverage inventory, not a completed percentage.

## Resumption and publication

See [PLAN29](../../PLAN/29_alpha_capacity_and_congruence_completion.md).
After a capacity decision, use new versioned provider/enrollment/edition,
admission, catalogue and verifier modules. Preserve the historical first
admissions, exact 119-row artifact and default Stable channel. Fresh original
HA, same-byte Lean and ordinary-principal gates remain mandatory.

Apply the constructive-proof-explorer model: conservative definition
identities, exact AST roundtrips, distinct proof/use/expansion arrows, canonical
Quadratic Reciprocity renderer, immutable earlier readers and live-evidence
publication checks.

Only the established faculty `proofs/` and `peano-lab-next/` paths are intended
for publication after acceptance. Production `peano-lab/` still has the
documented cache-header gate; this audit did not retest or waive it.

Raw observations from this turn are in
[the readiness record](alpha-v34-readiness-observations-v1.json). They are
documentary evidence only and cannot authorize a release.
