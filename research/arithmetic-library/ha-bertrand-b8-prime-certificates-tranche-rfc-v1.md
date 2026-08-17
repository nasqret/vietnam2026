# HA Bertrand B8 Prime-Certificate Tranche RFC v1

Status: binding subordinate contract; this document grants no theorem authority

Date: 2026-08-17

Parent campaign:

- `ha-bertrand-postulate-campaign-rfc-v1.md`
  (`0b8bf90d53878150272ed3949c6316568d83d857b2e392622bfb8a7b65af8a0b`);
- `ha-bertrand-postulate-campaign-rfc-v2.md`
  (`af5ab20980b32f31d3a6ad5f3f3f041c64b3d359489b50114733da3c4d2f1618`).

Repository parent: commit
`5e2720a136b49f2ec314bf7eab2cf6c21449af06`.

Edition parent: Alpha v11, frozen by 1,123 rows, 3,482 edges, 45 layers,
and `editions_v11.py` SHA-256
`10b2d9b86b2014e685a75e12a3b5991cfd605fce5f7557835bc4da37e219acaf`.

The candidate source is frozen at:

```text
peano-lab/py/peano_lab/library/bertrand_b8_prime_certificates_candidate.py
e38954201d57680644ec6353d7d4c25b320f720d36f07c1c32d590c7920d3387
```

The focused-test byte seal remains pending until all fail-closed receipts are
populated.  Hashes and receipts are evidence only and grant no authority.

## 1. Scope

This 18-row tranche begins campaign stage B8.  It proves a reusable,
constructive trial-division criterion below a displayed square and supplies
native PA certificates for the nine primes not already present in Stable:

```text
5, 7, 13, 23, 43, 83, 163, 317, 521.
```

Together with Stable `prime_two` and `prime_three`, these rows supply the
entire finite prime chain required by the final Bertrand covering argument.
The tranche does not yet prove the covering inequalities, the general finite
covering lemma, `bertrand_small_closed_upper`, or either public capstone.

All rows remain body-checked candidates.  This tranche mutates no Stable,
Alpha, edition, enrollment, or checked-use registry.

## 2. Representation contract

`Prime`, `Le`, `Lt`, and divisibility are fully expanded before parsing:

```text
Prime(p) := p != 1 /\ forall a b. p=a*b -> a=1 \/ b=1
Le(a,b) := exists k. k+a=b
Lt(a,b) := exists k. k+S a=b
Dvd(d,n) := exists q. n=d*q
```

The three largest public certificate carriers are deliberately compact:

```text
163 := 13 * 12 + 7
317 := 18 * 17 + 11
521 := 2 * (11 * 22) + 37
```

They are ordinary Peano terms, not new numeric primitives.  The 521 proof
checks its equality with `23*22+15` exactly once in the square-bound prelude.
This prevents repeated large normalization and keeps every `norm_num` input
within the unchanged value/depth limits.

## 3. Binding rows and direct dependencies

Rows appear in this exact order.  Dependency order is binding first-use
order; the direct-Cut vector is

```text
(0,6,8,2,5,4,4,3,1,5,5,5,5,5,11,10,10,12)
```

and contains 101 direct dependency edges in total.

1. `fixed_nontrivial_factor_not_prime`: no dependencies.
2. `factor_pair_has_small_member_below_square`:
   `le_total`, `le_or_lt`, `mul_le_mul_right`, `mul_le_mul_left`,
   `le_trans`, `lt_not_le`.
3. `nonprime_has_small_prime_divisor_below_square`:
   `prime_or_composite`, row 2, `mul_zero_left`, `prime_divisor_exists`,
   `divisor_le_nonzero`, `le_trans`, `multiple_trans`, `mul_comm`.
4. `prime_of_no_small_prime_divisor_below_square`:
   `prime_decidable`, row 3.
5. `prime_le_twenty_two_cases`:
   `le_eq_or_lt`, `le_of_succ_le_succ`, `prime_is_succ_succ`,
   `lt_not_le`, row 1.
6. `nonzero_remainder_not_multiple`:
   `multiple_refl`, `divides_remainder`, `divisor_le_nonzero`, `lt_not_le`.
7. `scaled_remainder_lift`:
   `mul_add`, `mul_assoc`, `mul_comm`, `add_assoc`.
8. `add_remainder_lift`: `mul_add`, `add_assoc`, `add_comm`.
9. `double_scaled_remainder_lift`: row 7.
10. `prime_five`: rows 6 and 4, `le_trans`, row 5, `lt_not_le`.
11. `prime_seven`: the same five dependencies as row 10.
12. `prime_thirteen`: the same five dependencies as row 10.
13. `prime_twenty_three`: the same five dependencies as row 10.
14. `prime_forty_three`: the same five dependencies as row 10.
15. `prime_eighty_three`: `add_eq_zero_right`, `le_not_lt`,
    `add_assoc`, `add_comm`, `mul_succ_left`, row 7, row 6, row 4,
    `le_trans`, row 5, `lt_not_le`.
