# HA Bertrand B5 Factor Ranges Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-17

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`33ab3f4ad371a40fa257818d9faf07beb413b663`.

Edition parent: Alpha v11, frozen by 1,123 rows, 3,482 edges, 45 layers,
and `editions_v11.py` SHA-256
`10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

The immediately preceding zero-range tranche is pinned by source
`8ad4f3c5b90832dddc28d94f2b82f21eb47e8bd1e3f059696bbfa6e2b5c11b4e`,
test `6d35906e4fe9a0550a60c36a45aa5f3a97c6e94a1339cd72aa336faaead782a3`,
and RFC `9b920ae8f646fb3b460a352ac82c332d4cd23e3d7bbe4e6fa9ba74e17c1696fc`.

## 1. Scope

This eight-row tranche converts the quotient and floor-square-root boundaries
of B5 into pointwise bounds on complete prime-power contributions.  Its public
endpoint says that, under the no-Bertrand assumption, every relational power
selected by the central valuation has one of exactly three reviewed forms:

```text
(LE(p,s) /\ LE(a,n+n)) \/
((LT(s,p) /\ LE(p,q)) /\ a=p) \/
a=1.
```

Here `FloorSqrt(n+n,s)`, `DivRem(3,n+n,q,r)`, `Prime(p)`,
`CentralBinom(n,C)`, `PowerVal(p,C,v)`, and `Pow(p,v,a)` are explicit
premises.  Thus a later beta-product client may compare small contributions
with a uniform `n+n` prefix, middle contributions with a duplicate-free
prime product through `q`, and every excluded contribution with one.

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_central_binom_factor_ranges_candidate.py
d03e4f7fb9a0f8f4de8db3022eb867cc600f4ec4f1a3050e3d9e35432ab4a8ae
```

## 2. Representation contract

`Prime`, `LE`, `LT`, `DivRem`, `FloorSqrt`, `CentralBinom`, `PowerVal`,
and `Pow` are authoring abbreviations only.  Every occurrence is fully
expanded before parsing.  No row may use raw beta-code equality, DNE,
classical choice, a whole `CentralBinom` or `PowerVal` rewrite, or an opaque
five-range arithmetic assertion.

Rows 1 and 3 transport only small order formulas.  Rows 2 and 4 apply the
already checked zero-range and square-tail results.  Rows 5 through 8 must
retain the visible small, middle, and neutral branches; collapsing those
branches into an unproved product estimate is forbidden.

## 3. Binding rows and dependencies

The row order is dependency-topological and binding.

### 3.1 `division_three_scaled_upper_of_quotient_lt`

```text
forall n q r p. DivRem(3,n+n,q,r) -> LT(q,p) -> LT(n+n,(p+p)+p)
```

Tags: `bdtsuql_division`, `bdtsuql_quotient`, `bdtsuql_result`.

Dependencies:

```text
(division_block_upper, mul_le_mul_left, lt_of_lt_of_le,
 mul_succ_left, one_mul)
```

The canonical remainder bound gives `n+n < 3*S q`; scaling `S q<=p`
gives `3*S q<=3*p`, and only the final small equality rewrites `3*p` as
`(p+p)+p`.

### 3.2 `central_binom_prime_valuation_zero_above_third_quotient`

```text
forall p n C v q r.
Prime(p) -> LT(2,n) -> DivRem(3,n+n,q,r) -> LT(q,p) -> LE(p,n) ->
CentralBinom(n,C) -> PowerVal(p,C,v) -> v=0
```

Tags start with `bcpvzatq_` and are exact in the frozen source.

Dependencies:

```text
(division_three_scaled_upper_of_quotient_lt,
 central_binom_prime_valuation_zero_two_thirds_range)
```

### 3.3 `floor_sqrt_above_root_power_two_strict`

```text
forall x s p t.
FloorSqrt(x,s) -> LT(s,p) -> Pow(p,2,t) -> LT(x,t)
```

Tags start with `bfsarpts_`.

Dependencies:

```text
(mul_le_mul_right, mul_le_mul_left, le_trans, lt_of_lt_of_le, pow_two)
```

The proof composes `(S s)^2<=p*(S s)<=p^2` with the strict upper half of
`FloorSqrt` and then identifies the relational square using `pow_two`.

### 3.4 `central_binom_prime_above_floor_sqrt_valuation_le_one`

```text
forall p n C v s.
Prime(p) -> LT(2,n) -> CentralBinom(n,C) -> PowerVal(p,C,v) ->
FloorSqrt(n+n,s) -> LT(s,p) -> LE(v,1)
```

Tags start with `bcpafs_vlo_`.

Dependencies:

