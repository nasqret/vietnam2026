---
title: "A Campaign for Formalized Elementary Number Theory in First-Order Heyting Arithmetic"
subtitle: "Research, proof-engineering, and publication blueprint for a public database of strict HA derivations"
date: "3 August 2026"
lang: en-US
---

# Executive summary

This document proposes a coordinated campaign to build a public database of machine-checked proofs in **first-order Heyting arithmetic** (HA), with elementary number theory as the organizing domain. The campaign is deliberately stricter than ordinary constructive formalization. A theorem counts as completed only when the final artifact is an object-level derivation

\[
\mathsf{HA}\vdash\varphi,
\]

or a certificate accepted by a checker whose only mathematical axioms and logical rules are those of HA. A theorem proved about a host system's native natural numbers in Rocq, Lean, Agda, Isabelle, Minlog, or another constructive environment is valuable prior art, but it is not by itself the target artifact.

The campaign has four mutually reinforcing goals:

1. **Mathematics:** produce a coherent elementary-number-theory library from Euclidean division through quadratic reciprocity, Diophantine classifications, Pell's equation, Bertrand's postulate, and the four-square theorem.
2. **Foundations:** make every use of intuitionistic logic, induction, bounded search, coding, and definitional extension explicit and auditable.
3. **Computation:** attach witness-producing algorithms, obstruction certificates, and executable specifications to constructive existence and decision theorems.
4. **Scholarship:** maintain a dated prior-art ledger and use disciplined language about novelty. The phrase "not formalized in HA" must always mean "no public strict object-level HA derivation was located under the documented search protocol," not an unqualified historical impossibility claim.

The recommended opening release is **Euclidean and Modular Arithmetic in HA**: division, extended Euclid, modular inverses, linear congruences, and binary/finite/generalized CRT. It is small enough to finish with a rigorous trust boundary, yet valuable enough to support almost every later package. The first flagship mathematical release should culminate in **quadratic reciprocity**. A second flagship line should culminate in the **sum-of-two-squares criterion** and **Pell's equation**.

> **Campaign commitment.** Convenience may live in the elaborator; trust must live in the exported HA certificate. Every theorem will ship with a canonical statement, expanded statement, dependency manifest, induction footprint, proof certificate, human proof note, and reproducible build.

# 1. Scope, terminology, and claim discipline

## 1.1 What counts as Heyting arithmetic

The base theory is first-order intuitionistic arithmetic in the language

\[
\mathcal L_{\mathrm{HA}}=\{0,S,+,\times,=\},
\]

with intuitionistic first-order logic, equality, the usual defining axioms for addition and multiplication, successor axioms, and the full induction scheme for every formula of the object language. It is acceptable to work in a conservative extension containing symbols for primitive-recursive functions, provided that every symbol has:

- defining equations or a graph formula;
- an HA proof of totality and functionality where appropriate;
- a mechanically checked elimination translation to the base language;
- an explicit record in the theorem manifest.

The campaign does **not** weaken induction unless a theorem is explicitly being calibrated over a fragment. Results about bounded arithmetic, intuitionistic PRA, or HA with restricted induction are separate research products.

## 1.2 Strict HA proof versus constructive host proof

The following judgments must be kept distinct:

```text
Host-level theorem:
    The proof assistant proves P n for its native natural numbers.

Object-level HA theorem:
    The proof assistant proves Derivable(HA, encode(P)).
```

Only the second judgment establishes the campaign's foundational claim. Existing constructive developments remain extremely useful as proof blueprints, algorithm sources, regression oracles, and candidates for translation.

## 1.3 The current evidence base

The public landscape located for this plan contains:

- explicit Coq encodings of HA syntax, axioms, semantics, soundness, and realizability infrastructure [R3, R4];
- a substantial constructive Minlog number-theory corpus covering Euclidean and extended gcd algorithms, Bezout, primes, infinitude of primes, prime factorization, FTA, and Fermat factorization, in the stronger finite-type setting TCF [R1, R2];
- constructive Rocq/Coq infrastructure for CRT, recursive-function coding, DPRM, and Hilbert's tenth problem [R5, R6];
- a mature metatheory of semi-classical arithmetic, conservation, realizability, and restricted excluded middle [R7-R10].

No broad public library was located in which the elementary-number-theory corpus is exported as strict first-order HA derivations. This is a **candidate gap**, not an absolute historical assertion. Each theorem must pass the audit protocol in Section 3 before a priority claim is published.

## 1.4 What the campaign will not claim

The campaign will not claim that:

- a theorem has never been formalized in any proof assistant;
- a native constructive proof automatically yields a strict HA proof;
- PA-to-HA conservation is itself the desired certificate;
- a classical prenex normalization preserves intuitionistic meaning;
- an extracted program is efficient merely because it exists;
- the absence of a search result proves absence of prior art.

# 2. Scientific rationale

## 2.1 Why elementary number theory is the right domain

Elementary number theory is unusually well matched to HA. Its objects are finite, its predicates are often decidable, and its existence theorems frequently specify computable witnesses. Division algorithms, gcds, modular inverses, prime factorizations, finite residue permutations, continued-fraction states, and Diophantine representations all admit direct coding by natural numbers.

The domain is also mathematically coherent. A small substrate supports a long sequence of recognizable theorems:

```text
order and bounded search
  -> division and gcd
  -> prime factorization and valuations
  -> congruences and CRT
  -> finite permutations and arithmetic functions
  -> finite fields and polynomial root bounds
  -> quadratic residues and reciprocity
  -> Diophantine classifications and continued fractions
```

This makes the corpus valuable both as mathematics and as a benchmark for proof engineering, program extraction, and theorem-prover automation.

## 2.2 Why PA-provability is useful but not sufficient

PA is \(\Pi^0_2\)-conservative over HA. Consequently, many computational statements of the form

\[
\forall x\,\exists y\,R(x,y),
\]

with bounded or decidable \(R\), are HA-provable whenever they are PA-provable [R7]. This gives strong planning confidence for witness theorems such as Pell's equation and four squares.

However, the conservation theorem does not replace a formalization. A campaign theorem must still exhibit its constructive mechanism, induction structure, definitions, and certificate. The conservation theorem is best used as a **feasibility filter**, not as the public proof artifact.

## 2.3 Constructive proof patterns the library should expose

The recurring legitimate patterns are:

- finite case distinction from decidability;
- bounded search and least witnesses inside an explicit bound;
- Euclidean descent with a natural-number measure;
- finite pigeonhole and permutation arguments;
- canonical normalization followed by literal uniqueness;
- proof by contradiction when the final proposition is decidable or negative;
- finite state repetition rather than appeal to infinitary compactness;
- algorithm-first existence proofs.

The recurring danger signs are unrestricted least-counterexample arguments, unbounded excluded middle, Markov's principle, quotient constructions with hidden choice, and classical rephrasing of disjunctions or existentials.

# 3. Prior-art audit protocol

Before any theorem is advertised as a first strict-HA formalization, complete the following audit.

1. **Freeze the exact statement.** Record the base-language formula and every convenient definitional extension.
2. **Search by theorem and synonyms.** Include English names, historical names, symbolic fragments, and algorithm names.
3. **Search by foundation.** Query "Heyting arithmetic," "intuitionistic arithmetic," "first-order arithmetic," "HA derivation," and "object theory" together with the theorem.
4. **Inspect likely repositories.** Search HA metatheory repositories, Minlog, Rocq/Coq arithmetic and undecidability libraries, Metamath intuitionistic developments, Mizar, Isabelle AFP, Lean Mathlib, Agda libraries, and thesis archives.
5. **Classify every hit.** Mark it as strict object-level HA, constructive host proof, classical host proof, metatheory only, statement only, or inaccessible/unverified.
6. **Contact maintainers when warranted.** For a plausible but ambiguous development, ask whether an HA certificate or translation exists.
7. **Archive the evidence.** Store query strings, dates, repository commits, file paths, and screenshots or metadata where licenses permit.
8. **Use cautious wording.** The default claim is "to the best of our knowledge, the first publicly available machine-checked object-level HA derivation."
9. **Invite correction.** Put a prior-art issue template in the repository and update claims promptly.

The audit result should be versioned separately from the proof. Novelty can change when prior work is discovered; mathematical correctness cannot.

# 4. Trust architecture

## 4.1 Recommended two-layer design

Use a comfortable host prover as an **elaborator**, but export to a small explicit HA calculus.

- **Elaboration layer:** notation, automation, reflection procedures, data structures, proof search, and human-facing lemmas.
- **Certificate layer:** first-order formulas, derivation rules, equality, induction instances, and conservative definitional-extension steps.
- **Independent replay layer:** a small standalone checker or second implementation that consumes the serialized certificate.

Rocq is a strong initial host candidate because relevant HA encodings, constructive arithmetic utilities, and DPRM infrastructure already exist [R3-R6]. The architecture should nevertheless keep the certificate format host-neutral.

## 4.2 Proof calculus recommendation

A focused intuitionistic sequent calculus is recommended for certificates:

- local checking rules are simple;
- assumptions and eigenvariable conditions are explicit;
- cuts can be retained for compactness;
- derived natural-deduction notation can elaborate into sequents;
- induction can appear as a tagged axiom-schema instance with its formula stored verbatim.

A Hilbert calculus would minimize the kernel but make authored proofs and diagnostics unnecessarily difficult. Native natural deduction is attractive for extraction, but a sequent certificate usually gives cleaner context management. The campaign can support both by compiling readable natural-deduction scripts into the sequent format.

## 4.3 Trusted base

The trusted mathematical base should contain only:

- parser and syntax well-formedness checks;
- capture-avoiding substitution and renaming;
- intuitionistic logical rules;
- equality rules;
- the fixed arithmetic axioms;
- verification that each induction node is a valid instance;
- verification of registered definitional-extension rules;
- certificate serialization and hashing.

Automation, decision procedures, normalizers, and extracted algorithms need not be trusted if they emit replayable certificates.

## 4.4 Formula and term representation

Use de Bruijn indices or a locally nameless representation in the kernel. Human scripts may use named binders, but the serialized form should have deterministic alpha-normalization. Every theorem package should include a pretty-printed named statement and a canonical machine encoding.

## 4.5 Definitional extensions

The campaign should support two proof products:

- **compact certificate:** may use registered primitive-recursive symbols and proven derived rules;
- **expanded certificate:** eliminates all extensions to the base language, or references separately checked elimination theorems with content-addressed hashes.

This avoids both extremes: unreadably enormous raw proofs and an opaque trusted arithmetic library.

# 5. Canonical representations

| Object | Canonical representation | Reason |
| --- | --- | --- |
| Natural numbers | Object-language numerals; host naturals only in the elaborator. | The foundational domain. |
| Signed integers | Canonical sign-magnitude or parity code with no negative zero. | Bezout coefficients and integer polynomials. |
| Pairs and lists | Primitive-recursive pairing, explicit length, nested canonical cells. | Must precede CRT to avoid circular beta coding. |
| Finite sets | Sorted duplicate-free lists with membership and cardinality theorems. | Makes uniqueness and counting literal. |
| Permutations | List of images plus bounded bijectivity certificate. | Euler, Wilson, Gauss, finite algebra. |
| Congruence | A first-order relation on naturals, preferably equality of canonical remainders after division is available. | Avoid quotient rings in the certificate. |
| Polynomials | Trimmed coefficient lists over coded integers; explicit zero polynomial. | Root bounds, Schur, Hensel, reciprocity support. |
| Finite fields | Canonical residues \(x<p\) with operations followed by remainder. | No quotient type required. |
| Rationals | Coprime numerator/positive denominator pair with canonical sign. | Continued fractions and Pell. |
| Finite functions | Graph-coded bounded tables with functionality proof. | Generic sums, permutations, and algorithms. |

A representation is accepted only after proving:

1. decoding is functional on valid codes;
2. canonical constructors produce valid codes;
3. equality of represented objects is decidable;
4. operations preserve validity and satisfy their specifications;
5. any host-level representation used during elaboration compiles to the object code.

# 6. Foundational packages

The following packages are prerequisites rather than headline novelty claims. Some have constructive formalizations in stronger systems, especially MinlogArith, but strict HA ports are indispensable.

## K0. Object language and proof calculus

**Deliverable.** First-order intuitionistic logic with equality over \(0,S,+,\times\), full induction for every object-language formula, and an explicitly checked derivation format.

**Why it matters.** This fixes the meaning of every later claim. The host prover may be strong, but the exported certificate must be replayable by the HA kernel.

## K1. Decidable bounded arithmetic

**Deliverable.** Decidability and reflection for equality, order, divisibility with bounded witnesses, primality, finite list membership, and general \(\Delta^0_0\) formulas.

**Why it matters.** This is the legitimate source of finite case splits, bounded minimization, and computation inside HA.

## K2. Primitive-recursive definitional extensions

**Deliverable.** Graph formulas and conservative symbols for exponentiation, factorial, quotient, remainder, coding, evaluation, and finite folds.

**Why it matters.** Every convenient symbol must have an elimination translation back to the base language.

## K3. Finite-data coding

**Deliverable.** Canonical codes for pairs, signed integers, lists, sorted sets, matrices, permutations, finite functions, and proof-relevant bijections.

**Why it matters.** The first list coding must not depend on CRT; CRT-based beta coding can be added later as a theorem.

## K4. Division and Euclidean algorithms

**Deliverable.** Canonical quotient and remainder, gcd, lcm, extended Euclid, Bezout coefficients, and their executable specifications.

**Why it matters.** This is the arithmetic engine for all modular and Diophantine work.

## K5. Prime factorization and valuations

**Deliverable.** Least prime divisor, Euclid\'s lemma, sorted prime-factor list, uniqueness, and \(p\)-adic valuation algebra.

**Why it matters.** A constructive Minlog development is an important source, but the campaign must port it to an object-level HA certificate.

## K6. Finite sums, products, and cardinality

**Deliverable.** Reindexing, partitioning, duplicate-free lists, permutations, pigeonhole, finite double counting, and product cancellation.

**Why it matters.** These lemmas prevent every major theorem from rebuilding a bespoke finite combinatorics layer.


# 7. Release architecture and dependency map

## 7.1 Proposed releases

- **R0 - Kernel and arithmetic substrate:** K0-K6.
- **R1 - Euclidean and modular arithmetic:** M1-M5.
- **R2 - Elementary multiplicative number theory:** E1-E7 and D1-D2.
- **R3 - Finite fields and quadratic reciprocity:** F1-F2 and Q1-Q3.
- **R4 - Digit arithmetic and prime powers:** E8-E9 and Q4-Q5.
- **R5 - Diophantine classifications:** D3-D4 and A1-A4.
- **R6 - Large elementary landmarks:** A5-A8.

## 7.2 High-level dependency map

```text
K0-K3  logic, coding, bounded reflection
   |
K4     division, gcd, Bezout
   |
K5-K6  factorization, valuations, finite combinatorics
   |
   +--> M1-M5  inverses, congruences, CRT
   |       |
   |       +--> E3-E6  Euler, phi, Mobius
   |       +--> D1     Frobenius
   |       +--> Q5     primitive-root classification
   |
   +--> E1-E2, E4, E7, D2
           |
           +--> F1 --> F2
           |      |      |
           |      +--> Q1-Q3
           |             |
           |             +--> A2-A4
           |
           +--> E8-E9
           +--> D3-D4
           +--> A5-A8
```

The machine-readable dependency graph is authoritative. The diagram is explanatory only.

# 8. Portfolio overview and prioritization

Scores are provisional and use a five-point scale. "Burden" is higher when harder. The heuristic priority score is \(2\cdot\text{value}+2\cdot\text{reuse}+\text{novelty confidence}-\text{burden}\). Novelty confidence concerns the strict object-level HA gap after a targeted search, not absence from all proof assistants.

| ID | Theorem | Release | Value | Reuse | Burden | Gap confidence | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1 | Modular inverse criterion | R1 | 5 | 5 | 1 | 4 | 23 |
| M3 | Binary Chinese remainder theorem | R1 | 5 | 5 | 2 | 4 | 22 |
| M4 | Finite Chinese remainder theorem | R1 | 5 | 5 | 3 | 4 | 21 |
| M2 | Classification of linear congruences | R1 | 4 | 5 | 2 | 4 | 20 |
| M5 | Generalized Chinese remainder theorem | R1 | 4 | 5 | 3 | 4 | 19 |
| E2 | Fermat's little theorem | R2 | 5 | 5 | 2 | 4 | 22 |
| E3 | Euler's theorem | R2 | 5 | 5 | 3 | 4 | 21 |
| E5 | Euler totient package | R2 | 5 | 5 | 3 | 4 | 21 |
| E7 | Legendre's formula for factorial valuations | R2 | 4 | 5 | 2 | 4 | 20 |
| E4 | Wilson's theorem in both directions | R2 | 5 | 4 | 3 | 4 | 19 |
| D2 | Classification of primitive Pythagorean triples | R2 | 5 | 3 | 3 | 4 | 17 |
| E1 | Infinitude of prime numbers | R2 | 5 | 3 | 2 | 3 | 17 |
| E6 | Mobius function and finite Mobius inversion | R2 | 4 | 4 | 3 | 4 | 17 |
| D1 | Two-variable Frobenius coin theorem | R2 | 4 | 3 | 3 | 4 | 15 |
| F1 | Polynomial root bound over a prime field | R3 | 5 | 5 | 3 | 4 | 21 |
| Q1 | Euler's criterion | R3 | 5 | 5 | 3 | 4 | 21 |
| F2 | Cyclicity of the multiplicative group of a prime field | R3 | 5 | 5 | 5 | 4 | 19 |
| Q3 | Quadratic reciprocity | R3 | 5 | 5 | 5 | 4 | 19 |
| Q2 | Gauss's lemma and the supplementary laws | R3 | 5 | 4 | 4 | 4 | 18 |
| Q5 | Classification of moduli admitting primitive roots | R4 | 5 | 5 | 5 | 4 | 19 |
| E9 | Kummer's theorem | R4 | 5 | 4 | 4 | 4 | 18 |
| Q4 | Finite Hensel lifting for simple roots | R4 | 4 | 5 | 4 | 4 | 18 |
| E8 | Lucas's theorem | R4 | 4 | 4 | 3 | 4 | 17 |
| A4 | Full sum-of-two-squares criterion | R5 | 5 | 5 | 5 | 4 | 19 |
| D4 | Euclid-Euler classification of even perfect numbers | R5 | 5 | 4 | 4 | 4 | 18 |
| A3 | Fermat's two-square theorem | R5 | 5 | 4 | 5 | 4 | 17 |
| A1 | Infinitely many primes congruent to 3 modulo 4 | R5 | 4 | 3 | 2 | 4 | 16 |
| A2 | Infinitely many primes congruent to 1 modulo 4 | R5 | 4 | 4 | 4 | 4 | 16 |
| D3 | Fermat's theorem for exponent four | R5 | 5 | 3 | 4 | 4 | 16 |
| A5 | Pell's equation | R6 | 5 | 4 | 5 | 4 | 17 |
| A6 | Bertrand's postulate | R6 | 5 | 4 | 5 | 4 | 17 |
| A7 | Lagrange's four-square theorem | R6 | 5 | 4 | 5 | 4 | 17 |
| A8 | Schur's theorem on prime divisors of polynomial values | R6 | 4 | 4 | 4 | 4 | 16 |

