# Foundations & canonical references + four-prover comparison

> The authoritative, edition-precise reading list for the Church-to-Curry-Howard-to-dependent-type-theory backbone of the course, paired with a rigorous side-by-side of the four proof assistants the course artifacts use (Lean 4, Agda, Rocq, Mizar) — logical foundation, proof style, library, and current release each verified against a primary source as of July 2026.

## Learning objectives

- Trace the historical chain from Church's lambda-calculus and Church's thesis (1936), through the simple theory of types (1940) and the Curry-Howard 'formulae-as-types' correspondence (Howard 1969/1980), to Martin-Lof type theory (1984) and Homotopy Type Theory (2013).
- Distinguish the three type-theoretic foundations used in the course (CIC for Lean 4 and Rocq; MLTT for Agda) from the one set-theoretic foundation (Tarski-Grothendieck set theory for Mizar), and articulate what each choice buys (proof-relevance, universes, classicality) and costs.
- Read and situate a proof in each of the two dominant proof-authoring paradigms: the term/tactic paradigm of Lean, Agda and Rocq (proof = lambda-term checked by a small kernel via the de Bruijn criterion) versus the declarative natural-deduction vernacular of Mizar.
- Match each formalization library to the prover and foundation it rests on: Mathlib (Lean), agda-stdlib (Agda), the Rocq standard library + Mathematical Components (Rocq), and the Mizar Mathematical Library (Mizar).
- Locate every canonical text with an exact edition/year and a free URL where one exists, and know each prover's current stable release and the library version pinned by the author's own EML artifact (Lean 4.28.0 / Mathlib v4.28).
- Explain why AlphaProof (Lean) and the classical machine-checked landmarks (Four Colour Theorem, Odd Order Theorem, Jordan Curve Theorem) sit where they do across these four systems.

## Prerequisites

- Mathematical maturity: fluency with proof by induction, first-order logic, and naive ZFC set theory.
- Working knowledge of the untyped and simply-typed lambda-calculus (alpha/beta/eta, Church encodings, Y combinator) at the level of the course's own lambda_lab / book chapters 2-7.
- The Curry-Howard slogan 'propositions as types, proofs as programs' as introduced in book chapter 8.
- Basic functional programming: functions as first-class values, recursion, algebraic data types and pattern matching.
- No prior exposure to any proof assistant is assumed; the dossier is the on-ramp to book chapters 9-9c (Lean, NNG, Macbeth).

## Lean 4 — Calculus of Inductive Constructions; term + tactic; Mathlib; v4.32.0 (course artifacts pinned to 4.28.0)

FOUNDATION: the Calculus of Inductive Constructions (CIC) — a dependent type theory with a non-cumulative universe hierarchy Sort u, where Prop = Sort 0 is impredicative and definitionally proof-irrelevant, and Type u = Sort (u+1) is predicative and proof-relevant. Lean adds quotient types primitively; classical mathematics in Mathlib rests on exactly three axioms (propositional extensionality, quotient soundness Quot.sound, and Classical.choice, from which excluded middle follows via Diaconescu). PROOF STYLE: dual and interchangeable — term mode writes the raw lambda-term (e.g. `fun ⟨hp,hq⟩ => ⟨hq,hp⟩ : P ∧ Q → Q ∧ P`), tactic mode runs a `by` script that the elaborator compiles down to the same term; Lean's metaprogramming (tactics, macros, elaboration) is written in Lean itself. Trust rests on a small type-checking kernel (the de Bruijn criterion): the ~99% of Lean outside the kernel may be buggy yet proofs stay sound. LIBRARY: Mathlib, a single monolithic ~1.2M-line classical library (50k+ definitions, 50k+ lemmas), built with Lake, cached as .olean. Notable for powering DeepMind's AlphaProof (IMO 2024 silver-medal level). VERSION: latest stable Lean 4.32.0 (2026-07-13), with 4.33.0-rc1 (2026-07-15) in the pipeline; the author's EML formalization is pinned to Lean 4.28.0 / Mathlib v4.28 — a reminder that toolchain pinning, not the head release, defines a reproducible artifact.

**Key definitions**

- Calculus of Inductive Constructions (CIC)
- Sort/Prop/Type universe hierarchy; impredicative proof-irrelevant Prop
- term mode vs tactic mode; the `by` block; elaboration
- de Bruijn criterion / trusted kernel
- the three Mathlib axioms: propext, Quot.sound, Classical.choice
- Lake build system; .olean; `#print axioms`

**Key results**

