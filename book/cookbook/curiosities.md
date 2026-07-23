# Curiosities and lore

Every field has its campfire stories. The λ-calculus — ninety years old, seven symbols deep — has
better ones than most: a theorem discovered in a dentist's chair, a single term that is
simultaneously a number and a lie, an equation whose only honest answer is *I don't know*. This
chapter collects the folklore, and — because this is the Lambda Lab cookbook — every runnable claim
in it has been run. Open the [lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/) in a second
tab and check us at every step; the outputs printed below are the engine's own, verbatim.

## The predecessor legend

Princeton, early 1930s. Alonzo Church has his numerals: $n$ is *the act of doing something $n$
times*, $\lambda f x.\, f^n(x)$. Addition, multiplication, even exponentiation fall out almost for
free — to add, iterate the successor; to multiply, iterate the addition. Then someone asks the
innocent question: what about *subtracting one*?

Suddenly everything is stuck. A numeral only knows how to *apply* $f$ another time. There is no
un-apply. From inside $f^n(x)$ you cannot peel off a single $f$ — the term offers you iteration and
nothing else. Church, so the story goes, began to suspect that the predecessor function simply was
not λ-definable, which would have been fatal for the whole enterprise of encoding arithmetic.

His student Stephen Kleene found the trick, and the anecdote — told by Kleene himself in his
recollections (*Origins of Recursive Function Theory*, 1981) and lovingly retold ever since — is
that the idea came to him in the dentist's chair, while his wisdom teeth were being extracted. Take
the story with the usual grain of salt reserved for well-polished anecdotes; the mathematics,
however, checks out completely, as we are about to verify.

The insight: **don't undo — redo.** If you cannot step backwards from $n$, walk forwards from $0$
and keep a one-step memory. Iterate, $n$ times, the *pair* operation

$$
(a, b) \;\longmapsto\; (b,\, b+1)
$$

starting from $(0,0)$. After $n$ iterations the pair is $(n-1,\, n)$ — the second component counts
the laps, the first trails one lap behind. Take the first component and you have subtracted one,
using nothing but forward iteration.

Watch it happen. Start with
[`let SHIFT = \p. PAIR (SND p) (SUCC (SND p))`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=let%20SHIFT%20%3D%20%5Cp.%20PAIR%20%28SND%20p%29%20%28SUCC%20%28SND%20p%29%29)
and continue in the same session:

```text
nf SND (SHIFT (PAIR 0 0))
nf 3 SHIFT (PAIR 0 0)
let KPRED = \n. FST (n SHIFT (PAIR 0 0))
nf KPRED 4
nf KPRED 0
equiv KPRED 7 = PRED 7
```

The lab answers, in order — one shift puts $1$ in the back seat; three shifts (note the numeral `3`
*driving the loop*) produce the pair $\langle 2, 3\rangle$ in the flesh:

```text
β-normal form · 16 step(s)
  λf x. f x
  = 1  (Church numeral)
```

```text
β-normal form · 60 step(s)
  λf. f (λf' x. f' (f' x)) (λf'' x'. f'' (f'' (f'' x')))
```

and the assembled predecessor works, including at the famous edge case $0 - 1 = 0$:

```text
β-normal form · 46 step(s)
  λf x. f (f (f x))
  = 3  (Church numeral)
```

```text
β-normal form · 9 step(s)
  λf x. x
  = 0 / FALSE  (the same untyped Church term)
```

```text
β-convertibility by normal forms (η is not used)
  left NF:  λf x. f (f (f (f (f (f x)))))
  right NF: λf x. f (f (f (f (f (f x)))))
  equal β-normal forms up to α
```

The lab's built-in `PRED` is a distilled one-liner of the same idea — the "pair" has been compiled
away into two continuation-like arguments, but the trailing-memory trick is intact. Its trace is
short enough to savour whole: run
[`reduce PRED 2`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=reduce%20PRED%202)
and watch nine steps of 1930s dental surgery:

```text
β-reduction (normal order · highlight = next redex)
  start:  (λn. (λf. (λx. n (λg. (λh. h (g f))) (λu. x) (λu'. u')))) (λf'. (λx'. f' (f' x')))
  →β      λf. (λx. (λf'. (λx'. f' (f' x'))) (λg. (λh. h (g f))) (λu. x) (λu'. u'))
  →β      λf. (λx. (λx'. (λg. (λh. h (g f))) ((λg'. (λh'. h' (g' f))) x')) (λu. x) (λu'. u'))
  →β      λf. (λx. (λg. (λh. h (g f))) ((λg'. (λh'. h' (g' f))) (λu. x)) (λu'. u'))
  →β      λf. (λx. (λh. h ((λg. (λh'. h' (g f))) (λu. x) f)) (λu'. u'))
  →β      λf. (λx. (λu. u) ((λg. (λh. h (g f))) (λu'. x) f))
  →β      λf. (λx. (λg. (λh. h (g f))) (λu. x) f)
  →β      λf. (λx. (λh. h ((λu. x) f)) f)
  →β      λf. (λx. f ((λu. x) f))
  →β      λf x. f x
  β-normal form reached in 9 step(s).
  = 1  (Church numeral)
```

````{admonition} Inspect the legend up close
:class: seealso
The lab knows this is the famous one.

- [`church PRED`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=church%20PRED) — the
  conceptual and fully-expanded forms of the "hard one", side by side.
- [`nf PRED 3`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%20PRED%203) — the
  headline act in 11 steps: `λf x. f (f x)` `= 2  (Church numeral)`.
- [`debruijn PRED`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=debruijn%20PRED) —
  the wisdom-tooth term namelessly: `λ λ λ 2 (λ λ 0 (1 3)) (λ 1) (λ 0)`.
````

## One term, two meanings: FALSE is 0

Run [`decode FALSE`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=decode%20FALSE) and
the lab refuses to pick a side:

```text
  = 0 / FALSE  (the same untyped Church term)
```

This is not an implementation quirk. Look at the two definitions namelessly (`debruijn FALSE`,
`debruijn 0`):

```text
  named:    λt f. f
  nameless: λ λ 0
```

```text
  named:    λf x. x
  nameless: λ λ 0
```

Identical. `FALSE` says *take two things, return the second*; the numeral `0` says *take a function
and an argument, apply the function zero times* — which is to say, return the second thing. Same
term, and `equiv FALSE = 0` confirms it officially (`equal β-normal forms up to α`). The untyped
λ-calculus has no opinion about what a term *means*; meaning is supplied entirely by the context
that consumes it. Feed the term to a conditional and it selects the else-branch; feed it a successor
and a number and it iterates zero times:

```text
nf FALSE SUCC 2
```

```text
β-normal form · 2 step(s)
  λf x. f (f x)
  = 2  (Church numeral)
```

`FALSE` just *added zero*. (Its partner in crime appears later in this chapter: when you define the
K combinator, the lab dryly notes `= TRUE  (Church boolean)`.)

How would types tell them apart? Ask
[`ch term \t f. f`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=ch%20term%20%5Ct%20f.%20f):
the principal type is `α → β → β`. The Boolean reading specializes it to $o \to o \to o$; the
numeral reading specializes it to $(\iota\to\iota) \to \iota \to \iota$. Both are instances of one
scheme — but in a typed language you must *declare* which instance you mean, and `Bool` and `Nat`
are different types by fiat. Typing is exactly the act of choosing one meaning and making the
other one ill-formed. Untyped λ-calculus declines to choose, and this little pun is the cheapest
demonstration of what that costs — and what it buys.

## The η-story of exponent zero

Here is a definition so elegant it appears in half the textbooks: exponentiation is

$$
\mathrm{POW} \;=\; \lambda m\, n.\; n\; m
$$

