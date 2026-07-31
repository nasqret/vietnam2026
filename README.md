# An Introduction to Automatic Theorem Proving in Mathematics

> A six-lecture VIASM mini-course taking you from the **λ-calculus and type theory** through
> **Lean** all the way to the **auto-formalization of research mathematics** — building the
> foundations first, then climbing.

**Course page (VIASM):** <https://viasm.edu.vn/en/hdkh/Mini-Course_AIATPM>
**Landing page (notes hub):** <https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026>
**Live Lambda Lab (runs in your browser):** <https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda>
**Live Peano Lab (kernel-checked PA proofs):** <https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/>
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
| `peano-lab/` | The **Peano Lab** browser prover, its independent PA kernel, 247-entry checked arithmetic ladder, and reproducible proof-trace corpus. |
| `research/` | The **research dossier** — including the 248-node foundational arithmetic catalog (247 checked and one representation-blocked), native and Lean FTA certificates, and source/license maps. |
| `scripts/` | Book replay gate plus the deterministic Peano trace generation, export, and kernel-judged evaluation pipeline. |
| `docs/` | Lecturer-facing docs: how to build, deploy, and run each piece. |
| `MEMORY.md` · `JOURNAL.md` · `PLAN.md` + `PLAN/` | Project **memory**, dated **journal**, and the multi-level **plan**. |

For the native Apple-silicon proof-policy shell—including the sealed setup,
offline model cache, live `pa prove-model` transcript, and checking semantics—see
[`docs/LOCAL_MODEL_LAB.md`](docs/LOCAL_MODEL_LAB.md).

The installed launcher keeps the trained and current-native authorities
separate: `pa model` (and legacy bare `pa`) runs this frozen 247-theorem
diagnostic, while `pa native` dispatches to the sibling current arithmetic
worktree without verifying or loading model artifacts.

The 247-entry native ladder now reaches the Fundamental Theorem of Arithmetic
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
does not use double-negation elimination. The catalog now has 23 baseline
checked entries, 224 M20 checked entries, no planned theorem, and one
deliberately blocked conventional
integer-coefficient Bézout interface. This is a local draft-PR checkpoint, not
a deployment claim. The generated 247-theorem snapshot has 982,534 structural
nodes, 28,892 Cuts, and 204 Cut-bearing certificates, with ordered root
`eb4775dfd181dc5e45bec463a93f14b0ea9d02501c40c5167b7cae77cd4ff432`
and source digest
`295ca3b65970324e7d2ed51b57dc4510227b0abbc2d35b68a809dbde26aba868`.
The synchronized vault has 327 notes and 3,286 resolved links, including all
247 generated lemma notes. The corpus retains 13,344 transitions in 1,692
kernel-checked sessions under fingerprint
`6fc52e25f17dc2ff0c0e7a141c350430d6aa1d0a7a87b82e22840f442f666939`;
its isolated smoke has 494 sessions, 9,235 raw/9,232 unique transitions, and
all 247 authored QEDs. Local browser build `2026-07-29k` packages application
`a-77df7c0860bc`; it is not staged or deployed. The strict Jupyter Book rebuild
passes over all 38 sources with zero warnings; 194 deep links and 47 session
blocks containing 287 commands verify. Its guided zero-to-FTA route and
generated interactive atlas embed all 247 exact statements and authored proof
recipes with searchable dependency navigation. The complete Peano Lab suite
passes 1,298 tests with one intentional skip in 1,275.58 seconds; Lambda Lab
passes 360 tests plus 36 subtests. No
in-app browser was attached for this checkpoint, so direct Pyodide and rendered
book UI smokes are explicitly unclaimed.

The next proof-policy experiment is implemented as `model-v3`: 8,494 exact
authored predecessor-prefix transitions from the complete checked library plus
a version-2 deterministic plan for 70,000 synthetic rows, 32,600 unique roots,
and all 51 schemas. Its split and attestation rules keep catalog-derived proofs
train-only and reject held-out targets from every intermediate state. A
lossless v3-only prompt encoding keeps the audited worst stress-proof turn at
29,111 of Qwen's 32,768 native tokens. WMI preparation `172536` completed the
library lane and then failed closed on an over-limit synthetic ring instance;
no training or evaluation job was submitted. The repaired run uses pinned
Qwen3-1.7B Base with rank-32/alpha-64 LoRA for two epochs. This describes a
preflighted launch plan awaiting complete replay, not a trained adapter or
measured solve rate.

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

## License

Code and associated documentation are released under the MIT License; prose in `book/`, `vault/`,
and `research/` is additionally available under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). See [`LICENSE`](LICENSE).

*Course notes co-developed with Claude (Anthropic) as a writing and formalization assistant.*