16. `prime_one_hundred_sixty_three`: `add_eq_zero_right`, `le_not_lt`,
    `add_assoc`, `add_comm`, row 7, row 6, row 4, `le_trans`, row 5,
    `lt_not_le`.
17. `prime_three_hundred_seventeen`: the same ten dependencies as row 16.
18. `prime_five_hundred_twenty_one`: `add_eq_zero_right`, `le_not_lt`,
    `add_assoc`, `add_comm`, row 9, `add_mul`, `mul_assoc`, `one_mul`,
    row 6, row 4, `le_trans`, row 5.  Unlike the smaller certificates, its
    active bound is already 22, so no above-bound `lt_not_le` branch exists.

## 4. Binding theorem surfaces

The support surfaces are:

```text
forall n a b.
  n=a*b -> a!=1 -> b!=1 -> Prime(n) -> false

forall B n a b.
  n=a*b -> Lt(n,S B*S B) -> Le(a,B) \/ Le(b,B)

forall B n.
  n!=0 -> n!=1 -> Lt(n,S B*S B) -> ~Prime(n) ->
  exists p. Prime(p) /\ Le(p,B) /\ Dvd(p,n)

forall B n.
  n!=0 -> n!=1 -> Lt(n,S B*S B) ->
  (forall p. Prime(p) -> Le(p,B) -> ~Dvd(p,n)) -> Prime(n)

forall p. Prime(p) -> Le(p,22) ->
  p=2 \/ p=3 \/ p=5 \/ p=7 \/ p=11 \/ p=13 \/ p=17 \/ p=19

forall d n q r.
  n=d*q+r -> r!=0 -> Lt(r,d) -> ~Dvd(d,n)

forall d x q t c r s u.
  x=d*q+t -> c*t+r=d*s+u -> c*x+r=d*(c*q+s)+u

forall d x y q s r t u v.
  x=d*q+r -> y=d*s+t -> r+t=d*u+v ->
  x+y=d*((q+s)+u)+v

forall d x q t s r u v.
  x=d*q+t -> 11*t=d*s+r -> 2*r+37=d*u+v ->
  2*(11*x)+37=d*(2*(11*q+s)+u)+v
```

Rows 10--18 are the exact closed `Prime` expansions at their displayed
carriers.  Generated occurrence tags are the source-defined `bb8*` tags and
must be independently rebuilt by the focused test.

## 5. Binding proof topology

1. Row 1 eliminates the supplied `Prime` factor property directly.
2. Row 2 compares the two factors, assumes both exceed `B`, scales the two
   weak inequalities, and contradicts the strict square bound.
3. Row 3 uses constructive `prime_or_composite`; in the composite branch it
   chooses the small factor, obtains a prime divisor, and transports that
   divisor into `n` with `multiple_trans`.
4. Row 4 cases `prime_decidable` and contradicts its negative branch using
   row 3 and the supplied finite exclusion.
5. Row 5 descends from 22 to 2 with `le_eq_or_lt`.  Composite endpoints are
   refuted by explicit nontrivial factorizations; the eight prime-shaped
   endpoints are returned.  No host primality oracle is permitted.
6. Row 6 derives that a common divisor divides the remainder, obtains
   `d<=r`, and contradicts `r<d`.
7. Rows 7--9 are explicit distributive/associative remainder identities.
8. Each concrete certificate applies row 4 at its natural square-root bound,
   cases row 5, rejects values above the active bound, and proves every live
   remainder nonzero with row 6.
9. The concrete scripts may be mechanically generated, but every quotient,
   remainder, bound, and representation equality is kernel checked.

No DNE, classical choice, host enumeration, untrusted primality oracle,
literal unary 163/317/521, or cap increase is permitted.

## 6. Focused evidence gates

The focused test must fail closed unless it independently reproduces:

- the exact 18 names, order, surfaces, scripts, and dependency tuples;
- the exact source, parent-RFC, Alpha-v11, and provider hashes;
- Stable plus earlier-local-prefix authority only;
- all 101 dependency-removal failures;
- one false target and one genuine semantic mutation per row;
- kernel-accepted dependency-curried bodies and bounded envelopes;
- no occurrence of `DNE`;
- recursively rebuilt empty-context closures;
- the exact direct-Cut count for each row and rejection after corruption of
  every direct Cut before receipt comparison.

Artifact, body, envelope, and closure manifests begin with fail-closed
sentinels.  Concrete values may be frozen only after isolated serial replay.

## 7. Release boundary

This RFC authorizes only the candidate source, its focused fail-closed test,
and this document.  Enrollment or checked-use promotion requires a separate
additive edition tranche.  The next B8 tranche must prove the consecutive
covering inequalities and a general finite-covering lemma before it may claim
`bertrand_small_closed_upper`.