- Mathlib: ~1.2M lines, 50k+ definitions, 50k+ lemmas (2026)
- AlphaProof (DeepMind, 2024) produces Lean proofs at IMO silver level
- author's own EML formalization: 8062 kernel jobs, sorry-free, 100 public theorems, on Lean 4.28.0

## Agda — Martin-Lof (intensional) dependent type theory; proofs-as-programs (no tactic language); agda-stdlib; v2.8.0

FOUNDATION: intensional Martin-Lof Type Theory (MLTT) — a predicative dependent type theory with a cumulative universe hierarchy Set0 : Set1 : … and universe polymorphism (Level). Equality is the intensional identity type; by default there is no proof irrelevance and no built-in Prop sort (an irrelevant/Prop mechanism exists but is secondary). Constructive by default: no excluded middle or choice unless postulated. The Cubical Agda extension (`--cubical`) realises Voevodsky's univalence axiom computationally, making Agda the natural home for Homotopy Type Theory as a programming language. PROOF STYLE: there is essentially no tactic language — a proof IS a total dependently-typed function written directly, using dependent pattern matching, with-abstraction, and copattern matching; totality is enforced by a termination checker and a strict positivity checker. This makes Agda 'the one that looks most like writing mathematics as programs' and the cleanest illustration of Curry-Howard: the proof term is the whole artifact, checked by type-checking alone. LIBRARY: agda-stdlib, comparatively small and foundational (order, algebra, data structures, relations) rather than research-grade analysis; the separate cubical library covers HoTT. VERSION: Agda 2.8.0 (stable, 2025-07-05); agda-stdlib in the 2.x series (v2.3). Agda 2.8.0 ships as a self-contained single binary.

**Key definitions**

- intensional Martin-Lof Type Theory (MLTT); predicativity
- universe polymorphism (Set/Level); cumulative hierarchy
- dependent pattern matching; with-abstraction; copatterns
- termination checker; strict positivity checker
- propositional (identity) type; `--safe`; `--without-K`
- Cubical Agda; computational univalence

**Key results**

- Agda 2.8.0 is a single self-contained binary (2025-07-05)
- Cubical Agda gives a computational model of HoTT/univalence
- used widely in programming-language and type-theory research (e.g. the 'programming language foundations in Agda' PLFA tradition)

## Rocq (formerly Coq) — Calculus of Inductive Constructions; tactic (Ltac/Ltac2) + SSReflect; stdlib + Mathematical Components; v9.2.0

FOUNDATION: the original CIC prover — Coquand-Huet's Calculus of Constructions (1988) extended with inductive types. Foundation is the predicative Calculus of (Co)Inductive Constructions (pCuIC): an impredicative sort Prop, a predicative Type hierarchy with universe polymorphism, plus (since 8.10) a definitionally proof-irrelevant strict sort SProp. Constructive core; classical axioms are routinely imported when needed. Renamed Coq -> Rocq in 2025 (the '.v' file extension and the lineage are unchanged); 'Rocq (formerly Coq)' is one system, not two. PROOF STYLE: predominantly tactic-based over the Gallina term language, scripted in Ltac / the redesigned Ltac2; the SSReflect (small-scale reflection) proof language underpins Mathematical Components. Verified programs can be extracted to OCaml/Haskell/Scheme. LIBRARY: the Rocq standard library (now packaged/split out from the core) plus two flagship external libraries — Mathematical Components (MathComp, rebuilt on the Hierarchy Builder) and MathComp-Analysis. VERSION: latest stable Rocq 9.2.0 (2026-03-27); Rocq 9.3 branched 2026-07-08 but was not yet released as of late July 2026; MathComp 2.5.0 (2025-10-13, compatible with Rocq 9.0/9.1). Landmark for the most celebrated machine-checked theorems.

**Key definitions**

- Calculus of Inductive Constructions; impredicative Prop; SProp
- Gallina (term language) vs Ltac / Ltac2 (tactics)
- SSReflect / small-scale reflection; Hierarchy Builder
- program extraction to OCaml/Haskell
- Prop vs Set (informative vs logical content); Coq→Rocq rename (2025)

**Key results**

- Four Colour Theorem, fully machine-checked (Gonthier, 2005)
- Feit-Thompson Odd Order Theorem (Gonthier et al., 2012) — the MathComp/SSReflect showcase
- CompCert verified optimising C compiler (Leroy et al.)

## Mizar — Tarski-Grothendieck set theory; declarative natural-deduction vernacular; Mizar Mathematical Library; v8.1.15

