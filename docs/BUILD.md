# Building the course materials

For the current shared theorem/definition DAG, Hydra proof-search direction,
and post-training readiness, see
[`HYDRA_PRODUCT_ROADMAP.md`](HYDRA_PRODUCT_ROADMAP.md).

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
The project pins `leanprover/lean4:v4.28.0-rc1` and uses **no Mathlib**, so it
builds in seconds. Reproducibility follows the pinned toolchain rather than an
unstable claim about whichever upstream release is newest.

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

If an older `make lean-browser` process is already running, stop it with
`Ctrl-C` and start the command again so the service loads the current standalone
proof exporter and verification rules.

Open the exact theorem graph at
<http://127.0.0.1:8787/book/_static/pa-proof-explorer/graph.html?target=PA000F> or its
definition-aware edition at
<http://127.0.0.1:8787/book/_static/pa-proof-explorer/defined/graph.html?target=PA000F>.
Select a theorem and choose **Build Lean proof** in the right-hand selected-node
panel. The browser shows actual dependency translation and Lean compilation
progress, permits cancellation, and offers the generated Lean source and
complete named-module ZIP after successful independent verification.

For every reconstructible readable strand, Hydra generates one complete
self-contained proof, independently compiles it locally, and chooses the
shorter documented Lean Live `#code` or compressed `#codez` link. **Open in
Lean Live** receives exactly the verified source: all named dependency proofs,
only the definitions actually used, no Mathlib, no Peano Lab companion
imports, **no import statements whatsoever**, no `sorry`, and no additional
axioms. Lean's default prelude supplies the core language and tactics. The
service verifies the share decodes byte-for-byte to the checked source before
displaying it. A proof that still requires a checked certificate fallback or
remains oversized even after compression is downloadable but is never
misrepresented as independently runnable in Lean Live.

Compressed `#codez` links use Lean Live's actual unpadded LZ-String **Base64**
codec, with reserved `+` and `/` characters escaped as `%2B` and `%2F`. The
visually similar URL-safe LZ-String alphabet is incompatible with Lean Live and
must never be substituted: it silently changes proof text whenever its `-`
symbol occurs. Both Hydra's browser and its acceptance checker verify the
canonical escaped Base64 fragment against the exact compiled Lean source.

The service starts one proof worker, listens only on loopback by default, and
requires an existing installed Lean companion/toolchain. Browser jobs default
to a 1,024 MiB Lean memory ceiling, at most 1,024 dependency nodes, a 1 MiB
standalone proof-source limit, and a 512 KiB compressed Lean Live link limit.
All 1,890 historical Alpha-v22 theorems have dependency closures below the
node ceiling; their largest historical closure contains 557 named theorems.
The 59 additional Alpha-v23 results also lie below that ceiling: their
complete joint dependency certificate contains 616 named theorem nodes.
Extremely
large proofs may still exceed the separately enforced source, URL, or compiler
time limits and remain available through the checked local proof package.
Choose
another local port with `make lean-browser PEANO_LEAN_BROWSER_PORT=8890`. A network-accessible
deployment additionally requires the explicit service `--public-host` switch;
ordinary static site hosting cannot run the required compiler service. See
[`LEAN_PROOF_STRANDS.md`](LEAN_PROOF_STRANDS.md),
[`LEAN_SELECTOR_UI.md`](LEAN_SELECTOR_UI.md), and
[`LEAN_LIVE_INTEGRATION.md`](LEAN_LIVE_INTEGRATION.md).

Validate the entire real proof workflow with one command:

```bash
make lean-browser-check
```

If the local service is not already running, the checker automatically starts a
temporary loopback-only browser service and shuts it down when the check
finishes. An existing service is reused and left running. Pass
`PEANO_LEAN_BROWSER_CHECK_ARGS=--require-running` to disable automatic startup.

This checks the existing graph's interactive sidebar, compiles the complete
three-theorem `add_comm` strand, independently checks its standalone source,
compares the downloaded Lean file byte-for-byte against its Lean Live share,
and validates the safe generated-module ZIP.

To exercise the much larger prime-inverse Alpha campaign example explicitly:

```bash
make lean-browser-check \
  PEANO_LEAN_BROWSER_CHECK_ARGS="--theorem prime_inverse_prefix_fixed_cases --edition alpha"
```

A substantially larger campaign proof is also independently verified and
shareable: `prime_choose_unused_nonendpoint_orbit` has 159 theorem nodes and
generates 398,596 bytes of standalone Lean source with a 129,151-byte Lean Live
link. Check that complete proof on a free local port with:

```bash
make lean-browser-check \
  PEANO_LEAN_BROWSER_PORT=8902 \
  PEANO_LEAN_BROWSER_CHECK_ARGS="--theorem prime_choose_unused_nonendpoint_orbit --edition alpha"
```

For unusually large self-contained proofs, the browser accepts an explicit
4 MiB source and 1 MiB compressed-link policy while retaining a single bounded
Lean compiler:

```bash
make lean-browser \
  PEANO_LEAN_BROWSER_ARGS="--max-live-source-kib 4096 --max-live-url-bytes 1048576"
```

The same controls are also injected into the Bertrand and all historical and
current constructive-campaign graphs. For a small, genuinely new Alpha-v19
result, open
<http://127.0.0.1:8787/book/_static/constructive-frontier-explorer/pythagorean-fermat-four/explorer/defined/graph.html?target=PF0000>;
the selected `pythagorean_double_product` theorem has a nine-node dependency
strand, is correctly labeled **Alpha**, not Stable, and has a fully readable,
import-free, independently checked Lean Live proof with no certificate
fallback.