— to compute $m^n$, apply the numeral $n$ *to the numeral* $m$: iterating "compose with $m$"
$n$ times really does build $m^n$. Try it:
[`let NPOW = \m n. n m`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=let%20NPOW%20%3D%20%5Cm%20n.%20n%20m),
then in the same session:

```text
nf NPOW 2 3
nf NPOW 5 0
equiv NPOW 5 0 = 1
```

```text
β-normal form · 16 step(s)
  λx x0. x (x (x (x (x (x (x (x x0)))))))
  = 8  (Church numeral)
```

$2^3 = 8$: flawless. But now the second answer:

```text
β-normal form · 3 step(s)
  λx. x
```

No `(Church numeral)` tag. $5^0$ came out as the *identity function* — one λ short of the numeral
`1` $= \lambda f x.\, f\, x$. And the lab is strict about it:

```text
β-convertibility by normal forms (η is not used)
  left NF:  λx. x
  right NF: λf x. f x
  different β-normal forms
```

Is the textbook wrong? Not quite — it is implicitly working modulo **η**: the principle that
$\lambda x.\, f\, x = f$ whenever $x$ is not free in $f$, i.e. that two functions agreeing on every
argument are equal. Under η, the identity and the numeral `1` collapse into each other. Run
[`eta 1`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=eta%201) and watch
extensionality act:

```text
η-reduction  (λx. f x → f when x ∉ FV(f); no β steps taken)
  start:  λf x. f x
  →η      λf. f
  η-normal form reached in 1 step(s).
```

The lab keeps β and η deliberately separate — `nf` means *exactly* β-normal form, never a silent
mix — so its built-in `POW` takes the other exit: it is **η-expanded** just enough that pure β
suffices. Compare
[`church POW`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=church%20POW): the
definition is `λm n f x. n m f x` — the naive `n m` wearing two extra abstractions — and now
[`nf POW 5 0`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%20POW%205%200) lands
exactly on the canonical numeral:

```text
β-normal form · 4 step(s)
  λf x. f x
  = 1  (Church numeral)
```

A one-character-deep moral: *how equal* you want your functions to be is a design decision, and
$m^0$ is where the decision becomes visible.

## The Ω zoo

Every calculus needs a monster. The classic is

$$
\Omega \;=\; (\lambda x.\, x\, x)\,(\lambda x.\, x\, x),
$$

the self-application applied to itself. β-reduce it and the redex reproduces itself *exactly*:
run [`reduce OMEGA`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=reduce%20OMEGA):

```text
β-reduction (normal order · highlight = next redex)
  start:  (λx. x x) (λx'. x' x')
  →β      (λx. x x) (λx'. x' x')
  →β      (λx. x x) (λx'. x' x')
  →β      (λx. x x) (λx'. x' x')
  ⋮
  … stopped after 60 steps; the displayed term is partial.
```

Sixty identical lines: Ω is a fixed point of β-reduction itself, running in place forever at
constant size. It is the standard witness that not every term has a normal form — and,
via [`ch term \x. x x`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=ch%20term%20%5Cx.%20x%20x),
the standard witness of what simple types forbid to buy their termination theorem:

```text
Term not typeable in STLC: Cannot unify α with α → β
```

But Ω loops *politely*. Add one more `x` and you get its feral cousin:

```text
let OMEGA3 = (\x. x x x) (\x. x x x)
reduce OMEGA3
```

```text
β-reduction (normal order · highlight = next redex)
  start:  (λx. x x x) (λx'. x' x' x')
  →β      (λx. x x x) (λx'. x' x' x') (λx''. x'' x'' x'')
  →β      (λx. x x x) (λx'. x' x' x') (λx''. x'' x'' x'') (λx'''. x''' x''' x''')
  →β      (λx. x x x) (λx'. x' x' x') (λx''. x'' x'' x'') (λx'''. x''' x''' x''') (λx'''2. x'''2 x'''2 x'''2)
  ⋮
  … stopped after 60 steps; the displayed term is partial.
```

