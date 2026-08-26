# HA Bertrand B5 Range-Boundary Support Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-17

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`b95566f416d2a5cafdcf8e1d99c6883b62201b9b`.

Edition parent: Alpha v11, frozen by 1,123 rows, 3,482 edges, 45 layers,
and `editions_v11.py` SHA-256
`10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_b5_range_boundaries_candidate.py
767e574d2e93639e967b9cd497de83a80a266a051a7315990d0d9bd27613e95e
```

Its executed relation helpers are pinned by:

```text
bertrand_choose_foundation_candidate.py
97307689cedbb28c13dd296ac47d86f052e947ef1cf18f7c9a6f2cf27499c17d

bertrand_ceil_sqrt_candidate.py
745db5174c6f9348ec97fc6076a909f1dd98e04e899e5a26ebd38b61b842b237

bertrand_b5_order_quotient_candidate.py
4a307f03a5f832db2470cf27e2958902ac203aa7e1263138432f47df72e81f6e
```

The focused-test seal remains pending until all fail-closed receipts are
measured.  Hashes and receipts are evidence only and grant no theorem
authority.

## 1. Scope

This ten-row tranche establishes the constructive ordering of the two B5
cut points

```text
s = floor(sqrt(n+n))
q = floor((n+n)/3).
```

For `2<n`, it proves `s<=q`, `q<=n+n`, and packages exact additive gaps

```text
exists g h. s+g=q /\ q+h=n+n.
```

These gaps are the checked indices required by the next finite-product
prefix/suffix split.  This tranche does not split a Product, define a
division or square-root function, prove a contribution bound, or claim the
five-range central-binomial upper estimate.

## 2. Representation contract

All readable relations below are authoring abbreviations expanded before
parsing.  No new kernel symbol is introduced.

```text
LE(a,b) := exists g. g+a=b
LT(a,b) := exists g. g+S a=b

DivRem(d,N,q,r) := N=d*q+r /\ LT(r,d)

FloorSqrt(N,s) := LE(s*s,N) /\ LT(N,S s*S s)
```

The exact `FloorSqrt` and `DivRem` expansions are delegated to the pinned
helpers.  Generated binders must be collision-checked against the complete
public and local context.  Compound terms are parsed in that context and
canonically rendered before expansion.

No row may use DNE, a division function, a square-root function, raw beta
codes, arbitrary provider discovery, or a whole-relation rewrite of
`FloorSqrt` or `DivRem`.

## 3. Binding rows, tags, and dependencies

The order below is dependency-topological and binding.

### 3.1 `two_lt_double_lower_six`

```text
forall n. LT(2,n) -> LE(3+3,n+n)
```

Public tags are `b5rbtdls_positive` and `b5rbtdls_result`.
Private proof tags are `b5rbtdls_left` and `b5rbtdls_right`.

Dependencies, in order:

```text
(add_le_add_right, add_le_add_left, le_trans)
```

The proof reads `LT(2,n)` as `3<=n`, adds the bound on each side, and
composes the two weak inequalities.

### 3.2 `floor_sqrt_two_le_of_two_lt`

```text
forall n s. LT(2,n) -> FloorSqrt(n+n,s) -> LE(2,s)
```

Public tags are `b5rbfstl_positive`, `b5rbfstl_floor`, and
`b5rbfstl_result`.  Other `b5rbfstl_*` tags are private proof formulas.

Dependencies:

```text
(le_or_lt, le_refl, le_succ, lt_of_lt_of_le, lt_three_cases,
 floor_sqrt_strict_upper_bound, two_lt_double_lower_six, le_trans,
 lt_not_le, lt_irrefl_expanded)
```

The reverse case `s<2` is strengthened to `s<3`, classified as
`s=0`, `s=1`, or `s=2`, and contradicted against the strict floor upper
bound and row 1.  The three-way disjunction is eliminated in its parsed
left-associated shape.

### 3.3 `three_mul_le_square_of_three_le`

```text
forall s. LE(3,s) -> LE(3*s,s*s)
```

Tags are `b5rbtmsts_source` and `b5rbtmsts_result`.

Dependencies:

```text
(mul_le_mul_right)
```

### 3.4 `floor_sqrt_three_mul_le_double`

```text
forall n s.
  LT(2,n) -> FloorSqrt(n+n,s) -> LE(3*s,n+n)
```

Public tags are `b5rbfstmd_positive`, `b5rbfstmd_floor`, and
`b5rbfstmd_result`; the other `b5rbfstmd_*` tags are private.

Dependencies:

```text
(two_lt_double_lower_six, floor_sqrt_two_le_of_two_lt,
 three_mul_le_square_of_three_le, le_eq_or_lt,
 floor_sqrt_lower_bound, le_trans)
```

The equality case `s=2` uses row 1 and the small checked equality
`3*2=3+3`.  In the strict case, `3<=s`, so row 3 and the floor lower
bound compose to the result.

### 3.5 `division_quotient_lower_of_scaled_le`

```text
forall d N q r s.
  DivRem(d,N,q,r) -> LE(d*s,N) -> LE(s,q)
```

Public tags are `b5rbdqlosl_division`, `b5rbdqlosl_scaled`, and
`b5rbdqlosl_result`; the remaining `b5rbdqlosl_*` tags are private.

Dependencies:

```text
(division_block_upper, le_or_lt, mul_le_mul_left,
 lt_of_lt_of_le, lt_not_le)
```

If `q<s`, the quotient block bound gives `N<d*S q`; multiplication
monotonicity gives `d*S q<=d*s`, contradicting `d*s<=N`.

