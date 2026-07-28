# Primes and unique factorization

Prime numbers are a major destination of the library, but they are not a
primitive. Their useful theory rests on divisibility, order, induction,
division, and gcd.

## A first-order prime definition

Writing $d\mid p$ for its existential expansion, define

$$
\operatorname{Prime}(p)
\;:\!\Longleftrightarrow\;
p\ne1\land\forall a\,b.\bigl(p=a\cdot b\to a=1\lor b=1\bigr).
$$

This factor-pair definition is stateable in Peano Lab now and is equivalent
over the naturals to the usual divisor formulation. A readable `Prime p`
surface form would be only a macro; the stored theorem and final checker target
contain the expanded quantifiers and multiplication equality.

The first concrete instance is already checked:

```text
prime_two : ~(2 = 1) /\ forall a b. 2 = a * b -> a = 1 \/ b = 1
```

Its proof depends on `two_large_factors_impossible`; neither theorem adds a
trusted primality oracle or a primitive `Prime` atom.

The checked division layer now supplies constructive quotient-remainder
existence and uniqueness. The remaining prime layer should establish:

1. zero and one are not prime;
2. a non-prime number at least two has a proper nontrivial divisor;
3. every number at least two has a prime divisor, by strong induction;
4. a prime dividing a product divides one factor, after the gcd/Bézout layer;
5. there are primes above every bound.

These claims are expressible today, but they are catalog targets rather than
checked entries in the first snapshot.

## GCD without a gcd function

Use the relational specification

$$
\operatorname{IsGCD}(g,a,b)
$$

to say that $g$ divides $a$ and $b$, and every common divisor divides $g$.
The checked API now provides symmetry, both divisibility projections, the
greatest-common-divisor projection, a constructor when one input divides the
other, and `is_gcd_unique`. Its uniqueness proof uses the checked
`multiple_antisymm`; gcd existence remains a separate Euclidean-descent
milestone. The unit bridge proves `mul_eq_one_components`, divisors of one,
coprimality with one on both sides, and both directions between expanded
coprimality and `IsGCD(1,a,b)`.

A balanced four-natural Bézout equation will connect the eventual gcd
existence proof to Gauss cancellation without importing integers into the
kernel language.

The exact next statements, prototype certificate metrics, bounded-induction
construction, and balanced coefficient transport are developed in
{doc}`GCD and balanced Bézout construction <gcd-and-bezout>`.

The key route is

$$
\operatorname{IsGCD}(1,a,p)
\to \text{Bézout witness}
\to p\mid ab\Rightarrow p\mid b,
$$

when $p$ is prime and $p\nmid a$. Together with the case $p\mid a$, this is
Euclid's lemma.

## Existence and uniqueness are different theorems

Factorization existence follows by strong induction: a number at least two is
prime, or it splits into smaller nontrivial factors which factor recursively.
Uniqueness uses Euclid's lemma to match one prime from one factorization with a
prime in the other, cancel it, and continue.

That familiar paper proof quietly quantifies over finite products. An honest
formal statement needs a representation and theorems for:

- finite collections of natural numbers;
- the product of a collection;
- “every entry is prime”;
- permutation or multiplicity equality;
- deletion of a matched prime and product cancellation.

Peano Lab has no primitive data interface for these objects. The project now
has two deliberately separate results:

- a selected conservative Peano representation, using sorted Gödel β-coded
  factor sequences and a β-coded prefix-product trace; and
- an independently checked Lean companion proving the conventional finite-list
  theorem, including uniqueness up to permutation.

The companion closes the mathematical cross-check, but it does not turn the
unfinished Peano encoding lemmas into a `pa lib` theorem.

## The representation milestone

Three designs were compared:

| Design | Advantage | Cost |
|---|---|---|
| Gödel-coded sequences inside first-order arithmetic | No kernel-language extension | Long, opaque interfaces poorly suited to everyday reuse |
| Conservative sequence predicate over encoded naturals | Keeps the term grammar fixed | Still requires a substantial coding library and bounded-index relations |
| Reviewed finite-list/multiset layer | Natural theorem statements and permutation reasoning | Adds data syntax and needs a separate soundness review |

The selected Peano design is the first row: natural codes preserve the kernel
unchanged. For codes $b,c$, index $i$, and value $x$, define

$$
M(c,i)=1+(i+1)c,
\qquad
\operatorname{At}(b,c,i,x)
\;:\!\Longleftrightarrow\;
x<M(c,i)\land\exists q.\;b=qM(c,i)+x.
$$

A second code stores the prefix products, beginning at one and multiplying by
the decoded factor at each step. `AllPrime` expands the factor-pair prime
formula at every bounded index, and `Sorted` makes the representation
canonical by decoded values. Codes themselves are never equated because one
finite prefix can have more than one β-code.

The selected formula schemas and dependency spine are recorded in
`research/arithmetic-library/finite-factorization-encoding.md`.

## The checked Lean theorem

The separate `artifacts/lean-fta/FTA.lean` project now proves:

```lean
theorem fundamental_theorem_of_arithmetic (n : ℕ) (hn : n ≠ 0) :
    ∃ factors : List ℕ,
      IsPrimeFactorization n factors ∧
      ∀ other : List ℕ,
        IsPrimeFactorization n other → other.Perm factors
```

The witness is `n.primeFactorsList`. Existence checks that its entries are
prime and its product is $n$; uniqueness proves that any other prime list with
product $n$ is a permutation of it. For $n=1$, the witness is the empty list.

The project pins Lean 4.23.0 and Mathlib commit
`37df177aaa770670452312393d4e84aaad56e7b6`. Its audit rejects `sorryAx` and
requires exactly the declared standard axioms `propext`, `Classical.choice`,
and `Quot.sound`. This makes the dependency footprint visible rather than
calling a library import “axiom-free.”

## What “include FTA” means in this release

This release contains two deliberately separate FTA forms:

- the Lean companion is a checked existence-and-uniqueness proof up to
  permutation, with no admission;
- the conservative Peano representation design and formula schemas are
  documented;
- source curricula are mapped to the missing lemmas;
- no external theorem is smuggled into `pa lib` as a Peano certificate.

The remaining Peano work starts by freezing and implementing the hygienic
macro expansions with round-trip tests. It then discharges the
gcd/Bézout/Euclid and β-coding lemmas and produces the two closed PA
certificates.
