# HA Bertrand B5 Central-Valuation Bridge Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-16

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`62005803aed7ba3d2ed314f2dde6073a8a29057d`.

Edition parent: Alpha v11, frozen by:

- 1,123 Alpha rows, 3,482 dependency edges, and 45 layers;
- enrollment identity
  `c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36`;
- edition identity
  `46d07832b0c630b9ce1da1d6e639687347cd737774b2b88b923bc5f477b9ddc3`;
- `editions_v11.py` SHA-256
  `10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`;
- `alpha_enrollment_v11.py` SHA-256
  `400201f7075b15ca6b4eed3e367a522803c6e431e3afc553692e4757ed3ba093`.

The immediately preceding B5 support is pinned by:

- source SHA-256
  `4a307f03a5f832db2470cf27e2958902ac203aa7e1263138432f47df72e81f6e`;
- focused-test SHA-256
  `ad7193afcb0d00fd5daa53c096bc3864d292c78d2ffa255472c8f5c0d82a4dca`;
- subordinate-RFC SHA-256
  `fdcaf69b3913b7dbbcf312373b49f39b42819ba398cbb35f77e8eb66fb4762c1`.

## 1. Scope

This ten-row tranche connects the checked factorial bridge for
`CentralBinom(n,c)` to prime-power valuations and Legendre sums.  It then
compares the quotient prefixes for `n` and `n+n` extensionally and proves the
first public central-valuation bound:

```text
Prime(p) -> CentralBinom(n,c) -> PowerVal(p,c,e) -> LE(e,n+n).
```

This is genuine B5 progress, but it is not yet the complete prime-power
contribution bound `p^e <= n+n`.  The latter additionally needs a sparse-carry
argument locating the highest nonzero carry.  This tranche also does not claim
the square-tail exponent-one theorem, the `2n/3 < p <= n` zero-contribution
theorem, or either five-range capstone.

The new source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_central_binom_valuation_candidate.py
76ab449e7ae0dc58d7c99743e7df39e59d5619b8801387cd40a8cb242e2b79e8
```

The focused-test seal is populated only after all fail-closed receipts are
measured.  Source, test, and receipt seals are evidence, not theorem authority.

## 2. Representation contract

All readable relations below are authoring abbreviations expanded before
parsing into the unchanged first-order Peano language:

```text
LE(a,b)                    := exists g. g+a=b
LT(a,b)                    := exists g. g+S(a)=b
Prime(p)                   := the existing expanded prime relation
Pow(p,e,x)                 := the existing relational power
PowerVal(p,a,e)            := the existing bounded maximal valuation graph
DivRem(d,n,q,r)            := n=d*q+r /\ LT(r,d)
BetaAt(b,c,i,a)            := the existing beta-decoding relation
Sum(b,c,l,s)               := the existing relational finite sum
FactorialVal(p,n,e)        := exists F. Factorial(n,F) /\ PowerVal(p,F,e)
PowerQuotientPrefix(p,n,b,c,l)
                            := the first l quotients floor(n/p^(i+1))
LegendreSum(p,n,e)         := a length-n quotient prefix with sum e
CentralBinom(n,c)          := Choose(n+n,n,c)
```

Compound values and lengths are expanded only through factory-owned,
capture-checked markers.  `PowerVal` contains exactly four occurrences of its
valued number.  Row 1 freezes four scoped equality rewrites and no client may
rewrite an entire `PowerVal`, `FactorialVal`, `LegendreSum`, or
`CentralBinom` premise as an unreviewed shortcut.

## 3. Rows, surfaces, tags, and dependencies

The following order is binding and dependency-topological.

### 3.1 `power_valuation_value_eq_transport`

```text
forall p a b e.
  a=b -> PowerVal(p,a,e) -> PowerVal(p,b,e)
```

Tags: `b5cvvet_source`, `b5cvvet_target`.

Direct dependencies: `()`.

The proof has four forward rewrites at the source hypothesis and no Cut.

### 3.2 `central_binom_factorial_valuation_balance`

```text
forall p n c e A B.
  Prime(p) -> CentralBinom(n,c) -> PowerVal(p,c,e) ->
  FactorialVal(p,n+n,A) -> FactorialVal(p,n,B) ->
  A=(B+B)+e
