# The theorem dependency graph

The interactive dependency graph answers two complementary questions: *what
does this theorem ultimately depend on?* and *which later theorems use it?*
It opens below with quadratic reciprocity, permanent tag **PA00FW**, selected
as the target.

```{admonition} Alpha QR slice, not the complete library graph
:class: note
These 557 nodes are exactly the reciprocity campaign slice: 241 Stable
prerequisites and 316 Alpha-only specifications. The complete Stable catalog
has 432 rows, of which 191 are outside this graph. Stable union this slice has
748 distinct theorem names, while canonical Alpha has 885; other Alpha layers
such as K3B are separate until
the unified Alpha explorer is generated. See {doc}`Alpha and
Stable library editions <library-editions>`.
```

```{admonition} The graph records proof structure, not extra axioms
:class: important
Every vertex is a theorem specification in the quadratic-reciprocity closure.
The 48 theorem roots have no **theorem** prerequisites inside this corpus; they
are not axioms. The underlying first-order language, PA1--PA6, induction, and
the kernel proof rules are documented separately in the
{doc}`PA foundations <../peano/axioms-and-rules>`.
```

<div class="pa-dashboard-metrics" aria-label="Quadratic-reciprocity dependency graph metrics">
  <div><strong>557</strong><span>theorem nodes</span></div>
  <div><strong>1,787</strong><span>direct dependency edges</span></div>
  <div><strong>45</strong><span>dependency layers</span></div>
  <div><strong>48</strong><span>theorem roots</span></div>
</div>

<p>
  <a class="btn btn-primary" href="../_static/pa-proof-explorer/graph.html?target=PA00FW&amp;view=neighborhood&amp;edges=focus">
    Open the full graph · PA00FW
  </a>
  <a class="btn btn-outline-primary" href="../_static/pa-proof-explorer/tag/PA00FW.html">
    Open the PA00FW proof page
  </a>
</p>

<iframe
  src="../_static/pa-proof-explorer/graph.html?target=PA00FW&amp;view=neighborhood&amp;edges=focus"
  title="Native PA theorem dependency paths to quadratic reciprocity"
  width="100%"
  height="980"
  loading="lazy">
  <p>
    Your browser does not support embedded pages.
    <a href="../_static/pa-proof-explorer/graph.html?target=PA00FW&amp;view=neighborhood&amp;edges=focus">Open the dependency graph directly.</a>
  </p>
</iframe>

## Reading an arrow

An arrow always runs from a prerequisite to the theorem that uses it:

$$
A \longrightarrow B
\qquad\text{means}\qquad
B\text{ declares }A\text{ as a direct prerequisite.}
$$

Following arrows therefore moves forward through the library. Moving against
them traces a proof back toward its premises. A direct edge is different from
a transitive dependency: selecting **Complete prerequisite cone** displays all
ancestors, while **Direct neighborhood** displays only the adjacent nodes.
The dashed edge style marks a declared packaging prerequisite whose theorem
name does not occur literally in the later tactic body; it is still a real
declared dependency.

Click a node to select it. Use its north-east arrow or the details-panel link
to open the exact theorem page.
The graph can show a chosen path, a start-to-target corridor, either transitive
cone, or the entire corpus. The ordinary linked list beneath the canvas is a
text alternative for the selected route.

The initial view is intentionally sparse: it shows the target's direct
neighborhood and draws only its incident arrows plus the chosen premise path.
The **Arrows** control can hide all arrows or restore every exact direct arrow.
This changes rendering only—the details panel and `api/graph.json` always retain
the complete relation. Views above 160 nodes switch to compact clickable marks,
so the full corpus remains navigable without constructing thousands of labelled
SVG cards.

## Short and critical premise chains

The two automatic routes intentionally answer different questions.

| Route | Exact meaning | PA00FW route |
|---|---|---:|
| **Short premise chain** | Fewest edges from any theorem root, with a deterministic admission-order tie-break | 4 vertices / 3 edges |
| **Critical/deepest premise chain** | A dependency-depth witness reaching the target's maximum layer | 45 vertices / 44 edges |

The short route is not a compressed proof: it follows only one premise at
each junction and leaves the theorem's other prerequisites off the displayed
chain. The critical route is likewise one depth witness, not a claim that its
lemmas are the uniquely important ones. To see everything required by a
theorem, use its complete prerequisite cone.

The canonical short route is
`mod_eq_symm` (**PA003L**) $\to$
`odd_prime_gauss_eisenstein_orientation_data_exists` (**PA00D7**) $\to$
`distinct_odd_primes_gauss_eisenstein_data_exists` (**PA00FG**) $\to$
`quadratic_reciprocity_combined` (**PA00FW**). It is short because these are
direct edges, not because the intermediate theorems have small proofs.

For PA00FW there are **101,278 distinct theorem-root-to-target premise
chains**. It is the unique terminal of this closure and all other 556 nodes
are its ancestors. One representative mathematical spine is

```text
arithmetic and balanced Bézout
  → Gauss cancellation
  → β/CRT sequence machinery
  → finite injectivity, omission, and prime pair-order
  → Wilson's theorem
  → Euler's criterion
  → Gauss's lemma
  → Gauss–Eisenstein data · PA00FG
  → quadratic reciprocity · PA00FW
```

That display is an orientation guide through the subject. The interactive
graph and its generated JSON, rather than this editorial summary, are the
exact dependency record.

## Release membership and proof evidence remain visible

Node color and the details panel preserve the same status distinctions as the
{doc}`proof explorer <proof-explorer>`. The live closure contains 241 Stable
theorems and 316 Alpha-only specifications. Canonical Alpha evidence partitions
those 316 rows into 314 body-checked-only rows, the Alpha-closed
`mod_eq_add_cancel_left` overlap, and the pending root. The older QR corpus
still labels that overlap `candidate_body_checked`; its HA empty-context
receipt is the separate evidence that strengthens the canonical status.
`bounded_mod_inverse_unique` is the one exact-compatible
Stable migration in this slice; its Alpha-source specification and owner
remain recorded as provenance, but its reachable-graph scope is Stable.
A `candidate_body_checked` node has an independently kernel-checked
dependency-curried body, but is not thereby promoted to Stable. PA00FW is
`pending_layered_closure`: its complete layered closed certificate still has
to pass the WMI and Stable-promotion gates. The current graph receipt is
`26017364ea943c4ed51a4a83f63ff0cd56b0de3686f0e0b458e7548ee84b1253`;
the 557 nodes, 1,787 edges and 45 layers are unchanged.

The embedded generated pages remain a campaign-oriented explorer, so they
retain historical `public`/`candidate` wording and the current 241/316 badge
split. Those labels describe the QR slice, not canonical closure evidence. A
path, graph hash, or green body-check
badge supplies provenance, never an axiom or theorem authority.

For the exact statements and numbered tactic scripts, use the
{doc}`native PA proof explorer <proof-explorer>`. For the language and trust
boundary, continue with {doc}`Language, notation, and trust
<language-and-trust>`.
