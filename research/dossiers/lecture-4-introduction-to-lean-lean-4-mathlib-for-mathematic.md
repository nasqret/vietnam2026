# Lecture 4 — Introduction to Lean (Lean 4 + Mathlib for mathematicians)

> A hands-on first contact with the Lean 4 proof assistant: proofs as kernel-checked λ-terms, term vs tactic mode, Prop vs data, induction/rewriting on Nat, the beginner tactic set, and one honest end-to-end proof — with NNG4 and Macbeth's "Mechanics of Proof" as the on-ramp.

## Learning objectives

- Read and write the SAME theorem in both term mode (a pure λ-term, e.g. `fun ⟨hp,hq⟩ => ⟨hq,hp⟩`) and tactic mode (a `by` script), and explain why both elaborate to one term that the small trusted kernel checks (the de Bruijn criterion).
- Distinguish `Prop` (proof-irrelevant propositions) from `Type`/data, and fluently use the Curry-Howard dictionary — `→` as a function, `∧` as a structure/pair, `∃` as a dependent pair — to build and destructure proofs with `intro`, `exact`, `apply`, `constructor`, `rcases`/`obtain`.
- Prove statements about `Nat` by structural induction (`induction n with | zero => _ | succ k ih => _`) and close goals with `rfl`, `rw` (including reverse `rw [← h]`) and `simp` — reproducing `add_comm` from `add_succ`/`succ_add` and understanding why `add_zero` is `rfl` but `zero_add` needs induction.
- Discharge arithmetic goals with the right automation — `decide` (evaluate a `Decidable` instance), `omega` (linear integer/nat arithmetic), and a first look at `ring`/`linarith` — and know each one's scope and failure modes.
- Set up and run a real Lean 4 + Mathlib project: install with `elan`, build with `lake`, pull the prebuilt library cache (`lake exe cache get`), pin the toolchain via `lean-toolchain`, and use `#check`/`#eval`/`#print axioms` plus the VS Code InfoView to inspect the live proof state.
- Complete one honest end-to-end proof (Gauss's sum by induction) AND the complementary 'library-driven corollary' idiom (cite a Mathlib lemma such as `Nat.exists_infinite_primes` or `Nat.Prime.irrational_sqrt`), then continue independently in the Natural Number Game 4 and Macbeth's 'The Mechanics of Proof'.

## Prerequisites

- Lambda calculus basics (abstraction, application, β-reduction) — falenty-2026 notebooks 02–06
- The Curry-Howard correspondence at an intuitive level (proofs = programs, types = propositions) — notebook 08
- Peano axioms and proof by mathematical induction — notebook 07
- Propositional and first-order logic: connectives ∧ ∨ → ¬, quantifiers ∀ ∃
- Comfort with functional programming ideas (functions as values, pattern matching, recursion)
- A laptop able to install Lean 4 via elan + VS Code (or willingness to use the browser-only NNG4 for the interactive part)

## Two modes, one term: term mode vs tactic mode and the trusted kernel

The opening beat and the whole conceptual payoff of arriving from the λ-calculus lectures: Lean 4 IS a λ-calculus with dependent types, a proof is literally a term, and 'tactic mode' is just a metaprogram that BUILDS such a term. Show both versions of the same lemma side by side, then reveal the underlying term (via `#print` / `pp.all`). Tie trust to the de Bruijn criterion: a small type-checking kernel is the only thing that must be correct; the other ~99% of Lean may have bugs and proofs stay sound. This directly extends notebook 08 (Curry-Howard) and 09 (Lean first steps).

**Key definitions**

- Term mode: writing the proof directly as a λ-term inhabiting the goal type, e.g. `theorem modus_ponens {P Q : Prop} : (P → Q) → P → Q := fun f p => f p`
- Tactic mode: a `by ...` block whose tactics (a proof-producing metaprogram) elaborate to a term; e.g. `by intro f p; exact f p`
- The kernel / de Bruijn criterion: a small trusted type-checker verifies the final term has the stated type; correctness does not depend on the elaborator or tactics being bug-free
- `Sort u`, `Prop = Sort 0`, `Type = Sort 1`: the universe hierarchy in which propositions and data both live as types

**Key results**

- `theorem and_comm_term {P Q : Prop} : P ∧ Q → Q ∧ P := fun ⟨hp, hq⟩ => ⟨hq, hp⟩` and the tactic twin `theorem and_comm_tac {P Q : Prop} (h : P ∧ Q) : Q ∧ P := by obtain ⟨hp, hq⟩ := h; constructor; · exact hq; · exact hp` compile to the SAME term (from proofs/lean/and_comm.lean)
- `theorem modus_ponens {P Q : Prop} : (P → Q) → P → Q := fun f p => f p` — modus ponens is literally function application
- Combinators as proofs: `k_combinator : P → Q → P := fun p _ => p`; `s_combinator : (P → Q → R) → (P → Q) → P → R := fun f g p => f p (g p)` (from term_proofs.lean) — the S,K seen in the λ-calculus lectures reappear as propositional tautologies

## Propositions vs data: Prop, proof irrelevance, and the Curry-Howard dictionary in dependent type theory

The load-bearing distinction that trips up every mathematician: `P : Prop` is proof-irrelevant (any two proofs of `P` are equal) and cannot in general be eliminated to produce data, whereas `Nat : Type` carries information. Present the dictionary concretely as datatypes: `And` is a two-field structure, `Exists`/`Sigma` is a dependent pair, `Iff` is a pair of implications. The punchline students remember: `∃` is not a mystical quantifier, it is a pair type whose constructor is `⟨witness, proof⟩` and whose eliminator is destructuring.

**Key definitions**

- `Prop`: the universe of propositions; definitionally proof-irrelevant — `h1 h2 : P` gives `h1 = h2`
- `And P Q` (`P ∧ Q`): a structure with fields `left : P`, `right : Q`; introduced by `⟨_, _⟩`/`constructor`, eliminated by `.left`/`.right`/`rcases`
- `Exists (fun x => p x)` (`∃ x, p x`): dependent pair; introduced by `⟨w, hw⟩`, eliminated by `obtain ⟨w, hw⟩ := h`
- `Iff P Q` (`P ↔ Q`): structure bundling `mp : P → Q` and `mpr : Q → P`
- Definitional equality: `2 ∣ n` unfolds to `∃ k, n = 2 * k` — the same proposition, no lemma needed

**Key results**

- `theorem exists_sq_four_term : ∃ n : Nat, n ^ 2 = 4 := ⟨2, rfl⟩` — the proof is the pair (witness 2, proof by reflexivity) (from exists_square.lean)
- `theorem tutorial_two_dvd_iff (n : Nat) : 2 ∣ n ↔ ∃ k, n = 2 * k := by constructor; · intro h; exact h; · intro ⟨k, hk⟩; exact ⟨k, hk⟩` — both directions are near-identical because the two sides are definitionally equal (from notebook 15b)
- The Curry-Howard table (notebook 08): Proposition↔Type, Implication `P→Q`↔function type, Proof of `P`↔term of type `P`, `P∧Q`↔pair, `P∨Q`↔`Either`, `∀x.P(x)`↔dependent function `(x:α)→P x`

## Nat, structural induction, and recursion (the Peano payoff)

Bridges directly from notebook 07 (Peano axioms via Church encoding) into the real thing. `Nat` is an inductive type with two constructors `zero` and `succ`; the induction principle is the automatically-generated recursor `Nat.rec`. Motivate why `add` recurses on its SECOND argument (this is exactly why `add_zero` is `rfl` but `zero_add` is not — a subtlety students must feel, not just be told). The Natural Number Game reconstructs this from scratch on a private copy `MyNat`, which is the ideal 20-minute live segment.

**Key definitions**

- `inductive Nat where | zero : Nat | succ : Nat → Nat` — Peano's zero and successor as data constructors
- The `induction n with | zero => ... | succ k ih => ...` tactic: splits a goal into base case and successor step, giving the induction hypothesis `ih` in the successor branch
- Structural recursion: `def add : MyNat → MyNat → MyNat | m, .zero => m | m, .succ n => .succ (add m n)` (recursion on the second argument)
- Peano axioms 1–5 (notebook 07): `0 ∈ ℕ`; `S : ℕ → ℕ`; `S n ≠ 0`; `S` injective; induction

**Key results**

- `theorem add_zero (m : MyNat) : m + 0 = m := rfl` — holds by definition (base of the `add` recursion)
- `theorem zero_add (n : MyNat) : 0 + n = n := by induction n with | zero => rfl | succ k ih => show MyNat.succ (0 + k) = MyNat.succ k; rw [ih]` — needs induction precisely because `add` does not recurse on the first argument
- `theorem add_comm (m n : MyNat) : m + n = n + m := by induction n with | zero => rw [add_zero, zero_add] | succ k ih => rw [add_succ, succ_add, ih]` — the classic NNG milestone (all from proofs/lean/nng_addition.lean)
- `theorem add_assoc (a b c : MyNat) : (a + b) + c = a + (b + c)` by induction on `c`

## Rewriting: rfl, rw, and simp

The everyday mechanics of equational reasoning, and the single most confusing cluster for beginners. `rfl` closes only definitional/reflexive equalities; `rw [h]` rewrites the goal left-to-right by an equation and fails if the LHS does not appear syntactically (or with a 'motive is not type correct' error); `rw [← h]` rewrites right-to-left; `simp` normalizes using the whole `@[simp]` lemma set and is non-directional. Show the exact ordering discipline of `rw [add_succ, succ_add, ih]` and contrast with `simp` closing the Gauss base case automatically.

**Key definitions**

- `rfl`: proves `a = a` when both sides are definitionally equal (reduces to the same normal form)
- `rw [h]` / `rw [h₁, h₂, ...]`: rewrite occurrences of the LHS of each equation with its RHS, left-to-right; `rw [← h]` uses the equation in reverse
- `simp` / `simp only [lemmas]`: repeatedly rewrite with the simp-set (lemmas tagged `@[simp]`) until no rule applies; `simp` also does definitional/arithmetic simplification
- `@[simp]` attribute: registers a lemma (e.g. `add_zero`, `zero_add`) as a default rewrite rule

**Key results**

- Base case of Gauss's sum: `| zero => simp` — `simp` knows `∑ k ∈ Finset.range 1, k = 0` and closes `0 = 0*1` (notebook 15a)
- Inductive step chaining rewrites: `rw [Finset.sum_range_succ, Nat.mul_add, ih]; ring` (Gauss, notebook 15a)
- Reverse rewrite in practice: `have h3 : (a - b) * 2 = 4 := by rw [← h2]; exact hprod` (macbeth_calc.lean)
- `add_right_comm (a b c) : (a + b) + c = (a + c) + b := by rw [add_assoc, add_comm b c, ← add_assoc]` — a pure `rw` chain, no induction (nng_addition.lean)

## The beginner tactic vocabulary: rfl, exact, intro, apply, rcases/obtain, constructor, induction

A tight reference set that covers >90% of first proofs. Frame each tactic by the shape of goal it attacks: `intro` for `→`/`∀`, `exact`/`apply` to finish/backward-chain, `constructor`/`⟨_,_⟩` for `∧`/`∃`/structures, `rcases`/`obtain` to destructure hypotheses, `induction` for inductive types. `obtain` is sugar over `rcases`. Keep each demo to a two-to-four-line proof so the InfoView goal state is legible.

**Key definitions**

- `intro h`: move a `→`/`∀` premise into the context as a hypothesis (matches `fun h => ...` in term mode)
- `exact e`: close the goal with a term `e` of exactly the goal type; `apply f`: use `f` and leave its premises as new goals (backward reasoning)
- `rcases h with ⟨a, b⟩` / `obtain ⟨a, b⟩ := h`: destructure a conjunction/existential/structure into named pieces
- `constructor`: apply the (unique) constructor of the goal's inductive type, splitting `∧`/`↔` into subgoals
- `cases` / `induction`: case-split or induct on an inductive value

**Key results**

- `theorem imp_comp {P Q R : Prop} : (P → Q) → (Q → R) → P → R := by intro f g p; exact g (f p)` — versus the term `fun f g p => g (f p)` (Exercise 9.1, notebook 09)
- `theorem tutorial_prime_above (N : Nat) : ∃ p, N < p ∧ p.Prime := by obtain ⟨p, hN, hp⟩ := Nat.exists_infinite_primes (N + 1); exact ⟨p, by omega, hp⟩` (notebook 15d)
- `and_comm_tac`: `obtain ⟨hp, hq⟩ := h; constructor; · exact hq; · exact hp` (and_comm.lean)

## Arithmetic automation: decide and omega (with a peek at ring / linarith)

Where beginners either fall in love or get burned. `decide` runs a `Decidable` instance and can prove concrete closed goals by evaluation (but blows up or fails on non-`Decidable`/open goals). `omega` is a complete decision procedure for LINEAR arithmetic over `Int`/`Nat` (Presburger fragment) — it will NOT do nonlinear goals. `ring` proves commutative-(semi)ring identities; `linarith`/`nlinarith` handle linear/nonlinear inequalities from hypotheses. Teaching the SCOPE of each is the point — the misconception 'just try omega/decide on everything' is a real time sink.

**Key definitions**

- `decide`: closes a goal by evaluating its `Decidable` instance to `isTrue`; needs the proposition to be decidable and small enough to compute
- `omega`: decision procedure for linear integer/natural arithmetic (equalities, inequalities, divisibility by literals); does not handle multiplication of variables
- `ring` / `ring_nf`: proves/normalizes identities in commutative (semi)rings
- `linarith` / `nlinarith`: close linear / (heuristically) nonlinear arithmetic goals from a set of hypotheses and hints

**Key results**

- `theorem exists_sq_four_tac : ∃ n : Nat, n ^ 2 = 4 := by refine ⟨2, ?_⟩; decide` — vs the term proof `⟨2, rfl⟩` (exists_square.lean)
- `omega` promoting `N + 1 ≤ p` to `N < p` inside `tutorial_prime_above` (notebook 15d)
- `ring` finishing polynomial dust in the Gauss inductive step and every `calc` line of `(a + 2) * 3 = 3 * a + 6` (macbeth_calc.lean)
- `example (a : ℝ) : (a + 1) ^ 2 ≥ 2 * a + 1 := by ... nlinarith [sq_nonneg a]` — an inequality closed with one hint (macbeth_calc.lean)

## Tooling: elan, lake, Mathlib as a library, and #check/#eval

The unglamorous but decisive half of 'introduction to Lean'. `elan` manages toolchains (pinned per project by a `lean-toolchain` file), `lake` is the build tool and package manager, and Mathlib is added as a dependency in `lakefile.toml`; the crucial move is `lake exe cache get`, which downloads prebuilt `.olean` files so students do NOT recompile ~300k theorems (hours) on a laptop. Live-demo `#check`, `#eval`, `#print axioms` and the VS Code InfoView, and how to search Mathlib (`exact?`, `apply?`, `rw?`, and Loogle/Moogle). Note the real version skew in the author's own repos (see current_facts) as a teachable 'pin your toolchain' lesson.

**Key definitions**

- `elan`: the Lean toolchain manager (analogue of rustup); `lean-toolchain` file pins the exact compiler, e.g. `leanprover/lean4:v4.30.0-rc2`
- `lake`: Lean's build system / package manager; project config in `lakefile.toml`
- Mathlib dependency block: `[[require]] name = "mathlib"  scope = "leanprover-community"` (from the author's lakefile.toml)
- `lake exe cache get`: fetch prebuilt Mathlib artifacts instead of compiling from source
- `#check e` (report the type/elaboration of `e`), `#eval e` (run `e`), `#print axioms name` (audit the axioms a proof depends on)

**Key results**

- The author's working project pins `leanprover/lean4:v4.30.0-rc2` with `[leanOptions] autoImplicit = false`, `relaxedAutoImplicit = false` (proofs/lean/lakefile.toml + lean-toolchain) — a clean, reproducible beginner setup
- `#eval` gives Lean a REPL feel: `#eval 2 ^ 10` → `1024`; `#check Nat.add_comm` shows `∀ (n m : ℕ), n + m = m + n`
- `#print axioms` on the EML formalization returns a clean list (no `sorry`) — the trust audit students should learn to run (README, eml-formalization)

## A first honest end-to-end proof — and where to go next (NNG4, Macbeth)

Close the session with ONE complete, self-contained proof done live (Gauss's sum by induction), then contrast it with the 'library-driven corollary' idiom — cite a Mathlib lemma and adapt it — so students leave with both mental models: 'I can build a proof' AND 'the right move is often to find the lemma'. Then hand off to the two best self-study ramps: play NNG4's Addition World right now (it reconstructs exactly today's `add_comm`), and read Macbeth's 'Mechanics of Proof' for prose-vs-Lean parallel exposition. Preview Lecture 6 (the EML research formalization) as the destination this on-ramp leads to.

**Key definitions**

- 'Honest end-to-end proof': a complete Lean proof of a genuine theorem, verified by the kernel, with no `sorry`
- 'Library-driven corollary': finish a proof by citing a stable Mathlib name and aligning types (the everyday mode of formal mathematics)
- NNG4 world structure: Tutorial (`rfl`,`rw`) → Addition (`induction`, `add_comm`) → Multiplication → Power → Implication → Advanced Addition → ≤ → Algorithm (`decide`)
- Macbeth chapter arc: calculation (`calc`) → structure (`have`,`obtain`) → parity/divisibility → logic → induction → number theory → functions → sets → relations

**Key results**

- `theorem tutorial_gauss_sum (n : Nat) : 2 * (∑ k ∈ Finset.range (n+1), k) = n * (n + 1) := by induction n with | zero => simp | succ n ih => rw [Finset.sum_range_succ, Nat.mul_add, ih]; ring` (notebook 15a) — the live end-to-end proof
- `theorem tutorial_sqrt2_irrational : Irrational (Real.sqrt 2) := by exact_mod_cast Nat.Prime.irrational_sqrt (p := 2) Nat.prime_two` (notebook 15b) — a one-liner on top of Mathlib
- `Nat.exists_infinite_primes : ∀ (n : ℕ), ∃ p, n ≤ p ∧ p.Prime` — the Mathlib name behind Euclid's theorem (notebook 15d)
- Macbeth `calc` idiom: `example (a : ℤ) : (a + 2) * 3 = 3 * a + 6 := by calc (a + 2) * 3 = a * 3 + 2 * 3 := by ring; _ = 3 * a + 6 := by ring`

## Pedagogical arc
"

## Connections to existing material
"This lecture IS the write-up of Part IV of the falenty-2026 book, so it reuses that spine almost verbatim. Core notebooks: book/en/notebooks/09_lean_first_steps.md (term vs tactic mode, and_comm, modus_ponens, the de Bruijn/kernel trust story, Exercise 9.1 imp_comp in both modes); 09b_natural_number_game.md (NNG4 worlds table + the add_comm induction proof); 09c_macbeth_mechanics_of_proof.md (calc/have/linarith style + Macbeth chapter map). Upstream bridges: 08_curry_howard.md (the Curry-Howard table and S/K/composition combinators that reappear as Lean tautologies) and 07_peano_preview.md (Peano axioms + Church encoding motivating inductive Nat). The 'honest end-to-end proof' menu comes from the tutorial notebooks 15a_tutorial_gauss.md (Gauss's sum by induction — the live demo), 15b_tutorial_sqrt2.md (by_contra + the Mathlib one-liner `Nat.Prime.irrational_sqrt`), 15d_tutorial_primes.md (`Nat.exists_infinite_primes` + obtain + omega), plus 15c/15e/15g (pigeonhole, AM-GM/nlinarith, Bézout). Runnable Lean sources to project on screen: lambda_lab/proofs/lean/and_comm.lean, term_proofs.lean, exists_square.lean, imp_comp.lean, congr.lean, nng_addition.lean (MyNat add_zero/zero_add/add_succ/succ_add/add_comm/add_assoc), macbeth_calc.lean, with the real build files lakefile.toml (Mathlib require, autoImplicit=false) and lean-toolchain. Lambda Lab commands that drive the session: `python -m lambda_lab lean and_comm|term_proofs|nng|macbeth|exists_square|imp_comp` (lab/commands/lean.py DEMOS map — runs Lean if installed, else shows a saved trace); `peano` (commands/peano.py) and the curry_howard playground; `tutorial 1`..`tutorial N` (commands/tutorial.py) which chain narrative → `ch explore --live` (inspect the proof TERM as a tree) → a `quiz` checkpoint (e.g. bundle tutorial_01_gauss) → `kb topic mathlib`. For Lecture 6, this lecture is the on-ramp to eml-formalization/ (Lean 4 + Mathlib v4.28, sorry-free, 8062 lake jobs, ~100 public theorems, EMLTerm/EMLTermℂ witness terms audited by `#print axioms`) surfaced via the `eml`/`eml_witnesses` commands (lab/commands/eml.py) and proofs/eml/2603_21852 — i.e. what a genuine research formalization looks like once the basics here are in hand. Depth/structure calibrated against classical-foundations-ann (intro.md + part-by-part JupyterBook layout)."

## Artifact ideas

- **Lean 4** (easy): Exercise 9.1: prove `(P → Q) → (Q → R) → P → R` twice — term mode `fun f g p => g (f p)` and tactic mode `by intro f g p; exact g (f p)` — then `#print` both and observe they are the same term.
- **Lean 4** (easy): `example : ∃ n : Nat, n ^ 2 = 4 := ⟨2, rfl⟩`, then prove the same goal via `by refine ⟨2, ?_⟩; decide`; discuss why `rfl` already works (definitional computation).
- **Lean 4** (medium): On a private `inductive MyNat | zero | succ`, define `add` by recursion on the second argument and prove `zero_add`, `succ_add`, and `add_comm (m n : MyNat) : m + n = n + m` by `induction` + `rw` (reproduce nng_addition.lean; equivalently, clear NNG4 Addition World).
- **Lean 4** (medium): `theorem gauss (n : Nat) : 2 * (∑ k ∈ Finset.range (n+1), k) = n * (n + 1) := by induction n with | zero => simp | succ n ih => rw [Finset.sum_range_succ, Nat.mul_add, ih]; ring` — the honest end-to-end proof.
- **Lean 4** (medium): Library-driven corollary: `theorem prime_above (N : Nat) : ∃ p, N < p ∧ p.Prime := by obtain ⟨p, hN, hp⟩ := Nat.exists_infinite_primes (N + 1); exact ⟨p, by omega, hp⟩` — find the Mathlib lemma with `exact?`, then close with `omega`.
- **Agda** (medium): Curry-Howard in a second system: define `id : A → A`, `k : A → B → A`, `s : (A → B → C) → (A → B) → A → C` as typed terms, and prove `+-comm : (m n : ℕ) → m + n ≡ n + m` by induction — mirroring the Lean `add_comm`.
- **Rocq (Coq)** (easy): `Theorem add_comm : forall n m : nat, n + m = m + n.` proved by `induction n` + `simpl`/`rewrite`/`lia`; plus `Theorem and_comm : forall P Q : Prop, P /\ Q -> Q /\ P.` — the same two exercises in Rocq to contrast tactic vocabularies (`lia` ~ `omega`, `reflexivity` ~ `rfl`).
- **Mizar** (hard): State and prove a first-order tautology (e.g. `P & Q implies Q & P`) or the existence of a natural number whose square is 4 in Mizar's declarative Jaśkowski-style natural deduction, to show a non-tactic, non-Curry-Howard proof style from the Mizar Mathematical Library.

## Pitfalls / misconceptions

- Thinking term mode and tactic mode are two different KINDS of proof. They are not: a `by` block is a metaprogram that builds a λ-term, and the kernel checks that term. Any tactic proof can be `#print`ed as a term.
- Expecting `rfl` to close every equality. `rfl` only proves definitional equalities: `add_zero : m + 0 = m` is `rfl`, but `zero_add : 0 + n = n` is NOT (because `Nat.add` recurses on its second argument) and needs induction. This asymmetry surprises everyone.
- Misusing `rw`: it rewrites strictly left-to-right and fails if the LHS does not appear syntactically (or throws 'motive is not type correct'); forgetting `rw [← h]` for the reverse direction; and reaching for `simp` when a targeted `rw` (with the right lemma order) is what is needed, or vice versa.
- Assuming NNG4's tactic names and syntax transfer verbatim to real Lean 4 + Mathlib. The game deliberately curates a subset and lightly renames things; production Lean uses `induction n with | ... => ...`, full Mathlib lemma names, and `omega`/`ring`/`simp` that the game may hide.
- Treating `Prop` like a data type: expecting to pattern-match on a proof to extract computational data. Propositions are proof-irrelevant (any two proofs are equal) and cannot in general be eliminated into `Type` (the large-elimination restriction).
- Over-trusting automation. `decide` needs a `Decidable` instance and can hang or fail on non-decidable/large goals; `omega` only handles LINEAR integer/nat arithmetic and will not touch `x * y` — nonlinear goals need `ring`/`nlinarith`. 'Just try omega/decide' is a real time sink.
- Underestimating install friction: skipping `lake exe cache get` (and then recompiling all of Mathlib for hours), or a `lean-toolchain` that does not match the Mathlib version — reproducibility depends on pinning both.
- Believing you must re-prove classical theorems from scratch. The everyday idiom is to CITE a Mathlib lemma (`Nat.exists_infinite_primes`, `Nat.Prime.irrational_sqrt`) and align types with `exact_mod_cast`/`omega`; searching (`exact?`, `apply?`, Loogle) is a core skill, not cheating.
- Fighting the surface syntax: Lean is indentation- and Unicode-sensitive (enter `∀ ∃ → ∧ ↔ ℕ` via `\forall`, `\exists`, `\to`, `\and`, `\iff`, `\N`), and implicit arguments `{P Q : Prop}` vs explicit `(h : P ∧ Q)` change how you call a lemma.
- Confusing `=` (propositional equality, a `Prop`) with `:=` (definition) and with `↔`; and confusing definitional equality (checked by `rfl`) with provable-but-not-definitional equality (needs a lemma/induction).

## Canonical references

- Lean 4 official release notes / language reference, latest — Lean 4.32.0 (2026-07-13), 4.33.0-rc1 (2026-07-15) — <https://lean-lang.org/doc/reference/latest/releases/>  
  _Authoritative version anchor for the lecture (which Lean the students install) and the reference manual for syntax; use to state the current version honestly._
- J. Avigad, L. de Moura, S. Kong, S. Ullrich — Theorem Proving in Lean 4 (official online textbook) — <https://leanprover.github.io/theorem_proving_in_lean4/>  
  _The canonical free introduction to term/tactic mode, Prop vs Type, inductive types and the tactic language; the single best primary reading to assign after the lecture._
- J. Avigad, P. Massot — Mathematics in Lean (online course / MIL) — <https://leanprover-community.github.io/mathematics_in_lean/>  
  _The community's hands-on Mathlib tutorial; complements TPiL by teaching how to DO mathematics (rw/simp/ring/linarith, Nat, sets) rather than logic foundations._
- Natural Number Game 4 (NNG4), leanprover-community, on the Lean 4 Game engine (adam.math.hhu.de) — <https://adam.math.hhu.de/#/g/leanprover-community/NNG4>  
  _The zero-install browser game that reconstructs Nat from Peano axioms and drills exactly this lecture's induction+rw skills up to add_comm/mul_comm; the primary in-class/after-class activity. Repo: github.com/leanprover-community/NNG4._
- Heather Macbeth — The Mechanics of Proof (Fordham Math 2001), online book + github.com/hrmacbeth/math2001 — <https://hrmacbeth.github.io/math2001/>  
  _Every proof given in both prose and Lean, at first-year-university level; the recommended follow-on textbook and the source of the calc/have/linarith style used in the author's macbeth_calc demos._
- Lean install guide (elan + lake) and 'Using mathlib4 as a dependency', leanprover-community — <https://lean-lang.org/install/>  
  _Canonical, current setup instructions for the tooling segment: elan install, lake project, `lake exe cache get`, VS Code + InfoView; pair with github.com/leanprover-community/mathlib4/wiki/Using-mathlib4-as-a-dependency._
- Mathlib4 repository and live statistics (leanprover-community) — <https://leanprover-community.github.io/mathlib_stats.html>  
  _Grounds the claim that citing Mathlib is the everyday idiom: current counts (≈283k theorems, ≈135k definitions) and the library students depend on; repo at github.com/leanprover-community/mathlib4._
- L. de Moura, S. Ullrich — The Lean 4 Theorem Prover and Programming Language (CADE-28, 2021, LNCS 12699) — <https://leanprover.github.io/papers/lean4.pdf>  
  _Primary citation for the system's design and the small-trusted-kernel / de Bruijn criterion that underpins the lecture's trust story._

## Volatile facts (sent to fact-check)

- The latest stable Lean 4 release is 4.32.0 (2026-07-13); 4.33.0-rc1 (2026-07-15) is the current release candidate. Recent stable line: 4.31.0 (2026-06-13), 4.30.0 (2026-05-26), 4.29.1 (2026-04-14), 4.28.0 (2026-02-17). (src: https://lean-lang.org/doc/reference/latest/releases/)
- Mathlib currently contains roughly 283,067 theorems and 134,678 definitions, contributed by ~772 people — evidence for the lecture's claim that 'cite a library lemma' is the normal mode of formal mathematics. (src: https://leanprover-community.github.io/mathlib_stats.html)
- Natural Number Game 4 (NNG4) is maintained by leanprover-community, runs in the browser with no install on the Lean 4 Game engine, and is hosted at adam.math.hhu.de; it reconstructs ℕ from the Peano axioms and its Addition World culminates in add_comm via induction + rw. (src: https://adam.math.hhu.de/#/g/leanprover-community/NNG4)
- Heather Macbeth's 'The Mechanics of Proof' (Fordham University, Math 2001) presents every proof in both prose and Lean 4, with 200+ worked problems and hundreds of exercises; free online with a GitHub repository. (src: https://hrmacbeth.github.io/math2001/)
- The author's own Lean projects pin slightly earlier tooling than current stable — proofs/lean/lean-toolchain is leanprover/lean4:v4.30.0-rc2 and the eml-formalization targets Mathlib v4.28 (Lean 4.28.0) — a concrete 'pin your toolchain / version skew is normal' teaching point. (src: https://github.com/leanprover-community/mathlib4)
