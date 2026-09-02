# An Introduction to Automatic Theorem Proving in Mathematics

> A six-lecture VIASM mini-course taking you from the **λ-calculus and type theory** through
> **Lean** all the way to the **auto-formalization of research mathematics** — building the
> foundations first, then climbing.

**Course page (VIASM):** <https://viasm.edu.vn/en/hdkh/Mini-Course_AIATPM>
**Landing page (notes hub):** <https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026>
**Live Lambda Lab (runs in your browser):** <https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda>
**Live Peano Lab (kernel-checked PA proofs):** <https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/>
**Interactive proof explorers:** <https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/>
**Multiscale number-theory research atlas:** <https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/grand-campaign/>
**Author:** dr Bartosz Naskręcki — Faculty of Mathematics and Computer Science, Adam Mickiewicz University in Poznań · Centre for Trustworthy AI (CCAI), Warsaw University of Technology

---

## The six lectures

| # | Title | One line |
|---|-------|----------|
| 1 | **A general introduction to type theory** | Judgments, simply-typed λ-calculus, Church vs Curry, and why proof assistants stand on type theory rather than set theory. |
| 2 | **Simple calculations with the Church (λ-)calculus** | Untyped λ-calculus, β/η-reduction, Church booleans & numerals, the predecessor, and the Y-combinator — every β-step reproducible in the Lambda Lab. |
| 3 | **Propositional logic proofs** | Natural deduction and the BHK / Curry–Howard reading of the connectives, taught through Emily Riehl's *A Reintroduction to Proofs* Lean game. |
| 4 | **Introduction to Lean** | Term vs tactic mode, `Nat` and induction, the Natural Number Game and Macbeth's *Mechanics of Proof* — a first honest end-to-end proof. |
| 5 | **Advanced Lean** | Dependent types in practice, typeclasses, `simp`/`ring`/`linarith`/`omega`, `calc`, Mathlib search, and a real analysis/algebra proof. |
| 6 | **Auto-formalization of mathematics with Lean** | The 2024–2026 AI-for-proof landscape and the **EML project** (`arXiv:2603.21852`) as a worked human + AI + kernel case study. |

The exact abstracts, session plans and reading lists live on the [landing page](book/) and in the
[knowledge book](book/); this README is the map.

---

## What is in this repository

