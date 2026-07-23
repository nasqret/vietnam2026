# Lecture 3 — Propositional Logic Proofs (A Reintroduction to Proofs)

> A hands-on tour of natural deduction for propositional logic through Emily Riehl's Lean game "A Reintroduction to Proofs", using the Curry–Howard correspondence (→ as function, ∧ as product, ∨ as sum, ⊥ as empty, ¬ as →⊥) to turn each inference rule into a Lean tactic, and marking exactly where intuitionistic reasoning ends and classical logic begins.

## Learning objectives

- State the introduction and elimination rules of Gentzen-style natural deduction for the propositional connectives →, ∧, ∨, ⊥ (and derived ¬, ⊤), and reproduce each as a rule with premises and conclusion.
- Explain the BHK (Brouwer–Heyting–Kolmogorov) interpretation of the connectives and use it to decide whether a propositional formula is intuitionistically valid, correctly identifying LEM (P ∨ ¬P), double-negation elimination (¬¬P → P) and Peirce's law (((P→Q)→P)→P) as the classical boundary.
- Articulate the Curry–Howard correspondence for propositional connectives — → as function type, ∧ as product, ∨ as sum, ⊥ as the empty type, ¬P as P→⊥ — and read a Lean proof term (e.g. `fun p => p`, `⟨p, q⟩`, `Or.inl p`) as the program that witnesses a proposition.
- Map each Lean tactic used in the game (intro, exact, apply, constructor, cases/obtain/rcases, left/right, exfalso, by_contra) to the exact natural-deduction rule or term-former it performs, and predict how it transforms the goal and the underlying partial proof term.
- Complete the propositional worlds of Riehl's game and produce sorry-free proofs of representative theorems: ∧- and ∨-symmetry, currying P∧Q→C ≃ P→Q→C, double-negation introduction P→¬¬P, triple-negation collapse ¬¬¬P→¬P, and a De Morgan law.
- Distinguish a constructive proof from a classical one and justify precisely when by_contra or Classical.em is genuinely required, versus when a direct constructive proof exists.

## Prerequisites

- Lecture 1–2 material: untyped and simply-typed lambda calculus, terms/types, β-reduction, and the first statement of Curry–Howard (types = propositions, programs = proofs).
- Comfort with propositional connectives ∧, ∨, →, ¬ at the level of a first course in logic or discrete mathematics (truth tables acceptable as background, but the lecture deliberately replaces them with derivations).
- Familiarity with functions as first-class objects (currying, composition) — the identity, K and S combinators from Lecture 2.
- A modern web browser (the game runs entirely in-browser on the Lean 4 Game server; no local Lean install needed). Optional: a working `lean`/`lake` toolchain for the Lambda Lab `ch verify` demonstration.

## Natural deduction for propositional logic (Gentzen)

Open the lecture on paper before touching Lean. Present Gentzen's 1934/35 calculus of natural deduction: each connective has introduction rules (how to prove it) and elimination rules (how to use it), and the two are in harmony (an intro immediately followed by an elim reduces — the seed of normalization). Do →, ∧, ∨, ⊥ carefully; derive ¬ and ⊤. Emphasize the discharge of hypotheses in →-introduction (the box/assumption that gets closed) because this is exactly what Lean's `intro` and lambda-abstraction do. Keep it syntactic: a proof is a tree built from rules, not a truth-table verification. This is the abstract skeleton that every game world instantiates.

**Key definitions**

- A derivation is a finite tree whose leaves are assumptions and whose internal nodes are instances of inference rules; the conclusion is the root formula.
- Discharged assumption: an assumption that is 'used up' (closed) by an →-introduction, indicated by bracketing.
- Harmony / local soundness: eliminating a just-introduced connective returns the components used to introduce it (detour/redex).

**Key results**

