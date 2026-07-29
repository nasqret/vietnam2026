# Native gcd and balanced Bézout roadmap

## Status boundary

The checked runtime currently exposes the relational gcd/coprimality API
through uniqueness, the zero-right gcd base case, and both directions of
Euclidean-step invariance, together with bounded and unrestricted relational
gcd existence. It now also exposes simultaneous relational-gcd/balanced-Bézout
existence, result-one witnesses for coprime inputs, Gauss cancellation, and
Euclid's lemma. A separate constructive search spine now decides equality,
divisibility, bounded factor pairs, and primality, and constructs a prime
divisor of every nonzero nonunit natural. Greatest-prime descent and the
encoded finite-product layer remain separate milestones.

All relations below are authoring notation only. In particular,

```text
IsGCD(g,a,b) :=
  ((exists x. a = g * x) /\ (exists y. b = g * y)) /\
  forall c.
    (exists u. a = c * u) ->
    (exists v. b = c * v) ->
    exists w. g = c * w
```

must be fully expanded before parsing. The parentheses are intentional:
Peano Lab parses repeated conjunctions left-associatively.

The current checked layer contains:

- `mul_eq_one_components`, `divisor_one`, and the two coprime-with-one laws;
- `is_gcd_symm`, the two divisibility projections, and `is_gcd_greatest`;
- `is_gcd_of_dvd` and the two `IsGCD(1)`/coprimality bridges; and
- `multiple_antisymm` and `is_gcd_unique`;
- `factor_difference`, `divides_remainder`, and `divides_linear_step`; and
- `is_gcd_zero_right`, `is_gcd_euclid_forward`, and
  `is_gcd_euclid_backward`; and
- `gcd_exists_up_to` and `gcd_exists_relational`; and
- `add_permute_outer`, `balanced_bezout_euclid_step`,
  `gcd_balanced_bezout_exists_up_to`, `gcd_balanced_bezout_exists`,
  `balanced_combination_scale_right`,
  `common_divisor_divides_balanced_result`, `coprime_balanced_bezout`,
  `gauss_coprime_cancel`, `prime_divisor_eq_one_or_self`, and
  `euclid_prime_dvd_product`; and
- `eq_decidable`, `multiple_decidable_nonzero`, `multiple_decidable`,
  `factor_nonzero_left`, `factor_property_succ`, `factor_search_up_to`,
  `prime_nonzero`, `prime_or_composite`, `prime_decidable`,
  `proper_factor_lt`, `prime_divisor_exists_up_to`, and
  `prime_divisor_exists`.

In the current shared representation, the largest certificate in this layer is
`euclid_prime_dvd_product` at 5,382 proof nodes/depth 55. Every entry replays
constructively and checks from the empty context. The snapshot-wide maximum
depth is now 80, set by `prime_divisor_exists`.

## Checked Euclidean invariance

The runtime now contains closed, independently kernel-accepted certificates
for the subtraction-free Euclidean ladder. Their authored scripts, catalog
records, generated artifacts, and regression tests are admitted together as
ordinary native library entries.

| Checked theorem | Role | Shared nodes/depth |
|---|---|---:|
| `is_gcd_zero_right` | base case `IsGCD(a,a,0)` | 65 / 11 |
| `factor_difference` | from `c*u = c*v + r`, construct `c | r` | 265 / 26 |
| `divides_remainder` | common divisors of `a,b` divide `r` when `a=b*q+r` | 427 / 29 |
| `divides_linear_step` | divisors of `b,r` divide `b*q+r` | 224 / 19 |
| `is_gcd_euclid_forward` | `IsGCD(d,b,r) -> IsGCD(d,a,b)` | 741 / 38 |
| `is_gcd_euclid_backward` | `IsGCD(d,a,b) -> IsGCD(d,b,r)` | 741 / 37 |

The key subtraction-free lemma is

```text
forall c u v r.
  c * u = c * v + r ->
  exists w. r = c * w
```

Its proof inducts simultaneously through the two multiples rather than
forming a natural-number subtraction. With it, both directions of Euclidean
invariance are ordinary divisibility algebra.

## Checked formula-specific strong induction for gcd existence

