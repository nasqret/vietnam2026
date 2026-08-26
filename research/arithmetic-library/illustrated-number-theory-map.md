# Illustrated Theory of Numbers companion-source map

## Purpose and scope

This note maps Martin H. Weissman's computational number-theory notebooks to
current and future Peano library layers and documentation artifacts. The notebooks are an
algorithm and example index, not a source of trusted proofs or MIT-licensed
code.

The audit covers the official companion page and notebook repository at the
immutable revision
[`5e819522e52e6a75c5dec597f024729bfc9ba4c5`](https://github.com/MartyWeissman/Python-for-number-theory/tree/5e819522e52e6a75c5dec597f024729bfc9ba4c5),
checked on 2026-07-28.

## Pinned provenance and licensing

| Field | Value |
|---|---|
| Source IDs | `weissman_illustrated_programming`, `weissman_python_number_theory` |
| Companion page | [Programming resources](https://illustratedtheoryofnumbers.com/prog.html#notebooks) |
| Repository | [`MartyWeissman/Python-for-number-theory`](https://github.com/MartyWeissman/Python-for-number-theory) |
| Revision | `5e819522e52e6a75c5dec597f024729bfc9ba4c5` |
| Notebook license | [GNU GPL version 3](https://github.com/MartyWeissman/Python-for-number-theory/blob/5e819522e52e6a75c5dec597f024729bfc9ba4c5/LICENSE) |
| Published book | [AMS, *An Illustrated Theory of Numbers*](https://bookstore.ams.org/mbk-105/) |
| Peano reuse mode | `algorithm_index_clean_room` |

The repository README explicitly identifies the notebooks as GPLv3. Do not
copy or adapt notebook code, prose, outputs, or exercises into the MIT Peano
project. Linking to the notebooks, recording topic coverage, and independently
implementing standard algorithms and proofs are the intended uses.

The AMS book is publisher-controlled. Its prose, illustrations, layout, and
source are not open project assets. The companion resources do not expose an
explicitly licensed TeX source for the book. No book or notebook source is
vendored here.

## Notebook inventory

The repository contains parallel Python 2 and Python 3 notebook series. The
Python 3 sequence is the clearest current subject index.

| Notebook | Primary topics | Formal-library destination |
|---|---|---|
| [Part 1](https://github.com/MartyWeissman/Python-for-number-theory/blob/5e819522e52e6a75c5dec597f024729bfc9ba4c5/P3wNT%20Notebook%201.ipynb) | Exact integer arithmetic, quotient/remainder operations, divisibility tests, Boolean logic, finite iteration | Arithmetic foundations, divisibility, executable examples |
| [Part 2](https://github.com/MartyWeissman/Python-for-number-theory/blob/5e819522e52e6a75c5dec597f024729bfc9ba4c5/P3wNT%20Notebook%202.ipynb) | Euclidean algorithm and linear Diophantine equations | Division algorithm, relational gcd, Bézout, coprimality |
| [Part 3](https://github.com/MartyWeissman/Python-for-number-theory/blob/5e819522e52e6a75c5dec597f024729bfc9ba4c5/P3wNT%20Notebook%203.ipynb) | Primality testing, sieve of Eratosthenes, prime counting, prime gaps | Prime definitions and theorems; later verified algorithms |
| [Part 4](https://github.com/MartyWeissman/Python-for-number-theory/blob/5e819522e52e6a75c5dec597f024729bfc9ba4c5/P3wNT%20Notebook%204.ipynb) | Prime-decomposition dictionaries and multiplicative functions | Fundamental theorem of arithmetic, valuations, arithmetic functions |
| [Part 5](https://github.com/MartyWeissman/Python-for-number-theory/blob/5e819522e52e6a75c5dec597f024729bfc9ba4c5/P3wNT%20Notebook%205.ipynb) | Modular arithmetic, fast exponentiation, Fermat's theorem, Miller--Rabin | Congruence algebra, powers, Fermat layer, algorithm specifications |
| [Part 6](https://github.com/MartyWeissman/Python-for-number-theory/blob/5e819522e52e6a75c5dec597f024729bfc9ba4c5/P3wNT%20Notebook%206.ipynb) | Primitive roots, Sophie Germain primes, Diffie--Hellman | Finite multiplicative groups and applications; long-term layer |
| [Part 7](https://github.com/MartyWeissman/Python-for-number-theory/blob/5e819522e52e6a75c5dec597f024729bfc9ba4c5/P3wNT%20Notebook%207.ipynb) | Euler's totient, Euler's theorem, modular inverses, RSA | Totient/counting, modular exponentiation, cryptographic application docs |

Notebook execution demonstrates algorithms on examples; it does not provide
a proof certificate for a general theorem. Numerical outputs may become
independently generated regression vectors, but they are not mathematical
dependencies.

## Formalization map

### Division and Euclidean algorithms

Formalize the mathematical specifications before any executable algorithm:

1. quotient/remainder existence and uniqueness;
2. remainder bounds and the remainder-zero divisibility criterion;
3. relational `IsGCD` existence and uniqueness;
4. Euclidean-step invariance;
5. a subtraction-free natural formulation of Bézout;
6. correctness and termination specifications for an eventual executable
   implementation.

The Python loop structure is not to be translated. A Peano proof should arise
from induction and the checked quotient/remainder lemmas.

The subtraction-free four-natural balanced Bézout relation is checked. A
conventional integer-coefficient interface remains unavailable because the
native term language has no integer or subtraction terms.

### Primality and sieving

Separate mathematical facts from algorithm claims:

- foundational facts: prime definition, proper factor of a composite,
  existence of a prime divisor, Euclid's lemma, and infinitude of primes;
- decision specifications: trial division bounds and correctness of a
  bounded primality test;
- data algorithms: sieve soundness and completeness over a finite bound;
- analytic experiments: prime counts and gaps, which belong in notebooks or
  data artifacts rather than the theorem ladder unless a precise theorem is
  selected.

The first foundational and decision layer is now substantially native:
`eq_decidable`, `multiple_decidable_nonzero`, and `multiple_decidable` support
`factor_search_up_to`; that bounded search feeds `prime_or_composite`,
`prime_decidable`, `proper_factor_lt`, and bounded/public prime-divisor
existence. All are independently reconstructed Peano certificates, not
translations of notebook code. Infinitude, sieve correctness, and executable
trial-division implementations remain future milestones.

### Prime factorization and arithmetic functions

The dictionary representation in Part 4 suggests a useful documentation API:
finite maps from primes to exponents. It is not a Peano term. Native PA now
instead checks sorted β-coded factorization existence and canonical
extensional uniqueness. Future interfaces should support:

- factor multiplicities and valuation laws;
- reconstruction of a number from its finite support;
- multiplicative functions determined on prime powers;
- divisor-count and divisor-sum formulas.

Keep these dictionary-like and arithmetic-function APIs planned rather than
encoding a Python dictionary into theorem statements. Their absence does not
block the checked relational β-coded FTA.

### Modular powers and primality tests

The formal dependency spine for Part 5 is:

1. balanced natural congruence and canonical residues;
2. congruence under addition and multiplication;
3. a generic power relation or checked power term;
4. repeated-squaring correctness;
5. Fermat's little theorem;
6. prime-field consequences used by probabilistic tests;
7. a precise Miller--Rabin specification separating sound rejection of a
   composite from probabilistic acceptance behavior.

Do not infer theorem correctness from successful notebook runs. Algorithm
implementations need their own independently written code and proof/test
artifacts.

### Totients and cryptographic examples

Euler's totient requires finite counting, and Euler's theorem requires
generic exponentiation plus a developed coprimality/congruence layer. RSA and
Diffie--Hellman additionally depend on modular inverses and group-like
reasoning. Recommended order:

1. coprimality and modular inverse existence;
2. finite reduced-residue systems;
3. totient of a prime and a prime power;
4. totient multiplicativity for coprime inputs;
5. Euler's theorem;
6. modular root/exponent inversion;
7. small, explicitly non-production cryptographic correctness examples.

Cryptographic material is pedagogical documentation, not security guidance
or production code.

## Current-language boundary

Peano Lab can presently state first-order facts about natural numbers using
`0`, successor, addition, multiplication, equality, additive-witness order,
connectives, quantifiers, and induction. It has no generic power, quotient,
remainder, gcd, factorial, prime-factor list, finite set, or counting term.

Therefore, quotient/remainder, relational gcd, balanced Bézout, constructive
primality and prime-divisor search, Euclid's lemma, greatest-prime-divisor
descent, finite β recoding, exact Product traces, canonical existence,
extensional uniqueness, and native FTA are checked at this integration
checkpoint. The endpoint metrics are:

| Endpoint | Nodes | Depth | Cuts |
|---|---:|---:|---:|
| factorization existence | 43,973 | 98 | 1,328 |
| factorization uniqueness | 29,789 | 82 | 854 |
| combined FTA | 73,767 | 99 | 2,184 |

The FTA certificate SHA-256 is
`fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
It passes the 500,000-occurrence/100,000-object/depth-256 live/use cap using
PA1–PA6 and induction
only, with no DNE. Runtime integration is complete.

No primitive dictionary, list, or multiset was added, and uniqueness never
identifies raw β codes. `prime_unbounded` is now checked constructively from
the bounded-common-multiple and prime-divisor APIs. Algorithms may be
specified relationally, but executable functions still require an explicit
architecture decision. Fermat, Euler, Miller--Rabin, primitive-root, and RSA
layers still require generic powers and additional finite algebra/counting
infrastructure.

## Artifact policy

For each notebook-inspired target, keep the following artifacts distinct:

- a source-register entry with the pinned upstream URL and GPL-3.0 boundary;
- an independently written mathematical specification;
- a dependency graph pointing only to checked Peano lemmas;
- a replayed, kernel-checked certificate when the target is formalized;
- independently generated tests or example data, labeled as tests rather
  than proofs;
- a Jupyter Book page that links to the external notebook without embedding
  GPL prose or code;
- an Obsidian concept note linked to the theorem and source records.
