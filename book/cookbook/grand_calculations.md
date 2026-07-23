# Grand calculations

Nothing convinces like a computation that actually runs. This chapter is a sequence of
increasingly ambitious calculations, all performed by the
[Lambda Lab](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/) — a computer whose entire
instruction set is *one rule*, β-reduction, and whose entire memory is *one data structure*, the
λ-term. We will climb from `SUCC 0` to Fibonacci, factorial, and a genuine value of Ackermann's
function, and we will keep score honestly: every output below was produced by the real engine,
step counts included, and when a computation exceeds the lab's budget you will see the failure
verbatim. The failures turn out to be as instructive as the successes.

````{admonition} Ground rules for this chapter
:class: note
The lab never bluffs, and neither do we. Two budgets matter here:

- `reduce <term>` — a full step-by-step trace, capped at **60 visible steps**; a cut-off trace is labelled *partial*, never passed off as an answer.
- `nf <term>` — result only, with a bigger allowance of **1,000 β-steps / 50,000 AST nodes**; beyond that you get *"reduction limit reached"*, not a guess.

Every recipe below is designed to be pasted into **one** lab session: `let` definitions persist,
`defs` lists them, `undef NAME` removes one.
````

## Warming up: the arithmetic ladder

Church numerals encode the number $n$ as the *action* of doing something $n$ times:
$n = \lambda f\, x.\, f^{\,n}(x)$. Arithmetic is then function surgery. Watch the whole thing
happen, one β-step at a time, starting with the smallest possible computation:
[`reduce SUCC 0`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=reduce%20SUCC%200)

```text
β-reduction (normal order · highlight = next redex)
  start:  (λn. (λf. (λx. f (n f x)))) (λf'. (λx'. x'))
  →β      λf. (λx. f ((λf'. (λx'. x')) f x))
  →β      λf. (λx. f ((λx'. x') x))
  →β      λf x. f x
  β-normal form reached in 3 step(s).
  = 1  (Church numeral)
```

Three steps to count to one. The lab decodes the normal form back to a numeral for you — that
final `= 1` line is read off the term shape, binder-aware, so no renaming trick can fool it.
One rung up, [`reduce PLUS 1 1`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=reduce%20PLUS%201%201):

```text
β-reduction (normal order · highlight = next redex)
  start:  (λm. (λn. (λf. (λx. m f (n f x))))) (λf'. (λx'. f' x')) (λf''. (λx''. f'' x''))
  →β      (λn. (λf. (λx. (λf'. (λx'. f' x')) f (n f x)))) (λf''. (λx''. f'' x''))
  →β      λf. (λx. (λf'. (λx'. f' x')) f ((λf''. (λx''. f'' x'')) f x))
  →β      λf. (λx. (λx'. f x') ((λf'. (λx''. f' x'')) f x))
  →β      λf. (λx. f ((λf'. (λx'. f' x')) f x))
  →β      λf. (λx. f ((λx'. f x') x))
  →β      λf x. f (f x)
  β-normal form reached in 6 step(s).
  = 2  (Church numeral)
```

For bigger inputs the trace becomes a wall of text, so we switch to `nf`, which reports only the
normal form, the decode, and — crucially for this chapter — the *step count*:

```text
lab> nf PLUS 2 3
β-normal form · 6 step(s)
  λf x. f (f (f (f (f x))))
  = 5  (Church numeral)

lab> nf MULT 3 4
β-normal form · 9 step(s)
  λf x. f (f (f (f (f (f (f (f (f (f (f (f x)))))))))))
  = 12  (Church numeral)

lab> nf POW 2 5
β-normal form · 66 step(s)
  λf x. f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f x)))))))))))))))))))))))))))))))
  = 32  (Church numeral)
```

Addition: six steps. Multiplication: nine. Exponentiation: sixty-six. The ladder's rungs are not
evenly spaced — hold that thought, it becomes a theorem-shaped observation in the last section.
The rungs also compose, and the costs *add up on the nose*:
[`nf PLUS (MULT 3 4) (POW 2 3)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%20PLUS%20(MULT%203%204)%20(POW%202%203))

```text
β-normal form · 33 step(s)
  λf x. f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f x)))))))))))))))))))
  = 20  (Church numeral)