The object language has no predicate variables, so a polymorphic strong-
induction theorem is not a possible library entry. For this concrete motive,
ordinary induction can instead prove the bounded statement

```text
forall B b.
  (exists t. t + b = B) ->
  forall a.
    exists d. IsGCD(d,a,b)
```

with `IsGCD` expanded as above. The construction is:

1. Induct on `B`.
2. At zero, `b <= 0` forces `b = 0`; choose `d = a`.
3. At `S B`, split `b <= S B` into `b <= B` or `b = S B`.
4. In the first branch, apply the induction hypothesis directly.
5. In the equality branch, divide `a = b*q+r` with `r < b`.
6. Convert `r < S B` to `r <= B`, apply the induction hypothesis to `(b,r)`,
   and transport the result through `is_gcd_euclid_forward`.

The public `gcd_exists_relational` theorem is then the instance `B=b`, using
reflexivity of `<=`.

The admitted `gcd_exists_up_to` script closes against its
dependency-curried target in 90 nodes.
The former dependency inliner produced a 1,024-node substituted tree (971
after reduction) which the independent kernel correctly rejected because of a
capture-sensitive induction defect. That failure motivated the sharing gate.
With nested self-contained Cuts, the same bounded theorem now checks
constructively from the empty context at 1,232 nodes/depth 44.
`gcd_exists_relational` takes the instance $B=b$, obtains $b\le b$ from
`le_refl`, and checks from the empty context at 1,268 nodes/depth 46. Both are
now synchronized runtime and catalog entries.

The reviewed remedy is now the self-contained derived rule
`Cut(A,B,lemma,body)`. The kernel checks its lemma once and its body under the
new hypothesis; the node contains no theorem names, hashes, or external
authority. This enlarges the trusted checker without changing the object
language or logic. See [the proof-sharing design](proof-sharing-design.md).
The two admitted theorems provide the fresh replay and arithmetic proof that
the composition mechanism alone could not supply.

## Balanced-natural Bézout

Conventional signed coefficients are not terms in the current language. The
constructive native relation uses four naturals:

```text
BalancedBezout(d,a,b) :=
  exists xp yp xn yn.
    a * xp + b * yp = d + (a * xn + b * yn)
```

This represents

$$a(x_+-x_-)+b(y_+-y_-)=d$$

without adding integers or subtraction.

For `a = b*q+r`, a witness for `(b,r)` transports to one for `(a,b)` by

```text
xp' = yp
yp' = xp + q * yn
xn' = yn
yn' = xn + q * yp
```

because the target equality is

```text
a * yp + b * (xp + q * yn)
  = d + (a * yn + b * (xn + q * yp)).
```

The coefficient identity is now admitted as
`balanced_bezout_euclid_step`; `add_permute_outer` is its only new additive
helper. The checked proof uses explicit associativity, commutativity, and
distributivity certificates rather than treating `ring` as a library oracle.

## Checked simultaneous bounded descent

The strengthened bounded theorem is

```text
forall B b.
  b <= B ->
  forall a.
    exists d. IsGCD(d,a,b) /\ BalancedBezout(d,a,b)
```

with both relations expanded in the stored formula. This is ordinary
induction on `B`, not a polymorphic strong-induction axiom.

1. At zero, `b = 0`; choose `d = a` and coefficients `(1,0,0,0)`.
2. At `S B`, split into `b <= B` and `b = S B`.
3. The first branch applies the induction hypothesis directly.
4. In the boundary branch, divide `a = b*q+r`; the remainder bound gives
   `r <= B`.
5. Apply the induction hypothesis to `(b,r)`.
6. Transport the full `IsGCD(d,b,r)` proof with
   `is_gcd_euclid_forward`, and independently transport the four coefficients
   with `balanced_bezout_euclid_step`.

The word *full* is important. The bounded proof carries the complete
greatest-common-divisor clause through the Euclidean step. It does not derive
maximality afterward from the balanced equation.

The public `gcd_balanced_bezout_exists` wrapper takes `B=b` using `le_refl`.
For coprime inputs, the constructed gcd divides both inputs and therefore must
equal one; `coprime_balanced_bezout` exposes the resulting balanced result-one
witness directly.

## Checked Gauss bridge

Two independent algebraic interfaces turn that result-one witness into Gauss
cancellation:

