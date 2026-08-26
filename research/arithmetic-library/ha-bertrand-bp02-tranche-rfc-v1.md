# HA Bertrand BP02 Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-17

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`476060b` (`Prove the closed-upper Bertrand capstone`).

Edition parent: Alpha v11, frozen by 1,123 rows, 3,482 edges, 45 layers,
and `editions_v11.py` SHA-256
`10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

BP01 evidence parent:

```text
peano-lab/py/peano_lab/library/bertrand_bp01_candidate.py
30e31d66c4160fb91df9b846ae58010e4eeb7618506431058d440336e32afad7

peano-lab/py/tests/test_bertrand_bp01_candidate.py
bea3edced4394777f2711ffb1dfbf7f6d8652e5704279b03524e9101a69a6c81

research/arithmetic-library/ha-bertrand-bp01-tranche-rfc-v1.md
7eff83b267a9be832f2d6b7f0b6a2e2fff82d3cd1e6d09e806f264a5459c1ec3
```

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/bertrand_bp02_candidate.py
1bb7045f9b033e6e6167b329525d4833f66baab67bb5e846c3f572adbbb7ec0c
```

The focused-test byte seal remains pending until its fail-closed receipts are
populated. Hashes and receipts are evidence only and grant no authority.

## 1. Scope

This two-row tranche proves the endpoint-factorization boundary required by
campaign B8 and derives BP02 `bertrand_strict` as a corollary of BP01.

The first row displays `p = 2*n` when `p=n+n` and uses the constructive prime
definition to refute primality for `1<n`. The second row obtains BP01's
open-closed witness and eliminates its equality branch.

No theorem registry, edition, enrollment, or authority file changes in this
tranche.

## 2. Exact BP02 surface

The public BP02 row uses the exact frozen base-language source:

```text
forall n. (exists h. h + S 1 = n) -> exists p.
  ((~(p = 1) /\ forall a b. p = a * b -> a = 1 \/ b = 1) /\
  ((exists u. u + S n = p) /\ (exists v. v + S p = n + n)))
```

Removing the displayed formatting line breaks and indentation gives the
exact one-line source. Its SHA-256 is
`6c55889276eb7ad2577191ad7b7e46cae45a6c1437a0275db44801b54ee7ad39`.
The defined surface remains exactly:

```text
forall n. Lt(1,n) -> exists p.
  Prime(p) /\ (Lt(n,p) /\ Lt(p,n + n))
```

The public carrier remains `n+n`; neither `2*n` nor a commuted sum is an
acceptable source substitution.

## 3. Binding rows and dependencies

Rows appear in this exact order. Dependency order is first-use order. The
direct-Cut vector is `(4,4)` and contains 8 live edges.

### 3.1 `bertrand_upper_endpoint_factorization`

Surface:

```text
forall n p. Lt(1,n) -> Prime(p) -> p=n+n -> false
```

Direct dependencies:

```text
lt_not_le
zero_add
two_mul_eq_add_self
fixed_nontrivial_factor_not_prime
```

The proof derives `n != 1` from `Lt(1,n)`, proves `2 != 1` by PA1/PA2,
rewrites only the small factorization equality through
`two_mul_eq_add_self`, and applies the generic displayed-factor theorem. It
does not rewrite a whole Prime relation.

### 3.2 `bertrand_strict`

Surface: the exact BP02 source in Section 2.

Direct dependencies:

```text
add_eq_zero_right
bertrand_closed_upper
le_eq_or_lt
bertrand_upper_endpoint_factorization
```

The proof derives `n != 0` constructively from `Lt(1,n)`, obtains the BP01
witness, splits its upper `Le` by `le_eq_or_lt`, refutes equality with row 1,
and returns the strict branch. BP02 must depend on BP01 exactly as shown.

## 4. Binding topology

Row 1 has exactly 33 commands and row 2 exactly 39 commands. The audit must
freeze both scripts byte-for-byte. In particular:

- row 1 calls `fixed_nontrivial_factor_not_prime` once with factors `2,n`;
- row 1 uses no relation-wide Prime rewrite;
- row 2 applies BP01 once;
- row 2 performs one `le_eq_or_lt` split at `x,n+n`;
- only the equality branch calls the endpoint boundary; and
- the strict branch reconstructs the exact nested result conjunction.

No DNE, classical tactic, host arithmetic search, or exact-source transport
is permitted.

## 5. Fail-closed evidence and capacity

The focused audit must independently rebuild both public surfaces and all
private relation occurrences. It must pin the complete BP01/B8 provider
chain, exact scripts/dependencies, eight live edges, false targets, genuine
mutations, bounded bodies/envelopes, zero-DNE traversals, and direct-Cut
corruption before receipt comparison.

The BP02 closure must extend BP01's accepted rebuilt-body LayeredReplay
lineage. Stable theorem bodies are recursively reconstructed from exact
declared dependencies; no Stable or Alpha certificate may be inserted as an
untracked authority shortcut. The final ordinary certificate must check from
the empty context under every unchanged default resource cap.

The accepted strict-root lineage contains 546 nodes: 202 rebuilt Stable
bodies, 344 candidate bodies, and zero atomic Stable certificates. Its 1,921
dependency edges form 45 checked layers. The final empty-context certificate
has 201,312 proof occurrences, depth 235, 45,408 proof objects, 58,684 proof
edges, 13,277 reused references, 1,319,167 annotation occurrences, and
envelope depth 244. It therefore retains 298,688 proof occurrences of
headroom under the unchanged 500,000 cap.

The separate endpoint-boundary root closes in 442 proof occurrences, depth
28, and six checked layers. The focused audit freezes both topology and proof
DAG digests and corrupts every layer Cut before receipt comparison.

## 6. Genuine mutations

At minimum the audit must reject:

1. row 1 with `Lt(0,n)` in place of `Lt(1,n)`, witnessed by `n=1,p=2`;
2. row 1 with endpoint `p=S(n+n)`, witnessed by `n=2,p=5`;
3. row 1 with the Prime premise removed, witnessed by `n=2,p=4`;
4. BP02 with `Lt(0,n)` in place of `Lt(1,n)`, witnessed by `n=1`;
5. BP02 with result upper `Lt(p,n)`, witnessed by `n=2`; and
6. each row conjoined with `false`.

Replacing public `n+n` by the extensionally equal `2*n` is an exact-source
contract mutation, not a semantic counterexample.

## 7. Release boundary

Acceptance authorizes only these two candidate rows, their focused audit, and
this RFC as checked evidence. It does not itself enroll BP01/BP02 or change
checked-use status.

Once the final closure is sealed, the mathematical theorem campaign is
complete at candidate level. The remaining work is release engineering:
additive Alpha enrollment, evidence upgrade, dependency-closed Stable
promotion, generated artifacts, Book/PLAN/MOC updates, and reproducible cold
closure receipts.
