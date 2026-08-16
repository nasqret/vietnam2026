# RFC HA-R6-BERTRAND-PRIMORIAL-5: interval divisibility into Choose

**Status:** binding subordinate statement, dependency, evidence, trust,
capacity, and release contract; no theorem is enrolled or admitted by this
document

**Parent campaign:**
[`RFC HA-R6-BERTRAND-1`](ha-bertrand-postulate-campaign-rfc-v1.md), SHA-256
`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`

**Representation amendment:**
[`RFC HA-R6-BERTRAND-2`](ha-bertrand-postulate-campaign-rfc-v2.md), SHA-256
`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`

**Primorial interval contract:** `RFC HA-R6-BERTRAND-PRIMORIAL-3`,
`ha-bertrand-primorial-interval-split-tranche-rfc-v1.md`, SHA-256
`db7d2d58f0b44d3793673b21496ea7f5d5d2747c75795587f6b1c99b2e80f46e`

**Immutable edition parent:** Alpha v10 at commit
`1888aef98eb8cb6e421122e165ed938f7d5e03ef`

**Candidate parent:** commit
`5eef9a5b441c4b882705a573f8cc418d2b9792c6`

**Object language:** unchanged first-order HA over
\(\{0,S,+,\times,=\}\)

**Kernel change:** none

**Classical axioms:** none

This RFC freezes the ten-row bridge from relational factorial membership to
the even and odd Primorial-interval bounds needed by B4. The words **must**,
**must not**, **should**, and **may** are normative.

## 1. Scope and non-claims

This tranche supplies:

1. both directions of prime membership in a relational factorial;
2. prime divisibility of `Choose(n,k,c)` when the prime is above both
   denominator indices and at most the row;
3. a generic pairwise-coprime Product/common-multiple theorem;
4. pairwise coprimality of dense prime-or-one interval selectors;
5. generic interval divisibility into a suitable Choose value; and
6. the even-central and odd-middle divisibility and weak-order bounds.

It does **not** prove the elementary central coefficient upper inequalities,
`primorial_le_four_pow`, a B5 range inequality, B7, B8, BP01, or BP02. It
does not enroll a theorem or grant checked use.

## 2. Exact providers and source seal

All arithmetic rows not named below must come from Stable. Candidate support
must be rebuilt from the exact source bytes, using only the minimal prefixes
required by the ten proofs. Alpha membership and old receipts are not
authority.

```text
theorems.py
05a17b1f33a1c415582785885ca428ce2acb0f3da72700b2b25ad17e890b8919

finite_fold_surface.py
95ef546b5865dce135453afc3b7fe02ea1fa680b588e3358bfa243d358683f30

finite_factorial_theorems.py
a51240629fb661c3d732cb30ad32d3fdc1d3da8b9d01f80023f12429dc7e3709

bertrand_choose_foundation_candidate.py
97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d

bertrand_choose_factorial_bridge_candidate.py
22c07f0192b7e3cf6e85cb4b71fe70ecd3146c1c23cf6962ce261b369be10e09

bertrand_choose_positive_candidate.py
6c289d581e218841013b4f321fb39e66cc815c3ecc7be17d04b6f9fb586592cc

bertrand_central_binom_candidate.py
c495dc5fbb68ac6369788b8b65f0fd1c50658c8d44bb2692bf69d74b7064e61e

bertrand_primorial_foundation_candidate.py
70e50275253977d96537a256c2b0b676975ade8464c33b29786b5f70963e7a98

bertrand_primorial_interval_candidate.py
02e59e0f7addcae3bb127271ddeaa6728c5dab1dee096a878fced278065c10a3

finite_product_prefix_suffix_candidate.py
b0e98632b5668a688067ecdddebe0f906db00ebe84c267b395592d5797d27d9d

fermat_residue_product_candidate.py
b43a6fa9be64b806d9973abfb0d566533910c8a841fba16777b8a9498b98d59d
```

The new source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_primorial_choose_interval_candidate.py
5442a23447d87f3452b6fdb4fa44093063047592127707abcdc0defc29b4ac09
```

The focused-test seal remains pending until its fail-closed receipts are
measured. Any source change invalidates this seal and the focused manifest.

## 3. Exact authoring relations

Inherited `Prime`, `Factorial`, `Choose`, `BetaAt`, `Product`,
`PrimorialInterval`, and `CentralBinom` are fully expanded before parsing.
The only new readable abbreviation is:

```text
PairwiseCoprime(b,c,l) :=
  forall i j p q.
    Lt(i,l) -> Lt(j,l) ->
    BetaAt(b,c,i,p) -> BetaAt(b,c,j,q) ->
    ~(i=j) -> Coprime(p,q)
