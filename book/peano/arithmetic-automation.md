# Checked arithmetic automation: compute, then certify

Arithmetic automation is useful precisely where its soundness boundary is easy to blur.  Python can
calculate that $2\cdot3=6$ immediately, but a Python integer is not a derivation in Peano arithmetic.
Peano Lab therefore gives computation one narrow job: **choose which proof to construct**.  The
independent kernel still decides whether the resulting certificate proves the equality goal.

The live [`norm_num` card](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20tactic%20norm_num)
and the ENTER-driven
[`norm_num` tutorial](https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/?cmd=pa%20tutorial%20norm_num)
exercise that boundary in the browser.

## A numerical normal form is a claim, not evidence

Write $\overline{k}$ for the kernel term made from $k$ successors of zero.  For a closed arithmetic
term $t$, the untrusted normalizer first computes a candidate value $k$.  It must then construct a
proof term

$$
  p_t : t = \overline{k}.
$$

That certificate uses only instantiated PA3--PA6 equations and the kernel's equality combinators
`EqTrans`, `EqSym`, `CongS`, `CongAdd`, and `CongMul`.  The closed-term routine asks the kernel to
check $p_t$ before returning it.  Evaluation may select $\overline{k}$; it never creates a trusted
shortcut from syntax to truth.

`norm_num` applies this operation to an equality, optionally beneath leading universal binders.  It
visits maximal variable-free, non-numeral subterms in deterministic left-to-right order.  Thus it can normalize all of a closed
equation, or a closed numerical island below an open parent:

$$
  n + (2\cdot3) = n + 6
  \quad\rightsquigarrow\quad
  n + 6 = n + 6.
$$

Congruence lifts the checked proof of $2\cdot3=6$ through the surrounding addition.  If both
normalized sides are identical, reflexivity closes the middle equality and the tactic checks the
finished certificate before publishing success.  If useful normalization leaves a genuinely
different open equality, the same equality transport surrounds one remaining certificate hole;
the tactic has simplified the obligation, not declared it solved.

Here is one executable session containing both cases:

```text
pa> pa prove (2 * 3 = 6) /\ (forall n. n + (2 * 3) = n + 6)
pa> split
pa> norm_num
pa> intro n
pa> norm_num
pa> qed
```

The last command still checks the complete conjunction against the session owner's original target.
The automation layer never gets to replace that target with its normalized rendering.

## Four tools, four contracts

The tactics overlap in convenient examples, but their contracts are intentionally different:

| Tool | What it chooses | Evidence it builds | Deliberate stopping point |
|---|---|---|---|
| `simp` | Ordered PA and explicitly named rewrites | Equality transport for each rewrite | No permitted decreasing rewrite or closing congruence |
| `norm_num` | Values of closed numerical islands | PA3--PA6 numeral proofs, lifted by congruence | Unsupported goals, unresolved metas, false closed equations, or non-closing no progress |
| `ring` | A sparse commutative-semiring normal form | Rechecked semiring laws plus PA arithmetic | Different polynomials or any request to use hypotheses implicitly |
| `auto d` | A path through a bounded tactic search tree | Replay of the winning ordinary tactic sequence | No plan within the stated depth and node budgets |

Use `simp` when the defining equations or a named hypothesis should visibly rewrite a formula.  Use
`norm_num` when a goal contains concrete arithmetic.  Use `ring` for an unconditional polynomial
identity with variables.  Use `auto` when bounded proof search, rather than one known normalization,
is the lesson.  None of these commands adds a kernel inference rule.

The separation is visible even on a tiny open identity:

```text
pa> pa prove forall n. n + (2 * 3) = n + 6
pa> intro n
pa> hint
pa> norm_num
pa> qed
```

`hint` performs a pure bounded applicability check and suggests `norm_num`; it does not allocate a
proof hole, append history, or speculatively publish a tactic result.  A `limit` hint means only that
inspection stopped.  The user must still run the suggestion, and QED must still check its output.

## Browser limits are part of the result

A compact multiplication can denote a very large unary numeral and an even larger proof tree.
`norm_num` therefore rejects an attempt before it can monopolize the browser.  One invocation allows
at most 256 equality-term AST nodes at depth 64, at most 64 leading universal binders, 32 closed
computations, intermediate values up to 128, 25,000 work units, and a generated numerical bridge of
50,000 nodes at depth 256.  The complete live partial proof is separately capped at 100,000 nodes
and depth 512.  Its wall-clock budget is five seconds.  Multiplication checks the value bound before
multiplying, so a small source term cannot first allocate an enormous Python integer or successor
chain.

Crossing any bound is reported as a resource limit, not as a false theorem or an unprovability
result.  The proof state and its undo history remain unchanged.  The page's **Stop** button is the
hard abort for a running Python call: it terminates the disposable Web Worker and starts a fresh one.

## The boundary is intentionally smaller than arithmetic

This tactic proves equalities and normalizes closed numerical subterms inside equalities.  It may
open leading universal binders structurally and wrap the result in `ForallIntro`, but it does not
decide arbitrary quantified formulas, inequalities, disequalities, or consequences of local
hypotheses.  In particular, neither `norm_num` nor `ring` is a nonlinear hypothesis solver.
Conditional calculations still need visible proof structure such as `intro`, `trans`, and
`rewrite`.

Peano Lab also has no `omega` tactic.  A future Presburger decision procedure would need its own
certificate-producing design and explicit limits; it is not hidden inside this milestone.  Even such
a procedure would cover only a decidable fragment, not general Peano arithmetic.  The broader
logical boundary continues in {doc}`The deliberate limits <limits>`, while
{doc}`Induction and the theorem ladder <induction-ladder>` and
{doc}`The checked theorem ladder <ladder>` show how symbolic theorems are built when calculation is
not enough.
