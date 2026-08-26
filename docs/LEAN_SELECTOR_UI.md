# Build a Lean proof from the selected theorem

The PA and defined-notation proof explorers expose a **Build Lean proof** card in
the selected-theorem panel. The card remains idle until a human deliberately
starts a proof job. It follows the exact theorem currently selected in the
graph, including selection changes, without rebuilding or replaying the
complete theorem library.

1. Select a checked theorem in the graph, or open its theorem page.
2. Inspect whether the card identifies its source as **Stable** or **Alpha**.
3. Click **Build Lean proof** to start one bounded, authenticated background job.
4. Watch the current stage, processed theorem count, and percentage.
5. After the independent Lean compiler succeeds, download its standalone
   `.lean` proof when available, or the **Verified Lean package (.zip)**.
   Certificate-backed fallback proofs require the separately configured Lean
   companion project; the ZIP does not publish or bundle that private project.
6. Choose the prominent **Open verified self-contained proof in Lean Live** action only after
   the exact standalone source has also passed an independent local Lean check.
   The button stays hidden until its complete checked-source receipt is present.

**Cancel** stops the current background job. Selecting another theorem cancels
the previous request instead of silently changing its target. Service failures
offer **Retry Build**. Definitions remain visibly disabled because they have no
theorem proof; unchecked theorem bodies never receive checked-theorem build
authority. A large graph selection reports its already-recorded dependency
count when available and warns before the default 1,024-node service limit. The
frontend never traverses the dependency graph or starts a worker on selection.

The frontend is shared by explicit and definition-aware explorer pages:

```text
book/_static/lean-selector/lean-selector.js
book/_static/lean-selector/lean-selector.css
```

The same files enhance the quadratic-reciprocity and Bertrand graph pairs,
plus the Kummer, Lucas, two-squares, four-squares, supplementary-laws, and
Pythagorean/Fermat-four constructive-frontier graphs. They also enhance both
the graph and individual checked-theorem pages in the Alpha-v20
`constructive-next-layer-explorer` and Alpha-v21
`constructive-advanced-layer-explorer`, the Alpha-v22
`constructive-transport-layer-explorer`, and the current Alpha-v23
`constructive-milestone-closure-explorer`, and the newest Alpha-v24
`constructive-research-layer-explorer`. Individual campaign pages are enabled
only when their authority receipt is exactly `Alpha v<number> checked use`;
unchecked or embellished receipt text cannot grant proof-building authority.
For a small Alpha v19
example, select `PF0000` (`pythagorean_double_product`) in the last graph;
`PA000F` (`add_comm`) is the corresponding small Stable example.

The local service injects those two assets into selected explorer responses.
For the public faculty website, `make stage-proofs` copies the same assets to
`/proofs/assets/lean-selector.js` and `/proofs/assets/lean-selector.css`, then
enhances only the staged explorer HTML. Existing frozen proof pages, graph
receipts, pinned explorer scripts, and generated corpus manifests
do not need regeneration. The canonical family pages and exact original proof
assets remain unchanged. Advanced integrations
may use `window.PeanoLeanSelector.mount(panel, {theorem, edition, eligible})`.
The optional service prefix comes from
`window.PEANO_LEAN_STRAND_API` or a
`<meta name="peano-lean-strand-api" content="...">` element. Same-origin
`/api/lean-strands` is the safe default. An explicitly configured HTTPS service
origin is accepted only when its bounded backend approves the exact faculty
origin without allowing cookies or other credentials.

On faculty hosting the default same-origin API is a tiny PHP gateway. The web
and SSH servers share an owner-only `0700` mailbox outside `public_html`; an
SSH-attached foreground broker forwards its allowlisted routes through a
loopback-only reverse tunnel to the operator's existing checked local Lean
installation:

```bash
make deploy-proofs
make lean-public
make lean-public-check
```

The first command publishes the static selectors and isolated gateway; the
second keeps the proof worker and reverse tunnel available; the third checks a
real public Stable proof, independent Lean compilation, downloads, and its Lean
Live source. No persistent daemon, Lean installation, private companion, or
repository checkout is needed on the faculty server. When the tunnel is
offline, visitors see a factual unavailable-service response rather than a
false verification claim.

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
It accepts download URLs only from the exact selected job and its authenticated
same-origin gateway or explicitly configured HTTPS proof-service origin.
Lean Live links must use exactly one of the official inline forms
`https://live.lean-lang.org/#code=...` or
`https://live.lean-lang.org/#codez=...`. The latter uses Lean Live's actual
unpadded standard-Base64 LZ-string alphabet, with `+` and `/` escaped as `%2B`
and `%2F`; LZ-string's similarly named URI-safe alphabet is incompatible. This
form carries the very same source more compactly, making more complete proofs
fit the reviewed 524,288-byte default ceiling. Before exposing either
link, the service decodes its bounded payload and verifies that its SHA-256 is
identical to the exact standalone `.lean` source that the local Lean compiler
accepted. This source contains **no `import` declarations at all**: no Lean
library import, no Mathlib, no private companion, and no external dependency.
The browser additionally requires a locally verified standalone receipt,
an explicitly empty import list, zero companion-backed fallback nodes, the
matching encoding, the exact official host, and a successful independent
package compilation. The successful action is labeled
**No imports · self-contained · locally compiled · no Mathlib/external libraries**.

The default 1,024-node campaign budget covers the current checked Alpha-v24
campaign dependency trees, including the 557-node quadratic-reciprocity closure.
Operators
can opt in to a 1,048,576-byte escaped URL and 4 MiB decoded proof source using
the service's `--max-live-url-bytes` and `--max-live-source-kib` flags. Large
URLs remain in the authenticated job snapshot and source sidecar instead of
overflowing bounded progress-event lines.

Certificate-dependent, oversized, private-import, missing-receipt, or
unavailable candidates expose no misleading link. If even the compressed
standalone proof exceeds the sharing limit, its exact checked `.lean` download
remains available with a clear explanation. The interface never accepts hosted
`#url` fragments, arbitrary external source locations, or companion-dependent
certificate proofs; the separate private Lean project remains private.
Even `import Lean.Elab.Tactic` is refused: Lean accepts the generated standalone
proof with zero import lines. Public hosted `#url` handoff is not enabled.

The unchanged Peano kernel still owns Peano theorem acceptance. A progress
bar, release badge, generated source file, or browser button is not a proof.
The frontend refuses a completed job unless its authenticated status explicitly
reports `lean_verified: true`; only that actual successful independent Lean
check establishes the corresponding Lean statement. Stable membership and
Alpha checked-use authority remain
explicit, and selecting or exporting a theorem does not promote it between
releases.
