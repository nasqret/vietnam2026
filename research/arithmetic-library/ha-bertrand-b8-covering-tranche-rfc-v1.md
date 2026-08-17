# HA Bertrand B8 Covering Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-17

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`7a8e7318acfad1830d65415969ee79e5e24eebfb`.

Edition parent: Alpha v11, frozen by 1,123 rows, 3,482 edges, 45 layers,
and `editions_v11.py` SHA-256
`10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

Prime-certificate parent:

```text
peano-lab/py/peano_lab/library/bertrand_b8_prime_certificates_candidate.py
e38954201d57680644ec6353d7d4c25b320f720d36f07c1c32d590c7920d3387

peano-lab/py/tests/test_bertrand_b8_prime_certificates_candidate.py
2db7fe77f2700d03d1e9b78f1a98c6da671f7f9be33efe8c758af691d4ccd022

research/arithmetic-library/
  ha-bertrand-b8-prime-certificates-tranche-rfc-v1.md
356e8d69498f117921b1229c9a07b42f9caad48febe612a2e89ab93578a3ba73
```

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/bertrand_b8_covering_candidate.py
cd44578fee0cf4aa362f925d9f13bc8b64f511e4d3f628a40b5432e59b72b31e
```

The focused-test byte seal remains pending until every fail-closed receipt is
populated.  Hashes and receipts are evidence only and grant no authority.

## 1. Scope

This 14-row tranche supplies the checked arithmetic behind the finite
Bertrand cover.  It proves one generic adjacent-interval theorem and every
cover inequality in the chain

```text
1 -- 2 -- 3 -- 5 -- 7 -- 13 -- 23 -- 43 -- 83 -- 163 -- 317 -- 521.
```

The first edge covers `n=1`; the next ten edges connect the eleven certified
primes.  Together they are sufficient for the later constructive finite-case
split through `n<512`.  This tranche does not yet assemble that split, prove
`bertrand_small_closed_upper`, prove the endpoint factorization bridge, or
publish either final Bertrand capstone.

All rows remain body-checked candidates.  This tranche mutates no Stable,
Alpha, edition, enrollment, or checked-use registry.

## 2. Representation contract

`Prime`, `Le`, and `Lt` are fully expanded before parsing:

```text
Prime(p) := p != 1 /\ forall a b. p=a*b -> a=1 \/ b=1
Le(a,b) := exists k. k+a=b
Lt(a,b) := exists k. k+S a=b
```

The final four prime carriers are frozen exactly as:

```text
83  := 9 * 9 + 2
163 := 13 * 12 + 7
317 := 18 * 17 + 11
521 := 2 * (11 * 22) + 37
```

The public covering relation always has orientation `Le(next,current+current)`.
No proof may replace a compact carrier by a literal unary 163, 317, or 521.

## 3. Binding rows and direct dependencies

Rows appear in this exact order.  Dependency order is binding first-use
order; the direct-Cut vector is

```text
(2,2,3,0,0,0,0,0,0,0,0,3,6,8)
```

and contains 24 direct dependency edges in total.

1. `bertrand_add_swap_nested`: `add_assoc`, `add_comm`.
2. `bertrand_add_six_permute`: `add_assoc`, row 1.
3. `bertrand_covering_interval`:
   `add_le_add_right`, `add_le_add_left`, `le_trans`.
4. `bertrand_cover_one_two`: no dependencies.
5. `bertrand_cover_two_three`: no dependencies.
6. `bertrand_cover_three_five`: no dependencies.
7. `bertrand_cover_five_seven`: no dependencies.
8. `bertrand_cover_seven_thirteen`: no dependencies.
9. `bertrand_cover_thirteen_twenty_three`: no dependencies.
10. `bertrand_cover_twenty_three_forty_three`: no dependencies.
11. `bertrand_cover_forty_three_eighty_three`: no dependencies.
12. `bertrand_cover_eighty_three_one_hundred_sixty_three`:
    `add_mul`, `add_assoc`, `add_comm`.
