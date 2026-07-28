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

The 119-theorem candidate includes a complete relational API through
uniqueness:

- symmetry and both input-divisibility projections;
- extraction of the greatest-common-divisor clause;
- a constructor showing that $a$ is a gcd of $a,b$ whenever $a\mid b$;
- mutual-divisibility antisymmetry and uniqueness of relational gcds;
- factor-one rigidity and the fact that every divisor of one is one; and
- both directions between the expanded common-divisor definition of
  coprimality and $\operatorname{IsGCD}(1,a,b)$.

All fifteen new certificates are constructive. The largest,
`is_gcd_unique`, has 600 proof nodes and depth 51.

Gcd **existence** is a different theorem and is not yet in `pa lib`.

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

An independently checked prototype proves this by induction on the two
multipliers. It supports the following candidate ladder:

| Candidate | Meaning | Expanded proof nodes |
|---|---|---:|
| `factor_difference` | remove a common multiple prefix | 250 |
| `divides_remainder` | $c\mid a$ and $c\mid b$ imply $c\mid r$ | 378 |
| `divides_linear_step` | $c\mid b$ and $c\mid r$ imply $c\mid bq+r$ | 194 |
| `is_gcd_euclid_forward` | $\operatorname{IsGCD}(d,b,r)\to\operatorname{IsGCD}(d,a,b)$ | 586 |
| `is_gcd_euclid_backward` | the converse direction | 586 |

These metrics are research evidence, not library authority. Admission still
requires the ordinary source, catalog, artifact, test, and documentation gate.

## A concrete strong-induction surrogate

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

The authored bounded proof closes against its dependency-curried goal in 90
nodes. Current dependency substitution corrupts the resulting closed tree
(1,024 nodes before and 971 after reduction), which the independent kernel
rejects. This is a proof-composition defect, not a mathematical or PA
expressibility failure, so gcd existence remains unadmitted.

The reviewed remedy is a self-contained derived proof node

```text
Cut(A, B, lemma, body)
```

whose checker rule verifies `lemma : A` in the ambient context and verifies
`body : B` with `A` as a new hypothesis. It contains no theorem names, hashes,
or external theorem authority. Because this changes the trusted checker, it
must land as its own audited milestone.

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
x'_+=y_+,qquad
y'_+=x_+ + qy_-,qquad
x'_-=y_-,qquad
y'_-=x_- + qy_+.
$$

An independently checked 918-node prototype proves the maximality bridge:
if $c$ divides $a$ and $b$, then a balanced combination equal to $d$ implies
$c\mid d$. The efficient recursive theorem should therefore construct the two
divisibility witnesses and the four coefficients simultaneously; maximality
then turns it into `IsGCD`.

After this gate, the route is balanced Bézout $\to$ Gauss cancellation
$\to$ Euclid's lemma. Prime-divisor existence is a separate bounded-search
milestone, and finite factorization still requires the selected β-coded
sequence/product layer.
