# The foundational arithmetic library

This part of the book is the readable front end to a native first-order Peano
arithmetic library. It begins with ordinary equality and semiring laws, builds
division, relational gcd, balanced Bézout, Gauss cancellation and Euclid's
lemma, then constructs finite factor sequences and their products using
Gödel-β codes. The endpoint is a checked, β-coded Fundamental Theorem of
Arithmetic.

```{admonition} Two cumulative editions
:class: tip
The **Stable** library contains **432 closed native theorems**, including
factorization existence, extensional uniqueness, their combined FTA, and a
constructive theorem producing a prime above every supplied bound. The newest
Alpha quadratic-reciprocity campaign includes parity, constructive
residue decision, finite folds, factorial and power algebra, modular units,
sign and half-range bridges, β swap/reindex, finite pigeonhole, replacement
balance, and exact swap-last product invariance. Twenty-five strict-HA entries
now expose canonical remainder, congruence, bounded modular inverses, relational
gcd/LCM compatibility, LCM existence and uniqueness, and the gcd--LCM product
law. The exact 23-row generalized-CRT dependency closure is now Stable: it
covers the all-modulus solvability criterion, classification modulo a
relational LCM, the zero/nonzero canonical boundary, certified obstruction,
and raw-input total decision. New reviewed layers enter **Alpha** first and
move to Stable only after closure, compilation, dependency, resource, and
release audits. Sealed Alpha v2 adds seventeen body-checked K3C rows for
valid list codes, membership, unique in-range lookup, extensional code
equality, and unique outer-cell decomposition. Sealed Alpha v3 adds the first
twenty-one Bertrand rows, and sealed Alpha v4 adds forty-two Round-2 rows for
exact valuation multiplication, integer envelopes, ceiling/floor-square
arithmetic, and the quotient budget. Sealed Alpha v5 preserves that complete
965-row ledger and appends seven body-checked `FactorialVal` rows. Sealed
Alpha v5 therefore has 972 rows, sealed Alpha v6 has 993, sealed Alpha v7 has
1,017, sealed Alpha v8 has 1,055, sealed Alpha v9 has 1,076, and sealed Alpha
v10 has 1,085. Current Alpha v11 preserves the entire v10 ledger and appends
thirty-eight body-checked
Bertrand rows in exact 20+18 microbatches. They close the dependency chain from
duplicate-free products and interval Choose bounds through
`primorial_le_four_pow` and the first B5 prime-support rows. See
{doc}`Alpha and Stable library editions
<library-editions>` for the exact scopes and lifecycle.
```

<div class="pa-dashboard-metrics" aria-label="Alpha and Stable arithmetic library metrics">
  <div><strong>432</strong><span>Stable theorems</span></div>
  <div><strong>1,123</strong><span>Alpha v11 theorems</span></div>
  <div><strong>570</strong><span>Alpha checked-use rows</span></div>
  <div><strong>691</strong><span>Alpha-only rows</span></div>
</div>

The generated Stable snapshot has ordered root
`4d02dc439d53533e8992a471b26ee34059fb6001f822041e42c56b2cc0a7a079`.
Every entry is reconstructed from its authored script and checked from the
empty context. Names, summaries and hashes organize the library; none of them
grant proof authority. Its graph has **1,185** direct dependency edges; the
Book exposes **432** theorem cards, while the synchronized vault contains
**531** notes and **5,377** resolved links.

The current additive Alpha v11 graph has 1,123 theorems, 3,482 direct edges,
and 45 dependency layers. Its mixed evidence is intentional: 570 rows have
complete checked-use evidence, while 552 body-only rows and one pending row
remain visible without being treated as empty-context facts. Stable remains
432; the 885-row Alpha v1, 902-row Alpha v2, 923-row Alpha v3, 965-row Alpha
v4, 972-row Alpha v5, 993-row Alpha v6, and 1,017-row Alpha v7 parents remain
sealed; Alpha v8 remains sealed at 1,055, Alpha v9 remains sealed at 1,076,
and Alpha v10 remains sealed at 1,085. The
exact contract and opt-in API are on the {doc}`edition page
<library-editions>`.

Alpha v11 retains the Alpha-v10 interval-split tranche, then adds the
dependency-closed duplicate-free, Primorial/Choose interval, central-upper,
Primorial-four-power, and central-prime-support tranches.
The evidence partition is exactly 432 `stable_closed`, 138 `alpha_closed`,
552 `body_checked`, and one `pending_layered_closure`; checked use remains
570. Bertrand's postulate itself is not yet proved: B4's Primorial bound is now
available, but the five-range no-prime central upper bound, large-input
contradiction, finite coverage, and constructive capstone remain.