# 9. Detailed theorem dossiers

Each dossier states the intended theorem, a preferred constructive proof route, the expected computational artifact, and a release gate. The proof route may change after formal experimentation, but the canonical statement and acceptance conditions should change only through a reviewed specification update.

## M1. Modular inverse criterion

**Target statement.** For \(m>0\), \(\gcd(a,m)=1\) if and only if there exists a unique \(u<m\) with \(au\equiv 1\pmod m\).

**Mathematical value.** This is the smallest high-leverage theorem connecting Bezout arithmetic to modular arithmetic. It supplies the computational inverse operation used by CRT, linear congruences, finite fields, and later algorithms.

**Dependencies.** Euclidean division, gcd, extended Euclid, integer coding, congruence, canonical remainder.

**Preferred constructive route.** Run extended Euclid to obtain signed coefficients, reduce the coefficient of \(a\) modulo \(m\), and prove uniqueness by modular cancellation. Prove the converse by showing any inverse forces every common divisor of \(a\) and \(m\) to divide \(1\).

**Computational or database artifact.** A primitive-recursive function \(\operatorname{invmod}(a,m)\) with a graph formula, a correctness theorem, and the existential criterion as a corollary.

**Primary formalization risk.** The main issue is clean handling of signed Bezout coefficients without importing a host integer theory into the trusted statement.

**Acceptance gate.** The expanded theorem uses only \(0,S,+,\times,=\); the witness computes correctly on a regression suite; no classical axiom appears in the manifest.

## M2. Classification of linear congruences

**Target statement.** For \(m>0\) and \(d=\gcd(a,m)\), the congruence \(ax\equiv b\pmod m\) is solvable exactly when \(d\mid b\); when solvable it has exactly \(d\) residue classes modulo \(m\).

**Mathematical value.** It turns modular inverse into a complete solver for one-variable linear congruences and establishes the first nontrivial counting theorem in the modular layer.

**Dependencies.** M1, gcd identities, divisibility cancellation, quotient and remainder, finite list cardinality.

**Preferred constructive route.** Divide \(a,b,m\) by \(d\), invert \(a/d\) modulo \(m/d\), construct one solution, then enumerate the \(d\) lifts separated by \(m/d\). Prove exhaustiveness and distinctness by canonical remainder arguments.

**Computational or database artifact.** A certified solver returning either a divisibility obstruction or the sorted list of all canonical solutions.

**Primary formalization risk.** The phrase "exactly \(d\) solutions" requires an explicit finite-set representation and a bijection, not informal residue-class language.

**Acceptance gate.** The solver output is proved sound, complete, duplicate-free, and of length \(d\).

## M3. Binary Chinese remainder theorem

**Target statement.** For coprime \(m,n>0\) and arbitrary residues \(a,b\), there is a unique \(x<mn\) with \(x\equiv a\pmod m\) and \(x\equiv b\pmod n\).

**Mathematical value.** This is the recommended inaugural named theorem: familiar, constructive, computational, and foundational for simultaneous congruences and sequence coding.

**Dependencies.** M1, remainder arithmetic, coprime product lemmas, canonical representatives.

**Preferred constructive route.** Construct inverses \(u\) and \(v\), set \(z=anu+bmv\), and return \(z\bmod mn\). Prove uniqueness by showing simultaneous divisibility by coprime \(m,n\) implies divisibility by \(mn\).

**Computational or database artifact.** A binary CRT constructor with a direct correctness theorem, uniqueness theorem, and normalized output bound.

**Primary formalization risk.** Avoid quotient rings in the trusted layer; congruence should be a first-order relation on natural numbers.

**Acceptance gate.** Existence and uniqueness are checked after full definitional expansion, and sample computations agree with an independent executable reference.

## M4. Finite Chinese remainder theorem

**Target statement.** Every finite family of residues modulo pairwise coprime positive moduli has a unique simultaneous representative below the product of the moduli.

**Mathematical value.** This theorem creates the finite-sequence and product infrastructure needed by coding arguments, multiplicative functions, and finite algebra.

**Dependencies.** M3, coded lists, finite products, pairwise coprimality, induction over list codes.

**Preferred constructive route.** Fold the binary CRT over a canonical list, maintaining the invariant that the accumulated modulus is the product of the processed moduli and remains coprime to the next modulus.

**Computational or database artifact.** A list-based CRT program plus a theorem that its output is canonical and independent of the fold proof presentation.

**Primary formalization risk.** Pairwise-coprime bookkeeping and list invariants can dominate the proof unless the finite-data API is designed first.

**Acceptance gate.** The proof handles the empty and singleton families, repeated-modulus rejection, and permutation invariance of the specification.

## M5. Generalized Chinese remainder theorem

**Target statement.** A finite system \(x\equiv a_i\pmod{m_i}\) is solvable exactly when \(a_i\equiv a_j\pmod{\gcd(m_i,m_j)}\) for every pair \(i,j\); solutions are unique modulo the least common multiple.

**Mathematical value.** This is the mathematically complete CRT and an important stress test for compatibility conditions, lcm, and canonical solution sets.

**Dependencies.** M2-M4, lcm identities, pairwise compatibility over coded lists.

**Preferred constructive route.** First prove the binary noncoprime theorem using a reduced linear congruence; then fold it while maintaining the accumulated lcm and all compatibility obligations.

**Computational or database artifact.** A decision procedure returning either a canonical solution modulo the lcm or an explicit incompatible pair.

**Primary formalization risk.** The constructive statement should return a concrete obstruction, not merely the negation of solvability.

**Acceptance gate.** Soundness, completeness, obstruction correctness, and uniqueness modulo lcm are all separate checked theorems.

## E1. Infinitude of prime numbers

**Target statement.** For every \(N\), there exists a prime \(p>N\).

**Mathematical value.** It is a universally recognizable landmark and a compact showcase of constructive factor search. A constructive formalization exists in Minlog, so the novelty here is the strict object-level HA certificate.

**Dependencies.** Factorial or finite products, least prime divisor, Euclid lemma, order.

**Preferred constructive route.** Take a prime divisor of \(N!+1\) and show it cannot be at most \(N\). Alternatively use the product of the finite list of primes below \(N\) plus one.

**Computational or database artifact.** A witness-producing search procedure for a prime exceeding the input, together with a proof of termination and correctness.

**Primary formalization risk.** The direct extracted algorithm may be intentionally inefficient; distinguish proof-theoretic extraction from practical prime generation.

**Acceptance gate.** The theorem is stated uniformly, not as a schema of numeral instances, and the output is verified prime and greater than the input.

## E2. Fermat's little theorem

**Target statement.** If \(p\) is prime, then \(a^p\equiv a\pmod p\); equivalently, if \(p\nmid a\), then \(a^{p-1}\equiv1\pmod p\).

**Mathematical value.** This is the first major theorem of modular exponentiation and a gateway to primality tests, Euler criterion, and finite fields.

**Dependencies.** Exponentiation, prime cancellation, finite permutations or binomial coefficients.

**Preferred constructive route.** Prefer the permutation proof: multiplication by a nonzero residue permutes \(1,\ldots,p-1\); compare products and cancel \((p-1)!\). Keep the binomial proof as an independent validation route.

**Computational or database artifact.** A theorem in both coprime and unrestricted forms, plus a reusable permutation-of-residues lemma.

**Primary formalization risk.** Cancellation of the factorial modulo \(p\) must be justified without assuming Wilson's theorem.

**Acceptance gate.** Both formulations are derived, and the proof dependency graph contains no cycle through Wilson or Euler criterion.

## E3. Euler's theorem