```text
(lt_to_le, le_trans, pow_exists,
 floor_sqrt_above_root_power_two_strict,
 central_binom_prime_square_tail_valuation_le_one)
```

### 3.5 `no_bertrand_central_nonzero_valuation_live_ranges`

With binders `n s q r C p v`, the premises are:

```text
NoBertrandClosed(n) -> Prime(p) -> LT(2,n) -> DivRem(3,n+n,q,r) ->
CentralBinom(n,C) -> PowerVal(p,C,v) -> ~(v=0).
```

The conclusion is:

```text
LE(p,s) \/ (LT(s,p) /\ LE(p,q)).
```

Tags start with `bnbcnvlr_`.

Dependencies:

```text
(power_valuation_nonzero_exponent_divides_base,
 no_bertrand_central_prime_divisor_ranges,
 central_binom_prime_valuation_zero_above_third_quotient)
```

The nonzero valuation supplies divisibility.  The checked divisor classifier
exposes three ranges; row 2 contradicts the third one.

### 3.6 `no_bertrand_central_nonzero_valuation_factor_ranges`

This row adds `FloorSqrt(n+n,s)` to row 5's premises and concludes:

```text
LE(p,s) \/ ((LT(s,p) /\ LE(p,q)) /\ v=1).
```

Tags reuse the public range occurrences from row 5 and use the exact
`bnbcnvfr_` private tags in the source.

Dependencies:

```text
(no_bertrand_central_nonzero_valuation_live_ranges,
 central_binom_prime_above_floor_sqrt_valuation_le_one,
 one_le_of_ne_zero, le_antisymm)
```

### 3.7 `no_bertrand_central_nonzero_contribution_factor_ranges`

This row adds `Pow(p,v,a)` and retains `~(v=0)`.  Its conclusion is:

```text
(LE(p,s) /\ LE(a,n+n)) \/
((LT(s,p) /\ LE(p,q)) /\ a=p).
```

Tags start with `bnbcncfr_`, with the shared public range tags frozen in the
source.

Dependencies:

```text
(no_bertrand_central_nonzero_valuation_factor_ranges,
 lt_to_le, le_trans, central_binom_prime_power_contribution_le_double,
 pow_one)
```

### 3.8 `no_bertrand_central_prime_contribution_ranges`

This is the public endpoint from Section 1.  It removes the nonzero-exponent
premise and adds the final neutral disjunct `a=1`.

Dependencies:

```text
(eq_decidable, pow_zero,
 no_bertrand_central_nonzero_contribution_factor_ranges)
```

## 4. Fail-closed evidence

The focused harness must independently rebuild all public formulas and freeze
exact scripts, dependency order, artifact receipts, body receipts, bounded
envelopes, and empty-context layered closures.  Direct dependency counts are
`(5,2,5,5,3,4,5,3)`, totaling 32 live edges.  Every dependency removal,
false target, and one genuine semantic mutation per row must fail body replay.
Every closure must kernel-check, remain below the unchanged occurrence,
object, depth, envelope, and annotation caps, contain no DNE, and reject
corruption of every direct replay-layer Cut before receipt acceptance.

Large roots run one at a time in fresh subprocesses with
`PYTHONMALLOC=malloc`.  Retaining several expanded closure DAGs in one Python
process is not valid evidence.

## 5. Genuine mutations

The harness uses these non-equivalent mutations:

1. replace the final `3*p` bound by `2*p`; use `n=4,q=2,r=2,p=3`;
2. replace `v=0` by `v=1`; use `p=3,n=4,C=70,v=0,q=2,r=2`;
3. reverse the strict square result; use `x=8,s=2,p=3,t=9`;
4. replace `LE(v,1)` by `v=0`; use `n=5,C=252,p=7,v=1,s=3`;
5. through 8. replace `NoBertrandClosed(n)` by truth and use
   `n=5,C=252,p=7,v=1,a=7,s=q=3,r=1`.

The last four mutations are false precisely because the prime `7` in
`(5,10]` is no longer excluded.  Binder renaming, tag changes, reassociation,
or commutation is not a genuine mutation.

## 6. Authority and next step

Passing this tranche creates candidate body and empty-context evidence only.
Stable and Alpha v11 remain unchanged.  Authority is Stable plus the exact
dependency-closed Alpha-v11/post-v11 candidate prefix and preceding local
rows.

The next tranche should construct an extensional beta prefix of these complete
prime-power contributions, split it at `s` and `q`, and compare the three
pieces with `(n+n)^s`, `Primorial(q)`, and one.  The reconstruction of `C`
from its prime valuations remains an explicit theorem obligation; it may not
be replaced by raw-code identity.
