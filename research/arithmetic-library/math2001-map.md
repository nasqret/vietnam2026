# The Mechanics of Proof source map

## Purpose and scope

This note maps the arithmetic material in Heather Macbeth's *The Mechanics of
Proof* to a Peano-native theorem library. It is a coverage and dependency map,
not a port of the Lean development. Every Peano statement must be normalized
to the project's first-order language, and every proof must be reconstructed
and accepted by Peano Lab's independent kernel.

The audit covers the public course site and its associated Lean repository at
the immutable revision
[`e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b`](https://github.com/hrmacbeth/math2001/tree/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b),
checked on 2026-07-28.

## Pinned provenance and reuse boundary

| Field | Value |
|---|---|
| Source IDs | `macbeth_mechanics_site`, `macbeth_math2001_repo` |
| Course site | [The Mechanics of Proof](https://hrmacbeth.github.io/math2001/) |
| Repository | [`hrmacbeth/math2001`](https://github.com/hrmacbeth/math2001) |
| Revision | `e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b` |
| Repository license | No `LICENSE` file; GitHub reports no detected repository license |
| File notices | The audited arithmetic Lean files state `All rights reserved` |
| Permitted project use | Bibliographic and topic reference; clean-room formalization only |

Public availability is not a reuse license. Do not copy or adapt Lean proof
scripts, course prose, generated RST/HTML, diagrams, or exercises into the MIT
Peano repository. Mathematical propositions may guide a coverage checklist,
but statements should be restated in Peano's canonical vocabulary and proofs
must be derived independently. No source file from this project is vendored.

The repository contains Lean sources and generated documentation sources, not
an explicitly licensed TeX corpus. The generated `_sources/*.rst.txt` files do
not change the licensing boundary and are not candidates for vendoring.

## Authoritative arithmetic sources

### Reusable theory layer

- [Division algorithm and non-divisibility criteria](https://github.com/hrmacbeth/math2001/blob/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b/Library/Theory/Division.lean)
- [Euclidean GCD and Bézout identity](https://github.com/hrmacbeth/math2001/blob/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b/Library/Theory/GCD.lean)
- [Prime definition and prime-factor existence](https://github.com/hrmacbeth/math2001/blob/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b/Library/Theory/Prime.lean)
- [Parity definitions and dichotomy](https://github.com/hrmacbeth/math2001/blob/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b/Library/Theory/Parity.lean)
- [Parity as congruence modulo two](https://github.com/hrmacbeth/math2001/blob/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b/Library/Theory/ParityModular.lean)
- [Integer modular-congruence definition](https://github.com/hrmacbeth/math2001/blob/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b/Library/Theory/ModEq/Defs.lean)
- [Modular-congruence algebra](https://github.com/hrmacbeth/math2001/blob/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b/Library/Theory/ModEq/Lemmas.lean)
- [Number-theory parity consequences](https://github.com/hrmacbeth/math2001/blob/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b/Library/Theory/NumberTheory.lean)

### Course developments and capstones

- [Parity and divisibility chapter](https://hrmacbeth.github.io/math2001/03_Parity_and_Divisibility.html)
- [Induction, division, and Euclidean algorithm chapter](https://hrmacbeth.github.io/math2001/06_Induction.html)
- [Number-theory chapter](https://hrmacbeth.github.io/math2001/07_Number_Theory.html)
- [Division-algorithm Lean chapter](https://github.com/hrmacbeth/math2001/blob/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b/Math2001/06_Induction/06_Division_Algorithm.lean)
- [Euclidean-algorithm Lean chapter](https://github.com/hrmacbeth/math2001/blob/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b/Math2001/06_Induction/07_Euclidean_Algorithm.lean)
- [Infinitely many primes](https://github.com/hrmacbeth/math2001/blob/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b/Math2001/07_Number_Theory/01_Infinitely_Many_Primes.lean)
- [Gauss's and Euclid's lemmas](https://github.com/hrmacbeth/math2001/blob/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b/Math2001/07_Number_Theory/02_Euclid_Lemma.lean)
- [Irrationality pattern for the square root of two](https://github.com/hrmacbeth/math2001/blob/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b/Math2001/07_Number_Theory/03_Sqrt_Two.lean)

## Topic-to-library map

The entries below describe mathematical targets only. They do not authorize
translation of the corresponding Lean proof.

### Parity

The source covers existential definitions of even and odd, even-or-odd,
mutual exclusion, complement equivalences, parity modulo two, odd powers, and
the implication from an even power to an even base.

Recommended Peano dependency order:

1. `even_def` and `odd_def` as documented formula abbreviations.
2. `even_or_odd` from division by two or direct induction.
3. `odd_not_even`, `even_not_odd`, and their converse directions.
4. Addition and multiplication parity tables.
5. Fixed-exponent square and fourth-power parity lemmas.
6. `even_square_implies_even` and its contradiction-based corollaries.

The first four groups are expressible in the current language by expanding
the existential definitions. Generic powers require a representation choice;
fixed powers can be written as repeated multiplication.

### Divisibility

Use the Peano-native expansion

\[
a \mid b \quad:\!\Longleftrightarrow\quad \exists k,\; b=a k.
\]

The source motivates closure under polynomial expressions, composition of
divisibility witnesses, divisor bounds for positive naturals, product-factor
projections, and a criterion showing that a number strictly between two
consecutive multiples is not divisible by the modulus.

Recommended reusable family:

- reflexivity, transitivity, `one_divides`, and `divides_zero`;
- multiplication on either side and addition of divisible terms;
- equality transport for dividends and divisors;
- powers and repeated products after power support exists;
- positive-divisor bounds and divisibility antisymmetry on naturals;
- consecutive-multiple exclusion and remainder-zero characterizations.

### Modular congruence and residues

Macbeth defines congruence over integers using divisibility of a difference.
Peano Lab currently has naturals but no subtraction. A symmetric natural
encoding avoids introducing integers:

\[
a \equiv b \pmod n
\quad:\!\Longleftrightarrow\quad
\exists u\,v,\; a+n u=b+n v.
\]

Build reflexivity, symmetry, transitivity, and compatibility with addition
and multiplication before fixed-modulus results. Keep the existing quotient
and residue form `a = n*q + r` as a separate relation, connected to balanced
congruence by bridge lemmas. The source's `add`, `sub`, `neg`, `mul`, `pow`,
factor-zero, multiple-insertion, and unique-representative results become a
coverage checklist. Subtraction and negation variants are deferred until an
integer representation exists.

### Division algorithm

The source proves existence and uniqueness of quotient and remainder for
naturals and integers, plus weak existence forms and non-divisibility gap
criteria. The Peano order is already additive-witness order, so the natural
target can be stated directly:

\[
m\ne0 \;\Longrightarrow\;
\exists q\,r,\; n=mq+r\;\land\; r<m.
\]

The current Peano snapshot checks natural existence and uniqueness, exact
divisibility/remainder-zero bridges, and the fixed modulus-five exhaustion.
Additional generated fixed-modulus clients remain broader library work. The
integer version is outside the present term language.

### GCD, coprimality, and Bézout

The source implements a recursive integer-valued `gcd`, proves nonnegativity
and divisibility of both inputs, constructs Bézout coefficients, and derives
Gauss's lemma. Peano currently has no user-defined function symbols, so the
first interface should be relational:

\[
\operatorname{IsGCD}(g,a,b) :\!\Longleftrightarrow
g\mid a\land g\mid b\land
\forall d,\;(d\mid a\land d\mid b)\to d\mid g.
\]

The current Peano snapshot checks existence, uniqueness, symmetry, zero/one
cases, and both directions of the Euclidean-step law around this relation. It
also checks four-natural balanced Bézout witnesses in the subtraction-free
form

\[
a x_+ + b y_+ = g + (a x_- + b y_-),
\]

then derives coprime Bézout and Gauss cancellation. This is a clean-room Peano
formulation, not a translation of the integer Lean implementation.

### Primes

The source's reusable spine is:

1. prime definition;
2. elementary prime tests and primality of two;
3. a proper factor for every non-prime `n >= 2`;
4. existence of a prime factor;
5. Gauss's lemma for coprime factors;
6. Euclid's lemma for a prime dividing a product;
7. the corresponding prime-divides-power result;
8. existence of a prime above every bound.

The current Peano snapshot independently checks the first concrete instance,
`prime_two`, through `two_large_factors_impossible`, the general
divisor-of-a-prime one-or-self API, Gauss cancellation, and Euclid's lemma. It
also checks constructive equality and divisibility decisions, bounded factor
search, a prime-or-nontrivial-factor-pair split, proper-factor descent, general
primality decidability, and bounded/unrestricted prime-divisor existence. In
runtime terms this is the linked spine from `eq_decidable` and
`multiple_decidable_nonzero` through `factor_search_up_to`,
`prime_or_composite`, `proper_factor_lt`, and `prime_divisor_exists`.
Primes above every bound and the greatest-prime-divisor descent needed by the
selected sorted factorization construction remain open. Macbeth remains a
reference-only statement and dependency source; no Lean proof or prose was
copied into the Peano certificate.

All except generic power notation can be expressed by inlining first-order
definitions. Infinitude need not wait for a factorial term: independently
prove that every finite initial interval has a common multiple `M`, take a
prime divisor of `M+1`, and show that it exceeds the bound.

### Factorization and irrationality

The square-root-of-two argument contributes parity, descent, and strong
induction patterns, but is not itself foundational for factorization. Prime
factorization existence uses strong induction and prime-factor existence;
uniqueness uses Euclid's lemma. A single natural-language statement of the
Fundamental Theorem of Arithmetic additionally needs a representation of an
arbitrary finite list or multiset of prime factors.

## Current-language boundary

Peano Lab formulas currently provide natural-number terms `0`, `S`, `+`, and
`*`; equality; `<=` as defined surface sugar; first-order connectives and
quantifiers; and induction. They do not provide:

- integers or subtraction;
- user-defined predicate or function symbols;
- generic exponentiation;
- quotient, remainder, gcd, or factorial terms;
- lists, multisets, finite maps, or quantification over functions.

Consequently:

- parity, divisibility, balanced natural congruence, the natural division
  algorithm, relational gcd, prime-factor existence, and Euclid's lemma are
  current-language targets already represented by checked native
  certificates; infinitude of primes and greatest-prime descent remain
  expressible next targets;
- integer modular arithmetic should remain a documented future layer;
- generic powers need a graph relation or a conservative term-language
  extension;
- the Fundamental Theorem of Arithmetic needs a checked finite-sequence or
  multiset representation before it can be stated naturally as one theorem.

Gödel coding of sequences is theoretically possible in first-order
arithmetic, but it is not an appropriate user-facing library interface.

## Clean-room acceptance rule

A Macbeth-inspired catalog entry is acceptable only when:

1. its source record contains an immutable URL and the `reference_only_clean_room`
   reuse mode;
2. its statement has been independently normalized to Peano syntax;
3. its dependency list refers only to earlier checked Peano results;
4. its tactic script was written without copying or translating the Lean
   proof;
5. replay retains dependency applications as self-contained
   `Cut(A,B,lemma,body)` nodes, and the independent kernel accepts the resulting
   closed certificate without theorem-name or hash authority;
6. certificate node and depth limits are recorded.