```text
balanced_combination_scale_right:
  BalancedBezout(d,a,b) -> BalancedBezout(d*z,a,b*z)

common_divisor_divides_balanced_result:
  c | a -> c | b -> BalancedBezout(d,a,b) -> c | d
```

The second theorem has a 626-node shared certificate. It is used here, in the
Gauss proof; it is **not** the source of the maximality clause in the bounded
gcd/Bézout construction. Scaling a coprime result-one equation by `z` and
applying the bridge to the inputs `(a,b*z)` proves

```text
Coprime(a,b) -> a | b*z -> a | z.
```

This is `gauss_coprime_cancel`.

## Checked Euclid lemma

The checked `prime_divisor_eq_one_or_self` packages the prime factor-pair API
as the reusable implication `Prime(p) -> g | p -> g = 1 \/ p = g`.

For a prime `p`, choose a relational gcd `g` of `(p,a)`. Since `g | p`, this
new divisor characterization gives two constructive branches:

- if `g = 1`, then `p` and `a` are coprime, so Gauss turns `p | a*b` into
  `p | b`;
- if `p = g`, the gcd divisibility witness gives `p | a`.

Thus the checked `euclid_prime_dvd_product` theorem proves

```text
Prime(p) -> p | a*b -> p | a \/ p | b
```

with every displayed relation expanded in its actual first-order statement.

## Checked constructive prime search

The prime-divisor theorem is independent of Euclid's lemma: it has to produce
a prime rather than reason about a supplied one. The admitted route is fully
constructive and never turns a bare negation of primality into a witness.

1. `eq_decidable` proves natural equality decidable by induction.
2. Unique quotient/remainder makes divisibility by a nonzero divisor
   decidable; `multiple_decidable` discharges the zero-divisor branch.
3. `factor_search_up_to` inducts over an explicit factor bound. At each new
   boundary it decides whether the boundary divides the number and either
   returns a nontrivial factor pair or extends the universal factor property.
4. `prime_or_composite` instantiates the bound at the number itself, using the
   positive-divisor bound to cover every possible factor.
5. `proper_factor_lt` shows that a factor paired with a nonunit cofactor is
   strictly smaller than the nonzero product.
6. `prime_divisor_exists_up_to` performs formula-specific bounded strong
   induction: return the number if prime; otherwise recurse into the smaller
   proper factor and transport its prime divisor by divisibility transitivity.
7. `prime_divisor_exists` instantiates the explicit bound reflexively.

The companion nodes `factor_nonzero_left`, `prime_nonzero`, and
`prime_decidable` expose reusable boundary facts and the final total decision
API. The whole route is accepted by the intuitionistic kernel; no excluded
middle or double-negation elimination is hidden in the search.

| Checked theorem | Nodes/depth |
|---|---:|
| `eq_decidable` | 48 / 20 |
| `multiple_decidable_nonzero` | 1,242 / 61 |
| `multiple_decidable` | 1,352 / 64 |
| `factor_nonzero_left` | 37 / 12 |
| `factor_property_succ` | 150 / 20 |
| `factor_search_up_to` | 1,925 / 69 |
| `prime_nonzero` | 49 / 11 |
| `prime_or_composite` | 2,038 / 71 |
| `prime_decidable` | 2,194 / 73 |
| `proper_factor_lt` | 468 / 26 |
| `prime_divisor_exists_up_to` | 2,931 / 78 |
| `prime_divisor_exists` | 2,977 / 80 |

## Shared-certificate metrics

| Checked theorem | Nodes/depth |
|---|---:|
| `add_permute_outer` | 149 / 15 |
| `balanced_bezout_euclid_step` | 880 / 35 |
| `gcd_balanced_bezout_exists_up_to` | 2,233 / 45 |
| `gcd_balanced_bezout_exists` | 2,269 / 47 |
| `balanced_combination_scale_right` | 754 / 28 |
| `common_divisor_divides_balanced_result` | 626 / 39 |
| `coprime_balanced_bezout` | 2,304 / 48 |
| `gauss_coprime_cancel` | 3,800 / 51 |
| `prime_divisor_eq_one_or_self` | 57 / 12 |
| `euclid_prime_dvd_product` | 5,382 / 55 |

