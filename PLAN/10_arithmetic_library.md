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
- [x] Replay and independently check all 170 unique library entries and enforce
      the live 32,768-node/depth-128 import bound.
- [x] Generate a deterministic versioned JSON snapshot, exact metrics,
      certificate hashes, structural Cut counts, and Mermaid dependency graph.

## M20C — Conservative notation and modular congruence

- [ ] Specify untrusted, round-tripping expansions for `a | b`, balanced
      natural congruence, relational gcd/coprimality, and primality.
- [x] Prove balanced congruence reflexive and symmetric.
- [x] Prove balanced congruence transitive as `mod_eq_trans`.
- [x] Prove congruence compatibility with addition as `mod_eq_add`.
- [x] Prove right, left, and paired multiplication compatibility as
      `mod_eq_mul_right`, `mod_eq_mul_left`, and `mod_eq_mul`.
- [x] Bridge directed quotient/remainder decompositions into balanced
      congruence as `remainder_decomposition_to_mod_eq`.
- [x] Prove bounded representative uniqueness as `mod_eq_bounded_unique`.
- [x] Recover a directed remainder decomposition from nonzero modulus, bound,
      and balanced congruence as `mod_eq_to_remainder_decomposition`.
- [ ] Add even/odd definitions, dichotomy, exclusivity, arithmetic tables, and
      parity-as-congruence-modulo-two.
- [ ] Add fixed-modulus residue exhaustions only as generated downstream
      clients of generic division/remainder facts.

## M20D — Division, gcd, and prime spine

- [x] Add the discrete-order, additive/multiplicative monotonicity, cancellation,
      and strict-block contradiction interface needed by division uniqueness.
- [x] Add the concrete bounded-search interface needed for constructive factor
      extraction.
- [ ] Add reusable strong-induction and least-counterexample proof-producing
      interfaces for later greatest-prime and factorization descent.
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
- [ ] Add round-tripping prime surface syntax and capture tests; the checked
      theorem layer deliberately continues to use fully expanded formulas.
- [x] Prove constructive prime/composite and prime decisions, prime nonzero,
      equality/divisibility decisions, and the bounded factor-search API:
      `eq_decidable`, `multiple_decidable_nonzero`, `multiple_decidable`,
      `factor_property_succ`, `factor_search_up_to`, `prime_or_composite`,
      `prime_nonzero`, and `prime_decidable`.
- [x] Prove Euclid's lemma constructively from relational gcd existence, Gauss,
      and the expanded prime factor-pair disjunction.
- [x] Prove proper-factor descent and constructive prime-divisor existence via
      `factor_nonzero_left`, `proper_factor_lt`,
      `prime_divisor_exists_up_to`, and `prime_divisor_exists`.
- [ ] Prove primes above every bound and the greatest-prime descent interface
      needed by canonical factorization.

## M20E — Finite factorization representation and FTA

- [x] Compare Gödel-coded sequences with a reviewed finite-list/multiset layer;
      select sorted β-coded factors plus a β-coded prefix-product trace, and
      document the trust and browser-cost implications.
- [x] Prove the expanded β-value foundation: `beta_modulus_nonzero`,
      `beta_at_self_of_bound`, `beta_at_exists`, `beta_at_unique`, and
      `beta_at_exists_unique`.
- [x] Bridge every expanded β value to balanced congruence as
      `beta_at_to_mod_eq`.
- [x] Prove the reverse bounded bridge as `beta_at_of_mod_eq_bound`, so
      expanded β decoding is equivalent to bound plus balanced congruence.
- [x] Prove the subtraction-free binary CRT layer:
      `bezout_mod_left`, `bezout_mod_right`,
      `mod_eq_predecessor_cancel`, `binary_crt`,
      `binary_crt_remainders`, and `binary_crt_beta_pair`.
      The β-pair theorem retains pairwise modulus coprimality as an explicit
      premise.
- [ ] Prove β-modulus coprimality and bounded CRT iteration, then
      finite-prefix extension/restriction, prefix products, all-prime, sorted
      canonical form, and extensional equality without adding kernel atoms.
      Add hygienic round-tripping surface expanders separately. The
      mathematical schemas and representation choice are documented.
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

- Checked runtime: 170 unique theorems — 23 baseline and 147 post-baseline.
  The latter are the 135-entry general foundational layer plus twelve unique upstream
  modular capstones.
- Research catalog: 177 nodes — 23 `checked_existing`, 147 `checked_m20`, three
  `planned_expressible`, and four `blocked_by_language`.
- Shared-certificate metrics: 99,137 total structural proof nodes and 2,693
  Cuts across 130 Cut-bearing entries. The largest by nodes and Cuts is
  `binary_crt_beta_pair` at 6,941/201.
  `prime_divisor_exists` supplies the ladder's maximum depth of 80. The
  immutable upstream report retains the
  former fully expanded capstone metric of 21,515/depth 66.
- Trusted-kernel change: one self-contained Cut constructor and checker rule.
  The checker is 247 lines (formerly 234). The object language and logical
  strength are unchanged; the untrusted erasure utility is diagnostic and is
  not a complete or authoritative admission route.
- Full FTA companion status: checked in Lean for every nonzero natural, with
  finite-list existence and permutation uniqueness and no `sorryAx`.
- Full Peano FTA status: absent from `pa lib` pending greatest-prime descent
  and the still-open β-modulus coprimality, bounded CRT iteration,
  finite-prefix, and prefix-product representation spine;
  no admitted theorem or hidden primitive.
- Validation record: all 1,098 Peano tests pass on CPython 3.10, including the
  constructive CRT admission gate. Lambda's 360 tests plus 36 subtests, the
  36-source warning-as-error Jupyter Book, 213 deep links, and 45
  sessions/264 replayed commands, the
  249-note/2,194-link Obsidian graph with 170 generated lemma
  notes, and exact snapshot/catalog/corpus/application/Lean-FTA audits are
  current. The corpus retains 13,344 transitions/1,692 sessions under run
  fingerprint `53305cfb…`; the isolated smoke has 340 sessions, 4,474 raw
  and 4,471 unique transitions, and all 170 authored QEDs. Local browser build
  `2026-07-29e` has content identity `a-ac494e524f2f`; it is not
  staged, deployed, or promoted.
