# Puzzles and extended exercises

A graded problem collection. Every puzzle here follows the same protocol, and it is the whole
point of this chapter: **commit to a prediction before you run anything.** Write your answer on
paper — the normal form, the step count, the yes/no, the type — and only then open the
[lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/) and check. A puzzle you merely read
is a puzzle wasted; the λ-calculus is small enough that your errors are always *interesting*, and
the engine will tell you exactly where your mental substitution went wrong.

Difficulty is marked ★ (a minute), ★★ (a good think), ★★★ (bring coffee). Solutions hide in
dropdown boxes; every output inside them was produced by the real engine, step counts included.

```{admonition} Ground rules
:class: tip
Five conventions used throughout, all checkable in the lab itself:

- [`constants`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=constants) — the named library (TRUE, PLUS, LEQ, Y, …) every puzzle may use freely
- `let NAME = <term>` — session-local definitions; recipes below assume you paste their `let` lines **in order, in one session**
- `decode <term>` — normalizes and reads the result back as a numeral/boolean; our favourite oracle
- `equiv <t> = <u>` — β-convertibility via normal forms (no η!); `alpha` is the strict renaming-only cousin
- `help <command>` — every command explains itself with examples when in doubt
```

## Warm-ups ★

Five finger exercises. For each: predict the output *and*, where a step count is printed, the
number of β-steps.

**W1.** What is the normal form of `(λx. x x) (λy. y)`, and in how many steps?
[`nf (\x. x x) (\y. y)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%20%28%5Cx.%20x%20x%29%20%28%5Cy.%20y%29)

**W2.** A Church numeral is a function — so apply one to another. What number is `2 2`? What
about `3 2` and `2 3`? (Careful: it is not symmetric, and it is not multiplication.)
[`decode 2 2`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=decode%202%202)

**W3.** A numeral *iterates*. What is `3 SUCC 4` — the numeral 3 used as a loop, body `SUCC`,
seed 4? [`decode 3 SUCC 4`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=decode%203%20SUCC%204)

**W4.** `TRUE` is a projection wearing a costume. Predict the normal form of `(λx. λy. x) A B`
where `A`, `B` are free variables.
[`nf (\x. \y. x) A B`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%20%28%5Cx.%20%5Cy.%20x%29%20A%20B)

**W5.** Subtraction, but the answer would be negative. What does the lab say — and *how* does it
say it? [`decode SUB 2 5`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=decode%20SUB%202%205)

````{admonition} Solutions to the warm-ups
:class: dropdown
**W1** — two steps, not one: first the self-application copies the identity, then the copy fires.

```text
β-normal form · 2 step(s)
  λy. y
```

**W2** — application of numerals is *exponentiation with the arguments flipped*: `n m` computes mⁿ.

```text
decode 2 2   = 4  (Church numeral)
decode 3 2   = 8  (Church numeral)
decode 2 3   = 9  (Church numeral)
```

So `3 2` is 2³ = 8 and `2 3` is 3² = 9. Keep this in your pocket for puzzle N1.

**W3** — three successors applied to 4:

```text
  = 7  (Church numeral)
```

**W4** — `TRUE` selects its first argument; two β-steps, one per application:

```text
β-normal form · 2 step(s)
  A
```

**W5** — Church subtraction is *monus*: it floors at zero. And the lab is honest about a deeper
pun — the normal form λf x. x is **the same term** as `FALSE`:

```text
  = 0 / FALSE  (the same untyped Church term)
```
````

## Binding puzzles ★★

Names are scaffolding; binding structure is the building. These puzzles are about seeing through
the scaffolding — with [`alpha`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=help%20alpha)
(strict α-equivalence, no β), `debruijn` (the nameless view), and one deliberate trap that the
engine defuses in front of you.

**B1. The shadowing trap.** Consider λx. λx. x. Which x does the body see? Decide whether it is
α-equivalent to λx. λy. y, then to λx. λy. x, and check both. Then look at its De Bruijn form.
[`alpha \x. \x. x = \x. \y. y`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=alpha%20%5Cx.%20%5Cx.%20x%20%3D%20%5Cx.%20%5Cy.%20y)

```text
alpha \x. \x. x = \x. \y. x
debruijn \x. \x. x
```

**B2. Swapped names, same term?** Are λx. λy. x y and λy. λx. y x α-equivalent? (Do not let the
letter swap hypnotize you — trace which *binder* each variable points to.)
[`alpha \x. \y. x y = \y. \x. y x`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=alpha%20%5Cx.%20%5Cy.%20x%20y%20%3D%20%5Cy.%20%5Cx.%20y%20x)

**B3. Nameless S.** Write down, by hand, the De Bruijn form of the S combinator
λx. λy. λz. x z (y z). Then check.
[`debruijn \x. \y. \z. x z (y z)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=debruijn%20%5Cx.%20%5Cy.%20%5Cz.%20x%20z%20%28y%20z%29)

