# Constructive strict descent and the complete Fermat-four theorem

Date: 2026-08-27. Parent: immutable Alpha v25, together with the additive
coprime-square-factor and primitive-Pythagorean-inverse candidates in this
first-wave tranche. The original first-order Heyting-arithmetic kernel and all
historical evidence remain unchanged.

## Exact mathematical endpoints

The campaign G078 endpoint is now a real proof body of

```text
forall x y z.
  ~(x = 0) -> ~(y = 0) ->
  ~(x*x*x*x + y*y*y*y = z*z).
```

The quantified height `z` is arbitrary: no hypothesis `z != 0`, primitive
condition, inverse-parametrization assumption, or unproved descent premise
survives in this endpoint. The theorem name is
`fermat_four_positive_sum_not_square`.

The stronger natural-solution classification is also proved:

```text
x^4 + y^4 = z^4
  iff ((x = 0 and y = z) or (y = 0 and x = z)).
```

Here fourth powers and `iff` are display notation only. The checked statement
uses four ordinary multiplications and the conjunction of the two implications.
The theorem name is `fermat_four_complete_classification`.

The historically explicit open premise `fermat_four_strict_descent(tag=...)`
is separately discharged by `fermat_four_strict_descent_proved`. This is the
exact same expanded formula up to renaming its bound variables; the candidate
does not replace it with a weaker condition.

## Conservative definition structure

All definitions are transparent expansions into `{0,S,+,*,=}` and ordinary
intuitionistic quantifiers and connectives:

- `FermatFourCounterexample(a,b,h)` is the historical relation: all three
  coordinates are nonzero and `a^4+b^4=h^2`.
- `PrimitiveFermatFourCounterexample(a,b,h)` conjoins that relation with the
  existing common-divisor definition of `Coprime(a,b)`.
- `SmallerFermatFourCounterexample(A,B,H,h)` conjoins a real positive
  counterexample at `H` with an explicit natural gap `k+S(H)=h`.
- `TrivialFermatFourSolution(a,b,h)` is exactly
  `(a=0 and b=h) or (b=0 and a=h)`.

Thus the definition DAG shares the existing positivity, coprimality,
counterexample, and strict-order concepts. There is no primitive Fermat
predicate or hidden solver fact. Public helper arguments and tags are checked
for invalid syntax and binder capture; changing a tag preserves the parsed
formula up to bound-variable renaming.

## Actual arithmetic descent

Given a positive counterexample `(a,b,h)`, choose the constructive relational
gcd `d` of `a,b`, and its positive coprime quotients `A,B`. Explicit
product-square identities show `d^4 | h^2`. The checked square-divisibility
reflection theorem constructs `H` with `h=d^2 H`; cancellation gives
`A^4+B^4=H^2`, and `H<=h`. This is a constructed normalization witness,
not an assumption that the initial bases were coprime.

For a primitive counterexample, constructive parity selection puts its square
legs in odd-even order. The first actual Pythagorean inverse constructs
positive ordered coprime parameters `m,n` with

```text
h = m^2+n^2,
m^2 = n^2+a^2,
b^2 = 2mn.
```

The square-gap coprimality theorem makes `(a,n,m)` a second primitive
Pythagorean triangle. Its hypotenuse `m` is odd. Therefore coprime
square-product extraction from `b^2=m(2n)` constructs

```text
m = u^2,   n = 2v^2.
```

This step proves that the square root of `2n` is even by constructive parity
cases; it does not infer parity from an unproved factorization rule.

Apply the checked odd-even inverse a second time, now to `(a,n,m)`, obtaining
positive coprime `r,s` with

```text
m = r^2+s^2,   n = 2rs.
```

Cancelling two gives `rs=v^2`. Coprime square-product extraction constructs
positive `C,D` with `r=C^2`, `s=D^2`. Consequently

```text
C^4+D^4 = u^2.
```

The explicitly witnessed estimate `u<=u^2=m<=m^2<m^2+n^2=h` constructs the
strictly smaller height. Combining this with gcd normalization constructs a
strictly smaller counterexample from every possible initial counterexample.

Only after that construction is complete do the final two rows instantiate
the historical checked bounded-induction descent theorem. Decidable equality
of naturals then includes the zero boundary; injectivity of natural squaring
gives the complete exponent-four solution classification.

## Exact verification inventory

The candidate contributes 26 dependency-ordered theorem bodies, 93 direct
dependency edges, and 852 tactic commands. Independent original-kernel
checking accepts all 26 dependency-curried bodies: 1,515 structural proof
nodes in total, maximum body size 226 nodes, maximum depth 45.

The ordered-name SHA-256 is
`08f056f73a80bab76d79464c97e7c4632e6b09cb2fbb3a00c6706f4c29d4edba`.

The key exact expanded-statement hashes are:

| Theorem | SHA-256 |
| --- | --- |
| `fermat_four_primitive_normalization` | `cc973a8899e25fcdd918ae57abfb71a29e25cf64056588f3f755231a3ff4902a` |
| `fermat_four_strict_descent_proved` | `a3d8f109acbc3a7a254ad16d0bd5560807da349e8e7d6dabc5bb727dbafde85e` |
| `fermat_four_no_square` | `2931b656d7b3fa9d5a7abb43237803705f1871882fa07e14f5caac2d7d348786` |
| `fermat_four_no_fourth` | `9c058a04f2efb7f105017c15d34a94522937627b0008a4ea06305b66e0077cde` |
| `fermat_four_complete_classification` | `92c99d3f0a218c2706416d7c8b362aee310df0db1180729b85165d4ab11788bd` |
| `fermat_four_positive_sum_not_square` | `ae59505ab1243e444869a6385357022e648728cb483e36ae9f97a1f0a404409b` |

The focused test suite contains 95 passing tests. It checks every actual
body, corrupts every final tactic step, removes the essential inverse
dependency, attempts the false strengthening that omits base positivity,
checks the exact historical strict-descent formula and exact G078 endpoint,
and checks definition hygiene. Small natural examples include every zero
boundary; they are supplementary checks, never proof certificates.

The source is
`peano-lab/py/peano_lab/library/fermat_four_descent_candidate.py` and the audit
is `peano-lab/py/tests/test_fermat_four_descent_candidate.py`.

These local receipts alone do not confer Alpha or Stable authority. Separate
first-wave closure must reconstruct the full historical dependency cone,
check the original kernel bundle and compiled Lean verifier, and bind the
exact source, tests, RFC, statement hashes, and proof nodes before admission.
Stable remains unchanged.
