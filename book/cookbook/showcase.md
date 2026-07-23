# What this lab can do

This chapter is the feature parade. If you are a colleague deciding whether to put the
[Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/) in front of your own students, skim
it top to bottom: every section is a two-minute demo, every output below was produced by the actual
engine, and every command is either a clickable deep link (it opens the lab with the command pre-typed)
or a line you can paste into a running session. Nothing here is typeset by hand — including the places
where the lab says *"I don't know"*, which we consider a feature worth demonstrating on its own.

If you have sixty seconds and one click to spare, spend them on
[`tour`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=tour) — a curated sequence of
reductions with decoded values — or on the one-liner
[`nf PLUS 2 3`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%20PLUS%202%203):

```text
β-normal form · 6 step(s)
  λf x. f (f (f (f (f x))))
  = 5  (Church numeral)
```

Note the shape of the answer: the actual normal form, an honest step count, and a decoded value.
That shape — *result, cost, interpretation* — is the house style of the whole lab.

## The trace that teaches normal order

The single best classroom command is
[`reduce AND (OR TRUE FALSE) (NOT FALSE)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=reduce%20AND%20(OR%20TRUE%20FALSE)%20(NOT%20FALSE)).
It prints one line per β-step, and at every line the **next redex is highlighted in yellow** (in the
browser; this printout necessarily loses the color). Watching where the highlight sits *is* the
definition of normal order — leftmost-outermost — absorbed through the eyes rather than the ears:

```text
β-reduction (normal order · highlight = next redex)
  start:  (λp. (λq. p q p)) ((λp'. (λq'. p' p' q')) (λt. (λf. t)) (λt'. (λf'. f'))) ((λp''. p'' (λt''. (λf''. f'')) (λt'''. (λf'''. t'''))) (λt'''2. (λf'''2. f'''2)))
  →β      (λq. (λp. (λq'. p p q')) (λt. (λf. t)) (λt'. (λf'. f')) q ((λp'. (λq''. p' p' q'')) (λt''. (λf''. t'')) (λt'''. (λf'''. f''')))) ((λp''. p'' (λt'''2. (λf'''2. f'''2)) (λt'''3. (λf'''3. t'''3))) (λt'''4. (λf'''4. f'''4)))
  →β      (λp. (λq. p p q)) (λt. (λf. t)) (λt'. (λf'. f')) ((λp'. p' (λt''. (λf''. f'')) (λt'''. (λf'''. t'''))) (λt'''2. (λf'''2. f'''2))) ((λp''. (λq'. p'' p'' q')) (λt'''3. (λf'''3. t'''3)) (λt'''4. (λf'''4. f'''4)))
   ⋮
  →β      (λp. p (λt. (λf. f)) (λt'. (λf'. t'))) (λt''. (λf''. f''))
  →β      (λt. (λf. f)) (λt'. (λf'. f')) (λt''. (λf''. t''))
  →β      (λf. f) (λt. (λf'. t))
  →β      λt f. t
  β-normal form reached in 11 step(s).
  = TRUE  (Church boolean)
```

Three observations to make out loud with a class:

- **The highlight never leaves the head.** At every one of the eleven steps the yellow region is the
  leftmost-outermost application — the `AND` redex first, never the `OR` or `NOT` inside the
  arguments. Normal order attacks the function *before* the data.
- **Arguments are substituted unevaluated.** After step one, look closely: `AND = λp q. p q p`
  duplicated its still-unreduced first argument — the whole `OR TRUE FALSE` machinery appears twice
  in the term. Call-by-name really does copy work; students see the cost, not just the rule.
- **The last four steps are the payoff.** Once the Boolean skeleton is exposed, the trace collapses
  crisply to `λt f. t`, and the engine volunteers the decoding `= TRUE`. Fresh primed names
  (`t'''2`, `f'''4`, …) are the pretty-printer keeping binders unambiguous — α-renaming happening
  before your eyes.

## whnf versus nf — the laziness lesson in four lines

Weak-head normal form is what lazy languages actually compute; β-normal form is what mathematicians
usually mean. The cleanest possible contrast is one term and two commands. Click
[`whnf \x. (\y. y) z`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=whnf%20%5Cx.%20(%5Cy.%20y)%20z),
then run the second line in the same session:

```text
λ> whnf \x. (\y. y) z
Weak-head normal form · 0 step(s)
  λx. (λy. y) z

λ> nf \x. (\y. y) z
β-normal form · 1 step(s)
  λx. z
```

Four lines of output, and the entire definition is in the difference: the redex `(λy. y) z` sits
*under* the binder `λx`, so `whnf` refuses to touch it (zero steps — the term is already a weak-head
normal form), while `nf` reduces under the λ and finishes the job. There is no faster way to make the
phrase "does not reduce under a lambda" mean something.

And the companion moral — normal order never evaluates what it can discard — in one more pair:

```text
λ> nf (\x. \y. x) a OMEGA
β-normal form · 2 step(s)
  a

λ> reduce (\x. \y. x) a OMEGA
β-reduction (normal order · highlight = next redex)
  start:  (λx. (λy. x)) a ((λx'. x' x') (λx''. x'' x''))
  →β      (λy. a) ((λx. x x) (λx'. x' x'))
  →β      a
  β-normal form reached in 2 step(s).
```

The divergent Ω rides along as an argument, is never once selected as a redex, and vanishes.
An applicative-order evaluator would loop forever on this term; the lab's normal-order engine
finds the normal form in two steps. That is the normalization theorem — leftmost-outermost reaches
a normal form whenever one exists — made runnable.

## The honesty suite

Every reducer in the lab runs on an explicit budget — `reduce` displays at most 60 steps, `nf` gets
1000 β-steps and a 50,000-node cap on intermediate terms — and when a budget is hit, the lab says so
in so many words. It never rounds a partial result up to an answer. Three demonstrations:

**Ω has no normal form, and the lab does not pretend otherwise.**
[`nf OMEGA`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%20OMEGA):

```text
Reduction limit reached after 1000 β-step(s)
  Step limit reached. This is not claimed to be a normal form:
  (λx. x x) (λx'. x' x')
```

One thousand steps in, the term is *exactly what it was at the start* — the fixed point of futility —
and the report is careful to label it "not claimed to be a normal form".

**The node guard trips on size, not time.**
[`nf 24 24`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%2024%2024) asks for the
Church numeral of 24²⁴ ≈ 1.3 × 10³³ — a normal form with more applications than there are grams in
the Earth. The engine notices after three β-steps that the intermediate term has blown through
50,000 AST nodes:

```text
Reduction limit reached after 3 β-step(s)
  Intermediate term exceeded the AST size limit. This is not claimed to be a normal form:
  λx x0. (λx0'. (λf x'. f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f x')))))))))))))))))))))))) ((λf' x''. f' (f' (f' (f' (f' (f' (f' …
   ⋮
   … [269540 characters omitted]
```

(The trailing "characters omitted" marker is the engine's own display cap, appended by the lab
itself — even the *rendering* is budgeted and says so.)

**Convertibility checks inherit the honesty.**
[`equiv OMEGA = OMEGA`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=equiv%20OMEGA%20%3D%20OMEGA)
is a question whose answer is "yes" for silly syntactic reasons — the two sides are identical — but
`equiv` decides β-convertibility *by normal forms*, and neither side has one:

```text
Inconclusive: at least one side did not reach β-normal form within the limit.
```

"Inconclusive" is the exactly right word, and it doubles as a lesson: β-equality of arbitrary terms
is undecidable, so a terminating tool must sometimes shrug. The lab shrugs in writing.

````{admonition} Why we teach with the limits, not around them
:class: note
The budgets are not an embarrassment to hide; they are the discussion.
- [`nf OMEGA`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%20OMEGA) — non-termination reported as a step limit, term unchanged after 1000 steps.
- [`nf 24 24`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%2024%2024) — astronomical *size* caught by the 50k-node guard after only 3 steps.
- [`equiv OMEGA = OMEGA`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=equiv%20OMEGA%20%3D%20OMEGA) — undecidability surfacing as an honest "inconclusive".
````

## The full Curry–Howard loop in sixty seconds

This is the demo that sells the lab to logicians. We will prove

$$
(P \to Q) \to (Q \to R) \to P \to R
$$

tactic by tactic, watch the proof *term* grow hole by hole, extract it, re-infer its type from
scratch, and land in the Lean web editor — the whole propositions-as-types story in one terminal
session. Start with
[`prove (P -> Q) -> (Q -> R) -> P -> R`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=prove%20(P%20-%3E%20Q)%20-%3E%20(Q%20-%3E%20R)%20-%3E%20P%20-%3E%20R)
and follow along:

```text
λ> prove (P -> Q) -> (Q -> R) -> P -> R
Proof builder  —  ⊢ (P → Q) → (Q → R) → P → R

Goal 1/1
  Context: (empty)
  Target:  (P → Q) → (Q → R) → P → R
  Term:    ?₀

λ> hint
Hint: try `exact λp q r. q (p r)`.

λ> intro f
Goal 1/1
  Context: f : P → Q
  Target:  (Q → R) → P → R
  Term:    λf. ?₁

λ> intro g
Goal 1/1
  Context: f : P → Q, g : Q → R
  Target:  P → R
  Term:    λf g. ?₂

λ> intro p
Goal 1/1
  Context: f : P → Q, g : Q → R, p : P
  Target:  R
  Term:    λf g p. ?₃

λ> apply g
Goal 1/1
  Context: f : P → Q, g : Q → R, p : P
  Target:  Q
  Term:    λf g p. g ?₄

λ> apply f
Goal 1/1
  Context: f : P → Q, g : Q → R, p : P
  Target:  P
  Term:    λf g p. g (f ?₅)

λ> exact p
All goals closed.
Type qed to extract the proof term, or undo to step back.

λ> qed
All goals closed.  QED.
  Final lambda-term: λf g p. g (f p)
  Proves:            (P → Q) → (Q → R) → P → R
  Principal type:    (α → β) → (β → γ) → α → γ
```

Things worth pausing on. The `hint` — answered by the built-in Wajsberg-style proof search — cheekily
offered the entire proof term up front; we ignored the spoiler and built it by hand, which is the
pedagogically honest order. Each tactic edits the **term**, not just the goal: `intro` wraps a λ,
`apply g` refines the hole `?₃` into `g ?₄`, and the metavariable subscripts tick upward exactly as in
Lean. And `qed` reports not only the proposition we proved but the *principal type* of the extracted
term — which we can independently confirm by handing the naked term back to the type-inference engine:

```text
λ> ch term \f. \g. \p. g (f p)
╭──────────────────────────────────── lambda-term + type ────────────────────────────────────╮
│ Term:            λf g p. g (f p)                                                           │
│ Type:            (α → β) → (β → γ) → α → γ                                                 │
│ Free variables:  -                                                                         │
│ Proof of:        Curry-Howard: this lambda-term is a proof that (α → β) → (β → γ) → α → γ. │
╰────────────────────────────────────────────────────────────────────────────────────────────╯
```

Algorithm W, run cold on the syntax with no memory of the proof session, re-derives the same type.
The loop closes in Lean. `lean s_comb` displays the S combinator — the most famous of these
implicational one-liners — together with a link that opens it, editable and checkable, in the Lean 4
web editor:

```text
λ> lean s_comb
Lean 4 · the S combinator (Curry–Howard)
  theorem s_combinator {p q r : Prop}
      (f : p → q → r) (g : p → q) (x : p) : r :=
    f x (g x)

  ▶ run it in Live Lean (click / open):
  https://live.lean-lang.org/#code=theorem%20s_combinator%20%7Bp%20q%20r%20%3A%20Prop%7D%0A%20%20%20%20%28f%20%3A%20p%20%E2%86%92%20q%20%E2%86%92%20r%29%20%28g%20%3A%20p%20%E2%86%92%20q%29%20%28x%20%3A%20p%29%20%3A%20r%20%3A%3D%0A%20%20f%20x%20%28g%20x%29
```

````{admonition} The exact theorem we just proved, in Lean
:class: seealso
Our session's theorem is a named snippet too — `lean imp_comp` prints implication-composition with
the very term the proof builder produced, modulo spelling:

```text
theorem imp_comp {P Q R : Prop} (f : P → Q) (g : Q → R) : P → R :=
  fun p => g (f p)
```

Terminal λ-term, principal type, Lean theorem, live kernel check: four notations, one object. That
is the Curry–Howard correspondence as a *workflow*, not a slogan.
````

## Guided inhabitation — and a constructive refusal

`prove` has a sibling, `ch build`, that runs the same hole-filling game from the *types* side, and it
comes with training wheels: `hint` at any point asks the inhabitation search for a way forward. Try
[`ch build P -> Q -> P`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=ch%20build%20P%20-%3E%20Q%20-%3E%20P):

```text
λ> ch build P -> Q -> P
╭───── Goal 1/1 ──────╮
│ Context:  (empty)   │
│ Target:   P → Q → P │
│ Term:     ?₀        │
╰─────────────────────╯

λ> hint
Hint: try `exact λp q. p`.

λ> intro p
╭──── Goal 1/1 ────╮
│ Context:  p : P  │
│ Target:   Q → P  │
│ Term:     λp. ?₁ │
╰──────────────────╯

λ> intro q
╭─────── Goal 1/1 ───────╮
│ Context:  p : P, q : Q │
│ Target:   P            │
│ Term:     λp q. ?₂     │
╰────────────────────────╯

λ> assumption
All goals closed.
╭─────── Proof builder ───────╮
│ Final lambda-term:  λp q. p │
╰─────────────────────────────╯
╭──────────────── Lean theorem ────────────────╮
│ theorem ch_proof {α β : Prop} : α → β → α := │
│   fun p q => p                               │
╰──────────────────────────────────────────────╯
```

The K combinator, discovered by a student in three tactics, with a Lean theorem and a Live Lean link
(elided above) falling out for free. The non-interactive form is just as useful for lectures —
`ch type (P -> Q) -> (Q -> R) -> P -> R` finds `λp q r. q (p r)` on its own and prints the
ready-to-run Lean.

But the refusals teach the most. Ask for Peirce's law,
[`ch type ((P -> Q) -> P) -> P`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=ch%20type%20((P%20-%3E%20Q)%20-%3E%20P)%20-%3E%20P):

```text
Type ((P → Q) → P) → P is not inhabited in intuitionistic STLC (classical theorems like Peirce have no constructive witness).
```

A classical tautology with **no** program behind it — the sharpest available evidence that
propositions-as-types is intuitionistic logic, delivered as an error message. Its untyped mirror
image is just as quotable:

```text
λ> ch term \x. x x
Term not typeable in STLC: Cannot unify α with α → β
```

Self-application, the engine of Ω and Y, cannot be given a simple type — the occurs check in one line.

## One lesson on names — debruijn and alpha together

The shadowing classic. Are `λx. λy. x` and `λx. λx. x` the same function dressed differently? Click
[`debruijn \x. \x. x`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=debruijn%20%5Cx.%20%5Cx.%20x)
and compare with its neighbor in the same session:

```text
λ> debruijn \x. \y. x
De Bruijn view  (indices count binders outward, from 0)
  named:    λx y. x
  nameless: λ λ 1

λ> debruijn \x. \x. x
De Bruijn view  (indices count binders outward, from 0)
  named:    λx x'. x'
  nameless: λ λ 0

λ> alpha \x. \y. x = \x. \x. x
Strict α-equivalence (no β or η reduction)
  left:  λx y. x
  right: λx x'. x'
  ≢α not alpha-equivalent

λ> alpha \x. \y. x = \a. \b. a
Strict α-equivalence (no β or η reduction)
  left:  λx y. x
  right: λa b. a
  ≡α alpha-equivalent
```

The nameless forms tell the whole story before `alpha` pronounces the verdict:
`λ λ 1` reaches for the *outer* binder, `λ λ 0` for the *inner* one — shadowing resolved by
arithmetic, no prose required. This is not just a visualization: the `alpha` command, and Lean's
kernel, decide binder identity by exactly this comparison.

```{admonition} Predict, then check
:class: tip
Before running it: what is the nameless form of the Church numeral `2`, written `\f x. f (f x)`?
```

````{admonition} Solution
:class: dropdown
The lab answers:

```text
λ> debruijn \f x. f (f x)
De Bruijn view  (indices count binders outward, from 0)
  named:    λf x. f (f x)
  nameless: λ λ 1 (1 0)
```

Both `f`s point one binder out (`1`), the `x` points at the nearest (`0`). Every Church numeral is
`λ λ 1 (1 (… (1 0)))` — the number is literally the count of `1`s.
````

## The Y combinator, drawn by alligators

Bret Victor's *Alligator Eggs* renders a λ as a hungry alligator guarding its family and a variable
as an egg. The lab draws any term this way, and the one to show a class is
[`alligators Y`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=alligators%20Y) — the
fixed-point combinator as nested wildlife:

```text
╭──────────────── 🐊 Alligator Eggs view ─────────────────╮
│                                                         │
│  ╭────────────────── 🐊 hungry «f» ──────────────────╮  │
│  │  ╭────────── 🐊 family (application) ──────────╮  │  │
│  │  │  ╭──────────── 🐊 hungry «x» ────────────╮  │  │  │
│  │  │  │  ╭──── 🐊 family (application) ────╮  │  │  │  │
│  │  │  │  │  🥚 f                           │  │  │  │  │
│  │  │  │  │           ⇣ feeding ⇣           │  │  │  │  │
│  │  │  │  │  ╭─ 🐊 family (application) ─╮  │  │  │  │  │
│  │  │  │  │  │  🥚 x                     │  │  │  │  │  │
│  │  │  │  │  │  ⇣ feeding ⇣              │  │  │  │  │  │
│  │  │  │  │  │  🥚 x                     │  │  │  │  │  │
│  │  │  │  │  ╰───────────────────────────╯  │  │  │  │  │
│  │  │  │  ╰─────────────────────────────────╯  │  │  │  │
│  │  │  ╰───────────────────────────────────────╯  │  │  │
│  │  │                 ⇣ feeding ⇣                 │  │  │
│  │  │  ╭──────────── 🐊 hungry «x» ────────────╮  │  │  │
│  │  │  │  ╭──── 🐊 family (application) ────╮  │  │  │  │
│  │  │  │  │  🥚 f                           │  │  │  │  │
│  │  │  │  │           ⇣ feeding ⇣           │  │  │  │  │
│  │  │  │  │  ╭─ 🐊 family (application) ─╮  │  │  │  │  │
│  │  │  │  │  │  🥚 x                     │  │  │  │  │  │
│  │  │  │  │  │  ⇣ feeding ⇣              │  │  │  │  │  │
│  │  │  │  │  │  🥚 x                     │  │  │  │  │  │
│  │  │  │  │  ╰───────────────────────────╯  │  │  │  │  │
│  │  │  │  ╰─────────────────────────────────╯  │  │  │  │
│  │  │  ╰───────────────────────────────────────╯  │  │  │
│  │  ╰─────────────────────────────────────────────╯  │  │
│  ╰───────────────────────────────────────────────────╯  │
│                                                         │
╰─────────────────────────────────────────────────────────╯
```

The symmetry is the point: one outer alligator `f`, and inside, *twice*, the same family
`λx. f (x x)` — self-application about to feed itself to itself, forever. Students who have seen this
picture do not forget why `Y g = g (Y g)`.

## A geometry proof, replayed AlphaGeometry-style

Lecture 6 discusses how AlphaGeometry couples a deductive database (DD) with algebraic reasoning
(AR). The lab ships replays of recorded proofs in exactly that format. Run
[`ag angle_bisector`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=ag%20angle_bisector)
— isosceles triangle, bisector equals altitude — and read the three-step kernel of the replay:

```text
╭────────────────────── DD+AR step #1 ───────────────────────╮
│  premises    AB = AC (assumption)                          │
│              AD = AD (common side)                         │
│              ∠BAD = ∠CAD (AD is the bisector)              │
│  rule        SAS (side-angle-side)                         │
│  conclusion  △ABD ≅ △ACD                                   │
╰────────────────────────────────────────────────────────────╯
╭─────────────────────────── DD+AR step #2 ────────────────────────────╮
│  premises    △ABD ≅ △ACD                                             │
│  rule        property of congruent triangles                         │
│  conclusion  ∠ADB = ∠ADC                                             │
╰──────────────────────────────────────────────────────────────────────╯
╭────────────────────────────────── DD+AR step #3 ───────────────────────────────────╮
│  premises    ∠ADB + ∠ADC = 180°                                                    │
│              ∠ADB = ∠ADC                                                           │
│  rule        algebra (linear arithmetic)                                           │
│  conclusion  ∠ADB = 90°                                                            │
│  why         Half of 180° is 90° — this is where AlphaGeometry's AR module works.  │
╰────────────────────────────────────────────────────────────────────────────────────╯
```

Steps 1–2 are pure deductive-database moves (rule applications over a fact base); step 3 is the AR
handoff — a linear-arithmetic step no geometric rule covers. The replay banner is candid about what
this is: *"the desktop replayer pauses for ENTER between steps; the browser prints the whole replay"*
— a recording of a found proof, not a geometry engine in your tab. Honest scope, real structure.

## Tutorials, quizzes, and a knowledge base

Three study modes live behind three commands, all ported from the desktop lab.

**Tutorials.** [`tutorial 2`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=tutorial%202)
opens the √2-is-irrational walkthrough — seven gated steps from Pythagorean scandal to Mathlib's
`Nat.Prime.irrational_sqrt`:

```text
Chapter 2: The square root of 2 is irrational

  The archetypal proof by contradiction: we extract a contradiction from
  sqrt(2) = p/q. Mathlib delivers it as a corollary of
  `Nat.Prime.irrational_sqrt`.

  Steps: 7, time: ~14 min.

Step 1/7 · Narrative
  Scandal in the Pythagorean school

  In the Pythagorean school everything was supposed to be expressible as a
  ratio of integers. Measure, harmony, justice - all rational. So the
  disciple who is said to have first proven that the diagonal of a unit
  square cannot be such a ratio met a stern example: legend speaks of
  Hippasus of Metapontum drowned at sea. …
```

Twelve chapters (Gauss's sum, pigeonhole, Euclid's primes, AM–GM, Bézout, Cauchy–Schwarz, …), each a
stepwise dialogue; progress is kept for the browser session.

**Quizzes.** [`quiz intro_lambda`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=quiz%20intro_lambda)
starts a shuffled 20-question run (nine bundles, ~290 questions in all, up to `final_exam`). The
grader is the point: open answers are parsed, normalized, and compared **up to α-equivalence** — it
grades mathematics, not spelling. From our run:

```text
Quiz · Question 14/20 · Topic: lambda · Type: open · Difficulty: **---
  What does (\x. x x) (\y. y) reduce to?
```

The canonical answer is `\y. y`. We deliberately answered with different letters — `\w. w`:

```text
✓ Correct! (α-equivalent)
  (α-equivalent — your form: λw. w, canonical: λy. y)
  (\y.y)(\y.y) → \y.y.
```

Accepted, with a note showing both forms. (Question order is shuffled per session, so your
question 14 will differ — the grading behavior will not.)

**Knowledge base.** [`kb search lean`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=kb%20search%20lean)
full-text-searches a curated registry of books, courses, papers and talks:

```text
Search results for: lean (33)
  ID                                Kind    Year  Title                                             Authors
  --------------------------------------------------------------------------------------------------------------------------------
  lean-4-manual                     MANUAL  2025  The Lean 4 Reference Manual                       The Lean Team
  mathematics-in-lean               BOOK    2024  Mathematics in Lean                               Jeremy Avigad, Patrick Massot
  moura-ullrich-2021-lean4-paper    PAPER   2021  The Lean 4 Theorem Prover and Programming Langu…  Leonardo de Moura, Sebastian …
  nng-natural-number-game           COURSE  2024  Natural Number Game (Lean 4)                      Kevin Buzzard, Mohammad Pedra…
  pfr-formalised-2024               PAPER   2024  Lean formalisation of the Polynomial Freiman-Ru…  Terence Tao, Timothy Gowers, …
  macbeth-mechanics-of-proof        BOOK    2025  The Mechanics of Proof                            Heather Macbeth
   ⋮
  … 3 more; narrow with --topic / --kind / --difficulty.
  Details: kb show <id>
```

Thirty-three hits, from the 1988 Calculus of Constructions paper to 2025-vintage formalization news,
each expandable with `kb show <id>`; concept pages like `kb curry-howard` give one-breath
explanations with readings attached.

## Terminal quality of life — did you know?

Small things that make the lab feel like a tool rather than a toy. All of these are in the browser
build you deep-link from this book:

| Did you know… | Details |
|---|---|
| **TAB completes** | First word completes against all 29 commands; later words complete constant names (`TRU⇥` → `TRUE`); after `help`, command names again. |
| **History persists** | ↑/↓ walk your past commands; the last 200 lines survive page reloads (stored locally in your browser, nowhere else). |
| **Every command has a manual page** | [`help equiv`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=help%20equiv) prints syntax, semantics, four worked examples, and the fine print ("η is NOT used… Strict renaming-only comparison is alpha."). |
| **You can extend the language** | [`let COMPOSE = \f g x. f (g x)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=let%20COMPOSE%20%3D%20%5Cf%20g%20x.%20f%20(g%20x)) defines a session constant usable anywhere a built-in is; `defs` lists, `undef` removes. |
| **Every command is a URL** | Append `?cmd=…` to the lab URL and the command is typed and run on load — which is how every link in this book works. |
| **A term is a command** | Type a bare term like `PLUS 1 1` with no keyword and the lab reduces it; `reduce`, `red`, `r` are all the same verb. |

The `let` mechanism deserves one real transcript, because it quietly demonstrates that composition of
successors is addition:

```text
λ> let COMPOSE = \f g x. f (g x)
defined COMPOSE (this session only)
  λf g x. f (g x)

λ> nf COMPOSE SUCC SUCC 1
β-normal form · 9 step(s)
  λf x. f (f (f x))
  = 3  (Church numeral)
```

Definitions are expanded at `let`-time (so they can build on each other but never form cycles), live
only in your session, and cannot shadow the built-ins listed by
[`constants`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=constants).

## Under the hood

Four honest paragraphs for the colleague who wants to know what they would actually be adopting.

**It is Python in your browser, and nothing leaves your machine.** The engine is CPython running
inside [Pyodide](https://pyodide.org)'s WebAssembly runtime, displayed through xterm.js. There is no
evaluation server: terms you type are parsed, reduced and typed entirely in the tab, which is why the
lab works on a train and why student input is private by construction. The one caveat the lab itself
states in `about`: a `?cmd=` deep link is part of a URL, so *that* command can appear in ordinary web
server logs.

**The engine is small, strict about its contract, and checkable.** The core is an untyped λ-calculus
AST with capture-avoiding substitution; `alpha` decides binder identity by De Bruijn-index
comparison, never by variable-name equality, so shadowing cannot fool it. Normalization is *checked*:
every `nf`/`whnf`/`decode`/`equiv` call goes through a routine that returns the term together with a
completeness flag and a step count, and the printed status — "β-normal form · 6 step(s)", "reduction
limit reached", "inconclusive" — is that flag verbatim. The reducer is β-only by design; η-conversion
exists as its own opt-in command (`eta`), so "normal form" in this lab always means exactly β-normal
form.

**It is tested like software, because it is software.** The Python package behind the browser build
carries a suite of 290 tests — the reduction engine and parser regressions, the help pages, and each
ported feature module (`prove`, `ch`, `kb`, `quiz`, `ag`, `alligators`, output alignment) — run
against the same code the browser loads. When this book claims an output, the output came from that
engine; when the engine changed during writing, the tests are what noticed.

**You can host it yourself.** The deployment is a directory of static files: one HTML page, the
Python sources, and a `vendor/` tree with pinned Pyodide, xterm.js and fonts under a SHA-256
manifest. Any static web server — a department box, GitHub Pages, `python -m http.server` — serves a
fully working lab with no backend, no accounts, and no telemetry to configure. The source lives in
the course repository (`github.com/nasqret/vietnam2026`), linked from the lab's `about` page.

```{admonition} Where this connects
:class: seealso
- [Lecture 2 — Simple calculations with the Church λ-calculus](../lectures/l2_lambda_calculus.md) — the theory behind `reduce`, `nf`, `whnf`, and the Church encodings the traces animate.
- [Lecture 3 — Propositional logic proofs](../lectures/l3_propositional.md) — the `prove` and `ch` commands are this lecture's engine room: tactics, hints, and the intuitionistic refusals.
- [Lecture 4 — Introduction to Lean](../lectures/l4_lean_intro.md) — every `lean` snippet and Live Lean link lands in the toolchain introduced here.
- [Lecture 6 — Auto-formalization of mathematics with Lean](../lectures/l6_autoformalization.md) — the `ag` replays are this lecture's DD+AR story, step by recorded step.
- [The cheatsheet](../appendix/cheatsheet.md) — the whole command surface on one page, with a lab one-liner per concept.
```
