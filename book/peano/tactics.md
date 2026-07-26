# Anatomy of a tactic

A tactic does not prove a theorem by persuading Peano Lab that the theorem is true. It edits an
unfinished **certificate**. The independent kernel will later decide whether that certificate is a
proof. This division of labour is the central design choice of the lab: tactics may be convenient,
ambitious, or buggy, while the meaning of QED remains small enough to inspect.

Try the smallest example that still exposes an engine metavariable:

```text
pa> pa prove forall n. n = n
pa> intro n
pa> trans ?
pa> refl
pa> refl
pa> qed
```

After `trans ?`, the engine has two obligations, informally $n=?t_1$ and $?t_1=n$. The first
`refl` determines that the flexible unknown must be $n$. That substitution reaches the sibling
goal and the partial proof term, so the second `refl` closes $n=n$. Nothing about `?` enters the
trusted language: QED refuses any certificate in which a metavariable remains.

You can also open the live [`trans` tactic card](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20tactic%20trans),
which separates its effect on goals from its effect on the certificate.

## A state is goals plus a proof with matching holes

A visible goal is a sequent

$$
  \Gamma \vdash \varphi,
$$

where $\Gamma$ is the ordered local context and $\varphi$ is the target. A whole proof state is
roughly

$$
  S=(G_1,\ldots,G_k;\ C[\square_1,\ldots,\square_k];\ H;\ T;\sigma;V).
$$

Here $C$ is one partial certificate, $H$ is undo history, $T$ is the cached original target,
$\sigma$ is the term-metavariable substitution, and $V$ remembers deterministic surface names for
de Bruijn variables. The crucial invariant is

$$
  \#\text{goals}=\#\text{distinct certificate holes}.
$$

Moreover, left-to-right goal order is left-to-right hole order. A tactic replaces the focused hole
with a proof constructor and zero or more new holes, then installs exactly the corresponding new
goals. `split`, for example, changes a goal $A\land B$ into goals $A$ and $B$, while replacing its
hole by `AndIntro(Hole(...), Hole(...))`. `intro` changes $A\to B$ into a goal for $B$ under a new
hypothesis and installs `ImpIntro(Hole(...))`.

This representation is worth dwelling on. If a UI merely kept a list of goals, it could reorder or
close the wrong one and still *look* plausible. Peano Lab instead carries the growing evidence and
checks the hole/goal bijection after every successful step. Read the short
[`ProofState` implementation](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/engine/state.py)
beside the kernel's
[`proof constructors`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/kernel/proofs.py).

The two-column reading is useful when learning any primitive. On a goal $S(a)=S(b)$, `congr`
opens $a=b$ and places `CongS(Hole(...))` in the certificate. On
$a_1+a_2=b_1+b_2$, the same command opens two goals and places
`CongAdd(Hole(...), Hole(...))`. `refl` has no new goal and replaces its hole by `EqRefl(t)`, but
only after rigid unification shows the two sides are identical modulo legitimate metavariable
solutions. A tactic card therefore reports **goal effect** and **certificate effect** separately.
The display explains the work requested from the learner; the proof constructor explains what the
kernel will eventually inspect. Neither description substitutes for the other.

## Immutability makes failure transactional

The public tactic type is deliberately ordinary Python:

```python
Tactic = Callable[[ProofState, str], ProofState]
```

An expected failure raises `TacticError` with final, user-facing English. It does not return a
half-edited state. `ProofState`, `Goal`, and `Step` are frozen dataclasses; their collections are
tuples, and the substitution map is copied behind a read-only proxy. A successful `_commit` makes a
new value and appends a `Step` whose `state_before` is the exact old value. Consequently `undo`
returns the actual snapshot, including goals, holes, names, and substitutions.

This is stronger than “we catch exceptions and try to repair the damage.” The input object never
changed. A tactic can allocate fresh hole numbers before discovering that it cannot proceed; those
unused numbers are harmless implementation detail. What must not leak is a logical edit to the
published state. The trace logger enforces the same story: an error record's `goals_after` must be
identical to `goals_before`.

