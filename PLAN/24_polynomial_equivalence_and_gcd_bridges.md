# Polynomial formal equivalence and the next gcd/Bézout bridges

Continuation authorized on 2026-08-31, from pushed commit `7259a8d60`.
The preceding 113-row working checkpoint and every file in
`working/prime-field-euclidean-v1/` remain immutable. Alpha v32 has 3,971
checked-use entries; Stable remains the unchanged default 432. No new
admission or public deployment is implied by a working proof checkpoint.

## First tranche: genuine representation congruence

Use the existing conservative `PolynomialEquivalent`, `PolynomialLeftPad`,
`PolynomialPowerCoefficient`, aligned field-operation and actual convolution
graphs. Formal equivalence compares coefficients at every power, not values
of polynomial functions over a finite field. Beta codes and unused table
entries are never identified.

The required principal contracts are:

1. `prime_field_polynomial_equivalent_implies_left_pad`: equivalence of a
   representation of length `L` and one of length `t+L` implies the actual
   `t`-entry left-padding relation. No primality or canonical-code premise.
2. `prime_field_polynomial_add_equivalent_congruent`: over a prime field,
   two actual aligned additions, at possibly different lengths, with
   pairwise formally equivalent inputs have formally equivalent outputs.
3. `prime_field_polynomial_subtract_equivalent_congruent`: the corresponding
   statement for actual subtraction graphs.
4. `prime_field_polynomial_convolution_equivalent_congruent`: at nonzero
   modulus, two actual convolution products of pairwise formally equivalent
   factors have formally equivalent outputs. Both empty factors and mixed
   length-order directions must be handled. Needed intermediate products
   are constructed, not assumed equal to a desired output.

Only genuine helper lemmas needed by these contracts enter this tranche.
All new sources, tests and controls live under
`research/arithmetic-library/working/prime-field-equivalence-v1/`.

## Proof and definition gates

- Preserve the original kernel, compiler, codecs, provider sources, historical
  artifacts and limits: CPU 170/175 seconds, wall 180 seconds, observed RSS
  1,610,612,736 bytes per proof process. Do not overlap heavy Alpha imports.
- Focused tests check actual conditional HA bodies, independently expanded
  contracts, finite examples and rejected missing/poisoned dependencies.
  No accepting proof mocks, trusted oracle rows or changed theorem premises.
- Reuse all 397 existing conservative definitions and all 865 expansion
  edges. New statement compaction must re-expand to the identical core AST.
  Definition expansion, theorem-definition use and proof prerequisites stay
  separate. None of these syntax checks grants proof authority.
- Freeze actual source/test/specification identities, then compare new rows
  with each other, the prior 113 working rows and all 3,971 current Alpha
  statements. The prior 113 remain working rows, not inherited Alpha.
- Export a real dependency-complete bundle using freshly checked exact
  seeds. Run original whole-bundle HA and independently compiled Lean on
  the same bytes, plus each of the four exact ordinary principals in its
  own fresh window. Rebind inputs before and after each phase.
- Record observations separately from proof inputs. An old receipt, JSON
  status, manifest or definition arrow cannot authorize a proof or release.

## Subsequent open work

The congruence tranche is a prerequisite, not polynomial associativity.
Associativity still needs an actual coefficient-level argument: induction
using a proved append recurrence is the first route to try, with generic
finite-sum reindexing an alternative. Scalar/unit products, actual
divisibility and linear-combination witnesses then support gcd/Bézout.
Keep factor order explicit in the backward step:

`A = Q*B + R`, `G = U*B + V*R` imply `G = V*A + (U-V*Q)*B`.

The eventual induction is on the second reduced length. Zero/zero, constant
divisors, characteristic two, arbitrary encodings and monic normalization
remain explicit. Bézout coefficients are not unique. Full gcd/Bézout,
arbitrary formal-identity division-pair uniqueness and G091 remain open.

### Source-only API audit for the associativity step

The broader finite-sum route can reuse `beta_sum_pointwise_mod_congruent` from
`peano-lab/py/peano_lab/library/finite_congruence_theorems.py`. It already
transports actual native-natural sums along pointwise modular congruence
on equal-length prefixes, even for modulus zero. A replacement modular-sum
wrapper would not supply the missing associativity argument.

Existing native-natural tools also include `beta_sum_exists`,
`beta_sum_functional`, `beta_sum_zero`, `beta_sum_succ_decompose`,
`beta_sum_transport_prefix`, `beta_sum_pointwise_add`, `beta_repeat_sum_exact`
and actual `beta_pointwise_mul_prefix_exists`. The preserved working rows
add `beta_sum_pointwise_mod_add` and actual left-pad/zero-tail sum invariance.

