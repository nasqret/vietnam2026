# Lecture 3 — Propositional logic proofs

```{admonition} Abstract
:class: tip
We learn to *prove* — and to see a proof as a program. Natural deduction for propositional logic, the
**BHK interpretation**, and the **Curry–Howard** reading of the connectives: implication is a function,
conjunction a product, disjunction a sum, negation a function into the empty type. We do it hands-on
through Emily Riehl's Lean game **[A Reintroduction to Proofs](https://adam.math.hhu.de/#/g/emilyriehl/ReintroductionToProofs)**,
mapping each level to an inference rule, and we mark precisely where **intuitionistic** reasoning ends
and **classical** logic begins.
```

## Learning objectives

- State Gentzen's introduction and elimination rules for $\To, \land, \lor, \bot$ (and derived
  $\neg, \top$), and read a rule as premises-over-conclusion with hypothesis discharge.
- Explain the Brouwer–Heyting–Kolmogorov (BHK) meaning of each connective and use it to judge whether a
  formula is *intuitionistically* valid.
- Articulate the Curry–Howard dictionary — $\To$ a function type, $\land$ a product, $\lor$ a sum,
  $\bot$ the empty type, $\neg A = A\To\bot$ — and read a proof term as the program that witnesses a
  proposition.
- Map each Lean tactic (`intro`, `exact`, `apply`, `constructor`, `rcases`/`obtain`, `left`/`right`,
  `exfalso`, `by_contra`) to the exact rule or term-former it performs.
- Produce `sorry`-free proofs of representative theorems: $\land$/$\lor$-symmetry, currying,
  $A\To\neg\neg A$, $\neg\neg\neg A\To\neg A$, and a De Morgan law.
- Identify $A\lor\neg A$, $\neg\neg A\To A$ and Peirce's law as the classical boundary, and justify
  exactly when `by_contra` is genuinely required.

## Why this matters

A first logic course usually *decides* propositional formulas with truth tables: a tautology is a
formula true under every valuation, and that is that. A proof assistant cannot work this way. Its kernel
does not evaluate a table; it checks a **derivation** — a syntactic object built from a fixed stock of
inference rules. So before Lean can help us with real mathematics we must answer a deceptively simple
question, the one that opens this lecture: *what, precisely, is a proof?*

The answer that makes machine-checked mathematics possible is that a proof is a **construction**, and a
construction is a **typed program**. This is the Curry–Howard correspondence, glimpsed already in
{doc}`Lecture 2 <l2_lambda_calculus>` as the slogan *proofs = programs*. This lecture turns the slogan
into a working dictionary: every connective becomes a type former, every inference rule becomes a
term former, and every Lean tactic becomes a recipe that fills a hole in a proof term. The same moves
you learn here on toy propositions are, unchanged, the moves that build the hundred kernel-checked
theorems of the {doc}`Lecture 6 <l6_autoformalization>` research formalization.

## Natural deduction for propositional logic

Gentzen's calculus (1934/35) gives each connective **introduction** rules (how to *prove* it) and
**elimination** rules (how to *use* it). A *derivation* is a finite tree whose leaves are assumptions
and whose internal nodes are rule instances; the formula at the root is the conclusion. We write a rule
as premises over conclusion.

Implication is the subtle one, because its introduction **discharges** a hypothesis. The bracket $[A]$
marks an assumption that is "used up" — closed off — by the rule below it:

$$
\frac{\begin{array}{c}[A]\\ \vdots\\ B\end{array}}{A\To B}\;{\To}I
\qquad\qquad
\frac{A\To B \qquad A}{B}\;{\To}E
$$

The elimination rule ${\To}E$ is *modus ponens*. Conjunction and disjunction follow the same
premises-over-conclusion pattern:

$$
\frac{A \qquad B}{A\land B}\;{\land}I
\qquad
\frac{A\land B}{A}\;{\land}E_1
\qquad
\frac{A\land B}{B}\;{\land}E_2
$$

$$
\frac{A}{A\lor B}\;{\lor}I_1
\qquad
\frac{B}{A\lor B}\;{\lor}I_2
\qquad
\frac{A\lor B \qquad
      \begin{array}{c}[A]\\ \vdots\\ C\end{array} \qquad
      \begin{array}{c}[B]\\ \vdots\\ C\end{array}}{C}\;{\lor}E