```

The generic interval side condition is:

```text
forall i. Lt(i,l) ->
  Lt(k,S(a+i)) /\ (Lt(j,S(a+i)) /\ Le(S(a+i),n))
```

It describes exactly the candidates `a+1` through `a+l`.

## 4. Frozen names and order

1. `factorial_prime_divides_of_le`
2. `factorial_prime_le_of_divides`
3. `choose_prime_divides_between`
4. `beta_pairwise_coprime_product_divides_common_multiple`
5. `primorial_interval_pairwise_coprime`
6. `primorial_interval_divides_choose_between`
7. `primorial_even_interval_divides_central`
8. `primorial_odd_interval_divides_middle`
9. `primorial_even_interval_le_central`
10. `primorial_odd_interval_le_middle`

No reordering or extra public row is permitted in this tranche.

## 5. Frozen abstract surfaces

```text
factorial_prime_divides_of_le :
  forall p n F.
    Prime(p) -> Le(p,n) -> Factorial(n,F) -> Dvd(p,F)

factorial_prime_le_of_divides :
  forall p n F.
    Prime(p) -> Factorial(n,F) -> Dvd(p,F) -> Le(p,n)

choose_prime_divides_between :
  forall n k j p c.
    k+j=n -> Prime(p) -> Lt(k,p) -> Lt(j,p) -> Le(p,n) ->
    Choose(n,k,c) -> Dvd(p,c)

beta_pairwise_coprime_product_divides_common_multiple :
  forall b c l n z.
    PairwiseCoprime(b,c,l) ->
    PointwiseDivides(b,c,l,z) ->
    Product(b,c,l,n) -> Dvd(n,z)

primorial_interval_pairwise_coprime :
  forall a b c l.
    IntervalFactorPrefix(a,b,c,l) -> PairwiseCoprime(b,c,l)

primorial_interval_divides_choose_between :
  forall a l n k j c z.
    k+j=n -> Choose(n,k,c) -> PrimorialInterval(a,l,z) ->
    (forall i. Lt(i,l) ->
      Lt(k,S(a+i)) /\ (Lt(j,S(a+i)) /\ Le(S(a+i),n))) ->
    Dvd(z,c)

primorial_even_interval_divides_central :
  forall n z c.
    PrimorialInterval(n,n,z) -> CentralBinom(n,c) -> Dvd(z,c)

primorial_odd_interval_divides_middle :
  forall n z c.
    PrimorialInterval(S n,n,z) ->
    Choose(S(n+n),n,c) -> Dvd(z,c)

primorial_even_interval_le_central :
  forall n z c.
    PrimorialInterval(n,n,z) -> CentralBinom(n,c) -> Le(z,c)

primorial_odd_interval_le_middle :
  forall n z c.
    PrimorialInterval(S n,n,z) ->
    Choose(S(n+n),n,c) -> Le(z,c)
```

## 6. Frozen dependencies

```text
factorial_prime_divides_of_le :
  (prime_is_succ_succ,
   beta_factor_divides_product,
   add_succ_left,
   zero_add)

factorial_prime_le_of_divides :
  (divisor_one,
   le_succ,
   euclid_prime_dvd_product,
   divisor_le_nonzero,
   succ_ne_zero,
   factorial_zero,
   factorial_succ_decompose)

choose_prime_divides_between :
  (factorial_exists,
   choose_factorial_bridge,
   factorial_prime_divides_of_le,
   euclid_prime_dvd_product,
   factorial_prime_le_of_divides,
   lt_not_le)

beta_pairwise_coprime_product_divides_common_multiple :
  (beta_product_zero,
   beta_product_succ_decompose,
   le_succ,
   le_refl,
   one_multiple,
   lt_irrefl_expanded,
   beta_product_pointwise_coprime,
   coprime_product_is_lcm)

primorial_interval_pairwise_coprime :
  (beta_at_unique,
   add_left_cancel,
   distinct_primes_coprime,
   coprime_one_left,
   coprime_one_right)

primorial_interval_divides_choose_between :
  (beta_at_unique,
   one_multiple,
   choose_prime_divides_between,
   primorial_interval_pairwise_coprime,
   beta_pairwise_coprime_product_divides_common_multiple)

primorial_even_interval_divides_central :
  (add_comm,
   add_le_add_left,
   primorial_interval_divides_choose_between)

