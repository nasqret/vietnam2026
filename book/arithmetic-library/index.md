# The foundational arithmetic library

This part turns Peano Lab's original theorem ladder into a general-purpose,
dependency-organized arithmetic library. The fourth-power-modulo-five exercise
was a useful stress test, but it is now only one possible application. The
organizing spine is reusable mathematics:

$$
\text{equality}
\to \text{semiring laws}
\to \text{order}
\to \text{divisibility}
\to \text{congruence}
\to \gcd
\to \text{primes}
\to \text{factorization}.
$$

The first public snapshot contains **51 replayed, closed, independently
kernel-checked Peano theorems**. Twenty-eight are the new foundational layer:
named equality congruences, additive cancellation and order facts,
zero-sum and nonzero-product facts, a small-factor obstruction, divisibility
closure, constructive non-divisibility normal forms, and generic
quotient-and-remainder algebra. This layer includes `prime_two`, the first
checked instance of the fully expanded prime predicate. Every theorem fits the
browser's ordinary `use` limit; the largest new certificate has 1,601 nodes
and depth 59, below the 4,096-node/depth-128 bound.

That number is deliberately narrower than the 75-node research catalog: 23
nodes are `checked_existing`, 28 are `checked_m20`, 20 are
`planned_expressible`, and four are `blocked_by_language`. Beyond
`prime_two`, the catalog records candidate lemmas on modular congruence,
division, gcd, coprimality, the general prime spine, Euclid's lemma, and prime
factorization. Those entries are not presented as proved until a script and
closed certificate pass the same kernel gate.

## How to read the status labels

| Label | Meaning |
|---|---|
| `checked_existing` | Already in the original 23-theorem Peano ladder. |
| `checked_m20` | Added in this foundational release and independently checked. |
| `planned_expressible` | Stateable in today's first-order Peano language, but not yet admitted. |
| `blocked_by_language` | Needs a reviewed representation such as finite sequences or powers before it can be stated honestly. |

There is no status called “obvious.” A familiar mathematical fact and a
checked theorem are different repository objects.

## Reading route

1. {doc}`Language, notation, and trust <language-and-trust>` explains why
   divisibility and primality are expanded formulas rather than new kernel
   predicates.
2. {doc}`The dependency ladder <dependency-ladder>` gives the complete
   architecture from equality through factorization.
3. {doc}`Divisibility and congruence <divisibility-and-congruence>` develops
   the checked first layer and the balanced natural-number encoding of modular
   congruence.
4. {doc}`Primes and unique factorization <primes-and-factorization>` separates
   what can be formalized now from the finite-sequence milestone needed for a
   clean Fundamental Theorem of Arithmetic.
5. {doc}`Sources and clean-room provenance <source-audit>` maps the Natural
   Number Game, *The Mechanics of Proof*, and *An Illustrated Theory of
   Numbers* into the corpus without silently copying material.
6. {doc}`Using and extending the library <using-the-library>` shows the live
   workflow and the admission contract.

## Four synchronized views

One stable theorem name is intended to identify the same object in four views:

- the executable `TheoremSpec` and its kernel-checked certificate;
- the generated JSON snapshot and Mermaid dependency graph;
- the explanatory Jupyter Book anchor;
- the atomic Obsidian concept or lemma note.

The generated artifact binds the exact statement, dependency list, tactic
script, certificate representation hash, node count, depth, and one ordered
root digest. These hashes make drift visible; they do not grant authority.
Authority still comes only from checking the closed proof term against the
closed formula.
