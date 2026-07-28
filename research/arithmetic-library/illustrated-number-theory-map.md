# Illustrated Theory of Numbers companion-source map

## Purpose and scope

This note maps Martin H. Weissman's computational number-theory notebooks to
future Peano library layers and documentation artifacts. The notebooks are an
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
finite maps from primes to exponents. It is not currently a Peano term. A
future checked representation should support:

- existence and uniqueness of prime factorization;
- factor multiplicities and valuation laws;
- reconstruction of a number from its finite support;
- multiplicative functions determined on prime powers;
- divisor-count and divisor-sum formulas.

Until finite maps or multisets exist, keep these as planned interfaces rather
than encoding a Python dictionary into theorem statements.

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

Therefore:

- quotient/remainder existence, divisibility, relational gcd, constructive
  primality decision, prime-divisor existence, and Euclid's lemma are now
  checked native layers; balanced congruence is checked through transitivity
  and addition, and expanded Gödel-β values are total and functional;
- greatest-prime descent and infinitude of primes remain expressible without
  changing the object language;
- algorithms may be specified relationally, but executable functions require
  an explicit project architecture decision;
- prime-decomposition dictionaries require a finite-map or multiset layer;
- the selected β route still requires CRT, finite-prefix extension, and
  encoded prefix-product traces before it can replace that external data
  structure inside native PA;
- Fermat, Euler, Miller--Rabin, primitive-root, and RSA layers require generic
  powers and additional finite algebra/counting infrastructure.

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