```

Public tags begin with `b5cvfb`.  Direct dependencies, in order:

```text
(central_binom_positive, factorial_nonzero, choose_factorial_bridge,
 power_valuation_exists, power_valuation_value_eq_transport,
 prime_power_valuation_mul, mul_ne_zero)
```

The proof reuses the same factorial witness for both complementary columns,
applies valuation multiplicativity first to `K*K` and then to `(K*K)*c`, and
transports only the valued-number occurrences in `PowerVal`.

### 3.3 `central_binom_legendre_valuation_balance`

```text
forall p n c e A B.
  Prime(p) -> CentralBinom(n,c) -> PowerVal(p,c,e) ->
  LegendreSum(p,n+n,A) -> LegendreSum(p,n,B) ->
  A=(B+B)+e
```

Public tags begin with `b5cvlb`.  Direct dependencies:

```text
(factorial_valuation_exists,
 prime_factorial_valuation_eq_legendre_sum,
 central_binom_factorial_valuation_balance)
```

### 3.4 `prime_power_quotient_zero_of_exponent_gt`

```text
forall p n e d q r.
  Prime(p) -> LT(n,e) -> Pow(p,e,d) -> DivRem(d,n,q,r) -> q=0
```

Public tags begin with `b5cvqz`.  Direct dependencies:

```text
(prime_power_exponent_le, lt_of_lt_of_le,
 division_zero_quotient_of_lt)
```

### 3.5 `power_quotient_prefix_tail_entry_zero`

```text
forall p n b c l i.
  Prime(p) -> PowerQuotientPrefix(p,n,b,c,l) ->
  LE(n,i) -> LT(i,l) -> BetaAt(b,c,i,0)
```

Public tags begin with `b5cvptez`.  Direct dependencies:

```text
(prime_power_quotient_zero_of_exponent_gt)
```

The proof eliminates only the existential produced by the prefix hypothesis,
aligns the stored quotient by uniqueness, and rewrites the decoded value
exactly twice.

### 3.6 `power_quotient_prefix_sum_extend_zero`

```text
forall p n b c g t e.
  Prime(p) -> PowerQuotientPrefix(p,n,b,c,n+g) ->
  Sum(b,c,n+g,t) -> LegendreSum(p,n,e) -> t=e
```

Public tags begin with `b5cvpsez`.  Direct dependencies, in order:

```text
(legendre_sum_functional, le_succ, add_comm, zero_add,
 beta_sum_succ_last_zero, power_quotient_prefix_tail_entry_zero)
```

The proof inducts on `g`, restricts the same quotient code, proves its last
entry zero, and drops that summand.  It never equates raw beta codes.

### 3.7 `legendre_sum_extended_prefix_exists`

```text
forall p n e g.
  Prime(p) -> LegendreSum(p,n,e) ->
  exists b c.
    PowerQuotientPrefix(p,n,b,c,n+g) /\ Sum(b,c,n+g,e)
```

Public tags begin with `b5cvlsepe`.  Direct dependencies:

```text
(prime_power_quotient_prefix_exists, beta_sum_exists,
 power_quotient_prefix_sum_extend_zero)
```

### 3.8 `power_quotient_double_pointwise_upper`

```text
forall p n b c d e l.
  PowerQuotientPrefix(p,n,b,c,l) ->
  PowerQuotientPrefix(p,n+n,d,e,l) ->
  forall i q Q.
    LT(i,l) -> BetaAt(b,c,i,q) -> BetaAt(d,e,i,Q) ->
    LE(Q,S(q+q))
```

Public tags begin with `b5cvpdpu`.  Direct dependencies:

```text
(beta_at_unique, pow_functional, division_double_quotient_upper)
```

Only the two occurrences of the stored divisor in the small target division
record are transported.  No whole prefix is rewritten.

### 3.9 `beta_sum_pointwise_double_succ_le`

```text
forall b c d e l B A.
  Sum(b,c,l,B) -> Sum(d,e,l,A) ->
  (forall i q Q.
     LT(i,l) -> BetaAt(b,c,i,q) -> BetaAt(d,e,i,Q) ->
     LE(Q,S(q+q))) ->
  LE(A,(B+B)+l)
```

Public tags begin with `b5cvbsdsl`.  Direct dependencies:

```text
(beta_sum_zero, beta_sum_succ_decompose, le_succ, le_refl,
 add_le_add_right, add_le_add_left, le_trans, add_assoc, add_comm)
