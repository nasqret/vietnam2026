# Lecture 5 — Advanced Lean: Dependent Types, Mathlib, and Powerful Tactics

> A hands-on tour of Lean 4 as a working mathematician's tool — dependent types and typeclasses in practice, the ~351k-declaration Mathlib and how to search it, the computation-tactic zoo (simp/ring/linarith/omega/norm_num/field_simp/positivity/gcongr/decide/grind), calc blocks, structural and well-founded recursion, one real analysis/algebra proof end-to-end, and a first look at Lean 4 macros and elaboration.

## Learning objectives

- Read and write dependent function types: recognise that `∀ n : ℕ, P n` elaborates to the Π-type `(n : ℕ) → P n`, distinguish `Prop` from `Type u` in the `Sort` hierarchy, and explain proof irrelevance and the large-elimination restriction and why they matter.
- Define and use `structure` (bundled data-with-proofs / dependent records) and `class` (typeclasses), read a real Mathlib algebraic-hierarchy class (Monoid → Group → Ring → Field, Module R M), and explain instance resolution and the diamond problem.
- Locate the right Mathlib lemma for a goal using the in-editor search tactics `exact?`, `apply?`, `rw?`, `simp?`, the type-shape engine Loogle, and the natural-language engines LeanSearch/Moogle, and reproduce Mathlib's naming convention from a lemma statement.
- Choose and drive the correct automation tactic for a goal — `ring`, `linarith`/`nlinarith`, `omega`, `norm_num`, `field_simp`, `positivity`, `gcongr`, `decide`, `simp [lemmas]`, and the new SMT-style `grind` — and know that `polyrith` is retired and what replaced it.
- Structure multi-step proofs with `calc` blocks and `have`, and define functions by structural recursion (equation compiler) versus well-founded recursion (`termination_by` / `decreasing_by`), knowing when each is required.
- Carry one genuine analysis/algebra theorem (irrationality of √2, AM-GM/Cauchy-Schwarz, or Euler's identity) from statement to kernel-checked proof, and read a minimal `macro`/`elab` example that exposes Lean 4's parse → macro-expand → elaborate → kernel-check pipeline.

## Prerequisites

- Lectures 1–4: untyped and simply-typed λ-calculus, the Curry–Howard correspondence (propositions-as-types), and the first-contact Lean 4 material in notebook 09 (term mode vs tactic mode, the kernel / de Bruijn trust model).
- Mathematical maturity with ordinary proof techniques: induction, proof by contradiction, and basic algebra/analysis (the √2, AM-GM, Cauchy–Schwarz arguments).
- Comfort reading the propositions-as-types dictionary from notebook 08 (P → Q is a function type, P ∧ Q a pair, ∀x.P(x) a Π-type).
- Access to a Lean 4 + Mathlib toolchain (Lean 4.32.x / Mathlib on the matching toolchain) OR the offline fallback: `python -m lambda_lab lean <demo>` and `python -m lambda_lab tutorial`, which display prepared traces when Lean is absent.

## Dependent types in practice: Π-types, Prop vs Type, proof irrelevance

Open by cashing out the Lecture-4 slogan 'Lean is a λ-calculus with dependent types'. The dependent function type `(x : α) → β x` is the single primitive that makes ∀ and → the same connective: a proof of `∀ n : ℕ, P n` IS a function that maps each `n` to a proof of `P n`. Contrast the two universes — `Prop` (proof-irrelevant, one 'truth value' of inhabitation, restricted elimination) vs `Type u` (data, full elimination). Explain proof irrelevance concretely and the large-elimination restriction (you cannot generally pattern-match a `Prop` to build `Type`-level data — this prevents leaking non-computational choices). Reinforce the de Bruijn criterion: a term is trusted only because the small kernel type-checks it; `#print axioms` audits which axioms (propext, Classical.choice, Quot.sound) a proof actually used. This topic reuses notebook 09 verbatim and sets up why structures/typeclasses (next) are just Σ-types with instance search.

**Key definitions**

- Dependent function type (Π-type): `(x : α) → β x`; sugar `∀ x, β x`. The non-dependent arrow `α → β` is the special case where β does not mention x.
- `Sort` hierarchy: `Prop = Sort 0`, `Type u = Sort (u+1)`; a type's type is a universe, universes are cumulative-by-lifting, avoiding Girard's paradox.
- Proof irrelevance: for `p : Prop` and `h₁ h₂ : p`, `h₁` and `h₂` are definitionally equal — proofs carry no data.
- Σ-type / dependent pair `(x : α) × β x` (`Sigma`) and `Subtype {x // p x}`: the data-side dual of Π, the basis of `structure`.

**Key results**

- `theorem and_comm_term {P Q : Prop} : P ∧ Q → Q ∧ P := fun ⟨hp, hq⟩ => ⟨hq, hp⟩` — a pure λ-term proof (notebook 09).
- `theorem modus_ponens {P Q : Prop} : (P → Q) → P → Q := fun f p => f p` — implication elimination is literally application.
- `theorem imp_comp {P Q R : Prop} : (P → Q) → (Q → R) → P → R := fun f g p => g (f p)` — proof composition = function composition (Exercise 9.1).
- de Bruijn criterion: only the kernel is trusted; the other 99% of Lean may be buggy and proofs remain sound; `#print axioms thm` reports the axiom footprint.

## Structures and typeclasses: Mathlib's algebraic hierarchy

A `structure` is a one-constructor inductive — a Σ-type bundling data with proof obligations; a `class` is a `structure` whose instances are found by automatic instance resolution instead of being passed explicitly. Show the progression: a bare `structure Point`, then a `class` with an instance, then how Mathlib stacks classes with `extends` to build Monoid → Group → CommGroup and Semiring → Ring → CommRing → Field, plus `Module R M` as a two-parameter class. Explain that algebraic facts are stated once at the right level of generality (`mul_comm` for any `CommMonoid`) and inherited everywhere. Name the diamond problem (two inheritance paths to the same superclass must give definitionally equal instances) and how Mathlib solves it by making fields explicit / using `where` overrides. Ground the abstraction in the author's L6 artefact, which is built exactly this way.

**Key definitions**

- `structure S where field₁ : τ₁; field₂ : τ₂ …` — desugars to a single-constructor inductive with projections; anonymous constructor `⟨…⟩`.
- `class C (α : Type*) extends D α where op : …; law : …` and `instance : C τ := …` — typeclass + instance, resolved by tabled search over the instance database.
- Mathlib class (current): `class Group (G) extends DivInvMonoid G where inv_mul_cancel : ∀ a : G, a⁻¹ * a = 1` — a Monoid with inverses, one law added on top of the extended structure.
- Bundled vs unbundled hierarchies and the 'diamond' coherence requirement that shared ancestors resolve to definitionally-equal instances.

**Key results**

- Dependent record as a real artefact: `structure EMLRealization (f : PartialFun) where term : EMLTerm; spec : ∀ env, term.eval? env = f env` — bundles a syntax tree with a proof it computes f (eml-formalization, Realization.lean).
- Typeclass abstracting a hypothesis: `class EDLTranscendenceBarrier : Prop where neg_one_not_closed : ¬ EDLClosedVal (-1); two_not_closed : ¬ EDLClosedVal 2; half_not_closed : ¬ EDLClosedVal ((1:ℝ)/2)` — three conjectures packaged so downstream theorems state cleanly (eml, EDLClosedVal.lean).
- Generality payoff: `mul_comm : a * b = b * a` is proved once for `CommMonoid` and applies to ℕ, ℤ, polynomials, matrices-over-comm-rings … via instance resolution.

## The Mathlib architecture: scale, naming, and search

Give students a map of the largest formal-math library in existence and the reflexes to search it — the single biggest practical skill for post-formalisation mathematics. State the current scale, the monorepo/CI social model, and the rigid naming convention that lets you *guess* lemma names (`Nat.Prime.eq_one_or_self_of_dvd` = namespace `Nat.Prime`, then the conclusion in camelCase). Then demo the four search modalities live: (1) `exact?`/`apply?` synthesise a closing/one-step lemma; `rw?` proposes rewrites; `simp?` reveals the simp set it used. (2) Loogle — Breitner's syntactic engine — matches by *shape*, e.g. `Loogle "(_ * _) ^ _"` or by constant/hypothesis pattern. (3) LeanSearch (PKU BICMR) and (4) Moogle (Morph Labs) — neural/NL engines for when you don't know the shape. Frame the trade-off: formal engines are complete and predictable; neural engines are forgiving of vague intent. The √2 tutorial (15b) is the worked search story: `exact?` surfaces `Nat.Prime.irrational_sqrt`.

**Key definitions**

- Mathlib naming convention: lemma names read left-to-right as the statement's shape/conclusion in lowerCamelCase, namespaced by the head symbol (e.g. `Nat.add_comm`, `Finset.sum_range_succ`, `Real.sq_sqrt`).
- `exact?` (formerly `library_search`) and `apply?` — search for a term closing the goal or reducing it by one `apply`; `rw?` — candidate rewrites; `simp?`/`simp only [...] says` — report the exact simp lemmas used.
- Loogle query language: `_`/named holes for subterms, `|- pattern` to match the goal, `⊢`, comma-separated conjunctive constraints, search by constant name, by hypothesis, or by type shape.
- LeanSearch / Moogle — embedding-based semantic search over Mathlib declarations, queried in natural language or informal statements.

**Key results**

- Current scale (mid-2026): Mathlib holds ~351,397 formal declarations and over 2,000,000 lines across a single continuously-integrated monorepo; it supplies ~90% of declarations across the Lean library ecosystem.
- Worked search: goal `Irrational (Real.sqrt 2)` → `exact?`/Loogle returns `Nat.Prime.irrational_sqrt : p.Prime → Irrational (Real.sqrt ↑p)` (tutorial 15b).
- Naming as decoder: from the name alone, `Nat.Prime.eq_one_or_self_of_dvd hp m hm : m = 1 ∨ m = p` is predictable — 'a divisor of a prime equals one or itself' (tutorial 15l).

## The tactic zoo: automation for computation

The heart of the lecture — matching goals to decision/normalisation procedures so students stop hand-rolling algebra. Go tactic-by-tactic with the *goal shape each one owns*: `ring`/`ring_nf` for commutative-(semi)ring identities (no hypotheses used!); `linarith` for linear arithmetic over ordered fields, `nlinarith` for nonlinear goals when fed square hints; `omega` a complete decision procedure for linear integer/nat arithmetic (Presburger); `norm_num` for closed numeric (in)equalities; `field_simp` to clear denominators (dischargers call `norm_num`/`positivity`); `positivity` proves `0 < e` / `0 ≤ e` / `e ≠ 0` structurally; `gcongr` ('generalised congruence') reduces `f a ⋈ f b` to `a ⋈ b` through monotone contexts; `decide` evaluates a `Decidable` proposition to `isTrue`; `simp [lemmas]` rewrites to normal form. Then the 2025–26 update: `grind` (an SMT-style tactic introduced in Lean 4.22.0) ships `cutsat` (supersedes `omega`, with model construction) and a Gröbner-basis solver; the thin wrapper `grobner` closes polynomial goals. Flag prominently that `polyrith` is retired — its external Sage certificate server was shut down — so `grind`/`grobner`/`linear_combination` are the modern polynomial tools. Every claim here is demoed on the author's tutorial proofs.

**Key definitions**

- `ring` — proves identities in any `CommRing`/`CommSemiring` by normal form; uses NO hypotheses. `linear_combination e` — certificate-based equality from a linear combination of hypotheses.
- `linarith`/`nlinarith [hints]` — Positivstellensatz-style search over linear (resp. nonlinear, via provided products/squares) hypotheses. `polyrith` — RETIRED (Sage server shut down).
- `omega` — complete decision procedure for linear arithmetic over ℤ/ℕ. `decide` — reduces a `Decidable` prop by kernel computation. `norm_num` — normalises/closes numeric goals `A = B`, `A ≤ B`, `A ≠ B`.
- `field_simp` (clear denominators), `positivity` (prove positivity/nonneg/nonzero structurally), `gcongr` (monotone congruence), `simp [ℓ…]` (simp-set rewriting), and `grind` / `grobner` (SMT-style, cutsat + Gröbner; Lean 4.22.0+).

**Key results**

- Cauchy–Schwarz for two reals in ONE line: `theorem cs (a b x y : ℝ) : (a*x + b*y)^2 ≤ (a^2 + b^2) * (x^2 + y^2) := by nlinarith [sq_nonneg (a*y - b*x)]` (tutorial 15h).
- AM-GM for two reals: `theorem amgm (a b : ℝ) (ha : 0 ≤ a) (hb : 0 ≤ b) : 2 * Real.sqrt (a*b) ≤ a + b := by nlinarith [sq_nonneg (a - b), Real.sq_sqrt (mul_nonneg ha hb), Real.sqrt_nonneg (a*b)]` (tutorial 15e).
- `decide` on a concrete Decidable statement: Wilson's theorem for a fixed small prime, e.g. `example : Nat.factorial 6 % 7 = 6 := by decide` (tutorial 15j).
- `ring` closes a school identity with zero cleverness: `example (a : ℤ) : (a + 2) * 3 = 3 * a + 6 := by ring` (tutorial 09c).

## calc blocks: structured equational and inequality chains

`calc` lets a proof read like a pen-and-paper derivation: each line names an intermediate term via `_` and justifies one step by a tactic or lemma. It generalises beyond `=`: through the `Trans` typeclass a single `calc` can mix `=`, `≤`, `<`, `∣`, `⊆`, chaining them to the transitive conclusion. Teach the 'Macbeth pattern': alternate `have` (introduce an auxiliary fact) with `calc` (carry the computation), closing the linear tail with `linarith`. This is the readability bridge that convinces working mathematicians the formal text is legible. Draw directly on notebook 09c.

**Key definitions**

- `calc a = b := by t₁\n  _ ≤ c := by t₂\n  _ < d := h₃` — anchored on the first term, each `_` continues from the previous right-hand side.
- `Trans` typeclass — supplies the transitivity instance letting `calc` compose heterogeneous relations (e.g. `=` then `≤` yields `≤`).
- 'Macbeth pattern' — interleave `have hAux : … := by …` with `calc`, then discharge with `linarith`/`ring`.

**Key results**

- Pen-and-paper style: `example (a : ℤ) : (a + 2) * 3 = 3 * a + 6 := by calc (a+2)*3 = a*3 + 2*3 := by ring\n  _ = 3*a + 6 := by ring` (09c).
- Mixed have/calc: `example (a b : ℝ) (h1 : a^2 = b^2 + 4) (h2 : a + b = 2) : a - b = 2 := by\n  have hprod : (a - b) * (a + b) = 4 := by calc (a-b)*(a+b) = a^2 - b^2 := by ring\n    _ = 4 := by linarith\n  … ; linarith` (09c) — the canonical demonstration of chained reasoning.

## Recursion: structural (equation compiler) vs well-founded

Two ways to define functions and prove by induction. Structural recursion: definitions that recurse on strict subterms compile to the auto-generated recursor (`brecOn`); the equation compiler accepts them without a termination proof and generates definitional equation lemmas usable by `simp`/`rw`. Induction proofs (`induction n with | zero => … | succ n ih => …`) are the proof-side mirror. Well-founded recursion: when the decreasing argument is not a literal subterm (e.g. `gcd (y % x) x`), supply `termination_by` (the measure) and `decreasing_by` (a proof it strictly decreases in a well-founded order); Lean builds the definition via `WellFounded.fix`. Contrast `partial def`, which sidesteps the kernel entirely and yields no equation lemmas (fine for tooling, useless for proofs). The author's EMLTerm size/eval functions are the clean structural example; Nat.gcd is the canonical well-founded one.

**Key definitions**

- Structural recursion / equation compiler: `def f | ctor₁ … => …` recursing on subterms; elaborated to the type's recursor, with generated equational lemmas.
- Induction tactic: `induction n with | zero => …  | succ n ih => …` — the eliminator surfaced as a tactic; `ih` is the inductive hypothesis.
- Well-founded recursion: `termination_by <measure>` + `decreasing_by <proof>`; realised through `WellFounded.fix` / `Nat.strongRecOn`.
- `partial def` — bypasses the termination checker and the kernel; produces an opaque function with no defining equations for proofs.

**Key results**

- Structural definition + `omega`: `def EMLTerm.size : EMLTerm → Nat | one => 1 | var _ => 1 | eml a b => 1 + size a + size b` and `lemma size_pos : ∀ t, 1 ≤ t.size` closed structurally / by `omega` (eml, Term.lean).
- Induction + ring (Gauss's sum): `theorem gauss_sum (n : Nat) : 2 * (∑ k ∈ Finset.range (n+1), k) = n * (n+1) := by induction n with | zero => simp | succ n ih => rw [Finset.sum_range_succ, Nat.mul_add, ih]; ring` (tutorial 15a).
- Well-founded gcd: `Nat.gcd 0 y = y`, `Nat.gcd (succ x) y = gcd (y % succ x) (succ x)` terminates because `y % succ x < succ x`; the same computation yields Bézout witnesses `Nat.gcdA/gcdB` with `Nat.gcd_eq_gcd_ab a b : gcd a b = a * gcdA a b + b * gcdB a b` (tutorial 15g).

## A worked proof end-to-end, plus a taste of macros and elaboration

Close by carrying one theorem the whole way and then lifting the curtain on how Lean turns your text into a kernel term. Worked proof — pick the √2 story (15b): the professional one-liner cites Mathlib (`exact_mod_cast Nat.Prime.irrational_sqrt Nat.prime_two`), and the from-scratch version opens with `by_contra`, extracts a rational witness, and derives an even/odd contradiction — showing both 'stand on the library' and 'build it yourself'. Euler's identity (15k) is an alternative crowd-pleaser where all the analytic depth hides inside one lemma. Metaprogramming taster: Lean 4 is written in Lean 4, and user code runs at every stage of the pipeline — parser (`syntax`) → macro expansion (`macro`/`macro_rules`, purely syntactic) → elaboration (`elab`, syntax → `Expr` in `MetaM`/`TermElabM`) → kernel type-check. Show a 3-line tactic macro and mention that Mathlib's own tactics (and the author's 'direct-macro alternative witnesses' in eml, AlternativeWitnesses.lean) are exactly this. End on the punchline: term mode and tactic mode both produce the *same* `Expr`, and only the kernel's acceptance makes it a theorem.

**Key definitions**

- `by_contra h` — classical contradiction: assume `¬goal`, drive to `False`. `exact_mod_cast` / `push_cast` — bridge coercions ↑ between ℕ, ℤ, ℚ, ℝ.
- `Expr` — Lean's kernel term datatype (bvar/fvar/const/app/lam/forallE/…); tactics and macros ultimately build `Expr` values checked by the kernel.
- `syntax`, `macro`, `macro_rules`, `notation` (syntactic layer) vs `elab`/`elab_rules` (semantic layer producing `Expr`); monads `MacroM`, `MetaM`, `TermElabM`, `TacticM`.
- The elaboration pipeline: parse → macro-expand → elaborate → kernel type-check; `#check`, `#eval`, `#print axioms` as introspection commands.

**Key results**

- Library-standing proof: `theorem sqrt2_irrational : Irrational (Real.sqrt 2) := by exact_mod_cast Nat.Prime.irrational_sqrt (p := 2) Nat.prime_two` (tutorial 15b).
- Analytic depth in one lemma: `theorem euler_identity : Complex.exp (Real.pi * Complex.I) + 1 = 0 := by rw [Complex.exp_pi_mul_I]; ring` (tutorial 15k).
- A user tactic macro: `macro "split_and" : tactic => `(tactic| refine ⟨?_, ?_⟩)` — three lines add a new tactic; after expansion it is ordinary `Expr`-building, kernel-checked like everything else.
- Kernel-as-sole-arbiter, at scale: the L6 eml-formalization compiles in 8,062 `lake` kernel jobs with `sorry`/`admit` = 0, audited by `#print axioms` — the de Bruijn criterion applied to a real research artefact.

## Pedagogical arc
"A ~90-minute session, roughly 60% live coding at the projector, 40% narrated slides, using either a real Lean+Mathlib install or the lambda_lab fallback traces. (0–10 min) Recap Lecture 4 through notebook 09: Lean = λ-calculus + dependent types; prove `and_comm` in term and tactic mode, then run `#print axioms` to show they compile to the same kernel-checked term — establish the de Bruijn trust model. (10–25) Dependent types in practice: Π-types, `∀ n, P n` = `(n:ℕ)→P n`, Prop vs Type, proof irrelevance and large elimination, Σ/Subtype — using the propositions-as-types table from notebook 08. (25–40) Structures and typeclasses: build a bare `structure`, then a `class` + `instance`, watch instance resolution fire; sketch Mathlib's Monoid→Group→Ring→Field tower and the diamond problem; preview the L6 artefact's `EMLRealization` structure and `EDLTranscendenceBarrier` class. (40–52) Mathlib architecture and search: state the scale (~351k declarations, >2M lines), decode a lemma name, then live-demo `exact?`/`apply?`/`rw?`/`simp?`, a Loogle shape query, and a LeanSearch natural-language query — hunting down `Nat.Prime.irrational_sqrt`. (52–68) The tactic zoo: run Cauchy–Schwarz (`nlinarith [sq_nonneg …]`) and AM-GM live, then rapid-fire `ring`, `omega`, `norm_num`, `field_simp`, `positivity`, `gcongr`, `decide`; explicitly flag that `polyrith` is retired and demo `grind`/`grobner` on a polynomial goal. (68–78) calc + recursion: the Macbeth have/calc pattern (09c); structural recursion via `EMLTerm.size` (closed by `omega`) versus well-founded `Nat.gcd` with `termination_by`/`decreasing_by`, and Gauss's sum by `induction`. (78–88) One real proof end-to-end — √2 irrational, both the Mathlib one-liner and the `by_contra` sketch (15b) — followed by a 3-line tactic `macro` and the parse→macro→elaborate→kernel pipeline diagram. (88–90) Bridge to Lecture 6: the eml-formalization is precisely this toolkit at research scale — 8,062 kernel jobs, sorry-free, `#print axioms`-audited — and gestures at the AI frontier (Aristotle, Erdős #728) that L6 explores."

## Connections to existing material
"Direct reuse from falenty-2026/book/en/notebooks: 09_lean_first_steps.md (term vs tactic mode, dependent types, kernel/de Bruijn — the lecture's opening 10 min); 09b_natural_number_game.md (induction, rw, add_comm via MyNat — structural-recursion warm-up); 09c_macbeth_mechanics_of_proof.md (calc blocks, the have/calc Macbeth pattern, Trans). Tactic-zoo and worked-proof demos come straight from the 15* tutorial series: 15a_tutorial_gauss.md (induction + ring), 15b_tutorial_sqrt2.md (by_contra, exact_mod_cast, Nat.Prime.irrational_sqrt — also the canonical search story), 15e_tutorial_amgm.md and 15h_tutorial_cauchy_schwarz.md (nlinarith with sq_nonneg hints), 15g_tutorial_bezout.md (Nat.gcd_eq_gcd_ab, well-founded gcd / extended Euclid), 15j_tutorial_wilson.md (decide on a Decidable prop), 15k_tutorial_euler.md (rw + ring, Complex.exp_pi_mul_I), 15l_tutorial_heroic_ii.md (dot notation, Nat.Prime interface-over-definition). Foundations for the dependent-types topic reuse 08_curry_howard.md and 10d_curry_howard_playground.md, and 07_peano_preview.md for induction. lambda_lab commands invoked live: `python -m lambda_lab lean <demo>` (demos and_comm, imp_comp, term_proofs, macbeth_calc/calc, nng_addition, erdos_728), `python -m lambda_lab tutorial` (the 15a–15l chapters with progress tracking), `curry_howard` (curry_howard/lean_verify.py, lean_bridge.py — Prop-as-type), and `peano`. For Lecture 6, this lecture is the on-ramp to eml-formalization: EML/Term.lean (`inductive EMLTerm`, structural `size`/`eval`, `size_pos` by omega) exemplifies dependent types + structural recursion; Framework/Realization.lean (`structure EMLRealization` = dependent record bundling a term with its correctness proof) and Framework/EDLClosedVal.lean (`class EDLTranscendenceBarrier : Prop`) exemplify structures/typeclasses; Framework/AlternativeWitnesses.lean ('direct-macro alternative witnesses') and Framework/KCounting.lean (rfl/#eval-checked tree sizes) exemplify metaprogramming; and README.md/DASHBOARD.md supply the scale story (Mathlib v4.28, 8,062 lake jobs, 0 sorry, #print axioms audit) that makes the de Bruijn criterion concrete. Notebook 10b_aristotle_and_ai_math.md and the `lean erdos_728` demo pre-stage the AI/automation thread that Lecture 6 develops."

## Artifact ideas

- **Lean 4** (easy): Prove `∀ P Q : Prop, P ∧ Q → Q ∧ P` twice — once as a bare term `fun ⟨hp,hq⟩ => ⟨hq,hp⟩`, once with `obtain`/`constructor`/`exact` — then run `#print axioms` on both and confirm the axiom footprint is empty and identical. Teaches: term vs tactic mode collapse to the same kernel term.
- **Lean 4** (easy): Define `inductive Tree | leaf | node : Tree → Tree → Tree`, a structurally-recursive `def size : Tree → Nat`, and prove `theorem size_pos (t : Tree) : 1 ≤ t.size` by structural induction closing each case with `omega`. (Mirrors eml Term.lean.)
- **Lean 4** (easy-medium): Tactic-selection drill on one page: prove `example (a b x y : ℝ) : (a*x+b*y)^2 ≤ (a^2+b^2)*(x^2+y^2) := by nlinarith [sq_nonneg (a*y-b*x)]`; `example (n : Nat) : 2*(∑ k ∈ Finset.range (n+1), k) = n*(n+1) := by induction n with | zero => simp | succ n ih => rw [Finset.sum_range_succ, Nat.mul_add, ih]; ring`; and `example : Nat.factorial 6 % 7 = 6 := by decide`. One goal per tactic family (nlinarith, induction+ring, decide).
- **Lean 4** (medium): calc challenge: `example (a b : ℝ) (h1 : a^2 = b^2 + 4) (h2 : a + b = 2) : a - b = 2`, forcing a `have … := by ring`/`calc`/`linarith` chain in the Macbeth pattern (from notebook 09c).
- **Lean 4** (medium): Search skill: state `theorem sqrt2 : Irrational (Real.sqrt 2)` with `sorry`, use `exact?` and/or Loogle to discover `Nat.Prime.irrational_sqrt`, then finish `exact_mod_cast Nat.Prime.irrational_sqrt Nat.prime_two`. Deliverable includes the Loogle query used.
- **Lean 4** (medium): Typeclass build: `class MyAddMonoid (α : Type*) where zero : α; add : α → α → α; add_zero : ∀ a, add a zero = a; zero_add : ∀ a, add zero a = a`, give the `Nat` instance, and prove a lemma stated only from the class interface (`∀ a : α, add (add a zero) zero = a`). Teaches instance resolution and interface-over-definition.
- **Lean 4** (medium-hard): Well-founded recursion: define `def mygcd : Nat → Nat → Nat` with the Euclid step `mygcd (y % (x+1)) (x+1)`, supply `termination_by`/`decreasing_by` (needs `Nat.mod_lt`), and prove `theorem mygcd_dvd_left (a b) : mygcd a b ∣ a`. Contrast with a `partial def` version that admits no equation lemmas.
- **Lean 4** (hard): Metaprogramming: write `macro "split_goal" : tactic => `(tactic| refine ⟨?_, ?_⟩)` and use it to prove a conjunction; then write an `elab` command `#mysize` that takes a term and prints its `Expr` head via `Lean.Meta`. Teaches the syntax→macro→elab→Expr pipeline.
- **Rocq (Coq)** (easy-medium): Port artifact #2: `Inductive tree := leaf | node : tree -> tree -> tree.` with `Fixpoint size (t:tree) : nat` and `Lemma size_pos : forall t, 1 <= size t`, closed by `induction t; simpl; lia.` — the same structural-recursion idea in a second prover, with `lia` playing omega's role.
- **Agda** (medium): Dependent types made visible: `data Vec (A : Set) : ℕ → Set` with `_++_ : Vec A m → Vec A n → Vec A (m + n)`, showing the return type depends on the length index — the phenomenon Lean's Π-types encode. Optionally prove `length (xs ++ ys) ≡ length xs + length ys` by definitional computation.
- **Mizar** (hard): Structures theme in Mizar's set-theoretic idiom: use the built-in `struct` / algebraic structure machinery to state and prove commutativity of the group operation in a `commutative Group`, illustrating how a different foundation (Tarski–Grothendieck set theory, no dependent types) packages the same 'data + axioms' bundle that Lean's `class` provides.

## Pitfalls / misconceptions

- Confusing `Prop` with `Type`: trying to `cases`/pattern-match a proof of an existential in `Prop` to extract computational data into `Type` — blocked by the large-elimination restriction (proof irrelevance would otherwise leak).
- Assuming `=` (propositional equality), `↔`, and definitional equality (`rfl`) are interchangeable; `rfl` only closes goals true by computation/definition, not every true equation.
- Expecting `ring` to use hypotheses — it proves identities in the free commutative ring and ignores context; hypothesis-driven equalities need `linear_combination`, `nlinarith`, or `field_simp` + `ring`.
- Firing `linarith` at a nonlinear goal: it only handles linear arithmetic; nonlinear goals need `nlinarith` fed the right square hints (e.g. `sq_nonneg (a-b)`) or `polyrith`'s replacement.
- Reaching for `polyrith` (retired — its external Sage certificate server was shut down) instead of the current tools `grind`/`grobner`/`linear_combination`.
- Overusing `simp` and hitting nonterminating or goal-changing rewrites; forgetting that `simp?` (and `simp only [...] says`) reveal and pin the exact lemma set for a robust proof.
- Believing a tactic-mode proof is somehow weaker or different from a term-mode proof; after elaboration both are the identical kernel-checked `Expr` — and only the kernel's acceptance confers theoremhood.
- Coercion blindness: mixing ℕ/ℤ/ℚ/ℝ and being surprised by `↑` arrows; goals often need `push_cast`, `norm_cast`, or `exact_mod_cast` to align types.
- Typeclass friction: 'failed to synthesize instance' from a missing `import`/`open`, an unregistered instance, or a diamond where two inheritance paths give non-defeq instances.
- Recursion traps: expecting structural recursion on a non-subterm argument (needs well-founded `termination_by`/`decreasing_by`); or using `partial def`, which escapes the kernel and generates no equation lemmas, so nothing about it can be proved.
- Guessing Mathlib lemma names from memory instead of searching; the library is ~351k declarations — `exact?`, Loogle, and LeanSearch are the intended workflow, not rote recall.
- Dependent-rewrite surprises: `rw` failing with 'motive is not type correct' when the rewritten term appears in a type/index — a cue to use `simp only`, `conv`, or `subst` instead.

## Canonical references

- J. Avigad, K. Buzzard, R. Y. Lewis, P. Massot, *Mathematics in Lean* (release v4.19.0, 11 Jun 2026), Lean community. — <https://leanprover-community.github.io/mathematics_in_lean/>  
  _The standard hands-on course for doing real mathematics in Lean 4 + Mathlib; dependent types, structures/classes, and the tactic zoo are all introduced against live Mathlib. Primary lecture backbone for the analysis/algebra material._
- J. Avigad, L. de Moura, S. Kong, S. Ullrich, *Theorem Proving in Lean 4*, Lean community (continuously updated). — <https://leanprover.github.io/theorem_proving_in_lean4/>  
  _The authoritative reference for dependent type theory in Lean 4 — Π-types, the Prop/Type universe hierarchy, proof irrelevance, structures, typeclasses, and instance resolution. Grounds Topics 1–2 rigorously._
- H. Macbeth, *The Mechanics of Proof* (Fordham University, 2023, updated for Lean 4 + Mathlib). — <https://hrmacbeth.github.io/math2001/>  
  _The gentlest route into calc, have, rw, linarith, ring, induction for a mathematically mature audience; every proof appears in prose and Lean. Directly reused by notebook 09c and the 15* tutorial series._
- H. Macbeth, *Algebraic Computations in Lean* (Fordham University). — <https://hrmacbeth.github.io/computations_in_lean/>  
  _The dedicated reference for the computation-tactic zoo — field_simp, ring, nlinarith, linear_combination, norm_num, positivity — with idioms for combining them. Core source for Topic 4._
- A. Baanen, A. Bentkamp, J. Hölzl, J. Limperg, et al., *Metaprogramming in Lean 4*, Lean community. — <https://leanprover-community.github.io/lean4-metaprogramming-book/>  
  _The book for the macros/elaboration taster: syntax, macro/macro_rules, elab, the Expr datatype, and the MetaM/TermElabM/TacticM monads underpinning the parse→elaborate→kernel pipeline. Source for Topic 8._
- Lean community, 'Searching for theorems in Mathlib' (community blog) + Loogle (J. Breitner, Lean FRO) and LeanSearch (PKU BICMR). — <https://leanprover-community.github.io/blog/posts/searching-for-theorems-in-mathlib/>  
  _Canonical explanation of the three search modalities (exact?/apply?/rw?, Loogle syntactic search, LeanSearch/Moogle neural search) and when to use each — the practical skill of Topic 3._
- Mathlib4 API documentation (auto-generated), incl. Mathlib.Tactic.Polyrith and Init.Grind.Tactics. — <https://leanprover-community.github.io/mathlib4_docs/Mathlib/Tactic/Polyrith.html>  
  _Load-bearing for current tactic status: the Polyrith page states it is no longer supported (Sage server shut down); the grind/grobner docs describe the SMT-style replacement (cutsat superseding omega, Gröbner solver). Primary URL for the L4 tactic facts._
- Lean FRO, Lean 4 release notes (v4.22.0 introducing grind; v4.30.0–v4.32.0, 2026) and 'Mathlib: A Foundation for Formal Mathematics' use-case page. — <https://lean-lang.org/doc/reference/latest/releases/>  
  _Anchors the volatile version/scale facts: latest stable Lean 4.32.0 (2026-07-13), grind introduced in 4.22.0, and Mathlib's 'over two million lines'. Needed to state current numbers accurately._

## Volatile facts (sent to fact-check)

- The latest stable Lean release is Lean 4.32.0 (2026-07-13), with Lean 4.33.0-rc1 (2026-07-15) in the release-candidate channel; recent stable line includes 4.30.0 (2026-05-26) and 4.31.0 (2026-06-13). (src: https://lean-lang.org/doc/reference/latest/releases/)
- Mathlib comprises over two million lines of formalized mathematics; recent measurements (Mathlib versions 4.27–4.29) put it at roughly 351,397 formal declarations, ~90% of all declarations across the surveyed Lean library ecosystem. (src: https://lean-lang.org/use-cases/mathlib/)
- The `polyrith` tactic is no longer supported in Mathlib: its external Sage certificate server was shut down, so it is effectively retired (could be revived only with a new backend). (src: https://leanprover-community.github.io/mathlib4_docs/Mathlib/Tactic/Polyrith.html)
- Lean's SMT-style `grind` tactic (introduced in Lean 4.22.0, 2025-08-14) ships theory solvers including `cutsat` (superseding `omega`, with model construction) and a Gröbner-basis solver; the `grobner` tactic is a thin wrapper enabling only that solver. (src: https://lean-lang.org/doc/reference/latest/releases/v4.22.0/)
- Three complementary Mathlib search engines are current: Loogle (Joachim Breitner / Lean FRO, syntactic shape search), LeanSearch (PKU BICMR, neural/semantic), and Moogle (Morph Labs, embedding-based, now somewhat dated), alongside the in-editor `exact?`/`apply?`/`rw?` tactics. (src: https://leanprover-community.github.io/blog/posts/searching-for-theorems-in-mathlib/)