- →-introduction: from a derivation of B under assumption A, conclude A→B (discharging A). →-elimination (modus ponens): from A→B and A conclude B.
- ∧-introduction: from A and B conclude A∧B. ∧-elimination: from A∧B conclude A (and, separately, B).
- ∨-introduction: from A conclude A∨B (and from B conclude A∨B). ∨-elimination (case analysis): from A∨B, and derivations of C from A and of C from B, conclude C.
- ⊥-elimination (ex falso quodlibet): from ⊥ conclude any C. There is no ⊥-introduction rule — that absence is the whole point.
- Derived: ¬A := A→⊥; the introduction/elimination rules for ¬ are just the →-rules specialized to conclusion ⊥.

## The BHK interpretation and intuitionistic meaning of the connectives

Give the connectives their constructive semantics before Curry–Howard makes it official. BHK reads each connective as a recipe for building proofs, not as a truth value. This is the conceptual pivot of the whole lecture: 'proof' becomes a first-class mathematical object (a construction), which is exactly why it can be a Lean term. Stress the disjunction and negation clauses — they are where classical and intuitionistic logic diverge. Use BHK to explain, informally, why there is no construction witnessing P∨¬P in general: you would need to actually decide P.

**Key definitions**

- BHK for ∧: a proof of A∧B is a pair ⟨a,b⟩ where a proves A and b proves B.
- BHK for ∨: a proof of A∨B is a pair (i, p) where the tag i∈{0,1} selects a disjunct and p proves that disjunct (i.e. a tagged/sum construction).
- BHK for →: a proof of A→B is a construction (function) transforming any proof of A into a proof of B.
- BHK for ⊥: there is no proof of ⊥ (falsum has no constructions).
- BHK for ¬: a proof of ¬A = A→⊥ is a construction turning any putative proof of A into a proof of ⊥.
- BHK for ∀/∃ (preview for the next lecture): ∀x.A(x) is a function x↦proof of A(x); ∃x.A(x) is a pair ⟨t, proof of A(t)⟩.

**Key results**

- Intuitionistically PROVABLE: A→¬¬A; ¬¬¬A→¬A; ¬(A∧¬A) (non-contradiction); both directions of the De Morgan law ¬(A∨B) ↔ (¬A∧¬B); the one-way (¬A∨¬B)→¬(A∧B).
- Intuitionistically NOT PROVABLE (need classical logic): excluded middle A∨¬A; double-negation elimination ¬¬A→A; Peirce's law ((A→B)→A)→A; the converse De Morgan ¬(A∧B)→(¬A∨¬B).
- Glivenko's theorem (1929): a propositional formula A is classically provable iff ¬¬A is intuitionistically provable — a precise measure of the gap, and why double-negation translations work.

## Curry–Howard for propositional connectives (propositions as types)

Now make BHK official: the constructions ARE typed terms. This reuses the author's notebook 08 dictionary verbatim and extends it to ∨, ⊥, ¬. Historically: Curry (1934) saw combinator types match Hilbert axioms for implication; Howard (1980) extended it to full natural deduction and the simply-typed λ-calculus, adding products, sums, empty type. The deep payoff to state explicitly: proof normalization in natural deduction (Prawitz) corresponds exactly to β-reduction of terms — cut elimination is running a program. In Lean, `And` is a structure (product), `Or` is an inductive with two constructors (sum), `False`/`Empty` is the inductive with no constructors, `True`/`Unit` has one.

**Key definitions**

- Proposition-as-type: a proposition P is the type of its proofs; 'P is provable' = 'the type P is inhabited'; a proof is a term p : P.
- → is the (non-dependent) function type A→B; a proof is a lambda term `fun a => …`.
- ∧ is the product/pair type: A∧B with constructor And.intro / ⟨a,b⟩ and projections .1, .2.
- ∨ is the sum/coproduct type: A∨B with injections Or.inl : A→A∨B and Or.inr : B→A∨B, eliminated by matching on both constructors.
- ⊥ is the empty type (False/Empty): no constructors, and its eliminator False.elim / absurd witnesses ex falso quodlibet; ¬A is the function type A→False; ⊤ is the unit type (True/Unit) with sole term trivial.
- Curry–Howard–Lambek extension (mention): these type formers are the universal constructions (product, coproduct, exponential, initial/terminal object) of a category — the L6/HoTT bridge.

