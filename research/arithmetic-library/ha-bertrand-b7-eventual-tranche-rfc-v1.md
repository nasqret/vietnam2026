# HA Bertrand B7 Eventual Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-17

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`6973472beb8074d28d659f9ea1a28b6c70c43215`.

Edition parent: Alpha v11, frozen by 1,123 rows, 3,482 edges, 45 layers,
and `editions_v11.py` SHA-256
`10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/bertrand_b7_eventual_candidate.py
6be00fab2b46ecc787b9f7f4a25f4f552a1021a20c62f5895c6047c74744d50b
```

The focused-test byte seal remains pending until all fail-closed receipts are
populated.  Hashes and receipts are evidence only and grant no authority.

## 1. Scope

This one-row tranche closes campaign stage B7.  It specializes the checked
constructive bounded-prime search to `(n,n+n]`.  The witness branch is
returned directly.  The explicit prime-free branch constructs the B3, B5,
and B6 relational witnesses and derives the strict/weak cycle

```text
4^n < n * CentralBinom(n) <= n * A * B <= 4^n.
```

The theorem is still a body-checked candidate.  It is not added to Stable,
Alpha, an edition registry, or checked-use authority by this tranche.

## 2. Representation contract

All readable relations below are authoring abbreviations expanded before
parsing.  They add no kernel symbol.

```text
BertrandClosed(n,p) := Prime(p) /\ n<p /\ p<=n+n
NoBertrandClosed(n) :=
  forall p. Prime(p) -> n<p -> p<=n+n -> false
Central(n,C) := Choose(n+n,n,C)
```

`Le`, `Lt`, `Prime`, `Choose`, `FloorSqrt`, `DivRem`, and `Pow` use their
already frozen raw Peano expansions.  Generated binders are capture-checked
against the complete public or local context.

The public cutoff is the RFC-v2 carrier `16 * 32`.  The source and focused
test must contain that carrier and must not replace it by the unary numeral
`512`, by `32 * 16`, or by any newly introduced multiplication symbol.

## 3. Binding public row

The sole public row is `bertrand_eventually_closed_upper`:

```text
forall n.
  Le(16 * 32,n) ->
  exists p. Prime(p) /\ Lt(n,p) /\ Le(p,n+n)
```

Binding public occurrence tags are:

```text
b7_threshold
b7_result_prime
b7_result_lower
b7_result_upper
```

The direct dependencies, in binding first-use order, are:

```text
bounded_prime_interval_search
le_mul_of_one_le_right
le_trans
lt_of_lt_of_le
floor_sqrt_total
division_remainder_exists
central_binom_exists
pow_exists
four_pow_lt_mul_central_binom
central_binom_le_of_no_bertrand_prime
mul_le_mul_left
mul_assoc
bertrand_main_inequality_nat
lt_not_le
```

The proof script has exactly 139 commands and the dependency-curried body has
exactly 14 direct dependency premises.

## 4. Binding proof topology

The proof must follow this constructive topology.

1. Introduce `n` and the factorized threshold hypothesis.
2. Specialize `bounded_prime_interval_search` at `n` and `n+n`.
3. Case the resulting constructive disjunction exactly once.
4. Return the supplied witness branch without rebuilding it.
5. In the exclusion branch, use `exfalso`; do not use DNE, classical choice,
   double-negation elimination, or a theorem equivalent to Bertrand.
6. Derive `4<=n` from `4<=16<=16*32<=n` and then derive `2<n`.
7. Obtain, in separate theorem-application haves, witnesses for:
   `FloorSqrt(n+n,s)`, `DivRem(3,n+n,q,r)`, `Central(n,C)`,
   `Pow(n+n,s,A)`, `Pow(4,q,B)`, and `Pow(4,n,F)`.
8. Apply the B3 lower bound to obtain `F<n*C`.
9. Apply the B5 capstone with the explicit exclusion branch to obtain
   `C<=A*B`.
10. Scale and reassociate only the small inequality to obtain
    `n*C<=n*A*B`.
11. Apply the exact balanced-lineage B6 theorem to obtain `n*A*B<=F`.
12. Compose the two weak bounds and contradict `F<n*C` with `lt_not_le`.

No whole `Pow`, `Central`, `FloorSqrt`, `DivRem`, or prime-search relation is
rewritten.  The sole algebraic rewrite is the scoped use of `mul_assoc` on
the scaled weak inequality.

## 5. Exact local occurrence tags

The focused audit independently rebuilds every local relation.  Their tags
are binding:

```text
b7_exclusion
b7_four_sixteen
b7_one_thirty_two
b7_sixteen_threshold
b7_four_threshold
b7_four_n
b7_two_four
b7_two_n
b7_floor
b7_division
b7_central
b7_power_a
b7_power_b
b7_power_f
b7_lower
b7_central_upper
b7_scaled_upper
b7_associated_upper
b7_main
b7_contradiction_upper
```

