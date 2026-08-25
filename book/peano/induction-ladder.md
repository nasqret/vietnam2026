# Induction and the checked theorem ladder

Peano Lab begins with six arithmetic rule constants, but the interesting mathematics starts where
those equations stop.  PA3 says

$$
  \forall n.\;n+0=n,
$$

while the apparently symmetric equation $0+n=n$ is not an axiom.  The difference is intentional:
addition is specified by recursion on its **right** argument,

$$
  n+0=n, \qquad n+S(m)=S(n+m).
$$

The expression $0+n$ is stuck when $n$ is a variable.  We must reason about how $n$ is built.  This
small asymmetry is the first moment the lab stops behaving like a calculator and starts behaving like
a theorem prover.

The implementation is short enough to inspect: the tactic-side construction lives in
[`engine/induction.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/engine/induction.py),
while the trusted interpretation of its proof term is in
[`kernel/checker.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/kernel/checker.py).

## Induction is a schema, not a magic command

For each arithmetic formula $\varphi(n,\bar a)$, with any additional parameters $\bar a$, induction
permits the inference

$$
\frac{
  \varphi(0,\bar a)
  \qquad
  \forall n.\;\varphi(n,\bar a)\to\varphi(Sn,\bar a)
}{
  \forall n.\;\varphi(n,\bar a)
}.
$$

The first-order language cannot quantify over formulas.  There is therefore no object-language
variable called $\varphi$ and no single first-order sentence saying “induct over every property.”
Instead, every chosen motive supplies one instance of an infinite effective **schema**.  Peano Lab
makes that choice visible: an `Ind` certificate stores the motive formula, and the checker reconstructs
its zero and successor instances before accepting it.

Run the smallest useful example yourself:

```text
pa> pa prove forall n. 0 + n = n
pa> induction n
pa> simp
pa> simp [IH]
pa> qed
```

The first command creates the original closed goal.  `induction n` replaces its one hole by an `Ind`
node with two holes.  The base goal $0+0=0$ follows from PA3.  In the step, the context contains a
rigid $n$ and the induction hypothesis $IH:0+n=n$; PA4 changes $0+S(n)$ to $S(0+n)$, and congruence
transports the induction hypothesis beneath $S$.  `simp` is merely a convenient certificate builder.
The last line checks the completed `Ind` tree against the formula supplied on the first line.

This also explains why “induction on a variable” is not a textual substitution trick.  The tactic must
keep outer parameters at the right de Bruijn indices, shift hypotheses beneath the new term binder,
and construct the step as universal introduction followed by implication introduction.  A scoping bug
produces a certificate the checker rejects; it does not produce a theorem.

## The recursive side predicts the proof

The same right-argument choice explains the shape of the next rungs.  To prove commutativity,

$$
  \forall n\,m.\;n+m=m+n,
$$

the library inducts on $m$.  The left side then unfolds directly.  The base case becomes
$n=0+n$, so it needs the previously proved `zero_add`; PA3 only knows $n+0=n$.  In the step, PA4
turns $n+S(m)$ into $S(n+m)$, while the other side $S(m)+n$ is stuck for exactly the same reason
$0+n$ was stuck.  The separate `add_succ_left` lemma moves that successor through addition, and
the induction hypothesis identifies the terms underneath it.  See the exact four-command body at
[`pa lib add_comm`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20add_comm).

Multiplication repeats the lesson at a larger scale.  PA5 and PA6 define $n\cdot m$ by examining
$m$:

$$
  n\cdot0=0,
  \qquad
  n\cdot S(m)=n\cdot m+n.
$$

Thus $0\cdot n=0$ needs induction even though $n\cdot0=0$ is immediate.  Commutativity becomes
readable only after proving the mirror equation
$S(n)\cdot m=n\cdot m+m$.  Associativity and distributivity similarly choose the variable that
exposes PA6 and then use earlier addition facts to rearrange the resulting sums.  There is no general
normalizer secretly solving semiring algebra: the scripts record which recursive equation was opened
and which checked lemma repaired the inconvenient orientation.

This is a useful proof-planning heuristic beyond this lab.  Before trying tactics, ask which argument
the defining equations inspect.  Inducting on that argument tends to expose computation; inducting on
the other one tends to demand a mirror lemma first.

## Twenty core rungs, plus a checked semiring basis

The theorem library is an ordered regression suite.  Its complete data is in
[`library/theorems.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/library/theorems.py),
and [`tests/test_ladder.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/tests/test_ladder.py)
replays every entry.  The order is pedagogical rather than a claim that every row depends on the row
immediately above it:

| Rung | Statement or purpose | Earlier checked facts used |
|---|---|---|
| `zero_add` | $\forall n.\;0+n=n$ | none |
| `add_succ_left` | $S(n)+m=S(n+m)$ | none |
| `add_comm` | $n+m=m+n$ | `zero_add`, `add_succ_left` |
| `add_assoc` | $(n+m)+k=n+(m+k)$ | none |
| `mul_zero_left` | $0\cdot n=0$ | none |
| `mul_succ_left` | $S(n)\cdot m=n\cdot m+m$ | `add_comm`, `add_assoc` |
| `mul_comm` | $n\cdot m=m\cdot n$ | the two multiplication-side lemmas |
| `mul_add` | $n\cdot(m+k)=n\cdot m+n\cdot k$ | `add_assoc` |
| `mul_assoc` | $(n\cdot m)\cdot k=n\cdot(m\cdot k)$ | `mul_add` |
| `one_mul` | $1\cdot n=n$ | none |
| `mul_one` | $n\cdot1=n$ | `zero_add` |
| `add_mul` | $(n+m)\cdot k=n\cdot k+m\cdot k$ | `mul_comm`, `mul_add` |
| `succ_ne_zero` | $S(n)\ne0$ | PA1 |
| `succ_injective` | $S(n)=S(m)\to n=m$ | PA2 |
| `le_refl` | $n\le n$ | `zero_add` |
| `le_trans` | $n\le m\to m\le k\to n\le k$ | `add_assoc` |
| `no_succ_add_fixed` | $S(p)+n=n\to\bot$ | none |
| `drop_add_prefix_from_fixed` | remove $b$ from a fixed-sum equation | three earlier additive facts |
| `antisymm_from_witnesses` | opposing additive witnesses force equality | two earlier additive facts |
| `le_antisymm` | $n\le m\to m\le n\to n=m$ | the witness lemma |
| `le_total` | $n\le m\lor m\le n$ | none |
| `add_eq_zero_right` | $a+b=0\to b=0$ | none |
| `mul_eq_zero` | $n\cdot m=0\to n=0\lor m=0$ | `add_eq_zero_right` |

Here order is not primitive syntax in the kernel.  The surface parser expands

$$
  n\le m \quad:\!\Longleftrightarrow\quad \exists k.\;k+n=m.
$$

Consequently, `le_refl` supplies witness $0$; `le_trans` composes two witnesses by addition; and
antisymmetry must do real arithmetic to show that opposing witnesses cannot contain a positive
successor.  The five M7 helper rows name those genuine proof obligations rather than hiding them
inside opaque automation.

M11 appends exactly the three multiplication rows shown after `mul_assoc`. Together with PA3/PA5,
`zero_add`, `mul_zero_left`, and the existing associativity, commutativity, and distributivity
certificates, they form the complete oriented basis used by the later `ring` tactic. No separate
numeral lemma is needed: a numeral is an iterated successor of zero, and closed coefficient
arithmetic already builds PA3–PA6 proof terms.

Browse the executable index at [`pa lib`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib).
Each card displays the closed statement, earlier dependencies, generated prelude, authored tactic body,
certificate size, and the result of the independent check.

## Reuse without a trusted theorem oracle

A conventional prover keeps a persistent environment of checked declarations.  Peano Lab's binding
kernel intentionally has no theorem table and no proof-ascription constructor.  Giving the checker a
special “trust library theorem by name” case would make the library part of the trusted computing base.

Instead, suppose a new entry claims $T$ and uses already checked facts $D_1,\ldots,D_r$.  Replay first
proves the temporary goal

$$
  D_1\to D_2\to\cdots\to D_r\to T.
$$

The generated `intro` commands make dependencies ordinary local hypotheses, so all authored commands
go through the normal tactic engine.  After replay, the untrusted library layer simultaneously replaces
those hypothesis slots with the earlier closed certificates.  It shifts proposition and term indices to
avoid capture and contracts the universal- and implication-introduction/elimination redexes exposed by
substitution.  This is a small, explicit cut-elimination pass.

The key is what happens next:

$$
  \operatorname{check}((),\;p_T,\;T)=\mathsf{true}.
$$

The empty context matters.  No dependency assumption remains, and the target is the entry's original
statement—not the temporary curried formula.  If replay, substitution, normalization, or dependency
bookkeeping is wrong, the final check fails.  Library composition therefore increases convenience but
does not increase logical authority.

## Reading the capstone

Open [`pa lib mul_eq_zero`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20mul_eq_zero)
to see its exact script.  The proof inducts on $m$.  At zero, the right disjunct $m=0$ is reflexive;
the specialized premise is the PA5 equation, but this branch need not use it.  At a successor, PA6
rewrites the assumption as

$$
  n\cdot S(m)=0
  \quad\Longrightarrow\quad
  n\cdot m+n=0.
$$

The checked helper `add_eq_zero_right` extracts $n=0$, giving the left disjunct.  Its own proof is an
induction on the right addend: a successor sum rewrites to a successor, which PA1 says cannot equal
zero.  Notice that no excluded middle is needed.  The entire twenty-entry M7 core replays in the
intuitionistic checker.

Finally, [`pa lean mul_eq_zero`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lean%20mul_eq_zero)
shows a bounded, theorem-first view of the exact closed formula over Lean's
`Nat`; the Peano tactic script is labeled separately. Its independently
checkable Lean proof has no `sorry`: an explicit
`python3 scripts/export_peano_lean.py mul_eq_zero --format compact --package-dir /private/tmp/peano-lean-mul-eq-zero --verify`
command builds the readable theorem and its separately imported checked
certificate. Previewing alone neither replays nor verifies the proof. The
authority for the original Peano theorem remains the closed certificate that
its own small kernel accepted.
