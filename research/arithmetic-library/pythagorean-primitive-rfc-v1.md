# D2 — constructive primitive Pythagorean forward parametrization

Status: **27 independently kernel-checked dependency-curried candidate proof
bodies**, with at most **159 structural kernel nodes**. These 27 results extend
the existing 17 Pythagorean/Fermat-four foundation bodies to a 44-node campaign.
The forward primitive Euclidean parametrization is proved. The reverse inverse
parametrization remains unproved. The Fermat strict-descent premise remains
unproved. No Alpha/Stable enrollment or checked-use authority is claimed.

Fermat strict-descent premise remains unproved.

## Exact constructive hypotheses

All relations expand into the unchanged intuitionistic first-order arithmetic
language `{0, S, +, *, =}`. No gcd oracle, parity predicate, host-language
decision, classical excluded middle, new axiom, or trusted kernel rule is added:

```text
Even(n) := exists k. n = 2*k

Odd(n) := exists k. n = 2*k + 1

OppositeParity(m,n) :=
  (Even(m) /\ Odd(n)) \/ (Odd(m) /\ Even(n))

Coprime(m,n) :=
  forall d. (exists a. m = d*a) -> (exists b. n = d*b) -> d = 1

PrimitivePythagorean(x,y,z) :=
  (x*x + y*y = z*z) /\ Coprime(x,y)
```

The exact forward endpoint `pythagorean_primitive_euclidean_from_order` is:

```text
forall m n.
  (exists gap. gap + n = m)
    -> Coprime(m,n)
    -> OppositeParity(m,n)
    -> exists d.
         PrimitivePythagorean(d, 2*(m*n), m*m+n*n).
```

There are precisely three ordinary constructive hypotheses: witnessed order,
coprime parameters, and opposite parameter parity. No hidden inverse theorem,
unproved descent step, decidability assumption, or postulated primitive-leg
conclusion occurs. The subtraction-free difference witness satisfies
`m*m = n*n + d` and is supplied by the earlier actual forward constructor.

## Proved primitive-leg factor and parity ladder

The first parameter-parity bodies show that even squares remain even and odd
squares remain odd. Constructive exhaustive parity cases then prove that the
witnessed difference of opposite-parity squares is odd in either orientation:

```text
m*m = n*n + d /\ OppositeParity(m,n) -> Odd(d).

OppositeParity(m,n) -> Odd(m*m+n*n).
```

The actual prime-two theorem and the incompatibility of even/odd witnesses
prove `Odd(d) -> Coprime(d,2)`. Constructive remainder divisibility and
multiplicative closure of coprimality give:

```text
m*m = n*n + d /\ Coprime(m,n)
  -> Coprime(d,m)
  /\ Coprime(d,n)
  /\ Coprime(d,m*n).
```

Combining the last result with `Coprime(d,2)` proves the central endpoint
`pythagorean_primitive_euclidean_legs`:

```text
m*m = n*n + d
  -> Coprime(m,n)
  -> OppositeParity(m,n)
  -> Coprime(d,2*(m*n)).
```

The existing checked Brahmagupta-based Euclidean identity supplies the
Pythagorean equation itself. Consequently the full primitive constructor and
its swapped-leg form both have actual unchanged-kernel proof bodies.

## Necessary normal form of every primitive triple

The campaign also proves unconditional consequences of the *existing exact
primitive-triple premise*. First, any common divisor of a leg and hypotenuse
would also divide the other leg's square, contradicting coprimality of the
legs. Thus all three coordinates are pairwise coprime:

```text
PrimitivePythagorean(x,y,z)
  -> Coprime(x,y) /\ Coprime(x,z) /\ Coprime(y,z).
```

Primitive legs cannot both be even because two would be a common nonunit
divisor. Moreover, no Pythagorean triple at all can have two odd legs: odd
squares are one modulo four, their sum is two modulo four, and no square has
that residue. All residue contradictions are checked through constructive
bounded-remainder uniqueness, not external modular computation.

The resulting genuinely proved endpoints are:

```text
pythagorean_primitive_legs_opposite_parity:
  PrimitivePythagorean(x,y,z) -> OppositeParity(x,y).

pythagorean_primitive_hypotenuse_odd:
  PrimitivePythagorean(x,y,z) -> Odd(z).

pythagorean_primitive_normal_form:
  PrimitivePythagorean(x,y,z)
    -> OppositeParity(x,y)
       /\ Odd(z)
       /\ Coprime(x,y)
       /\ Coprime(x,z)
       /\ Coprime(y,z).
```

Examples include `(1,0,1)`, `(3,4,5)`, `(5,12,13)`, `(15,8,17)`,
`(7,24,25)`, `(21,20,29)`, `(9,40,41)`, `(35,12,37)`, and `(39,80,89)`.
The zero-leg `(1,0,1)` boundary is legitimate because primitiveness here
means coprime natural legs, not positivity of both legs. Numeric calculations
are examples only and never substitute for the independent proof checker.

## Exact remaining frontier

The forward primitive parametrization and necessary parity/coprimality normal
form are complete. The converse claim that every nondegenerate primitive
Pythagorean triple yields coprime opposite-parity Euclidean parameters is not
proved. In particular, constructive extraction of the two square factors from
the appropriate coprime half-sum/half-difference product is still outstanding.
The inverse parametrization remains unproved. The Fermat strict-descent premise
remains unproved, so no unconditional Fermat exponent-four theorem follows.

The candidate source is
[`pythagorean_primitive_candidate.py`](../../peano-lab/py/peano_lab/library/pythagorean_primitive_candidate.py).
The focused exact-statement, unchanged-kernel, dependency, mutation, parity,
boundary-example, and evidence audit is
[`test_pythagorean_primitive_candidate.py`](../../peano-lab/py/tests/test_pythagorean_primitive_candidate.py).

Every dependency belongs to sealed Alpha v15, the preceding 17 Pythagorean
candidate bodies, or an earlier row of this exact 27-row factory. Statements
and scripts remain outside both release channels: **No Alpha/Stable enrollment**,
empty-context closure, checked theorem use, complete inverse classification, or
unconditional Fermat descent is inferred.