**Target statement.** If \(\gcd(a,n)=1\), then \(a^{\varphi(n)}\equiv1\pmod n\).

**Mathematical value.** It generalizes Fermat's theorem and forces a clean treatment of reduced residue systems and finite permutation arguments.

**Dependencies.** M1-M4, totient definition, coded finite sets, product congruences.

**Preferred constructive route.** Show that multiplication by \(a\) permutes the reduced residues modulo \(n\), compare the products, and cancel the product because every factor is a unit.

**Computational or database artifact.** A certified reduced-residue enumeration and permutation witness, not merely a cardinality argument.

**Primary formalization risk.** Proving that the product of all reduced residues is itself a unit requires a finite coprimality lemma.

**Acceptance gate.** The proof exports the actual permutation and validates Euler's theorem on all small moduli by reflection tests.

## E4. Wilson's theorem in both directions

**Target statement.** For \(n>1\), \(n\) is prime if and only if \((n-1)!\equiv-1\pmod n\).

**Mathematical value.** Wilson is an exact primality characterization with a short, elegant proof and strong pedagogical value.

**Dependencies.** Modular inverses, finite pairing/permutation, factorial, divisor bounds.

**Preferred constructive route.** For the forward direction pair every nonzero residue with its inverse, leaving only \(1\) and \(-1\). For the converse, if \(n=ab\) with \(1<a,b<n\), show \((n-1)!\equiv0\pmod n\), with a separate square-factor edge case.

**Computational or database artifact.** A prime-to-factorial equivalence and an explicit involution on the reduced residue list.

**Primary formalization risk.** The composite converse has small exceptional cases that should be isolated and tested.

**Acceptance gate.** Both directions are present under the same exact hypotheses, including \(n=2\), with no informal use of residue classes.

## E5. Euler totient package

**Target statement.** Prove \(\varphi(p^k)=p^k-p^{k-1}\), coprime multiplicativity, and \(\sum_{d\mid n}\varphi(d)=n\).

**Mathematical value.** These identities form the arithmetic-function backbone of elementary multiplicative number theory and support Euler, primitive-root, and counting results.

**Dependencies.** M4, prime factorization, finite divisor enumeration, finite cardinality.

**Preferred constructive route.** Use CRT for multiplicativity, count nonmultiples of \(p\) for prime powers, and partition \(1,\ldots,n\) by \(\gcd(k,n)\) for the divisor-sum identity.

**Computational or database artifact.** A computable \(\varphi\), certified divisor list, and cardinality-preserving bijections for each formula.

**Primary formalization risk.** The proofs should separate list cardinality from extensional finite-set equality to avoid duplicated combinatorial infrastructure.

**Acceptance gate.** All formulas are proved from one canonical definition of \(\varphi\), and the implementation agrees with factorization-based computation.

## E6. Mobius function and finite Mobius inversion

**Target statement.** Define \(\mu\), prove \(\sum_{d\mid n}\mu(d)=1\) for \(n=1\) and \(0\) otherwise, and prove finite divisor-lattice inversion.

**Mathematical value.** Mobius inversion is a compact but powerful abstraction that unlocks multiplicative-function manipulations and counting formulas.

**Dependencies.** Canonical prime factorization, divisor lists, finite sums, squarefreeness.

**Preferred constructive route.** Define \(\mu\) from the canonical prime factorization; prove the basic divisor sum via subsets of distinct prime factors; derive inversion by reindexing finite double sums.

**Computational or database artifact.** A factorization-based Mobius algorithm and a generic inversion theorem for coded arithmetic functions over bounded domains.

**Primary formalization risk.** Generic function coding can become heavier than the number theory. A first release may state inversion for graph-coded functions with explicit bounds.

**Acceptance gate.** The theorem includes both directions of inversion and a worked corollary such as recovering \(\varphi\) from the identity function.

## E7. Legendre's formula for factorial valuations

**Target statement.** For prime \(p\), \(v_p(n!)=\sum_{j\ge1}\lfloor n/p^j\rfloor\), with the sum truncated once \(p^j>n\).

**Mathematical value.** This is a highly reusable bridge between valuations, factorials, binomial coefficients, and base expansions.

**Dependencies.** Prime valuations, factorial, bounded finite sums, powers and division.

**Preferred constructive route.** Count the contribution of each multiple of \(p\), then each additional contribution from multiples of \(p^2\), and so on. Formalize the finite double-counting bijection.

**Computational or database artifact.** A terminating valuation algorithm and the floor-sum specification.

**Primary formalization risk.** The index bound for the finite sum should be explicit and primitive recursive, rather than expressed as an informal infinite sum.

**Acceptance gate.** The theorem is proved with two equivalent finite bounds and tested against direct factorization for a substantial finite range.

## E8. Lucas's theorem

**Target statement.** If \(n=\sum n_ip^i\) and \(k=\sum k_ip^i\), then \(\binom nk\equiv\prod_i\binom{n_i}{k_i}\pmod p\).

**Mathematical value.** Lucas connects base-\(p\) digits, polynomial congruences, and binomial coefficients in an explicitly computable theorem.

**Dependencies.** E2, binomial theorem, base expansion, polynomial coefficient comparison modulo \(p\).

**Preferred constructive route.** Use \((1+X)^p\equiv1+X^p\pmod p\), expand according to the base-\(p\) digits of \(n\), and compare the coefficient of \(X^k\).

**Computational or database artifact.** Certified digit expansion and a digitwise binomial-modulo algorithm.

**Primary formalization risk.** Coefficient extraction and finite polynomial multiplication require a well-designed polynomial library.

**Acceptance gate.** The proof includes the zero convention when some \(k_i>n_i\) and a corollary characterizing nonzero binomial coefficients modulo \(p\).

## E9. Kummer's theorem

**Target statement.** The valuation \(v_p\!\binom nk\) equals the number of carries when adding \(k\) and \(n-k\) in base \(p\).

**Mathematical value.** It is one of the most striking exact correspondences between arithmetic valuation and a digit algorithm.

**Dependencies.** E7, base-\(p\) digit sums, carry recursion, binomial valuations.

**Preferred constructive route.** Derive the digit-sum form of Legendre's formula and prove that the loss of digit sum under addition is exactly \((p-1)\) times the number of carries.

**Computational or database artifact.** A carry-counting program whose equality with the valuation is machine checked.

**Primary formalization risk.** Carry sequences need canonical coding and careful endpoint conventions.

**Acceptance gate.** The theorem is proved for all \(0\le k\le n\), and its zero-carry corollary is cross-checked against Lucas's theorem.

## D1. Two-variable Frobenius coin theorem

**Target statement.** For coprime \(a,b>1\), the largest natural number not representable as \(ax+by\) with \(x,y\ge0\) is \(ab-a-b\).

**Mathematical value.** This is a concrete optimization and representation theorem that uses modular inverses without requiring advanced algebra.

**Dependencies.** M1, order, bounded search, divisibility, finite residue systems.

**Preferred constructive route.** Use the distinct residues of \(0,a,\ldots,(b-1)a\) modulo \(b\) to represent every integer above \((a-1)(b-1)\); prove nonrepresentation of \(ab-a-b\) by a modular and inequality argument.

**Computational or database artifact.** A representation algorithm for every \(n>ab-a-b\), plus the maximality certificate.

**Primary formalization risk.** The exact strict inequalities and boundary conversion between \((a-1)(b-1)\) and \(ab-a-b\) are common sources of off-by-one errors.

**Acceptance gate.** The formal statement includes both universal representability above the bound and explicit nonrepresentability at the bound.

## D2. Classification of primitive Pythagorean triples

**Target statement.** Every primitive solution \(x^2+y^2=z^2\) is, after swapping the legs, \(x=m^2-n^2\), \(y=2mn\), \(z=m^2+n^2\) for coprime \(m>n\) of opposite parity.

**Mathematical value.** This is a classical Diophantine classification with elementary proof ingredients and a meaningful canonical parametrization.

**Dependencies.** gcd, parity, square-factor lemmas from prime factorization, inequalities.

**Preferred constructive route.** Show exactly one leg is even; factor \((z-x)(z+x)=y^2\); divide by \(2\), prove the factors are coprime squares, and reconstruct \(m,n\).

**Computational or database artifact.** A normalization function from a primitive triple to canonical parameters and a constructor in the reverse direction.

**Primary formalization risk.** The square-product lemma for coprime factors should be proved once from valuations and reused.

**Acceptance gate.** Both classification directions, uniqueness of normalized parameters, and all parity/coprimality side conditions are formalized.

## D3. Fermat's theorem for exponent four

**Target statement.** There are no positive natural numbers satisfying \(x^4+y^4=z^2\); hence no positive solution of \(x^4+y^4=z^4\).

**Mathematical value.** This is the canonical elementary example of infinite descent and a major test of constructive negative reasoning.

**Dependencies.** D2, well-founded descent on naturals, gcd and parity, square-factor lemmas.

**Preferred constructive route.** Assume a solution with minimal hypotenuse, reduce to a primitive Pythagorean triple, derive a strictly smaller solution, and contradict minimality. Package descent as an explicit map and decrease proof.

