# The kernel and the De Bruijn criterion

When Peano Lab prints `QED`, it is making a deliberately narrow claim: a small checker has validated
one explicit certificate, from the empty context, against the formula that began this proof session.
The claim does not depend on whether the tactic engine behaved sensibly on the way there.  Search may
choose a terrible route, `simp` may contain a bug, and the terminal may render an unhelpful panel.
None of those components is allowed to manufacture a theorem.

This is the project's first law:

$$
  \text{successful QED}
  \quad\Longrightarrow\quad
  \operatorname{check}((),\,p,\,A)=\mathsf{true},
$$

where $A$ is the **original** stated goal, retained by the proof-session owner, and $p$ is a complete
proof term.  The implementation of that final boundary is the short
[`checked_final`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/engine/tactics.py)
function.  The independent judgment it calls is in
[`kernel/checker.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/kernel/checker.py).

A tiny example traverses the whole boundary:

```text
pa> pa prove forall x. x = x
pa> intro x
pa> refl
pa> qed
```

`intro` and `refl` close engine goals, but only the last line licenses the theorem.  Even a state with
no visible goals can fail QED if it contains a hole, an unresolved metavariable, a malformed node, or
a certificate for some easier formula.

## Certificates are data, not authority

The kernel proof language has one inert constructor for each natural-deduction, equality, arithmetic,
or induction rule.  A few representative definitions from
[`proofs.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/kernel/proofs.py)
are almost boring:

```python
@dataclass(frozen=True, slots=True)
class ImpIntro(Proof):
    body: Proof

@dataclass(frozen=True, slots=True)
class ForallElim(Proof):
    p: Proof
    t: Term

@dataclass(frozen=True, slots=True)
class Ind(Proof):
    motive: Formula
    base: Proof
    step: Proof
```

Constructing `ImpIntro(...)` does not prove an implication, just as constructing a syntax tree for
`2 + 2 = 5` does not make the equation true.  The checker gives the tree meaning by recursively
matching it against a target formula and context.  An implication introduction is accepted only
when the target is $A\to B$ and its body checks as $B$ in the context extended by $A$.  A universal
elimination first synthesizes a formula $\forall x.\varphi$, then capture-safely substitutes its
term argument into $\varphi$.  An induction node must check both the zero case and the universally
quantified successor step for its stored motive.

The checker is bidirectional.  Elimination and annotated equality forms usually *synthesize* their
conclusion; introduction forms are *checked* against a conclusion already known.  This avoids
stuffing every proof node with redundant formula annotations while keeping the recursion readable.
The whole trusted checker is 234 physical lines at this stage, below the project's roughly
300-line design ceiling, and an import-hygiene test forbids it from importing the engine or UI.

Python adds an unusual adversarial wrinkle.  A subclass can override equality and pretend to equal
any target.  The trusted recursion therefore accepts exact frozen kernel constructors at rule
boundaries—`type(node) is EqRefl`, for example—rather than granting meaning to arbitrary subclasses.
Engine-only `Hole` and `MetaVar` nodes consequently cannot slip across QED merely because they share
a marker base class.

## Why proof terms rather than an LCF theorem type?

There are two classic ways to isolate a prover's trusted core.

In an **LCF-style** architecture, the implementation hides the constructor of an abstract `Theorem`
type.  Client code can obtain theorem values only by calling a small collection of trusted inference
functions.  Tactics are programs that compose those functions.  This is a powerful design, and its
central idea—untrusted proof search over a tiny trusted base—survives in modern systems.

In a **proof-term** architecture, tactics construct ordinary certificate syntax.  An independent
checker later validates that syntax.  Lean and Coq follow this broad pattern, and Peano Lab chooses
it for three practical reasons.  First, the certificate continues the Curry–Howard story: students
can watch a tree of holes become a proof.  Second, certificates can be printed, stored, mutated in
tests, and replayed without preserving privileged runtime values.  Third, final checking is a clean
second opinion: the tactic engine proposes; the kernel disposes.

Neither architecture is automatically sound.  An incorrect primitive inference function breaks an
LCF kernel; an incorrect certificate checker breaks a proof-term kernel.  An inconsistent axiom set
also proves too much no matter how elegant the software is.  The engineering goal is not to abolish
trust, but to concentrate it in code and rules small enough to inspect.

