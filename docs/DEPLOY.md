# Deploying

The current published proof-site and preview mathematical release is
[`channels-v34.json`](../artifacts/peano-library/channels-v34.json).
All 22 fresh proof jobs and six same-live publication phases (171 UI cases)
passed, and all six reader/atlas trees are installed. **The v34 proof site and
Peano preview are deployed; protected Peano production promotion is deferred.**
The proof, publication and delivery checks are described below. The separate
Hydra development sequence is in [`HYDRA_PRODUCT_ROADMAP.md`](HYDRA_PRODUCT_ROADMAP.md);
each training epoch retains its own explicitly frozen authority. Publishing new
proofs does not expand an existing training experiment. Public on-demand Lean
build controls are currently hidden. The operator gateway remains same-origin;
deployment commands below remain explicit, separately authorized operations,
not automatic Hydra preparation.

The public presentation now adds a non-admitting layout layer after the sealed
v34 stage. `make stage-proof-layout` preserves `_deploy/proofs-v34` and creates
or checks `_deploy/proofs-layout-v1`. Its `presentation/layout-v1.json`
records the accepted base manifest
and every changed page's before/after hashes. The only HTML change gives
direct-child release notices `grid-column: 1 / -1;`, keeping the proof in the
wide column and the receipt in the sidebar. It also works with the existing
single-column mobile layout. Original CSS/JavaScript, proof text, definition
data, historical manifests and mathematical evidence stay byte-identical.
Do not deploy the unadjusted base alone, which would restore the layout bug.
The preserved base provides an exact rollback; no proof promotion is involved.
See [the verified layout-repair record](PROOF_EXPLORER_LAYOUT_REPAIR_2026-09-04.md)
for the deployment scope, checks and exact public manifest.

The `make stage-public-proof-policy` step then creates or checks
the preserved `_deploy/proofs-public-v1` parent. Its
`presentation/lean-policy-v1.json` records a single asset substitution:
`assets/lean-selector.js` becomes the inactive publication-only script from
`deploy/proofs/lean-selector-disabled.js`. Every HTML page, proof artifact and
original reader asset stays byte-identical to the checked layout stage.
The canonical local selector and backend remain untouched. This hides the
public build card without changing evidence or silently depending on an
operator's SSH connection. No standalone Lean Live proofs are pre-published
in this release; adding direct theorem links requires a separately checked
static standalone source and its authenticated share link, not an empty
playground link. Do not deploy either earlier stage alone: that would restore
the hidden controls. Re-enabling them requires an explicit publication-policy
change, not merely restarting or deploying the gateway.
See [the public-control deployment record](PUBLIC_LEAN_POLICY_2026-09-04.md)
for verification and exact file identities.

The new default `make stage-proofs` adds the library-wide reading policy and
creates or checks `_deploy/proofs-readable-v1`; `make deploy-proofs` now selects
that final tree. This reading layer is **prepared locally, not yet deployed**.
It authenticates the preserved public parent, retains the inactive public Lean
policy and original assets, and verifies byte-for-byte recovery of every
original theorem page. If the public parent is absent, the original staging
chain remains the prerequisite; an existing parent must pass its complete
authenticated inventory check instead of being silently regenerated.

The separate `presentation/readability-v1.json` and `reading/audit.json` record
the presentation changes, source pairs, conservative notation checks and
coverage. Existing mathematical definitions, proof artifacts and Alpha/Stable
admissions do not change. The same reading policy applies to all 68 families,
with historical checkpoint pages still explicitly non-admitting. See the
[reading policy and verification record](PROOF_READABILITY_POLICY.md), including
the browser-visual and fresh textual-Lean verification limitations. Uploading
an earlier stage would remove these reading improvements.

Five browser surfaces and one narrowly scoped PHP endpoint on the faculty server
(`bnaskrecki@lts-faculty.wmi.amu.edu.pl`, static Apache + PHP,
**no persistent daemons** — which is why the lab is fully client-side):

| URL | Server path | Contents |
|-----|-------------|----------|
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026> | `~/public_html/vietnam2026/` | landing page + built book + slides |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda> | `~/public_html/lab-lambda/` | the browser Lambda Lab |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/> | `~/public_html/peano-lab/` | production Peano Lab |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab-next/> | `~/public_html/peano-lab-next/` | v34 preview, app `a-ea9ae0d7f72a`, build `2026-09-02a` |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/> | `~/public_html/proofs/` | 68 current proof families, preserved first-admission/checkpoint routes, the combined campaign atlas and proof artifacts; public on-demand Lean controls are hidden |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/api/lean-strands/> | `~/public_html/api/lean-strands/` | isolated same-origin PHP gateway to the operator's loopback-only Lean proof worker |

The SSH key (`~/.ssh/id_ed25519`) is already configured for the `lts-faculty` host.

## Core site and Lambda Lab

```bash
make deploy        # = stage + deploy-site + deploy-lab
```

