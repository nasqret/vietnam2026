# Why Peano arithmetic?

Peano Lab is deliberately much smaller than Lean.  It has one sort of object—natural numbers—and
only four pieces of arithmetic notation: $0$, successor $S$, addition, and multiplication.  That
small language is not a limitation to apologize for.  It is what lets us put the entire route from
a command such as `induction n` to a checked proof certificate on the page.

Arithmetic is a particularly good laboratory for a prover because it becomes interesting at exactly
the right pace.  Equations force us to implement equality and rewriting.  The recursive definitions
of addition and multiplication force us to distinguish computation from proof.  Induction introduces
a rule schema and hypotheses whose scope matters.  Quantifiers add substitution and eigenvariables;
conjunction, disjunction, implication, and falsity add the familiar structure of natural deduction.
By the time we reach a theorem such as

$$
  \forall n\,m.\; n\cdot m=0 \to n=0 \lor m=0,
$$

the language is still tiny, but nearly every architectural problem in a serious interactive prover
has appeared in a form that we can inspect.

The live lab prints the six fixed arithmetic axiom constants, followed by the induction schema:
[`pa axioms`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20axioms).
The corresponding frozen formulas live in the small
[`axiom_formula`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/kernel/checker.py)
function rather than in a large, hidden arithmetic library.

## One language, built in stages

Trying to implement all of first-order arithmetic in one pass would mix four different sources of
difficulty.  If a proof failed, we would not know whether the culprit was equality transport,
capture-avoiding substitution, induction, or a connective rule.  Peano Lab therefore grows the
logic in stages.  Each stage is chosen to force one new *kind* of prover machinery.

| Stage | Formulas available | What the prover must learn |
|---|---|---|
| A | Quantifier-free equations | reflexivity, congruence, symmetry, transitivity, rewriting |
| B | Equations plus structural induction | motives, base and step goals, induction hypotheses |
| C | $\forall,\exists,\to,\land,\lor,\bot$ | binders, witnesses, cases, natural-deduction contexts |
| D | The same logic, with automation | tacticals, ordered simplification, bounded search |

Stage D is worth reading carefully: automation does not add a new mathematical inference rule.
`simp`, `auto`, and tactical combinators are programs that assemble certificates from the earlier
rules.  If one of those programs is buggy, the certificate checker must reject its output.  That
separation is the central soundness idea of the project.

The object language itself is compact.  Terms and formulas follow these grammars:

$$
\begin{aligned}
t &::= x \mid 0 \mid S\,t \mid t+t \mid t\cdot t,\\
\varphi &::= t=t \mid \bot \mid \varphi\to\varphi
          \mid \varphi\land\varphi \mid \varphi\lor\varphi
          \mid \forall x.\varphi \mid \exists x.\varphi.
\end{aligned}
$$

Decimal numerals are only input sugar: `3` expands to $S(S(S(0)))$.  Negation is also sugar,
$\neg A := A\to\bot$.  Finally, the displayed order relation is a definition rather than a trusted
predicate:

$$
  n\le m \quad:=\quad \exists k.\;k+n=m.
$$

The parser expands all three forms before the kernel sees them.  This keeps the trusted syntax
honest: there is no numeral evaluator, negation oracle, or hidden order rule.  The
[`terms.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/kernel/terms.py)
and
[`formulas.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/kernel/formulas.py)
modules also choose one deterministic Unicode spelling on output, so a goal has one stable textual
identity in the terminal and in proof traces.

## Recursive equations are directional

The six arithmetic constants divide into three pairs.  PA1 says that no successor is zero; PA2 says
that successor is injective.  PA3 and PA4 define addition by recursion on its **right** argument:

$$
  x+0=x, \qquad x+S(y)=S(x+y).
$$

PA5 and PA6 do the same for multiplication:

$$
  x\cdot0=0, \qquad x\cdot S(y)=x\cdot y+x.
$$

The direction is pedagogically useful.  The equation $n+0=n$ is an instance of PA3.  The mirror
image $0+n=n$ is not: the variable occurs in the recursive position, so its proof needs induction.
The difference is visible in a complete live proof:

```text
pa> pa prove forall n. 0 + n = n
pa> induction n
pa> simp
pa> simp [IH]
pa> qed
```

After `induction n`, the engine creates a base obligation for $0+0=0$ and a successor obligation
with an induction hypothesis.  `simp` uses PA3 in the base and PA4 in the step; `simp [IH]` supplies
the one fact that computation alone cannot invent.  The final `qed` does not merely notice that no
goals remain.  It checks the generated induction certificate against the original universal
formula.

This modest example explains why PA is more revealing than a calculator.  Evaluating `2 + 3` tells
us one closed fact.  Induction proves a uniform statement about every natural number.  Conversely,
a bounded computation that finds no counterexample is not an induction proof and is never promoted
to one.  Peano Lab keeps those activities separately labeled.

## Induction is a schema, not a magic loop

For each formula $\varphi(n,\bar a)$, possibly containing additional parameters $\bar a$, induction
admits the instance

$$
\frac{\varphi(0,\bar a) \qquad
      \forall n.\;\varphi(n,\bar a)\to\varphi(Sn,\bar a)}
     {\forall n.\;\varphi(n,\bar a)}.
$$

First-order arithmetic cannot quantify over formulas, so the symbol $\varphi$ above is metalanguage.
There is one effective rule instance for every formula: an infinite **schema**, not one additional
first-order sentence.  The kernel certificate `Ind(motive, base, step)` stores the particular
motive, and the checker reconstructs all three displayed formulas before accepting the node.  The
live [induction card](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20tactic%20induction)
shows the tactic effect and the certificate effect side by side.

This distinction also disciplines tactic design.  `induction n` does not ask Python to test several
values of `n`, nor does it add `IH` as a global axiom.  It creates exactly the holes required by an
`Ind` certificate.  The induction hypothesis exists only in the step branch.  If a tactic leaks it
into the base case, the independent checker rejects the finished tree.

## Logic after arithmetic, automation after logic

Once induction works, Stage C adds the ordinary constructive meanings of the connectives.  To prove
$A\to B$, assume a certificate for $A$ and construct one for $B$.  To prove $A\land B$, construct
both parts.  To prove $\exists x.\varphi(x)$, provide a concrete witness and a proof of its instance.
Universal introduction and existential elimination are where variable capture becomes a genuine
soundness issue, so they arrive only after substitution has already been isolated and tested.

The default core is intuitionistic arithmetic—Heyting arithmetic in logical character—because its
proof terms have a direct constructive reading.  Conventional classical PA is an explicitly labeled
extension.  `classical on` authorizes a visible double-negation-elimination certificate
$\neg\neg A\to A$; it does not change the meanings of $0$, $S$, $+$, or $\cdot$.  Constructive
certificates remain valid in classical mode, while a certificate containing that classical node is
rejected when the mode is off.  The distinction is summarized in the executable
[HA versus PA card](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20kb%20heyting-vs-classical-pa).

Only after these rules are explicit does Stage D introduce a tactic *language*.  Sequencing,
alternatives, repetition, and goal focus combine existing tactics; `simp` chooses terminating
rewrite directions; `auto` performs bounded backtracking.  None is a theorem oracle.  Their value is
that they expose proof construction at a more useful scale while leaving the mathematical authority
in the same small kernel.

That is why PA is the right-sized subject for this lab.  It is elementary enough that every trusted
rule fits in one chapter, yet expressive enough to teach binders, induction, automation, classical
boundaries, and eventually incompleteness.  We can climb from $0+n=n$ to order and zero products
without changing what counts as proof—only how efficiently we learn to build one.
