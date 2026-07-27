# Module 08 — Release & deploy

**Goal:** everything reproducible and live. Local git → public GitHub (`nasqret/vietnam2026`) → faculty
server, deploying **incrementally** as pieces are ready.

## Targets
- **GitHub:** `nasqret/vietnam2026` (public). Push `main`; enable Pages later for a mirror if useful.
- **Faculty server** (`bnaskrecki@lts-faculty.wmi.amu.edu.pl`, static Apache + PHP, no daemons):
  - `~/public_html/vietnam2026/` ← landing page, `book/_build/html`, `slides/`, artifact browse.
  - `~/public_html/lab-lambda/`  ← the built browser lab.
  - `~/public_html/peano-lab-next/` ← Peano Lab staging.
  - `~/public_html/peano-lab/` ← Peano Lab production, promoted only after staging gates.

## Deploy recipes
```bash
make deploy-site   # stages (_deploy/vietnam2026) + rsyncs landing page + book + slides
make deploy-lab    # rsyncs browser lab
make deploy-peano-next  # stages and publishes a clean, recorded candidate commit
make deploy-peano       # reassembles that unchanged commit and promotes it
```
Equivalent inline commands (the Makefile is the source of truth):
```bash
# landing page + book + slides (after `make stage`)
rsync -avz --delete _deploy/vietnam2026/ lts-faculty.wmi.amu.edu.pl:~/public_html/vietnam2026/
# browser lab
rsync -avz --delete --exclude '__pycache__' --exclude 'worker' lab-lambda/ lts-faculty.wmi.amu.edu.pl:~/public_html/lab-lambda/
```

## Subtasks
- [x] Create public GitHub repo; first push.
- [x] Deploy landing page (v1).
- [x] Deploy browser lab (v1).
- [x] Deploy book build once it's clean.
- [x] Link check across live URLs; CI runs the book/command gate, both lab suites, and the
      Lean/Rocq/Agda artifact checks on pushes to `main` or `peano-lab` and on pull requests.
- [x] Add isolated Peano staging/production targets and a Peano pytest CI job.
- [ ] Pin the Peano cache/compression contract and verify every application byte plus decoded WASM against local
      hashes before promotion.

## Acceptance criteria
- All four live targets return 200 and render; GitHub shows the repo with README.
- The explicit target sequence in `docs/DEPLOY.md` reproduces the go-live; `make deploy` intentionally
  excludes both Peano channels so they cannot bypass their staging gate.
