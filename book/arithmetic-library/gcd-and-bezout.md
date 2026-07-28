# GCD and balanced Bézout construction

The native gcd layer uses a relation rather than a new function symbol. With
$d\mid n$ expanded as `exists q. n = d * q`, write

$$
\operatorname{IsGCD}(g,a,b)\;:\!\Longleftrightarrow\;
\bigl(g\mid a\land g\mid b\bigr)\land
\forall c,\;c\mid a\to c\mid b\to c\mid g.
$$

The grouping is part of the interface. Peano Lab parses repeated `/\`
left-associatively, so the stored formulas explicitly parenthesize the two
divisibility witnesses before the greatest-common-divisor clause.

## What is checked now

The 149-theorem runtime contains 23 baseline entries and 126 checked
post-baseline entries. One hundred and fourteen of the latter form the general
foundational layer; the other twelve are the fixed modular capstone. The
broader catalog has 158 nodes: those 149 checked entries, five planned
entries, and four blocked-by-language entries.

The checked gcd layer includes the relational API through uniqueness and
existence:

- symmetry and both input-divisibility projections;
- extraction of the greatest-common-divisor clause;
- a constructor showing that $a$ is a gcd of $a,b$ whenever $a\mid b$;
- mutual-divisibility antisymmetry and uniqueness of relational gcds;
- factor-one rigidity and the fact that every divisor of one is one; and
- both directions between the expanded common-divisor definition of
  coprimality and $\operatorname{IsGCD}(1,a,b)$; and
- bounded formula-specific gcd construction and unrestricted relational gcd
  existence.

Every gcd/coprimality, Euclidean-step, Bézout, and Gauss certificate is
constructive. No theorem in this layer uses integer coefficients, subtraction,
or classical logic.

## Euclidean invariance without subtraction

Suppose

$$a=bq+r.$$

The hard direction in the usual paper argument says that every common divisor
of $a$ and $b$ divides $r$. Naturals have no subtraction in this language, so
the proof uses the constructive lemma

```text
forall c u v r.
  c * u = c * v + r ->
  exists w. r = c * w