Peano Lab is deliberately promoted through its own staging and production
targets; `make deploy` does not publish either Peano channel.

## Standalone proof explorers

### Published v34 proof site and preview (production deferred)

The admitted additive release preserves v33's 4,092 entries and adds exactly 131:
119 in `polynomial-gcd-bezout` and 12 in `congruence-arithmetic`. Its sealed
catalogue has 4,223 Alpha checked-use entries and 13,816 proof-dependency edges;
Stable remains the identical 432-theorem default. The five family scopes contain
68 families: the two new families plus all 66 prior families, with their original
first-admission identities. The shared reviewed registry has 407 conservative
definitions and 884 expansion arrows, distinct from proof prerequisites.

The polynomial scope includes normalized gcd/Bézout existence, greatestness and
uniqueness up to formal coefficient equivalence. It does not assert equality of
beta encodings or uniqueness of Bézout coefficients. These two exact tranches
do not close full G091 prime-power fields, Jordan-totient multiplicativity (G008) or the whole F02
campaign. G012 retains its original v19 first admission and G009 its v32 first
admission. Historical proof and deployment records retain their original scopes.

The commands remain explicit procedures; local release verification does not
perform or establish remote delivery:

```bash
make alpha-v34-release        # fresh proof gates, immutable release, six reader trees
make alpha-v34-release-check  # fresh verification against existing immutable bytes
make stage-proofs-v34 PEANO_DELIVERY_PYTHON=python3.11  # separate tree; no upload
```

If release files already exist but readers are not installed, the recovery
procedure is a fresh full run without `--create-release` or `--check`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONMALLOC=pymalloc python3 -B scripts/publish_constructive_research_v34.py
```

All 22 fresh proof jobs passed: current-parent/new-row exact-statement
novelty, two complete artifact checks in original HA and same-byte independently
compiled Lean, and 19 ordinary principal certificates (14 polynomial, five
congruence). Six sequential fork-only phases then inherited the genuine live
capability and passed all 171 declared same-live UI cases before reader
installation. The successful full rerun compared the six existing immutable
release files byte-for-byte without replacing them. These gates remain required
for each fresh publication; this is not a manual browser-visual verification.
Saved reports, source-only tests and explicitly non-authorizing
private preflights cannot substitute for these gates.

The phases are `gcd-congruence`, `polynomial`, `research`, `completed`,
`historical` and `atlas`. They add `constructive-gcd-congruence-explorer-v34`,
reproject the four v33 family scopes into their corresponding v34 directories,
and produce `constructive-research-campaign-v34`, preserving the original
Quadratic Reciprocity layout and historical evidence. Old reader trees remain
unchanged.

Only the new logical catalogue capacity changes: 4,096 to 8,192 rows. The
nonrecursive three-file catalogue retains the literal v30 base plus a cumulative
1,001-row delta and the new manifest. Original CPU 170/175 seconds, wall 180
seconds, 1,536 MiB RSS, proof depth 256 and file/codec limits remain unchanged;
old catalogue codecs still enforce their original bounds.

Source commit `97a1ed75c3a307eebe872774a82a8822c2c2ffeb` was pushed and deployed
additively, retaining prior files and activating entrypoints last. All 13,549
proof-site files and 630 preview files matched exact remote SHA-256 checks.
Fifteen fixed HTTPS batches passed all 230 requests across the 68 families;
eight critical preview HTTPS checks also passed, including new modules and both
new proof bundles. Preview serves app `a-ea9ae0d7f72a`, build `2026-09-02a`.
The [deployment observations](../research/arithmetic-library/working/alpha-v34-release-v1/deployment-observations-v1.json)
record delivery separately from mathematical acceptance.

The public Lean gateway was restored with its original single-worker 1,024 MiB
and 180-second limits. The [live conversion smoke test](../research/arithmetic-library/working/alpha-v34-release-v1/public-lean-smoke-observations-v1.json)
compiled all nine nodes of the new modulus-one congruence theorem with zero
certificate fallbacks and verified its standalone Lean payload and package.
The production entrypoint and both `.htaccess` files remain unchanged. Fresh
unversioned preview and production HEAD responses returned HTTP 200 without
the required `Cache-Control: no-store`. Protected production promotion therefore
remains deferred: successful proof-site/preview byte checks do not waive the
cache-header gate or establish manual browser-visual verification.

Future delivery still requires authenticated stage hashes, inspected remote
destinations, retained rollback entrypoints, uploads without deletion, remote
hash verification and entrypoint-last activation. Proof-site delivery, Peano
preview and protected Peano production remain separate authorized operations.

The complete v34 stage passed in 164.79 seconds with CPython 3.11.12, using
the unchanged single 180-second deadline and original CPU/RSS limits. Its
13,549 files include 68 family entrances; all 793,606 local links and 466,223
fragments passed. `PEANO_DELIVERY_PYTHON` selected the two v34 staging branches
in that release; it now also selects the additive presentation stagers and
reading-policy test target. The default remains `python3`; proof verification,
the Lean backend and historical recipes are unchanged. The original 87-case deployment
contract suite verifies this isolation. Two earlier timed-out delivery
attempts are preserved as failures in the working observations.

### Historical sealed v33 release

The additive polynomial release contains 4,092 Alpha checked-use entries:
the unchanged 3,971-entry v32 parent plus exactly 121 first admissions.
Stable remains the identical 432-theorem default. The new
`polynomial-euclidean-division` family covers arbitrary nonzero-divisor
execution, its formal coefficient identity and remainder bound, execution
uniqueness, leading-zero padding and representation-independent operations.
It does not claim arbitrary identity-pair quotient uniqueness, polynomial
associativity, gcd/Bézout, or the full G091 prime-power-field construction.
G009 retains its original v32 first admission.

The canonical Quadratic Reciprocity design is unchanged. The combined map
retains 144 milestone nodes and 120 major goals, with 397 reviewed conservative
definitions, 865 expansion arrows and 13,212 actual theorem dependencies.
Notation arrows never become proof premises. Seven new reviewed definitions
link from G091 to their exact expansion pages, without invented blueprint aliases.

```bash
make alpha-v33-release        # create a new immutable release and five reader trees
make alpha-v33-release-check  # fresh verification; compare existing immutable bytes
make stage-proofs-v33         # new dedicated _deploy/proofs-v33 tree, or exact check
```

If the six immutable v33 release files exist but the reader directories were
not installed, rerun publication without `--create-release` or `--check`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONMALLOC=pymalloc python3 -B scripts/publish_constructive_research_v33.py
```

