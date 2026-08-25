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

To regenerate the exact and conservative definition-aware proof explorers
without rebuilding the whole book:

```bash
make book-proof-explorer             # Quadratic Reciprocity and Bertrand editions
make book-bertrand-defined-explorer  # exact and definition-aware Bertrand only
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

## Readable certificate-backed Lean exports

Generate a small, importable theorem together with its independently checked,
separately named proof-certificate module:

```bash
python3 scripts/export_peano_lean.py add_comm \
  --format compact --package-dir /private/tmp/peano-lean-addition --verify
python3 scripts/export_peano_lean.py prime_unbounded --format pretty
```

The package contains a reusable `PeanoLab/Presentation.lean` notation module,
content-addressed `Certificate.lean` and `Theorem.lean` modules, and a canonical
`manifest.json`. Verification uses the existing Mathlib-free sibling checker,
one bounded Lean worker, and no proof placeholders. The old self-contained
single-file export remains available as `--format full`. See
[`LEAN_CERTIFIED_PRESENTATION.md`](LEAN_CERTIFIED_PRESENTATION.md) for
edition boundaries, proof bundles, source layouts, and large-proof limits.

## Interactive theorem graph and Lean Live

Start the theorem explorer and its bounded, independently checked proof builder
from the repository root:

```bash
make lean-browser
```

Open the exact theorem graph at
<http://127.0.0.1:8787/book/_static/pa-proof-explorer/graph.html?target=PA000F> or its
definition-aware edition at
<http://127.0.0.1:8787/book/_static/pa-proof-explorer/defined/graph.html?target=PA000F>.
Select a theorem and choose **Build Lean proof** in the right-hand selected-node
panel. The browser shows actual dependency translation and Lean compilation
progress, permits cancellation, and offers the generated Lean source and
complete named-module ZIP after successful independent verification.

For an entirely readable strand whose self-contained source fits Lean Live's
share limit, **Open in Lean Live** sends that exact source directly to the
official editor. Certificate-backed strands and larger proof packages remain
downloadable; Lean Live does not automatically contain the separate Peano Lab
certificate-checker project. Conservative definitions are definitions, not new
axioms, and verification never uses `sorry`.

The service starts one proof worker, listens only on loopback by default, and
requires an existing installed Lean companion/toolchain. Browser jobs default
to a 1,024 MiB Lean memory ceiling and at most 256 dependency nodes. Choose
another local port with `make lean-browser PEANO_LEAN_BROWSER_PORT=8890`. A network-accessible
deployment additionally requires the explicit service `--public-host` switch;
ordinary static site hosting cannot run the required compiler service. See
[`LEAN_PROOF_STRANDS.md`](LEAN_PROOF_STRANDS.md),
[`LEAN_SELECTOR_UI.md`](LEAN_SELECTOR_UI.md), and
[`LEAN_LIVE_INTEGRATION.md`](LEAN_LIVE_INTEGRATION.md).

With the browser service still running, validate the entire real proof workflow
from another terminal:

```bash
make lean-browser-check
```

This checks the existing graph's interactive sidebar, compiles the complete
three-theorem `add_comm` strand, independently checks its standalone source,
compares the downloaded Lean file byte-for-byte against its Lean Live share,
and validates the safe generated-module ZIP.

The same controls are also injected into the Bertrand and six constructive
campaign graphs. For a small, genuinely new Alpha-v19 result, open
<http://127.0.0.1:8787/book/_static/constructive-frontier-explorer/pythagorean-fermat-four/explorer/defined/graph.html?target=PF0000>;
the selected `pythagorean_double_product` theorem has a nine-node dependency
strand and is correctly labeled **Alpha**, not Stable.

## Fully checked constructive Alpha v19 release

The opt-in Alpha-v19 edition contains **1,737 independently checked theorems**
and **5,779 checked dependency edges**: **432 unchanged Stable** results and
**1,305 Alpha-only** results, with **zero body-only or pending statements**.
It closes **84** historical obligations and adds **64** checked Pythagorean,
prime two-square, linear-congruence, and one-modulo-four prime theorems.
Regenerate its canonical artifacts or run every release, mutation, and
independent Lean bundle check with:

```bash
make peano-library-alpha-v19
make peano-library-alpha-v19-check
```

Inspect the resulting theorem or its complete dependency outline without
replaying a large certificate:

```bash
python3 scripts/export_peano_lean.py infinitely_many_primes_one_mod_four \
  --edition alpha --format pretty
python3 scripts/export_peano_lean.py infinitely_many_primes_one_mod_four \
  --edition alpha --format outline
```

In the browser, `pa lib alpha` reports the checked inventory and
`pa proof alpha infinitely_many_primes_one_mod_four` shows a bounded readable
proof strand. Neither preview claims fresh kernel replay or independent Lean
compilation; request an explicit bounded export and `--verify` for that audit.
Stable remains the default, and the still-open primitive Pythagorean inverse
and Fermat exponent-four strict descent are not asserted.

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
