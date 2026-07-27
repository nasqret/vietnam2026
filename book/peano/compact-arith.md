# `compact_arith`: searching for a small PA certificate

A proof can be short on the blackboard and enormous after elaboration.  That is not a soundness
failure: every node of the enormous result may be correct.  It is a lesson about the difference
between three objects that are easy to conflate:

1. the **tactic program** a person writes;
2. the **proof tree** constructed by the untrusted engine; and
3. the judgment checked by the trusted kernel.

This chapter develops `compact_arith`, a deliberately PA-specific arithmetic tactic.  Its job is
not to enlarge what Peano Lab can prove.  Its job is to search for a smaller ordinary certificate
for one rigid equality, using the direction in which PA's recursive equations are actually stated.
The tactic remains untrusted, the kernel language remains unchanged, and “smallest found” never
silently becomes “mathematically minimal.”

## The experiment that forced the question

Consider the familiar parity theorem

$$
  \forall n\;\exists x\; n(n+1)=2x.
$$

The historical pre-M18 readable replay first proves the stronger recurrence-normal statement

$$
  \forall n\;\exists x\; n^2+n=2x
$$

and then transports it to the displayed theorem.  Its source is only eighteen proof tactics, with
two generic `ring` calls doing the arithmetic:

```text
pa prove forall n. exists x. n * (n + 1) = 2 * x
have strong : forall n. exists x. n * n + n = 2 * x
induction n
exists 0
norm_num
cases IH
exists x + S n
trans ((n * n + n) + S n) + S n
ring
rewrite IH_witness
ring
intro n
specialize strong n
suffices normalize : n * (n + 1) = n * n + n
rewrite normalize
exact strong
rewrite PA4
rewrite PA3
apply PA6
qed
```

Yet the finalized result has **30,030 structural proof-tree nodes**.  Measuring the partial
certificate after each interesting line locates the growth:

| Point in the replay | Proof-tree nodes |
|---|---:|
| after `trans`, before the first `ring` | 35 |
| after the first `ring` | 18,651 |
| after rewriting by the induction hypothesis | 18,654 |
| after the second `ring` | 30,016 |
| after all source tactics, before local-cut compilation | 30,037 |
| finalized ordinary kernel certificate | 30,030 |

The two `ring` calls are doing honest work.  The generic normalizer derives associativity,
commutativity, distribution, and coefficient calculations by instantiating checked semiring-law
certificates.  Those derivations are then cut-normalized into the final tree.  A high-level law
name is not a one-node oracle in the kernel.

Nor do `have` and `suffices` add sharing.  They are convenient schedules for local cuts.  Before
checking, their engine-only nodes are compiled away.  If a local fact is used repeatedly, its proof
may consequently occur repeatedly in the tree.  In this example the proof of `strong` is used only
once, so local-cut duplication is not the main source of growth: generic `ring` elaboration is.

This gives the first rule of the experiment:

> Source-line count, rendered-character count, proof-tree count, and mathematical difficulty are
> different measurements.