`beta_sum_permutation_invariant` requires an actual bounded-injective
beta-coded target-to-source map on the same complete window, together with
pointwise alignment. It is not an unequal-window support-reindex theorem.
Likewise, `prime_field_polynomial_convolution_outside_zero` concerns actual
antidiagonal coefficients, not arbitrary beta entries after a prefix.

The bounded source audit did not locate generic native-natural rectangle
flattening/Fubini. Existing signed Fubini and signed block/support reindexing
use canonical signed codes and `SignedSum`; Eisenstein Fubini is specialized
to actual indicator/count data. Neither is a drop-in law for convolution's
native-natural `Sum`.

Proposed next contracts, not implemented or counted here:

1. Actual natural scalar-sum linearity: if two length-`l` prefixes have
   entries related by `b = k*a`, and actual sums `u`, `v`, prove `v = k*u`.
2. Reuse the existing `beta_affine_matrix_slice_exists` for actual native
   slices; construct the needed slice sums and row-total tables, including
   zero dimensions, with actual witnesses rather than supplied totals.
3. Prove row-major flattening from the actual slice/row-total graphs.
4. Prove equality of the two actual rectangular iteration orders, then
   construct and verify the specific triangular-support reindex map needed
   by three-factor convolution. Combine this with zero-padding invariance
   and the existing modular-sum transport to prove polynomial associativity.

Any notation introduced for these future graphs requires a new conservative
definition audit. No proposed rectangle alias is registered in this tranche,
and scalar associativity alone must not be reported as convolution
associativity.

A second bounded audit suggests a narrower first route: induction on the
rightmost factor's actual represented length. Generic natural Fubini is not
mathematically required, and this alternative is not yet a proved resource
minimum. Reuse `prime_field_polynomial_convolution_left_add`, the actual
`prime_field_polynomial_constant_product_to_scale` /
`prime_field_polynomial_scale_to_constant_product` correspondence, existing
scalar-add distribution/functionality/transport, the actual product
constructors, and the left-padding compatibility laws.

The missing contracts for this route are:

- Actual trailing-zero shift covariance `A*(X*C) ≃ X*(A*C)`. A trailing zero
  represents multiplication by `X`; it is not leading-zero padding.
- Right-input scalar covariance, from actual `Scale(c,B,S)`, `Conv(A,B,P)`
  and `Conv(A,S,Q)` to actual `Scale(c,P,Q)`. Induction on a canonical scalar
  using bilinearity, or one-dimensional natural scalar-sum linearity, are
  noncircular options.
- An all-index append recurrence
  `A*append(C,c) ≃ X*(A*C) + c*A`, with actual aligned output sums and the
  required left-padding witnesses. Existing triangular lemmas cover earlier
  coefficients and a boundary coefficient, not this complete recurrence.
- Proper-product-length bookkeeping and the final length induction,
  including empty factors and constants. No nonzero-leading-coefficient
  assumption is needed; evaluation/Horner laws cannot substitute for these
  formal coefficient identities.

Release planning is separate: admitting all 121 working rows would bring
Alpha from 3,971 to 4,092 entries, leaving four under the current 4,096-entry
transport bound. This turn neither admits these rows nor changes that bound;
a later large promotion needs an explicit capacity plan.

## Execution record

The initial worktree is clean. The existing 113-row artifact is 2,219,445
bytes, SHA-256
`c2e097f0e04c4b4f01bb219102405d0e93bc847c19625113eb48e55c7900734d`.
Its earlier completed HA/Lean evidence is retained, but every seed used by
the new exporter will be freshly checked. New proof results will be recorded
only after their actual gates finish.

Eight new source rows have now passed the original conditional HA checker:
five representation/additive lemmas (24 declared edges, 544 script commands,
652 body occurrences) and three convolution congruence lemmas (442 body
occurrences). This is not a dependency-closed proof claim. Both final focused
independent-contract, model and dependency-attack suites passed: 368 distinct
representation/additive cases and 353 distinct convolution cases. Repeated
development runs add no cases to these counts. Their compact observations
and actual commands are saved in the new working directory.

The final 43 notation/DAG cases passed against both frozen authors' sources
in 20.249 seconds at 101,138,432 bytes RSS. They reuse the identical
397-definition/865-edge registry, check actual new statement compaction and
independent named principal contracts, and separate all three arrow kinds.
The saved source-only DAG contains eight theorem nodes, 37 declared proof
edges, 20 theorem-definition use edges, and a selected closure of 21 existing
definitions with 35 expansion edges. External proof prerequisites remain
explicitly unresolved in this presentation artifact; proof paths cover only
the supplied eight rows. These checks never perform theorem acceptance.