13. `bertrand_cover_one_hundred_sixty_three_three_hundred_seventeen`:
    `add_mul`, `mul_add`, `add_assoc`, `add_comm`, row 1, row 2.
14. `bertrand_cover_three_hundred_seventeen_five_hundred_twenty_one`:
    `add_mul`, `mul_add`, `mul_assoc`, `mul_comm`, `add_assoc`,
    `add_comm`, `one_mul`, row 2.

## 4. Binding theorem surfaces

Rows 1--3 have the following abstract surfaces:

```text
forall a b c. a+(b+c)=b+(a+c)

forall a b c d e f.
  ((a+b)+(c+d))+(e+f)=(a+e)+((b+c)+(d+f))

forall a b n.
  Prime(b) -> Le(a,n) -> Lt(n,b) -> Le(b,a+a) ->
  exists p. Prime(p) /\ Lt(n,p) /\ Le(p,n+n)
```

Rows 4--14 are the exact closed expanded `Le(next,current+current)`
relations for:

```text
(1,2), (2,3), (3,5), (5,7), (7,13), (13,23),
(23,43), (43,9*9+2),
(9*9+2,13*12+7),
(13*12+7,18*17+11),
(18*17+11,2*(11*22)+37).
```

The generated occurrence tags are the source-defined `bb8ci_*` and
`bb8c_*` tags and must be independently rebuilt by the focused test.

## 5. Binding proof topology

1. Row 1 reassociates, commutes the first pair, and reassociates back.
2. Row 2 uses row 1 three times to normalize six addends.  It contains no
   induction, multiplication, or numerical normalization.
3. Row 3 scales `Le(a,n)` once on each side, composes the two inequalities,
   composes with `Le(b,a+a)`, and returns the supplied prime `b`.
4. Rows 4--11 use a single explicit gap witness and one bounded `norm_num`.
5. Row 12 proves `163=83+80` and `3+80=83` using only additions and one
   distributed product.
6. Row 13 expands `(13+5)*(12+5)`, uses rows 1--2 for the six resulting
   addends, and proves the explicit gap nine.
7. Row 14 normalizes both sides to compact products in 17, proves
   `521=317+204`, and proves the actual cover gap
   `113+521=317+317`, where `113` is represented as `6*17+11`.

Every `norm_num` target stays below its unchanged value and AST-depth limits.
No `simp`, induction, DNE, classical choice, host arithmetic oracle, or cap
increase is permitted.  Every repeated associative or distributive theorem
use is either isolated in a local `have` or has an independent direct edge.

## 6. Focused evidence gates

The focused test must fail closed unless it independently reproduces:

- the exact 14 names, order, surfaces, scripts, and dependency tuples;
- the exact source, parent-RFC, Alpha-v11, and provider hashes;
- Stable plus earlier-local-prefix authority only;
- all 24 dependency-removal failures;
- one false target and one genuine semantic mutation per row;
- kernel-accepted dependency-curried bodies and bounded envelopes;
- no occurrence of `DNE`;
- recursively rebuilt empty-context closures;
- the exact direct-Cut count for each row and rejection after corruption of
  every direct Cut before receipt comparison.

For the eleven cover rows, reversing the inequality is not a genuine
mutation.  Binding mutations must instead strengthen the right carrier or
successor-shift the left `next` carrier, with an explicit standard-natural
counterfixture.

Artifact, body, envelope, and closure manifests begin with fail-closed
sentinels.  Concrete values may be frozen only after isolated serial replay.

## 7. Release boundary

This RFC authorizes only the candidate source, its focused fail-closed test,
and this document.  Enrollment or checked-use promotion requires a separate
additive edition tranche.  The next B8 tranche may consume these rows and the
native prime certificates to construct the finite interval split and
`bertrand_small_closed_upper`.
