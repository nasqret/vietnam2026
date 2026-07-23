# Lecture 1 — A General Introduction to Type Theory

> A gentle-but-rigorous on-ramp that grows the untyped lambda calculus of the falenty-2026 book into simply-typed lambda calculus, reveals the Curry-Howard correspondence, previews dependent types and Martin-Löf type theory, and explains why type theory (not ZFC) is the native language of Lean, Agda and Rocq — while Mizar keeps set theory — setting up all six lectures of the VIASM mini-course.

## Learning objectives

- State the three typing rules of the simply-typed lambda calculus (Var, Abs, App) as inference rules over a judgment Gamma ⊢ t : sigma, and use them to derive the type of a small term by hand.
- Distinguish Church-style (intrinsic, type-annotated, unique-typing) from Curry-style (extrinsic type-assignment, many types, principal type) typing, and explain how type erasure relates the two.
- Explain the types-as-sets intuition (→ as function space, × as product, + as disjoint union) and pinpoint at least two places where it breaks: proof-relevance/intensionality and the inconsistency of a type-of-all-types (Girard's paradox).
- State the Curry-Howard correspondence as a dictionary (propositions↔types, proofs↔terms, →↔function, ∧↔×, ∨↔+, ∀↔Π, ∃↔Σ, β-reduction↔proof normalization) and show why an inhabited type = a provable proposition, using Peirce's law as the intuitionistic/classical boundary.
- Describe, in one breath, the extra ingredients Martin-Löf type theory adds over STLC — dependent Π/Σ-types, the identity type, inductive types with their elimination = induction principles, and a universe hierarchy — and why the hierarchy is forced by consistency.
- Justify why modern proof assistants build on type theory rather than ZFC (de Bruijn criterion + a small kernel, decidable type-checking, built-in computation via definitional equality, proofs-as-programs), and correctly place the course's four systems: Lean = CIC, Rocq = CIC, Agda = MLTT, Mizar = Tarski–Grothendieck set theory.

## Prerequisites

- Comfort with the untyped lambda calculus at the level of book chapters 2–6: the grammar t ::= x | λx.t | t t, α-conversion, free vs bound variables, and β-reduction (the falenty-2026 audience already has this).
- Familiarity with Church encodings and the Y combinator (book ch.4–6), so the 'these are untypable in STLC' payoff lands.
- Basic inference-rule / natural-deduction notation (premises over a line), and elementary propositional logic (implication, conjunction, disjunction, the intuitionistic-vs-classical distinction, Peirce's law).
- Naive set theory and functions (Cartesian product, disjoint union, function space) to seed the types-as-sets intuition, plus awareness that Russell-style 'set of all sets' is paradoxical.
- Mathematical maturity: reading theorem statements and following a short structural-induction argument; no prior exposure to any proof assistant is required.

## From untyped to simply-typed lambda calculus: judgments and typing rules

Start exactly where the book's chapter 2 (02_lambda_basics.md) stops: the grammar t ::= x | λx.t | t t and free/bound variables are already known; STLC adds a type discipline on top. Introduce types τ ::= ι | τ→τ (base types plus arrows), typing contexts Γ = x₁:σ₁,…,xₙ:σₙ, and the judgment form Γ ⊢ t : σ read 'in context Γ, term t has type σ'. Present the three rules as a natural-deduction-style inference system and derive Γ ⊢ λf.λx. f(f x) : (ι→ι)→ι→ι at the board. Emphasise that a typing derivation is a *tree*, foreshadowing that proofs will be trees too. Tie normalization back to book chapters 3, 5, 6: the Y combinator and Ω = (λx.xx)(λx.xx) that made recursion possible in the untyped world are *untypable* here — that is the price of type safety.

**Key definitions**

- Type: τ ::= ι (base/atomic type) | τ → τ (function type); → associates to the right
- Context Γ: a finite list of distinct-variable bindings x:σ
- Typing judgment Γ ⊢ t : σ
- β-redex and β-reduction (λx.t) u →β t[x:=u], reused from book ch.3
- Strongly normalizing term: no infinite β-reduction sequence

**Key results**

- Typing rules — (Var) if (x:σ) ∈ Γ then Γ ⊢ x : σ; (Abs) if Γ, x:σ ⊢ t : τ then Γ ⊢ λx:σ.t : σ→τ; (App) if Γ ⊢ t : σ→τ and Γ ⊢ u : σ then Γ ⊢ t u : τ
- Uniqueness of types (Church presentation): if Γ ⊢ t : σ and Γ ⊢ t : τ then σ = τ
- Subject reduction / type preservation: if Γ ⊢ t : σ and t →β t' then Γ ⊢ t' : σ
- Strong normalization (Tait 1967, reducibility method): every well-typed STLC term is strongly normalizing; consequently the Y combinator and Ω are not typable and STLC is not Turing-complete
- Decidability: type-checking and type-inference for STLC are decidable

## Church-style vs Curry-style typing

Two philosophies of what 'typing' means, both due to Church's 1940 simple theory of types being read in two directions. Church-style (typé à la Church / intrinsic): terms are *born* with type annotations (λx:σ.t), untyped terms are meaningless, and every term has at most one type. Curry-style (à la Curry / extrinsic, 'type assignment'): the terms are the bare untyped λ-terms of book ch.2, and typing is an external relation that may assign *many* types to one term (e.g. λx.x gets α→α for every α). This is exactly the distinction the lambda_lab `ch` command surfaces: `ch term \p. p` reports a Curry-style principal type α→α, while the emitted Lean theorem `fun p => p : P → P` is Church-style. de Bruijn's Automath is the historical Church-style ancestor of every modern assistant.

**Key definitions**

- Church-style (intrinsic) typing: syntax carries type annotations; typing is a property of a term
- Curry-style (extrinsic) typing / type assignment: bare untyped terms; typing is a relation Γ ⊢ t : σ
- Type erasure map |·|: deletes annotations, sending a Church term to its underlying Curry term
- Principal type of a term M: a type σ such that every derivable type of M is a substitution instance of σ
- Type substitution (instantiation of type variables)

**Key results**

- Erasure/decoration correspondence: a Curry-style term M has type σ iff some Church-style term whose erasure is M has type σ
- Principal type theorem (Hindley 1969 / Milner 1978, the basis of Hindley–Milner inference): every Curry-typable term has a principal type computable by unification, of which all its types are substitution instances
- Church-style types are unique (per the previous topic); Curry-style types are not — e.g. the K combinator λx.λy.x is typable at α→β→α for all α,β

## Types-as-sets intuition — and the three places it breaks

The most valuable intuition for a mathematician new to the field, and the most important place to install healthy scepticism. First give the friendly dictionary: read a type as the *set of its closed normal terms*, → as the set of functions, × as Cartesian product, + as disjoint union, Bool as {true,false}, ⊥ as ∅, ⊤ as a singleton. This genuinely works for STLC (Henkin/full type-frame models). Then break it deliberately, three ways, because every break motivates something later in the course. Break 1 (proof-relevance/intensionality): a type's *elements are programs/proofs*, not abstract points — two proofs of the same proposition need not be equal, and definitional equality ('computes to') differs from propositional equality ('provably equal'); this is why Lecture on MLTT needs an identity type. Break 2 (no set of all sets): a naive 'type of all types' Type:Type is inconsistent — Girard's paradox — the type-theoretic echo of Russell's/Burali-Forti's paradox. Break 3 (constructive existence): an inhabitant of Σx.B(x) or of ∃ carries a *witness/algorithm*, unlike a set-theoretic non-empty set proved non-empty classically.

**Key definitions**

- Naive semantics: [[σ→τ]] = functions [[σ]]→[[τ]], [[σ×τ]] = [[σ]]×[[τ]], [[σ+τ]] = disjoint union, [[⊥]] = ∅, [[⊤]] = {∗}
- Definitional (judgmental) equality a ≡ b : both sides reduce to a common normal form
- Propositional equality a = b : an inhabited identity type, a theorem to be proved
- Universe / 'type of types'; System U (Girard's inconsistent λ-calculus with two impredicative universes)
- Proof relevance vs proof irrelevance

**Key results**

- Girard's paradox (1972): System U, and equivalently any theory with the rule Type : Type, is inconsistent — it contains a closed term of the empty type and loses strong normalization (later simplified by Hurkens 1995); it is the type-theoretic form of the Burali-Forti/Russell paradox
- Design consequence: consistent type theories replace Type:Type by a cumulative hierarchy U₀ : U₁ : U₂ : … (used by Agda, Rocq, Lean)
- STLC does have sound set-theoretic (full type frame / Henkin) models, so the intuition is *safe for STLC* but must be abandoned once impredicative universes or proof-relevant equality enter

## The Curry-Howard correspondence at a high level

The conceptual centre of the lecture and the spine of book chapters 8, 10d. Present the historical arc: Curry (1934, then 1958) noticed the types of combinators match Hilbert's implicational axioms; Howard (1969, circulated, published 1980) extended it to full intuitionistic natural deduction and STLC; de Bruijn arrived independently via Automath. State the dictionary as a table and *demonstrate it live* with the lambda_lab `ch` command: `ch type 'P -> P'` returns λp.p and the Lean theorem; `ch type '(P->Q)->(Q->R)->P->R'` returns composition λf g p. g(f p) — transitivity of implication *is* function composition (the B combinator). The punchline for consistency: β-reduction of terms corresponds exactly to normalization (cut/detour elimination) of proofs, and strong normalization = the proof system has no proof of ⊥. Draw the intuitionistic boundary with Peirce's law, which the `ch` engine correctly reports as uninhabited.

**Key definitions**

- Propositions-as-types / proofs-as-programs (Curry-Howard correspondence, sometimes 'isomorphism')
- The dictionary: proposition↔type, proof↔term, implication →↔function type, conjunction ∧↔product ×, disjunction ∨↔sum +, truth ⊤↔unit type, falsity ⊥↔empty type, ∀↔Π, ∃↔Σ
- Inhabited type: a type σ for which some closed t with ⊢ t : σ exists
- Proof normalization / cut elimination as the logical face of β-reduction

**Key results**

- Curry-Howard theorem: Γ ⊢ t : σ is derivable in STLC iff the formula σ (types read as implicational formulas) is derivable from Γ in intuitionistic natural deduction; term formation ↔ proof construction, β-reduction ↔ proof normalization
- Provability = inhabitation: a proposition is intuitionistically provable iff its corresponding type is inhabited
- Peirce's law ((P→Q)→P)→P is a classical tautology but is NOT inhabited in intuitionistic STLC — a constructive proof would require the law of excluded middle (verified live by lambda_lab `ch type '((P -> Q) -> P) -> P'`)
- Curry's original 1934 observation: the principal types of the combinators K and S are exactly Hilbert's axioms P→(Q→P) and (P→(Q→R))→((P→Q)→(P→R))

## Dependent types — a preview

The single generalization that turns 'a logic of implications' into 'a logic of all of mathematics': let types *depend on values*. The motivating example is the vector type Vec A n whose very identity mentions the number n. Two constructors do all the work: the dependent function type Π(x:A).B(x) (a function whose result *type* depends on its input) generalizes both the ordinary arrow A→B (when B is constant) and the universal quantifier ∀x.B(x); the dependent pair Σ(x:A).B(x) generalizes the product and the existential ∃x.B(x), and its first projection literally extracts the witness. This is already visible in the book: chapter 9 (09_lean_first_steps.md) states 'the proposition ∀n.P(n) corresponds to the type (n:ℕ)→P n'. Locate the whole design in Barendregt's λ-cube: STLC is the base vertex; adding terms-depending-on-types gives polymorphism (System F), types-depending-on-types gives λω, and types-depending-on-terms gives dependent types (λP); the apex λC (Calculus of Constructions) has all three and is the ancestor of Lean's and Rocq's CIC.

**Key definitions**

- Dependent function (Π-) type Π(x:A).B(x): value f with f a : B(a); when B is constant this is A→B
- Dependent pair (Σ-) type Σ(x:A).B(x): pairs ⟨a,b⟩ with a:A and b:B(a); projections π₁,π₂
- Identity type Id_A(a,b) (written a =_A b): the type of proofs that a and b are equal; introduced by refl : Id_A(a,a)
- Indexed inductive family, e.g. Vec A n (length-indexed vectors)
- Barendregt's λ-cube; apex = Calculus of Constructions (λC / λPω)

**Key results**

- Π generalizes → and realises the universal quantifier: Π(x:A).B corresponds under Curry-Howard to ∀x:A. B(x)
- Σ generalizes × and realises the (constructive, witness-carrying) existential ∃x:A. B(x); π₁ of a proof of ∃ returns an actual witness
- Type-level function application example: for cons : A→Vec A n→Vec A (n+1), the output type is computed from the input length — a theorem (append length adds) becomes a *typing*
- The λ-cube places STLC, System F (polymorphism), λP (dependent types) and λC (all combined) as vertices reached by independently switching on the three dependency axes

## Martin-Löf type theory in one breath

Give the students the name and the shape of the foundation that Agda implements directly and that CIC extends. Per Martin-Löf (1972 preprint; 1984 Padova lectures, notes by Sambin) proposed a constructive foundation intended to stand to intuitionistic mathematics as ZFC stands to classical. Its distinctive move is *four* judgment forms rather than one, and *elimination rules that are induction principles*. Enumerate the type formers in one sweep: the finite types 0,1,2, the natural numbers ℕ with its recursor, Π, Σ, the identity type Id, W-types for well-founded trees, and the universe hierarchy U₀:U₁:…. The most important pedagogical link back to the book: the elimination rule for ℕ *is* the principle of mathematical induction — this is exactly book chapter 7 (07_peano_preview.md), where the Peano axioms including induction were emulated in the Church world; MLTT makes induction a *primitive typing rule*. Flag the intensional (ITT, decidable type-checking, the practical choice) vs extensional (ETT, has equality reflection, undecidable type-checking) split, and mention one deep surprise that motivates the whole HoTT successor: in ITT you cannot prove that all proofs of a=b are equal (uniqueness of identity proofs fails, Hofmann–Streicher groupoid model 1994).

**Key definitions**

- The four judgment forms: 'A type', 'A = B' (type equality), 'a : A', 'a = b : A' (element equality)
- Formation / introduction / elimination / computation (β) rules — the standard four-part recipe for each type former
- ℕ with recursor rec_ℕ; Π, Σ, Id, finite types 0/1/2, W-types
- Predicative cumulative universe hierarchy U₀ : U₁ : U₂ : …
- Intensional (ITT) vs extensional (ETT) type theory; equality reflection rule (from p : Id_A(a,b) infer a ≡ b : A)

**Key results**

- The elimination rule for ℕ is exactly mathematical induction: to inhabit Π(n:ℕ).C(n) it suffices to give C(0) and Π(n:ℕ).C(n)→C(n+1) — connecting directly to book ch.7's Peano treatment
- Intensional MLTT has decidable type-checking (hence usable as a proof assistant); extensional MLTT, via equality reflection, has undecidable type-checking
- The predicative universe hierarchy blocks Girard's paradox, keeping MLTT consistent and normalizing
- Uniqueness of identity proofs (UIP / axiom K) is NOT provable in intensional MLTT (Hofmann–Streicher groupoid model, 1994) — the gap that later opens into Homotopy Type Theory and univalence

## Why type theory, not ZFC, underlies modern proof assistants

The 'why should a working mathematician care' payoff. Four concrete reasons, each demonstrable. (1) de Bruijn criterion / small trusted kernel: a proof is a *term*, checking a proof is *type-checking* a term, and type-checking is decidable and done by a tiny kernel — the book already states this in chapter 9 ('Lean has a type-checking kernel… the remaining 99% may have bugs and proofs are still correct'). (2) Computation is native: definitional equality means the kernel *runs* the term — 2+2 and 4 are literally the same type, no axioms fired; in ZFC every step is a first-order derivation with no built-in reduction. (3) Constructive content / extraction: a proof of ∃ hands back a program. (4) Theorems are types: Curry-Howard lets you *state* a theorem as a type and *prove* it by inhabiting it. Then be honest and balanced: ZFC-based checking is not dead — Mizar (Tarski–Grothendieck) and Isabelle/ZF prove real mathematics; the point is that Lean, Rocq and Agda chose type theory for decidable checking + computation + proofs-as-programs. This is the natural pivot into the four-foundations preview and into Lecture 6's Lean/Mathlib work (eml-formalization).

**Key definitions**

- de Bruijn criterion: trust reduces to a small, independently checkable proof-checking kernel
- Proof term / proof object (a term whose type is the theorem)
- Conversion (type-conversion) rule: if Γ ⊢ t : σ and σ ≡ τ then Γ ⊢ t : τ — computation inside the type system
- Definitional equality vs propositional equality (revisited operationally)
- Foundational split: type-theoretic (Lean, Rocq, Agda) vs set-theoretic/FOL (Mizar, Isabelle/ZF, Metamath)

**Key results**

- Kernel adequacy: a term is accepted as a proof iff the kernel confirms it has the stated type — proof checking is decidable type-checking (contrast: ZFC proof search / checking of arbitrary first-order derivations)
- Native computation: in CIC/MLTT, closed numerals with 2+2 and 4 are definitionally equal, so the equation holds by the conversion rule with no axiom invoked — a capability ZFC's first-order engine lacks
- Program extraction: from a constructive proof of Πx.∃y.R(x,y) one can extract a function f with R(x, f x) for all x
- The eml-formalization repo is a live instance: Lean 4.28.0 + Mathlib v4.28, 8062 kernel jobs, 0 sorry, audited by `#print axioms` — the de Bruijn criterion in production (Lecture 6)

## The four foundations of the course, previewed

Close by placing the four systems the mini-course will use on one slide, so students carry a map into Lectures 2–6. Lean 4 (Lecture 6, eml-formalization) and Rocq both sit on the Calculus of Inductive Constructions: dependent types + inductive families + an impredicative, definitionally proof-irrelevant universe Prop. Lean adds quotient types and is deliberately classical in Mathlib (it assumes Classical.choice, propositional extensionality, and derives excluded middle), whereas Rocq's Prop is intuitionistic by default. Agda implements intensional predicative MLTT more literally — universe-polymorphic, no built-in classical axioms, and the natural home for cubical/HoTT experiments. Mizar is the outlier and the reason set theory stays on the syllabus: it is classical first-order logic over Tarski–Grothendieck set theory (ZFC strengthened with Grothendieck universes / inaccessible cardinals), with a 'soft type' layer that is not the logical foundation. This contrast — three type theories and one set theory — is the intellectual through-line of the whole course.

**Key definitions**

- Calculus of Inductive Constructions (CIC): dependent type theory = λC + inductive types + universe hierarchy + an impredicative Prop
- Lean 4 kernel: CIC with proof-irrelevant impredicative Prop, quotient types, and a small set of adopted axioms (Classical.choice, propext, Quot) used by Mathlib
- Rocq (formerly Coq) kernel: predicative CIC (pCIC) with impredicative intuitionistic Prop
- Agda: intensional, predicative, universe-polymorphic Martin-Löf type theory (with a cubical mode)
- Tarski–Grothendieck (TG) set theory: ZFC + Tarski's axiom A (every set belongs to a Grothendieck universe), the axiomatic base of Mizar

**Key results**

- Lean = CIC and Rocq = CIC (both type-theoretic, dependent, proofs-as-terms); Agda = MLTT (type-theoretic, intensional); Mizar = classical FOL over Tarski–Grothendieck set theory (set-theoretic) — the course's one non-type-theoretic system
- Every theorem in the Mizar Mathematical Library is a machine-verified logical consequence of the TG axioms (over 1400 articles, 65,000+ theorems as of 2023)
- Lean/Mathlib is classical (excluded middle is available via Classical.choice), while Agda and Rocq are constructive by default — the same Curry-Howard machinery, different axiomatic commitments
- The renaming Coq → 'The Rocq Prover' completed with version 9.0 (March 2025); the current line is Rocq 9.2.0 (March 2026)

## Pedagogical arc
"A 90-minute on-ramp in six movements. (1) Hook, 8 min — reuse the book's untyped world (alligators / λx.x from 02_lambda_basics.md) and ask a single question that types answer: 'the term (λx. x x)(λx. x x) never stops — can we rule that out mechanically?' Motivate types as a discipline that buys termination and meaning. (2) STLC, 20 min — introduce the judgment Γ ⊢ t : σ, put the three rules (Var/Abs/App) on the board, and derive the type of λf.λx.f(f x) together; state subject reduction and strong normalization, and land the payoff that the book's Y combinator and Ω are untypable. (3) Church vs Curry, 10 min — same term, two philosophies; show the lambda_lab `ch term \\p. p` output (Curry-style α→α) versus the emitted Church-style Lean `fun p => p : P → P`; mention principal types and Hindley–Milner. (4) The big reveal — Curry-Howard, 20 min — build the dictionary table, then run three live `ch type` demos (P→P = identity, transitivity = composition, and Peirce's law refused) so the correspondence is *seen*, not asserted; state provability = inhabitation and mark the intuitionistic boundary. (5) Going deeper — dependent types + MLTT, 20 min — motivate Vec A n, introduce Π and Σ as the quantifiers, name the identity type, and give MLTT 'in one breath' with the punchline that ℕ-elimination is the induction of the book's Peano chapter; drop the one-slide warning about Girard's paradox to explain why universes are stacked. (6) Landing — foundations, 12 min — why kernels + decidable type-checking + native computation make type theory the assistant-builder's choice (quote the book's ch.9 kernel paragraph), then the four-foundations map (Lean=CIC, Rocq=CIC, Agda=MLTT, Mizar=TG set theory) as the trailer for Lectures 2–6, ending on the live eml-formalization badge (0 sorry, 8062 kernel jobs) as 'this is where we are going.' Leave 5 min buffer for a hands-on `ch build P -> P` if the room is lively; assign Wadler's article as the evening read."

## Connections to existing material
"This lecture is the type-theory capstone the falenty-2026 book was implicitly building toward, so it should reuse the book's own artifacts rather than reintroduce notation. Direct reuse: book/en/notebooks/02_lambda_basics.md supplies the untyped grammar t ::= x | λx.t | t t and free/bound-variable machinery that STLC types sit on top of; 03_substitution_reduction.md supplies β-reduction, needed for subject reduction and normalization; 04_church_booleans.md, 05_church_numerals.md and 06_recursion_and_Y.md provide Ω and the Y combinator — the concrete terms this lecture shows are *untypable* in STLC (the point of strong normalization). 07_peano_preview.md is reused twice: its Peano/induction content is exactly what MLTT's ℕ-elimination formalizes. 08_curry_howard.md and especially 10d_curry_howard_playground.md are the spine of the Curry-Howard segment — the lecture should run the actual `ch` sub-commands documented there (ch term / ch type / ch lib / ch lean / ch build / ch verify), including the Peirce's-law non-inhabitation demo and the K/S = Hilbert-axioms observation. 09_lean_first_steps.md and 09c_macbeth_mechanics_of_proof.md give the kernel / de Bruijn-criterion paragraph reused verbatim in the 'why type theory' movement, and the Church-vs-tactic term-mode Lean proofs. 12_further_reading.md already lists Pierce, Girard–Lafont–Taylor and the HoTT book, so the reference slide is continuous with the book. lambda_lab commands to demo live: `church`, `reduce`, `peano` (link to MLTT induction), and the whole `curry_howard`/`ch` family; `tour`, `quiz` and `kb` can seed exercises. For Lecture 6 the lecture points forward to eml-formalization/README.md and DASHBOARD.md: the EMLTerm/EMLTermℂ inductive type with eval? : Option ℂ is a perfect 'types-as-data / theorems-as-typings' payoff, and the badges (Lean 4.28.0 + Mathlib v4.28, 8062 kernel jobs, 0 sorry, audited by #print axioms) are the concrete de-Bruijn-criterion evidence this lecture promises. classical-foundations-ann supplies the house style (historical-context → real definitions/theorems → runnable code → exercises) that the lecture notes should match."

## Artifact ideas

- **Lean 4** (easy): theorem id' {P : Prop} : P → P := fun p => p  — the identity proof; then theorem s_comb {P Q R : Prop} : (P → Q → R) → (P → Q) → P → R := fun f g p => f p (g p) (the S combinator = its Hilbert axiom). Have students confirm both with lambda_lab `ch verify`.
- **Lean 4** (easy): example {P Q : Prop} : (P → Q) → P → Q := fun f p => f p  (modus ponens = function application) and example {P Q : Prop} : P ∧ Q → Q ∧ P := fun ⟨hp, hq⟩ => ⟨hq, hp⟩ (∧ commutes = swap a pair) — mirrors book ch.8 exactly, now kernel-checked.
- **Lean 4** (medium): theorem peirce {P Q : Prop} : ((P → Q) → P) → P := by exact Classical.byContradiction (fun h => h (fun hp => absurd hp h)) — and then show that deleting `Classical` makes it fail, dramatizing the intuitionistic/classical boundary that `ch type '((P -> Q) -> P) -> P'` reports as uninhabited.
- **Lean 4** (medium): Dependent-type demo: inductive Vec (α : Type) : Nat → Type with nil and cons, then def head {α n} : Vec α (n+1) → α := fun (Vec.cons x _) => x — a total head whose *type* forbids the empty case. Shows types-depending-on-values and why '∀ n, P n' is the type '(n : ℕ) → P n' from book ch.9.
- **Agda** (easy): id : {A : Set} → A → A ; id x = x   and the dependent function/∀ demo  everything-implies-itself : {A : Set} → A → A ; everything-implies-itself = id, plus data ⊥ : Set (no constructors) and ⊥-elim : {A : Set} → ⊥ → A ; ⊥-elim ()  — Agda as literal MLTT, the empty type = false.
- **Agda** (medium): Σ / ∃ with a real witness: open the standard library's Data.Nat and prove ∃-even : Σ ℕ (λ n → n + n ≡ 4) ; ∃-even = 2 , refl — a constructive existence whose first projection literally returns the witness 2, illustrating Σ-as-∃.
- **Rocq (Coq)** (easy): Definition modus_ponens (P Q : Prop) : (P -> Q) -> P -> Q := fun f p => f p.  and  Definition and_comm (P Q : Prop) : P /\ Q -> Q /\ P := fun H => match H with conj hp hq => conj hq hp end.  — the same Curry-Howard terms as Lean, on the other CIC assistant, to show foundation-portability.
- **Rocq (Coq)** (medium): Show the intuitionistic wall directly: Lemma peirce_needs_classical (P Q : Prop) : ((P -> Q) -> P) -> P. Attempt a constructive proof (fails), then Require Import Classical and close it with `apply NNPP` or `tauto` under the classical axiom — same lesson as the Lean Peirce artifact, default-constructive assistant.
- **Mizar** (hard): A minimal Tarski–Grothendieck-flavoured theorem to contrast set-theoretic style with the type-theoretic ones: `theorem for x, y being set holds x in {x, y};` (or reflexivity `for X being set holds X = X;`) proved inside an environ importing TARSKI — demonstrates classical FOL over TG set theory, no Curry-Howard term, the course's one non-type-theoretic foundation.
- **Lean 4** (medium): Church-encoding bridge to book ch.5/7: def CNat := (α : Type) → (α → α) → α → α ; def czero : CNat := fun _ f x => x ; def csucc (n : CNat) : CNat := fun α f x => f (n α f x) — the typed (System F/CIC) home of the untyped Church numerals, showing the same encoding now carries a type.

## Pitfalls / misconceptions

- 'A type is just the set of its values.' Safe for STLC, but students over-generalize: it fails once equality is proof-relevant (two proofs of a=b need not be equal) and collapses entirely at a type-of-all-types (Girard's paradox). Install the caveat the same hour you give the intuition.
- Confusing definitional/judgmental equality (a ≡ b, 'computes to', checked automatically) with propositional equality (a = b, a theorem needing a proof / an inhabitant of Id_A(a,b)). This is the single most common MLTT stumbling block.
- Believing every classical tautology has a proof term. Peirce's law and double-negation elimination are inhabited only with a classical axiom; Curry-Howard yields *intuitionistic* proofs. Students expect λ-terms for excluded middle and are surprised none exists.
- Thinking Church-style and Curry-style are rival theories rather than two readings of the same system related by type erasure — and expecting a unique type in the Curry world (λx.x has infinitely many types) or many types in the Church world (annotations force uniqueness).
- Assuming the Y combinator / general recursion 'obviously' still type-checks. In STLC it does not — strong normalization forbids it — which is exactly why STLC is a *logic* and not a Turing-complete language. Recursion returns only with inductive types and their recursors.
- Reading ∀ as merely a decorated → and ∃ as merely a decorated ×. The dependency is the whole point: in Π(x:A).B(x) the codomain type varies with the input, and in Σ the second component's type depends on the first — that is what ordinary function/product types cannot express.
- Assuming 'proof assistant' implies 'type theory', so Mizar gets mis-slotted. Mizar is classical first-order logic over Tarski–Grothendieck set theory; its 'types' are a soft convenience layer, not the logical foundation — the deliberate contrast the course exploits.
- Overstating 'type theory replaced ZFC'. Type theory is the foundation of Lean/Rocq/Agda for engineering reasons (small kernel, decidable checking, native computation, proofs-as-programs), but ZFC-style checking (Mizar, Isabelle/ZF, Metamath) verifies real mathematics too. Present it as a design choice, not a victory.

## Canonical references

- Benjamin C. Pierce, Types and Programming Languages, MIT Press, 2002 (ISBN 0-262-16209-1). — <https://www.cis.upenn.edu/~bcpierce/tapl/>  
  _The standard textbook for STLC: the exact typing rules (Var/Abs/App), Church vs Curry presentations, type preservation and progress, and normalization. It is already the book's own recommended reference (12_further_reading.md and ch. 10d)._
- Jean-Yves Girard, Yves Lafont, Paul Taylor, Proofs and Types, Cambridge Tracts in Theoretical Computer Science 7, Cambridge University Press, 1989 (free PDF). — <http://www.paultaylor.eu/stable/prot.pdf>  
  _The canonical, freely available source on Curry-Howard, System F and normalization; already cited in the book's further-reading list. Use for the β-reduction ↔ cut-elimination story._
- Morten Heine Sørensen & Paweł Urzyczyn, Lectures on the Curry–Howard Isomorphism, Studies in Logic and the Foundations of Mathematics 149, Elsevier, 2006 (ISBN 978-0-444-52077-7). — <https://disi.unitn.it/~bernardi/RSISE11/Papers/curry-howard.pdf>  
  _The most complete single reference tying STLC typing, intuitionistic natural deduction, the λ-cube and inhabitation together — exactly the arc of this lecture. Urzyczyn is a Polish logician, a nice local anchor for a Polish-led course._
- Philip Wadler, 'Propositions as Types', Communications of the ACM 58(12), 75–84, 2015. — <https://homepages.inf.ed.ac.uk/wadler/papers/propositions-as-types/propositions-as-types.pdf>  
  _The best high-level, historically rich exposition of Curry-Howard for a general mathematical/CS audience — ideal to hand out as the lecture's single 'read this tonight' article._
- Per Martin-Löf, Intuitionistic Type Theory (Padova lectures, notes by Giovanni Sambin), Bibliopolis, 1984. — <https://archive-pml.github.io/martin-lof/pdfs/Bibliopolis-Book-retypeset-1984.pdf>  
  _The primary source for MLTT: the four judgment forms, Π/Σ/Id and the identity type, inductive types with elimination = induction. Grounds the 'MLTT in one breath' and Agda=MLTT segments._
- The Univalent Foundations Program, Homotopy Type Theory: Univalent Foundations of Mathematics, Institute for Advanced Study, 2013. — <https://homotopytypetheory.org/book/>  
  _Free, modern reference for dependent types, identity types and universes, and the successor to plain MLTT (UIP failure, univalence). Already listed in the book's further reading; use for the dependent-types preview and the 'where types-as-sets breaks' equality discussion._
- Ana Bove, Peter Dybjer, 'Dependent Types at Work' / 'Intuitionistic Type Theory' (Stanford Encyclopedia of Philosophy, entry by Peter Dybjer & Erik Palmgren), 2016–2025 revisions. — <https://plato.stanford.edu/entries/type-theory-intuitionistic/>  
  _Authoritative, continuously updated encyclopedic account of MLTT, propositions-as-types, intensional vs extensional theory and universes — a citable one-stop reference for the lecture's conceptual claims (Curry 1958, Howard 1980, de Bruijn 1970)._
- Jeremy Avigad, Leonardo de Moura, Soonho Kong, Sebastian Ullrich, Theorem Proving in Lean 4 (official documentation). — <https://leanprover.github.io/theorem_proving_in_lean4/>  
  _Grounds the 'Lean = CIC' claim and the de Bruijn-criterion / kernel discussion in an authoritative primary source, and is the bridge document to Lecture 6 and the on-disk eml-formalization (Lean 4.28 + Mathlib)._

## Volatile facts (sent to fact-check)

- Lean 4's kernel implements a dependent type theory in the family of the Calculus of Inductive Constructions (CIC); as of mid-July 2026 the latest toolchain line is Lean 4.32.0 (released 2026-07-13) with 4.33.0-rc1 (2026-07-15), while the course's eml-formalization repo is pinned to Lean 4.28.0 + Mathlib v4.28. (src: https://github.com/leanprover-community/mathlib4/blob/master/lean-toolchain)
- The Coq proof assistant has been officially renamed 'The Rocq Prover': version 9.0.0 (the first release under the new name) shipped on 12 March 2025, and the current line is Rocq 9.2.0 (released 30 March 2026). Its kernel is CIC, the same family as Lean's. (src: https://rocq-prover.org/releases/9.0.0)
- Mizar is built on classical first-order logic over Tarski–Grothendieck set theory (ZFC plus Grothendieck universes / Tarski's Axiom A); as of 2023 its Mizar Mathematical Library contains over 1,400 articles with more than 13,000 definitions and over 65,000 machine-verified theorems. (src: https://mizar.uwb.edu.pl/library/)
- Mathlib, Lean's classical mathematics library, comprises roughly 230,000 theorems and 115,000 definitions across about 2.1 million lines of code contributed by 500+ people as of late 2025 — the practical scale that makes Lean the course's flagship assistant. (src: https://arxiv.org/pdf/2508.21593)
- Girard proved System U inconsistent in 1972 (Girard's paradox): a type theory with a type-of-all-types rule Type : Type contains a non-normalizing proof of falsity, the type-theoretic form of the Burali-Forti/Russell paradox; this is why consistent systems (Agda, Rocq, Lean) use a cumulative universe hierarchy U₀ : U₁ : U₂ : … . (src: https://en.wikipedia.org/wiki/System_U)
