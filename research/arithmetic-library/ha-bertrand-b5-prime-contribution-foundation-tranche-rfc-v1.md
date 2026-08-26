# HA Bertrand B5 Prime-Contribution Foundation Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-17

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`f659e24b157d40ceab1557439054253d630075f2`.

Edition parent: Alpha v11, frozen by 1,123 rows, 3,482 edges, 45 layers,
and `editions_v11.py` SHA-256
`10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

The immediately preceding factor-range tranche is pinned by source
`d03e4f7fb9a0f8f4de8db3022eb867cc600f4ec4f1a3050e3d9e35432ab4a8ae`,
test `33b9d18ae6185c299162c25f442f0ece36b790997297053917c0c83eaad087f1`,
and RFC `32765966c68b0db98fb48136e5b3fdbc3312b6c7ef6d35737e7f1381e03f2c3b`.

## 1. Scope

This twelve-row tranche introduces an extensional beta product of complete
prime-power contributions.  At position `i`, the selected factor is the
complete power of the prime `S i` dividing `n`, or one when `S i` is not
prime.  The tranche proves totality and functionality of the selector,
prefix, and Product relations; proves that distinct selected factors are
coprime; proves every selected factor divides `n`; and concludes that every
finite selected Product divides `n`.

The public endpoint is:

```text
forall n m z. PrimeContributionProduct(n,m,z) -> Dvd(z,n).
```

This is the checked one-way reconstruction bridge.  The converse
`Dvd(n,z)` for a sufficiently long prefix, and hence equality by
`multiple_antisymm`, remains an explicit later obligation.  It may not be
replaced by equality of beta codes or by a unique-factorization oracle.

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_prime_contribution_candidate.py
fe7dae9ad7e788c1c861e870a1a69fc872498b06267f05b9c6200bf1d45eee33
```

## 2. Representation contract

The following are authoring abbreviations only.  Every occurrence is fully
expanded before parsing.

```text
Choice(n,i,a) :=
  (Prime(S i) /\ exists e. PowerVal(S i,n,e) /\ Pow(S i,e,a)) \/
  (~Prime(S i) /\ a=1)

ContributionPrefix(n,b,c,m) :=
  forall i. LT(i,m) ->
    exists a. BetaAt(b,c,i,a) /\ Choice(n,i,a)

PrimeContributionProduct(n,m,z) :=
  exists b c. ContributionPrefix(n,b,c,m) /\ Product(b,c,m,z)
```

`Coprime(a,b)` is the constructive common-divisor predicate already used by
the arithmetic library.  `PairwiseCoprimePrefix(b,c,m)` quantifies two
distinct decoded positions below `m` and asserts `Coprime` of their values.
`PointwiseDivides(b,c,m,n)` quantifies a decoded value below `m` and asserts
that it divides `n`.

No row may use raw beta-code equality, DNE, classical choice, an opaque
factorization theorem, or an `AllPrime` product lemma.  The dense prefix has
neutral factors at nonprime positions, so `AllPrime` is intentionally false.
All transports are through decoded `BetaAt` values and functionality.

## 3. Binding rows and dependencies

The row order is dependency-topological and binding.

### 3.1 `prime_contribution_choice_exists`

```text
forall n i. exists a. Choice(n,i,a)
```

Public tag: `bpcce_result`.

Dependencies:

```text
(prime_decidable, power_valuation_exists, pow_exists)
```

The prime branch chooses the functional valuation exponent and then a
relational power.  The nonprime branch chooses one.

### 3.2 `prime_contribution_choice_functional`

```text
forall n i a z. Choice_left(n,i,a) -> Choice_right(n,i,z) -> a=z
```

Public tags: `bpccf_left`, `bpccf_right`.

Dependencies:

```text
(power_valuation_functional, pow_functional)
```

The mixed prime/nonprime branches are contradictory.  In the prime branch,
valuation functionality first aligns the exponents and power functionality
then aligns the selected values.

