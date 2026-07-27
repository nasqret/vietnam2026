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

## Local lemmas schedule one cut in two useful orders

Mathematical proofs rarely proceed in one uninterrupted line. We prove an intermediate proposition
$P$, give it a name, and use it while proving the old target $B$. In natural-deduction notation the
underlying operation is a cut:

$$
\frac{\Gamma\vdash P \qquad h:P,\Gamma\vdash B}{\Gamma\vdash B}.
$$

Peano Lab exposes two surface forms with the same logical meaning and deliberately different goal
orders. The exact syntax is `have h : P` or `suffices h : P`. The name must be fresh, and the
proposition is parsed using only the rigid arithmetic variables already visible in the focused
goal.

`have` follows the forward rhythm “establish the lemma, then use it”:

```text
pa> pa prove 0 = 0
pa> have h : 0 = 0
pa> refl
pa> exact h
pa> qed
```

If the old sequent was $\Gamma\vdash B$, the two new goals are ordered

$$
\Gamma\vdash P
\quad\text{then}\quad
h:P,\Gamma\vdash B.
$$

`suffices` follows the backward rhythm “show why this would be enough, then establish it”:

```text
pa> pa prove 0 = 0
pa> suffices h : 0 = 0
pa> exact h
pa> refl
pa> qed
```

Its order is

$$
h:P,\Gamma\vdash B
\quad\text{then}\quad
\Gamma\vdash P.
$$

This is not mere UI sorting. Goal order must equal left-to-right certificate-hole order, including
under `focus` and tacticals. The untrusted engine therefore has two administrative proof shapes:
`LocalHave(P, proof-hole, body-hole)` and
`LocalSuffices(P, body-hole, proof-hole)`. Their field order schedules exactly the obligations shown
above. They are **not kernel proof constructors**.

Once every hole is filled, untrusted finalization compiles either shape to the same mathematical
operation: substitute the proof of $P$ for hypothesis zero in the body. The substitution shifts
proposition indices and term variables beneath every binder, just as theorem-reuse cut elimination
must, so inserting an outer proof cannot capture an inner name. Only the compiled tree of ordinary
natural-deduction constructors reaches the unchanged checker, which checks it from the empty
context against the session owner's original $B$.

This separation makes the feature pedagogically useful without making it trusted. A parsing,
scheduling, or capture bug can produce a rejected certificate, never a false QED. It also explains
a performance subtlety: local names organize the script, but the final certificate is a tree rather
than a shared graph. If the body mentions `h` several times, compilation may copy its proof several
times. Read the administrative nodes and capture-safe compiler in
[`proof_reduction.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/engine/proof_reduction.py).

For a longer example, the
[`triangular-even-readable.pa`](https://github.com/nasqret/vietnam2026/blob/peano-lab/artifacts/triangular-even-readable.pa)
replay proves that every consecutive product $n(n+1)$ is even. It uses `have` for the stronger
induction invariant, `suffices` for the final normalization step, and `compact_arith` only for its
rigid equality leaves. The thirteen-tactic replay compiles to the retained 180-node certificate;
every QED still comes from the ordinary compiled tree. The size experiment and its honest
minimality boundary are developed in {doc}`compact_arith: searching for a small PA certificate
<compact-arith>`.

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

## A replayable script is not evidence

The owner can also render the surviving proof branch as a small surface program:

```text
pa> pa prove forall n. n + 0 = n
pa> intro n
pa> rewrite PA3
pa> refl
pa> script
pa> qed
pa> script
```

The first `script` response is labeled `ACTIVE (not kernel-checked)` and omits `qed`, although no
engine goals remain. The second is retained only after the independent checker accepts the original
universal statement; it is labeled `CHECKED QED` and ends with canonical `qed`. This distinction is
the same owner/kernel boundary seen above, now applied to saved text.

The replay follows the current undo branch. Failed tactics, failed QED attempts, `hint`, `?`,
`script`, and `undo` itself are absent; undo removes the transaction it restored. Complete
tacticals and `use` imports retain enough surface information to replay. A top-level `auto` expands
to its winning primitive commands because those commands are separately undoable in the live
session. Necessary `classical on`/`off` transitions come from the owner-held authority, never from a
tactic-controlled target.

Typing `script download` directly in the browser saves exactly the unindented replay body as
LF-only, newline-terminated UTF-8. A deep link cannot initiate that download. The body contains no
status comments: it is meant to be fed back to Peano Lab one line at a time.

A replay file is an untrusted program, not a [proof certificate](kernel.md) or a library
declaration. Replaying it reconstructs a candidate certificate; only `qed` checks the original
theorem. That is why saving a transcript does not add a theorem rule to the kernel or a declaration
to the checked ladder.

## Multiline paste is sequential replay

Entering a saved proof one line at a time is transparent but unnecessarily awkward. M17 therefore
provides two equivalent browser entry points: an accessible **Paste multiline proof** dialog and a
direct multiline paste into the terminal. Both require a complete replay. Ignoring blank lines, its
first line must begin exactly `pa prove ` and its last line must be exactly `qed`:

```text
pa prove forall n. n + 0 = n

intro n
rewrite PA3
refl
qed
```

This is not a new tactic and it is not one giant transaction. After structural and resource
preflight, the browser submits each nonblank line to the existing driver in order. If line $i$
fails, no later line runs, but the successful prefix $1,\ldots,i-1$ remains in the ordinary proof
session. Each successful proof command is still a separate undo step. That choice preserves the
most useful property of interactive failure: the learner can inspect the exact state where the
script stopped, repair it, and continue.

An explicit interruption is different from a failed line. **Stop**, Escape, or Control-C terminates
the worker so that a long command cannot keep the page busy; restarting the worker necessarily
discards that in-memory proof session.

The whole batch is bounded before execution: 100,000 characters, 256 nonblank lines, and the
existing `MAX_INPUT` bound on every individual line. Thus a malformed boundary or an oversized
paste cannot partially start. CRLF and LF input share the same line semantics, and blank lines do
not create history entries.

The paste boundary also removes ambient browser authority. Preflight rejects `script` commands,
and the batch executor ignores download payloads; only an explicitly typed single-line command may
request that side effect.
Most importantly, the final `qed` follows the same owner-held finalization path as manual entry and
asks the unchanged independent kernel to check the original theorem. Multiline paste is only an
input convenience. The bounded event/worker tests and readable replay exercise this contract; a
visual browser click-through is deliberately not claimed when no in-app browser is attached.