### 3.6 `floor_sqrt_le_third_quotient`

```text
forall n s q r.
  LT(2,n) -> FloorSqrt(n+n,s) -> DivRem(3,n+n,q,r) -> LE(s,q)
```

Tags are `b5rbfsltq_positive`, `b5rbfsltq_floor`,
`b5rbfsltq_division`, and `b5rbfsltq_result`.

Dependencies:

```text
(floor_sqrt_three_mul_le_double,
 division_quotient_lower_of_scaled_le)
```

### 3.7 `floor_sqrt_third_quotient_gap_exists`

```text
forall n s q r.
  LT(2,n) -> FloorSqrt(n+n,s) -> DivRem(3,n+n,q,r) ->
  exists g. s+g=q
```

The premise tags are the row-6 tags.  The existential conclusion contains
no generated relation binder.

Dependencies:

```text
(add_comm, floor_sqrt_le_third_quotient)
```

### 3.8 `division_quotient_le_dividend`

```text
forall n q r. DivRem(3,n+n,q,r) -> LE(q,n+n)
```

Public tags are `b5rbdqld_division` and `b5rbdqld_result`; the other
`b5rbdqld_*` tags are private.

Dependencies:

```text
(le_mul_of_one_le_left, le_add_right, le_trans)
```

The proof composes `q<=3*q` and `3*q<=3*q+r`, then transports only the
small outer equality from the division record.

### 3.9 `third_quotient_double_gap_exists`

```text
forall n q r.
  DivRem(3,n+n,q,r) -> exists h. q+h=n+n
```

The public division tag is `b5rbdqld_division`.

Dependencies:

```text
(add_comm, division_quotient_le_dividend)
```

### 3.10 `floor_third_double_gap_package`

```text
forall n s q r.
  LT(2,n) -> FloorSqrt(n+n,s) -> DivRem(3,n+n,q,r) ->
  exists g h. s+g=q /\ q+h=n+n
```

The public premise tags are `b5rbfsltq_positive`, `b5rbfsltq_floor`, and
`b5rbfsltq_division`.

Dependencies:

```text
(floor_sqrt_third_quotient_gap_exists,
 third_quotient_double_gap_exists)
```

Both existential packages must be obtained from direct theorem
applications and eliminated separately before the final pair is built.

## 4. Dependency and proof-topology contract

The direct dependency/Cut vector is binding:

```text
(3, 10, 1, 6, 5, 2, 2, 3, 2, 2)
```

There are 36 live direct edges.  Every edge must be removed independently
and the shortened body must fail replay.  Every direct Cut in every closed
certificate must be proposition-and-lemma corrupted independently and
rejected by the kernel before receipt comparison.

The focused harness must additionally freeze:

1. the exact ten statements, scripts, tags, row order, and dependency order;
2. exact source, helper, Alpha-v11, campaign-RFC, and tranche-RFC hashes;
3. Stable plus the exact Alpha-v11 dependency catalog as the only external
   authority, with preceding local rows added only by row prefix;
4. body kernel checking, bounded proof envelopes, live resource caps, and
   absence of DNE before body receipts are accepted;
5. recursively closed empty-context certificates, the same resource gates,
   exact direct-Cut counts, and exhaustive corruption before closure
   receipts are accepted;
6. explicit rejection of Alpha/Stable/provider enrollment for these rows.

No receipt value may remain `None` at release.

## 5. Genuine mutations and counterfixtures

The focused test must reject at least these one-surface mutations:

1. row 1 strengthens `LE(3+3,n+n)` to `LE(7,n+n)`; use `n=3`;
2. row 2 strengthens `LE(2,s)` to `LE(3,s)`; use `n=3,s=2`;
3. row 3 changes `3*s` to `4*s`; use `s=3`;
4. row 4 changes `3*s` to `4*s`; use `n=3,s=2`;
5. row 5 strengthens the result to `LE(S s,q)`; use
   `d=3,N=6,q=2,r=0,s=2`;
6. row 6 strengthens the result to `LE(S s,q)`; use
   `n=3,s=2,q=2,r=0`;
7. row 7 changes the gap equation to `S s+g=q`; use the same fixture;
8. row 8 strengthens the result to `LE(S q,n+n)`; use `n=q=r=0`;
9. row 9 changes the gap equation to `S q+h=n+n`; use `n=q=r=0`;
10. row 10 changes its first gap to `S s+g=q`; use
    `n=3,s=2,q=2,r=0`.

Commuting a gap equation or changing only private expansion tags is not a
genuine mutation.

## 6. Capacity and execution policy

Body replay is cheap and may run as one focused selector.  Recursive closure
workers must run serially and attached, with `PYTHONMALLOC=malloc`; no two
closure workers may overlap.  Polling intervals must remain short enough to
observe memory growth and terminate an accidental duplicate worker.

Default layered-replay caps remain unchanged.  No cap may be raised merely
to admit this tranche.  Source and test files must have no line longer than
88 columns and must pass `git diff --check`.

## 7. Release boundary

Passing focused evidence permits a candidate commit only.  It does not alter
Stable, Alpha v11, edition catalogs, checked-use status, or runtime provider
lookup.  Enrollment requires a later additive edition release with its own
immutable parent, evidence bundle, mutation audit, and channel seals.

The next B5 tranche may consume row 10 to drive two checked Product splits:
first at `s`, then at `q`.  It must still prove the pointwise contribution
bounds for the resulting intervals and may not infer them from this arithmetic
package alone.
