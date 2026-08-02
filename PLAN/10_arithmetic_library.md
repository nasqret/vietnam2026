# Foundational arithmetic library — L2/L3 plan

## Objective

Build a versioned, dependency-ordered, independently checked arithmetic
library for Peano Lab. The library begins with equality and semiring structure,
continues through order, divisibility, modular congruence, division, gcd and
primes, and now reaches a native Fundamental Theorem of Arithmetic through a
reviewed finite-factorization representation based on natural-number codes.

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
- Full factorization is claimed only in its exact checked form: sorted
  Gödel-β-coded factors, a β-coded prefix-product trace, and extensional
  equality of decoded entries. This does not add a primitive list type and
  does not identify non-unique raw codes.

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
- [x] Replay and independently check the published 189-entry checkpoint.
      The audited FTA integration now uses the dual live/use cap of 500,000
      structural occurrences, 100,000 distinct proof objects, and depth 256.
- [x] Generate a deterministic versioned JSON snapshot, exact metrics,
      certificate hashes, structural Cut counts, and Mermaid dependency graph.

## M20C — Conservative notation and modular congruence

- [x] Specify untrusted, round-tripping expansions for `a | b`, balanced
      natural congruence, relational gcd/coprimality, and primality. The
      completed 40-entry Proof Explorer registry (38 used in this closure)
      now checks conservative expansion by parsed PA AST equality; it is
      reading notation, not trusted core-language or kernel syntax.
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
- [x] Add formula-specific strengthened-induction certificates for
      greatest-prime and factorization descent. A polymorphic predicate-level
      induction theorem remains outside the first-order object language.
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
- [x] Prove the greatest-prime-divisor search, existence, quotient bound, and
      strict descent interface needed by canonical factorization.
- [x] Prove a prime above every supplied bound as `prime_unbounded`, a later
      constructive client of bounded common multiples and prime-divisor
      existence. Its certificate has 4,595 nodes, depth 82, and 146 Cuts; it
      is not needed by the checked FTA route.

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
- [x] Prove the correct conditional β-modulus coprimality interface:
      `beta_modulus_coprime_base`,
      `common_divisor_beta_moduli_divides_gap_times_c`, and
      `beta_moduli_coprime_of_gap_dvd`; discharge the β-pair CRT premise
      with `binary_crt_beta_pair_of_gap_dvd`.
- [x] Construct a nonzero multiple of every positive natural through a bound
      with `bounded_common_multiple_step` and
      `bounded_common_multiple_exists`.
- [x] Combine the bounded common multiple with ordered-index/gap bounds through
      `beta_moduli_coprime_of_lt_bounded_common_multiple`,
      `beta_moduli_pairwise_coprime_bounded`, and
      `bounded_beta_moduli_pairwise_coprime_exists`.
- [x] Prove the fold algebra: `coprime_mul_left`,
      `coprime_mul_right`, `mod_eq_of_mod_eq_multiple`, and
      the invariant-preserving one-step constructor `binary_crt_fold_step`.
- [x] Prove `right_factor_divides_product`, the accumulated-product and
      decoded-congruence successor lemmas, their combined invariant step, and
      `bounded_beta_crt_prefix_invariant` by ordinary induction. Expose
      `bounded_beta_crt_for_existing_code` only as a wrapper for values already
      decoded from a supplied `BetaAt` code; do not describe it as arbitrary
      finite-sequence coding.
- [x] Prove genuine β finite-prefix recoding and one-value extension, exact
      prefix-product trace existence and functionality, finite-product
      decomposition/append/transport, all-prime and sorted elimination, and
      canonical append without adding kernel atoms.
      Equality remains extensional on decoded entries; raw codes are not
      equated. Hygienic readable notation remains an untrusted surface layer.
      Unconditional pairwise β-modulus coprimality is not a target: it is
      false, as `c=1` at indices 1 and 4 gives moduli 3 and 6.
- [x] Add a pinned Lean 4/Mathlib companion proving existence and uniqueness
      up to permutation, with `sorryAx` rejection and an exact standard-axiom
      audit, without treating it as Peano theorem authority.
- [x] Prove prime-factorization existence by formula-specific strengthened
      induction: 43,973 nodes, depth 98.
- [x] Prove uniqueness using Euclid's lemma, sorted last-factor matching,
      cancellation, and extensional decoded-entry equality: 29,789 nodes,
      depth 82.