FOUNDATION: the set-theoretic outlier and the oldest system still maintained (Andrzej Trybulec, from 1973). Logic is classical first-order; the axioms are Tarski-Grothendieck set theory = ZFC plus Tarski's Axiom A, which yields arbitrarily large (inaccessible) universes, so Grothendieck universes are available for category-theoretic constructions. It is NOT a type theory: Mizar 'types' are a soft layer of unary predicates ('adjectives'/'modes') over the single set-theoretic domain, not a Curry-Howard type discipline — there are no proof terms. PROOF STYLE: purely declarative. A Mizar proof is written in a fixed, English-like block-structured vernacular that mirrors the natural-deduction prose of an ordinary paper — `assume`, `let`, `take`, `thus`/`hence`, `per cases`, `now … end` — and is accepted by the Mizar verifier, whose 'obviousness' checker (Analyzer/Checker) decides each atomic inference. This is the deliberate opposite of the tactic/term paradigm and the best pedagogical contrast to Lean. LIBRARY: the Mizar Mathematical Library (MML), the largest corpus of formalized mathematics built on a single fixed axiomatic base, curated and continuously published in the journal Formalized Mathematics. VERSION: Mizar 8.1.15 with MML 5.94.1493 — 1493 articles, 65k+ theorems, 13k+ definitions (as of 2025-05-30); recent additions include the surreal numbers.

**Key definitions**

- Tarski-Grothendieck set theory; Tarski's Axiom A; Grothendieck universes
- declarative proof / natural-deduction vernacular (assume/thus/hence/take/per cases)
- soft type system: modes and adjectives as predicates (no proof terms)
- the Checker/Analyzer 'obviousness' inference engine
- the journal Formalized Mathematics as the MML publication channel

**Key results**

- MML: 1493 articles, 65k+ theorems, 13k+ definitions (Mizar 8.1.15 / MML 5.94.1493, 2025-05-30)
- Jordan Curve Theorem formalized in Mizar (Korniłowicz and collaborators)
- one of the four 'big' systems tracked in Freek Wiedijk's '100 theorems' comparison

## Pedagogical arc
"The dossier is designed to be delivered right after the Curry-Howard chapter and before the hands-on Lean chapters, converting the slogan 'proofs are programs' into a concrete map of the tool landscape. Arc in four beats. (1) HISTORICAL SPINE: read the reading list as a genealogy — Church 1936/1940 (what is computation; what is a type) -> Howard 1969/1980 (types ARE propositions) -> Martin-Löf 1984 (dependent types make it a foundation for all of mathematics) -> HoTT 2013 (the modern refinement) -> the pedagogy layer (Pierce, Sørensen-Urzyczyn, Nederpelt-Geuvers, Avigad) that makes it teachable. (2) THE FORK: use the four-prover table to show that a single idea (Curry-Howard) branches into concrete design choices — CIC vs MLTT, impredicative/proof-irrelevant Prop vs predicative Set, tactic/term vs declarative, constructive vs classical — and that one system (Mizar) deliberately takes the other road entirely (set theory, no proof terms), which sharpens by contrast what the type-theoretic three have in common. (3) ONE THEOREM, FOUR VOICES: have students see the SAME elementary statement (the course already uses `P ∧ Q → Q ∧ P` in chapters 8-9) rendered in each system, feeling the difference between `fun ⟨hp,hq⟩ => ⟨hq,hp⟩` (Lean term), an Agda pattern-matching function, an Ltac/SSReflect script, and a Mizar `assume … thus … hence` block. (4) GROUNDING IN A REAL ARTIFACT: close by pointing at the author's own EML formalization (Lean 4.28.0 / Mathlib v4.28, sorry-free, 8062 kernel jobs) as proof that this is not a toy — the same kernel that checks `P ∧ Q → Q ∧ P` checks 100 research theorems. Throughout, every volatile claim (version numbers, who-proved-what) is cited so students learn the habit of pinning facts to primary sources, and so the material survives the fast release cadence of these tools."

