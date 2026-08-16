# HA Bertrand B5 Central-Carry Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-16

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`fd3741453ed4bae851d9b346332817c00cd868a1`.

Edition parent: Alpha v11, frozen by:

- 1,123 Alpha rows, 3,482 dependency edges, and 45 layers;
- enrollment identity
  `c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36`;
- edition identity
  `46d07832b0c630b9ce1da1d6e639687347cd737774b2b88b923bc5f477b9ddc3`;
- `editions_v11.py` SHA-256
  `10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

The immediately preceding central-valuation tranche is pinned by:

- source SHA-256
  `76ab449e7ae0dc58d7c99743e7df39e59d5619b8801387cd40a8cb242e2b79e8`;
- focused-test SHA-256
  `4ec910f58563edc4f5cc31554e3f6bf92867015df25be1299873e6a285c1d02e`;
- subordinate-RFC SHA-256
  `aebab5f4cf6a63b67a0716c3dcd792a876f263bce6d371d25dcb4e3dbf78a8b3`.

## 1. Scope

This ten-row tranche refines the central-binomial valuation bound into the
complete prime-power contribution bound required by B5.  It beta-encodes the
binary carry in each doubled quotient, identifies the valuation with the
number of carries, locates a final nonzero carry, and proves:

```text
Prime(p) -> LE(1,n) -> CentralBinom(n,C) -> PowerVal(p,C,v) ->
Pow(p,v,D) -> LE(D,n+n).
```

The positivity premise on `n` is necessary: at `n=0`, the exponent-zero
contribution is one and is not at most zero.  This tranche does not claim the
large-prime exponent-one theorem, the `2n/3 < p <= n` zero-contribution
theorem, or either five-range capstone.

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_central_binom_carry_candidate.py
a480ca001ad0837c2ae45315bd5520c666d5e716a34c72ec5f5fcc0d7601c0f0
```

The focused-test seal is populated only after all fail-closed receipts are
measured.  Source, test, and receipt seals are evidence, not theorem authority.

## 2. Representation contract

All readable relations are authoring abbreviations expanded before parsing:

```text
CarryChoice(q,Q,b) :=
  (b=0 /\ Q=q+q) \/ (b=1 /\ Q=S(q+q))

CarryPrefix(B,S,D,T,F,G,l) :=
  forall i<l. exists q Q b.
    BetaAt(B,S,i,q) /\ BetaAt(D,T,i,Q) /\
    BetaAt(F,G,i,b) /\ CarryChoice(q,Q,b)
```

`BitCount(F,G,l,e)` is the existing relational finite bit count.
`PowerQuotientPrefix(p,n,B,S,l)` is the existing prefix of the quotients
`floor(n/p^(i+1))`.  Compound lengths such as `n+n` are expanded through
factory-owned, capture-checked markers.  No row may equate raw beta codes or
rewrite an entire quotient prefix, bit count, valuation, or central-binomial
hypothesis.

## 3. Rows and dependencies

The following order is binding and dependency-topological.

### 3.1 `double_quotient_carry_choice`

For two quotient prefixes at dividends `n` and `n+n`, every common position
has a uniquely stored carry choice.  Public tags begin with `b5ccqc`.

```text
(pow_functional, division_double_quotient_bit)
```

### 3.2 `double_quotient_carry_prefix_extend`

Extends a carry prefix by one separately supplied terminal carry.  Public tags
begin with `b5ccpe`.

```text
(beta_prefix_extend, finite_lt_succ_eq_or_lt)
```

### 3.3 `double_quotient_carry_prefix_exists`

Builds carry codes for two quotient prefixes of the same length.  Public tags
begin with `b5ccpx`.

```text
(add_eq_zero_right, succ_ne_zero, le_succ, le_refl,
 double_quotient_carry_choice, double_quotient_carry_prefix_extend)
```

### 3.4 `double_quotient_carry_prefix_all_bits`

Every decoded carry value is zero or one.  Public tags begin with `b5ccpab`.
Direct dependencies: `()`.

### 3.5 `double_quotient_carry_prefix_restrict`

Drops the terminal position of a successor-length carry prefix.  Public tags
begin with `b5ccpr`.

```text
(le_succ)
```

### 3.6 `bit_count_positive_last_one`

```text
BitCount(B,S,l,S(e)) ->
exists i. LT(i,l) /\ BetaAt(B,S,i,1) /\ LE(S(e),S(i)).
```

Public tags begin with `b5ccbclo`.  Direct dependencies:

```text
(bit_count_zero, bit_count_succ_decompose, bit_count_bounded,
 le_succ, le_refl)
```

### 3.7 `division_successor_quotient_divisor_le`

```text
DivRem(d,n,S(q),r) -> LE(d,n).
```

Public tags begin with `b5ccsqdl`.  Direct dependencies:

```text
(add_assoc, add_comm)
```

### 3.8 `beta_sum_double_carry_exact`

```text
Sum(B,S,l,left) -> Sum(D,T,l,right) -> CarryPrefix(...) ->
BitCount(F,G,l,e) -> right=(left+left)+e.
```