**Computational or database artifact.** A reusable descent combinator for decidable counterexample predicates, plus the number-theoretic specialization.

**Primary formalization risk.** Textbook proofs vary in normalization and may hide a classical least-counterexample step. Use bounded minimization from an assumed witness or direct well-founded recursion.

**Acceptance gate.** Every normalization preserves positivity, the descent measure strictly decreases, and the theorem is proved without unrestricted excluded middle.

## D4. Euclid-Euler classification of even perfect numbers

**Target statement.** An even number is perfect exactly when it has the form \(2^{p-1}(2^p-1)\) with \(2^p-1\) prime.

**Mathematical value.** This elegant classification combines multiplicative functions, prime factorization, geometric sums, and Mersenne primes.

**Dependencies.** E5, divisor-sum multiplicativity, prime factorization, geometric-series identities.

**Preferred constructive route.** Prove the forward construction using the divisor-sum formula. For the converse, split an even perfect number as \(2^{p-1}m\) with \(m\) odd, use the perfection equation and coprimality to force \(m=2^p-1\) prime.

**Computational or database artifact.** A decision theorem for even perfect numbers and certified conversion between a perfect-number witness and a Mersenne-prime witness.

**Primary formalization risk.** The converse requires careful divisibility inequalities rather than field-style cancellation.

**Acceptance gate.** The definition of perfect uses an explicit finite divisor sum; both directions are checked with all positivity hypotheses.

## F1. Polynomial root bound over a prime field

**Target statement.** A nonzero polynomial modulo a prime \(p\), of degree at most \(d\), has at most \(d\) distinct canonical roots below \(p\).

**Mathematical value.** This is the central finite-field lemma behind cyclicity, residue counting, and many existence proofs.

**Dependencies.** Polynomial coding, modular arithmetic, coefficient normalization, factor theorem, finite cardinality.

**Preferred constructive route.** Prove polynomial division by \(X-a\) when \(a\) is a root, then induct on the degree while deleting one root from the finite list.

**Computational or database artifact.** Certified polynomial evaluation, division-by-linear-factor function, and root-list bound.

**Primary formalization risk.** Degree conventions for the zero polynomial and leading-zero coefficient lists must be canonical.

**Acceptance gate.** The root bound is stated for duplicate-free lists and includes an explicit theorem that a degree-zero nonzero polynomial has no root.

## F2. Cyclicity of the multiplicative group of a prime field

**Target statement.** For every prime \(p\), there exists \(g<p\) whose powers enumerate every nonzero residue modulo \(p\).

**Mathematical value.** Primitive roots modulo primes are a flagship finite-algebra theorem and unlock a streamlined theory of residues and orders.

**Dependencies.** F1, E2, factorization of \(p-1\), element order, lcm, finite group lemmas.

**Preferred constructive route.** For each prime power dividing \(p-1\), use the root bound to find an element whose order contains that prime power; combine commuting elements of coprime orders to obtain order \(p-1\).

**Computational or database artifact.** A bounded-search primitive-root constructor with a proof that the returned element has exact order \(p-1\).

**Primary formalization risk.** A generic finite-group library can become overabstract. Start with residues modulo a prime and generalize only lemmas that demonstrably reduce duplication.

**Acceptance gate.** The proof produces a concrete generator and a duplicate-free enumeration of all nonzero residues by its powers.

## Q1. Euler's criterion

**Target statement.** For an odd prime \(p\) and \(p\nmid a\), \(a^{(p-1)/2}\equiv 1\pmod p\) exactly for quadratic residues, and is congruent to \(-1\) otherwise.

**Mathematical value.** Euler's criterion connects exponentiation with quadratic residuosity and gives a computable Legendre symbol.

**Dependencies.** E2, F1, decidability of quadratic residuosity, counting nonzero squares.

**Preferred constructive route.** Show the half-power is a root of \(X^2-1\), hence \(\pm1\). Every nonzero square gives \(+1\); use the root bound and the two-to-one squaring map to show no other elements do.

**Computational or database artifact.** A Legendre-symbol evaluator and equivalence between the search definition and the exponentiation criterion.

**Primary formalization risk.** Counting nonzero squares requires a precise quotient-free two-to-one argument.

**Acceptance gate.** The zero case is handled separately, and multiplicativity of the resulting symbol is proved.

## Q2. Gauss's lemma and the supplementary laws

**Target statement.** Formalize Gauss\'s sign-count lemma and derive \(\left(\frac{-1}{p}\right)=(-1)^{(p-1)/2}\) and \(\left(\frac{2}{p}\right)=(-1)^{(p^2-1)/8}\).

**Mathematical value.** This package is finite, combinatorial, and the natural immediate precursor to quadratic reciprocity.

**Dependencies.** Q1, canonical least residues, finite products, sign parity, floor sums.

**Preferred constructive route.** Pair the least residues of \(a,2a,\ldots,((p-1)/2)a\) with their absolute representatives, compare products, and count the representatives exceeding \(p/2\). Specialize the count to \(-1\) and \(2\).

**Computational or database artifact.** A certified sign-count function and executable supplementary-law evaluator.

**Primary formalization risk.** The proof is sensitive to residue conventions; define least positive, least nonnegative, and signed representatives once and prove conversion lemmas.

**Acceptance gate.** Gauss's lemma is proved independently of reciprocity, and both supplementary laws are derived as named corollaries.

## Q3. Quadratic reciprocity

**Target statement.** For distinct odd primes \(p,q\), \(\left(\frac pq\right)\left(\frac qp\right)=(-1)^{(p-1)(q-1)/4}\).

**Mathematical value.** This is the flagship theorem for the modular and quadratic-residue campaign.

**Dependencies.** Q2, finite lattice-point or floor-sum counting, parity arithmetic.

**Preferred constructive route.** Use Gauss's lemma to convert both symbols into parity counts and prove the standard rectangle decomposition identity. Keep an Eisenstein floor-sum proof as the primary route and a Zolotarev permutation proof as a later independent verification.

**Computational or database artifact.** A complete Legendre/Jacobi symbol package and a computational reciprocity reduction algorithm.

**Primary formalization risk.** The informal proof often suppresses boundary exclusions in the lattice rectangle. Formalize the no-lattice-point-on-the-diagonal lemma early.

**Acceptance gate.** Reciprocity, both supplementary laws, multiplicativity, and Jacobi-symbol computation appear in one dependency-acyclic release.

## Q4. Finite Hensel lifting for simple roots

**Target statement.** If \(f(a)\equiv0\pmod{p^k}\) and \(f^{\prime}(a)\not\equiv0\pmod p\), then there is a unique \(t<p\) such that \(a+t p^k\) is a root modulo \(p^{k+1}\).

**Mathematical value.** This is a purely finite lifting theorem with direct algorithmic value for modular roots and prime-power arithmetic.

**Dependencies.** M1, polynomial evaluation and formal derivative, binomial expansion with remainder divisibility, prime powers.

**Preferred constructive route.** Expand \(f(a+t p^k)\) modulo \(p^{k+1}\), reduce the correction condition to a linear congruence modulo \(p\), and solve it using the derivative inverse.

**Computational or database artifact.** A one-step lift function and an iterated simple-root lifting procedure.

**Primary formalization risk.** The Taylor-style congruence must be proved algebraically for coefficient lists; avoid importing formal power series.

**Acceptance gate.** Existence, uniqueness, preservation of simplicity, and iteration to arbitrary larger exponents are checked.

## Q5. Classification of moduli admitting primitive roots

**Target statement.** The unit group modulo \(n\) is cyclic exactly for \(n=1,2,4,p^k,2p^k\), where \(p\) is an odd prime.

**Mathematical value.** This is a major capstone joining CRT, prime powers, valuations, element orders, and lifting generators.

**Dependencies.** F2, Q4 or a dedicated primitive-root lifting lemma, M4, totient formulas, finite group order.

**Preferred constructive route.** Construct generators for odd prime powers and twice odd prime powers; prove noncyclicity for the excluded forms using CRT decompositions and multiple involutions or exponent bounds.

**Computational or database artifact.** A decision-and-construction algorithm for primitive-root existence modulo an arbitrary positive modulus.

**Primary formalization risk.** The exact low-modulus exceptions and the lift from \(p\) to \(p^k\) require careful case separation.

**Acceptance gate.** The theorem returns either a generator with proof of exact order or a structural certificate showing why no generator can exist.

## A1. Infinitely many primes congruent to 3 modulo 4

**Target statement.** For every \(N\), there exists a prime \(p>N\) with \(p\equiv3\pmod4\).

**Mathematical value.** This is the simplest nontrivial infinitude theorem in an arithmetic progression and a good bridge from Euclid's proof to residue arguments.

**Dependencies.** Prime factor existence, products, congruence multiplication.

**Preferred constructive route.** Take a prime divisor of \(4M-1\), where \(M\) is a product containing all relevant smaller primes; prove at least one prime factor is \(3\bmod4\) and is new.

