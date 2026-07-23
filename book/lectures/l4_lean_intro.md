# Lecture 4 — Introduction to Lean

```{admonition} Abstract
:class: tip
From paper to kernel. We meet **Lean 4**: the difference between **term mode** and **tactic mode**,
between **propositions** and **data**, the natural numbers and **induction**, and the handful of tactics
that get you to a first honest end-to-end proof. We anchor the practice in the **Natural Number Game**
and Heather Macbeth's **Mechanics of Proof**.
```

## Learning objectives

By the end of this lecture you can:

- Read the **same** theorem in **term mode** (a bare $\lam$-term) and **tactic mode** (a `by` script),
  and explain why both elaborate to one kernel-checked term — the **de Bruijn criterion**.
- Distinguish `Prop` (proof-irrelevant propositions) from `Type`/data and use the Curry–Howard
  dictionary — $\To$ a function, $\land$ a pair, $\exists$ a dependent pair — with `intro`, `exact`,
  `apply`, `constructor`, and `obtain`/`rcases`.
- Prove statements about the naturals by **structural induction**, and explain why $n+0=n$ holds by
  `rfl` but $0+n=n$ needs induction.
- Drive equational reasoning with `rfl`, `rw` (including the reverse `rw [← h]`) and `simp`, controlling
  direction and order.
- Choose the right **automation** — `decide`, `omega`, `ring`, `linarith` — and state each one's scope and
  failure mode.
- Set up a real **Lean 4 + Mathlib** project (`elan`, `lake`, `lake exe cache get`, a pinned
  `lean-toolchain`) and inspect proofs with `#check`, `#eval`, `#print axioms`.
