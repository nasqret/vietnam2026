# HA Bertrand B5 Order and Quotient Support Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-16

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Edition parent: Alpha v11 at commit
`02c5d4421fa39ed61dc5f2057d230b37a7304f5a`.

The parent edition is frozen by:

- 1,123 Alpha rows, 3,482 dependency edges, and 45 layers;
- enrollment identity
  `c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36`;
- edition identity
  `46d07832b0c630b9ce1da1d6e639687347cd737774b2b88b923bc5f477b9ddc3`;
- catalog SHA-256
  `d992c4aeb37829838cefd668679c513c5d45f6304f9842dcbe825bb25563182c`;
- metrics SHA-256
  `92cb654431a1b631cede3a0957993b41b8ad0fb0a0175d1587413dbf54c14300`;
- dependency graph SHA-256
  `c020f3207b0408cf446200b2c91f0767874c50466eebda830c3faeeef08aeae1`;
- channel manifest SHA-256
  `039712b6a1db739738f49b5cec20afdc0582ffae477bc43c52f96c00687b066f`.

## 1. Scope

This tranche supplies the generic constructive order machinery needed by the
B5 valuation audit.  It deliberately does not claim the complete
prime-power contribution bound, the zero-contribution interval, the
five-range factorization, or `central_binom_le_of_no_bertrand_prime`.

The tranche has twelve rows:

1. two already checked finite-product order rows;
2. two strict-addition laws;
3. two finite-sum order rows;
4. four relational division-doubling laws;
5. two monotone-power laws.

The two pre-existing rows are pinned, replayed, and reviewed here because
they were not members of Alpha v11.  Their exact source and focused test are:

- `finite_product_order_candidate.py`, SHA-256
  `4a502fe8e233c631305ebb644cec9e3c877e1830e0348995f8e6e481fff1b433`,
  9,695 bytes;
- `test_finite_product_order_candidate.py`, SHA-256
  `5fcd164e0fee70f48dd2fd4117676c570b7c4f09271d0896098bee435161f132`,
  20,922 bytes.

The new source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_b5_order_quotient_candidate.py
4a307f03a5f832db2470cf27e2958902ac203aa7e1263138432f47df72e81f6e
```

The focused-test seal remains pending until commit publication.  A source
seal or receipt is evidence only and is not theorem authority.

## 2. Representation contract

Every readable relation is an authoring abbreviation expanded before
parsing.  No order, division, sequence, sum, product, or power symbol is
added to the kernel.

The following abbreviations are used below:

```text
LE(a,b)       := exists g. g + a = b
LT(a,b)       := exists g. g + S a = b
DivRem(d,n,q,r)
              := n = d*q+r /\ LT(r,d)
BetaAt(b,c,i,x)
              := the existing expanded beta-decoding relation
Sum(b,c,l,n)  := the existing expanded finite-sum relation
Product(b,c,l,n)
              := the existing expanded finite-product relation
Pow(a,e,x)    := the existing expanded relational power
```

All generated binders must be collision-checked against the complete public
and local context.  Compound terms must be parsed in that context and
canonically pretty-printed before expansion.  Public formulas freeze the
displayed association and argument order.

## 3. Rows, surfaces, tags, and dependencies

The row order below is binding and dependency-topological.

### 3.1 `beta_product_pointwise_le`

Exact surface and private tags remain byte-identical to the pinned source:

```text
forall b c d e l n q.
  (forall i a z. LT(i,l) -> BetaAt(b,c,i,a) ->
     BetaAt(d,e,i,z) -> LE(a,z)) ->
  Product(b,c,l,n) -> Product(d,e,l,q) -> LE(n,q)
```

Frozen tags begin with `bppl`; direct dependencies, in order:

```text
(beta_product_zero, beta_product_succ_decompose,
 le_succ, le_refl, mul_le_mul)
```

### 3.2 `beta_product_uniform_le_pow`

```text
forall b c a l n q.
  (forall i x. LT(i,l) -> BetaAt(b,c,i,x) -> LE(x,a)) ->
  Product(b,c,l,n) -> Pow(a,l,q) -> LE(n,q)