**Key results**

- Dictionary: P→Q ≙ function type; P∧Q ≙ A×B; P∨Q ≙ A⊕B; ⊥ ≙ ∅ (initial type); ⊤ ≙ 1 (terminal type); ¬P ≙ P→∅.
- Identity/assumption: the proof of P→P is `fun p => p` (the identity program) — TypeWorld/FunctionWorld.
- Modus ponens = function application: `(P→Q)→P→Q` is `fun f p => f p`.
- ∧-commutativity as a program: `fun ⟨p,q⟩ => ⟨q,p⟩` proves P∧Q→Q∧P; currying `(P∧Q→C) ≃ (P→Q→C)` is the product/exponential adjunction.
- Normalization ↔ β-reduction (Prawitz): removing a proof detour (intro-then-elim) equals β-reducing the corresponding redex, so proof simplification is computation.

## Lean's tactic language as proof-term construction

The lecture's central bilingual claim: every tactic is a recipe that builds a piece of the proof term. Present the tactic↔rule↔term table and, for each, show what happens to BOTH the goal state and the partial term (the author's Lambda Lab `ch build` visualizes exactly this hole-filling). Warn that `by_contra` is not a natural-deduction rule but a classical axiom in disguise. Note that Riehl's game uses `obtain`/`rcases` for destructuring and `left`/`right` for ∨-intro; the author's 22-tactic encyclopedia (tactics.py) already covers intro/exact/apply/constructor/cases/rcases/left/right/by_contra — this lecture extends it with `exfalso` and `obtain`, which are not yet in that list.

**Key definitions**

- Tactic: a metaprogram that transforms the proof state (hypotheses ⊢ goal) and appends to the proof term; `by … ` enters tactic mode building a term of the goal type.
- Goal state ⊢: a sequent of local hypotheses (the context) and a target type to inhabit.
- Anonymous constructor ⟨…⟩: term-mode structure/inductive introduction, equivalent to the `constructor` tactic for single-constructor types.

**Key results**

- intro h ≙ →-introduction / Π-introduction ≙ lambda abstraction `fun h => ?`; turns goal A→B into B with h:A in context.
- exact e ≙ closing a goal by a term / the assumption rule; `assumption` searches the context (TypeWorld L02).
- apply f ≙ →-elimination used backward (modus ponens); turns goal Q into goal P when f : P→Q (ImplicationWorld L02).
- constructor / ⟨p,q⟩ ≙ ∧-introduction (also ∃-/structure-intro); splits goal A∧B into A and B (ConjunctionWorld L01).
- cases / obtain / rcases h with … ≙ ∧-elimination (destructure a pair), ∨-elimination (case split, two subgoals), and ⊥-elimination (zero subgoals when h : Empty/False) (DisjunctionWorld L03, EmptyWorld L01).
- left / right ≙ ∨-introduction (Or.inl / Or.inr); exfalso ≙ ⊥-elimination, replacing any goal by False (NegationWorld L01/EmptyWorld); by_contra h ≙ classical reduction, replacing goal P by False with h:¬P (ClassicalWorld L01).

## Riehl's 'A Reintroduction to Proofs' — world-by-world map

The spine of the live portion. The game (17 worlds, Lean v4.23.0, MIT, ~248 commits, built for a Fall-2025 JHU first-year seminar) deliberately front-loads the constructive core and quarantines classical logic into its own world; it even studies the Empty type BEFORE negation so that ¬ arrives as an already-understood P→⊥. For a 90-minute propositional-logic session, play/skip through TypeWorld → FunctionWorld → ImplicationWorld → ProductWorld/ConjunctionWorld → CoproductWorld/DisjunctionWorld → EmptyWorld → NegationWorld → ClassicalWorld; defer QuantifierWorld, NaturalNumbersWorld, EqualityWorld, AdvancedFunctionWorld, BooleanWorld, DependentWorld to later lectures. Each world instantiates exactly one cluster of rules from Topic 1.