**Computational or database artifact.** A witness-producing construction parameterized by the lower bound.

**Primary formalization risk.** If the proof starts from a list of primes rather than a bound, a separate completeness lemma for the list is needed.

**Acceptance gate.** The theorem is uniform in \(N\) and does not merely state that no finite complete list exists.

## A2. Infinitely many primes congruent to 1 modulo 4

**Target statement.** For every \(N\), there exists a prime \(p>N\) with \(p\equiv1\pmod4\).

**Mathematical value.** It is a deeper elementary progression theorem and a direct application of order modulo a prime.

**Dependencies.** Prime divisors, modular order or Q1, finite products.

**Preferred constructive route.** Construct a number of the form \((2M)^2+1\). Any odd prime divisor not dividing \(M\) has an element of order \(4\), forcing \(4\mid p-1\).

**Computational or database artifact.** A certified constructor for a new \(1\bmod4\) prime above a bound.

**Primary formalization risk.** Prove explicitly that the chosen prime divisor is odd, new, and has exact order four rather than merely order dividing four.

**Acceptance gate.** All order arguments are carried out in the previously certified finite-residue layer.

## A3. Fermat's two-square theorem

**Target statement.** Every prime \(p\equiv1\pmod4\) is representable as \(p=x^2+y^2\).

**Mathematical value.** This is one of the most celebrated constructive existence theorems in elementary number theory.

**Dependencies.** Q1 or A2 order lemmas, Euclidean algorithm, descent or Cornacchia-style reduction, square roots of \(-1\) modulo \(p\).

**Preferred constructive route.** Construct a square root of \(-1\) modulo \(p\), then use a certified Euclidean/Cornacchia descent to obtain a short relation whose norm is \(p\). An alternative proof through Gaussian-integer norms can be added only after a first-order coding of pairs.

**Computational or database artifact.** A witness-producing algorithm returning \((x,y)\) and a proof that \(x^2+y^2=p\).

**Primary formalization risk.** Geometry-of-numbers proofs obscure constructivity. Prefer an explicit terminating descent with a natural-number measure.

**Acceptance gate.** The extracted constructor is total under the prime and congruence hypotheses and is validated on a broad prime test set.

## A4. Full sum-of-two-squares criterion

**Target statement.** A positive integer is a sum of two squares exactly when every prime congruent to \(3\pmod4\) occurs with even exponent in its prime factorization.

**Mathematical value.** This is the complete multiplicative classification and a natural culmination of factorization, valuations, and the two-square identity.

**Dependencies.** A3, canonical prime factorization, valuations, Brahmagupta-Fibonacci identity.

**Preferred constructive route.** For necessity, show a \(3\bmod4\) prime dividing a sum of two squares divides both summands and descend on the valuation. For sufficiency, represent each prime-power factor and combine representations multiplicatively.

**Computational or database artifact.** A decision-and-construction procedure that either returns a two-square representation or a bad prime with odd valuation.

**Primary formalization risk.** The necessity proof needs a clean lemma that \(-1\) is not a square modulo a \(3\bmod4\) prime.

**Acceptance gate.** The positive and negative branches both return explicit certificates, and zero/one conventions are documented.

## A5. Pell's equation

**Target statement.** For every nonsquare \(D>1\), there exist positive \(x,y\) with \(x^2-Dy^2=1\).

**Mathematical value.** Pell is a major algorithmic existence theorem and an ideal stress test for finite continued fractions inside first-order arithmetic.

**Dependencies.** Integer and rational coding, finite sequences, division, square-root bounds, continued-fraction recurrences, pigeonhole.

**Preferred constructive route.** Encode the continued-fraction state of \(\sqrt D\) by integer triples, prove the state space is bounded, obtain repetition, and derive a convergent with norm \(\pm1\); square if necessary to get norm \(+1\).

**Computational or database artifact.** A terminating continued-fraction solver with a certified Pell solution.

**Primary formalization risk.** Avoid real-number completeness. Every comparison with \(\sqrt D\) should be replaced by integer inequalities after squaring with sign conditions.

**Acceptance gate.** All states and convergents are natural-number codes, the period argument is finite, and positivity of the returned solution is explicit.

## A6. Bertrand's postulate

**Target statement.** For every \(n>1\), there exists a prime \(p\) with \(n<p<2n\).

**Mathematical value.** This is a strong quantitative theorem about primes with a remarkably simple final statement.

**Dependencies.** Binomial coefficients, factorial valuations, explicit inequalities, prime-product bounds.

**Preferred constructive route.** Formalize an elementary Erdos-style proof using the central binomial coefficient, explicit upper and lower bounds, and control of prime factors in specified intervals.

**Computational or database artifact.** A bounded prime-search theorem whose existence proof is certified by quantitative inequalities.

**Primary formalization risk.** Inequality engineering, not logic, is the main burden. All constants and small base cases must be explicit.

**Acceptance gate.** The theorem has exact strict bounds, finite base cases are discharged by reflection, and every analytic-looking inequality is reduced to integer arithmetic.

## A7. Lagrange's four-square theorem

**Target statement.** Every natural number is a sum of four squares.

**Mathematical value.** This is a landmark universal representation theorem with clear witness content.

**Dependencies.** Quaternion/four-square identity or explicit coordinate identity, modular square arguments, finite descent, prime factorization.

**Preferred constructive route.** Choose a constructive elementary proof: first represent each prime by four squares using a bounded pigeonhole argument and descent, then combine representations with Euler's four-square identity.

**Computational or database artifact.** A certified four-square constructor for arbitrary \(n\).

**Primary formalization risk.** Several textbook proofs use a minimal positive multiple and implicit classical minimization. Replace it by bounded search below a known represented multiple.

**Acceptance gate.** The output quadruple is bounded by an explicit function of \(n\), and the constructor is total and executable.

## A8. Schur's theorem on prime divisors of polynomial values

**Target statement.** For every nonconstant integer polynomial \(P\), infinitely many distinct primes divide nonzero values \(P(n)\).

**Mathematical value.** Schur's theorem is strikingly strong for an elementary argument and introduces uniform polynomial coding beyond finite fields.

**Dependencies.** Integer polynomial evaluation, prime divisors, congruence substitution, finite products.

**Preferred constructive route.** Assume a finite list of prime divisors, construct a suitable input congruent to a base point modulo their product, and force a new prime divisor using the nonconstant growth/difference identity.

**Computational or database artifact.** A constructor taking a bound or finite forbidden prime list and returning a new prime divisor of a polynomial value.

**Primary formalization risk.** The constant-term-zero case and nonzero-value guarantee require a careful normalization of the polynomial and input.

**Acceptance gate.** The theorem is uniform in a polynomial code and returns the value index, the new prime, and the divisibility proof.


# 10. Optional frontier after the main campaign

The following topics are not required for the first campaign, but they fit the architecture and would broaden the database beyond the standard sequence of textbook landmarks.

| ID | Topic | Reason to pursue |
| --- | --- | --- |
| X1 | Lifting-the-exponent lemmas (LTE) | A compact valuation toolkit with broad olympiad and prime-power utility; a natural sequel to E7 and Q4. |
| X2 | Carmichael function and RSA correctness | Connect the elementary library to verified public-key arithmetic while remaining entirely finite and first-order. |
| X3 | Counting roots of quadratic congruences modulo arbitrary moduli | Combine prime-power analysis and CRT into a complete algorithmic classification. |
| X4 | Cauchy-Davenport theorem | A finite additive-combinatorics landmark over \(\mathbb F_p\), likely approachable after F1 and polynomial methods. |
| X5 | Chevalley-Warning theorem | A deeper finite-field counting theorem with attractive divisibility consequences. |
| X6 | Bang-Zsigmondy theorem | A high-value primitive-prime-divisor result that would stress valuations, cyclotomic identities, and exceptional-case handling. |
| X7 | Continued-fraction best approximation theorems | Strengthen the Pell package into a reusable rational-approximation library without invoking real completeness. |
| X8 | Partition identities and congruences in finite form | Develop finite generating-polynomial methods before attempting infinite-series presentations. |
# 11. Work packages and release gates

## WP0. Landscape audit and statement freeze

**Outputs.** A searchable evidence ledger for each candidate, exact first-order statements, provenance links, and cautious novelty language.

**Gate.** Every theorem has a dated audit record and an approved canonical statement before proof work begins.

## WP1. HA kernel and certificate format

**Outputs.** Syntax, substitution, derivations, equality, induction schema, checker, serialization, and independent test suite.

**Gate.** A false formula is rejected; all sample derivations replay in two implementations or one implementation plus an independently generated checker.

## WP2. Arithmetic and bounded reflection

**Outputs.** Order, bounded decidability, primitive recursion graphs, finite search, coding, and reflection tactics.

**Gate.** All bounded goals used by later releases can be discharged by checked certificates rather than trusted host computation.

## WP3. Euclidean and factorization substrate

**Outputs.** Division, gcd, extended Euclid, Bezout, primes, least prime divisor, sorted factorization, valuations.

**Gate.** Canonical algorithms and uniqueness theorems are present, with strict-HA export and sample execution.

