# Deploying

Five browser surfaces and one narrowly scoped PHP endpoint on the faculty server
(`bnaskrecki@lts-faculty.wmi.amu.edu.pl`, static Apache + PHP,
**no persistent daemons** — which is why the lab is fully client-side):

| URL | Server path | Contents |
|-----|-------------|----------|
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026> | `~/public_html/vietnam2026/` | landing page + built book + slides |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda> | `~/public_html/lab-lambda/` | the browser Lambda Lab |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/> | `~/public_html/peano-lab/` | production Peano Lab |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab-next/> | `~/public_html/peano-lab-next/` | Peano Lab staging channel |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/> | `~/public_html/proofs/` | all 27 checked proof families, the grand campaign atlas, proof artifacts, and public Lean selectors |
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

This rebuilds both exact and definition-aware proof editions, stages all 27
quadratic-reciprocity, Bertrand, constructive-frontier, next-layer,
advanced-layer, transport-layer, milestone-closure, research-layer, and
breakthrough-layer families under `_deploy/proofs`, and installs their shared
public **Build Lean proof** controls. The three new canonical
Quadratic-Reciprocity-style routes are `/proofs/matrix-cofactor-expansion/`,
`/proofs/polynomial-taylor-hensel/`, and
`/proofs/generalized-crt-compatibility/`.
It separately publishes the narrow two-file PHP gateway under
`~/public_html/api/lean-strands/`; neither publication target can be widened by
overriding its Make variable. The proof site also publishes the grand campaign
atlas and exact checked proof artifacts through current Alpha v25: 2,080
independently checked theorems, including 432 unchanged Stable and 1,648
Alpha-only theorems, 6,633 proof-dependency edges, 179 blueprint definitions,
and 120 reviewed conservative definitions. Its 302-node breakthrough proof
bundle is independently accepted by the original intuitionistic kernel and
the compiled Lean verifier. Each family retains its unchanged proof evidence,
Stable/Alpha distinction, first-admission history, original explorer assets,
and honest open boundaries for T13, G095, and G011.

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