M18 keeps the same human-visible mathematics but replaces those two generic algebra calls and the
closed base calculation with the PA-specific tactic.  The current replay is retained in
[`artifacts/triangular-even-readable.pa`](https://github.com/nasqret/vietnam2026/blob/peano-lab/artifacts/triangular-even-readable.pa):

```text
pa prove forall n. exists x. n * (n + 1) = 2 * x
have strong : forall n. exists x. n * n + n = 2 * x
induction n
exists 0
compact_arith
cases IH
exists x + S n
compact_arith [IH_witness]
intro n
specialize strong n
suffices normalize : n * (n + 1) = n * n + n
rewrite normalize
exact strong
compact_arith
qed
```

Notice what did **not** disappear: the stronger claim, induction, both witness choices, the explicit
permission to use `IH_witness`, and the final bridge.  Compact arithmetic elaboration shortens the
certificate construction; it does not conceal the mathematical proof plan.  These thirteen proof
tactics finalize to the same 180-node, depth-34 ordinary tree retained by the hand-authored
certificate artifact; the canonical certificate bytes are identical.

## Discovery: normalize the recurrence, not every step

The 30,030-node result prompted a sequence of checked experiments.  A direct induction with a more
careful successor witness produced 343 nodes.  Replacing generic library derivations with smaller
special-purpose arithmetic lemmas brought that route to 252 nodes.  The decisive improvement was
not a cleverer printer or a trusted shortcut.  It was a better induction statement.

PA defines operations by recursion on the **second** argument:

$$
\begin{aligned}
  a+0 &= a &&\text{(PA3)},\\
  a+S b &= S(a+b) &&\text{(PA4)},\\
  a\cdot0 &= 0 &&\text{(PA5)},\\
  a\cdot S b &= a\cdot b+a &&\text{(PA6)}.
\end{aligned}
$$

The surface term $n(n+1)$ therefore hides exactly the recurrence that PA6 wants to expose.  Proving
$n^2+n=2x$ inside the induction makes the induction hypothesis syntactically useful without
renormalizing the original product at every successor step.  After eliminating

$$
  n^2+n=2x,
$$

choose the next witness $x+S n$.  The remaining equality is organized as

$$
  (S n)^2+S n
    = (n^2+n)+S n+S n
    = 2x+S n+S n
    = 2(x+S n).
$$

Only after the universal induction proof is complete do we prove

$$
  n(n+1)=n^2+n
$$

and use one whole-proposition equality substitution to transport

$$
  \exists x\;(n^2+n=2x)
  \quad\text{to}\quad
  \exists x\;(n(n+1)=2x).
$$

Transporting the existential as a whole is important.  Opening it, recovering its witness, and
rebuilding it would add logical scaffolding and would repeat a conversion that is independent of
the witness.

The reproducible constructor in
[`scripts/minimize_parity_certificate.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/scripts/minimize_parity_certificate.py)
builds a cut-normal **180-node**, depth-34 certificate.  Its canonical rendering is retained as
[`artifacts/triangular-even-180.certificate.txt`](https://github.com/nasqret/vietnam2026/blob/peano-lab/artifacts/triangular-even-180.certificate.txt).
The independent kernel accepts it for the original theorem and rejects it for the nearby mutated
claim $n(n+1)=2x+1$.

The arithmetic subderivations explain where those nodes go:

| Specialized derivation | Role | Tree nodes when measured on its stated instance |
|---|---|---:|
| `add_succ` | $S a+b=S(a+b)$ | 20 |
| `swap_special` | move two successor additions in the exact required shape | 51 |
| `mul_succ_left_special` | $S a\cdot n=a\cdot n+n$ | 75 |
| `arithmetic_finish_special` | $(2w+j)+j=2(w+j)$ at the needed instance | 65 |

These headline figures must not be added: some derivations occur inside others and the complete
tree has its own surrounding logical nodes.  The stronger universal theorem has 165 nodes; the
final transport adds fifteen, giving 180.

The regression suite pins that accounting more precisely.  The closed base equality costs 9 nodes
and its existential introduction adds one.  The successor equality selected with `IH_witness`
costs 149 nodes; existential introduction, elimination of the induction-hypothesis existential,
and the induction-step binders add five.  With the `Ind` node this makes the stronger universal
theorem $10+(149+5)+1=165$.  The final multiplication-by-`+1` bridge costs 11.  Orienting it with
`EqSym`, specializing `strong` with `ForallElim`, transporting the existential with `EqSubst`, and
reintroducing the outer variable with `ForallIntro` add four, so the complete tree is
$165+15=180$ at depth 34.

## The surface contract

`compact_arith` deliberately does less than the hand-authored 180-node constructor.  Version 1
closes one **rigid equality goal**.  It does not invent an induction invariant, choose an
existential witness, introduce variables, or secretly scan every hypothesis.  The learner remains
responsible for the mathematical shape of the proof.

The two intended forms are:

```text
compact_arith
compact_arith [h, <- k]
```

With no bracketed list, the tactic uses only PA's defining equations and its fixed, checked
recurrence templates.  A bracketed list makes exactly those named equality hypotheses available,
in the written order.  The selected certificate may use a subset, but can never consult an
unlisted equation.  `h` offers its equation from left to right; `<- k` offers `k` from right to
left.  There is no wildcard, implicit context mining, or “use whatever works” mode.

Consequently the pedagogical parity proof still has to say, visibly:

- which stronger proposition to establish;
- that induction is on `n`;
- that the base witness is `0`;
- that the successor witness is `x + S n`;
- where the induction hypothesis may be used; and
- how the recurrence-normal statement is transported back to the requested statement.

`compact_arith` replaces only the bulky arithmetic equality derivations inside that structure.  A
pure `compact_arith?` preview reports the selected plan, equations actually used, expanded proof
nodes, proof depth, annotation nodes, and synthesis work without
changing goals, history, holes, trace steps, or allocator state.  Preview is an inspection command,
not a weaker acceptance path: running `compact_arith` must synthesize and check the certificate
again.

The following calls are outside the version-1 contract:

```text
# not equality goals
compact_arith              # when the target is an existential or implication

# no unresolved witness guessing
compact_arith              # when either equality side still contains a flexible metavariable

# no hidden assumptions
compact_arith [*]
```

Unsupported shapes, malformed lists, unknown or non-equality hypotheses, exhausted bounds, and
different arithmetic normal forms are ordinary transactional tactic failures.  None may publish a
partial candidate.

## What certificate language may it use?

There is no `CompactArith` node in the trusted language.  The synthesizer targets the constructors
already defined in `kernel/proofs.py`:

| Kernel constructor | Arithmetic meaning |
|---|---|
| `Axiom("PA3")` ... `Axiom("PA6")` | the four recursive equations above |
| `ForallElim` | instantiate a universally quantified PA equation or proved template |
| `EqRefl`, `EqSym`, `EqTrans` | reflexivity, orientation, and equality paths |
| `CongS`, `CongAdd`, `CongMul` | lift equalities through term constructors |
| `EqSubst` | Leibniz transport, including replacement of several occurrences at once |
| `ForallIntro`, `ImpIntro`, `Hyp`, `Ind` | construct the bounded recurrence templates themselves |

The tactic needs no classical `DNE`, no new arithmetic axiom, and no engine-only local-cut node in
the proof fragment it publishes.  Logic constructors such as `ExistsIntro` remain the work of the
surrounding human-written proof.

A named helper is not trusted merely because the engine calls it a lemma.  The fully quantified
addition-successor template is paired with an ordinary certificate and checked once from the empty
proof context.  The parameter-specialized induction instances for offset swapping, successor-left
multiplication, and doubling are likewise checked with no hypotheses before their final induction-
index elimination.  The small `+1`, `+2`, and multiplication-by-`+1` bridges are direct PA
derivations rather than induction templates.  Every selected focused result is cut-normalized and
checked again.  The kernel never resolves a helper name.

## A typed synthesis layer

The safest implementation pattern is already present in `ring.py`: carry the claimed endpoints
beside every proof fragment.  Conceptually, the internal value is

```python
EqualityCertificate(left, right, proof, cost)
```

Smart constructors enforce local contracts:

- symmetry swaps the recorded endpoints;
- transitivity requires the first right endpoint to equal the second left endpoint;
- congruence constructs the corresponding compound endpoints;
- a PA instance records the exact terms substituted for its quantifiers; and
- equality substitution records both its one-hole formula motive and the direction of transport.

These wrappers are untrusted bookkeeping.  They make engine bugs easier to locate, but only the
independent checker turns the underlying `proof` into evidence.

The synthesis pipeline is:

1. **Validate the request.** Require a rigid equality, parse the optional ordered hypothesis list,
   reject unresolved metavariables, and scan the term AST under explicit limits.
2. **Seed exact edges.** Instantiate PA3--PA6, reflexivity, explicitly selected hypotheses, and the
   small recurrence templates at terms already present in the goal.
3. **Explore bounded alternatives.** The phase-1 seeded planner memoizes a finite candidate grammar:
   useful orientations, congruence positions, transitivity paths, equality-motive substitutions
   that may replace several term occurrences, and
   recurrence instances derived from goal subterms.  It is not a general Dijkstra search, e-graph,
   or invariant synthesizer.
4. **Keep the cheapest exact endpoint proof found in that grammar.** Memoization may discard a more
   expensive derivation of the same syntactic equality.  Ties use a documented structural key so
   browser and native runs agree.  Candidates also retain their generation ordinal, so two
   equal-cost selected hypotheses respect the user's written order instead of being reordered by a
   set or dictionary traversal.
5. **Normalize administrative cuts.** Existing capture-avoiding reduction expands checked helper
   applications to the ordinary kernel tree.
6. **Measure the expanded candidate.** A one-node reference to a large helper is not charged as one
   if finalization will inline it.
7. **Check before commit.** Call the independent kernel on the exact focused context, candidate,
   and target.  Only then replace the focused hole and append one history/trace transaction.
8. **Check again at QED.** Session finalization still compiles the complete proof and checks the
   session owner's original theorem in its original logic mode.

This double check is intentional.  The focused check prevents a bad arithmetic candidate from
entering a live state; the final check prevents any tactic-layer or state-routing defect from
changing the theorem that receives QED.

### Reading the implementation

The complete untrusted engine is
[`engine/compact_arith.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/engine/compact_arith.py).
`CompactArithLimits` is the resource contract; `_EqualityProof` and `_Candidate` carry exact
endpoints; `_Planner` performs bounded memoized selection; `prove_compact_equation` constructs and
checks one focused fragment; and `compact_arith_checked` performs the immutable proof-state
transaction.  The parser, named-hypothesis resolution, preview, trace, replay, and tactical routing
are in
[`ui/prove.py`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/peano_lab/ui/prove.py).

The tests are meant to be read beside that code.  The
[`engine tests`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/tests/test_compact_arith.py)
pin endpoint composition, exact seed costs, deterministic selection, template checking, malformed
inputs, and every resource boundary.  The
[`surface tests`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/tests/test_compact_arith_surface.py)
pin preview purity, explicit hypotheses, trace/history/undo behavior, binders, and tacticals.  The
[`180-node replay`](https://github.com/nasqret/vietnam2026/blob/peano-lab/peano-lab/py/tests/test_readable_parity_artifact.py)
then checks the complete original theorem, exact depth, and canonical certificate bytes.

## Recurrence templates, not a hidden decision procedure

The useful search space is finite because the implementation fixes it, not because PA is easy.
Version 1 seeds a small family of schema shapes suggested by PA's right-recursive equations:

$$
\begin{aligned}
  a+1 &= S a,\\
  a+2 &= S(Sa),\\
  a(b+1) &= ab+a,\\
  S a+b &= S(a+b),\\
  S a\cdot b &= a\cdot b+b,\\
  (A+j)+S a &= (A+a)+S j,\\
  (2w+j)+j &= 2(w+j).
\end{aligned}
$$

The first three bridges cost 6, 10, and 11 proof nodes respectively.  In particular, the
11-node multiplication-by-add-one bridge proves the final displayed normalization directly from a
six-node successor bridge and PA6, avoiding a trip through the general polynomial normalizer.

The four genuine recurrence identities after the three direct bridges are justified by `Ind`
certificates.  Parameters are shifted beneath the induction binder by the existing De Bruijn
substitution utilities.  The search instantiates a schema only at terms drawn from the focused
equality and explicitly named hypotheses; it does not enumerate arbitrary formulas.

The zero-offset form of the final doubling recurrence is a typical proof-engineering choice.  Its
base case reduces immediately with PA3 and PA5.  The recorded hand experiment compared it with an
algebraically equivalent successor-offset template, which looked closer to the goal but produced a
larger certificate.  Version 1 retains the 65-node zero-offset winner as its single doubling seed;
that historical comparison is not performed again on every tactic call.

This is not `omega`, nonlinear hypothesis solving, or a decision procedure for PA.  It does not
claim completeness even for all polynomial identities: `ring` remains the broad commutative-
semiring normalizer.  `compact_arith` trades breadth for certificate shape in a small, documented
family of recurrence equalities.

## Cost means expanded proof-tree cost

Peano Lab's existing metric is

$$
  |p| = 1 + \sum_{q\text{ a direct proof child of }p}|q|.
$$

It counts occurrences of `Proof` constructors.  It does not count term AST nodes or formula
annotations stored in `EqSubst` and `Ind`.  It also treats the certificate as a tree: if the same
Python proof object appears twice, both occurrences are counted.  Canonical text likewise prints
both occurrences.

This metric is useful because it describes the work visible to the current structural checker, but
it is not the only reasonable metric.  A richer future planner could retain a small Pareto frontier
over at least:

- expanded proof-tree nodes;
- maximum proof depth;
- term/formula annotation size or canonical rendered bytes; and
- synthesis work and elapsed time.

Version 1 instead memoizes one winner per exact endpoint pair and assumption-permission mode, using
the deterministic lexicographic key `(expanded nodes, proof depth, annotation nodes, generation
ordinal)`.  The extra mode prevents an internal recurrence prefix from silently consuming a named
hypothesis.  Work units and elapsed time are stopping bounds, not optimization objectives.  The
public result must name which measure it reports.  “120 unique subtrees” is not the same claim
as “120 expanded nodes.”  Hash-consing can reduce engine memory, but it does not reduce the current
tree metric.  A serialized DAG with references would require a new acyclicity- and context-aware
kernel design—particularly because `Hyp` and binders make sharing scope-sensitive—and is outside
this tactic.

## What may honestly be called minimal?

The 180-node artifact is a **checked upper bound**: it proves that a certificate of size 180 exists.
It is the smallest result found in the recorded experiment.  It is not a proof that no 179-node
certificate exists.

The distinction is unusually important here because the node metric ignores the sizes of terms and
motives.  There are infinitely many possible annotations at a fixed constructor count, so “try all
proofs with fewer nodes” is not automatically a finite computation.  A global minimality claim
would need both:

1. a precisely fixed, finite candidate language and cost model; and
2. an exhaustive search or a formally verified lower-bound argument for that language.

`compact_arith` may make the narrower statement “cheapest among the candidates generated by
template set T under bounds B,” provided it really enumerates that finite set and charges the
post-expansion tree.  It may report “matches the current 180-node record” if a complete surrounding
proof actually does.  It must not print “optimal certificate” as a synonym for “best route this
heuristic happened to visit.”

For comparison, changing the cost to canonical serialized bytes would make the set below each
fixed cost finite in principle.  Exhaustive search would still be fantastically expensive.  No
general tactic for arbitrary PA statements can promise to find a proof—or a smallest proof—and
terminate on every input.

## Bounds and transactional failure

Certificate minimization is search, and search needs visible stopping rules.  The implementation
therefore fixes limits for at least:

- input term nodes and depth;
- number and size of explicitly selected hypotheses;
- recurrence-schema instantiations;
- candidate equality endpoints and paths;
- work units and wall-clock time;
- generated proof nodes and depth; and
- complete partial-proof nodes and depth after insertion.

The version-1 defaults admit at most 256 aggregate input-term nodes at depth 64, 16 explicitly
selected equalities, 64 seed/template instances, 512 memo/search states, 512 generated candidates,
100,000 term/formula annotation nodes at depth 256, 20,000 work units, a generated fragment of
10,000 proof nodes at depth 256, a complete partial certificate of 100,000 proof nodes at depth
512, and five seconds.  Annotation accounting matters because the primary `proof_size` metric
deliberately omits the terms and motives stored inside proof nodes.

Limits are checked before expensive construction and throughout the search.  Crossing one raises a
typed tactic limit; it does not mean the equality is false, unprovable, or lacks a smaller proof.
The immutable input `ProofState`, history, substitutions, and holes remain exactly unchanged.

Likewise, a failed `compact_arith?` preview has no state effect.  The browser's Stop action remains
the hard interruption boundary because Python runs inside a disposable worker; restarting that
worker discards the in-memory session rather than publishing an unfinished candidate.

## Tests are part of the theorem prover

The central positive regression is not merely “the tactic returned success.”  It should establish
all of the following:

- the readable parity proof supplies the stronger invariant, witnesses, and explicit IH use;
- every `compact_arith` equality fragment checks in its exact local context;
- the finalized complete certificate checks from the empty context against the original theorem;
- its expanded node/depth metrics are deterministic and meet the recorded bound; and
- the same certificate fails against a nearby mutated target.

Across the existing kernel and arithmetic suites, adversarial tests mutate a PA axiom instance,
equality orientation, witness, induction motive, substitution motive, and target.  M18 adds exact-
endpoint, orientation, and nearby-target attacks.  Capture regressions run template use beneath extra
universal, existential, and implication binders.  Transaction tests cover malformed lists, unknown
hypotheses, non-equation hypotheses, unresolved metavariables, different endpoints, exhausted
budgets, host recursion failure, and a candidate rejected by the independent checker.

Repeated runs must choose byte-identical plans.  Preview must leave state, history, holes,
metavariable allocation, and JSONL traces untouched.  Running the tactic adds exactly one ordinary
transaction, and one `undo` restores the exact earlier state.  A static import test continues to
prove that the kernel imports neither the new engine module nor any UI code.

The most valuable test is still the ordinary last line:

```text
qed
```

It submits the complete expanded certificate—not the cost report, recurrence plan, preview, or
tactic's claim of success—to the unchanged checker with the original formula.

At the M18 close, the focused suite has 46 passing tests and the full Peano suite has 744; the
sibling Lambda suite remains green at 360 tests plus 36 subtests.  The warning-as-error book build,
193-link/170-command executable-prose gate, 61-note/356-link connected vault, 1,692-session source-
bound corpus, application and vendor manifests, Node interaction harnesses, and exact local stage
are also green.  The local assembly is build `2026-07-28c`, application `a-953fa3777cd4`.  No in-app
browser was attached, so this report does not claim a live Pyodide click-through; M18 was not
deployed.

## What students should take away

The 30,030-to-180 experiment is not an argument against readable tactics.  Readability helped reveal
the right invariant.  Nor is it an argument that the kernel should trust a faster arithmetic
oracle.  It shows that proof engineering has at least two creative levels:

- choose a proposition and witness whose recurrence matches the axioms; and
- choose a certificate construction that avoids paying for general algebra when a specialized
  derivation is enough.

`compact_arith` automates part of the second level while leaving the first visible.  That boundary
is pedagogically deliberate.  A student can inspect why the step works, compare its certificate
with `ring`, alter a recurrence template, and see the independent checker accept or reject the
result.  The lesson is not that 180 is a magical number.  It is that optimization may change how
evidence is built, but never who is allowed to validate it.

Continue with {doc}`The deliberate limits <limits>` for the boundary between bounded automation and
general PA, or return to {doc}`Checked arithmetic automation <arithmetic-automation>` to compare
the contracts of `simp`, `norm_num`, `ring`, and `auto`.