```

The proof is one ordinary induction on `l`; its successor branch has one
recursive use, two sum decompositions, one pointwise terminal bound, and no
constructed existential which is later eliminated.

### 3.10 `central_binom_prime_valuation_le_double`

```text
forall p n c e.
  Prime(p) -> CentralBinom(n,c) -> PowerVal(p,c,e) -> LE(e,n+n)
```

Public tags begin with `b5cvpvd`.  Direct dependencies:

```text
(prime_legendre_sum_exists,
 central_binom_legendre_valuation_balance,
 legendre_sum_extended_prefix_exists,
 power_quotient_double_pointwise_upper,
 beta_sum_pointwise_double_succ_le,
 add_comm, add_le_cancel_right)
```

The proof constructs the two Legendre sums, extends only the `n`-dividend
prefix to length `n+n`, applies the pointwise carry bound, substitutes the
exact valuation balance, and cancels the common doubled column sum.

## 4. Proof topology and authority

The direct-dependency vector is frozen as:

```text
(0, 7, 3, 3, 1, 6, 3, 3, 9, 7)
```

It contains 42 live dependency edges.  The focused harness must reject every
dependency removal.  Empty-context closure uses the existing root-pruned
`LayeredReplay` compiler with Stable certificates as leaves, dependency-
curried candidate bodies as internal nodes, balanced layer packages, and the
unchanged kernel as final authority.  The harness must corrupt and kernel-
reject every resulting layer Cut before accepting a closure receipt.

The proof core is Stable checked-use authority plus exact recursively rebuilt
Alpha-v11 candidate support, the preceding B5 order/quotient source, and the
earlier local prefix of this source.  Alpha membership is never treated as
logical authority.  The module must remain absent from Stable, Alpha,
enrollment manifests, and edition registries.

All existential and disjunctive packages which are later eliminated must be
direct theorem or hypothesis eliminations.  No DNE is permitted.  The
unchanged caps are:

```text
occurrence nodes <= 500000
distinct objects <= 100000
proof depth <= 256
annotations <= 5000000
```

Because of the prior memory incident, layered closures are run one row per
fresh Python process with `PYTHONMALLOC=malloc`.  A monolithic retained-DAG
closure run is not release evidence for this tranche, and the older recursive
Cut expansion is deliberately excluded from this tranche.

## 5. Genuine mutations

Each row requires a false target and one independently rebuilt semantic
mutation.  The binding mutations and standard counterfixtures are:

1. transport the target exponent to `S e`; use `p=2`, `a=b=1`, `e=0`;
2. replace the factorial balance by `A=(B+B)+S e`; use `n=0`, `c=1`,
   `e=A=B=0`;
3. make the same successor change in the Legendre balance with that fixture;
4. conclude `q=1`; use `p=2`, `n=0`, `e=1`, `d=2`, `q=r=0`;
5. conclude `BetaAt(b,c,i,1)`; use the length-one quotient prefix for
   `p=2`, `n=i=0`;
6. conclude `t=S e`; use `p=2`, `n=g=t=e=0`;
7. return a sum of `S e`; use `p=2`, `n=g=e=0`;
8. strengthen the pointwise upper bound to `LE(Q,q+q)`; use divisor 2 and
   dividend 1, whose doubled quotient is 1;
9. drop the `+l` term; a singleton pair `q=0`, `Q=1` has sums `B=0`,
   `A=1`;
10. strengthen the public result to `LE(S e,n+n)`; use the central base
    coefficient `n=0`, `c=1`, `e=0` at `p=2`.

Binder renaming, reassociation, commutation, or replacing a relation by an
alpha-equivalent expansion is not a genuine mutation.

## 6. Release policy and next step

Passing this RFC creates candidate body and empty-context evidence only.
Stable and Alpha remain unchanged.  A later additive Alpha may enroll these
rows as `body_checked`, `checked_use=False`; checked use requires a separate
dependency-closed cold-closure promotion.

The next B5 tranche must refine the linear exponent bound into the complete
prime-power contribution bound.  The intended route is a sparse carry prefix:
count the `Q=S(q+q)` indices, show the highest nonzero carry supplies a power
at most `n+n`, and compare its exponent with the carry count.  The already
checked square-tail theorem then yields valuation at most one above
`sqrt(n+n)`.  Only after those rows should the proof attack the
`2n/3 < p <= n` zero range and the five-range product capstone.
