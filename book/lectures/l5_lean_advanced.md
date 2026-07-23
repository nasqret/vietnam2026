# Lecture 5 — Advanced Lean

```{admonition} Abstract
:class: tip
The tools that make formalizing *real* mathematics tractable: **dependent types** in practice,
**structures** and **typeclasses**, the architecture of **Mathlib** and how to search it, the heavy-duty
tactics (`simp`, `ring`, `linarith`, `omega`, `norm_num`, `decide`, `positivity`, and the new `grind`),
**`calc`** blocks, **structural vs. well-founded recursion** — closing on a genuine analysis/algebra
proof and a first look under the hood at Lean's macro-and-elaboration pipeline.
```

## Learning objectives

- Read and write dependent function types, distinguish `Prop` from `Type u` in the `Sort` hierarchy, and
  explain proof irrelevance and the large-elimination restriction and why they matter.
- Use `structure` and `class`/`instance` to state general theorems, read a Mathlib algebraic-hierarchy
  class, and explain instance resolution and the diamond problem.
- Search Mathlib effectively (`exact?`, `apply?`, `rw?`, `simp?`, **Loogle**, **LeanSearch**) and decode a
  lemma from its name using Mathlib's convention.
- Choose the right automation tactic for a goal — `ring`, `linarith`/`nlinarith`, `omega`, `norm_num`,
  `field_simp`, `positivity`, `decide`, `grind` — and know which goal *shape* each one owns.
- Chain steps with `calc`, and define functions by structural recursion versus well-founded recursion,
  knowing when each is required.
- Carry one genuine theorem (irrationality of $\sqrt 2$) from statement to kernel-checked proof.
- Read a minimal `macro` example and name the four stages of Lean's parse → macro-expand → elaborate →
  kernel-check pipeline.

## Why this matters

{doc}`Lecture 4 <l4_lean_intro>` got us to a first honest proof: `Nat`, induction, a starter kit of
tactics, and the slogan that a term-mode proof and a tactic-mode script produce the *same* kernel-checked
object. That is enough to reprove undergraduate lemmas one keystroke at a time. It is *not* enough to do
mathematics at scale.