## Connections to existing material
"Slots directly into the falenty-2026 JupyterBook between chapter 08 (`08_curry_howard.md`, which already gives the logic/types table and the `λp.p : P → P` and `fun (p,q) => (q,p)` examples) and chapters 09/09b/09c (`09_lean_first_steps.md` already contrasts term vs tactic mode with `and_comm_term`/`and_comm_tac`, invokes the de Bruijn criterion, and drives `python -m lambda_lab lean and_comm`; `09b` is the Natural Number Game; `09c` is Macbeth's Mechanics of Proof). The reading list is a strict superset of the existing chapter 12 'Further reading' (Pierce, Girard-Lafont-Taylor, Barendregt, HoTT Book, Lean/Coq-Rocq/Agda/Idris) with editions, years and free URLs added and Church/Howard/Martin-Löf/Sørensen-Urzyczyn/Nederpelt-Geuvers/Avigad/Riehl inserted. The four-prover comparison generalizes the book's current single-prover focus (Lean) to the full artifact set. The Lean column is grounded in the author's live eml-formalization repo (Lean 4.28.0 / Mathlib v4.28, sorry-free, 8062 kernel jobs, 100 public theorems) and in lambda_lab's `curry_howard/` command (builder.py, tactics.py, lean_bridge.py, lean_verify.py) and `lean_server.py`, so the same codebase that renders the book can demo every claim. The 'one theorem, four voices' idea reuses the `P ∧ Q → Q ∧ P` example already canonical in chapters 8-9 and the DeMorgan/CircleCount Aristotle Lean artifacts under lambda_lab/proofs/. Style and depth mirror the classical-foundations-ann book (historical-context + rigorous-definitions + runnable-artifact structure)."

## Artifact ideas

- **Lean 4** (beginner): Prove `theorem and_comm {P Q : Prop} : P ∧ Q → Q ∧ P` twice — once in term mode (`fun ⟨hp,hq⟩ => ⟨hq,hp⟩`) and once with a `by` tactic block — then `#print and_comm` to show both elaborate to the SAME lambda-term, and `#print axioms and_comm` to show it uses none. Extends the existing chapter-9 example into an explicit 'term = compiled tactics' demonstration.
- **Agda** (beginner): Define the identical proposition as a dependent function `and-comm : {P Q : Set} → P × Q → Q × P` by pattern matching (`and-comm (p , q) = (q , p)`), under `--safe`, to show there is no `by`/tactic layer at all — the proof term is the whole program — and contrast the predicative `Set` universe with Lean's `Prop`.
- **Rocq (formerly Coq)** (intermediate): Prove `Lemma and_comm (P Q : Prop) : P /\ Q -> Q /\ P` first in vanilla Ltac (`intros H; destruct H; split; assumption`), then in the SSReflect style (`move=> [hp hq]; split`), and finally `Extraction and_comm` to inspect the erased OCaml term — highlighting Rocq's tactic-first culture and program extraction.
- **Mizar** (intermediate): Write the same commutativity of conjunction as a short declarative Mizar proof block (`assume A & B; hence B & A;`), run the Mizar verifier on it, and annotate how the natural-deduction vernacular and the Tarski-Grothendieck set-theoretic foundation dispense with proof terms entirely — the sharpest contrast to the three type-theoretic systems.
- **Multi-prover (Lean 4 / Agda / Rocq / Mizar)** (advanced): Build a 'one theorem, four voices' comparison page: take a single elementary statement (P ∧ Q → Q ∧ P, or the infinitude of primes) and present the full proof side by side in all four systems with a foundation/proof-style/library/version caption per column, driven from lambda_lab so each snippet is actually machine-checkable, not just quoted.

## Pitfalls / misconceptions

- Conflating 'Prop' across systems: it is impredicative and definitionally proof-irrelevant in Rocq and Lean, predicative/absent-by-default (proof-relevant) in Agda, and simply does not exist as a separate notion in Mizar (which has no Curry-Howard type discipline at all).
- Assuming all four are constructive. Mizar is classical (Tarski-Grothendieck); Lean's Mathlib is classical (Classical.choice, hence excluded middle); Rocq is constructive at its core but routinely imports classical axioms; only Agda is constructive by default.
- Treating 'Coq' and 'Rocq' as two different systems. It is a 2025 rename of one continuous system (same .v files, same CIC lineage); write 'Rocq (formerly Coq)'.
- Reading Curry-Howard as a mere analogy. In Lean/Agda/Rocq it is literally the implementation: a proof is a lambda-term and proof-checking IS type-checking (the de Bruijn criterion). Mizar breaks the isomorphism — declarative, set-theoretic, no proof terms — which is exactly why it is the instructive contrast.
- Citing editions loosely. Barendregt is specifically the 1984 revised edition (Studies in Logic 103); Martin-Löf's book is Sambin's 1984 notes of the 1980 Padua lectures; Howard's paper was written in 1969 but only published in 1980.
- Version drift and reproducibility. The July-2026 head releases (Lean 4.32.0, Rocq 9.2.0, Agda 2.8.0) are NOT what a reproducible artifact pins to — the author's EML sits on Lean 4.28.0 / Mathlib v4.28. Always report both the current release and the pinned toolchain.
- Assuming Rocq 9.3 is out: as of late July 2026 it had only branched (2026-07-08), not released — 9.2.0 is the current stable.

