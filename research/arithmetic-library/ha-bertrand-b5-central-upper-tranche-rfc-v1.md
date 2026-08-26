# HA Bertrand B5 Central-Upper Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-17

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`1034ba1806d4357fc47da3818200c713f2327236`.

Edition parent: Alpha v11, frozen by 1,123 rows, 3,482 edges, 45 layers,
and `editions_v11.py` SHA-256
`10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_b5_central_upper_candidate.py
95b11876de61baa50ed1b7ff4debc2ce9afb52a35aeb2a83ff5920ca81ca77a7
```

The focused-test seal and measured proof receipts remain pending.  Hashes and
receipts are evidence only and grant no authority.

## 1. Scope

This ten-row tranche converts the reviewed pointwise prime-contribution
trichotomy into the quantitative B5 upper bound.  It proves:

```text
C <= (2*n)^s * 4^q
```

from the relational central coefficient, floor-root and division witnesses,
and the assertion that `(n,2*n]` contains no prime.  The exact public capstone
is `central_binom_le_of_no_bertrand_prime`.

The proof keeps the three Product ranges explicit.  Small factors are bounded
uniformly by `2*n`; middle factors are compared pointwise with the dense
Primorial selector interval and then with `4^q`; high factors are all one.
No neutral-factor compaction, raw beta-code equality, unique factorization,
classical choice, or DNE is introduced.

## 2. Representation contract

All readable relations below are authoring abbreviations expanded before
parsing.  They add no kernel symbol.

```text
Choice(C,i,a) := CompletePrimeContribution(C,i,a)
ContributionProduct(C,l,z) :=
  exists b c. ContributionPrefix(C,b,c,l) /\ Product(b,c,l,z)
ContributionInterval(C,a,l,z) :=
  exists b c. IntervalPrefix(C,a,b,c,l) /\ Product(b,c,l,z)
Selector(i,p) := Prime(S i) ? S i : 1
PrimorialInterval(a,l,P) :=
  exists b c. SelectorIntervalPrefix(a,b,c,l) /\ Product(b,c,l,P)
Central(n,C) := Choose(n+n,n,C)
NoBertrand(n) := forall p. Prime(p) -> n<p -> p<=n+n -> false
```

`Pow`, `FloorSqrt`, `DivRem`, `Product`, `BetaAt`, order, and every displayed
relation use their already frozen raw Peano expansions.  Generated binders are
capture-checked against the full context.

## 3. Binding row order and dependencies

The row order is dependency-topological and binding.

### 3.1 `beta_product_all_one_exact`

```text
forall b c l z.
  (forall i a. i<l -> BetaAt(b,c,i,a) -> a=1) ->
  Product(b,c,l,z) -> z=1
```

Public tags: `b5bpao_bound`, `b5bpao_entry`, `b5bpao_product`.

```text
(beta_product_zero, beta_product_succ_decompose,
 le_succ, le_refl, mul_one)
```

### 3.2 `no_bertrand_small_contribution_choice_le_double`

```text
forall n s q r C i a.
  NoBertrand(n) -> 2<n -> FloorSqrt(n+n,s) ->
  DivRem(3,n+n,q,r) -> Central(n,C) -> i<s -> Choice(C,i,a) ->
  a<=n+n
```

Public premise/result tag stem: `b5nbscc`.

```text
(lt_not_le, lt_to_le, le_trans, le_add_right,
 no_bertrand_central_contribution_choice_ranges)
```

### 3.3 `no_bertrand_middle_contribution_choice_le_selector`

```text
forall n s q r C i a p.
  NoBertrand(n) -> 2<n -> FloorSqrt(n+n,s) ->
  DivRem(3,n+n,q,r) -> Central(n,C) ->
  s<S i -> S i<=q -> Choice(C,i,a) -> Selector(i,p) -> a<=p
```

Public premise/result tag stem: `b5nbmcc`.

```text
(lt_not_le, le_refl,
 no_bertrand_central_contribution_choice_ranges)
```

### 3.4 `no_bertrand_high_contribution_choice_eq_one`

```text
forall n s q r C i a.
  NoBertrand(n) -> 2<n -> FloorSqrt(n+n,s) ->
  DivRem(3,n+n,q,r) -> Central(n,C) ->
  q<S i -> Choice(C,i,a) -> a=1
```

Public premise tag stem: `b5nbhcc`.

```text
(le_trans, lt_not_le, floor_sqrt_le_third_quotient,
 no_bertrand_central_contribution_choice_ranges)
```

### 3.5 `no_bertrand_small_contribution_product_le_power`

```text
forall n s q r C z A.
  NoBertrand(n) -> 2<n -> FloorSqrt(n+n,s) ->
  DivRem(3,n+n,q,r) -> Central(n,C) ->
  ContributionProduct(C,s,z) -> Pow(n+n,s,A) -> z<=A
```

Public premise/result tag stem: `b5nbscplp`.

```text
(beta_at_unique, beta_product_uniform_le_pow,
 no_bertrand_small_contribution_choice_le_double)
```

### 3.6 `no_bertrand_middle_contribution_interval_le_primorial_interval`

