# The definition-aware proof explorer

The definition-aware explorer is a parallel reading edition of the same
557-theorem quadratic-reciprocity corpus. It gives recurring formulas short,
linked names—such as `Dvd(d,n)`, `Prime(p)`, and `ModEq(m,a,b)`—without changing
the explicit theorem statements, tactic scripts, proof terms, or kernel.

```{admonition} Alpha QR slice
:class: note
This is not a second release edition and not the whole Alpha library. It is the
definition-aware view of the same 557-node QR slice: 241 Stable prerequisites
and 316 Alpha-only specifications. The complete Stable catalog has 432 rows,
the canonical Alpha catalog has 885, and {doc}`K3B
<cell-history-and-lookup>` is a separate focused Alpha lens. See
{doc}`Alpha and Stable library editions <library-editions>` for the canonical
scope distinction.
```

```{admonition} Defined notation is not kernel syntax
:class: important
Every purple token on these pages is produced by an untrusted, conservative
presentation layer. Before replay, the compiler expands the theorem statement
and every compacted local proposition back into the ordinary PA formula
language. The unchanged kernel sees only that expansion. A definition page is
therefore neither an axiom nor a theorem nor a new predicate constant.
```

<p>
  <a class="btn btn-primary" href="../_static/pa-proof-explorer/defined/index.html">
    Open the definition-aware explorer
  </a>
  <a class="btn btn-outline-primary" href="../_static/pa-proof-explorer/defined/graph.html?target=PA00FW&amp;view=neighborhood&amp;definitions=selected&amp;edges=focus">
    Draw the mixed graph · PA00FW
  </a>
  <a class="btn btn-outline-primary" href="../_static/pa-proof-explorer/index.html">
    Open the exact explicit edition
  </a>
</p>

<iframe
  src="../_static/pa-proof-explorer/defined/index.html"
  title="Definition-aware native Peano arithmetic proof explorer"
  width="100%"
  height="920"
  loading="lazy">
  <p>
    Your browser does not support embedded pages.
    <a href="../_static/pa-proof-explorer/defined/index.html">Open the definition-aware explorer directly.</a>
  </p>
</iframe>

## What the second edition changes

The complete elaboration pass covers all 557 theorem specifications and all
27,491 tactic lines. Of the 557 statements, 506 contain at least one selected
definition. Of the 1,839 proposition-bearing `have` or `suffices` commands,
1,275 become definition-aware.

| Surface measured | Fully expanded text | Defined edition | Reduction |
|---|---:|---:|---:|
| all theorem statements | 2,457,096 characters | 107,386 characters | 95.63% |
| all local `have`/`suffices` propositions | 1,971,403 | 111,519 | 94.34% |
| longest theorem statement (<a href="../_static/pa-proof-explorer/defined/tag/PA00EH.html"><code>PA00EH</code></a>) | 82,377 | 1,759 | 97.86% |
| largest expanded `have` command (<a href="../_static/pa-proof-explorer/defined/tag/PA00FE.html#proof-line-0015"><code>PA00FE</code>, line 15</a>) | 36,497 | 642 | 98.24% |

The longest remaining defined local proposition is 963 characters
(<a href="../_static/pa-proof-explorer/defined/tag/PA00EX.html#proof-line-0026"><code>PA00EX</code>, line 26</a>);
its full `have` command is 988 characters.

The quadratic-reciprocity endpoint itself is now displayed as:

```text
∀ p. ∀ q. Prime(p) → Prime(q) → ¬p = q → Odd(p) → Odd(q) →
  (Mod4One(p) ∨ Mod4One(q) →
     (QRes(p,q) ∧ QRes(q,p)) ∨ (¬QRes(p,q) ∧ ¬QRes(q,p))) ∧
  (Mod4Three(p) ∧ Mod4Three(q) →
     (QRes(p,q) ∧ ¬QRes(q,p)) ∨ (¬QRes(p,q) ∧ QRes(q,p)))
```

This is the same parsed formula as the expanded endpoint, not a replacement
theorem. Open <a href="../_static/pa-proof-explorer/defined/tag/PA00FW.html"><code>PA00FW</code></a>
to move from any purple predicate call to its expansion and back to the exact
native statement.