This repeats all ten fresh proof jobs, checks the existing release bytes,
and creates the readers only after all five publication phases pass.

Admission requires ten fresh jobs: exact-statement novelty, the complete
377-node artifact checked in original HA and independently compiled Lean,
and eight complete ordinary principal certificates. Each job retains CPU
170/175 seconds, wall 180 seconds and 1,536 MiB RSS. Five subsequent sequential
publication phases inherit the genuine live capability and must pass all
163 declared same-live UI cases before any reader directory is installed.
Stored receipts, display metadata and generated manifests cannot authorize
new proofs. The three-file catalogue remains nonrecursive: the literal
v30 base plus one cumulative 870-row delta and the current manifest. The
64 MiB/file and 4,096-entry limits are unchanged; v33 leaves four entry slots.

The four family packages are `constructive-polynomial-euclidean-explorer-v33`
(one family), `constructive-research-explorer-v33` (two v32-admitted families),
`constructive-completed-lower-explorer-v33` (19 v31-admitted families), and
`constructive-historical-explorers-v33` (44 established families). The fifth
tree is `constructive-research-campaign-v33`. All older source trees, proof
bundles and first-admission records remain literal history; the 89 historical
non-admitted aliases are not promoted by a new display version.

Register delivery hashes only after the real publication passes. The v33
stager authenticates every source and retains `_deploy/proofs-v32`, creating
a separate tree without overwriting either historical stage. For faculty
deployment, inspect the exact owned remote destinations, retain rollback
entrypoints, upload without deletion, verify all staged remote file hashes,
and publish entrypoints last. Proof-site delivery and Peano preview are
separate from the protected Peano production cache-header gate below.
Do not change hosting headers or weaken that gate as part of this release.

The two completed working archives (`prime-field-euclidean-v1` and
`prime-field-equivalence-v1`) retain their original strict temporary-import
guards. They are historical tests for commit `022330e80`, not entrypoints for
the canonical v33 runtime. Use the new canonical v33 suites for current
admission; use an exact historical checkout to reproduce archived tests.
Do not weaken those guards or execute archived loaders after promotion.

### Historical v31 release

The additive v31 release admits 574 completed lower-layer theorems, giving
3,796 Alpha checked-use entries. Stable remains the unchanged default 432.
Its 19 new families cover Euler units, prime fields, Möbius values, signed
sums, divisor tables, polynomial arithmetic, convolution, finite Möbius
inversion and general signed Dirichlet inverses. G007 and G014 have exact
closed endpoints. Full G009 multiplicative closure and general prime-power
fields G091 remain open in the sealed v31 catalogue. The separately verified
G009 research reader below closes the finite-prefix G009 contract without
altering that catalogue or admitting its 90 new rows. G091 remains open.

Run `make peano-library-alpha-v31` once to create the six new release files
and the three current presentation trees. If the six sealed release files
already exist but publication has not installed its output trees, run
`make peano-library-alpha-v31-publish`. To verify an existing release and its
published trees, run `make peano-library-alpha-v31-check`. All three workflows
execute all 72 fresh
verification jobs: exact-statement novelty, 19 full original-HA/compiled-Lean
bundles and 52 ordinary principal certificates. Each proof job retains the
original 170/175 CPU seconds, 180 wall seconds and 1,536 MiB peak-RSS bounds.
The three subsequent renderers each inherit the genuine live verification
capability, have their own original bounded window, and must pass their
same-live UI tests before any new output tree is installed. No saved receipt
can replace the proof gate or create that capability.