- [x] Check the exact combined FTA certificate from the empty context:
      73,767 nodes, depth 99, and 2,184 self-contained Cuts, with certificate
      SHA-256
      `fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
      It fits the 500,000-occurrence/100,000-object/depth-256 live/use gate,
      uses only PA1–PA6 and
      induction, and contains no DNE. Runtime integration first completed in
      the historical synchronized 247-theorem checkpoint and remains present
      in the current 384-theorem runtime.

## M20F — Knowledge and release gates

- [x] Add a dedicated Jupyter Book part with formulas, executable commands,
      trust boundary, dependency route, source audit, and extension workflow.
- [x] Add a ten-stage guided route and deterministic interactive theorem atlas
      initially released with 247 exact native statements and now regenerated
      for all 384 checked statements, with authored proof recipes,
      dependency/dependent navigation, metrics, hashes, live-lab actions, and
      source/vault links.
- [x] Add an arithmetic Obsidian MOC, concept notes, and generated per-lemma
      pages linked by exact dependencies and dependents.
- [x] Add a parallel 40-entry defined-notation edition for the exact 557-node QR
      closure. It preserves explicit native replay lines, theorem dependencies,
      and public/candidate status while linking compact formulas to persistent
      `PD` expansion pages.
- [x] Update project memory, journal, plans, root maps, and artifact index.
- [x] Pass the complete Peano suite, warning-as-error book build, executable
      command replay, vault/link checks, research-catalog validator, artifact
      drift checks, and browser deployment-manifest checks.
- [x] Publish a reviewable branch and draft pull request targeting `peano-lab`;
      do not merge or deploy without owner authorization.
- [x] Complete the final full-suite, strict-book, corpus, snapshot, vault, and
      browser-manifest gates for the synchronized FTA snapshot.
- [ ] Run a direct Pyodide UI smoke in an attached in-app browser. No browser
      was attached to this session, so this observational gate is unclaimed
      rather than inferred from another browser backend.

## M20G — Curated conservative authoring edition

- [x] Write the binding curation policy with definition tiers, API matrix,
      paired-edition identity gates, and release artifacts in
      `research/arithmetic-library/curation-policy.md`.
- [x] Extend the separate Lean formalization with the production `Cut` rule,
      version the artifact grammar as `peano-lab-v2`, mirror the repaired
      Python kernel, and pass the local build, mutation, source-identity,
      differential, and axiom gates.
- [x] Seal that kernel identity with pinned Lean 4.31 and an immutable WMI
      receipt. Source commit
      [`ab966fd1`](https://github.com/nasqret/peano-lab-lean/commit/ab966fd1b8207b99eea0c9dc3d719c6e61ef73c2)
      passed job
      [`218358`](https://github.com/nasqret/peano-lab-lean/tree/8515336ab3b89ca6f0c8ab521d01745a220b5211/artifacts/wmi/218358);
      historical job `211445` covers only cut-free v1.
- [ ] Freeze the eleven P0 authoring definitions: `Le`, `Lt`, `Dvd`, `Prime`,
      `Coprime`, `IsGCD`, `DivRem`, `ModEq`, `BetaAt`, `Product`, and `Sum`.
- [ ] Replace duplicate private text builders with canonical AST-first owners,
      prioritizing `Lt`, `Dvd`, `Prime`, `Coprime`, `IsGCD`, `DivRem`,
      `ModEq`, and `BetaAt`, without changing expanded theorem ASTs.
- [ ] Publish the relation API-completeness matrix: introduction, elimination,
      boundary, characterization/functionality, transport, decision/search,
      and composition.
- [ ] Compile defined theorem statements and typed `have`/`suffices`
      propositions immediately to ordinary `TheoremSpec` formulas; require
      exact expanded-AST, dependency, status, command, and certificate receipts
      against the explicit edition.
- [ ] Complete the parity API, round-tripping prime surface with capture tests,
      and generated fixed-residue clients already open in M20C/M20D.
- [ ] Consolidate P1 definitions next; keep the eight campaign-specific P2
      definitions namespaced. Review `BalancedBezout`, `PermutationPrefix`,
      and `CanonicalPF` before assigning new stable PD identifiers.
- [ ] Release paired readable/expanded training rows, Proof Explorer pages,
      proof-only and mixed graphs, Jupyter Book text, Obsidian notes, expansion
      hashes, duplicate reports, and kernel-verifier identity receipts.

## Current acceptance record

- The definition-aware Proof Explorer is a completed conservative presentation
  of the exact 557-specification QR closure, not a larger trusted language. It
  compacts 506 statements and 1,275/1,839 local propositions using a 40-entry
  registry; 38 definitions occur in the closure. Aggregate statement/local
  text falls by 95.63%/94.34%. Expansion receipts reconstruct the same parsed
  native formulas. The proof
  DAG remains 557 nodes, 1,791 edges, and 45 layers; its status split remains
  240 public, 316 body-checked candidates, and the QR root pending layered
  closure.
- The factorization and unbounded-primes tranches are synchronized into the
  current 384-theorem runtime, 385-entry catalog, generated snapshot, and all
  384 generated lemma notes. The catalog split is 23 baseline checked, 361
  post-baseline checked, and one representation-blocked conventional
  integer-coefficient Bézout interface. The
  previously published 189-theorem snapshot remains historical provenance.
- At this integration checkpoint, the exact expanded catalog statements for
  `prime_factorization_existence`, `prime_factorization_uniqueness`, and
  `fundamental_theorem_of_arithmetic` all have deterministic, closed,
  empty-context kernel checks. Their final metrics are respectively
  43,973/depth 98, 29,789/depth 82, and 73,767/depth 99; the combined theorem
  contains 2,184 Cuts.
- The exact FTA certificate SHA-256 is
  `fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
  The full prove/use/exact/QED path passes under the
  500,000-occurrence/100,000-object/depth-256 cap. Dependency, hypothesis, and
  PA-rule mutation audits are live. The proof
  uses only PA1–PA6 and induction and contains no DNE.