```

The checked native theorem `factor_difference` proves this by induction on the
two multipliers. It supports the following admitted ladder:

| Checked theorem | Meaning | Shared nodes/depth |
|---|---|---:|
| `is_gcd_zero_right` | base case $\operatorname{IsGCD}(a,a,0)$ | 65 / 11 |
| `factor_difference` | remove a common multiple prefix | 265 / 26 |
| `divides_remainder` | $c\mid a$ and $c\mid b$ imply $c\mid r$ | 427 / 29 |
| `divides_linear_step` | $c\mid b$ and $c\mid r$ imply $c\mid bq+r$ | 224 / 19 |
| `is_gcd_euclid_forward` | $\operatorname{IsGCD}(d,b,r)\to\operatorname{IsGCD}(d,a,b)$ | 741 / 38 |
| `is_gcd_euclid_backward` | the converse direction | 741 / 37 |

Each entry replays from its declared earlier dependencies and its
self-contained certificate checks from the empty context. Euclidean invariance supplies the
descent transport used by the separate checked existence construction; it did
not by itself provide an existence witness.

## Checked formula-specific strong induction

The object language has no predicate variables, so it cannot store one
polymorphic strong-induction theorem. For gcd existence, ordinary induction on
a bound $B$ can prove the concrete formula

$$
\forall B,b,\quad b\le B\to
\forall a,\;\exists d,\operatorname{IsGCD}(d,a,b).
$$

At the successor step, discrete order gives either $b\le B$ or $b=S B$. The
first branch uses the induction hypothesis. In the second, division supplies
$a=bq+r$ with $r<b=S B$, hence $r\le B$; the induction hypothesis factors the
smaller pair $(b,r)$ and Euclidean invariance transports its gcd back to
$(a,b)$.

The checked theorem `gcd_exists_up_to` is exactly this bounded construction.
Its authored body closes against the dependency-curried goal in 90 nodes. The
former dependency inliner corrupted the closed induction tree, which the
independent kernel correctly rejected. With reviewed self-contained sharing,
the theorem now checks constructively from the empty context at 1,232
nodes/depth 44.

The public `gcd_exists_relational` theorem specializes the bound to $B=b$.
The checked `le_refl` supplies

$$
\exists t.\;t+b=b,
$$

after which `gcd_exists_up_to` yields a gcd for arbitrary $a$ and $b$. This
wrapper also checks constructively from the empty context, at 1,268
nodes/depth 46. Neither theorem introduces subtraction, a gcd function, or
classical choice.

The reviewed remedy is the now-implemented self-contained derived proof node

```text
Cut(A, B, lemma, body)
```

whose checker rule verifies `lemma : A` in the ambient context and verifies
`body : B` with `A` as a new hypothesis. It contains no theorem names, hashes,
or external theorem authority. Because this changes the trusted checker, it
landed as its own audited milestone. It changes neither the arithmetic object
language nor the logic; {doc}`Self-contained proof sharing <proof-sharing>`
records the exact trust and erasure boundary. The two existence theorems now
complete the arithmetic admission that this architecture was designed to
support.

## Bézout with four natural coefficients

Signed integer coefficients are unnecessary. Define the balanced relation

$$
\exists x_+,y_+,x_-,y_-,\quad
a x_+ + b y_+
=d+\bigl(a x_-+b y_-\bigr).
$$

For $a=bq+r$, coefficients for $(b,r)$ transport to coefficients for $(a,b)$
by

$$
x'_+=y_+,\qquad
y'_+=x_+ + qy_-,\qquad
x'_-=y_-,\qquad
y'_-=x_- + qy_+.
$$

The checked `balanced_bezout_euclid_step` theorem proves this identity using
only ordinary semiring equalities. The small `add_permute_outer` helper makes
the balanced equation available as an exact subterm; neither theorem invokes
`ring` as an oracle.

## Simultaneous bounded construction

The admitted bounded motive strengthens the earlier gcd-only construction to

$$
\forall B,b,\quad b\le B\to\forall a,\;\exists d,\quad
\operatorname{IsGCD}(d,a,b)\land\operatorname{BalancedBezout}(d,a,b).
$$

At $B=0$, $b=0$, so $d=a$ and coefficients $(1,0,0,0)$ close the balanced
equation. At a successor bound, the branch $b\le B$ uses the induction
hypothesis directly. In the boundary branch $b=S B$, division gives
$a=bq+r$ and $r<b$, hence $r\le B$. The induction hypothesis supplies both a
full `IsGCD(d,b,r)` proof and balanced coefficients for $(b,r)$.
`is_gcd_euclid_forward` transports the complete relational gcd proof, while
`balanced_bezout_euclid_step` transports the coefficients.

This distinction matters: `common_divisor_divides_balanced_result` is not used
to manufacture the greatest-divisor clause in the bounded proof. It is a
separate bridge used downstream in Gauss cancellation.

The unrestricted `gcd_balanced_bezout_exists` theorem takes $B=b$, exactly as
`gcd_exists_relational` does. Coprimality then forces the constructed gcd to be
one, yielding `coprime_balanced_bezout`.

## From balanced Bézout to Gauss

The scale theorem has the precise semantic form

$$
\operatorname{BalancedBezout}(d,a,b)
\Longrightarrow
\operatorname{BalancedBezout}(dz,a,bz).
$$

Its stored name is `balanced_combination_scale_right`; the displayed formula
clarifies that the second input and balanced result are scaled, while the
first input absorbs $z$ into its positive and negative coefficients.

The checked `common_divisor_divides_balanced_result` theorem says that if
$c\mid a$, $c\mid b$, and a balanced equation has result $d$, then $c\mid d$.
Applied to the scaled result-one equation, with inputs $a$ and $bz$, it proves

$$
\operatorname{Coprime}(a,b)\land a\mid bz\Longrightarrow a\mid z.
$$

This is the admitted `gauss_coprime_cancel` theorem. The complete new ladder
has the following shared-certificate metrics:

| Checked theorem | Role | Nodes/depth |
|---|---|---:|
| `add_permute_outer` | four-summand additive permutation | 149 / 15 |
| `balanced_bezout_euclid_step` | coefficient transport across $a=bq+r$ | 880 / 35 |
| `gcd_balanced_bezout_exists_up_to` | bounded simultaneous gcd/Bézout descent | 2,233 / 45 |
| `gcd_balanced_bezout_exists` | unrestricted simultaneous existence | 2,269 / 47 |
| `balanced_combination_scale_right` | scale the balanced result and second input | 754 / 28 |
| `common_divisor_divides_balanced_result` | recover divisibility of the result | 626 / 39 |
| `coprime_balanced_bezout` | balanced result-one witnesses for coprime inputs | 2,304 / 48 |
| `gauss_coprime_cancel` | cancel a coprime factor from divisibility | 3,800 / 51 |
| `prime_divisor_eq_one_or_self` | every divisor of a prime is one or that prime | 57 / 12 |
| `euclid_prime_dvd_product` | a prime divisor of a product divides a factor | 5,382 / 55 |

Every certificate checks from the empty context in the intuitionistic kernel.
Euclid's lemma is developed in {doc}`Primes and unique factorization
<primes-and-factorization>`. The independent constructive search branch now
also checks bounded nontrivial-factor search, proper-factor descent, and
`prime_divisor_exists`. Finite factorization still requires greatest-prime
descent plus the selected β/CRT/prefix-product layer; native FTA is not yet
proved.