$$

Disjunction elimination is **case analysis**: to *use* $A\lor B$ toward a goal $C$ you must handle both
possibilities, and each case may discharge its own assumption. Falsity has an elimination but, tellingly,
**no introduction** — that absence is the whole point:

$$
\frac{\bot}{C}\;{\bot}E \quad(\text{ex falso quodlibet}).
$$

Negation is *derived*: $\neg A := A\To\bot$, so the rules for $\neg$ are exactly ${\To}I$ and ${\To}E$
specialized to conclusion $\bot$. Likewise $\top := \bot\To\bot$ (or a primitive with a single trivial
proof).

```{admonition} Harmony and normalization
:class: note
Introduction and elimination are in **harmony**: an introduction immediately followed by the matching
elimination is a *detour* that can be removed. For conjunction, ${\land}E_1$ applied to ${\land}I$ of
$A$ and $B$ simply returns the $A$ you started with. Prawitz proved that removing all such detours
*normalizes* a derivation, and — the punchline of the lecture — under Curry–Howard **detour removal is
exactly $\beta$-reduction**. Simplifying a proof is running a program.
```

## BHK: what a proof *is*

The Brouwer–Heyting–Kolmogorov interpretation reads each connective as a **recipe for constructions**,
not as a truth value. This is the conceptual pivot: "proof" becomes a first-class object, which is
exactly why it can later be a Lean term.

- A proof of $A\land B$ is a **pair** $\langle a,b\rangle$: a proof $a$ of $A$ together with a proof $b$
  of $B$.
- A proof of $A\lor B$ is a **tagged** proof $(i,p)$: a bit $i\in\{0,1\}$ choosing a disjunct, plus a
  proof $p$ of that disjunct.
- A proof of $A\To B$ is a **function** turning any proof of $A$ into a proof of $B$.
- There is **no** proof of $\bot$.
- A proof of $\neg A = A\To\bot$ is a function turning any putative proof of $A$ into a proof of $\bot$.

Two clauses do the real work. The disjunction clause forces you to *know which side holds*: to assert
$A\lor B$ constructively you must exhibit the tag. That is why there is, in general, no construction
witnessing $A\lor\neg A$ — you would need to actually decide $A$. And the negation clause explains a
common stumble: $\neg A$ is not "the truth value false"; it is a **map** $A\to\bot$, something you
*apply*, never something you *evaluate*.

## Curry–Howard for the connectives

BHK's "constructions" are literally typed terms. This extends the dictionary of {doc}`Lecture 2
<l2_lambda_calculus>` (and of the course's `08_curry_howard` notebook) from $\To$ and $\land$ to $\lor$,
$\bot$ and $\neg$:

| Logic | Type theory | Introduce | Eliminate |
|-------|-------------|-----------|-----------|
| $A \To B$ | function $A \to B$ | $\lam$-abstraction `fun a => …` | application $f\,a$ |
| $A \land B$ | product $A \times B$ | pairing $\langle a,b\rangle$ | projections $\pi_1,\pi_2$ |
| $A \lor B$ | sum $A + B$ | injections $\mathsf{inl},\mathsf{inr}$ | case analysis |
| $\bot$ | empty type $\varnothing$ | — (no intro) | $\mathsf{absurd}$ / `False.elim` |
| $\neg A$ | $A \to \varnothing$ | assume $A$, derive $\bot$ | apply to a proof of $A$ |
| $\top$ | unit type $\mathbf 1$ | the sole point `trivial` | — |

*Provability becomes inhabitation*: $A$ is provable iff the type $A$ has a closed term. In Lean, `And`
is a structure (product), `Or` is an inductive type with two constructors `Or.inl`/`Or.inr` (sum),
`False` is the inductive type with **no** constructors, and `True` has one.

```{admonition} Theorem (Howard 1969/1980; Prawitz)
:class: important
Closed normal terms of the simply-typed $\lam$-calculus with products, sums and the empty type —
normal for $\beta$ together with the *permutative (commuting) conversions* required for
$\lor$-elimination and $\bot$-elimination — are in bijection with Prawitz-normal natural-deduction
derivations of intuitionistic propositional logic, and this bijection carries **detour reduction
($\beta$ together with permutative conversions) to proof normalization**. In particular the calculus
is *strongly normalizing*, so there is **no** closed term of type $\bot$ — the proof system is
consistent.
```

### Worked example 1 — conjunction is commutative

Here is the full derivation of $A\land B\To B\land A$. We open the hypothesis $A\land B$, project twice,
repackage, then discharge:

$$
\frac{\dfrac{\dfrac{[A\land B]}{B}\;{\land}E_2 \qquad \dfrac{[A\land B]}{A}\;{\land}E_1}{B\land A}\;{\land}I}{(A\land B)\To(B\land A)}\;{\To}I
$$

Read off the proof term by naming the discharged hypothesis $h$ and the projections $h.1,h.2$: the
program is $\lam h.\,\langle h.2,\,h.1\rangle$. In Lean, term mode and tactic mode build the *same*
kernel object:

```lean
-- term mode: the proof IS the program
theorem and_comm' {P Q : Prop} : P ∧ Q → Q ∧ P :=
  fun h => ⟨h.2, h.1⟩

