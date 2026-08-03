# The foundational arithmetic library

This part of the book is the readable front end to a native first-order Peano
arithmetic library. It begins with ordinary equality and semiring laws, builds
division, relational gcd, balanced Bézout, Gauss cancellation and Euclid's
lemma, then constructs finite factor sequences and their products using
Gödel-β codes. The endpoint is a checked, β-coded Fundamental Theorem of
Arithmetic.

```{admonition} The result in one sentence
:class: tip
The current runtime contains **393 closed native theorems**, including
factorization existence, extensional uniqueness, their combined FTA, and a
constructive theorem producing a prime above every supplied bound. The newest
137-theorem quadratic-reciprocity campaign now includes parity, constructive
residue decision, finite folds, factorial and power algebra, modular units,
sign and half-range bridges, β swap/reindex, finite pigeonhole, replacement
balance, and exact swap-last product invariance. The next nine entries expose
canonical remainder, congruence, and bounded modular-inverse interfaces.
```

<div class="pa-dashboard-metrics" aria-label="Current arithmetic library metrics">
  <div><strong>393</strong><span>checked native theorems</span></div>
  <div><strong>1,830,078</strong><span>structural proof occurrences</span></div>
  <div><strong>53,293</strong><span>self-contained Cuts</span></div>
  <div><strong>0</strong><span>remaining planned catalog theorems</span></div>
</div>

The generated snapshot has ordered root
`539a1195df131ed3e202efa15f48bef76a8b8c757789119e2265172453aaf566`.
Every entry is reconstructed from its authored script and checked from the
empty context. Names, summaries and hashes organize the library; none of them
grant proof authority.

## The mathematical metro map

The exact dependency graph has 393 vertices and 1,070 edges and is useful to machines, but a
human first needs the stations. Each box below is a link into the guided tour.

<nav class="pa-roadmap" aria-label="Arithmetic dependency roadmap">
  <a href="guided-tour.html#stage-foundations"><strong>1 · Foundations</strong><small>equality · semiring · induction</small></a>
  <a href="guided-tour.html#stage-order"><strong>2 · Discrete order</strong><small>bounds · cancellation · descent</small></a>
  <a href="guided-tour.html#stage-division"><strong>3 · Division</strong><small>n = dq + r · r &lt; d · uniqueness</small></a>
  <a href="guided-tour.html#stage-bezout"><strong>4 · GCD &amp; Bézout</strong><small>Euclidean invariance · four coefficients</small></a>
  <a href="guided-tour.html#stage-euclid"><strong>5 · Gauss &amp; Euclid</strong><small>coprime cancellation · prime products</small></a>
  <a href="guided-tour.html#stage-primes"><strong>6 · Prime search</strong><small>bounded factors · descent · unboundedness</small></a>
  <a href="guided-tour.html#stage-beta"><strong>7 · CRT &amp; β codes</strong><small>finite prefixes without primitive lists</small></a>
  <a href="guided-tour.html#stage-products"><strong>8 · Prefix products</strong><small>decoded factors · exact recurrence traces</small></a>
  <a href="guided-tour.html#stage-factorization"><strong>9 · Factorization</strong><small>greatest prime · sorted append · cancellation</small></a>
  <a href="guided-tour.html#stage-fta"><strong>10 · Native FTA</strong><small>existence ∧ extensional uniqueness</small></a>
</nav>