The final 133 source/ownership/integration guards passed. Actual global
comparison of the 121 working statements against all 3,971 Alpha statements
found no duplicates (64.831 seconds, 1,072,594,944 bytes RSS). The full cone
has 376 mathematical nodes: 255 inherited Alpha rows and 121 working rows;
with packaging it needs 377 nodes and 1,071 edges.

Exact inert seed inspection covers 367 of the 368 pre-existing targets.
The remaining inherited `prime_field_polynomial_add_functional` is an
existing v31 execution-frontier row whose three ordered premises are all
in the preserved seed. Its original body will be rebuilt alongside the
eight new bodies, with no broader historical-provider scan. Inert coverage
and novelty do not substitute for the pending actual whole-bundle gates.

Actual full authoring subsequently passed: all 368 seed nodes freshly
checked, 367 mathematical bodies retained, one inherited 147-node body and
eight new bodies reconstructed, and all 377 resulting nodes checked by the
original HA kernel. The complete bundle has 1,071 edges and 30,527 body
nodes; it is 2,449,379 bytes, SHA-256
`6ae667d8518e4dbe722bb08ad1b08715a0d282c2893e533c8133d770fe861dcf`.
The export used 69.977 seconds and 1,053,179,904 bytes RSS. Original limits
and all old files remained unchanged. Independent same-byte Lean and four
ordinary-principal windows remained separate acceptance gates.

After registering only that real artifact, all 134 final integration guards
passed. The fresh whole-bundle HA and independent compiled Lean gate then
passed on the identical artifact bytes: 41.885 seconds, 1,040,613,376 bytes
RSS and final before/after source binding
`ab82ddaa7947a5d392a816cf78db4946d983f1b981b4467f33631179fb5ea1bb`.
The four ordinary-principal replays are still in progress.

The additional joint 898-case run exposed an import-lifetime regression:
851 passed, four failed and 43 setup errors. Both new focused test modules
left the temporary representation alias installed after successful imports;
the later unchanged ownership guards correctly rejected it. All old files
remained byte-identical. The initial joint observation is retained. The fix
is limited to import-scoped cleanup in the two new tests; test-only identities
will be refrozen and the final same-byte HA/Lean and four ordinary gates
repeated under the new binding. Mathematical scripts and proof bytes are not
being changed, and no guard is being relaxed.

The corrected imports reuse the existing ownership-safe context. Both
collection orders passed the same nine selected guards, with no surviving
representation alias/package attribute and no Alpha import; repeated order
runs add no distinct cases. The five-row test is now 19,312 bytes,
SHA-256 `778a8c9dcd43d5bed00125f176ac013a6aabfa4ae132a3ca16ba2bae2875b0dc`;
the convolution test is 19,162 bytes,
SHA-256 `224e7d441f17217616a34e9e6fe85d321ba8c1ba410675cbacf56c34b6f7c4b8`.
Only these two test identities are being updated in the new controls.

The final joint suite now passes all 898 cases in one process, with exactly
the same ordered IDs as the initial failing run: 114.613 seconds,
113.741 CPU seconds and 168,738,816 bytes peak RSS. All before/after source
identities match. It includes all 368 representation/additive, 353
convolution, 134 integration and 43 notation/DAG cases. Only the two test
files and their literal registrations changed; reversing those four
registration literals reproduces the prior control hashes exactly. The
final joint record, original failure and both-order smoke evidence are
saved separately. Heavy final gates continue under the refrozen binding.

The refrozen whole-bundle HA/same-byte compiled Lean gate passed with all
377 kernel calls, 1,071 edges and 30,527 body nodes: 42.173 seconds and
1,277,902,848 bytes RSS. The final source binding is
`33af357c30aca8f5bb6f2d838ef6cb4dd3f608dd90e6443e06d69a45f7a2a0c0`.
The first ordinary endpoint also passed under this binding, yielding an
8,711-node empty-context certificate for equivalence-to-padding. The earlier
pre-cleanup observations are historical, not the final input binding.

All five final gates are now complete under that final binding and the
unchanged artifact. Ordinary certificates have 8,711 nodes for
equivalence-to-padding, 10,075 for addition congruence, 10,163 for subtraction
congruence and 17,731 for convolution congruence. The final five windows took
220.908 seconds in total, with a largest single window of 48.327 seconds and
1,288,896,512 bytes RSS; original per-process limits were never raised.
All 898 distinct joint tests passed. This completes the eight-row congruence
tranche and the overlapping 121-row working checkpoint, not associativity,
gcd/Bézout, G091 or an Alpha/Stable/public-site release.
