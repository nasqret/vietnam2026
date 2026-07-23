# Building the course materials

## Prerequisites

- Python 3.10+ (`pip install -r requirements.txt`) for the knowledge book.
- [`elan`](https://github.com/leanprover/elan) (Lean version manager) for the Lean artifact.
- Node is *not* required to build; the browser lab ships as static files that pull Pyodide + xterm.js
  from a CDN at runtime.

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
lake env lean --run <(echo 'import Artifacts
open Artifacts
#print axioms add_comm')          # → "does not depend on any axioms"
```
The project pins `leanprover/lean4:v4.28.0-rc1` (the locally installed toolchain) and uses **no
Mathlib**, so it builds in seconds. Current Lean stable is 4.32.0.

Agda / Rocq / Mizar artifacts are authored to standard idioms; run them under a local install of each
(`agda`, `rocq compile`/`coqc`, Mizar+MML). See [`../artifacts/README.md`](../artifacts/README.md).

## The browser Lambda Lab (local preview)

```bash
cd lab-lambda
python3 -m http.server 8001       # → http://localhost:8001/
```
It loads Pyodide (~7 MB) once from jsdelivr, mounts the vendored engine into the Pyodide virtual FS, and
runs the REPL entirely client-side. To sanity-check the Python engine without a browser:

```bash
cd lab-lambda/py && python3 -c "import sys; sys.path.insert(0,'.'); import driver; print(driver.get_session().run('nf PLUS 2 3'))"
```

## One-shot

```bash
make book      # build the book
make lean      # build + axiom-check Lean
make lab-serve # preview the lab
```