```

Frozen tags begin with `bpulp`; direct dependencies, in order:

```text
(beta_repeat_entry_eq, beta_product_pointwise_le)
```

### 3.3 `add_lt_add`

```text
forall a b c d. LT(a,b) -> LT(c,d) -> LT(a+c,b+d)
```

Public occurrence tags are `b5alaa_left`, `b5alaa_right`, and
`b5alaa_result`.  Direct dependencies:

```text
(add_succ_left, add_shuffle_middle)
```

### 3.4 `add_lt_cancel_left`

```text
forall c a b. LT(c+a,c+b) -> LT(a,b)
```

Public occurrence tags are `b5altcl_source` and `b5altcl_result`.  Direct
dependencies, in first-use order:

```text
(add_assoc, add_comm, add_left_cancel)
```

### 3.5 `beta_sum_pointwise_le`

```text
forall b c d e l n q.
  (forall i a z. LT(i,l) -> BetaAt(b,c,i,a) ->
     BetaAt(d,e,i,z) -> LE(a,z)) ->
  Sum(b,c,l,n) -> Sum(d,e,l,q) -> LE(n,q)
```

Tags begin with `bspl`.  Direct dependencies:

```text
(beta_sum_zero, beta_sum_succ_decompose, le_succ, le_refl,
 add_le_add_right, add_le_add_left, le_trans)
```

### 3.6 `beta_sum_uniform_le_mul`

```text
forall b c a l n.
  (forall i x. LT(i,l) -> BetaAt(b,c,i,x) -> LE(x,a)) ->
  Sum(b,c,l,n) -> LE(n,l*a)
```

Tags begin with `bsulm`.  Direct dependencies:

```text
(beta_repeat_exists, beta_sum_exists, beta_repeat_entry_eq,
 beta_repeat_sum_exact, beta_sum_pointwise_le)
```

### 3.7 `division_zero_quotient_of_lt`

```text
forall d n q r.
  DivRem(d,n,q,r) -> LT(n,d) -> q=0
```

Tags are `bdzq_source` and `bdzq_bound`.  Direct dependencies:

```text
(zero_add, division_remainder_unique)
```

### 3.8 `division_double_quotient_bit`

```text
forall d n q r Q R.
  DivRem(d,n,q,r) -> DivRem(d,n+n,Q,R) ->
  (Q=q+q \/ Q=S(q+q))
```

Tags are `bddqb_source` and `bddqb_double`.  Direct dependencies, in
first-use order:

```text
(le_or_lt, le_eq_or_lt, lt_not_le, zero_le, one_le_of_ne_zero,
 add_shuffle_middle, mul_add, add_assoc, add_comm,
 add_lt_add, add_lt_cancel_left, division_remainder_unique)
```

The conclusion is a constructive quotient bit, not a Boolean or a division
function.  The proof splits `LE(r+r,d)` into equality/strict cases and the
remaining `LT(d,r+r)` case.  It constructs a canonical division of `n+n`
with quotient `q+q` or `S(q+q)` and then uses division uniqueness.

### 3.9 `division_double_quotient_lower`

```text
forall d n q r Q R.
  DivRem(d,n,q,r) -> DivRem(d,n+n,Q,R) -> LE(q+q,Q)
```

Tags are `bddql_source`, `bddql_double`, and `bddql_result`.  Direct
dependencies:

```text
(division_double_quotient_bit, le_refl, le_succ)
```

### 3.10 `division_double_quotient_upper`

```text
forall d n q r Q R.
  DivRem(d,n,q,r) -> DivRem(d,n+n,Q,R) -> LE(Q,S(q+q))
```

Tags are `bddqu_source`, `bddqu_double`, and `bddqu_result`.  Direct
dependencies:

```text
(division_double_quotient_bit, le_refl, le_succ)
```

### 3.11 `pow_le_pow_of_exponent_le`

```text
forall p e f x y.
  LE(1,p) -> LE(e,f) -> Pow(p,e,x) -> Pow(p,f,y) -> LE(x,y)
```

Tags are `bppem_base`, `bppem_exponent`, `bppem_left_power`,
`bppem_right_power`, and `bppem_result`.  Direct dependencies:

```text
(pow_exists, add_comm, pow_add, one_le_pow,
 le_mul_of_one_le_right)
```

The proof obtains the missing exponent power, uses `pow_add`, and bounds the
extra factor below by one.  It does not use exponentiation as a function.

### 3.12 `pow_tail_strict_of_square`

```text
forall p e x s n.
  LE(1,p) -> LE(2,e) -> Pow(p,2,s) -> Pow(p,e,x) ->
  LT(n,s) -> LT(n,x)