Public tags begin with `b5ccsdce`.  Direct dependencies:

```text
(beta_sum_zero, beta_sum_succ_decompose, bit_count_zero,
 bit_count_succ_decompose, beta_at_unique, le_refl,
 double_quotient_carry_prefix_restrict, add_assoc,
 add_permute_outer, add_comm)
```

### 3.9 `central_binom_carry_bit_count`

```text
Prime(p) -> CentralBinom(n,C) -> PowerVal(p,C,v) ->
exists B S D T F G.
  PowerQuotientPrefix(p,n,B,S,n+n) /\
  PowerQuotientPrefix(p,n+n,D,T,n+n) /\
  CarryPrefix(B,S,D,T,F,G,n+n) /\ BitCount(F,G,n+n,v).
```

Public tags begin with `b5cccbbc`.  Direct dependencies:

```text
(prime_legendre_sum_exists, central_binom_legendre_valuation_balance,
 legendre_sum_extended_prefix_exists,
 double_quotient_carry_prefix_exists,
 double_quotient_carry_prefix_all_bits, bit_count_exists,
 beta_sum_double_carry_exact, add_left_cancel)
```

### 3.10 `central_binom_prime_power_contribution_le_double`

```text
forall p n C v D.
  Prime(p) -> LE(1,n) -> CentralBinom(n,C) -> PowerVal(p,C,v) ->
  Pow(p,v,D) -> LE(D,n+n).
```

Public tags begin with `b5ccppcld`.  Direct dependencies:

```text
(pow_zero, le_add_right, le_trans, prime_nonzero, one_le_of_ne_zero,
 beta_at_unique, pow_le_pow_of_exponent_le,
 bit_count_positive_last_one, division_successor_quotient_divisor_le,
 central_binom_carry_bit_count)
```

The zero-exponent branch uses `Pow(p,0,D)` and `LE(1,n)`.  The successor
branch obtains a one-valued carry at an index `i >= v`, aligns the doubled
quotient by beta uniqueness, bounds `p^(i+1)` by `n+n` from its successor
quotient, and applies relational power monotonicity.  It does not use the
induction hypothesis and does not rewrite a whole relation.

## 4. Proof topology and resource policy

The exact dependency and command-count vectors are:

```text
dependencies = (2, 2, 6, 0, 1, 5, 2, 10, 8, 10)
commands     = (72, 71, 73, 30, 16, 69, 21, 174, 116, 149)
```

All 46 dependency edges are live.  The focused harness must reject each
dependency removal, every false target, and every declared semantic mutation.
It must kernel-check bounded dependency-curried bodies and root-pruned,
empty-context `LayeredReplay` closures, reject DNE, assert the exact direct-Cut
count, corrupt every layer Cut, and reject each corruption before accepting a
receipt.

Because a retained multirow replay previously caused severe memory pressure,
every body and closure root is run in a fresh Python subprocess with
`PYTHONMALLOC=malloc`.  No process may retain multiple growing carry DAGs.
The unchanged closure caps are:

```text
occurrence nodes <= 500000
distinct objects <= 100000
proof depth <= 256
annotations <= 5000000
```

The proof core is Stable checked-use authority plus exact recursively rebuilt
Alpha-v11 support, the B5 order/quotient and central-valuation candidates, and
only the earlier local prefix of this source.  Alpha membership is never
logical authority.  This module must remain absent from Stable, Alpha,
enrollment manifests, and edition registries.

## 5. Genuine mutations

Each row requires one independently rebuilt mutation in addition to its false
target.  The binding changes are:

1. erase the successor alternative in `CarryChoice`; divisor two at dividend
   one supplies the missing odd doubled quotient;
2. demand a two-position extension from one supplied terminal carry;
3. demand a successor-length carry prefix from quotient prefixes known only
   through length `l`;
4. strengthen every stored bit to zero; an odd doubled quotient has bit one;
5. strengthen the restricted length from `l` to `S(S(l))`;
6. strengthen `LE(S(e),S(i))` to `LE(S(S(e)),S(i))`; a singleton one has
   count one at index zero;
7. strengthen `LE(d,n)` to `LE(S(d),n)`; use quotient one with `d=n`;
8. replace the exact result by `right=(left+left)+S(e)`; use empty sums;
9. replace the final bit count `v` by `S(v)`; use the central base case;
10. strengthen the public result to `LE(S(D),n+n)`; use
    `p=2,n=1,C=2,v=1,D=2`.

Binder renaming, reassociation, commutation, tag changes, or an alpha-equivalent
relation expansion is not a genuine mutation.

## 6. Release policy and next step

Passing this RFC creates candidate body and empty-context evidence only.
Stable and Alpha remain unchanged.  A later additive Alpha may enroll these
rows as `body_checked`, `checked_use=False`; checked use requires a separate
dependency-closed cold-closure promotion.

The next B5 tranche should combine this complete-contribution bound with the
already checked square-tail theorem to prove exponent at most one above
`sqrt(n+n)`, then prove zero contribution on `2n/3 < p <= n`.  Those results
feed the filtered-product five-range upper bound; none is claimed here.
