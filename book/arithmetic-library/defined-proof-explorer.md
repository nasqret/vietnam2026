# The definition-aware proof explorer

The definition-aware explorer is a parallel reading edition of the same
557-theorem quadratic-reciprocity corpus. It gives recurring formulas short,
linked names—such as `Dvd(d,n)`, `Prime(p)`, and `ModEq(m,a,b)`—without changing
the explicit theorem statements, tactic scripts, proof terms, or kernel.

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
  <a class="btn btn-outline-primary" href="../_static/pa-proof-explorer/defined/graph.html?target=PA00FW">
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

## Two synchronized views of one proof

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

```{admonition} Proof paths contain theorem edges only
:class: note
Critical paths and prerequisite cones are computed exclusively from the
frozen theorem dependency adjacency. Purple notation edges never shorten,
extend, or otherwise participate in a proof path.
```

<iframe
  src="../_static/pa-proof-explorer/defined/graph.html?target=PA00FW"
  title="Mixed theorem and conservative-definition graph"
  width="100%"
  height="980"
  loading="lazy">
  <p>
    Your browser does not support embedded pages.
    <a href="../_static/pa-proof-explorer/defined/graph.html?target=PA00FW">Open the mixed graph directly.</a>
  </p>
</iframe>

## Trust boundary and provenance

Persistent `PA` tags identify theorem pages; persistent `PD` tags identify
definitions. The generated corpus records the explicit-corpus digest, the
definition-edition identity, source locations, expansion hashes, and all typed
edges. None of those identifiers grants theorem authority. Public admission
and candidate status remain exactly those of the {doc}`explicit proof explorer
<proof-explorer>`.

For the core grammar and accepted proof constructors, read the
{doc}`PA language reference <../peano/language-reference>` and
{doc}`axioms and proof rules <../peano/axioms-and-rules>`. For theorem-only
routes, use the {doc}`dependency graph <dependency-graph>`.
