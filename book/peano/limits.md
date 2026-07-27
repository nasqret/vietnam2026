# Limits: what checking can—and cannot—tell us

Peano Lab is sound by construction in a precise engineering sense: an untrusted tactic cannot finish
a proof merely by declaring success.  It must supply a certificate, and QED sends that certificate and
the **original** goal to a small independent checker.  This is a strong promise, but it is easy to turn
it into three promises the lab does not make:

1. that every true arithmetic sentence will eventually be proved;
2. that unsuccessful automation has found a counterexample or established unprovability;
3. that checking a derivation proves the checker, the axioms, or their intended interpretation sound.

Keeping those boundaries visible is part of the project, not a disclaimer added after the interesting
work.  The implemented overview is available as the live
[`Gödel and limits`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=kb%20godel-limits)
knowledge-base card, backed by
[`ui/data_kb.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/ui/data_kb.py).

## A proof checker is not an oracle for truth

For a fixed finite certificate $p$ and formula $A$, kernel checking is a terminating structural
computation:

$$
  \operatorname{check}(\Gamma,p,A)\in\{\mathsf{true},\mathsf{false}\}.
$$

It answers whether this syntax tree is a valid derivation of $A$ from context $\Gamma$ according to
the encoded natural-deduction, equality, PA1–PA6, and induction rules.  That is not the same question
as whether $A$ is true in the standard natural numbers, whether some other certificate exists, or
whether the rules are consistent.

The distinction is the De Bruijn criterion in action.  We reduce trust to a program small enough to
inspect; we do not eliminate trust.  A defect in the checker or an inconsistent axiom set could still
certify nonsense.  Conversely, rejection of one malformed certificate says nothing about whether the
same theorem has a valid proof.  Soundness here is a disciplined boundary between search and checking,
not a machine-checked metatheorem about the Python runtime.

## Gödel–Rosser: incompleteness is structural

The first incompleteness phenomenon applies to any consistent, effectively axiomatized theory strong
enough to formalize ordinary arithmetic, including PA and HA.  There is an arithmetic sentence $G$
such that the theory proves neither $G$ nor $\neg G$.  Rosser's refinement obtains this conclusion from
ordinary consistency; the older presentation of Gödel's first theorem used a stronger consistency
condition.

This is not a limitation of Peano Lab's depth bound, Python implementation, tactic vocabulary, or user
interface.  Replacing `auto` with perfect engineering cannot make a consistent effective arithmetic
theory prove every arithmetic truth.  Adding one independent sentence as a new axiom does not end the
story either: if the strengthened effective theory remains consistent and arithmetically strong, an
incompleteness result applies again.

Under the usual representability and derivability conditions, the second incompleteness theorem says
that such a consistent theory cannot prove its own suitably encoded consistency statement
$\operatorname{Con}(T)$.  It does **not** say that PA is inconsistent, that individual independent
statements can never be settled by stronger principles, or that mathematical reasoning is futile.  It
says there is no final, consistent, effective proof system of this strength that internally certifies
all arithmetic truth and its own consistency.

Peano Lab therefore makes a modest claim: accepted certificates are derivations from the rules that
the checker implements.  It neither identifies derivability with standard-model truth nor uses a green
test suite as a proof of PA's consistency.

## Three kinds of computation, three kinds of result

The automation layer deliberately separates evaluation, finite observation, and proof production in
[`engine/decide.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/engine/decide.py).

First, a closed term can simply be evaluated.  This browser command computes in Python and reports a
number:

```text
pa> pa eval 2 * (3 + 1)
```

Second, `decide_closed_equation` computes both sides of a closed equation.  Its verdict is explicitly
not a proof term.  When proof evidence is requested, the separate `prove_closed_equation` routine
normalizes the two terms using congruence and instantiated PA3–PA6 certificates, then asks the kernel
to check the result.  Computation may suggest the theorem; only constructed evidence can close it.

Third, `bounded_check(A, N)` interprets every quantifier in $A$ over the finite set
$\{0,1,\ldots,N\}$.  Its label includes the bound and the word “bounded.”  If $A$ contains any
quantifier, the result remains marked incomplete even when the sample finds a witness or a
counterexample.  For example, failing to find a witness for $\exists x.\,P(x)$ below $N$ does not show
that none exists above $N$; observing $P(0),\ldots,P(N)$ does not prove $\forall x.\,P(x)$.  The bounded
API never manufactures a certificate from that finite observation.

