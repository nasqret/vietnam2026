# Deploying

Four static targets on the faculty server (`bnaskrecki@lts-faculty.wmi.amu.edu.pl`, static Apache + PHP,
**no persistent daemons** — which is why the lab is fully client-side):

| URL | Server path | Contents |
|-----|-------------|----------|
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026> | `~/public_html/vietnam2026/` | landing page + built book + slides |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda> | `~/public_html/lab-lambda/` | the browser Lambda Lab |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/> | `~/public_html/peano-lab/` | production Peano Lab |
| <https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab-next/> | `~/public_html/peano-lab-next/` | Peano Lab staging channel |

The SSH key (`~/.ssh/id_ed25519`) is already configured for the `lts-faculty` host.

## Core site and Lambda Lab

```bash
make deploy        # = stage + deploy-site + deploy-lab
```

Peano Lab is deliberately promoted through its own staging and production
targets; `make deploy` does not publish either Peano channel.

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
manifest and all 34 worker/Python entries match local hashes; normal, `206`, and `304` versioned
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

## GitHub

The repository `nasqret/vietnam2026` is the source of record. Push the current
milestone branch; merging it to `main` is a milestone-owner decision. GitHub
Pages may optionally mirror the built book.
