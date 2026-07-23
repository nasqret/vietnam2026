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
# landing page + book + slides
rsync -avz --delete deploy/vietnam2026/ lts-faculty.wmi.amu.edu.pl:~/public_html/vietnam2026/
# browser lab
rsync -avz --delete lab-lambda/ lts-faculty.wmi.amu.edu.pl:~/public_html/lab-lambda/
```

## Subtasks
- [ ] Create public GitHub repo; first push.
- [ ] Deploy landing page (v1).
- [ ] Deploy browser lab (v1).
- [ ] Deploy book build once it's clean.
- [ ] Link check across live URLs; add a `.github/workflows` build+link-check CI.

## Acceptance criteria
- Both live URLs return 200 and render; GitHub shows the repo with README.
- A single `make deploy` (or `docs/DEPLOY.md` steps) reproduces the whole go-live.