Two things stand between "I can prove `0 + n = n`" and "I can formalize a research paper." First,
**generality**: you do not want to reprove `a * b = b * a` for $\N$, then $\Z$, then polynomials, then
matrices. You want to state it *once*, at the right level of abstraction, and have it apply everywhere —
that is what typeclasses buy you. Second, **automation and search**: [Mathlib](https://lean-lang.org/use-cases/mathlib/)
is roughly **351,000 declarations** across **over two million lines**, and no human recalls it. The
working skill is not memorizing lemmas; it is *finding* them and letting decision procedures discharge the
routine algebra. This lecture is that toolkit. It is also the on-ramp to {doc}`Lecture 6 <l6_autoformalization>`,
where exactly these tools carry a whole paper.

## Dependent types in practice: Π-types, `Prop` vs `Type`

The one primitive that separates Lean from a simply-typed language is the **dependent function type**, or
Π-type: given a type $\alpha$ and a family $\beta : \alpha \to \mathrm{Sort}\,u$,

$$\prod_{x:\alpha} \beta\,x \quad\text{written in Lean as}\quad (x : \alpha) \to \beta\,x \quad\text{or}\quad \forall\,x,\ \beta\,x .$$

The ordinary arrow $\alpha \to \beta$ is the degenerate case where $\beta$ does not mention $x$. This is
why `∀` and `→` are the *same* connective in Lean: a proof of `∀ n : ℕ, P n` **is** a function that maps
each `n` to a proof of `P n`. `Matrix (Fin m) (Fin n) ℝ` is a type whose *shape* is part of its type; a
term of `Vector α n` carries its length in its type. Types depend on values.

Everything lives in the universe hierarchy `Sort`:

$$\mathrm{Prop} = \mathrm{Sort}\,0, \qquad \mathrm{Type}\,u = \mathrm{Sort}\,(u+1).$$

The split between `Prop` and `Type u` is not cosmetic. `Prop` is **proof-irrelevant**: for a proposition
`p : Prop` and any two proofs `h₁ h₂ : p`, the two are *definitionally equal*,

$$h_1 \equiv h_2 \quad (p : \mathrm{Prop}).$$

A proposition carries no data beyond the bare fact that it is inhabited. `Type u` is where data lives, and
data must be distinguishable: `0` and `1` in `Nat` are not interchangeable. Because proofs are irrelevant,
Lean imposes the **large-elimination restriction**: you generally cannot pattern-match on a proof of a
`Prop` to build a value in `Type`. If you could case-split `∃ n, P n` to *extract* the witness `n` as
computational data, you would be leaking a non-computational choice through a proof-irrelevant door — and
two definitionally-equal proofs could yield different data, a contradiction. (`Prop` *does* permit
eliminating into `Prop`, and singleton-like types have special large-elimination rules; the blanket
restriction is what keeps the system coherent.)

The data-side dual of the Π-type is the **Σ-type** (dependent pair) $\sum_{x:\alpha}\beta\,x$, written
`(x : α) × β x`, together with the `Subtype` `{x // p x}`. These are the raw material of `structure`,
next.

Finally, recall the **de Bruijn criterion** from {doc}`l4_lean_intro`: only Lean's small kernel is
trusted. The elaborator, the tactic framework, Mathlib — all of it may be buggy, and a proof is still
sound, because the kernel independently re-checks the final `Expr`. The command `#print axioms thm`
audits *which* axioms a proof actually used — typically `propext`, `Classical.choice`, `Quot.sound`, or
none at all.

```{admonition} Run it — the computational core, in the browser
:class: seealso
Before dependent types, remember the untyped core from {doc}`l2_lambda_calculus`. In the Lambda Lab,
watch a logical connective *compute* by β-reduction — proofs-as-programs made literal:
[`reduce IMPLIES TRUE FALSE`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=reduce%20IMPLIES%20TRUE%20FALSE).
In Lean the same idea has types attached: `#check (fun n : ℕ => rfl : ∀ n : ℕ, n + 0 = n)` type-checks
because `∀` *is* a Π-type.
```

## Structures and typeclasses: Mathlib's algebraic hierarchy

A `structure` is a one-constructor inductive type — a Σ-type that bundles data together with the proofs of
its axioms. A `class` is a `structure` whose instances Lean *finds automatically* by instance resolution,
instead of your passing them by hand. This is the mechanism behind `+`, `0`, `≤` meaning the right thing
on every type at once. Here is a real Mathlib class, a group as a monoid with inverses:

```lean
class Group (G : Type*) extends DivInvMonoid G where
  inv_mul_cancel : ∀ a : G, a⁻¹ * a = 1
```

Mathlib stacks classes with `extends` into a tower — `Monoid → Group → CommGroup`, `Semiring → Ring →
CommRing → Field`, and two-parameter classes like `Module R M`. State a theorem under `[CommMonoid M]`
and it fires on $\N$, $\Z$, polynomials, and matrices over a commutative ring alike:

$$\texttt{mul\_comm} : a * b = b * a \quad\text{proved once, inherited everywhere.}$$

The price of a rich hierarchy is the **diamond problem**: when two inheritance paths reach the same
ancestor, the instances they produce must be *definitionally equal*, or Lean sees two different `+` on the
same type and typeclass resolution breaks. Mathlib manages diamonds by making the shared fields explicit
and overriding them with `where` clauses so the paths coincide by definition.

````{admonition} Worked example 1 — a class you can prove against its interface
:class: important
Define a minimal additive monoid, register `Nat` as an instance, then prove a lemma *stated only from the
class interface* — it will hold for every future instance for free.

```lean
class MyAddMonoid (α : Type*) where
  zero    : α
  add     : α → α → α
  add_zero : ∀ a, add a zero = a
  zero_add : ∀ a, add zero a = a

instance : MyAddMonoid Nat where
  zero := 0
  add := Nat.add
  add_zero := Nat.add_zero
  zero_add := Nat.zero_add

open MyAddMonoid in
theorem add_zero_zero {α : Type*} [MyAddMonoid α] (a : α) :
    add (add a zero) zero = a := by
  rw [add_zero, add_zero]
```

The proof never mentions `Nat`. It reasons purely from `add_zero`, so it applies to *any* `MyAddMonoid`.
This is "interface over definition" — the discipline that lets Mathlib reuse each lemma across the entire
hierarchy.
````

## The shape of Mathlib, and how to search it

Mathlib is a single continuously-integrated monorepo — the largest formal-mathematics library in
existence — and it supplies roughly 90% of declarations across the Lean ecosystem. You will never recall
it; you *decode* and *search* it.

**Decode.** Names read left-to-right as the shape of the conclusion in `lowerCamelCase`, namespaced by the
head symbol. From the name alone you can reconstruct the statement:

- `Nat.add_comm` — in namespace `Nat`, "add is commutative".
- `Finset.sum_range_succ` — a sum over `range (n+1)`, split at the last term.
- `Nat.Prime.eq_one_or_self_of_dvd hp m hm : m = 1 ∨ m = p` — "a divisor of a prime is one or itself."

**Search**, in four complementary modalities:

1. **In-editor tactics.** `exact?` looks for a single lemma that closes the goal; `apply?` for one that
   reduces it by one `apply`; `rw?` proposes rewrites; `simp?` reports the exact simp set it used so you
   can pin a robust `simp only [...]`.
2. **Loogle** ([loogle.lean-lang.org](https://loogle.lean-lang.org/)) — Breitner's *syntactic* engine.
   You search by *shape*: `Loogle "(_ * _) ^ _"`, by a constant that must appear, by a hypothesis
   pattern, or by the goal shape `|- _`. Complete and predictable.
3. **LeanSearch** ([leansearch.net](https://leansearch.net/)) — a neural/semantic engine you query in
   natural language or with an informal statement, for when you do not know the shape.
4. **Moogle** (Morph Labs) — embedding-based, older, similar in spirit.

The trade-off: formal engines are complete and literal; neural engines forgive vague intent. The reflex is
`exact?` first, Loogle when you can describe the shape, LeanSearch when you can only describe the idea.

````{admonition} Run it — hunt down the √2 lemma
:class: seealso
Open a Lean web editor with Mathlib (the [Lean 4 web playground](https://live.lean-lang.org/)), then:

```lean
import Mathlib
example : Irrational (Real.sqrt 2) := by exact?
```

Watch `exact?` surface `Nat.Prime.irrational_sqrt`. Or state the shape to Loogle:
`Irrational, Real.sqrt`. Both routes land on the same lemma — the search *is* the proof.
````

## The tactic zoo: automation for computation

The heart of the practice is matching each goal to the decision or normalisation procedure that *owns its
shape*, so you stop hand-rolling algebra.

| Tactic | Owns the goal shape… |
|--------|----------------------|
| `ring` / `ring_nf` | identities in a commutative (semi)ring — **uses no hypotheses** |
| `linear_combination e` | an equality that is a linear combination of hypotheses (a certificate) |
| `linarith` / `nlinarith [hints]` | linear (resp. nonlinear, via square hints) arithmetic over ordered fields |
| `omega` | linear integer/natural arithmetic — complete (Presburger) |
| `norm_num` | closed numeric goals `A = B`, `A ≤ B`, `A ≠ B` |
| `field_simp` | clear denominators, then hand off to `ring` |
| `positivity` | prove `0 < e`, `0 ≤ e`, or `e ≠ 0` structurally |
| `gcongr` | reduce `f a ⋈ f b` to `a ⋈ b` through a monotone context |
| `decide` | a `Decidable` proposition, by kernel computation |
| `simp [lemmas]` | rewrite to a normal form |

Two facts that trip newcomers. First, `ring` proves identities in the *free* commutative ring and
therefore **ignores the context**: a hypothesis-driven equality needs `linear_combination`, `nlinarith`,
or `field_simp` then `ring`. Second, `linarith` is *linear*; a nonlinear goal needs `nlinarith` fed the
right square hints.

The 2025–26 update: **`grind`**, an SMT-style tactic introduced in Lean 4.22.0, ships theory solvers
including `cutsat` (which supersedes `omega`, with model construction) and a Gröbner-basis solver; the
thin wrapper `grobner` enables only the latter for polynomial goals. **`polyrith` is retired** — its
external Sage certificate server was shut down — so the modern polynomial tools are
`grind`/`grobner`/`linear_combination`.

````{admonition} Worked example 2 — Cauchy–Schwarz and AM–GM in one line each
:class: important
The two-variable Cauchy–Schwarz inequality is a single `nlinarith`, because the gap is a perfect square,
$(a^2+b^2)(x^2+y^2) - (ax+by)^2 = (ay - bx)^2 \ge 0$ — you just hand `nlinarith` that square:

```lean
theorem cauchy_schwarz (a b x y : ℝ) :
    (a*x + b*y)^2 ≤ (a^2 + b^2) * (x^2 + y^2) := by
  nlinarith [sq_nonneg (a*y - b*x)]
```

The AM–GM inequality for two nonnegative reals is the same trick, plus the defining fact
$(\sqrt{ab})^2 = ab$:

```lean
theorem amgm (a b : ℝ) (ha : 0 ≤ a) (hb : 0 ≤ b) :
    2 * Real.sqrt (a*b) ≤ a + b := by
  nlinarith [sq_nonneg (a - b), Real.sq_sqrt (mul_nonneg ha hb),
             Real.sqrt_nonneg (a*b)]
```

Here `nlinarith` uses $(a-b)^2 \ge 0$, i.e. $(a+b)^2 \ge 4ab = (2\sqrt{ab})^2$, and the nonnegativity of
both sides to conclude $a+b \ge 2\sqrt{ab}$. Contrast a purely finite goal, closed by evaluation —
Wilson's theorem at $p = 7$: `example : Nat.factorial 6 % 7 = 6 := by decide`.
````

## `calc` — proofs that read like the blackboard

`calc` makes a formal proof read like a hand derivation: each line names an intermediate term with `_` and
justifies exactly one step. Through the `Trans` typeclass a single `calc` may *mix* relations — `=`, `≤`,
`<`, `∣`, `⊆` — chaining them to the transitive conclusion. The idiom to learn (Heather Macbeth's
pattern) alternates `have` (introduce an auxiliary fact) with `calc` (carry the computation), closing the
linear tail with `linarith`.

````{admonition} Worked example 3 — the Macbeth have/calc pattern
:class: important
Given $a^2 = b^2 + 4$ and $a + b = 2$, show $a - b = 2$. On paper: $(a-b)(a+b) = a^2 - b^2 = 4$, and since
$a+b = 2$ this gives $2(a-b) = 4$. Formalized, the prose survives intact:

```lean
example (a b : ℝ) (h1 : a^2 = b^2 + 4) (h2 : a + b = 2) : a - b = 2 := by
  have hprod : (a - b) * (a + b) = 4 := by
    calc (a - b) * (a + b) = a^2 - b^2 := by ring
      _ = 4 := by rw [h1]; ring
  rw [h2] at hprod          -- hprod : (a - b) * 2 = 4
  linarith
```

Read the `calc` block aloud and it *is* the blackboard line. `ring` does the algebra; `rw` substitutes the
hypothesis; `linarith` finishes the linear tail. This legibility is what convinces working mathematicians
the formal text is honest mathematics, not code.
````

## Recursion: structural vs. well-founded

There are two ways to define a recursive function, and which one you must use is dictated by the recursive
call.

**Structural recursion.** When every recursive call is on a *strict subterm* of the argument, the equation
compiler accepts the definition with no termination proof, elaborating it to the type's auto-generated
recursor (`brecOn`) and emitting equational lemmas usable by `simp`/`rw`. The proof-side mirror is the
`induction` tactic.

````{admonition} Worked example 4 — a tree, its size, and structural induction
:class: important
```lean
inductive Tree where
  | leaf : Tree
  | node : Tree → Tree → Tree

def Tree.size : Tree → Nat
  | .leaf     => 1
  | .node l r => 1 + l.size + r.size

theorem Tree.size_pos : ∀ t : Tree, 1 ≤ t.size
  | .leaf     => by decide
  | .node l r => by simp only [Tree.size]; omega
```

`size` recurses on the subtrees `l` and `r`, so no termination proof is needed; `size_pos` is closed
case-by-case, `omega` handling `1 ≤ 1 + l.size + r.size` once `simp only` has unfolded the definition.
This is exactly the shape of the EML project's `EMLTerm.size` you will meet in {doc}`l6_autoformalization`.
````

The `induction` tactic surfaces the same recursor. Gauss's summation formula falls to it directly:

```lean
theorem gauss_sum (n : Nat) :
    2 * (∑ k ∈ Finset.range (n+1), k) = n * (n+1) := by
  induction n with
  | zero => simp
  | succ n ih => rw [Finset.sum_range_succ, Nat.mul_add, ih]; ring
```

**Well-founded recursion.** When the decreasing argument is *not* a literal subterm — the classic case is
Euclid's `gcd`, which recurses on `y % (x+1)` — you must supply a measure with `termination_by` and a
proof that it strictly decreases in a well-founded order with `decreasing_by`. Lean then builds the
definition through `WellFounded.fix`.

```lean
def mygcd : Nat → Nat → Nat
  | 0,     y => y
  | x + 1, y => mygcd (y % (x + 1)) (x + 1)
termination_by a _ => a
decreasing_by exact Nat.mod_lt _ (Nat.succ_pos x)
```

The obligation is exactly $y \bmod (x+1) < x+1$, discharged by `Nat.mod_lt`. Contrast `partial def`, which
sidesteps the termination checker and the kernel entirely: it is fine for tooling but produces **no
equation lemmas**, so you can prove *nothing* about it.

## One theorem end-to-end: √2 is irrational

Bring the pieces together on a real theorem. Standing on the library, it is one line:

```lean
theorem sqrt2_irrational : Irrational (Real.sqrt 2) := by
  exact_mod_cast Nat.Prime.irrational_sqrt (p := 2) Nat.prime_two
```

`Nat.Prime.irrational_sqrt` gives `Irrational (Real.sqrt ↑p)` for a prime `p`; `exact_mod_cast` bridges
the coercion $\uparrow(2:\N) : \R$ to the literal `2`. But the *instructive* proof reconstructs the
classical argument, and every step is a tactic you now own. Suppose for contradiction $\sqrt 2 = p/q$ in
lowest terms. Squaring gives

$$2 q^2 = p^2 \;\Rightarrow\; 2 \mid p^2 \;\Rightarrow\; 2 \mid p \;\Rightarrow\; 4 \mid p^2 = 2q^2 \;\Rightarrow\; 2 \mid q,$$

contradicting $\gcd(p,q) = 1$. In Lean the skeleton is `by_contra h` to assume $\neg$goal, then extraction
of the rational witness, then a parity contradiction driven by `omega` and divisibility lemmas. The lesson
is the two idioms side by side: *stand on Mathlib* when the lemma exists, *build it yourself* when you need
to see the machinery.

```{admonition} It's checked — the "build it yourself" version, verified
:class: seealso
This course ships the *Mathlib-free* descent as a machine-checked artifact:
[`artifacts/lean/Artifacts/Sqrt2.lean`](https://github.com/nasqret/vietnam2026/blob/main/artifacts/lean/Artifacts/Sqrt2.lean)
proves `no_sqrt2 : ∀ p q : Nat, p * p = 2 * (q * q) → q = 0` by infinite descent in Lean 4 core — no
library — so `lake build` stays fast, and `#print axioms no_sqrt2` reports only `propext` and
`Quot.sound`. The single engine is `even_sq_iff` (a square is even iff its root is); everything else is
strong induction. Read it next to the one-line Mathlib proof above: the same theorem, *stood on the
library* and *built from nothing*, side by side.
```

Euler's identity is an alternative where all the analytic depth hides inside a single library lemma:

```lean
theorem euler_identity :
    Complex.exp (Real.pi * Complex.I) + 1 = 0 := by
  rw [Complex.exp_pi_mul_I]; ring
```

```{admonition} Run it — the same statement in four foundations
:class: seealso
The course ships the *same* small statements — the S combinator, Peano addition, commutativity, a tiny
evaluator — in **four provers**, so you can watch different foundations do one job:
[Lean 4](https://github.com/nasqret/vietnam2026/blob/main/artifacts/lean/Artifacts.lean),
[Rocq](https://github.com/nasqret/vietnam2026/blob/main/artifacts/rocq/Artifacts.v),
[Agda](https://github.com/nasqret/vietnam2026/blob/main/artifacts/agda/Artifacts.agda), and
[Mizar](https://github.com/nasqret/vietnam2026/blob/main/artifacts/mizar/artifact.miz).
Build the Lean one with `lake build`; the run finishes `sorry`-free with **no axioms** (`#print axioms`).
```

## A glimpse under the hood: macros and elaboration

Lean 4 is written in Lean 4, and *your* code can run at every stage of the pipeline that turns text into a
theorem:

```text
parse  ──▶  macro-expand  ──▶  elaborate  ──▶  kernel type-check
(syntax)   (macro/           (elab: Syntax     (the sole
            macro_rules,       → Expr in         arbiter of
            purely             MetaM/TermElabM)  theoremhood)
            syntactic)
```

The `syntax` command adds grammar; `macro`/`macro_rules` rewrite syntax to syntax; `elab`/`elab_rules`
turn syntax into an `Expr` — the kernel's term datatype (`bvar`, `const`, `app`, `lam`, `forallE`, …);
and only the kernel's acceptance of that `Expr` makes it a theorem. A three-line macro adds a new tactic:

```lean
macro "split_and" : tactic => `(tactic| refine ⟨?_, ?_⟩)

example (p q : Prop) (hp : p) (hq : q) : p ∧ q := by
  split_and
  · exact hp
  · exact hq
```

After expansion `split_and` is ordinary `Expr`-building, kernel-checked like everything else. The
punchline ties the whole lecture together: term mode and tactic mode, `simp` and `grind`, your macro and
Mathlib's — all of them produce the *same kind of object*, an `Expr`, and the kernel is the only thing
that confers theoremhood. That is the de Bruijn criterion, and it is what makes
{doc}`Lecture 6 <l6_autoformalization>`'s research-scale formalization trustworthy: 8,062 build jobs,
zero `sorry`, audited by `#print axioms`.

## Common pitfalls

- **`Prop` is not `Type`.** You cannot pattern-match a proof of `∃ n, P n` to pull the witness `n` out as
  computational data — the large-elimination restriction blocks it, precisely because proof irrelevance
  would otherwise leak a non-computational choice.
- **`rfl`, `=`, and `↔` are not interchangeable.** `rfl` closes only goals true *by computation or
  definition*, not every true equation. Definitional equality is stronger than propositional equality.
- **`ring` ignores your hypotheses.** It proves identities in the free commutative ring. A
  hypothesis-driven equality needs `linear_combination`, `nlinarith`, or `field_simp` + `ring`.
- **`linarith` on a nonlinear goal fails.** Feed `nlinarith` the right square hints (`sq_nonneg (a - b)`),
  or use the `grind`/`grobner` family.
- **Do not reach for `polyrith`** — it is retired (its Sage server was shut down). Use
  `grind`/`grobner`/`linear_combination`.
- **`simp` can loop or over-rewrite.** Use `simp?` to see and then pin the exact lemma set with
  `simp only [...]` for a robust, reproducible proof.
- **A tactic proof is not "weaker" than a term proof.** After elaboration both are the identical
  kernel-checked `Expr`.
- **Coercion blindness.** Mixing $\N/\Z/\Q/\R$ produces `↑` arrows; goals often need `push_cast`,
  `norm_cast`, or `exact_mod_cast` to align types.
- **"Failed to synthesize instance"** usually means a missing `import`/`open`, an unregistered instance, or
  a diamond where two paths give non-defeq instances.
- **Recursion traps.** Structural recursion demands a genuine subterm; anything else needs
  `termination_by`/`decreasing_by`. And `partial def` escapes the kernel, generating no equation lemmas —
  you can prove nothing about it.
- **Don't guess lemma names from memory.** With ~351k declarations, `exact?`, Loogle, and LeanSearch are
  the intended workflow, not rote recall.

## Exercises

1. **(paper)** Explain in one paragraph why `∀ n : ℕ, P n` and `(n : ℕ) → P n` are literally the same
   type in Lean, and give the degenerate case in which a Π-type is an ordinary function type.
2. **(Lean, easy)** Prove `∀ P Q : Prop, P ∧ Q → Q ∧ P` twice — once as a bare term
   `fun ⟨hp, hq⟩ => ⟨hq, hp⟩`, once with `intro`/`obtain`/`constructor`. Run `#print axioms` on both and
   confirm the footprint is empty and identical.
3. **(Lean, easy)** Reproduce Worked Example 4: define `Tree`, `Tree.size`, and prove `Tree.size_pos`,
   closing each case with `decide`/`omega`. Then state and prove `size (node t t) = 2 * size t + 1`.
4. **(Lean, easy–medium)** One goal per tactic family: prove the Cauchy–Schwarz inequality with
   `nlinarith [sq_nonneg (a*y - b*x)]`; `gauss_sum` with `induction … ; ring`; and
   `Nat.factorial 6 % 7 = 6` with `decide`.
5. **(Lean, medium)** Search skill: state `theorem sqrt2 : Irrational (Real.sqrt 2) := by sorry`, use
   `exact?` **and** a Loogle query to discover `Nat.Prime.irrational_sqrt`, then finish with
   `exact_mod_cast …`. Submit the Loogle query you used.
6. **(Lean, medium)** Build the `MyAddMonoid` class from Worked Example 1, give the `Nat` instance, and
   prove a *new* lemma stated only from the interface — e.g. `add zero (add zero a) = a`. Confirm the
   proof never names `Nat`.
7. **(Lean, medium–hard)** *Hard.* Define `mygcd` with `termination_by`/`decreasing_by` (you will need
   `Nat.mod_lt`), and prove `theorem mygcd_dvd_left (a b) : mygcd a b ∣ a`. Then write a `partial def`
   version and explain, in one sentence, why you cannot prove the same lemma about it.
8. **(Lean, hard)** *Hard.* Write `macro "split_and" : tactic => …` and use it to prove a conjunction.
   Then trace the four pipeline stages for your proof (parse → macro-expand → elaborate → kernel) and say
   which stage your macro runs in.

## References

- J. Avigad, K. Buzzard, R. Y. Lewis, P. Massot, [*Mathematics in Lean*](https://leanprover-community.github.io/mathematics_in_lean/) — the standard hands-on course for real mathematics in Lean 4 + Mathlib.
- J. Avigad, L. de Moura, S. Kong, S. Ullrich, [*Theorem Proving in Lean 4*](https://leanprover.github.io/theorem_proving_in_lean4/) — the authoritative reference for dependent types, the `Prop`/`Type` hierarchy, proof irrelevance, structures, and typeclass resolution.
- H. Macbeth, [*The Mechanics of Proof*](https://hrmacbeth.github.io/math2001/) — the gentlest route into `calc`, `have`, `rw`, `linarith`, `ring`, and `induction` for a mathematically mature audience.
- H. Macbeth, [*Algebraic Computations in Lean*](https://hrmacbeth.github.io/computations_in_lean/) — the dedicated reference for the computation-tactic zoo (`field_simp`, `ring`, `nlinarith`, `linear_combination`, `positivity`).
- A. Baanen et al., [*Metaprogramming in Lean 4*](https://leanprover-community.github.io/lean4-metaprogramming-book/) — `syntax`, `macro`, `elab`, the `Expr` datatype, and the elaboration monads.
- Lean community, [*Searching for theorems in Mathlib*](https://leanprover-community.github.io/blog/posts/searching-for-theorems-in-mathlib/); [Loogle](https://loogle.lean-lang.org/) and [LeanSearch](https://leansearch.net/).
- [Mathlib4 API docs](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Tactic/Polyrith.html) (Polyrith retirement) and the [Lean release notes](https://lean-lang.org/doc/reference/latest/releases/) (`grind` in v4.22.0; current scale on the [Mathlib use-case page](https://lean-lang.org/use-cases/mathlib/)).
- The course's [four-prover artifacts](https://github.com/nasqret/vietnam2026/tree/main/artifacts) and the [EML formalization](https://github.com/nasqret/eml-formalization) previewed in {doc}`l6_autoformalization`.
```