The witness names after the nested existential eliminations are binding to
the checked script: `x=s`, `x1=q`, `x2=r`, `x3=C`, `x4=A`, `x5=B`, and
`x6=F`.

## 6. Authority and provider contract

The focused audit starts from the checked Stable registry and reconstructs
every reachable non-Stable body.  Candidate support is drawn only from:

- the exact Alpha-v11 body specifications;
- the exact B5 support factories and final B5 central-upper factory;
- the exact balanced-v1 B6 candidate pool for
  `bertrand_main_inequality_nat`;
- this B7 factory.

The balanced-v1 B6 pool must override its reviewed same-name candidate
lineage exactly as frozen by `test_bertrand_b6_layered_closure.py`.  The
legacy Alpha-v7 seed lineage must remain unreachable from the B6 root.
Prior body, envelope, artifact, or closure receipts are never theorem
authority.

The following exact providers are particularly binding:

```text
bertrand_prime_interval_candidate.py
  6b9263ffd4aa39130ff4cee9ae3f3449e4aadbc544363900f7f2289ffc701a97
bertrand_central_binom_lower_bound_candidate.py
  60e24bb5ab7681deb6fb269033b57c74531b086e54504d5fa0239389afddaab6
bertrand_b5_central_upper_candidate.py
  95b11876de61baa50ed1b7ff4debc2ce9afb52a35aeb2a83ff5920ca81ca77a7
bertrand_b6_main_inequality_candidate.py
  0b6aed58cf2865fde8e41c5d20e301169727e40599afec7ce03e0a9517d2f657
bertrand_balanced_v1_successor_candidate.py
  852f3dc63a0bd6e80dccee70046c628e1929ae3e08bb200a016d25e1429d5b7b
test_bertrand_b6_layered_closure.py
  1b9651a9fcb0096a06b3bd1177b200c309adc48ec640bb5c2e4ebb64c97f81e6
```

## 7. Fail-closed audit requirements

The focused test must reject all of the following before accepting any
receipt.

1. Any source, RFC, Alpha-v11, B3, B5, or B6 provider hash drift.
2. Any public statement, dependency order, script, tag, witness, or command
   count drift.
3. Any deletion of one of the 14 direct dependency edges.
4. Replacement of the target by `target /\ false`.
5. Replacement of the result upper bound `p<=n+n` by `p<=n`.  This mutation
   is genuinely false because the same result also requires `n<p`.
6. Deletion of `bounded_prime_interval_search` or replacement of the
   explicit exclusion branch by a double-negated existence claim.
7. Any DNE node, classical token, unchecked-use token, or authority leak.
8. Any change to the exact factorized cutoff spelling.
9. Any mismatch in the 14 direct dependency edges or 30 compiled layer Cuts.
10. Any corrupted layer Cut that the unchanged kernel accepts.

Every receipt table starts with a fail-closed sentinel and becomes concrete
only after the corresponding gate has passed in an isolated serial worker.

## 8. Measured resource contract

The dependency-curried body is frozen at:

```text
dependencies 14
commands     139
occurrences  389
depth        77
objects      382
edges        388
reused       7
envelope     (389, 382, 77, 1055, 79)
```

The exact root-pruned layered graph is frozen at:

```text
nodes             413
candidate bodies  308
dependency edges  1278
layers            30
topology SHA-256   9b9d4c4c0304af0c2f6b5bf4358a54895be03e9aabae6a054121cd7a6fe21cf6
layer sizes        119,82,51,30,20,14,19,12,11,8,8,6,6,2,1,
                   1,1,2,2,2,2,1,1,1,1,3,3,2,1,1
```

The checked empty-context closure is frozen at:

```text
proof occurrences       499202
proof depth             181
proof objects           37293
proof edges             48349
reused objects          11057
annotation occurrences  2227190
envelope depth          211
proof DAG SHA-256
  069aa5641175a85043ab5657a3c88d4cccf645e69721bef0a5cd2610ef4dd883
```

The occurrence margin is only 798 below the unchanged 500,000 cap.  This is
a hard topology seal, not permission to raise a limit.  Any proof, provider,
or graph change must be remeasured and must still pass the existing default
limits.  Heavy workers run serially with `PYTHONMALLOC=malloc`.

## 9. Exit condition

This tranche is complete only when:

- the source, RFC, and focused test byte seals are frozen;
- artifact, body, envelope, and closure receipts are all concrete;
- the complete focused suite passes in one serial run;
- all 14 dependency removals and the genuine mutation fail closed;
- all 14 direct edges are live and all 30 layer Cuts are exhaustively
  corrupted and rejected;
- tracked/staged scope, whitespace, line length, and provider isolation are
  clean.

Completion establishes the candidate B7 theorem only.  B8 finite coverage,
`bertrand_closed_upper`, and `bertrand_strict` remain separate campaign gates.