These targets use the additive `publish_constructive_completed_lower_v31.py`
entrypoint. Its narrowly scoped presentation correction fixes the aggregate
index's relative atlas link and recomputes that page's manifest entry. Its
schema compatibility adapter also preserves the exact edition-agnostic
definition-graph schemas of Quadratic Reciprocity and Bertrand: neither
schema has a current Alpha-version constraint to migrate. Only these two
literal pinned schemas receive that exception; other schemas retain the
original reviewed version migration and rejection rules. The adapter uses
private function globals without modifying a historical module. It
preserves the six sealed release files and their original source pins; the
original proof gates and atomic non-overwriting publication remain in force.
The original catalogue-bound renderer and test sources are historical evidence,
not files to edit when correcting a delivery link or an observation harness.

The historical UI phase retains all 155 collected case identities. Of these,
111 execute their original assertions unchanged. The 44 mixed-graph cases use
the reviewed `constructive_historical_graph_test_support.py` pytest adapter:
the canonical renderer deliberately omits SVG anchors in compact graphs, and
visible-definition mode excludes definitions unused by the displayed theorems.
The adapter checks the exact visible node sets and typed-arrow counts, actual selection
and viewport, and compact-mode behavior. It also renders a focused view with
real SVG anchors to check getter-only `href` handling for every family. It
changes only test observations, not the renderer, graphs, theorem evidence, or
original test files. A source-pinned, exact-file/function hook selects these
44 cases; mandatory collection and outcome checks reject missing, filtered,
skipped, duplicated or failed cases. Normal pytest and publication use the
same repository plugin. The publisher binds that plugin, its tests and root
pytest configuration before the fresh proof run and after every phase.

The current presentation directories are:

- `constructive-completed-lower-explorer-v31`: 19 new families, 574 proofs.
- `constructive-historical-explorers-v31`: 44 established families, with exact
  per-theorem first-admission sidecars and original eligibility/aliases.
- `constructive-completed-lower-campaign-v31`: the combined 120-goal atlas,
  372 reviewed conservative definitions and 787 actual expansion arrows.

The historical readers contain 3,096 displayed theorem instances, of which
3,007 were source-checked and 89 intentionally not admitted. These display
counts include repeated shared prerequisites; they are not the unique
3,796-entry Alpha count. Publication never upgrades a historical alias.

The v30 catalogue is within the existing 64 MiB file limit but a monolithic v31
successor would not be. The new catalogue is therefore a small authenticated
manifest plus one 574-row delta referencing the literal v30 parent. All three
files are bound, including in the service's warm-cache key; the 64 MiB per-file
limit is unchanged. Missing, changed or unsafe inputs fail closed. A present
v31 atlas cannot downgrade the current service to a valid old release.

The v31 staging layer retains the original historical checks and routes,
then overlays the exact current v31 files. The delivery-only hub and staging
scripts compare the actual published byte inventories; they do not grant
proof authority. This base uses the original Quadratic Reciprocity
design, with exactly 63 primary family entrances. The subsequent G009 overlay
adds the explicitly non-admitted 64th family. Old research checkpoints
and the explicitly staged QR/k3b supplement remain available. The literal
v30 hub remains in `deploy/proofs/history/index-v30.html` for its historical
regressions; a separate mandatory suite checks the real v31 hub and routes.

The final staging audit runs after the existing public Lean-selector overlay
and permits only that exact insertion into eligible proof HTML. The remote
upload remains the existing dedicated faculty `deploy-proofs` workflow below.
Inspect exact remote targets and a checksum/deletion preview before upload;
verify complete staged/live bytes afterward. Proof-site delivery is separate
from Peano-next and the protected Peano production/cache-header gate.

### Non-admitting G009 research workflow

The additive `multiplicative-convolution` family implements the remaining
finite-signed G009 closure contract. It has 90 new statements, 371 inherited
Alpha-v31 prerequisites, and eleven new conservative definitions. Its exact
scope is nonempty actual signed prefixes normalized by `F(1)=+1`, with the
product law for positive coprime inputs whose product is within the prefix.
Zeroth values and table encodings remain unrestricted; uniqueness is equality
of represented positive values. Multiplicativity of the constructed inverse
is not asserted. General prime-power fields in G091 remain separate.

Create the reader once, or recheck an existing immutable reader:

```sh
PYTHONMALLOC=pymalloc python3 scripts/build_constructive_g009_explorer.py
make book-constructive-g009-explorer
```