- Trusted-kernel change: one self-contained Cut constructor and checker rule.
  The checker is 247 lines (formerly 234). The object language and logical
  strength are unchanged; the untrusted erasure utility is diagnostic and is
  not a complete or authoritative admission route.
- Full FTA companion status: checked in Lean for every nonzero natural, with
  finite-list existence and permutation uniqueness and no `sorryAx`.
- Native Peano FTA status: checked and synchronized in the 384-theorem runtime
  in the conservative β-coded representation. The endpoint is not a conventional list theorem: there is no
  primitive list type, and uniqueness compares lengths and decoded entries
  rather than raw β codes. The conventional list statement remains the
  separate Lean companion.
- `prime_unbounded` is checked constructively at 4,595 nodes/depth 82 with
  146 Cuts and certificate SHA-256
  `8a44fb2d207c2a41684de6d6630674f3f3b951cd036f733b3dd493321099d37b`.
  It takes a prime divisor of the successor of a bounded nonzero common
  multiple; any such divisor at or below the bound would divide both
  consecutive numbers and hence one. It uses PA1–PA6 only, has no DNE, and
  passes dependency, PA, hypothesis, and live-use audits.
- The generated 384-theorem snapshot has 1,806,923 structural occurrences,
  52,626 Cuts, and 329 Cut-bearing certificates. Its ordered root is
  `73b31b4775d24b6bb9730f2f2df37409aa56dc771fe3e1d0f9de5134b166e89b`.
  The vault has 475 notes and 4,825 resolved links, including all 384 generated
  theorem notes. The last source-bound 1,692-session/13,344-transition corpus
  remains intentionally tied to the historical 247-theorem checkpoint and has
  fingerprint
  `6fc52e25f17dc2ff0c0e7a141c350430d6aa1d0a7a87b82e22840f442f666939`;
  its smoke has 494 sessions, 9,235 raw/9,232 unique transitions, and all 247
  QEDs. The integrated local browser candidate deterministically verifies as
  build `2026-08-02a`, application `a-cd3e54b68949`, with 149 worker sources;
  it assembles successfully in the local content-addressed stage and has not
  been deployed.
- The current Book source set has 45 sources. Its last strict arithmetic-branch
  rebuild completed without warnings; 194 deep links and 47 executable blocks
  containing 287 commands verify. The generated atlas contains 384 checked
  proof cards, one explicit boundary card, all 1,038 dependency edges, and a
  local 1–4-hop navigator. The post-merge compatibility matrix passed 1,183
  tests with five intentional skips, and the strict 45-source Book replay plus
  its 2,323-page integrity gate passed with zero broken or escaping targets.
  Direct Pyodide UI smoke and a complete passing 136-gate QR WMI receipt are
  still explicitly unclaimed.
- Remaining mathematical/library limits are explicit: generic powers, finite
  maps, and primitive lists remain absent; a
  conventional integer-coefficient Bézout statement is not representable in
  the natural-only term language, while the four-natural balanced Bézout
  theorem is checked.
- Pre-integration validation record: all 1,098 Peano tests passed on CPython 3.10 in 181.34
  seconds, including the bounded-prefix invariant admission gate. Lambda's
  preceding independent result remains 360 tests plus 36 subtests. Those exact
  snapshot, catalog, corpus, and application audits belong to the published
  189-theorem checkpoint. The corpus retains
  13,344 transitions/1,692 sessions under run fingerprint
  `a3c2f8c5c762b10fc9c1117723c74fecb50348cfb699f73bc76fb3714df3bf1b`;
  the isolated smoke has 378 sessions, 5,373 raw and 5,370 unique transitions,
  and all 189 authored QEDs. Local browser build `2026-07-29h` has content
  identity `a-98b1d8bb8dd7`; it is not
  staged, deployed, or promoted.
- The pre-integration generated Obsidian graph has 268 notes and 2,513 resolved links,
  including all 189 checked lemma notes.
- The preceding checkpoint's independent Lambda result (360 tests plus 36
  subtests) and strict 36-source book/213-link/264-command record are retained
  as prior evidence, not relabeled as a current 189-theorem documentary gate.
