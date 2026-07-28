# Foundational arithmetic library — L2/L3 plan

## Objective

Build a versioned, dependency-ordered, independently checked arithmetic
library for Peano Lab. The library begins with equality and semiring structure,
continues through order, divisibility, modular congruence, division, gcd and
primes, and reaches the Fundamental Theorem of Arithmetic only after the
language has a reviewed finite-factorization representation.

The modulus-five fourth-power theorem is a downstream regression example. It
does not determine the architecture.

## Non-negotiable contracts

- A theorem is `checked` only after deterministic script replay, packaging of
  complete dependency proofs in self-contained Cuts, and independent
  empty-context kernel acceptance. Names and hashes never confer authority.
- Divisibility, congruence, gcd, coprimality, and primality begin as conservative
  formula expansions or relations; no new trusted predicate is introduced for
  convenience.
- Every catalog node has a stable name, layer, ordered dependencies, status,
  source references, and either a Peano statement or an explicit blocker.
- External curricula provide coverage and provenance. Unlicensed or GPL source
  code/prose is not copied into the MIT/CC BY-SA corpus.
- Code, generated artifact, Jupyter Book, and Obsidian views use the same stable
  names and are checked for drift.
- Full factorization is not claimed inside current Peano syntax until finite
  products and uniqueness up to order/multiplicity are representable.

## M20A — Architecture, source audit, and version-1 catalog

- [x] Audit the active Peano language and identify the exact expressibility
      boundary for divisibility, congruence, gcd, primes, and factorization.
- [x] Audit and pin the requested Natural Number Game 4, *The Mechanics of
      Proof*, and *An Illustrated Theory of Numbers* resources.
- [x] Record license/reuse modes and adopt clean-room reconstruction where
      redistribution or adaptation rights are absent or incompatible.
- [x] Create a machine-readable source register and research catalog with
      checked, planned-expressible, and language-blocked statuses.
- [x] Validate unique names, source IDs, dependency order, checked-runtime
      coverage, and explicit blockers.

## M20B — First checked general-purpose layer

- [x] Add named equality symmetry/transitivity and successor/addition/
      multiplication congruence.
- [x] Add left/right additive cancellation and the basic `zero_le`,
      `le_succ_self`, and `le_zero` endpoints.
- [x] Add the symmetric zero-sum projection, nonzero-product closure, the
      two-large-factors obstruction, and the first expanded-prime instance
      `prime_two`.
- [x] Add witness-expanded divisibility facts: zero, one, reflexivity,
      transitivity, addition closure, and both multiplication orientations.
- [x] Add both constructive normal forms for non-divisibility.
- [x] Add modulus-independent quotient-and-remainder transport through
      addition and squaring.
- [x] Replay and independently check all 137 unique library entries and enforce
      the live 32,768-node/depth-128 import bound.
- [x] Generate a deterministic versioned JSON snapshot, exact metrics,
      certificate hashes, structural Cut counts, and Mermaid dependency graph.

## M20C — Conservative notation and modular congruence

- [ ] Specify untrusted, round-tripping expansions for `a | b`, balanced
      natural congruence, relational gcd/coprimality, and primality.
- [x] Prove balanced congruence reflexive and symmetric.
- [ ] Prove balanced congruence transitive.
- [ ] Prove congruence compatibility with addition and multiplication, plus
      equality/divisibility transport.
- [ ] Add even/odd definitions, dichotomy, exclusivity, arithmetic tables, and
      parity-as-congruence-modulo-two.
- [ ] Add fixed-modulus residue exhaustions only as generated downstream
      clients of generic division/remainder facts.

## M20D — Division, gcd, and prime spine

- [x] Add the discrete-order, additive/multiplicative monotonicity, cancellation,
      and strict-block contradiction interface needed by division uniqueness.
- [ ] Add strong-induction, least-counterexample, and bounded-search interfaces
      suited to divisor descent and constructive factor extraction.
- [x] Prove quotient-remainder existence and uniqueness for positive divisors,
      plus zero-remainder equivalence bridges for divisibility.
- [x] Prove the relational gcd projection, symmetry, constructor, and uniqueness
      API, including mutual-divisibility antisymmetry.
