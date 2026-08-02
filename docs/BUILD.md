# Building the course materials

## Prerequisites

- Python 3.10+ (`pip install -r requirements.txt`) for the knowledge book.
- [`elan`](https://github.com/leanprover/elan) (Lean version manager) for the Lean artifact.
- Node is *not* required. The browser lab is fully self-hosted: Pyodide, xterm.js and the fonts are
  vendored under `lab-lambda/vendor/` (refresh them with `scripts/fetch_vendor.sh`), so it runs with
  no network access after the first load.

## The knowledge book (JupyterBook 1.x)

```bash
pip install -r requirements.txt
jupyter-book build book/          # → book/_build/html/
open book/_build/html/index.html  # index.html redirects to intro.html
```

## The Lean artifact (verified locally)

```bash
cd artifacts/lean
lake build                        # builds Artifacts.lean, sorry-free
printf 'import Artifacts\nopen Artifacts\n#print axioms add_comm'"'"'\n' > /tmp/check.lean
lake env lean /tmp/check.lean     # → "'Artifacts.add_comm'' does not depend on any axioms"
```
The project pins `leanprover/lean4:v4.28.0-rc1` (the locally installed toolchain) and uses **no
Mathlib**, so it builds in seconds. Current Lean stable is 4.32.0.

## The Lean FTA companion

The full natural-number Fundamental Theorem of Arithmetic is a separate,
Mathlib-backed artifact so the small course artifact above remains
Mathlib-free:

```bash
make lean-fta
```

This resolves the exact pinned Mathlib revision, builds
`artifacts/lean-fta/FTA.lean`, rejects `sorryAx`, and requires the declared
axiom footprint to be exactly `propext`, `Classical.choice`, and `Quot.sound`.
It proves finite-list existence and uniqueness up to permutation and is not
imported as a Peano theorem.

Agda / Rocq / Mizar artifacts are authored to standard idioms; run them under a local install of each
(`agda`, `rocq compile`/`coqc`, Mizar+MML). See [`../artifacts/README.md`](../artifacts/README.md).

## Local preview of the whole site

```bash
make book      # once — the preview serves book/_build/html
make serve     # → http://localhost:8000/  (Ctrl-C to stop)
```

`make serve` builds `_preview/` out of **symlinks** (so edits are live, nothing is copied) and serves
it with the same URL shape as the faculty server:

| Local URL | What |
|---|---|
| <http://localhost:8000/> | landing page |
| <http://localhost:8000/book/> | knowledge book |
| <http://localhost:8000/slides/> | the six decks |
| <http://localhost:8000/lab-lambda/> | the Lambda Lab |
| <http://localhost:8000/vietnam2026/…> | the same site under its production prefix |

That last row is the point of the script: the landing page links to the lab with an **absolute**
path (`/lab-lambda/`, because on the server the two live side by side under `~/public_html/`), and
some pages link back to `/vietnam2026/`. Serving the repo root or `_deploy/vietnam2026` directly
gives 404s for those; the preview tree resolves both shapes. `_preview/` is gitignored.

Only the lab, on its own:

```bash
make lab-serve                    # → http://localhost:8001/
```

To sanity-check the Python engine with no browser at all:

```bash
cd lab-lambda/py && python3 -c "import sys; sys.path.insert(0,'.'); import driver; print(driver.get_session().run('nf PLUS 2 3'))"
cd lab-lambda/py && python3 -m pytest tests/ -q      # the full engine suite
```

## One-shot

```bash
make book      # build the book
make lean      # build + axiom-check Lean
make lean-fta  # build + exact-axiom-check full FTA companion
make lab-serve # preview the lab
```
