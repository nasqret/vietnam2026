# HA Bertrand B5 Prime-Contribution Completeness Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-17

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`4f4bc37245efbbb291042d9bd53dfa00a643bd44`.

Edition parent: Alpha v11, frozen by 1,123 rows, 3,482 edges, 45 layers,
and `editions_v11.py` SHA-256
`10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

The prime-contribution foundation is pinned by source
`fe7dae9ad7e788c1c861e870a1a69fc872498b06267f05b9c6200bf1d45eee33`,
test `64856b02f273bc7f95c29d74666df8b8e05edfb6427e8318b3bbb034d5b75232`,
and RFC
`4970fabdc7ff1872a52bed7a18643a777939304cf7b2061a196518533385b520`.

The pointwise factor-range provider is pinned by source
`d03e4f7fb9a0f8f4de8db3022eb867cc600f4ec4f1a3050e3d9e35432ab4a8ae`,
test `33b9d18ae6185c299162c25f442f0ece36b790997297053917c0c83eaad087f1`,
and RFC
`32765966c68b0db98fb48136e5b3fdbc3312b6c7ef6d35737e7f1381e03f2c3b`.

## 1. Scope

This ten-row tranche proves the missing converse direction for the complete
prime-contribution product.  If every prime divisor of a nonzero natural lies
inside the finite contribution prefix, then the prefix Product equals the
natural itself.  The proof is constructive and does not invoke unique
factorization: a hypothetical prime divisor of the remaining cofactor raises
its already selected valuation power, contradicting maximality.

The tranche then specializes this exact reconstruction to central binomial
values and transports the checked B5 factor-range trichotomy to every decoded
entry of the central contribution prefix.  This is the precise input required
by the next prefix-splitting and pointwise-product comparison tranche.

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_prime_contribution_complete_candidate.py
7e07f6c8908170d4aa12a3d234efb7b3200bd40f854de577ef12485ddca2f67d
```

Focused evidence is implemented in
`peano-lab/py/tests/test_bertrand_prime_contribution_complete_candidate.py`.
All ten artifact, body, envelope, and closure receipt entries must be concrete
before release.

## 2. Representation contract

The readable abbreviations below are authoring notation only and are fully
expanded before parsing:

```text
PrimeSupport(n,m) :=
  forall p. Prime(p) -> Dvd(p,n) -> LE(p,m)

ContributionProduct(n,m,z) :=
  exists b c. ContributionPrefix(n,b,c,m) /\ Product(b,c,m,z)
```

`Prime`, `LE`, `LT`, `Dvd`, `Pow`, `PowerVal`, `CentralBinom`,
`NoBertrandClosed`, `FloorSqrt`, `DivRem`, `BetaAt`, and `Product` retain
their previously reviewed expansions.  No row may use DNE, a unique
factorization oracle, raw beta-code equality, arbitrary provider scanning, or
whole-relation rewriting of `ContributionProduct`, `PowerVal`, `Pow`, or
`CentralBinom`.

The only equality transport across a prime representation is scoped to the
small `Prime`, `LE`, and `Dvd` formulas in row 3.  The expanded valuation and
power relations stay natively indexed by `S i`.

## 3. Binding rows and dependencies

The row order is dependency-topological and binding.

### 3.1 `prime_contribution_selected_entry`

```text
forall n m z i.
Prime(S i) -> LE(S i,m) -> ContributionProduct(n,m,z) ->
exists e a. PowerVal(S i,n,e) /\ (Pow(S i,e,a) /\ Dvd(a,z))
```

Tags: `bpcse_prime`, `bpcse_bound`, `bpcse_source`, and the
`bpcse_result_*` family.

Dependencies:

```text
(beta_factor_divides_product)
```

The decoded entry is obtained from the contribution prefix.  The supplied
primality eliminates the neutral branch, while the generic Product theorem
shows that the decoded selected power divides the Product value.

### 3.2 `prime_contribution_selected_successor_divides`