Proof search in
[`engine/search.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/engine/search.py)
has the same honesty rule.  `auto d` explores a bounded deterministic tree.  A `found` result is replayed
as ordinary tactics and independently checked; `none` and `limit` mean only that this search did not
find a plan.  Here is a successful run:

```text
pa> pa prove forall n. 0 + n = n
pa> auto 5
pa> qed
```

The tactic's executable card is at
[`pa tactic auto`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20tactic%20auto).
No negative search status is a proof of falsity or unprovability.

## Normalization is not a decision procedure for PA

The proof-producing arithmetic tactics have the same honest stopping rule. `norm_num` calculates
only closed numerical islands in an equality, optionally beneath leading universal binders. Every accepted value is accompanied by a
PA3--PA6 certificate, and a false closed equality is rejected transactionally. `ring` handles
unconditional polynomial identities by constructing a certificate from the checked
commutative-semiring basis. Equal computed normal forms choose those proofs; the normal forms are
not themselves kernel evidence.

Neither tactic decides quantified arithmetic, mines local hypotheses for nonlinear consequences, or
turns resource exhaustion into a mathematical result. Peano Lab does not contain a hidden `omega`
tactic: a certificate-producing Presburger procedure belongs to a later design, and would still
decide only that fragment. {doc}`Checked arithmetic automation <arithmetic-automation>` compares the
exact `simp`, `norm_num`, `ring`, and `auto` contracts and records their browser limits.

## Loading the runtime is not theorem proving

Peano Lab is a static site. Opening it does not start a Python proof service on the faculty server;
the browser downloads Pyodide, creates a disposable Web Worker, and runs both the tactic engine and
kernel locally. This distinction explains an initially surprising observation: the prover source is
small, but a cold browser still needs an 8.6 MB WebAssembly runtime and a 2.4 MB Python standard
library before the prompt can appear.

M14 treats that delivery path as an explicit engineering boundary. The HTML page is never stored,
so it always discovers the current build. Pinned vendor bytes live below a URL containing a digest
of the canonical source manifest; worker and application bytes live below a separate path derived
from their own manifest. Those content-versioned responses may therefore be cached for a year
without making an upgrade stale. Apache compresses
WASM and source-like media with Brotli or gzip, but does not waste time recompressing ZIP and WOFF2.
The worker starts every small Python-source transfer together while Pyodide initializes, then checks
all results and mounts them in the original declared order.

Concurrency here is not concurrency in the logic. It changes arrival time only: source bytes are
validated by HTTP status, mounted deterministically, and imported exactly as before. A source
failure mounts nothing and reports the earliest file in declaration order, independent of which
network request happened to finish first. Once ready, QED still submits the complete certificate and
the original theorem to the same independent checker. Compression, caching, and parallel transfer
add no axiom and no trusted proof-producing component.

A **cold start** pays for network transfer plus WebAssembly/Python initialization. A **warm start**
reuses the immutable bytes but must still instantiate a fresh worker; Stop deliberately terminates
that worker so an unresponsive proof cannot survive. This is why transport timing, tactic timing,
and kernel-checking time should be measured and reported separately.

## HA first; classicality must leave a trace

Peano Lab's default is Heyting arithmetic: the arithmetic axioms and induction schema interpreted in
intuitionistic first-order logic.  Its introduction and elimination rules retain the constructive BHK
reading.  Conventional PA uses classical logic, so the lab offers one explicit extension,

$$
  \neg\neg A\to A,
$$

as a `DNE(A)` proof node.  `classical on` authorizes that node; `classical off` is the default.  The
authority is held by the session owner outside the untrusted `ProofState`, and finalization calls the
matching checker mode.  Switching the mode off before QED makes a certificate containing DNE fail.

This replay is a compact specimen of the boundary:

```text
pa> pa prove ((0 = S 0 -> false) -> false) -> 0 = S 0
pa> intro h
pa> classical on
pa> apply DNE
pa> exact h
pa> qed
```

The example deliberately builds a DNE certificate; it is not a claim that this particular decidable
equality instance is independent of HA.  Its point is inspectability: the intuitionistic checker
rejects that proof node, while the explicitly classical checker accepts it.  The arithmetic meanings
of $0$, $S$, $+$, and $\cdot$ do not change with the toggle.

The logical comparison also needs one careful qualification.  For a closed $\Pi_1$ sentence whose
matrix HA proves decidable, negative-translation results give the direction

$$
  \mathrm{PA}\vdash A \quad\Longrightarrow\quad \mathrm{HA}\vdash A.
$$

That useful conservation phenomenon is not a blanket equivalence between HA and PA, and it is not a
procedure implemented by Peano Lab.  See the live
[`HA versus classical PA`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=kb%20heyting-vs-classical-pa)
card for the same boundary in terminal form.

## What Lean has that this little lab does not

Peano Lab and Lean share a crucial architectural idea: tactics elaborate human commands into proof
objects that a smaller kernel checks.  Both use nameless bound-variable machinery internally, and both
can keep sophisticated search outside the trusted core.  The similarity is deliberately narrow.

Lean is a dependently typed programming language and prover.  It has universes; inductive types and
families; dependent functions; definitional reduction; recursive definitions guarded by termination;
an elaborator with implicit arguments and coercions; a persistent declaration environment; typeclass
resolution; macros and metaprogramming; compiled programs; and the enormous reusable Mathlib library.
Its `Nat` is an inductive datatype whose recursor and defining equations participate in a much richer
type theory.

Peano Lab has one implicit sort of natural numbers and one fixed signature: $0$, $S$, $+$, $\cdot$,
and equality.  Its $\le$ is parser sugar for an existential formula.  It has no dependent types,
universes, general definitions, definitional-equality engine, elaborator, coercions, typeclasses, proof
irrelevance machinery, module system, or kernel theorem environment.  Library reuse is compiled away
by untrusted proof-term substitution and checked again from the empty context.  These absences are
listed explicitly in
[`design §8`](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/PEANO_LAB_DESIGN.md#8-what-we-are-explicitly-not-building).

The narrowness is the teaching instrument.  A student can follow PA4 from parser, through `simp` or
`norm_num`, into an equality-transport certificate, and finally through a checker that fits in one
sitting.  Lean's scale makes serious formal mathematics possible; Peano Lab's scale makes the
soundness boundary visible.

The bridge is intentionally one-way and non-authoritative.  [`pa lean mul_eq_zero`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20lean%20mul_eq_zero)
translates the exact Peano formula to a Lean theorem over `Nat`, comments the source tactic script, and
leaves one visible `sorry` stub.  The exporter in
[`library/lean.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/library/lean.py)
is a cross-checking convenience.  Lean does not certify Peano Lab's QED, and Peano Lab does not pretend
to be Lean.  Each system's own kernel remains the judge of its own proof object.