Both operations require all eight fresh bounded proof jobs: exact-AST novelty
against all 3,796 parent statements, the complete original-HA bundle and
independently compiled Lean check of its identical bytes, and six ordinary
empty-context principal certificates. All 277 same-live explorer tests are
mandatory. The original CPU, wall, RSS, file-size and certificate limits stay
unchanged. No saved audit, authoring seed, partial prefix, filtered suite or
successful transport check can replace this acceptance. Creation never
overwrites an existing reader tree. `make check-constructive-g009` runs the
fresh proof audit without constructing pages.

Ordinary pytest also obtains a genuinely fresh snapshot:

```sh
PYTHONMALLOC=pymalloc PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  peano-lab/py/tests/test_constructive_g009_explorer.py
```

With no live builder plugin, its fixture runs all eight proof jobs and the
mandatory inner 277-case suite in an owned temporary directory, then runs the
outer tests against those exact bytes. It neither installs the public reader
nor accepts a saved report. A present but invalid plugin fails; it is not
replaced. The helper does not alter the outer test scheduler, alarms, CPU
limits or proof caches.

The independent verification recorded for this release uses the literally
pinned local Lean 4.28.0 executable. The general Linux CI workflow currently
provisions Lean 4.31.0 and cannot reproduce that native executable's byte
identity. Standalone-fixture support is not a claim of cross-platform CI
verification; that separate verifier-distribution boundary remains explicit.

G009 uses CPython's standard `pymalloc` allocator in its new proof workers
and the two dedicated Make targets. This allocation policy is independently
regressed; it does not raise any limit or change the old kernel, proof
compiler, caches or historical launchers. Inherited provider authentication
streams all 39 exact files instead of retaining complete byte buffers, and
unused local input owners are released before ordinary replay/exact checking.

The canonical reader lives in `book/_static/constructive-g009-explorer`.
It reuses the five original Quadratic Reciprocity assets unchanged, publishes
exact and definition-aware theorem pages `MX0001`–`MX005A`, and retains all
earlier definition identities. Its principal closure theorem is `MX0059`.
Definition-expansion, definition-usage and proof-dependency arrows remain
distinct. The extended combined atlas has 383 reviewed definitions and 825
actual expansion edges; research verification does not change Alpha 3,796,
Stable 432, or a historical first admission.

The fresh production run installed 255 files (53,690,970 bytes), after all
eight proof jobs and 277 reader tests passed. The literal reader-manifest
identity is `3882fba2f018961d90d8afd1ffbe317ec49e85320b7a0d6adb9e97d48db91f20`.
Its evidence remains separate from subsequent static delivery observations
and from a future additive Alpha promotion.

After the reader passes, its literal manifest and the actual v31 hub/lock
identify the narrowly scoped delivery registration. `make stage-proofs` keeps
all original staging gates, applies the v31 overlay and eligible Lean controls,
then applies and checks the G009 overlay. Only the root hub and four atlas
files may replace existing content; all five shared assets must be identical.
The additional root card is explicitly non-admitted research. Checkpoint
metadata is served under `release-g009/`, while its unchanged proof bundle is
under `checkpoints/g009-multiplicative-convolution-proof-bundle-v1.json`.
Every merged byte, local link and fragment is checked. The new research pages
do not receive an unsupported Alpha-only on-demand Lean selector.

For an already completely verified v31 stage, the same additive delivery step
can be checked independently without rebuilding or changing historical data:

```sh
python3 scripts/stage_constructive_g009_publication.py --root _deploy/proofs
python3 scripts/stage_constructive_g009_publication.py --root _deploy/proofs --check
```

These are delivery checks only. The separately verified reader and all old
stage prerequisites must already exist. Upload remains the same dedicated
faculty proof-site workflow, with a checksum/deletion preview, root index last,
complete local/remote hashes and certificate-verifying HTTPS comparisons.

### Historical v30 staging base (preserved)

```bash
make deploy-proofs
```