## Canonical references

- A. Church, "An Unsolvable Problem of Elementary Number Theory," American Journal of Mathematics 58(2), 345-363 (1936). doi:10.2307/2371045. — <https://www.jstor.org/stable/2371045>  
  _The founding paper of the lambda-calculus as a model of effective calculability and the origin of Church's thesis; the historical root of everything downstream in the course._
- A. Church, "A Formulation of the Simple Theory of Types," Journal of Symbolic Logic 5(2), 56-68 (1940). doi:10.2307/2266170. — <https://www.jstor.org/stable/2266170>  
  _Introduces the simply-typed lambda-calculus / higher-order logic — the direct ancestor of the HOL family and the type discipline that Curry-Howard later reinterprets as logic._
- W. A. Howard, "The formulae-as-types notion of construction" (manuscript 1969), in J. P. Seldin & J. R. Hindley (eds.), To H. B. Curry: Essays on Combinatory Logic, Lambda Calculus and Formalism, Academic Press, 1980, pp. 479-490. — <https://www.cs.cmu.edu/~crary/819-f09/Howard80.pdf>  
  _The canonical statement of the Curry-Howard isomorphism (propositions-as-types, proofs-as-programs) — the conceptual spine linking book chapter 8 to every type-theoretic prover in the comparison. Note the 1969/1980 write/publish split._
- H. P. Barendregt, The Lambda Calculus: Its Syntax and Semantics, revised edition, Studies in Logic and the Foundations of Mathematics vol. 103, North-Holland/Elsevier, 1984. ISBN 0-444-87508-5. — <https://www.elsevier.com/books/the-lambda-calculus/barendregt/978-0-444-87508-2>  
  _The standard reference monograph ('the bible') for the untyped lambda-calculus; the technical backing for the reduction theory demonstrated in lambda_lab. Cite the 1984 revised edition specifically._
- J.-Y. Girard, Y. Lafont, P. Taylor, Proofs and Types, Cambridge Tracts in Theoretical Computer Science 7, Cambridge University Press, 1989. ISBN 0-521-37181-3. — <https://www.paultaylor.eu/stable/prot.pdf>  
  _The canonical, legally-free introduction to Curry-Howard, System F and normalization; already the anchor citation in book chapter 12. Free PDF hosted by Paul Taylor._
- M. H. Sørensen, P. Urzyczyn, Lectures on the Curry-Howard Isomorphism, Studies in Logic and the Foundations of Mathematics vol. 149, Elsevier, 2006. ISBN 978-0-444-52077-7. (Earlier free DIKU lecture-notes version, 1998.) — <https://disi.unitn.it/~bernardi/RSISE11/Papers/curry-howard.pdf>  
  _The most thorough textbook-length development of Curry-Howard from propositional to higher-order and dependent logic; bridges the slogan of chapter 8 to the real type systems of the four provers. Free 1998 lecture-notes preprint widely mirrored._
- P. Martin-Löf, Intuitionistic Type Theory, notes by Giovanni Sambin of lectures given in Padua, June 1980, Studies in Proof Theory, Bibliopolis, Naples, 1984. — <https://archive-pml.github.io/martin-lof/pdfs/Bibliopolis-Book-retypeset-1984.pdf>  
  _The primary source for Martin-Löf Type Theory — the exact foundation of Agda and the intellectual ancestor of CIC (Lean/Rocq) and of HoTT. Cite as Sambin's 1984 notes of the 1980 Padua lectures._
- The Univalent Foundations Program, Homotopy Type Theory: Univalent Foundations of Mathematics, first edition, Institute for Advanced Study, Princeton, 2013. — <https://homotopytypetheory.org/book/>  
  _The modern successor programme to plain type theory (univalence, higher inductive types); realised computationally in Cubical Agda. Free and canonical; already cited in book chapter 12._
- B. C. Pierce, Types and Programming Languages, MIT Press, 2002. ISBN 0-262-16209-1. — <https://www.cis.upenn.edu/~bcpierce/tapl/>  
  _The standard systematic introduction to typed lambda-calculi (STLC, subtyping, System F, dependent types); the bridge from the course's untyped material to the typed foundations of the provers. Already the lead 'Books' citation in chapter 12._
