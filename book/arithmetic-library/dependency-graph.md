# The theorem dependency graph

The interactive dependency graph answers two complementary questions: *what
does this theorem ultimately depend on?* and *which later theorems use it?*
It opens below with quadratic reciprocity, permanent tag **PA00FW**, selected
as the target.

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
  <a class="btn btn-primary" href="../_static/pa-proof-explorer/graph.html?target=PA00FW">
    Open the full graph · PA00FW
  </a>
  <a class="btn btn-outline-primary" href="../_static/pa-proof-explorer/tag/PA00FW.html">
    Open the PA00FW proof page
  </a>
</p>

<iframe
  src="../_static/pa-proof-explorer/graph.html?target=PA00FW"
  title="Native PA theorem dependency paths to quadratic reciprocity"
  width="100%"
  height="980"
  loading="lazy">
  <p>
    Your browser does not support embedded pages.
    <a href="../_static/pa-proof-explorer/graph.html?target=PA00FW">Open the dependency graph directly.</a>
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

## Proof status remains visible

Node color and the details panel preserve the same status distinctions as the
{doc}`proof explorer <proof-explorer>`. The closure contains 240 public closed
theorems and 317 candidate specifications. A `candidate_body_checked` node
has an independently kernel-checked dependency-curried body, but is not thereby
publicly admitted. PA00FW is `pending_layered_closure`: its complete layered
closed certificate still has to pass the WMI and release admission gates.
A path, graph hash, or green body-check badge supplies provenance, never an
axiom or theorem authority.

For the exact statements and numbered tactic scripts, use the
{doc}`native PA proof explorer <proof-explorer>`. For the language and trust
boundary, continue with {doc}`Language, notation, and trust
<language-and-trust>`.