The retained base verifies the frozen flagship editions without rewriting them,
regenerates its historical constructive presentations, and stages all 44
quadratic-reciprocity, Bertrand, constructive-frontier, next-layer,
advanced-layer, transport-layer, milestone-closure, research-layer, and
breakthrough-layer, second-wave, lower-layer, priority-layer and Gaussian
factorization families under `_deploy/proofs`, and installs their shared public
**Build Lean proof** controls. Six additional canonical Quadratic-Reciprocity-style
routes are `/proofs/prime-valuation-support/`, `/proofs/best-approximation/`,
`/proofs/totient-products/`, `/proofs/squarefree-kernels/`,
`/proofs/exponent-lifting/`, and `/proofs/gaussian-factorization/`.
The original v27, v28 and v29 explorer snapshots remain byte-for-byte historical
artifacts. Separate current packages `constructive-second-wave-explorer-v30`,
`constructive-lower-layer-explorer-v30`, and
`constructive-priority-layer-explorer-v30` retain all 904 historical proofs and
their exact first-admission receipts, at the same public URLs. The new Gaussian
chapter is generated under `constructive-gaussian-factorization-explorer`.
Five exact legacy `arithmetic-library/*.html` read-more destinations redirect
to their existing `/vietnam2026/book/arithmetic-library/` chapters, preserving
the frozen flagship HTML. This proof-site-only compatibility rule does not
change any cache headers or the production Peano delivery gate.
The same five paths also have ordinary static fallback pages: when hosting
ignores rewrite rules, their fixed-destination browser redirects preserve the
query and fragment, with a normal chapter link and a no-JavaScript fallback.
The separate `constructive-gaussian-campaign` atlas is the historical staging
base; the v31 overlay supplies the current public `/proofs/grand-campaign/`
URL. Neither historical source atlas is overwritten.
It separately publishes the narrow two-file PHP gateway under
`~/public_html/api/lean-strands/`; neither publication target can be widened by
overriding its Make variable. The proof site also publishes the grand campaign
atlas and exact checked proof artifacts through historical Alpha v30: 3,222
independently checked theorems, including 432 unchanged Stable and 2,790
Alpha-only theorems, 10,588 proof-dependency edges, 370 blueprint definitions,
and 284 reviewed conservative definitions with 560 audited definition edges.
The 566-node priority-layer and 453-node Gaussian-factorization bundles are
independently accepted by the original intuitionistic kernel and the compiled
Lean verifier; the receipts state the actual local compiler provenance separately
from CI's pinned 4.31 toolchain. Each family retains its unchanged proof evidence,
Stable/Alpha distinction, first-admission history, and original explorer assets.
G001–G005, G021–G022, G081, and G084 are complete at their exact recorded scope;
G072 best approximation, G006 totient products, G010 squarefree kernels and
perfect-power profiles, G036 odd-prime LTE, and G082 Gaussian unique prime
factorization are now complete at their exact guarded statements. G082
constructs a genuine unit-matching bijection, not literal or sorted factor-list
equality. Gaussian prime classification and the Eisenstein factorization and
classification milestones remain separate open goals.
The earlier v27 finite T13, Hensel G095, and generalized CRT G011 contracts
remain closed without claiming stronger lattice or p-adic completion results.

The current catalog uses compact JSON whitespace while preserving every exact
theorem and inherited receipt. The service's 64 MiB catalog limit, one-worker
policy and other resource/security bounds are unchanged. A broken present
current atlas fails closed instead of silently falling back to an older release.
`make peano-library-alpha-v30-check` also checks all seven historical-family
presentation controllers and their ten regression suites serially, both Lean
export formats, and the immutable application manifest. The v27, v28 and v29
mathematical release gates remain separately available and unchanged.
The next-layer presentation suite uses seven disjoint fresh-process windows
to avoid retaining multiple large catalog fixtures at once. The deployment
contract independently collects every case and verifies exact, once-only
coverage of all 261 tests; no test or authority check is skipped.
Research and breakthrough presentation tests separate their 30 adversarial
catalogue cases from the 78 and 99 positive cases in fresh processes. Their
test-only streaming JSON encoder preserves the exact compact catalogue bytes,
all corruption cases, rehashed pointers and actual rejection checks. The
deployment contract verifies complete, once-only coverage for both suites.
These presentation checks explicitly use CPython's standard `pymalloc`
allocator, matching the recorded resource measurements.
The separate exact-reader navigation regression gate preserves frozen historical
HTML while marking the current v30 links to their existing definition-aware
graphs. The original explorer JavaScript and its QR/Bertrand behavior remain
unchanged; current exact readers must not inject a second, nonexistent graph.
Bulk publication is not a single proof job: the original combined historical
publisher completed at an observed peak of 2,226,962,432 resident bytes. Run
publication serially. The experimental 1,536 MiB bulk-publisher diagnostic did
not pass and is not shipped; no original release, kernel, proof-job or service
limit is disabled or increased.

### Historical public research checkpoints without Alpha promotion

The separate `/proofs/checkpoints/` section publishes 170 additional complete
HA/Lean-checked theorems: Euler units (32), prime fields (87), Möbius values
(21), and signed sums (30). These are independently checked dependency-closed
proofs, **not Alpha or Stable admissions in those checkpoint records**. At that
historical publication, the library was Alpha v30 with 3,222 entries and the
unchanged 432 Stable entries. The full G014 Euler endpoint was proved at its
guarded statement; full G091 prime-power fields and G007 Möbius inversion were
still open in that release. Later admissions do not rewrite these records.

The immutable local development snapshot remains under
`book/_static/constructive-bottom-layer-explorer`. A separate public adapter
generates `book/_static/constructive-bottom-layer-publication`, preserving
literal bundles, sources, theorem tags, proof statements and false admission
flags. Each build freshly runs the original HA and independently compiled
Lean verifiers. Stored receipts and a matching hash are not proof authority.

```sh
PYTHONMALLOC=malloc python3 scripts/check_constructive_bottom_layers.py --check
PYTHONMALLOC=malloc python3 scripts/build_constructive_bottom_layer_publication.py --check
make -j1 stage-proofs
python3 scripts/stage_public_checkpoint_navigation.py --root _deploy/proofs --check
python3 scripts/stage_public_lean_selector.py --root _deploy/proofs --check
```