Each step rewrites the head redex $(\lambda x.\, x\,x\,x)\,A$ into $A\,A\,A$ — one copy of the
triplicator in, three out — so the term gains a copy per step and its size increases strictly
monotonically: a computation that not only never finishes but never even revisits a previous size. (Try `nf OMEGA3` if you enjoy watching a step-limit report whose "partial term" is a
paragraph wide.) Ω and Ω₃ bracket the two ways to diverge: in place, and explosively. And notice
what `nf OMEGA` actually prints:

```text
Reduction limit reached after 1000 β-step(s)
  Step limit reached. This is not claimed to be a normal form:
  (λx. x x) (λx'. x' x')
```

*Not claimed to be a normal form.* Hold that phrase — it becomes a theorem at the end of the
chapter.

## Fixed points of everything

The fixed-point combinator
([`church Y`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=church%20Y) shows
`λf. (λx. f (x x)) (λx. f (x x))`) delivers on an outrageous promise: **every** term $F$, without
exception, has a fixed point, and $Y\,F$ is one. The two-line proof is best watched live with a
free variable standing in for an arbitrary $F$ — run
[`reduce Y g`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=reduce%20Y%20g):

```text
β-reduction (normal order · highlight = next redex)
  start:  (λf. (λx. f (x x)) (λx'. f (x' x'))) g
  →β      (λx. g (x x)) (λx'. g (x' x'))
  →β      g ((λx. g (x x)) (λx'. g (x' x')))
  →β      g (g ((λx. g (x x)) (λx'. g (x' x'))))
  →β      g (g (g ((λx. g (x x)) (λx'. g (x' x')))))
  ⋮
  … stopped after 60 steps; the displayed term is partial.
```

Line 2 to line 3 is the whole theorem: the term reached after one step reduces to `g` applied to
*itself*, so $Y g =_\beta g\,(Y g)$ — and then, having nothing better to do, it keeps unfolding,
sprouting one more `g` per step, forever.

Because *every* term qualifies, we can demand fixed points of things that have no business having
them. A fixed point of `TRUE`? `TRUE` ignores its second argument and returns its first, so its
fixed point must be a function that swallows an argument and returns itself. Run `reduce Y TRUE`:

```text
β-reduction (normal order · highlight = next redex)
  start:  (λf. (λx. f (x x)) (λx'. f (x' x'))) (λt. (λf'. t))
  →β      (λx. (λt. (λf. t)) (x x)) (λx'. (λt'. (λf'. t')) (x' x'))
  →β      (λt. (λf. t)) ((λx. (λt'. (λf'. t')) (x x)) (λx'. (λt''. (λf''. t'')) (x' x')))
  →β      λf. (λx. (λt. (λf'. t)) (x x)) (λx'. (λt'. (λf''. t')) (x' x'))
  ⋮
  →β      λf. (λf'. (λf''. (λx. (λt. (λf'''. t)) (x x)) (λx'. (λt'. (λf'''2. t')) (x' x'))))
  ⋮
  … stopped after 60 steps; the displayed term is partial.
```

An ever-growing tower `λf. λf'. λf''. …` — folklore calls such terms *ogres*: they devour any
number of arguments and are never satisfied. And a fixed point of `NOT`? Classically, $X = \neg X$
has no solution at all; here `reduce Y NOT` obligingly builds one, queueing up alternating
`FALSE`/`TRUE` arguments that the poor Boolean will never finish consuming:

```text
β-reduction (normal order · highlight = next redex)
  start:  (λf. (λx. f (x x)) (λx'. f (x' x'))) (λp. p (λt. (λf'. f')) (λt'. (λf''. t')))
  →β      (λx. (λp. p (λt. (λf. f)) (λt'. (λf'. t'))) (x x)) (λx'. (λp'. p' (λt''. (λf''. f'')) (λt'''. (λf'''. t'''))) (x' x'))
  →β      (λp. p (λt. (λf. f)) (λt'. (λf'. t'))) ((λx. (λp'. p' (λt''. (λf''. f'')) (λt'''. (λf'''. t'''))) (x x)) (λx'. (λp''. p'' (λt'''2. (λf'''2. f'''2)) (λt'''3. (λf'''3. t'''3))) (x' x')))
  ⋮
  … stopped after 60 steps; the displayed term is partial.
```

What does it *mean* to "solve" $X =_\beta \mathrm{NOT}\,X$? Only this: the equation holds as
β-convertibility between terms without normal forms. `Y NOT` is not `TRUE` and not `FALSE`; it is a
third thing, a perfectly legal term that no context can ever force to a Boolean answer. This
universality of fixed points is simultaneously the calculus's superpower (general recursion:
Fibonacci in the *Grand calculations* chapter runs on exactly this `Y`) and its original sin — in
Church's first system, where terms doubled as propositions, a fixed point of negation is the
Kleene–Rosser/Curry paradox waiting to happen, and it is precisely why consistent type theories
must evict `Y` and earn recursion some other way. One honest caveat, verified: don't ask `equiv`
to certify the fixed-point equation —

```text
equiv Y NOT = NOT (Y NOT)
```

```text
Inconclusive: at least one side did not reach β-normal form within the limit.
```

`equiv` works by normalizing both sides, and neither side terminates. The convertibility is real
(the `reduce Y g` trace above *is* the proof), but it lives one level up from what a
normalize-and-compare procedure can see. More on this at the chapter's end.

## The combinator zoo

