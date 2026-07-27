# The checked theorem ladder

Peano Lab's library is not a bag of trusted facts.  Each entry contains a closed PA statement,
an ordered list of earlier rungs, and the exact tactic script used to rebuild it.  CI
replays all current entries, removes dependency assumptions from their proof terms, and asks the
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
\Longrightarrow \operatorname{mul\_assoc}
\Longrightarrow \{\operatorname{one\_mul},\operatorname{mul\_one},\operatorname{add\_mul}\},
\end{aligned}
$$

The final three are the M11 extension. They complete the oriented commutative-semiring basis needed
by proof-producing polynomial normalization; numerals need no extra axiom or theorem scheme because
they are successor terms and closed coefficient arithmetic already produces PA3–PA6 certificates.

After them come the successor lemmas and the witness definition

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

## Reusing a checked theorem live

The same compilation idea is available in an interactive proof.  `use` adds a checked library
formula to the focused context under its canonical name or a fresh alias:

```text
pa> pa prove forall a b. S a + b = S (b + a)
pa> use add_succ_left
pa> use add_comm
pa> intro a
pa> intro b
pa> simp [add_succ_left, add_comm]
pa> qed
```

The partial certificate visibly contains local cuts while the proof is open. At QED, Peano Lab
contracts the exposed implication and universal redexes in an untrusted pass and then invokes the
same independent checker with the original target. This gives the convenience of a theorem
environment without adding a trusted `Theorem(name)` constructor to the kernel. `undo` restores
the exact state before an import, and an unknown theorem or colliding alias changes nothing.
Explicit import and live-certificate node/depth budgets turn excessive reuse into a transactional
resource limit rather than a host recursion failure.

## From the checked basis to `ring`

M12's `ring` is a proof-producing normalizer, not a trusted arithmetic oracle. It reifies a focused
equality as two sparse polynomials, chooses one deterministic monomial order, and constructs every
normalization step from PA3--PA6 and the checked M11 basis. The generated equality certificate is
checked before the tactic closes the goal; QED later checks the complete induction certificate
against its original statement.

The odd-square theorem also illustrates what `ring` does **not** do. It never searches the context
for useful equations. The proof author supplies a middle expression, proves the first polynomial
identity, rewrites the second goal with the induction hypothesis, and proves the remaining identity:

```text
pa> pa prove forall n. exists x. (2 * n + 1) * (2 * n + 1) = 8 * x + 1
pa> induction n
pa> exists 0
pa> ring
pa> cases IH
pa> exists x + S n
pa> trans ((2 * n + 1) * (2 * n + 1)) + (8 * S n)
pa> ring
pa> rewrite IH_witness
pa> ring
pa> qed
```

The middle term is

$$
  (2n+1)^2+8(n+1).
$$

Thus the first `ring` in the step certifies
$(2(n+1)+1)^2=(2n+1)^2+8(n+1)$. After the explicit rewrite, the last one certifies
$(8x+1)+8(n+1)=8(x+n+1)+1$. Different normal forms are an ordinary transactional failure, not a
request for the tactic to infer a missing hypothesis. Explicit AST, polynomial, coefficient, work,
proof-size, and wall-clock limits keep the browser attempt finite.

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