The live
[`LCF versus proof terms`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20kb%20lcf-vs-proof-terms)
card keeps this comparison beside the prover rather than presenting the chosen design as the only
possible one.

## Two De Bruijn ideas, both about trust

Nicolaas de Bruijn's name appears here in two distinct ideas.  **De Bruijn indices** represent bound
variables by distance to their binder.  The **De Bruijn criterion** says that formal proofs should be
checkable by a small, independently inspectable program.  The former helps us implement binding
correctly; the latter tells us why the resulting checker, rather than the tactic UI, is the source of
proof authority.

Consider

$$
  \forall x.\;\exists y.\;x+y=y+x.
$$

Inside the equation, $y$ is index $0$ because its binder is nearest, while $x$ is index $1$.
Renaming either surface binder changes no kernel object.  Alpha-equivalent formulas are therefore
literally the same representation, and hypothesis lookup never depends on a user's favorite letter.

Names disappear easily; substitution is the difficult part.  Suppose the internal formula
$\forall y.\;x=y$ contains a free outer variable $x$, and we substitute another free variable $z$
for it.  Before descending beneath $\forall y$, $z$ is index $0$.  Beneath that binder it must be
shifted to index $1$:

$$
  \forall y.\;\#1=\#0.
$$

A naive substitution would insert `#0` unchanged and silently turn the result into
$\forall y.\;y=y$.  That is variable capture: a free occurrence has acquired a binder and the
meaning has changed.  Peano Lab's
[`subst.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/kernel/subst.py)
separates **shifting** indices from **opening** one variable slot.  When opening descends through a
quantifier, it increases the binder depth and lifts the replacement.  Induction motives,
universal elimination, existential elimination, rewriting beneath binders, and theorem-library cut
elimination all ultimately rely on this small operation.

The distinction has a useful slogan: indices remove alpha-renaming accidents, but they do not make
capture avoidance automatic.  Correct shifting is part of the proof rule.

## The audit that made QED a hard boundary

The independent final check is not decorative architecture.  A 2026 audit of the sibling Lambda Lab
found that four cooperating defects let its interactive builder report a false QED for Peirce's law.
The details involved metavariable discipline, proof-wide substitutions, and finalization, but the
larger failure was simpler: the tactic layer's account of success was treated as authoritative.
The repair introduced a checked finalization path and a single session owner, then made those lessons
binding for Peano Lab.  The project history records the incident in the
[`JOURNAL`](https://github.com/nasqret/vietnam2026/blob/peano-lab/JOURNAL.md), while the original broader
Lambda Lab review remains in
[`docs/lambda-lab-audit.md`](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/lambda-lab-audit.md).

Peano Lab therefore treats its own engine state as untrusted input.  `ProofState.target` is frozen,
but a buggy tactic could replace the entire frozen object.  The browser session separately retains
the original parsed formula and passes it into `checked_final`; finalization also rejects a state
whose cached target differs.  Classical mode is retained by that same owner as an exact Boolean.
The ordinary `check` rejects every double-negation-elimination node, while the explicitly selected
`check_classical` accepts such a node and leaves it visible in the certificate.

The tests attack this boundary directly.  They replace the cached goal, forge a goal-free state for
$0=S(0)$, leak unresolved metavariables, mutate induction motives and branches, attempt eigenvariable
escape, subclass AST nodes with dishonest equality, and perform naive capture under binders.  Passing
happy-path examples would show that the prover can work; rejecting these mutations is evidence that
its claimed boundary is real.

## What the checker does—and does not—establish

If the checker accepts $p:A$, we have evidence that $A$ is derivable from the encoded natural-
deduction rules, PA1–PA6, and the selected induction instances (plus explicit DNE only in classical
mode).  This is the lab's operational meaning of sound proof checking.

It is not a machine-checked proof that the Python checker itself is correct.  It does not establish
that PA is consistent, that every true arithmetic sentence is derivable, or that the intended
natural-number model is the only model of the first-order axioms.  The De Bruijn criterion reduces
the trusted computing base; it does not erase metamathematics or hardware and runtime trust.

That modesty is a strength.  The tactic engine can grow new search procedures, simplifiers, and even
learned tactic proposers without enlarging the logical authority they possess.  Every proposed QED
still has to fit through the same small door: a closed certificate, the owner's original statement,
and an independent structural check.
