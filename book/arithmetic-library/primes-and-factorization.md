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

The remaining prime layer should establish:

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
The division algorithm supports existence; divisibility antisymmetry supports
uniqueness. A signed-pair Bézout equation then connects gcd to coprimality
without importing integers into the kernel language.

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

Peano Lab currently has none of these data interfaces. Consequently the
Fundamental Theorem of Arithmetic is marked `blocked_by_language`, with
`finite_factorization_representation` as its explicit missing dependency.

## The representation milestone

Three designs are possible:

| Design | Advantage | Cost |
|---|---|---|
| Gödel-coded sequences inside first-order arithmetic | No kernel-language extension | Long, opaque interfaces poorly suited to everyday reuse |
| Conservative sequence predicate over encoded naturals | Keeps the term grammar fixed | Still requires a substantial coding library and bounded-index relations |
| Reviewed finite-list/multiset layer | Natural theorem statements and permutation reasoning | Adds data syntax and needs a separate soundness review |

The plan prefers a reviewed finite-sequence or multiset layer, with translation
to ordinary kernel evidence made explicit. A companion proof in a mature
system can cross-check the theorem, but it cannot substitute for Peano's own
certificate.

## What “include FTA” means in this release

FTA is included as a fully specified destination:

- its prerequisite graph is recorded;
- its mathematical existence and uniqueness halves are separated;
- the exact current-language blocker is named;
- source curricula are mapped to the missing lemmas;
- no unchecked or admitted theorem is exposed through `pa lib`.

That is more useful than a ceremonial theorem name with hidden trusted
machinery. Future milestones can discharge the graph one interface at a time.