The β-coprimality/common-multiple clients of this gcd and Gauss layer are:

| Checked theorem | Nodes/depth |
|---|---:|
| `beta_modulus_coprime_base` | 874 / 30 |
| `common_divisor_beta_moduli_divides_gap_times_c` | 855 / 30 |
| `beta_moduli_coprime_of_gap_dvd` | 6,007 / 56 |
| `binary_crt_beta_pair_of_gap_dvd` | 12,980 / 71 |
| `bounded_common_multiple_step` | 483 / 29 |
| `bounded_common_multiple_exists` | 640 / 30 |

The bounded-prefix and CRT fold-algebra tranche has independently audited
shared metrics:

| Checked theorem | Nodes/depth/Cuts |
|---|---:|
| `beta_moduli_coprime_of_lt_bounded_common_multiple` | 6,227 / 57 / 181 |
| `beta_moduli_pairwise_coprime_bounded` | 6,348 / 59 / 183 |
| `bounded_beta_moduli_pairwise_coprime_exists` | 7,019 / 61 / 207 |
| `coprime_mul_left` | 3,975 / 53 / 115 |
| `coprime_mul_right` | 4,017 / 54 / 117 |
| `mod_eq_of_mod_eq_multiple` | 157 / 23 / 3 |
| `binary_crt_fold_step` | 5,501 / 52 / 156 |

The bounded existing-code prefix tranche continues with:

| Checked theorem | Nodes/depth/Cuts |
|---|---:|
| `right_factor_divides_product` | 229 / 25 / 7 |
| `beta_accumulated_product_step` | 11,174 / 69 / 330 |
| `beta_crt_prefix_congruence_step` | 7,352 / 64 / 213 |
| `beta_crt_prefix_invariant_step` | 18,613 / 70 / 545 |
| `bounded_beta_crt_prefix_invariant` | 25,496 / 78 / 752 |
| `bounded_beta_crt_for_existing_code` | 25,545 / 79 / 755 |

## Admission gates

1. **Complete:** admit and mutation-test the Euclidean invariance ladder.
2. **Complete:** land and audit self-contained proof sharing.
3. **Complete:** admit bounded gcd existence and its public wrapper.
4. **Complete:** prove the coefficient-update identity with an ordinary
   checked semiring certificate.
5. **Complete:** admit simultaneous balanced gcd/Bézout existence and derive
   coprime Bézout and Gauss cancellation.
6. **Complete:** combine relational gcd, primality, and Gauss to prove Euclid's
   lemma.
7. **Complete:** develop constructive factor search, prime/composite and
   primality decisions, proper-factor descent, and bounded/public
   prime-divisor existence.
8. **Complete:** establish β modulus nonzeroness, bounded self-decoding, and
   decoded-value existence/uniqueness.
9. **Complete:** establish full additive/multiplicative balanced-congruence
   compatibility, bounded representative uniqueness, both remainder/
   congruence directions, and equivalence of β decoding with bound plus
   congruence.
10. **Complete:** project balanced Bézout coefficients into modular inverse
    equations, prove constructive binary CRT and its bounded-residue wrapper,
    and construct two β positions under an explicit modulus-coprimality
    premise.
11. **Complete:** prove conditional β-modulus coprimality when the ordered
    index gap divides `c`, discharge the two-position CRT premise, and
    construct nonzero bounded common multiples.
12. **Complete:** prove bounded-prefix pairwise coprimality, coprime-product
    closure, modulus descent, and one invariant-preserving binary CRT fold
    step.
13. **Complete:** advance accumulated-product and decoded-congruence
    invariants together, fold them through a bounded prefix by ordinary
    induction, and expose the result for values already decoded from a
    supplied `BetaAt` code. This does not code an arbitrary finite sequence.
14. Prove genuine prefix-product recurrence and bounds, then β finite-prefix
    recoding and the product gate; develop greatest-prime-divisor descent for
    the later sorted-factorization construction.

Prime-divisor existence does not follow automatically from gcd or Bézout, and
Euclid's lemma does not construct a prime divisor; both sides are now checked
independently. The existing-code prefix wrapper does not supply arbitrary
finite sequences or genuine prefix products for FTA.