| Path | What it is |
|------|------------|
| `index.html` | The **landing page** — hero, the six-lecture plan, descriptions, and cross-links. Deployed to `/vietnam2026`. |
| `book/` | The **knowledge book** — a [JupyterBook](https://jupyterbook.org/) with the full text-friendly notes: mathematics, code, and links. This is the "learning data". |
| `slides/` | **Presentations** — one reveal.js deck per lecture, to follow along live. |
| `vault/` | The **Obsidian vault** — the atomic, wiki-linked knowledge base behind the book. |
| `artifacts/` | **Formal proofs** in four systems, plus `lean-fta/`: a pinned, sorry-free Lean proof of prime-factorization existence and uniqueness up to permutation. |
| `lab-lambda/` | The **Lambda Lab**, repackaged to run **directly in the browser** (Pyodide + xterm.js). Deployed to `/lab-lambda`. |
| `peano-lab/` | The **Peano Lab** browser prover, its independent PA kernel, 432-entry checked arithmetic ladder, and reproducible proof-trace corpus. |
| `research/` | The **research dossier** — including the 433-node arithmetic catalog (432 checked and one representation-blocked), native and Lean FTA certificates, the quadratic-reciprocity campaign, and source/license maps. |
| `scripts/` | Book replay gate plus the deterministic Peano trace generation, export, and kernel-judged evaluation pipeline. |
| `docs/` | Lecturer-facing docs: how to build, deploy, and run each piece. |
| `MEMORY.md` · `JOURNAL.md` · `PLAN.md` + `PLAN/` | Project **memory**, dated **journal**, and the multi-level **plan**. |

The certificate calculus and reference checker also have an independent Lean
formalization in
[`nasqret/peano-lab-lean`](https://github.com/nasqret/peano-lab-lean).
Lean proves checker acceptance implies a `Derives` judgment and that every such
judgment is true in the standard natural numbers, relative to Lean's kernel
and reported standard axioms. Historical WMI job `211445` covers the cut-free
kernel. The production `Cut` rule and `peano-lab-v2` codec at immutable source
commit
[`ab966fd1`](https://github.com/nasqret/peano-lab-lean/commit/ab966fd1b8207b99eea0c9dc3d719c6e61ef73c2)
passed the complete pinned Lean 4.31/WMI matrix in job
[`218358`](https://github.com/nasqret/peano-lab-lean/tree/8515336ab3b89ca6f0c8ab521d01745a220b5211/artifacts/wmi/218358).
Canonical decoding and finite differential tests support Python/Lean
correspondence but are not an exhaustive theorem about CPython execution.

The current published proof-site and preview mathematical release is
[Alpha v34](artifacts/peano-library/channels-v34.json), with **4,223 checked-use
entries** and the unchanged **432-theorem Stable** default. It preserves all
4,092 v33 entries and adds **131 theorems**: 119 polynomial gcd/Bézout results
and 12 congruence arithmetic results, giving **13,816 proof-dependency edges**
and **68 proof families**. **The v34 proof site and Peano preview are deployed;
protected Peano production promotion remains deferred.** The readers retain the Quadratic Reciprocity
design and separate **407 conservative definitions / 884 expansion arrows**
from proof dependencies and campaign planning.

The polynomial checkpoint proves normalized gcd/Bézout existence, greatestness
and uniqueness up to formal coefficient equivalence, not equality of encodings
or uniqueness of Bézout coefficients. Neither it nor the congruence tranche
closes full G091, Jordan-totient multiplicativity (G008) or the entire F02 campaign.
All **22 fresh proof jobs and six same-live publication phases / 171 UI cases
passed**. G012 retains its v19 first admission and G009 its v32 first admission.
Stored working receipts and private display preflights are not release authority.
Only the new logical catalogue capacity increases, from 4,096 to 8,192 rows;
the original kernel, proof and resource limits remain unchanged.

Source commit `97a1ed75c3a307eebe872774a82a8822c2c2ffeb` was pushed and delivered
additively, with entrypoints published last. All **13,549 proof-site files** and
**630 preview files** matched remote SHA-256 checks; **230 proof-site HTTPS
requests across all 68 families** and **eight critical preview HTTPS requests**
passed. Preview serves app `a-ea9ae0d7f72a`, build `2026-09-02a`. The production
entrypoint and both hosting-policy files were unchanged. Fresh unversioned
preview and production responses still omit required `Cache-Control: no-store`,
so the production gate remains blocked, not waived. These are byte-delivery
checks, not a manual browser-visual verification. See the
[v34 deployment procedure](docs/DEPLOY.md#published-v34-proof-site-and-preview-production-deferred)
and [delivery observations](research/arithmetic-library/working/alpha-v34-release-v1/deployment-observations-v1.json).

The historical constructive-verification milestone closes the full exact
quadratic-reciprocity endpoint. The unchanged original Peano kernel accepts
`quadratic_reciprocity_combined` from the empty context as one certificate with
54,870 structural nodes, 35,052 proof objects, and depth 129. A separate
canonical, self-contained certificate DAG retains all 557 actual theorem
bodies and 1,787 dependencies; the independent compiled Lean verifier accepts
its exact final root. The 2,790,229-byte artifact is retained at
[`research/arithmetic-library/artifacts/quadratic-reciprocity-proof-bundle-v1.json`](research/arithmetic-library/artifacts/quadratic-reciprocity-proof-bundle-v1.json)
with SHA-256
`3cd040d145f1004d07d277c66a3ffbcb355cd9c4b21938d79a6ec51b4258709c`.
[`scripts/export_peano_lean.py`](scripts/export_peano_lean.py) also translates
individual checked Peano certificates directly into completed, independently
compiler-checked Lean theorems. Its optional compact packages separate short,
human-readable theorem modules from named, independently checked certificate
modules while preserving exact constructive Peano definitions; the full
standalone certificate remains available for audits. See the
[readable certified Lean export guide](docs/LEAN_CERTIFIED_PRESENTATION.md).
Historical immutable Alpha v16 first promoted the 315 genuinely closed
quadratic-reciprocity results; Alpha v17 then closed both supplementary laws.
Historical Alpha v18 subsequently closed strict Bertrand, multidigit Lucas,
both Kummer endpoints, universal four squares, and the complete all-natural
two-square criterion. Historical immutable **Alpha v19** closes all **84**
remaining historical obligations and adds **64** genuinely proved results:
**44 Pythagorean forward-construction theorems, the exact prime two-square
classification, nine complete linear-congruence theorems, and ten theorems
proving infinitely many primes congruent to one modulo four**. Historical
immutable **Alpha v20** preserves every one of those 1,737 historical rows
and adds **39 independently proved results**: **seven natural polynomial
Horner theorems, ten finite matrix and dot-product components, thirteen
strict Bertrand prime-window and prime-chain theorems, and nine finite
continued-fraction theorems**. Historical immutable **Alpha v21** preserves that
entire 1,776-row historical parent and adds **54 independently proved
results**: **23 arbitrary natural/signed matrix-product and determinant
theorems, 15 Euclidean execution and two-step-halving theorems, and 16 binary
modular-exponentiation theorems**. Historical immutable **Alpha v22** preserves
that complete 1,830-row parent and adds **60 independently proved results**:
**21 total, functional, and unique first-order binary-length theorems, 20
Euclidean gcd-invariant and terminal-state identification theorems, and 19
complete supplied-digit binary modular execution/power-correctness
theorems**. Historical immutable **Alpha v23** preserves every one of those
1,890 checked results and adds **59 independently proved theorems**: **17
complete logarithmic Euclidean-GCD theorems, 24 canonical binary-digit and
logarithmic modular-execution theorems, and 18 theorems proving infinitely
many primes congruent to three modulo four**. Historical immutable
**Alpha v24** preserves that complete 1,949-theorem parent and adds **59
independently proved results**: **17 signed-matrix/minor theorems, 15 exact
natural-polynomial formal-derivative theorems, and 27 finite-list CRT/LCM
theorems**. Historical immutable **Alpha v25** preserves all 2,008 independently
checked predecessor results and adds **72 genuinely proved theorems**: **29
signed-cofactor and alternating-fold theorems, 19 exact Taylor and one-step
Hensel-lifting theorems, and 24 non-coprime CRT-compatibility and gcd/LCM
lattice theorems**. In that release, all **2,080 enrolled theorems have independently checked-use
authority**: **432 Stable** and **1,648 Alpha-only**, with **zero body-only or
pending entries**, **6,633 checked dependency edges**, and **53 dependency
layers**. The **432-theorem default Stable edition remains
unchanged**. Every historical flagship bundle, the historical **590-node
Alpha-v20 next-layer certificate**, the historical **209-node Alpha-v21
advanced-layer certificate**, the historical **240-node Alpha-v22
transport-layer certificate**, the historical **617-node Alpha-v23
milestone-closure certificate**, the historical **203-node Alpha-v24
research-layer certificate**, and the historical **302-node Alpha-v25
breakthrough-layer certificate** are independently checked by the original
intuitionistic kernel and the separately compiled Lean verifier. Arbitrary
natural and signed matrix multiplication, unique first-order `BitLen`, actual
Euclidean terminal-state gcd identification with the exact
`steps <= 2 * BitLen(b) + 1` bound, arbitrary-exponent canonical binary
digits with actual power-correct execution and
`operations <= 3 * BitLen(e) + 2`, and infinitude of primes three modulo four
are proved. Exact signed first-row cofactor families, quadratic Taylor
remainders, constructive one-step Hensel lifts, and canonical non-coprime CRT
under exact merge compatibility are also proved. At that historical checkpoint,
the stronger unrestricted matrix/lattice milestone **T13**, unrestricted
prime-power Hensel milestone **G095**, and fully pairwise-compatible finite CRT
milestone **G011** were
genuinely **OPEN**, as were higher reciprocity laws, three squares, and Fermat
exponent-four descent.

The [historical constructive number-theory research atlas](book/_static/constructive-grand-campaign/index.html)
organizes that checkpoint within **five mathematical domains**, **twelve
families**, **120 major goals**, **16 reusable constructive tools**, **eight
existing anchors**, and **179 shared mathematical terms**. Its five-level
navigation connects the complete programme to individual campaigns, verified
theorem roots, definition-aware proof graphs, exact shared notation
dependencies, and the honest still-open research frontier. Actual proof
prerequisites remain visibly separate from conservative display definitions,
future planning vocabulary, and conceptual mathematical connections. The
shared registry contains **120 hygienically checked conservative definitions**,
**214 actual definition prerequisites**, and **88 signature-verified links**
from blueprint vocabulary into the local proof explorers.

The 432-entry native ladder—23 legacy, 212 foundation, 12 mod-five, 137
quadratic-residue, and 48 strict-HA theorems—reaches the Fundamental Theorem of Arithmetic
without adding lists, division, remainder, gcd, or factorization as primitive
symbols. Finite factor sequences and their prefix products are represented by
expanded Gödel-β relations; code equality is extensional on the selected
prefix. The checked dependency spine includes generic division with
remainder, relational gcd, balanced-natural Bézout, Gauss cancellation,
constructive prime search, Euclid's lemma, binary and bounded CRT, β recoding,
prefix-product traces, greatest-prime-divisor descent, canonical factorization
existence, uniqueness, and a prime strictly above every supplied bound. The
last result is constructive: choose a nonzero common multiple through the
bound, take a prime divisor of its successor, and rule out a prime at or below
the bound because it would divide both consecutive numbers and hence divide
one. The exact native FTA certificate has 73,767
structural nodes, depth 99, 2,184 self-contained Cuts, and SHA-256
`fd978f59bf3b0aa7b6c9ec1bc92ab5e7bbf949c25309173e098bd8f3b8de0958`.
It checks from the empty context using only PA1–PA6 and ordinary induction; it
does not use double-negation elimination. A 137-certificate checkpoint forms a
systematic quadratic-reciprocity foundation: parity and residue decision,
finite folds, factorial and power algebra, small-modulus classifications,
modular units, sign and positive-half-range bridges, β-prefix swap/reindex,
constructive finite pigeonhole, replacement balance, and exact swap-last
product invariance. Those 137 admitted certificates do not themselves claim
the reciprocity law. The 48 strict-HA entries comprise nine canonical
remainder/congruence/modular-inverse interfaces, 16 public K4 gcd/LCM rows, and
23 selectively admitted M5 generalized-CRT rows. The K4 rows provide the
universal-property LCM core, its constructive totality and unique-existence
bridge, and the gcd-times-LCM product identity.
The M5 public closure occupies indices 409--431 and exposes arbitrary-modulus
solvability iff gcd compatibility, the complete relational-LCM solution class,
the exact zero/nonzero canonical boundary, and a raw-input constructive
solution-or-obstruction endpoint. Six reviewed convenience rows remain private.
A separate registry-isolated quadratic-reciprocity campaign stack has now
closed its exact sign-free combined root, both through a complete ordinary
unchanged-kernel certificate and through the independently Lean-verified
557-node shared dependency DAG described above. The optimized combined body
itself is `3/65/113/35` (dependencies/commands/nodes/depth). Public
Stable promotion, a fresh pinned WMI receipt, and remote publication remain
separate operations; the complete proof already has checked-use authority in
the opt-in Alpha release. The historical Stable catalog
has 433 entries: 23 `checked_existing`, 409 `checked_m20`, no planned theorem,
and one `blocked_by_language` conventional
integer-coefficient Bézout interface. This is a local draft-PR checkpoint, not
a deployment claim. The generated 432-theorem snapshot has 1,982,360
structural nodes, 468,010 distinct proof objects, 57,692 structural Cut
occurrences, 373 Cut-bearing certificates, and 1,185 dependency edges, with
ordered root
`4d02dc439d53533e8992a471b26ee34059fb6001f822041e42c56b2cc0a7a079`.
The synchronized vault contains 432 generated theorem notes, 531 total notes,
and 5,377 internal links. The released
source-bound corpus retains 13,344 transitions in 1,692
kernel-checked sessions under fingerprint
`6fc52e25f17dc2ff0c0e7a141c350430d6aa1d0a7a87b82e22840f442f666939`;
its isolated smoke has 494 sessions, 9,235 raw/9,232 unique transitions, and
all 247 authored QEDs. The append-only M5 admission leaves that frozen
first-247 model prefix unchanged. The integrated local browser candidate
deterministically verifies as build `2026-08-04i`, application
`a-b544a04993a1`, with 180 worker
sources; it assembles successfully in the local content-addressed stage and is
not deployed. The
strict Jupyter Book rebuild completes over all 47 sources; its post-build
integrity gate reports zero broken relative targets or fragments and
byte-identical explicit and defined Proof Explorer trees.
The existing 194 deep links and 47 session blocks containing 287 commands
verify. Its guided zero-to-FTA route and
generated interactive atlas embed all 432 exact statements, authored proof
recipes, and 1,185 dependency edges with searchable navigation. The selected post-merge
compatibility matrix passed 1,183 tests with five intentional skips, including
six loopback-server tests run outside the socket-restricted sandbox; this is
not relabeled as the complete 220-file Peano suite. Historical pre-closure QR
cluster attempts are retained for provenance; they are not the status of the
new independently checked local final certificate. Full 136-gate job
`187187`, against exact dirty snapshot
`2bab0898a5bc628a0e1f06b5e6cdf56af86fe39c2fdbeaaa4147ac43d2c7faaa`,
failed closed after 39 seconds at gate 5: four scaled-inverse gates passed,
then the dependency-hygiene mutation test exposed an unused `succ_ne_zero`
edge. The remaining 131 gates did not run, so that historical job was not a QR
result. Corrected full job `210714`, from exact clean
snapshot `989011c0…1757`, later failed closed after 8 minutes 29 seconds at
gate 15/136: 14 gates passed, then the direct-edge mutation audit showed that
replacing `odd_upper_remainder_reflection -> add_succ_left` did not invalidate
the certificate. The remaining 121 gates did not run. This is a second
dependency-minimality failure, not a kernel-soundness failure or a QR result.
The new complete local closure receipt documents the successful final ordinary
kernel check and independent Lean verification; no new pinned WMI run is
represented as having occurred. No in-app browser was attached for this
checkpoint, so direct Pyodide and rendered
book UI smokes are explicitly unclaimed.

The current proof-policy experiment is implemented as `model-v3`: 8,494 exact
authored predecessor-prefix transitions from its frozen 247-theorem training
authority plus
a version-2 deterministic plan for 70,000 synthetic rows, 32,600 unique roots,
and all 51 schemas. Its split and attestation rules keep catalog-derived proofs
train-only and reject held-out targets from every intermediate state. A
lossless v3-only prompt encoding keeps the audited worst stress-proof turn at
29,111 of Qwen's 32,768 native tokens. WMI preparation `172536` completed the
library lane and then failed closed on an over-limit synthetic ring instance;
retry `172729` generated the complete split, continuation `173040` independently
replayed and audited it, and job `213641` published the verified immutable seal
with content SHA-256
`7b22bdf083894e3d87b84fc463ff537a75eeecba8e34098429db215592ec6b5b`.
The first current-source sealed-preparation attempt, job `214264`, then failed
closed before runtime smoke or model loading: the selected train curriculum
contained 73,446,475 tokens, above the reviewed 70,000,000-token ceiling. The
reviewed retry, job `217123`, raised only that linear ceiling to 74,000,000 and
passed the complete token audit. It then ran the representative LoRA and real-
Trainer smoke steps but failed closed before publishing the smoke report: the
live model still carried Accelerate's BF16/FP32 forward wrapper, while the
fresh reload used the bare inference forward, so their exact output
fingerprints could not agree. The repair removes and verifies that wrapper
before saved-policy admission in both smoke and production. Fresh same-source
preparation `217851` subsequently passed every gate, and guarded production job
`217859` completed the registered 649-update rank-32 Qwen3-1.7B run on one WMI
A100. Trained evaluation `218171` and the revision/configuration-pinned
pretrained comparison `218172`, whose report declares no PEFT adapter,
completed sequentially. Their immutable four-goal `k=1` reports are 3/4 and
0/4; all three trained proof claims independently replay through the Peano
kernel, while the induction-heavy goal remains unsolved. Ordinary replay still
rejects the trained report's incomplete historical nested environment, but the
version-pinned trained and pretrained recovery attestations and their paired
cross-binding pass as `paired_launch_smoke_admitted`. This admits only that
narrow launch smoke. Base weight shards were not content-hashed before and
after loading, complete raw generation/extraction/search-edge transcripts are
absent, and four goals cannot establish bit-for-bit base identity, a causal or
statistical training effect, broad PA ability, or induction capability.

---

## Hydra: one verified proof-development workflow

Hydra is the untrusted proof-search, proof-optimization, proof-discovery, and
post-training layer of the same Peano product. It never introduces a second
kernel, a parallel theorem collection, or a parallel definition registry.
Every accepted route is freshly replayed against its original closed theorem
through the unchanged independent kernel.

The canonical product has exactly two growing mathematical graphs: the sealed
**2,080-theorem, 6,633-edge checked theorem DAG**, and the independent
**120-definition, 214-edge reviewed conservative definition DAG**. Research
milestones, browser notation references, and blueprint vocabulary remain
separate planning/presentation evidence. The ordinary tactic surface remains
Stable-only; checked Alpha use requires an exact full-digest edition identity
and finite explicit theorem/tactic authority. The historical Qwen3-1.7B
adapter keeps its immutable 247-theorem training environment.

Run the integrated local product checks and deterministic development-data
preparation with:

```console
make hydra-check
make hydra-prepare
make hydra-posttrain-ready
```

The preparation workflow writes checked proof-state transitions,
independently verified shorter-route preferences, unadmitted checked
discovery receipts, and exact epoch/file identities into `_deploy/hydra/`.
The complete `hydra-posttrain-ready` workflow independently replays a bounded
mixture of Stable and Alpha proofs, quarantines every historical held-out
theorem and its complete lineage from **both** training and validation,
prepares a fresh Alpha-authorized Qwen corpus, and verifies a matched
pretrained/trained evaluation plan. A demonstrated safe run checks **192
theorems**, including **91 Alpha-only results**, and produces **1,798
independently checked tactic transitions**. Dependency-closure profiling
prevents short-looking imports from loading large flagship proof bundles.
Its separate bounded symbolic control independently proves **three of four**
historical benchmark goals; the induction-heavy fourth remains honestly
`unknown`, and no unrun model receives an invented score.

Preparation never trains or deploys a model, promotes a theorem, asserts
global tactic optimality or semantic novelty, or claims an LLM advantage.
Actual bounded BF16 LoRA training is separate and explicit:

```console
make hydra-posttrain-execute  # one prepared CUDA GPU and pinned Qwen weights
```

The first Alpha-v25 run has now completed on Helios: **222 optimizer steps**,
then **0/4 pretrained → 3/4 trained** on the four diagnostic goals. All three
model-generated proofs independently replayed locally. The fixed symbolic
control also solves **3/4**; no advantage over it is demonstrated, and the
fourth goal remains unknown. The base model's failures were malformed tactic
output, so this measures adaptation to Hydra's interface rather than broad
mathematical superiority. Read the
[experiment report and independently replayable evidence](artifacts/peano-hydra/alpha-v25-posttrain-2026-08-26/README.md).

The next isolated `catalog-460` curriculum is **prepared, not trained**:
**460 checked routes**, **7,154 transitions**, and **7,129 training rows**
after the original historical-goal quarantine. Its 12-row development set
has not expanded with the training set.

The new **model-free DEV run** measures broader native search: closure solves
**16/64** generated goals and the generic symbolic portfolio **48/64**.
The four historical diagnostics are reported separately: **2/4** versus
**3/4**, with consecutive-product evenness still unknown. Independent
verification replayed **69 positive proofs** and checked **130 completed
policy rows**; six portfolio workers reached the three-CPU-second guard and
remain unknown. There were no model calls, external solvers, imports, or
retrieval. This narrower authority is not comparable with the old Alpha
model/control scores. See the [DEV guide](docs/HYDRA_DEVELOPMENT_EVALUATION.md)
and [archived results](artifacts/peano-hydra/development-2026-08-27/README.md).

The lineage audit joins all eight generated families into **one component
with 2,048 catalog members**. All eight families are **blocked for unseen-model
comparison** with both existing preparations; 64 goals are not 64 independent
lineages. The bounded native seven-action DEV protocol and the
[reference/lineage review workflow](docs/HYDRA_REFERENCE_REVIEW.md) are
implemented. The latter prepares authenticated component proposals, fresh
Lean reference checks, and bounded cold-replay evidence; it never grants
human approval or seals a benchmark. Full H0.3 and H0/H1/H5 acceptance remain
open.

The [archived Alpha-v25 reference execution](artifacts/peano-hydra/reference-review-2026-08-27/README.md)
records eight freshly built Lean 4.28 modules, a passing axiom audit, and
**1,321 matching fixture outcomes**. Cold replay checked **14/16 targets in
each pass**, yielding 28 positive receipts; four resource-limited workers
remain unknown. The allocation review is still blocked, with no unexposed
DEV component under the retained audits. Fresh frozen-source archive
verification passed; it does not close the remaining review gates.

**The single next milestone is a human-reviewed new-lineage/reference
readiness bundle:** reviewed model-facing TRAIN/DEV lineage separation,
the required H0 semantic/reference evidence in the pinned Lean 4.31
environment, and two complete cold library passes before any further GPU
comparison. Lean 4.28 checks are compatibility evidence only; a cold sample
is not a full-library replay. Do not train `catalog-460` and present these
DEV goals as unseen.

The historical 247-theorem adapter remains untouched. The active next track
and honest experimental gates are in the
[single Hydra product roadmap](docs/HYDRA_PRODUCT_ROADMAP.md) and the
[verified post-training guide](docs/HYDRA_POST_TRAINING.md).

---

## Design principle

Every idea is introduced **twice**: once informally (a picture, a calculation you can run in the
Lambda Lab, a game level) and once formally (a definition, a theorem, a machine-checked proof). The
course reuses and extends the author's earlier material — the *Falenty 2026* λ-calculus book and lab
(`nasqret/falenty-2026`) and the EML formalization (`nasqret/eml-formalization`) — so the notes are
continuous with work that already exists.

## Quick start (local build)

```bash
# 1. Python environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Build the knowledge book
jupyter-book build book/

# 3. Serve the landing page + lab locally
python3 -m http.server 8000   # then open http://localhost:8000/

# 4. Check the Lean artifacts
cd artifacts/lean && lake build
```

See [`docs/BUILD.md`](docs/BUILD.md) and [`docs/DEPLOY.md`](docs/DEPLOY.md) for the full pipeline.

## Unified local Peano terminal

When this worktree is paired with the frozen diagnostic-model worktree, the
installed `pa` launcher exposes both authorities without mixing their Python
imports:

```text
pa native    # this model-free 432-theorem source tree
pa model     # frozen 247-theorem trained-policy environment
pa           # backward-compatible alias for `pa model`
```

At the native `pa>` prompt, inspect the current library with `pa lib`, start a
manual proof with `pa prove FORMULA`, and import a checked fact with
`use THEOREM`. For example:

```text
pa prove forall n. n * 1 + 0 = n
use mul_one
intro n
specialize mul_one n
rewrite mul_one
simp
qed
```

For automation, repeat `-c` without opening an interactive terminal:

```bash
pa native -c 'pa lib mul_one'
```

Native mode requires Python 3.10 or newer and does not verify or
load model artifacts. Each selected theorem is nevertheless reconstructed,
embedded through checked `Cut` nodes, and checked again as part of the final
empty-context certificate.

The opt-in research channel keeps Stable as the default. Inspect its evidence
without replaying every certificate using `pa lib alpha`; open the completed
root with `pa lib alpha quadratic_reciprocity_combined`, or explicitly check
one bounded admitted theorem using `pa lib alpha check THEOREM`. The safe
theorem-first `pa lean alpha THEOREM` preview and readable
`pa proof alpha infinitely_many_primes_one_mod_four` proof strand inspect
authenticated metadata without replaying large certificates. Explicit terminal
exports and `--verify` perform the requested proof and independent Lean
checks within their reviewed resource limits. Rebuild or verify the exact
fully checked release with `make peano-library-alpha-v21` or
`make peano-library-alpha-v21-check`; the historical v20 targets remain
available for their unchanged parent snapshot.

## Interactive Lean proof browser

```bash
make lean-browser
```

Open <http://127.0.0.1:8787/book/_static/pa-proof-explorer/graph.html?target=PA000F>, select
a theorem, and choose **Build Lean proof** in its right-hand panel. Hydra
reconstructs its checked dependency strand on demand, reports translation and
Lean compilation progress, permits cancellation, and provides both Lean-source
and complete-module ZIP downloads. Every offered Lean Live proof is
independently compiled, entirely self-contained, free of Mathlib/private
imports/placeholders, contains no import statements at all, and is shared
using the shorter documented plain or
compressed editor link. Stable and opt-in Alpha checked-use theorems retain their distinct
release boundaries. See the
[readable proof-strand guide](docs/LEAN_PROOF_STRANDS.md). The standalone
`make lean-browser-check` command starts a temporary local service when needed
and independently verifies the complete HTTP-to-Lean-Live workflow.

To publish the same interactive proof experience on the existing faculty
website, deploy the explorer controls and isolated same-origin PHP gateway,
then start the managed loopback-only SSH proof tunnel:

```bash
make deploy-lean-public
make lean-public-start
make lean-public-check
```

The faculty server receives neither a Lean installation nor the private
companion project: its narrowly scoped gateway forwards reviewed proof jobs to
the existing bounded, independently checked worker. The public theorem graphs
retain progress, cancellation, verified `.lean`/ZIP downloads, and genuinely
self-contained Lean Live links. Use `make lean-public-status` to inspect the
service and `make lean-public-stop` to disconnect it. The foreground
`make lean-public` workflow also remains available. See the
[public Lean hosting guide](docs/PUBLIC_LEAN_SERVICE.md).

## License

Code and associated documentation are released under the MIT License; prose in `book/`, `vault/`,
and `research/` is additionally available under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). See [`LICENSE`](LICENSE).

*Course notes co-developed with Claude (Anthropic) as a writing and formalization assistant.*