```

Tags are `bpsts_base`, `bpsts_exponent`, `bpsts_square_power`,
`bpsts_tail_power`, `bpsts_source`, and `bpsts_result`.  Direct dependencies:

```text
(pow_le_pow_of_exponent_le, lt_of_lt_of_le)
```

## 4. Proof-topology requirements

The focused harness must freeze the following structural facts in addition
to exact scripts:

- `add_lt_add` constructs one witness and uses no induction;
- `add_lt_cancel_left` rewrites only the small equality before cancellation;
- `beta_sum_pointwise_le` has exactly two length branches and exactly one
  direct recursive application in the successor branch;
- `beta_sum_uniform_le_mul` builds one repeat prefix and one sum, then calls
  the pointwise law exactly once;
- `division_zero_quotient_of_lt` constructs the zero-quotient equation,
  reuses the supplied remainder bound, and applies uniqueness once;
- `division_double_quotient_bit` has exactly three arithmetic leaves and
  applies division uniqueness exactly once per leaf;
- the two quotient bounds case only the theorem-produced disjunction;
- `pow_le_pow_of_exponent_le` uses one theorem-produced existential power and
  no induction;
- no theorem rewrites a whole `Sum`, `Product`, `Pow`, or `DivRem` premise.

The known inferability rule remains binding: an existential or disjunction
which will later be eliminated must be sourced directly from a hypothesis or
theorem application.  Constructed local packages may be passed to an
immediate theorem application but must not be cased later.

## 5. Authority and evidence

The initial focused core is Stable checked-use authority plus exact pinned,
recursively rebuilt candidate support.  It must not use Alpha membership as
logical authority.  Within the new source, each row sees only the preceding
local rows.  The existing product-order second row sees the first pinned row
only.

Every row requires concrete artifact, body, bounded-envelope, and recursive
empty-context closure receipts.  Receipt comparison occurs only after:

1. kernel checking;
2. body/envelope/live-cap checks;
3. no-DNE inspection;
4. exact direct-Cut counting;
5. exhaustive corruption and rejection of every direct Cut.

Default caps remain unchanged:

```text
proof occurrence nodes <= 500000
distinct proof objects <= 100000
proof depth <= 256
annotations <= 5000000
```

The direct-Cut vector is frozen as:

```text
(5, 2, 2, 3, 7, 5, 2, 12, 3, 3, 5, 2)
```

It has 51 dependency edges.  Every edge requires a liveness rejection.

## 6. Genuine mutations

At least one semantic mutation per row must be rebuilt independently and
rejected.  The following standard-natural counterfixtures are binding:

1. `beta_product_pointwise_le`: reverse the final product order; singleton
   factors 1 and 2 give `2 <= 1`, false.
2. `beta_product_uniform_le_pow`: reverse the final order; a singleton factor
   1 bounded by 2 gives `2 <= 1`, false.
3. `add_lt_add`: conclude `LT(a+d,b+c)`; use `(a,b,c,d)=(0,1,0,1)`.
4. `add_lt_cancel_left`: conclude `LT(b,a)`; use `(c,a,b)=(0,0,1)`.
5. `beta_sum_pointwise_le`: reverse the final sum order; singleton summands
   0 and 1 give `1 <= 0`, false.
6. `beta_sum_uniform_le_mul`: replace `l*a` by `a`; use two summands 1 with
   `l=2`, `a=1`, and sum 2.
7. `division_zero_quotient_of_lt`: conclude `q=1`; use
   `(d,n,q,r)=(1,0,0,0)`.
8. `division_double_quotient_bit`: delete the successor disjunct; use
   `(d,n,q,r,Q,R)=(2,1,0,1,1,0)`.
9. `division_double_quotient_lower`: strengthen the result to
   `LE(S(q+q),Q)`; use `(2,0,0,0,0,0)`.
10. `division_double_quotient_upper`: replace the result by `LE(Q,q+q)`;
    use `(2,1,0,1,1,0)`.
11. `pow_le_pow_of_exponent_le`: strengthen `LE(x,y)` to `LT(x,y)`; use
    `p=1`, `e=f=0`, `x=y=1`.
12. `pow_tail_strict_of_square`: strengthen the result to `LT(S n,x)`; use
    `p=2`, `e=2`, `s=x=4`, and `n=3`.

Each row also receives the standard false-target and dependency-removal
gates.  Commuted addition, alpha-renamed beta binders, or swapped equivalent
disjuncts are not genuine mutations.

## 7. Release policy

Passing this tranche creates body evidence only.  The rows may then enter the
next additive Alpha edition as `body_checked`, `checked_use=False`, with null
closure tags.  Stable is unchanged.  Neither the present RFC nor Alpha
membership authorizes a theorem in another proof; a client must replay the
dependency-closed candidate prefix until a later cold-closure promotion.

The next B5 tranche should consume these rows to prove the factorial/Legendre
valuation balance, the large-prime exponent-one result, and the
`2n/3 < p <= n` zero-contribution result.  The complete contribution bound
and extensional five-range product factorization remain explicit later gates.