**Key definitions**

- World dependency (from Game.lean): TypeWorld → FunctionWorld → {ImplicationWorld, ProductWorld} → ConjunctionWorld; ProductWorld → CoproductWorld → DisjunctionWorld; CoproductWorld → EmptyWorld → {NegationWorld, EqualityWorld}; NegationWorld → ClassicalWorld; then QuantifierWorld → AdvancedFunctionWorld → {EquivalenceWorld, NaturalNumbersWorld} → DependentWorld.
- TypeWorld: p : P means p is a proof of P; tactics `exact`, `assumption` (L02 Proofs: `{P : Prop} (p : P) : P`).
- FunctionWorld/ImplicationWorld: → as function; identity `fun p => p`, composition, `intro`/`apply`/`exact` (L02 ModusPonens: `(p : P) (h : P → Q) : Q` proved by `apply h; exact p`).
- Conjunction/Product & Disjunction/Coproduct: `constructor`/⟨,⟩/projections and `left`/`right`/`obtain`; symmetry, associativity, universal properties, distributivity.
- Empty/NegationWorld: Empty→A (`intro p; cases p`), ¬P := P→False, ex falso; Classical/BooleanWorld: `by_contra`, `Classical.em`.

**Key results**

- ConjunctionWorld L01: `{P Q : Prop} (p : P) (q : Q) : P ∧ Q` — `constructor; exact p; exact q` (or `exact ⟨p,q⟩`).
- DisjunctionWorld L03/L04 (∨-symmetry): `{P Q : Prop} : P ∨ Q → Q ∨ P` — `intro h; rcases h with p | q; · exact Or.inr p; · exact Or.inl q`.
- EmptyWorld L01: `{A : Type} : Empty → A` — `intro p; cases p` (elimination with zero constructors).
- NegationWorld: double-negation intro `P → ¬¬P`, non-contradiction `¬(P ∧ ¬P)`, triple-negation `¬¬¬P → ¬P` — all constructive.
- ClassicalWorld L03 (case-exhaustion via em): `(P ∧ Q) ∨ (P ∧ ¬Q) ∨ (¬P ∧ Q) ∨ (¬P ∧ ¬Q)`, proved with `have := em P; have := em Q; rcases … `.

## The classical boundary: by_contra, excluded middle, and constructive vs classical proof

Close the loop by making the constructive/classical distinction operational and honest. In the game this is physically a separate world reached only after negation; philosophically it is where you stop building a witness and start reasoning about non-existence of counterexamples. Demonstrate the boundary live with the author's `ch type ((P→Q)→P)→P` returning 'not inhabited in intuitionistic STLC' (Peirce's law), then show Lean closing the same goal with `by_contra`/`tauto`. Tie back to Glivenko: everything classical is just a double negation away. Flag the honest cost: a classical proof of ∃ need not hand you the object.

**Key definitions**

- Classical.em P : P ∨ ¬P — the law of excluded middle, an axiom (not a theorem) in Lean's constructive core, made available via `open Classical` / `Classical.em`.
- by_contra h : to prove P, assume h : ¬P and derive False; equivalent to double-negation elimination ¬¬P→P.
- Contrapositive: (P→Q) → (¬Q→¬P) is constructive, but its converse strengthening to (¬Q→¬P)→(P→Q) is classical.
- Glivenko translation / Gödel–Gentzen negative translation: embeddings making classical provability reflect into intuitionistic provability via ¬¬.

**Key results**

