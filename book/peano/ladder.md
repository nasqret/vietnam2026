# The checked theorem ladder

Peano Lab's library is not a bag of trusted facts.  Each entry contains a closed PA statement,
an ordered list of earlier rungs, and the exact tactic script used to rebuild it.  CI
replays all current entries, discharges dependency assumptions through embedded self-contained
Cuts, and asks the independent kernel to check the resulting closed certificate against the
original statement.

The current local candidate runtime contains 149 unique checked entries: the
original 23-entry base, 114 post-baseline foundational entries, and twelve
further unique records from the upstream modular catalog. The upstream
26-record catalog ends at the fourth-power modulo-five capstone. Its first
reconciliation with the 51-entry M20 branch exposed fourteen coincident
post-core records once and produced the historical 63-entry snapshot.
Subsequent foundational passes add discrete order and cancellation, generic
quotient-and-remainder existence and uniqueness, relational gcd, balanced
Bézout, Gauss cancellation, `prime_divisor_eq_one_or_self`, and
`euclid_prime_dvd_product`. They retain `prime_two`, the first checked fully
expanded prime instance. The latest twelve-rung native milestone adds
`eq_decidable`, constructive divisibility decisions, bounded factor-pair
search, `prime_or_composite`, `prime_decidable`, proper-factor descent, and
bounded plus general prime-divisor existence. None of those certificates uses
DNE. Across the snapshot, 67,844 structural nodes include 1,800 self-contained
Cuts; 109 certificates contain a Cut. `euclid_prime_dvd_product` remains the
largest certificate at 5,382 nodes and also sets the per-certificate Cut
maximum at 159, while `prime_divisor_exists` sets the depth maximum at 80. The
complete layered design continues
in {doc}`The foundational arithmetic library <../arithmetic-library/index>`;
this chapter retains the construction story of the original core and the public modular route.

Open the currently deployed index or the core zero-product card:

- [`pa lib`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib)
- [`pa lib mul_eq_zero`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lib%20mul_eq_zero)
- [`pa lean add_comm`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lean%20add_comm)

Local candidate build `2026-07-29a`, immutable application release
`a-d0758315633d`, also exposes `pa lib mod5_fourth_power_one`. Its production deep link
will be added only after the candidate is actually deployed; documentation does not pretend that a
local theorem is already live.

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

That is the capstone of the original 23-entry core. In the upstream public-catalog snapshot, a
26-entry extension continues
through multiples, residue algebra, the completeness of residues modulo five, square residues,
and fourth-power residues. The 49th entry is

$$
\forall n.\;\neg(\exists q.\;n=5q)\to
\exists q.\;n^4=5q+1.
$$

It is not a new axiom or an opaque solver result. Its source script replays through the same public
tactic surface. The immutable upstream report records the former fully expanded certificate at
21,515 nodes/depth 66. Current replay packages dependencies with self-contained sharing and yields
2,675 structural nodes/depth 38; the independent kernel checks the complete certificate in the
empty context. The source revision, catalog hash, license notice, and unaltered pre-integration
validation report are retained under `artifacts/peano-library/`.

Once imported, the long derivation can be reused in an ordinary short proof:

```text
pa prove forall n. ~(exists x. n = 5 * x) -> exists x. n * n * n * n = 5 * x + 1
intro n
intro h
use mod5_fourth_power_one
apply mod5_fourth_power_one
exact h
qed
```

The open proof reaches 2,682 structural nodes at depth 41, and finalization checks a
2,670-node/depth-41 certificate. The import ceiling remains 32,768 nodes; repeated capstone imports
eventually reach the separate live-partial bound and fail transactionally without changing state.

Five named helper lemmas keep the scripts readable.  They are not shortcuts around checking: each
helper is itself an ordinary scripted theorem with a closed certificate.  For example,
`mul_succ_left` makes the multiplication-commutativity proof six commands long, while
`antisymm_from_witnesses` exposes the real additive argument behind order antisymmetry.

## Self-contained theorem sharing

The kernel deliberately has no mutable theorem environment or trusted theorem-name rule.
Library replay therefore proves a temporary curried statement

$$
D_1 \to D_2 \to \cdots \to D_r \to T,
$$

where each $D_i$ is an earlier checked theorem. The library layer peels those introductions and
wraps the remaining body in nested nodes

```text
Cut(A, B, lemma, body).
```

The kernel checks `lemma : A` in the ambient context and `body : B` with `A` as its newest
hypothesis. The node contains both formulas and both proofs—never a theorem name, hash, or external
lookup. This is a reviewed enlargement of the certificate grammar and checker, while the arithmetic
term/formula language, PA axioms, induction, and intuitionistic default remain unchanged.

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

The partial certificate visibly contains self-contained Cuts while the proof is open. At QED,
Peano Lab removes only engine-administrative local schedulers and then invokes the independent
checker with the original target. This gives the convenience of a theorem environment without
adding a trusted `Theorem(name)` constructor or external declaration table. `undo` restores
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

## From a replay file to a library entry

The browser command `script download` is a useful handoff from an exploratory proof, but it does
not modify this ladder. Its file is a full live surface program beginning with `pa prove`; the
library stores a narrower reviewed record:

```python
TheoremSpec(
    name="my_theorem",
    statement="forall n. ...",
    dependencies=("earlier_fact",),
    script=("intro n", "..."),
    summary="...",
)
```

The statement must be closed, so visible free variables have to be bound explicitly. Every
dependency must name an earlier checked entry. The replay layer generates those dependency
introductions itself, so a live `use earlier_fact` line becomes the `dependencies` entry and is not
copied into the authored body. The current library runner accepts its deliberately small primitive
script language; a downloaded proof containing tacticals, top-level `auto`, `ring`, `use`, or
classical-mode changes must be reviewed and lowered rather than pasted blindly.

Admission then replays the dependency-curried goal, packages the earlier closed certificates in
self-contained Cuts, and asks the independent kernel to check the resulting closed certificate
against the original statement. Tests, a source commit, and deployment are part of the change.
Thus a replay file can preserve the discovery without becoming either trusted evidence or a mutable
theorem environment.

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