The contract is tested for every primitive, including failures after parsing, unification, and
rewrite matching. Its implementation lives in
[`tactics.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/engine/tactics.py),
outside the kernel by design.

## Holes are not metavariables

It is tempting to call every unknown a hole, but two different unknowns need different disciplines.

- A `Hole` stands for an unfinished **proof**. It is paired with one visible goal.
- A `MetaVar` stands for an unfinished arithmetic **term**, such as the middle term in `trans ?` or
  the witness in `exists ?`.

Kernel terms—`0`, `S`, `+`, `*`, and de Bruijn variables—are rigid. Unification may bind only a
`MetaVar`; it cannot decide that two distinct variables are equal or reinterpret a function symbol.
An occurs check rejects cyclic solutions. Each metavariable occurrence also records how many newer
binders protect it. Solving an outer metavariable with an inner eigenvariable is rejected rather
than allowing that variable to escape its scope.

Most importantly, $\sigma$ is proof-wide. When one goal solves $?t_1$, the engine applies the
copy-on-write substitution to every goal, every hypothesis, and every term embedded in the partial
certificate. It deliberately does **not** rewrite the original target or old history snapshots.
This is why focused goals cannot be treated as independent worksheets: siblings may share the same
unknown.

## Rewrite produces transport evidence

Here is a direct PA3 rewrite rather than a hidden arithmetic evaluator:

```text
pa> pa prove forall n. n + 0 = n
pa> intro n
pa> rewrite PA3
pa> refl
pa> qed
```

The kernel's Leibniz rule stores a motive $P$ with one distinguished de Bruijn slot. If $e$ proves
$s=t$ and $q$ proves $P(s)$, then `EqSubst(P, e, q)` proves $P(t)$. The rewrite engine chooses the
first occurrence in canonical left-to-right, term-preorder order and constructs a motive whose two
instantiations reproduce the formulas before and after the edit. Shifting under binders makes this
capture-safe.

There is a subtle reversal for goals. A visible rewrite changes the *new obligation* from $P(s)$ to
$P(t)$, but the certificate must transport a future proof of $P(t)$ back to the original $P(s)$.
It therefore stores the symmetric equality. Rewriting a hypothesis uses the forward transport and
an explicit local implication, retaining the old hypothesis at an honest kernel index. The details
are readable in
[`rewrite.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/engine/rewrite.py).

`simp` repeats the same certified operation. Its ordered set begins with PA3–PA6; every chosen step
records an equation proof and a motive. The final normal form is closed only by reflexivity, an exact
hypothesis, or structural congruence, and the transports are folded back around that proof. Since
PA6 can make a syntax tree larger, termination is not justified by node count. The simplifier uses
a lexicographic path order with $\cdot > + > S > 0$ and requires every actual rewrite step to
decrease. Permutative schemas are admitted only when their instantiated orientation passes that
ordered check. Open
the live [`simp` card](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20tactic%20simp)
to inspect its complete executable example.

## The owner, not the tactic, says what QED means

Even a frozen state is not an authority: buggy Python could manufacture an entirely new frozen
state and replace its cached target. The browser's `ProofSession` therefore retains the originally
parsed formula and the exact classical-mode Boolean separately. On `qed` it calls, schematically,

```python
certificate = checked_final(state, owner.original_target,
                            classical=owner.classical)
```

Finalization requires no open goals, holes, or term metavariables; checks that the state's cached
target still equals the owner-held target; and finally calls the independent kernel in the empty
context against that owner-held formula. A failure leaves the session alive for inspection or
undo. The security boundary is visible in
[`ui/prove.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/ui/prove.py)
and the small
[`kernel checker`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/kernel/checker.py).

That gives the anatomy in one sentence: a tactic transaction replaces one certificate hole with
explicit evidence, propagates only legitimate flexible-term solutions, and hands the result back
to an owner that still trusts none of it until the kernel checks the original theorem.