**B4. The capture trap.** Reduce (λx. λy. x) y — where the argument y is *free*. Naive textual
substitution would produce λy. y, the identity. That answer is **wrong**: it captures the free y.
Predict what the engine does instead, then watch it.
[`reduce (\x. \y. x) y`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=reduce%20%28%5Cx.%20%5Cy.%20x%29%20y)

```text
equiv (\x. \y. x) y = \z. y
equiv (\x. \y. x) y = \y. y
```

**B5. Three notions of "the same".** Take λx. f x and the bare f. Are they the same term? You
have three judges: `alpha` (renaming only), `equiv` (β-normal forms, *no* η), and `eta`. Predict
each verdict before you poll them.
[`alpha \x. f x = f`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=alpha%20%5Cx.%20f%20x%20%3D%20f)

```text
equiv \x. f x = f
eta \x. f x
```

````{admonition} Solutions to the binding puzzles
:class: dropdown
**B1** — the inner binder wins; the body's x belongs to the *second* λ. So the term is really
"constant function returning the identity":

```text
alpha \x. \x. x = \x. \y. y
  left:  λx x'. x'
  right: λx y. y
  ≡α alpha-equivalent

alpha \x. \x. x = \x. \y. x
  left:  λx x'. x'
  right: λx y. x
  ≢α not alpha-equivalent
```

Note how the printer already renames the shadowed binder to x′ — it refuses to even *display* the
ambiguity. The nameless view settles it in one line:

```text
debruijn \x. \x. x
  named:    λx x'. x'
  nameless: λ λ 0
```

Index 0 = "nearest λ": shadowing resolved, permanently.

**B2** — yes, α-equivalent. In both terms the head of the body points at the outer binder and the
argument at the inner one; the nameless form of each is λ λ 1 0:

```text
  left:  λx y. x y
  right: λy x. y x
  ≡α alpha-equivalent
```

**B3** — indices count binders *outward from 0*, so x ↦ 2, y ↦ 1, z ↦ 0:

```text
  named:    λx y z. x z (y z)
  nameless: λ λ λ 2 0 (1 0)
```

**B4** — the engine α-renames the inner binder *before* substituting, so the free y stays free:

```text
β-reduction (normal order · highlight = next redex)
  start:  (λx. (λy'. x)) y
  →β      λy0. y
  β-normal form reached in 1 step(s).
```

Look at the `start:` line — the rename to y′ happens the moment the term is displayed, and the
result is λy0. y, a constant function returning the *free* y. The two `equiv` checks confirm the
verdicts: correct answer accepted, captured answer rejected:

```text
equiv (\x. \y. x) y = \z. y
  equal β-normal forms up to α

equiv (\x. \y. x) y = \y. y
  left NF:  λy0. y
  right NF: λy. y
  different β-normal forms
```

That last pair differs precisely because the right-hand λy. y binds its y — capture in a nutshell.

**B5** — the judges disagree, and each is right about its own law:

```text
alpha \x. f x = f      →  ≢α not alpha-equivalent
equiv \x. f x = f      →  different β-normal forms   (η is not used)
eta \x. f x            →  →η  f   · η-normal form reached in 1 step(s)
```

λx. f x and f are *extensionally* the same function, β-*in*convertible, and η-convertible. Three
notions of equality, strictly ordered — remember this in puzzle E3, where the same phenomenon
bites at the level of whole truth tables.
````

## Encoding puzzles ★★

Now you build. Each recipe is a fresh session: paste the `let` lines in order, then interrogate
your creation. `defs` lists what you have defined; `undef NAME` removes a mistake.

### E1. MAX and MIN from LEQ and IF

Define binary maximum and minimum of Church numerals using only the library's `LEQ` and `IF`.
Then convince yourself with a slick one-liner that for *any* pair, MIN and MAX together preserve
the sum.

[`let MAX = \m. \n. IF (LEQ m n) n m`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=let%20MAX%20%3D%20%5Cm.%20%5Cn.%20IF%20%28LEQ%20m%20n%29%20n%20m)

```text
let MIN = \m. \n. IF (LEQ m n) m n
decode MAX 3 5
decode MAX 5 3
decode MIN 4 2
decode MAX 3 3
equiv PLUS (MIN 4 2) (MAX 4 2) = PLUS 4 2
```

````{admonition} Solution
:class: dropdown
The two definitions differ only in which branch returns which argument:

```text
let MAX = \m. \n. IF (LEQ m n) n m
defined MAX (this session only)
  λm n. (λb t f. b t f) ((λm' n'. (λn''. n'' (λ_ t' f'. f') (λt'' f''. t'')) ((λm'' n'''. n''' (λn'''2 f''' x. n'''2 (λg h. h (g f''')) (λu. x) (λu'. u')) m'') m' n')) m n) n m
```