- Complete one **honest end-to-end** proof (Gauss's sum by induction) and one **library-driven**
  corollary, then continue independently in NNG4 and Macbeth.

## Why this matters

Three lectures of theory now pay off. In {doc}`Lecture 1 <l1_type_theory>` we met the judgment
$\Gamma \proves t : A$; in {doc}`Lecture 2 <l2_lambda_calculus>` we computed with pure $\lam$-terms; in
{doc}`Lecture 3 <l3_propositional>` we read the connectives as type formers. **Lean 4 is that story made
executable.** It is a dependently-typed $\lam$-calculus in which a *proposition is a type* and a *proof is
a term inhabiting it*. Nothing new is asked of you conceptually — but now a machine checks every step.

Why should a mathematician trust a machine? Because of a deliberate architectural choice: **only a small
type-checking kernel must be correct.** A proof, however it was produced, is ultimately a term; the kernel
verifies that this term has the claimed type. The elaborator, the tactic framework, the pretty-printer —
tens of thousands of lines — may all contain bugs without endangering soundness, as long as the term they
emit type-checks. This is the **de Bruijn criterion**, and it is why "the computer says the proof is
correct" means something precise. It is also the foundation for the research formalization we build toward
in {doc}`Lecture 6 <l6_autoformalization>`.

The second reason is **Mathlib**: a single, coherent library holding on the order of $283{,}000$ theorems
and $135{,}000$ definitions (2026). Formalizing modern mathematics is feasible precisely because you rarely
start from nothing — you *cite* a lemma. Learning to search for the right name is as much a skill as
learning to prove.

## Two modes, one term: term mode, tactic mode, and the kernel

In Lean every proof is a term. You can write that term two ways.

**Term mode** — write the inhabitant directly. Modus ponens is *literally* function application:

```lean
theorem modus_ponens {P Q : Prop} : (P → Q) → P → Q :=
  fun f p => f p
```

**Tactic mode** — a `by` block whose tactics are a metaprogram that *builds* the term for you:

```lean
theorem modus_ponens' {P Q : Prop} : (P → Q) → P → Q := by
  intro f p
  exact f p
```

These are not two kinds of proof. `by` is a term-builder; when it finishes, Lean hands the kernel a
$\lam$-term, exactly as term mode does. You can always see it: after a tactic proof, `#print modus_ponens'`
reveals `fun f p => f p`. The universe bookkeeping behind this is small: every type lives in some
`Sort u`, with `Prop = Sort 0` for proof-irrelevant propositions and `Type = Type 0 = Sort 1` for data.

```{admonition} So does every proof "fully expand" into one giant λ-term? No — three precisions
:class: note
**Names stay names.** The elaborated term references the lemmas it uses as *constants* — `#print` on
this course's `add_comm'` shows `Nat.recAux`, `Eq.mpr`, and the names `zero_add'`/`succ_add'`, not
their inlined proofs. Proofs form a shared DAG; the kernel unfolds a definition lazily only when a
definitional-equality check demands it, and never β-normalizes your proof. This sharing is what makes
a 283 000-theorem library feasible. (Our lab's `let` expands *eagerly* at definition time — the
miniature version; Lean keeps a persistent name table instead.)

**Some terms are small because the kernel computes.** `theorem four : 2 + 2 = 4 := by decide`
elaborates to just `of_decide_eq_true (id (Eq.refl true))` — the work happens when the kernel
*evaluates* `decide (2 + 2 = 4)` to `true` during checking. Term size and checking effort are
decoupled in both directions: `simp` builds long explicit `Eq.mpr` chains, `decide` builds two nodes.

**The compiler erases proofs entirely.** Elaborated terms have two consumers: the kernel certifies
everything (including all of `Prop`), while the code generator erases `Prop` as computationally
irrelevant — a proof is checked once, stored as a compressed expression in the `.olean`, and never
becomes runtime code. Even `sorry` is a term (`sorryAx …`), which is exactly why `#print axioms` can
audit for it.
```

```{admonition} Run it
:class: seealso
Experience "tactics build a term" before Lean is even installed — each direction is one lab command:

- [`prove (P -> Q) -> P -> Q`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=prove%20%28P%20-%3E%20Q%29%20-%3E%20P%20-%3E%20Q)
  — an interactive proof builder: type `intro f`, `intro p`, `apply f`, `assumption`, then `qed`.
- [`ch term \f. \p. f p`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20term%20%5Cf.%20%5Cp.%20f%20p)
  — infers the principal type of the hand-written λ-term.

`qed` prints the extracted term `λf p. f p` with the type it proves: the tactics were a program that
*built* the term, and `qed` is your `#print` — the de Bruijn criterion on one screen.
```

**Worked example 1 (symmetry of conjunction, both ways).** Conjunction is a *structure* with two fields,
so a proof of $P \land Q$ is a pair, and swapping is trivial:

```lean
-- term mode: destructure the pair, rebuild it swapped
theorem and_comm_term {P Q : Prop} : P ∧ Q → Q ∧ P :=
  fun ⟨hp, hq⟩ => ⟨hq, hp⟩

-- tactic mode: the SAME term, built step by step
theorem and_comm_tac {P Q : Prop} (h : P ∧ Q) : Q ∧ P := by
  obtain ⟨hp, hq⟩ := h   -- split the hypothesis into hp : P, hq : Q
  constructor            -- goal Q ∧ P becomes two goals: Q, then P
  · exact hq
  · exact hp
```

Run `#print and_comm_tac` and you get `fun h => ⟨h.2, h.1⟩` — the anonymous constructor and projections
of the same structure. Term mode and tactic mode differ only in how much of the term *you* write.

```{admonition} Run it
:class: seealso
Project the sources on screen and run them through the lab:
[`lean and_comm`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=lean%20and_comm),
[`lean term_proofs`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=lean%20term_proofs),
[`lean imp_comp`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=lean%20imp_comp). The same
tautologies appear in all four provers — compare
[`artifacts/lean`](https://github.com/nasqret/vietnam2026/tree/main/artifacts/lean),
[`artifacts/agda`](https://github.com/nasqret/vietnam2026/tree/main/artifacts/agda),
[`artifacts/rocq`](https://github.com/nasqret/vietnam2026/tree/main/artifacts/rocq) and
[`artifacts/mizar`](https://github.com/nasqret/vietnam2026/tree/main/artifacts/mizar).
```

## Propositions vs data: `Prop`, proof irrelevance, and the Curry–Howard dictionary

Here is the distinction that trips up every mathematician. A proposition `P : Prop` is
**proof-irrelevant**: any two proofs of `P` are *equal*, so a proof carries no information beyond "this
holds." Data `n : Nat` is not: `2` and `3` are different. Consequently you may **not**, in general,
pattern-match on a proof to extract data (the *large-elimination* restriction) — a proof of $\exists n,\ 
\dots$ does not hand you a computable witness in `Type`.

```{tip}
**Why can't I extract the witness?** Because proof irrelevance forces functions out of proofs to be
constant. Suppose you could pattern-match `h : ∃ n, 2 ∣ n` and return the witness. The proofs
`⟨2, _⟩` and `⟨4, _⟩` inhabit the same proposition, so they are *equal* — yet your extractor would send
equal inputs to the unequal outputs `2` and `4`. Contradiction; hence the restriction. When you
genuinely need the witness *as data*, use the `Type`-valued siblings — the subtype `{n // 2 ∣ n}` or a
sigma type `Σ n, …` — whose elements really are pairs you may take apart.
```

Everything else is the dictionary you already know from {doc}`Lecture 3 <l3_propositional>`, now as
concrete datatypes:

| Logic | Lean type | Introduce | Eliminate |
|-------|-----------|-----------|-----------|
| $P \To Q$ | function `P → Q` | `fun h => …` / `intro` | apply it |
| $P \land Q$ | structure `And P Q` | `⟨_, _⟩` / `constructor` | `.left`, `.right` / `obtain` |
| $P \lor Q$ | sum `Or P Q` | `Or.inl`, `Or.inr` / `left`,`right` | `rcases`/`cases` |
| $\exists x,\ p\,x$ | dependent pair `Exists p` | `⟨w, hw⟩` | `obtain ⟨w, hw⟩ := h` |
| $P \Leftrightarrow Q$ | structure `Iff P Q` | `⟨mp, mpr⟩` | `.mp`, `.mpr` |
| $\forall x,\ p\,x$ | dependent function `(x : α) → p x` | `fun x => …` / `intro` | apply it |

The punchline students remember: **$\exists$ is not a mystical quantifier, it is a pair type.** Its
constructor is $\langle \text{witness}, \text{proof} \rangle$; its eliminator is destructuring.

**Worked example 2 (an existential is a pair).**

```lean
-- the proof IS the pair (witness 2, a proof that 2^2 = 4)
theorem exists_sq_four : ∃ n : Nat, n ^ 2 = 4 := ⟨2, rfl⟩
```

Why does `rfl` prove $2^2 = 4$? Because on `Nat` the expression $2^2$ *computes* to $4$; the two sides
share a normal form, so they are **definitionally equal**. The same phenomenon explains a slogan you will
meet constantly: `2 ∣ n` is *by definition* `∃ c, n = 2 * c`. The two are the *same* proposition — no
lemma is needed to pass between them, only destructuring:

```lean
theorem two_dvd_iff (n : Nat) : 2 ∣ n ↔ ∃ c, n = 2 * c :=
  ⟨fun h => h, fun h => h⟩   -- both directions are the identity: same type
```

## The natural numbers and induction

`Nat` is an **inductive type** — Peano's axioms as data constructors, exactly the `zero`/`succ` of
{doc}`Lecture 2 <l2_lambda_calculus>`, now with a real recursor:

```lean
inductive Nat where
  | zero : Nat
  | succ : Nat → Nat
```

Addition is defined by structural recursion **on its second argument**:

$$ m + 0 = m, \qquad m + (n+1) = (m + n) + 1. $$

This asymmetry is the single most instructive surprise of the day. Because the recursion consumes the
*right* operand, $m + 0 = m$ is the *defining equation* — it holds by `rfl`. But $0 + n = n$ is **not** a
defining equation (the recursion never looks at a left zero), so it must be *proved*, by induction on $n$.

**Worked example 3 (rebuilding addition, as in NNG4).** On a private copy of the naturals we reconstruct
commutativity from the two defining equations alone:

```lean
inductive N where
  | zero : N
  | succ : N → N

namespace N

def add (m : N) : N → N
  | .zero   => m                 -- add_zero: m + 0     = m
  | .succ n => .succ (add m n)   -- add_succ: m + (n+1) = (m + n) + 1

@[simp] theorem add_zero (m : N)   : add m .zero = m := rfl
@[simp] theorem add_succ (m n : N) : add m (.succ n) = .succ (add m n) := rfl

theorem zero_add (n : N) : add .zero n = n := by
  induction n with
  | zero      => rfl                    -- add .zero .zero = .zero  by rfl
  | succ k ih => rw [add_succ, ih]      -- succ (add .zero k) → succ k

theorem succ_add (m n : N) : add (.succ m) n = .succ (add m n) := by
  induction n with
  | zero      => rfl
  | succ k ih => rw [add_succ, ih, add_succ]

theorem add_comm (m n : N) : add m n = add n m := by
  induction n with
  | zero      => rw [add_zero, zero_add]
  | succ k ih => rw [add_succ, succ_add, ih]
```

Read `add_comm` slowly, because it is the whole method in four lines. `induction n` splits into the base
case ($n = 0$), closed by rewriting both sides to $m$, and the successor case, which *assumes* the
induction hypothesis `ih : add m k = add k m` and rewrites the goal
$\text{add } m\,(k{+}1) = \text{add }(k{+}1)\,m$ down to a syntactic identity using, in order,
`add_succ`, `succ_add`, and `ih`. This is precisely the milestone the Natural Number Game's Addition World
hands you a star for.

```{admonition} Run it
:class: seealso
Play the [Natural Number Game](https://adam.math.hhu.de/#/g/leanprover-community/NNG4) through the
Tutorial and Addition worlds — no installation, it runs in the browser and culminates in exactly this
`add_comm`. Then see the offline trace with
[`lean add_comm`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=lean%20add_comm). The Agda twin
`+-comm` and the Rocq twin `add_comm` (via `induction n` + `rewrite`) live in the
[four-prover artifacts](https://github.com/nasqret/vietnam2026/tree/main/artifacts).
```

## Rewriting: `rfl`, `rw`, `simp`

Equational reasoning is the everyday mechanics, and its three tools have sharply different jobs.

- **`rfl`** closes `a = a` when both sides are **definitionally equal** — reduce to a common normal form.
  It proves $m + 0 = m$ and $2^2 = 4$; it does **not** prove $0 + n = n$.
- **`rw [h]`** rewrites the goal **left-to-right** by the equation `h`, replacing occurrences of its LHS
  with its RHS. It fails if the LHS does not appear *syntactically*, and can raise `motive is not type
  correct` in dependent situations. Use **`rw [← h]`** for the reverse direction, and chain
  `rw [h₁, h₂, …]` to apply several in order. After a `rw` that makes both sides identical, the goal is
  closed automatically.
- **`simp`** repeatedly rewrites with the whole `@[simp]` lemma set (plus arithmetic/definitional
  simplification) until nothing applies. It is *non-directional* and powerful, but opaque — reach for a
  targeted `rw` when you know the exact step, and `simp only [lemmas]` when you want a controlled subset.

A pure `rw` chain — no induction — illustrates the discipline; here `←` is essential:

```lean
example (a b : ℝ) (h1 : a^2 = b^2 + 4) (h2 : a + b = 2) : (a - b) * 2 = 4 := by
  have hprod : (a - b) * (a + b) = 4 := by
    have : a^2 - b^2 = 4 := by linarith
    calc (a - b) * (a + b) = a^2 - b^2 := by ring
      _ = 4 := this
  rw [← h2]        -- turn the goal's `2` back into `a + b`, matching hprod
  exact hprod
```

## A first honest end-to-end proof — and a library-driven corollary

Two mental models coexist in formal mathematics: *I can build a proof from primitives*, and *the right
move is usually to find the lemma*. You need both.

**Worked example 4 (Gauss's sum, built by induction).** The schoolchild identity, kernel-checked:

$$ 2\sum_{k=0}^{n} k = n(n+1). $$

```lean
import Mathlib

theorem gauss (n : Nat) : 2 * (∑ k ∈ Finset.range (n + 1), k) = n * (n + 1) := by
  induction n with
  | zero      => simp                                    -- both sides are 0
  | succ n ih => rw [Finset.sum_range_succ, Nat.mul_add, ih]; ring
```

The base case is `simp` (it knows the empty-then-single-term sum reduces and $0 = 0\cdot 1$). The step
peels off the last summand with `Finset.sum_range_succ`, distributes with `Nat.mul_add`, substitutes the
induction hypothesis `ih`, and lets `ring` clear the polynomial dust. That is a complete, `sorry`-free
proof of a genuine theorem.

**Worked example 5 (the library-driven idiom).** Euclid's theorem — infinitely many primes — is already
in Mathlib as `Nat.exists_infinite_primes`. The everyday move is to *cite* it and align types:

```lean
theorem prime_above (N : Nat) : ∃ p, N < p ∧ p.Prime := by
  obtain ⟨p, hN, hp⟩ := Nat.exists_infinite_primes (N + 1)  -- gives N + 1 ≤ p
  exact ⟨p, by omega, hp⟩                                    -- omega: N + 1 ≤ p ⟹ N < p
```

You did not reprove Euclid; you found the name, destructured its output, and let `omega` promote
$N + 1 \le p$ to $N < p$. Searching (`exact?`, `apply?`, Loogle, LeanSearch) is a core skill, not
cheating — the same idiom makes `Irrational (Real.sqrt 2)` a one-liner on top of
`Nat.Prime.irrational_sqrt`, developed further in {doc}`Lecture 5 <l5_lean_advanced>`.

```{admonition} Run it
:class: seealso
Walk the guided tutorial that chains narrative → live proof-term inspection → a checkpoint quiz:
[`tutorial 1`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=tutorial%201) (the Gauss bundle),
then [`ch explore --live`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20explore%20--live)
to see the finished proof as a term *tree*, and
[`kb mathlib`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=kb%20mathlib) for the
lemma-search cheatsheet.
```

## Arithmetic automation: `decide`, `omega`, and a peek at `ring`/`linarith`

Beginners either fall in love with automation or get burned by it. The cure is knowing each tactic's
**scope**.

| Tactic | Discharges | Fails / out of scope when… |
|--------|-----------|-----------------------------|
| `decide` | a **decidable** proposition, by evaluating its `Decidable` instance to `isTrue` | the goal is not decidable, or is decidable but too large to compute |
| `omega` | **linear** integer/natural arithmetic — equalities, inequalities, `∣` by literals (Presburger) | any product of *variables*, e.g. `x * y` |
| `ring` / `ring_nf` | identities in a commutative (semi)ring | (in)equalities, or non-ring goals |
| `linarith` / `nlinarith` | linear (and, heuristically, nonlinear) inequalities from hypotheses | needs the right hints; not a normalizer |

Two contrasts make the point. First, `⟨2, rfl⟩` and `by refine ⟨2, ?_⟩; decide` both prove
$\exists n,\ n^2 = 4$ — one by definitional computation, one by running a decision procedure. Second, the
misconception "just try `omega`" wastes real time: `omega` will not touch $x \cdot y$, and reaching for it
on a nonlinear goal simply fails. Match the tactic to the shape of the goal.

```{admonition} Run it
:class: seealso
Every row of this table is a card in the lab's Lean tactic encyclopedia — summary, effect on the goal,
when to reach for it, and a worked example:
[`ch tactic decide`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20tactic%20decide) ·
[`ch tactic omega`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20tactic%20omega) ·
[`ch tactic ring`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20tactic%20ring) ·
[`ch tactic linarith`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20tactic%20linarith).
Exercise 7 (automation scope) is easiest after reading the `omega` and `ring` cards side by side.
```

## Tooling: `elan`, `lake`, Mathlib, and `#check`/`#eval`

The unglamorous but decisive half of "introduction to Lean."

```bash
# one-time: install the toolchain manager, then Lean + lake come with it
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh

# a fresh Mathlib-backed project
lake +leanprover-community/mathlib4:lean-toolchain new my_project math
cd my_project
lake exe cache get          # download prebuilt Mathlib .olean files — do NOT skip this
lake build
```

Three points a mathematician must internalize:

- **`elan`** pins the exact compiler per project via a `lean-toolchain` file, e.g.
  `leanprover/lean4:v4.28.0-rc1`. The current stable line is Lean **4.32.0** (2026-07); the author's own
  demo repo pins `v4.28.0-rc1` and the EML formalization targets **Lean v4.28** — deliberate *version
  skew* is normal, and *pinning both toolchain and Mathlib* is what makes a build reproducible.
- **`lake exe cache get`** downloads prebuilt `.olean` artifacts. Skip it and you recompile ~300k
  theorems from source — hours on a laptop.
- **Inspection is instant.** `#check Nat.add_comm` reports `∀ (n m : ℕ), n + m = m + n`; `#eval 2 ^ 10`
  prints `1024`; and — the trust audit you should always run — `#print axioms gauss` lists exactly the
  axioms a proof depends on, confirming there is no hidden `sorry`.

## Common pitfalls

- **"Term mode and tactic mode are different kinds of proof."** They are not. A `by` block is a
  metaprogram that builds a $\lam$-term; the kernel checks that term. Any tactic proof can be `#print`ed
  as a term.
- **"`rfl` closes every equality."** It closes only *definitional* ones. `add_zero : m + 0 = m` is `rfl`;
  `zero_add : 0 + n = n` is not, because `Nat.add` recurses on its second argument. This asymmetry
  surprises everyone.
- **Misusing `rw`.** It rewrites strictly left-to-right and fails if the LHS is not present syntactically
  (or throws `motive is not type correct`). Forgetting `rw [← h]` for the reverse direction, or reaching
  for `simp` where a targeted `rw` is needed (or vice versa), is the usual beginner friction.
- **Treating `Prop` like data.** Propositions are proof-irrelevant; you cannot pattern-match on a proof to
  extract computational data (large-elimination restriction).
- **Over-trusting automation.** `decide` needs a `Decidable` instance and can hang; `omega` is *linear
  only* and will not touch `x * y`. "Just try `omega`/`decide`" is a real time sink.
- **Assuming NNG4 transfers verbatim.** The game curates a subset and lightly renames things; production
  Lean uses `induction n with | … => …`, full Mathlib names, and `omega`/`ring`/`simp` the game may hide.
- **Underestimating install friction.** Skipping `lake exe cache get`, or a `lean-toolchain` that does not
  match your Mathlib version, breaks reproducibility.
- **Fighting the surface syntax.** Lean is indentation- and Unicode-sensitive: enter
  $\forall\,\exists\,\to\,\land\,\leftrightarrow\,\N$ via `\forall`, `\exists`, `\to`, `\and`, `\iff`,
  `\N`. And `{P Q : Prop}` (implicit) vs `(h : P ∧ Q)` (explicit) changes how you *call* a lemma.

## Exercises

1. **(Composition, both modes.)** Prove `(P → Q) → (Q → R) → P → R` in term mode
   (`fun f g p => g (f p)`) *and* in tactic mode (`by intro f g p; exact g (f p)`). Then `#print` both and
   confirm they are the same term.
2. **(Squares.)** Prove `∃ n : Nat, n ^ 2 = 4` first as the pair `⟨2, rfl⟩`, then as
   `by refine ⟨2, ?_⟩; decide`. Explain in one sentence why `rfl` already works.
3. **(NNG4, pen-and-paper first.)** Before touching Lean, write out, by hand, the two-case induction for
   `zero_add` and `add_comm` on `N`. Then clear NNG4's Addition World and check your cases matched.
4. **(Rewrite discipline.)** On the private naturals `N`, prove
   `add_right_comm (a b c : N) : add (add a b) c = add (add a c) b` using only `rw` with `add_assoc` and
   `add_comm` — no induction. *(Hint: you will need at least one `rw [← …]`.)*
5. **(Gauss.)** Reproduce Worked Example 4 in a Mathlib project and run `#print axioms gauss`. Confirm the
   output contains no `sorryAx`.
6. **(Library hunt — medium.)** Prove `∃ p, 100 < p ∧ p.Prime` by finding the Mathlib lemma with `exact?`
   and finishing with `omega`. Name the lemma you used.
7. **(Automation scope — medium.)** Exhibit one goal that `omega` closes and `ring` cannot, and one that
   `ring` closes and `omega` cannot. State why in each case.
8. **(Cross-prover — hard.)** Prove commutativity of addition on your own inductive naturals in **two**
   systems: Lean (`induction` + `rw`) and Agda (`+-comm` by pattern-matching induction), starting from the
   [four-prover artifacts](https://github.com/nasqret/vietnam2026/tree/main/artifacts). Contrast how each
   system presents the induction hypothesis. *(Optional: add the Rocq version with `induction` + `lia`.)*

## References

- [Theorem Proving in Lean 4](https://leanprover.github.io/theorem_proving_in_lean4/) — Avigad, de Moura,
  Kong, Ullrich: the canonical free introduction to term/tactic mode, `Prop` vs `Type`, and inductive
  types. The best reading to assign after this lecture.
- [Mathematics in Lean](https://leanprover-community.github.io/mathematics_in_lean/) — Avigad, Massot: the
  hands-on Mathlib tutorial (`rw`/`simp`/`ring`/`linarith`, `Nat`, sets).
- [Natural Number Game 4 (NNG4)](https://adam.math.hhu.de/#/g/leanprover-community/NNG4) — the zero-install
  browser game that reconstructs `Nat` from Peano and drills exactly this lecture's `induction`+`rw` up to
  `add_comm`.
- [The Mechanics of Proof](https://hrmacbeth.github.io/math2001/) — Heather Macbeth: every proof in both
  prose and Lean, at first-year level; source of the `calc`/`have`/`linarith` style.
- [Lean install guide (elan + lake)](https://lean-lang.org/install/) and the
  [Lean release notes](https://lean-lang.org/doc/reference/latest/releases/) — current tooling and the
  version anchor.
- [Mathlib4 statistics](https://leanprover-community.github.io/mathlib_stats.html) — the live theorem and
  definition counts behind "citing a lemma is the normal mode."
- [The Lean 4 Theorem Prover and Programming Language](https://leanprover.github.io/papers/lean4.pdf) — de
  Moura, Ullrich: the system's design and the small-trusted-kernel / de Bruijn criterion.
- The course's own [four-prover artifacts](https://github.com/nasqret/vietnam2026/tree/main/artifacts) and
  the [Lean sources](https://github.com/nasqret/vietnam2026/tree/main/artifacts/lean).
```{note}
This chapter is the write-up of Part IV of the falenty-2026 course; NNG4 and Macbeth are the intended
self-study ramps out of it, and the EML formalization of {doc}`Lecture 6 <l6_autoformalization>` is where
it leads.
```