- [x] Prove both directions of relational gcd Euclidean-step invariance.
- [x] Add and audit the conservative self-contained `Cut(A,B,lemma,body)`
      proof-sharing rule without changing the PA term/formula language, axioms,
      induction schema, or intuitionistic default.
- [x] Prove relational gcd existence by bounded induction and derive the
      unrestricted theorem from reflexivity of the order relation.
- [x] Prove subtraction-free four-natural Bézout, its common-divisor and
      scaling bridges, and Gauss cancellation.
- [x] Check `prime_two` as a completely expanded first-order formula, without
      adding a primitive `Prime` predicate.
- [ ] Add round-tripping prime surface syntax and capture tests, prove zero and
      one non-prime, and complete the remaining composite/prime decision and
      bounded divisor-search API.
- [x] Prove Euclid's lemma constructively from relational gcd existence, Gauss,
      and the expanded prime factor-pair disjunction.
- [ ] Prove proper-factor descent, constructive prime-divisor existence, and
      primes above every bound.

## M20E — Finite factorization representation and FTA

- [x] Compare Gödel-coded sequences with a reviewed finite-list/multiset layer;
      select sorted β-coded factors plus a β-coded prefix-product trace, and
      document the trust and browser-cost implications.
- [ ] Freeze and implement decoded-value, finite-product, all-prime, sorted
      canonical-form, and extensional-equality expanders with hygiene and
      round-trip tests, without adding kernel atoms. The mathematical schemas
      and representation choice are documented.
- [x] Add a pinned Lean 4/Mathlib companion proving existence and uniqueness
      up to permutation, with `sorryAx` rejection and an exact standard-axiom
      audit, without treating it as Peano theorem authority.
- [ ] Prove prime-factorization existence by strong induction.
- [ ] Prove uniqueness using Euclid's lemma and the selected finite-collection
      equality.
- [ ] Expose FTA through `pa lib` only after its closed certificate and all
      representation lemmas pass the ordinary kernel and resource gates.

## M20F — Knowledge and release gates

- [x] Add a dedicated Jupyter Book part with formulas, executable commands,
      trust boundary, dependency route, source audit, and extension workflow.
- [x] Add an arithmetic Obsidian MOC, concept notes, and generated per-lemma
      pages linked by exact dependencies and dependents.
- [x] Update project memory, journal, plans, root maps, and artifact index.
- [x] Pass the complete Peano suite, warning-as-error book build, executable
      command replay, vault/link checks, research-catalog validator, artifact
      drift checks, and browser deployment-manifest checks.
- [x] Publish a reviewable branch and draft pull request targeting `peano-lab`;
      do not merge or deploy without owner authorization.

## Current acceptance record

- Checked runtime: 137 unique theorems — 23 baseline and 114 post-baseline.
  The latter are the 102-node foundational layer plus twelve unique upstream
  modular capstones.
- Research catalog: 148 nodes — 23 `checked_existing`, 114 `checked_m20`, seven
  `planned_expressible`, and four `blocked_by_language`.
- Shared-certificate metrics: 52,433 total structural proof nodes and 1,345
  Cuts across 98 entries. The largest by nodes is
  `euclid_prime_dvd_product` at 5,382/depth 55, while the ladder's maximum
  depth remains 57. The immutable upstream report retains the
  former fully expanded capstone metric of 21,515/depth 66.
- Trusted-kernel change: one self-contained Cut constructor and checker rule.
  The checker is 247 lines (formerly 234). The object language and logical
  strength are unchanged; the untrusted erasure utility is diagnostic and is
  not a complete or authoritative admission route.
- Full FTA companion status: checked in Lean for every nonzero natural, with
  finite-list existence and permutation uniqueness and no `sorryAx`.
- Full Peano FTA status: absent from `pa lib` pending closed certificates for
  prime-divisor existence and the selected β-sequence/product encoding;
  no admitted theorem or hidden primitive.
- Current validation: 1,090 Peano tests on Python 3.10; 36-source
  warning-as-error Jupyter Book; 199 deep links and 45 sessions/264 replayed
  commands; 216-note/1,696-link Obsidian graph; exact
  snapshot, catalog, corpus, application-manifest, and Lean FTA audits.