- R. Nederpelt, H. Geuvers, Type Theory and Formal Proof: An Introduction, Cambridge University Press, 2014. ISBN 978-1-107-03650-5. doi:10.1017/CBO9781139567725. — <https://doi.org/10.1017/CBO9781139567725>  
  _The most classroom-ready bridge from lambda-cube type theory to actual formal proof (Automath lineage), pitched exactly at mathematically-mature newcomers to formal methods — the target audience of this VIASM course._
- J. Avigad, Mathematical Logic and Computation, Cambridge University Press, 2022. ISBN 978-1-108-47875-4. doi:10.1017/9781108778756. — <https://www.cambridge.org/core/books/mathematical-logic-and-computation/>  
  _A modern logic textbook by a leading Mathlib author that treats computation, type theory and formalization on an equal footing with classical model/proof theory — the ideal rigorous backbone tying the course's logic and its Lean practice together._
- E. Riehl, "A Reintroduction to Proofs" — first-year seminar (Johns Hopkins, Fall 2025) and the accompanying 'Reintroduction to Proofs' Lean game on the Lean Game Server; expository lecture notes/slides. — <https://emilyriehl.github.io/files/reintroduction-to-proofs-hardy.pdf>  
  _A working model for teaching an intro-to-proofs course in the vernacular of dependent type theory rather than set theory — directly relevant pedagogy for a mathematically-mature audience meeting Lean. See also the formalization hub at emilyriehl.github.io/formalization/._
- H. Macbeth, The Mechanics of Proof (online textbook, Lean 4 + Mathlib), developed for Math 2001 at Fordham University, 2023-. — <https://hrmacbeth.github.io/math2001/>  
  _A complete, free, dual-column (prose + Lean) proofs course; the course's own book chapter 9c is built on it, so it is the primary continuity reference for the Lean-teaching arc._
- Natural Number Game (NNG4) — K. Buzzard, J. Macdonald et al., on the Lean Game Server (Duper/adam.math.hhu.de). — <https://adam.math.hhu.de/>  
  _The single most effective first-contact Lean experience (Peano arithmetic built tactic-by-tactic); cited in chapter 12 and the basis of book chapter 9b. The same server now also hosts Riehl's proofs game._
- Lean/Mathlib documentation: Theorem Proving in Lean 4 (leanprover.github.io/theorem_proving_in_lean4), Mathematics in Lean (leanprover-community.github.io/mathematics_in_lean), Mathlib4 API docs, and the Lean Language Reference. — <https://leanprover-community.github.io/mathematics_in_lean/>  
  _The living, version-tracked primary documentation for the prover the course leans on hardest; 'Theorem Proving in Lean 4' is the term/tactic reference and 'Mathematics in Lean' the Mathlib-first tutorial, both already linked in chapter 12._

## Volatile facts (sent to fact-check)

- Latest stable Lean is 4.32.0 (released 2026-07-13), with 4.33.0-rc1 released 2026-07-15; Mathlib is ~1.2M lines of code with 50k+ definitions and 50k+ lemmas as of 2026. The author's EML artifact is pinned to Lean 4.28.0 / Mathlib v4.28. (src: https://github.com/leanprover/lean4/releases)
- Latest stable Rocq (formerly Coq) is 9.2.0 (released 2026-03-27); Rocq 9.3 had only branched (2026-07-08) and was not yet released as of late July 2026. Mathematical Components (MathComp) latest is 2.5.0 (2025-10-13, compatible with Rocq 9.0/9.1). (src: https://rocq-prover.org/releases/9.2.0)
- Latest stable Agda is 2.8.0 (released 2025-07-05), shipped as a self-contained single binary; agda-stdlib is in the 2.x series (v2.3). (src: https://github.com/agda/agda/releases)
- Current Mizar is 8.1.15 with Mizar Mathematical Library MML 5.94.1493 — 1493 articles, 65k+ theorems, 13k+ definitions, as of 2025-05-30. (src: https://mizar.uwb.edu.pl/library/)
- The Curry-Howard correspondence is realised literally in Lean, Agda and Rocq (proof = lambda-term, checking = type-checking / de Bruijn criterion) but not in Mizar, which is declarative and founded on Tarski-Grothendieck set theory (ZFC + Tarski's Axiom A) with no proof terms. (src: https://www.cs.cmu.edu/~crary/819-f09/Howard80.pdf)