The persistent inventory, including raw overlapping occurrence counts and
source provenance, is recorded in
[`pa-proof-definitions.json`](https://github.com/nasqret/vietnam2026/blob/agent/quadratic-reciprocity-campaign/research/arithmetic-library/pa-proof-definitions.json)
and its [human-readable audit](https://github.com/nasqret/vietnam2026/blob/agent/quadratic-reciprocity-campaign/research/arithmetic-library/defined-edition.md).

## The forty persistent definitions

| Mathematical layer | Linked definition pages |
|---|---|
| order and divisibility | <a href="../_static/pa-proof-explorer/defined/definition/PD0001.html"><code>Le</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0002.html"><code>Lt</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0003.html"><code>Dvd</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0007.html"><code>DivRem</code></a> |
| primes, gcd, and coprimality | <a href="../_static/pa-proof-explorer/defined/definition/PD0004.html"><code>Prime</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0005.html"><code>Coprime</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0006.html"><code>IsGCD</code></a> |
| congruence, parity, and small residues | <a href="../_static/pa-proof-explorer/defined/definition/PD0008.html"><code>ModEq</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0009.html"><code>Even</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0010.html"><code>Odd</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0011.html"><code>Mod4One</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0012.html"><code>Mod4Three</code></a> |
| finite coding and folds | <a href="../_static/pa-proof-explorer/defined/definition/PD0013.html"><code>BetaAt</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0014.html"><code>Product</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0015.html"><code>Sum</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0016.html"><code>AllBits</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0017.html"><code>BitCount</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0018.html"><code>Range</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0019.html"><code>Repeat</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0020.html"><code>Pow</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0023.html"><code>Factorial</code></a> |
| quadratic residues | <a href="../_static/pa-proof-explorer/defined/definition/PD0021.html"><code>QRes</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0022.html"><code>BoundedQRes</code></a> |
| finite maps and factorization invariants | <a href="../_static/pa-proof-explorer/defined/definition/PD0024.html"><code>BoundedPrefix</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0025.html"><code>InjectivePrefix</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0026.html"><code>SurjectivePrefix</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0027.html"><code>ContainsPrefix</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0028.html"><code>AllPrime</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0029.html"><code>Sorted</code></a> |
| modular units and inverse maps | <a href="../_static/pa-proof-explorer/defined/definition/PD0030.html"><code>UnitResidue</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0031.html"><code>BalancedInverse</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0032.html"><code>BoundedNonzeroInverse</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0033.html"><code>ScaledInverse</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0034.html"><code>ScaledFixedPoint</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0035.html"><code>SuccessorInverse</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0036.html"><code>InverseIndex</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0037.html"><code>InversePrefix</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0038.html"><code>ScaledInverseIndex</code></a> · <a href="../_static/pa-proof-explorer/defined/definition/PD0039.html"><code>ScaledInversePrefix</code></a> |
| finite division traces | <a href="../_static/pa-proof-explorer/defined/definition/PD0040.html"><code>DivisionPrefix</code></a> |

`AllPrime` and `Sorted` have no whole-schema occurrence in this particular QR
closure, but they are retained because the same notation registry also serves
the factorization and FTA development. Three broader authoring composites—
`PermutationPrefix`, `BalancedBezout`, and `CanonicalPF`—are also accepted by
the opt-in parser, but remain outside the forty persistent graph nodes in this
frozen edition.

## Three synchronized views of one proof

Every theorem page presents three related objects:

1. The compact theorem statement, with every definition occurrence linked to
   its persistent `PD` page.
2. The definition-aware tactic body. Only proposition bodies introduced by
   `have` and `suffices` are compacted; ordinary tactic commands remain exact.
3. The expanded native statement and an expandable **Exact native replay
   line** beneath every changed local command.

The adapter records a SHA-256 receipt for each exact explicit statement and
tactic line. It also checks that expanding each compact formula reconstructs
the same parsed PA abstract syntax tree. The explorer validates those receipts
against the frozen explicit corpus before it writes any page.

This makes back-and-forth reading deliberate: open a purple formula token to
study its expansion, follow a theorem token to its formal proof, and expand the
native replay line whenever the abstraction hides a detail you want to inspect.

## Authoring with the notation

The notation is also available through an explicit compiler API. For example,

```python
from peano_lab.library.defined_edition import (
    DefinedTheoremSpec,
    compile_defined_spec,
)

surface = DefinedTheoremSpec(
    "dvd_self_readable",
    "forall n. Dvd(n,n)",
    ("mul_one",),
    ("intro n", "exists 1", "symm", "apply mul_one"),
    "Every natural number divides itself.",
)
native = compile_defined_spec(surface)
```

`native` is an ordinary `TheoremSpec`: `Dvd` has already disappeared from its
statement, and the normal proof engine and kernel receive only the expanded PA
formula. The core parsing entry points still reject defined calls; authors opt
in by using `parse_defined_formula*` or this compiler.

## Reading the mixed dependency graph

The mixed graph contains two kinds of vertices and two logically different
kinds of arrows:

| Shape | Meaning |
|---|---|
| Rounded theorem node | One theorem in the exact PA corpus |
| Purple hexagon | A conservative display definition |
| Solid proof arrow $A\to B$ | Theorem $A$ is a direct prerequisite of theorem $B$ |
| Purple notation arrow $T\to D$ | The statement or a local proof proposition of theorem $T$ uses definition $D$ |

Definition-to-definition arrows record that one readable expansion is phrased
using another definition. They describe notation structure, not proof
authority. The graph records statement and local-proposition occurrence counts
separately.

The mixed graph opens in a sparse neighborhood mode. It adds only the selected
node's definition closure and draws only the selected node's direct arrows plus
the theorem premise path. **Definitions** can be switched to off or to all
definitions used by the visible theorems; **Arrows** can be hidden or restored
in full. These controls suppress visual objects only. The selected-node panel
and typed graph API continue to expose every exact proof and notation relation.

```{admonition} Proof paths contain theorem edges only
:class: note
Critical paths and prerequisite cones are computed exclusively from the
frozen theorem dependency adjacency. Purple notation edges never shorten,
extend, or otherwise participate in a proof path.
```

<iframe
  src="../_static/pa-proof-explorer/defined/graph.html?target=PA00FW&amp;view=neighborhood&amp;definitions=selected&amp;edges=focus"
  title="Mixed theorem and conservative-definition graph"
  width="100%"
  height="980"
  loading="lazy">
  <p>
    Your browser does not support embedded pages.
    <a href="../_static/pa-proof-explorer/defined/graph.html?target=PA00FW&amp;view=neighborhood&amp;definitions=selected&amp;edges=focus">Open the mixed graph directly.</a>
  </p>
</iframe>

## Trust boundary and provenance

Persistent `PA` tags identify theorem pages; persistent `PD` tags identify
definitions. The generated corpus records the explicit-corpus digest, the
definition-edition identity, source locations, expansion hashes, and all typed
edges. None of those identifiers grants theorem authority. The generated
labels remain exactly those of the {doc}`explicit QR proof explorer
<proof-explorer>`, but they are campaign-local rather than canonical evidence:
the later HA receipt upgrades `mod_eq_add_cancel_left` to `alpha_closed` only
in the Alpha catalog. The historical labels are not a complete edition
catalog.

This edition gate validates source-to-source compilation for all 557
specifications; it is not a second closed-certificate replay or admission
claim. This notation view adds no proof evidence; canonical evidence, including
the later HA overlap upgrade, comes from the Alpha catalog and its receipts.

For the core grammar and accepted proof constructors, read the
{doc}`PA language reference <../peano/language-reference>` and
{doc}`axioms and proof rules <../peano/axioms-and-rules>`. For theorem-only
routes, use the {doc}`dependency graph <dependency-graph>`.

For the promotion rules, P0/P1/P2 tiers, API-completeness matrix, and paired
source release gates, continue to {doc}`Curating the next conservative edition
<curation>`.