(The echo shows the *fully expanded* λ-term — your named constants are sugar, and `let` melts
them immediately.) The tests:

```text
decode MAX 3 5   = 5  (Church numeral)
decode MAX 5 3   = 5  (Church numeral)
decode MIN 4 2   = 2  (Church numeral)
decode MAX 3 3   = 3  (Church numeral)
```

The tie case 3 3 costs nothing: when LEQ says TRUE we return n, and n = m. And the conservation
law min(m,n) + max(m,n) = m + n, checked at (4,2) by comparing β-normal forms:

```text
equiv PLUS (MIN 4 2) (MAX 4 2) = PLUS 4 2
  left NF:  λf x. f (f (f (f (f (f x)))))
  right NF: λf x. f (f (f (f (f (f x)))))
  equal β-normal forms up to α
```
````

```{admonition} Why does reduce stop "before the end" on this one?
:class: note
If you watch the conservation check with `reduce PLUS (MIN 4 2) (MAX 4 2)`, the trace halts after
60 steps saying *"the displayed term is partial"*. Nothing is stuck — the term reaches its normal
form in **76 β-steps** (`nf` confirms: `= 6`); `reduce` simply caps its *step-by-step display* at 60
lines, because it is a chalkboard, not a calculator.

Where do 76 steps go for such a tiny computation? Measured piece by piece: branch selection is cheap
(`IF TRUE 4 2` — 5 steps), but the *boolean* is not: each Kleene predecessor rebuilds its numeral
(`PRED 4` — 13 steps), `SUB 4 2` applies it twice (28), so one `LEQ` costs 28 and each of
`MIN 4 2`/`MAX 4 2` costs 35 — and the conservation law runs **both** before `PLUS` even starts.
Meanwhile the *discarded* branch of every `IF` vanishes unevaluated — normal order is lazy; the
whole price is in deciding, never in the road not taken.

And `reduce MIN 4 2` **on its own** fits comfortably — 35 steps — with a finale worth watching:
around step 32 the whole `LEQ` computation collapses into a literal selector, and the last four
lines read

```text
  →β      (λt. (λf. f)) (λf'. (λx. f' (f' (f' (f' x))))) (λf''. (λx'. f'' (f'' x')))
  →β      (λf. f) (λf'. (λx. f' (f' x)))
  →β      λf x. f (f x)
  β-normal form reached in 35 step(s).   = 2  (Church numeral)
```

— `FALSE` appears *as a term*, swallows the numeral `4` without ever evaluating it, and hands back
`2`. The endpoint `λf x. f (f x)` **is** the numeral `2` — `church 2` prints the identical term.
(Meanwhile `alpha MIN 4 2 = 2` says ≢α — strict α never computes — while `equiv` agrees they are
β-equal: the two judgments in one example.)

Rules of thumb: `reduce` to watch mechanics whenever the count fits the 60-line window;
`nf`/`decode`/`equiv` for answers (1,000-step budget). And if `MIN` ever comes back as a stuck free
variable in `nf MIN 4 2 → MIN … (0 steps)`, your page was reloaded — `let` definitions live only in
the session; run the `let` lines again (`defs` shows what survived).
```

### E2. NOR from NOT and OR — and a lucky strike

Define `MYNOR p q = NOT (OR p q)`, verify all four rows of its truth table, and then try
something bolder: is your term β-convertible to the library's `NOR` — not just pointwise equal,
but *as a function*?

[`let MYNOR = \p. \q. NOT (OR p q)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=let%20MYNOR%20%3D%20%5Cp.%20%5Cq.%20NOT%20%28OR%20p%20q%29)

```text
decode MYNOR FALSE FALSE
decode MYNOR FALSE TRUE
decode MYNOR TRUE FALSE
decode MYNOR TRUE TRUE
equiv MYNOR = NOR
```

````{admonition} Solution
:class: dropdown
The truth table is NOR's: true only on (F,F).

```text
decode MYNOR FALSE FALSE   = TRUE  (Church boolean)
decode MYNOR FALSE TRUE    = 0 / FALSE  (the same untyped Church term)
decode MYNOR TRUE FALSE    = 0 / FALSE  (the same untyped Church term)
decode MYNOR TRUE TRUE     = 0 / FALSE  (the same untyped Church term)
```

And the equivalence check succeeds *at the function level*:

```text
equiv MYNOR = NOR
  left NF:  λp q. p p q (λt f. f) (λt' f'. t')
  right NF: λp q. p p q (λt f. f) (λt' f'. t')
  equal β-normal forms up to α
```

No luck involved, actually: [`church NOR`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=church%20NOR)
reveals the library defines NOR *conceptually as* λp q. NOT (OR p q) — you re-derived its exact
construction, so the normal forms coincide. Hold that thought for E3, where the same experiment
fails spectacularly.
````

### E3. IMPLIES from NAND alone

NAND is functionally complete, so implication must be buildable from it and nothing else.
Recall p → q ≡ ¬p ∨ q ≡ NAND(p, ¬q), and ¬q ≡ NAND(q, q). Define it, verify the full truth
table — and then ask the dangerous question: `equiv MYIMP = IMPLIES`?

[`let MYIMP = \p. \q. NAND p (NAND q q)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=let%20MYIMP%20%3D%20%5Cp.%20%5Cq.%20NAND%20p%20%28NAND%20q%20q%29)

```text
decode MYIMP TRUE TRUE
decode MYIMP TRUE FALSE
decode MYIMP FALSE TRUE
decode MYIMP FALSE FALSE
equiv MYIMP TRUE FALSE = IMPLIES TRUE FALSE
equiv MYIMP = IMPLIES
```

````{admonition} Solution — and a moral about extensionality
:class: dropdown
The truth table is perfect — false only at (T,F):

```text
decode MYIMP TRUE TRUE     = TRUE  (Church boolean)
decode MYIMP TRUE FALSE    = 0 / FALSE  (the same untyped Church term)
decode MYIMP FALSE TRUE    = TRUE  (Church boolean)
decode MYIMP FALSE FALSE   = TRUE  (Church boolean)
```

Pointwise, the two functions agree on every boolean input:

```text
equiv MYIMP TRUE FALSE = IMPLIES TRUE FALSE
  left NF:  λt f. f
  right NF: λt f. f
  equal β-normal forms up to α
```

But as bare λ-terms they are **not** β-convertible:

```text
equiv MYIMP = IMPLIES
  left NF:  λp q. p (q q q (λt f. f) (λt' f'. t')) p (λt'' f''. f'') (λt''' f'''. t''')
  right NF: λp q. p (λt f. f) (λt' f'. t') (p (λt'' f''. f'') (λt''' f'''. t''')) q
  different β-normal forms
```

Both normal forms are *stuck* on the abstract variables p, q — neither can compute further
without knowing its input. They only collapse to the same value once you feed them actual
booleans. This is the E2 contrast made sharp: **agreeing on all booleans is extensional equality;
`equiv` decides β-conversion, which is strictly finer.** (η would not save you here either — the
two shapes differ in structure, not just in a spare binder.) In B5 you saw this gap for the
smallest possible example; here it separates two perfectly correct implementations of the same
connective.
````

### E4. Three-way XOR

Define `XOR3 p q r` by folding the library's binary `XOR`. Then answer *before running*: what is
`XOR3 TRUE TRUE TRUE`? (If your instinct says FALSE because "they're all equal", this puzzle was
built for you.)

[`let XOR3 = \p. \q. \r. XOR p (XOR q r)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=let%20XOR3%20%3D%20%5Cp.%20%5Cq.%20%5Cr.%20XOR%20p%20%28XOR%20q%20r%29)

```text
decode XOR3 TRUE TRUE TRUE
decode XOR3 TRUE TRUE FALSE
decode XOR3 TRUE FALSE FALSE
decode XOR3 TRUE FALSE TRUE
decode XOR3 FALSE FALSE FALSE
```

````{admonition} Solution
:class: dropdown
Chained XOR computes **parity** — TRUE iff an *odd* number of inputs are TRUE — not
"exactly one":

```text
decode XOR3 TRUE TRUE TRUE     = TRUE  (Church boolean)
decode XOR3 TRUE TRUE FALSE    = 0 / FALSE  (the same untyped Church term)
decode XOR3 TRUE FALSE FALSE   = TRUE  (Church boolean)
decode XOR3 TRUE FALSE TRUE    = 0 / FALSE  (the same untyped Church term)
decode XOR3 FALSE FALSE FALSE  = 0 / FALSE  (the same untyped Church term)
```

Three TRUEs is odd, hence TRUE. The remaining rows follow by symmetry — XOR3 only counts, it
cannot tell its arguments apart (try `equiv XOR3 TRUE FALSE TRUE = XOR3 FALSE TRUE FALSE` in the
same session… which is `different β-normal forms`, because those rows have parities 2 and 1. Even
the counterexample teaches.)

*Extension for the road:* an "exactly one of three" connective is genuinely different — build it
from AND/OR/NOT and find the first row where it disagrees with XOR3.
````

## Numeral puzzles ★★

Arithmetic on Church numerals is full of small scandals. Three of the best:

**N1. Zero to the zero.** The library's `POW` is λm n f x. n m f x — exponentiation is literally
"apply n to m" (warm-up W2!). So what is `POW 0 0`? Predict, then run — and count the steps.
[`nf POW 0 0`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%20POW%200%200)

**N2. The monus surprise.** Is `PRED (SUCC n) = n` for every numeral n? And symmetrically — is
`SUCC (PRED n) = n`? Find a counterexample to one of them or argue there is none.
[`equiv PRED (SUCC 7) = 7`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=equiv%20PRED%20%28SUCC%207%29%20%3D%207)

```text
equiv PRED (SUCC 0) = 0
equiv SUCC (PRED 0) = 0
```

**N3. Parity in four symbols.** A numeral n is an iterator; `NOT` is an involution. So what does
`n NOT TRUE` compute? Test your claim on 0, 6, 7, then wrap it as a definition.
[`decode 6 NOT TRUE`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=decode%206%20NOT%20TRUE)

```text
decode 7 NOT TRUE
decode 0 NOT TRUE
let EVEN = \n. n NOT TRUE
decode EVEN 10
decode EVEN 9
```

````{admonition} Solutions to the numeral puzzles
:class: dropdown
**N1** — the lab votes with the algebraists: 0⁰ = 1, in four steps.

```text
β-normal form · 4 step(s)
  λf x. f x
  = 1  (Church numeral)
```

Why: `POW 0 0` unfolds to `0 0`, i.e. the numeral 0 = λf x. x applied to itself — "iterate the
function 0 zero times", which is the identity on the seed… and the resulting term λf x. f x is
exactly the numeral 1. Iterating *anything* zero times gives 1, which is also why
`decode POW 2 0` = 1 while `decode POW 0 2` = 0.

**N2** — `PRED (SUCC n) = n` holds for **every** n (we swept n = 0…5 and 7; SUCC n ≥ 1, so PRED
never hits its floor):

```text
equiv PRED (SUCC 7) = 7
  left NF:  λf x. f (f (f (f (f (f (f x))))))
  right NF: λf x. f (f (f (f (f (f (f x))))))
  equal β-normal forms up to α
```

The other direction fails at exactly one point. PRED is monus-flavoured: PRED 0 = 0, so:

```text
equiv SUCC (PRED 0) = 0
  left NF:  λf x. f x
  right NF: λf x. x
  different β-normal forms
```

SUCC (PRED 0) = 1 ≠ 0. Moral: SUCC has a *left* inverse (PRED ∘ SUCC = id) but no right inverse —
on Church numerals, subtraction saturates at zero, as W5 already whispered.

**N3** — `n NOT TRUE` applies NOT n times to TRUE: the answer is TRUE exactly when n is even.
Parity, in four symbols, with no recursion anywhere:

```text
decode 6 NOT TRUE   = TRUE  (Church boolean)
decode 7 NOT TRUE   = 0 / FALSE  (the same untyped Church term)
decode 0 NOT TRUE   = TRUE  (Church boolean)

let EVEN = \n. n NOT TRUE
defined EVEN (this session only)
  λn. n (λp. p (λt f. f) (λt' f'. t')) (λt'' f''. t'')

decode EVEN 10      = TRUE  (Church boolean)
decode EVEN 9       = 0 / FALSE  (the same untyped Church term)
```
````

## Typed puzzles ★★

Switch engines: `ch term` runs principal-type inference (Algorithm W) on untyped terms, and
`ch type` searches for inhabitants of implicational formulas — provability in intuitionistic
logic, live. The game: **write the type before the machine does.**

**T1. Four famous combinators.** Infer, by hand, the principal types of

$$
\mathsf{B} = \lambda f\, g\, x.\, f\,(g\,x) \qquad
\mathsf{C} = \lambda f\, x\, y.\, f\,y\,x \qquad
\mathsf{W} = \lambda f\, x.\, f\,x\,x \qquad
\mathsf{pair} = \lambda a\, b\, f.\, f\,a\,b
$$

then check each:
[`ch term \f. \g. \x. f (g x)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=ch%20term%20%5Cf.%20%5Cg.%20%5Cx.%20f%20%28g%20x%29)

```text
ch term \f. \x. \y. f y x
ch term \f. \x. f x x
ch term \a. \b. \f. f a b
```

**T2. The one that got away.** W duplicates its argument and is perfectly typable. So why does
[`ch term \x. x x`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=ch%20term%20%5Cx.%20x%20x)
fail? Predict the error message's shape before you look.

**T3. Tautology or not?** Read each closed type below as a propositional formula. Decide —
*by logic alone* — which are intuitionistic tautologies, then let the inhabitation search vote:

- [`ch type (A -> A -> B) -> A -> B`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=ch%20type%20%28A%20-%3E%20A%20-%3E%20B%29%20-%3E%20A%20-%3E%20B) — contraction
- [`ch type A -> B -> (A -> B -> C) -> C`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=ch%20type%20A%20-%3E%20B%20-%3E%20%28A%20-%3E%20B%20-%3E%20C%29%20-%3E%20C) — pairing's shadow
- [`ch type ((A -> B) -> A) -> A`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=ch%20type%20%28%28A%20-%3E%20B%29%20-%3E%20A%29%20-%3E%20A) — Peirce's law
- [`ch type ((A -> B) -> B) -> A`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=ch%20type%20%28%28A%20-%3E%20B%29%20-%3E%20B%29%20-%3E%20A) — a double-negation-elimination lookalike
- [`ch type (A -> B) -> B -> A`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=ch%20type%20%28A%20-%3E%20B%29%20-%3E%20B%20-%3E%20A) — converse-of-implication

````{admonition} Solutions to the typed puzzles
:class: dropdown
**T1** — the machine's verdicts:

```text
λf g x. f (g x)   :  (α → β) → (γ → α) → γ → β
λf x y. f y x     :  (α → β → γ) → β → α → γ
λf x. f x x       :  (α → α → β) → α → β
λa b f. f a b     :  α → β → (α → β → γ) → γ
```

Read as logic, these are old friends: B is *transitivity* of implication (composition), C is
*exchange* of premises, W is *contraction* (use a hypothesis twice), and pair is the
Curry–Howard shadow of ∧-introduction — "from α and β, anything that follows from both follows".
Together with K (λx y. x, weakening) they are precisely the structural rules of intuitionistic
implication — the BCKW basis.

**T2** — self-application demands a type that contains itself as a proper part:

```text
Term not typeable in STLC: Cannot unify α with α → β
```

`x` would need type α and simultaneously α → β — the occurs check says no. W dodges this because
its *two* uses of x can share one type; the single x in `x x` cannot.

**T3** — the first two are constructive theorems and the search prints a witness (which the lab
also exports as a one-click Live Lean theorem):

```text
ch type (A -> A -> B) -> A -> B
  Lambda-term:  λp q. p q q          ← W itself reappears!

ch type A -> B -> (A -> B -> C) -> C
  Lambda-term:  λp q r. r p q        ← pair, rediscovered
```

The last three all fail, with the same brutally honest message:

```text
Type ((A → B) → A) → A is not inhabited in intuitionistic STLC
(classical theorems like Peirce have no constructive witness).
```

(and likewise for `((A → B) → B) → A` and `(A → B) → B → A`). Peirce's law is *classically*
valid — truth tables love it — yet no closed λ-term proves it. The other two are not even
classically valid (set A false, B true). One search, two different reasons to fail; the
proof-relevant world distinguishes what truth tables cannot.
````

## The prove ladder ★★→★★★

The [`prove`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=help%20prove) command is
the lab's interactive Curry–Howard proof builder: state an implicational proposition, close it
tactic by tactic (`intro`, `apply`, `exact`, `assumption`…), and watch the proof *term* grow hole
by hole (?₀, ?₁, …). Five rungs, strictly increasing. If you get stuck mid-proof, `hint` asks the
built-in proof search for the next move, and `undo` retracts a step — but try to climb bare-handed
first. `qed` extracts your λ-term and its principal type.

- **R1** ★ — [`prove P -> P`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=prove%20P%20-%3E%20P) — say hello to the identity
- **R2** ★ — [`prove P -> Q -> P`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=prove%20P%20-%3E%20Q%20-%3E%20P) — discover K; try to do it in two tactics
- **R3** ★★ — [`prove (P -> Q) -> (Q -> R) -> P -> R`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=prove%20%28P%20-%3E%20Q%29%20-%3E%20%28Q%20-%3E%20R%29%20-%3E%20P%20-%3E%20R) — composition, forwards or backwards?
- **R4** ★★ — [`prove ((P -> Q) -> P) -> (P -> Q) -> P`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=prove%20%28%28P%20-%3E%20Q%29%20-%3E%20P%29%20-%3E%20%28P%20-%3E%20Q%29%20-%3E%20P) — Peirce's law thrown a rope
- **R5** ★★★ — [`prove ((((P -> Q) -> P) -> P) -> Q) -> Q`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=prove%20%28%28%28%28P%20-%3E%20Q%29%20-%3E%20P%29%20-%3E%20P%29%20-%3E%20Q%29%20-%3E%20Q) — Peirce-adjacent: T3 just told you Peirce itself is unprovable, yet *this* wrapper is a theorem. You will need your main hypothesis **twice**.

````{admonition} Solution — R1 and R2
:class: dropdown
R1, two tactics, and the proof term is the identity:

```text
prove P -> P
intro p
exact p
qed
```

```text
All goals closed.  QED.
  Final lambda-term: λp. p
  Proves:            P → P
  Principal type:    α → α
```

R2 in two tactics — `intros` introduces everything at once, and `assumption` scans the context:

```text
prove P -> Q -> P
intros
assumption
qed
```

```text
All goals closed.  QED.
  Final lambda-term: λp q. p
  Proves:            P → Q → P
  Principal type:    α → β → α
```

K, discovered rather than defined.
````

````{admonition} Solution — R3
:class: dropdown
Work *backwards* from R: to get R, `apply g` (reducing the goal to Q), then `apply f` (reducing
it to P), then the hypothesis closes it.

```text
prove (P -> Q) -> (Q -> R) -> P -> R
intro f
intro g
intro p
apply g
apply f
exact p
qed
```

Watch the term grow around the migrating hole — after `apply f` the state is:

```text
Goal 1/1
  Context: f : P → Q, g : Q → R, p : P
  Target:  P
  Term:    λf g p. g (f ?₅)
```

and `qed` delivers function composition:

```text
All goals closed.  QED.
  Final lambda-term: λf g p. g (f p)
  Proves:            (P → Q) → (Q → R) → P → R
  Principal type:    (α → β) → (β → γ) → α → γ
```
````

````{admonition} Solution — R4
:class: dropdown
Peirce's law ((P→Q)→P)→P is unprovable (T3) — but hand it the extra rope P→Q and it collapses to
a triviality:

```text
prove ((P -> Q) -> P) -> (P -> Q) -> P
intro f
intro g
apply f
exact g
qed
```

```text
All goals closed.  QED.
  Final lambda-term: λf g. f g
  Proves:            ((P → Q) → P) → (P → Q) → P
  Principal type:    (α → β) → α → β
```

Look closely at that `qed` block: the proof term is *bare application*, and its **principal type
(α → β) → α → β is strictly more general than the proposition proved**. Your proof never used the
inner structure of P → Q at all — the same term proves every instance of modus ponens. The
gap between "the proposition stated" and "the principal type of your proof" is a little
plagiarism detector for over-engineered proofs.
````

````{admonition} Solution — R5
:class: dropdown
The trick: after `intro f` the only way to produce Q is through f — so `apply f` and prove
((P→Q)→P)→P *under the extra hypotheses you accumulate on the way*. When you later hold p : P
and owe another Q, apply f **again** and this time discard the new hypothesis:

```text
prove ((((P -> Q) -> P) -> P) -> Q) -> Q
intro f
apply f
intro g
apply g
intro p
apply f
intro h
exact p
qed
```

Mid-proof, just before the second `apply f`, the state shows how far down the rabbit hole you
are — proving Q inside a term that already mentions f once:

```text
Goal 1/1
  Context: f : (((P → Q) → P) → P) → Q, g : (P → Q) → P, p : P
  Target:  Q
  Term:    λf. f (λg. g (λp. ?₅))
```

and the closing extraction:

```text
All goals closed.  QED.
  Final lambda-term: λf. f (λg. g (λp. f (λh. p)))
  Proves:            ((((P → Q) → P) → P) → Q) → Q
  Principal type:    ((((α → β) → α) → α) → β) → β
```

The hypothesis f is used **twice** — count its occurrences in the final term — and the proof
cannot be done otherwise. This proposition is (essentially) the double-negation shadow of Peirce's law:
intuitionistic logic cannot prove Peirce, but it *can* prove that Peirce is undeniable. That is
Glivenko's theorem in miniature, and you just built its witness by hand.
````

## Research-grade finale ★★★ — trees that fold themselves

Church numerals encode "iterate n times". The same idea — *a data structure is its own
recursor* — encodes any algebraic datatype. A binary tree with numeral-labelled leaves becomes a
function of two arguments: what to do at a leaf, and how to combine two folded subtrees:

$$
\mathrm{LEAF}\;n \;=\; \lambda l\,b.\; l\,n
\qquad\qquad
\mathrm{BRANCH}\;t\,u \;=\; \lambda l\,b.\; b\;(t\,l\,b)\;(u\,l\,b)
$$

Every "recursive" function on trees is then a single application — no Y combinator, no general
recursion, ever. Build the kit in one session:

[`let LEAF = \n. \l. \b. l n`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=let%20LEAF%20%3D%20%5Cn.%20%5Cl.%20%5Cb.%20l%20n)

```text
let BRANCH = \t. \u. \l. \b. b (t l b) (u l b)
let T1 = BRANCH (LEAF 1) (BRANCH (LEAF 2) (LEAF 3))
let SUMTREE = \t. t (\n. n) PLUS
let LEAVES = \t. t (\n. 1) PLUS
let MAX = \m. \n. IF (LEQ m n) n m
let DEPTH = \t. t (\n. 1) (\a. \c. SUCC (MAX a c))
```

Now the puzzles:

1. Predict `SUMTREE T1`, `LEAVES T1`, `DEPTH T1` — then `decode` all three.
2. Define `T2 = BRANCH T1 (BRANCH T1 (LEAF 10))` and predict all three again *before* running.
3. **Mirror.** Define a function reflecting a tree left↔right, *as a fold that rebuilds the
   tree*. Check that mirroring changes T1 but that mirroring **twice** is the identity — as an
   honest `equiv` between λ-terms, not just as matching sums.
4. **Type the constructors.** What does `ch term` make of LEAF and BRANCH? Can you recognize the
   fold in the type?

````{admonition} Solution — sums, counts, depths
:class: dropdown
T1 is the tree (1 ∨ (2 ∨ 3)): sum 6, three leaves, depth 3 (counting leaves as depth 1):

```text
decode SUMTREE T1   = 6  (Church numeral)
decode LEAVES T1    = 3  (Church numeral)
decode DEPTH T1     = 3  (Church numeral)
```

`SUMTREE` folds with l = identity, b = PLUS; `LEAVES` is the same fold with every label
overwritten by 1; `DEPTH` combines with λa c. SUCC (MAX a c), reusing E1's MAX. For scale,
`nf SUMTREE T1` (same session) reports the whole computation takes

```text
β-normal form · 33 step(s)
  λf x. f (f (f (f (f (f x)))))
  = 6  (Church numeral)
```

For T2 = BRANCH T1 (BRANCH T1 (LEAF 10)): sums 6 + (6 + 10), leaves 3 + (3 + 1), depth
1 + max(3, 1 + max(3,1)):

```text
let T2 = BRANCH T1 (BRANCH T1 (LEAF 10))
decode SUMTREE T2   = 22  (Church numeral)
decode LEAVES T2    = 7  (Church numeral)
decode DEPTH T2     = 5  (Church numeral)
```

(We also fed it `T3 = BRANCH T2 T2` — sum 44, instantly. The budgets are nowhere in sight.)
````

````{admonition} Solution — mirror, and the involution certificate
:class: dropdown
A fold whose leaf-action rebuilds a leaf and whose branch-action rebuilds a *swapped* branch:

```text
let MIRROR = \t. t LEAF (\a. \c. BRANCH c a)
```

Sums are symmetric, so `decode SUMTREE (MIRROR T1)` still reads `= 6  (Church numeral)`. But the
term-level facts are sharper. Mirroring once genuinely changes the tree:

```text
equiv MIRROR T1 = T1
  left NF:  λl b. b (b (l (λf x. f (f (f x)))) (l (λf' x'. f' (f' x')))) (l (λf'' x''. f'' x''))
  right NF: λl b. b (l (λf x. f x)) (b (l (λf' x'. f' (f' x'))) (l (λf'' x''. f'' (f'' (f'' x'')))))
  different β-normal forms
```

— you can *read* the mirrored tree in the left normal form: (3 ∨ 2) first, the 1-leaf last. And
mirroring twice is the identity, as a bona-fide β-conversion:

```text
equiv MIRROR (MIRROR T1) = T1
  left NF:  λl b. b (l (λf x. f x)) (b (l (λf' x'. f' (f' x'))) (l (λf'' x''. f'' (f'' (f'' x'')))))
  right NF: λl b. b (l (λf x. f x)) (b (l (λf' x'. f' (f' x'))) (l (λf'' x''. f'' (f'' (f'' x'')))))
  equal β-normal forms up to α
```

An algebraic identity about a datatype, certified by normalization alone — no induction
principle, no proof assistant, just β.
````

````{admonition} Solution — the constructors, typed
:class: dropdown
Algorithm W sees straight through the encoding:

```text
ch term \n. \l. \b. l n
  Type: α → (α → β) → γ → β

ch term \t. \u. \l. \b. b (t l b) (u l b)
  Type: (α → (β → γ → δ) → β) → (α → (β → γ → δ) → γ) → α → (β → γ → δ) → δ
```

Squint at LEAF's type with α = label, and read a tree of result β as
"give me a leaf-handler α → β (and a branch-handler γ) and I produce β". BRANCH's type says: two
things that fold to β resp. γ, combined by a handler β → γ → δ, fold to δ — with everything
specialized to β = γ = δ this is exactly the recursor

$$
\mathrm{Tree}_\alpha \;\cong\; \forall \beta.\; (\alpha \to \beta) \to (\beta \to \beta \to \beta) \to \beta ,
$$

the tree-shaped sibling of the numeral type (β → β) → β → β. The datatype *is* its induction
principle. That single idea — Böhm–Berarducci encoding — scales to lists, syntax trees, and
beyond, and it is the untyped seed of the inductive types you will meet in Lean.
````

```{admonition} Where this connects
:class: seealso
The puzzles above are the lab-side shadows of the lectures:

- [Lecture 2 — λ-calculus](../lectures/l2_lambda_calculus.md) — α/β/η, capture-avoiding substitution, De Bruijn indices, and the Church encodings behind W1–N3
- [Lecture 1 — type theory](../lectures/l1_type_theory.md) — principal types, Algorithm W, and the inhabitation questions of T1–T3
- [Lecture 3 — propositional logic](../lectures/l3_propositional.md) — the intuitionistic/classical divide that makes T3 and the prove ladder tick
- [Lecture 4 — Lean](../lectures/l4_lean_intro.md) — every `ch type` witness ships with a one-click Live Lean theorem; the finale's fold is the ancestor of Lean's inductive types
- [Cheatsheet](../appendix/cheatsheet.md) — the whole command surface on one page, for when a puzzle sends you hunting
```