- Peirce's law ((P→Q)→P)→P has no simply-typed lambda witness (verified by Lambda Lab's `ch type`); it is provable only classically.
- ¬¬P→P, P∨¬P, and Peirce's law are inter-derivable over intuitionistic propositional logic — adding any one recovers full classical logic.
- ClassicalWorld L02 (contrapositive), L05 (negating an implication: ¬(P→Q) → P∧¬Q needs classical logic; the converse P∧¬Q→¬(P→Q) is constructive).
- Glivenko (1929): ⊢_c A iff ⊢_i ¬¬A (propositional) — so classical propositional logic embeds into intuitionistic logic under double negation.

## Pedagogical arc
"A 90-minute session in three movements — chalk, dictionary, keyboard. (0–12 min) Motivation and callback: revisit Lecture 2's `fun p => p` and the slogan proofs=programs; ask 'what actually IS a proof?' and answer 'a construction', setting up BHK. (12–28 min) Chalk natural deduction: derive the intro/elim rules for →, ∧, ∨, ⊥ on the board (Topic 1), doing one two-line derivation (∧-commutativity) fully by hand and highlighting hypothesis discharge in →-intro. (28–40 min) The dictionary: put up the Curry–Howard table (reuse notebook 08's table, extended to ∨/⊥/¬), and the tactic↔rule↔term table (Topic 4); demonstrate on the projector with Lambda Lab `ch type 'P -> P'` and `ch build P -> P` so students SEE a tactic fill a hole in the term. (40–72 min) Keyboard — the game: students open 'A Reintroduction to Proofs' in browsers and play TypeWorld→FunctionWorld→ImplicationWorld (intro/exact/apply), then ConjunctionWorld+DisjunctionWorld (constructor/obtain/left/right), then EmptyWorld+NegationWorld (exfalso; ¬ as →False). Instructor plays boss levels live and narrates each tactic back to its rule. (72–84 min) The classical boundary: play ClassicalWorld L01/L03; contrast with `ch type '((P->Q)->P)->P'` returning 'not inhabited' (Peirce's law); state Glivenko and the honest cost of classical existence proofs (Topic 6). (84–90 min) Synthesis and forward pointer: recap the tactic↔rule table as the lecture's one-slide takeaway; preview that the SAME tactics scale to real mathematics (QuantifierWorld next lecture; and in Lecture 6 the author's eml-formalization proves a research paper in Lean 4 + Mathlib with exactly these moves). Homework: finish NegationWorld and one De Morgan law; optionally reproduce a game proof as a bare term with `ch verify`."

## Connections to existing material
"Directly reuses and extends several assets in falenty-2026 and eml-formalization. (1) book/en/notebooks/08_curry_howard.md — its Logic↔Types table is the exact dictionary of Topic 3; the lecture extends it from →/∧ to ∨ (sum), ⊥ (empty) and ¬ (=→⊥). (2) book/en/notebooks/10d_curry_howard_playground.md — the `ch` command family (term/type/lib/lean/from-lean/tactic/build/verify) is the live demo engine: `ch build P -> P` visualizes intro/exact hole-filling; `ch type '((P -> Q) -> P) -> P'` demonstrates Peirce's law being uninhabited (Topic 6), and Exercise 10d.2 already stages the intuitionistic boundary. (3) lambda_lab/lab/curry_howard/tactics.py — the 22-tactic encyclopedia already documents intro, exact, apply, constructor, cases, rcases, left, right, by_contra, contradiction, tauto; THIS lecture should add `exfalso` and `obtain`, which are currently missing, so the encyclopedia matches the game's tactic set. (4) lambda_lab/lab/curry_howard/explore/data/*.json — id.json, K.json, S.json, modus_ponens.json, and_comm.json, or_comm.json, not_not_intro.json, de_morgan_pl.json are ready-made propositional witnesses mapping one-to-one onto ImplicationWorld, ConjunctionWorld, DisjunctionWorld and NegationWorld; use them as the paper-to-term bridge. (5) book/en/notebooks/09_lean_first_steps.md, 09b_natural_number_game.md, 09c_macbeth_mechanics_of_proof.md — establish Lean tactic syntax and the game-server workflow (NNG4 on the same adam.math.hhu.de engine); Riehl's game slots in as a logic-first companion to NNG's arithmetic-first game. (6) book/en/notebooks/07_peano_preview.md — inductive types and recursion, the prerequisite for the game's later NaturalNumbersWorld/DependentWorld (out of scope here, flagged as sequel). (7) lambda_lab/lab/games/data/ (nng4, lambda_lab_tutorial manifests) — the natural place to add a small 'reintro' world manifest mirroring the game's propositional worlds for offline play. (8) L6 forward link: eml-formalization/README.md + DASHBOARD.md + lambda_lab/proofs/eml/2603_21852/lean_workspace/EML/Framework/PaperClaims.lean — the propositions-as-types thread started here culminates in a real Lean 4 + Mathlib formalization where the same intro/exact/apply/constructor/rcases tactics build 100 sorry-free theorems; use it to answer 'does any of this scale?'"