The normal staging target includes the checkpoint subtree, so future complete
deployments do not remove it. Its atlas backlink and scope notice are added
only to staged HTML; frozen atlas source, campaign JSON, definition JSON and
recorded admission statuses remain unchanged. The main hub links all four
chapters separately from the 44 Alpha families.

The existing on-demand Lean service accepts Alpha-enrolled theorem names.
The public selector deliberately excludes the top-level `checkpoints` namespace;
these readers offer their independently verified downloadable proof bundles,
not unsupported Alpha service jobs. No worker restart, gateway change, catalog
limit change, Peano production deployment or cache-header work is required.
Before upload, inspect remote symlinks and the checksum/deletion preview. After
upload, compare the complete staged tree and representative public HTTPS bytes.
The deployment receipt records observed results separately from proof evidence.

Adding the twelve Python modules also regenerates the local browser source
inventory and its content-addressed application manifest. The prepared local
app is `a-86993f944ca2` (483 browser Python sources, 505 manifest entries).
This keeps checkout and local staging reproducible; it does not admit those
modules' theorems or deploy either Peano channel. Production remains deferred.

The [2026-08-28 checkpoint deployment receipt](../research/arithmetic-library/bottom-layer-publication-receipt-2026-08-28.md)
records the actual pushed source, complete staging audits and exact live HTTPS
verification, separately from the immutable mathematical proof receipts.

## Interactive Lean proof building

The following describes the retained operator/local capability. As of
2026-09-04 the final public presentation policy hides its build controls;
these commands do not override that policy or restore public build cards.

The theorem-graph **Build Lean proof** action needs the bounded Python/Lean
proof service. Faculty Apache cannot run persistent daemons, but its existing
PHP support can forward the exact same-origin API through a faculty-loopback
SSH reverse tunnel. Start the complete public workflow in two steps:

```bash
# Publish all explorer controls and their isolated same-origin PHP gateway.
make deploy-proofs

# Keep this command running on the checked local repository.
make lean-public

# From another terminal, independently exercise the real deployed workflow.
make lean-public-check
```

For a managed background connection, use `make deploy-lean-public`, followed by
`make lean-public-start`. Inspect its authenticated public/local configuration
with `make lean-public-status`, and disconnect only its owned worker and tunnel
with `make lean-public-stop`.

The faculty web host and faculty SSH login host are separate machines, but they
share the account owner's private home directory. The foreground
`make lean-public` command starts or safely reuses the ordinary checked Lean
service on `127.0.0.1:8787`. Its attached SSH session opens only this exact
remote forward and runs a small foreground mailbox broker:

```bash
ssh -T \
  -o BatchMode=yes \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -R 127.0.0.1:18787:127.0.0.1:8787 \
  lts-faculty.wmi.amu.edu.pl \
  'python3 -u ~/.hydra-lean-mailbox/broker.py \
    --directory ~/.hydra-lean-mailbox --upstream-port 18787'
```

The faculty-side port is loopback-only: it is unreachable from the public
Internet. PHP places bounded requests in `~/.hydra-lean-mailbox`, outside
`public_html`, with owner-only `0700` directory and `0600` file permissions.
The foreground broker atomically claims each request, sends it through the
loopback tunnel, and publishes one size-bounded, SHA-256-authenticated
response. No remote daemon remains when the SSH session ends.

The gateway accepts only its exact faculty hostname, same-origin JSON job
mutations, and bounded opaque job routes. It cannot browse the repository,
select an arbitrary upstream host, forward credentials, or weaken the existing
one-worker, memory, time, request-size, source-size, and artifact-retention
limits. The private Lean companion and compiler remain on the operator's
machine. Stop the foreground command with Ctrl-C to close both the broker and
public tunnel; an already-running independent local service is not terminated.

Visitors can open any checked Stable or Alpha theorem, build its complete
dependency-ordered proof, follow actual progress, download verified `.lean` or
ZIP output, and open a self-contained Lean Live proof when its exact
import-free source was independently compiled. Definitions and unchecked
theorems remain ineligible. If the tunnel is not running, the PHP gateway
returns an honest HTTP 503 instead of claiming a proof was verified.

The existing local-only experience remains available without publication:

```bash
make lean-browser
make lean-browser-check
```

The published browser deliberately sends proof jobs only to its own faculty
origin. The existing PHP gateway and private SSH tunnel need no additional
host, and no theorem payload or generated proof is sent to a third-party
service.

## Step by step

