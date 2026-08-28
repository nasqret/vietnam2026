# Deploying

The current mathematical release is sealed by
[`channels-v30.json`](../artifacts/peano-library/channels-v30.json). The separate
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
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/> | `~/public_html/proofs/` | all 44 checked proof families, the grand campaign atlas, proof artifacts, and public Lean selectors |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/api/lean-strands/> | `~/public_html/api/lean-strands/` | isolated same-origin PHP gateway to the operator's loopback-only Lean proof worker |

The SSH key (`~/.ssh/id_ed25519`) is already configured for the `lts-faculty` host.

## Core site and Lambda Lab

```bash
make deploy        # = stage + deploy-site + deploy-lab
```

Peano Lab is deliberately promoted through its own staging and production
targets; `make deploy` does not publish either Peano channel.

## Standalone proof explorers

```bash
make deploy-proofs
```

This verifies the frozen flagship editions without rewriting them, regenerates
the current constructive presentations, and stages all 44
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
The separate `constructive-gaussian-campaign` atlas is staged at the existing
public `/proofs/grand-campaign/` URL; neither historical atlas is overwritten.
It separately publishes the narrow two-file PHP gateway under
`~/public_html/api/lean-strands/`; neither publication target can be widened by
overriding its Make variable. The proof site also publishes the grand campaign
atlas and exact checked proof artifacts through current Alpha v30: 3,222
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
