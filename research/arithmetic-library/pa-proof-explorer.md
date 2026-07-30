# PA Proof Explorer: stable theorem pages and tactic-level navigation

## Purpose

The PA Proof Explorer is the reading interface for the complete native
quadratic-reciprocity dependency closure. It combines three ideas:

- the [Stacks Project tag system](https://stacks.math.columbia.edu/tags), in
  which a short identifier keeps naming the same mathematical item even when
  the item moves;
- [LeanBlueprint](https://github.com/PatrickMassot/leanblueprint), in which
  informal statements, formal declarations, dependency edges, and proof
  readiness are distinct pieces of metadata;
- a Peano-specific formal-line inspector, in which tactic keywords, explicit
  theorem references, PA axioms, and stable proof-line anchors are navigable.

The explorer is generated, not hand-copied. Its current scope is exactly the
557-node dependency closure of `quadratic_reciprocity_combined`: 240 public
ancestors and 317 unadmitted candidate ancestors, 1,791 direct edges, 45
dependency layers, and 27,491 authored PA tactic commands.

## Stable identity

Canonical theorem URLs use persistent opaque tags:

```text
_static/pa-proof-explorer/tag/PAxxxx.html
```

The authoritative name-to-tag registry is versioned separately from generated
pages. Existing tags are never recomputed from theorem order, filenames,
source lines, statements, or hashes. Those values can change while the
mathematical item remains the same. A future rename moves the old name to the
record's alias list; a removed or invalid result retains a tombstone explaining
why its tag no longer denotes a live theorem.

The theorem name remains a useful human alias. The permanent tag is the
citation identity.

## Truthful proof status

The explorer must not collapse several different facts into a single green
badge.

| Status | Meaning |
|---|---|
| `public` | The theorem is in the current Peano Lab registry and its ordinary empty-context replay is the public path. |
| `candidate_body_checked` | The dependency-curried tactic body has been independently kernel checked, but the closed dependency package is not publicly admitted. |
| `pending_layered_closure` | The QR candidate additionally awaits the exact WMI layered compile/check, mutation, capacity, and deterministic-replay gates. |
| `admitted` | Reserved for the future state after registry enrollment, release regeneration, and browser replay. |
| `tombstone` | The stable tag is retained, but the former item is no longer live; the reason must be recorded. |

In particular, `quadratic_reciprocity_combined` is not displayed as a public
theorem before the WMI and release gates pass. A graph hash, source hash,
dashboard page, or body receipt is provenance, never theorem authority.

## Canonical theorem record

Every generated theorem record contains:

```text
tag, name, aliases, statement, summary, status,
dependencies, dependents, layer, source,
statement/script/spec hashes,
formal_lines[{id, text, tactic, references}],
informal_proof{review_status, paragraphs, references},
transitive prerequisite/client counts
```

The forward dependency graph and reverse-dependent graph are exact inverses.
Every dependency resolves to a live tag. Generated JSON is timestamp-free and
byte-deterministic.

## Dependency paths

The graph orientation is always `dependency_to_dependent`: an edge `A -> B`
means that `B` declares `A` as a direct prerequisite. The 48 nodes with no
incoming theorem edge are called theorem roots or foundations in graph
metadata. They are roots only relative to this theorem corpus, not additional
PA axioms; the separate foundations prelude owns the language, PA1--PA6,
induction, and proof rules.

The graph records 557 nodes, 1,791 direct edges, and 45 layers. Path arrays
include both endpoints and use deterministic admission-order/lexicographic
tie-breaking:

- `shortest_root_path` minimizes the number of edges from any theorem root;
- `foundation_path` is retained as an alias of `shortest_root_path`;
- `critical_root_path` is a dependency-depth witness reaching the node's
  layer;
- `root_path_count` counts all directed theorem-root-to-node paths.

These are individual premise chains, not certificates and not substitutes for
the full ancestor set. In particular, PA00FW has a four-node shortest path, a
45-node critical path, and 101,293 root-to-target paths. Its readable critical
spine passes through arithmetic/Bézout and Gauss cancellation, β/CRT sequence
machinery, finite injectivity and omission, prime pair-order, Wilson, Euler's
criterion, Gauss's lemma, and PA00FG. That spine is representative; the graph's
complete prerequisite cone is the exact view of all required ancestors.

## Formal-line linking rule

Line linking is syntax-aware. It does not replace every token that happens to
equal a theorem somewhere in the global corpus.

For a theorem body, a proof-name token is linked only when it is one of that
theorem's declared direct dependencies and occurs in a theorem-accepting
position of `specialize`, `forall_elim`, `apply`, `exact`, `cases`, `rewrite`,
or `simp`. PA1--PA6 link to the foundations page. The first tactic token links
to the tactic reference. Local hypotheses remain plain local names.

Across the present closure, this identifies 8,557 explicit dependency-token
occurrences. Seven of the 1,791 declared edges are packaging prerequisites
that do not occur literally in the later authored body. They remain visible
and clickable through the theorem's explicit dependency-import rows and
dependency panel; they must not be fabricated as tactic-line references.

Each authored command has a stable human line anchor such as
`#proof-line-0017`.
The source Python line is not used as the command identity because helper
functions, tuple concatenation, f-strings, and template transformations can
assemble one semantic PA script from several Python locations.

## Informal proof layer

Every page has an informal-proof section, but its review state is explicit.

- Curated mathematical explanations live in a separate persistent sidecar
  keyed by theorem tag or canonical name. Regeneration never overwrites them.
- Until a page receives curated prose, it displays a deterministic structural
  proof outline derived from its declared prerequisites and actual tactics.
  This is labelled generated, not silently presented as expert exposition.
- Informal references are validated against the tag registry.

The QR endpoint and major Gauss--Eisenstein bridge lemmas receive curated
explanations first. The long-term editorial goal is reviewed prose for all 557
pages, without holding back the complete formal navigation surface.

## Foundations

The foundations page is grounded directly in the native implementation and
links every use back to the relevant item. It includes:

- terms `x | 0 | S t | t+t | t*t`;
- formulas `t=t | bottom | implication | conjunction | disjunction | forall | exists`, with negation as implication to bottom;
- PA1--PA6 exactly as recognized by the checker;
- formula-specific induction as a proof rule, not a seventh arithmetic axiom;
- all current proof constructors, including contextual `Cut` as certificate
  sharing and DNE as a separately controlled classical extension;
- the surface tactics used by the QR proof, with operational explanations and
  links to the full Book chapters;
- the trust boundary: tactics and generators are untrusted; only the kernel's
  empty-context judgment grants theorem authority.

## Static delivery

The explorer is a generated static microsite copied with the Jupyter Book:

```text
book/_static/pa-proof-explorer/
  index.html
  graph.html
  foundations.html
  manifest.json
  api/corpus.json
  api/graph.json
  api/graph.schema.json
  tag/PAxxxx.html
  name/<canonical-name>.html
  assets/explorer.css
  assets/explorer.js
```

The Book contains ordinary chapters linking to and embedding the theorem
dashboard and dependency graph; the 557 theorem pages do not flood the Sphinx
sidebar. All pages remain
readable without JavaScript. JavaScript supplies progressive search, filters,
copy controls, and focus management without remote dependencies or HTML
injection.

For direct `file://` use, `graph.html` contains a deterministic, safely escaped
copy of the compact graph payload.  It is embedded in that page rather than
stored as another `_static/*.js` file, because Jupyter Book would otherwise
inject the million-byte data bundle into every narrative chapter.

`book/_static/pa-proof-explorer/` is the source-tree delivery root. Jupyter
Book copies it to `_build/html/_static/pa-proof-explorer/`, so deployed links
are relative to the Book base rather than site-root absolute. From a chapter
under `arithmetic-library/`, the graph link is therefore
`../_static/pa-proof-explorer/graph.html?target=PA00FW`; inside the microsite,
assets and API files remain relative to `graph.html`. The `target` query is
runtime selection state, not part of the filesystem path. Stable citations
continue to use `tag/PAxxxx.html`; a query-selected graph view does not replace
the permanent theorem URL.

## Future trace overlay

Static theorem metadata is sufficient for exact script and dependency
navigation. It is not sufficient to claim the goal and context before and
after each tactic, the exact PA3--PA6 rewrites selected by `simp`, or local
hypothesis lineage through branches.

Those views require genuine replay. A later WMI job may export a versioned
per-line trace overlay tied to the statement, script, dependency, graph, and
source hashes. The dashboard will treat a missing or stale trace as missing
evidence, never reconstruct it heuristically.

## Release gates

Before publication, the explorer must prove all of the following mechanically:

1. exact `557 / 1,791 / 45 / 27,491` topology and command counts;
2. exact `240 public / 317 candidate` status partition;
3. unique persistent tags and complete live-name coverage;
4. deterministic graph, corpus, manifest, tag pages, and aliases;
5. valid forward/reverse edges and valid formal/informal references;
6. stable unique proof-line anchors and safe tactic/reference tokenization;
7. complete PA1--PA6, grammar, tactic, and proof-constructor foundations;
8. no remote runtime assets, `eval`, or HTML-string injection;
9. a WMI Jupyter Book build and relative-link integrity receipt;
10. browser smoke tests for search, filters, theorem-to-lemma navigation,
    line anchors, Back/Forward, keyboard access, dark mode, and mobile layout.

The explorer makes the proof inspectable. It does not weaken any QR admission
gate.
