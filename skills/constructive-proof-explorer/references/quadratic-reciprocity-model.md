# Canonical Quadratic Reciprocity proof-family model

## Authoritative reference surfaces

Inspect the current repository rather than treating this document as a static
copy of the production design:

- `deploy/proofs/quadratic-reciprocity.html`: canonical public family entrance.
- `deploy/proofs/bertrand-postulate.html`: second established flagship.
- `deploy/proofs/proofs.css`: only public family landing-page stylesheet.
- `book/_static/pa-proof-explorer/`: original exact proof-reading surface.
- `book/_static/pa-proof-explorer/defined/`: original definition-aware reading
  surface, searchable index, graph, theorem pages, and definition pages.
- `scripts/constructive_proof_explorer_template.py`: reusable canonical
  family-landing renderer for newly generated campaigns.
- `scripts/build_constructive_frontier_explorer.py`: historical family
  implementation already conforming to the flagship design.
- `scripts/build_constructive_next_layer_explorer.py` and
  `scripts/build_constructive_advanced_layer_explorer.py`: historical
  Alpha-v20/v21 families using the same canonical renderer while preserving
  their exact first-admission proof bundles and honest open-milestone caveats.
- `scripts/build_constructive_transport_layer_explorer.py`: concrete example
  of three independently authenticated families sharing the canonical renderer.
- `scripts/build_constructive_milestone_closure_explorer.py`: complete example
  of a new immutable three-family release using the shared canonical renderer,
  exact closed-milestone roots, independently compiled Lean evidence, and
  additive reviewed definitions.
- `scripts/constructive_milestone_closure_definitions.py`: example of hygienic
  definition extension that reuses established identities instead of silently
  duplicating an existing mathematical concept.
- `scripts/constructive_definition_graph.py`: reviewed global conservative
  definition registry and blueprint/signature matching.
- `book/_static/constructive-grand-campaign/campaign.json` and
  `definitions.json`: mathematical milestones, domain/family links, and the
  audited global definition DAG.

## Required public family entrance

Each `proofs/<slug>/index.html` is a true sibling of Quadratic Reciprocity, not
a differently styled dashboard. Use `render_canonical_family_landing(...)` and
retain these semantic and visual anchors:

```html
<body class="family-page <slug>-page">
  <header class="family-hero">
    <div class="shell">
      <nav class="crumbs">…</nav>
      <p class="eyebrow">…</p>
      <h1>…</h1>
      <p class="formula">…</p>
      <p class="lede">…</p>
      <div class="hero-actions">…</div>
    </div>
  </header>
  <main class="shell family-main">
    <section class="view-grid">
      <article class="view-card featured">…</article>
      <article class="view-card">…</article>
      <article class="view-card">…</article>
    </section>
    <section class="release-note">…</section>
  </main>
</body>
```

The three cards open the definition-aware edition, exact fully expanded
edition, and focused prerequisite graph. Hero actions open the selected mixed
graph, root theorem, and corresponding campaign milestone. Include correct
description/OpenGraph/canonical metadata, a list of genuine checked roots,
exact theorem/edge/definition/tactic counts, immutable bundle evidence, and
honest open-milestone caveats.

All HTML navigation uses the first twelve hexadecimal characters of the current
sealed Alpha catalog SHA-256 as its `v` revision. Preserve the root theorem's
stable tag. For focused mixed graphs include meaningful `target`, `view`,
`definitions`, and `edges` query arguments. Ensure HTML-escaped `&amp;`
separators and navigation depth are correct at every page.

## Required generated branch topology

At minimum, each campaign generator publishes:

```text
<slug>/index.html
<slug>/api/corpus.json
<slug>/explorer/index.html
<slug>/explorer/tag/<TAG>.html
<slug>/explorer/defined/index.html
<slug>/explorer/defined/graph.html
<slug>/explorer/defined/api/graph.json
<slug>/explorer/defined/tag/<TAG>.html
<slug>/explorer/defined/definition/<DEFINITION-ID>.html
```

Reuse the existing exact/defined JS and CSS assets and their hash pins. The
definition-aware dashboard keeps `pa-defined-proof-site`, `pd-header`,
`pd-controls`, `pd-results`, searchable theorem/definition entries, and the
original graph controls. The graph page keeps `data-defined-graph`,
`data-graph-svg`, and `window.PA_DEFINED_GRAPH`; avoid browser-incompatible
assignment to getter-only SVG properties such as `href`.

Provide actual verified theorem statements, tactic scripts, proof dependencies,
source references, provenance, print support, and complete root/detail pages.
Do not substitute prose summaries or percentages for real proof artifacts.

## Definition and evidence boundaries

Every reviewed definition is a `DefinitionSpec` over the unchanged strict
Heyting-arithmetic signature. Preserve old `PD...`/`ND...` identifiers, allocate
new stable IDs only for genuinely new definitions, reject shadowing/capture,
verify arity/signature and parsed AST equality, and order the definition DAG by
actual prerequisites. Blueprint aliases require explicit compatible argument
alignment; incompatible homonyms never inherit proof authority.

Mixed graph edges have exactly three distinct meanings:

- `proof_dependency`: actual theorem proof prerequisite.
- `uses_definition`: theorem statement uses a conservative abbreviation.
- `definition_uses_definition`: abbreviation expands through another one.

Only proof-dependency edges determine theorem reachability, proof paths, and
critical paths. A notation arrow is never a mathematical proof premise.

Authenticate each published row against the sealed current catalog and its
actual dependency-closed kernel-checked proof bundle. Independently check Lean
receipts where claimed. Preserve first-admission provenance when updating
historical families to a later current Alpha edition. Explicitly distinguish
verified partial components from any larger blueprint goal that remains open.

## Regression and publication checklist

Extend focused generator tests to compare each new entrance structurally with
the Quadratic Reciprocity reference, pin all stable root/definition tags,
verify graph categories and AST-equivalence, authenticate catalog/bundle
digests, check current-versus-first Alpha provenance, test honest open/closed
milestone wording, and exercise every relative atlas/explorer link.

Regenerate the family snapshot and its deterministic manifest. Run the global
definition graph, grand campaign, browser-shell, deployment-contract, and
public-site tests relevant to the changed surfaces. If the user requests
publication, stage the existing proof website and immutable Peano application,
verify their hashes, then use only the repository's established dedicated
faculty-server deployment paths; publication is not implicit in this skill.
