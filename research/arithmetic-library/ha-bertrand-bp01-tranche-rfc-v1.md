# HA Bertrand BP01 Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-17

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`d5cfb82d1557817224cc5947e85b987ac92e6e09`.

Edition parent: Alpha v11, frozen by 1,123 rows, 3,482 edges, 45 layers,
and `editions_v11.py` SHA-256
`10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

Logical evidence parents:

```text
peano-lab/py/peano_lab/library/bertrand_b7_eventual_candidate.py
6be00fab2b46ecc787b9f7f4a25f4f552a1021a20c62f5895c6047c74744d50b

peano-lab/py/peano_lab/library/bertrand_b8_small_candidate.py
2886dc0bc4ac85667ec5223ed0074794ff66f828e34e7dbd2791757d141702b0
```

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/bertrand_bp01_candidate.py
30e31d66c4160fb91df9b846ae58010e4eeb7618506431058d440336e32afad7
```

The focused-test byte seal remains pending until every accepted receipt is
populated. Hashes and receipts are evidence only and grant no authority.

## 1. Scope

This one-row tranche proves the primary frozen Bertrand endpoint
`bertrand_closed_upper`. It constructively splits each nonzero input at the
factorized cutoff. The weak large-input branch invokes B7; the strict
small-input branch invokes the checked native B8 finite-cover theorem.

This tranche does not yet exclude equality at the right endpoint, prove
BP02, change theorem authority, or enroll either dependency for checked use.

## 2. Exact public statement

The candidate statement is the exact frozen base-language source from the
parent campaign, not merely an alpha-equivalent helper expansion:

```text
forall n. ~(n = 0) -> exists p.
  ((~(p = 1) /\ forall a b. p = a * b -> a = 1 \/ b = 1) /\
  ((exists u. u + S n = p) /\ (exists v. v + p = n + n)))
```

Removing the two displayed formatting line breaks and indentation gives the
exact one-line source. Its exact source SHA-256 is
`7131d5cb2f6264600646df6ae949e9bb2b69a927458ce5b39682e9e284f9ad2c`.
The defined presentation remains exactly:

```text
forall n. ~(n = 0) -> exists p.
  Prime(p) /\ (Lt(n,p) /\ Le(p,n + n))
```

Public spelling preserves `n + n`. It may not be changed to `2 * n` even
though the two terms are provably equal. The proof cutoff remains exactly
`16 * 32`; neither unary 512 nor `32 * 16` is accepted.

## 3. Binding row and dependencies

The sole row is `bertrand_closed_upper`. Its direct dependencies, in exact
first-use order, are:

```text
le_or_lt
bertrand_eventually_closed_upper
bertrand_small_closed_upper
```

The direct-Cut count is 3. Every edge is live.

## 4. Binding proof topology

The exact twelve commands are:

```text
intro n
intro hnonzero
specialize le_or_lt (16 * 32)
specialize le_or_lt n
cases le_or_lt
specialize bertrand_eventually_closed_upper n
apply bertrand_eventually_closed_upper
exact le_or_lt_left
specialize bertrand_small_closed_upper n
apply bertrand_small_closed_upper
exact hnonzero
exact le_or_lt_right
```

The split is constructive. `le_or_lt (16*32) n` yields either the weak B7
threshold `Le(16*32,n)` or the strict B8 bound `Lt(n,16*32)`. No arithmetic
transport, relation-wide rewrite, classical choice, DNE, or host search is
permitted.

## 5. Fail-closed evidence and capacity

The focused audit must independently freeze the exact statement, script,
dependency order, source pins, body receipt, bounded envelope, liveness,
false target, genuine mutations, and direct-Cut corruption.

The complete dependency closure must ultimately be an ordinary certificate
accepted by the unchanged intuitionistic kernel from the empty context. The
existing B7 layered receipt is 499,202 proof occurrences, so blindly nesting
the independently closed B7 and small-range certificates is forbidden: it
would exceed the unchanged 500,000-occurrence policy cap. No cap increase,
receipt substitution, registry lookup, Alpha membership, or assumed theorem
leaf is authorized.

The closure audit must therefore use a reviewed root-pruned layered lineage
whose candidate remains under all default limits. If the first shared graph
does not fit, the response is to compact or rebalance the lineage and refreeze
its exact topology. Until that succeeds, the row may carry only fail-closed
`body_checked` or `pending_layered_closure` evidence and is unavailable for
checked use.

The accepted lineage recursively rebuilds every reachable Stable theorem
body from its exact declared dependencies instead of inserting already-closed
Stable certificates as atomic leaves. This is proof reconstruction, not an
authority upgrade: every rebuilt dependency-curried body and the final
certificate are checked by the unchanged kernel. The frozen graph has:

```text
544 nodes
202 rebuilt Stable bodies
342 candidate bodies
0 atomic Stable certificates
1,913 dependency edges
44 layers / 44 checked layer Cuts
```

Its empty-context certificate has 201,187 proof occurrences, depth 235,
45,334 proof objects, 58,587 proof edges, 13,254 reused references,
1,318,798 annotation occurrences, and envelope depth 244. Thus it retains
298,813 occurrences of headroom under the unchanged 500,000 cap. The exact
topology and proof DAG digests are frozen by the focused test.

## 6. Genuine mutations

At minimum the audit must reject:

1. replacing `~(n=0)` by `n=0`, witnessed by `n=0`;
2. strengthening the result upper bound to `Le(p,n)`, witnessed by `n=1`;
3. strengthening the lower bound to `Lt(S n,p)`, witnessed by `n=1`; and
4. conjoining the exact statement with `false`.

The audit must also reject proof-topology mutations that use unary 512,
`32 * 16`, reverse the cutoff split, or remove either branch dependency.
Changing `n+n` to `2*n` is an exact-source contract mutation, not a semantic
counterexample.

## 7. Release boundary

Acceptance of the source/body tranche authorizes only this candidate source,
its focused fail-closed test, and this RFC. The theorem is not public or
available for checked use until its complete empty-context layered closure is
sealed under the unchanged resource policy.

The next mathematical tranche is the endpoint-factorization boundary and
BP02 `bertrand_strict`. Those rows may be authored against the exact BP01
body, but no later checked-use release may treat BP01 as authority while its
closure evidence is pending.