### 3.3 `prime_contribution_prefix_extend`

```text
forall n b c m.
ContributionPrefix_before(n,b,c,m) ->
exists d e. ContributionPrefix_after(n,d,e,S m)
```

Public tags: `bpcpe_before`, `bpcpe_after`.

Dependencies:

```text
(prime_contribution_choice_exists, beta_prefix_extend,
 finite_lt_succ_eq_or_lt)
```

The terminal branch transports all twelve free occurrences of the index in
the decoded-entry-plus-choice package.  The older branch transports only the
small decoded `BetaAt` entry supplied by `beta_prefix_extend`.

### 3.4 `prime_contribution_prefix_exists`

```text
forall n m. exists b c. ContributionPrefix(n,b,c,m)
```

Public tag: `bpcpx_result`.

Dependencies:

```text
(add_eq_zero_right, succ_ne_zero, prime_contribution_prefix_extend)
```

### 3.5 `prime_contribution_prefix_transport_entry`

```text
forall n b c d e m.
ContributionPrefix_left(n,b,c,m) ->
ContributionPrefix_right(n,d,e,m) ->
forall i a. LT(i,m) -> BetaAt(b,c,i,a) -> BetaAt(d,e,i,a)
```

Public tags: `bpcpt_left`, `bpcpt_right`, `bpcpt_bound`,
`bpcpt_source`, `bpcpt_target`.

Dependencies:

```text
(beta_at_unique, prime_contribution_choice_functional)
```

The two decoded factors are aligned by selector functionality and exactly
two scoped rewrites of the target `BetaAt` value.

### 3.6 `prime_contribution_product_exists`

```text
forall n m. exists z. PrimeContributionProduct(n,m,z)
```

Public tag: `bpc_product_exists`.

Dependencies:

```text
(beta_product_exists, prime_contribution_prefix_exists)
```

### 3.7 `prime_contribution_product_functional`

```text
forall n m x y.
PrimeContributionProduct_left(n,m,x) ->
PrimeContributionProduct_right(n,m,y) -> x=y
```

Public tags: `bpcpf_left`, `bpcpf_right`.

Dependencies:

```text
(beta_product_transport_prefix, beta_product_functional,
 prime_contribution_prefix_transport_entry)
```

The source Product is transported to the target code using the extensional
entry theorem before Product functionality is applied.

### 3.8 `coprime_power_right`

```text
forall p q e z. Coprime_source(p,q) -> Pow(q,e,z) -> Coprime_result(p,z)
```

Public tags: `bcpr_source`, `bcpr_power`, `bcpr_result`.

Dependencies:

```text
(pow_zero, pow_successor_decompose, coprime_one_right,
 coprime_mul_right)
```

The induction fixes `p` and `q` before generalizing the relational power
value `z`.

### 3.9 `coprime_powers`

```text
forall p q e f a z.
Coprime_source(p,q) -> Pow(p,e,a) -> Pow(q,f,z) -> Coprime_result(a,z)
```

Public tags: `bcpowers_source`, `bcpowers_left`, `bcpowers_right`,
`bcpowers_result`.

Dependencies:

```text
(pow_zero, pow_successor_decompose, coprime_one_left,
 coprime_mul_left, coprime_power_right)
```

### 3.10 `prime_contribution_prefix_pairwise_coprime`

```text
forall n b c m.
ContributionPrefix(n,b,c,m) -> PairwiseCoprimePrefix(b,c,m)
```

Public tags: `bpcppc_source`, `bpcppc_result`.

Dependencies:

```text
(beta_at_unique, distinct_primes_coprime, coprime_one_left,
 coprime_one_right, coprime_powers)
```

Distinct indices give distinct prime bases by successor injectivity.  The
four prime/nonprime selector branches are retained explicitly; no hidden
all-prime premise is introduced.