-- tactic mode: a recipe that fills the same hole
theorem and_comm'' {P Q : Prop} : P ∧ Q → Q ∧ P := by
  intro h            -- goal Q ∧ P, with h : P ∧ Q      (→I / λ)
  obtain ⟨p, q⟩ := h  -- destructure the pair            (∧E)
  exact ⟨q, p⟩        -- build the swapped pair           (∧I)
```

The disjunction analogue is the same shape with case analysis instead of projection: from `h : P ∨ Q`,
`rcases h with p | q` splits into two goals, closed by `Or.inr p` and `Or.inl q` respectively.

### Worked example 2 — currying is the exponential adjunction

The two ways of taking two hypotheses are interderivable:

$$
(A\land B\To C)\;\;\cong\;\;(A\To B\To C).
$$

Left to right (*curry*) and right to left (*uncurry*) are one-line programs — and they are exactly the
product/exponential adjunction $\mathrm{Hom}(A\times B, C)\cong\mathrm{Hom}(A, C^{B})$ read as terms:

```lean
theorem curry   {P Q R : Prop} : (P ∧ Q → R) → (P → Q → R) :=
  fun f p q => f ⟨p, q⟩
theorem uncurry {P Q R : Prop} : (P → Q → R) → (P ∧ Q → R) :=
  fun g h => g h.1 h.2