## Artifact ideas

- **Lean 4** (easy): example {P Q : Prop} : P ∧ Q → Q ∧ P := by intro h; obtain ⟨p, q⟩ := h; exact ⟨q, p⟩  -- and the ∨ analogue P ∨ Q → Q ∨ P with rcases/left/right. Mirrors ConjunctionWorld L03 and DisjunctionWorld L03.
- **Lean 4** (medium): example {P : Prop} : P → ¬¬P := fun p f => f p   and   example {P : Prop} : ¬¬¬P → ¬P := fun h p => h (fun f => f p). Both fully constructive; contrast with the NON-provable-constructively ¬¬P → P (needs by_contra). Mirrors NegationWorld L03/L10.
- **Lean 4** (medium): Two De Morgan laws side by side: (a) example {P Q : Prop} : ¬(P ∨ Q) ↔ (¬P ∧ ¬Q) := ⟨fun h => ⟨fun p => h (Or.inl p), fun q => h (Or.inr q)⟩, fun ⟨np,nq⟩ h => h.elim np nq⟩  (constructive, both directions); (b) example {P Q : Prop} : ¬(P ∧ Q) → ¬P ∨ ¬Q := by intro h; by_contra g; ...  (classical only). The pair is the lecture's punchline on the intuitionistic boundary.
- **Lean 4** (hard): Peirce's law both ways: theorem peirce {P Q : Prop} : ((P → Q) → P) → P := by intro h; by_contra hnp; exact hnp (h (fun p => absurd p hnp))  — provable ONLY with by_contra/em — juxtaposed against a comment that no `fun`-only (term-mode, tactic-free) proof exists. Cross-check with Lambda Lab `ch type '((P -> Q) -> P) -> P'` reporting 'not inhabited in intuitionistic STLC'.
- **Agda** (medium): Define connectives from scratch: data _⊎_ (A B : Set) : Set with inj₁/inj₂; data ⊥ : Set (no constructors); ¬ A = A → ⊥. Prove ⊎-comm : A ⊎ B → B ⊎ A and dni : A → ¬ ¬ A constructively; then show that ¬ ¬ A → A can only be obtained by `postulate` (or by importing a decidable-instance), making the classical axiom explicit. Demonstrates Curry–Howard where types literally ARE the propositions.
- **Rocq (Coq)** (easy): Lemma or_comm : forall P Q : Prop, P \/ Q -> Q \/ P. Proof. intros P Q H. destruct H as [p | q]. - right; exact p. - left; exact q. Qed.  plus Lemma dni : forall P : Prop, P -> ~~P. Proof. intros P p H. apply H. exact p. Qed.  Then show excluded_middle requires `Require Import Classical.` — the same constructive/classical split in Coq's tactic language (intros/destruct/left/right vs classic).
- **Rocq (Coq)** (medium): Peirce in Coq under classical logic: Require Import Classical. Lemma peirce : forall P Q : Prop, ((P -> Q) -> P) -> P. Proof. intros P Q H. destruct (classic P) as [p | np]. - exact p. - apply H. intro p. contradiction. Qed.  Parallels the Lean by_contra proof, exhibiting `classic`/`NNPP` as the imported axiom.
- **Mizar** (hard): A propositional tautology in Mizar's Jaśkowski-style natural deduction, e.g. `theorem for P, Q being set holds ... ` encoded via a scheme, or the built-in propositional reasoning `A & B implies B & A` and `A or B implies B or A` proved with `assume`, `then`, `hence`, `per cases`. Pedagogical point: Mizar's logic is CLASSICAL by construction, so excluded middle and Peirce's law are free — the contrast to Lean/Agda/Coq's constructive default is the lesson.

