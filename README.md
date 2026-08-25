# An Introduction to Automatic Theorem Proving in Mathematics

> A six-lecture VIASM mini-course taking you from the **λ-calculus and type theory** through
> **Lean** all the way to the **auto-formalization of research mathematics** — building the
> foundations first, then climbing.

**Course page (VIASM):** <https://viasm.edu.vn/en/hdkh/Mini-Course_AIATPM>
**Landing page (notes hub):** <https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026>
**Live Lambda Lab (runs in your browser):** <https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda>
**Live Peano Lab (kernel-checked PA proofs):** <https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/>
**Interactive proof explorers:** <https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/>
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

The current local constructive-verification milestone closes the full exact
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
compiler-checked Lean theorems. Immutable Alpha v16 promotes the 315 genuinely
closed quadratic-reciprocity results, including the final root, without
changing its 1,673 enrolled statements or the 432-theorem default Stable
edition. Its 885 checked-use theorems remain separate from 788 body-only
research entries; this release does not claim a new WMI receipt.

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
Alpha/Stable promotion and a fresh pinned WMI receipt remain separate release
operations; the proof itself is complete. The catalog now
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
one admitted theorem using `pa lib alpha check THEOREM`. Theorem export through
`pa lean alpha THEOREM` independently replays its actual closed proof before
translating it to Lean; body-only Alpha rows cannot be checked or exported.

## License

Code and associated documentation are released under the MIT License; prose in `book/`, `vault/`,
and `research/` is additionally available under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). See [`LICENSE`](LICENSE).

*Course notes co-developed with Claude (Anthropic) as a writing and formalization assistant.*
