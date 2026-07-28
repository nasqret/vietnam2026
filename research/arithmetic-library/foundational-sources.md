# Foundational arithmetic sources and clean-room policy

## Purpose

This file records the source classes used to design the general arithmetic
library, their licensing boundaries, and the dependency architecture they
support. A citation establishes provenance for a topic or coverage decision;
it does not make an external proof part of Peano's trusted base.

## Verified source register

| Source | Immutable reference | License status | Allowed role |
|---|---|---|---|
| Peano Lab checked ladder | Project-pinned source and validation report | MIT/project-internal | Binding source for existing checked theorems |
| Published Peano modular catalog | [`923f6816c8c5f17a9a276b9e767145f89aff2e09`](https://github.com/nasqret/vietnam2026/tree/923f6816c8c5f17a9a276b9e767145f89aff2e09/artifacts/peano-library) | MIT with retained notice | Binding provenance for 26 source records; fourteen identical overlaps are deduplicated |
| Mathlib natural factorization | [`37df177aaa770670452312393d4e84aaad56e7b6`](https://github.com/leanprover-community/mathlib4/tree/37df177aaa770670452312393d4e84aaad56e7b6) | [Apache-2.0](https://github.com/leanprover-community/mathlib4/blob/37df177aaa770670452312393d4e84aaad56e7b6/LICENSE) | Pinned Lean FTA companion only; no Peano theorem authority |
| Natural Number Game 4 | [`727e4d219838eeb7f3945d2e9a0539f244d50540`](https://github.com/leanprover-community/NNG4/tree/727e4d219838eeb7f3945d2e9a0539f244d50540) | [Apache-2.0](https://github.com/leanprover-community/NNG4/blob/727e4d219838eeb7f3945d2e9a0539f244d50540/LICENSE) | Statement and coverage map; Peano proofs reconstructed |
| Heather Macbeth, *The Mechanics of Proof* | [`e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b`](https://github.com/hrmacbeth/math2001/tree/e660f42b13ddcb6d12b52ba036d6bd071a0cfb9b) | No repository license; arithmetic files say `All rights reserved` | Reference-only clean-room taxonomy |
| Weissman number-theory notebooks | [`5e819522e52e6a75c5dec597f024729bfc9ba4c5`](https://github.com/MartyWeissman/Python-for-number-theory/tree/5e819522e52e6a75c5dec597f024729bfc9ba4c5) | [GPL-3.0](https://github.com/MartyWeissman/Python-for-number-theory/blob/5e819522e52e6a75c5dec597f024729bfc9ba4c5/LICENSE) | External algorithm and example index only |
| Weissman, *An Illustrated Theory of Numbers* | [AMS publication page](https://bookstore.ams.org/mbk-105/) | Publisher-controlled book content | Bibliographic reference only |
| Open Logic Project TeX | [`9620cc73f9c8e0ad003c514a5d3748f29611c4c0`](https://github.com/OpenLogicProject/OpenLogic/tree/9620cc73f9c8e0ad003c514a5d3748f29611c4c0) | CC BY 4.0 | Open TeX reference for induction and arithmetization |
| Stein elementary-number-theory TeX | [`c4984c7ddb22258674816f8c000b0d8eb485d694`](https://github.com/williamstein/ent/tree/c4984c7ddb22258674816f8c000b0d8eb485d694) | No repository license; Springer publication | Reference-only TeX coverage map |
| Newstead, *An Infinite Descent into Pure Mathematics* TeX | [`3fcac1afe2a37fb92adf5fa9d22c25c83b1abf11`](https://codeberg.org/cnewstead/infdesc/src/commit/3fcac1afe2a37fb92adf5fa9d22c25c83b1abf11) | CC BY-SA 4.0 and LPPL 1.3c | Open TeX reference for induction and elementary number theory |

The detailed source-specific mappings are maintained in
[`nng4-map.md`](nng4-map.md), [`math2001-map.md`](math2001-map.md), and
[`illustrated-number-theory-map.md`](illustrated-number-theory-map.md).

## TeX and source-material decision

No external TeX manuscript is vendored in this arithmetic corpus. The search
did identify three pinned source trees with different legal roles:

- the Open Logic Project publishes CC-BY-4.0 TeX for natural-number induction,
  strong induction, and arithmetization;
- Clive Newstead publishes CC-BY-SA-4.0/LPPL TeX for induction, divisibility,
  modular arithmetic, and primes;
- William Stein publishes the TeX tree for *Elementary Number Theory: Primes,
  Congruences, and Secrets*, but the repository has no license and identifies
  a Springer publication, so it remains reference-only.

The first two could legally support attributed adaptations under their license
conditions. This release still proves and explains its facts independently so
the corpus has one coherent voice and no unnecessary license-derived files.

The Mathlib dependency is different: it is imported by the explicitly
separate `artifacts/lean-fta` formal companion under Apache-2.0. The companion
is kernel-checked in Lean, rejects `sorryAx`, and records its standard axioms;
it is never converted into a trusted Peano theorem constant.

The published modular catalog is repository code under MIT, not clean-room
reference material. Its exact 26-record source report, original source commit,
catalog hash, and notice are retained. Fourteen records match independently
developed M20 specifications exactly; the runtime guard accepts those once,
adds twelve unique capstones, and rejects any nonidentical same-name record.

- The audited Macbeth project supplies Lean and generated RST/HTML but no
  explicitly licensed TeX source. Its absence of a reuse license makes the
  material reference-only.
- The Weissman companion repository supplies GPL-3.0 notebooks, not the
  book's TeX source. GPL notebook code is not copied into the MIT project.
- The AMS publication page is not an open-source grant for the book's prose,
  illustrations, or source.
- NNG4 has an explicit Apache-2.0 license, but its Lean teaching source is
  used only as a coverage map; Peano proofs remain independent.

An additional source may be vendored only after its exact immutable revision,
copyright holder, and explicit license have been recorded and compatibility
with the project license has been reviewed. A downloadable `.tex` file without
an explicit reuse license is not an open source.

Standard arithmetic facts are instead proved independently from Peano's
axioms. External sources may identify a theorem worth including, but no
external proof text or code is needed for the certificate.

## Clean-room formalization workflow

1. **Register.** Record the source ID, immutable URL, retrieval date, license,
   and one of the repository's reuse modes.
2. **Extract only coverage.** Record a short fact label and mathematical
   subject. Do not paste proof text, source code, distinctive exposition, or
   exercise solutions.
3. **Normalize.** State the target independently in Peano's canonical syntax,
   expanding unsupported definitions or documenting a language blocker.
4. **Design dependencies.** Link only to earlier checked Peano entries. A
   source's import graph is evidence about subject structure, not the Peano
   dependency graph.
5. **Reconstruct.** Write a new tactic script from the PA axioms and checked
   local lemmas. Do not transliterate Lean, Python, TeX, or prose proofs.
6. **Check.** Replay the script, retain each dependency as a self-contained
   `Cut(A,B,lemma,body)`, and submit the resulting closed certificate to the
   independent kernel. Every Cut embeds both formulas and both proof branches;
   no theorem name or hash supplies authority.
7. **Measure.** Record proof nodes, depth, replay determinism, and live-`use`
   compatibility.
8. **Document.** Link theorem, dependency graph, source record, certificate,
   journal entry, Jupyter Book page, and Obsidian note without duplicating
   restricted source content.

## General dependency architecture

The library should be organized by mathematical prerequisites rather than by
the chapter order of any one source.

### L0: Logic, equality, and congruence

- implication, conjunction, disjunction, negation, and quantifier helpers;
- equality reflexivity, symmetry, transitivity, and substitution;
- congruence for successor, addition, and multiplication;
- named left/right and nested-context congruence wrappers.

These are Peano-native facts and should not be attributed to an external
course merely because that course uses a powerful congruence tactic.

### L1: Natural semiring normalization

- successor normal forms;
- zero and one laws;
- associative, commutative, and distributive laws;
- additive cancellation and zero-sum rigidity;
- zero products, nonzero products, multiplication cancellation, and products
  equal to one;
- high-value rearrangement lemmas chosen to keep expanded certificates small.

### L2: Order and induction

- additive-witness order laws;
- zero and successor bounds;
- monotonicity and cancellation under addition and multiplication;
- strict order encoded by successor;
- trichotomy, finite-bound decompositions, strong induction, and least
  counterexample.

### L3: Divisibility

- existential witness definition;
- identity, zero, one, transitivity, and equality transport;
- closure under addition, multiplication, and repeated products;
- positive-divisor bounds, common divisors, common multiples, and exclusion
  between consecutive multiples.

### L4: Congruence and residues

- subtraction-free balanced congruence on naturals;
- equivalence-relation laws;
- compatibility with addition and multiplication;
- quotient/residue bridge lemmas;
- generic decomposition arithmetic and fixed-modulus residue exhaustions.

### L5: Parity and small moduli

- even/odd definitions, dichotomy, and exclusivity;
- parity arithmetic;
- fixed-square and fixed-power residue facts;
- examples such as the fourth-power modulo five theorem only as applications
  of general residue infrastructure.

### L6: Division, gcd, and coprimality

- checked natural division algorithm and uniqueness;
- checked relational `IsGCD` existence and uniqueness;
- checked Euclidean-step invariance;
- checked subtraction-free four-natural balanced Bézout relation;
- checked coprimality and Gauss cancellation; modular inverses remain planned.

### L7: Primes

- prime and composite definitions;
- the checked expanded instance `prime_two` and its small-factor prerequisites;
- the checked general divisor-of-a-prime one-or-self API;
- checked Euclid's lemma, with finite-product consequences still planned;
- proper factors and constructive prime-divisor existence;
- infinitude of primes;
- bounded primality-test specifications after the mathematical layer is
  complete.

### L8: Factorization

- strong-induction factorization existence;
- prime-factor cancellation;
- uniqueness up to permutation or equality of multiplicities;
- valuations and arithmetic-function interfaces;
- the Fundamental Theorem of Arithmetic as the capstone.

### L9: Powers and computational number theory

- generic powers and their algebra;
- repeated-squaring correctness;
- Fermat's little theorem and Euler's theorem;
- totients, multiplicative functions, and verified finite algorithms;
- pedagogical cryptographic correctness examples.

## Current-language capability boundary

The current kernel language has natural-number terms `0`, `S`, `+`, and `*`,
equality, `<=` as defined sugar, first-order connectives and quantifiers, and
induction. It has no integers, subtraction, user-defined predicates or
functions, generic powers, lists, multisets, finite maps, or function
quantification.

This boundary should be explicit in the plan:

- **Current-language feasible:** semiring and order facts; existential
  divisibility; balanced natural congruence; parity; natural quotient/remainder
  existence; relational gcd; prime definition; prime-divisor existence;
  Euclid's lemma; infinitude of primes.
- **Feasible with relational encodings but potentially unwieldy:** generic
  algorithms, signed-coefficient APIs beyond the checked four-natural balanced
  Bézout relation, and recursive arithmetic-function graphs.
- **Language-design milestone:** generic exponentiation, finite sequences or
  multisets, finite-support exponent maps, and finite counting.
- **Blocked as a natural single theorem until that milestone:** the full
  Fundamental Theorem of Arithmetic and its uniqueness clause, totient-based
  results, and generic finite-product theorems.

Gödel coding represents sequences inside first-order arithmetic at the cost of
a less direct pedagogical API and potentially very large certificates. The
representation review nevertheless selected a conservative Gödel-β authoring
facade because it expands into the unchanged Peano language; the relations and
their proof spine still require implementation and ordinary kernel-checked
certificates.

## Source and artifact invariants

- Every external URL used as proof-planning evidence is pinned when the host
  supports immutable revisions.
- A theorem never becomes trusted because Lean, Python, a notebook, or a book
  asserts it; only Peano's independent kernel accepts certificates.
- GPL and unlicensed source content are not copied into MIT files.
- Generated examples and notebook test vectors are labeled as tests, never as
  proofs.
- Each theorem has one canonical name, statement, dependency list, source
  links, status, and certificate metrics.
- Obsidian and Jupyter Book pages link to the canonical theorem record rather
  than maintaining divergent copies of the statement or dependency graph.
