# HA Bertrand B8 Small-Range Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-17

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`76feaf6969b474539cb2eccbd14bf9a6bdee1aa1`.

Edition parent: Alpha v11, frozen by 1,123 rows, 3,482 edges, 45 layers,
and `editions_v11.py` SHA-256
`10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

B8 evidence parents:

```text
peano-lab/py/peano_lab/library/bertrand_b8_prime_certificates_candidate.py
e38954201d57680644ec6353d7d4c25b320f720d36f07c1c32d590c7920d3387

peano-lab/py/peano_lab/library/bertrand_b8_covering_candidate.py
cd44578fee0cf4aa362f925d9f13bc8b64f511e4d3f628a40b5432e59b72b31e
```

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/bertrand_b8_small_candidate.py
2886dc0bc4ac85667ec5223ed0074794ff66f828e34e7dbd2791757d141702b0
```

The focused-test byte seal remains pending until every fail-closed receipt is
populated. Hashes and receipts are evidence only and grant no authority.

## 1. Scope

This two-row tranche completes the finite mathematical branch required by
campaign gate B8. It proves the compact cutoff comparison and then assembles
the checked prime certificates and adjacent cover inequalities into
`bertrand_small_closed_upper`.

The proof is a native constructive decision tree. It does not enumerate 511
host values, invoke a host primality oracle, literalize 512 or 521, use DNE,
or mutate Stable, Alpha, edition, enrollment, or checked-use registries.

This tranche does not yet combine the small branch with B7, prove the
factorization boundary excluding the upper endpoint, or publish BP01/BP02.

## 2. Representation contract

The cutoff is exactly `16 * 32`. The final prime is exactly
`2 * (11 * 22) + 37`. Public theorem sources may not replace those carriers
by unary 512 or 521, nor reorder the cutoff to `32 * 16`.

`Prime`, `Le`, and `Lt` are fully expanded before parsing:

```text
Prime(p) := p != 1 /\ forall a b. p=a*b -> a=1 \/ b=1
Le(a,b) := exists k. k+a=b
Lt(a,b) := exists k. k+S a=b
```

The public result uses the unchanged RFC endpoint orientation
`Prime(p) /\ (Lt(n,p) /\ Le(p,n+n))`.

## 3. Binding rows and dependencies

Rows appear in this exact order. Dependency order is binding first-use order.
The direct-Cut vector is `(8,27)` and contains 35 edges.

### 3.1 `bertrand_cutoff_lt_final_prime`

Surface:

```text
Lt(16 * 32, 2 * (11 * 22) + 37)
```

Direct dependencies:

```text
add_succ_left
mul_add
bertrand_add_swap_nested
mul_comm
add_mul
add_assoc
add_comm
mul_assoc
```

The proof witnesses the strict gap by `8`, normalizes both sides to a shared
compact sum, and permits `norm_num` only on subequalities whose values are at
most 109. No tactic may normalize a unary 512 or 521.

### 3.2 `bertrand_small_closed_upper`

Surface:

```text
forall n. ~(n = 0) -> Lt(n,16 * 32) ->
  exists p. Prime(p) /\ (Lt(n,p) /\ Le(p,n + n))
```

Direct dependencies, in exact order:

```text
nonzero_is_succ
le_or_lt
lt_trans
bertrand_cutoff_lt_final_prime
bertrand_covering_interval
prime_five_hundred_twenty_one
bertrand_cover_three_hundred_seventeen_five_hundred_twenty_one
prime_three_hundred_seventeen
bertrand_cover_one_hundred_sixty_three_three_hundred_seventeen
prime_one_hundred_sixty_three
bertrand_cover_eighty_three_one_hundred_sixty_three
prime_eighty_three
bertrand_cover_forty_three_eighty_three
prime_forty_three
bertrand_cover_twenty_three_forty_three
prime_twenty_three
bertrand_cover_thirteen_twenty_three
prime_thirteen
bertrand_cover_seven_thirteen
prime_seven
bertrand_cover_five_seven
prime_five
bertrand_cover_three_five
prime_three
bertrand_cover_two_three
prime_two
bertrand_cover_one_two
```

## 4. Binding proof topology

The small theorem must:

1. derive `Le(1,n)` constructively from `n != 0` via `nonzero_is_succ`;
2. split successively with `le_or_lt` at
   `2,3,5,7,13,23,43,83,163,317`;
3. return each strict branch through `bertrand_covering_interval`, its exact
   prime certificate, and its exact preceding cover inequality;
4. derive `Lt(n,521)` from `Lt(n,16*32)` and row 1 with `lt_trans`; and
5. close the final `317 <= n` branch with the 521 certificate and cover.

The compact carriers for 83, 163, 317, and 521 remain exactly those frozen in
the two parent B8 tranches. No relation-wide rewrite, external loop, theorem
name oracle, or unproved numerical assertion is permitted.

## 5. Fail-closed evidence

The focused audit must independently rebuild both statements, exact scripts,
dependency order, occurrence tags, and all executed provider bytes. Its core
authority is Stable plus recursively rebuilt exact prime-certificate and
covering prefixes; neither Alpha membership nor prior receipt tuples are
proof authority.

For each row it must freeze:

- artifact length and statement/script/logical hashes;
- body dependency/command/resource metrics;
- bounded body-envelope metrics;
- an empty-context closure receipt; and
- the exact direct-Cut count, with every Cut proposition and proof corrupted
  and rejected before receipt comparison.

Every one of the 35 dependencies must be live. Kernel checking, bounded
resource envelopes, live caps, and zero-DNE traversal precede receipt
acceptance. Receipt placeholders fail closed.

## 6. Genuine mutations

At minimum the audit must reject:

1. row 1 with left carrier `17 * 32` (544 is not below 521);
2. row 1 with right carrier `2 * (11 * 22) + 28` (512 is not below 512);
3. row 2 with `n = 0` replacing `~(n = 0)`, witnessed by `n=0`;
4. row 2 with result upper bound `Le(p,n)`, witnessed by `n=1`; and
5. row 2 with result lower bound `Lt(S n,p)`, witnessed by `n=1`.

The audit also conjoins each statement with `false` and requires body replay
to fail. Commuted or associated arithmetic equalities are not mutations.

## 7. Release boundary

Acceptance authorizes only the candidate source, its focused test, and this
RFC as body-checked evidence. The rows remain unavailable for checked use
until a later additive edition enrollment and closure review.

The next B8 tranche may use `bertrand_small_closed_upper` and the checked B7
theorem to construct BP01 at the factorized cutoff. BP02 still additionally
requires the checked endpoint-factorization boundary.
