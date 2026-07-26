# The checked theorem ladder

Peano Lab's library is not a bag of trusted facts.  Each entry contains a closed PA statement,
an ordered list of earlier rungs, and the exact tactic script used to rebuild it.  CI
replays all twenty entries, removes dependency assumptions from their proof terms, and asks the
independent kernel to check the resulting closed certificate against the original statement.

Open the live index or the capstone card:

- [`pa lib`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib)
- [`pa lib mul_eq_zero`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20mul_eq_zero)
- [`pa lean add_comm`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lean%20add_comm)

## The route

The binding rungs are

$$
\begin{aligned}
0+n=n
&\Longrightarrow \operatorname{add\_succ\_left}
\Longrightarrow \operatorname{add\_comm}
\Longrightarrow \operatorname{add\_assoc} \\
&\Longrightarrow 0\cdot n=0
\Longrightarrow \operatorname{mul\_comm}
\Longrightarrow \operatorname{mul\_add}
\Longrightarrow \operatorname{mul\_assoc},
\end{aligned}
$$

followed by the successor lemmas, the witness definition

$$
n \le m \;:\!\!\Longleftrightarrow\; \exists k.\;k+n=m,
$$

reflexivity, transitivity, antisymmetry, totality, and finally

$$
\forall n\,m.\;n\cdot m=0 \to n=0\lor m=0.
$$

Five named helper lemmas keep the scripts readable.  They are not shortcuts around checking: each
helper is itself an ordinary scripted theorem with a closed certificate.  For example,
`mul_succ_left` makes the multiplication-commutativity proof six commands long, while
`antisymm_from_witnesses` exposes the real additive argument behind order antisymmetry.

## Compiling theorem reuse away

The kernel deliberately has neither a mutable theorem environment nor a proof-ascription rule.
Library replay therefore proves a temporary curried statement

$$
D_1 \to D_2 \to \cdots \to D_r \to T,
$$

where each $D_i$ is an earlier checked theorem.  The library layer then performs simultaneous,
capture-avoiding substitution of the closed certificates for those hypothesis slots.  It contracts
the implication and universal introduction/elimination redexes exposed by substitution.  This is
ordinary cut elimination in an **untrusted** layer: even if that transformation is buggy, its output
still has to pass `check((), certificate, T)`.

That final call is the important line.  The tactic script, dependency graph, substitution code,
pretty-printer, browser card, and Lean exporter may all be wrong without turning a false formula
into a theorem.

## A script you can inspect

The capstone card shows this authored body after its generated dependency introduction:

```text
intro n
induction m
intro h
right
refl
intro h
left
specialize add_eq_zero_right (n * m)
specialize add_eq_zero_right n
apply add_eq_zero_right
rewrite PA6 at h
exact h
```

In the zero case, the right factor is zero.  In the successor case, PA6 changes the hypothesis to
$n\cdot m+n=0$; the checked helper `add_eq_zero_right` extracts $n=0$.  The disjunction is therefore
proved constructively—classical mode is not involved.

`pa lean <name>` translates the exact closed formula to a theorem over Lean's `Nat`, comments the
Peano Lab script beside it, and leaves one explicit `sorry` proof stub.  The accompanying Live Lean
URL encodes exactly the displayed program.  This is a cross-checking invitation, never an alternate
authority for Peano Lab's QED.