```text
forall n s q r C g y P.
  NoBertrand(n) -> 2<n -> FloorSqrt(n+n,s) ->
  DivRem(3,n+n,q,r) -> Central(n,C) -> s+g=q ->
  ContributionInterval(C,s,g,y) -> PrimorialInterval(s,g,P) -> y<=P
```

Public premise/result tag stem: `b5nbmcilpi`.

```text
(add_comm, add_le_add_left, beta_at_unique,
 beta_product_pointwise_le,
 no_bertrand_middle_contribution_choice_le_selector)
```

Only decoded entries are aligned.  Independently constructed beta codes are
never equated.

### 3.7 `no_bertrand_middle_contribution_interval_le_four_pow`

```text
forall n s q r C g y B.
  NoBertrand(n) -> 2<n -> FloorSqrt(n+n,s) ->
  DivRem(3,n+n,q,r) -> Central(n,C) -> s+g=q ->
  ContributionInterval(C,s,g,y) -> Pow(4,q,B) -> y<=B
```

Public premise/result tag stem: `b5nbmcilfp`.

```text
(le_trans, le_mul_of_one_le_left, primorial_exists,
 primorial_index_eq_transport, primorial_positive,
 primorial_prefix_interval_split, primorial_le_four_pow,
 no_bertrand_middle_contribution_interval_le_primorial_interval)
```

The dense Primorial is constructed once at `q`, transported to `s+g`, split,
and its positive prefix is used only to embed the interval factor.

### 3.8 `no_bertrand_high_contribution_interval_eq_one`

```text
forall n s q r C h w.
  NoBertrand(n) -> 2<n -> FloorSqrt(n+n,s) ->
  DivRem(3,n+n,q,r) -> Central(n,C) ->
  ContributionInterval(C,q,h,w) -> w=1
```

Public premise tag stem: `b5nbhcieu`.

```text
(add_comm, beta_at_unique, beta_product_all_one_exact,
 no_bertrand_high_contribution_choice_eq_one)
```

### 3.9 `central_binom_factorization_small`

```text
forall n s q r C g h z.
  NoBertrand(n) -> 2<n -> FloorSqrt(n+n,s) ->
  DivRem(3,n+n,q,r) -> Central(n,C) ->
  s+g=q -> q+h=n+n -> ContributionProduct(C,n+n,z) ->
  exists x y.
    ContributionProduct(C,s,x) /\
    (ContributionInterval(C,s,g,y) /\ z=x*y)
```

Public premise/result tag stem: `b5cbfs`.

```text
(mul_one, prime_contribution_product_length_eq_transport,
 prime_contribution_prefix_interval_split,
 no_bertrand_high_contribution_interval_eq_one)
```

The proof performs two generic prefix/interval splits.  It deliberately does
not call `prime_contribution_three_range_split`, whose frozen surface couples
the contribution number and doubled length and therefore cannot accept the
central value `C` with row length `n+n`.

### 3.10 `central_binom_le_of_no_bertrand_prime`

```text
forall n s q r C A B.
  NoBertrand(n) -> 2<n -> FloorSqrt(n+n,s) ->
  DivRem(3,n+n,q,r) -> Central(n,C) ->
  Pow(n+n,s,A) -> Pow(4,q,B) -> C<=A*B
```

Public premise/result tag stem: `b5cblonbp`.

```text
(mul_le_mul, floor_third_double_gap_package,
 central_binom_prime_contribution_product_exists,
 no_bertrand_small_contribution_product_le_power,
 no_bertrand_middle_contribution_interval_le_four_pow,
 central_binom_factorization_small)
```

This is the binding B5 central upper-bound interface required by the parent
campaign.

## 4. Evidence gates

The focused harness must:

1. pin every executed provider source, this RFC, Alpha v11, and the exact new
   candidate source;
2. parse every public statement as closed raw PA and freeze exact statement,
   script, dependency, and tag bytes through fail-closed artifact receipts;
3. expose Stable plus exact pinned candidate support and earlier local rows,
   never arbitrary provider discovery or registry enrollment;
4. remove every one of the 47 direct dependency edges and require replay
   failure;
5. reject a false target and at least one genuine finite counterfixture per
   row; conditional-row fixtures must relax the standardly impossible
   `NoBertrand(n)` premise rather than claim a vacuous countermodel;
6. kernel-check every body and dependency-closed root, reject DNE, enforce the
   default body/envelope/live caps, and freeze fail-closed receipts;
7. assert the exact direct-dependency vector
   `(5,5,3,4,3,5,8,4,4,6)`, exercise all 47 dependency-removal cases, and
   corrupt every compiled layered Cut under its exact accumulated Cut context
   before receipt acceptance;
8. use a deduplicating layered replay for the final roots, because the range,
   contribution reconstruction, split, and Primorial graphs share large
   transitive subgraphs and must not be duplicated structurally;
9. execute roots serially and clear replay caches between roots.

## 5. Promotion boundary

These rows enter no edition in this tranche.  Initial evidence is body-checked
and fail-closed only.  Alpha enrollment, checked-use promotion, Stable
promotion, and the eventual B7 contradiction remain separate reviewed acts.