## Pitfalls / misconceptions

- Reading ¬P as a truth value ('P is false') rather than as the function type P→False: students expect to 'evaluate' ¬P instead of constructing a map that turns a proof of P into a proof of ⊥.
- Believing ∨-elimination tells you WHICH disjunct holds. From h : P ∨ Q you must handle BOTH cases (rcases/obtain into two subgoals); you never learn the tag constructively.
- Assuming excluded middle P∨¬P, double-negation elimination ¬¬P→P, and Peirce's law are 'obviously true' and therefore provable in the constructive core — they are exactly the axioms the game quarantines in ClassicalWorld.
- Reaching for by_contra reflexively. by_contra is a classical move (=¬¬-elimination); many goals (P→¬¬P, ¬(P∧¬P), De Morgan ¬(P∨Q)↔¬P∧¬Q) have direct constructive proofs, and using by_contra hides the constructive content.
- Confusing exfalso with by_contra. exfalso is ⊥-elimination ('from False, anything', always valid); by_contra is 'assume ¬goal, derive False' (classical). They are different rules that both mention False.
- Direction/role confusion among tactics: constructor/⟨,⟩ BUILDS a conjunction (∧-intro) while cases/obtain/rcases USES one (∧-elim); intro moves the hypothesis of an implication into context (forward) while apply reasons backward through modus ponens.
- Not seeing that `exact ⟨p, q⟩` (anonymous constructor) and `constructor` invoke the SAME ∧-introduction rule — treating term-mode and tactic-mode as different logics.
- Misparsing P → Q → R: forgetting → is right-associative and curried, so it means P → (Q → R) and takes its arguments one at a time (the K/S combinator shapes from Lecture 2).
- Equating a truth-table check with a proof. A propositional formula can be classically valid (true under every valuation) yet have NO intuitionistic natural-deduction derivation / no lambda-term witness; the semantic tautology and the constructive proof are different objects (Glivenko measures the gap).
- Expecting a classical existence/decision proof to yield the witness. by_contra/em can prove 'something exists' or 'P∨¬P' without exhibiting the object or deciding P — the honest cost of leaving the constructive fragment.

## Canonical references

- Emily Riehl, "A Reintroduction to Proofs" — Lean 4 game, hosted on the Lean Game Server; source repository github.com/emilyriehl/ReintroductionToProofs (MIT, built for a Fall 2025 first-year seminar at Johns Hopkins). Pinned to Lean v4.23.0. — <https://adam.math.hhu.de/#/g/emilyriehl/ReintroductionToProofs>  
  _The primary object of the lecture: the game whose worlds we play and whose exact theorem statements (TypeWorld L02, ImplicationWorld L02, ConjunctionWorld L01, DisjunctionWorld L03, EmptyWorld L01, ClassicalWorld L03) anchor every rule._
- Emily Riehl, course page for the Fall 2025 first-year seminar on computer-verified proof, describing the game's design (informal dependent type theory in place of set theory; Empty type studied before negation to separate constructive from classical proofs). — <https://emilyriehl.github.io/formalization/>  
  _Author's own pedagogical rationale for the world ordering and the constructive-first design — directly informs the lecture's pedagogical arc and the constructive/classical split._