## Fully checked constructive Alpha v25 release

The opt-in current Alpha-v25 edition contains **2,080 independently checked
theorems** and **6,633 checked dependency edges**: **432 unchanged Stable**
results and **1,648 Alpha-only** results, with **zero body-only or pending
statements**. Its historical Alpha-v19 ancestor closed **84** historical
obligations and
added **64** checked Pythagorean, prime two-square, linear-congruence, and
one-modulo-four prime theorems. Historical Alpha v20 independently adds **39**
polynomial Horner, finite matrix-component, strict Bertrand-prime, and finite
continued-fraction theorems. Historical Alpha v21 preserves its complete
1,776-theorem v20 parent and adds **54** checked results: **23** arbitrary
natural/signed matrix-product theorems, **15** Euclidean execution/halving
theorems, and **16** binary modular-exponentiation theorems. Historical Alpha v22
preserves all 1,830 historical v21 entries and adds **60** genuinely checked
results: **21** total, functional, and unique binary-length theorems, **20**
Euclidean gcd-invariant/terminal-state identification theorems, and **19**
complete supplied-digit binary modular execution/power-correctness theorems.
Its historical **240-node**, **597-edge**, **1,099,541-byte** proof bundle is
independently accepted by both the original intuitionistic kernel and the
separately compiled Lean verifier; SHA-256 is
`95e5f8a3baef113721d748f9d7071864b4bf9511737a27a1272d2695428fb938`.

Historical Alpha v23 preserves every historical v22 theorem and adds **59**
checked results: **17** complete logarithmic Euclidean-GCD proofs, **24**
canonical arbitrary-exponent binary-digit/execution proofs, and **18** proofs
of infinitely many primes congruent to three modulo four. Its complete
**617-node**, **1,871-edge**, **2,518,315-byte** proof bundle is independently
accepted by both unchanged checkers; SHA-256 is
`cc0051da2cac31e382c79223999d448a1119f62aa448f1c7f68a6b9c3edf9d11`.

Historical Alpha v24 preserves all **1,949** historical v23 theorems and adds
**59** newly checked results: **17** arbitrary signed cofactor-minor and
four-dimensional determinant theorems, **15** exact coupled Horner and formal
derivative theorems, and **27** finite pairwise-coprime CRT/arbitrary-list-LCM
theorems. Its complete **203-node**, **502-edge**, **738,923-byte** proof
bundle is independently accepted by the unchanged original kernel and Lean
verifier; SHA-256 is
`627e39ed29b10db48bf37d5bef8750d48009a7524c822a7c5e7c83e96a8e9cf9`.

Current Alpha v25 preserves all **2,008** historical v24 theorems and adds
**72** newly checked results: **29** signed cofactor/alternating-fold
theorems, **19** exact Taylor/formal-derivative and qualified one-step Hensel
theorems, and **24** noncoprime CRT compatibility/gcd-LCM lattice theorems.
Its complete **302-node**, **820-edge**, **1,041,166-byte** proof bundle is
independently accepted by the unchanged original kernel and Lean verifier;
SHA-256 is
`d4532076049be869e4e397d0fcee81b668bd3fd5c7d9173028bb1bdb80b9793a`.

Actual Euclidean terminal-state gcd identification with
`steps <= 2 * BitLen(b) + 1`, canonical digits and genuine modular execution
with `operations <= 3 * BitLen(e) + 2`, and infinitely many primes three
modulo four were **proved in historical v23**. Historical Alpha v24 additionally
proves signed minors, exact natural formal derivatives, and pairwise-coprime
finite CRT. Current v25 proves exact alternating cofactor folds, formal Taylor
correction with qualified one-step Hensel lifting, and exact compatible
noncoprime CRT merges. Unrestricted-dimensional determinants/rank/lattices,
unrestricted prime-power Hensel lifting, and the full arbitrary
pairwise-compatible noncoprime-list CRT milestone remain open. Regenerate the
current artifacts or run every release,
mutation, and independent Lean bundle check with:

```bash
make peano-library-alpha-v25
make peano-library-alpha-v25-check
```

The historical immutable parents remain reproducible with
`make peano-library-alpha-v20-check` and
`make peano-library-alpha-v21-check`, and
`make peano-library-alpha-v22-check`, and
`make peano-library-alpha-v23-check`, and
`make peano-library-alpha-v24-check`.

Inspect the resulting theorem or its complete dependency outline without
replaying a large certificate:

```bash
python3 scripts/export_peano_lean.py infinitely_many_primes_one_mod_four \
  --edition alpha --format pretty
python3 scripts/export_peano_lean.py infinitely_many_primes_one_mod_four \
  --edition alpha --format outline
python3 scripts/export_peano_lean.py signed_matrix_two_determinant_exists \
  --edition alpha --format compact \
  --package-dir /private/tmp/peano-lean-signed-determinant \
  --verify --lean-project ../peano-lab-lean \
  --max-memory-mib 768 --max-verify-seconds 60
```

In the browser, `pa lib alpha` reports the checked inventory and
`pa proof alpha infinitely_many_primes_one_mod_four` shows a bounded readable
proof strand. Neither preview claims fresh kernel replay or independent Lean
compilation; request an explicit bounded export and `--verify` for that audit.
Stable remains the default, and the still-open primitive Pythagorean inverse
and Fermat exponent-four strict descent are not asserted. The complete
arbitrary matrix-and-lattice milestone likewise remains open despite 33
independently checked finite matrix and arbitrary-product components in
historical v21, **50 checked components in historical v24**, and **79 checked
components in current v25**.

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
make serve     # preview the whole site locally
make lab-serve # preview just the lab
```
