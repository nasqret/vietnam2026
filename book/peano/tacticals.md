# When tactics become a language

A collection of tactics is a toolbox. It becomes a language when we can sequence tools, try
alternatives, iterate, and direct work to particular goals. Peano Lab reaches that point without
adding a single logical rule. Its tacticals are higher-order Python functions: they accept tactics
and return a new tactic with the same transactional contract.

The pinned low-level type stays wonderfully small:

$$
  \mathsf{Tactic}=(\mathsf{ProofState}\times\mathsf{String})\to
  (\mathsf{ProofState}\;\text{or}\;\mathsf{TacticError}).
$$

The string carries a primitive's arguments. The surface parser first assembles a child such as
`simp [IH]`; tacticals then invoke that assembled child with an empty extra argument string.

For example, `induction n; simp` compiles to `then(induction_n, simp)`. It applies induction to the
focused goal and simplification to every new induction obligation:

```text
pa> pa prove forall n. 0 + n = n
pa> induction n; simp
pa> qed
```

The browser's live [`tactical index`](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20tactic)
contains a checked script for every construct described below.

## Six combinators, six precise meanings

The surface grammar is small enough to state completely.

| Form | Meaning |
|---|---|
| `t1; t2` | Run `t1` on the focus, then `t2` on every goal newly made by `t1`. |
| `t1 <|> t2` | Try `t1`; only if it raises `TacticError`, run `t2` on the exact input. |
| `repeat t` | Keep applying `t` until expected failure, no progress, or a detected cycle. |
| `first [t1 | t2 | ...]` | Try choices left-to-right on the same snapshot; publish the first success. |
| `all_goals t` | Apply `t` once to each goal present when the command starts. |
| `focus n t` | Apply `t` to one one-based goal and splice its certificate back in place. |

`then` and `all_goals` snapshot the goals they promise to visit. They do not recursively chase
subgoals created by their right-hand or child tactic. This distinction prevents surprising loops
and makes command cost understandable. If recursive behaviour is desired, it must be said with
`repeat` or another explicit composition.

The following proof makes goal selection observable. `focus 2` closes only the second conjunct;
`all_goals` then visits the one goal that existed at its own entry:

```text
pa> pa prove (0 = 0) /\ (0 = 0)
pa> split
pa> focus 2 (refl <|> assumption)
pa> all_goals (first [assumption | refl])
pa> qed
```

`repeat` treats a child's failure as its normal stopping condition. The compound command succeeds
with the last good state, as in this introduction spine:

```text
pa> pa prove (0 = 0 -> 0 = 0) -> 0 = 0 -> 0 = 0
pa> repeat intro
pa> assumption
pa> qed
```

There are two extra safeguards. If a tactic succeeds without changing the logical goals or
substitution, repetition stops. If states cycle—as `repeat symm` can do—it stops rather than growing
an infinite tower of symmetric certificates. A final 256-step guard reports resource exhaustion as
an error; it is operational protection, not a logical verdict.

## Focus follows holes, not list positions

The difficult combinator is `focus`. Suppose the partial certificate is
$C[\square_1,\square_2,\square_3]$ and the user writes `focus 2 t`. Reordering the visible goals and
running `t` on the front would be unsafe: the result might be inserted into $\square_1$. Instead
Peano Lab builds a one-goal local state whose partial certificate is exactly `Hole(id₂)`. After the
child succeeds, it replaces that same ID inside $C$ and restores generated goals at the second
position.

The merge also propagates the child's metavariable substitution through the whole proof. A witness
chosen while focusing goal two may constrain goals one and three. This is why each combinator
validates not just the goal list but the exact state class, hole invariant, original theorem,
history prefix, and every substitution that existed before the child ran.

The implementation is intentionally comment-rich rather than clever; read
[`engine/tacticals.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/engine/tacticals.py)
alongside its
[`contract tests`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/tests/test_tacticals.py).

## One tactical expression is one transaction

A child tactical can take several successful internal steps before a later child fails. Those
intermediate values never become the caller's state. `orelse` catches `TacticError` and hands its
right branch the original immutable value; `first` does the same for each candidate. If all choices
fail, the caller still owns the exact input.

On success, child history entries are hidden and the outer combinator records one `Step`. Thus one
explicit tactical expression is one `undo`, including `induction n; simp` or `all_goals t`. This is
both a usability rule and a semantic one: the compound unit the learner typed is the unit that
history rolls back. `auto` is deliberately different: it replays its winning primitive plan, so
each replayed primitive remains a separate undo step and a separate successful trace record.

The surface parser lives separately in
[`ui/prove.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/ui/prove.py).
It splits only outside parentheses and brackets. `<|>` is parsed before `;`, while parentheses make
grouping explicit; `first` accepts `|`, comma, or `<|>` between choices. Session commands such as
`undo` and `classical on` cannot be nested as tactics because they change owner-level state rather
than certificate holes.

## `auto` is bounded search followed by replay

`auto [depth]` is related to the tactic language but is not a magical seventh logical rule. It
enumerates a deterministic menu of ordinary moves—`simp`, assumptions, introductions,
constructors, selected local equations through contextual simp sets, induction, and
applications—over immutable proof states. The
depth is proof-tree depth, so sibling obligations reuse the same allowance. A separate node budget
protects the browser.

Backtracking matters when siblings share a metavariable. A locally successful witness choice in the
first branch may make the second impossible; the search generator must then resume the earlier
choice and try another solution. At a complete leaf, an advisory kernel call discards malformed
certificates. It is still not QED, because search owns neither the original statement nor the
classical-mode authority.

Once a plan is found, `auto` throws away the speculative search tree and replays only the winning
primitive commands through the public dispatcher. You can watch it solve commutativity and still
require the ordinary owner-held final check:

```text
pa> pa prove forall n m. n + m = m + n
pa> auto 5
pa> qed
```

If a finite candidate tree is exhausted, the result is “no proof found”; if a depth or node boundary
was hit, the result is explicitly “limit.” Neither means unprovable. The complete policy is in
[`engine/search.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/engine/search.py).

## Traces are executable semantics

Every interactive tactic application—and every programmatic application given a logger—emits a
version-1 JSONL transition with canonical goals before and after, a zero-based focus, the tactic
text, and either `status: "ok"` or final error text. Failed applications are valuable training
examples, so they are recorded too—with unchanged before/after goals. A successful QED appends a
footer naming the theorem, certificate size, and tactic count.

For an explicitly written tactical, the record contains the complete surface command. Replaying
that text from the corresponding full session state must reproduce `goals_after`; rendered
`goals_before` alone is not a standalone snapshot because it omits the partial certificate,
substitution, history, original target, and classical authority. For a successful nonempty `auto`,
speculative branches are deliberately silent and only the winning **primitive** sequence is logged.
A failed `auto`, or a successful no-op on an already complete checked state, records `auto` itself.
The corpus therefore remains linear: it never claims that the prover jumped from one search branch
to another.

Metavariable aliases such as `?t1` stay stable for the whole session, control characters are escaped,
and JSON object fields have fixed insertion order. These are more than cosmetic promises. A learner
cannot infer a reliable state transition function if the printer gives one formula several names,
if focus is ambiguous, or if failures secretly mutate state. See the executable
[`trace contract`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/engine/trace.py)
and its
[`tests`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/tests/test_trace.py).

The resulting architecture has three clean layers: tacticals organize untrusted certificate
construction; replayable traces describe what happened; the independent kernel alone decides
whether the final certificate proves the owner-held theorem. That is how a tiny collection of
tactics becomes a useful language without becoming part of the trusted logic.
