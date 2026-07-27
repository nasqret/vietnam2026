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

# 4. Push Peano Lab to staging; promote only a fully green milestone.
make deploy-peano-next
make deploy-peano
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
  are green.
- Formal artifacts are browsed on GitHub (`nasqret/vietnam2026/tree/main/artifacts`), not deployed to the
  server, so the landing page's artifact links point there.

## GitHub

The repository `nasqret/vietnam2026` is the source of record. Push the current
milestone branch; merging it to `main` is a milestone-owner decision. GitHub
Pages may optionally mirror the built book.
