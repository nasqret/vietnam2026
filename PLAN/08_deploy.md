# Module 08 — Release & deploy

**Goal:** everything reproducible and live. Local git → public GitHub (`nasqret/vietnam2026`) → faculty
server, deploying **incrementally** as pieces are ready.

## Targets
- **GitHub:** `nasqret/vietnam2026` (public). Push `main`; enable Pages later for a mirror if useful.
- **Faculty server** (`bnaskrecki@lts-faculty.wmi.amu.edu.pl`, static Apache + PHP, no daemons):
  - `~/public_html/vietnam2026/` ← landing page, `book/_build/html`, `slides/`, artifact browse.
  - `~/public_html/lab-lambda/`  ← the built browser lab.

## Deploy recipes
```bash
make deploy-site   # stages (_deploy/vietnam2026) + rsyncs landing page + book + slides
make deploy-lab    # rsyncs browser lab
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
- [x] Link check across live URLs; CI runs build + the book-command replay gate,
      Lean/Rocq/Agda artifact checks, and the 304-test lab suite on every push.

## Acceptance criteria
- Both live URLs return 200 and render; GitHub shows the repo with README.
- A single `make deploy` (or `docs/DEPLOY.md` steps) reproduces the whole go-live.
