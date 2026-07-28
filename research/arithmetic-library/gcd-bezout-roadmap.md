# Native gcd and balanced Bézout roadmap

## Status boundary

The checked runtime currently exposes the relational gcd/coprimality API
through uniqueness, the zero-right gcd base case, and both directions of
Euclidean-step invariance. It does **not** yet expose gcd existence, Bézout,
Gauss cancellation, or Euclid's lemma.

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
  `is_gcd_euclid_backward`.

The largest new certificate is `is_gcd_unique` at 600 proof nodes and depth
51. Every entry replays constructively and checks from the empty context.

## Checked Euclidean invariance

The runtime now contains closed, independently kernel-accepted certificates
for the subtraction-free Euclidean ladder. Their authored scripts, catalog
records, generated artifacts, and regression tests are admitted together as
ordinary native library entries.

| Checked theorem | Role | Expanded nodes |
|---|---|---:|
| `is_gcd_zero_right` | base case `IsGCD(a,a,0)` | 45 |
| `factor_difference` | from `c*u = c*v + r`, construct `c | r` | 250 |
| `divides_remainder` | common divisors of `a,b` divide `r` when `a=b*q+r` | 378 |
| `divides_linear_step` | divisors of `b,r` divide `b*q+r` | 194 |
| `is_gcd_euclid_forward` | `IsGCD(d,b,r) -> IsGCD(d,a,b)` | 586 |
| `is_gcd_euclid_backward` | `IsGCD(d,a,b) -> IsGCD(d,b,r)` | 586 |

The key subtraction-free lemma is

```text
forall c u v r.
  c * u = c * v + r ->
  exists w. r = c * w
```

Its proof inducts simultaneously through the two multiples rather than
forming a natural-number subtraction. With it, both directions of Euclidean
invariance are ordinary divisibility algebra.

## Formula-specific strong induction for gcd existence

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

This bounded script closes against its dependency-curried target in 90 nodes.
The current dependency inliner, however, produces a 1,024-node substituted
tree (971 after reduction) which the independent kernel correctly rejects.
This is an implementation defect in capture-sensitive dependency substitution
around induction—not a mathematical, expressibility, or resource-limit
failure. Consequently no gcd-existence theorem is admitted yet.

Two sound remedies are under review:

- repair and exhaustively regression-test the existing substitution reducer;
  or
- add the self-contained derived rule
  `Cut(A,B,lemma,body)`, whose two branches are both checked by the kernel and
  which contains no theorem names, hashes, or external authority.

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

The maximality bridge is already prototype-checked: if `c` divides both `a`
and `b`, any balanced combination equal to `d` gives `c | d`. Its expanded
certificate has 918 nodes. Thus the most efficient recursive theorem should
construct divisibility witnesses and balanced coefficients simultaneously;
the bridge then supplies the greatest-common-divisor clause.

## Admission gates

1. **Complete:** admit and mutation-test the Euclidean invariance ladder.
2. Land reviewed proof sharing or a fully verified reducer repair.
3. Admit bounded gcd existence and its public wrapper.
4. Prove the coefficient-update identity with an ordinary checked semiring
   certificate; library replay cannot treat `ring` as an oracle.
5. Admit balanced gcd/Bézout existence, derive maximality, then prove Gauss
   cancellation.
6. Develop prime-divisor existence separately by bounded search/strong
   induction before combining it with Gauss to obtain Euclid's lemma.

Prime-divisor existence does not follow automatically from gcd or Bézout, and
none of these steps yet supplies finite sequences or products for FTA.