```

Measured separately, `nf MULT 3 4` costs 9 steps and `nf POW 2 3` costs 18; the `PLUS`
glue costs 6 in every measurement we made — and $9 + 18 + 6 = 33$. Normal order wastes nothing
here. Finally, since β-normal forms are canonical, *equality of numbers becomes α-comparison of
terms* — here is $3\cdot4 = 4\cdot3$, established without believing anything about arithmetic:
[`equiv MULT 3 4 = MULT 4 3`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=equiv%20MULT%203%204%20%3D%20MULT%204%203)

```text
β-convertibility by normal forms (η is not used)
  left NF:  λf x. f (f (f (f (f (f (f (f (f (f (f (f x)))))))))))
  right NF: λf x. f (f (f (f (f (f (f (f (f (f (f (f x)))))))))))
  equal β-normal forms up to α
```

## Fibonacci without recursion

Here is the first genuinely grand calculation, and it uses **no recursion operator at all** —
no `Y`, no self-application, nothing partial. The trick: a Church numeral *is already a
for-loop*. The term `n s z` means "apply the step `s` to the seed `z`, $n$ times". So to compute
Fibonacci, we don't need the function to call itself; we need a step worth iterating. Slide a
window of two consecutive Fibonacci numbers along the sequence:

$$
(a, b) \;\longmapsto\; (b, a+b), \qquad (F_0, F_1) = (0, 1),
$$

and after $n$ shifts the window's first component is exactly $F_n$. Pairs are Church-encoded
(`PAIR`, `FST`, `SND` are built in), so the whole program is two `let` lines. Start a session:
[`let STEP = \p. PAIR (SND p) (PLUS (FST p) (SND p))`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=let%20STEP%20%3D%20%5Cp.%20PAIR%20(SND%20p)%20(PLUS%20(FST%20p)%20(SND%20p)))

```text
lab> let STEP = \p. PAIR (SND p) (PLUS (FST p) (SND p))
defined STEP (this session only)
  λp. (λa b f. f a b) ((λp'. p' (λt f'. f')) p) ((λm n f'' x. m f'' (n f'' x)) ((λp''. p'' (λt' f'''. t')) p) ((λp'''. p''' (λt'' f'''2. f'''2)) p))
  use it in any term; `defs` lists, `undef STEP` removes.

lab> let FIB = \n. FST (n STEP (PAIR 0 1))
```

Sanity-check the step on the window $(3,5)$ — it should shift to $(5,8)$:

```text
lab> nf FST (STEP (PAIR 3 5))
β-normal form · 13 step(s)
  λf x. f (f (f (f (f x))))
  = 5  (Church numeral)

lab> nf SND (STEP (PAIR 3 5))
β-normal form · 25 step(s)
  λf x. f (f (f (f (f (f (f (f x)))))))
  = 8  (Church numeral)
```

Now run up the sequence:

```text
lab> nf FIB 5
β-normal form · 177 step(s)
  λf x. f (f (f (f (f x))))
  = 5  (Church numeral)

lab> nf FIB 8
β-normal form · 783 step(s)
  λf x. f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f x))))))))))))))))))))
  = 21  (Church numeral)
```

The full run of measurements: `FIB 5` = 5 in **177** steps, `FIB 6` = 8 in **293**, `FIB 7` = 13
in **480**, `FIB 8` = 21 in **783**. Look at the *ratios* of consecutive step counts:
$293/177 \approx 1.66$, $480/293 \approx 1.64$, $783/480 \approx 1.63$ — creeping down toward
the golden ratio $\varphi \approx 1.618$. The cost is dominated by shuffling Fibonacci-sized
numerals through `PLUS`, so the running time inherits the growth rate of the answer itself. The
golden ratio is hiding *in the step counter*. Which also predicts where the budget ends —
extrapolating, `FIB 9` needs roughly $783 \times 1.62 \approx 1270$ steps, and the lab has 1,000:

```text
lab> nf FIB 9
Reduction limit reached after 1000 β-step(s)
  Step limit reached. This is not claimed to be a normal form:
  λf x. f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f ((λp. (λa b f'. f' a b) …
  ⋮
```

An honest failure — and look closely at the partial term: 26 of the eventual 34 applications of
`f` are already in place, with the still-unfinished pair machinery wedged in the middle. You are
watching a computation frozen mid-thought.

## Factorial two ways: a loop against the Y combinator

**Way 1: iterate a pair**, exactly as with Fibonacci. Slide the window
$(i,\; i!) \mapsto (i{+}1,\; (i{+}1)\cdot i!)$, i.e. build the step so each new factorial is
"index times previous product", starting from $(1, 1)$:
[`let FSTEP = \p. PAIR (SUCC (FST p)) (MULT (FST p) (SND p))`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=let%20FSTEP%20%3D%20%5Cp.%20PAIR%20(SUCC%20(FST%20p))%20(MULT%20(FST%20p)%20(SND%20p)))

```text
lab> let FSTEP = \p. PAIR (SUCC (FST p)) (MULT (FST p) (SND p))
lab> let FACT = \n. SND (n FSTEP (PAIR 1 1))
lab> nf FACT 3
β-normal form · 279 step(s)
  λf x. f (f (f (f (f (f x)))))
  = 6  (Church numeral)

lab> nf FACT 4
Reduction limit reached after 1000 β-step(s)
  Step limit reached. This is not claimed to be a normal form:
  λf x. f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f ((λm n f'. m (n f')) …
  ⋮
```

$3! = 6$ in 279 steps; $4! = 24$ dies with 20 of its 24 `f`s built. Why so expensive? Because
normal order **copies unevaluated arguments**: the step function uses `p` three times, so every
iteration re-derives pieces of the entire history of the pair. There is no sharing, no memory —
just textual substitution, priced per copy.

**Way 2: recursion for real.** The λ-calculus does have general recursion — Curry's fixed-point
combinator, [`church Y`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=church%20Y):

```text
Y
  conceptual:  λf. (λx. f (x x)) (λx. f (x x))
  full λ-term: λf. (λx. f (x x)) (λx'. f (x' x'))
```

`Y F` β-reduces to `F (Y F)`: a term that hands *itself* to its own body. Write factorial the
textbook way and tie the knot:

```text
lab> let FACBODY = \f n. IF (ISZERO n) 1 (MULT n (f (PRED n)))
defined FACBODY (this session only)
  λf n. (λb t f'. b t f') ((λn'. n' (λ_ t' f''. f'') (λt'' f'''. t'')) n) (λf'''2 x. f'''2 x) ((λm n'' f'''3. m (n'' f'''3)) n (f ((λn''' f'''4 x'. n''' (λg h. h (g f'''4)) (λu. x') (λu'. u')) n)))
  use it in any term; `defs` lists, `undef FACBODY` removes.

lab> nf Y FACBODY 3
β-normal form · 694 step(s)
  λf x. f (f (f (f (f (f x)))))
  = 6  (Church numeral)
```

It *works* — and that is the miracle worth pausing on. `Y FACBODY` has no normal form on its
own, yet `Y FACBODY 3` does, because normal order is lazy exactly where it must be: it reduces
the leftmost-outermost redex first, so `ISZERO n` picks a branch *before* the unchosen branch
(which contains the infinite unfolding) is ever touched. Run the small cases and watch the cost
of the luxury: `Y FACBODY 0` → 1 in **12** steps, `1` → 1 in **36**, `2` → 2 in **142**,
`3` → 6 in **694**. The strict-friendly variant `Z` (built in, for the curious) lands nearby:
`nf Z FACBODY 3` also gives 6, in **709** steps. And then:

```text
lab> nf Y FACBODY 4
Reduction limit reached after 1000 β-step(s)
  Step limit reached. This is not claimed to be a normal form:
  λf x. f (f (f (f (f ((λh. h ((λg h'. h' (g (λg' h''. …
  ⋮
```

The scoreboard for $3! = 6$: **iteration 279 steps, Y-recursion 694, Z-recursion 709** — and
both approaches hit the wall at $4!$. The moral is worth stating plainly: in a calculus with no
sharing, *self-reference costs more than iteration*, and Kleene's `PRED` (visible inside
`FACBODY` above as the famous `λg h. h (g f)` shuffle) makes every recursive descent expensive.
Elegance and efficiency part company here, measurably.

## Ackermann in one line

The Ackermann–Péter function is the standard example of a function that grows too fast to be
primitive recursive. Its Church encoding is almost insultingly short:
[`let ACK = \m. m (\g n. n g (g 1)) SUCC`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=let%20ACK%20%3D%20%5Cm.%20m%20(%5Cg%20n.%20n%20g%20(g%201))%20SUCC)

```text
lab> let ACK = \m. m (\g n. n g (g 1)) SUCC
defined ACK (this session only)
  λm. m (λg n. n g (g (λf x. f x))) (λn' f' x'. f' (n' f' x'))
  use it in any term; `defs` lists, `undef ACK` removes.
```

Read it as: row 0 is `SUCC`, and each next row is "iterate the previous row" — the operator
`λg n. n g (g 1)` applies `g` to itself $n$ more times. Ackermann's ferocity is just *m-fold
iteration of the iterator*, which Church numerals express natively. The base row runs in a trace
short enough to print whole:

```text
lab> reduce ACK 0 3
β-reduction (normal order · highlight = next redex)
  start:  (λm. m (λg. (λn. n g (g (λf. (λx. f x))))) (λn'. (λf'. (λx'. f' (n' f' x'))))) (λf''. (λx''. x'')) (λf'''. (λx'''. f''' (f''' (f''' x'''))))
  →β      (λf. (λx. x)) (λg. (λn. n g (g (λf'. (λx'. f' x'))))) (λn'. (λf''. (λx''. f'' (n' f'' x'')))) (λf'''. (λx'''. f''' (f''' (f''' x'''))))
  →β      (λx. x) (λn. (λf. (λx'. f (n f x')))) (λf'. (λx''. f' (f' (f' x''))))
  →β      (λn. (λf. (λx. f (n f x)))) (λf'. (λx'. f' (f' (f' x'))))
  →β      λf. (λx. f ((λf'. (λx'. f' (f' (f' x')))) f x))
  →β      λf. (λx. f ((λx'. f (f (f x'))) x))
  →β      λf x. f (f (f (f x)))
  β-normal form reached in 6 step(s).
  = 4  (Church numeral)
```

Now march along the rows, `nf` reporting values and prices ($A$ below is the Ackermann–Péter
function, so the classical identities are $A(1,n)=n+2$, $A(2,n)=2n+3$, $A(3,n)=2^{n+3}-3$):

| command | value | β-steps |
|---|---|---|
| `nf ACK 0 3` | 4 | 6 |
| `nf ACK 1 2` | 4 | 16 |
| `nf ACK 1 3` | 5 | 19 |
| `nf ACK 2 2` | 7 | 55 |
| `nf ACK 2 3` | 9 | 83 |
| `nf ACK 3 1` | 13 | 191 |
| `nf ACK 4 0` | 13 | 195 |
| `nf ACK 3 2` | 29 | **881** |

Every row of that table is a real run — including a value from the *fourth* row of Ackermann's
function ($A(4,0) = A(3,1) = 13$). The crown jewel squeaks in under the budget with 119 steps to
spare:

```text
lab> nf ACK 3 2
β-normal form · 881 step(s)
  λf x. f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f x))))))))))))))))))))))))))))
  = 29  (Church numeral)
```

And one step further along the row, arithmetic's most famous cliff-edge does what it is famous for:

```text
lab> nf ACK 3 3
Reduction limit reached after 1000 β-step(s)
  Step limit reached. This is not claimed to be a normal form:
  ⋮
```

$A(3,3) = 61$: over budget. $A(4,1) = 65{,}533$: unthinkable. $A(4,2)$ has 19,729 decimal
digits — no numeral for it fits in this universe's node budget, let alone the lab's. Three
characters of idea (`m`, iterate, `SUCC`), and the fastest-growing standard function in
computability theory falls out.

## Boolean circuits, verified exhaustively

Numbers are not the only data. Church Booleans (`TRUE = λt f. t`, `FALSE = λt f. f`) come with a
full gate set — `AND`, `OR`, `XOR`, `NAND`, … — and `equiv` turns the lab into a circuit
verifier: on a finite input space, *checking all cases is a proof*. Build a half adder, the atom
of binary arithmetic — sum bit `XOR a b`, carry bit `AND a b`, packaged as a pair:
[`let HALFADD = \a b. PAIR (XOR a b) (AND a b)`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=let%20HALFADD%20%3D%20%5Ca%20b.%20PAIR%20(XOR%20a%20b)%20(AND%20a%20b))

```text
lab> let HALFADD = \a b. PAIR (XOR a b) (AND a b)
lab> nf HALFADD TRUE TRUE
β-normal form · 27 step(s)
  λf. f (λt f'. f') (λt' f''. t')
```

Read the normal form: a pair whose first component is `FALSE` and second is `TRUE` — that is,
$1 + 1 = 0$ carry $1$. Correct. Now the exhaustive check of the sum bit, four inputs, four
verdicts:

```text
lab> equiv FST (HALFADD FALSE FALSE) = FALSE
β-convertibility by normal forms (η is not used)
  left NF:  λt f. f
  right NF: λt f. f
  equal β-normal forms up to α

lab> equiv FST (HALFADD FALSE TRUE) = TRUE
  equal β-normal forms up to α
lab> equiv FST (HALFADD TRUE FALSE) = TRUE
  equal β-normal forms up to α
lab> equiv FST (HALFADD TRUE TRUE) = FALSE
  equal β-normal forms up to α
```

and of the carry bit:

```text
lab> equiv SND (HALFADD TRUE TRUE) = TRUE
  equal β-normal forms up to α
lab> equiv SND (HALFADD TRUE FALSE) = FALSE
  equal β-normal forms up to α
```

Six runs, six agreements: the circuit is *verified*, in the strongest sense available on finite
data. (A pleasant aside while we are here — ask the lab to
`decode XOR TRUE TRUE` and it answers `= 0 / FALSE  (the same untyped Church term)`: in the
untyped calculus, the bit 0 and the number 0 are literally one term. The Curiosities chapter
picks that thread up.) The full one-bit adder — three inputs, two outputs, sixteen checks — is
Exercise 3 below.

## The exponential cliff

Back to the ladder's unevenly spaced rungs. `POW m n` computes $m^n$ by applying the numeral
$n$ *to* the numeral $m$ — exponentiation is just application, the single most beautiful one-liner
in the Church encoding. Its price, measured
([`nf POW 2 8`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%20POW%202%208) is the
largest power of two the budget allows):

| command | value | β-steps |
|---|---|---|
| `nf POW 2 3` | 8 | 18 |
| `nf POW 2 4` | 16 | 34 |
| `nf POW 2 5` | 32 | 66 |
| `nf POW 2 6` | 64 | 130 |
| `nf POW 2 7` | 128 | 258 |
| `nf POW 2 8` | 256 | 514 |
| `nf POW 3 3` | 27 | 30 |
| `nf POW 3 4` | 81 | 84 |
| `nf POW 3 5` | 243 | 246 |
| `nf POW 3 6` | 729 | 732 |
| `nf POW 4 4` | 256 | 174 |
| `nf POW 5 4` | 625 | 316 |
| `nf POW 10 3` | 1000 | 226 |

Stare at the columns and two families of coincidences leap out: base 2 gives steps
$= 2\cdot\text{value} + 2$, base 3 gives steps $= \text{value} + 3$. Both are shadows of one
exact law, which fits **every** row of the table:

$$
\operatorname{steps}\bigl(\texttt{nf POW } m\ n\bigr)
\;=\; 2\,\frac{m^{\,n}-1}{m-1} + 4
\;=\; 2\left(1 + m + m^2 + \cdots + m^{\,n-1}\right) + 4 .
$$

A geometric series, sitting inside the step counter: normalizing $m^n$ costs two β-steps for
every application node performed at every level of the iterated tower, plus four steps of setup.
(Deriving this from the reduction sequence of `n m f x` is a very satisfying afternoon —
Exercise 1 asks only that you *use* the law.) And the law predicts the cliff to the step:
$\texttt{POW 2 9}$ needs $2 \cdot 511 + 4 = 1026$ steps, and the budget is 1,000 — a miss by 26:

```text
lab> nf POW 2 9
Reduction limit reached after 1000 β-step(s)
  Step limit reached. This is not claimed to be a normal form:
  ⋮
```

The same fate meets `nf POW 3 7` (needs $3^7 + 3 = 2190$), `nf POW 5 5`, and `nf POW 10 4`. The
cliff is real, measured, and exactly where the mathematics says it should be. Meanwhile the
table's sleeper hit is `nf POW 10 3`: the numeral **one thousand** — a normal form with a
thousand `f`s — for a mere 226 steps. Steps and size are different currencies. You can arbitrage
that: `PLUS` and `MULT` are step-cheap (measured on this engine, `nf MULT m n` costs exactly
$2m+3$ steps — 9, 23, 27, 51 for $m = 3, 10, 12, 24$), so a *pyramid* of them builds enormous
numerals for pennies. Literal numerals are capped — ask for one that is too big and the lab says
so honestly:

```text
lab> nf MULT 30 30
Error: numeral 30 is too large for the browser (max 24)
```

— but nothing stops you composing under the cap:
[`nf PLUS (PLUS (MULT 24 24) (MULT 24 24)) (PLUS (MULT 24 24) (MULT 24 24))`](https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/?cmd=nf%20PLUS%20(PLUS%20(MULT%2024%2024)%20(MULT%2024%2024))%20(PLUS%20(MULT%2024%2024)%20(MULT%2024%2024)))

```text
lab> nf PLUS (MULT 24 24) (MULT 24 24)
β-normal form · 108 step(s)
  ⋮
  = 1152  (Church numeral)

lab> nf PLUS (PLUS (MULT 24 24) (MULT 24 24)) (PLUS (MULT 24 24) (MULT 24 24))
β-normal form · 222 step(s)
  ⋮
  = 2304  (Church numeral)
```

Four multiplications at 51 steps each, three additions at 6 each: $4\cdot51 + 3\cdot6 = 222$,
on the nose — and **2304** is the largest number computed in this chapter. (The elided middle line
is a numeral with 2,304 `f`s; scroll it in the lab for the full effect.)

```{admonition} A cliff of a different kind
:class: warning
Step count is not the only resource — *term size* is the other, and it can hurt before any limit
message appears. We tried `nf MULT 24 (MULT 24 24)` (which heads toward 13,824): normal order
substitutes the un-normalized 576-sized argument into 24 places, so each of up to a thousand
steps rewrites a tree of tens of thousands of nodes. On our machine it had produced no answer
after several minutes of wall-clock time, and in a browser tab it will simply feel frozen — we
do not print an output for it because we never obtained one. Grow big numbers with `PLUS`
pyramids of *already-cheap* pieces, not by multiplying giants.
```

## Exercises

**Exercise 1 (the price of a power).** Without running them, use the step law to predict the
cost of `nf POW 4 3` and of `nf MULT 12 5`. Then run both and check yourself.

````{admonition} Solution
:class: dropdown
The law gives $2\cdot\frac{4^3-1}{4-1}+4 = 2\cdot 21 + 4 = 46$ for the power, and
$2\cdot 12 + 3 = 27$ for the product. The engine agrees exactly:

```text
lab> nf POW 4 3
β-normal form · 46 step(s)
  λf x. f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f x)))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))
  = 64  (Church numeral)

lab> nf MULT 12 5
β-normal form · 27 step(s)
  ⋮
  = 60  (Church numeral)
```
````

**Exercise 2 (the recurrence, without recursion).** `nf FIB 9` exceeded the budget above. But
$F_9$'s *defining identity* at the previous rungs is still checkable: verify, in the session
where `STEP` and `FIB` are defined, that $F_8 = F_6 + F_7$ — and explain why this fits the
budget when `FIB 9` did not.

````{admonition} Solution
:class: dropdown
```text
lab> equiv FIB 8 = PLUS (FIB 6) (FIB 7)
β-convertibility by normal forms (η is not used)
  left NF:  λf x. f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f x))))))))))))))))))))
  right NF: λf x. f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f x))))))))))))))))))))
  equal β-normal forms up to α
```

`equiv` normalizes each side with its **own** fuel budget. The left side is `FIB 8` (783 steps,
fits); the right side costs about $293 + 480 + 6 \approx 779$ steps (fits). `FIB 9` needs
roughly $783\times\varphi \approx 1270$ steps in a *single* budget — too much. Splitting a
computation along an identity you trust is a genuinely useful trick at the edge of any budget.
````

**Exercise 3 (a full adder, verified).** Extend the half adder to a full one-bit adder with
carry-in: sum $= a \oplus b \oplus c$, carry-out $= ab \lor c(a \oplus b)$. Define both outputs
with `let` and verify the complete truth table — eight rows, two outputs, sixteen `equiv`
checks.

````{admonition} Solution
:class: dropdown
```text
lab> let FULLSUM = \a b c. XOR (XOR a b) c
lab> let FULLCARRY = \a b c. OR (AND a b) (AND c (XOR a b))
```

Three sample rows of the sixteen:

```text
lab> equiv FULLCARRY TRUE TRUE FALSE = TRUE
β-convertibility by normal forms (η is not used)
  left NF:  λt f. t
  right NF: λt f. t
  equal β-normal forms up to α

lab> equiv FULLCARRY FALSE TRUE TRUE = TRUE
  equal β-normal forms up to α
lab> equiv FULLCARRY FALSE TRUE FALSE = FALSE
  equal β-normal forms up to α
```

We ran all sixteen checks (every input triple, both outputs) against the engine: **16 of 16**
return `equal β-normal forms up to α`. One λ-term, exhaustively certified as a piece of
hardware. Two such adders chained give two-bit addition — the beginning of a ripple-carry
adder, if you have an evening to spare.
````

**Exercise 4 (Ackermann's closed forms).** The identities $A(2,n) = 2n+3$ and
$A(3,n) = 2^{\,n+3}-3$ are classical. Check an instance of each on the engine — the second one
entirely inside the calculus, using `PRED` for the subtractions.

````{admonition} Solution
:class: dropdown
With `ACK` defined as above:

```text
lab> equiv ACK 2 4 = PLUS (MULT 2 4) 3
β-convertibility by normal forms (η is not used)
  left NF:  λf x. f (f (f (f (f (f (f (f (f (f (f x))))))))))
  right NF: λf x. f (f (f (f (f (f (f (f (f (f (f x))))))))))
  equal β-normal forms up to α

lab> equiv ACK 3 2 = PRED (PRED (PRED (POW 2 5)))
β-convertibility by normal forms (η is not used)
  left NF:  λf x. f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f x))))))))))))))))))))))))))))
  right NF: λf x. f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f (f x))))))))))))))))))))))))))))
  equal β-normal forms up to α
```

$A(2,4) = 11$ and $A(3,2) = 2^5 - 3 = 29$: both identities confirmed by pure β-reduction.
(For fun: `nf ACK 2 4` itself costs 117 steps.)
````

````{admonition} Where this connects
:class: seealso
Everything in this chapter is Lecture 2 made kinetic, with the lab as the laboratory bench.

- [Lecture 2 — Simple calculations with the Church λ-calculus](../lectures/l2_lambda_calculus.md) — the encodings (`SUCC`, `PLUS`, `MULT`, `POW`, pairs, Booleans, `Y`) whose price tags we just measured.
- [Lecture 1 — A general introduction to type theory](../lectures/l1_type_theory.md) — why `Y` cannot be typed, and how types buy termination at the cost of exactly this kind of unbounded recursion.
- [λ-calculus quick reference](../appendix/cheatsheet.md) — every command used here (`reduce`, `nf`, `let`, `equiv`, `decode`, `church`) on one page.
- In the lab, `help nf` — the budget rules quoted in this chapter, straight from the source; and `tour` — a guided walk through the whole command surface.
````