```text
forall p e a z q n.
Pow(p,e,a) -> Dvd(a,z) -> Dvd(p,q) -> n=z*q -> PowDiv(p,S e,n)
```

Tags start with `bpcssd_`.

Dependencies:

```text
(mul_assoc, multiple_mul_left, power_divides_successor_of_cofactor)
```

This row isolates the only product reassociation in the maximality
contradiction.  If `z=a*x` and `p|q`, then `n=a*(x*q)` and `p|(x*q)`.

### 3.3 `prime_contribution_cofactor_prime_contradiction`

```text
forall n m z q p.
~(n=0) -> PrimeSupport(n,m) -> ContributionProduct(n,m,z) ->
n=z*q -> Prime(p) -> Dvd(p,q) -> false
```

Tags start with `bpccpc_`.

Dependencies:

```text
(prime_is_succ_succ, multiple_mul_left,
 prime_contribution_selected_entry,
 prime_contribution_selected_successor_divides,
 power_valuation_successor_not_divides)
```

The prime is written as `S(S k)`.  Its small support bound and cofactor
divisibility formulas are transported to that carrier.  Row 1 extracts the
selected valuation power, row 2 raises it, and maximality closes the branch.

### 3.4 `prime_contribution_cofactor_eq_one`

```text
forall n m z q.
~(n=0) -> PrimeSupport(n,m) -> ContributionProduct(n,m,z) ->
n=z*q -> q=1
```

Tags: `bpcceo_support`, `bpcceo_product`, and the private
`bpcceo_prime` / `bpcceo_divides` witness family.

Dependencies:

```text
(eq_decidable, prime_divisor_exists,
 prime_contribution_cofactor_prime_contradiction)
```

If `q` is neither zero nor one, constructive prime-divisor existence produces
the contradiction from row 3.  The zero case contradicts `n!=0` directly by
PA5; no separate factor-nonzero dependency is allowed.

### 3.5 `prime_contribution_reverse_divides`

```text
forall n m z.
~(n=0) -> PrimeSupport(n,m) -> ContributionProduct(n,m,z) -> Dvd(n,z)
```

Tags: `bpcrd_support`, `bpcrd_product`, `bpcrd_result`.

Dependencies:

```text
(mul_one, prime_contribution_product_divides,
 prime_contribution_cofactor_eq_one)
```

### 3.6 `prime_contribution_product_eq`

```text
forall n m z.
~(n=0) -> PrimeSupport(n,m) -> ContributionProduct(n,m,z) -> n=z
```

Tags: `bpcpeq_support`, `bpcpeq_product`, with private forward and reverse
divisibility tags.

Dependencies:

```text
(multiple_antisymm, prime_contribution_product_divides,
 prime_contribution_reverse_divides)
```

This is the generic complete-factorization endpoint.  It combines the two
checked divisibility directions extensionally and never compares beta codes.

### 3.7 `prime_contribution_complete_exists`

```text
forall n m.
~(n=0) -> PrimeSupport(n,m) ->
exists z. ContributionProduct(n,m,z) /\ n=z
```

Tags: `bpcce_support`, `bpcce_product`.

Dependencies:

```text
(prime_contribution_product_exists, prime_contribution_product_eq)
```

### 3.8 `central_binom_prime_contribution_product_exists`

```text
forall n C.
CentralBinom(n,C) ->
exists z. ContributionProduct(C,n+n,z) /\ C=z
```

Tags: `bcbpcpe_central`, `bcbpcpe_product`, and private support tags.

Dependencies:

```text
(central_binom_positive, central_binom_prime_divisor_le_double,
 prime_contribution_complete_exists)
```

Positivity supplies `C!=0`; the checked central divisor theorem supplies
`PrimeSupport(C,n+n)`.

### 3.9 `no_bertrand_central_contribution_choice_ranges`

With binders `n s q r C i a`, premises are:

```text
NoBertrandClosed(n) -> LT(2,n) -> FloorSqrt(n+n,s) ->
DivRem(3,n+n,q,r) -> CentralBinom(n,C) -> ContributionChoice(C,i,a).
```

The conclusion is:

```text
((LE(S i,s) /\ LE(a,n+n)) \/
 ((LT(s,S i) /\ LE(S i,q)) /\ a=S i)) \/ a=1.
```

Tags start with `bnbccr_`.

Dependencies:

```text
(no_bertrand_central_prime_contribution_ranges)
```

The prime branch applies the checked factor-range endpoint to the selected
valuation and power; the nonprime branch is the neutral disjunct.

### 3.10 `no_bertrand_central_contribution_prefix_ranges`

This row replaces the final Choice premise of row 9 by a central contribution
prefix and exposes the same conclusion for every bounded decoded entry:

```text
ContributionPrefix(C,b,c,n+n) ->
forall i a. LT(i,n+n) -> BetaAt(b,c,i,a) -> Range(n,s,q,i,a).
```

Tags start with `bnbcpr_`.

Dependencies:

```text
(beta_at_unique, no_bertrand_central_contribution_choice_ranges)
```

Only the small three-occurrence result is transported from the canonical
decoded value to the caller's decoded value.

## 4. Fail-closed evidence

The focused harness must independently rebuild every public relation and
freeze exact scripts, dependency order, artifact receipts, body receipts,
bounded envelopes, and empty-context layered closures.  Direct dependency
counts are:

```text
(1, 3, 5, 3, 3, 3, 2, 3, 1, 2)
```

There are 26 live edges.  Every dependency removal, false target, and one
genuine semantic mutation per row must fail body replay.  Every closure must
kernel-check, stay below unchanged occurrence/object/depth/envelope/annotation
caps, contain no DNE, and reject corruption of every direct replay-layer Cut
before receipt acceptance.

Large roots run serially in fresh attached subprocesses with
`PYTHONMALLOC=malloc`.  Keeping multiple expanded closure DAGs alive in one
interpreter is invalid evidence.

## 5. Genuine mutations

The harness uses these non-equivalent mutations and standard finite-model
counterfixtures:

1. require the selected output power to have exponent `S e`; use
   `n=2,m=2,z=2,i=1`, whose selected factor is `2^1=2`;
2. require a double-successor power divisor; use
   `p=2,e=0,a=z=1,q=n=2`;
3. replace `Prime(p)` by truth; use
   `n=z=q=p=1,m=0`, whose neutral empty Product satisfies every remaining
   premise;
4. replace the conclusion `q=1` by `q=0`; use `n=z=q=1,m=0`;
5. replace `Dvd(n,z)` by `Dvd(S n,z)`; use `n=z=1,m=0`;
6. replace `n=z` by `n=S z`; use `n=z=1,m=0`;
7. replace the existential equality `n=z` by `n=S z`; use `n=1,m=0`;
8. replace `C=z` by `C=S z`; use `n=0,C=z=1`;
9. and 10. replace `NoBertrandClosed(n)` by truth and use
   `n=5,C=252,s=q=3,r=1,i=6,a=7`.

Binder renaming, tag changes, conclusion association, commuting factors, or
reversing an equality is not a genuine mutation.

## 6. Authority and next step

Passing this tranche creates candidate body and empty-context evidence only.
Stable and Alpha v11 remain unchanged.  Authority is Stable plus the exact
dependency-closed Alpha-v11 and post-v11 candidate prefix and preceding local
rows.  No stored receipt, Alpha membership, or unrelated provider is theorem
authority.

The next B5 tranche should split the exact central contribution Product at
the floor-square-root and quotient boundaries.  It should compare the small
prefix pointwise with the uniform bound `n+n`, the duplicate-free middle
prefix with `Primorial(q)`, and the neutral suffix with one.  That comparison
is the direct precursor of `central_binom_factorization_small` and
`central_binom_le_of_no_bertrand_prime`.
