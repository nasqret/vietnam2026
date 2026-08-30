# Deploying

The current mathematical release is sealed by
[`channels-v31.json`](../artifacts/peano-library/channels-v31.json). The separate
Hydra development sequence is in [`HYDRA_PRODUCT_ROADMAP.md`](HYDRA_PRODUCT_ROADMAP.md);
each training epoch retains its own explicitly frozen authority. Publishing new
proofs does not expand an existing training experiment. The supported public
Lean route is the same-origin proof gateway; deployment commands below remain
explicit, separately authorized operations, not automatic Hydra preparation.

Five browser surfaces and one narrowly scoped PHP endpoint on the faculty server
(`bnaskrecki@lts-faculty.wmi.amu.edu.pl`, static Apache + PHP,
**no persistent daemons** — which is why the lab is fully client-side):

| URL | Server path | Contents |
|-----|-------------|----------|
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026> | `~/public_html/vietnam2026/` | landing page + built book + slides |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda> | `~/public_html/lab-lambda/` | the browser Lambda Lab |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/> | `~/public_html/peano-lab/` | production Peano Lab |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab-next/> | `~/public_html/peano-lab-next/` | Peano Lab staging channel |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/> | `~/public_html/proofs/` | 63 proof families under current Alpha v31, preserved historical checkpoint routes, the grand campaign atlas, proof artifacts, and eligible public Lean selectors |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/api/lean-strands/> | `~/public_html/api/lean-strands/` | isolated same-origin PHP gateway to the operator's loopback-only Lean proof worker |

The SSH key (`~/.ssh/id_ed25519`) is already configured for the `lts-faculty` host.

## Core site and Lambda Lab

```bash
make deploy        # = stage + deploy-site + deploy-lab
```

Peano Lab is deliberately promoted through its own staging and production
targets; `make deploy` does not publish either Peano channel.

## Standalone proof explorers

### Current v31 release

The additive v31 release admits 574 completed lower-layer theorems, giving
3,796 Alpha checked-use entries. Stable remains the unchanged default 432.
Its 19 new families cover Euler units, prime fields, Möbius values, signed
sums, divisor tables, polynomial arithmetic, convolution, finite Möbius
inversion and general signed Dirichlet inverses. G007 and G014 have exact
closed endpoints. Full G009 multiplicative closure and general prime-power
fields G091 remain open in this release.

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

`make stage-proofs` retains the original historical staging checks and routes,
then overlays the exact current v31 files. The delivery-only hub and staging
scripts compare the actual published byte inventories; they do not grant
proof authority. The public root uses the original Quadratic Reciprocity
design, with exactly 63 primary family entrances. Old research checkpoints
and the explicitly staged QR/k3b supplement remain available. The literal
v30 hub remains in `deploy/proofs/history/index-v30.html` for its historical
regressions; a separate mandatory suite checks the real v31 hub and routes.

The final staging audit runs after the existing public Lean-selector overlay
and permits only that exact insertion into eligible proof HTML. The remote
upload remains the existing dedicated faculty `deploy-proofs` workflow below.
Inspect exact remote targets and a checksum/deletion preview before upload;
verify complete staged/live bytes afterward. Proof-site delivery is separate
from Peano-next and the protected Peano production/cache-header gate.

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

### Public research checkpoints without Alpha promotion

The separate `/proofs/checkpoints/` section publishes 170 additional complete
HA/Lean-checked theorems: Euler units (32), prime fields (87), Möbius values
(21), and signed sums (30). These are independently checked dependency-closed
proofs, **not Alpha or Stable admissions**. The current library remains Alpha
v30 with 3,222 entries and the unchanged 432 Stable entries. The full G014
Euler endpoint is proved at its guarded statement; full G091 prime-power
fields and G007 Möbius inversion remain open.

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
- Formal artifacts are browsed on GitHub (`nasqret/vietnam2026/tree/main/artifacts`), not deployed to the
  server, so the landing page's artifact links point there.

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