## WP4. Modular arithmetic release

**Outputs.** M1-M5, congruence API, modular cancellation, canonical representatives, simultaneous-congruence algorithms.

**Gate.** Release R1 passes complete soundness, completeness, and definitional-expansion audits.

## WP5. Elementary multiplicative number theory

**Outputs.** E1-E7 and D1-D2, including factorials, totient, divisor sums, Mobius, and finite permutations.

**Gate.** Release R2 provides the standard reusable elementary number-theory core.

## WP6. Finite fields and reciprocity

**Outputs.** F1-F2 and Q1-Q3, with coefficient-list polynomials, root counting, residue symbols, and reciprocity.

**Gate.** Release R3 culminates in quadratic reciprocity with an acyclic dependency graph.

## WP7. Prime powers and digit arithmetic

**Outputs.** E8-E9 and Q4-Q5: base expansions, carries, Hensel lifting, and primitive-root classification.

**Gate.** Release R4 contains certified digit and lifting algorithms with cross-theorem consistency checks.

## WP8. Diophantine classifications

**Outputs.** D3-D4 and A1-A4: descent, perfect numbers, progression primes, and sums of two squares.

**Gate.** Release R5 returns constructive witnesses or explicit obstructions wherever the theorem admits them.

## WP9. Large landmarks

**Outputs.** A5-A8: Pell, Bertrand, four squares, and Schur.

**Gate.** Release R6 demonstrates that the kernel and library scale to substantial textbook theorems.

## WP10. Metatheory, extraction, and publication

**Outputs.** Axiom-footprint reports, witness extraction, normalized proof exports, documentation, archival releases, and reproducible builds.

**Gate.** Every public theorem has a stable identifier, proof hash, human proof, machine certificate, and archived source bundle.


# 12. Proof-engineering standards

## 12.1 Algorithm-first theorem design

Whenever a theorem asserts existence, define the intended constructor first and prove its specification. Preferred interfaces include:

\[
\begin{aligned}
\operatorname{divmod}(a,b)&=(q,r),\\
\operatorname{xgcd}(a,b)&=(d,u,v),\\
\operatorname{factor}(n)&=L,\\
\operatorname{crt}(\vec m,\vec a)&=x,\\
\operatorname{pell}(D)&=(x,y).
\end{aligned}
\]

The existential theorem then follows immediately. This gives a stable computational API and prevents later extraction from depending on proof accidents.

## 12.2 Canonical outputs

Choose outputs that make uniqueness literal:

- quotient and remainder with \(r<b\);
- inverses in \([0,m)\);
- CRT solutions in \([0,M)\);
- sorted prime-factor lists;
- normalized signed integers;
- trimmed coefficient lists;
- sorted duplicate-free root lists;
- normalized Pythagorean parameters;
- least positive Pell solutions only if the proof actually constructs minimality; otherwise return the first certified solution from the chosen algorithm.

## 12.3 Bounded reflection

Build a checked reflection mechanism for bounded arithmetic. A decision procedure may run in the host, but it must emit a proof certificate for the bounded formula. Use it for:

- numeral computation and finite base cases;
- primality of fixed small numbers;
- polynomial evaluation on fixed inputs;
- finite list membership and duplicate checks;
- routine semiring inequalities;
- verification of sample outputs.

Reflection should not become a back door for unbounded classical reasoning.

## 12.4 Induction footprint

Every theorem manifest should list its induction instances by formula hash and a human-readable summary. This enables later research on the induction strength actually used by elementary number theory and supports ports to fragments of HA.

## 12.5 Direct proofs versus translations

The preferred public proof is direct and algorithmic. Negative translation, realizability, or PA-to-HA conservation may be used to:

- validate feasibility;
- compare computational content;
- generate an initial certificate;
- establish a second proof for cross-checking.

They should not obscure the theorem's natural constructor when one is available.

## 12.6 Reusable finite mathematics

The campaign should treat finite mathematics as a first-class library:

- map, fold, filter, and bounded enumeration;
- sortedness and duplicate freedom;
- finite sums and products;
- permutations and involutions;
- partitions and double counting;
- pigeonhole and finite choice for decidable predicates;
- cardinality-preserving bijections;
- bounded polynomial coefficient operations.

Many number-theory proofs become short only after this layer exists.

# 13. Theorem package format

A proposed repository layout is:

```text
ha-number-theory/
  kernel/
  extensions/
  arithmetic/
  finite/
  theorems/
    M3_binary_crt/
      statement.ha
      statement.expanded.ha
      proof.hap
      proof.normalized.hap
      manifest.yaml
      algorithm/
      tests/
      proof-notes.md
      prior-art.md
  checker/
  tools/
  docs/
  releases/
```

A theorem manifest should contain at least:

```yaml
id: M3
title: Binary Chinese remainder theorem
theory: HA
logic: intuitionistic-first-order
base_language: [zero, successor, addition, multiplication, equality]
extensions: [lt, divides, congruent, gcd, remainder]
classical_axioms: []
depends_on: [K0, K1, K2, K3, K4, M1]
induction_instances:
  - formula_hash: ...
    purpose: correctness of extended Euclid
certificate:
  compact_sha256: ...
  expanded_sha256: ...
algorithm:
  name: crt2
  executable_tests: ...
prior_art_audit:
  snapshot_date: 2026-08-03
  status: candidate-strict-HA-gap
```

The public website should render this metadata into a theorem page with the human statement, proof dependencies, axiom footprint, extracted algorithm, and links to every artifact.

# 14. Quality assurance

## 14.1 Kernel-level checks

- malformed binders and substitutions are rejected;
- eigenvariable side conditions are tested with negative cases;
- induction instances are syntactically and semantically well formed;
- equality substitution cannot capture variables;
- certificate parsing is deterministic;
- hashes are computed over canonical serialization;
- the checker rejects deliberately corrupted proofs.

## 14.2 Theorem-level checks

- compact certificate replays from a clean environment;
- expanded certificate or extension-elimination proof replays;
- dependency graph is acyclic;
- no unapproved axiom or host theorem appears;
- the pretty statement is linked to the machine formula by a checked equivalence or generated from it;
- extracted algorithms satisfy executable property tests;
- edge cases are explicit;
- the human proof names every nontrivial constructive choice.

## 14.3 Cross-validation

For high-value theorems, seek at least one of:

- a second proof route;
- replay by an independent checker;
- comparison with an existing formalization in another system;
- exhaustive finite testing below a documented bound;
- agreement between two independently implemented algorithms.

Examples include permutation and binomial proofs of Fermat, two proofs of quadratic reciprocity, and Lucas/Kummer cross-checks.

## 14.4 Reproducibility

Every release should include pinned tool versions, a clean build command, archived source, certificate hashes, and a machine-readable bill of materials. Avoid proofs that work only in an interactive session with hidden state.

# 15. Publication strategy

## 15.1 Publish the substrate, not only the headline theorem

A paper on CRT should publish division, gcd, congruence, inverse, coding, and the proof kernel as reusable artifacts. A paper on reciprocity should publish the residue-symbol and finite-counting libraries. This makes each result independently valuable even if a priority claim is later revised.

## 15.2 Suggested paper sequence

1. **A Small Kernel and Certificate Format for First-Order Heyting Arithmetic.**
2. **Euclidean and Modular Arithmetic in HA: Extended GCD, Modular Inverses, and CRT.**
3. **Finite Arithmetic in HA: Euler, Fermat, Wilson, Totients, and Mobius Inversion.**
4. **Finite Fields and Quadratic Reciprocity in HA.**
5. **Constructive Diophantine Classifications in HA: Pythagorean Triples, Two Squares, and Perfect Numbers.**
6. **Large Elementary Existence Theorems in HA: Pell, Bertrand, and Four Squares.**

Each paper should state exactly whether the novelty is a first formalization generally, a first constructive formalization, or a first strict object-level HA derivation.

## 15.3 Community model

Use public issue templates for:

- theorem proposals;
- prior-art reports;
- statement corrections;
- proof optimization;
- independent checker implementations;
- translations to other host provers;
- fragment-strength analysis.

Require code review by both a number theorist and a proof-theory/formalization reviewer for flagship theorems.

# 16. Risk register