In 1924 — before Church, before the λ — Moses Schönfinkel showed that all of logic's
variable-shuffling could be done by a handful of fixed "building blocks". Haskell Curry rediscovered
and systematized them, and his 1930 dissertation made the letters canonical. The zoo's residents,
in the lab's `let` syntax (definitions are session-local; `defs` lists them):
start with
[`let S = \x y z. x z (y z)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=let%20S%20%3D%20%5Cx%20y%20z.%20x%20z%20%28y%20z%29)
and continue:

```text
let K = \x y. x
let I = \x. x
let B = \f g x. f (g x)
let C = \f x y. f y x
let W = \f x. f x x
```

(One easter egg on the way in — the lab annotates `let K = \x y. x` with `= TRUE  (Church boolean)`.
K *is* TRUE, just as FALSE *is* 0: the pun section above, striking again.)

Now ask `ch term` for each combinator's principal type, and something wonderful happens: the zoo
turns out to be a textbook of implicational logic. Verified with `ch term` on each body:

| Combinator | Term | Principal type | As a logic law |
|---|---|---|---|
| S | `λx y z. x z (y z)` | `(α → β → γ) → (α → β) → α → γ` | Frege's axiom (distribution) |
| K | `λx y. x` | `α → β → α` | *a fortiori* (weakening) |
| I | `λx. x` | `α → α` | identity |
| B | `λf g x. f (g x)` | `(α → β) → (γ → α) → γ → β` | hypothetical syllogism (composition) |
| C | `λf x y. f y x` | `(α → β → γ) → β → α → γ` | exchange of premises |
| W | `λf x. f x x` | `(α → α → β) → α → β` | contraction of premises |

Every row is a tautology of minimal logic, and `ch type` will happily reprove any of them from the
proposition side — with a Lean-ready witness. For S:

```text
ch type (A -> B -> C) -> (A -> B) -> A -> C
```

```text
╭──────────────── Found proof ────────────────╮
│ Goal:         (A → B → C) → (A → B) → A → C │
│ Lambda-term:  λp q r. p r (q r)             │
╰─────────────────────────────────────────────╯
╭─────────────────────────────── Lean ───────────────────────────────╮
│ theorem ch_proof {A B C : Prop} : (A → B → C) → (A → B) → A → C := │
│   fun p q r => p r (q r)                                           │
╰────────────────────────────────────────────────────────────────────╯
```

The search found S. It had to: by Curry–Howard, *being the principal inhabitant of that type* is
what S is. Curry's deeper observation was structural: **B, C, K, W** form a complete basis, and
each one embodies exactly one bookkeeping right you may exercise over hypotheses — compose them
(B), reorder them (C), discard them (K), duplicate them (W). Substructural logics are what you get
by revoking these rights one combinator at a time: forbid K and you get relevance logic (no
throwing hypotheses away); forbid W and contraction dies (each hypothesis used at most once, the
road to linear logic). A century-old zoo, and it turned out to be a map of logic's design space.

## SKI in practice: bracket abstraction

Schönfinkel's headline theorem is more brutal still: **S and K alone suffice.** Every closed
λ-term — every one — can be rewritten with no λ, no bound variables, no α-renaming headaches, just
applications of two constants. The compilation is called *bracket abstraction*: to eliminate
$\lambda x$ from a body, recurse with three rules:

$$
[x]\,x = \mathbf{I}, \qquad
[x]\,M = \mathbf{K}\,M \;\; (x \notin M), \qquad
[x]\,(M\,N) = \mathbf{S}\,([x]M)\,([x]N).
$$

And I itself? Apply the rules to $\lambda x.\,x$ viewed as $[x]\,x$ where we refuse to use the
first rule. Since $x = x\,$ appears alone, split nothing; instead note the slick classical answer:
$\mathbf{I} = \mathbf{S}\,\mathbf{K}\,\mathbf{K}$. Why does that work? $S\,K\,K\,v$ unfolds to
$K\,v\,(K\,v)$ — "give me $v$, and also this other thing I will ignore" — which is $v$. Keep the
zoo session open and watch, five steps, no waste:

```text
reduce S K K v
```

```text
β-reduction (normal order · highlight = next redex)
  start:  (λx. (λy. (λz. x z (y z)))) (λx'. (λy'. x')) (λx''. (λy''. x'')) v
  →β      (λy. (λz. (λx. (λy'. x)) z (y z))) (λx'. (λy''. x')) v
  →β      (λz. (λx. (λy. x)) z ((λx'. (λy'. x')) z)) v
  →β      (λx. (λy. x)) v ((λx'. (λy'. x')) v)
  →β      (λy. v) ((λx. (λy'. x)) v)
  →β      v
  β-normal form reached in 5 step(s).
```

Officially, then:

```text
equiv S K K = I
```

```text
β-convertibility by normal forms (η is not used)
  left NF:  λz. z
  right NF: λx. x
  equal β-normal forms up to α
```

— while `alpha S K K = I` correctly reports `≢α not alpha-equivalent`: as raw syntax they are
different terms; equality here is a *computation*, not a spelling check. One worked example of the
S-rule to take home: compiling composition. $[f]([g]([x]\,f(g\,x)))$ grinds down to
$\mathbf{S}\,(\mathbf{K}\,\mathbf{S})\,\mathbf{K}$, and the lab confirms the folklore:

```text
equiv S (K S) K = B
```

```text
β-convertibility by normal forms (η is not used)
  left NF:  λz y z0. z (y z0)
  right NF: λf g x. f (g x)
  equal β-normal forms up to α
```

This is not just a party trick. Bracket abstraction is a *compiler* — from λ-calculus to a language
with no binders at all — and its descendants (supercombinators, categorical combinators) sat inside
real functional-language implementations in the 1980s. When binders get hard, combinators are the
traditional escape hatch.

```{admonition} Exercise: the third K is a decoy
:class: tip
The middle argument of `S K K` is never actually used. Predict what `S K S`, `S K OMEGA`, and in
general `S K M` reduce to — then check yourself in the lab before opening the solution.
```

````{admonition} Solution
:class: dropdown
`S K M x → K x (M x) → x` for **any** `M` whose application `M x` we then discard — so every
`S K M` is an identity. The lab agrees:

```text
nf S K S
```

```text
β-normal form · 4 step(s)
  λz. z
```

and `equiv S K S = I` reports `equal β-normal forms up to α`. Even the scary one is tamed —
`nf S K OMEGA` answers

```text
β-normal form · 4 step(s)
  λz. z
```

because `nf` uses *normal order*, which discards the `OMEGA` before ever reducing it (watch
`reduce S K OMEGA`: the step `λz. (λy. z) ((λx. x x) (λx'. x' x') z) →β λz. z` throws the bomb
away unexploded). An applicative-order evaluator would diverge instead — one more reason
evaluation order is part of the mathematics, not a detail.
````

## de Bruijn's revenge

Nicolaas de Bruijn, building the pioneering AUTOMATH proof checker around 1970, got fed up with
bound-variable names and, in a famous 1972 paper, deleted them: replace each bound variable by a
number counting how many binders sit between it and its own λ. Names become arithmetic;
α-equivalence becomes *literal identity of strings*. The lab's `debruijn` command shows the view
that proof-assistant kernels — Lean's included — actually compare.

Two classics. First, terms that **look different but are the same**. Shadowing makes
`λx. λx. x` look exotic — which `x` is bound? Run
[`debruijn \x. \x. x`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=debruijn%20%5Cx.%20%5Cx.%20x)
and then `debruijn \a. \b. b`:

```text
  named:    λx x'. x'
  nameless: λ λ 0
```

```text
  named:    λa b. b
  nameless: λ λ 0
```

Same nameless skeleton — the inner binder wins, the shadowed outer `x` is unreachable, and
`alpha \x. \x. x = \a. \b. b` duly reports `≡α alpha-equivalent`. (For the same reason
`λx y. x (x y)` and `λf x. f (f x)` — which share only one letter — are both `λ λ 1 (1 0)`: the
numeral 2 in disguise, twice.)

Second, terms that **look nearly identical but differ**. The classic exam trap: is `λx. λy. x`
the same as `λx. λx. x`? One letter apart —

```text
debruijn \x. \y. x
```

```text
  named:    λx y. x
  nameless: λ λ 1
```

`λ λ 1` versus `λ λ 0`: the first returns the *outer* argument (it is K, alias TRUE), the second
the *inner* (FALSE, alias 0). `alpha \x. \y. x = \x. \x. x` answers `≢α not alpha-equivalent`, and
no amount of renaming will ever connect a `1` to a `0`. That is de Bruijn's revenge on the naming
disputes of mathematical prose: once names are gone, every question about binding has a mechanical,
kernel-checkable answer — which is exactly how Lean can compare your proof terms without ever
asking what you meant by `x`.

## Numbers are for-loops

By now the theme is unmistakable, so let us say it plainly: a Church numeral is not a datum that
*represents* $n$ — it **is** the control structure `for i in 1..n`. Everything numerals "are" in
this calculus follows from taking that literally.

Iterate a Boolean flip three times from `TRUE` and you have computed the parity of 3 — run
[`nf 3 NOT TRUE`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%203%20NOT%20TRUE):

```text
β-normal form · 11 step(s)
  λt f. f
  = 0 / FALSE  (the same untyped Church term)
```

while `nf 4 NOT TRUE` and `nf 10 NOT TRUE` both come back `= TRUE  (Church boolean)` (14 and 32
steps): even numbers of flips cancel. Iterate the *successor* and you have addition with no
`PLUS` in sight — `nf 3 SUCC 4`:

```text
β-normal form · 11 step(s)
  λf x. f (f (f (f (f (f (f x))))))
  = 7  (Church numeral)
```

Three is "do it three times"; do *successor* three times to 4 and you have 7. (Indeed the official
`PLUS m n f x = m f (n f x)` is just this idea inlined.) Iterate an *iterator* and you have
exponentiation — the tower
[`nf 2 2 2 f x`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%202%202%202%20f%20x)
applies `f` exactly $2^{2^2}=16$ times:

```text
β-normal form · 44 step(s)
  f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f x)))))))))))))))
```

And the predecessor legend that opened this chapter was the same move with a compound loop body:
`n SHIFT (PAIR 0 0)` is a for-loop over a two-field state. Church's encoding anticipated, by
several decades, a slogan the functional programmers would later sell as new: *data is defined by
how you fold over it.*

```{admonition} Exercise: predict the parity
:class: tip
Without running it: what is `nf 5 NOT FALSE` — and roughly how many steps should it take, given
that `nf 3 NOT TRUE` took 11 and `nf 4 NOT TRUE` took 14?
```

````{admonition} Solution
:class: dropdown
Five flips starting from `FALSE`: odd, so `TRUE`. The step count grows by 3 per extra flip:

```text
β-normal form · 17 step(s)
  λt f. t
  = TRUE  (Church boolean)
```
````

## Honest infinity

For the finale, ask the lab the most innocent question in mathematics — is a thing equal to
itself? Run
[`equiv OMEGA = OMEGA`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=equiv%20OMEGA%20%3D%20OMEGA):

```text
Inconclusive: at least one side did not reach β-normal form within the limit.
```

The lab just declined to affirm that Ω equals Ω. Before you file a bug report, note that it is
perfectly capable of the *syntactic* observation — `alpha OMEGA = OMEGA` instantly answers
`≡α alpha-equivalent`. What it refuses to certify is *β-convertibility*, because its `equiv` is a
specific algorithm: normalize both sides, compare up to α. Ω has no normal form, the fuel runs out,
and the algorithm reports precisely what it knows: nothing.

This is not a weakness of one little web lab; it is the shape of the theorem. Church proved in 1936
— in the very paper that introduced what we now call Church's Thesis, months before Turing's
machines — that β-convertibility of λ-terms is **undecidable**: no algorithm answers correctly on
all pairs. What remains is *semi-decidability*: if two terms **are** convertible, a patient search
will eventually find a common reduct and say yes; if they are not, no general method can be counted
on ever to say no. An honest terminating tool therefore has exactly three outputs — *yes*, *no*,
and *I ran out of fuel* — and collapsing the third into either of the first two would be a lie.
Every "Step limit reached — this is not claimed to be a normal form" you have seen in this chapter
is that third answer, worn as a badge.

The sting in the tail: sometimes *we* can settle what the algorithm cannot. Consider
`equiv Y I = OMEGA` — also `Inconclusive`, both sides diverge. But you can prove by hand that they
are **not** convertible: the only reduct of Ω is Ω itself, while every reduct of `Y I` is of the
form $I^k(W W)$ for $W = \lambda x.\, I\,(x\,x)$ — and by the Church–Rosser theorem, convertible
terms must share a common reduct, which these two term families visibly never do. A human argument,
using a confluence theorem *about* the rewriting system, decides a case the general procedure
inside it cannot. That is the correct final image for this chapter: the lab is scrupulously honest
about the boundary of mechanical knowledge — and mathematics is what you do standing on the far
side of it.

```{admonition} Where this connects
:class: seealso
- [Lecture 2 — λ-calculus](../lectures/l2_lambda_calculus.md) — β, η, normal forms, Church
  encodings and Y: the theory behind every trick in this chapter.
- [Lecture 1 — type theory](../lectures/l1_type_theory.md) — why `\x. x x` is untypable, and how
  types buy back termination by evicting the Ω zoo.
- [Lecture 3 — propositional logic](../lectures/l3_propositional.md) — the combinator zoo's types
  as axioms; `ch type` as a proof search you can also drive by hand with `prove`.
- [Cheatsheet](../appendix/cheatsheet.md) — every command used here (`reduce`, `nf`, `eta`,
  `debruijn`, `alpha`, `equiv`, `let`, `church`, `decode`, `ch`) on one page.
```
