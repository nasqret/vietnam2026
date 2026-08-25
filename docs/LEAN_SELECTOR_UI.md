# Build a Lean proof from the selected theorem

The PA and defined-notation proof explorers expose a **Build Lean proof** card in
the selected-theorem panel. The card remains idle until a human deliberately
starts a proof job. It follows the exact theorem currently selected in the
graph, including selection changes, without rebuilding or replaying the
complete theorem library.

1. Select a checked theorem in the graph, or open its theorem page.
2. Inspect whether the card identifies its source as **Stable** or **Alpha**.
3. Click **Build Lean proof** to start one bounded, same-origin background job.
4. Watch the current stage, processed theorem count, and percentage.
5. After the independent Lean compiler succeeds, download its standalone
   `.lean` proof when available, or the **Verified Lean package (.zip)**.
   Certificate-backed fallback proofs require the separately configured Lean
   companion project; the ZIP does not publish or bundle that private project.
6. Choose **Open in Lean Live** only when the service supplies a genuinely
   self-contained, bounded, independently meaningful Lean Live source.

**Cancel** stops the current background job. Selecting another theorem cancels
the previous request instead of silently changing its target. Service failures
offer **Retry Build**. Definitions remain visibly disabled because they have no
theorem proof; unchecked theorem bodies never receive checked-theorem build
authority. A large graph selection reports its already-recorded dependency
count when available and warns before the default 256-node service limit. The
frontend never traverses the dependency graph or starts a worker on selection.

The frontend is shared by explicit and definition-aware explorer pages:

```text
book/_static/lean-selector/lean-selector.js
book/_static/lean-selector/lean-selector.css
```

The same files enhance the quadratic-reciprocity and Bertrand graph pairs,
plus the Kummer, Lucas, two-squares, four-squares, supplementary-laws, and
Pythagorean/Fermat-four constructive-frontier graphs. For a small Alpha v19
example, select `PF0000` (`pythagorean_double_product`) in the last graph;
`PA000F` (`add_comm`) is the corresponding small Stable example.

The local service injects those two assets into selected explorer responses.
Existing frozen proof pages, graph receipts, pinned explorer scripts, and
generated corpus manifests do not need regeneration. Advanced integrations
may use `window.PeanoLeanSelector.mount(panel, {theorem, edition, eligible})`.
The optional same-origin service prefix comes from
`window.PEANO_LEAN_STRAND_API` or a
`<meta name="peano-lean-strand-api" content="...">` element.

The job protocol is deliberately small:

```text
POST   /api/lean-strands/jobs
       {"theorem":"prime_unbounded","edition":"stable"}
GET    /api/lean-strands/jobs/<job_id>
DELETE /api/lean-strands/jobs/<job_id>
GET    /api/lean-strands/jobs/<job_id>/download?format=lean
GET    /api/lean-strands/jobs/<job_id>/download?format=zip
```

The client polls bounded job snapshots approximately every 750 milliseconds.
It accepts download URLs only from the same origin and exact selected job.
Lean Live links must use exactly `https://live.lean-lang.org/#code=...` and
remain below the reviewed 8,192-byte ceiling; a certificate-dependent,
oversized, private-import, or unavailable candidate exposes no fake link.
When a genuine standalone proof exceeds the sharing limit, its `.lean` download
remains available with a clear explanation. Live never receives a
companion-dependent certificate proof.

The unchanged Peano kernel still owns Peano theorem acceptance. A progress
bar, release badge, generated source file, or browser button is not a proof.
The frontend refuses a completed job unless its authenticated status explicitly
reports `lean_verified: true`; only that actual successful independent Lean
check establishes the corresponding Lean statement. Stable membership and
Alpha checked-use authority remain
explicit, and selecting or exporting a theorem does not promote it between
releases.