| Risk | Failure mode | Mitigation |
| --- | --- | --- |
| Classical leakage | A host tactic or library theorem silently uses excluded middle, choice, proof irrelevance, quotient principles, or a classical integer library. | Require object-level certificates; scan manifests for imported axioms; replay after full expansion; forbid host theorems from counting as final evidence. |
| Statement drift | A convenient host-level formulation is not intuitionistically equivalent to the intended first-order theorem. | Freeze a canonical object-language statement; prove equivalence to every user-facing formulation inside HA where possible. |
| Circular dependencies | For example, using CRT to define sequence coding needed to prove CRT, or Wilson to prove Fermat while Fermat proves Wilson. | Maintain a machine-checked dependency DAG and require every release to build from an empty cache in topological order. |
| Unmanageable proof size | Full expansion of primitive-recursive definitions can make certificates enormous. | Support conservative definitional extensions with separately checked elimination theorems; retain compact and fully expanded artifacts. |
| Finite combinatorics duplication | Each theorem invents its own lists, permutations, counts, and sums. | Invest early in canonical finite-data and bijection APIs; require reuse reviews at theorem design time. |
| Inequality bottlenecks | Bertrand, Pell, and descent proofs can spend most effort on elementary bounds. | Develop a checked normalization/reflection layer for semiring and bounded integer inequalities, plus explicit finite-base-case evaluation. |
| Overstated novelty | An unindexed or unpublished strict-HA proof may exist. | Use "to the best of our knowledge" language, publish the search protocol, and invite prior-art corrections before claiming priority. |
| Poor computational content | A theorem is proved existentially but the extracted witness is opaque or unusable. | Specify algorithms first, prove graph correctness, retain executable reference implementations, and document complexity separately from logical correctness. |
| Kernel lock-in | The database becomes inseparable from one host prover. | Define a stable external certificate format and maintain a minimal standalone checker or a second verified parser/checker. |
| Maintenance decay | Proofs depend on unstable tactics or library internals. | Pin toolchains, archive containers, minimize tactic magic, serialize final certificates, and run continuous clean-room builds. |

# 17. Recommended execution order

The campaign should not begin with quadratic reciprocity or Pell. The highest-value path is:

1. Freeze K0-K3 and validate the certificate architecture.
2. Port division, extended Euclid, prime factorization, and valuations into strict HA.
3. Complete M1-M3 and publish the first named theorem release.
4. Add finite CRT and generalized CRT, then freeze the congruence API.
5. Build finite permutations, factorials, totient, divisor sums, and valuations.
6. Complete E2-E7, Wilson, Frobenius, and Pythagorean triples.
7. Build coefficient-list polynomials and prove F1.
8. Complete Euler criterion, Gauss's lemma, supplementary laws, and quadratic reciprocity.
9. Add cyclicity, Lucas, Kummer, Hensel lifting, and primitive-root classification.
10. Pursue the Diophantine line: Fermat exponent four, perfect numbers, progression primes, and two squares.
11. Finish with Pell, Bertrand, four squares, and Schur.

This order maximizes reuse and creates publishable intermediate releases. It also ensures that the most difficult theorems are attempted only after the kernel, coding, finite combinatorics, and automation have been tested repeatedly.

# 18. Definition of campaign success

The campaign is successful when it produces more than a collection of isolated scripts. The target is a durable mathematical database with:

- a precise and independently checkable HA trust boundary;
- a coherent dependency-ordered number-theory library;
- strict object-level derivations of recognizable theorems;
- constructive algorithms and obstruction certificates;
- transparent induction and axiom footprints;
- cautious, auditable novelty claims;
- reproducible archived releases;
- documentation suitable for logicians, number theorists, and proof engineers;
- an architecture that can be ported to another host prover without changing the mathematical certificates.

The decisive first milestone is not the largest theorem. It is a trustworthy release in which modular inverses and CRT are genuinely theorems of the encoded HA system. Once that standard is met, the rest of the campaign becomes cumulative rather than experimental.

# Appendix A. Formal statement templates

## A.1 Divisibility

\[
d\mid n\;:\!\!\iff\;\exists k\;(n=dk).
\]

## A.2 Positive congruence without subtraction

One base-language option is

\[
\operatorname{Cong}(m,x,y)\;:\!\!\iff\;\exists r\,\exists s\;(x+mr=y+ms).
\]

After division is available, prove equivalence with equality of canonical remainders.

## A.3 Primality

\[
\operatorname{Prime}(p)\;:\!\!\iff\;p>1\wedge
\forall d\le p\,(d\mid p\to d=1\vee d=p).
\]

All quantifiers in the divisor test are bounded.

## A.4 Canonical binary CRT

\[
\begin{aligned}
\forall m,n,a,b\;(&m>0\wedge n>0\wedge\operatorname{Coprime}(m,n)\to\\
&\exists x<mn\,[\operatorname{Cong}(m,x,a)\wedge\operatorname{Cong}(n,x,b)\\
&\qquad\wedge\forall y<mn\,((\operatorname{Cong}(m,y,a)\wedge\operatorname{Cong}(n,y,b))\to y=x)]).
\end{aligned}
\]

## A.5 Canonical factorization

\[
\forall n>0\;\exists L\;(
\operatorname{SortedPrimeList}(L)\wedge\operatorname{Product}(L)=n).
\]

Prove literal uniqueness of the sorted code.

## A.6 Pell

\[
\forall D>1\;(\operatorname{Nonsquare}(D)\to
\exists x>0\,\exists y>0\;(x^2=1+Dy^2)).
\]

This avoids object-language subtraction.

# Appendix B. Release checklist

For every release:

- [ ] Canonical statements frozen and reviewed.
- [ ] Prior-art audit snapshot archived.
- [ ] Dependency graph acyclic.
- [ ] Compact certificates replay.
- [ ] Expanded certificates or elimination proofs replay.
- [ ] No unapproved axioms.
- [ ] Induction instances listed.
- [ ] Algorithms and obstruction certificates tested.
- [ ] Human proof notes complete.
- [ ] Standalone checker or independent replay completed for flagship theorems.
- [ ] Toolchain pinned and clean build verified.
- [ ] Archive DOI or equivalent persistent release created.
- [ ] Novelty wording reviewed against the evidence ledger.

# References

The landscape claims in this document are a dated snapshot as of 3 August 2026. Repository contents and publication status may change.

- **[R1]** F. Wiesnet, "Verified Program Extraction in Number Theory: The Fundamental Theorem of Arithmetic and Relatives," arXiv:2504.03460, 2025, revised material and repository snapshot current in 2026. <https://arxiv.org/abs/2504.03460>
- **[R2]** F. Wiesnet, MinlogArith repository: gcd, extended Euclid, prime factorization, infinitude of primes, FTA, and Fermat factorization in Minlog/TCF. <https://github.com/FranziskusWiesnet/MinlogArith>
- **[R3]** A. Lundstedt, pca-realizability: an explicit Coq encoding of HA syntax, axioms, semantics, and realizability infrastructure. <https://github.com/anderslundstedt/pca-realizability>
- **[R4]** Y. Kaddar et al., Coherence of first-order Heyting arithmetic in Coq. <https://github.com/youqad/Coherence-of-Heyting-arithmetic>
- **[R5]** D. Larchey-Wendling and Y. Forster, "Hilbert's Tenth Problem in Coq," arXiv:2003.04604. <https://arxiv.org/abs/2003.04604>
- **[R6]** Coq/Rocq Library of Undecidability Proofs, including constructive CRT utilities, recursive-function coding, DPRM, and H10 undecidability. <https://github.com/uds-psl/coq-library-undecidability>
- **[R7]** M. Fujiwara and T. Kurahashi, "Conservation theorems on semi-classical arithmetic," arXiv:2107.11356. <https://arxiv.org/abs/2107.11356>
- **[R8]** Y. Akama, S. Berardi, S. Hayashi, and U. Kohlenbach, "An arithmetical hierarchy of the law of excluded middle and related principles," LICS 2004, DOI 10.1109/LICS.2004.1319613. <https://doi.org/10.1109/LICS.2004.1319613>
- **[R9]** F. Aschieri and S. Berardi, "Interactive Learning-Based Realizability for Heyting Arithmetic with EM1," Logical Methods in Computer Science 6(3), 2010. <https://doi.org/10.2168/LMCS-6(3:19)2010>
- **[R10]** S. Berardi and S. Steila, "Ramsey's Theorem for Pairs and K Colors as a Sub-Classical Principle of Arithmetic," Journal of Symbolic Logic 82(2), 2017. <https://doi.org/10.1017/jsl.2016.41>
- **[R11]** S. Shapiro, C. McCarty, and M. Rathjen, "Intuitionistic sets and numbers: small set theory and Heyting arithmetic," Archive for Mathematical Logic 64, 2025. <https://doi.org/10.1007/s00153-024-00935-4>
- **[R12]** A. S. Troelstra, Metamathematical Investigation of Intuitionistic Arithmetic and Analysis, Springer Lecture Notes in Mathematics 344, 1973. <https://doi.org/10.1007/BFb0066739>
- **[R13]** A. S. Troelstra and D. van Dalen, Constructivism in Mathematics, Volumes I-II, North-Holland, 1988. <https://www.sciencedirect.com/bookseries/studies-in-logic-and-the-foundations-of-mathematics/vol/121/suppl/C>
- **[R14]** D. Nelson, "Recursive functions and intuitionistic number theory," Transactions of the American Mathematical Society 61, 307-368, 1947. <https://www.jstor.org/stable/1990143>
- **[R15]** P. Hajek and P. Pudlak, Metamathematics of First-Order Arithmetic, Springer, 1993. <https://doi.org/10.1007/978-3-662-22156-3>
- **[R16]** F. Wiedijk, Formalizing 100 Theorems, continuously maintained survey of theorem formalizations across proof assistants. <https://www.cs.ru.nl/~freek/100/>