### 3.11 `prime_contribution_factor_divides`

```text
forall n i a. Choice(n,i,a) -> Dvd(a,n)
```

Public tags: `bpcfd_choice`, `bpcfd_result`.

Dependencies:

```text
(power_valuation_power_divides, pow_functional, one_multiple)
```

The prime branch aligns the power supplied by valuation divisibility with
the selected contribution.  The nonprime branch reduces to divisibility by
one.

### 3.12 `prime_contribution_product_divides`

```text
forall n m z. PrimeContributionProduct(n,m,z) -> Dvd(z,n)
```

Public tags: `bpcpd_source`, `bpcpd_result`.

Dependencies:

```text
(beta_at_unique,
 beta_pairwise_coprime_product_divides_common_multiple,
 prime_contribution_prefix_pairwise_coprime,
 prime_contribution_factor_divides)
```

The pointwise divisibility premise is rebuilt from the decoded contribution
prefix, and the reviewed pairwise-coprime Product theorem supplies the final
common-multiple divisor.

## 4. Fail-closed evidence

The focused harness must independently rebuild every public formula and
freeze exact scripts, dependency order, artifact receipts, body receipts,
bounded envelopes, and empty-context layered closures.  Direct dependency
counts are:

```text
(3,2,3,3,2,2,3,4,5,5,3,4)
```

They total 39 live edges.  Every dependency removal, false target, and one
genuine semantic mutation per row must fail body replay.  Every closure must
kernel-check, remain below the unchanged occurrence, object, depth, envelope,
and annotation caps, contain no DNE, and reject corruption of every direct
replay-layer Cut before receipt acceptance.

Expanded Choice statements are large.  Closure roots run serially in fresh
subprocesses with `PYTHONMALLOC=malloc`; retaining multiple expanded closure
DAGs in one process is not valid evidence.

## 5. Genuine mutations

The harness uses these non-equivalent mutations and standard finite-model
fixtures:

1. require the selected witness to equal zero; use `n=1,i=0`, whose neutral
   contribution is one;
2. replace `a=z` by `a=S z`; use `n=1,i=0,a=z=1`;
3. require the extended terminal decoded value to be zero; use
   `n=1,m=0`;
4. require a length-one prefix's index-zero value to be zero; use `n=1,m=1`;
5. transport the source value `a` to target value `S a`; use the same
   length-one neutral prefix;
6. require the Product witness to equal zero; use the empty Product `1`;
7. replace `x=y` by `x=S y`; use two empty Products;
8. remove the source coprimality premise; use `p=q=2,e=1,z=2`;
9. remove the source coprimality premise; use
   `p=q=2,e=f=1,a=z=2`;
10. require coprimality at equal decoded positions; use `n=2,m=2` and the
    index-one contribution `2`;
11. replace `Dvd(a,n)` by `Dvd(S a,n)`; use `n=1,i=0,a=1`;
12. replace `Dvd(z,n)` by `Dvd(S z,n)`; use `n=1,m=0,z=1`.

Range shifts that preserve totality, binder renaming, tag changes,
association, or commutation are not genuine mutations.

## 6. Authority and next step

Passing this tranche creates candidate body and empty-context evidence only.
Stable and Alpha v11 remain unchanged.  Authority is Stable plus the exact
dependency-closed Alpha-v11 candidate graph and preceding local rows.  In
particular, the final row recursively rebuilds the pinned
`beta_pairwise_coprime_product_divides_common_multiple`; it does not treat its
Alpha membership or stored receipt as theorem authority.

The next B5 theorem must prove the converse divisibility for a sufficiently
long contribution prefix.  A cap-safe route should use strong or bounded
induction on `n`, exact cofactors, and valuation maximality, then combine both
directions with `multiple_antisymm`.  Only after that reconstruction bridge
is checked may the product be split at the floor-square-root and quotient
boundaries and compared with the three factor ranges from the preceding
tranche.