The exact generated graph remains available as an immutable
[`dependency-graph.mmd`](https://github.com/nasqret/vietnam2026/blob/5fff3eab2a7599035a6833c52b658da118f4a20c/artifacts/peano-library/dependency-graph.mmd).
The {doc}`interactive theorem atlas <theorem-atlas>` gives a readable local
neighborhood instead of attempting to draw all 1,070 edges at once. The
{doc}`native PA proof explorer <proof-explorer>` adds permanent theorem tags,
numbered tactic-line targets, and the larger quadratic-reciprocity closure.
Its parallel {doc}`definition-aware edition <defined-proof-explorer>` renders
the same 557 specifications with a 40-entry conservative-definition registry
(38 definitions occur) and exact native replay lines; it does not change the
proof graph or admission status.
Its {doc}`interactive dependency graph <dependency-graph>` draws short or
critical premise chains, start-to-target corridors, and complete transitive
cones.

## Choose your route

| If you want to… | Begin here | Then move to… |
|---|---|---|
| understand the mathematics | {doc}`Guided route from zero to FTA <guided-tour>` | the focused theorem links inside each stage |
| inspect every native proof | {doc}`Interactive theorem atlas <theorem-atlas>` | exact statements, complete scripts, dependencies and dependents |
| follow a proof line by line | {doc}`Native PA proof explorer <proof-explorer>` | permanent tags, linked lemma references, informal outlines and source receipts |
| read expanded formulas through linked names | {doc}`Definition-aware proof explorer <defined-proof-explorer>` | persistent `PD` expansions, exact native replay lines, and the unchanged theorem status |
| curate the next conservative edition | {doc}`Curating the next conservative edition <curation>` | P0/P1/P2 definitions, API completeness, and paired-source gates |
| see how theorems depend on one another | {doc}`Interactive dependency graph <dependency-graph>` | short and critical premise chains, route corridors and complete prerequisite cones |
| understand soundness | {doc}`Language, notation, and trust <language-and-trust>` | {doc}`Self-contained proof sharing <proof-sharing>` |
| study division and congruence | {doc}`Divisibility and subtraction-free congruence <divisibility-and-congruence>` | {doc}`GCD and balanced Bézout <gcd-and-bezout>` |
| study primes and factorization | {doc}`Primes and unique factorization <primes-and-factorization>` | the FTA and `prime_unbounded` cards in the atlas |
| follow the reciprocity campaign | {doc}`Quadratic reciprocity campaign <quadratic-reciprocity>` | parity, residue-decision, and finite-fold cards in the atlas |
| train a proof-producing model | {doc}`Using and extending the library <using-the-library>` | the snapshot, corpus and vault links below |
| audit provenance | {doc}`Sources and clean-room provenance <source-audit>` | catalog source mappings and the separate Lean companion |

## What the native FTA says

At the readable level, the endpoint is

$$
\begin{aligned}
&\left(\forall n,\ n\ne0\Longrightarrow\exists F.\;
  \operatorname{CanonicalPF}(n,F)\right)\\
&\qquad\land
\left(\forall n,F,G.\;
  \operatorname{CanonicalPF}(n,F)\land
  \operatorname{CanonicalPF}(n,G)
  \Longrightarrow F=_{\mathrm{ext}}G\right).
\end{aligned}
$$

Here $F$ and $G$ are not primitive lists. `BetaAt` decodes a bounded entry
from two natural-number codes, a second β code records prefix products, and
equality is extensional on the selected finite prefix. The exact statement is
ordinary first-order PA over `0`, `S`, `+`, `*` and equality.

| Native endpoint | Nodes | Depth | Cuts |
|---|---:|---:|---:|
| `prime_factorization_existence` | 43,973 | 98 | 1,328 |
| `prime_factorization_uniqueness` | 29,789 | 82 | 854 |
| `fundamental_theorem_of_arithmetic` | 73,767 | 99 | 2,184 |

The top-level authored proof is deliberately only three commands:

```text
split
exact prime_factorization_existence
exact prime_factorization_uniqueness
```

That contrast is central. A short modular script is not a hidden axiom: its
dependencies are embedded as self-contained `Cut` nodes, producing the
73,767-node closed certificate checked by the kernel. Read the complete card
for <a href="theorem-atlas.html#theorem-fundamental_theorem_of_arithmetic"><code>fundamental_theorem_of_arithmetic</code></a>.

## Prime unboundedness is a separate constructive theorem

FTA is not used to prove that there is a prime above every bound. The native
proof obtains a nonzero common multiple $c$ of every positive number through
$n$, takes a prime divisor $p$ of $S(c)$, and excludes $p\le n$: such a $p$
would divide both $c$ and $S(c)$, hence one.

$$
c \longrightarrow S(c) \longleftarrow p,
\qquad p\le n \Longrightarrow p\mid c \land p\mid S(c)
\Longrightarrow p\mid1.
$$

The theorem `prime_unbounded` has 4,595 nodes, depth 82 and 146 Cuts. Its full
84-command authored proof is embedded in the
<a href="theorem-atlas.html#theorem-prime_unbounded"><code>prime_unbounded</code> atlas card</a>.

## The trust path

<div class="pa-flow-bridge" role="figure" aria-label="From mathematical dependency graph to kernel-checked theorem">
  <div class="pa-flow-node"><strong>Authored scripts</strong><br><small>readable tactic bodies</small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong>Nested Cuts</strong><br><small>complete dependency proofs embedded</small></div>
  <div class="pa-flow-arrow" aria-hidden="true">→</div>
  <div class="pa-flow-node"><strong>Empty-context kernel check</strong><br><small>original closed formula</small></div>
</div>

The checked FTA and `prime_unbounded` use only PA1–PA6 and ordinary induction;
their audits find no double-negation elimination. The object language gained
no primitive division, remainder, gcd, prime, list, product or factorization
symbol.

## Four synchronized views

One theorem name identifies the same object in four places:

1. the executable `TheoremSpec` and checked certificate;
2. the generated snapshot and dependency graph;
3. its card and narrative links in this Jupyter Book;
4. its atomic Obsidian vault note.

The current synchronized surfaces are:

- [native theorem source](https://github.com/nasqret/vietnam2026/blob/5fff3eab2a7599035a6833c52b658da118f4a20c/peano-lab/py/peano_lab/library/theorems.py);
- [checked-theorem snapshot](https://github.com/nasqret/vietnam2026/blob/5fff3eab2a7599035a6833c52b658da118f4a20c/artifacts/peano-library/catalog-v1.json);
- [research catalog](https://github.com/nasqret/vietnam2026/blob/5fff3eab2a7599035a6833c52b658da118f4a20c/research/arithmetic-library/catalog.json);
- [arithmetic vault map](https://github.com/nasqret/vietnam2026/blob/5fff3eab2a7599035a6833c52b658da118f4a20c/vault/moc/arithmetic-library-moc.md);
- [deterministic training corpus](https://github.com/nasqret/vietnam2026/tree/5fff3eab2a7599035a6833c52b658da118f4a20c/peano-lab/corpus).

There is exactly one deliberately unproved catalog boundary: the conventional
integer-coefficient Bézout interface. Peano Lab quantifies only over naturals.
The separately named balanced four-natural Bézout theorem is checked and is
the interface used by Gauss cancellation and Euclid's lemma.

## Start reading

Continue with the {doc}`guided route <guided-tour>`. It alternates intuition,
exact formulas, proof anatomy and immutable proof links. When you want to move
backward or forward through the dependency DAG, open the
{doc}`theorem atlas <theorem-atlas>` and focus the theorem you are reading.