```

Note that $\To$ is **right-associative and curried**: $P\To Q\To R$ means $P\To(Q\To R)$ and eats its
arguments one at a time — the K/S combinator shape from {doc}`Lecture 2 <l2_lambda_calculus>`.

### Worked example 3 — negation, constructively

Three theorems about $\neg$ that people wrongly assume need classical logic. All are pure
constructions. Recall $\neg\neg A = (A\To\bot)\To\bot$.

$$
A\To\neg\neg A,\qquad \neg(A\land\neg A),\qquad \neg\neg\neg A\To\neg A.
$$

```lean
theorem dni  {P : Prop} : P → ¬¬P            := fun p k => k p
theorem noncontra {P : Prop} : ¬(P ∧ ¬P)     := fun h => h.2 h.1
theorem tne  {P : Prop} : ¬¬¬P → ¬P          := fun h p => h (fun k => k p)
```

Trace `dni`: given `p : P` we must produce a term of `¬¬P = (P → False) → False`, i.e. a function
`k : P → False ↦ (k p : False)` — literally *apply the continuation to the proof*. The converse
$\neg\neg A\To A$ is the one that is **not** available here; it is double-negation elimination, and it is
the classical boundary in disguise (see below).

```{admonition} Run it — Algorithm W rediscovers double negation
:class: tip
Strip the types away and `dni` is the untyped term $\lam p\,k.\,k\,p$. Ask the lab for its principal
type: [`ch term \p k. k p`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20term%20%5Cp%20k.%20k%20p)
runs Algorithm W and reports $\alpha\To(\alpha\To\beta)\To\beta$ — read the result atom $\beta$ as
$\bot$ and this *is* $A\To\neg\neg A$. Same game for `tne`:
[`ch term \h p. h (\k. k p)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20term%20%5Ch%20p.%20h%20%28%5Ck.%20k%20p%29).
The Curry-style moral: the *program* comes first, and the theorem it proves is its most general type.
```

### Worked example 4 — a De Morgan law, and its classical cousin

One direction-pair is fully constructive; one implication is genuinely classical.

$$
\neg(A\lor B)\;\Longleftrightarrow\;(\neg A\land\neg B)\qquad(\text{intuitionistic, both directions})
$$

$$
\neg(A\land B)\;\To\;(\neg A\lor\neg B)\qquad(\text{classical only}).
$$

The constructive equivalence, as a single proof term, uses only $\lor$-elimination and function
application:

```lean
theorem deMorgan_or {P Q : Prop} : ¬(P ∨ Q) ↔ (¬P ∧ ¬Q) :=
  ⟨fun h => ⟨fun p => h (Or.inl p), fun q => h (Or.inr q)⟩,
   fun ⟨np, nq⟩ h => h.elim np nq⟩
```

The forward map takes `h : ¬(P ∨ Q)` and builds each conjunct by feeding it an injection; the backward
map takes `⟨np, nq⟩` and an alleged `h : P ∨ Q` and case-splits. The *other* De Morgan direction,
$\neg(A\land B)\To(\neg A\lor\neg B)$, cannot be a term: to output the sum you would have to pick a tag,
i.e. decide which conjunct fails, and BHK forbids that without more information. It needs excluded
middle.

## Lean tactics as proof-term construction

The bilingual claim of the lecture: **every tactic is a recipe that builds a piece of the proof term**.
A tactic transforms the goal state (a context of hypotheses $\Gamma$ and a target $\vdash A$) *and*
appends to the underlying term. Here is the dictionary that the whole live session runs on.

| Tactic | Natural-deduction rule | Term action | Effect on goal |
|--------|------------------------|-------------|----------------|
| `intro h` | ${\To}I$ (discharge) | $\lam h.\,?$ | $A\To B\;\leadsto\;B$ with `h : A` |
| `exact e` | assumption / close | plug in $e$ | closes the goal |
| `apply f` | ${\To}E$ backward | build $f\,?$ | $Q\leadsto P$ when `f : P → Q` |
| `constructor` / `⟨a,b⟩` | ${\land}I$ | pair | $A\land B\leadsto A,\;B$ |
| `rcases`/`obtain h with …` | ${\land}E$, ${\lor}E$, ${\bot}E$ | project / match | destructure (0, 1 or 2 subgoals) |
| `left` / `right` | ${\lor}I_1$ / ${\lor}I_2$ | $\mathsf{inl}$ / $\mathsf{inr}$ | $A\lor B\leadsto A$ (or $B$) |
| `exfalso` | ${\bot}E$ | `False.elim ?` | replaces any goal by $\bot$ |
| `by_contra h` | classical (¬¬-elim) | `Classical.byContradiction` | goal $A\leadsto\bot$ with `h : ¬A` |

The single crucial warning: `by_contra` is **not** a natural-deduction rule. It is the classical axiom
$\neg\neg A\To A$ wearing a tactic's clothes. Everything above it in the table is constructive; only the
last row leaves the intuitionistic fragment. And do not confuse it with `exfalso`: `exfalso` is
${\bot}E$ ("from $\bot$, anything"), always valid; `by_contra` is "assume $\neg$goal, derive $\bot$",
which is where classical logic enters.

```{admonition} Run it — drive the tactics yourself
:class: seealso
The [Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda) has an interactive proof builder
that speaks exactly the implication rows of this table. Open
[`prove (P -> Q) -> P -> Q`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=prove%20%28P%20-%3E%20Q%29%20-%3E%20P%20-%3E%20Q)
and close the goal with `intro`, `apply` and `exact` (`hint` nudges you when stuck, `undo` backtracks).
On `qed` the lab **extracts the λ-term you just built** and infers its principal type — the "term
action" column of the table made visible: every tactic appended exactly one node to the program.
```

```{admonition} Run it — see a tactic fill a hole
:class: seealso
Copy the four worked theorems above into the game's editor or any Lean playground and watch the goal
state change line by line. Or feel the "proof = program" identity in the untyped world of the
[Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda): the $\land$-elimination rule *is*
projection —
[`reduce FST (PAIR a b)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=reduce%20FST%20%28PAIR%20a%20b%29)
computes to `a` — and modus ponens *is* application, which you can watch by reducing the S-combinator
proof term $\lam f\,g\,x.\,f\,x\,(g\,x)$ on concrete "proofs". The same statement is proved in all four
provers in the [artifacts directory](https://github.com/nasqret/vietnam2026/tree/main/artifacts)
([Lean](https://github.com/nasqret/vietnam2026/blob/main/artifacts/lean/Artifacts.lean),
[Agda](https://github.com/nasqret/vietnam2026/blob/main/artifacts/agda/Artifacts.agda),
[Rocq](https://github.com/nasqret/vietnam2026/blob/main/artifacts/rocq/Artifacts.v),
[Mizar](https://github.com/nasqret/vietnam2026/blob/main/artifacts/mizar/artifact.miz)).
```

## The game, world by world

Riehl's *A Reintroduction to Proofs* is a Lean 4 game (17 worlds, MIT-licensed, built for a Fall-2025
first-year seminar at Johns Hopkins, pinned to Lean `v4.23.0`) that runs entirely in the browser on the
Lean Game Server. Its design is a gift to this lecture: it **front-loads the constructive core** and
**quarantines classical logic** in a single world reached only at the end. It even studies the `Empty`
type *before* negation, so that $\neg P$ arrives as an already-understood $P\To\bot$ rather than a
mysterious primitive.

For a propositional-logic session, play this dependency chain (deferring the quantifier, arithmetic and
equality worlds to later lectures):

- **TypeWorld** — `p : P` means "$p$ is a proof of $P$"; meet `exact`, `assumption`.
- **FunctionWorld / ImplicationWorld** — $\To$ as a function; the identity proof `fun p => p`,
  composition, and `intro`/`apply`/`exact`.
- **ProductWorld / ConjunctionWorld** — `constructor`, `⟨_,_⟩`, projections; $\land$-symmetry and
  associativity.
- **CoproductWorld / DisjunctionWorld** — `left`/`right`, `obtain`/`rcases`; $\lor$-symmetry.
- **EmptyWorld** — `Empty → A` by `intro p; cases p` (elimination with zero constructors).
- **NegationWorld** — $\neg P := P\To\bot$, ex falso, and the three constructive negation theorems of
  Worked Example 3.
- **ClassicalWorld** — and only here: `by_contra`, `Classical.em`.

```{admonition} Run it — play the constructive core
:class: seealso
Open [A Reintroduction to Proofs](https://adam.math.hhu.de/#/g/emilyriehl/ReintroductionToProofs) and
clear TypeWorld → FunctionWorld → ImplicationWorld, then Conjunction/DisjunctionWorld, then
Empty/NegationWorld — *without touching* ClassicalWorld. After each world, return to the tactic table
above and name the row you just used. Nothing to install; it runs in the browser on the same engine as
the {doc}`Natural Number Game <l4_lean_intro>`.
```

## The classical boundary

Everything so far lived in the intuitionistic fragment. The following are equivalent over intuitionistic
propositional logic — adding any one recovers full classical logic:

$$
\text{excluded middle } A\lor\neg A,\qquad
\text{double-negation elim } \neg\neg A\To A,\qquad
\text{Peirce's law } ((A\To B)\To A)\To A.
$$

None of the three is constructively provable, precisely because each would let you manufacture a
disjunction tag (or a witness) out of thin air. Lean keeps them out of its computational core and offers
them as the axiom `Classical.em : ∀ P, P ∨ ¬P`, which `by_contra` invokes.

### Worked example 5 — Peirce's law needs `by_contra`

$$
((A\To B)\To A)\To A.
$$

Classically it is a two-move proof; constructively it has no proof term at all.

```lean
theorem peirce {P Q : Prop} : ((P → Q) → P) → P := by
  intro h
  by_contra hnp                     -- hnp : ¬P, goal : False
  exact hnp (h (fun p => absurd p hnp))
```

Trace it: `hnp : ¬P`; from it we can prove *anything*, so `fun p => absurd p hnp : P → Q`; feeding that
to `h` yields `P`; feeding *that* to `hnp` yields `False`. Every step but `by_contra` is constructive —
the classical content is isolated in exactly one move.

Contrast this with the honest fact that no tactic-free, `fun`-only term of that type exists:

```{admonition} Theorem (no intuitionistic witness)
:class: warning
There is no closed simply-typed $\lam$-term of type $((A\To B)\To A)\To A$ for atomic $A\neq B$. *Sketch:*
by strong normalization it suffices to inspect $\beta$-normal, $\eta$-long inhabitants. Such a term must
begin $\lam h.\,t$ with $h:(A\To B)\To A$ and $t:A$; the only way to reach an $A$ is $h\,u$ with
$u:A\To B$, i.e. $u=\lam a.\,s$ with $a:A,\ s:B$; but $B$ is a fresh atom with no closed inhabitant and
nothing in context produces one — the search loops with no base case. Hence Peirce's law is not
intuitionistically derivable.
```

This is what the Curry–Howard lab reports:
[`ch type '((P -> Q) -> P) -> P'`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20type%20%27%28%28P%20-%3E%20Q%29%20-%3E%20P%29%20-%3E%20P%27)
answers *not inhabited in intuitionistic STLC*. Feel the sketch's dead end yourself with
[`ch build '((P -> Q) -> P) -> P'`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=ch%20build%20%27%28%28P%20-%3E%20Q%29%20-%3E%20P%29%20-%3E%20P%27):
after `intro h`, `apply h`, `intro p` you face the goal `Q` with only proofs of `P` in scope — the
search loops with no base case, exactly as the theorem predicts. The classical proof and the
(nonexistent) constructive one are different objects, and the gap is measured exactly:

```{admonition} Theorem (Glivenko, 1929)
:class: important
For a propositional formula $A$: $\;\proves_c A\;$ iff $\;\proves_i \neg\neg A$. Classical propositional
provability embeds into intuitionistic provability under double negation. Everything classical is, quite
literally, a double negation away — which is why double-negation translations work and why `by_contra`
succeeds exactly when a $\neg\neg$-shifted goal is constructive.
```

The pedagogical cost to state plainly: a classical existence proof by `by_contra` shows *that a
counterexample cannot exist* without ever handing you the object. When you later want the witness — a
root, a bound, a construction — you must stay inside the constructive fragment.

## Common pitfalls

- **Reading $\neg P$ as a truth value.** $\neg P$ is the function type $P\To\bot$: something you
  *apply* to a proof of $P$ to get $\bot$, not something you "evaluate to false".
- **Thinking $\lor$-elimination tells you which disjunct holds.** From `h : P ∨ Q` you must handle
  **both** cases (`rcases h with p | q`); constructively you never learn the tag.
- **Assuming $A\lor\neg A$, $\neg\neg A\To A$ and Peirce's law are "obviously provable".** They are
  exactly the axioms the game quarantines in ClassicalWorld; the constructive core deliberately lacks
  them.
- **Reaching for `by_contra` reflexively.** It is a classical move. Many goals — $A\To\neg\neg A$,
  $\neg(A\land\neg A)$, both directions of $\neg(A\lor B)\Leftrightarrow\neg A\land\neg B$ — have direct
  constructive proofs, and `by_contra` merely hides that content.
- **Confusing `exfalso` with `by_contra`.** `exfalso` is ${\bot}E$ (always valid); `by_contra` assumes
  the negation of the goal (classical). Different rules that both mention `False`.
- **Direction confusion among tactics.** `constructor`/`⟨_,_⟩` *builds* a conjunction (${\land}I$) while
  `rcases`/`obtain` *uses* one (${\land}E$); `intro` moves a hypothesis in (forward) while `apply`
  reasons backward through modus ponens.
- **Treating term mode and tactic mode as different logics.** `exact ⟨p, q⟩` and `constructor` invoke
  the *same* rule ${\land}I$ and build the *same* kernel term.
- **Misparsing $P\To Q\To R$.** Implication is right-associative and curried: it means $P\To(Q\To R)$.
- **Equating a truth-table check with a proof.** A formula can be classically valid yet have no
  intuitionistic derivation and no $\lam$-term witness; Glivenko's theorem measures precisely that gap.

## Exercises

1. **(Pen & paper.)** Draw the full natural-deduction derivation of $\lor$-symmetry
   $A\lor B\To B\lor A$, marking every discharged assumption. Then read off its proof term.
2. **(Lab / Lean.)** Prove $\land$-symmetry $P\land Q\To Q\land P$ and $\lor$-symmetry
   $P\lor Q\To Q\lor P$ in the game (ConjunctionWorld and DisjunctionWorld) using `intro`,
   `obtain`/`rcases`, `left`/`right`, `exact`. Rewrite each as a single term-mode `fun … => …`.
3. **(Lean.)** Give constructive proof terms for $P\To\neg\neg P$ and $\neg\neg\neg P\To\neg P$, then try
   and fail to prove $\neg\neg P\To P$ without `by_contra`. Explain the failure via BHK.
4. **(Lean.)** Prove *both* directions of $\neg(P\lor Q)\Leftrightarrow(\neg P\land\neg Q)$
   constructively, and the one-way $(\neg P\lor\neg Q)\To\neg(P\land Q)$. Which De Morgan implication is
   missing, and why?
5. **(Lab.)** In the [Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda), evaluate
   [`reduce FST (PAIR a b)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda?cmd=reduce%20FST%20%28PAIR%20a%20b%29)
   and `reduce SND (PAIR a b)`, and explain, in one sentence each, which inference rule each reduction
   realizes under Curry–Howard.
6. **(Lean, hard.)** Prove Peirce's law $((P\To Q)\To P)\To P$ using `by_contra`. Then argue, in prose,
   why no tactic-free `fun`-only term of this type exists (use the normal-form sketch above).
7. **(Pen & paper, hard.)** Using Glivenko's theorem, show that $\neg\neg(A\lor\neg A)$ *is*
   intuitionistically provable even though $A\lor\neg A$ is not. Exhibit a proof term for
   $\neg\neg(A\lor\neg A)$.
8. **(Lean, hard.)** In ClassicalWorld, prove the four-way case exhaustion
   $(P\land Q)\lor(P\land\neg Q)\lor(\neg P\land Q)\lor(\neg P\land\neg Q)$ from `Classical.em P` and
   `Classical.em Q`. Identify the single place where classical logic is unavoidable.

## References

- [Emily Riehl, *A Reintroduction to Proofs* (Lean 4 game)](https://adam.math.hhu.de/#/g/emilyriehl/ReintroductionToProofs) — the primary object of the lecture; [source repository](https://github.com/emilyriehl/ReintroductionToProofs).
- [Emily Riehl, Fall 2025 seminar on computer-verified proof](https://emilyriehl.github.io/formalization/) — the game's design rationale (constructive-first, `Empty` before negation).
- [Philip Wadler, *Propositions as Types*, CACM 58(12):75–84, 2015](https://homepages.inf.ed.ac.uk/wadler/papers/propositions-as-types/propositions-as-types.pdf) — the definitive accessible account of Curry–Howard and normalization = $\beta$-reduction.
- [Morten Heine Sørensen & Paweł Urzyczyn, *Lectures on the Curry–Howard Isomorphism*, Elsevier 2006](https://www.sciencedirect.com/bookseries/studies-in-logic-and-the-foundations-of-mathematics/vol/149) — rigorous treatment of BHK, natural deduction and the propositional isomorphism.
- [W. A. Howard, *The formulae-as-types notion of construction* (1969/1980)](https://www.cs.cmu.edu/~crary/819-f09/Howard80.pdf) — the historical source extending Curry's observation to sums, products and the empty type.
- [Joan Moschovakis, *Intuitionistic Logic*, Stanford Encyclopedia of Philosophy](https://plato.stanford.edu/entries/logic-intuitionistic/) — BHK, Heyting's rules, and Glivenko's theorem.
- [Jeremy Avigad et al., *Theorem Proving in Lean 4* — Propositions and Proofs](https://leanprover.github.io/theorem_proving_in_lean4/propositions_and_proofs.html) — authoritative documentation for the Lean tactics used here.
- The course's own [Curry–Howard notebook `08_curry_howard`](https://github.com/nasqret/falenty-2026/tree/main/book/en) and the [four-prover artifacts](https://github.com/nasqret/vietnam2026/tree/main/artifacts).