primorial_odd_interval_divides_middle :
  (add_comm,
   add_succ_left,
   add_le_add_left,
   le_refl,
   lt_trans,
   primorial_interval_divides_choose_between)

primorial_even_interval_le_central :
  (primorial_even_interval_divides_central,
   central_binom_positive,
   divisor_le_nonzero)

primorial_odd_interval_le_middle :
  (primorial_odd_interval_divides_middle,
   choose_positive,
   add_succ_left,
   divisor_le_nonzero)
```

The direct-Cut vector is exactly:

```text
(4, 7, 6, 8, 5, 5, 3, 6, 3, 4)
```

There are exactly `51` dependency edges. Every edge must be live.

## 7. Binding proof topology

1. Factorial forward membership obtains the prime shape `S(S k)`, decodes
   the consecutive Range entry at index `S k`, and applies only the checked
   Product factor-divisibility theorem. Its final numeral alignment is a
   small equality goal; no whole-Factorial rewrite is permitted.
2. Factorial reverse membership inducts the length, uses factorial zero and
   successor decomposition, then Euclid. The terminal branch uses
   `divisor_le_nonzero`; it must not pretend `S n` is prime.
3. The Choose bridge obtains exactly three factorial witnesses, applies the
   factorial identity once, and uses Euclid twice. A denominator branch is
   rejected by factorial reverse membership and `lt_not_le`.
4. The pairwise Product theorem inducts the Product length. The successor
   step proves the prefix product coprime to the last factor with
   `beta_product_pointwise_coprime`, then uses `coprime_product_is_lcm`.
5. Interval pairwise coprimality cases directly on the two selector
   disjunctions. Prime/prime uses distinct candidate indices; every branch
   containing the neutral factor uses the appropriate coprime-with-one law.
6. Generic interval divisibility aligns each decoded value with its selector
   by beta uniqueness. The prime branch invokes Row 3 and the neutral branch
   invokes `one_multiple`; Row 4 combines the factors.
7. The even and odd specializations prove only their three elementary index
   inequalities before applying Row 6. They perform no whole-Choose or
   whole-interval rewrite.
8. The final two rows turn divisibility into weak order using positivity of
   the target coefficient and `divisor_le_nonzero`.

No proof may use DNE, an `AllPrime` assertion for the dense selector interval,
valuation, cancellation of a possibly-zero multiplier, or a raw beta-code
identity.

## 8. Genuine mutation gates

At least one false semantic mutation per row must be kernel-rejected:

1. change the factorial result divisor from `p` to `S p`;
2. strengthen reverse membership from `Le(p,n)` to `Le(S p,n)`;
3. change the Choose result divisor from `p` to `S p`;
4. change the product result divisor from `n` to `S n`;
5. strengthen pairwise output from `Coprime(p,q)` to
   `Coprime(S p,q)`;
6. change the generic interval divisor from `z` to `S z`;
7. change the even interval divisor from `z` to `S z`;
8. change the odd interval divisor from `z` to `S z`;
9. strengthen `Le(z,c)` to `Le(S z,c)` in the even row; and
10. make the same strengthening in the odd row.

Standard counterfixtures use `2! = 2`, `Choose(2,1)=2`, the empty Product
value `1`, interval selectors `1,2`, and the zero-index central or odd-middle
coefficient `1`.

## 9. Fail-closed evidence

The focused test must:

- pin every executed source and this RFC;
- rebuild candidate support from source in dependency order;
- expose Stable plus the required support and only the earlier local prefix;
- freeze the exact names, surfaces, tags, dependencies, and scripts;
- require concrete artifact, body, bounded-envelope, and recursive-closure
  receipts for all ten rows;
- kernel-check every body and empty-context closure;
- enforce the unchanged body and closure caps;
- reject DNE;
- reject every dependency removal, false target, and genuine mutation; and
- count and corrupt every direct Cut before accepting a closure receipt.

Because prior memory pressure was observed, body and closure selectors must be
run serially in fresh processes. A broad shared-cache run is not release
evidence for this tranche.

## 10. Release boundary

Passing this RFC yields body-checked candidate evidence only. A later additive
Alpha enrollment may include the rows after a separate edition RFC and
artifact build. Stable promotion and checked use remain separate decisions.

The next B4 tranche should prove the strong central and odd-middle coefficient
upper inequalities. The final `primorial_le_four_pow` tranche should then use
bounded induction on an explicit upper bound, parity, the interval split, the
two interval inequalities here, and `pow_add`.
