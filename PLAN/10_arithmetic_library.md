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

- A theorem is `checked` only after deterministic script replay, dependency-cut
  elimination, and independent empty-context kernel acceptance.
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
- [x] Replay and independently check all 51 total library entries and enforce
      the live 4,096-node/depth-128 import bound.
- [x] Generate a deterministic JSON snapshot, exact metrics, certificate hashes,
      and Mermaid dependency graph.

## M20C — Conservative notation and modular congruence

- [ ] Specify untrusted, round-tripping expansions for `a | b`, balanced
      natural congruence, relational gcd/coprimality, and primality.
- [ ] Prove balanced congruence reflexive, symmetric, and transitive.
- [ ] Prove congruence compatibility with addition and multiplication, plus
      equality/divisibility transport.
- [ ] Add even/odd definitions, dichotomy, exclusivity, arithmetic tables, and
      parity-as-congruence-modulo-two.
- [ ] Add fixed-modulus residue exhaustions only as generated downstream
      clients of generic division/remainder facts.

## M20D — Division, gcd, and prime spine

- [ ] Add strong induction and least-counterexample interfaces suited to
      divisor descent.
- [ ] Prove quotient-remainder existence and uniqueness for positive divisors.
- [ ] Prove relational gcd existence/uniqueness and Euclidean-step invariance.
- [ ] Prove subtraction-free signed-pair Bézout and Gauss cancellation.
- [x] Check `prime_two` as a completely expanded first-order formula, without
      adding a primitive `Prime` predicate.
- [ ] Add round-tripping prime surface syntax and capture tests, and prove zero
      and one non-prime before admitting a broader prime API.
- [ ] Prove proper-factor descent, prime-divisor existence, Euclid's lemma, and
      primes above every bound.

## M20E — Finite factorization representation and FTA

- [ ] Compare Gödel-coded sequences with a reviewed finite-list/multiset layer;
      document the trust and browser-cost implications.
- [ ] Specify finite product, all-prime, permutation/multiplicity, deletion,
      and product-cancellation interfaces.
- [ ] Add a companion cross-check in a mature prover without treating it as
      Peano theorem authority.
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
- [ ] Publish a reviewable branch and draft pull request targeting `peano-lab`;
      do not merge or deploy without owner authorization.

## Current acceptance record

- Checked runtime: 51 theorems, of which 28 are the M20 extension.
- Research catalog: 75 nodes — 23 `checked_existing`, 28 `checked_m20`, 20
  `planned_expressible`, and four `blocked_by_language`.
- Largest new closed certificate: 1,601 nodes, depth 59.
- Trusted-kernel changes: none.
- Full FTA status: `blocked_by_language` pending a finite-factorization
  representation; no admitted theorem or hidden primitive.