## The mathematical metro map

The exact dependency graph has 432 vertices and 1,185 edges and is useful to machines, but a
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
[`dependency-graph.mmd`](https://github.com/nasqret/vietnam2026/blob/ff3d0ebd440d52f3df12dbae765fe7acc53ee6c5/artifacts/peano-library/dependency-graph.mmd).
The {doc}`Stable theorem atlas <theorem-atlas>` gives a readable local
neighborhood instead of attempting to draw all 1,185 edges at once. The
{doc}`Alpha QR proof explorer <proof-explorer>` adds permanent theorem tags,
numbered tactic-line targets, and the larger quadratic-reciprocity campaign
slice. It is not the complete Alpha or Stable catalog.
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
| understand the two release editions | {doc}`Alpha and Stable library editions <library-editions>` | canonical counts, checked-use boundary, promotion lifecycle, and graph legend |
| understand the mathematics | {doc}`Guided route from zero to FTA <guided-tour>` | the focused theorem links inside each stage |
| inspect every Stable proof | {doc}`Stable theorem atlas <theorem-atlas>` | exact statements, complete scripts, dependencies and dependents |
| follow the Alpha QR slice line by line | {doc}`Alpha QR proof explorer <proof-explorer>` | permanent tags, linked lemma references, informal outlines and source receipts |
| read expanded formulas through linked names | {doc}`Definition-aware proof explorer <defined-proof-explorer>` | persistent `PD` expansions, exact native replay lines, and the unchanged theorem status |
| curate the next conservative edition | {doc}`Curating the next conservative edition <curation>` | P0/P1/P2 definitions, API completeness, and paired-source gates |
| see how theorems depend on one another | {doc}`Interactive dependency graph <dependency-graph>` | short and critical premise chains, route corridors and complete prerequisite cones |
| understand soundness | {doc}`Language, notation, and trust <language-and-trust>` | {doc}`Self-contained proof sharing <proof-sharing>` |
| study division and congruence | {doc}`Divisibility and subtraction-free congruence <divisibility-and-congruence>` | {doc}`GCD and balanced Bézout <gcd-and-bezout>` |
| study encoded lists and lookup | {doc}`K3B Alpha: cell histories and extensional lookup <cell-history-and-lookup>` | the compact Alpha/Stable graph, exact proof sources, and WMI receipt |
| use list validity and membership | {doc}`K3C Alpha: valid lists, membership, and semantic lookup <list-validity-and-membership>` | the seventeen-row interface, exact body receipts, and append/restriction gate |
| study primes and factorization | {doc}`Primes and unique factorization <primes-and-factorization>` | the FTA and `prime_unbounded` cards in the atlas |
| follow the reciprocity campaign | {doc}`Quadratic reciprocity campaign <quadratic-reciprocity>` | parity, residue-decision, and finite-fold cards in the atlas |
| follow the Bertrand campaign | {doc}`Bertrand's postulate campaign <bertrand-campaign>` | constructive interval search, valuations, the central-binomial route, and exact risk gates |
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

- [native theorem source](https://github.com/nasqret/vietnam2026/blob/ff3d0ebd440d52f3df12dbae765fe7acc53ee6c5/peano-lab/py/peano_lab/library/theorems.py);
- [checked-theorem snapshot](https://github.com/nasqret/vietnam2026/blob/ff3d0ebd440d52f3df12dbae765fe7acc53ee6c5/artifacts/peano-library/catalog-v1.json);
- [research catalog](https://github.com/nasqret/vietnam2026/blob/ff3d0ebd440d52f3df12dbae765fe7acc53ee6c5/research/arithmetic-library/catalog.json);
- [arithmetic vault map](https://github.com/nasqret/vietnam2026/blob/ff3d0ebd440d52f3df12dbae765fe7acc53ee6c5/vault/moc/arithmetic-library-moc.md);
- [deterministic training corpus](https://github.com/nasqret/vietnam2026/tree/ff3d0ebd440d52f3df12dbae765fe7acc53ee6c5/peano-lab/corpus).

There is exactly one deliberately unproved catalog boundary: the conventional
integer-coefficient Bézout interface. Peano Lab quantifies only over naturals.
The separately named balanced four-natural Bézout theorem is checked and is
the interface used by Gauss cancellation and Euclid's lemma.

## Start reading

Continue with the {doc}`guided route <guided-tour>`. It alternates intuition,
exact formulas, proof anatomy and immutable proof links. When you want to move
backward or forward through the dependency DAG, open the
{doc}`theorem atlas <theorem-atlas>` and focus the theorem you are reading.