```bash
# 1. Build & assemble the site (landing + book + slides) into _deploy/vietnam2026
make stage

# 2. Push the site
rsync -avz --delete _deploy/vietnam2026/ lts-faculty.wmi.amu.edu.pl:~/public_html/vietnam2026/

# 3. Push the browser lab (worker + fully self-hosted; assembles index.html,
#    worker.js, .htaccess, py/, vendor/ — see the Makefile target)
make deploy-lab

# 4. Freeze a clean Peano candidate, push it to staging, verify it, then
#    promote without changing the commit or worktree.
test -z "$(git status --porcelain)"
candidate=$(git rev-parse HEAD)
make deploy-peano-next
bash scripts/verify_peano_delivery.sh \
  https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab-next
test "$(git rev-parse HEAD)" = "$candidate"
test -z "$(git status --porcelain)"
make deploy-peano
bash scripts/verify_peano_delivery.sh \
  https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab
```

## Notes

- `book/_build/html/index.html` is an auto-generated redirect to `intro.html`, so `/vietnam2026/book/`
  resolves via Apache's directory index.
- The lab is the worker build (promoted 2026-07-24): Pyodide runs in a Web Worker (Stop button, no UI
  freezes) and every asset — Pyodide core, xterm+addons, fonts — is served from this site (vendor/,
  fetched by scripts/fetch_vendor.sh). `/lab-lambda-next/` is the staging channel. A service-worker
  precache for guaranteed offline remains future work.
- Peano Lab uses the same worker/self-hosted layout. `/peano-lab-next/` is its staging channel;
  `/peano-lab/` is promoted only after the milestone tests, book, vault, corpus, and staging gates
  are green. Its application and vendor directories are manifest-versioned; never reuse an
  `a-<digest>` or `v-<digest>` namespace for different bytes. Deployment retains old immutable
  directories, uploads new assets first, and publishes `index.html` last.
- The course landing page's general artifact links point to GitHub
  (`nasqret/vietnam2026/tree/main/artifacts`). The proof explorers separately
  publish their explicitly inventoried proof bundles and source snapshots
  under the dedicated `/proofs/` delivery tree.

## Peano Lab delivery gate

After deploying staging, verify the page policy, every application hash, immutable versioned
assets, negotiated WASM compression, decoded bytes, archive exclusions, errors, and the encoded
transfer bound before promotion:

```bash
bash scripts/verify_peano_delivery.sh \
  https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab-next \
  _deploy/peano-lab
```

The verifier fails unless the page is byte-identical and `no-store`; the remote application
manifest and every worker, Python source, and packaged QR proof-artifact entry match local hashes;
normal, `206`, and `304` versioned
responses are immutable while HTML `200`/`304` stays `no-store`; negotiated WASM is Brotli/gzip with `Vary: Accept-Encoding`; `br;q=0` falls back to
gzip; identity, ZIP, and WOFF2 are not encoded; the 404 is `no-store`; decoded WASM matches the
pinned local hash; and curl's encoded `size_download` is below 3,000,000 bytes. Its final line
records the URL, human build, application/vendor IDs, and encoded byte count.

Repeat the verifier against `/peano-lab/` after promotion. Never reuse a vendor namespace,
application namespace, or human-facing `BUILD`; the script derives all three values from the staged
tree. Record a clean candidate commit before staging and do not change either `HEAD` or the worktree
until production is verified. `make deploy-peano-next` and `make deploy-peano` intentionally do not
use remote `--delete`, because an older open page must retain its immutable worker and runtime
through the release transition.

If faculty hosting strips the `Cache-Control` headers declared in the deployed
`.htaccess`, the staging verifier must fail and production promotion must stop.
Restoring Apache header support or preventing an upstream proxy from removing
those headers requires hosting-administrator action; missing cache guarantees
must not be bypassed by weakening the verifier or publishing production
directly.

## GitHub

The repository `nasqret/vietnam2026` is the source of record. Push the current
milestone branch; merging it to `main` is a milestone-owner decision. GitHub
Pages may optionally mirror the built book.

### Read-only Lean companion access in CI

The Peano shards check out the private `nasqret/peano-lab-lean` repository at
the exact pinned commit, using the dedicated Actions secret
`PEANO_LEAN_READONLY_DEPLOY_KEY`. Its matching repository deploy key must have
**read-only** access to that companion only. Neither repository needs a
visibility change, a personal account token in Actions, or write access.

The private key is provided only to the presence check and companion checkout;
it is not a job-wide environment variable. SSH host verification remains
strict, and both checkouts disable credential persistence. The ordinary
Actions token is restricted to `contents: read`. Never print key contents,
store a key in Git, reuse the operator's faculty SSH key, or expose this secret
through `pull_request_target` or another privileged fork workflow.

Fork pull requests intentionally receive no repository secret, so this gate
fails closed with an explanatory message. Run the full private-companion
suite from a reviewed trusted branch. Removing this one repository deploy key
revokes companion access; deleting its one Actions secret removes the CI copy.
Rotation must preserve the exact source/toolchain pins and proof checks.

Peano production promotion can be deferred while this CI setup and proof
development continue. That does not waive the cache-header delivery gate and
does not prevent publishing the separately checked static proof website.
