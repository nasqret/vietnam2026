# HA Bertrand B5 Square-Tail Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-16

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`52e676f1b92f1ca2b134984586c85aacba49d055`.

Edition parent: Alpha v11, frozen by:

- 1,123 Alpha rows, 3,482 dependency edges, and 45 layers;
- enrollment identity
  `c9f6f4015e8e3e5aaeee803706113c85098551276ea3eb01039ade7bd97b1a36`;
- edition identity
  `46d07832b0c630b9ce1da1d6e639687347cd737774b2b88b923bc5f477b9ddc3`;
- `editions_v11.py` SHA-256
  `10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

The immediately preceding complete-contribution tranche is pinned by:

- source SHA-256
  `a480ca001ad0837c2ae45315bd5520c666d5e716a34c72ec5f5fcc0d7601c0f0`;
- focused-test SHA-256
  `2189efe66e32bd3631041cc79a98f8a58060e828a175ce8829731b65947ce3ee`;
- subordinate-RFC SHA-256
  `a9074118af3e2077b95305a7de7c2a25837bcf56999f44e7e7bc5b48eb144974`.

## 1. Scope

This two-row tranche proves the large-prime exponent bound required by B5.
It combines the checked complete contribution bound

```text
Pow(p,v,D) -> LE(D,n+n)
```

with monotonicity of relational powers.  If `Pow(p,2,s)` and `n+n<s`, then
an exponent `v>=2` would force `n+n<D`, contradicting the contribution
bound.  Discrete total order then gives `v<=1`.

The public result is:

```text
Prime(p) -> LE(1,n) -> CentralBinom(n,C) -> PowerVal(p,C,v) ->
Pow(p,2,s) -> LT(n+n,s) -> LE(v,1).
```

The complete contribution value is intentionally existential and does not
appear in the public surface.  This tranche does not claim zero valuation on
`2n/3<p<=n`, the no-Bertrand upper interval, or either five-range capstone.

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/
  bertrand_central_binom_square_tail_candidate.py
b07163c977af5bbbf4f84aaec3629c9c58c06e8acc7fed476134e980aec7a9ff
```

The focused-test seal is populated only after all fail-closed receipts are
measured.  Source, test, and receipt seals are evidence, not theorem authority.

## 2. Representation contract

`Prime`, `LE`, `LT`, `CentralBinom`, `PowerVal`, and `Pow` are authoring
abbreviations only.  Every occurrence must be fully and capture-safely
expanded before parsing.  The square remains the relational premise
`Pow(p,2,s)`; neither exponentiation nor square root is introduced as a
function.

The proof may obtain `exists D. Pow(p,v,D)` directly from `pow_exists`, but
may not expose `D` in the public conclusion.  It may not rewrite an entire
central-binomial, valuation, or power relation.  All transports are confined
to small order goals, and this tranche uses no equality transport at all.

## 3. Rows and dependencies

The following order is binding and dependency-topological.

### 3.1 `central_binom_prime_square_tail_exponent_not_two_le`

```text
forall p n C v s.
  Prime(p) -> LE(1,n) -> CentralBinom(n,C) -> PowerVal(p,C,v) ->
  Pow(p,2,s) -> LT(n+n,s) -> ~(LE(2,v))
```

Public tags are:

```text
bcpsten_prime
bcpsten_positive
bcpsten_central
bcpsten_valuation
bcpsten_square
bcpsten_strict
bcpsten_exponent
```

Direct dependencies, in first-use order:

```text
(pow_exists, prime_nonzero, one_le_of_ne_zero,
 pow_tail_strict_of_square,
 central_binom_prime_power_contribution_le_double, lt_not_le)
```

The proof obtains one complete-power witness.  Primality supplies `1<=p`.
Assuming `2<=v`, `pow_tail_strict_of_square` gives `n+n<D`; the complete
contribution theorem gives `D<=n+n`; `lt_not_le` closes the contradiction.

### 3.2 `central_binom_prime_square_tail_valuation_le_one`

```text
forall p n C v s.
  Prime(p) -> LE(1,n) -> CentralBinom(n,C) -> PowerVal(p,C,v) ->
  Pow(p,2,s) -> LT(n+n,s) -> LE(v,1)
```

Public tags are:

```text
bcpstvlo_prime
bcpstvlo_positive
bcpstvlo_central
bcpstvlo_valuation
bcpstvlo_square
bcpstvlo_strict
bcpstvlo_result
```

Direct dependencies:

```text
(le_or_lt, central_binom_prime_square_tail_exponent_not_two_le)
```

`le_or_lt v 1` gives either the result or `1<v`.  The second branch is the
expanded Peano relation `2<=v`, rejected by the first row.  No classical
double-negation elimination is permitted.

## 4. Proof-topology and authority requirements

The focused harness must freeze:

- exact statements, public tags, dependency order, and scripts;
- 56 commands in row 1 and 31 commands in row 2;
- one direct `pow_exists` witness elimination in row 1;
- one `le_or_lt` split in row 2;
- zero induction commands and zero whole-relation rewrites;
- direct dependency counts `(6,2)` and all eight edge-removal failures;
- rejection of a false target and a genuine mutation for each row;
- kernel checking, bounded envelopes, live resource caps, and no-DNE gates;
- fresh-process empty-context closure and exhaustive replay-layer Cut corruption
  before accepting any closure receipt.

Authority is Stable plus the exact dependency-closed Alpha-v11/candidate
prefix needed to rebuild the order, valuation, and carry providers.  Neither
new row may occur in Stable, Alpha v11, an edition registry, or the core used
to validate its own body.  The second row may see the first row only as its
local prefix.

Because the earlier crash was cumulative proof-DAG retention, each body,
rejection, and closure root must run in a fresh subprocess with
`PYTHONMALLOC=malloc`.  A monolithic growing-root run is not release evidence.

## 5. Genuine mutations

Each row requires one independently rebuilt semantic mutation:

1. strengthen the excluded bound from `~LE(2,v)` to `~LE(1,v)`;
2. strengthen the final bound from `LE(v,1)` to `LE(S v,1)`.

Both are refuted by the standard fixture

```text
p=2, n=1, C=2, v=1, s=4.
```

Here 2 is prime, `CentralBinom(1,2)`, `PowerVal(2,2,1)`, `Pow(2,2,4)`,
and `2<4`, while `~LE(1,1)` and `LE(2,1)` are false.  Binder renaming, tag
changes, reassociation, or alpha-equivalent relation spelling is not a
genuine mutation.

## 6. Release policy and next step

Passing this RFC creates candidate body and empty-context evidence only.
Stable and Alpha remain unchanged.  A later additive Alpha may enroll both
rows as `body_checked`, `checked_use=False`; checked use requires a separate
dependency-closed cold-closure promotion.

The next B5 tranche should prove zero contribution for primes in
`2n/3<p<=n`, using the checked Legendre quotient formula.  That row and the
already checked no-Bertrand exclusion above `n` feed the explicit five-range
filtered-product upper bound.