- Philip Wadler, "Propositions as Types", Communications of the ACM 58(12):75–84, December 2015. — <https://homepages.inf.ed.ac.uk/wadler/papers/propositions-as-types/propositions-as-types.pdf>  
  _The definitive accessible modern account of Curry–Howard connecting Gentzen's natural deduction to typed lambda calculus and normalization=β-reduction; ideal single reading to hand students._
- Morten Heine Sørensen & Paweł Urzyczyn, "Lectures on the Curry–Howard Isomorphism", Studies in Logic and the Foundations of Mathematics, vol. 149, Elsevier, 2006. — <https://www.sciencedirect.com/bookseries/studies-in-logic-and-the-foundations-of-mathematics/vol/149>  
  _Rigorous textbook treatment of intuitionistic propositional logic, natural deduction, the BHK interpretation, and the propositional Curry–Howard isomorphism with full proofs — the reference for the mathematically mature reader._
- W. A. Howard, "The formulae-as-types notion of construction" (1969 manuscript), in J. P. Seldin & J. R. Hindley (eds.), To H. B. Curry: Essays on Combinatory Logic, Lambda Calculus and Formalism, Academic Press, 1980, pp. 479–490. — <https://www.cs.cmu.edu/~crary/819-f09/Howard80.pdf>  
  _The historical source extending Curry's observation to full natural deduction with products, sums and the empty type — grounds the Curry–Howard dictionary the lecture presents._
- Dag Prawitz, "Natural Deduction: A Proof-Theoretical Study", Almqvist & Wiksell, 1965 (Dover reprint 2006). — <https://store.doverpublications.com/products/9780486446554>  
  _Canonical source for the introduction/elimination rules, normalization, and the harmony/inversion principle that Curry–Howard mirrors as β-reduction._
- Joan Moschovakis, "Intuitionistic Logic", The Stanford Encyclopedia of Philosophy (E. N. Zalta ed.) — includes the BHK interpretation, Heyting's rules, Glivenko's theorem, and non-derivability of excluded middle. — <https://plato.stanford.edu/entries/logic-intuitionistic/>  
  _Authoritative, free, precise reference for BHK, the intuitionistic/classical boundary, and Glivenko's theorem cited in Topics 2 and 6._
- Jeremy Avigad, Leonardo de Moura, Soonho Kong & Sebastian Ullrich, "Theorem Proving in Lean 4" (official tutorial; chapters on Propositions and Proofs, and Tactics). — <https://leanprover.github.io/theorem_proving_in_lean4/propositions_and_proofs.html>  
  _Authoritative documentation for the Lean tactics (intro, apply, exact, constructor, cases/obtain, left/right, exfalso, by_contra) and for how Prop-terms realize Curry–Howard in Lean 4._

## Volatile facts (sent to fact-check)

- Emily Riehl's 'A Reintroduction to Proofs' is a Lean 4 game built for a Fall 2025 first-year seminar on computer-verified proof at Johns Hopkins; it comprises 17 worlds arranged so that the Empty type is studied before negation and classical reasoning is isolated in its own world, and it is playable on the Lean Game Server. (src: https://github.com/emilyriehl/ReintroductionToProofs)
- The game repository is pinned to Lean toolchain leanprover/lean4:v4.23.0 (per its lean-toolchain file), and is MIT-licensed with Lean making up ~96% of the source. (src: https://raw.githubusercontent.com/emilyriehl/ReintroductionToProofs/main/lean-toolchain)
- The current stable Lean 4 release as of the course date is 4.32.0 (released 2026-07-13), with 4.31.0 (2026-06-13) and 4.30.0 (2026-05-26) preceding it — i.e. the game's v4.23.0 is a few versions behind current stable, which is normal for a game-server deployment. (src: https://lean-lang.org/doc/reference/latest/releases/)
- Riehl's course design uses informal dependent type theory in place of set theory and first-order logic, and the game separates constructive proofs from classical ones by construction (its own stated rationale), which is why negation (¬P := P→False) is introduced constructively before by_contra and Classical.em appear. (src: https://emilyriehl.github.io/formalization/)
