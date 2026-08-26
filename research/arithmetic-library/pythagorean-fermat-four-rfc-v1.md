# D2/D3 — constructive Pythagorean and Fermat-four descent foundations

Status: **17 independently kernel-checked dependency-curried candidate proof
bodies**. No new candidate is enrolled in Alpha or Stable. No full primitive
classification and no unconditional Fermat exponent-four theorem are claimed.

## Exact first-order definitions

All formulas expand into the unchanged intuitionistic arithmetic language
`{0, S, +, *, =}`:

```text
Pythagorean(x,y,z) := x*x + y*y = z*z

Coprime(x,y) :=
  forall d. (exists a. x = d*a) -> (exists b. y = d*b) -> d = 1

PrimitivePythagorean(x,y,z) :=
  Pythagorean(x,y,z) /\ Coprime(x,y)

FermatFourCounterexample(x,y,z) :=
  x != 0 /\ y != 0 /\ z != 0 /\ x*x*x*x + y*y*y*y = z*z
```

None is installed as a new trusted predicate, axiom, host-language decision,
or classical excluded-middle principle.

## Completed Euclidean forward constructor

The existing actual Brahmagupta--Fibonacci identity gives the subtraction-free
Euclidean identity:

```text
m*m = n*n + d
  -> d*d + (2*(m*n))*(2*(m*n)) = (m*m+n*n)*(m*m+n*n).
```

The checked theorem `pythagorean_square_gap_from_order` constructs `d` from
every witnessed natural inequality `n <= m`. Consequently
`pythagorean_euclidean_from_order` supplies an explicit Pythagorean triple for
every ordered pair of natural Euclidean parameters. Additional checked bodies
prove symmetric cross products, both leg orders, uniqueness of the difference
witness, an explicit even leg, incompatibility of that leg with an odd witness,
nonzero hypotenuses, symmetric coprimality, and primitive-triple leg symmetry.

Examples include `(3,4,5)`, `(5,12,13)`, `(15,8,17)`, `(7,24,25)`,
`(21,20,29)`, `(9,40,41)`, and `(35,12,37)`. Host numerical examples are
illustrations only; theorem authority comes exclusively from the unchanged
independent intuitionistic kernel.

## Exact remaining Fermat-four obligation

The separate finite-descent premise is:

```text
forall x y z. FermatFourCounterexample(x,y,z)
  -> exists a b c.
       FermatFourCounterexample(a,b,c)
       /\ exists gap. gap + S(c) = z.
```

`fermat_four_bounded_descent` proves by ordinary bounded natural induction
that this premise rules out a counterexample with any bounded hypotenuse.
`fermat_four_no_square_from_descent` consequently proves the stronger
square-hypotenuse prohibition **under the exact displayed premise**.
`fermat_four_no_fourth_from_descent` then derives Fermat's exponent-four
prohibition **under the same premise**, by regrouping the right fourth power
as the square of a square.

The strict descent premise remains unproved: extracting a smaller positive
counterexample requires the reverse primitive-triple classification, the
coprime-square-product splitting lemma, and constructive parity/gcd
normalization. **No full primitive classification** is claimed.
**No unconditional Fermat exponent-four theorem** is claimed.

## Review and release boundary

The candidate source is
[`pythagorean_fermat_four_candidate.py`](../../peano-lab/py/peano_lab/library/pythagorean_fermat_four_candidate.py).
The focused source, formula, mutation, exact-receipt, example, and evidence
audit is
[`test_pythagorean_fermat_four_candidate.py`](../../peano-lab/py/tests/test_pythagorean_fermat_four_candidate.py).

Every statement is closed, every dependency occurs earlier in the candidate
list or the unchanged sealed Alpha v13 release, every actual proof body has at
most 63 structural kernel nodes, and formula/script mutations fail closed.
No Alpha/Stable enrollment, empty-context closure, checked theorem use,
unconditional inverse parametrization, or unproved descent step is inferred.
