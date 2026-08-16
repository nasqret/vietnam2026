# HA Bertrand B5 Zero Two-Thirds Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-17

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`ee403b630a38556249784aebc7541c6abb1be6da`.

Edition parent: Alpha v11, frozen by 1,123 rows, 3,482 edges, 45 layers,
and `editions_v11.py` SHA-256
`10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

The immediately preceding square-tail tranche is pinned by source
`b07163c977af5bbbf4f84aaec3629c9c58c06e8acc7fed476134e980aec7a9ff`,
test `06046c6ee9da364057bfdce44d31de6ab2b011c9e61b1cdadcfc2106478b6dba`,
and RFC `dac2a5aee172a8ec78121ff5c83cbeead54f6b08733a0b91fb79183318eac7b5`.

## 1. Scope

This seven-row tranche proves that a prime in the open two-thirds range has
zero valuation in the central binomial coefficient.  Its public endpoint is:

```text
Prime(p) -> LT(2,n) -> LE(p,n) -> LT(n+n,(p+p)+p) ->
CentralBinom(n,C) -> PowerVal(p,C,v) -> v=0.
```

The scaled premise is the division-free form `2n<3p`.  Together with `p<=n`
it fixes the first quotients of `n` and `2n` by `p` at one and two.  Primality
and `2<n` put `p^2` above `2n`; every later quotient and therefore every
carry bit is zero.  The checked carry-count identity then forces `v=0`.

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_central_binom_zero_range_candidate.py
8ad4f3c5b90832dddc28d94f2b82f21eb47e8bd1e3f059696bbfa6e2b5c11b4e
```

## 2. Representation contract

`Prime`, `LE`, `LT`, `DivRem`, `Pow`, `PowerQuotientPrefix`, `CarryPrefix`,
`CentralBinom`, and `PowerVal` are authoring abbreviations only.  Every public
and local occurrence is fully expanded before parsing.  No theorem may use
raw beta-code equality, classical choice, DNE, a whole-relation rewrite, or an
unbounded retained replay graph.

The first four rows are small arithmetic constructors.  Row 5 may rewrite
only local `DivRem`, `BetaAt`, equality, and decoded-bit hypotheses.  Row 6
must obtain the carry package directly from `central_binom_carry_bit_count`.
Row 7 may rewrite only the small numeral alignment `2=1+1`.

## 3. Binding rows and dependencies

The order below is dependency-topological and binding.

### 3.1 `division_quotient_one_of_bounds`

```text
forall d n. LE(d,n) -> LT(n,d+d) -> exists r. DivRem(d,n,1,r)
```

Tags: `bdqob_lower`, `bdqob_upper`, `bdqob_result`.

Dependencies:

```text
(add_comm, mul_one, add_lt_cancel_left)
```

### 3.2 `division_quotient_two_of_bounds`

```text
forall d n. LE(d+d,n) -> LT(n,(d+d)+d) -> exists r. DivRem(d,n,2,r)
```

Tags: `bdqtb_lower`, `bdqtb_upper`, `bdqtb_result`.

Dependencies:

```text
(add_comm, mul_one, add_lt_cancel_left)
```

### 3.3 `prime_square_tail_of_two_three_range`

```text
forall p n s. Prime(p) -> LT(2,n) -> LT(n+n,(p+p)+p) ->
Pow(p,2,s) -> LT(n+n,s)
```

Tags: `bpstt_prime`, `bpstt_positive`, `bpstt_scaled`, `bpstt_power`,
`bpstt_result`.

Dependencies:

```text
(prime_is_succ_succ, zero_or_succ, add_le_add_right, add_le_add_left,
 le_trans, lt_not_le, mul_le_mul_left, mul_one, lt_of_lt_of_le, pow_two)
```

The `p=2` branch contradicts `6<=2n<6`.  The successor branch scales
`3<=p` to `3p<=p^2` and composes strict order.

### 3.4 `division_first_two_of_two_three_range`

```text
forall p n. LE(p,n) -> LT(n+n,(p+p)+p) ->
exists r R. DivRem(p,n,1,r) /\ DivRem(p,n+n,2,R)
```

Tags: `bdftt_lower`, `bdftt_scaled`, `bdftt_left`, `bdftt_right`.

Dependencies:

```text
(add_le_add_right, add_le_add_left, le_trans, lt_of_le_of_lt, add_comm,
 add_lt_cancel_left, division_quotient_one_of_bounds,
 division_quotient_two_of_bounds)
```

### 3.5 `double_quotient_carry_prefix_entries_zero`

```text
forall p n b c d e f g l q r R s.
LE(1,p) -> Pow(p,2,s) -> LT(n+n,s) ->
PowerQuotientPrefix(p,n,b,c,l) ->
PowerQuotientPrefix(p,n+n,d,e,l) ->
CarryPrefix(b,c,d,e,f,g,l) ->
DivRem(p,n,q,r) -> DivRem(p,n+n,q+q,R) ->
forall i. LT(i,l) -> BetaAt(f,g,i,0)
```

Tags start with `bdqcpez_` and are exact in the frozen source.

Dependencies:

```text
(zero_or_succ, pow_one, division_remainder_unique, beta_at_unique,
 zero_add, lt_irrefl_expanded, pow_tail_strict_of_square,
 division_zero_quotient_of_lt)
```

At index zero, `pow_one` and division uniqueness align both stored quotients
with `q` and `q+q`; the carry-one alternative contradicts irreflexivity.  At
a successor index, the power is at least the square, the right quotient is
zero, and the carry-one alternative contradicts `PA1`.

### 3.6 `central_binom_prime_valuation_zero_of_exact_double_quotients`

```text
forall p n C v q r R s.
Prime(p) -> CentralBinom(n,C) -> PowerVal(p,C,v) -> LE(1,p) ->
Pow(p,2,s) -> LT(n+n,s) -> DivRem(p,n,q,r) ->
DivRem(p,n+n,q+q,R) -> v=0
```

Tags start with `bcpvzeq_` and are exact in the frozen source.

Dependencies:

```text
(central_binom_carry_bit_count, zero_or_succ,
 bit_count_positive_last_one, double_quotient_carry_prefix_entries_zero,
 beta_at_unique)
```

If `v` is positive, `bit_count_positive_last_one` exposes a decoded one while
row 5 exposes a decoded zero at the same index.  `beta_at_unique` rejects it.

### 3.7 `central_binom_prime_valuation_zero_two_thirds_range`

The surface is the public endpoint from Section 1.  Tags start with
`bcpvztt_` and are exact in the frozen source.

Dependencies:

```text
(pow_exists, prime_square_tail_of_two_three_range,
 division_first_two_of_two_three_range, prime_nonzero,
 one_le_of_ne_zero,
 central_binom_prime_valuation_zero_of_exact_double_quotients)
```

## 4. Fail-closed evidence

The focused harness must freeze exact statements, scripts, dependency order,
and artifact/body/envelope/empty-context closure receipts.  Direct dependency
counts are `(3,3,10,8,8,5,6)`, totaling 43 live edges.  Every removal, false
target, and one genuine mutation per row must fail body replay.  Every closure
must kernel-check, remain under the standard occurrence/object/depth/annotation
caps, contain no DNE, and reject corruption of every replay-layer Cut before
its receipt is accepted.

Each body, rejection, and closure root runs in a fresh subprocess with
`PYTHONMALLOC=malloc`.  The earlier cumulative-DAG memory failure makes a
monolithic growing-root run inadmissible as evidence.

## 5. Genuine mutations

The harness uses one non-equivalent mutation per row:

1. quotient one changed to quotient zero;
2. quotient two changed to quotient one;
3. final strict square bound changed to its converse;
4. second quotient changed from two to one;
5. decoded result changed from zero to one;
6. conclusion `v=0` changed to `v=1`;
7. public conclusion `v=0` changed to `v=1`.

Small standard divisions and the fixture `p=3,n=4,C=70,v=0,s=9` refute these
mutations.  Binder renaming, tag changes, reassociation, or swapping an
equality orientation is not a genuine mutation.

## 6. Authority and next step

Passing this tranche creates candidate body and empty-context evidence only.
Stable and Alpha v11 remain unchanged.  Authority is Stable plus the exact
dependency-closed Alpha-v11/candidate prefix and the preceding local rows.

The next B5 step is to translate the scaled range into the explicit middle
prime-product factor and combine zero valuation here with the checked
square-tail exponent bound and complete prime-power contribution bound.  That
feeds the five-range central-binomial upper estimate.
